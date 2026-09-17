"""
Gestión de datos, sincronización y cálculo de densidades del Catálogo de Conceptos.
- Integración con base de datos AISC Shapes v15.0 para columnas (IPR Doble / WD, W, HSS Cuadrada, HSS Rectangular).
- Cálculo paramétrico de columnas con nivel de desplante (debajo N.P.T.), desperdicio, placa tapón y altura promedio Hp.
- Cálculo paramétrico de Plantillas (+30cm por sentido, redondeo a 5cm, 37.5 kg/m²).
- Cálculo de Anclas (cajones de 4, 6, 8 y 12 anclas de 18 a 95 kg).
- Si no está sincronizado con STAAD.Pro, los valores marcan 0.
"""

import os
import sys
import math
import streamlit as st

# Asegurar app en sys.path
app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app"))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

import prediseno
from .aisc_loader import (
    get_aisc_db, 
    find_profile, 
    calculate_plantilla, 
    calculate_anclas_default,
    format_profile_mexican_label
)

# Paleta sobria de colores para ingeniería estructural (Azules oscuros y grises)
SOBER_PALETTE = {
    "Columnas": "#0f2b48",      # Azul marino profundo
    "Armaduras": "#1b3b6f",     # Azul acero oscuro
    "Joists": "#2c4a75",        # Azul pizarra
    "Contravientos": "#3e5c76", # Pizarra intermedio
    "Conexiones": "#50657b",    # Carbón frío
    "Cubierta": "#64748b",      # Gris pizarra
    "Mezanine": "#94a3b8"       # Gris metálico
}

ROUND_BAR_WEIGHTS = {
    1.905: 2.24,  # 3/4"  -> 2.24 kg/m
    2.54: 3.97,   # 1"    -> 3.97 kg/m
    3.175: 6.21,  # 1 1/4"-> 6.21 kg/m
    3.81: 9.00,   # 1 1/2"-> 9.00 kg/m
    4.445: 12.18, # 1 3/4"-> 12.18 kg/m
    5.08: 15.89   # 2"    -> 15.89 kg/m
}

def init_column_group_state(c_name, mids, model, staad_profile=None):
    """
    Inicializa o recupera el estado detallado de cuantificación para un tipo de columna.
    """
    state_key = f"col_quant_{c_name}"
    if state_key in st.session_state:
        return st.session_state[state_key]

    cant = len(mids)
    hlibre = float(getattr(model, "HLibre_m", 9.75))
    harm = float(getattr(model, "HArmad_m", 1.8))
    
    # Altura inicial del modelo
    h_init = 4.70
    if mids and mids[0] in model.members:
        n1, n2 = model.members[mids[0]]
        y1 = model.nodes[n1][1]
        y2 = model.nodes[n2][1]
        h_init = round(abs(y2 - y1) / 100.0, 2)
    else:
        h_init = round(hlibre + harm, 2)

    # Determinar perfil sugerido desde STAAD o defaults
    perfil_nom = staad_profile or st.session_state.get(f"sel_{c_name}", "WD14X90")
    perfil_data = find_profile(perfil_nom)
    
    if not perfil_data:
        # Fallback a WD14X90 o W14X90
        perfil_data = find_profile("WD14X90") or find_profile("W14X90") or {
            "nombre": "WD14X90",
            "peso_kg_m": 267.86,
            "largo_cm": 35.56,
            "ancho_cm": 36.83
        }

    # Tipo de sección
    nom_upper = perfil_data["nombre"].upper()
    if nom_upper.startswith("WD"):
        sec_type = "IPR Doble (WD)"
    elif "HSS" in nom_upper:
        sec_type = "HSS Cuadrada" if perfil_data.get("ht_in") == perfil_data.get("b_in") else "HSS Rectangular"
    else:
        sec_type = "W"

    # Filas de cuantificación de alturas (Imagen 1)
    rows = [
        {"no": cant, "longitud": h_init, "npt": 0.10},
        {"no": 0, "longitud": 0.0, "npt": 0.10},
        {"no": 0, "longitud": 0.0, "npt": 0.10},
        {"no": 0, "longitud": 0.0, "npt": 0.10},
        {"no": 0, "longitud": 0.0, "npt": 0.10}
    ]

    anclas_num, anclas_peso = calculate_anclas_default(perfil_data.get("largo_cm", 35.0), perfil_data.get("ancho_cm", 35.0))

    data = {
        "c_name": c_name,
        "sec_type": sec_type,
        "perfil": perfil_data["nombre"],
        "peso_kg_m": float(perfil_data["peso_kg_m"]),
        "largo_cm": float(perfil_data.get("largo_cm", 35.0)),
        "ancho_cm": float(perfil_data.get("ancho_cm", 35.0)),
        "cant": cant,
        "altura_modelo_m": h_init,
        "desplante_m": 0.10,
        "desperdicio_pct": 2.0,
        "placa_tapon_kg": 70.0,
        "anclas_num": anclas_num,
        "anclas_peso_kg": anclas_peso
    }

    st.session_state[state_key] = data
    return data

def calculate_column_group_totals(col_state):
    """
    Calcula las magnitudes para un tipo de columna de forma simplificada:
    Toma la altura del modelo y le suma el nivel de desplante (debajo N.P.T. por defecto 0.10m).
    """
    cant = int(col_state.get("cant", 0))
    h_model = float(col_state.get("altura_modelo_m", 0.0))
    desplante_m = float(col_state.get("desplante_m", 0.10))

    # Altura total por columna: usar altura_promedio_m si está presente, o h_model + desplante_m
    if "altura_promedio_m" in col_state and float(col_state["altura_promedio_m"]) > 0:
        altura_total_col = round(float(col_state["altura_promedio_m"]), 2)
    elif h_model > 0:
        altura_total_col = round(h_model + desplante_m, 2)
    else:
        altura_total_col = round(float(col_state.get("altura_total_col", 10.61)), 2)

    total_no = cant
    total_long_m = round(total_no * altura_total_col, 2)
    long_promedio_m = altura_total_col
    hp_cm = round(altura_total_col * 100.0, 1)

    peso_kg_m = float(col_state.get("peso_kg_m", 134.0))
    desp_pct = float(col_state.get("desperdicio_pct", 2.0))
    placa_tapon = float(col_state.get("placa_tapon_kg", 70.0))

    peso_columna_base = round(altura_total_col * peso_kg_m, 2)
    peso_con_desp = round(peso_columna_base * (1.0 + desp_pct / 100.0), 2)
    peso_por_columna = round(peso_con_desp + placa_tapon, 2)
    peso_total_grupo = round(peso_por_columna * total_no, 2)

    # Cálculo de plantillas (+30cm por sentido, redondeado a 5cm, 37.5 kg/m2)
    l_cm = col_state.get("largo_cm", 35.0)
    b_cm = col_state.get("ancho_cm", 35.0)
    l_plan, b_plan, area_plan, p_unit_plan = calculate_plantilla(l_cm, b_cm)
    peso_plantillas_grupo = round(total_no * p_unit_plan, 2)

    # Cálculo de anclas
    anclas_num = col_state.get("anclas_num", 8)
    anclas_peso = col_state.get("anclas_peso_kg", 80.0)
    peso_anclas_grupo = round(total_no * anclas_peso, 2)

    return {
        "cant": cant,
        "altura_modelo_m": h_model,
        "desplante_m": desplante_m,
        "altura_total_col": altura_total_col,
        "total_no": total_no,
        "total_long_m": total_long_m,
        "long_promedio_m": long_promedio_m,
        "hp_cm": hp_cm,
        "peso_columna_base": peso_columna_base,
        "peso_por_columna": peso_por_columna,
        "peso_total_grupo": peso_total_grupo,
        # Plantillas
        "largo_plan_cm": l_plan,
        "ancho_plan_cm": b_plan,
        "area_plan_m2": area_plan,
        "peso_unit_plan": p_unit_plan,
        "peso_plantillas_grupo": peso_plantillas_grupo,
        # Anclas
        "anclas_num": anclas_num,
        "anclas_peso_kg": anclas_peso,
        "peso_anclas_grupo": peso_anclas_grupo
    }

def compute_catalogo_from_model(model, is_synchronized=False, staad_profiles=None):
    """
    Calcula los conceptos a partir del modelo y la base AISC.
    Mantiene los expanders y cuantificación disponibles tanto con OpenSTAAD conectado como en modo local.
    """
    if model is None:
        return {
            "is_synchronized": False,
            "area_m2": 0.0,
            "peso_total_acero": 0.0,
            "densidad_total": 0.0,
            "pesos_por_categoria": {k: 0.0 for k in SOBER_PALETTE.keys()},
            "densidades_por_categoria": {k: 0.0 for k in SOBER_PALETTE.keys()},
            "porcentajes": {k: 0.0 for k in SOBER_PALETTE.keys()},
            "columnas_detalle": {},
            "conceptos_por_tab": {
                "Columnas": [],
                "Plantillas": [],
                "Anclas": [],
                "Armaduras": [],
                "Joists": [],
                "Contravientos": [],
                "Conexiones": [],
                "Cubierta": [],
                "Mezanine": []
            }
        }

    # 1. Geometría general del modelo
    larm = float(getattr(model, "Larm_m", 20.0))
    ljoist = float(getattr(model, "Ljoist_m", 10.0))
    nbay = int(getattr(model, "nBay", 4))
    nspan = int(getattr(model, "nSpan", 3))
    area_m2 = round(larm * nspan * ljoist * nbay, 2)
    if area_m2 <= 0:
        area_m2 = 1.0

    staad_prof = staad_profiles or {}

    # 2. Procesar cada tipo de columna con la base AISC
    cols_dict = prediseno.clasificar_columnas(model)
    columnas_detalle = {}
    tab_columnas = []
    tab_plantillas = []
    tab_anclas = []

    peso_total_cols_acero = 0.0
    peso_total_plantillas = 0.0
    peso_total_anclas = 0.0

    for c_name, mids in sorted(cols_dict.items()):
        col_state = init_column_group_state(c_name, mids, model, staad_prof.get(c_name))
        res = calculate_column_group_totals(col_state)
        columnas_detalle[c_name] = {**col_state, **res}

        if res["total_no"] > 0:
            peso_total_cols_acero += res["peso_total_grupo"]
            peso_total_plantillas += res["peso_plantillas_grupo"]
            peso_total_anclas += res["peso_anclas_grupo"]

            # Renglón para catálogo
            perf_lbl = format_profile_mexican_label(col_state['perfil'])
            tab_columnas.append({
                "concepto": c_name,
                "descripcion": f"Columna {c_name} a base de {perf_lbl} Hp={res['hp_cm']:.1f}",
                "cant": res["total_no"],
                "unidad": "pza",
                "p_unit": res["peso_por_columna"],
                "peso_total": res["peso_total_grupo"]
            })

            tab_plantillas.append({
                "concepto": f"Plantilla {c_name}",
                "descripcion": f"Plantilla para {c_name} de {res['largo_plan_cm']:.0f}x{res['ancho_plan_cm']:.0f} cm e=3/16\"",
                "cant": res["total_no"],
                "unidad": "pza",
                "p_unit": res["peso_unit_plan"],
                "peso_total": res["peso_plantillas_grupo"]
            })

            tab_anclas.append({
                "concepto": f"Anclas {c_name}",
                "descripcion": f"Cajón con {res['anclas_num']} anclas para {c_name}",
                "cant": res["total_no"],
                "unidad": "pza",
                "p_unit": res["anclas_peso_kg"],
                "peso_total": res["peso_anclas_grupo"]
            })

    # 3. Armaduras
    total_trusses = (nbay + 1) * nspan
    cant_a1 = round(total_trusses * 0.4)
    cant_a2 = total_trusses - cant_a1
    p_unit_a1 = round(larm * 58.0, 2)
    p_unit_a2 = round(larm * 50.0, 2)
    p_tot_a1 = round(cant_a1 * p_unit_a1, 2)
    p_tot_a2 = round(cant_a2 * p_unit_a2, 2)
    cant_sec = round(nbay * (nspan + 1) * 2)
    p_tot_sec = round(cant_sec * (ljoist * 24.0), 2)
    peso_armaduras = p_tot_a1 + p_tot_a2 + p_tot_sec

    tab_armaduras = [
        {"concepto": "A-1", "descripcion": f"Armadura A-1 Lp={round(larm*100,1)}", "cant": cant_a1, "unidad": "pza", "p_unit": p_unit_a1, "peso_total": p_tot_a1},
        {"concepto": "A-2", "descripcion": f"Armadura A-2 Lp={round(larm*100,1)}", "cant": cant_a2, "unidad": "pza", "p_unit": p_unit_a2, "peso_total": p_tot_a2},
        {"concepto": "Secundarias", "descripcion": "Armaduras secundarias", "cant": cant_sec, "unidad": "pza", "p_unit": round(ljoist * 24.0, 2), "peso_total": p_tot_sec}
    ]

    # 4. Joists
    cant_joists = len(model.groups.get("_JOISTGRAL", [])) or round(area_m2 / 18.0)
    p_tot_joist = round(cant_joists * (ljoist * 12.0), 2)
    m_flambeo = round(nbay * ljoist * 4 * (nspan * 5), 1)
    p_tot_flamb = round(m_flambeo * 1.08, 2)
    peso_joists = p_tot_joist + p_tot_flamb

    tab_joists = [
        {"concepto": "J-1", "descripcion": f"Larguero Joist J-1 L={round(ljoist*100,1)}", "cant": cant_joists, "unidad": "pza", "p_unit": round(ljoist*12.0, 2), "peso_total": p_tot_joist},
        {"concepto": "Contraflambeo", "descripcion": "Contraflambeo continuo", "cant": m_flambeo, "unidad": "m", "p_unit": 1.08, "peso_total": p_tot_flamb}
    ]

    # 5. Contravientos
    tot_cv = len(model.groups.get("_CVH", [])) or 120
    lp_cv = round(math.sqrt(larm**2 + ljoist**2) * 100, 1)
    peso_cv = round(tot_cv * (lp_cv / 100.0) * 4.5, 2)
    tab_cv = [{"concepto": "CVH", "descripcion": f"Contraviento horizontal redondo Lp={lp_cv}", "cant": tot_cv, "unidad": "pza", "p_unit": round((lp_cv/100.0)*4.5, 2), "peso_total": peso_cv}]

    # 6. Conexiones (3% sobre estructura acumulada)
    peso_base_cx = peso_total_cols_acero + peso_armaduras + peso_joists + peso_cv
    peso_conexiones = round(peso_base_cx * 0.03, 2)
    tab_conexiones = [{"concepto": "Conexiones", "descripcion": "Ángulos y placas de conexión (3% est.)", "cant": 1, "unidad": "lote", "p_unit": peso_conexiones, "peso_total": peso_conexiones}]

    # Suma de columnas incluye perfiles de columna + plantillas + anclas
    peso_cat_columnas = round(peso_total_cols_acero + peso_total_plantillas + peso_total_anclas, 2)

    pesos_cat = {
        "Columnas": peso_cat_columnas,
        "Armaduras": round(peso_armaduras, 2),
        "Joists": round(peso_joists, 2),
        "Contravientos": round(peso_cv, 2),
        "Conexiones": round(peso_conexiones, 2),
        "Cubierta": 0.0,
        "Mezanine": 0.0
    }

    peso_total_acero = sum(pesos_cat.values())
    densidad_total = round(peso_total_acero / area_m2, 2)
    densidades_cat = {k: round(v / area_m2, 2) for k, v in pesos_cat.items()}
    porcentajes = {k: round((v / peso_total_acero * 100.0), 1) if peso_total_acero > 0 else 0.0 for k, v in pesos_cat.items()}

    return {
        "is_synchronized": True,
        "area_m2": area_m2,
        "peso_total_acero": round(peso_total_acero, 2),
        "densidad_total": densidad_total,
        "pesos_por_categoria": pesos_cat,
        "densidades_por_categoria": densidades_cat,
        "porcentajes": porcentajes,
        "columnas_detalle": columnas_detalle,
        "conceptos_por_tab": {
            "Columnas": tab_columnas,
            "Plantillas": tab_plantillas,
            "Anclas": tab_anclas,
            "Armaduras": tab_armaduras,
            "Joists": tab_joists,
            "Contravientos": tab_cv,
            "Conexiones": tab_conexiones,
            "Cubierta": [],
            "Mezanine": []
        }
    }
