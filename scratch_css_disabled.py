import sys

with open('app/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_css = """    section[data-testid="stSidebar"] button[kind="primary"]:active {
        transform: translateY(1px) !important;
    }"""

new_css = """    section[data-testid="stSidebar"] button[kind="primary"]:active {
        transform: translateY(1px) !important;
    }
    section[data-testid="stSidebar"] button[kind="primary"]:disabled, button[kind="primary"]:disabled {
        background-color: #e0e0e0 !important;
        color: #9e9e9e !important;
        cursor: not-allowed !important;
        box-shadow: none !important;
        transform: none !important;
        border: 1px solid #d0d0d0 !important;
    }"""

content = content.replace(old_css, new_css)

with open('app/main.py', 'w', encoding='utf-8') as f:
    f.write(content)
