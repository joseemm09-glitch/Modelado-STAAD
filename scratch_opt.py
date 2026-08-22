import sys
import os

with open('app/prediseno.py', 'a', encoding='utf-8') as f:
    f.write('''
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
''')
