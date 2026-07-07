import textwrap
import os
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

def build_lines(blocks, max_len=79):
    """
    Groups string blocks into lines, ensuring no line exceeds max_len.
    A block will not be broken across lines.
    """
    lines = []
    current_line = ""
    for block in blocks:
        if not current_line:
            current_line = block
        elif len(current_line) + 1 + len(block) <= max_len:
            current_line += " " + block
        else:
            lines.append(current_line)
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
    
    out.append(build_lines(nodes_blocks, 79))
    
    # ------------------
    # MEMBER INCIDENCES
    # ------------------
    out.append("MEMBER INCIDENCES")
    members_blocks = []
    for mid, (n1, n2) in model.members.items():
        members_blocks.append(f"{mid} {n1} {n2};")
    
    out.append(build_lines(members_blocks, 79))
    
    # ------------------
    # Groups
    # ------------------
    out.append("START GROUP DEFINITION")
    out.append("MEMBER")
    
    # Group names mapping
    group_map = {
        '_COL': model.groups.get('_COL', []),
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
        '_CVH': model.groups.get('_CVH', [])
    }
    
    for name, members in group_map.items():
        if members:
            range_str = group_ranges(members)
            if range_str:
                line = f"{name} {range_str}"
                out.append(build_lines([line], 79))
                
    # ------------------
    # Propiedades (User Tables primero)
    # ------------------
    from templates import USER_TABLES_TEMPLATE, CARGAS_TEMPLATE
    out.append(USER_TABLES_TEMPLATE.strip())
    
    out.append("MEMBER PROPERTY AMERICAN")
    
    col_str = group_ranges(group_map.get('_COL', []))
    larg_str = group_ranges(group_map.get('_LARGUEROS', []))
    cs_str = group_ranges(group_map.get('_CS', []))
    ci_str = group_ranges(group_map.get('_CI', []))
    celosia_str = group_ranges(group_map.get('_CELOSIA', []))
    armadura_str = group_ranges(group_map.get('_ARMADURA', []))
    cv_str = group_ranges(group_map.get('_CVH', []))
    
    if col_str:
        out.append(build_lines(col_str.split(" ") + ["TABLE", "ST", "HSST14X14X0.313"], 79))
    if larg_str:
        out.append("MEMBER PROPERTY SJIJOIST")
        out.append(build_lines(larg_str.split(" ") + ["TABLE", "ST", "16K5"], 79))
        
    if cs_str:
        out.append(build_lines(cs_str.split(" ") + ["UPT", "1", "33"], 79))
    if ci_str:
        out.append(build_lines(ci_str.split(" ") + ["UPT", "1", "33"], 79))
        
    if celosia_str:
        out.append(build_lines(celosia_str.split(" ") + ["UPT", "1", "12"], 79))
        
    if cv_str:
        out.append("MEMBER PROPERTY AMERICAN")
        out.append(build_lines(cv_str.split(" ") + ["TABLE", "ST", "PIPE", "OD", "1.905", "ID", "0"], 79))
        
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
    # Supports
    # ------------------
    if model.base_nodes:
        out.append("SUPPORTS")
        base_str = group_ranges(model.base_nodes)
        support_line = f"{base_str} {model.support_type}"
        out.append(build_lines([support_line], 79))
        
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
            return build_lines(tokens, 79)
            
        lines = []
        if wind_type == "X+":
            lines.append(f"******BARLOVENTO: {model.v_barlovento} KG/M2******")
            lines.append(gl(model.wind_cols['X0_CORNER'], 'GX', model.w_barl_x_co, 1))
            lines.append(gl(model.wind_cols['X0_INNER'], 'GX', model.w_barl_x_in, 1))
            lines.append(f"******SOTAVENTO: {model.v_sotavento} KG/M2******")
            lines.append(gl(model.wind_cols['XMAX_CORNER'], 'GX', model.w_sot_x_co, 1))
            lines.append(gl(model.wind_cols['XMAX_INNER'], 'GX', model.w_sot_x_in, 1))
            lines.append(f"******LATERALES 1: {model.v_laterales} KG/M2******")
            lines.append(gl(model.wind_cols['Z0_CORNER'], 'GZ', model.w_lat_z_co, -1))
            lines.append(gl(model.wind_cols['Z0_INNER'], 'GZ', model.w_lat_z_in, -1))
            lines.append(f"******LATERALES 2: {model.v_laterales} KG/M2******")
            lines.append(gl(model.wind_cols['ZMAX_CORNER'], 'GZ', model.w_lat_z_co, 1))
            lines.append(gl(model.wind_cols['ZMAX_INNER'], 'GZ', model.w_lat_z_in, 1))
        elif wind_type == "X-":
            lines.append(f"******BARLOVENTO: {model.v_barlovento} KG/M2******")
            lines.append(gl(model.wind_cols['XMAX_CORNER'], 'GX', model.w_barl_x_co, -1))
            lines.append(gl(model.wind_cols['XMAX_INNER'], 'GX', model.w_barl_x_in, -1))
            lines.append(f"******SOTAVENTO: {model.v_sotavento} KG/M2******")
            lines.append(gl(model.wind_cols['X0_CORNER'], 'GX', model.w_sot_x_co, -1))
            lines.append(gl(model.wind_cols['X0_INNER'], 'GX', model.w_sot_x_in, -1))
            lines.append(f"******LATERALES 1: {model.v_laterales} KG/M2******")
            lines.append(gl(model.wind_cols['Z0_CORNER'], 'GZ', model.w_lat_z_co, -1))
            lines.append(gl(model.wind_cols['Z0_INNER'], 'GZ', model.w_lat_z_in, -1))
            lines.append(f"******LATERALES 2: {model.v_laterales} KG/M2******")
            lines.append(gl(model.wind_cols['ZMAX_CORNER'], 'GZ', model.w_lat_z_co, 1))
            lines.append(gl(model.wind_cols['ZMAX_INNER'], 'GZ', model.w_lat_z_in, 1))
        elif wind_type == "Z+":
            lines.append(f"******BARLOVENTO: {model.v_barlovento} KG/M2******")
            lines.append(gl(model.wind_cols['Z0_CORNER'], 'GZ', model.w_barl_z_co, 1))
            lines.append(gl(model.wind_cols['Z0_INNER'], 'GZ', model.w_barl_z_in, 1))
            lines.append(f"******SOTAVENTO: {model.v_sotavento} KG/M2******")
            lines.append(gl(model.wind_cols['ZMAX_CORNER'], 'GZ', model.w_sot_z_co, 1))
            lines.append(gl(model.wind_cols['ZMAX_INNER'], 'GZ', model.w_sot_z_in, 1))
            lines.append(f"******LATERALES 1: {model.v_laterales} KG/M2******")
            lines.append(gl(model.wind_cols['X0_CORNER'], 'GX', model.w_lat_x_co, -1))
            lines.append(gl(model.wind_cols['X0_INNER'], 'GX', model.w_lat_x_in, -1))
            lines.append(f"******LATERALES 2: {model.v_laterales} KG/M2******")
            lines.append(gl(model.wind_cols['XMAX_CORNER'], 'GX', model.w_lat_x_co, 1))
            lines.append(gl(model.wind_cols['XMAX_INNER'], 'GX', model.w_lat_x_in, 1))
        elif wind_type == "Z-":
            lines.append(f"******BARLOVENTO: {model.v_barlovento} KG/M2******")
            lines.append(gl(model.wind_cols['ZMAX_CORNER'], 'GZ', model.w_barl_z_co, -1))
            lines.append(gl(model.wind_cols['ZMAX_INNER'], 'GZ', model.w_barl_z_in, -1))
            lines.append(f"******SOTAVENTO: {model.v_sotavento} KG/M2******")
            lines.append(gl(model.wind_cols['Z0_CORNER'], 'GZ', model.w_sot_z_co, -1))
            lines.append(gl(model.wind_cols['Z0_INNER'], 'GZ', model.w_sot_z_in, -1))
            lines.append(f"******LATERALES 1: {model.v_laterales} KG/M2******")
            lines.append(gl(model.wind_cols['X0_CORNER'], 'GX', model.w_lat_x_co, -1))
            lines.append(gl(model.wind_cols['X0_INNER'], 'GX', model.w_lat_x_in, -1))
            lines.append(f"******LATERALES 2: {model.v_laterales} KG/M2******")
            lines.append(gl(model.wind_cols['XMAX_CORNER'], 'GX', model.w_lat_x_co, 1))
            lines.append(gl(model.wind_cols['XMAX_INNER'], 'GX', model.w_lat_x_in, 1))
        
        lines.append(f"**** SUCCIÓN : {model.v_succion} KG/M2 *****")
        lines.append(build_lines(["_LARGUEROS", "UNI", "GY", format_num(model.load_succion)], 79))
        
        return "\n".join([x for x in lines if x])
        
    old_wind_block = "******BARLOVENTO: 86 KG/M2******\n******SOTAVENTO: 50 KG/M2******\n******LATERALES 1: 78 KG/M2******\n******LATERALES 2: 78 KG/M2******\n**** SUCCIÓN : 95 KG/M2 *****"
    
    cargas_text = cargas_text.replace(f"LOAD 7 LOADTYPE None  TITLE VIENTO X+\nMEMBER LOAD\n{old_wind_block}", f"LOAD 7 LOADTYPE None  TITLE VIENTO X+\nMEMBER LOAD\n{wind_block('X+', model)}")
    cargas_text = cargas_text.replace(f"LOAD 8 LOADTYPE None  TITLE VIENTO X-\nMEMBER LOAD\n{old_wind_block}", f"LOAD 8 LOADTYPE None  TITLE VIENTO X-\nMEMBER LOAD\n{wind_block('X-', model)}")
    cargas_text = cargas_text.replace(f"LOAD 9 LOADTYPE None  TITLE VIENTO Z+\nMEMBER LOAD\n{old_wind_block}", f"LOAD 9 LOADTYPE None  TITLE VIENTO Z+\nMEMBER LOAD\n{wind_block('Z+', model)}")
    cargas_text = cargas_text.replace(f"LOAD 10 LOADTYPE None  TITLE VIENTO Z-\nMEMBER LOAD\n{old_wind_block}", f"LOAD 10 LOADTYPE None  TITLE VIENTO Z-\nMEMBER LOAD\n{wind_block('Z-', model)}")

    
    # Cambiar el tipo de carga sismica a Seismic-H según petición
    cargas_text = cargas_text.replace("LOADTYPE Seismic", "LOADTYPE Seismic-H")
    
    # Parámetros de Diseño Análisis 1
    fyld_celosia = build_lines(["FYLD", "3515", "MEMB"] + celosia_str.split(" "), 79)
    select_celosia = build_lines(["SELECT", "MEMB"] + celosia_str.split(" "), 79)
    
    cargas_text = cargas_text.replace("FYLD 3520 MEMB 1", fyld_celosia)
    cargas_text = cargas_text.replace("SELECT MEMB 1", select_celosia)
    
    # Parámetros de Diseño Análisis 2
    # El archivo termina en "CODE AISC", así que lo anexamos al final
    cargas_text = cargas_text.strip()
    if cargas_text.endswith("CODE AISC"):
        fyld_cols = build_lines(["FYLD", "3200", "MEMB"] + col_str.split(" "), 79)
        fyld_arm = build_lines(["FYLD", "3515", "MEMB"] + armadura_str.split(" "), 79)
        cargas_text += f"\n{fyld_cols}\n{fyld_arm}\n"
        
        if cv_str:
            tmain_cv = build_lines(["TMAIN", "10000", "MEMB"] + cv_str.split(" "), 79)
            main_cv = build_lines(["MAIN", "10000", "MEMB"] + cv_str.split(" "), 79)
            fyld_cv = build_lines(["FYLD", "2530", "MEMB"] + cv_str.split(" "), 79)
            cargas_text += f"{tmain_cv}\n{main_cv}\n{fyld_cv}\n"
            
        # Build check code commands to avoid >79 chars
        cc_cols = build_lines(["CHECK", "CODE", "MEMB"] + col_str.split(" "), 79)
        cc_arm = build_lines(["CHECK", "CODE", "MEMB"] + armadura_str.split(" "), 79)
        cargas_text += f"{cc_cols}\n{cc_arm}\n"
        
        if cv_str:
            cc_cv = build_lines(["CHECK", "CODE", "MEMB"] + cv_str.split(" "), 79)
            cargas_text += f"{cc_cv}\n"
    
    out.append(cargas_text.strip())

    out.append("FINISH")
    
    return "\n".join(out)
