import sys
import re

with open('app/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

replacement = """
        if tab_sel == "Columnas":
            import prediseno
            grupos = prediseno.clasificar_columnas(model)
        elif tab_sel == "Armaduras":
            grupos = {k: v for k, v in model.groups.items() if k.startswith(('_CS', '_CI', '_DIAG', '_MONT'))}
        else:
            grupos = {k: v for k, v in model.groups.items() if k.startswith('_CV')}
            
        if not grupos:
            st.info(f"No hay grupos definidos para {tab_sel}")
        else:
            sel_g = st.radio("Seleccionar Grupo:", list(sorted(grupos.keys())), key="highlight_diseno", horizontal=True)
            m_ids = grupos[sel_g]
            
            st.markdown(f"<div style='margin-top: 10px; padding: 15px; border-radius: 8px; background-color: #f8f9fa; border: 1px solid #e9ecef;'>", unsafe_allow_html=True)
            st.markdown(f"**Grupo {sel_g}** ({len(m_ids)} elementos)")
            
            if staad_info["status"] != "disconnected" and not st.session_state.get("is_analyzing", False):
                from link import get_design_results
                ratios = get_design_results(m_ids)
                
                # Filter out zeroes or errors
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
                    st.warning("No se encontraron resultados de diseño de acero para este grupo. Verifica que el modelo haya corrido y tenga comandos de CHECK CODE.")
            else:
                st.info("Sincroniza y corre el análisis para ver los resultados de diseño.")
                
            st.markdown("</div>", unsafe_allow_html=True)
"""

old = """        if tab_sel == "Columnas":
            st.write("Resultados de columnas (En desarrollo...)")
        elif tab_sel == "Armaduras":
            st.write("Resultados de armaduras (En desarrollo...)")
        else:
            st.write("Resultados de contravientos (En desarrollo...)")"""

content = content.replace(old, replacement.strip())

with open('app/main.py', 'w', encoding='utf-8') as f:
    f.write(content)
