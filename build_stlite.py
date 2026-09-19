import os
import json
import base64

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

FILES_TO_INCLUDE = [
    (".streamlit/config.toml", "text"),
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
    ("FrameOne2.jpg", "binary"),
    ("FrameOne3.png", "binary"),
    ("staad_darkslate.ico", "binary"),
    ("staad_black.ico", "binary"),
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
    files_json = files_json.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    
    logo_base64 = files_dict.get('FrameOne2.jpg', {}).get('base64', '')
    logo_small_base64 = files_dict.get('FrameOne3.png', {}).get('base64', '')
    splash_logo_base64 = logo_base64
    
    html_template = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8" />
    <meta http-equiv="X-UA-Compatible" content="IE=edge" />
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no" />
    <title>Naves Industriales STAAD.Pro</title>
    <link rel="icon" type="image/png" href="data:image/png;base64,{logo_small_base64}" />
    <link rel="apple-touch-icon" href="data:image/png;base64,{logo_small_base64}" />
    <meta name="theme-color" content="#005cb2" />
    <meta name="apple-mobile-web-app-capable" content="yes" />
    <meta name="apple-mobile-web-app-status-bar-style" content="default" />
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@stlite/mountable@0.73.1/build/stlite.css" />
    <style>
        :root {{
            --primary-color: #005cb2 !important;
        }}

        body, html, #root {{
            margin: 0;
            padding: 0;
            width: 100vw;
            height: 100vh;
            overflow: hidden;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #f8fafc;
        }}

        /* Ocultar popups técnicos de stlite (Loading Pyodide, Mounting files, etc.) */
        [class*="toast"], [class*="Toast"], [class*="stlite-toast"], [data-testid="stToast"] {{
            display: none !important;
            opacity: 0 !important;
            visibility: hidden !important;
            pointer-events: none !important;
        }}

        /* Ocultar barra decorativa superior multicolor */
        [data-testid="stDecoration"], .stDecoration, div[class*="stDecoration"] {{
            display: none !important;
            visibility: hidden !important;
            height: 0 !important;
        }}

        /* Pantalla de carga profesional */
        #splash-screen {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: #ffffff;
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 999999;
            transition: opacity 0.5s ease;
        }}

        .splash-card {{
            background: #ffffff;
            padding: 32px 40px;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.06), 0 1px 3px rgba(0, 0, 0, 0.04);
            border: 1px solid #e2e8f0;
            text-align: center;
            max-width: 380px;
            width: 90%;
            animation: fadeIn 0.4s ease-out;
        }}

        .splash-logo {{
            width: 150px;
            height: auto;
            max-height: 150px;
            object-fit: contain;
            border-radius: 22px;
            box-shadow: 0 10px 22px rgba(0, 92, 178, 0.22);
            margin: 0 auto 20px auto;
        }}

        .splash-title {{
            font-size: 20px;
            font-weight: 600;
            color: #0f172a;
            margin: 0 0 0 0;
            padding: 0;
            letter-spacing: -0.3px;
            line-height: 1.25;
        }}

        .splash-subtitle {{
            font-size: 14px;
            color: #64748b;
            margin: 2px 0 22px 0;
            padding: 0;
            line-height: 1.2;
        }}

        .splash-spinner {{
            width: 30px;
            height: 30px;
            border: 3px solid #e2e8f0;
            border-top: 3px solid #005cb2;
            border-radius: 50%;
            margin: 0 auto 12px auto;
            animation: spin 0.8s linear infinite;
        }}

        .splash-status {{
            font-size: 12px;
            color: #94a3b8;
            margin: 0;
            font-weight: 500;
        }}

        /* Ocultar skeleton loaders de Streamlit para que no parpadeen */
        [data-testid="stSkeleton"], [data-testid="stSkeletonBlock"], .stSkeleton {{
            opacity: 0 !important;
        }}

        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(8px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
    </style>
</head>
<body>
    <div id="splash-screen">
        <div class="splash-card">
            <img src="data:image/jpeg;base64,{splash_logo_base64}" class="splash-logo" alt="Logo" />
            <h1 class="splash-title">FrameOne</h1>
            <p class="splash-subtitle">Modelado de Naves Industriales para STAAD.Pro</p>
            <div class="splash-spinner"></div>
            <p class="splash-status">Iniciando aplicación...</p>
        </div>
    </div>
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

        const splash = document.getElementById("splash-screen");
        let dismissed = false;
        let observer = null;

        function hideSessionStateWarnings() {{
            const alerts = document.querySelectorAll('[data-testid="stAlert"]');
            for (let i = 0; i < alerts.length; i++) {{
                const el = alerts[i];
                if (el.textContent && el.textContent.includes('was created with a default value')) {{
                    el.style.display = 'none';
                }}
            }}
        }}

        function tryDismiss() {{
            hideSessionStateWarnings();
            if (dismissed) return;
            // Verificar que los botones del menú y el gráfico o título ya estén completamente dibujados
            const hasSidebarButtons = document.querySelectorAll('section[data-testid="stSidebar"] button').length >= 3;
            const hasPlotly = document.querySelector('.js-plotly-plot') || document.querySelector('[data-testid="stPlotlyChart"]');
            const hasHeading = Array.from(document.querySelectorAll('h1, h2, h3')).some(el => el.textContent.includes('Naves Industriales'));
            const hasSkeleton = document.querySelector('[data-testid="stSkeleton"]') || document.querySelector('[data-testid="stSkeletonBlock"]') || document.querySelector('.stSkeleton');

            if ((hasSidebarButtons || hasPlotly || hasHeading) && !hasSkeleton) {{
                dismissed = true;
                if (observer) observer.disconnect();
                
                // Mantener un observer ligero para seguir ocultando alertas de duplicate key si el usuario interactúa
                const postObserver = new MutationObserver(hideSessionStateWarnings);
                postObserver.observe(document.getElementById("root"), {{ childList: true, subtree: true }});

                // Dar 5.0 segundos adicionales para asegurar que todo el 3D y CSS se haya pintado suavemente
                setTimeout(() => {{
                    if (splash) {{
                        splash.style.opacity = "0";
                        setTimeout(() => splash.remove(), 600);
                    }}
                }}, 5000);
            }}
        }}

        observer = new MutationObserver(tryDismiss);
        observer.observe(document.getElementById("root"), {{ childList: true, subtree: true }});

        const pollInterval = setInterval(() => {{
            hideSessionStateWarnings();
            tryDismiss();
            if (dismissed) clearInterval(pollInterval);
        }}, 300);

        stlite.mount({{
            requirements: ["plotly"],
            entrypoint: "app/main.py",
            files: processedFiles,
            streamlitConfig: {{
                "theme.primaryColor": "#005cb2",
                "theme.backgroundColor": "#ffffff",
                "theme.secondaryBackgroundColor": "#f8fafc",
                "theme.textColor": "#1e293b",
                "global.disableWidgetStateDuplicationWarning": true
            }}
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
