import sys
import re

with open('app/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update logo logic
old_sidebar_top = """with st.sidebar:
    panel = st.session_state.current_panel

    if panel == "Main":
        # Logo at the top of the sidebar
        try:
            st.image(icono_path, use_container_width=True)
        except:
            pass
        st.markdown("<h3 style='text-align: center; margin-top: 10px;'>"""

new_sidebar_top = """with st.sidebar:
    panel = st.session_state.current_panel

    if panel == "Main":
        try:
            st.image(icono_path, use_container_width=True)
        except:
            pass
        st.markdown("<h3 style='text-align: center; margin-top: 10px;'>"""

# Wait, if panel != "Main", where should it go?
# Let's just put it at the very top of `with st.sidebar:` unconditionally.

old_sidebar_full = """with st.sidebar:
    panel = st.session_state.current_panel

    if panel == "Main":
        # Logo at the top of the sidebar
        try:
            st.image(icono_path, use_container_width=True)
        except:
            pass
        st.markdown("<h3 style='text-align: center; margin-top: 10px;'>"""

new_sidebar_full = """with st.sidebar:
    panel = st.session_state.current_panel
    
    if panel == "Main":
        try:
            st.image(icono_path, use_container_width=True)
        except:
            pass
    else:
        try:
            col1, col2, col3 = st.columns([1,2,1])
            with col2:
                st.image(icono_path, use_container_width=True)
        except:
            pass

    if panel == "Main":
        st.markdown("<h3 style='text-align: center; margin-top: 10px;'>"""

content = content.replace(old_sidebar_full, new_sidebar_full)

# 2. Update visualizer highlight logic in Diseño
old_vis = """        # Using the last active group for highlighting if any
        highlight_col = st.session_state.get("highlight_diseno_active", "Ninguno")
        fig = plot_model(model, show_supports=True, highlight_ids=None) # Highlight logic would go here if implemented"""

new_vis = """        # Using the last active group for highlighting if any
        highlight_col = st.session_state.get("highlight_diseno_active", "Ninguno")
        import prediseno
        all_grps = {**prediseno.clasificar_columnas(model), **model.groups}
        h_ids = all_grps.get(highlight_col, None)
        fig = plot_model(model, show_supports=True, highlight_ids=h_ids)"""

content = content.replace(old_vis, new_vis)

with open('app/main.py', 'w', encoding='utf-8') as f:
    f.write(content)
