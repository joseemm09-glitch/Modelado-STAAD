import math

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

def generar_base_datos_w():
    # Perfiles IPR (W) comunes para columnas de viento
    # Propiedades aproximadas: A en cm2, Sx en cm3, peso en kg/m, r en cm (radio de giro menor)
    perfiles = [
        {"nombre": "W 8x10", "nombre_staad": "W8X10", "A": 19.1, "Sx": 128, "r": 2.13, "peso": 15.0},
        {"nombre": "W 8x13", "nombre_staad": "W8X13", "A": 25.0, "Sx": 162, "r": 3.20, "peso": 19.3},
        {"nombre": "W 8x18", "nombre_staad": "W8X18", "A": 34.0, "Sx": 249, "r": 3.12, "peso": 26.8},
        {"nombre": "W 10x12", "nombre_staad": "W10X12", "A": 22.8, "Sx": 178, "r": 2.28, "peso": 17.9},
        {"nombre": "W 10x15", "nombre_staad": "W10X15", "A": 28.5, "Sx": 226, "r": 2.94, "peso": 22.5},
        {"nombre": "W 10x22", "nombre_staad": "W10X22", "A": 41.9, "Sx": 380, "r": 3.37, "peso": 32.7},
        {"nombre": "W 12x14", "nombre_staad": "W12X14", "A": 26.8, "Sx": 244, "r": 2.41, "peso": 21.0},
        {"nombre": "W 12x19", "nombre_staad": "W12X19", "A": 35.9, "Sx": 349, "r": 3.30, "peso": 28.3},
        {"nombre": "W 12x26", "nombre_staad": "W12X26", "A": 49.4, "Sx": 547, "r": 3.81, "peso": 38.7},
        {"nombre": "W 14x22", "nombre_staad": "W14X22", "A": 41.9, "Sx": 475, "r": 2.64, "peso": 32.7},
        {"nombre": "W 14x30", "nombre_staad": "W14X30", "A": 57.1, "Sx": 688, "r": 3.78, "peso": 44.6}
    ]
    return sorted(perfiles, key=lambda x: x["peso"])

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
            
    # Agregar columnas de viento
    for mem_id in model.groups.get('_COLVIENTO', []):
        grupos["CV-1"].append(mem_id)
            
    # Filtrar los que están vacíos
    return {k: v for k, v in grupos.items() if len(v) > 0}

def predisenar_grupo(nombre_grupo, model):
    """
    Estima las cargas y devuelve el top 5 de perfiles OR o W.
    """
    if "CV" in nombre_grupo:
        perfiles = generar_base_datos_w()
    else:
        perfiles = generar_base_datos_or()
    
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
        
    # Fuerzas estimadas
    P_kg = At_vert * (CM + CV)
    
    # Momento por viento (viga simplemente apoyada = wL^2/8)
    w_viento_kg_m = viento * L_trib_viento
    M_viento_kg_m = (w_viento_kg_m * H**2) / 8.0
    M_viento_kg_cm = M_viento_kg_m * 100.0
    
    # Esfuerzo de fluencia del acero (Fy) en kg/cm2, usualmente A500 Gr. B es ~3230 kg/cm2 (46 ksi)
    Fy = 3230.0
    E = 2039000.0 # Módulo de elasticidad kg/cm2
    Cc = math.sqrt(2 * math.pi**2 * E / Fy)
    KL = H * 100.0 # Altura efectiva en cm (K=1.0)
    
    resultados = []
    
    for perfil in perfiles:
        A = perfil["A"]
        Sx = perfil["Sx"]
        r = perfil.get("r", 5.0)
        
        # Revisión de esbeltez
        klr = KL / r
        if klr > 200:
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
            A = perfil["A"]
            Sx = perfil["Sx"]
            r = perfil.get("r", 5.0)
            
            klr = KL / r
            if klr > 200: continue
                
            fa = P_kg / A if A > 0 else 0
            fb = M_viento_kg_cm / Sx if Sx > 0 else 0
            
            Fb_adm = 0.6 * Fy
            if klr < Cc:
                FS = (5.0/3.0) + (3.0 * klr)/(8.0 * Cc) - (klr**3)/(8.0 * Cc**3)
                Fa_adm = (1.0 - (klr**2)/(2.0 * Cc**2)) * Fy / FS
            else:
                Fa_adm = (12.0 * math.pi**2 * E) / (23.0 * klr**2)
                
            ratio = (fa / Fa_adm) + (fb / Fb_adm)
            if 0.3 <= ratio <= 1.2:
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
