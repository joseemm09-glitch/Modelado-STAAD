import math
from perfiles_w import PERFILES_W

def generar_base_datos_or():
    perfiles = []
    # Tamaños B en pulgadas y espesores en fracciones de pulgada
    tamanos = [6, 8, 10, 12, 14, 16, 18, 20, 22, 24]
    espesores = [
        ("3/16", 0.1875), ("1/4", 0.25), ("5/16", 0.3125),
        ("3/8", 0.375), ("1/2", 0.5), ("5/8", 0.625),
        ("3/4", 0.75), ("7/8", 0.875), ("1", 1.0)
    ]
    
    for B in tamanos:
        for t_name, t_in in espesores:
            if t_in > B / 10.0 and B > 10: # Limitar espesores irreales
                pass
            B_cm = B * 2.54
            t_cm = t_in * 2.54
            
            # Aproximación de propiedades para tubo cuadrado (ignorando radios de curvatura para el pre-diseño)
            b_int = B_cm - 2 * t_cm
            
            # Área (cm2)
            A = (B_cm**2) - (b_int**2)
            
            if A <= 0:
                continue
                
            # Momento de Inercia Ix = Iy (cm4)
            Ix = (B_cm**4 - b_int**4) / 12.0
            
            # Módulo de sección elástico Sx (cm3)
            Sx = Ix / (B_cm / 2.0)
            
            # Peso lineal (kg/m) - Densidad acero 7850 kg/m3 = 0.00785 kg/cm3
            peso = A * 100 * 0.00785
            
            nombre = f"OR {B}\"x{B}\"x{t_name}\""
            t_str = f"{t_in:.3f}".rstrip('0').rstrip('.') if '.' in f"{t_in:.3f}" else str(t_in)
            nombre_staad = f"HSST{B}X{B}X{t_str}"
            
            # Radio de giro (cm)
            r = math.sqrt(Ix / A)
            
            perfiles.append({
                "nombre": nombre,
                "nombre_staad": nombre_staad,
                "A": A,
                "Ix": Ix,
                "Sx": Sx,
                "r": r,
                "peso": peso,
                "B": B,
                "t": t_in
            })
            
    # Ordenar por peso
    return sorted(perfiles, key=lambda x: x["peso"])

def cargar_base_datos_excel():
    perfiles = [
        {'nombre': 'HSS4X4X1/8', 'nombre_staad': 'HSST4X4X0.125', 'A': 11.42, 'Ix': 183.14, 'Sx': 36.05, 'r': 4.0, 'peso': 8.96},
        {'nombre': 'HSS4X4X3/16', 'nombre_staad': 'HSST4X4X0.188', 'A': 16.65, 'Ix': 258.48, 'Sx': 50.88, 'r': 3.94, 'peso': 13.07},
        {'nombre': 'HSS6X6X1/8', 'nombre_staad': 'HSST6X6X0.125', 'A': 17.42, 'Ix': 645.16, 'Sx': 84.67, 'r': 6.09, 'peso': 13.67},
        {'nombre': 'HSS4X4X1/4', 'nombre_staad': 'HSST4X4X0.25', 'A': 21.74, 'Ix': 324.66, 'Sx': 63.91, 'r': 3.86, 'peso': 17.07},
        {'nombre': 'HSS8X8X1/8', 'nombre_staad': 'HSST8X8X0.125', 'A': 23.35, 'Ix': 1556.71, 'Sx': 153.22, 'r': 8.16, 'peso': 18.33},
        {'nombre': 'HSS6X6X3/16', 'nombre_staad': 'HSST6X6X0.188', 'A': 25.68, 'Ix': 928.2, 'Sx': 121.81, 'r': 6.01, 'peso': 20.16},
        {'nombre': 'HSS4X4X5/16', 'nombre_staad': 'HSST4X4X0.313', 'A': 26.45, 'Ix': 380.44, 'Sx': 74.89, 'r': 3.79, 'peso': 20.76},
        {'nombre': 'HSS4X4X3/8', 'nombre_staad': 'HSST4X4X0.375', 'A': 30.84, 'Ix': 428.72, 'Sx': 84.39, 'r': 3.73, 'peso': 24.21},
        {'nombre': 'HSS6X6X1/4', 'nombre_staad': 'HSST6X6X0.25', 'A': 33.81, 'Ix': 1190.42, 'Sx': 156.22, 'r': 5.93, 'peso': 26.54},
        {'nombre': 'HSS8X8X3/16', 'nombre_staad': 'HSST8X8X0.188', 'A': 34.65, 'Ix': 2264.3, 'Sx': 222.86, 'r': 8.08, 'peso': 27.2},
        {'nombre': 'HSS4X4X1/2', 'nombre_staad': 'HSST4X4X0.5', 'A': 38.84, 'Ix': 495.32, 'Sx': 97.5, 'r': 3.57, 'peso': 30.49},
        {'nombre': 'HSS6X6X5/16', 'nombre_staad': 'HSST6X6X0.313', 'A': 41.48, 'Ix': 1427.67, 'Sx': 187.36, 'r': 5.87, 'peso': 32.56},
        {'nombre': 'HSS10X10X3/16', 'nombre_staad': 'HSST10X10X0.188', 'A': 43.61, 'Ix': 4495.3, 'Sx': 353.96, 'r': 10.15, 'peso': 34.24},
        {'nombre': 'HSS8X8X1/4', 'nombre_staad': 'HSST8X8X0.25', 'A': 45.81, 'Ix': 2942.76, 'Sx': 289.64, 'r': 8.02, 'peso': 35.96},
        {'nombre': 'HSS6X6X3/8', 'nombre_staad': 'HSST6X6X0.375', 'A': 48.9, 'Ix': 1644.11, 'Sx': 215.76, 'r': 5.8, 'peso': 38.39},
        {'nombre': 'HSS12X12X3/16', 'nombre_staad': 'HSST12X12X0.188', 'A': 52.58, 'Ix': 7866.77, 'Sx': 516.19, 'r': 12.23, 'peso': 41.28},
        {'nombre': 'HSS8X8X5/16', 'nombre_staad': 'HSST8X8X0.313', 'A': 56.52, 'Ix': 3562.94, 'Sx': 350.68, 'r': 7.94, 'peso': 44.37},
        {'nombre': 'HSS10X10X1/4', 'nombre_staad': 'HSST10X10X0.25', 'A': 57.81, 'Ix': 5868.86, 'Sx': 462.12, 'r': 10.08, 'peso': 45.38},
        {'nombre': 'HSS6X6X1/2', 'nombre_staad': 'HSST6X6X0.5', 'A': 62.84, 'Ix': 2010.4, 'Sx': 263.83, 'r': 5.66, 'peso': 49.33},
        {'nombre': 'HSS8X8X3/8', 'nombre_staad': 'HSST8X8X0.375', 'A': 67.1, 'Ix': 4162.31, 'Sx': 409.68, 'r': 7.88, 'peso': 52.67},
        {'nombre': 'HSS12X12X1/4', 'nombre_staad': 'HSST12X12X0.25', 'A': 69.68, 'Ix': 10322.54, 'Sx': 677.33, 'r': 12.17, 'peso': 54.7},
        {'nombre': 'HSS10X10X5/16', 'nombre_staad': 'HSST10X10X0.313', 'A': 71.61, 'Ix': 7159.18, 'Sx': 563.72, 'r': 10.0, 'peso': 56.22},
        {'nombre': 'HSS6X6X5/8', 'nombre_staad': 'HSST6X6X0.625', 'A': 75.48, 'Ix': 2297.6, 'Sx': 301.52, 'r': 5.52, 'peso': 59.25},
        {'nombre': 'HSS10X10X3/8', 'nombre_staad': 'HSST10X10X0.375', 'A': 85.16, 'Ix': 8407.87, 'Sx': 662.04, 'r': 9.94, 'peso': 66.85},
        {'nombre': 'HSS12X12X5/16', 'nombre_staad': 'HSST12X12X0.313', 'A': 86.45, 'Ix': 12653.44, 'Sx': 830.28, 'r': 12.1, 'peso': 67.86},
        {'nombre': 'HSS8X8X1/2', 'nombre_staad': 'HSST8X8X0.5', 'A': 87.1, 'Ix': 5202.89, 'Sx': 512.1, 'r': 7.73, 'peso': 68.37},
        {'nombre': 'HSS14X14X5/16', 'nombre_staad': 'HSST14X14X0.313', 'A': 101.29, 'Ix': 20395.34, 'Sx': 1147.09, 'r': 14.19, 'peso': 79.51},
        {'nombre': 'HSS12X12X3/8', 'nombre_staad': 'HSST12X12X0.375', 'A': 103.23, 'Ix': 14859.46, 'Sx': 975.03, 'r': 12.0, 'peso': 81.03},
        {'nombre': 'HSS8X8X5/8', 'nombre_staad': 'HSST8X8X0.625', 'A': 105.81, 'Ix': 6076.98, 'Sx': 598.13, 'r': 7.58, 'peso': 83.06},
        {'nombre': 'HSS10X10X1/2', 'nombre_staad': 'HSST10X10X0.5', 'A': 110.97, 'Ix': 10655.52, 'Sx': 839.02, 'r': 9.8, 'peso': 87.11},
        {'nombre': 'HSS16X16X5/16', 'nombre_staad': 'HSST16X16X0.313', 'A': 116.77, 'Ix': 30759.5, 'Sx': 1513.76, 'r': 16.23, 'peso': 91.67},
        {'nombre': 'HSS14X14X3/8', 'nombre_staad': 'HSST14X14X0.375', 'A': 120.64, 'Ix': 24016.55, 'Sx': 1350.76, 'r': 14.11, 'peso': 94.71},
        {'nombre': 'HSS12X12X1/2', 'nombre_staad': 'HSST12X12X0.5', 'A': 134.84, 'Ix': 19021.78, 'Sx': 1248.15, 'r': 11.88, 'peso': 105.85},
        {'nombre': 'HSS10X10X5/8', 'nombre_staad': 'HSST10X10X0.625', 'A': 135.48, 'Ix': 12653.44, 'Sx': 996.33, 'r': 9.66, 'peso': 106.35},
        {'nombre': 'HSS16X16X3/8', 'nombre_staad': 'HSST16X16X0.375', 'A': 138.71, 'Ix': 36337.0, 'Sx': 1788.24, 'r': 16.19, 'peso': 108.89},
        {'nombre': 'HSS14X14X1/2', 'nombre_staad': 'HSST14X14X0.5', 'A': 158.71, 'Ix': 30925.99, 'Sx': 1739.37, 'r': 13.96, 'peso': 124.59},
        {'nombre': 'HSS10X10X3/4', 'nombre_staad': 'HSST10X10X0.75', 'A': 159.35, 'Ix': 14443.23, 'Sx': 1137.26, 'r': 9.52, 'peso': 125.09},
        {'nombre': 'HSS12X12X5/8', 'nombre_staad': 'HSST12X12X0.625', 'A': 165.81, 'Ix': 22809.48, 'Sx': 1496.69, 'r': 11.73, 'peso': 130.16},
        {'nombre': 'HSS16X16X1/2', 'nombre_staad': 'HSST16X16X0.5', 'A': 182.58, 'Ix': 47034.15, 'Sx': 2314.67, 'r': 16.05, 'peso': 143.33},
        {'nombre': 'HSS14X14X5/8', 'nombre_staad': 'HSST14X14X0.625', 'A': 195.48, 'Ix': 37335.96, 'Sx': 2099.89, 'r': 13.82, 'peso': 153.45},
        {'nombre': 'HSS12X12X3/4', 'nombre_staad': 'HSST12X12X0.75', 'A': 195.48, 'Ix': 26264.2, 'Sx': 1723.37, 'r': 11.59, 'peso': 153.45},
        {'nombre': 'HSS18X18X1/2', 'nombre_staad': 'HSST18X18X0.5', 'A': 207.1, 'Ix': 67845.72, 'Sx': 2967.88, 'r': 18.1, 'peso': 162.57},
        {'nombre': 'HSS16X16X5/8', 'nombre_staad': 'HSST16X16X0.625', 'A': 225.81, 'Ix': 57023.71, 'Sx': 2806.28, 'r': 15.89, 'peso': 177.26},
        {'nombre': 'HSS20X20X1/2', 'nombre_staad': 'HSST20X20X0.5', 'A': 230.97, 'Ix': 94068.3, 'Sx': 3703.48, 'r': 20.18, 'peso': 181.31},
        {'nombre': 'HSS14X14X3/4', 'nombre_staad': 'HSST14X14X0.75', 'A': 231.61, 'Ix': 43288.07, 'Sx': 2434.65, 'r': 13.67, 'peso': 181.82},
        {'nombre': 'HSS18X18X5/8', 'nombre_staad': 'HSST18X18X0.625', 'A': 255.48, 'Ix': 82413.82, 'Sx': 3605.15, 'r': 17.96, 'peso': 200.55},
        {'nombre': 'HSS14X14X7/8', 'nombre_staad': 'HSST14X14X0.875', 'A': 265.81, 'Ix': 48699.08, 'Sx': 2738.98, 'r': 13.54, 'peso': 208.66},
        {'nombre': 'HSS16X16X3/4', 'nombre_staad': 'HSST16X16X0.75', 'A': 267.74, 'Ix': 66180.8, 'Sx': 3256.93, 'r': 15.72, 'peso': 210.18},
        {'nombre': 'HSS20X20X5/8', 'nombre_staad': 'HSST20X20X0.625', 'A': 285.81, 'Ix': 114463.64, 'Sx': 4506.44, 'r': 20.01, 'peso': 224.36},
        {'nombre': 'HSS18X18X3/4', 'nombre_staad': 'HSST18X18X0.75', 'A': 303.87, 'Ix': 96565.69, 'Sx': 4224.22, 'r': 17.83, 'peso': 238.54},
        {'nombre': 'HSS16X16X7/8', 'nombre_staad': 'HSST16X16X0.875', 'A': 307.74, 'Ix': 74921.66, 'Sx': 3687.09, 'r': 15.6, 'peso': 241.58},
        {'nombre': 'HSS20X20X3/4', 'nombre_staad': 'HSST20X20X0.75', 'A': 339.35, 'Ix': 134442.75, 'Sx': 5293.02, 'r': 19.9, 'peso': 266.39},
        {'nombre': 'HSS18X18X7/8', 'nombre_staad': 'HSST18X18X0.875', 'A': 350.32, 'Ix': 109468.86, 'Sx': 4788.66, 'r': 17.68, 'peso': 275.0},
        {'nombre': 'HSS22X22X3/4', 'nombre_staad': 'HSST22X22X0.75', 'A': 375.48, 'Ix': 181060.67, 'Sx': 6480.34, 'r': 21.96, 'peso': 294.75},
        {'nombre': 'HSS20X20X7/8', 'nombre_staad': 'HSST20X20X0.875', 'A': 392.26, 'Ix': 152756.93, 'Sx': 6014.05, 'r': 19.73, 'peso': 307.92},
        {'nombre': 'HSS22X22X7/8', 'nombre_staad': 'HSST22X22X0.875', 'A': 434.19, 'Ix': 206867.02, 'Sx': 7403.97, 'r': 21.83, 'peso': 340.84},
    ]
    return perfiles

def clasificar_columnas(model):
    """
    Clasifica las columnas principales en C-1, C-2, C-3 y C-4, y de viento en CV-1.
    Devuelve un diccionario { "C-1": [ids], "C-2": [ids], ... }
    """
    grupos = {"C-1": [], "C-2": [], "C-3": [], "C-4": [], "CV-1": []}
    
    # Identificar límites del modelo
    xs = [coord[0] for coord in model.nodes.values()]
    zs = [coord[2] for coord in model.nodes.values()]
    
    if not xs or not zs:
        return grupos
        
    x_min, x_max = min(xs), max(xs)
    z_min, z_max = min(zs), max(zs)
    
    tol = 0.1
    
    is_tilt_up = getattr(model, 'wall_type', '') == "Tilt-Up"
    
    if is_tilt_up:
        # Extraer coordenadas X de las bahías de extensión
        x_ext = []
        if getattr(model, 'ext_bays_active', False):
            if getattr(model, 'ext_bl', False) or getattr(model, 'ext_tl', False):
                x_ext.append(round(model.get_x(0), 2))
            if getattr(model, 'ext_br', False) or getattr(model, 'ext_tr', False):
                x_ext.append(round(model.get_x(model.nSpan), 2))
                
        # Agrupar columnas por coordenada X
        x_groups = {}
        for mem_id in model.groups.get('_COL', []):
            n1, n2 = model.members[mem_id]
            x, y, z = model.nodes[n1]
            rx = round(x, 2)
            if rx not in x_groups: x_groups[rx] = []
            x_groups[rx].append(mem_id)
            
        x_main_keys = [rx for rx in x_groups.keys() if rx not in x_ext]
        
        grupos_tiltup = {}
        group_num = 1
        
        if x_main_keys:
            x_center = (max(x_main_keys) + min(x_main_keys)) / 2.0
            
            # Agrupar las de main por distancia al centro
            dist_groups = {}
            for rx in x_main_keys:
                d = round(abs(rx - x_center), 2)
                if d not in dist_groups: dist_groups[d] = []
                dist_groups[d].extend(x_groups[rx])
                
            sorted_dists = sorted(dist_groups.keys())
            
            # C-1: Centrales
            grupos_tiltup[f"C-{group_num}"] = dist_groups[sorted_dists[0]]
            group_num += 1
            
            # C-2: Intermedias (si hay, agrupar TODAS las distancias intermedias)
            if len(sorted_dists) > 2:
                mid_cols = []
                for d in sorted_dists[1:-1]:
                    mid_cols.extend(dist_groups[d])
                grupos_tiltup[f"C-{group_num}"] = mid_cols
                group_num += 1
                
            # Últimos ejes completos (si son distintos de los centrales)
            if len(sorted_dists) > 1:
                grupos_tiltup[f"C-{group_num}"] = dist_groups[sorted_dists[-1]]
                group_num += 1
                
        # Bahías de extensión
        ext_cols = []
        for rx in x_ext:
            if rx in x_groups:
                ext_cols.extend(x_groups[rx])
        
        if ext_cols:
            grupos_tiltup[f"C-{group_num}"] = ext_cols
            
        cv_cols = model.groups.get('_COLVIENTO', [])
        if cv_cols:
            grupos_tiltup["CV-1"] = cv_cols
            
        return grupos_tiltup

    # Lógica normal para naves metálicas
    for mem_id in model.groups.get('_COL', []):
        n1, n2 = model.members[mem_id]
        x, y, z = model.nodes[n1]
        
        is_x_edge = abs(x - x_min) < tol or abs(x - x_max) < tol
        is_z_edge = abs(z - z_min) < tol or abs(z - z_max) < tol
        
        if is_x_edge and is_z_edge:
            grupos["C-4"].append(mem_id)
        elif is_x_edge and not is_z_edge:
            grupos["C-3"].append(mem_id)
        elif not is_x_edge and is_z_edge:
            grupos["C-2"].append(mem_id)
        else:
            grupos["C-1"].append(mem_id)
            
    for mem_id in model.groups.get('_COLVIENTO', []):
        grupos["CV-1"].append(mem_id)
            
    return {k: v for k, v in grupos.items() if len(v) > 0}

def predisenar_grupo(nombre_grupo, model, usar_2w=False):
    """
    Realiza el pre-diseño de un grupo de columnas basado en las cargas y geometría.
    Retorna una lista con los 5 mejores perfiles que cumplen.
    """
    is_wind_col = "CV" in nombre_grupo
    perfiles_base = PERFILES_W if is_wind_col else generar_base_datos_or()
    
    if is_wind_col and not usar_2w:
        perfiles = [p for p in perfiles_base if not p["nombre"].startswith("WD")]
    else:
        perfiles = perfiles_base
        
    # Heurística rápida para Muros Tilt-Up (Aproximación inicial solicitada)
    if getattr(model, 'wall_type', '') == "Tilt-Up" and nombre_grupo.startswith("C-"):
        try:
            g_idx = int(nombre_grupo.split("-")[1])
        except:
            g_idx = 1
            
        if g_idx == 1:
            target_name = "OR 14\"x14\"x3/8\""
            alternatives = ["OR 14\"x14\"x1/2\"", "OR 16\"x16\"x5/16\"", "OR 16\"x16\"x3/8\"", "OR 14\"x14\"x5/16\""]
        elif g_idx == 2:
            target_name = "OR 12\"x12\"x3/8\""
            alternatives = ["OR 12\"x12\"x1/2\"", "OR 14\"x14\"x5/16\"", "OR 14\"x14\"x1/4\"", "OR 12\"x12\"x5/16\""]
        elif g_idx == 3:
            target_name = "OR 10\"x10\"x5/16\""
            alternatives = ["OR 10\"x10\"x3/8\"", "OR 12\"x12\"x1/4\"", "OR 12\"x12\"x5/16\"", "OR 10\"x10\"x1/4\""]
        else:
            target_name = "OR 8\"x8\"x1/4\""
            alternatives = ["OR 8\"x8\"x5/16\"", "OR 10\"x10\"x3/16\"", "OR 10\"x10\"x1/4\"", "OR 8\"x8\"x3/16\""]
            
        resultados_tiltup = []
        for p in perfiles:
            if p["nombre"] == target_name:
                resultados_tiltup.append({"perfil": p, "ratio": 0.80})
                break
        for alt in alternatives:
            for p in perfiles:
                if p["nombre"] == alt:
                    resultados_tiltup.append({"perfil": p, "ratio": 0.85})
                    break
        if resultados_tiltup:
            return resultados_tiltup

    # Extraer parámetros del modelo
    L_span = model.Larm_m
    L_bay = model.Ljoist_m
    H = model.HLibre_m
    CM = model.c_muerta
    CV = model.c_viva
    
    # Viento máximo
    viento = max(model.v_barlovento, model.v_sotavento, model.v_laterales)
    
    # Asignar áreas tributarias y anchos tributarios de viento
    add_wind = getattr(model, 'add_wind_cols', False)
    w_dist = getattr(model, 'max_wind_dist', 8.0)
    s_front = min(L_span, w_dist) if add_wind else L_span
    s_lat = min(L_bay, w_dist) if add_wind else L_bay
    
    if "CV" in nombre_grupo:
        At_vert = 0.0 # Las columnas de viento solo cargan su peso propio y viento
        L_trib_viento = w_dist
    elif "C-4" in nombre_grupo:
        At_vert = (L_span / 2.0) * (L_bay / 2.0)
        L_trib_viento = max(s_front / 2.0, s_lat / 2.0)
    elif "C-3" in nombre_grupo:
        At_vert = (L_span / 2.0) * L_bay
        L_trib_viento = s_lat
    elif "C-2" in nombre_grupo:
        At_vert = L_span * (L_bay / 2.0)
        L_trib_viento = s_front
    else: # C-1
        At_vert = L_span * L_bay
        L_trib_viento = 0.0 # Interiores no reciben viento directo de fachada
        
    # Peso propio estructural estimado (joists, armaduras, lámina, etc.)
    PP_est = 35.0 # kg/m2
    
    # Fuerzas estimadas (Axial)
    P_kg = At_vert * (CM + CV + PP_est)
    
    # Momentos estimados (método aproximado)
    if "CV" in nombre_grupo:
        # Columna de viento (simplemente apoyada)
        M_viento_kg_m = (viento * L_trib_viento * H**2) / 8.0
    else:
        # Marco Principal - Efecto de Desplazamiento Lateral (Sway)
        # Los marcos en los extremos (C-3, C-4) reciben la mitad de carga tributaria de viento
        is_end_frame = "C-3" in nombre_grupo or "C-4" in nombre_grupo
        V_marco_x = viento * H * (L_bay / 2.0 if is_end_frame else L_bay)
        
        n_cols = model.nSpan + 1
        V_col = V_marco_x / n_cols
        
        is_pinned = getattr(model, 'support_type', 'FIXED') == "PINNED"
        # Si está articulado en base, el momento es mayor (V*H). Si está empotrado, se reparte (V*H/2 o menos)
        M_sway = V_col * H if is_pinned else V_col * (H / 2.0)
        
        # Efecto de viento local en fachada (para perimetrales)
        M_local = (viento * L_trib_viento * H**2) / 8.0
        
        # Excentricidad mínima accidental (5 cm)
        M_grav = P_kg * 0.05
        
        M_viento_kg_m = max(M_sway, M_local) + M_grav
        
    M_viento_kg_cm = M_viento_kg_m * 100.0
    
    # Esfuerzo de fluencia del acero (Fy) en kg/cm2
    # Usualmente A500 Gr. B es ~3230 kg/cm2 (46 ksi) para HSS
    # Para perfiles W (A992) es ~3515 kg/cm2 (50 ksi)
    Fy = 3515.0 if "CV" in nombre_grupo else 3230.0
    
    E = 2039000.0 # Módulo de elasticidad kg/cm2
    Cc = math.sqrt(2 * math.pi**2 * E / Fy)
    # Longitud efectiva (K) para igualar a los parámetros KZ de STAAD
    K_val = 1.7 # Para columnas principales
    if "CV" in nombre_grupo:
        K_val = 1.4 # Para columnas de viento
            
    KL = K_val * H * 100.0 # Altura efectiva en cm
    
    resultados = []
    
    for perfil in perfiles:
        A = perfil.get("area", perfil.get("A"))
        Sx = perfil["Sx"]
        # Tomar el radio de giro menor (min(rx, ry)) para la revisión de esbeltez general
        r = min(perfil.get("rx", 5.0), perfil.get("ry", 5.0))
        
        # Revisión de esbeltez (ahora usamos la longitud total para viento también)
        klr = KL / r
            
        if klr > 195:
            continue # Se descarta por esbeltez excesiva
            
        # Esfuerzos actuantes
        fa = P_kg / A if A > 0 else 0
        fb = M_viento_kg_cm / Sx if Sx > 0 else 0
        
        # Esfuerzos permisibles (AISC ASD)
        Fb_adm = 0.6 * Fy
        
        if klr < Cc:
            FS = (5.0/3.0) + (3.0 * klr)/(8.0 * Cc) - (klr**3)/(8.0 * Cc**3)
            Fa_adm = (1.0 - (klr**2)/(2.0 * Cc**2)) * Fy / FS
        else:
            Fa_adm = (12.0 * math.pi**2 * E) / (23.0 * klr**2)
            
        if Fa_adm <= 0: continue
        
        # Ratio de interacción
        ratio = (fa / Fa_adm) + (fb / Fb_adm)
        
        if 0.6 <= ratio <= 0.95:
            resultados.append({
                "perfil": perfil,
                "ratio": ratio
            })
            
    # Si no hay resultados (cargas muy altas o muy bajas), relajar el límite
    if len(resultados) < 5:
        for perfil in perfiles:
            A = perfil.get("area", perfil.get("A"))
            Sx = perfil["Sx"]
            r = min(perfil.get("rx", 5.0), perfil.get("ry", 5.0))
            
            klr = KL / r
                
            if klr > 195: continue
                
            fa = P_kg / A if A > 0 else 0
            fb = M_viento_kg_cm / Sx if Sx > 0 else 0
            
            Fb_adm = 0.6 * Fy
            if klr < Cc:
                FS = (5.0/3.0) + (3.0 * klr)/(8.0 * Cc) - (klr**3)/(8.0 * Cc**3)
                Fa_adm = (1.0 - (klr**2)/(2.0 * Cc**2)) * Fy / FS
            else:
                Fa_adm = (12.0 * math.pi**2 * E) / (23.0 * klr**2)
                
            ratio = (fa / Fa_adm) + (fb / Fb_adm)
            if 0.2 <= ratio <= 1.5:
                resultados.append({"perfil": perfil, "ratio": ratio})
                
    # Ordenar resultados para acercarse lo más posible a ratio 0.8
    resultados.sort(key=lambda x: abs(0.8 - x["ratio"]))
    
    # Evitar duplicados si relajamos el límite
    vistos = set()
    top_5 = []
    for r in resultados:
        if r["perfil"]["nombre"] not in vistos:
            vistos.add(r["perfil"]["nombre"])
            top_5.append(r)
        if len(top_5) == 5:
            break
            
    # Ordenar los top 5 finales por peso (de más ligero a más pesado)
    top_5.sort(key=lambda x: x["perfil"]["peso"])
    
    # Si aún no hay nada (muy raro), devolver los 5 más pesados
    if not top_5:
        return [{"perfil": p, "ratio": 0.0} for p in perfiles[-5:]]
        
    return top_5

def optimizar_perfil(nombre_actual, ratio_actual, es_w=False, ratio_objetivo=0.95):
    """
    Propone un nuevo perfil (W u OR) calculando una Inercia objetivo.
    Busca en la base de datos el perfil más ligero cuya Inercia sea >= Inercia objetivo.
    Si ratio_actual > 1.0, sube el perfil. Si es < 0.85, lo baja. (O lo acerca a 0.95 en ambos casos).
    """
    if ratio_actual <= 0:
        return nombre_actual # No data
        
    db_or = cargar_base_datos_excel()
    db_w = PERFILES_W
    
    # Identify current profile
    perfil_actual = None
    db_activa = db_w if es_w else db_or
    
    for p in db_activa:
        if p['nombre'] == nombre_actual or p.get('nombre_staad', '') == nombre_actual:
            perfil_actual = p
            break
            
    if not perfil_actual:
        return nombre_actual
        
    # Calculate current Inertia
    if es_w:
        # W profiles typically don't have Ix explicitly in the dict we defined, 
        # but we have area and rx, so Ix = area * rx^2
        ix_actual = perfil_actual['area'] * (perfil_actual['rx'] ** 2)
    else:
        ix_actual = perfil_actual.get('Ix', 0)
        
    if ix_actual <= 0:
        return nombre_actual
        
    # Target Inertia
    ix_target = ix_actual * (ratio_actual / ratio_objetivo)
    
    # Find valid profiles
    validos = []
    for p in db_activa:
        if es_w:
            ix_p = p['area'] * (p['rx'] ** 2)
        else:
            ix_p = p.get('Ix', 0)
            
        # We want Ix >= ix_target
        if ix_p >= ix_target:
            validos.append((p, ix_p))
            
    if not validos:
        # If no profile satisfies the condition (e.g. required too large), return the largest available
        if es_w:
            mayor = max(db_w, key=lambda x: x['area'] * (x['rx'] ** 2))
        else:
            mayor = max(db_or, key=lambda x: x.get('Ix', 0))
        return mayor['nombre']
        
    # Sort valid profiles by weight (lightest first)
    validos.sort(key=lambda x: x[0]['peso'])
    
    mejor = validos[0][0]
    return mejor['nombre']
