import sys

with open('app/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

helpers = """def render_siblings_top(group, current):
    for name in group:
        if name == current: break
        c1, c2, c3 = st.columns([1, 6, 1])
        with c2: st.button(name, type="primary", use_container_width=True, on_click=go_panel, args=(name,), key=f"nav_top_{name}")

def render_siblings_bottom(group, current):
    found = False
    for name in group:
        if found:
            c1, c2, c3 = st.columns([1, 6, 1])
            with c2: st.button(name, type="primary", use_container_width=True, on_click=go_panel, args=(name,), key=f"nav_bot_{name}")
        if name == current: found = True

nav_group1 = ["Geometría", "Cargas", "Prediseño"]
nav_group2 = ["Diseño", "Catálogo"]

with st.sidebar:"""

content = content.replace('with st.sidebar:', helpers)

# Update Geometria
content = content.replace('st.button("⬅", type="secondary", on_click=go_panel, args=("Main",))\n        st.header("Geometría")', 'st.button("⬅ Volver", type="secondary", on_click=go_panel, args=("Main",))\n        render_siblings_top(nav_group1, "Geometría")\n        st.header("Geometría")')

content = content.replace('st.session_state.add_wind_cols = False\n\n    elif panel == "Cargas":', 'st.session_state.add_wind_cols = False\n        render_siblings_bottom(nav_group1, "Geometría")\n\n    elif panel == "Cargas":')

# Update Cargas
content = content.replace('st.button("⬅", type="secondary", on_click=go_panel, args=("Main",))\n        st.header("Cargas")', 'st.button("⬅ Volver", type="secondary", on_click=go_panel, args=("Main",))\n        render_siblings_top(nav_group1, "Cargas")\n        st.header("Cargas")')

content = content.replace('st.number_input("Carga Viva para Sismo (kg/m²)", min_value=0.0, step=5.0, value=st.session_state.cv_sismo, key="_cv_sismo", on_change=update_val, args=("cv_sismo",))\n\n    elif panel == "Prediseño":', 'st.number_input("Carga Viva para Sismo (kg/m²)", min_value=0.0, step=5.0, value=st.session_state.cv_sismo, key="_cv_sismo", on_change=update_val, args=("cv_sismo",))\n        render_siblings_bottom(nav_group1, "Cargas")\n\n    elif panel == "Prediseño":')

# Update Prediseno
content = content.replace('st.button("⬅", type="secondary", on_click=go_panel, args=("Main",))\n        st.header("Prediseño")', 'st.button("⬅ Volver", type="secondary", on_click=go_panel, args=("Main",))\n        render_siblings_top(nav_group1, "Prediseño")\n        st.header("Prediseño")')

content = content.replace('st.markdown("<div style=\'margin-top:-15px; font-size:12px; color:#888;\'>(Requiere Base de Datos WD)</div>", unsafe_allow_html=True)\n\n    elif panel == "Diseño":', 'st.markdown("<div style=\'margin-top:-15px; font-size:12px; color:#888;\'>(Requiere Base de Datos WD)</div>", unsafe_allow_html=True)\n        render_siblings_bottom(nav_group1, "Prediseño")\n\n    elif panel == "Diseño":')

# Update Diseno
content = content.replace('st.button("⬅", type="secondary", on_click=go_panel, args=("Main",))\n        st.header("Diseño")', 'st.button("⬅ Volver", type="secondary", on_click=go_panel, args=("Main",))\n        render_siblings_top(nav_group2, "Diseño")\n        st.header("Diseño")\n        render_siblings_bottom(nav_group2, "Diseño")')

# Update Catalogo
content = content.replace('st.button("⬅", type="secondary", on_click=go_panel, args=("Main",))\n        st.header("Catálogo")', 'st.button("⬅ Volver", type="secondary", on_click=go_panel, args=("Main",))\n        render_siblings_top(nav_group2, "Catálogo")\n        st.header("Catálogo")\n        render_siblings_bottom(nav_group2, "Catálogo")')

with open('app/main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done")
