import sys
import re

with open('app/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

pattern = r'        def render_group_results.*?st\.markdown\("</div>", unsafe_allow_html=True\)'

new_render = """        def render_group_results(tab_name, grupos_dict):
            if not grupos_dict:
                st.info(f"No hay grupos definidos para {tab_name}")
                return
            sel_g = st.radio("Seleccionar Grupo:", list(sorted(grupos_dict.keys())), key=f"highlight_diseno_{tab_name}", horizontal=True)
            st.session_state["highlight_diseno_active"] = sel_g
            m_ids = grupos_dict[sel_g]
            
            st.markdown(f"<div style='margin-top: 10px; padding: 15px; border-radius: 8px; background-color: #f8f9fa; border: 1px solid #e9ecef;'>", unsafe_allow_html=True)
            st.markdown(f"**Grupo {sel_g}** ({len(m_ids)} elementos)")
            
            can_modify = not (sel_g.startswith('_DIAG') or sel_g.startswith('_MONT'))
            es_w = sel_g.startswith('_COL') or sel_g.startswith('_CV')
            
            import prediseno
            db_or = prediseno.cargar_base_datos_excel()
            db_w = prediseno.PERFILES_W
            opciones = [p['nombre'] for p in db_w] if es_w else [p['nombre'] for p in db_or]
            
            curr_key = f"sel_{sel_g}"
            if curr_key not in st.session_state:
                st.session_state[curr_key] = opciones[0] if opciones else ""
                
            if can_modify:
                st.selectbox("Perfil Asignado:", options=opciones, key=curr_key)
            else:
                st.write(f"Perfil Asignado: Auto (Comando SELECT de STAAD)")
            
            if staad_info["status"] != "disconnected" and not st.session_state.get("is_analyzing", False):
                from link import get_design_results
                ratios = get_design_results(m_ids)
                
                valid_ratios = {k: v for k, v in ratios.items() if v > 0.0}
                if valid_ratios:
                    max_id = max(valid_ratios, key=valid_ratios.get)
                    max_ratio = valid_ratios[max_id]
                    
                    c1, c2 = st.columns([1, 1])
                    with c1:
                        st.metric(label="Ratio Crítico", value=f"{max_ratio:.3f}", delta=f"Barra más crítica: {max_id}", delta_color="off")
                        if max_ratio > 1.0:
                            st.markdown("<span style='color: #ba281b; font-weight: bold;'>⚠️ Falla por capacidad</span>", unsafe_allow_html=True)
                        else:
                            st.markdown("<span style='color: #0b7a0b; font-weight: bold;'>✅ Diseño Adecuado</span>", unsafe_allow_html=True)
                            
                    with c2:
                        if can_modify:
                            st.markdown("<br>", unsafe_allow_html=True)
                            if st.button("Optimizar Grupo ⚡", key=f"btn_opt_{sel_g}", type="primary"):
                                st.session_state.is_analyzing = True
                                nuevo_perfil = prediseno.optimizar_perfil(st.session_state[curr_key], max_ratio, es_w=es_w, ratio_objetivo=0.95)
                                if nuevo_perfil != st.session_state[curr_key]:
                                    st.session_state[curr_key] = nuevo_perfil
                                    
                                    import staad_writer
                                    name_to_staad = {p['nombre']: p.get('nombre_staad', p['nombre']) for p in db_or + db_w}
                                    selected_profiles = {}
                                    all_groups = {**prediseno.clasificar_columnas(model), **{k: v for k, v in model.groups.items() if k.startswith(('_CS', '_CI', '_DIAG', '_MONT', '_CV'))}}
                                    for g in all_groups.keys():
                                        ui_name = st.session_state.get(f"sel_{g}")
                                        if ui_name:
                                            staad_name = name_to_staad.get(ui_name)
                                            if staad_name:
                                                selected_profiles[g] = staad_name
                                                
                                    staad_text = staad_writer.write_staad(model, selected_profiles=selected_profiles)
                                    clean_name = st.session_state.get("active_staad_file", "Modelo.std")
                                    export_path = st.session_state.get("export_path", ".")
                                    import os
                                    full_path = os.path.join(export_path, clean_name)
                                    with open(full_path, "w", encoding="utf-8") as f:
                                        f.write(staad_text)
                                        
                                st.rerun()
                else:
                    st.warning("No se encontraron resultados de diseño. Verifica comandos CHECK CODE.")
            else:
                st.info("Sincroniza y corre el análisis para ver los resultados.")
            st.markdown("</div>", unsafe_allow_html=True)"""

content = re.sub(pattern, new_render, content, flags=re.DOTALL)

with open('app/main.py', 'w', encoding='utf-8') as f:
    f.write(content)
