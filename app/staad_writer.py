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
            else:
                ranges.append(f"{start} TO {end}")
            start = n
            end = n
            
    if start == end:
        ranges.append(str(start))
    else:
        ranges.append(f"{start} TO {end}")
        
    return " ".join(ranges)

def build_lines(blocks, max_len=72, continuation_char=" -"):
    """
    Groups string blocks into lines, ensuring no line exceeds max_len.
    A block will not be broken across lines.
    If a line wraps, the continuation_char is appended.
    """
    lines = []
    current_line = ""
    for i, block in enumerate(blocks):
        if not current_line:
            current_line = block
            continue
            
        # If this is the last block, it won't be followed by a continuation,
        # otherwise we must reserve space for the continuation character.
        is_last = (i == len(blocks) - 1)
        allowed_len = max_len if is_last else (max_len - len(continuation_char))
        
        if len(current_line) + 1 + len(block) <= allowed_len:
            current_line += " " + block
        else:
            lines.append(current_line + continuation_char)
            current_line = block
            
    if current_line:
        lines.append(current_line)
    return "\n".join(lines)

def write_staad(model):
    """Generates the STAAD file content from a StaadModel object."""
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
    # Groups
    # ------------------
    out.append("START GROUP DEFINITION")
    out.append("MEMBER")
    
    # Group names mapping
    group_map = {
        '_COL': model.groups.get('_COL', []),
        '_COLVIENTO': model.groups.get('_COLVIENTO', []),
        '_CS': model.groups.get('_CS', []),
        '_CI': model.groups.get('_CI', []),
        '_MONTANTES': model.groups.get('_MONTANTES', []),
        '_DIAG': model.groups.get('_DIAG', []),
        '_CELOSIA': sorted(list(set(
            model.groups.get('_MONTANTES', []) + 
            model.groups.get('_DIAG', [])
        ))),
        '_LARGUEROS': model.groups.get('_LARGUEROS', []),
        '_ARMADURA': sorted(list(set(
            model.groups.get('_CS', []) + 
            model.groups.get('_CI', []) + 
            model.groups.get('_MONTANTES', []) + 
            model.groups.get('_DIAG', [])
        ))),
        '_CVH': model.groups.get('_CVH', []),
        '_REL_START': model.release_start,
        '_REL_END': model.release_end,
        '_REL_END_FX': model.release_end_fx,
        '_CI_INT': model.ci_int
    }
    
    for name, members in group_map.items():
        if members:
            range_str = group_ranges(members)
            if range_str:
                out.append(build_lines([name] + range_str.split(" "), 72))
                
    # ------------------
    # Propiedades (User Tables primero)
    # ------------------
    from templates import USER_TABLES_TEMPLATE, CARGAS_TEMPLATE
    out.append(USER_TABLES_TEMPLATE.strip())
    
    out.append("MEMBER PROPERTY AMERICAN")
    
    col_str = group_ranges(group_map.get('_COL', []))
    colviento_str = group_ranges(group_map.get('_COLVIENTO', []))
    larg_str = group_ranges(group_map.get('_LARGUEROS', []))
    cs_str = group_ranges(group_map.get('_CS', []))
    ci_str = group_ranges(group_map.get('_CI', []))
    celosia_str = group_ranges(group_map.get('_CELOSIA', []))
    armadura_str = group_ranges(group_map.get('_ARMADURA', []))
    cv_str = group_ranges(group_map.get('_CVH', []))
    
    if col_str:
        out.append(build_lines(col_str.split(" ") + ["TABLE", "ST", "HSST14X14X0.313"], 72))
    if colviento_str:
        out.append(build_lines(colviento_str.split(" ") + ["TABLE", "ST", "W12X19"], 72))
    if larg_str:
        out.append("MEMBER PROPERTY SJIJOIST")
        out.append(build_lines(larg_str.split(" ") + ["TABLE", "ST", "16K5"], 72))
        
    if cs_str:
        out.append(build_lines(cs_str.split(" ") + ["UPT", "1", "33"], 72))
    if ci_str:
        out.append(build_lines(ci_str.split(" ") + ["UPT", "1", "33"], 72))
        
    horiz_truss_str = group_ranges(getattr(model, 'horizontal_truss_members', []))
    if horiz_truss_str:
        out.append(build_lines(horiz_truss_str.split(" ") + ["UPT", "1", "33"], 72))
        
    if celosia_str:
        out.append(build_lines(celosia_str.split(" ") + ["UPT", "1", "12"], 72))
        
    if cv_str:
        out.append("MEMBER PROPERTY AMERICAN")
        out.append(build_lines(cv_str.split(" ") + ["TABLE", "ST", "PIPE", "OD", "1.905", "ID", "0"], 72))
        
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
    out.append("MATERIAL STEEL ALL")
    
    # ------------------
    # Specifications
    # ------------------
    if model.release_start or model.release_end or model.release_end_fx:
        out.append("MEMBER RELEASE")
        if model.release_start:
            out.append("_REL_START START MY MZ")
        if model.release_end:
            out.append("_REL_END END MY MZ")
        if model.release_end_fx:
            out.append("_REL_END_FX END FX MY MZ")
            
    if model.groups.get('_CVH', []):
        out.append("MEMBER TENSION")
        out.append("_CVH")

        
    # ------------------
    # Supports
    # ------------------
    if model.base_nodes or model.wind_base_nodes:
        out.append("SUPPORTS")
        if model.base_nodes:
            base_str = group_ranges(model.base_nodes)
            support_line = f"{base_str} {model.support_type}"
            out.append(build_lines([support_line], 72))
        if model.wind_base_nodes:
            w_base_str = group_ranges(model.wind_base_nodes)
            support_line = f"{w_base_str} PINNED"
            out.append(build_lines([support_line], 72))
        
    # ------------------
    # Cargas y Combinaciones
    # ------------------
    cargas_text = CARGAS_TEMPLATE
            
    # Reemplazar Carga Muerta (LOAD 1)
    cargas_text = cargas_text.replace(
        "**** CM CUBIERTA: 39.50 KG/M² *****",
        f"**** CM CUBIERTA: {model.c_muerta} KG/M2 *****\nMEMBER LOAD\n_LARGUEROS UNI GY -{format_num(model.load_cm)}"
    )
    # Añadir Carga Viva (LOAD 5)
    cargas_text = cargas_text.replace(
        "**** CV CUBIERTA: 100 KG/M2 *****\nMEMBER LOAD",
        f"**** CV CUBIERTA: {model.c_viva} KG/M2 *****\nMEMBER LOAD\n_LARGUEROS UNI GY -{format_num(model.load_cv)}"
    )
    # Añadir Granizo (LOAD 15)
    cargas_text = cargas_text.replace(
        "**** CARGA DE GRANIZO: 60 KG/M2 *****",
        f"**** CARGA DE GRANIZO: {model.c_granizo} KG/M2 *****\nMEMBER LOAD\n_LARGUEROS UNI GY -{format_num(model.load_granizo)}"
    )
    
    # Función auxiliar para viento
    def wind_block(wind_type, model):
        def gl(members, d_str, val, mult):
            rng = group_ranges(members)
            if not rng: return ""
            tokens = rng.split(" ") + ["UNI", d_str, format_num(val * mult)]
            return build_lines(tokens, 72)
            
        lines = []
        if wind_type == "X+":
            lines.append(f"******BARLOVENTO: {model.v_barlovento} KG/M2******")
            lines.append(gl(model.wind_cols['X0_CORNER'], 'GX', model.w_barl_x_co, 1))
            lines.append(gl(model.wind_cols['X0_INNER'], 'GX', model.w_barl_x_in, 1))
            lines.append(gl(model.wind_cols.get('X0_WINDCOL', []), 'GX', model.w_barl_x_in, 1))
            lines.append(f"******SOTAVENTO: {model.v_sotavento} KG/M2******")
            lines.append(gl(model.wind_cols['XMAX_CORNER'], 'GX', model.w_sot_x_co, 1))
            lines.append(gl(model.wind_cols['XMAX_INNER'], 'GX', model.w_sot_x_in, 1))
            lines.append(gl(model.wind_cols.get('XMAX_WINDCOL', []), 'GX', model.w_sot_x_in, 1))
            lines.append(f"******LATERALES 1: {model.v_laterales} KG/M2******")
            lines.append(gl(model.wind_cols['Z0_CORNER'], 'GZ', model.w_lat_z_co, -1))
            lines.append(gl(model.wind_cols['Z0_INNER'], 'GZ', model.w_lat_z_in, -1))
            lines.append(gl(model.wind_cols.get('Z0_WINDCOL', []), 'GZ', model.w_lat_z_in, -1))
            lines.append(f"******LATERALES 2: {model.v_laterales} KG/M2******")
            lines.append(gl(model.wind_cols['ZMAX_CORNER'], 'GZ', model.w_lat_z_co, 1))
            lines.append(gl(model.wind_cols['ZMAX_INNER'], 'GZ', model.w_lat_z_in, 1))
            lines.append(gl(model.wind_cols.get('ZMAX_WINDCOL', []), 'GZ', model.w_lat_z_in, 1))
        elif wind_type == "X-":
            lines.append(f"******BARLOVENTO: {model.v_barlovento} KG/M2******")
            lines.append(gl(model.wind_cols['XMAX_CORNER'], 'GX', model.w_barl_x_co, -1))
            lines.append(gl(model.wind_cols['XMAX_INNER'], 'GX', model.w_barl_x_in, -1))
            lines.append(gl(model.wind_cols.get('XMAX_WINDCOL', []), 'GX', model.w_barl_x_in, -1))
            lines.append(f"******SOTAVENTO: {model.v_sotavento} KG/M2******")
            lines.append(gl(model.wind_cols['X0_CORNER'], 'GX', model.w_sot_x_co, -1))
            lines.append(gl(model.wind_cols['X0_INNER'], 'GX', model.w_sot_x_in, -1))
            lines.append(gl(model.wind_cols.get('X0_WINDCOL', []), 'GX', model.w_sot_x_in, -1))
            lines.append(f"******LATERALES 1: {model.v_laterales} KG/M2******")
            lines.append(gl(model.wind_cols['Z0_CORNER'], 'GZ', model.w_lat_z_co, -1))
            lines.append(gl(model.wind_cols['Z0_INNER'], 'GZ', model.w_lat_z_in, -1))
            lines.append(gl(model.wind_cols.get('Z0_WINDCOL', []), 'GZ', model.w_lat_z_in, -1))
            lines.append(f"******LATERALES 2: {model.v_laterales} KG/M2******")
            lines.append(gl(model.wind_cols['ZMAX_CORNER'], 'GZ', model.w_lat_z_co, 1))
            lines.append(gl(model.wind_cols['ZMAX_INNER'], 'GZ', model.w_lat_z_in, 1))
            lines.append(gl(model.wind_cols.get('ZMAX_WINDCOL', []), 'GZ', model.w_lat_z_in, 1))
        elif wind_type == "Z+":
            lines.append(f"******BARLOVENTO: {model.v_barlovento} KG/M2******")
            lines.append(gl(model.wind_cols['Z0_CORNER'], 'GZ', model.w_barl_z_co, 1))
            lines.append(gl(model.wind_cols['Z0_INNER'], 'GZ', model.w_barl_z_in, 1))
            lines.append(gl(model.wind_cols.get('Z0_WINDCOL', []), 'GZ', model.w_barl_z_in, 1))
            lines.append(f"******SOTAVENTO: {model.v_sotavento} KG/M2******")
            lines.append(gl(model.wind_cols['ZMAX_CORNER'], 'GZ', model.w_sot_z_co, 1))
            lines.append(gl(model.wind_cols['ZMAX_INNER'], 'GZ', model.w_sot_z_in, 1))
            lines.append(gl(model.wind_cols.get('ZMAX_WINDCOL', []), 'GZ', model.w_sot_z_in, 1))
            lines.append(f"******LATERALES 1: {model.v_laterales} KG/M2******")
            lines.append(gl(model.wind_cols['X0_CORNER'], 'GX', model.w_lat_x_co, -1))
            lines.append(gl(model.wind_cols['X0_INNER'], 'GX', model.w_lat_x_in, -1))
            lines.append(gl(model.wind_cols.get('X0_WINDCOL', []), 'GX', model.w_lat_x_in, -1))
            lines.append(f"******LATERALES 2: {model.v_laterales} KG/M2******")
            lines.append(gl(model.wind_cols['XMAX_CORNER'], 'GX', model.w_lat_x_co, 1))
            lines.append(gl(model.wind_cols['XMAX_INNER'], 'GX', model.w_lat_x_in, 1))
            lines.append(gl(model.wind_cols.get('XMAX_WINDCOL', []), 'GX', model.w_lat_x_in, 1))
        elif wind_type == "Z-":
            lines.append(f"******BARLOVENTO: {model.v_barlovento} KG/M2******")
            lines.append(gl(model.wind_cols['ZMAX_CORNER'], 'GZ', model.w_barl_z_co, -1))
            lines.append(gl(model.wind_cols['ZMAX_INNER'], 'GZ', model.w_barl_z_in, -1))
            lines.append(gl(model.wind_cols.get('ZMAX_WINDCOL', []), 'GZ', model.w_barl_z_in, -1))
            lines.append(f"******SOTAVENTO: {model.v_sotavento} KG/M2******")
            lines.append(gl(model.wind_cols['Z0_CORNER'], 'GZ', model.w_sot_z_co, -1))
            lines.append(gl(model.wind_cols['Z0_INNER'], 'GZ', model.w_sot_z_in, -1))
            lines.append(gl(model.wind_cols.get('Z0_WINDCOL', []), 'GZ', model.w_sot_z_in, -1))
            lines.append(f"******LATERALES 1: {model.v_laterales} KG/M2******")
            lines.append(gl(model.wind_cols['X0_CORNER'], 'GX', model.w_lat_x_co, -1))
            lines.append(gl(model.wind_cols['X0_INNER'], 'GX', model.w_lat_x_in, -1))
            lines.append(gl(model.wind_cols.get('X0_WINDCOL', []), 'GX', model.w_lat_x_in, -1))
            lines.append(f"******LATERALES 2: {model.v_laterales} KG/M2******")
            lines.append(gl(model.wind_cols['XMAX_CORNER'], 'GX', model.w_lat_x_co, 1))
            lines.append(gl(model.wind_cols['XMAX_INNER'], 'GX', model.w_lat_x_in, 1))
            lines.append(gl(model.wind_cols.get('XMAX_WINDCOL', []), 'GX', model.w_lat_x_in, 1))
        
        lines.append(f"**** SUCCIÓN : {model.v_succion} KG/M2 *****")
        lines.append(build_lines(["_LARGUEROS", "UNI", "GY", format_num(model.load_succion)], 72))
        
        return "\n".join([x for x in lines if x])
        
    old_wind_block = "******BARLOVENTO: 86 KG/M2******\n******SOTAVENTO: 50 KG/M2******\n******LATERALES 1: 78 KG/M2******\n******LATERALES 2: 78 KG/M2******\n**** SUCCIÓN : 95 KG/M2 *****"
    
    cargas_text = cargas_text.replace(f"LOAD 7 LOADTYPE None  TITLE VIENTO X+\nMEMBER LOAD\n{old_wind_block}", f"LOAD 7 LOADTYPE None  TITLE VIENTO X+\nMEMBER LOAD\n{wind_block('X+', model)}")
    cargas_text = cargas_text.replace(f"LOAD 8 LOADTYPE None  TITLE VIENTO X-\nMEMBER LOAD\n{old_wind_block}", f"LOAD 8 LOADTYPE None  TITLE VIENTO X-\nMEMBER LOAD\n{wind_block('X-', model)}")
    cargas_text = cargas_text.replace(f"LOAD 9 LOADTYPE None  TITLE VIENTO Z+\nMEMBER LOAD\n{old_wind_block}", f"LOAD 9 LOADTYPE None  TITLE VIENTO Z+\nMEMBER LOAD\n{wind_block('Z+', model)}")
    cargas_text = cargas_text.replace(f"LOAD 10 LOADTYPE None  TITLE VIENTO Z-\nMEMBER LOAD\n{old_wind_block}", f"LOAD 10 LOADTYPE None  TITLE VIENTO Z-\nMEMBER LOAD\n{wind_block('Z-', model)}")

    # Función auxiliar para sismo
    def seismic_block(direction, model):
        col_str = group_ranges(model.groups.get('_COL', []))
        colviento_str = group_ranges(model.groups.get('_COLVIENTO', []))
        lines = []
        
        axis = "X" if "X" in direction else "Z"
        sign = -1 if "-" in direction else 1
        
        # SELFWEIGHT
        all_cols = model.groups.get('_COL', []) + model.groups.get('_COLVIENTO', [])
        all_cols_str = group_ranges(all_cols)
        if all_cols_str:
            lines.append(f"SELFWEIGHT {axis} {format_num(sign * model.seismic_v)} LIST {all_cols_str}")
            
        lines.append("JOINT LOAD")
        
        def joint_load(nodes, load_val):
            rng = group_ranges(nodes)
            if not rng: return ""
            tokens = rng.split(" ") + [f"F{axis}", format_num(sign * load_val)]
            return build_lines(tokens, 72)
            
        lines.append(joint_load(model.seismic_nodes['corner'], model.seismic_loads['corner']))
        lines.append(joint_load(model.seismic_nodes['edge_x'], model.seismic_loads['edge_x']))
        lines.append(joint_load(model.seismic_nodes['edge_z'], model.seismic_loads['edge_z']))
        lines.append(joint_load(model.seismic_nodes['interior'], model.seismic_loads['interior']))
        
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
        out.append("** CELOSIA **")
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

    if armadura_str:
        out.append("** ARMADURAS **")
        out.append(build_lines(["FYLD", "3515", "MEMB"] + armadura_str.split(" "), 72))
        
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
    if armadura_str:
        out.append(build_lines(["CHECK", "CODE", "MEMB"] + armadura_str.split(" "), 72))
    if cv_str:
        out.append(build_lines(["CHECK", "CODE", "MEMB"] + cv_str.split(" "), 72))
    out.append("STEEL TAKE OFF ALL")
    if col_str:
        out.append(build_lines(["STEEL", "TAKE", "OFF", "LIST"] + col_str.split(" "), 72))
    if colviento_str:
        out.append(build_lines(["STEEL", "TAKE", "OFF", "LIST"] + colviento_str.split(" "), 72))
    if armadura_str:
        out.append(build_lines(["STEEL", "TAKE", "OFF", "LIST"] + armadura_str.split(" "), 72))
    if cv_str:
        out.append(build_lines(["STEEL", "TAKE", "OFF", "LIST"] + cv_str.split(" "), 72))

    out.append("FINISH")
    
    return "\n".join(out)
