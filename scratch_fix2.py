import sys

with open('app/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("st.plotly_chart(fig, use_container_width=True, config={'displaylogo': False}))", "st.plotly_chart(fig, use_container_width=True, config={'displaylogo': False})")

with open('app/main.py', 'w', encoding='utf-8') as f:
    f.write(content)
