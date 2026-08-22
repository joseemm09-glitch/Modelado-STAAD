import sys

with open('app/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the split f-string: 
# st.success(f"Guardado exitosamente en:
# {full_path}")
content = content.replace('st.success(f"Guardado exitosamente en:\n{full_path}")', 'st.success(f"Guardado exitosamente en:\\n{full_path}")')

with open('app/main.py', 'w', encoding='utf-8') as f:
    f.write(content)
