import os
import sys
import time
import json
import base64
import socket
import urllib.request
import subprocess
import threading
import webview

# Asegurar que el directorio raíz esté en sys.path para importar security
if getattr(sys, 'frozen', False):
    base_dir = os.path.dirname(os.path.abspath(sys.executable))
    if not os.path.exists(os.path.join(base_dir, "app")):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(base_dir)))
else:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from security.client import LicenseClient
from security.config import HEARTBEAT_INTERVAL_SECONDS
from security.hwid import get_hardware_id, get_computer_name

app_script = os.path.join(base_dir, "app", "main.py")
logo_jpg = os.path.join(base_dir, "FrameOne_logo.jpg")
if not os.path.exists(logo_jpg):
    logo_jpg = os.path.join(base_dir, "FrameOne2.jpg")

icon_ico = os.path.join(base_dir, "FrameOne.ico")

PORT = 8501
URL = f"http://localhost:{PORT}/?embed=true&embed_options=light_theme&embed_options=show_padding"

# Ruta para guardar credenciales de forma segura en AppData
appdata_dir = os.path.join(os.environ.get("APPDATA", base_dir), "FrameOne")
os.makedirs(appdata_dir, exist_ok=True)
CACHE_FILE = os.path.join(appdata_dir, "auth_cache.json")


def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


def wait_for_server(url, timeout=35):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = urllib.request.urlopen(url)
            if response.getcode() == 200:
                return True
        except Exception:
            pass
        time.sleep(0.4)
    return False


# --- Generador de la Interfaz Visual (HTML/CSS/JS) ---
def get_app_container_html(url):
    logo_html = ""
    try:
        if os.path.exists(logo_jpg):
            with open(logo_jpg, 'rb') as f:
                b64_data = base64.b64encode(f.read()).decode('utf-8')
                logo_html = f'<img src="data:image/jpeg;base64,{b64_data}" class="splash-logo-img" alt="FrameOne" />'
        else:
            logo_html = "<h1 style='color:#005cb2;'>FrameOne</h1>"
    except Exception:
        logo_html = "<h1 style='color:#005cb2;'>FrameOne</h1>"

    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>FrameOne</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Segoe+UI:wght@400;500;600;700&display=swap');
            
            * {{
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }}
            
            html, body {{
                width: 100vw;
                height: 100vh;
                overflow: hidden;
                background: #ffffff;
                font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
                color: #1f2937;
            }}
            
            /* Barra de ventana minimalista personalizada */
            .window-titlebar {{
                position: fixed;
                top: 0;
                left: 0;
                width: 100vw;
                height: 34px;
                display: flex;
                justify-content: flex-end;
                align-items: center;
                z-index: 100000;
                background: transparent;
                user-select: none;
                -webkit-app-region: drag;
            }}
            
            .window-controls {{
                display: flex;
                align-items: center;
                padding-right: 6px;
                -webkit-app-region: no-drag;
                pointer-events: auto;
            }}
            
            .win-btn {{
                width: 32px;
                height: 26px;
                background: transparent;
                border: none;
                color: #94a3b8;
                display: flex;
                justify-content: center;
                align-items: center;
                cursor: pointer;
                border-radius: 6px;
                transition: background 0.15s, color 0.15s;
                outline: none;
            }}
            
            .win-btn:hover {{
                background: rgba(0, 0, 0, 0.06);
                color: #475569;
            }}
            
            .win-btn-close:hover {{
                background: #fee2e2;
                color: #dc2626;
            }}
            
            #app-frame {{
                width: 100vw;
                height: 100vh;
                border: none;
                position: absolute;
                top: 0;
                left: 0;
                z-index: 1;
                background: #ffffff;
                display: none;
            }}
            
            /* Capa de fondo estilo Google Gemini (degradado suave cielo / aurora) */
            #auth-layer {{
                position: absolute;
                top: 0;
                left: 0;
                width: 100vw;
                height: 100vh;
                background: radial-gradient(115% 90% at 50% -5%, #dbeafe 0%, #ebf4fe 32%, #f5f9ff 65%, #ffffff 100%);
                z-index: 9999;
                display: flex;
                justify-content: center;
                align-items: center;
                transition: opacity 0.7s cubic-bezier(0.4, 0, 0.2, 1);
                opacity: 1;
                -webkit-app-region: no-drag;
            }}
            
            #auth-layer.fade-out {{
                opacity: 0;
                pointer-events: none;
            }}
            
            /* Tarjeta de Login flotante estilo Google */
            .auth-card {{
                background: #ffffff;
                padding: 40px 44px;
                border-radius: 28px;
                text-align: center;
                max-width: 420px;
                width: 90%;
                box-shadow: 0 10px 30px rgba(0, 92, 178, 0.08), 0 2px 8px rgba(0, 0, 0, 0.03);
                border: 1px solid rgba(226, 232, 240, 0.75);
                animation: cardAppear 0.4s ease-out;
                -webkit-app-region: no-drag !important;
                user-select: text !important;
            }}
            
            .auth-card * {{
                -webkit-app-region: no-drag !important;
            }}
            
            @keyframes cardAppear {{
                from {{ opacity: 0; transform: translateY(12px) scale(0.98); }}
                to {{ opacity: 1; transform: translateY(0) scale(1); }}
            }}
            
            /* Logotipo de FrameOne */
            .splash-logo-box {{
                width: 100%;
                max-width: 230px;
                margin: 0 auto 18px auto;
                display: flex;
                justify-content: center;
                align-items: center;
            }}
            
            .splash-logo-img {{
                width: 100%;
                height: auto;
                border-radius: 16px;
                box-shadow: 0 6px 18px rgba(0, 92, 178, 0.16);
                display: block;
            }}
            
            .splash-title {{
                font-size: 22px;
                font-weight: 700;
                color: #0f172a;
                margin: 0 0 4px 0;
                letter-spacing: -0.3px;
            }}
            
            .splash-subtitle {{
                font-size: 13px;
                color: #64748b;
                margin: 0 0 22px 0;
            }}
            
            /* Formulario estilo Google */
            .form-group {{
                text-align: left;
                margin-bottom: 15px;
            }}
            
            .form-label {{
                display: block;
                font-size: 12.5px;
                font-weight: 600;
                color: #374151;
                margin-bottom: 6px;
            }}
            
            .form-input {{
                width: 100%;
                padding: 12px 16px;
                font-size: 14px;
                border: 1px solid #dadce0;
                border-radius: 12px;
                outline: none;
                transition: border-color 0.2s, box-shadow 0.2s;
                color: #111827;
                background: #ffffff;
                font-family: inherit;
            }}
            
            .form-input:focus {{
                border-color: #005cb2;
                box-shadow: 0 0 0 3px rgba(0, 92, 178, 0.15);
            }}
            
            .form-options {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 20px;
                font-size: 13px;
                color: #4b5563;
            }}
            
            .remember-label {{
                display: flex;
                align-items: center;
                gap: 8px;
                cursor: pointer;
                user-select: none;
            }}
            
            .remember-checkbox {{
                accent-color: #005cb2;
                width: 16px;
                height: 16px;
                cursor: pointer;
            }}
            
            /* Botón tipo Pill de Google */
            .btn-login {{
                width: 100%;
                padding: 12px 20px;
                font-size: 14.5px;
                font-weight: 600;
                color: #ffffff;
                background: #005cb2;
                border: none;
                border-radius: 24px;
                cursor: pointer;
                transition: all 0.2s ease;
                font-family: inherit;
                box-shadow: 0 4px 12px rgba(0, 92, 178, 0.2);
            }}
            
            .btn-login:hover {{
                background: #004b93;
                box-shadow: 0 6px 16px rgba(0, 92, 178, 0.28);
                transform: translateY(-1px);
            }}
            
            .btn-login:active {{
                transform: translateY(0);
            }}
            
            .btn-login:disabled {{
                background: #94a3b8;
                cursor: not-allowed;
                box-shadow: none;
                transform: none;
            }}
            
            /* Alertas de Estado suaves */
            .alert-box {{
                margin-top: 18px;
                padding: 12px 16px;
                border-radius: 12px;
                font-size: 13px;
                text-align: left;
                display: none;
            }}
            
            .alert-success {{
                background: #f0fdf4;
                border: 1px solid #bbf7d0;
                color: #166534;
            }}
            
            .alert-success-title {{
                font-weight: 700;
                font-size: 13.5px;
                color: #15803d;
                margin-bottom: 3px;
            }}
            
            .alert-error {{
                background: #fef2f2;
                border: 1px solid #fecaca;
                color: #991b1b;
            }}
            
            .alert-warning {{
                background: #fffbeb;
                border: 1px solid #fde68a;
                color: #92400e;
            }}
            
            .ocupantes-list {{
                margin-top: 6px;
                display: flex;
                flex-wrap: wrap;
                gap: 6px;
            }}
            
            .ocupante-badge {{
                background: #fef3c7;
                border: 1px solid #fcd34d;
                padding: 3px 8px;
                border-radius: 6px;
                font-size: 11.5px;
                font-weight: 600;
                color: #78350f;
            }}
            
            .auth-footer {{
                margin-top: 26px;
                font-size: 11.5px;
                line-height: 1.6;
                color: #9ca3af;
                user-select: text !important;
                -webkit-app-region: no-drag !important;
            }}
            
            .card-view {{
                transition: opacity 0.25s cubic-bezier(0.4, 0, 0.2, 1), transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            }}
            
            .validating-container {{
                padding: 16px 0 8px 0;
            }}
            
            .validating-box {{
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 10px;
                margin-top: 14px;
            }}
            
            .validating-spinner {{
                width: 18px;
                height: 18px;
                border: 2px solid #e2e8f0;
                border-top: 2px solid #005cb2;
                border-radius: 50%;
                animation: spin 0.8s linear infinite;
            }}
            
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
            
            .validating-text {{
                font-size: 14px;
                font-weight: 500;
                color: #475569;
                letter-spacing: -0.1px;
                transition: color 0.2s ease;
            }}
        </style>
    </head>
    <body>
        <!-- Barra de Controles Minimalista (Solo iconos grises pequeños) -->
        <div class="window-titlebar pywebview-drag-region">
            <div class="window-controls">
                <button class="win-btn" onclick="window.pywebview.api.minimize()" title="Minimizar">
                    <svg width="10" height="10" viewBox="0 0 10 10" fill="none" stroke="currentColor" stroke-width="1.3">
                        <path d="M1 5h8"/>
                    </svg>
                </button>
                <button class="win-btn" onclick="window.pywebview.api.toggle_maximize()" title="Maximizar">
                    <svg width="10" height="10" viewBox="0 0 10 10" fill="none" stroke="currentColor" stroke-width="1.3">
                        <rect x="1.5" y="1.5" width="7" height="7" rx="1"/>
                    </svg>
                </button>
                <button class="win-btn win-btn-close" onclick="window.pywebview.api.close()" title="Cerrar">
                    <svg width="10" height="10" viewBox="0 0 10 10" fill="none" stroke="currentColor" stroke-width="1.3">
                        <path d="M2 2l6 6M8 2l-6 6"/>
                    </svg>
                </button>
            </div>
        </div>

        <iframe id="app-frame" src="about:blank"></iframe>
        
        <div id="auth-layer">
            <div class="auth-card">
                <!-- Vista 1: Formulario de Login -->
                <div id="view-login" class="card-view">
                    <!-- Logotipo de FrameOne -->
                    <div class="splash-logo-box">
                        {logo_html}
                    </div>
                    
                    <h1 class="splash-title">Iniciar Sesión</h1>
                    <p class="splash-subtitle">Modelado de Naves Industriales para STAAD.Pro</p>
                    
                    <!-- Formulario -->
                    <form id="login-form" onsubmit="handleLoginSubmit(event)">
                        <div class="form-group">
                            <label class="form-label" for="user-email">Correo Electrónico</label>
                            <input class="form-input" type="email" id="user-email" placeholder="nombre@empresa.com" required autocomplete="email" />
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label" for="user-password">Contraseña</label>
                            <input class="form-input" type="password" id="user-password" placeholder="••••••••" required autocomplete="current-password" />
                        </div>
                        
                        <div class="form-options">
                            <label class="remember-label">
                                <input type="checkbox" id="remember-me" class="remember-checkbox" checked />
                                <span>Recordar en este equipo</span>
                            </label>
                        </div>
                        
                        <button type="submit" class="btn-login" id="btn-submit">
                            <span id="btn-text">Entrar a FrameOne</span>
                        </button>
                    </form>
                    
                    <div id="alert-box" class="alert-box"></div>
                    
                    <div class="auth-footer">
                        <div>FrameOne 2026</div>
                        <div style="margin-top: 4px;">&reg; Todos los derechos reservados.</div>
                    </div>
                </div>

                <!-- Vista 2: Validando Licencia -->
                <div id="view-validating" class="card-view validating-container" style="display: none; opacity: 0; transform: scale(0.96);">
                    <div class="splash-logo-box" style="margin-bottom: 20px;">
                        {logo_html}
                    </div>
                    <h1 class="splash-title" style="font-size: 24px; margin-bottom: 6px;">FrameOne</h1>
                    
                    <!-- Estado 1: Mientras valida en la nube -->
                    <div class="validating-box" id="validating-loader-box">
                        <div class="validating-spinner" id="validating-spinner"></div>
                        <span id="validating-status-text" class="validating-text">Validando licencia</span>
                    </div>

                    <!-- Estado 2: Una vez validada (se muestra durante 1 segundo antes de entrar) -->
                    <div id="license-info-box" style="display: none; margin-top: 14px; animation: cardAppear 0.3s ease-out;">
                        <div style="font-size: 14px; font-weight: 600; color: #0f172a; margin-bottom: 4px;">
                            Producto licenciado a <span id="empresa-name" style="color: #005cb2;"></span>
                        </div>
                        <div style="font-size: 12.5px; color: #64748b; font-weight: 500;">
                            Asientos ocupados <span id="asientos-count" style="font-weight: 600; color: #005cb2;"></span>
                        </div>
                    </div>
                </div>
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

            window.addEventListener('DOMContentLoaded', () => {{
                if (window.pywebview && window.pywebview.api) {{
                    loadSavedCreds();
                }} else {{
                    window.addEventListener('pywebviewready', loadSavedCreds);
                }}
            }});

            function loadSavedCreds() {{
                if (window.pywebview && window.pywebview.api) {{
                    window.pywebview.api.get_saved_credentials().then(creds => {{
                        if (creds && creds.email) {{
                            document.getElementById('user-email').value = creds.email;
                            if (creds.password) {{
                                document.getElementById('user-password').value = creds.password;
                            }}
                            document.getElementById('remember-me').checked = creds.remember !== false;
                        }}
                    }}).catch(err => console.error(err));
                }}
            }}

            function showAlert(type, title, message, ocupantes = []) {{
                const alertBox = document.getElementById('alert-box');
                alertBox.className = 'alert-box alert-' + type;
                
                let ocupantesHtml = '';
                if (ocupantes && ocupantes.length > 0) {{
                    ocupantesHtml = '<div class="ocupantes-list">' + 
                        ocupantes.map(pc => '<span class="ocupante-badge">' + pc + '</span>').join('') +
                        '</div>';
                }}
                
                if (type === 'success') {{
                    alertBox.innerHTML = `
                        <div class="alert-success-title">${{title}}</div>
                        <div>${{message}}</div>
                    `;
                }} else if (type === 'warning') {{
                    alertBox.innerHTML = `
                        <div style="font-weight:700;margin-bottom:3px;">${{title}}</div>
                        <div>${{message}}</div>
                        ${{ocupantesHtml}}
                    `;
                }} else {{
                    alertBox.innerHTML = `
                        <div style="font-weight:700;margin-bottom:3px;">${{title}}</div>
                        <div>${{message}}</div>
                    `;
                }}
                
                alertBox.style.display = 'block';
            }}

            function hideAlert() {{
                const alertBox = document.getElementById('alert-box');
                alertBox.style.display = 'none';
            }}

            async function handleLoginSubmit(event) {{
                event.preventDefault();
                hideAlert();
                
                const email = document.getElementById('user-email').value.trim();
                const password = document.getElementById('user-password').value.trim();
                const remember = document.getElementById('remember-me').checked;
                
                const viewLogin = document.getElementById('view-login');
                const viewValidating = document.getElementById('view-validating');
                const loaderBox = document.getElementById('validating-loader-box');
                const licenseBox = document.getElementById('license-info-box');
                
                // Reiniciar estado visual del validador
                if (loaderBox) loaderBox.style.display = 'flex';
                if (licenseBox) licenseBox.style.display = 'none';
                
                // Transición suave hacia la pantalla minimalista de validación
                viewLogin.style.opacity = '0';
                viewLogin.style.transform = 'scale(0.96)';
                
                await new Promise(r => setTimeout(r, 220));
                viewLogin.style.display = 'none';
                viewValidating.style.display = 'block';
                void viewValidating.offsetWidth;
                viewValidating.style.opacity = '1';
                viewValidating.style.transform = 'scale(1)';
                
                try {{
                    const response = await window.pywebview.api.login(email, password, remember);
                    
                    if (response && response.success) {{
                        const empresa = response.empresa || 'Empresa';
                        const enUso = response.cuentas_en_uso || 1;
                        const maxCuentas = response.max_cuentas || 1;
                        
                        // Mostrar la información de la licencia validada
                        if (loaderBox) loaderBox.style.display = 'none';
                        const empEl = document.getElementById('empresa-name');
                        const asEl = document.getElementById('asientos-count');
                        if (empEl) empEl.textContent = empresa;
                        if (asEl) asEl.textContent = enUso + '/' + maxCuentas;
                        if (licenseBox) licenseBox.style.display = 'block';
                        
                        // Pre-cargar el iframe de FrameOne
                        const appFrame = document.getElementById('app-frame');
                        appFrame.src = '{url}';
                        appFrame.style.display = 'block';
                        
                        // Mantener exactamente 1 segundo mostrando "Producto licenciado a..." y asientos
                        await new Promise(r => setTimeout(r, 1000));
                        
                        // Transición suave hacia el programa principal
                        const splash = document.getElementById('auth-layer');
                        if (splash) {{
                            splash.classList.add('fade-out');
                            setTimeout(() => {{ splash.style.display = 'none'; }}, 700);
                        }}
                        
                    }} else {{
                        // Si falla la validación, volver con animación suave al formulario de login
                        await new Promise(r => setTimeout(r, 300));
                        viewValidating.style.opacity = '0';
                        viewValidating.style.transform = 'scale(0.96)';
                        
                        await new Promise(r => setTimeout(r, 220));
                        viewValidating.style.display = 'none';
                        viewLogin.style.display = 'block';
                        void viewLogin.offsetWidth;
                        viewLogin.style.opacity = '1';
                        viewLogin.style.transform = 'scale(1)';
                        
                        const code = response.error_code || 'ERROR';
                        const msg = response.error_message || 'No se pudo iniciar sesión.';
                        
                        if (code === 'SEATS_FULL') {{
                            showAlert('warning', 'Límite de licencias alcanzado (' + response.cuentas_en_uso + '/' + response.max_cuentas + ')', 'Las licencias están siendo utilizadas por:', response.ocupantes);
                        }} else if (code === 'HWID_LIMIT_REACHED') {{
                            showAlert('error', 'Equipo no autorizado', msg);
                        }} else if (code === 'HWID_REVOKED') {{
                            showAlert('error', 'Equipo bloqueado', msg);
                        }} else if (code === 'INVALID_CREDENTIALS') {{
                            showAlert('error', 'Acceso denegado', 'Correo electrónico o contraseña incorrectos.');
                        }} else {{
                            showAlert('error', 'Error de conexión', msg);
                        }}
                    }}
                }} catch (error) {{
                    viewValidating.style.opacity = '0';
                    viewValidating.style.transform = 'scale(0.96)';
                    await new Promise(r => setTimeout(r, 220));
                    viewValidating.style.display = 'none';
                    viewLogin.style.display = 'block';
                    void viewLogin.offsetWidth;
                    viewLogin.style.opacity = '1';
                    viewLogin.style.transform = 'scale(1)';
                    
                    showAlert('error', 'Error inesperado', error.message || 'Error al comunicarse con el sistema de seguridad.');
                }}
            }}
        </script>
    </body>
    </html>
    """
    return html


# --- 3. Backend de Comunicación con la UI (PyWebView JS API) ---
class Api:
    def __init__(self):
        self.client = LicenseClient()
        self.session_token = None
        self.heartbeat_running = False
        self.heartbeat_thread = None
        self.server_process = None
        self.is_maximized = False

    def minimize(self):
        if webview.windows:
            webview.windows[0].minimize()

    def toggle_maximize(self):
        if webview.windows:
            win = webview.windows[0]
            if self.is_maximized:
                win.restore()
                self.is_maximized = False
            else:
                win.maximize()
                self.is_maximized = True

    def close(self):
        if webview.windows:
            self.cleanup()
            webview.windows[0].destroy()

    def get_saved_credentials(self):
        """Carga las credenciales recordadas del usuario."""
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"email": "", "password": "", "remember": True}

    def save_credentials(self, email, password, remember):
        """Guarda o limpia las credenciales según la preferencia del usuario."""
        try:
            if remember:
                data = {"email": email, "password": password, "remember": True}
            else:
                data = {"email": "", "password": "", "remember": False}
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception:
            pass

    def start_streamlit_server(self):
        """Arranca el servidor local de Streamlit si no está en ejecución."""
        if not is_port_in_use(PORT):
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0
            
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
            self.server_process = subprocess.Popen(
                cmd, 
                startupinfo=startupinfo, 
                cwd=base_dir,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )

    def _heartbeat_worker(self):
        """Hilo en segundo plano que emite un pulso cada HEARTBEAT_INTERVAL_SECONDS."""
        while self.heartbeat_running and self.session_token:
            time.sleep(HEARTBEAT_INTERVAL_SECONDS)
            if not self.heartbeat_running or not self.session_token:
                break
            try:
                res = self.client.heartbeat(self.session_token)
                if not res.get("active", False):
                    self.heartbeat_running = False
                    self.cleanup()
                    if webview.windows:
                        webview.windows[0].destroy()
                    break
            except Exception as e:
                print(f"[Seguridad] Error en heartbeat: {e}")

    def login(self, email, password, remember):
        """
        Valida las credenciales contra Supabase.
        Si es exitoso, inicia el Heartbeat y arranca el servidor Streamlit.
        """
        res = self.client.login_and_acquire_seat(email, password)
        
        if res.get("success"):
            self.session_token = res.get("token")
            self.save_credentials(email, password, remember)
            
            # Iniciar hilo de latidos (Heartbeat)
            self.heartbeat_running = True
            self.heartbeat_thread = threading.Thread(target=self._heartbeat_worker, daemon=True)
            self.heartbeat_thread.start()
            
            # Iniciar servidor Streamlit
            self.start_streamlit_server()
            
            # Esperar a que el servidor responda
            wait_for_server(URL, timeout=30)
            
            return {
                "success": True,
                "empresa": res.get("empresa"),
                "cuentas_en_uso": res.get("cuentas_en_uso"),
                "max_cuentas": res.get("max_cuentas")
            }
        else:
            return res

    def cleanup(self):
        """Libera el asiento y detiene los procesos."""
        self.heartbeat_running = False
        if self.session_token:
            try:
                self.client.release_seat(self.session_token)
            except Exception:
                pass
            self.session_token = None
        if self.server_process:
            try:
                self.server_process.terminate()
            except Exception:
                pass
            self.server_process = None


def main():
    api_instance = Api()

    # Pre-arrancar el servidor local de Streamlit en segundo plano (Warm-up silencioso)
    # Así, para cualquiera que ejecute el .exe, la validación y entrada se sienten instantáneas
    api_instance.start_streamlit_server()

    # Calcular coordenadas para iniciar siempre perfectamente centrado en pantalla
    w, h = 1280, 800
    pos_x, pos_y = None, None
    try:
        if hasattr(webview, 'screens') and webview.screens:
            screen = webview.screens[0]
            pos_x = max(0, (screen.width - w) // 2)
            pos_y = max(0, (screen.height - h) // 2)
    except Exception:
        pass

    # Ventana sin barra estándar del SO (frameless=True), con controles flotantes minimalistas
    window_kwargs = dict(
        title='FrameOne StandAlone', 
        html=get_app_container_html(URL), 
        width=w, 
        height=h, 
        min_size=(960, 640), 
        resizable=True, 
        frameless=True,
        easy_drag=False,
        background_color='#FFFFFF',
        text_select=True,
        js_api=api_instance
    )
    if pos_x is not None and pos_y is not None:
        window_kwargs['x'] = pos_x
        window_kwargs['y'] = pos_y

    window = webview.create_window(**window_kwargs)
    
    def on_closing():
        api_instance.cleanup()
        return True

    window.events.closing += on_closing

    webview.start(icon=icon_ico)
    api_instance.cleanup()


if __name__ == "__main__":
    main()
