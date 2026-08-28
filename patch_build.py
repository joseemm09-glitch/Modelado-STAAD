import re

with open('build_stlite.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_link = '<link rel="icon" type="image/x-icon" href="data:image/x-icon;base64,{logo_base64}" />'
new_links = """<link rel="icon" type="image/x-icon" href="data:image/x-icon;base64,{logo_base64}" />
    <link rel="apple-touch-icon" href="data:image/x-icon;base64,{logo_base64}" />
    <meta name="theme-color" content="#005cb2" />
    <meta name="apple-mobile-web-app-capable" content="yes" />
    <meta name="apple-mobile-web-app-status-bar-style" content="default" />"""

content = content.replace(old_link, new_links)

with open('build_stlite.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patch build_stlite.py successful!")
