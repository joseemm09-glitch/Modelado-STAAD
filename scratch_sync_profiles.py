import sys

with open('app/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Modify the Diseño tab initialization
old_init = """            curr_key = f"sel_{sel_g}"
            if curr_key not in st.session_state:
                st.session_state[curr_key] = opciones[0] if opciones else ""
                
            if can_modify:"""

new_init = """            curr_key = f"sel_{sel_g}"
            if curr_key not in st.session_state:
                # Inicializar con logica de Prediseño para que empate con la exportacion
                usar_2w = st.session_state.get("usar_2w_checkbox", False)
                top_5 = prediseno.predisenar_grupo(sel_g, model, usar_2w)
                if top_5:
                    st.session_state[curr_key] = top_5[0]['perfil']['nombre']
                else:
                    st.session_state[curr_key] = opciones[0] if opciones else ""
                
            if can_modify:"""

content = content.replace(old_init, new_init)

# 2. Modify the Export logic initialization
old_export = """            selected_profiles = {}
            grupos_cols = prediseno.clasificar_columnas(model)
            for g in grupos_cols.keys():
                ui_name = st.session_state.get(f"sel_{g}")
                if ui_name:
                    staad_name = name_to_staad.get(ui_name)
                    if staad_name:
                        selected_profiles[g] = staad_name"""

new_export = """            selected_profiles = {}
            all_grps = {**prediseno.clasificar_columnas(model), **{k: v for k, v in model.groups.items() if k.startswith(('_CS', '_CI', '_CV'))}}
            for g in all_grps.keys():
                ui_name = st.session_state.get(f"sel_{g}")
                if not ui_name:
                    # Forzar calculo de Prediseño si el usuario no paso por esa pestaña
                    usar_2w = st.session_state.get("usar_2w_checkbox", False)
                    top_5 = prediseno.predisenar_grupo(g, model, usar_2w)
                    if top_5:
                        ui_name = top_5[0]['perfil']['nombre']
                        st.session_state[f"sel_{g}"] = ui_name
                
                if ui_name:
                    staad_name = name_to_staad.get(ui_name)
                    if staad_name:
                        selected_profiles[g] = staad_name"""

content = content.replace(old_export, new_export)

with open('app/main.py', 'w', encoding='utf-8') as f:
    f.write(content)
