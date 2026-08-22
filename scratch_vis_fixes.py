import sys
import re

with open('app/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix aspect mode
content = content.replace("scene=dict(aspectmode='cube')", "scene=dict(aspectmode='data')")

# Fix highlight active logic
old_func_def = """        def render_group_results(tab_name, grupos_dict):
            if not grupos_dict:
                st.info(f"No hay grupos definidos para {tab_name}")
                return
            sel_g = st.radio("Seleccionar Grupo:", list(sorted(grupos_dict.keys())), key=f"highlight_diseno_{tab_name}", horizontal=True)
            st.session_state["highlight_diseno_active"] = sel_g"""

new_func_def = """        def update_highlight(key):
            st.session_state["highlight_diseno_active"] = st.session_state[key]
            
        def render_group_results(tab_name, grupos_dict):
            if not grupos_dict:
                st.info(f"No hay grupos definidos para {tab_name}")
                return
            key_name = f"highlight_diseno_{tab_name}"
            sel_g = st.radio("Seleccionar Grupo:", list(sorted(grupos_dict.keys())), key=key_name, horizontal=True, on_change=update_highlight, args=(key_name,))
            if "highlight_diseno_active" not in st.session_state:
                st.session_state["highlight_diseno_active"] = sel_g"""

content = content.replace(old_func_def, new_func_def)

with open('app/main.py', 'w', encoding='utf-8') as f:
    f.write(content)
