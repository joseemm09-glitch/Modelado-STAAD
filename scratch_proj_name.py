import sys
import re

with open('app/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_block = """            file_name_export = "Modelo.std"

            st.markdown("**Ubicación:**")"""

new_block = """            st.markdown("**Nombre Proyecto:**")
            file_name_export = st.text_input("proj_name", value="Modelo.std", label_visibility="collapsed")
            
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            st.markdown("**Ubicación:**")"""

content = content.replace(old_block, new_block)

with open('app/main.py', 'w', encoding='utf-8') as f:
    f.write(content)
