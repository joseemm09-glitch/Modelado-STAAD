import os
import sys
import time
import socket
import urllib.request
import subprocess
import webview

# --- 1. Configuración de Rutas ---
if getattr(sys, 'frozen', False):
    # Si está compilado, sys.executable apunta a Ejecutable/dist/FrameOne StandAlone/FrameOne StandAlone.exe
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(sys.executable))))
else:
    # Si no está compilado, está en Ejecutable/
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app_script = os.path.join(base_dir, "app", "main.py")
icon_svg = os.path.join(base_dir, "Azul.svg")
icon_ico = os.path.join(base_dir, "FrameOne.ico")

PORT = 8501
URL = f"http://localhost:{PORT}/?embed=true&embed_options=light_theme&embed_options=show_padding"

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def wait_for_server(url, timeout=30):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = urllib.request.urlopen(url)
            if response.getcode() == 200:
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False

# --- 2. Contenedor con Pantalla de Carga y Transición Suave (HTML) ---
def get_app_container_html(url):
    svg_content = ""
    try:
        with open(icon_svg, 'r', encoding='utf-8') as f:
            svg_content = f.read()
    except Exception:
        svg_content = "<!-- Logo no encontrado -->"

    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Segoe+UI:wght@400;600;700&display=swap');
            
            * {{
                box-sizing: border-box;
            }}
            
            html, body {{
                margin: 0; padding: 0; background: #ffffff;
                width: 100vw; height: 100vh; overflow: hidden;
                font-family: 'Segoe UI', system-ui, sans-serif;
            }}
            
            #app-frame {{
                width: 100vw; height: 100vh; border: none;
                position: absolute; top: 0; left: 0;
                z-index: 1;
                background: #ffffff;
            }}
            
            #splash-layer {{
                position: absolute; top: 0; left: 0;
                width: 100vw; height: 100vh;
                background: #ffffff;
                z-index: 9999;
                display: flex; justify-content: center; align-items: center;
                transition: opacity 0.7s cubic-bezier(0.4, 0, 0.2, 1);
                opacity: 1;
                pointer-events: all;
            }}
            
            #splash-layer.fade-out {{
                opacity: 0;
                pointer-events: none;
            }}
            
            .splash-card {{
                background: #ffffff; padding: 32px 40px; border-radius: 20px;
                text-align: center; max-width: 380px; width: 90%;
                transform: scale(1.5);
                animation: splashAppear 0.4s ease-out;
            }}
            
            @keyframes splashAppear {{
                from {{ opacity: 0; transform: scale(1.4); }}
                to {{ opacity: 1; transform: scale(1.5); }}
            }}
            
            .splash-logo {{
                width: 150px; height: 150px;
                margin: 0 auto 20px auto;
                display: flex; justify-content: center; align-items: center;
            }}
            
            .splash-logo svg {{
                width: 100%; height: 100%;
                border-radius: 22px;
                box-shadow: 0 10px 22px rgba(0, 92, 178, 0.22);
            }}
            
            .splash-title {{
                font-size: 24px; font-weight: 700; color: #0f172a; margin: 0;
                letter-spacing: -0.5px;
            }}
            
            .splash-subtitle {{
                font-size: 14px; color: #64748b; margin: 5px 0 0 0;
            }}
        </style>
    </head>
    <body>
        <iframe id="app-frame" src="{url}"></iframe>
        
        <div id="splash-layer">
            <div class="splash-card">
                <div class="splash-logo">
                    {svg_content}
                </div>
                <h1 class="splash-title">FrameOne</h1>
                <p class="splash-subtitle">Modelado de Naves Industriales para STAAD.Pro</p>
            </div>
        </div>

        <script>
            // Pre-configurar tema light en localStorage
            try {{
                const themeVal = JSON.stringify('Light');
                localStorage.setItem('stActiveTheme-/-v2', themeVal);
                localStorage.setItem('stActiveTheme-/app-v2', themeVal);
                localStorage.setItem('stActiveTheme', themeVal);
            }} catch(e) {{}}

            // Transición suave: desvanecer la pantalla de carga tras inicializar
            setTimeout(function() {{
                const splash = document.getElementById('splash-layer');
                if (splash) {{
                    splash.classList.add('fade-out');
                    setTimeout(() => {{ splash.style.display = 'none'; }}, 700);
                }}
            }}, 3800);

            // Escuchar mensajes postMessage desde iframes hijos (Escape, minimizar, etc.)
            window.addEventListener('message', function(event) {{
                if (event.data === 'pywebview:restore' || (event.data && event.data.action === 'restore')) {{
                    if (window.pywebview && window.pywebview.api) {{
                        window.pywebview.api.restore();
                    }}
                }}
                if (event.data === 'pywebview:minimize' || (event.data && event.data.action === 'minimize')) {{
                    if (window.pywebview && window.pywebview.api) {{
                        window.pywebview.api.minimize();
                    }}
                }}
            }});

            // Manejo de la tecla ESC en la ventana principal
            window.addEventListener('keydown', function(e) {{
                if (e.key === 'Escape') {{
                    if (window.pywebview && window.pywebview.api) {{
                        window.pywebview.api.restore();
                    }}
                }}
            }});
        </script>
    </body>
    </html>
    """
    return html

# --- 3. Proceso Principal ---
class Api:
    def __init__(self):
        self.is_fullscreen = True

    def minimize(self):
        import webview
        if webview.windows:
            webview.windows[0].minimize()
            
    def restore(self):
        import webview
        if webview.windows:
            win = webview.windows[0]
            if self.is_fullscreen:
                win.toggle_fullscreen()
                self.is_fullscreen = False
            else:
                win.restore()

    def toggle_fullscreen(self):
        import webview
        if webview.windows:
            webview.windows[0].toggle_fullscreen()
            self.is_fullscreen = not self.is_fullscreen

def main():
    server_process = None
    
    # Iniciar servidor Streamlit si no está corriendo
    if not is_port_in_use(PORT):
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        cmd = [
            sys.executable, "-m", "streamlit", "run", app_script, 
            "--server.headless", "true", 
            "--server.port", str(PORT),
            "--theme.base", "light",
            "--theme.primaryColor", "#005cb2",
            "--theme.backgroundColor", "#ffffff",
            "--theme.secondaryBackgroundColor", "#f8fafc",
            "--theme.textColor", "#1e293b"
        ]
        server_process = subprocess.Popen(cmd, startupinfo=startupinfo, cwd=base_dir)
        
    api_instance = Api()

    # Iniciar la ventana en modo pantalla completa sin bordes (Frameless Fullscreen) con fondo blanco
    window = webview.create_window(
        'FrameOne StandAlone', 
        html=get_app_container_html(URL), 
        width=1280, 
        height=800, 
        min_size=(900, 600), 
        resizable=True, 
        frameless=False,
        fullscreen=True,
        background_color='#FFFFFF',
        text_select=True,
        js_api=api_instance
    )
    
    # Arrancar pywebview
    webview.start(icon=icon_ico)
    
    # Al cerrar la ventana, terminar Streamlit
    if server_process:
        server_process.terminate()

if __name__ == "__main__":
    main()
