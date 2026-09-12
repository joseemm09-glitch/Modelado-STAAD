import math
from datetime import datetime

def format_num(val):
    """Formats a float, rounding to 3 decimals and dropping unnecessary zeros."""
    val = round(float(val), 3)
    if val == int(val):
        return str(int(val))
    return f"{val:.3f}".rstrip('0').rstrip('.')

def group_ranges(numbers):
    if not numbers:
        return ""
    
    # Sort and remove duplicates
    nums = sorted(list(set(numbers)))
    
    ranges = []
    start = nums[0]
    end = nums[0]
    
    for n in nums[1:]:
        if n == end + 1:
            end = n
        else:
            if start == end:
                ranges.append(str(start))
            elif end == start + 1:
                ranges.append(f"{start} {end}")
            else:
                ranges.append(f"{start} TO {end}")
            start = n
            end = n
            
    if start == end:
        ranges.append(str(start))
    elif end == start + 1:
        ranges.append(f"{start} {end}")
    else:
        ranges.append(f"{start} TO {end}")
        
    return " ".join(ranges)

def build_lines(blocks, max_len=72, continuation_char=" -"):
    """
    Groups string blocks into lines, ensuring no line exceeds max_len.
    A block will not be broken across lines.
    If a line wraps, the continuation_char is appended.
    """
    merged_blocks = []
    i = 0
    while i < len(blocks):
        if blocks[i].upper() == "TO" and merged_blocks and i + 1 < len(blocks):
            last = merged_blocks.pop()
            merged_blocks.append(last + " TO " + blocks[i+1])
            i += 2
        else:
            merged_blocks.append(blocks[i])
            i += 1

    lines = []
    current_line = ""
    for i, block in enumerate(merged_blocks):
        if not current_line:
            current_line = block
            continue
            
        # If this is the last block, it won't be followed by a continuation,
        # otherwise we must reserve space for the continuation character.
        is_last = (i == len(merged_blocks) - 1)
        allowed_len = max_len if is_last else (max_len - len(continuation_char))
        
        if len(current_line) + 1 + len(block) <= allowed_len:
            current_line += " " + block
        else:
            lines.append(current_line + continuation_char)
            current_line = block
            
    if current_line:
        lines.append(current_line)
    return "\n".join(lines)

def parse_upt_to_user_table(file_path, table_number):
    import os
    if not os.path.exists(file_path):
        return ""
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()
    out = []
    out.append(f"TABLE {table_number}")
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.lower().startswith("unit"):
            out.append("UNIT CM KG")
        elif stripped.lower() == "general":
            out.append("GENERAL")
        else:
            if len(stripped) > 72 and " " in stripped:
                out.append(build_lines(stripped.split(" "), 72))
            else:
                out.append(stripped)
    return "\n".join(out)

def write_staad(model, selected_profiles=None):
    """
    Generates STAAD.Pro input file text from a StaadModel instance.
    If selected_profiles is provided, maps {'C-1': 'HSS10X10X0.250', ...} to the respective members.
    """
    date_str = datetime.now().strftime("%d-%b-%y")
    
    out = []
    out.append("STAAD SPACE")
    out.append("START JOB INFORMATION")
    out.append(f"ENGINEER DATE {date_str}")
    out.append("END JOB INFORMATION")
    out.append("INPUT WIDTH 79")
    out.append("UNIT CM KG")
    
    # ------------------
    # JOINT COORDINATES
    # ------------------
    out.append("JOINT COORDINATES")
    nodes_blocks = []
    for nid, (x, y, z) in model.nodes.items():
        nodes_blocks.append(f"{nid} {format_num(x)} {format_num(y)} {format_num(z)};")
    
    out.append(build_lines(nodes_blocks, 72, continuation_char=""))
    
    # ------------------
    # MEMBER INCIDENCES
    # ------------------
    out.append("MEMBER INCIDENCES")
    members_blocks = []
    for mid, (n1, n2) in model.members.items():
        members_blocks.append(f"{mid} {n1} {n2};")
    
    out.append(build_lines(members_blocks, 72, continuation_char=""))
    
    # ------------------
    # ELEMENT INCIDENCES
    # ------------------
    if getattr(model, 'plates', None):
        out.append("ELEMENT INCIDENCES")
        plates_blocks = []
        for pid, (n1, n2, n3, n4) in model.plates.items():
            plates_blocks.append(f"{pid} {n1} {n2} {n3} {n4};")
        out.append(build_lines(plates_blocks, 72, continuation_char=""))
    
    # ------------------
    # Groups
    # ------------------
    out.append("START GROUP DEFINITION")
    out.append("MEMBER")
    
    # Group names mapping

    group_map = {}
    larg_grp_info = getattr(model, 'largueros_group_info', None)
    if larg_grp_info:
        for grp_name in larg_grp_info.keys():
            group_map[grp_name] = model.groups.get(grp_name, [])
    else:
        for j in range(model.nSpan):
            group_map[f'_LARGUEROS_{j}'] = model.groups.get(f'_LARGUEROS_{j}', [])
    group_map.update({
        '_COL': model.groups.get('_COL', []),
        '_COLVIENTO': model.groups.get('_COLVIENTO', []),
        '_CS': model.groups.get('_CS', []),
        '_CI': model.groups.get('_CI', []),
        '_CS_PERIM': model.groups.get('_CS_PERIM', []),
        '_CI_PERIM': model.groups.get('_CI_PERIM', []),
        '_MONTANTES': model.groups.get('_MONTANTES', []),
        '_DIAG': model.groups.get('_DIAG', []),
        '_MONTANTES_PERIM': model.groups.get('_MONTANTES_PERIM', []),
        '_DIAG_PERIM': model.groups.get('_DIAG_PERIM', []),
        '_CELOSIA': sorted(list(set(
            model.groups.get('_MONTANTES', []) + 
            model.groups.get('_DIAG', []) +
            model.groups.get('_MONTANTES_PERIM', []) + 
            model.groups.get('_DIAG_PERIM', [])
        ))),

        '_JOISTGRAL': model.groups.get('_JOISTGRAL', []),
        '_JPUNTAL': model.groups.get('_JPUNTAL', []),
        '_ARMADURA_CENTRAL': sorted(list(set(
            model.groups.get('_CS', []) + 
            model.groups.get('_CI', []) + 
            model.groups.get('_MONTANTES', []) + 
            model.groups.get('_DIAG', [])
        ))),
        '_ARMADURA_PERIM': sorted(list(set(
            model.groups.get('_CS_PERIM', []) + 
            model.groups.get('_CI_PERIM', []) + 
            model.groups.get('_MONTANTES_PERIM', []) + 
            model.groups.get('_DIAG_PERIM', [])
        ))),
        '_CVH': model.groups.get('_CVH', []),
        '_REL_CSCI_START': model.rel_csci_start,
        '_REL_CSCI_END': model.rel_csci_end,
        '_REL_HORIZ_START': model.rel_horiz_start,
        '_REL_HORIZ_END': model.rel_horiz_end,
        '_REL_LARG_START': model.rel_larg_start,
        '_REL_LARG_END': model.rel_larg_end,
        '_REL_TILTUP_START': getattr(model, 'rel_tiltup_start', []),
        '_REL_TILTUP_END': getattr(model, 'rel_tiltup_end', []),
        '_REL_END_FX': model.release_end_fx,
        '_CI_INT': model.ci_int,
        '_CS_SEC': model.groups.get('_CS_SEC', []),
        '_CI_SEC': model.groups.get('_CI_SEC', []),
        '_MONTANTES_SEC': model.groups.get('_MONTANTES_SEC', []),
        '_DIAG_SEC': model.groups.get('_DIAG_SEC', []),
        '_REL_SEC_START': sorted(list(set(model.rel_cs_sec_start + model.rel_ci_sec_start))),
        '_REL_SEC_END': sorted(list(set(model.rel_cs_sec_end + model.rel_ci_sec_end))),
        '_CELOSIA_SEC': sorted(list(set(
            model.groups.get('_MONTANTES_SEC', []) + 
            model.groups.get('_DIAG_SEC', [])
        ))),
        '_ARMADURA_SEC': sorted(list(set(
            model.groups.get('_CS_SEC', []) + 
            model.groups.get('_CI_SEC', []) + 
            model.groups.get('_MONTANTES_SEC', []) + 
            model.groups.get('_DIAG_SEC', [])
        ))),
        '_ARMADURA_MD': getattr(model, 'groups', {}).get('_ARMADURA_MD', [])
    })
    
    for name, members in group_map.items():
        if members:
            range_str = group_ranges(members)
            if range_str:
                out.append(build_lines([name] + range_str.split(" "), 72))
                
    # ------------------
    # Propiedades (User Tables primero)
    # ------------------
    from templates import USER_TABLES_TEMPLATE, CARGAS_TEMPLATE
    import os
    user_tables_str = USER_TABLES_TEMPLATE.strip()
    if "END USER TABLE" in user_tables_str:
        user_tables_str = user_tables_str.replace("END USER TABLE", "").strip()
    out.append(user_tables_str)
    
    app_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_dir = os.path.dirname(app_dir)
    archivos_dir = os.path.join(workspace_dir, "Archivos")
    
    joist_gral_path = os.path.join(archivos_dir, "JOISTGRAL.UPT")
    if not os.path.exists(joist_gral_path):
        raise FileNotFoundError(f"No se encontro el archivo UPT para Joist General: {joist_gral_path}")
    out.append(parse_upt_to_user_table(joist_gral_path, 2))
        
    joist_puntal_path = os.path.join(archivos_dir, "JPUNTAL.UPT")
    if not os.path.exists(joist_puntal_path):
        raise FileNotFoundError(f"No se encontro el archivo UPT para Joist Puntal: {joist_puntal_path}")
    out.append(parse_upt_to_user_table(joist_puntal_path, 3))
        
    out.append("END USER TABLE")
    
    out.append("MEMBER PROPERTY AMERICAN")
    
    col_str = group_ranges(group_map.get('_COL', []))
    colviento_str = group_ranges(group_map.get('_COLVIENTO', []))
    larg_str = group_ranges(group_map.get('_LARGUEROS', []))
    cs_str = group_ranges(group_map.get('_CS', []))
    ci_str = group_ranges(group_map.get('_CI', []))
    cs_perim_str = group_ranges(group_map.get('_CS_PERIM', []))
    ci_perim_str = group_ranges(group_map.get('_CI_PERIM', []))
    celosia_str = group_ranges(group_map.get('_CELOSIA', []))
    armadura_central_str = group_ranges(group_map.get('_ARMADURA_CENTRAL', []))
    armadura_perim_str = group_ranges(group_map.get('_ARMADURA_PERIM', []))
    armadura_md_str = group_ranges(group_map.get('_ARMADURA_MD', []))
    armaduras_all = sorted(list(set(
        group_map.get('_ARMADURA_CENTRAL', []) + 
        group_map.get('_ARMADURA_PERIM', []) + 
        group_map.get('_ARMADURA_SEC', []) +
        group_map.get('_ARMADURA_MD', [])
    )))
    armaduras_all_str = group_ranges(armaduras_all)
    cv_str = group_ranges(group_map.get('_CVH', []))
    
    import prediseno
    grupos_cols = prediseno.clasificar_columnas(model)
    for g_name, ids in grupos_cols.items():
        if not ids: continue
        staad_prof = None
        if selected_profiles:
            staad_prof = selected_profiles.get(g_name)
        if not staad_prof:
            staad_prof = "W12X26" if "CV" in g_name else "HSST14X14X0.313"
        
        g_str = group_ranges(ids)
        if g_str:
            out.append(build_lines(g_str.split(" ") + [f"TABLE ST {staad_prof}"], 72))
            
    joistgral_str = group_ranges(group_map.get('_JOISTGRAL', []))
    jpuntal_str = group_ranges(group_map.get('_JPUNTAL', []))
    if joistgral_str:
        out.append(build_lines(joistgral_str.split(" ") + ["UPT 2 JOIST30"], 72))
    if jpuntal_str:
        out.append(build_lines(jpuntal_str.split(" ") + ["UPT 3 JPUNTAL"], 72))
        
    if cs_str:
        out.append(build_lines(cs_str.split(" ") + ["UPT 1 37"], 72))
    if ci_str:
        out.append(build_lines(ci_str.split(" ") + ["UPT 1 37"], 72))
    if cs_perim_str:
        out.append(build_lines(cs_perim_str.split(" ") + ["UPT 1 37"], 72))
    if ci_perim_str:
        out.append(build_lines(ci_perim_str.split(" ") + ["UPT 1 45"], 72))
        
    horiz_truss_str = group_ranges(getattr(model, 'horizontal_truss_members', []))
    if horiz_truss_str:
        out.append(build_lines(horiz_truss_str.split(" ") + ["UPT 1 33"], 72))
        
    if celosia_str:
        out.append(build_lines(celosia_str.split(" ") + ["UPT 1 12"], 72))
        
    cs_sec_str = group_ranges(group_map.get('_CS_SEC', []))
    ci_sec_str = group_ranges(group_map.get('_CI_SEC', []))
    celosia_sec_str = group_ranges(group_map.get('_CELOSIA_SEC', []))
    
    if cs_sec_str:
        out.append(build_lines(cs_sec_str.split(" ") + ["UPT 1 27"], 72))
    if ci_sec_str:
        out.append(build_lines(ci_sec_str.split(" ") + ["UPT 1 27"], 72))
    if celosia_sec_str:
        out.append(build_lines(celosia_sec_str.split(" ") + ["UPT 1 12"], 72))
        
    if cv_str:
        out.append("MEMBER PROPERTY AMERICAN")
        out.append(build_lines(cv_str.split(" ") + ["TABLE ST PIPE OD 1.905 ID 0"], 72))
        
    if getattr(model, 'dummy_md_members', []):
        dummy_str = group_ranges(model.dummy_md_members)
        if dummy_str:
            out.append("MEMBER PROPERTY AMERICAN")
            out.append(build_lines(dummy_str.split(" ") + ["PRIS YD 1.0"], 72))
        
    if getattr(model, 'plates', None):
        out.append("ELEMENT PROPERTY")
        plates_list = list(model.plates.keys())
        range_str = group_ranges(plates_list)
        out.append(build_lines(range_str.split(" ") + ["THICKNESS 20.32"], 72))
        
    # ------------------
    # Material Constants
    # ------------------
    out.extend([
        "DEFINE MATERIAL START",
        "ISOTROPIC STEEL",
        "E 2.09042e+06",
        "POISSON 0.3",
        "DENSITY 0.00783341",
        "ALPHA 1.2e-05",
        "DAMP 0.03",
        "TYPE STEEL",
        "STRENGTH FY 2581.92 FU 4158.4 RY 1.5 RT 1.2",
        "ISOTROPIC CONCRETE",
        "E 221466",
        "POISSON 0.17",
        "DENSITY 0.0024026",
        "ALPHA 5.5e-06",
        "DAMP 0.05",
        "G 94643.6",
        "TYPE CONCRETE",
        "STRENGTH FCU 281.227",
        "END DEFINE MATERIAL",
        "CONSTANTS"
    ])
    if getattr(model, 'plates', None):
        members_list = list(model.members.keys())
        if members_list:
            steel_range_str = group_ranges(members_list)
            out.append(build_lines(["MATERIAL", "STEEL", "MEMB"] + steel_range_str.split(" "), 72))
            
        plates_list = list(model.plates.keys())
        plate_range_str = group_ranges(plates_list)
        out.append(build_lines(["MATERIAL", "CONCRETE", "MEMB"] + plate_range_str.split(" "), 72))
    else:
        out.append("MATERIAL STEEL ALL")
        
    if hasattr(model, 'wind_cols'):
        beta_members = []
        beta_members.extend(model.wind_cols.get('Z0_WINDCOL', []))
        beta_members.extend(model.wind_cols.get('ZMAX_WINDCOL', []))
        if beta_members:
            beta_str = group_ranges(beta_members)
            out.append(build_lines(["BETA", "90", "MEMB"] + beta_str.split(" "), 72))
    
    # ------------------
    # Specifications
    # ------------------
    if (model.rel_csci_start or model.rel_csci_end or 
        model.rel_cs_sec_start or model.rel_cs_sec_end or
        model.rel_ci_sec_start or model.rel_ci_sec_end or
        model.rel_horiz_start or model.rel_horiz_end or 
        model.rel_larg_start or model.rel_larg_end or 
        getattr(model, 'rel_tiltup_start', []) or getattr(model, 'rel_tiltup_end', []) or
        model.release_end_fx):
        out.append("MEMBER RELEASE")
        if model.rel_csci_start:
            out.append("_REL_CSCI_START START MY MZ")
        if model.rel_csci_end:
            out.append("_REL_CSCI_END END MY MZ")
        if model.rel_cs_sec_start or model.rel_ci_sec_start:
            out.append("_REL_SEC_START START MY MZ")
        if model.rel_cs_sec_end or model.rel_ci_sec_end:
            out.append("_REL_SEC_END END MY MZ")
        if model.rel_horiz_start:
            out.append("_REL_HORIZ_START START MY MZ")
        if model.rel_horiz_end:
            out.append("_REL_HORIZ_END END MY MZ")
        if model.rel_larg_start:
            out.append("_REL_LARG_START START MY MZ")
        if model.rel_larg_end:
            out.append("_REL_LARG_END END MY MZ")
        if getattr(model, 'rel_tiltup_start', []):
            out.append("_REL_TILTUP_START START FX MY MZ")
        if getattr(model, 'rel_tiltup_end', []):
            out.append("_REL_TILTUP_END END FX MY MZ")
        if model.release_end_fx:
            out.append("_REL_END_FX END FX MY MZ")

    if getattr(model, 'plate_releases_j1_j4', []) or getattr(model, 'plate_releases_j2_j3', []):
        out.append("ELEMENT RELEASE")
        if getattr(model, 'plate_releases_j1_j4', []):
            range_str = group_ranges(model.plate_releases_j1_j4)
            out.append(build_lines(range_str.split(" ") + ["J1", "MX", "MY", "MZ"], 72))
            out.append(build_lines(range_str.split(" ") + ["J4", "MX", "MY", "MZ"], 72))
        if getattr(model, 'plate_releases_j2_j3', []):
            range_str = group_ranges(model.plate_releases_j2_j3)
            out.append(build_lines(range_str.split(" ") + ["J2", "MX", "MY", "MZ"], 72))
            out.append(build_lines(range_str.split(" ") + ["J3", "MX", "MY", "MZ"], 72))
            
    if model.groups.get('_CVH', []):
        out.append("MEMBER TENSION")
        out.append("_CVH")

    if getattr(model, 'dummy_md_members', []):
        dummy_str = group_ranges(model.dummy_md_members)
        if dummy_str:
            out.append(build_lines(["INACTIVE", "MEMBER"] + dummy_str.split(" "), 72))

        
    # ------------------
    # Supports
    # ------------------
    if model.base_nodes or getattr(model, 'wind_base_nodes', []):
        out.append("SUPPORTS")
        if model.base_nodes:
            base_str = group_ranges(model.base_nodes)
            if model.support_type == "RESORTE":
                val = getattr(model, 'resorte_val', '1000000')
                support_line = f"{base_str} FIXED BUT KMX {val} KMY {val} KMZ {val}"
            else:
                support_line = f"{base_str} {model.support_type}"
            out.append(build_lines(support_line.split(" "), 72))
        if getattr(model, 'wind_base_nodes', []):
            w_base_str = group_ranges(model.wind_base_nodes)
            support_line = f"{w_base_str} PINNED"
            out.append(build_lines(support_line.split(" "), 72))
        
    # ------------------
    # Cargas y Combinaciones
    # ------------------
    cargas_text = CARGAS_TEMPLATE
            
    # Reemplazar Carga Muerta (LOAD 1)
    def get_trib_x_sec(j_idx):
        if j_idx == 0:
            return (model.Larm_list[0] / model.subdiv_list[0]) / 2.0
        elif j_idx == model.nSpan:
            return (model.Larm_list[-1] / model.subdiv_list[-1]) / 2.0
        else:
            return (model.Larm_list[j_idx-1] / model.subdiv_list[j_idx-1] + model.Larm_list[j_idx] / model.subdiv_list[j_idx]) / 2.0

    cm_load_lines = [f"**** CM CUBIERTA: {model.c_muerta} Kg/m² *****\nMEMBER LOAD"]
    if getattr(model, 'largueros_group_info', None):
        for grp_name, info in model.largueros_group_info.items():
            if model.groups.get(grp_name):
                load_cm = (model.c_muerta * info['spacing']) / 100.0
                cm_load_lines.append(f"{grp_name} UNI GY -{format_num(load_cm)}")
    else:
        for j in range(model.nSpan):
            if model.groups.get(f'_LARGUEROS_{j}'):
                load_cm = (model.c_muerta * (model.Larm_list[j] / model.subdiv_list[j])) / 100.0
                cm_load_lines.append(f"_LARGUEROS_{j} UNI GY -{format_num(load_cm)}")
    for j in range(model.nSpan + 1):
        if f'_CS_SEC_{j}' in model.groups and model.groups[f'_CS_SEC_{j}']:
            load_cm = (model.c_muerta * get_trib_x_sec(j)) / 100.0
            rng = group_ranges(model.groups[f'_CS_SEC_{j}'])
            if rng: cm_load_lines.append(f"{rng} UNI GY -{format_num(load_cm)}")
    cm_load_str = "\n".join(cm_load_lines)
    
    cargas_text = cargas_text.replace(
        "**** CM CUBIERTA: 39.50 Kg/m² *****",
        cm_load_str
    )
    
    # Añadir Carga Viva (LOAD 5)
    cv_load_lines = [f"**** CV CUBIERTA: {model.c_viva} Kg/m² *****\nMEMBER LOAD"]
    if getattr(model, 'largueros_group_info', None):
        for grp_name, info in model.largueros_group_info.items():
            if model.groups.get(grp_name):
                load_cv = (model.c_viva * info['spacing']) / 100.0
                cv_load_lines.append(f"{grp_name} UNI GY -{format_num(load_cv)}")
    else:
        for j in range(model.nSpan):
            if model.groups.get(f'_LARGUEROS_{j}'):
                load_cv = (model.c_viva * (model.Larm_list[j] / model.subdiv_list[j])) / 100.0
                cv_load_lines.append(f"_LARGUEROS_{j} UNI GY -{format_num(load_cv)}")
    for j in range(model.nSpan + 1):
        if f'_CS_SEC_{j}' in model.groups and model.groups[f'_CS_SEC_{j}']:
            load_cv = (model.c_viva * get_trib_x_sec(j)) / 100.0
            rng = group_ranges(model.groups[f'_CS_SEC_{j}'])
            if rng: cv_load_lines.append(f"{rng} UNI GY -{format_num(load_cv)}")
    cv_load_str = "\n".join(cv_load_lines)
    
    cargas_text = cargas_text.replace(
        "**** CV CUBIERTA: 100 Kg/m² *****\nMEMBER LOAD",
        cv_load_str
    )
    
    # Añadir Granizo (LOAD 15)
    granizo_load_lines = [f"**** CARGA DE GRANIZO: {model.c_granizo} Kg/m² *****\nMEMBER LOAD"]
    if getattr(model, 'largueros_group_info', None):
        for grp_name, info in model.largueros_group_info.items():
            if model.groups.get(grp_name):
                load_granizo = (model.c_granizo * info['spacing']) / 100.0
                granizo_load_lines.append(f"{grp_name} UNI GY -{format_num(load_granizo)}")
    else:
        for j in range(model.nSpan):
            if model.groups.get(f'_LARGUEROS_{j}'):
                load_granizo = (model.c_granizo * (model.Larm_list[j] / model.subdiv_list[j])) / 100.0
                granizo_load_lines.append(f"_LARGUEROS_{j} UNI GY -{format_num(load_granizo)}")
    for j in range(model.nSpan + 1):
        if f'_CS_SEC_{j}' in model.groups and model.groups[f'_CS_SEC_{j}']:
            load_granizo = (model.c_granizo * get_trib_x_sec(j)) / 100.0
            rng = group_ranges(model.groups[f'_CS_SEC_{j}'])
            if rng: granizo_load_lines.append(f"{rng} UNI GY -{format_num(load_granizo)}")
    granizo_load_str = "\n".join(granizo_load_lines)
    cargas_text = cargas_text.replace(
        "**** CARGA DE GRANIZO: 60 Kg/m² *****",
        granizo_load_str
    )

    def write_column_wind_loads(col_list, v_wind, col_trib_dict, dir_axis, sign):
        # Groups columns by load magnitude and generates STAAD lines
        load_groups = {}
        for c in col_list:
            if c in col_trib_dict:
                trib = col_trib_dict[c]
                w = (v_wind * trib) / 100.0
                w_rounded = round(w, 3)
                if w_rounded not in load_groups:
                    load_groups[w_rounded] = []
                load_groups[w_rounded].append(c)
        
        lines = []
        for w, members in load_groups.items():
            if members:
                rng = group_ranges(members)
                if rng:
                    tokens = rng.split(" ") + ["UNI", dir_axis, format_num(w * sign)]
                    lines.append(build_lines(tokens, 72))
        return lines

    
    # Función auxiliar para viento
    def wind_block(wind_type, model):
        def gl(members, d_str, val, mult):
            rng = group_ranges(members)
            if not rng: return ""
            tokens = rng.split(" ") + ["UNI", d_str, format_num(val * mult)]
            return build_lines(tokens, 72)
            
        def pl(plates, d_str, val, mult):
            rng = group_ranges(plates)
            if not rng: return ""
            tokens = rng.split(" ") + ["PR", d_str, format_num((val / 10000.0) * mult)]
            return build_lines(tokens, 72)
            
        lines = []
        is_tiltup = (getattr(model, 'wall_type', None) == "Tilt-Up")
        
        if is_tiltup:
            lines.append("ELEMENT LOAD")
        else:
            lines.append("MEMBER LOAD")
            
        if wind_type == "X+":
            lines.append(f"******BARLOVENTO: {model.v_barlovento} Kg/m²******")
            if is_tiltup:
                lines.append(pl(model.plate_groups['X0'], 'GX', model.v_barlovento, 1))
            else:
                lines.extend(write_column_wind_loads(model.wind_cols['X0_CORNER'], model.v_barlovento, model.col_trib_x, 'GX', 1))
                lines.extend(write_column_wind_loads(model.wind_cols['X0_INNER'], model.v_barlovento, model.col_trib_x, 'GX', 1))
                lines.extend(write_column_wind_loads(model.wind_cols.get('X0_WINDCOL', []), model.v_barlovento, model.col_trib_x, 'GX', 1))
                
            lines.append(f"******SOTAVENTO: {model.v_sotavento} Kg/m²******")
            if is_tiltup:
                lines.append(pl(model.plate_groups['XMAX'], 'GX', model.v_sotavento, 1))
            else:
                lines.extend(write_column_wind_loads(model.wind_cols['XMAX_CORNER'], model.v_sotavento, model.col_trib_x, 'GX', 1))
                lines.extend(write_column_wind_loads(model.wind_cols['XMAX_INNER'], model.v_sotavento, model.col_trib_x, 'GX', 1))
                lines.extend(write_column_wind_loads(model.wind_cols.get('XMAX_WINDCOL', []), model.v_sotavento, model.col_trib_x, 'GX', 1))
                
            lines.append(f"******LATERALES 1: {model.v_laterales} Kg/m²******")
            if is_tiltup:
                lines.append(pl(model.plate_groups['Z0'], 'GZ', model.v_laterales, -1))
            else:
                lines.extend(write_column_wind_loads(model.wind_cols['Z0_CORNER'], model.v_laterales, model.col_trib_z, 'GZ', -1))
                lines.extend(write_column_wind_loads(model.wind_cols['Z0_INNER'], model.v_laterales, model.col_trib_z, 'GZ', -1))
                lines.extend(write_column_wind_loads(model.wind_cols.get('Z0_WINDCOL', []), model.v_laterales, model.col_trib_z, 'GZ', -1))
                
            lines.append(f"******LATERALES 2: {model.v_laterales} Kg/m²******")
            if is_tiltup:
                lines.append(pl(model.plate_groups['ZMAX'], 'GZ', model.v_laterales, 1))
            else:
                lines.extend(write_column_wind_loads(model.wind_cols['ZMAX_CORNER'], model.v_laterales, model.col_trib_z, 'GZ', 1))
                lines.extend(write_column_wind_loads(model.wind_cols['ZMAX_INNER'], model.v_laterales, model.col_trib_z, 'GZ', 1))
                lines.extend(write_column_wind_loads(model.wind_cols.get('ZMAX_WINDCOL', []), model.v_laterales, model.col_trib_z, 'GZ', 1))
                
        elif wind_type == "X-":
            lines.append(f"******BARLOVENTO: {model.v_barlovento} Kg/m²******")
            if is_tiltup:
                lines.append(pl(model.plate_groups['XMAX'], 'GX', model.v_barlovento, -1))
            else:
                lines.extend(write_column_wind_loads(model.wind_cols['XMAX_CORNER'], model.v_barlovento, model.col_trib_x, 'GX', -1))
                lines.extend(write_column_wind_loads(model.wind_cols['XMAX_INNER'], model.v_barlovento, model.col_trib_x, 'GX', -1))
                lines.extend(write_column_wind_loads(model.wind_cols.get('XMAX_WINDCOL', []), model.v_barlovento, model.col_trib_x, 'GX', -1))
                
            lines.append(f"******SOTAVENTO: {model.v_sotavento} Kg/m²******")
            if is_tiltup:
                lines.append(pl(model.plate_groups['X0'], 'GX', model.v_sotavento, -1))
            else:
                lines.extend(write_column_wind_loads(model.wind_cols['X0_CORNER'], model.v_sotavento, model.col_trib_x, 'GX', -1))
                lines.extend(write_column_wind_loads(model.wind_cols['X0_INNER'], model.v_sotavento, model.col_trib_x, 'GX', -1))
                lines.extend(write_column_wind_loads(model.wind_cols.get('X0_WINDCOL', []), model.v_sotavento, model.col_trib_x, 'GX', -1))
                
            lines.append(f"******LATERALES 1: {model.v_laterales} Kg/m²******")
            if is_tiltup:
                lines.append(pl(model.plate_groups['Z0'], 'GZ', model.v_laterales, -1))
            else:
                lines.extend(write_column_wind_loads(model.wind_cols['Z0_CORNER'], model.v_laterales, model.col_trib_z, 'GZ', -1))
                lines.extend(write_column_wind_loads(model.wind_cols['Z0_INNER'], model.v_laterales, model.col_trib_z, 'GZ', -1))
                lines.extend(write_column_wind_loads(model.wind_cols.get('Z0_WINDCOL', []), model.v_laterales, model.col_trib_z, 'GZ', -1))
                
            lines.append(f"******LATERALES 2: {model.v_laterales} Kg/m²******")
            if is_tiltup:
                lines.append(pl(model.plate_groups['ZMAX'], 'GZ', model.v_laterales, 1))
            else:
                lines.extend(write_column_wind_loads(model.wind_cols['ZMAX_CORNER'], model.v_laterales, model.col_trib_z, 'GZ', 1))
                lines.extend(write_column_wind_loads(model.wind_cols['ZMAX_INNER'], model.v_laterales, model.col_trib_z, 'GZ', 1))
                lines.extend(write_column_wind_loads(model.wind_cols.get('ZMAX_WINDCOL', []), model.v_laterales, model.col_trib_z, 'GZ', 1))
                
        elif wind_type == "Z+":
            lines.append(f"******BARLOVENTO: {model.v_barlovento} Kg/m²******")
            if is_tiltup:
                lines.append(pl(model.plate_groups['Z0'], 'GZ', model.v_barlovento, 1))
            else:
                lines.extend(write_column_wind_loads(model.wind_cols['Z0_CORNER'], model.v_barlovento, model.col_trib_z, 'GZ', 1))
                lines.extend(write_column_wind_loads(model.wind_cols['Z0_INNER'], model.v_barlovento, model.col_trib_z, 'GZ', 1))
                lines.extend(write_column_wind_loads(model.wind_cols.get('Z0_WINDCOL', []), model.v_barlovento, model.col_trib_z, 'GZ', 1))
                
            lines.append(f"******SOTAVENTO: {model.v_sotavento} Kg/m²******")
            if is_tiltup:
                lines.append(pl(model.plate_groups['ZMAX'], 'GZ', model.v_sotavento, 1))
            else:
                lines.extend(write_column_wind_loads(model.wind_cols['ZMAX_CORNER'], model.v_sotavento, model.col_trib_z, 'GZ', 1))
                lines.extend(write_column_wind_loads(model.wind_cols['ZMAX_INNER'], model.v_sotavento, model.col_trib_z, 'GZ', 1))
                lines.extend(write_column_wind_loads(model.wind_cols.get('ZMAX_WINDCOL', []), model.v_sotavento, model.col_trib_z, 'GZ', 1))
                
            lines.append(f"******LATERALES 1: {model.v_laterales} Kg/m²******")
            if is_tiltup:
                lines.append(pl(model.plate_groups['X0'], 'GX', model.v_laterales, -1))
            else:
                lines.extend(write_column_wind_loads(model.wind_cols['X0_CORNER'], model.v_laterales, model.col_trib_x, 'GX', -1))
                lines.extend(write_column_wind_loads(model.wind_cols['X0_INNER'], model.v_laterales, model.col_trib_x, 'GX', -1))
                lines.extend(write_column_wind_loads(model.wind_cols.get('X0_WINDCOL', []), model.v_laterales, model.col_trib_x, 'GX', -1))
                
            lines.append(f"******LATERALES 2: {model.v_laterales} Kg/m²******")
            if is_tiltup:
                lines.append(pl(model.plate_groups['XMAX'], 'GX', model.v_laterales, 1))
            else:
                lines.extend(write_column_wind_loads(model.wind_cols['XMAX_CORNER'], model.v_laterales, model.col_trib_x, 'GX', 1))
                lines.extend(write_column_wind_loads(model.wind_cols['XMAX_INNER'], model.v_laterales, model.col_trib_x, 'GX', 1))
                lines.extend(write_column_wind_loads(model.wind_cols.get('XMAX_WINDCOL', []), model.v_laterales, model.col_trib_x, 'GX', 1))
                
        elif wind_type == "Z-":
            lines.append(f"******BARLOVENTO: {model.v_barlovento} Kg/m²******")
            if is_tiltup:
                lines.append(pl(model.plate_groups['ZMAX'], 'GZ', model.v_barlovento, -1))
            else:
                lines.extend(write_column_wind_loads(model.wind_cols['ZMAX_CORNER'], model.v_barlovento, model.col_trib_z, 'GZ', -1))
                lines.extend(write_column_wind_loads(model.wind_cols['ZMAX_INNER'], model.v_barlovento, model.col_trib_z, 'GZ', -1))
                lines.extend(write_column_wind_loads(model.wind_cols.get('ZMAX_WINDCOL', []), model.v_barlovento, model.col_trib_z, 'GZ', -1))
                
            lines.append(f"******SOTAVENTO: {model.v_sotavento} Kg/m²******")
            if is_tiltup:
                lines.append(pl(model.plate_groups['Z0'], 'GZ', model.v_sotavento, -1))
            else:
                lines.extend(write_column_wind_loads(model.wind_cols['Z0_CORNER'], model.v_sotavento, model.col_trib_z, 'GZ', -1))
                lines.extend(write_column_wind_loads(model.wind_cols['Z0_INNER'], model.v_sotavento, model.col_trib_z, 'GZ', -1))
                lines.extend(write_column_wind_loads(model.wind_cols.get('Z0_WINDCOL', []), model.v_sotavento, model.col_trib_z, 'GZ', -1))
                
            lines.append(f"******LATERALES 1: {model.v_laterales} Kg/m²******")
            if is_tiltup:
                lines.append(pl(model.plate_groups['X0'], 'GX', model.v_laterales, -1))
            else:
                lines.extend(write_column_wind_loads(model.wind_cols['X0_CORNER'], model.v_laterales, model.col_trib_x, 'GX', -1))
                lines.extend(write_column_wind_loads(model.wind_cols['X0_INNER'], model.v_laterales, model.col_trib_x, 'GX', -1))
                lines.extend(write_column_wind_loads(model.wind_cols.get('X0_WINDCOL', []), model.v_laterales, model.col_trib_x, 'GX', -1))
                
            lines.append(f"******LATERALES 2: {model.v_laterales} Kg/m²******")
            if is_tiltup:
                lines.append(pl(model.plate_groups['XMAX'], 'GX', model.v_laterales, 1))
            else:
                lines.extend(write_column_wind_loads(model.wind_cols['XMAX_CORNER'], model.v_laterales, model.col_trib_x, 'GX', 1))
                lines.extend(write_column_wind_loads(model.wind_cols['XMAX_INNER'], model.v_laterales, model.col_trib_x, 'GX', 1))
                lines.extend(write_column_wind_loads(model.wind_cols.get('XMAX_WINDCOL', []), model.v_laterales, model.col_trib_x, 'GX', 1))
        
        if is_tiltup:
            lines.append("MEMBER LOAD")
            
        lines.append(f"**** SUCCIÓN: {model.v_succion} Kg/m² *****")
        if getattr(model, 'largueros_group_info', None):
            for grp_name, info in model.largueros_group_info.items():
                if model.groups.get(grp_name):
                    load_succion = (model.v_succion * info['spacing']) / 100.0
                    lines.append(build_lines([grp_name, "UNI", "GY", format_num(load_succion)], 72))
        else:
            for j in range(model.nSpan):
                dist_largueros = model.Larm_list[j] / model.subdiv_list[j]
                load_succion = (model.v_succion * dist_largueros) / 100.0
                if model.groups.get(f'_LARGUEROS_{j}'):
                    lines.append(build_lines([f"_LARGUEROS_{j}", "UNI", "GY", format_num(load_succion)], 72))
        
        return "\n".join([x for x in lines if x])
        
    old_wind_block = "******BARLOVENTO: 86 Kg/m²******\n******SOTAVENTO: 50 Kg/m²******\n******LATERALES 1: 78 Kg/m²******\n******LATERALES 2: 78 Kg/m²******\n**** SUCCIÓN: 95 Kg/m² *****"
    
    cargas_text = cargas_text.replace(f"LOAD 7 LOADTYPE None  TITLE VIENTO X+\nMEMBER LOAD\n{old_wind_block}", f"LOAD 7 LOADTYPE None  TITLE VIENTO X+\n{wind_block('X+', model)}")
    cargas_text = cargas_text.replace(f"LOAD 8 LOADTYPE None  TITLE VIENTO X-\nMEMBER LOAD\n{old_wind_block}", f"LOAD 8 LOADTYPE None  TITLE VIENTO X-\n{wind_block('X-', model)}")
    cargas_text = cargas_text.replace(f"LOAD 9 LOADTYPE None  TITLE VIENTO Z+\nMEMBER LOAD\n{old_wind_block}", f"LOAD 9 LOADTYPE None  TITLE VIENTO Z+\n{wind_block('Z+', model)}")
    cargas_text = cargas_text.replace(f"LOAD 10 LOADTYPE None  TITLE VIENTO Z-\nMEMBER LOAD\n{old_wind_block}", f"LOAD 10 LOADTYPE None  TITLE VIENTO Z-\n{wind_block('Z-', model)}")

    # Función auxiliar para sismo
    def seismic_block(direction, model):
        col_str = group_ranges(model.groups.get('_COL', []))
        colviento_str = group_ranges(model.groups.get('_COLVIENTO', []))
        lines = []
        
        axis = "X" if "X" in direction else "Z"
        sign = -1 if "-" in direction else 1
        
        # SELFWEIGHT
        if col_str:
            tokens = [f"SELFWEIGHT {axis} {format_num(sign * model.seismic_v)} LIST"] + col_str.split(" ")
            lines.append(build_lines(tokens))
            
        if colviento_str:
            tokens = [f"SELFWEIGHT {axis} {format_num(sign * model.seismic_v)} LIST"] + colviento_str.split(" ")
            lines.append(build_lines(tokens))
            
        if getattr(model, 'wall_type', None) == "Tilt-Up":
            if axis == "X":
                target_plates = model.plate_groups['X0'] + model.plate_groups['XMAX']
            else:
                target_plates = model.plate_groups['Z0'] + model.plate_groups['ZMAX']
            
            plates_str = group_ranges(target_plates)
            if plates_str:
                tokens = [f"SELFWEIGHT {axis} {format_num(sign * model.seismic_v)} LIST"] + plates_str.split(" ")
                lines.append(build_lines(tokens))
            
        lines.append("JOINT LOAD")
        
        def joint_load(nodes, load_val):
            rng = group_ranges(nodes)
            if not rng: return ""
            tokens = rng.split(" ") + [f"F{axis}", format_num(sign * load_val)]
            return build_lines(tokens, 72)
            
        # Agrupar las cargas sísmicas por categorías (ESQUINAS, PERIMETRALES, CENTRALES)
        if hasattr(model, 'seismic_nodal_groups') and model.seismic_nodal_groups:
            current_cat = None
            for grp in model.seismic_nodal_groups:
                nodes = grp['nodes']
                load_val = grp['load']
                if load_val > 0.0 and nodes:
                    cat = grp['category']
                    if cat != current_cat:
                        lines.append(f"* {cat}")
                        current_cat = cat
                    jl = joint_load(nodes, load_val)
                    if jl:
                        lines.append(jl)
        elif hasattr(model, 'seismic_load_groups'):
            for load_val, nodes in model.seismic_load_groups.items():
                if load_val > 0.0 and nodes:
                    jl = joint_load(nodes, load_val)
                    if jl:
                        lines.append(jl)
        
        return "\n".join([x for x in lines if x])
        
    cargas_text = cargas_text.replace("**** SISMO X+ BLOCK ****", seismic_block('X+', model))
    cargas_text = cargas_text.replace("**** SISMO X- BLOCK ****", seismic_block('X-', model))
    cargas_text = cargas_text.replace("**** SISMO Z+ BLOCK ****", seismic_block('Z+', model))
    cargas_text = cargas_text.replace("**** SISMO Z- BLOCK ****", seismic_block('Z-', model))
     
    # Cambiar el tipo de carga sismica a Seismic-H según petición
    cargas_text = cargas_text.replace("LOADTYPE Seismic", "LOADTYPE Seismic-H")
    
    # Append the base cargas text
    out.append(cargas_text.strip())
    
    # ------------------
    # Analysis & Design
    # ------------------
    out.append("PERFORM ANALYSIS")
    out.append("LOAD LIST 17 TO 54")
    out.append("PARAMETER 1")
    out.append("CODE AISC")
    
    if celosia_str:
        out.append("** CELOSÍA **")
        out.append(build_lines(["FYLD", "3515", "MEMB"] + celosia_str.split(" "), 72))
        out.append(build_lines(["SELECT", "MEMB"] + celosia_str.split(" "), 72))
        
    out.append("PERFORM ANALYSIS")
    out.append("LOAD LIST 17 TO 54")
    out.append("PARAMETER 2")
    out.append("CODE AISC")
    
    if col_str:
        out.append("** COLUMNAS **")
        out.append(build_lines(["FYLD", "3200", "MEMB"] + col_str.split(" "), 72))
        out.append(build_lines(["KY", "1.4", "MEMB"] + col_str.split(" "), 72))
        out.append(build_lines(["KZ", "1.7", "MEMB"] + col_str.split(" "), 72))
        for h_rounded, members in model.col_heights.items():
            if members:
                m_str = group_ranges(members)
                out.append(build_lines(["LY", str(h_rounded), "MEMB"] + m_str.split(" "), 72))
                
    if colviento_str:
        out.append("** COLUMNAS DE VIENTO **")
        out.append(build_lines(["FYLD", "3515", "MEMB"] + colviento_str.split(" "), 72))
        out.append(build_lines(["KY", "1.4", "MEMB"] + colviento_str.split(" "), 72))
        out.append(build_lines(["KZ", "1.4", "MEMB"] + colviento_str.split(" "), 72))
        
        # Parámetros especiales para columnas Doble IPR (WD)
        if selected_profiles:
            import prediseno
            grupos_cols = prediseno.clasificar_columnas(model)
            wd_members = []
            for g_name, ids in grupos_cols.items():
                staad_prof = selected_profiles.get(g_name, "")
                if staad_prof.startswith("WD") and ids:
                    wd_members.extend(ids)
            
            if wd_members:
                wd_str = group_ranges(wd_members)
                if wd_str:
                    out.append("** PARÁMETROS DOBLE IPR (WD) **")
                    out.append(build_lines(["LY", "100", "MEMB"] + wd_str.split(" "), 72))
                    out.append(build_lines(["UNL", "100", "MEMB"] + wd_str.split(" "), 72))
                    out.append(build_lines(["UNT", "100", "MEMB"] + wd_str.split(" "), 72))
                    out.append(build_lines(["UNB", "100", "MEMB"] + wd_str.split(" "), 72))


    if armaduras_all_str:
        out.append("** ARMADURAS **")
        out.append(build_lines(["FYLD", "3515", "MEMB"] + armaduras_all_str.split(" "), 72))
        
    if getattr(model, 'ci_ly_groups', {}):
        for ly_val, members in model.ci_ly_groups.items():
            if members:
                m_str = group_ranges(members)
                out.append(build_lines([f"LY", str(ly_val), "MEMB"] + m_str.split(" "), 72))
    else:
        # Fallback
        ci_int_str = group_ranges(model.ci_int)
        if ci_int_str:
            ly_val = math.ceil(3 * (model.Lx / model.numSubdiv))
            out.append(f"LY {ly_val} _CI_INT")
        
    if cv_str:
        out.append("** CVH **")
        out.append(build_lines(["FYLD", "2530", "MEMB"] + cv_str.split(" "), 72))
        out.append(build_lines(["TMAIN", "10000", "MEMB"] + cv_str.split(" "), 72))
        out.append(build_lines(["MAIN", "10000", "MEMB"] + cv_str.split(" "), 72))
        
    # Check code for specific groups separately to avoid overly long lines
    if col_str:
        out.append(build_lines(["CHECK", "CODE", "MEMB"] + col_str.split(" "), 72))
    if colviento_str:
        out.append(build_lines(["CHECK", "CODE", "MEMB"] + colviento_str.split(" "), 72))
    if armadura_central_str:
        out.append(build_lines(["CHECK", "CODE", "MEMB"] + armadura_central_str.split(" "), 72))
    if armadura_perim_str:
        out.append(build_lines(["CHECK", "CODE", "MEMB"] + armadura_perim_str.split(" "), 72))
    if cv_str:
        out.append(build_lines(["CHECK", "CODE", "MEMB"] + cv_str.split(" "), 72))
    if armadura_md_str:
        out.append(build_lines(["CHECK", "CODE", "MEMB"] + armadura_md_str.split(" "), 72))
    out.append("STEEL TAKE OFF ALL")
    if col_str:
        out.append(build_lines(["STEEL", "TAKE", "OFF", "LIST"] + col_str.split(" "), 72))
    if colviento_str:
        out.append(build_lines(["STEEL", "TAKE", "OFF", "LIST"] + colviento_str.split(" "), 72))
    if armadura_central_str:
        out.append(build_lines(["STEEL", "TAKE", "OFF", "LIST"] + armadura_central_str.split(" "), 72))
    if armadura_perim_str:
        out.append(build_lines(["STEEL", "TAKE", "OFF", "LIST"] + armadura_perim_str.split(" "), 72))
    if armadura_md_str:
        out.append(build_lines(["STEEL", "TAKE", "OFF", "LIST"] + armadura_md_str.split(" "), 72))
    if cv_str:
        out.append(build_lines(["STEEL", "TAKE", "OFF", "LIST"] + cv_str.split(" "), 72))

    out.append("FINISH")
    
    return "\n".join(out)
