import sys

with open('app/main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for i, line in enumerate(lines):
    if 'st.title("Naves Industriales STAAD.Pro")' in line and i > 200:
        continue
    if 'st.markdown("<div style=\'color: gray; font-size: 14px; margin-top: -15px; margin-bottom: 30px; margin-left: 5px;\'>M.I. José Ramón Márquez Montes</div>", unsafe_allow_html=True)' in line and i > 200:
        continue
    new_lines.append(line)

with open('app/main.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
