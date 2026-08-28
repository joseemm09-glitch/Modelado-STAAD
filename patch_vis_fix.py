import re

with open('app/visualizer.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = "largueros_groups = [g for g in lines_by_group.keys() if g.startswith('_LARGUEROS')]"
new = "largueros_groups = [g for g in model.groups.keys() if g.startswith('_LARGUEROS')]"

content = content.replace(old, new)

with open('app/visualizer.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patch successful!")
