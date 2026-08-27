import json, re

with open('embedded_profiles.json', 'r') as f:
    profiles = json.load(f)

profiles_str = "    perfiles = [\n"
for p in profiles:
    profiles_str += f"        {p},\n"
profiles_str += "    ]\n    return perfiles"

with open('prediseno.py', 'r', encoding='utf-8') as f:
    content = f.read()

pattern = re.compile(r"def cargar_base_datos_excel\(\):.*?return sorted\(perfiles, key=lambda x: x\[\"peso\"\]\)", re.DOTALL)

replacement = f"def cargar_base_datos_excel():\n{profiles_str}"

new_content = pattern.sub(replacement, content)

with open('prediseno.py', 'w', encoding='utf-8') as f:
    f.write(new_content)
