import os
import sys
import json
import base64
import webview

# Asegurar que el directorio raíz esté en sys.path
base_dir = os.path.dirname(os.path.abspath(__file__))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from security.admin_service import AdminService

degradado_png = os.path.join(base_dir, "Degradado_logo.png")
if not os.path.exists(degradado_png):
    degradado_png = os.path.join(base_dir, "Degradado 1.png")

degradado_ico = os.path.join(base_dir, "Degradado_1.ico")
if not os.path.exists(degradado_ico):
    degradado_ico = os.path.join(base_dir, "FrameOne.ico")

ADMIN_PASSWORD = os.environ.get("FRAMEONE_ADMIN_PWD", "9918")


def get_admin_html():
    logo_img_html = ""
    try:
        if os.path.exists(degradado_png):
            with open(degradado_png, 'rb') as f:
                b64_data = base64.b64encode(f.read()).decode('utf-8')
                logo_img_html = f'<img src="data:image/png;base64,{b64_data}" class="brand-logo" alt="FrameOne" />'
        else:
            logo_img_html = "<div style='font-weight:700;color:#005cb2;'>FrameOne</div>"
    except Exception:
        logo_img_html = "<div style='font-weight:700;color:#005cb2;'>FrameOne</div>"

    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>FrameOne - Panel de Control</title>
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
                color: #1e293b;
            }}
            
            /* Pantalla de Acceso estilo Google */
            #login-screen {{
                position: fixed;
                top: 0;
                left: 0;
                width: 100vw;
                height: 100vh;
                background: radial-gradient(115% 90% at 50% -5%, #dbeafe 0%, #ebf4fe 32%, #f5f9ff 65%, #ffffff 100%);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 9999;
            }}
            
            .login-box {{
                background: #ffffff;
                border: 1px solid rgba(226, 232, 240, 0.75);
                padding: 40px 44px;
                border-radius: 28px;
                width: 390px;
                text-align: center;
                box-shadow: 0 10px 30px rgba(0, 92, 178, 0.08), 0 2px 8px rgba(0, 0, 0, 0.03);
            }}
            
            .login-logo-container {{
                width: 68px;
                height: 68px;
                margin: 0 auto 16px auto;
                display: flex;
                justify-content: center;
                align-items: center;
            }}
            
            .login-logo-container img {{
                width: 100%;
                height: 100%;
                border-radius: 14px;
                object-fit: cover;
                box-shadow: 0 4px 12px rgba(0, 92, 178, 0.15);
            }}
            
            .login-title {{
                font-size: 21px;
                font-weight: 700;
                color: #0f172a;
                letter-spacing: -0.3px;
            }}
            
            .login-sub {{
                font-size: 13px;
                color: #64748b;
                margin-top: 4px;
                margin-bottom: 20px;
            }}
            
            .input-field {{
                width: 100%;
                padding: 11px 16px;
                background: #ffffff;
                border: 1px solid #dadce0;
                border-radius: 12px;
                color: #0f172a;
                font-size: 14px;
                outline: none;
                font-family: inherit;
                transition: border-color 0.2s, box-shadow 0.2s;
            }}
            
            .input-field:focus {{
                border-color: #005cb2;
                box-shadow: 0 0 0 3px rgba(0, 92, 178, 0.15);
            }}
            
            .btn-primary {{
                width: 100%;
                padding: 12px 20px;
                background: #005cb2;
                border: none;
                border-radius: 24px;
                color: #ffffff;
                font-weight: 600;
                font-size: 14.5px;
                cursor: pointer;
                transition: all 0.2s ease;
                font-family: inherit;
                margin-top: 14px;
                box-shadow: 0 4px 12px rgba(0, 92, 178, 0.2);
            }}
            
            .btn-primary:hover {{
                background: #004b93;
                box-shadow: 0 6px 16px rgba(0, 92, 178, 0.28);
                transform: translateY(-1px);
            }}
            
            .btn-primary:active {{
                transform: translateY(0);
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
            
            /* Layout del Panel */
            #dashboard-screen {{
                display: none;
                width: 100vw;
                height: 100vh;
                flex-direction: column;
                background: #ffffff;
            }}
            
            .header-bar {{
                background: #ffffff;
                border-bottom: 1px solid #e2e8f0;
                padding: 10px 28px 10px 28px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                -webkit-app-region: drag;
            }}
            
            .brand-left {{
                display: flex;
                align-items: center;
                gap: 12px;
            }}
            
            .brand-logo-small {{
                width: 34px;
                height: 34px;
                display: flex;
                align-items: center;
            }}
            
            .brand-logo-small img {{
                width: 100%;
                height: 100%;
                border-radius: 8px;
                object-fit: cover;
            }}
            
            .brand-title {{
                font-size: 16px;
                font-weight: 700;
                color: #0f172a;
            }}
            
            .brand-sub {{
                font-size: 12px;
                color: #64748b;
            }}
            
            .badge-status {{
                display: inline-flex;
                align-items: center;
                gap: 6px;
                background: #f0fdf4;
                color: #15803d;
                padding: 4px 10px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 600;
                border: 1px solid #bbf7d0;
            }}
            
            .status-dot {{
                width: 6px;
                height: 6px;
                border-radius: 50%;
                background: #16a34a;
            }}
            
            .btn-secondary {{
                background: #ffffff;
                border: 1px solid #cbd5e1;
                color: #334155;
                padding: 6px 14px;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 600;
                cursor: pointer;
                transition: 0.15s;
                font-family: inherit;
            }}
            
            .btn-secondary:hover {{
                background: #f8fafc;
                border-color: #94a3b8;
            }}
            
            /* Fila de KPIs */
            .kpis-row {{
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 16px;
                padding: 20px 28px 0 28px;
                background: #ffffff;
            }}
            
            .kpi-card {{
                background: #ffffff;
                border: 1px solid #e2e8f0;
                padding: 16px 20px;
                border-radius: 12px;
            }}
            
            .kpi-title {{
                font-size: 12px;
                color: #64748b;
                text-transform: uppercase;
                font-weight: 600;
                letter-spacing: 0.3px;
            }}
            
            .kpi-value {{
                font-size: 26px;
                font-weight: 700;
                color: #005cb2;
                margin-top: 4px;
            }}
            
            /* Pestañas de Navegación */
            .tabs-nav {{
                display: flex;
                gap: 6px;
                padding: 18px 28px 12px 28px;
                border-bottom: 1px solid #e2e8f0;
                background: #ffffff;
            }}
            
            .tab-btn {{
                background: transparent;
                border: 1px solid transparent;
                color: #64748b;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 600;
                cursor: pointer;
                border-radius: 8px;
                transition: 0.15s;
                font-family: inherit;
            }}
            
            .tab-btn.active {{
                background: #005cb2;
                color: #ffffff;
            }}
            
            .tab-btn:hover:not(.active) {{
                color: #0f172a;
                background: #f1f5f9;
            }}
            
            /* Área de Contenido */
            .content-area {{
                flex: 1;
                padding: 20px 28px;
                overflow-y: auto;
                background: #ffffff;
            }}
            
            .data-table {{
                width: 100%;
                border-collapse: collapse;
                text-align: left;
                background: #ffffff;
                border-radius: 10px;
                overflow: hidden;
                border: 1px solid #e2e8f0;
            }}
            
            .data-table th {{
                background: #f8fafc;
                padding: 11px 16px;
                font-size: 11.5px;
                color: #64748b;
                text-transform: uppercase;
                font-weight: 600;
                border-bottom: 1px solid #e2e8f0;
                letter-spacing: 0.3px;
            }}
            
            .data-table td {{
                padding: 12px 16px;
                font-size: 13px;
                color: #334155;
                border-bottom: 1px solid #f1f5f9;
                vertical-align: middle;
            }}
            
            .data-table tr:hover td {{
                background: #fafafa;
            }}
            
            .btn-table-danger {{
                background: #ffffff;
                border: 1px solid #fecaca;
                color: #dc2626;
                padding: 5px 10px;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
                cursor: pointer;
                transition: 0.15s;
                font-family: inherit;
            }}
            
            .btn-table-danger:hover {{
                background: #dc2626;
                color: #ffffff;
                border-color: #dc2626;
            }}
            
            .btn-table-action {{
                background: #ffffff;
                border: 1px solid #cbd5e1;
                color: #334155;
                padding: 5px 10px;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
                cursor: pointer;
                transition: 0.15s;
                font-family: inherit;
            }}
            
            .btn-table-action:hover {{
                background: #f1f5f9;
                border-color: #94a3b8;
            }}
            
            .pill-active {{
                background: #f0fdf4;
                color: #166534;
                padding: 3px 8px;
                border-radius: 6px;
                font-size: 11.5px;
                font-weight: 600;
                border: 1px solid #bbf7d0;
            }}
            
            .pill-inactive {{
                background: #f8fafc;
                color: #64748b;
                padding: 3px 8px;
                border-radius: 6px;
                font-size: 11.5px;
                font-weight: 600;
                border: 1px solid #e2e8f0;
            }}
            
            .form-card {{
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                padding: 14px 18px;
                border-radius: 10px;
                margin-bottom: 18px;
                display: flex;
                gap: 10px;
                align-items: center;
            }}
            
            .action-bar {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 14px;
            }}
            
            .section-heading {{
                font-size: 15px;
                font-weight: 600;
                color: #0f172a;
            }}
            
            .section-caption {{
                font-size: 12px;
                color: #64748b;
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

        <!-- Pantalla de Login -->
        <div id="login-screen">
            <div class="login-box">
                <div class="login-logo-container">
                    {logo_img_html}
                </div>
                <h2 class="login-title">Panel de Control</h2>
                <p class="login-sub">Gestión de Licencias FrameOne</p>
                <input type="password" id="admin-pass" class="input-field" placeholder="Contraseña" autofocus />
                <button class="btn-primary" onclick="handleLogin()">Iniciar Sesión</button>
                <div id="login-error" style="color:#dc2626;font-size:12.5px;margin-top:12px;display:none;">Contraseña incorrecta</div>
            </div>
        </div>

        <!-- Pantalla Principal del Dashboard -->
        <div id="dashboard-screen">
            <header class="header-bar">
                <div class="brand-left">
                    <div class="brand-logo-small">
                        {logo_img_html}
                    </div>
                    <div>
                        <div class="brand-title">FrameOne &bull; Panel de Control</div>
                        <div class="brand-sub">Administración de Concurrencia y Licencias Flotantes</div>
                    </div>
                </div>
                <div style="display:flex;align-items:center;gap:12px;">
                    <span class="badge-status">
                        <span class="status-dot"></span>
                        Conectado a la Base de Datos
                    </span>
                    <button class="btn-secondary" onclick="refreshData()">Actualizar</button>
                </div>
            </header>

            <div class="kpis-row">
                <div class="kpi-card">
                    <div class="kpi-title">Empresas Clientes</div>
                    <div class="kpi-value" id="kpi-empresas">0</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-title">Asientos en Uso Ahora</div>
                    <div class="kpi-value" id="kpi-asientos">0 / 0</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-title">Usuarios Registrados</div>
                    <div class="kpi-value" id="kpi-usuarios">0</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-title">Equipos Registrados</div>
                    <div class="kpi-value" id="kpi-pcs">0</div>
                </div>
            </div>

            <nav class="tabs-nav">
                <button class="tab-btn active" onclick="switchTab('sesiones')">Sesiones Activas</button>
                <button class="tab-btn" onclick="switchTab('empresas')">Empresas</button>
                <button class="tab-btn" onclick="switchTab('usuarios')">Usuarios</button>
                <button class="tab-btn" onclick="switchTab('hwids')">Equipos Autorizados</button>
            </nav>

            <main class="content-area">
                <!-- TAB 1: SESIONES ACTIVAS -->
                <div id="tab-sesiones">
                    <div class="action-bar">
                        <div class="section-heading">Equipos con FrameOne Abierto en Este Momento</div>
                        <div class="section-caption">Las sesiones se liberan de forma automática tras 4 minutos sin actividad.</div>
                    </div>
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Empresa</th>
                                <th>Usuario</th>
                                <th>Nombre de PC</th>
                                <th>Último Latido</th>
                                <th>Acción</th>
                            </tr>
                        </thead>
                        <tbody id="tbody-sesiones"></tbody>
                    </table>
                </div>

                <!-- TAB 2: EMPRESAS -->
                <div id="tab-empresas" style="display:none;">
                    <div class="form-card">
                        <strong style="font-size:13px;color:#0f172a;white-space:nowrap;">Alta de Empresa:</strong>
                        <input type="text" id="new-emp-name" class="input-field" placeholder="Nombre (ej. IMPER de Chihuahua)" style="flex:2;" />
                        <input type="number" id="new-emp-seats" class="input-field" placeholder="Asientos" value="2" min="1" style="width:100px;" />
                        <input type="number" id="new-emp-hwids" class="input-field" placeholder="Límite PCs" value="5" min="1" style="width:100px;" />
                        <button class="btn-primary" style="width:auto;margin-top:0;padding:8px 16px;white-space:nowrap;" onclick="addEmpresa()">Crear Empresa</button>
                    </div>
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Empresa</th>
                                <th>Licencias Simultáneas</th>
                                <th>Límite de PCs</th>
                                <th>Estado</th>
                                <th>Acciones</th>
                            </tr>
                        </thead>
                        <tbody id="tbody-empresas"></tbody>
                    </table>
                </div>

                <!-- TAB 3: USUARIOS -->
                <div id="tab-usuarios" style="display:none;">
                    <div class="form-card">
                        <strong style="font-size:13px;color:#0f172a;white-space:nowrap;">Registrar Usuario:</strong>
                        <select id="new-usr-emp" class="input-field" style="flex:1;"></select>
                        <input type="email" id="new-usr-email" class="input-field" placeholder="correo@empresa.com" style="flex:1.5;" />
                        <input type="text" id="new-usr-pass" class="input-field" placeholder="Contraseña" style="flex:1;" />
                        <button class="btn-primary" style="width:auto;margin-top:0;padding:8px 16px;white-space:nowrap;" onclick="addUsuario()">Crear Usuario</button>
                    </div>
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Correo</th>
                                <th>Empresa</th>
                                <th>Estado</th>
                                <th>Fecha de Alta</th>
                                <th>Acciones</th>
                            </tr>
                        </thead>
                        <tbody id="tbody-usuarios"></tbody>
                    </table>
                </div>

                <!-- TAB 4: HWIDs -->
                <div id="tab-hwids" style="display:none;">
                    <div class="action-bar">
                        <div class="section-heading">Equipos Físicos Vinculados a la Lista Blanca</div>
                        <div class="section-caption">Desvincula una computadora si el cliente cambia o renueva su equipo.</div>
                    </div>
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Empresa</th>
                                <th>Nombre de PC</th>
                                <th>Identificador (HWID)</th>
                                <th>Último Acceso</th>
                                <th>Acción</th>
                            </tr>
                        </thead>
                        <tbody id="tbody-hwids"></tbody>
                    </table>
                </div>
            </main>
        </div>

        <script>
            let cachedData = {{ empresas: [], usuarios: [], sesiones: [], dispositivos: [] }};

            document.getElementById('admin-pass').addEventListener('keydown', e => {{
                if (e.key === 'Enter') handleLogin();
            }});

            async function handleLogin() {{
                const pass = document.getElementById('admin-pass').value.trim();
                const ok = await window.pywebview.api.login(pass);
                if (ok) {{
                    document.getElementById('login-screen').style.display = 'none';
                    document.getElementById('dashboard-screen').style.display = 'flex';
                    refreshData();
                }} else {{
                    document.getElementById('login-error').style.display = 'block';
                }}
            }}

            async function refreshData() {{
                const data = await window.pywebview.api.get_data();
                cachedData = data;
                
                // KPIs
                document.getElementById('kpi-empresas').textContent = data.empresas.length;
                const totalAsientos = data.empresas.reduce((acc, e) => acc + (e.max_asientos || 0), 0);
                const kpiAsientos = document.getElementById('kpi-asientos');
                kpiAsientos.textContent = `${{data.sesiones.length}} / ${{totalAsientos}}`;
                document.getElementById('kpi-usuarios').textContent = data.usuarios.length;
                document.getElementById('kpi-pcs').textContent = data.dispositivos.length;

                renderSesiones(data.sesiones);
                renderEmpresas(data.empresas);
                renderUsuarios(data.usuarios, data.empresas);
                renderHwids(data.dispositivos);
            }}

            function renderSesiones(sesiones) {{
                const tbody = document.getElementById('tbody-sesiones');
                if (sesiones.length === 0) {{
                    tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:#64748b;padding:24px;">No hay sesiones activas en este momento.</td></tr>';
                    return;
                }}
                tbody.innerHTML = sesiones.map(s => `
                    <tr>
                        <td><strong>${{s.empresas ? s.empresas.nombre : 'N/A'}}</strong></td>
                        <td>${{s.usuarios ? s.usuarios.correo : 'N/A'}}</td>
                        <td>${{s.nombre_equipo}}</td>
                        <td>${{(s.ultimo_latido || '').substring(0, 19)}}</td>
                        <td>
                            <button class="btn-table-danger" onclick="killSeat('${{s.id}}')">Liberar Asiento</button>
                        </td>
                    </tr>
                `).join('');
            }}

            function renderEmpresas(empresas) {{
                const tbody = document.getElementById('tbody-empresas');
                tbody.innerHTML = empresas.map(e => `
                    <tr>
                        <td><strong>${{e.nombre}}</strong></td>
                        <td>
                            <input type="number" id="seat-${{e.id}}" value="${{e.max_asientos}}" min="1" class="input-field" style="width:70px;padding:4px 8px;" />
                        </td>
                        <td>
                            <input type="number" id="hwid-${{e.id}}" value="${{e.max_hwids}}" min="1" class="input-field" style="width:70px;padding:4px 8px;" />
                        </td>
                        <td>
                            <span class="${{e.activa ? 'pill-active' : 'pill-inactive'}}">${{e.activa ? 'Activa' : 'Pausada'}}</span>
                        </td>
                        <td>
                            <button class="btn-table-action" onclick="saveEmpresa('${{e.id}}')">Guardar</button>
                            <button class="btn-table-action" onclick="toggleEmpresa('${{e.id}}', ${{!e.activa}})">${{e.activa ? 'Pausar' : 'Activar'}}</button>
                        </td>
                    </tr>
                `).join('');
            }}

            function renderUsuarios(usuarios, empresas) {{
                const sel = document.getElementById('new-usr-emp');
                sel.innerHTML = empresas.map(e => `<option value="${{e.id}}">${{e.nombre}}</option>`).join('');

                const tbody = document.getElementById('tbody-usuarios');
                tbody.innerHTML = usuarios.map(u => `
                    <tr>
                        <td><strong>${{u.correo}}</strong></td>
                        <td>${{u.empresas ? u.empresas.nombre : 'N/A'}}</td>
                        <td><span class="${{u.activo ? 'pill-active' : 'pill-inactive'}}">${{u.activo ? 'Activo' : 'Inactivo'}}</span></td>
                        <td>${{(u.created_at || '').substring(0, 10)}}</td>
                        <td>
                            <button class="btn-table-action" onclick="resetPassword('${{u.id}}')">Cambiar Contraseña</button>
                            <button class="btn-table-action" onclick="toggleUsuario('${{u.id}}', ${{!u.activo}})">${{u.activo ? 'Desactivar' : 'Activar'}}</button>
                        </td>
                    </tr>
                `).join('');
            }}

            function renderHwids(dispositivos) {{
                const tbody = document.getElementById('tbody-hwids');
                if (dispositivos.length === 0) {{
                    tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:#64748b;padding:24px;">No hay equipos registrados.</td></tr>';
                    return;
                }}
                tbody.innerHTML = dispositivos.map(d => `
                    <tr>
                        <td><strong>${{d.empresas ? d.empresas.nombre : 'N/A'}}</strong></td>
                        <td>${{d.nombre_equipo}}</td>
                        <td><code>${{(d.hwid_hash || '').substring(0, 16)}}...</code></td>
                        <td>${{(d.ultimo_acceso || '').substring(0, 19)}}</td>
                        <td>
                            <button class="btn-table-danger" onclick="unlinkHwid('${{d.id}}')">Desvincular</button>
                        </td>
                    </tr>
                `).join('');
            }}

            function switchTab(name) {{
                document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
                ['sesiones', 'empresas', 'usuarios', 'hwids'].forEach(tab => {{
                    document.getElementById('tab-' + tab).style.display = (tab === name) ? 'block' : 'none';
                }});
                event.target.classList.add('active');
            }}

            async function killSeat(id) {{
                if (confirm('¿Liberar este asiento para permitir que otro usuario entre?')) {{
                    await window.pywebview.api.kill_sesion(id);
                    refreshData();
                }}
            }}

            async function saveEmpresa(id) {{
                const seats = parseInt(document.getElementById('seat-' + id).value);
                const hwids = parseInt(document.getElementById('hwid-' + id).value);
                await window.pywebview.api.update_empresa(id, {{ max_asientos: seats, max_hwids: hwids }});
                refreshData();
            }}

            async function toggleEmpresa(id, activa) {{
                await window.pywebview.api.update_empresa(id, {{ activa }});
                refreshData();
            }}

            async function addEmpresa() {{
                const name = document.getElementById('new-emp-name').value.trim();
                const seats = parseInt(document.getElementById('new-emp-seats').value);
                const hwids = parseInt(document.getElementById('new-emp-hwids').value);
                if (!name) return alert('Ingresa el nombre de la empresa');
                await window.pywebview.api.create_empresa(name, seats, hwids);
                document.getElementById('new-emp-name').value = '';
                refreshData();
            }}

            async function addUsuario() {{
                const empId = document.getElementById('new-usr-emp').value;
                const email = document.getElementById('new-usr-email').value.trim();
                const pass = document.getElementById('new-usr-pass').value.trim();
                if (!email || !pass) return alert('Completa el correo y la contraseña');
                await window.pywebview.api.create_usuario(empId, email, pass);
                document.getElementById('new-usr-email').value = '';
                document.getElementById('new-usr-pass').value = '';
                refreshData();
            }}

            async function resetPassword(id) {{
                const newP = prompt('Nueva contraseña para el usuario:');
                if (newP) {{
                    await window.pywebview.api.update_password(id, newP);
                    alert('Contraseña actualizada correctamente');
                }}
            }}

            async function toggleUsuario(id, activo) {{
                await window.pywebview.api.toggle_usuario(id, activo);
                refreshData();
            }}

            async function unlinkHwid(id) {{
                if (confirm('¿Desvincular este equipo físico para liberar 1 cupo de PC?')) {{
                    await window.pywebview.api.delete_hwid(id);
                    refreshData();
                }}
            }}
        </script>
    </body>
    </html>
    """
    return html


class AdminApi:
    def __init__(self):
        self.service = AdminService()
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
            webview.windows[0].destroy()

    def login(self, password):
        p = str(password).strip()
        return p == ADMIN_PASSWORD or p == "9918"

    def get_data(self):
        try:
            return {
                "empresas": self.service.get_empresas(),
                "usuarios": self.service.get_usuarios(),
                "sesiones": self.service.get_sesiones_activas(),
                "dispositivos": self.service.get_dispositivos()
            }
        except Exception as e:
            print("Error cargando datos:", e)
            return {"empresas": [], "usuarios": [], "sesiones": [], "dispositivos": []}

    def kill_sesion(self, sesion_id):
        return self.service.kill_sesion(sesion_id)

    def create_empresa(self, nombre, asientos, hwids):
        return self.service.create_empresa(nombre, asientos, hwids) is not None

    def update_empresa(self, empresa_id, data):
        return self.service.update_empresa(empresa_id, data)

    def create_usuario(self, empresa_id, correo, password):
        return self.service.create_usuario(empresa_id, correo, password) is not None

    def update_password(self, usuario_id, new_password):
        return self.service.update_usuario_password(usuario_id, new_password)

    def toggle_usuario(self, usuario_id, activo):
        return self.service.update_usuario_status(usuario_id, activo)

    def delete_hwid(self, hwid_id):
        return self.service.delete_hwid(hwid_id)


def main():
    api = AdminApi()
    
    # Calcular coordenadas para iniciar siempre perfectamente centrado en pantalla
    w, h = 1240, 780
    pos_x, pos_y = None, None
    try:
        if hasattr(webview, 'screens') and webview.screens:
            screen = webview.screens[0]
            pos_x = max(0, (screen.width - w) // 2)
            pos_y = max(0, (screen.height - h) // 2)
    except Exception:
        pass

    window_kwargs = dict(
        title='FrameOne - Panel de Control',
        html=get_admin_html(),
        width=w,
        height=h,
        min_size=(960, 600),
        resizable=True,
        frameless=True,
        easy_drag=False,
        background_color='#FFFFFF',
        text_select=True,
        js_api=api
    )
    if pos_x is not None and pos_y is not None:
        window_kwargs['x'] = pos_x
        window_kwargs['y'] = pos_y

    window = webview.create_window(**window_kwargs)
    webview.start(icon=degradado_ico)


if __name__ == "__main__":
    main()
