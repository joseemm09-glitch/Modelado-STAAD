import sys
import re

with open('app/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Modify Sidebar render functions
old_funcs = """def render_siblings_top(group, current):
    for name in group:
        if name == current: break
        c1, c2, c3 = st.columns([1, 6, 1])
        with c2: st.button(name, type="primary", use_container_width=True, on_click=go_panel, args=(name,), key=f"nav_top_{name}")

def render_siblings_bottom(group, current):
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

new_funcs = """def render_siblings_top(group, current):
    for name in group:
        if name == current: break
        c1, c2, c3 = st.columns([1, 6, 1])
        is_dis = False
        if name in ["Diseño", "Catálogo"] and not st.session_state.get("file_generated", False):
            is_dis = True
        with c2: st.button(name, type="primary", use_container_width=True, on_click=go_panel, args=(name,), key=f"nav_top_{name}", disabled=is_dis)

def render_siblings_bottom(group, current):
    found = False
    first_bot = True
    for name in group:
        if found:
            if first_bot:
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("<hr style='margin: 0px 0px 10px 0px; border: 0; border-top: 1px solid #e0e0e0;'>", unsafe_allow_html=True)
                first_bot = False
            c1, c2, c3 = st.columns([1, 6, 1])
            is_dis = False
            if name in ["Diseño", "Catálogo"] and not st.session_state.get("file_generated", False):
                is_dis = True
            with c2: st.button(name, type="primary", use_container_width=True, on_click=go_panel, args=(name,), key=f"nav_bot_{name}", disabled=is_dis)
        if name == current: found = True"""

content = content.replace(old_funcs, new_funcs)

# Update the main sidebar buttons
menu_old = """    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    if st.button("Diseño Estructural", type="secondary", use_container_width=True):
        st.session_state.current_panel = "Diseño"
        st.rerun()
        
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    if st.button("Catálogo de Conceptos", type="secondary", use_container_width=True):"""

menu_new = """    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    is_dis = not st.session_state.get("file_generated", False)
    if st.button("Diseño Estructural", type="secondary", use_container_width=True, disabled=is_dis):
        st.session_state.current_panel = "Diseño"
        st.rerun()
        
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    if st.button("Catálogo de Conceptos", type="secondary", use_container_width=True, disabled=is_dis):"""
content = content.replace(menu_old, menu_new)

# Generate logic
save_old = """                    st.session_state.current_panel = "Diseño"
                    st.rerun()"""
save_new = """                    st.session_state.file_generated = True
                    st.session_state.active_staad_file = clean_name
                    st.session_state.current_panel = "Diseño"
                    st.rerun()"""
content = content.replace(save_old, save_new)

# Update STAAD check in sidebar for Diseño
staad_check_old = """        if staad_info["status"] == "connected":
            color = "#005cb2" # Blue
            text = f"Sincronizado a modelo:<br><span style='color: #005cb2; font-weight: normal;'>{staad_info['filename']}</span>"
        elif staad_info["status"] == "connected_no_results":
            color = "#d4b106" # Yellow
            text = f"Sincronizado a modelo:<br><span style='color: #005cb2; font-weight: normal;'>{staad_info['filename']}</span>"
        else:
            color = "#ba281b" # Red
            text = "No sincronizado a modelo"
            
        st.markdown(f"<div style='margin-bottom: 20px; font-size: 14px; font-weight: 600;'><span style='color: {color}; font-size: 10px;'>●</span> {text}</div>", unsafe_allow_html=True)"""

staad_check_new = """        target_file = st.session_state.get("active_staad_file", "")
        if staad_info["status"] in ["connected", "connected_no_results"] and target_file and target_file.lower() == str(staad_info["filename"]).lower():
            color = "#005cb2" if staad_info["status"] == "connected" else "#d4b106"
            text = f"Sincronizado a modelo:<br><span style='color: {color}; font-weight: normal;'>{staad_info['filename']}</span>"
        else:
            # Override if disconnected or mismatched
            staad_info["status"] = "disconnected"
            color = "#ba281b" # Red
            text = "No sincronizado al modelo exportado"
            
        st.markdown(f"<div style='margin-bottom: 20px; font-size: 14px; font-weight: 600;'><span style='color: {color}; font-size: 10px;'>●</span> {text}</div>", unsafe_allow_html=True)"""

content = content.replace(staad_check_old, staad_check_new)

with open('app/main.py', 'w', encoding='utf-8') as f:
    f.write(content)
