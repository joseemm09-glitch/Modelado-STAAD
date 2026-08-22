import sys
import re

with open('app/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update the sidebar layout for Diseño
sidebar_diseno = """    elif panel == "Diseño":
        st.button("⬅ Menú Principal", type="secondary", on_click=go_panel, args=("Main",))
        
        st.markdown("<h3 style='margin-top: 10px; margin-bottom: 30px;'>Diseño Estructural</h3>", unsafe_allow_html=True)
        
        import sys, os
        if os.path.join(os.path.dirname(__file__), 'staad_link') not in sys.path:
            sys.path.append(os.path.join(os.path.dirname(__file__), 'staad_link'))
        from link import check_staad_status
        staad_info = check_staad_status()
        
        if staad_info["status"] == "connected":
            color = "#005cb2" # Blue
            text = f"Sincronizado a modelo:<br><span style='color: #005cb2; font-weight: normal;'>{staad_info['filename']}</span>"
        elif staad_info["status"] == "connected_no_results":
            color = "#d4b106" # Yellow
            text = f"Sincronizado a modelo:<br><span style='color: #005cb2; font-weight: normal;'>{staad_info['filename']}</span>"
        else:
            color = "#ba281b" # Red
            text = "No sincronizado a modelo"
            
        st.markdown(f"<div style='margin-bottom: 20px; font-size: 14px; font-weight: 600;'><span style='color: {color}; font-size: 10px;'>●</span> {text}</div>", unsafe_allow_html=True)
        
        render_siblings_bottom(nav_group2, "Diseño")
"""
content = re.sub(r'    elif panel == "Diseño":\n.*?render_siblings_bottom\(nav_group2, "Diseño"\)', sidebar_diseno, content, flags=re.DOTALL)


# 2. Add time.sleep to "Guardar Archivo"
guardar_btn = """            if st.button("Guardar Archivo .std", type="primary"):
                # Limpiar el nombre del archivo para evitar caracteres inválidos
                clean_name = "".join(c for c in file_name_export if c.isalnum() or c in " ._-").strip()
                if not clean_name.endswith(".std"):
                    clean_name += ".std"
                
                full_path = os.path.join(st.session_state.export_path, clean_name)
                try:
                    with open(full_path, "w", encoding="utf-8") as f:
                        f.write(staad_text)
                    st.success(f"Guardado exitosamente en:\n{full_path}")
                
                    import time
                    time.sleep(1)
                    st.session_state.current_panel = "Diseño"
                    st.rerun()"""
content = re.sub(r'            if st.button\("Guardar Archivo \.std", type="primary"\):.*?(?=                    # Abrir archivo automáticamente)', guardar_btn + '\n\n', content, flags=re.DOTALL)

# 3. Replace the old "if st.session_state.current_panel in ["Diseño", "Catálogo"]:" block with the new one
old_block = r'if st.session_state.current_panel in \["Diseño", "Catálogo"\]:\n.*?else:'

main_diseno = """if st.session_state.current_panel == "Diseño":
    st.title("Naves Industriales STAAD.Pro")
    st.markdown("<div style='color: gray; font-size: 14px; margin-top: -15px; margin-bottom: 30px; margin-left: 5px;'>M.I. José Ramón Márquez Montes</div>", unsafe_allow_html=True)
    
    col_izq, col_der = st.columns([1.2, 1])
    
    with col_izq:
        import sys, os
        if os.path.join(os.path.dirname(__file__), 'staad_link') not in sys.path:
            sys.path.append(os.path.join(os.path.dirname(__file__), 'staad_link'))
        from link import check_staad_status, run_analysis
        
        staad_info = check_staad_status()
        is_disabled = (staad_info["status"] == "disconnected")
        
        col_btn, col_spin = st.columns([1, 2])
        with col_btn:
            if st.button("Correr Análisis ▶", type="primary", disabled=is_disabled):
                st.session_state.is_analyzing = True
        
        if st.session_state.get("is_analyzing", False):
            with col_spin:
                with st.spinner("Corriendo análisis en STAAD.Pro..."):
                    run_analysis()
                st.session_state.is_analyzing = False
                st.rerun()
                
        st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
        
        st.markdown(\"""
        <style>
        div.row-widget.stRadio > div {
            flex-direction: row;
            background-color: #f1f3f6;
            border-radius: 8px;
            padding: 4px;
            display: inline-flex;
            border: 1px solid #d1d5db;
        }
        div.row-widget.stRadio > div > label {
            background-color: transparent;
            padding: 8px 16px;
            border-radius: 6px;
            margin-right: 4px;
            cursor: pointer;
        }
        div.row-widget.stRadio > div > label[data-checked="true"] {
            background-color: white;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        </style>
        \""", unsafe_allow_html=True)
        
        tab_sel = st.radio("Elementos a diseñar", ["Columnas", "Armaduras", "Contravientos"], label_visibility="collapsed")
        
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        if tab_sel == "Columnas":
            st.write("Resultados de columnas (En desarrollo...)")
        elif tab_sel == "Armaduras":
            st.write("Resultados de armaduras (En desarrollo...)")
        else:
            st.write("Resultados de contravientos (En desarrollo...)")

    with col_der:
        st.markdown("<b>Visualizador 3D</b>", unsafe_allow_html=True)
        
        vc1, vc2, vc3, vc4, _ = st.columns([1,1,1,1,2])
        if vc1.button("Iso", key="btn_iso"): st.session_state.d_view = "Iso"
        if vc2.button("Planta", key="btn_planta"): st.session_state.d_view = "Planta"
        if vc3.button("Lat. X", key="btn_latx"): st.session_state.d_view = "LatX"
        if vc4.button("Lat. Z", key="btn_latz"): st.session_state.d_view = "LatZ"
        
        v_cam = st.session_state.get("d_view", "Iso")
        highlight_col = st.session_state.get("highlight_diseno", "Ninguno")
        fig = plot_model(model, show_supports=True, highlight_ids=None)
        
        if v_cam == "Planta":
            camera = dict(eye=dict(x=0, y=2.5, z=0), up=dict(x=0, y=0, z=1))
        elif v_cam == "LatX":
            camera = dict(eye=dict(x=2.5, y=0, z=0), up=dict(x=0, y=1, z=0))
        elif v_cam == "LatZ":
            camera = dict(eye=dict(x=0, y=0, z=2.5), up=dict(x=0, y=1, z=0))
        else:
            camera = dict(eye=dict(x=1.5, y=1.5, z=1.5))
            
        fig.update_layout(
            scene_camera=camera,
            margin=dict(l=0, r=0, b=0, t=0),
            scene=dict(aspectmode='data')
        )
        st.plotly_chart(fig, use_container_width=True, config={'displaylogo': False})

elif st.session_state.current_panel == "Catálogo":
    st.title("Catálogo de Conceptos")
    st.write("En desarrollo...")

else:"""

content = re.sub(old_block, main_diseno, content, flags=re.DOTALL)

with open('app/main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Main refactored.")
