"""
Módulo de carga y utilidades de la base de datos AISC Shapes v15.0 para columnas.
Contiene W, IPR Doble (WD), HSS Cuadradas y HSS Rectangulares con dimensiones y pesos.
"""

import os
import json
import math

DB_PATH = os.path.join(os.path.dirname(__file__), "aisc_columns_db.json")

def load_aisc_columns_db():
    """
    Carga la base de datos AISC preprocesada.
    """
    if os.path.exists(DB_PATH):
        try:
            with open(DB_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"IPR_Doble": [], "W": [], "HSS_Square": [], "HSS_Rect": []}

_AISC_CACHE = None

def get_aisc_db():
    global _AISC_CACHE
    if _AISC_CACHE is None:
        _AISC_CACHE = load_aisc_columns_db()
    return _AISC_CACHE

def format_profile_mexican_label(nombre_perfil):
    """
    Convierte la nomenclatura AISC estándar a la nomenclatura usada en planos y catálogos de conceptos en México:
    - HSS16X16X3/8 -> OR 16" x 3/8"
    - HSS16X12X3/8 -> OR 16" x 12" x 3/8"
    - WD14X90 -> WD14X90
    - W14X90 -> W14X90
    """
    if not nombre_perfil:
        return ""
    nom_u = str(nombre_perfil).upper().strip()
    if nom_u.startswith("HSS"):
        parts = nom_u[3:].split("X")
        if len(parts) == 3:
            d1, d2, thk = parts[0], parts[1], parts[2]
            if d1 == d2:
                return f'OR {d1}" x {thk}'
            else:
                return f'OR {d1}" x {d2}" x {thk}'
    return str(nombre_perfil)

def find_profile(nombre_perfil):
    """
    Busca un perfil en la base de datos AISC y retorna sus datos o None.
    Soporta nombres AISC estándar (HSS16X16X3/8, WD14X90, W14X90)
    así como nombres en formato mexicano (OR 16" x 3/8", OR 16x3/8).
    """
    db = get_aisc_db()
    if not nombre_perfil:
        return None
    p_norm = str(nombre_perfil).upper().strip().replace(" ", "").replace("-", "").replace('"', '').replace("''", "")
    
    # Manejo si viene como OR 16 x 3/8 -> HSS16X16X3/8
    if p_norm.startswith("OR"):
        or_parts = p_norm[2:].split("X")
        if len(or_parts) == 2:
            p_norm = f"HSS{or_parts[0]}X{or_parts[0]}X{or_parts[1]}"
        elif len(or_parts) == 3:
            p_norm = f"HSS{or_parts[0]}X{or_parts[1]}X{or_parts[2]}"

    for cat, items in db.items():
        for it in items:
            it_nom = it["nombre"].upper().replace(" ", "").replace("-", "")
            if p_norm == it_nom:
                return it
            # Match alternativo sin prefijos o formatos
            if it_nom.endswith(p_norm) or p_norm.endswith(it_nom):
                return it
    return None

def calculate_plantilla(largo_cm, ancho_cm):
    """
    Lógica de Plantillas:
    Aumentar 30cm por sentido y redondear al múltiplo más cercano de 5cm.
    Área en m² * 37.5 kg/m² (peso placa de 3/16").
    Retorna: (largo_plan_cm, ancho_plan_cm, area_m2, peso_unit_kg)
    """
    # Aumentar 30 cm por sentido (15 cm por lado)
    l_bruto = largo_cm + 30.0
    b_bruto = ancho_cm + 30.0

    # Redondear al múltiplo más cercano de 5 cm
    l_plan = round(l_bruto / 5.0) * 5.0
    b_plan = round(b_bruto / 5.0) * 5.0

    area_m2 = round((l_plan / 100.0) * (b_plan / 100.0), 4)
    peso_unit = round(area_m2 * 37.5, 2)

    return l_plan, b_plan, area_m2, peso_unit

def calculate_anclas_default(largo_cm, ancho_cm):
    """
    Lógica de Anclas de acuerdo al tamaño de la columna:
    Considera cajones de 4, 6, 8 y 12 anclas con pesos de 18 kg a 95 kg.
    Retorna: (num_anclas, peso_cajon_kg)
    """
    max_dim = max(largo_cm, ancho_cm)

    if max_dim < 25.0: # Columna chica (< 10")
        return 4, 25.0
    elif max_dim < 35.0: # Columna mediana (10" a 14")
        return 6, 50.0
    elif max_dim < 45.0: # Columna estándar nave (14" a 16", e.g. OR 16")
        return 8, 80.0
    else: # Columna grande / pesada (> 18", WD pesada)
        return 12, 95.0
