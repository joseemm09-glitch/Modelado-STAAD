import sys

with open('app/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_block = """        def render_group_results(tab_name, grupos_dict):
            if not grupos_dict:
                st.info(f"No hay grupos definidos para {tab_name}")
                return
            key_name = f"highlight_diseno_{tab_name}"
            sel_g = st.radio("Seleccionar Grupo:", list(sorted(grupos_dict.keys())), key=key_name, horizontal=True, on_change=update_highlight, args=(key_name,))
            if "highlight_diseno_active" not in st.session_state:
                st.session_state["highlight_diseno_active"] = sel_g
            m_ids = grupos_dict[sel_g]
            
            st.markdown(f"<div style='margin-top: 10px; padding: 15px; border-radius: 8px; background-color: #f8f9fa; border: 1px solid #e9ecef;'>", unsafe_allow_html=True)
            st.markdown(f"**Grupo {sel_g}** ({len(m_ids)} elementos)")"""


new_block = """        def render_group_results(tab_name, grupos_dict):
            if not grupos_dict:
                st.info(f"No hay grupos definidos para {tab_name}")
                return
            key_name = f"highlight_diseno_{tab_name}"
            sel_g = st.radio("Seleccionar Grupo:", list(sorted(grupos_dict.keys())), key=key_name, horizontal=True, on_change=update_highlight, args=(key_name,))
            if "highlight_diseno_active" not in st.session_state:
                st.session_state["highlight_diseno_active"] = sel_g
            m_ids = grupos_dict[sel_g]
            
            st.markdown(f"<div style='margin-top: 10px; padding: 15px; border-radius: 8px; background-color: #f8f9fa; border: 1px solid #e9ecef;'>", unsafe_allow_html=True)
            
            if sel_g == "_CVH":
                DIAMETERS = [1.905, 2.54, 3.175, 3.81, 4.445, 5.08]
                DIAMETERS_STR = ["3/4\\"", "1\\"", "1 1/4\\"", "1 1/2\\"", "1 3/4\\"", "2\\""]
                
                if "cvh_props" not in st.session_state:
                    st.session_state.cvh_props = {m: 1.905 for m in m_ids}
                    
                from link import get_design_results
                ratios = {}
                if staad_info["status"] != "disconnected" and not st.session_state.get("is_analyzing", False):
                    ratios = get_design_results(m_ids)
                
                stats = {}
                for m in m_ids:
                    d = st.session_state.cvh_props.get(m, 1.905)
                    r = ratios.get(m, 0.0)
                    if d not in stats:
                        stats[d] = {'pass': 0, 'fail': 0, 'mids_pass': [], 'mids_fail': []}
                    if r <= 0.5:
                        stats[d]['pass'] += 1
                        stats[d]['mids_pass'].append(m)
                    else:
                        stats[d]['fail'] += 1
                        stats[d]['mids_fail'].append(m)
                
                st.markdown(f"**Grupo _CVH** ({len(m_ids)} elementos)")
                st.markdown("Ratio máximo permitido: **0.50**")
                
                options = []
                options_map = {}
                for d in DIAMETERS:
                    if d in stats:
                        idx = DIAMETERS.index(d)
                        label = f"Redondo {DIAMETERS_STR[idx]} [{stats[d]['pass']} Pasan, {stats[d]['fail']} Fallan]"
                        options.append(label)
                        options_map[label] = d
                        
                if not options:
                    st.info("No hay contravientos horizontales evaluados aún.")
                else:
                    sel_label = st.radio("Inspeccionar en visualizador 3D:", options, key="cvh_inspect")
                    sel_d = options_map[sel_label]
                    
                    h_colors = {}
                    for m in stats[sel_d]['mids_pass']:
                        h_colors[m] = 'green'
                    for m in stats[sel_d]['mids_fail']:
                        h_colors[m] = 'red'
                    st.session_state["highlight_colors_active"] = h_colors
                
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Optimizar CVH ⚡", type="primary"):
                    st.session_state.is_analyzing = True
                    changed = False
                    for m in m_ids:
                        r = ratios.get(m, 0.0)
                        if r > 0.5:
                            curr_d = st.session_state.cvh_props.get(m, 1.905)
                            try:
                                idx = DIAMETERS.index(curr_d)
                                if idx < len(DIAMETERS) - 1:
                                    st.session_state.cvh_props[m] = DIAMETERS[idx+1]
                                    changed = True
                            except ValueError:
                                pass
                    
                    if changed:
                        import staad_writer
                        name_to_staad = {p['nombre']: p.get('nombre_staad', p['nombre']) for p in db_or + db_w}
                        selected_profiles = {}
                        all_groups = {**prediseno.clasificar_columnas(model), **{k: v for k, v in model.groups.items() if k.startswith(('_CS', '_CI', '_DIAG', '_MONT', '_CV'))}}
                        for g in all_groups.keys():
                            if g == "_CVH": continue
                            ui_name = st.session_state.get(f"sel_{g}")
                            if ui_name:
                                staad_name = name_to_staad.get(ui_name)
                                if staad_name:
                                    selected_profiles[g] = staad_name
                                    
                        staad_text = staad_writer.write_staad(model, selected_profiles=selected_profiles, cvh_props=st.session_state.cvh_props)
                        clean_name = st.session_state.get("active_staad_file", "Modelo.std")
                        export_path = st.session_state.get("export_path", ".")
                        import os
                        full_path = os.path.join(export_path, clean_name)
                        with open(full_path, "w", encoding="utf-8") as f:
                            f.write(staad_text)
                            
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
                return

            st.markdown(f"**Grupo {sel_g}** ({len(m_ids)} elementos)")"""

content = content.replace(old_block, new_block)

with open('app/main.py', 'w', encoding='utf-8') as f:
    f.write(content)
