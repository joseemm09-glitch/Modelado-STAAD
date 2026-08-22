import os

with open('app/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = "st.session_state.export_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))"
new = "st.session_state.export_path = r'C:\\Users\\josee\\OneDrive\\Escritorio\\MODELOS GENERADOS'"

content = content.replace(old, new)

with open('app/main.py', 'w', encoding='utf-8') as f:
    f.write(content)
