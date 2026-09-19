"""
Interfaz gráfica del Catálogo de Conceptos para Streamlit.
- Vista idéntica en estética y formatos a la pestaña de Diseño Estructural.
- Submenús expandibles en Columnas: Columnas, Plantillas y Anclas.
- Cuantificación paramétrica detallada estilo Excel (Imagen 1) para cada grupo de columnas C-1, C-2...
- Sincronización estricta con STAAD.Pro (0 si no está sincronizado).
- Gráfica de anillos sobria con densidades en franja izquierda y Visualizador 3D a la derecha.
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import sys
import os

from .catalogo_state import (
    compute_catalogo_from_model, 
    calculate_column_group_totals, 
    SOBER_PALETTE
)
from .aisc_loader import (
    get_aisc_db, 
    find_profile, 
    calculate_plantilla, 
    calculate_anclas_default,
    format_profile_mexican_label
)
from .staad_sync import sync_profiles_from_staad
from .excel_exporter import export_catalogo_to_excel
from app.visualizer import plot_model
import app.prediseno as prediseno

# Conexión con módulo de STAAD link
if os.path.join(os.path.dirname(__file__), '..', 'app', 'staad_link') not in sys.path:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app', 'staad_link'))
from link import check_staad_status

def render_sober_donut_chart(catalogo_data):
    """
    Renderiza la gráfica de anillos sobria en la franja izquierda.
    Muestra densidades directamente en las rebanadas (ej. 5.23 kg/m²) y colores azul marino/gris.
    """
    is_sync = catalogo_data["is_synchronized"]
    densidades = catalogo_data["densidades_por_categoria"]
    pesos = catalogo_data["pesos_por_categoria"]
    densidad_total = catalogo_data["densidad_total"]

    labels = []
    values = []
    colors = []
    text_labels = []

    if is_sync and densidad_total > 0:
        for cat, dens in densidades.items():
            if dens > 0:
                labels.append(cat)
                values.append(pesos[cat])
                colors.append(SOBER_PALETTE.get(cat, "#475569"))
                text_labels.append(f"{dens:.2f} kg/m²")
    else:
        labels = ["Sin sincronizar"]
        values = [1]
        colors = ["#cbd5e1"]
        text_labels = ["0.00 kg/m²"]

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.68,
        marker=dict(colors=colors, line=dict(color="#ffffff", width=2)),
        text=text_labels,
        textinfo="text",
        textposition="auto",
        textfont=dict(family="Aptos Display, Segoe UI, sans-serif", size=10, color="#ffffff"),
        hovertemplate="<b>%{label}</b><br>Densidad: <b>%{text}</b><br>Peso: <b>%{value:,.1f} kg</b><extra></extra>",
        sort=False
    )])

    center_html = (
        f"<span style=\"font-family: 'Aptos Display', 'Segoe UI', sans-serif; font-size: 13px; font-weight: 500; color: #64748b;\">Densidad</span><br>"
        f"<span style=\"font-family: 'Aptos Display', 'Segoe UI', sans-serif; font-size: 26px; font-weight: 700; color: #005cb2;\">{densidad_total:.2f}</span><br>"
        f"<span style=\"font-family: 'Aptos Display', 'Segoe UI', sans-serif; font-size: 11px; font-weight: 600; color: #64748b;\">kg/m²</span>"
    )

    fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.08,
            xanchor="center",
            x=0.5,
            font=dict(family="Aptos Display, Segoe UI, sans-serif", size=10, color="#334155")
        ),
        margin=dict(l=5, r=5, t=5, b=25),
        height=260,
        annotations=[dict(
            text=center_html,
            x=0.5, y=0.5,
            font_size=18,
            showarrow=False,
            align="center"
        )]
    )

    return fig

def generate_plantilla_diagram(col_name, perfil, l_col, b_col, l_plan, b_plan, sec_type):
    """
    Genera un diagrama vectorial SVG tipo plano de ingeniería de la placa base (plantilla).
    Muestra la plantilla exterior (+30cm redondeado), la columna interior, cotas y barrenos.
    """
    cx, cy = 250, 150
    max_d = max(l_plan, b_plan, 1.0)
    scale = 175.0 / max_d
    
    pw = l_plan * scale
    ph = b_plan * scale
    px0 = cx - pw / 2
    py0 = cy - ph / 2
    
    cw = l_col * scale
    ch = b_col * scale
    cx0 = cx - cw / 2
    cy0 = cy - ch / 2
    
    # Representación de sección de columna
    if "WD" in str(perfil).upper() or "W" in str(sec_type).upper() or "IPR" in str(sec_type).upper():
        tf = max(4.0, ch * 0.16)
        tw = max(4.0, cw * 0.12)
        col_shape = f'''
            <rect x="{cx0}" y="{cy0}" width="{cw}" height="{tf}" fill="#005cb2" stroke="#0f172a" stroke-width="1.5"/>
            <rect x="{cx0}" y="{cy0+ch-tf}" width="{cw}" height="{tf}" fill="#005cb2" stroke="#0f172a" stroke-width="1.5"/>
            <rect x="{cx-tw/2}" y="{cy0+tf}" width="{tw}" height="{max(2, ch-2*tf)}" fill="#005cb2" stroke="#0f172a" stroke-width="1.5"/>
        '''
    else:
        # Perfil tubular (HSS / OR)
        t_wall = max(4.0, min(cw, ch) * 0.14)
        col_shape = f'''
            <rect x="{cx0}" y="{cy0}" width="{cw}" height="{ch}" rx="4" fill="#005cb2" fill-opacity="0.25" stroke="#005cb2" stroke-width="2.5"/>
            <rect x="{cx0+t_wall}" y="{cy0+t_wall}" width="{max(4, cw-2*t_wall)}" height="{max(4, ch-2*t_wall)}" rx="3" fill="#ffffff" stroke="#005cb2" stroke-width="1.5"/>
        '''

    svg = f'''
    <div style="display: flex; justify-content: center; margin: 12px 0;">
    <svg viewBox="0 0 500 310" width="100%" style="max-width: 520px; height: 300px; background: #ffffff; border: 1.5px solid #cbd5e1; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
        <!-- Ejes de simetría de la placa -->
        <line x1="{cx}" y1="{py0-20}" x2="{cx}" y2="{py0+ph+20}" stroke="#94a3b8" stroke-width="1" stroke-dasharray="5,4"/>
        <line x1="{px0-20}" y1="{cy}" x2="{px0+pw+20}" y2="{cy}" stroke="#94a3b8" stroke-width="1" stroke-dasharray="5,4"/>
        
        <!-- Placa Base / Plantilla -->
        <rect x="{px0}" y="{py0}" width="{pw}" height="{ph}" rx="6" fill="#f8fafc" stroke="#334155" stroke-width="2.5"/>
        
        <!-- Barrenos de anclas estándar en 4 esquinas -->
        <circle cx="{px0+16}" cy="{py0+16}" r="5.5" fill="#ffffff" stroke="#005cb2" stroke-width="2"/>
        <circle cx="{px0+pw-16}" cy="{py0+16}" r="5.5" fill="#ffffff" stroke="#005cb2" stroke-width="2"/>
        <circle cx="{px0+16}" cy="{py0+ph-16}" r="5.5" fill="#ffffff" stroke="#005cb2" stroke-width="2"/>
        <circle cx="{px0+pw-16}" cy="{py0+ph-16}" r="5.5" fill="#ffffff" stroke="#005cb2" stroke-width="2"/>
        
        <!-- Perfil Columna en el centro -->
        {col_shape}
        <text x="{cx}" y="{cy+4}" text-anchor="middle" font-family="'Aptos', 'Segoe UI', sans-serif" font-size="11" font-weight="800" fill="#0f172a">{col_name}</text>
        
        <!-- Cota Superior (Largo Plantilla) -->
        <line x1="{px0}" y1="{py0-12}" x2="{px0+pw}" y2="{py0-12}" stroke="#0284c7" stroke-width="1.5"/>
        <line x1="{px0}" y1="{py0-16}" x2="{px0}" y2="{py0-8}" stroke="#0284c7" stroke-width="1.5"/>
        <line x1="{px0+pw}" y1="{py0-16}" x2="{px0+pw}" y2="{py0-8}" stroke="#0284c7" stroke-width="1.5"/>
        <text x="{cx}" y="{py0-16}" text-anchor="middle" font-family="'Aptos', 'Segoe UI', sans-serif" font-size="12" font-weight="700" fill="#0284c7">{l_plan:.0f} cm</text>
        
        <!-- Cota Lateral Izquierda (Ancho Plantilla) -->
        <line x1="{px0-12}" y1="{py0}" x2="{px0-12}" y2="{py0+ph}" stroke="#0284c7" stroke-width="1.5"/>
        <line x1="{px0-16}" y1="{py0}" x2="{px0-8}" y2="{py0}" stroke="#0284c7" stroke-width="1.5"/>
        <line x1="{px0-16}" y1="{py0+ph}" x2="{px0-8}" y2="{py0+ph}" stroke="#0284c7" stroke-width="1.5"/>
        <text x="{px0-18}" y="{cy+4}" text-anchor="end" font-family="'Aptos', 'Segoe UI', sans-serif" font-size="12" font-weight="700" fill="#0284c7">{b_plan:.0f} cm</text>
        
        <!-- Leyendas Técnicas -->
        <text x="{cx}" y="{py0+ph+20}" text-anchor="middle" font-family="'Aptos', 'Segoe UI', sans-serif" font-size="11" font-weight="600" fill="#334155">Sección Columna: {l_col:.1f} x {b_col:.1f} cm (+30cm por sentido)</text>
        <text x="{cx}" y="{py0+ph+35}" text-anchor="middle" font-family="'Aptos', 'Segoe UI', sans-serif" font-size="11" font-weight="700" fill="#005cb2">Espesor: Placa de 3/16" (e = 4.8 mm &bull; 37.5 kg/m²)</text>
    </svg>
    </div>
    '''
    return svg

def render_compact_column_calculator(c_name, col_state):
    """
    Renderiza la tarjeta ultra-compacta y pequeña para el grupo de columna:
    - Muestra el nombre/descripción tal como saldría en el catálogo: 'Columna C-1 a base de OR 16" x 3/8" Hp=1191.0'.
    - Textboxes muy pequeños para Altura Promedio, Peso Placas y Desperdicio.
    - Selectores de Tipo y Sección integrados limpiamente.
    - Métricas automáticas y botón de confirmación.
    """
    aisc_db = get_aisc_db()

    # Cálculo preliminar para obtener datos de perfil y dimensiones actuales
    perf_val = col_state.get("perfil", "WD14X90")
    perf_lbl = format_profile_mexican_label(perf_val)
    
    # 1. Cabecera compacta
    h_prom_actual = float(col_state.get("altura_promedio_m", col_state.get("altura_modelo_m", 10.51) + col_state.get("desplante_m", 0.10)))
    hp_cm_actual = round(h_prom_actual * 100.0, 1)
    titulo_catalogo = f"Columna {c_name} a base de {perf_lbl} Hp={hp_cm_actual:.1f}"

    st.markdown(
        f"<div style=\"background: #f8fafc; border-left: 3px solid #005cb2; border-radius: 4px; padding: 5px 10px; margin-bottom: 8px; display: flex; align-items: center; justify-content: space-between; border-top: 1px solid #e2e8f0; border-right: 1px solid #e2e8f0; border-bottom: 1px solid #e2e8f0;\">"
        f"<span style=\"font-size: 13px; font-weight: 700; color: #005cb2;\">{titulo_catalogo}</span>"
        f"<span style=\"background: #e0f2fe; color: #0369a1; font-weight: 700; font-size: 11px; padding: 2px 8px; border-radius: 4px;\">"
        f"{col_state.get('total_no', col_state.get('cant', 1))} pzas"
        f"</span>"
        f"</div>",
        unsafe_allow_html=True
    )

    # 2. Fila compacta de Perfil AISC
    col_t1, col_t2, col_t3 = st.columns([1.3, 2.0, 1.1])
    with col_t1:
        sec_types = ["IPR Doble (WD)", "HSS Cuadrada", "HSS Rectangular", "W"]
        curr_type = col_state.get("sec_type", "IPR Doble (WD)")
        idx_type = sec_types.index(curr_type) if curr_type in sec_types else 0
        new_type = st.selectbox("Tipo de Perfil", sec_types, index=idx_type, key=f"sec_type_{c_name}")
        if new_type != curr_type:
            col_state["sec_type"] = new_type

    type_map = {
        "IPR Doble (WD)": "IPR_Doble",
        "HSS Cuadrada": "HSS_Square",
        "HSS Rectangular": "HSS_Rect",
        "W": "W"
    }
    perfiles_disponibles = aisc_db.get(type_map.get(col_state["sec_type"], "IPR_Doble"), [])
    nombres_perfiles = [p["nombre"] for p in perfiles_disponibles]

    with col_t2:
        curr_perf = col_state.get("perfil", nombres_perfiles[0] if nombres_perfiles else "WD14X90")
        if curr_perf not in nombres_perfiles and nombres_perfiles:
            curr_perf = nombres_perfiles[0]
            col_state["perfil"] = curr_perf
        perf_idx = nombres_perfiles.index(curr_perf) if curr_perf in nombres_perfiles else 0
        
        selected_perf = st.selectbox(
            "Sección", 
            nombres_perfiles, 
            index=perf_idx, 
            key=f"perf_sel_{c_name}",
            format_func=lambda x: f"{format_profile_mexican_label(x)} ({x})" if x.startswith("HSS") else x
        )
        
        if selected_perf != col_state.get("perfil"):
            col_state["perfil"] = selected_perf
            p_info = find_profile(selected_perf)
            if p_info:
                col_state["peso_kg_m"] = float(p_info["peso_kg_m"])
                col_state["largo_cm"] = float(p_info.get("largo_cm", 35.0))
                col_state["ancho_cm"] = float(p_info.get("ancho_cm", 35.0))
                lp, bp, _, _ = calculate_plantilla(col_state["largo_cm"], col_state["ancho_cm"])
                col_state["largo_plan_cm"] = lp
                col_state["ancho_plan_cm"] = bp
                a_num, a_peso = calculate_anclas_default(col_state["largo_cm"], col_state["ancho_cm"])
                col_state["anclas_num"] = a_num
                col_state["anclas_peso_kg"] = a_peso

    with col_t3:
        col_state["peso_kg_m"] = st.number_input(
            "Peso (kg/m)",
            min_value=1.0,
            value=float(col_state.get("peso_kg_m", 134.0)),
            step=1.0,
            format="%.2f",
            key=f"peso_ml_{c_name}"
        )

    # 3. Fila de Textboxs muy pequeños: Altura Promedio, Peso Placas, Desperdicio y Cantidad
    st.markdown("<div style='height: 2px;'></div>", unsafe_allow_html=True)
    c_p1, c_p2, c_p3, c_p4 = st.columns([1.2, 1.2, 1.2, 1.0])
    
    with c_p1:
        st.markdown("<div style='font-size: 11px; font-weight: 600; color: #475569;'>Altura Promedio (m)</div>", unsafe_allow_html=True)
        # Altura promedio por defecto tomada de altura del modelo + desplante
        def_h_prom = float(col_state.get("altura_promedio_m", col_state.get("altura_modelo_m", 10.51) + col_state.get("desplante_m", 0.10)))
        col_state["altura_promedio_m"] = st.number_input(
            "Altura Promedio",
            min_value=0.5,
            max_value=40.0,
            value=def_h_prom,
            step=0.10,
            format="%.2f",
            key=f"hprom_{c_name}",
            label_visibility="collapsed"
        )
        # Mantener consistencia con altura_total_col
        col_state["altura_total_col"] = col_state["altura_promedio_m"]
        col_state["hp_cm"] = round(col_state["altura_promedio_m"] * 100.0, 1)

    with c_p2:
        st.markdown("<div style='font-size: 11px; font-weight: 600; color: #475569;'>Peso Placas (kg)</div>", unsafe_allow_html=True)
        col_state["placa_tapon_kg"] = st.number_input(
            "Peso Placas (kg)",
            min_value=0.0,
            max_value=500.0,
            value=float(col_state.get("placa_tapon_kg", 70.0)),
            step=5.0,
            format="%.1f",
            key=f"tapon_{c_name}",
            label_visibility="collapsed"
        )

    with c_p3:
        st.markdown("<div style='font-size: 11px; font-weight: 600; color: #475569;'>Desperdicio (%)</div>", unsafe_allow_html=True)
        col_state["desperdicio_pct"] = st.number_input(
            "Desperdicio (%)",
            min_value=0.0,
            max_value=25.0,
            value=float(col_state.get("desperdicio_pct", 2.0)),
            step=0.5,
            format="%.1f",
            key=f"desp_{c_name}",
            label_visibility="collapsed"
        )

    with c_p4:
        st.markdown("<div style='font-size: 11px; font-weight: 600; color: #475569;'>Cantidad</div>", unsafe_allow_html=True)
        col_state["cant"] = st.number_input(
            "Cantidad",
            min_value=1,
            value=int(col_state.get("cant", col_state.get("total_no", 1))),
            step=1,
            key=f"cant_{c_name}",
            label_visibility="collapsed"
        )

    # 4. Cálculo dinámico de totales
    res = calculate_column_group_totals(col_state)
    
    # 5. Métricas compactas en una sola franja horizontal
    st.markdown(
        f"<div style='display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 6px 10px; margin: 8px 0; text-align: center;'>"
        f"<div><span style='font-size: 10px; color: #64748b; font-weight: 600;'>ALTURA HP</span><br><b style='font-size: 13px; color: #005cb2;'>{res['altura_total_col']:.2f} m</b></div>"
        f"<div><span style='font-size: 10px; color: #1e3a8a; font-weight: 600;'>PESO BASE</span><br><b style='font-size: 13px; color: #1e3a8a;'>{res['peso_columna_base']:,.1f} kg</b></div>"
        f"<div><span style='font-size: 10px; color: #854d0e; font-weight: 600;'>POR COLUMNA</span><br><b style='font-size: 13px; color: #854d0e;'>{res['peso_por_columna']:,.1f} kg</b></div>"
        f"<div><span style='font-size: 10px; color: #9a3412; font-weight: 700;'>TOTAL ({res['total_no']} PZS)</span><br><b style='font-size: 13.5px; color: #9a3412;'>{res['peso_total_grupo']:,.1f} kg</b></div>"
        f"</div>",
        unsafe_allow_html=True
    )

    c_btn, _ = st.columns([1.2, 3.8])
    with c_btn:
        if st.button(f"Guardar {c_name}", key=f"btn_save_{c_name}", type="primary", use_container_width=True):
            st.session_state[f"col_quant_{c_name}"] = col_state
            st.success(f"{c_name} guardado.")
            st.rerun()

def render_catalogo(model):
    """
    Renderiza la interfaz principal del Catálogo de Conceptos.
    """
    # 1. Verificar estado de sincronización con STAAD.Pro idéntico a Diseño
    staad_info = check_staad_status()
    target_file = st.session_state.get("active_staad_file", "")
    is_sync = (
        staad_info["status"] in ["connected", "connected_no_results"] and
        target_file and
        target_file.lower() == str(staad_info["filename"]).lower()
    )

    staad_profiles = st.session_state.get("staad_synced_profiles", {})

    # 2. Computar datos del modelo (si no está sincronizado, todo marca 0)
    cat_data = compute_catalogo_from_model(model, is_synchronized=is_sync, staad_profiles=staad_profiles)

    # 3. Layout en dos columnas: col_izq (2), col_der (1) idéntico a Diseño
    col_izq, col_der = st.columns([2, 1])

    with col_izq:
        # Botón de Sincronización en el mismo estilo de "Correr Análisis ▶"
        col_btn, col_spin = st.columns([1, 2])
        with col_btn:
            if st.button("Sincronizar Modelo ▶", type="primary", disabled=not is_sync):
                with st.spinner("Sincronizando perfiles desde STAAD.Pro..."):
                    sync_res = sync_profiles_from_staad(model)
                    if sync_res["status"] == "success":
                        st.session_state["staad_synced_profiles"] = sync_res["profiles_by_group"]
                        st.session_state["catalogo_last_sync"] = True
                        st.success("Perfiles sincronizados exitosamente.")
                        st.rerun()
                    else:
                        st.warning(sync_res["message"])

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

        # Gráfica de anillos sobria en la franja izquierda
        st.markdown(
            "<div style=\"font-family: 'Aptos Display', sans-serif; font-size: 13px; font-weight: 700; color: #1e293b; margin-bottom: 2px;\">"
            "Densidad por Concepto"
            "</div>",
            unsafe_allow_html=True
        )
        fig_donut = render_sober_donut_chart(cat_data)
        st.plotly_chart(fig_donut, use_container_width=True, config={'displaylogo': False})

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

        # Pestañas limpias sin iconos
        tabs_names = ["Columnas", "Armaduras", "Joists", "Contravientos", "Conexiones", "Cubierta", "Mezanine", "Resumen"]
        t_col, t_arm, t_joi, t_cv, t_cx, t_cub, t_mez, t_res = st.tabs(tabs_names)

        # ─── TAB COLUMNAS (Con Submenús Expanders: Columnas, Plantillas, Anclas) ───
        with t_col:
            if not is_sync:
                st.markdown(
                    "<div style='background-color: #f0f7ff; color: #005cb2; padding: 8px 12px; border-radius: 6px; font-size: 12px; font-weight: 500; margin-bottom: 10px;'>"
                    "● Modo local: Cuantificación basada en la geometría activa. Sincroniza con STAAD.Pro para vincular perfiles calculados."
                    "</div>",
                    unsafe_allow_html=True
                )

            cols_dict = prediseno.clasificar_columnas(model)
            cols_keys = list(sorted(cols_dict.keys()))

            # ── Submenú 1: Columnas ──
            with st.expander("Columnas", expanded=True):
                # 1. Selector horizontal compacto de grupo de columna idéntico al screenshot del usuario
                sel_col_name = st.radio(
                    "Seleccionar Grupo de Columna:",
                    cols_keys,
                    horizontal=True,
                    key="radio_sel_col_quant",
                    format_func=lambda c: f"{c} ({cat_data['columnas_detalle'].get(c, {}).get('total_no', 0)} pzas)",
                    label_visibility="collapsed"
                )

                col_state = cat_data["columnas_detalle"].get(sel_col_name, {})
                
                # Renderizar la tarjeta compacta y pequeña de la columna seleccionada
                render_compact_column_calculator(sel_col_name, col_state)

            # ── Submenú 2: Plantillas ──
            with st.expander("Plantillas", expanded=False):
                plantillas_data = []
                peso_tot_plantillas = 0.0

                for k in cols_keys:
                    col_s = cat_data["columnas_detalle"].get(k, {})
                    cant = col_s.get("total_no", 0)
                    l_p = float(col_s.get("largo_plan_cm", 65.0))
                    b_p = float(col_s.get("ancho_plan_cm", 65.0))
                    p_u = float(col_s.get("peso_unit_plan", 15.84))
                    p_tot = float(col_s.get("peso_plantillas_grupo", round(cant * p_u, 2)))
                    peso_tot_plantillas += p_tot
                    
                    perf_k = col_s.get("perfil", "")
                    perf_lbl = format_profile_mexican_label(perf_k)
                    plantillas_data.append({
                        "Grupo": k,
                        "Perfil": perf_lbl,
                        "Plantilla (cm)": f"{l_p:.0f} × {b_p:.0f}",
                        "Espesor": "3/16\"",
                        "Cant.": cant,
                        "P. Unit. (kg)": f"{p_u:.2f}",
                        "Peso Total (kg)": f"{p_tot:,.1f}"
                    })

                st.dataframe(pd.DataFrame(plantillas_data), use_container_width=True, hide_index=True)
                
                # Ajuste rápido de dimensiones de plantilla
                c_pcol, c_pl, c_pb, c_pbtn = st.columns([1.1, 1.2, 1.2, 1.1])
                with c_pcol:
                    sel_edit_p = st.selectbox("Grupo", cols_keys, key="sel_edit_plan_grp", label_visibility="collapsed")
                curr_col_p = cat_data["columnas_detalle"].get(sel_edit_p, {})
                with c_pl:
                    new_l = st.number_input(
                        "Largo (cm)",
                        min_value=20.0,
                        max_value=200.0,
                        value=float(curr_col_p.get("largo_plan_cm", 65.0)),
                        step=5.0,
                        key=f"inp_lplan_{sel_edit_p}",
                        label_visibility="collapsed"
                    )
                with c_pb:
                    new_b = st.number_input(
                        "Ancho (cm)",
                        min_value=20.0,
                        max_value=200.0,
                        value=float(curr_col_p.get("ancho_plan_cm", 65.0)),
                        step=5.0,
                        key=f"inp_bplan_{sel_edit_p}",
                        label_visibility="collapsed"
                    )
                with c_pbtn:
                    if st.button("Ajustar", key=f"btn_upd_plan_{sel_edit_p}", use_container_width=True):
                        state_k = f"col_quant_{sel_edit_p}"
                        if state_k in st.session_state:
                            st.session_state[state_k]["largo_plan_cm"] = new_l
                            st.session_state[state_k]["ancho_plan_cm"] = new_b
                        else:
                            curr_col_p["largo_plan_cm"] = new_l
                            curr_col_p["ancho_plan_cm"] = new_b
                            st.session_state[state_k] = curr_col_p
                        st.rerun()

                st.markdown(
                    f"<div style='display: flex; justify-content: space-between; font-weight: 700; font-size: 12.5px; color: #005cb2; margin-top: 4px; padding: 5px 10px; background: #f8fafc; border-radius: 4px; border: 1px solid #e2e8f0;'>"
                    f"<span>Criterio: +30 cm / Placa 3/16\" (37.5 kg/m²)</span>"
                    f"<span>TOTAL PLANTILLAS: {peso_tot_plantillas:,.1f} kg</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )

            # ── Submenú 3: Anclas ──
            with st.expander("Anclas", expanded=False):
                c_h1, c_h2, c_h3, c_h4 = st.columns([1.1, 1.4, 1.3, 1.2])
                with c_h1:
                    st.markdown("<span style='font-size: 11px; font-weight: 700; color: #64748b;'>GRUPO</span>", unsafe_allow_html=True)
                with c_h2:
                    st.markdown("<span style='font-size: 11px; font-weight: 700; color: #64748b;'>CAJÓN</span>", unsafe_allow_html=True)
                with c_h3:
                    st.markdown("<span style='font-size: 11px; font-weight: 700; color: #64748b;'>PESO CAJÓN (KG)</span>", unsafe_allow_html=True)
                with c_h4:
                    st.markdown("<span style='font-size: 11px; font-weight: 700; color: #64748b;'>SUBTOTAL</span>", unsafe_allow_html=True)

                peso_tot_anclas = 0.0

                for c_name in cols_keys:
                    col_state = cat_data["columnas_detalle"].get(c_name, {})
                    cant = col_state.get("total_no", 0)
                    
                    ca1, ca2, ca3, ca4 = st.columns([1.1, 1.4, 1.3, 1.2])
                    with ca1:
                        st.markdown(f"<div style='padding-top: 5px; font-weight: 700; font-size: 13px; color: #0369a1;'>{c_name} <span style='font-size: 11px; color: #64748b;'>({cant} cols)</span></div>", unsafe_allow_html=True)
                    with ca2:
                        opt_anclas = [4, 6, 8, 12]
                        curr_a = col_state.get("anclas_num", 8)
                        idx_a = opt_anclas.index(curr_a) if curr_a in opt_anclas else 2
                        col_state["anclas_num"] = st.selectbox(
                            f"Anclas {c_name}", 
                            opt_anclas, 
                            index=idx_a, 
                            key=f"sel_anc_num_{c_name}",
                            format_func=lambda x: f"{x} anclas",
                            label_visibility="collapsed"
                        )
                    with ca3:
                        col_state["anclas_peso_kg"] = st.number_input(
                            f"Peso cajón {c_name}",
                            min_value=18.0,
                            max_value=95.0,
                            value=float(col_state.get("anclas_peso_kg", 80.0)),
                            step=5.0,
                            format="%.1f",
                            key=f"inp_anc_peso_{c_name}",
                            label_visibility="collapsed"
                        )
                    with ca4:
                        sub_anc = round(cant * col_state["anclas_peso_kg"], 1)
                        peso_tot_anclas += sub_anc
                        st.markdown(f"<div style='padding-top: 5px; font-weight: 700; font-size: 13px; color: #0f172a;'>{sub_anc:,.1f} kg</div>", unsafe_allow_html=True)

                st.markdown(
                    f"<div style='text-align: right; font-weight: 700; font-size: 13px; color: #005cb2; margin-top: 4px; padding: 5px 10px; background: #f8fafc; border-radius: 4px; border: 1px solid #e2e8f0;'>"
                    f"TOTAL PESO ANCLAS: {peso_tot_anclas:,.1f} kg"
                    f"</div>",
                    unsafe_allow_html=True
                )

        # ─── TAB ARMADURAS ───
        with t_arm:
            grupos_a = {k: v for k, v in model.groups.items() if (k.startswith('_CS') or k.startswith('_CI')) and len(v) > 0}
            opts_a = list(sorted(grupos_a.keys())) if grupos_a else ["_CS"]
            key_a = "highlight_cat_arm"
            if key_a not in st.session_state or st.session_state[key_a] not in opts_a:
                st.session_state[key_a] = opts_a[0]

            st.write("Seleccionar Grupo:")
            sel_arm = st.radio("Seleccionar Grupo:", opts_a, key=key_a, horizontal=True, label_visibility="collapsed")
            st.session_state["highlight_cat_active"] = sel_arm

            cant_a_elem = len(grupos_a.get(sel_arm, [])) if is_sync else 0
            st.markdown(
                f"<div style='margin-top: 10px; padding: 15px; border-radius: 8px; background-color: #f8f9fa; border: 1px solid #e9ecef;'>",
                unsafe_allow_html=True
            )
            st.markdown(f"**Grupo {sel_arm}** ({cant_a_elem} elementos)")
            if is_sync:
                p_arm = staad_profiles.get(sel_arm) or st.session_state.get(f"sel_{sel_arm}", "2L 3X3X1/4")
                st.write(f"Perfil Asignado: **{p_arm}**")
                st.write(f"Longitud Armadura: **{model.Larm_m:.2f} m**")
                st.metric("Peso Armaduras", f"{cat_data['pesos_por_categoria']['Armaduras']:,.1f} kg")
            else:
                st.markdown(
                    "<div style='background-color: #f0f7ff; color: #005cb2; padding: 12px; border-radius: 6px; font-size: 14px; font-weight: 500; margin-top: 10px;'>"
                    "Sincroniza y corre el análisis para ver los resultados."
                    "</div>",
                    unsafe_allow_html=True
                )
            st.markdown("</div>", unsafe_allow_html=True)

        # ─── TAB JOISTS ───
        with t_joi:
            st.markdown(
                f"<div style='margin-top: 10px; padding: 15px; border-radius: 8px; background-color: #f8f9fa; border: 1px solid #e9ecef;'>",
                unsafe_allow_html=True
            )
            j_cnt = len(model.groups.get("_JOISTGRAL", [])) if is_sync else 0
            st.markdown(f"**Largueros Tipo Joist** ({j_cnt} elementos)")
            if is_sync:
                st.write(f"Longitud de Joist: **{model.Ljoist_m:.2f} m**")
                st.metric("Peso Joists", f"{cat_data['pesos_por_categoria']['Joists']:,.1f} kg")
            else:
                st.markdown(
                    "<div style='background-color: #f0f7ff; color: #005cb2; padding: 12px; border-radius: 6px; font-size: 14px; font-weight: 500; margin-top: 10px;'>"
                    "Sincroniza y corre el análisis para ver los resultados."
                    "</div>",
                    unsafe_allow_html=True
                )
            st.markdown("</div>", unsafe_allow_html=True)

        # ─── TAB CONTRAVIENTOS ───
        with t_cv:
            st.markdown(
                f"<div style='margin-top: 10px; padding: 15px; border-radius: 8px; background-color: #f8f9fa; border: 1px solid #e9ecef;'>",
                unsafe_allow_html=True
            )
            cv_cnt = len(model.groups.get("_CVH", [])) if is_sync else 0
            st.markdown(f"**Contravientos Horizontales** ({cv_cnt} elementos)")
            if is_sync:
                st.metric("Peso Contravientos", f"{cat_data['pesos_por_categoria']['Contravientos']:,.1f} kg")
            else:
                st.markdown(
                    "<div style='background-color: #f0f7ff; color: #005cb2; padding: 12px; border-radius: 6px; font-size: 14px; font-weight: 500; margin-top: 10px;'>"
                    "Sincroniza y corre el análisis para ver los resultados."
                    "</div>",
                    unsafe_allow_html=True
                )
            st.markdown("</div>", unsafe_allow_html=True)

        # ─── TAB CONEXIONES ───
        with t_cx:
            st.markdown(
                f"<div style='margin-top: 10px; padding: 15px; border-radius: 8px; background-color: #f8f9fa; border: 1px solid #e9ecef;'>",
                unsafe_allow_html=True
            )
            st.markdown("**Ángulos y Placas de Conexión**")
            if is_sync:
                st.write("Estimación estándar del **3.0%** sobre peso total de acero.")
                st.metric("Peso Conexiones", f"{cat_data['pesos_por_categoria']['Conexiones']:,.1f} kg")
            else:
                st.markdown(
                    "<div style='background-color: #f0f7ff; color: #005cb2; padding: 12px; border-radius: 6px; font-size: 14px; font-weight: 500; margin-top: 10px;'>"
                    "Sincroniza y corre el análisis para ver los resultados."
                    "</div>",
                    unsafe_allow_html=True
                )
            st.markdown("</div>", unsafe_allow_html=True)

        # ─── TAB CUBIERTA ───
        with t_cub:
            st.markdown(
                f"<div style='margin-top: 10px; padding: 15px; border-radius: 8px; background-color: #f8f9fa; border: 1px solid #e9ecef;'>",
                unsafe_allow_html=True
            )
            st.markdown("**Lámina y Accesorios de Cubierta**")
            if is_sync:
                st.write(f"Área en Planta: **{cat_data['area_m2']:,.1f} m²**")
                st.write("Lámina KR-18 cal. 22 Pintro, Aislante de fibra de vidrio 6\", domos y remates.")
            else:
                st.markdown(
                    "<div style='background-color: #f0f7ff; color: #005cb2; padding: 12px; border-radius: 6px; font-size: 14px; font-weight: 500; margin-top: 10px;'>"
                    "Sincroniza y corre el análisis para ver los resultados."
                    "</div>",
                    unsafe_allow_html=True
                )
            st.markdown("</div>", unsafe_allow_html=True)

        # ─── TAB MEZANINE ───
        with t_mez:
            st.markdown(
                f"<div style='margin-top: 10px; padding: 15px; border-radius: 8px; background-color: #f8f9fa; border: 1px solid #e9ecef;'>",
                unsafe_allow_html=True
            )
            st.markdown("**Mezanine y Estructuras Especiales**")
            if is_sync:
                st.write("Paso de gato para mantenimiento: **50 ml**")
            else:
                st.markdown(
                    "<div style='background-color: #f0f7ff; color: #005cb2; padding: 12px; border-radius: 6px; font-size: 14px; font-weight: 500; margin-top: 10px;'>"
                    "Sincroniza y corre el análisis para ver los resultados."
                    "</div>",
                    unsafe_allow_html=True
                )
            st.markdown("</div>", unsafe_allow_html=True)

        # ─── TAB RESUMEN ───
        with t_res:
            st.markdown(
                f"<div style='margin-top: 10px; padding: 15px; border-radius: 8px; background-color: #f8f9fa; border: 1px solid #e9ecef;'>",
                unsafe_allow_html=True
            )
            st.markdown("**Resumen General de Acero**")
            summary_rows = []
            for cat, w in cat_data["pesos_por_categoria"].items():
                summary_rows.append({
                    "Concepto": cat,
                    "Peso (kg)": f"{w:,.1f}",
                    "Densidad (kg/m²)": f"{cat_data['densidades_por_categoria'][cat]:.2f}",
                    "Participación": f"{cat_data['porcentajes'][cat]:.1f} %"
                })
            summary_rows.append({
                "Concepto": "TOTAL",
                "Peso (kg)": f"{cat_data['peso_total_acero']:,.1f}",
                "Densidad (kg/m²)": f"{cat_data['densidad_total']:.2f}",
                "Participación": "100.0 %" if is_sync else "0.0 %"
            })
            st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)

            if is_sync:
                st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                dummy_export_state = {
                    "metadata": {
                        "proyecto": target_file.replace(".std", "") if target_file else "Nave",
                        "ubicacion": "QUERÉTARO, QRO.",
                        "fecha": "2026-09-16",
                        "elaboro": "ING. ESTRUCTURAL",
                        "porc_conexiones": 3.0
                    },
                    "conceptos": {
                        "columnas": cat_data["conceptos_por_tab"]["Columnas"],
                        "plantillas": cat_data["conceptos_por_tab"]["Plantillas"],
                        "anclas": cat_data["conceptos_por_tab"]["Anclas"],
                        "armaduras": cat_data["conceptos_por_tab"]["Armaduras"],
                        "joists": cat_data["conceptos_por_tab"]["Joists"],
                        "contravientos": cat_data["conceptos_por_tab"]["Contravientos"],
                        "conexiones": cat_data["conceptos_por_tab"]["Conexiones"],
                        "cubierta": cat_data["conceptos_por_tab"]["Cubierta"],
                        "mezanine": cat_data["conceptos_por_tab"]["Mezanine"]
                    }
                }
                dummy_totals = {
                    "area_m2": cat_data["area_m2"],
                    "peso_total_acero": cat_data["peso_total_acero"],
                    "densidad_total": cat_data["densidad_total"],
                    "detalle_items": {it["concepto"]: it.get("peso_total", 0.0) for tab in cat_data["conceptos_por_tab"].values() for it in tab if "concepto" in it},
                    "peso_placas_conex": cat_data["pesos_por_categoria"]["Conexiones"]
                }
                excel_buf = export_catalogo_to_excel(dummy_export_state, dummy_totals)
                st.download_button(
                    "Descargar Catálogo Excel (.xlsx)",
                    data=excel_buf,
                    file_name=f"Catalogo_{target_file.replace('.std', '') if target_file else 'Nave'}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            st.markdown("</div>", unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────────
    # MITAD DERECHA: VISUALIZADOR 3D IDÉNTICO A DISEÑO
    # ─────────────────────────────────────────────────────────────
    with col_der:
        st.markdown("<b>Visualizador 3D</b>", unsafe_allow_html=True)
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

        active_grp = st.session_state.get("highlight_cat_active", "C-1")
        all_grps = {**prediseno.clasificar_columnas(model), **model.groups}
        h_ids = all_grps.get(active_grp, None)

        fig_3d = plot_model(model, show_supports=True, highlight_ids=h_ids)

        is_mobile_client = False
        cam_zoom = 3.6 if is_mobile_client else 1.8
        fig_3d.update_layout(
            scene_camera=dict(eye=dict(x=cam_zoom, y=cam_zoom, z=cam_zoom)),
            margin=dict(l=0, r=0, b=0, t=0),
            scene=dict(aspectmode='data')
        )
        st.plotly_chart(fig_3d, use_container_width=True, config={'displaylogo': False})
