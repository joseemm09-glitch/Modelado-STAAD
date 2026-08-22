import sys

with open('app/main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(580, 615):
    line = lines[i]
    if line.startswith('if tab_sel == "Columnas":'):
        lines[i] = '        ' + line
    elif line.strip() == '':
        continue
    elif not line.startswith('        '):
        lines[i] = '        ' + line.lstrip()

with open('app/main.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
