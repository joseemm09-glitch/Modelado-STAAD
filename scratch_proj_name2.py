import sys

with open('app/main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'file_name_export = "Modelo.std"' in line:
        lines[i] = '            st.markdown("**Nombre Proyecto:**")\n            file_name_export = st.text_input("proj_name", value="Modelo.std", label_visibility="collapsed")\n            st.markdown("<div style=\'height: 10px;\'></div>", unsafe_allow_html=True)\n'
        break

with open('app/main.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
