import sys
import re

with open('app/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update render_siblings_bottom
old_render = """def render_siblings_bottom(group, current):
    found = False
    for name in group:
        if found:
            c1, c2, c3 = st.columns([1, 6, 1])
            with c2: st.button(name, type="primary", use_container_width=True, on_click=go_panel, args=(name,), key=f"nav_bot_{name}")
        if name == current: found = True"""

new_render = """def render_siblings_bottom(group, current):
    found = False
    first_bot = True
    for name in group:
        if found:
            if first_bot:
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("<hr style='margin: 0px 0px 10px 0px; border: 0; border-top: 1px solid #e0e0e0;'>", unsafe_allow_html=True)
                first_bot = False
            c1, c2, c3 = st.columns([1, 6, 1])
            with c2: st.button(name, type="primary", use_container_width=True, on_click=go_panel, args=(name,), key=f"nav_bot_{name}")
        if name == current: found = True"""

content = content.replace(old_render, new_render)

# 2. Update Diseño columns and layout
# replace col_izq, col_der = st.columns([1.2, 1]) with [2, 1]
content = content.replace('col_izq, col_der = st.columns([1.2, 1])', 'col_izq, col_der = st.columns([2, 1])')

# 3. Replace the Radio logic with Tabs and helper function
# From `<style> ...  </style>` to the end of `st.markdown("</div>", unsafe_allow_html=True)`
pattern_radio_to_results = r'        st\.markdown\("""\n        <style>\n        div\.row-widget\.stRadio > div \{.*?st\.markdown\("</div>", unsafe_allow_html=True\)'

tabs_logic = """        def render_group_results(tab_name, grupos_dict):
            if not grupos_dict:
                st.info(f"No hay grupos definidos para {tab_name}")
                return
            sel_g = st.radio("Seleccionar Grupo:", list(sorted(grupos_dict.keys())), key=f"highlight_diseno_{tab_name}", horizontal=True)
            st.session_state["highlight_diseno_active"] = sel_g
            m_ids = grupos_dict[sel_g]
            
            st.markdown(f"<div style='margin-top: 10px; padding: 15px; border-radius: 8px; background-color: #f8f9fa; border: 1px solid #e9ecef;'>", unsafe_allow_html=True)
            st.markdown(f"**Grupo {sel_g}** ({len(m_ids)} elementos)")
            
            if staad_info["status"] != "disconnected" and not st.session_state.get("is_analyzing", False):
                from link import get_design_results
                ratios = get_design_results(m_ids)
                
                valid_ratios = {k: v for k, v in ratios.items() if v > 0.0}
                if valid_ratios:
                    max_id = max(valid_ratios, key=valid_ratios.get)
                    max_ratio = valid_ratios[max_id]
                    
                    st.metric(label="Ratio Crítico", value=f"{max_ratio:.3f}", delta=f"Barra más crítica: {max_id}", delta_color="off")
                    
                    if max_ratio > 1.0:
                        st.markdown("<span style='color: #ba281b; font-weight: bold;'>⚠️ Falla por capacidad</span>", unsafe_allow_html=True)
                    else:
                        st.markdown("<span style='color: #0b7a0b; font-weight: bold;'>✅ Diseño Adecuado</span>", unsafe_allow_html=True)
                else:
                    st.warning("No se encontraron resultados de diseño. Verifica comandos CHECK CODE.")
            else:
                st.info("Sincroniza y corre el análisis para ver los resultados.")
            st.markdown("</div>", unsafe_allow_html=True)

        tab_col, tab_arm, tab_cv = st.tabs(["Columnas", "Armaduras", "Contravientos"])
        
        with tab_col:
            import prediseno
            grupos_c = prediseno.clasificar_columnas(model)
            render_group_results("Columnas", grupos_c)
            
        with tab_arm:
            grupos_a = {k: v for k, v in model.groups.items() if k.startswith(('_CS', '_CI', '_DIAG', '_MONT'))}
            render_group_results("Armaduras", grupos_a)
            
        with tab_cv:
            grupos_v = {k: v for k, v in model.groups.items() if k.startswith('_CV')}
            render_group_results("Contravientos", grupos_v)"""

content = re.sub(pattern_radio_to_results, tabs_logic, content, flags=re.DOTALL)

# 4. Update the visualizer side
# Remove the view buttons and just set zoom extents
pattern_visualizer = r'        vc1, vc2, vc3, vc4, _ = st\.columns\(\[1,1,1,1,2\]\)\n.*?config=\{.*?\}'

visualizer_logic = """        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        # Using the last active group for highlighting if any
        highlight_col = st.session_state.get("highlight_diseno_active", "Ninguno")
        fig = plot_model(model, show_supports=True, highlight_ids=None) # Highlight logic would go here if implemented
        
        # Cube aspect ratio to prevent clipping, and zoomed out slightly
        fig.update_layout(
            scene_camera=dict(eye=dict(x=1.8, y=1.8, z=1.8)),
            margin=dict(l=0, r=0, b=0, t=0),
            scene=dict(aspectmode='cube')
        )
        st.plotly_chart(fig, use_container_width=True, config={'displaylogo': False})"""

content = re.sub(pattern_visualizer, visualizer_logic, content, flags=re.DOTALL)


with open('app/main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done refactoring UI.")
