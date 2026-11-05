"""
cimentacion_cad.py - Módulo de Extracción de Reacciones, Prediseño de Zapatas
y Generador Automático de Plano Estructural Preliminar (.DXF para AutoCAD).

Diseñado con Arquitectura Aditiva y No-Intrusiva para FrameOne.
Cumple con las mejores prácticas de ezdxf y OpenSTAAD COM API.
"""

import os
import math
import io
import re
from typing import Dict, Any, List, Tuple, Optional

try:
    import ezdxf
    from ezdxf import colors
except ImportError:
    ezdxf = None

# ==============================================================================
# PARTE 1: EXTRACCIÓN DE REACCIONES (OPENSTAAD Y FALLBACK ANALÍTICO)
# ==============================================================================

def map_base_nodes_to_groups(model) -> Dict[int, str]:
    """
    Mapea cada nodo base (Y == 0.0) a su grupo de columna ('C-1', 'C-2', 'C-3', 'C-4', 'CV-1').
    Utiliza la clasificación oficial de columnas de prediseno.clasificar_columnas().
    """
    try:
        from prediseno import clasificar_columnas
    except ImportError:
        import prediseno
        clasificar_columnas = prediseno.clasificar_columnas

    col_groups = clasificar_columnas(model)
    node_to_grp: Dict[int, str] = {}

    for grp, mem_list in col_groups.items():
        for mid in mem_list:
            if mid in model.members:
                nA, nB = model.members[mid]
                if nA in model.nodes and model.nodes[nA][1] == 0.0:
                    node_to_grp[nA] = grp
                if nB in model.nodes and model.nodes[nB][1] == 0.0:
                    node_to_grp[nB] = grp

    # Nodos de columnas de viento si no fueron asignados
    for mid in model.groups.get('_COLVIENTO', []):
        if mid in model.members:
            nA, nB = model.members[mid]
            if nA in model.nodes and model.nodes[nA][1] == 0.0 and nA not in node_to_grp:
                node_to_grp[nA] = "CV-1"
            if nB in model.nodes and model.nodes[nB][1] == 0.0 and nB not in node_to_grp:
                node_to_grp[nB] = "CV-1"

    # Nodos base restantes: asignar por proximidad geométrica
    xs = [coord[0] for coord in model.nodes.values()]
    zs = [coord[2] for coord in model.nodes.values()]
    x_min, x_max = (min(xs), max(xs)) if xs else (0.0, 1.0)
    z_min, z_max = (min(zs), max(zs)) if zs else (0.0, 1.0)
    tol = 10.0  # 10 cm

    all_base_nodes = set(getattr(model, 'base_nodes', [])) | set(getattr(model, 'wind_base_nodes', []))
    for nid, (x, y, z) in model.nodes.items():
        if y == 0.0:
            all_base_nodes.add(nid)

    for nid in all_base_nodes:
        if nid not in node_to_grp and nid in model.nodes:
            x, y, z = model.nodes[nid]
            is_x = (abs(x - x_min) < tol or abs(x - x_max) < tol)
            is_z = (abs(z - z_min) < tol or abs(z - z_max) < tol)
            if is_x and is_z:
                node_to_grp[nid] = "C-4"
            elif is_x:
                node_to_grp[nid] = "C-3"
            elif is_z:
                node_to_grp[nid] = "C-2"
            else:
                node_to_grp[nid] = "C-1"

    return node_to_grp


def _grp_sort_key(g: str) -> int:
    """Ordena los grupos para numeración continua de zapatas (C-1 -> Z-1, C-2 -> Z-2, etc.)."""
    if g == "C-1": return 1
    if g == "C-2": return 2
    if g == "C-3": return 3
    if g == "C-4": return 4
    if g == "CV-1": return 5
    if g.startswith("C-"):
        try: return 10 + int(g[2:])
        except Exception: return 50
    if g.startswith("CV-"):
        try: return 60 + int(g[3:])
        except Exception: return 90
    return 100


def obtener_reacciones_envolventes(model) -> Tuple[Dict[str, Dict[str, float]], str]:
    """
    Obtiene las reacciones envolventes críticas de diseño por grupo de columna.
    Prioridad 1: Conexión activa con OpenSTAAD.
    Prioridad 2: Fallback analítico tributario riguroso basado en cargas y geometría.
    
    Retorna: (reacciones_por_grupo, metodo_usado)
        Donde reacciones_por_grupo[grp] = {
            'P_max': float (Ton compresión),
            'P_uplift': float (Ton tensión/levantamiento),
            'Vx': float (Ton),
            'Vz': float (Ton),
            'Mx': float (Ton·m),
            'Mz': float (Ton·m),
            'count': int (nodos en el grupo)
        }
    """
    node_to_grp = map_base_nodes_to_groups(model)
    reacciones: Dict[str, Dict[str, float]] = {}

    # Intentar vía OpenSTAAD
    try:
        from openstaad import ops
        s = ops.connect()
        filename = s.GetSTAADFile()
        if filename:
            load_mod = ops.load
            n_comb = 0
            comb_cases: List[int] = []
            try:
                n_comb = load_mod.GetLoadCombinationCaseCount()
                if n_comb > 0:
                    comb_cases = list(load_mod.GetLoadCombinationCaseNumbers())
            except Exception:
                pass

            if not comb_cases:
                try:
                    n_prim = load_mod.GetPrimaryLoadCaseCount()
                    if n_prim > 0:
                        comb_cases = list(load_mod.GetPrimaryLoadCaseNumbers())
                except Exception:
                    pass

            if not comb_cases:
                comb_cases = list(range(17, 88)) + list(range(1, 17))

            output_mod = ops.output
            grupos_data: Dict[str, Dict[str, Any]] = {}
            exito_staad = False

            for nid, grp in node_to_grp.items():
                if grp not in grupos_data:
                    grupos_data[grp] = {
                        'P_max': 0.0, 'P_uplift': 0.0,
                        'Vx': 0.0, 'Vz': 0.0, 'Mx': 0.0, 'Mz': 0.0,
                        'nodes': set()
                    }
                grupos_data[grp]['nodes'].add(nid)

                for lc in comb_cases:
                    try:
                        reac = output_mod.GetSupportReactions(int(nid), int(lc))
                        if reac and len(reac) >= 6:
                            exito_staad = True
                            fx, fy, fz, mx, my, mz = reac[:6]
                            
                            # Convertir a Ton y Ton·m según convención STAAD
                            # En UNIT CM KG: Fuerzas en kg -> / 1000 = Ton; Momentos en kg·cm -> / 100000 = Ton·m
                            p_ton = fy / 1000.0
                            vx_ton = abs(fx) / 1000.0
                            vz_ton = abs(fz) / 1000.0
                            mx_tonm = abs(mx) / 100000.0
                            mz_tonm = abs(mz) / 100000.0

                            g = grupos_data[grp]
                            if p_ton > g['P_max']:
                                g['P_max'] = p_ton
                            if p_ton < 0 and abs(p_ton) > g['P_uplift']:
                                g['P_uplift'] = abs(p_ton)
                            if vx_ton > g['Vx']:
                                g['Vx'] = vx_ton
                            if vz_ton > g['Vz']:
                                g['Vz'] = vz_ton
                            if mx_tonm > g['Mx']:
                                g['Mx'] = mx_tonm
                            if mz_tonm > g['Mz']:
                                g['Mz'] = mz_tonm
                    except Exception:
                        continue

            if exito_staad:
                for grp, data in grupos_data.items():
                    reacciones[grp] = {
                        'P_max': round(data['P_max'], 2),
                        'P_uplift': round(data['P_uplift'], 2),
                        'Vx': round(data['Vx'], 2),
                        'Vz': round(data['Vz'], 2),
                        'Mx': round(data['Mx'], 2),
                        'Mz': round(data['Mz'], 2),
                        'count': len(data['nodes'])
                    }
                return reacciones, "OpenSTAAD (Análisis en Vivo)"
    except Exception:
        pass

    # --------------------------------------------------------------------------
    # Fallback Analítico Tributario Riguroso
    # --------------------------------------------------------------------------
    L_span = getattr(model, 'Larm_m', 15.24)
    L_bay = getattr(model, 'Ljoist_m', 12.192)
    H_col = getattr(model, 'HLibre_m', 9.75)
    H_arm = getattr(model, 'HArmad_m', 1.30)
    H_tot = H_col + H_arm

    cm = getattr(model, 'c_muerta', 30.0)     # kg/m²
    cv = getattr(model, 'c_viva', 100.0)      # kg/m²
    cg = getattr(model, 'c_granizo', 60.0)    # kg/m²
    w_grav = cm + max(cv, cg) + 35.0          # kg/m² (con peso propio estimado de armadura y joists)

    v_barl = getattr(model, 'v_barlovento', 85.0)  # kg/m²
    v_sota = getattr(model, 'v_sotavento', 50.0)   # kg/m²
    v_lat = getattr(model, 'v_laterales', 75.0)    # kg/m²
    v_succ = getattr(model, 'v_succion', 80.0)     # kg/m²

    cs = getattr(model, 'coef_sismico', 0.16)
    q_duct = getattr(model, 'ductilidad', 2.0)
    coef_sismo = cs / max(q_duct, 1.0)

    # Contar nodos por grupo
    grp_counts: Dict[str, int] = {}
    for grp in node_to_grp.values():
        grp_counts[grp] = grp_counts.get(grp, 0) + 1

    unique_grps = sorted(list(set(node_to_grp.values())), key=_grp_sort_key)
    if not unique_grps:
        unique_grps = ["C-1", "C-2", "C-3", "C-4"]

    for grp in unique_grps:
        if grp == "C-1":
            at_vert = L_span * L_bay
            at_viento = (L_bay * 0.2) * H_tot
            p_grav = at_vert * w_grav / 1000.0  # Ton
            vx = (v_lat * at_viento) / 1000.0 * 0.5
            vz = (v_barl * at_viento) / 1000.0 * 0.5
            p_up = max(0.0, (v_succ * at_vert - cm * at_vert) / 1000.0)
            mx = vx * (H_col * 0.5)
            mz = vz * (H_col * 0.5)
        elif grp == "C-2":
            at_vert = L_span * (L_bay / 2.0)
            at_viento = L_span * H_tot * 0.5
            p_grav = at_vert * w_grav / 1000.0
            vx = (v_lat * (L_bay / 2.0) * H_tot) / 1000.0
            vz = (v_barl * at_viento) / 1000.0 * 0.6
            p_up = max(0.0, (v_succ * at_vert - cm * at_vert) / 1000.0)
            mx = vx * (H_col * 0.5)
            mz = vz * (H_col * 0.5)
        elif grp == "C-3":
            at_vert = (L_span / 2.0) * L_bay
            at_viento = L_bay * H_tot * 0.5
            p_grav = at_vert * w_grav / 1000.0
            vx = (v_barl * at_viento) / 1000.0 * 0.6
            vz = (v_lat * (L_span / 2.0) * H_tot) / 1000.0
            p_up = max(0.0, (v_succ * at_vert - cm * at_vert) / 1000.0)
            mx = vx * (H_col * 0.5)
            mz = vz * (H_col * 0.5)
        elif grp == "C-4":
            at_vert = (L_span / 2.0) * (L_bay / 2.0)
            at_viento_x = (L_bay / 2.0) * H_tot
            at_viento_z = (L_span / 2.0) * H_tot
            p_grav = at_vert * w_grav / 1000.0
            vx = (v_barl * at_viento_x) / 1000.0 * 0.6
            vz = (v_barl * at_viento_z) / 1000.0 * 0.6
            p_up = max(0.0, (v_succ * at_vert - cm * at_vert) / 1000.0)
            mx = vx * (H_col * 0.5)
            mz = vz * (H_col * 0.5)
        elif grp == "CV-1":
            at_viento = getattr(model, 'max_wind_dist_m', 6.0) * H_tot
            at_vert = getattr(model, 'max_wind_dist_m', 6.0) * 1.5
            p_grav = at_vert * w_grav / 1000.0 + 1.5  # Peso propio de columna
            vx = (v_barl * at_viento) / 1000.0
            vz = 0.5
            p_up = 0.0
            mx = vx * (H_col * 0.25)  # Articulado en extremos
            mz = 0.2
        else:
            at_vert = L_span * L_bay * 0.75
            p_grav = at_vert * w_grav / 1000.0
            vx = 2.0
            vz = 2.0
            p_up = 0.0
            mx = 3.0
            mz = 3.0

        # Adicionar efecto de sismo basal estimado
        v_sismo = p_grav * coef_sismo
        vx = max(vx, v_sismo)
        vz = max(vz, v_sismo)

        reacciones[grp] = {
            'P_max': round(max(p_grav, 3.0), 2),
            'P_uplift': round(p_up, 2),
            'Vx': round(vx, 2),
            'Vz': round(vz, 2),
            'Mx': round(mx, 2),
            'Mz': round(mz, 2),
            'count': grp_counts.get(grp, 1)
        }

    return reacciones, "Analítico Tributario (Estimación de Ingeniería)"


# ==============================================================================
# PARTE 2: PREDIMENSIONAMIENTO DE ZAPATAS Y ESTIMACIÓN DE DADOS
# ==============================================================================

def estimar_dimension_dado(perfil_nombre: str) -> Tuple[float, float]:
    """
    Estima las dimensiones preliminares del pedestal/dado (b_d, l_d) en metros,
    asegurando una holgura mínima de 15 cm por lado alrededor del perfil.
    """
    if not perfil_nombre or perfil_nombre == "Auto":
        return 0.50, 0.50

    p_upper = perfil_nombre.upper()

    # Si es W / IPR (ej. W14X90, W21X68)
    mW = re.search(r'W(\d+)X(\d+)', p_upper)
    if mW:
        d_in = float(mW.group(1))
        d_m = d_in * 0.0254
        bf_m = max(d_m * 0.65, 0.20)
        # Holgura de 15 cm a cada lado: d + 0.30 m
        dado_x = math.ceil((bf_m + 0.30) * 10) / 10.0
        dado_z = math.ceil((d_m + 0.30) * 10) / 10.0
        return max(dado_x, 0.50), max(dado_z, 0.50)

    # Si es OR / HSS (ej. OR 16"x16"x3/8", HSS14X14X0.375)
    mOR = re.search(r'(\d+)\s*(?:X|")\s*(\d+)', p_upper)
    if mOR:
        b1_in = float(mOR.group(1))
        b2_in = float(mOR.group(2))
        dado_x = math.ceil(((b1_in * 0.0254) + 0.30) * 10) / 10.0
        dado_z = math.ceil(((b2_in * 0.0254) + 0.30) * 10) / 10.0
        return max(dado_x, 0.50), max(dado_z, 0.50)

    return 0.50, 0.50


def predimensionar_zapatas(
    reacciones: Dict[str, Dict[str, float]],
    q_adm_ton_m2: float = 15.0,
    gamma_s_ton_m3: float = 1.80,
    df_m: float = 1.50,
    perfiles_por_grupo: Optional[Dict[str, str]] = None,
    factor_desfactorizacion: float = 1.0,
    fc_kg_cm2: float = 250.0,
    fy_kg_cm2: float = 4200.0
) -> List[Dict[str, Any]]:
    """
    Calcula el predimensionamiento robusto de zapatas aisladas cuadradas y dados para cada grupo:
    1. Dimensión en Planta (B x L):
       - Revisa dos condiciones independientes y toma la mayor:
         a) Aplastamiento (compresión): Carga gravitacional aumentada 25-30% para absorber
            peso propio de zapata, relleno y momentos. Dividida entre la capacidad admisible neta.
         b) Levantamiento (succión de viento): FS = 1.5 contra volteo/succión.
            El peso combinado de la zapata y el relleno de tierra sobre ella debe equilibrar
            la fuerza de succión amplificada (1.5 * P_uplift).
       - Redondeo hacia arriba a múltiplos constructivos de 10 cm (mín. 1.00 x 1.00 m).
    2. Espesor de la zapata (Hz):
       - Rigidez: espesor efectivo entre un tercio y un cuarto del vuelo libre desde la cara del dado.
       - Revisión rápida de cortante unidireccional (como viga) y bidireccional (punzonamiento).
       - Recubrimiento inferior de 8 cm y redondeo a múltiplos de 5 cm (mín. 0.25 m, o 0.30 m en medianas/grandes).
    3. Armado Comercial Realista (Lecho inferior y Lecho superior):
       - Lecho inferior: flexión por presión hacia arriba en el vuelo + cuantía mínima por temperatura (0.0018 * b * h).
       - Lecho superior: flexión inversa por peso propio del suelo/zapata bajo succión de viento, o acero mínimo por temperatura.
       - Propuestas comerciales con varillas #4, #5 o #6 a separaciones de 15, 20 o 25 cm.
    """
    if perfiles_por_grupo is None:
        perfiles_por_grupo = {}

    filas_zapatas: List[Dict[str, Any]] = []

    # Capacidad neta admisible del suelo
    q_net = max(q_adm_ton_m2 - (gamma_s_ton_m3 * df_m), q_adm_ton_m2 * 0.70)
    f_desf = max(float(factor_desfactorizacion), 1.0)

    # Ordenar grupos para numeración continua de zapatas (Z-1, Z-2, Z-3, ...)
    sorted_grps = sorted(list(reacciones.keys()), key=_grp_sort_key)

    for idx, grp in enumerate(sorted_grps):
        r = reacciones[grp]
        tipo_z = f"Z-{idx + 1}"
        p_max = float(r.get('P_max', 10.0))
        p_up = float(r.get('P_uplift', 0.0))
        perfil = perfiles_por_grupo.get(grp, "Auto")

        dado_x, dado_z = estimar_dimension_dado(perfil)

        # ----------------------------------------------------------------------
        # 1. ANCHO Y LARGO (Zapata cuadrada, B = L)
        # ----------------------------------------------------------------------
        # Condición a) Aplastamiento / Compresión (+25% a 30% por peso propio y momentos)
        p_base_serv = (p_max / f_desf)
        p_comp = max(p_base_serv * 1.28, 1.0)
        area_comp = p_comp / q_net
        b_comp = math.sqrt(area_comp)

        # Condición b) Levantamiento / Succión de Viento (FS = 1.5)
        # Resistencia = peso combinado de concreto + tierra de relleno
        hz_est = 0.35 if df_m >= 1.50 else 0.25
        w_unit_resist = (hz_est * 2.40) + (max(df_m - hz_est, 0.0) * gamma_s_ton_m3)
        f_uplift_amplificada = 1.50 * max(p_up / f_desf, 0.0)
        area_succ = f_uplift_amplificada / max(w_unit_resist, 0.50)
        b_succ = math.sqrt(area_succ) if p_up > 0 else 0.0

        if b_succ > b_comp:
            b_raw = b_succ
            condicion_gob = "Succión"
        else:
            b_raw = b_comp
            condicion_gob = "Compresión"

        # Redondeo hacia arriba a múltiplos constructivos de 10 cm (mín. 1.00 m)
        b_m = max(math.ceil(b_raw * 10.0) / 10.0, 1.00)
        l_m = b_m

        # ----------------------------------------------------------------------
        # 2. ESPESOR DE LA ZAPATA (Peralte total Hz)
        # ----------------------------------------------------------------------
        vuelo_x = max((b_m - dado_x) / 2.0, 0.10)
        vuelo_z = max((l_m - dado_z) / 2.0, 0.10)
        vuelo_max = max(vuelo_x, vuelo_z)

        # Regla práctica de rigidez: peralte efectivo d ~ 1/3 a 1/4 del vuelo libre
        recub_m = 0.08  # 8 cm de recubrimiento inferior
        d_rig = vuelo_max / 3.5
        hz_rig = d_rig + recub_m

        # Mínimo absoluto según tamaño: 0.25 m si B < 1.50 m, 0.30 m en zapatas medianas/grandes
        hz_min = 0.30 if b_m >= 1.50 else 0.25
        hz_candidatos = [0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80]

        # Revisión rápida de cortante como viga y punzonamiento
        fc = max(float(fc_kg_cm2), 200.0)
        fy = max(float(fy_kg_cm2), 4000.0)
        q_ult = (p_comp * 1000.0) / ((b_m * 100.0) ** 2)  # kg/cm²

        hz_m = hz_min
        for hz_c in hz_candidatos:
            if hz_c < hz_min or hz_c < (math.ceil(hz_rig * 20.0) / 20.0):
                continue
            d_cm = (hz_c - recub_m) * 100.0
            v_cm = vuelo_max * 100.0

            # Cortante como viga a distancia d de la cara del dado
            if v_cm > d_cm:
                vu_viga = q_ult * (b_m * 100.0) * (v_cm - d_cm)
                phi_vc_viga = 0.75 * 0.53 * math.sqrt(fc) * (b_m * 100.0) * d_cm
                if vu_viga > phi_vc_viga:
                    continue

            # Punzonamiento en perímetro crítico bo
            c_cm = min(dado_x, dado_z) * 100.0
            bo = 4.0 * (c_cm + d_cm)
            area_crit = (c_cm + d_cm) ** 2
            vu_punz = q_ult * ((b_m * 100.0) ** 2 - area_crit)
            phi_vc_punz = 0.75 * 1.10 * math.sqrt(fc) * bo * d_cm
            if vu_punz > phi_vc_punz:
                continue

            hz_m = hz_c
            break

        hz_m = math.ceil(hz_m * 20.0) / 20.0

        # ----------------------------------------------------------------------
        # 3. ARMADO EN AMBOS SENTIDOS (Lecho inferior y Lecho superior)
        # ----------------------------------------------------------------------
        b_cm = b_m * 100.0
        d_cm = max((hz_m - recub_m) * 100.0, 15.0)

        # Flexión inferior por presión hacia arriba en el vuelo
        mu_inf_kgcm = (q_ult * b_cm * (vuelo_max * 100.0) ** 2) / 2.0
        as_inf_flex = mu_inf_kgcm / (0.90 * fy * 0.90 * d_cm)
        as_min = 0.0018 * b_cm * (hz_m * 100.0)
        as_inf = max(as_inf_flex, as_min)

        # Flexión superior por succión y contrapeso hacia abajo en el vuelo
        if p_up > 0:
            q_down_ton_m2 = (hz_m * 2.40) + (max(df_m - hz_m, 0.0) * gamma_s_ton_m3)
            q_down_kgcm2 = (q_down_ton_m2 * 1000.0 * 1.30) / 10000.0
            mu_sup_kgcm = (q_down_kgcm2 * b_cm * (vuelo_max * 100.0) ** 2) / 2.0
            as_sup_flex = mu_sup_kgcm / (0.90 * fy * 0.90 * d_cm)
            as_sup = max(as_sup_flex, as_min)
        else:
            as_sup = as_min

        def _seleccionar_rebar(as_req: float) -> str:
            # Varillas comerciales #4 (1.27 cm²), #5 (1.98 cm²), #6 (2.85 cm²)
            # Separaciones estándar cerradas a 15, 20 o 25 cm
            candidatos = [('#4', 1.27), ('#5', 1.98), ('#6', 2.85)]
            separaciones = [25.0, 20.0, 15.0]
            for nom, ab in candidatos:
                for s in separaciones:
                    as_prov = ab * (b_cm / s)
                    if as_prov >= as_req * 0.98:
                        return f"{nom} @ {int(s)}"
            return "#6 @ 15"

        rfzo_inf_str = _seleccionar_rebar(as_inf)
        rfzo_sup_str = _seleccionar_rebar(as_sup)

        filas_zapatas.append({
            "Tipo Zapata": tipo_z,
            "Z": tipo_z,
            "Grupo Columna": grp,
            "Perfil Columna": perfil,
            "P_max (Ton)": round(p_max, 2),
            "P_up (Ton)": round(p_up, 2),
            "B_ancho (m)": round(b_m, 2),
            "L_largo (m)": round(l_m, 2),
            "Hz_espesor (m)": round(hz_m, 2),
            "Dado_x (m)": round(dado_x, 2),
            "Dado_z (m)": round(dado_z, 2),
            "Gobernó": condicion_gob,
            "Lecho Inf": rfzo_inf_str,
            "Lecho Sup": rfzo_sup_str,
            "Rfzo_B": rfzo_inf_str,
            "Rfzo_D": rfzo_inf_str,
            "Rfzo_X": rfzo_sup_str,
            "Rfzo_Y": rfzo_sup_str
        })

    return filas_zapatas


# ==============================================================================
# PARTE 3: GENERADOR PROFESIONAL DE PLANOS EN AUTOCAD (.DXF) CON EZDXF
# ==============================================================================

def calcular_refuerzo_estimado(b_m: float, p_max: float, p_up: float = 0.0, hz_m: float = 0.35) -> Tuple[str, str, str, str]:
    """
    Propone especificaciones estándar de armado para la tabla de zapatas aisladas.
    Retorna: (rfzo_b, rfzo_d, rfzo_sup_x, rfzo_sup_y)
    """
    b_cm = b_m * 100.0
    as_min = 0.0018 * b_cm * (hz_m * 100.0)

    # Estimación de acero inferior
    if b_m <= 1.20:
        rfzo_inf = "#4 @ 25"
    elif b_m <= 1.50:
        rfzo_inf = "#4 @ 20"
    elif b_m <= 2.00:
        rfzo_inf = "#4 @ 15"
    elif b_m <= 2.50:
        rfzo_inf = "#5 @ 18"
    elif b_m <= 3.00:
        rfzo_inf = "#5 @ 15"
    else:
        rfzo_inf = "#6 @ 15"

    rfzo_b = rfzo_inf
    rfzo_d = rfzo_inf

    # Acero superior: si hay succión importante o zapata grande
    if p_up > 3.0 or b_m >= 2.00:
        if b_m <= 1.60:
            rfzo_sup = "#4 @ 25"
        elif b_m <= 2.20:
            rfzo_sup = "#4 @ 20"
        elif b_m <= 2.80:
            rfzo_sup = "#5 @ 20"
        else:
            rfzo_sup = "#5 @ 15"
    else:
        rfzo_sup = "#4 @ 25"

    return rfzo_b, rfzo_d, rfzo_sup, rfzo_sup


class GeneradorPlanoEstructuralDXF:
    """
    Genera un plano estructural de cimentación preliminar de alta fidelidad técnica (.DXF para AutoCAD)
    idéntico en presentación gráfica al archivo oficial '[CADDIES] Cimentación Preliminar.dwg':
    1. Planta de Cimentación orientada SIEMPRE horizontalmente (lado más largo en X):
       - Ejes con líneas CENTER y boyas CADDIES (bloque 'SIMB CABEZA EJES V1.3' con atributo NO.EJE).
       - Cotas parciales y totales (horizontal DIM100, vertical DIM100VERTICAL con _ArchTick).
       - Zapatas (polilínea amarilla capa ZAP.ASI) y dados (polilínea azul capa DADO con cruz de centro).
       - Etiquetas de texto D-1 y Z-1 / Z-2...
       - Sello central rojo 'SELLO PRELIMINAR'.
       - Título 'PLANTA DE CIMENTACION' con doble subrayado rojo y blanco al pie del plano.
    2. Detalles Estructurales CADDIES situados estrictamente a la derecha de la planta:
       - Detalle de elevación y corte de zapata aislada.
       - Detalle de armado de dado (DADO D-1).
       - Detalle de nivel de desplante.
       - Tabla interactiva 'ZAPATAS AISLADAS' completada dinámicamente con los datos del proyecto.
       - Tabla para varillas (ganchos, traslapes y pesos).
       - Cuadro de notas con la capacidad de carga admisible q_adm del sitio.
    3. Cero empalmes geométricos: cálculo analítico de offsets para cualquier proyecto y dimensiones.
    """

    def __init__(self, model, tabla_zapatas: List[Dict[str, Any]], q_adm: float, df: float):
        if ezdxf is None:
            raise RuntimeError("La librería 'ezdxf' no está instalada en el entorno.")

        self.model = model
        self.tabla_zapatas = tabla_zapatas
        self.q_adm = q_adm
        self.df = df

        self.zap_by_grp = {item.get("Grupo Columna", ""): item for item in tabla_zapatas}
        self.zap_by_tipo = {item.get("Tipo Zapata", item.get("Z", "")): item for item in tabla_zapatas}

        # Cargar plantilla oficial CADDIES
        import os
        template_names = ["template_caddies_base.dxf", "template_details_caddies.dxf"]
        template_path = None
        for tname in template_names:
            p = os.path.join(os.path.dirname(__file__), tname)
            if os.path.exists(p):
                template_path = p
                break

        if template_path:
            try:
                self.doc = ezdxf.readfile(template_path)
                self.has_template = True
            except Exception:
                self.doc = ezdxf.new("R2010", setup=True)
                self.has_template = False
        else:
            self.doc = ezdxf.new("R2010", setup=True)
            self.has_template = False

        self.doc.header["$INSUNITS"] = 6       # 6 = Metros
        self.doc.header["$MEASUREMENT"] = 1    # 1 = Métrico
        self.msp = self.doc.modelspace()

        self._setup_layers()
        self._setup_dimstyle()

    def _setup_layers(self):
        """Configura la tabla de capas profesional con colores y pesos estándar."""
        layers = [
            ("EJES", 1, "CENTER", 15),
            ("COTAS", 3, "CONTINUOUS", 18),
            ("ZAPATAS", 4, "CONTINUOUS", 35),
            ("ZAP.ASI", 2, "CONTINUOUS", 35),          # Amarillo CADDIES
            ("DADOS_Y_COLUMNAS", 2, "CONTINUOUS", 40),
            ("DADO", 5, "CONTINUOUS", 40),             # Azul CADDIES
            ("TEXTOS", 7, "CONTINUOUS", 20),
            ("TEXTO", 7, "CONTINUOUS", 20),
            ("0-TEXTO", 7, "CONTINUOUS", 18),          # Tabla CADDIES
            ("A-AXIS-LINE", 8, "CENTER", 15),          # Eje CADDIES
            ("A-SYMB-AXIS-LINE", 8, "CENTER", 15),     # Eje CADDIES oficial
            ("A-EJES-CABEZA", 2, "CONTINUOUS", 25),
            ("SYMB-GRID HEAD", 1, "CONTINUOUS", 25),   # Boya CADDIES oficial
            ("A-TEXT-TEXTO EJES", 1, "CONTINUOUS", 20),
            ("A-SYMB-DIM", 2, "CONTINUOUS", 18),       # Cotas CADDIES oficial
            ("ARMADURA", 1, "CONTINUOUS", 35),         # Rojo CADDIES
            ("ESTRUCTURA_CORTE", 1, "CONTINUOUS", 25), # Rojo para armaduras del corte
            ("LINEA_TIERRA", 8, "CONTINUOUS", 35),      # Suelo / Hatch
            ("MING", 7, "CONTINUOUS", 20),
            ("CONT", 7, "CONTINUOUS", 20),
            ("titulos", 1, "CONTINUOUS", 35),
        ]
        for name, color, lt, lw in layers:
            if name not in self.doc.layers:
                try:
                    self.doc.layers.add(name=name, color=color, linetype=lt, lineweight=lw)
                except Exception:
                    pass

    def _setup_dimstyle(self):
        """Asegura que los estilos de cota CADDIES estén en centímetros con 1 decimal y tamaño duplicado."""
        # Asegurar que el estilo de texto DIM100 tenga altura 0.0 para que dimtxt gobierne libremente
        if "DIM100" in self.doc.styles:
            try:
                self.doc.styles.get("DIM100").dxf.height = 0.0
            except Exception:
                pass

        # Configurar variables de encabezado del documento
        try:
            self.doc.header['$DIMLFAC'] = 100.0
            self.doc.header['$DIMDEC'] = 1
            self.doc.header['$DIMZIN'] = 0
            self.doc.header['$DIMDSEP'] = ord('.')
            self.doc.header['$DIMTXT'] = 1.10
            self.doc.header['$DIMASZ'] = 0.56
        except Exception:
            pass

        for sname in ["DIM100", "DIM100VERTICAL"]:
            if sname not in self.doc.dimstyles:
                base_style = "Standard" if "Standard" in self.doc.dimstyles else self.doc.dimstyles[0].dxf.name
                ds = self.doc.dimstyles.duplicate_entry(base_style, sname)
            else:
                ds = self.doc.dimstyles.get(sname)

            ds.dxf.dimtxt = 1.10         # Altura de texto para Planta (grande)
            ds.dxf.dimasz = 0.56         # Tamaño de flecha / tick arquitectónico
            ds.dxf.dimexe = 0.45         # Extensión de línea sobre cota
            ds.dxf.dimexo = 0.30         # Separación desde origen
            ds.dxf.dimgap = 0.25         # Separación entre texto y línea
            ds.dxf.dimlfac = 100.0       # Convierte metros a centímetros (ej. 6.00m -> 600.0cm)
            ds.dxf.dimdec = 1            # Exactamente 1 decimal
            ds.dxf.dimzin = 0            # No suprimir ceros decimales (ej. 600.0, 150.0)
            ds.dxf.dimdsep = ord('.')    # Punto decimal '.'
            ds.dxf.discard('dimrnd')     # Descartar dimrnd para evitar redondeo entero
            ds.dxf.dimclrd = 1           # Línea de cota roja
            ds.dxf.dimclre = 8           # Línea de referencia gris
            ds.dxf.dimclrt = 2           # Texto amarillo
            ds.dxf.dimblk = '_ArchTick'  # Tick arquitectónico CADDIES

        # Estilos específicos para el Corte Transversal (0.60x del tamaño de planta)
        for sname in ["DIM100_CORTE", "DIM100VERTICAL_CORTE"]:
            if sname not in self.doc.dimstyles:
                base_style = "Standard" if "Standard" in self.doc.dimstyles else self.doc.dimstyles[0].dxf.name
                ds = self.doc.dimstyles.duplicate_entry(base_style, sname)
            else:
                ds = self.doc.dimstyles.get(sname)

            ds.dxf.dimtxt = 0.66         # 0.60x de 1.10
            ds.dxf.dimasz = 0.34         # 0.60x de 0.56
            ds.dxf.dimexe = 0.27         # 0.60x de 0.45
            ds.dxf.dimexo = 0.18         # 0.60x de 0.30
            ds.dxf.dimgap = 0.15         # 0.60x de 0.25
            ds.dxf.dimlfac = 100.0       # Convierte metros a centímetros
            ds.dxf.dimdec = 1            # Exactamente 1 decimal
            ds.dxf.dimzin = 0            # No suprimir ceros decimales
            ds.dxf.dimdsep = ord('.')    # Punto decimal '.'
            ds.dxf.discard('dimrnd')     # Descartar dimrnd para evitar redondeo entero
            ds.dxf.dimclrd = 1           # Línea de cota roja
            ds.dxf.dimclre = 8           # Línea de referencia gris
            ds.dxf.dimclrt = 2           # Texto amarillo
            ds.dxf.dimblk = '_ArchTick'  # Tick arquitectónico CADDIES

    def exportar_bytes(self) -> io.BytesIO:
        """
        Ejecuta la generación completa y devuelve un buffer binario io.BytesIO.
        - Orienta la nave horizontalmente.
        - Posiciona la planta en la izquierda y los detalles CADDIES a la derecha sin empalmes.
        - Puebla dinámicamente la tabla ZAPATAS AISLADAS y la nota de suelo q_adm.
        - Centra el viewport y calcula los límites exactos de dibujo (EXTMIN/EXTMAX).
        """
        from ezdxf.math import Matrix44

        model = self.model
        node_to_grp = map_base_nodes_to_groups(model)

        # 1. Coordenadas de base en metros
        base_coords = {}
        for nid in set(getattr(model, 'base_nodes', [])) | set(getattr(model, 'wind_base_nodes', [])):
            if nid in model.nodes and model.nodes[nid][1] == 0.0:
                base_coords[nid] = (model.nodes[nid][0] / 100.0, model.nodes[nid][2] / 100.0)

        for nid, (x, y, z) in model.nodes.items():
            if y == 0.0 and nid not in base_coords:
                base_coords[nid] = (x / 100.0, z / 100.0)

        all_xs = sorted(list(set(round(pt[0], 3) for pt in base_coords.values())))
        all_zs = sorted(list(set(round(pt[1], 3) for pt in base_coords.values())))

        if not all_xs:
            all_xs = [0.0, getattr(model, 'Larm_m', 15.24)]
        if not all_zs:
            all_zs = [0.0, getattr(model, 'Ljoist_m', 12.192)]

        min_x, max_x = min(all_xs), max(all_xs)
        min_z, max_z = min(all_zs), max(all_zs)
        span_x = max_x - min_x
        span_z = max_z - min_z

        # REGLA: Orientar siempre el lado más largo de la nave horizontalmente (Eje X en CAD)
        rotate_90 = (span_z > span_x)

        if rotate_90:
            L_long = span_z
            L_short = span_x
            def to_cad(xm, zm):
                return (zm - min_z, xm - min_x)
            col_x_vals = [z - min_z for z in all_zs]
            col_y_vals = [x - min_x for x in all_xs]
            col_x_labels = [str(i + 1) for i in range(len(all_zs))]
            letras = [chr(65 + i) if i < 26 else f"A{i-25}" for i in range(len(all_xs))]
            col_y_labels = letras
        else:
            L_long = span_x
            L_short = span_z
            def to_cad(xm, zm):
                return (xm - min_x, zm - min_z)
            col_x_vals = [x - min_x for x in all_xs]
            col_y_vals = [z - min_z for z in all_zs]
            letras = [chr(65 + i) if i < 26 else f"A{i-25}" for i in range(len(all_xs))]
            col_x_labels = letras
            col_y_labels = [str(i + 1) for i in range(len(all_zs))]

        X_base = 15.0
        Y_base = 15.0
        e_ext = 3.5

        # Borde derecho de la planta y colocación de detalles a la derecha
        # En la planta: Cotas van primero y boyas van por fuera (boyas al doble de tamaño)
        X_bub_right = X_base + L_long + 4.5
        gap_details = 8.0
        X_det_start = X_bub_right + gap_details
        Y_det_start = max(Y_base - 2.0, Y_base + (L_short - 22.0) / 2.0)

        # 2. Desplazar los detalles CADDIES que ya existen en el template
        orig_det_min_x = 2211.402
        orig_det_min_y = 1632.582
        dx_det = X_det_start - orig_det_min_x
        dy_det = Y_det_start - orig_det_min_y

        m_trans = Matrix44.translate(dx_det, dy_det, 0)
        for e in list(self.msp):
            try:
                e.transform(m_trans)
            except Exception:
                pass

        # 3. Actualizar Nota 5 (Capacidad Admisible q_adm) con salto de línea limpio
        t_nota5 = None
        for t in self.msp.query('TEXT'):
            if "5.- LA RESISTENCIA" in t.dxf.text:
                self.msp.delete_entity(t)
            elif "PARA ZAPATAS AISLADAS" in t.dxf.text:
                t_nota5 = t

        if t_nota5:
            t_nota5.dxf.text = f"5.- CAPACIDAD DE CARGA ADMISIBLE DEL SUELO ES DE {self.q_adm:.1f} Ton/M2"
            self.msp.add_text(
                "    PARA ZAPATAS AISLADAS.",
                dxfattribs={
                    'layer': t_nota5.dxf.layer,
                    'style': t_nota5.dxf.style,
                    'height': t_nota5.dxf.height,
                    'insert': (t_nota5.dxf.insert.x, t_nota5.dxf.insert.y - 0.22, 0.0)
                }
            )

        # 4. Poblar dinámicamente la tabla ZAPATAS AISLADAS
        table_top_y = 1637.80 + dy_det
        for e in list(self.msp):
            t = e.dxftype()
            if t in ('TEXT', 'MTEXT'):
                ins = e.dxf.insert
                if (2220 + dx_det) <= ins.x <= (2238 + dx_det) and ins.y < (table_top_y - 0.05):
                    self.msp.delete_entity(e)
            elif t == 'LINE' and e.dxf.layer == '0-TEXTO':
                if abs(e.dxf.start.y - e.dxf.end.y) < 0.05 and e.dxf.start.y < (table_top_y - 0.05):
                    self.msp.delete_entity(e)
                elif abs(e.dxf.start.x - e.dxf.end.x) < 0.05 and e.dxf.start.y >= (1638.30 + dy_det):
                    e.dxf.end = (e.dxf.end.x, table_top_y, e.dxf.end.z)
            elif t == 'LWPOLYLINE':
                # Eliminar subrayado residual viejo del título bajo la tabla
                pts = list(e.get_points())
                if len(pts) == 2 and (2223 + dx_det) <= pts[0][0] <= (2236 + dx_det) and pts[0][1] < (table_top_y - 0.05):
                    self.msp.delete_entity(e)

        col_xs = [
            2221.24 + dx_det, 2223.16 + dx_det, 2224.47 + dx_det, 2225.78 + dx_det,
            2227.09 + dx_det, 2228.40 + dx_det, 2230.63 + dx_det, 2232.85 + dx_det,
            2235.08 + dx_det, 2237.30 + dx_det
        ]
        col_centers = [
            (col_xs[0] + col_xs[1]) / 2.0,
            (col_xs[1] + col_xs[2]) / 2.0,
            (col_xs[2] + col_xs[3]) / 2.0,
            (col_xs[3] + col_xs[4]) / 2.0,
            (col_xs[4] + col_xs[5]) / 2.0,
            (col_xs[5] + col_xs[6]) / 2.0,
            (col_xs[6] + col_xs[7]) / 2.0,
            (col_xs[7] + col_xs[8]) / 2.0,
            (col_xs[8] + col_xs[9]) / 2.0,
        ]

        row_height = 0.50
        curr_y = table_top_y
        total_rows = len(self.tabla_zapatas)

        for row_idx, item in enumerate(self.tabla_zapatas):
            tz = str(item.get("Tipo Zapata", item.get("Z", "Z-1")))
            b_m = float(item.get("B_ancho (m)", item.get("B (m)", 1.50)))
            l_m = float(item.get("L_largo (m)", item.get("L (m)", 1.50)))
            hz_m = float(item.get("Hz_espesor (m)", item.get("Hz (m)", 0.30)))
            dx_m = float(item.get("Dado_x (m)", 0.45))
            p_max = float(item.get("P_max (Ton)", item.get("P_max", 15.0)))
            p_up = float(item.get("P_up (Ton)", item.get("P_uplift", 0.0)))

            # Usar armado calculado en el prediseño si está disponible, o estimarlo
            rfzo_b = item.get("Rfzo_B", item.get("Lecho Inf"))
            rfzo_d = item.get("Rfzo_D", item.get("Lecho Inf"))
            rfzo_x = item.get("Rfzo_X", item.get("Lecho Sup"))
            rfzo_y = item.get("Rfzo_Y", item.get("Lecho Sup"))

            if not rfzo_b or not rfzo_x:
                cb, cd, cx, cy = calcular_refuerzo_estimado(b_m, p_max, p_up=p_up, hz_m=hz_m)
                rfzo_b = rfzo_b or cb
                rfzo_d = rfzo_d or cd
                rfzo_x = rfzo_x or cx
                rfzo_y = rfzo_y or cy

            z_cm = int(round((self.df - hz_m) * 100))
            if z_cm <= 0: z_cm = 80
            b_cm = int(round(b_m * 100))
            d_cm = int(round(l_m * 100))
            h_cm = f"{hz_m * 100:.1f}"

            row_vals = [tz, str(z_cm), str(b_cm), str(d_cm), h_cm, rfzo_b, rfzo_d, rfzo_x, rfzo_y]

            bot_y = curr_y - row_height
            mid_y = curr_y - row_height / 2.0

            # Línea horizontal divisoria entre filas (omitir en la última fila para que el borde redondeado sea el extremo limpio)
            if row_idx < total_rows - 1:
                self.msp.add_line((col_xs[0], bot_y), (col_xs[-1], bot_y), dxfattribs={'layer': '0-TEXTO'})

            # Textos centrados
            for val, cx in zip(row_vals, col_centers):
                self.msp.add_text(
                    val,
                    dxfattribs={
                        'layer': 'TEXTO',
                        'height': 0.22,
                        'insert': (cx, mid_y),
                        'align_point': (cx, mid_y),
                        'halign': 1,
                        'valign': 2
                    }
                )
            curr_y = bot_y

        # Líneas verticales interiores de columnas (no extender hasta el borde final redondeado para no intersectar la curva)
        v_end_y = curr_y + 0.10
        for x in col_xs[1:-1]:
            self.msp.add_line((x, table_top_y), (x, v_end_y), dxfattribs={'layer': '0-TEXTO'})

        # Actualizar borde exterior redondeado de la tabla para que coincida exactamente con la última fila
        table_border_poly = None
        for e in self.msp:
            if e.dxftype() == 'LWPOLYLINE' and e.dxf.layer == '0-TEXTO' and e.is_closed:
                table_border_poly = e
                break

        if table_border_poly:
            x_min_p = 2221.2446 + dx_det
            x_max_p = 2237.3034 + dx_det
            y_top_p = 1638.7790 + dy_det
            y_bot_p = curr_y
            r = 0.30
            bulge = 0.4142135623730951
            new_border_pts = [
                (x_min_p + r, y_bot_p, 0.0, 0.0, 0.0),
                (x_max_p - r, y_bot_p, 0.0, 0.0, bulge),
                (x_max_p, y_bot_p + r, 0.0, 0.0, 0.0),
                (x_max_p, y_top_p - r, 0.0, 0.0, bulge),
                (x_max_p - r, y_top_p, 0.0, 0.0, 0.0),
                (x_min_p + r, y_top_p, 0.0, 0.0, bulge),
                (x_min_p, y_top_p - r, 0.0, 0.0, 0.0),
                (x_min_p, y_bot_p + r, 0.0, 0.0, bulge),
            ]
            table_border_poly.set_points(new_border_pts, format='xyseb')

        # Título 'ZAPATA AISLADAS' formateado IDÉNTICO a 'DETALLE DE NIVEL DE DESPLANTE'
        # y más separado de la tabla hacia abajo (mayor margen)
        y_title_zap = curr_y - 1.15
        y_line_zap = y_title_zap - 0.11
        y_sin_escala = y_title_zap - 0.40
        title_x = col_xs[0]
        title_x_end = col_xs[-1]

        self.msp.add_text(
            "ZAPATA AISLADAS",
            dxfattribs={
                'layer': 'ARMADURA',
                'color': 256,
                'style': 'BOLD' if 'BOLD' in self.doc.styles else 'Standard',
                'height': 0.50,
                'insert': (title_x, y_title_zap)
            }
        )
        # Línea de subrayado idéntica (layer '0', color 256)
        self.msp.add_lwpolyline(
            [(title_x, y_line_zap), (title_x_end, y_line_zap)],
            dxfattribs={'layer': '0', 'color': 256}
        )
        # Texto 'SIN ESCALA' exactamente como el de Detalle de Desplante
        self.msp.add_text(
            "SIN ESCALA",
            dxfattribs={
                'layer': 'titulos',
                'color': 7,
                'style': 'TEXT' if 'TEXT' in self.doc.styles else ('SIMPLEX' if 'SIMPLEX' in self.doc.styles else 'Standard'),
                'height': 0.20,
                'insert': (title_x_end - 2.50, y_sin_escala)
            }
        )

        # ----------------------------------------------------------------------
        # 5. DIBUJAR PLANTA DE CIMENTACIÓN
        # ----------------------------------------------------------------------
        has_bubble_block = ("SIMB CABEZA EJES V1.3" in self.doc.blocks) or ("CABEZA EJES" in self.doc.blocks)
        bubble_block_name = "SIMB CABEZA EJES V1.3" if "SIMB CABEZA EJES V1.3" in self.doc.blocks else "CABEZA EJES"

        def _insertar_boya_cad(x_pos: float, y_pos: float, label: str):
            """Inserta boya de eje visible con escala profesional adecuada (ejes al doble de tamaño)."""
            if has_bubble_block:
                bref = self.msp.add_blockref(
                    bubble_block_name,
                    (x_pos, y_pos),
                    dxfattribs={"xscale": 360.0, "yscale": 360.0, "layer": "SYMB-GRID HEAD"}
                )
                bref.add_auto_attribs({"NO.EJE": str(label)})
            else:
                self.msp.add_circle((x_pos, y_pos), 1.50, dxfattribs={"layer": "SYMB-GRID HEAD", "color": 1})
                self.msp.add_text(
                    str(label),
                    dxfattribs={
                        "layer": "SYMB-GRID HEAD",
                        "color": 2,
                        "height": 1.10,
                        "insert": (x_pos, y_pos),
                        "align_point": (x_pos, y_pos),
                        "halign": 1,
                        "valign": 2
                    }
                )

        # ----------------------------------------------------------------------
        # ORDEN DE COTAS Y BOYAS EN PLANTA:
        # Las cotas van primero (cerca del edificio) y las boyas van por fuera.
        # ----------------------------------------------------------------------
        # Posiciones verticales para cotas y boyas (CAD Y)
        # Espaciado generoso para acomodar cotas y boyas ampliadas (ejes dobles)
        y_cota_parc_top = Y_base + L_short + 3.2
        y_cota_tot_top = y_cota_parc_top + 3.0
        y_bub_top = y_cota_tot_top + 4.0

        y_cota_parc_bot = Y_base - 3.2
        y_bub_bot = y_cota_parc_bot - 4.0

        # Posiciones horizontales para cotas y boyas (CAD X)
        x_cota_parc_left = X_base - 3.2
        x_cota_tot_left = x_cota_parc_left - 3.0
        x_bub_left = x_cota_tot_left - 4.0

        x_bub_right = X_base + L_long + 4.5

        # Ejes Verticales (a lo largo de CAD X, líneas van de y_bub_bot a y_bub_top)
        for x_rel, lbl in zip(col_x_vals, col_x_labels):
            x_pos = X_base + x_rel
            self.msp.add_line(
                (x_pos, y_bub_bot),
                (x_pos, y_bub_top),
                dxfattribs={'layer': 'A-SYMB-AXIS-LINE', 'color': 8, 'linetype': 'CENTER'}
            )
            # Boyas exteriores superior e inferior
            _insertar_boya_cad(x_pos, y_bub_top, lbl)
            _insertar_boya_cad(x_pos, y_bub_bot, lbl)

        # Ejes Horizontales (a lo largo de CAD Y, líneas van de x_bub_left a x_bub_right)
        for y_rel, lbl in zip(col_y_vals, col_y_labels):
            y_pos = Y_base + y_rel
            self.msp.add_line(
                (x_bub_left, y_pos),
                (x_bub_right, y_pos),
                dxfattribs={'layer': 'A-SYMB-AXIS-LINE', 'color': 8, 'linetype': 'CENTER'}
            )
            # Boyas exteriores izquierda y derecha
            _insertar_boya_cad(x_bub_left, y_pos, lbl)
            _insertar_boya_cad(x_bub_right, y_pos, lbl)

        # Cotas Superiores: Parciales primero, Totales después (en cm con 1 decimal)
        for i in range(len(col_x_vals) - 1):
            x1 = X_base + col_x_vals[i]
            x2 = X_base + col_x_vals[i + 1]
            try:
                dim = self.msp.add_linear_dim(
                    base=(x1, y_cota_parc_top),
                    p1=(x1, Y_base + L_short),
                    p2=(x2, Y_base + L_short),
                    dimstyle="DIM100",
                    dxfattribs={"layer": "A-SYMB-DIM"}
                )
                dim.render()
            except Exception:
                pass

        try:
            dim_tot_top = self.msp.add_linear_dim(
                base=(X_base, y_cota_tot_top),
                p1=(X_base, Y_base + L_short),
                p2=(X_base + L_long, Y_base + L_short),
                dimstyle="DIM100",
                dxfattribs={"layer": "A-SYMB-DIM"}
            )
            dim_tot_top.render()
        except Exception:
            pass

        # Cotas Inferiores Parciales (en cm con 1 decimal)
        for i in range(len(col_x_vals) - 1):
            x1 = X_base + col_x_vals[i]
            x2 = X_base + col_x_vals[i + 1]
            try:
                dim = self.msp.add_linear_dim(
                    base=(x1, y_cota_parc_bot),
                    p1=(x1, Y_base),
                    p2=(x2, Y_base),
                    dimstyle="DIM100",
                    dxfattribs={"layer": "A-SYMB-DIM"}
                )
                dim.render()
            except Exception:
                pass

        # Cotas Izquierdas (Verticales DIM100VERTICAL en cm con 1 decimal)
        for i in range(len(col_y_vals) - 1):
            y1 = Y_base + col_y_vals[i]
            y2 = Y_base + col_y_vals[i + 1]
            try:
                dim = self.msp.add_linear_dim(
                    base=(x_cota_parc_left, y1),
                    p1=(X_base, y1),
                    p2=(X_base, y2),
                    angle=90,
                    dimstyle="DIM100VERTICAL",
                    dxfattribs={"layer": "A-SYMB-DIM"}
                )
                dim.render()
            except Exception:
                pass

        try:
            dim_tot_left = self.msp.add_linear_dim(
                base=(x_cota_tot_left, Y_base),
                p1=(X_base, Y_base),
                p2=(X_base, Y_base + L_short),
                angle=90,
                dimstyle="DIM100VERTICAL",
                dxfattribs={"layer": "A-SYMB-DIM"}
            )
            dim_tot_left.render()
        except Exception:
            pass

        # Inserción de Zapatas y Dados
        inserted_pos = set()
        for nid, (xm, zm) in base_coords.items():
            xc_rel, yc_rel = to_cad(xm, zm)
            xc = X_base + xc_rel
            yc = Y_base + yc_rel

            pos_key = (round(xc, 2), round(yc, 2))
            if pos_key in inserted_pos:
                continue
            inserted_pos.add(pos_key)

            grp = node_to_grp.get(nid, "C-1")
            zap_info = self.zap_by_grp.get(grp, self.tabla_zapatas[0] if self.tabla_zapatas else None)
            tipo_z = zap_info["Tipo Zapata"] if zap_info else "Z-1"
            b_val = float(zap_info.get("B_ancho (m)", 1.50)) if zap_info else 1.50
            l_val = float(zap_info.get("L_largo (m)", 1.50)) if zap_info else 1.50
            dx_val = float(zap_info.get("Dado_x (m)", 0.45)) if zap_info else 0.45
            dz_val = float(zap_info.get("Dado_z (m)", 0.45)) if zap_info else 0.45

            if rotate_90:
                b_cad = l_val
                l_cad = b_val
                dx_cad = dz_val
                dz_cad = dx_val
            else:
                b_cad = b_val
                l_cad = l_val
                dx_cad = dx_val
                dz_cad = dz_val

            # Contorno de zapata (Amarillo Capa ZAP.ASI)
            hb, hl = b_cad / 2.0, l_cad / 2.0
            self.msp.add_lwpolyline(
                [(xc - hb, yc - hl), (xc + hb, yc - hl), (xc + hb, yc + hl), (xc - hb, yc + hl)],
                close=True,
                dxfattribs={'layer': 'ZAP.ASI', 'color': 2}
            )

            # Contorno de dado (Azul Capa DADO)
            hdx, hdz = dx_cad / 2.0, dz_cad / 2.0
            self.msp.add_lwpolyline(
                [(xc - hdx, yc - hdz), (xc + hdx, yc - hdz), (xc + hdx, yc + hdz), (xc - hdx, yc + hdz)],
                close=True,
                dxfattribs={'layer': 'DADO', 'color': 5}
            )

            # Cruz de centro del dado
            cross_ext = min(b_cad, l_cad) * 0.18
            self.msp.add_line((xc - cross_ext, yc), (xc + cross_ext, yc), dxfattribs={'layer': 'DADO', 'color': 5})
            self.msp.add_line((xc, yc - cross_ext), (xc, yc + cross_ext), dxfattribs={'layer': 'DADO', 'color': 5})

            # Etiquetas de texto D-1 y Z-1 / Z-2...
            self.msp.add_text(
                "D-1",
                dxfattribs={
                    'layer': 'DADO',
                    'color': 5,
                    'height': 0.32,
                    'insert': (xc + hb + 0.15, yc + 0.15)
                }
            )
            self.msp.add_text(
                tipo_z,
                dxfattribs={
                    'layer': 'ZAP.ASI',
                    'color': 2,
                    'height': 0.32,
                    'insert': (xc + hb + 0.15, yc - 0.25)
                }
            )

        # Sello central PRELIMINAR
        center_x = X_base + L_long / 2.0
        center_y = Y_base + L_short / 2.0
        if "SELLO PRELIMINAR" in self.doc.blocks:
            self.msp.add_blockref(
                "SELLO PRELIMINAR",
                (center_x, center_y),
                dxfattribs={'xscale': 53.21, 'yscale': 53.21, 'layer': 'ARMADURA', 'color': 1}
            )

        # Título PLANTA DE CIMENTACION con subrayado doble rojo y blanco
        title_x = X_base
        title_y = y_bub_bot - 4.2
        self.msp.add_text(
            "PLANTA DE CIMENTACION",
            dxfattribs={
                'layer': 'ARMADURA',
                'color': 1,
                'style': 'BOLD' if 'BOLD' in self.doc.styles else 'Standard',
                'height': 0.75,
                'insert': (title_x, title_y)
            }
        )
        self.msp.add_line((title_x, title_y - 0.25), (title_x + 16.0, title_y - 0.25), dxfattribs={'layer': 'ARMADURA', 'color': 1, 'lineweight': 35})
        self.msp.add_line((title_x, title_y - 0.50), (title_x + 16.0, title_y - 0.50), dxfattribs={'layer': '0', 'color': 7, 'lineweight': 15})
        self.msp.add_text(
            "ESCALA 1:100",
            dxfattribs={
                'layer': 'TEXTO',
                'color': 7,
                'height': 0.35,
                'insert': (title_x, title_y - 1.2)
            }
        )

        # ----------------------------------------------------------------------
        # 6. DIBUJAR CORTE TRANSVERSAL - MARCO TIPO (Bajo la Planta)
        # ----------------------------------------------------------------------
        idx_frame = len(model.frames) // 2 if hasattr(model, 'frames') and model.frames else 0
        z_mid = model.frames[idx_frame]['z'] if hasattr(model, 'frames') and model.frames else 0.0
        f_nodes = [
            model.nodes[nid] for mid, (nA, nB) in model.members.items()
            for nid in (nA, nB)
            if abs(model.nodes[nA][2] - z_mid) < 2.0 and abs(model.nodes[nB][2] - z_mid) < 2.0
        ]
        max_roof_h = max((pt[1] / 100.0 for pt in f_nodes), default=12.0)

        # Situar ground_y_corte dinámicamente con gap limpio de 4.5m entre títulos y boyas
        ground_y_corte = (title_y - 2.0) - (max_roof_h + 4.5 + 4.5)

        self.dibujar_corte_transversal(X_base, ground_y_corte, _insertar_boya_cad, all_xs)

        # ----------------------------------------------------------------------
        # 7. ENVOLVENTE Y ENFOQUE VPORT
        # ----------------------------------------------------------------------
        min_gx = min_gy = 1e9
        max_gx = max_gy = -1e9

        for e in self.msp:
            t = e.dxftype()
            pts = []
            if hasattr(e.dxf, 'insert'):
                pts.append((e.dxf.insert.x, e.dxf.insert.y))
            if hasattr(e.dxf, 'start') and hasattr(e.dxf, 'end'):
                pts.extend([(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)])
            if hasattr(e.dxf, 'defpoint'):
                pts.append((e.dxf.defpoint.x, e.dxf.defpoint.y))
            if hasattr(e.dxf, 'center'):
                pts.append((e.dxf.center.x, e.dxf.center.y))
            if t == 'LWPOLYLINE':
                pts.extend([(p[0], p[1]) for p in e.get_points()])
            if t == 'LEADER' and hasattr(e, 'vertices') and e.vertices:
                pts.extend([(v[0], v[1]) for v in e.vertices])
            for px, py in pts:
                min_gx = min(min_gx, px)
                min_gy = min(min_gy, py)
                max_gx = max(max_gx, px)
                max_gy = max(max_gy, py)

        if min_gx < max_gx and min_gy < max_gy:
            self.doc.header['$EXTMIN'] = (min_gx - 5.0, min_gy - 5.0, 0.0)
            self.doc.header['$EXTMAX'] = (max_gx + 5.0, max_gy + 5.0, 0.0)
            self.doc.header['$LIMMIN'] = (min_gx - 5.0, min_gy - 5.0)
            self.doc.header['$LIMMAX'] = (max_gx + 5.0, max_gy + 5.0)

            cx = (min_gx + max_gx) / 2.0
            cy = (min_gy + max_gy) / 2.0
            vh = (max_gy - min_gy) * 1.15
            for vp in self.doc.viewports:
                vp.dxf.center = (cx, cy)
                vp.dxf.height = max(vh, 30.0)

        str_buf = io.StringIO()
        self.doc.write(str_buf)
        dxf_bytes = str_buf.getvalue().encode("utf-8")
        return io.BytesIO(dxf_bytes)

    def dibujar_corte_transversal(self, x_start: float, ground_y: float, _insertar_boya_cad, all_xs: List[float]):
        """
        Dibuja el Marco Transversal Estructural (Corte Transversal) de alta fidelidad técnica:
        - Miembros de armadura: cuerdas superior/inferior y celosía (montantes y diagonales) en rojo (color 1, ESTRUCTURA_CORTE).
        - Columnas: perfiles rectangulares verticales en amarillo (color 2, DADOS_Y_COLUMNAS).
        - Línea de tierra: N.P.T. ±0.00 en capa LINEA_TIERRA.
        - Franja de suelo: franja inferior con hatch 'EARTH' (color 8).
        - Ejes verticales y boyas: para TODAS las columnas del marco (ejes A, B, C, D... con boyas ampliadas sobre la cubierta).
        - Cotas verticales en centímetros (1 decimal): altura libre a cuerda inferior, peralte de armadura y altura total.
        - Cotas horizontales en centímetros (1 decimal): claros entre columnas y claro total.
        - Título: 'CORTE TRANSVERSAL - MARCO TIPO' con doble subrayado rojo y blanco.
        """
        model = self.model
        if not hasattr(model, 'frames') or not model.frames:
            return

        idx_frame = len(model.frames) // 2
        frame_target = model.frames[idx_frame]
        z_target = frame_target['z']

        frame_members = [
            mid for mid, (nA, nB) in model.members.items()
            if abs(model.nodes[nA][2] - z_target) < 2.0 and abs(model.nodes[nB][2] - z_target) < 2.0
        ]

        if not frame_members:
            return

        xs_frame = sorted(list(set(model.nodes[nid][0] / 100.0 for mid in frame_members for nid in model.members[mid])))
        min_fx = min(xs_frame)
        max_fx = max(xs_frame)
        span_f = max_fx - min_fx

        def to_corte_cad(xm, ym):
            return (x_start + (xm - min_fx), ground_y + ym)

        # 1. Identificar Columnas del Marco
        col_mids = [mid for mid in frame_members if mid in model.groups.get('_COL', [])]
        col_data = {}  # xm -> {'clear_y': float, 'top_y': float, 'base_nid': int}

        for mid in col_mids:
            nA, nB = model.members[mid]
            xm = round(model.nodes[nA][0] / 100.0, 3)
            yA = round(model.nodes[nA][1] / 100.0, 3)
            yB = round(model.nodes[nB][1] / 100.0, 3)
            if xm not in col_data:
                col_data[xm] = {'clear_y': 0.0, 'top_y': 0.0, 'base_nid': None}
            if min(yA, yB) == 0.0:
                col_data[xm]['clear_y'] = max(yA, yB)
                col_data[xm]['base_nid'] = nA if yA == 0.0 else nB
            else:
                col_data[xm]['top_y'] = max(col_data[xm]['top_y'], max(yA, yB))

        # Garantizar que top_y esté poblado
        for xm in col_data:
            if col_data[xm]['top_y'] <= col_data[xm]['clear_y']:
                h_max = max(
                    (model.nodes[nid][1] / 100.0 for mid in frame_members for nid in model.members[mid] if abs(model.nodes[nid][0] / 100.0 - xm) < 0.15),
                    default=col_data[xm]['clear_y'] + getattr(model, 'HArmad_m', 1.30)
                )
                col_data[xm]['top_y'] = h_max

        sorted_col_xs = sorted(col_data.keys())

        if not sorted_col_xs:
            sorted_col_xs = [min_fx, max_fx]
            col_data[min_fx] = {'clear_y': getattr(model, 'HLibre_m', 9.75), 'top_y': getattr(model, 'HLibre_m', 9.75) + getattr(model, 'HArmad_m', 1.30), 'base_nid': None}
            col_data[max_fx] = {'clear_y': getattr(model, 'HLibre_m', 9.75), 'top_y': getattr(model, 'HLibre_m', 9.75) + getattr(model, 'HArmad_m', 1.30), 'base_nid': None}

        # 2. Dibujar Armadura (Cuerdas y Celosía en Rojo Capa ESTRUCTURA_CORTE)
        for mid in frame_members:
            if mid in col_mids:
                continue
            nA, nB = model.members[mid]
            ptA = model.nodes[nA]
            ptB = model.nodes[nB]
            p1 = to_corte_cad(ptA[0] / 100.0, ptA[1] / 100.0)
            p2 = to_corte_cad(ptB[0] / 100.0, ptB[1] / 100.0)
            self.msp.add_line(p1, p2, dxfattribs={'layer': 'ESTRUCTURA_CORTE', 'color': 1, 'lineweight': 25})

        # 3. Dibujar Columnas (Perfiles en Amarillo Capa DADOS_Y_COLUMNAS)
        w_col = 0.40
        for xm in sorted_col_xs:
            c_info = col_data[xm]
            xc, yc_ground = to_corte_cad(xm, 0.0)
            _, yc_clear = to_corte_cad(xm, c_info['clear_y'])
            _, yc_top = to_corte_cad(xm, c_info['top_y'])

            hw = w_col / 2.0
            self.msp.add_lwpolyline(
                [(xc - hw, yc_ground), (xc + hw, yc_ground), (xc + hw, yc_clear), (xc - hw, yc_clear)],
                close=True,
                dxfattribs={'layer': 'DADOS_Y_COLUMNAS', 'color': 2, 'lineweight': 35}
            )

            if yc_top > yc_clear:
                self.msp.add_line((xc - hw, yc_clear), (xc - hw, yc_top), dxfattribs={'layer': 'DADOS_Y_COLUMNAS', 'color': 2, 'lineweight': 25})
                self.msp.add_line((xc + hw, yc_clear), (xc + hw, yc_top), dxfattribs={'layer': 'DADOS_Y_COLUMNAS', 'color': 2, 'lineweight': 25})

        # 4. Línea de Tierra N.P.T. y Franja de Suelo (Hatch 'EARTH')
        x_left_g = x_start - 3.5
        x_right_g = x_start + span_f + 3.5
        self.msp.add_line((x_left_g, ground_y), (x_right_g, ground_y), dxfattribs={'layer': 'LINEA_TIERRA', 'color': 7, 'lineweight': 35})
        self.msp.add_text(
            "N.P.T. +-0.00",
            dxfattribs={
                'layer': 'LINEA_TIERRA',
                'color': 7,
                'height': 0.35,
                'insert': (x_right_g + 0.3, ground_y + 0.20)
            }
        )

        y_soil_bot = ground_y - 1.20
        soil_pts = [
            (x_left_g + 0.5, ground_y),
            (x_right_g - 0.5, ground_y),
            (x_right_g - 0.5, y_soil_bot),
            (x_left_g + 0.5, y_soil_bot)
        ]
        self.msp.add_lwpolyline(soil_pts, close=True, dxfattribs={'layer': 'LINEA_TIERRA', 'color': 8})
        try:
            hatch = self.msp.add_hatch(color=8, dxfattribs={'layer': 'LINEA_TIERRA'})
            hatch.set_pattern_fill('EARTH', scale=0.35)
            hatch.paths.add_polyline_path(soil_pts, is_closed=True)
        except Exception:
            try:
                hatch = self.msp.add_hatch(color=8, dxfattribs={'layer': 'LINEA_TIERRA'})
                hatch.set_pattern_fill('ANSI31', scale=0.35)
                hatch.paths.add_polyline_path(soil_pts, is_closed=True)
            except Exception:
                pass

        # 5. Ejes y Boyas para TODAS las columnas del marco ("Agregale más ejes", ejes al doble)
        max_frame_top_y = max(col_data[xm]['top_y'] for xm in sorted_col_xs)
        _, y_axis_top_uniform = to_corte_cad(0.0, max_frame_top_y + 4.5)

        for k, xm in enumerate(sorted_col_xs):
            xc, _ = to_corte_cad(xm, 0.0)
            lbl = chr(65 + k) if k < 26 else f"A{k-25}"

            # Línea de eje vertical desde el terreno hasta la altura uniforme
            self.msp.add_line(
                (xc, ground_y),
                (xc, y_axis_top_uniform),
                dxfattribs={'layer': 'A-SYMB-AXIS-LINE', 'color': 8, 'linetype': 'CENTER'}
            )
            # Boya exterior alineada horizontalmente (doble tamaño)
            _insertar_boya_cad(xc, y_axis_top_uniform + 1.45, lbl)

        # 6. Cotas Verticales en Centímetros (1 decimal) con DIM100VERTICAL_CORTE (0.60x)
        # Separación adecuada de las columnas para evitar empalmes
        # Columna Izquierda Exterior
        xm_left = sorted_col_xs[0]
        xc_left, _ = to_corte_cad(xm_left, 0.0)
        c_left = col_data[xm_left]
        yc_clear_l = ground_y + c_left['clear_y']
        yc_top_l = ground_y + c_left['top_y']

        try:
            dim_hl = self.msp.add_linear_dim(
                base=(xc_left - 2.8, ground_y),
                p1=(xc_left, ground_y),
                p2=(xc_left, yc_clear_l),
                angle=90,
                dimstyle="DIM100VERTICAL_CORTE",
                dxfattribs={"layer": "A-SYMB-DIM"}
            )
            dim_hl.render()
        except Exception:
            pass

        try:
            dim_harm = self.msp.add_linear_dim(
                base=(xc_left - 2.8, yc_clear_l),
                p1=(xc_left, yc_clear_l),
                p2=(xc_left, yc_top_l),
                angle=90,
                dimstyle="DIM100VERTICAL_CORTE",
                dxfattribs={"layer": "A-SYMB-DIM"}
            )
            dim_harm.render()
        except Exception:
            pass

        try:
            dim_htot = self.msp.add_linear_dim(
                base=(xc_left - 4.6, ground_y),
                p1=(xc_left, ground_y),
                p2=(xc_left, yc_top_l),
                angle=90,
                dimstyle="DIM100VERTICAL_CORTE",
                dxfattribs={"layer": "A-SYMB-DIM"}
            )
            dim_htot.render()
        except Exception:
            pass

        # Columnas Interiores: cota de altura libre separada para no empalmar
        for xm in sorted_col_xs[1:-1]:
            xc, _ = to_corte_cad(xm, 0.0)
            yc_c = ground_y + col_data[xm]['clear_y']
            try:
                dim_int = self.msp.add_linear_dim(
                    base=(xc + 2.0, ground_y),
                    p1=(xc, ground_y),
                    p2=(xc, yc_c),
                    angle=90,
                    dimstyle="DIM100VERTICAL_CORTE",
                    dxfattribs={"layer": "A-SYMB-DIM"}
                )
                dim_int.render()
            except Exception:
                pass

        # Columna Derecha Exterior
        xm_right = sorted_col_xs[-1]
        xc_right, _ = to_corte_cad(xm_right, 0.0)
        c_right = col_data[xm_right]
        yc_clear_r = ground_y + c_right['clear_y']
        yc_top_r = ground_y + c_right['top_y']

        try:
            dim_hr = self.msp.add_linear_dim(
                base=(xc_right + 2.8, ground_y),
                p1=(xc_right, ground_y),
                p2=(xc_right, yc_clear_r),
                angle=90,
                dimstyle="DIM100VERTICAL_CORTE",
                dxfattribs={"layer": "A-SYMB-DIM"}
            )
            dim_hr.render()
        except Exception:
            pass

        try:
            dim_harm_r = self.msp.add_linear_dim(
                base=(xc_right + 2.8, yc_clear_r),
                p1=(xc_right, yc_clear_r),
                p2=(xc_right, yc_top_r),
                angle=90,
                dimstyle="DIM100VERTICAL_CORTE",
                dxfattribs={"layer": "A-SYMB-DIM"}
            )
            dim_harm_r.render()
        except Exception:
            pass

        try:
            dim_htot_r = self.msp.add_linear_dim(
                base=(xc_right + 4.6, ground_y),
                p1=(xc_right, ground_y),
                p2=(xc_right, yc_top_r),
                angle=90,
                dimstyle="DIM100VERTICAL_CORTE",
                dxfattribs={"layer": "A-SYMB-DIM"}
            )
            dim_htot_r.render()
        except Exception:
            pass

        # 7. Cotas Horizontales de Claros entre Columnas (en Centímetros con DIM100_CORTE)
        y_cota_h_parc = ground_y - 2.5
        for i in range(len(sorted_col_xs) - 1):
            x1, _ = to_corte_cad(sorted_col_xs[i], 0.0)
            x2, _ = to_corte_cad(sorted_col_xs[i + 1], 0.0)
            try:
                dim_sp = self.msp.add_linear_dim(
                    base=(x1, y_cota_h_parc),
                    p1=(x1, ground_y),
                    p2=(x2, ground_y),
                    dimstyle="DIM100_CORTE",
                    dxfattribs={"layer": "A-SYMB-DIM"}
                )
                dim_sp.render()
            except Exception:
                pass

        y_cota_h_tot = y_cota_h_parc - 2.0
        x_first, _ = to_corte_cad(sorted_col_xs[0], 0.0)
        x_last, _ = to_corte_cad(sorted_col_xs[-1], 0.0)
        try:
            dim_sp_tot = self.msp.add_linear_dim(
                base=(x_first, y_cota_h_tot),
                p1=(x_first, ground_y),
                p2=(x_last, ground_y),
                dimstyle="DIM100_CORTE",
                dxfattribs={"layer": "A-SYMB-DIM"}
            )
            dim_sp_tot.render()
        except Exception:
            pass

        # 8. Título del Corte Transversal con Doble Subrayado Rojo y Blanco
        title_corte_y = y_cota_h_tot - 2.8
        self.msp.add_text(
            "CORTE TRANSVERSAL - MARCO TIPO",
            dxfattribs={
                'layer': 'ARMADURA',
                'color': 1,
                'style': 'BOLD' if 'BOLD' in self.doc.styles else 'Standard',
                'height': 0.75,
                'insert': (x_start, title_corte_y)
            }
        )
        self.msp.add_line((x_start, title_corte_y - 0.25), (x_start + 18.0, title_corte_y - 0.25), dxfattribs={'layer': 'ARMADURA', 'color': 1, 'lineweight': 35})
        self.msp.add_line((x_start, title_corte_y - 0.50), (x_start + 18.0, title_corte_y - 0.50), dxfattribs={'layer': '0', 'color': 7, 'lineweight': 15})
        self.msp.add_text(
            "ESCALA 1:100",
            dxfattribs={
                'layer': 'TEXTO',
                'color': 7,
                'height': 0.35,
                'insert': (x_start, title_corte_y - 1.0)
            }
        )

    def exportar(self, file_path: str) -> str:
        """
        Genera el plano completo y lo guarda en disco en la ruta especificada.
        Si el archivo ya está abierto en AutoCAD y bloqueado por Windows (PermissionError),
        genera automáticamente un nombre de versión alternativa disponible (ej. '... (1).dxf')
        sin lanzar excepción y retorna la ruta del archivo efectivamente guardado.
        """
        buf = self.exportar_bytes()
        bytes_data = buf.getvalue()

        # 1. Intentar guardar en la ruta solicitada directamente
        try:
            with open(file_path, "wb") as f:
                f.write(bytes_data)
            return file_path
        except (PermissionError, OSError):
            pass

        # 2. Si está bloqueado por AutoCAD, buscar la siguiente versión disponible
        base_dir = os.path.dirname(os.path.abspath(file_path))
        base_name, ext = os.path.splitext(os.path.basename(file_path))

        for i in range(1, 100):
            cand_name = f"{base_name} ({i}){ext}"
            cand_path = os.path.join(base_dir, cand_name)
            try:
                with open(cand_path, "wb") as f:
                    f.write(bytes_data)
                return cand_path
            except (PermissionError, OSError):
                continue

        # Si tras 100 intentos sigue bloqueado, lanzar error descriptivo
        raise PermissionError(f"No se pudo escribir en '{file_path}' ni en sus versiones incrementales porque están bloqueadas por AutoCAD.")


def abrir_en_autocad(file_path: str) -> bool:
    """
    Abre automáticamente el archivo exportado (.dxf / .dwg) en AutoCAD.
    Prioriza AcLauncher de Autodesk para enviar el archivo a la instancia de
    AutoCAD que ya está abierta sin crear ventanas duplicadas.
    """
    import os, subprocess
    abs_path = os.path.abspath(file_path)

    # 1. Prioridad: AcLauncher oficial de Autodesk (reutiliza la ventana abierta)
    launcher = r"C:\Program Files\Common Files\Autodesk Shared\AcShellEx\AcLauncher.exe"
    if os.path.exists(launcher):
        try:
            subprocess.Popen([launcher, "/O", abs_path])
            return True
        except Exception:
            pass

    # 2. Intentar vía COM si AutoCAD ya está activo
    try:
        import win32com.client
        acad = win32com.client.GetActiveObject("AutoCAD.Application")
        acad.Documents.Open(abs_path)
        acad.Visible = True
        return True
    except Exception:
        pass

    # 3. Fallback a shell open de Windows
    if os.name == 'nt':
        try:
            os.startfile(abs_path)
            return True
        except Exception:
            try:
                subprocess.Popen(['cmd', '/c', 'start', '', abs_path], shell=True)
                return True
            except Exception:
                pass

    # 4. Fallback directo a acad.exe
    for p in [r"C:\Program Files\Autodesk\AutoCAD 2021\acad.exe"]:
        if os.path.exists(p):
            try:
                subprocess.Popen([p, abs_path])
                return True
            except Exception:
                pass
    return False


# ==============================================================================
# PARTE 4: MOTOR DE PREVISUALIZACIÓN INTERACTIVA 2D (PLOTLY)
# ==============================================================================

def generar_figura_previsualizacion_cimentacion(
    model,
    tabla_zapatas: List[Dict[str, Any]],
    view_type: str = "Cimentación Preliminar",
    df_m: float = 1.50
):
    """
    Genera una figura interactiva 2D (Plotly) de alta fidelidad técnica.
    - Orienta siempre el lado más largo de la nave horizontalmente.
    - Separa ampliamente las líneas y boyas de ejes para evitar cualquier empalme con zapatas.
    - Muestra las etiquetas de zapata legibles y centradas.
    """
    import plotly.graph_objects as go

    zap_by_grp = {}
    for item in tabla_zapatas:
        grp = item.get("Grupo Columna", item.get("Grupo", ""))
        tipo = item.get("Tipo Zapata", item.get("Z", "Z-1"))
        if grp:
            zap_by_grp[grp] = item
        zap_by_grp[tipo] = item

    node_to_grp = map_base_nodes_to_groups(model)

    fig = go.Figure()

    is_corte = ("Corte" in view_type or "Marco" in view_type)

    if not is_corte:
        # ----------------------------------------------------------------------
        # CIMENTACIÓN PRELIMINAR (PLANTA 2D)
        # ----------------------------------------------------------------------
        base_coords = {}
        for nid in set(getattr(model, 'base_nodes', [])) | set(getattr(model, 'wind_base_nodes', [])):
            if nid in model.nodes and model.nodes[nid][1] == 0.0:
                base_coords[nid] = (model.nodes[nid][0] / 100.0, model.nodes[nid][2] / 100.0)

        for nid, (x, y, z) in model.nodes.items():
            if y == 0.0 and nid not in base_coords:
                base_coords[nid] = (x / 100.0, z / 100.0)

        all_xs = sorted(list(set(round(pt[0], 3) for pt in base_coords.values())))
        all_zs = sorted(list(set(round(pt[1], 3) for pt in base_coords.values())))

        if not all_xs:
            all_xs = [0.0, getattr(model, 'Larm_m', 15.24)]
        if not all_zs:
            all_zs = [0.0, getattr(model, 'Ljoist_m', 12.192)]

        min_x, max_x = min(all_xs), max(all_xs)
        min_z, max_z = min(all_zs), max(all_zs)

        span_x = max_x - min_x
        span_z = max_z - min_z

        # REGLA: Orientar siempre el lado más largo de la nave horizontalmente
        rotate_90 = (span_z > span_x)

        if rotate_90:
            # Eje horizontal = Z de la nave; Eje vertical = X de la nave
            def to_plot(xm, zm):
                return (zm, xm)
            plot_span_x = span_z
            plot_span_y = span_x
            x_label = "Ejes Longitudinales (Dirección Z Nave - Metros)"
            y_label = "Ejes Transversales (Dirección X Nave - Metros)"
        else:
            # Eje horizontal = X de la nave; Eje vertical = Z de la nave
            def to_plot(xm, zm):
                return (xm, zm)
            plot_span_x = span_x
            plot_span_y = span_z
            x_label = "Ejes Transversales (Dirección X Nave - Metros)"
            y_label = "Ejes Longitudinales (Dirección Z Nave - Metros)"

        # Responsive bubble size according to number of axes
        max_axes = max(len(all_xs), len(all_zs), 1)
        # Scale bubble between 14 and 26 px
        b_size = max(min(int(300 / max_axes), 26), 14)
        b_font_size = max(int(b_size * 0.45), 8)

        # Extensión amplia para las boyas de ejes para que nunca se empalmen con las columnas
        ext_x = max(plot_span_x * 0.12, 5.0)
        ext_y = max(plot_span_y * 0.14, 5.0)

        # 1. Dibujar Ejes de la Nave con boyas
        letras = [chr(65 + i) if i < 26 else f"A{i-25}" for i in range(len(all_xs))]
        
        if rotate_90:
            # Ejes transversales (A, B, C...) son líneas horizontales en Y_plot constante
            for x_val, letra in zip(all_xs, letras):
                yp = x_val
                x_start = min_z - ext_x
                x_end = max_z + ext_x
                fig.add_trace(go.Scatter(
                    x=[x_start, x_end],
                    y=[yp, yp],
                    mode='lines',
                    line=dict(color='#ef4444', width=1.2, dash='dashdot'),
                    hoverinfo='none',
                    showlegend=False
                ))
                for xp in [x_start, x_end]:
                    fig.add_trace(go.Scatter(
                        x=[xp],
                        y=[yp],
                        mode='markers+text',
                        marker=dict(size=b_size, color='#fef08a', line=dict(color='#ca8a04', width=2.0)),
                        text=[letra],
                        textposition='middle center',
                        textfont=dict(size=b_font_size, color='#854d0e', family='Segoe UI, sans-serif'),
                        hoverinfo='text',
                        hovertext=f"Eje {letra}",
                        showlegend=False
                    ))

            # Ejes longitudinales (1, 2, 3...) son líneas verticales en X_plot constante
            for idx, z_val in enumerate(all_zs, 1):
                xp = z_val
                y_start = min_x - ext_y
                y_end = max_x + ext_y
                fig.add_trace(go.Scatter(
                    x=[xp, xp],
                    y=[y_start, y_end],
                    mode='lines',
                    line=dict(color='#ef4444', width=1.2, dash='dashdot'),
                    hoverinfo='none',
                    showlegend=False
                ))
                for yp in [y_start, y_end]:
                    fig.add_trace(go.Scatter(
                        x=[xp],
                        y=[yp],
                        mode='markers+text',
                        marker=dict(size=b_size, color='#fef08a', line=dict(color='#ca8a04', width=2.0)),
                        text=[str(idx)],
                        textposition='middle center',
                        textfont=dict(size=b_font_size, color='#854d0e', family='Segoe UI, sans-serif'),
                        hoverinfo='text',
                        hovertext=f"Eje {idx}",
                        showlegend=False
                    ))
        else:
            # Orientación estándar
            for x_val, letra in zip(all_xs, letras):
                fig.add_trace(go.Scatter(
                    x=[x_val, x_val],
                    y=[min_z - ext_y, max_z + ext_y],
                    mode='lines',
                    line=dict(color='#ef4444', width=1.2, dash='dashdot'),
                    hoverinfo='none',
                    showlegend=False
                ))
                for y_b in [min_z - ext_y, max_z + ext_y]:
                    fig.add_trace(go.Scatter(
                        x=[x_val],
                        y=[y_b],
                        mode='markers+text',
                        marker=dict(size=b_size, color='#fef08a', line=dict(color='#ca8a04', width=2.0)),
                        text=[letra],
                        textposition='middle center',
                        textfont=dict(size=b_font_size, color='#854d0e', family='Segoe UI, sans-serif'),
                        hoverinfo='text',
                        hovertext=f"Eje {letra}",
                        showlegend=False
                    ))

            for idx, z_val in enumerate(all_zs, 1):
                fig.add_trace(go.Scatter(
                    x=[min_x - ext_x, max_x + ext_x],
                    y=[z_val, z_val],
                    mode='lines',
                    line=dict(color='#ef4444', width=1.2, dash='dashdot'),
                    hoverinfo='none',
                    showlegend=False
                ))
                for x_b in [min_x - ext_x, max_x + ext_x]:
                    fig.add_trace(go.Scatter(
                        x=[x_b],
                        y=[z_val],
                        mode='markers+text',
                        marker=dict(size=b_size, color='#fef08a', line=dict(color='#ca8a04', width=2.0)),
                        text=[str(idx)],
                        textposition='middle center',
                        textfont=dict(size=b_font_size, color='#854d0e', family='Segoe UI, sans-serif'),
                        hoverinfo='text',
                        hovertext=f"Eje {idx}",
                        showlegend=False
                    ))

        # 2. Zapatas y Dados
        zap_count = 0
        for nid, (xm, zm) in base_coords.items():
            grp = node_to_grp.get(nid, "C-1")
            info = zap_by_grp.get(grp, tabla_zapatas[0] if tabla_zapatas else {})
            b = float(info.get("B_ancho (m)", info.get("B (m)", 1.50)))
            l = float(info.get("L_largo (m)", info.get("L (m)", 1.50)))
            dx = float(info.get("Dado_x (m)", info.get("Dado X (m)", 0.50)))
            dz = float(info.get("Dado_z (m)", info.get("Dado Z (m)", 0.50)))
            tipo_z = info.get("Tipo Zapata", info.get("Z", "Z-1"))
            hz = float(info.get("Hz_espesor (m)", info.get("Hz (m)", 0.35)))
            p_max = float(info.get("P_max (Ton)", 10.0))

            xp, yp = to_plot(xm, zm)
            # Dimensiones orientadas en el gráfico
            w_box = l if rotate_90 else b
            h_box = b if rotate_90 else l
            d_w = dz if rotate_90 else dx
            d_h = dx if rotate_90 else dz

            # Contorno de Zapata
            fig.add_shape(
                type="rect",
                x0=xp - w_box / 2.0, y0=yp - h_box / 2.0,
                x1=xp + w_box / 2.0, y1=yp + h_box / 2.0,
                line=dict(color="#0284c7", width=1.8),
                fillcolor="rgba(56, 189, 248, 0.22)",
            )

            # Contorno de Dado
            fig.add_shape(
                type="rect",
                x0=xp - d_w / 2.0, y0=yp - d_h / 2.0,
                x1=xp + d_w / 2.0, y1=yp + d_h / 2.0,
                line=dict(color="#d97706", width=1.5),
                fillcolor="rgba(245, 158, 11, 0.38)",
            )

            # Etiqueta legible centrada en la zapata (sin desbordes hacia los ejes)
            fig.add_trace(go.Scatter(
                x=[xp],
                y=[yp],
                mode='markers+text',
                marker=dict(size=4, color='#0284c7'),
                text=[f"<b>{tipo_z}</b><br>{b:.2f}×{l:.2f}"],
                textposition='middle center',
                textfont=dict(size=8.5, color='#0f172a', family='Segoe UI, sans-serif'),
                hoverinfo='text',
                hovertext=(
                    f"<b>Zapata {tipo_z}</b> (Nodo {nid})<br>"
                    f"Grupo: {grp}<br>"
                    f"Dimensiones: {b:.2f} m × {l:.2f} m<br>"
                    f"Espesor Hz: {hz:.2f} m<br>"
                    f"Dado: {dx:.2f} m × {dz:.2f} m<br>"
                    f"P_max: {p_max:.1f} Ton"
                ),
                showlegend=(zap_count == 0),
                name="Zapatas Aisladas"
            ))
            zap_count += 1

        fig.update_layout(
            title=dict(text=""),
            xaxis=dict(title=x_label, zeroline=False, gridcolor="#e2e8f0"),
            yaxis=dict(title=y_label, zeroline=False, gridcolor="#e2e8f0", scaleanchor="x", scaleratio=1),
            plot_bgcolor="#f8fafc",
            paper_bgcolor="#ffffff",
            margin=dict(l=30, r=30, t=10, b=30),
            height=620,
            hovermode='closest'
        )

    else:
        # ----------------------------------------------------------------------
        # CORTE POR MARCO (ELEVACIÓN 2D)
        # ----------------------------------------------------------------------
        idx_frame = len(model.frames) // 2
        frame_target = model.frames[idx_frame]
        z_target = frame_target['z']

        frame_members = [
            mid for mid, (nA, nB) in model.members.items()
            if abs(model.nodes[nA][2] - z_target) < 2.0 and abs(model.nodes[nB][2] - z_target) < 2.0
        ]

        col_bases = []
        for mid in frame_members:
            nA, nB = model.members[mid]
            ptA = model.nodes[nA]
            ptB = model.nodes[nB]
            xA, yA = ptA[0] / 100.0, ptA[1] / 100.0
            xB, yB = ptB[0] / 100.0, ptB[1] / 100.0

            color_bar = "#3b82f6"
            w_bar = 2.0
            if mid in model.groups.get('_COL', []):
                color_bar = "#eab308"
                w_bar = 3.5
            elif mid in model.groups.get('_CS', []) or mid in model.groups.get('_CS_PERIM', []):
                color_bar = "#06b6d4"
                w_bar = 2.5
            elif mid in model.groups.get('_CI', []) or mid in model.groups.get('_CI_PERIM', []):
                color_bar = "#10b981"
                w_bar = 2.5

            fig.add_trace(go.Scatter(
                x=[xA, xB],
                y=[yA, yB],
                mode='lines',
                line=dict(color=color_bar, width=w_bar),
                hoverinfo='none',
                showlegend=False
            ))

            if yA == 0.0: col_bases.append((nA, xA))
            if yB == 0.0: col_bases.append((nB, xB))

        # Línea de tierra N.P.T. y Franja de Suelo
        xs = [pt[0] / 100.0 for pt in model.nodes.values()]
        min_x, max_x = min(xs), max(xs)

        # Franja de Suelo (Hatch/Banda de Soil bajo el nivel de terreno)
        fig.add_shape(
            type="rect",
            x0=min_x - 3.0, y0=-1.20,
            x1=max_x + 3.0, y1=0.0,
            line=dict(color="#94a3b8", width=1.5),
            fillcolor="rgba(148, 163, 184, 0.28)",
            layer="below"
        )

        fig.add_trace(go.Scatter(
            x=[min_x - 3.0, max_x + 3.0],
            y=[0.0, 0.0],
            mode='lines+text',
            line=dict(color='#475569', width=2.5, dash='solid'),
            text=["", "<b>N.P.T. +-0.00</b>"],
            textposition='top right',
            hoverinfo='none',
            showlegend=False
        ))

        # Ejes y Boyas para TODAS las columnas del marco ("Agregale más ejes")
        col_bases = sorted(list(set(col_bases)), key=lambda item: item[1])
        y_max_frame = max(
            (model.nodes[n][1] / 100.0 for mid in frame_members for n in model.members[mid]),
            default=10.0
        )
        y_axis_top_uniform = y_max_frame + 3.5

        # Responsive bubble size for cross section view
        num_corte_axes = max(len(col_bases), 1)
        b_size_corte = max(min(int(260 / num_corte_axes), 28), 16)
        b_font_corte = max(int(b_size_corte * 0.45), 9)

        for idx, (nid, x_col) in enumerate(col_bases):
            lbl = chr(65 + idx) if idx < 26 else f"A{idx-25}"

            # Línea de eje vertical
            fig.add_trace(go.Scatter(
                x=[x_col, x_col],
                y=[0.0, y_axis_top_uniform],
                mode='lines',
                line=dict(color='#ef4444', width=1.2, dash='dashdot'),
                hoverinfo='none',
                showlegend=False
            ))

            # Boya exterior sobre la cubierta
            fig.add_trace(go.Scatter(
                x=[x_col],
                y=[y_axis_top_uniform],
                mode='markers+text',
                marker=dict(size=b_size_corte, color='#fef08a', line=dict(color='#ca8a04', width=2.0)),
                text=[lbl],
                textposition='middle center',
                textfont=dict(size=b_font_corte, color='#854d0e', family='Segoe UI, sans-serif'),
                hoverinfo='text',
                hovertext=f"Eje {lbl} (Columna X={x_col:.2f}m)",
                showlegend=False
            ))

        # Zapatas y Dados en Elevación
        for nid, x_col in col_bases:
            grp = node_to_grp.get(nid, "C-1")
            info = zap_by_grp.get(grp, tabla_zapatas[0] if tabla_zapatas else {})
            b = float(info.get("B_ancho (m)", info.get("B (m)", 1.50)))
            hz = float(info.get("Hz_espesor (m)", info.get("Hz (m)", 0.35)))
            dx = float(info.get("Dado_x (m)", info.get("Dado X (m)", 0.50)))
            tipo_z = info.get("Tipo Zapata", info.get("Z", "Z-1"))

            # Dado
            y_dado_top = 0.10
            y_dado_bot = -(df_m - hz)
            fig.add_shape(
                type="rect",
                x0=x_col - dx / 2.0, y0=y_dado_bot,
                x1=x_col + dx / 2.0, y1=y_dado_top,
                line=dict(color="#d97706", width=1.5),
                fillcolor="rgba(245, 158, 11, 0.4)",
            )

            # Zapata
            y_zap_bot = -df_m
            fig.add_shape(
                type="rect",
                x0=x_col - b / 2.0, y0=y_zap_bot,
                x1=x_col + b / 2.0, y1=y_dado_bot,
                line=dict(color="#0284c7", width=1.8),
                fillcolor="rgba(56, 189, 248, 0.3)",
            )

            fig.add_trace(go.Scatter(
                x=[x_col],
                y=[y_zap_bot - 0.4],
                mode='text',
                text=[f"<b>{tipo_z}</b><br>{b:.2f}m"],
                textposition='bottom center',
                textfont=dict(size=9.5, color='#0f172a'),
                hoverinfo='none',
                showlegend=False
            ))

        fig.update_layout(
            title=dict(text=""),
            xaxis=dict(title="Claro Transversal (Metros)", zeroline=False, gridcolor="#e2e8f0"),
            yaxis=dict(title="Elevación Y (Metros)", zeroline=False, gridcolor="#e2e8f0", scaleanchor="x", scaleratio=1),
            plot_bgcolor="#f8fafc",
            paper_bgcolor="#ffffff",
            margin=dict(l=30, r=30, t=10, b=30),
            height=620,
            hovermode='closest'
        )

    return fig



