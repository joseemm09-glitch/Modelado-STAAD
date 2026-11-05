"""
reglamentos.py - Módulo de Normativas de Carga, Combinaciones Estructurales
y Metodologías de Diseño en Acero (ASD y LRFD) para la República Mexicana.

Reglamentos soportados:
1. Reglamento de Chihuahua / IBC (Actual en FrameOne)
2. ASCE 7-16 / 7-22 (Estándar Industrial / FM Global / Parques Industriales)
3. NTC-CDMX (2017 / 2023) - Normas Técnicas Complementarias sobre Criterios y Acciones
4. CFE MDSOC-2015 - Manual de Diseño de Obras Civiles de la CFE (Estándar Nacional)

Referencia de Casos de Carga Primaria en FrameOne (.std):
  LOAD 1  : CM   (Carga Muerta)
  LOAD 2  : CMP  (Carga Muerta Disminuida 0.6 CM)
  LOAD 3  : CV   (Carga Viva de Piso)
  LOAD 4  : CVR  (Carga Viva Reducida de Piso)
  LOAD 5  : CVT  (Carga Viva de Techo Máxima)
  LOAD 6  : CVRT (Carga Viva Instantánea / Reducida de Techo = 0.7 CVT)
  LOAD 7  : VX+  (Viento X+)
  LOAD 8  : VX-  (Viento X-)
  LOAD 9  : VZ+  (Viento Z+)
  LOAD 10 : VZ-  (Viento Z-)
  LOAD 11 : SX+  (Sismo X+)
  LOAD 12 : SX-  (Sismo X-)
  LOAD 13 : SZ+  (Sismo Z+)
  LOAD 14 : SZ-  (Sismo Z-)
  LOAD 15 : N    (Carga de Granizo / Nieve)
  LOAD 16 : MASA DE SISMO
"""

from typing import Tuple, List, Dict, Any

REGLAMENTOS_DISPONIBLES = [
    "Chihuahua / IBC",
    "ASCE 7-16 / 7-22",
    "NTC-CDMX",
    "CFE MDSOC-2015"
]

METODOS_DISENO = [
    "ASD",
    "LRFD"
]

GRUPOS_IMPORTANCIA = [
    "Grupo B",
    "Grupo A"
]


def normalizar_metodo(metodo_str: str) -> str:
    """Devuelve 'LRFD' o 'ASD' a partir de la cadena seleccionada en UI."""
    if not metodo_str:
        return "ASD"
    return "LRFD" if "LRFD" in metodo_str.upper() else "ASD"


def normalizar_grupo(grupo_str: str) -> str:
    """Devuelve 'A' o 'B' a partir de la cadena seleccionada en UI."""
    if not grupo_str:
        return "B"
    return "A" if "GRUPO A" in grupo_str.upper() or grupo_str.strip().upper() == "A" else "B"


def _fmt_factor(val: float) -> str:
    """Formatea un factor numérico sin ceros innecesarios a la derecha (ej. 1.0, 0.75, 0.33)."""
    s = f"{val:.3f}".rstrip("0").rstrip(".")
    if "." not in s:
        s += ".0"
    return s


def _add_comb(combs: List[Tuple[str, List[Tuple[int, float]]]], title: str, pairs: List[Tuple[int, float]]):
    """Agrega una combinación filtrando factores nulos."""
    valid_pairs = [(lc, f) for lc, f in pairs if abs(f) > 1e-6]
    if valid_pairs:
        combs.append((title, valid_pairs))


def _generar_pares_sismo(
    factor_principal: float,
    incluir_bidireccional: bool = False
) -> List[Tuple[str, List[Tuple[int, float]]]]:
    """
    Genera las solicitaciones sísmicas unidireccionales (X+, X-, Z+, Z-)
    y opcionalmente las 8 combinaciones bidireccionales ortogonales (100% + 30%):
      ±1.0 Sx ± 0.3 Sz   y   ±0.3 Sx ± 1.0 Sz
    """
    fp = round(factor_principal, 3)
    f_str = _fmt_factor(fp)
    casos: List[Tuple[str, List[Tuple[int, float]]]] = [
        (f"{f_str}(SX+)", [(11, fp)]),
        (f"{f_str}(SX-)", [(12, fp)]),
        (f"{f_str}(SZ+)", [(13, fp)]),
        (f"{f_str}(SZ-)", [(14, fp)]),
    ]
    if incluir_bidireccional:
        f30 = round(fp * 0.30, 3)
        f30_str = _fmt_factor(f30)
        # 100% X + 30% Z
        casos.extend([
            (f"{f_str}SX+{f30_str}SZ+", [(11, fp), (13, f30)]),
            (f"{f_str}SX+{f30_str}SZ-", [(11, fp), (14, f30)]),
            (f"{f_str}SX-{f30_str}SZ+", [(12, fp), (13, f30)]),
            (f"{f_str}SX-{f30_str}SZ-", [(12, fp), (14, f30)]),
            # 30% X + 100% Z
            (f"{f30_str}SX+{f_str}SZ+", [(11, f30), (13, fp)]),
            (f"{f30_str}SX+{f_str}SZ-", [(11, f30), (14, fp)]),
            (f"{f30_str}SX-{f_str}SZ+", [(12, f30), (13, fp)]),
            (f"{f30_str}SX-{f_str}SZ-", [(12, f30), (14, fp)]),
        ])
    return casos


def construir_lista_combinaciones(
    reglamento: str = "Chihuahua / IBC (Actual)",
    metodo: str = "ASD",
    grupo_importancia: str = "B",
    incluir_sismo_bidireccional: bool = False
) -> List[Tuple[str, str, List[Tuple[int, float]]]]:
    """
    Construye la lista ordenada de combinaciones de carga para el reglamento y método indicados.
    Retorna una lista de tuplas: (categoria, titulo_combinacion, [(load_id, factor), ...])
    """
    met = normalizar_metodo(metodo)
    grp = normalizar_grupo(grupo_importancia)
    reg_up = reglamento.upper()

    lista: List[Tuple[str, str, List[Tuple[int, float]]]] = []

    def add(cat: str, title: str, pairs: List[Tuple[int, float]]):
        valid = [(lc, f) for lc, f in pairs if abs(f) > 1e-6]
        if valid:
            lista.append((cat, title, valid))

    vientos = [
        ("VX+", 7),
        ("VX-", 8),
        ("VZ+", 9),
        ("VZ-", 10),
    ]

    # ==========================================================================
    # 1. REGLAMENTO DE CHIHUAHUA / IBC (ACTUAL EN FRAMEONE)
    # ==========================================================================
    if "CHIHUAHUA" in reg_up or ("IBC" in reg_up and "ASCE" not in reg_up):
        if met == "ASD":
            # Exactamente las combinaciones 17 a 54 originales de FrameOne + opcional bidireccional
            add("GRAVITACIONALES", "CM", [(1, 1.0)])
            add("GRAVITACIONALES", "CM+CV", [(1, 1.0), (3, 1.0)])
            add("GRAVITACIONALES", "CM+CVT", [(1, 1.0), (5, 1.0)])
            add("GRAVITACIONALES", "CM+N", [(1, 1.0), (15, 1.0)])
            add("GRAVITACIONALES", "CM+0.75CV+0.75CVT", [(1, 1.0), (3, 0.75), (5, 0.75)])
            add("GRAVITACIONALES", "CM+0.75CV+0.75N", [(1, 1.0), (3, 0.75), (15, 0.75)])

            # Viento
            for v_lbl, v_id in vientos:
                add("VIENTO", f"CM+({v_lbl})", [(1, 1.0), (v_id, 1.0)])
            for v_lbl, v_id in vientos:
                add("VIENTO", f"CM+0.75CV+0.75CVT+0.75({v_lbl})", [(1, 1.0), (3, 0.75), (5, 0.75), (v_id, 0.75)])
            for v_lbl, v_id in vientos:
                add("VIENTO", f"CM+0.75CV+0.75N+0.75({v_lbl})", [(1, 1.0), (3, 0.75), (15, 0.75), (v_id, 0.75)])
            for v_lbl, v_id in vientos:
                add("VIENTO", f"0.60CM+({v_lbl})", [(1, 0.6), (v_id, 1.0)])

            # Sismo
            sismos = _generar_pares_sismo(0.70, incluir_sismo_bidireccional)
            for s_lbl, s_pairs in sismos:
                add("SISMO", f"CM+{s_lbl}", [(1, 1.0)] + s_pairs)
            for s_lbl, s_pairs in sismos:
                add("SISMO", f"CM+0.75CV+0.75CVT+{s_lbl}", [(1, 1.0), (3, 0.75), (5, 0.75)] + s_pairs)
            for s_lbl, s_pairs in sismos:
                add("SISMO", f"CM+0.75CV+0.75N+{s_lbl}", [(1, 1.0), (3, 0.75), (15, 0.75)] + s_pairs)
            for s_lbl, s_pairs in sismos:
                add("SISMO", f"0.60CM+{s_lbl}", [(1, 0.6)] + s_pairs)

        else:
            # LRFD (Combinaciones 55 a 87 que estaban en la plantilla de Chihuahua)
            add("GRAVITACIONALES", "1.4CM", [(1, 1.4)])
            add("GRAVITACIONALES", "1.2CM+1.6CV+0.5CVT", [(1, 1.2), (3, 1.6), (5, 0.5)])
            add("GRAVITACIONALES", "1.2CM+1.6CV+0.5N", [(1, 1.2), (3, 1.6), (15, 0.5)])
            add("GRAVITACIONALES", "1.2CM+1.6CVT+1.0CV", [(1, 1.2), (5, 1.6), (3, 1.0)])
            add("GRAVITACIONALES", "1.2CM+1.6N+1.0CV", [(1, 1.2), (15, 1.6), (3, 1.0)])

            # Viento LRFD
            for v_lbl, v_id in vientos:
                add("VIENTO", f"1.2CM+1.6CVT+0.8({v_lbl})", [(1, 1.2), (5, 1.6), (v_id, 0.8)])
            for v_lbl, v_id in vientos:
                add("VIENTO", f"1.2CM+1.6N+0.8({v_lbl})", [(1, 1.2), (15, 1.6), (v_id, 0.8)])
            for v_lbl, v_id in vientos:
                add("VIENTO", f"1.2CM+1.6({v_lbl})+1.0CV+0.5CVT", [(1, 1.2), (v_id, 1.6), (3, 1.0), (5, 0.5)])
            for v_lbl, v_id in vientos:
                add("VIENTO", f"1.2CM+1.6({v_lbl})+1.0CV+0.5N", [(1, 1.2), (v_id, 1.6), (3, 1.0), (15, 0.5)])
            for v_lbl, v_id in vientos:
                add("VIENTO", f"0.9CM+1.6({v_lbl})", [(1, 0.9), (v_id, 1.6)])

            # Sismo LRFD
            sismos = _generar_pares_sismo(1.0, incluir_sismo_bidireccional)
            for s_lbl, s_pairs in sismos:
                add("SISMO", f"1.2CM+{s_lbl}+1.0CV+0.2N", [(1, 1.2)] + s_pairs + [(3, 1.0), (15, 0.2)])
            for s_lbl, s_pairs in sismos:
                add("SISMO", f"1.2CM+{s_lbl}+0.5CVT", [(1, 1.2)] + s_pairs + [(5, 0.5)])
            for s_lbl, s_pairs in sismos:
                add("SISMO", f"0.9CM+{s_lbl}", [(1, 0.9)] + s_pairs)

    # ==========================================================================
    # 2. ASCE 7-16 / 7-22 (INDUSTRIAL / FM GLOBAL)
    # ==========================================================================
    elif "ASCE" in reg_up:
        if met == "ASD":
            # ASCE 7 Sección 2.4 - Basic Combinations for Allowable Stress Design
            add("GRAVITACIONALES", "1.0CM", [(1, 1.0)])
            add("GRAVITACIONALES", "1.0CM+1.0CV", [(1, 1.0), (3, 1.0)])
            add("GRAVITACIONALES", "1.0CM+1.0CVT", [(1, 1.0), (5, 1.0)])
            add("GRAVITACIONALES", "1.0CM+1.0N", [(1, 1.0), (15, 1.0)])
            add("GRAVITACIONALES", "1.0CM+0.75CV+0.75CVT", [(1, 1.0), (3, 0.75), (5, 0.75)])
            add("GRAVITACIONALES", "1.0CM+0.75CV+0.75N", [(1, 1.0), (3, 0.75), (15, 0.75)])

            # Viento (0.6 W para presiones nominales/últimas ASCE 7, y 1.0 W para servicio directo)
            for v_lbl, v_id in vientos:
                add("VIENTO", f"1.0CM+0.60({v_lbl})", [(1, 1.0), (v_id, 0.60)])
            for v_lbl, v_id in vientos:
                add("VIENTO", f"1.0CM+1.0({v_lbl})", [(1, 1.0), (v_id, 1.0)])
            for v_lbl, v_id in vientos:
                add("VIENTO", f"1.0CM+0.75CV+0.75CVT+0.45({v_lbl})", [(1, 1.0), (3, 0.75), (5, 0.75), (v_id, 0.45)])
            for v_lbl, v_id in vientos:
                add("VIENTO", f"1.0CM+0.75CV+0.75CVT+0.75({v_lbl})", [(1, 1.0), (3, 0.75), (5, 0.75), (v_id, 0.75)])
            for v_lbl, v_id in vientos:
                add("VIENTO", f"1.0CM+0.75CV+0.75N+0.45({v_lbl})", [(1, 1.0), (3, 0.75), (15, 0.75), (v_id, 0.45)])
            for v_lbl, v_id in vientos:
                add("VIENTO", f"0.60CM+0.60({v_lbl})", [(1, 0.60), (v_id, 0.60)])
            for v_lbl, v_id in vientos:
                add("VIENTO", f"0.60CM+1.0({v_lbl})", [(1, 0.60), (v_id, 1.0)])

            # Sismo ASCE 7 ASD (0.7 E y 0.525 E con carga viva)
            sismos_07 = _generar_pares_sismo(0.70, incluir_sismo_bidireccional)
            sismos_0525 = _generar_pares_sismo(0.525, incluir_sismo_bidireccional)
            for s_lbl, s_pairs in sismos_07:
                add("SISMO", f"1.0CM+{s_lbl}", [(1, 1.0)] + s_pairs)
            for s_lbl, s_pairs in sismos_0525:
                add("SISMO", f"1.0CM+0.75CV+0.75CVT+{s_lbl}", [(1, 1.0), (3, 0.75), (5, 0.75)] + s_pairs)
            for s_lbl, s_pairs in sismos_0525:
                add("SISMO", f"1.0CM+0.75CV+0.75N+{s_lbl}", [(1, 1.0), (3, 0.75), (15, 0.75)] + s_pairs)
            for s_lbl, s_pairs in sismos_07:
                add("SISMO", f"0.60CM+{s_lbl}", [(1, 0.60)] + s_pairs)

        else:
            # ASCE 7 Sección 2.3 - LRFD Strength Design
            add("GRAVITACIONALES", "1.4CM", [(1, 1.4)])
            add("GRAVITACIONALES", "1.2CM+1.6CV+0.5CVT", [(1, 1.2), (3, 1.6), (5, 0.5)])
            add("GRAVITACIONALES", "1.2CM+1.6CV+0.5N", [(1, 1.2), (3, 1.6), (15, 0.5)])
            add("GRAVITACIONALES", "1.2CM+1.6CVT+1.0CV", [(1, 1.2), (5, 1.6), (3, 1.0)])
            add("GRAVITACIONALES", "1.2CM+1.6N+1.0CV", [(1, 1.2), (15, 1.6), (3, 1.0)])

            # Viento LRFD (0.5 W con máxima en techo y 1.0 W / 1.6 W envolvente)
            for v_lbl, v_id in vientos:
                add("VIENTO", f"1.2CM+1.6CVT+0.5({v_lbl})", [(1, 1.2), (5, 1.6), (v_id, 0.5)])
            for v_lbl, v_id in vientos:
                add("VIENTO", f"1.2CM+1.6N+0.5({v_lbl})", [(1, 1.2), (15, 1.6), (v_id, 0.5)])
            for v_lbl, v_id in vientos:
                add("VIENTO", f"1.2CM+1.0({v_lbl})+1.0CV+0.5CVT", [(1, 1.2), (v_id, 1.0), (3, 1.0), (5, 0.5)])
            for v_lbl, v_id in vientos:
                add("VIENTO", f"1.2CM+1.6({v_lbl})+1.0CV+0.5CVT", [(1, 1.2), (v_id, 1.6), (3, 1.0), (5, 0.5)])
            for v_lbl, v_id in vientos:
                add("VIENTO", f"1.2CM+1.0({v_lbl})+1.0CV+0.5N", [(1, 1.2), (v_id, 1.0), (3, 1.0), (15, 0.5)])
            for v_lbl, v_id in vientos:
                add("VIENTO", f"0.9CM+1.0({v_lbl})", [(1, 0.9), (v_id, 1.0)])
            for v_lbl, v_id in vientos:
                add("VIENTO", f"0.9CM+1.6({v_lbl})", [(1, 0.9), (v_id, 1.6)])

            # Sismo ASCE 7 LRFD
            sismos_10 = _generar_pares_sismo(1.0, incluir_sismo_bidireccional)
            for s_lbl, s_pairs in sismos_10:
                add("SISMO", f"1.2CM+{s_lbl}+1.0CV+0.2N", [(1, 1.2)] + s_pairs + [(3, 1.0), (15, 0.2)])
            for s_lbl, s_pairs in sismos_10:
                add("SISMO", f"1.2CM+{s_lbl}+0.5CVT", [(1, 1.2)] + s_pairs + [(5, 0.5)])
            for s_lbl, s_pairs in sismos_10:
                add("SISMO", f"0.9CM+{s_lbl}", [(1, 0.9)] + s_pairs)

    # ==========================================================================
    # 3. NTC-CDMX (2017 / 2023) Y 4. CFE MDSOC-2015
    # ==========================================================================
    else:
        # En NTC-CDMX y CFE MDSOC el sismo bidireccional (100% + 30%) es práctica obligatoria,
        # pero respetamos el flag del usuario (que en UI se activa automáticamente al elegir NTC o CFE).
        if met == "LRFD":
            # Factores de carga gravitacional según Grupo B (1.3 CM + 1.5 CV) o Grupo A (1.5 CM + 1.7 CV)
            fc_cm = 1.5 if grp == "A" else 1.3
            fc_cv = 1.7 if grp == "A" else 1.5
            s_cm = _fmt_factor(fc_cm)
            s_cv = _fmt_factor(fc_cv)

            # 1) Acciones Permanentes + Variables (Gravitacionales)
            add("GRAVITACIONALES", f"{s_cm}CM+{s_cv}CVT", [(1, fc_cm), (5, fc_cv)])
            add("GRAVITACIONALES", f"{s_cm}CM+{s_cv}CV+{s_cv}CVT", [(1, fc_cm), (3, fc_cv), (5, fc_cv)])
            add("GRAVITACIONALES", f"{s_cm}CM+{s_cv}N", [(1, fc_cm), (15, fc_cv)])
            add("GRAVITACIONALES", f"{s_cm}CM+{s_cv}CV+{s_cv}N", [(1, fc_cm), (3, fc_cv), (15, fc_cv)])

            # 2) Combinaciones Accidentales por Viento (1.1 CM + 1.1 CVRT + 1.1 V) y Volteo (0.9 CM + 1.1 V)
            # Nota técnica: En NTC y CFE, con acciones accidentales se usa Carga Viva Instantánea (LOAD 4 CVR y LOAD 6 CVRT)
            for v_lbl, v_id in vientos:
                add("VIENTO", f"1.1CM+1.1CVRT+1.1({v_lbl})", [(1, 1.1), (4, 1.1), (6, 1.1), (v_id, 1.1)])
            for v_lbl, v_id in vientos:
                add("VIENTO", f"1.1CM+1.1N+1.1({v_lbl})", [(1, 1.1), (15, 1.1), (v_id, 1.1)])
            for v_lbl, v_id in vientos:
                add("VIENTO", f"0.9CM+1.1({v_lbl})", [(1, 0.9), (v_id, 1.1)])

            # 3) Combinaciones Accidentales por Sismo (1.1 CM + 1.1 CVRT ± 1.1 S) y Volteo (0.9 CM ± 1.1 S)
            sismos_11 = _generar_pares_sismo(1.1, incluir_sismo_bidireccional)
            for s_lbl, s_pairs in sismos_11:
                add("SISMO", f"1.1CM+1.1CVRT+{s_lbl}", [(1, 1.1), (4, 1.1), (6, 1.1)] + s_pairs)
            for s_lbl, s_pairs in sismos_11:
                add("SISMO", f"0.9CM+{s_lbl}", [(1, 0.9)] + s_pairs)

        else:
            # ASD Equivalente (Esfuerzos Permisibles) para NTC-CDMX / CFE MDSOC
            # Utiliza Carga Viva Instantánea (LOAD 6 CVRT) en combinaciones accidentales con factor 0.75
            factor_imp = 1.15 if grp == "A" else 1.0
            s_imp = _fmt_factor(factor_imp)

            add("GRAVITACIONALES", f"{s_imp}CM", [(1, factor_imp)])
            add("GRAVITACIONALES", f"{s_imp}CM+{s_imp}CVT", [(1, factor_imp), (5, factor_imp)])
            add("GRAVITACIONALES", f"{s_imp}CM+{s_imp}CV+{s_imp}CVT", [(1, factor_imp), (3, factor_imp), (5, factor_imp)])
            add("GRAVITACIONALES", f"{s_imp}CM+{s_imp}N", [(1, factor_imp), (15, factor_imp)])

            # Viento Servicio / ASD
            for v_lbl, v_id in vientos:
                add("VIENTO", f"1.0CM+1.0({v_lbl})", [(1, 1.0), (v_id, 1.0)])
            for v_lbl, v_id in vientos:
                add("VIENTO", f"1.0CM+0.75CVRT+0.75({v_lbl})", [(1, 1.0), (4, 0.75), (6, 0.75), (v_id, 0.75)])
            for v_lbl, v_id in vientos:
                add("VIENTO", f"1.0CM+0.75N+0.75({v_lbl})", [(1, 1.0), (15, 0.75), (v_id, 0.75)])
            for v_lbl, v_id in vientos:
                add("VIENTO", f"0.60CM+1.0({v_lbl})", [(1, 0.60), (v_id, 1.0)])

            # Sismo Servicio / ASD (con CVRT instantánea y opción bidireccional 100%+30%)
            sismos_asd = _generar_pares_sismo(0.75, incluir_sismo_bidireccional)
            for s_lbl, s_pairs in sismos_asd:
                add("SISMO", f"1.0CM+{s_lbl}", [(1, 1.0)] + s_pairs)
            for s_lbl, s_pairs in sismos_asd:
                add("SISMO", f"1.0CM+0.75CVRT+{s_lbl}", [(1, 1.0), (4, 0.75), (6, 0.75)] + s_pairs)
            for s_lbl, s_pairs in sismos_asd:
                add("SISMO", f"0.60CM+{s_lbl}", [(1, 0.60)] + s_pairs)

    return lista


def generar_combinaciones_staad(
    reglamento: str = "Chihuahua / IBC (Actual)",
    metodo: str = "ASD",
    grupo_importancia: str = "B",
    incluir_sismo_bidireccional: bool = False,
    start_comb_id: int = 17
) -> Tuple[str, int, int]:
    """
    Genera el bloque de texto STAAD.Pro para todas las combinaciones de carga activas,
    respetando estrictamente el ancho máximo de línea (< 72 caracteres) y la sintaxis de STAAD.
    
    Retorna:
      (texto_staad, start_comb_id, end_comb_id)
    """
    met = normalizar_metodo(metodo)
    grp = normalizar_grupo(grupo_importancia)
    lista = construir_lista_combinaciones(
        reglamento=reglamento,
        metodo=met,
        grupo_importancia=grp,
        incluir_sismo_bidireccional=incluir_sismo_bidireccional
    )

    lines: List[str] = []
    lines.append("*" * 79)
    lines.append("**************************************COMBINACIONES DE CARGAS******************")
    lines.append("*" * 79)
    reg_clean = reglamento.upper().replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ó", "O").replace("Ú", "U")
    lines.append(f"***** REGLAMENTO: {reg_clean} | METODO: {met} | GRUPO: {grp} *****")

    curr_cat = None
    comb_id = start_comb_id

    for cat, title, pairs in lista:
        if cat != curr_cat:
            lines.append("*" * 79)
            lines.append(f"***** COMBINACIONES PARA CARGAS: {cat} *****")
            curr_cat = cat

        # Truncar título a longitud segura para INPUT WIDTH 79 (máx 70 chars toda la línea)
        header_line = f"LOAD COMB {comb_id} {title}"
        if len(header_line) > 72:
            header_line = header_line[:72]
        lines.append(header_line)

        # Formatear pares "load_id factor" respetando límite de 70 caracteres por renglón
        tokens: List[str] = []
        for lc, f in pairs:
            tokens.append(f"{lc} {_fmt_factor(f)}")

        curr_line = ""
        for tok in tokens:
            candidate = f"{curr_line} {tok}".strip() if curr_line else tok
            if len(candidate) > 68:
                lines.append(curr_line + " -")
                curr_line = tok
            else:
                curr_line = candidate
        if curr_line:
            lines.append(curr_line + " ")

        lines.append("*" * 79)
        comb_id += 1

    end_comb_id = comb_id - 1
    return "\n".join(lines), start_comb_id, end_comb_id


def obtener_comando_codigo_staad(metodo: str = "ASD") -> List[str]:
    """
    Devuelve las líneas de comando de código de diseño en STAAD.Pro según el método elegido:
      - En ASD: Mantiene 'CODE AISC' (estándar clásico de FrameOne).
      - En LRFD: Utiliza 'CODE AISC UNIFIED' + 'METHOD LRFD ALL' (AISC 360 LRFD).
    """
    met = normalizar_metodo(metodo)
    if met == "LRFD":
        return [
            "CODE AISC UNIFIED",
            "METHOD LRFD ALL"
        ]
    return ["CODE AISC"]


def obtener_factores_prediseno(
    reglamento: str = "Chihuahua / IBC (Actual)",
    metodo: str = "ASD",
    grupo_importancia: str = "B"
) -> Dict[str, float]:
    """
    Devuelve los factores de mayoración equivalentes para el prediseño rápido de columnas
    y el factor medio de conversión LRFD -> Servicio para zapatas.
    """
    met = normalizar_metodo(metodo)
    grp = normalizar_grupo(grupo_importancia)
    reg_up = reglamento.upper()

    if met == "ASD":
        factor_imp = 1.15 if (grp == "A" and ("NTC" in reg_up or "CFE" in reg_up)) else 1.0
        return {
            "metodo_num": 0.0,  # 0 = ASD
            "fc_cm": 1.0 * factor_imp,
            "fc_cv": 1.0 * factor_imp,
            "fc_viento": 1.0,
            "fc_sismo": 0.70 if ("ASCE" in reg_up or "CHIHUAHUA" in reg_up) else 0.75,
            "factor_desfactorizacion_zapata": 1.0
        }

    # LRFD
    if "NTC" in reg_up or "CFE" in reg_up:
        fc_cm = 1.5 if grp == "A" else 1.3
        fc_cv = 1.7 if grp == "A" else 1.5
        return {
            "metodo_num": 1.0,  # 1 = LRFD
            "fc_cm": fc_cm,
            "fc_cv": fc_cv,
            "fc_viento": 1.1,
            "fc_sismo": 1.1,
            "factor_desfactorizacion_zapata": 1.40 if grp == "B" else 1.55
        }
    else:
        # ASCE 7 / Chihuahua / IBC LRFD
        return {
            "metodo_num": 1.0,  # 1 = LRFD
            "fc_cm": 1.2,
            "fc_cv": 1.6,
            "fc_viento": 1.3,   # Envolvente representativa para prediseño lateral
            "fc_sismo": 1.0,
            "factor_desfactorizacion_zapata": 1.35
        }



def normalizar_reglamento(reg_str: str) -> str:
    if not reg_str:
        return "Chihuahua / IBC"
    r = reg_str.upper()
    if "NTC" in r:
        return "NTC-CDMX"
    if "CFE" in r:
        return "CFE MDSOC-2015"
    if "ASCE" in r:
        return "ASCE 7-16 / 7-22"
    return "Chihuahua / IBC"
