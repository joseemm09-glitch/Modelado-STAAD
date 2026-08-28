import re

with open('app/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

detect_logic = """
# Import configurations
is_mobile_client = False
try:
    import js
    if js.window.innerWidth <= 768:
        is_mobile_client = True
except Exception:
    pass
"""

old_import = "from visualizer import plot_model"
new_import = old_import + "\n" + detect_logic

content = content.replace(old_import, new_import)

with open('app/main.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patch for is_mobile_client definition successful!")
