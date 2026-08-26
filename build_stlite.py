import os
import json
import base64

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

FILES_TO_INCLUDE = [
    ("app/main.py", "text"),
    ("app/model.py", "text"),
    ("app/staad_writer.py", "text"),
    ("app/visualizer.py", "text"),
    ("app/prediseno.py", "text"),
    ("app/templates.py", "text"),
    ("app/perfiles_w.py", "text"),
    ("app/staad_link/__init__.py", "text"),
    ("app/staad_link/link.py", "text"),
    ("Archivos/JOISTGRAL.UPT", "text"),
    ("Archivos/JPUNTAL.UPT", "text"),
    ("staad_blue.ico", "binary"),
]

def build():
    files_dict = {}
    
    for rel_path, ftype in FILES_TO_INCLUDE:
        full_path = os.path.join(ROOT_DIR, rel_path.replace("/", os.sep))
        if not os.path.exists(full_path):
            print(f"Warning: {full_path} not found, skipping.")
            continue
            
        if ftype == "text":
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
            files_dict[rel_path] = content
        else:
            with open(full_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
            files_dict[rel_path] = {
                "base64": b64
            }
            
    files_json = json.dumps(files_dict, ensure_ascii=False)
    
    html_template = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8" />
    <meta http-equiv="X-UA-Compatible" content="IE=edge" />
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no" />
    <title>Naves Industriales STAAD.Pro</title>
    <link rel="icon" type="image/x-icon" href="data:image/x-icon;base64,{files_dict.get('staad_blue.ico', {}).get('base64', '')}" />
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@stlite/mountable@0.73.1/build/stlite.css" />
    <style>
        body, html, #root {{
            margin: 0;
            padding: 0;
            width: 100vw;
            height: 100vh;
            overflow: hidden;
        }}
    </style>
</head>
<body>
    <div id="root"></div>
    <script src="https://cdn.jsdelivr.net/npm/@stlite/mountable@0.73.1/build/stlite.js"></script>
    <script>
        const rawFiles = {files_json};
        const processedFiles = {{}};
        
        for (const [path, content] of Object.entries(rawFiles)) {{
            if (typeof content === "string") {{
                processedFiles[path] = content;
            }} else if (content && content.base64) {{
                const binStr = atob(content.base64);
                const bytes = new Uint8Array(binStr.length);
                for (let i = 0; i < binStr.length; i++) {{
                    bytes[i] = binStr.charCodeAt(i);
                }}
                processedFiles[path] = bytes;
            }}
        }}

        stlite.mount({{
            requirements: ["plotly"],
            entrypoint: "app/main.py",
            files: processedFiles
        }}, document.getElementById("root"));
    </script>
</body>
</html>
"""
    output_index = os.path.join(ROOT_DIR, "index.html")
    with open(output_index, "w", encoding="utf-8") as f:
        f.write(html_template)
        
    public_dir = os.path.join(ROOT_DIR, "public")
    os.makedirs(public_dir, exist_ok=True)
    output_public_index = os.path.join(public_dir, "index.html")
    with open(output_public_index, "w", encoding="utf-8") as f:
        f.write(html_template)
        
    print(f"Generated {output_index} and {output_public_index} successfully!")

if __name__ == "__main__":
    build()
