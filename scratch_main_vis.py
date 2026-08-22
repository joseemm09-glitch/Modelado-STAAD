import sys
import re

with open('app/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_vis_call = """        highlight_col = st.session_state.get("highlight_diseno_active", "Ninguno")
        import prediseno
        all_grps = {**prediseno.clasificar_columnas(model), **model.groups}
        h_ids = all_grps.get(highlight_col, None)
        fig = plot_model(model, show_supports=True, highlight_ids=h_ids)"""

new_vis_call = """        highlight_col = st.session_state.get("highlight_diseno_active", "Ninguno")
        import prediseno
        all_grps = {**prediseno.clasificar_columnas(model), **model.groups}
        h_ids = all_grps.get(highlight_col, None)
        h_colors = None
        if highlight_col == "_CVH" and "highlight_colors_active" in st.session_state:
            h_colors = st.session_state["highlight_colors_active"]
            h_ids = None # Override to use colors instead of simple highlight
        fig = plot_model(model, show_supports=True, highlight_ids=h_ids, highlight_colors=h_colors)"""

content = content.replace(old_vis_call, new_vis_call)

with open('app/main.py', 'w', encoding='utf-8') as f:
    f.write(content)
