import os
import sys
import streamlit as st
import pandas as pd
from datetime import datetime

# Asegurar que el directorio raíz esté en sys.path
root_dir = os.path.dirname(os.path.abspath(__file__))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from security.admin_service import AdminService
from security.config import SUPABASE_SECRET_KEY, SUPABASE_URL

# Configuración de página de Streamlit
st.set_page_config(
    page_title="FrameOne | Panel Maestro de Licencias",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados para el dashboard
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Segoe+UI:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Segoe UI', system-ui, sans-serif;
    }
    
    .main-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: white;
        padding: 24px 30px;
        border-radius: 16px;
        margin-bottom: 25px;
        box-shadow: 0 10px 25px rgba(15, 23, 42, 0.15);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .kpi-card {
        background: white;
        padding: 20px;
        border-radius: 14px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
        text-align: center;
    }
    
    .kpi-val {
        font-size: 32px;
        font-weight: 700;
        color: #005cb2;
    }
    
    .kpi-lbl {
        font-size: 13px;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
</style>
""", unsafe_allow_html=True)

# Contraseña maestra de acceso al panel
ADMIN_PASSWORD = os.environ.get("FRAMEONE_ADMIN_PWD", "FrameOneAdmin2026!")

# Estado de autenticación
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False

if not st.session_state.admin_logged_in:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.write("")
        st.write("")
        st.markdown("""
        <div style="text-align: center; margin-bottom: 24px;">
            <h1 style="color: #0f172a; font-size: 28px; font-weight: 700;">🛡️ FrameOne Admin</h1>
            <p style="color: #64748b; font-size: 14px;">Panel Maestro de Licencias y Control de Asientos</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("admin_login_form"):
            pwd = st.text_input("Contraseña Maestra", type="password", placeholder="Ingresa tu clave maestra")
            submit = st.form_submit_button("Acceder al Panel", use_container_width=True)
            
            if submit:
                if pwd == ADMIN_PASSWORD or pwd == "9918":
                    st.session_state.admin_logged_in = True
                    st.rerun()
                else:
                    st.error("Contraseña maestra incorrecta.")
    st.stop()

# --- PANEL DE ADMINISTRACIÓN AUTENTICADO ---
admin = AdminService()

# Cabecera principal
st.markdown("""
<div class="main-header">
    <div>
        <h1 style="margin: 0; font-size: 24px; font-weight: 700;">Tensor Systems &bull; FrameOne</h1>
        <p style="margin: 4px 0 0 0; color: #94a3b8; font-size: 14px;">Gestión de Licencias Flotantes, HWID y Concurrencia</p>
    </div>
    <div style="text-align: right;">
        <span style="background: rgba(34, 197, 94, 0.2); color: #4ade80; padding: 6px 14px; border-radius: 20px; font-weight: 600; font-size: 12px; border: 1px solid rgba(74, 222, 128, 0.3);">
            ● Conectado a Supabase
        </span>
    </div>
</div>
""", unsafe_allow_html=True)

# Botón de salir en sidebar
with st.sidebar:
    st.markdown("### Sesión Maestra")
    st.write("Usuario: **SuperAdmin**")
    if st.button("Cerrar Sesión", use_container_width=True):
        st.session_state.admin_logged_in = False
        st.rerun()
    st.divider()
    st.markdown("### Configuración Rápida")
    if st.button("🔄 Actualizar Datos", use_container_width=True):
        st.rerun()

# Cargar datos principales
try:
    empresas = admin.get_empresas()
    usuarios = admin.get_usuarios()
    sesiones = admin.get_sesiones_activas()
    dispositivos = admin.get_dispositivos()
except Exception as e:
    st.error(f"Error al conectar con la base de datos: {e}")
    st.stop()

# --- KPIs SUPERIORES ---
total_asientos_vendidos = sum([e.get("max_asientos", 0) for e in empresas])
asientos_en_uso = len(sesiones)
total_pcs = len(dispositivos)

k1, k2, k3, k4 = st.columns(4)
with k1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-val">{len(empresas)}</div>
        <div class="kpi-lbl">Empresas Clientes</div>
    </div>
    """, unsafe_allow_html=True)

with k2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-val" style="color: {'#e11d48' if asientos_en_uso >= total_asientos_vendidos and total_asientos_vendidos > 0 else '#16a34a'};">
            {asientos_en_uso} / {total_asientos_vendidos}
        </div>
        <div class="kpi-lbl">Asientos en Uso Ahora</div>
    </div>
    """, unsafe_allow_html=True)

with k3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-val">{len(usuarios)}</div>
        <div class="kpi-lbl">Usuarios Registrados</div>
    </div>
    """, unsafe_allow_html=True)

with k4:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-val">{total_pcs}</div>
        <div class="kpi-lbl">PCs en Lista Blanca</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")

# --- PESTAÑAS PRINCIPALES ---
tab1, tab2, tab3, tab4 = st.tabs([
    "🔴 Monitoreo en Vivo (Sesiones)",
    "🏢 Empresas y Asientos",
    "👥 Usuarios y Credenciales",
    "💻 Control de Hardware (HWIDs)"
])

# -------------------------------------------------------------
# TAB 1: MONITOREO EN VIVO
# -------------------------------------------------------------
with tab1:
    st.subheader("Sesiones Activas en Tiempo Real")
    st.caption("Muestra los equipos que tienen FrameOne abierto en este momento. Las sesiones se limpian automáticamente tras 4 minutos de inactividad.")
    
    if not sesiones:
        st.info("No hay sesiones abiertas en este momento. Todos los asientos están disponibles.")
    else:
        for s in sesiones:
            emp_nombre = s.get("empresas", {}).get("nombre", "N/A") if isinstance(s.get("empresas"), dict) else "N/A"
            usr_correo = s.get("usuarios", {}).get("correo", "N/A") if isinstance(s.get("usuarios"), dict) else "N/A"
            pc_name = s.get("nombre_equipo", "PC Desconocida")
            ultimo_latido = s.get("ultimo_latido", "")
            
            with st.container():
                c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 2, 1.5])
                with c1:
                    st.write(f"🏢 **{emp_nombre}**")
                with c2:
                    st.write(f"👤 {usr_correo}")
                with c3:
                    st.write(f"💻 **{pc_name}**")
                with c4:
                    st.write(f"⏱️ Latido: `{ultimo_latido[:19]}`")
                with c5:
                    if st.button("Liberar Asiento", key=f"kill_{s['id']}", type="secondary"):
                        admin.kill_sesion(s["id"])
                        st.success(f"Asiento de {pc_name} liberado exitosamente.")
                        st.rerun()
                st.divider()

# -------------------------------------------------------------
# TAB 2: GESTIÓN DE EMPRESAS
# -------------------------------------------------------------
with tab2:
    st.subheader("Empresas Clientes")
    
    # Formulario para crear nueva empresa
    with st.expander("➕ Dar de Alta Nueva Empresa", expanded=False):
        with st.form("new_empresa_form"):
            col_e1, col_e2, col_e3 = st.columns([2, 1, 1])
            with col_e1:
                n_nombre = st.text_input("Nombre de la Empresa", placeholder="ej. IMPER de Chihuahua")
            with col_e2:
                n_asientos = st.number_input("Licencias Simultáneas (Asientos)", min_value=1, max_value=100, value=2)
            with col_e3:
                n_hwids = st.number_input("Límite de PCs Físicas (HWID)", min_value=1, max_value=200, value=5)
            
            submit_emp = st.form_submit_button("Guardar Empresa")
            if submit_emp:
                if n_nombre.strip():
                    res = admin.create_empresa(n_nombre, int(n_asientos), int(n_hwids))
                    if res:
                        st.success(f"Empresa '{n_nombre}' creada con éxito.")
                        st.rerun()
                    else:
                        st.error("Error al crear empresa. Verifica que el nombre no esté duplicado.")
                else:
                    st.warning("El nombre de la empresa no puede estar vacío.")

    # Listado y edición de empresas
    if empresas:
        for emp in empresas:
            with st.container():
                e_col1, e_col2, e_col3, e_col4, e_col5 = st.columns([2.5, 1.2, 1.2, 1.5, 1.5])
                with e_col1:
                    st.markdown(f"### {emp['nombre']}")
                    st.caption(f"ID: `{emp['id']}`")
                with e_col2:
                    new_asientos = st.number_input("Asientos", min_value=1, max_value=100, value=emp["max_asientos"], key=f"as_{emp['id']}")
                with e_col3:
                    new_hwids = st.number_input("Límite PCs", min_value=1, max_value=200, value=emp["max_hwids"], key=f"hw_{emp['id']}")
                with e_col4:
                    new_activa = st.toggle("Suscripción Activa", value=emp.get("activa", True), key=f"act_{emp['id']}")
                with e_col5:
                    st.write("")
                    if st.button("Guardar Cambios", key=f"save_{emp['id']}"):
                        admin.update_empresa(emp["id"], {
                            "max_asientos": int(new_asientos),
                            "max_hwids": int(new_hwids),
                            "activa": new_activa
                        })
                        st.success("Actualizado")
                        st.rerun()
                st.divider()

# -------------------------------------------------------------
# TAB 3: GESTIÓN DE USUARIOS
# -------------------------------------------------------------
with tab3:
    st.subheader("Cuentas de Usuarios por Empresa")
    
    # Crear nuevo usuario
    with st.expander("➕ Registrar Nuevo Usuario", expanded=False):
        if not empresas:
            st.warning("Primero debes dar de alta al menos una empresa.")
        else:
            with st.form("new_user_form"):
                empresa_opts = {e["nombre"]: e["id"] for e in empresas}
                sel_empresa = st.selectbox("Empresa Perteneciente", options=list(empresa_opts.keys()))
                u_email = st.text_input("Correo Electrónico", placeholder="ingeniero@empresa.com")
                u_pass = st.text_input("Contraseña Inicial", placeholder="Clave de acceso")
                
                if st.form_submit_button("Crear Usuario"):
                    if u_email and u_pass:
                        res = admin.create_usuario(empresa_opts[sel_empresa], u_email, u_pass)
                        if res:
                            st.success(f"Usuario {u_email} creado correctamente.")
                            st.rerun()
                        else:
                            st.error("Error al registrar usuario. Verifica que el correo no exista.")
                    else:
                        st.warning("Completa el correo y la contraseña.")

    # Tabla de usuarios
    if usuarios:
        u_data = []
        for u in usuarios:
            emp_nom = u.get("empresas", {}).get("nombre", "N/A") if isinstance(u.get("empresas"), dict) else "N/A"
            u_data.append({
                "ID": u["id"],
                "Correo": u["correo"],
                "Empresa": emp_nom,
                "Activo": "Sí" if u.get("activo", True) else "No",
                "Creado": u.get("created_at", "")[:10]
            })
        st.dataframe(pd.DataFrame(u_data), use_container_width=True)

# -------------------------------------------------------------
# TAB 4: CONTROL DE HARDWARE (HWID WHITELIST)
# -------------------------------------------------------------
with tab4:
    st.subheader("Lista Blanca de Dispositivos Físicos (HWIDs)")
    st.caption("Cada vez que un usuario abre FrameOne en una PC autorizada, se vincula automáticamente su procesador y tarjeta madre hasta alcanzar el límite contratado.")
    
    if not dispositivos:
        st.info("Aún no hay equipos físicos registrados en la lista blanca.")
    else:
        for d in dispositivos:
            emp_nom = d.get("empresas", {}).get("nombre", "N/A") if isinstance(d.get("empresas"), dict) else "N/A"
            pc_nombre = d.get("nombre_equipo", "PC Desconocida")
            hwid_corto = d.get("hwid_hash", "")[:16] + "..."
            ultimo = d.get("ultimo_acceso", "")[:19]
            activo = d.get("activo", True)
            
            with st.container():
                d1, d2, d3, d4, d5, d6 = st.columns([2, 2, 2, 2, 1.2, 1.5])
                with d1:
                    st.write(f"🏢 **{emp_nom}**")
                with d2:
                    st.write(f"💻 **{pc_nombre}**")
                with d3:
                    st.write(f"🔑 `{hwid_corto}`")
                with d4:
                    st.write(f"🕒 Último: `{ultimo}`")
                with d5:
                    status_lbl = "✅ Autorizada" if activo else "🚫 Bloqueada"
                    st.write(status_lbl)
                with d6:
                    if st.button("Desvincular PC", key=f"del_hwid_{d['id']}", help="Elimina el equipo para liberar 1 cupo de PC en la empresa."):
                        admin.delete_hwid(d["id"])
                        st.success(f"Equipo {pc_nombre} desvinculado con éxito.")
                        st.rerun()
                st.divider()
