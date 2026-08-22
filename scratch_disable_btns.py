import sys
import re

with open('app/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace sidebar buttons
old_btn = """        st.divider()
        st.button("Diseño", type="primary", width="stretch", on_click=go_panel, args=("Diseño",))
        st.button("Catálogo", type="primary", width="stretch", on_click=go_panel, args=("Catálogo",))"""

new_btn = """        st.divider()
        is_disabled = not st.session_state.get("file_generated", False)
        st.button("Diseño", type="primary", width="stretch", on_click=go_panel, args=("Diseño",), disabled=is_disabled)
        st.button("Catálogo", type="primary", width="stretch", on_click=go_panel, args=("Catálogo",), disabled=is_disabled)"""

content = content.replace(old_btn, new_btn)

with open('app/main.py', 'w', encoding='utf-8') as f:
    f.write(content)
