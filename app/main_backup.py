import streamlit as st
import math
import os
import subprocess
from model import StaadModel
from staad_writer import write_staad
from visualizer import plot_model

st.set_page_config(page_title="Generador STAAD", layout="wide")

# CSS para botones
st.markdown("""
    <style>
    /* Botones principales (Ingeniería Clásica - Azul Acero/Marino) */
    section[data-testid="stSidebar"] button[kind="primary"] {
        background: linear-gradient(180deg, #2A4B7C 0%, #1A365D 100%) !important;
        color: white !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px !important;
        border-radius: 6px !important;
        width: 200% !important;
        margin: 0 auto !important;
        display: block !important;
        border: 1px solid #142A4A !important;
        text-align: center !important;
        justify-content: center !important;
        box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.2) !important;
        transition: all 0.2s ease-in-out !important;
    }
    section[data-testid="stSidebar"] button[kind="primary"]:hover {
        background: linear-gradient(180deg, #325A92 0%, #214371 100%) !important;
        box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.3) !important;
        transform: translateY(-1px) !important;
        border: 1px solid #1A365D !important;
    }
    section[data-testid="stSidebar"] button[kind="primary"]:active {
        transform: translateY(1px) !important;
        box-shadow: 0px 1px 2px rgba(0, 0, 0, 0.2) !important;
    }
    
    /* Botón de retroceso (Flecha gris) */
    section[data-testid="stSidebar"] button[kind="secondary"] {
        background-color: transparent !important;
        color: gray !important;
        border: none !important;
        padding: 0px !important;
        width: auto !important;
        font-size: 24px !important;
        box-shadow: none !important;
        margin-bottom: 10px !important;
    }
    section[data-testid="stSidebar"] button[kind="secondary"]:hover {
        color: darkgray !important;
        background-color: transparent !important;
    }

    /* Botón de Guardar/Acciones en Panel Derecho (Rojo Premium STAAD) */
    div[data-testid="stMainBlockContainer"] button[kind="primary"] {
        background: linear-gradient(180deg, #991B1B 0%, #7F1D1D 100%) !important;
        border: 1px solid #7F1D1D !important;
        color: white !important;
        font-weight: 600 !important;
        border-radius: 6px !important;
        box-shadow: 0px 2px 5px rgba(0, 0, 0, 0.2) !important;
        transition: all 0.2s ease-in-out !important;
        letter-spacing: 0.5px !important;
    }
    div[data-testid="stMainBlockContainer"] button[kind="primary"]:hover {
        background: linear-gradient(180deg, #DC2626 0%, #B91C1C 100%) !important;
        box-shadow: 0px 5px 10px rgba(220, 38, 38, 0.25) !important;
        transform: translateY(-2px) !important;
        border: 1px solid #B91C1C !important;
    }
    div[data-testid="stMainBlockContainer"] button[kind="primary"]:active {
        transform: translateY(1px) !important;
        box-shadow: 0px 1px 2px rgba(0, 0, 0, 0.2) !important;
    }
    
    /* Reducir ancho de la barra lateral */
    section[data-testid="stSidebar"] {
        min-width: 220px !important;
        max-width: 240px !important;
    }
    
    /* Reducir padding superior de la aplicación para aprovechar espacio */
    div.block-container {
        padding-top: 2rem !important;
        padding-bottom: 0rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }
    /* Ocultar footer y header por defecto de Streamlit que generan scroll vacío */
    header {visibility: hidden !important; display: none !important;}
    footer {visibility: hidden !important; display: none !important;}
    </style>
""", unsafe_allow_html=True)

st.markdown("<div style='color: gray; margin-top: 15px; margin-bottom: -10px;'>&emsp;&emsp;M.I. José Ramón Márquez Montes</div>", unsafe_allow_html=True)
st.title("Generador Paramétrico STAAD.Pro")
st.markdown("Generador automático de naves industriales para STAAD.Pro")

# Inicializar estado para variables por defecto
defaults = {
    "larm": 15.24, "ljoist": 12.20, "nbay": 10, "nspan": 5, 
    "harm": 1.30, "hlib": 9.75, "subdiv": 10,
    "roof_type": "2 Aguas", "slope_pct": 3.0, "support_type": "FIXED",
    "c_muerta": 30.0, "c_viva": 100.0, "c_granizo": 60.0,
    "v_barlovento": 86.0, "v_sotavento": 50.0, "v_laterales": 78.0, "v_succion": 95.0,
    "coef_sismico": 0.08, "ductilidad": 2.0, "cm_sismo": None, "cv_sismo": None,
    "current_panel": "Main"
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

def go_panel(p):
    st.session_state.current_panel = p

def update_val(key):
    st.session_state[key] = st.session_state["_" + key]

def update_larm():
    st.session_state.larm = st.session_state._larm
    # Auto-actualizar
    length = st.session_state.larm
    needed = math.ceil(length / 1.524)
    if needed % 2 != 0:
        needed += 1
    st.session_state.subdiv = max(2, int(needed))
    st.session_state['_subdiv'] = st.session_state.subdiv
    
    st.session_state.harm = math.ceil((length / 12.5) * 10) / 10.0
    st.session_state['_harm'] = st.session_state.harm

def update_c_viva():
    st.session_state.c_viva = st.session_state._c_viva
    st.session_state.cv_sismo = st.session_state.c_viva * 0.25
    st.session_state['_cv_sismo'] = st.session_state.cv_sismo

def update_c_muerta():
    st.session_state.c_muerta = st.session_state._c_muerta
    st.session_state.cm_sismo = st.session_state.c_muerta
    st.session_state['_cm_sismo'] = st.session_state.cm_sismo


with st.sidebar:
    panel = st.session_state.current_panel
    
    if panel == "Main":
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center;'>Menú Principal</h2>", unsafe_allow_html=True)
        st.button("Geometría", type="primary", on_click=go_panel, args=("Geometría",))
        st.button("Cargas", type="primary", on_click=go_panel, args=("Cargas",))
        st.button("Diseño", type="primary", on_click=go_panel, args=("Diseño",))
        
    elif panel == "Geometría":
        st.button("⬅", type="secondary", on_click=go_panel, args=("Main",))
        st.header("Geometría")
        
        st.number_input("Longitud de Armaduras (m)", min_value=1.0, step=0.1, value=st.session_state.larm, key="_larm", on_change=update_larm)
        st.number_input("Longitud de Joists (m)", min_value=1.0, step=0.1, value=st.session_state.ljoist, key="_ljoist", on_change=update_val, args=("ljoist",))
        
        st.number_input("Número de Bahías (Profundidad)", min_value=1, step=1, value=st.session_state.nbay, key="_nbay", on_change=update_val, args=("nbay",))
        st.number_input("Número de Entre-ejes (Ancho)", min_value=1, step=1, value=st.session_state.nspan, key="_nspan", on_change=update_val, args=("nspan",))
        
        st.number_input("Altura de Armadura (Peralte) (m)", min_value=0.5, step=0.1, value=st.session_state.harm, key="_harm", on_change=update_val, args=("harm",))
        
        # Relaciones L/10 y L/15
        l_10 = st.session_state.larm / 10.0
        l_15 = st.session_state.larm / 15.0
        st.markdown(f"<div style='font-size: 0.85em; color: gray; margin-top: -10px; margin-bottom: 10px;'>L/10 = {l_10:.2f} m.<br>L/15 = {l_15:.2f} m.</div>", unsafe_allow_html=True)
        
        st.number_input("Altura Libre (m)", min_value=1.0, step=0.1, value=st.session_state.hlib, key="_hlib", on_change=update_val, args=("hlib",))
        st.number_input("Subdivisiones (Debe ser par)", min_value=2, step=2, value=st.session_state.subdiv, key="_subdiv", on_change=update_val, args=("subdiv",))

        st.markdown("<hr style='border: none; border-top: 1px solid #d3d3d3; margin: 15px 0;'>", unsafe_allow_html=True)
        st.subheader("Cubierta")
        rt = st.radio("Tipo de Cubierta", ["1 Agua", "2 Aguas"], index=["1 Agua", "2 Aguas"].index(st.session_state.roof_type) if st.session_state.roof_type in ["1 Agua", "2 Aguas"] else 1)
        st.session_state.roof_type = rt
        sp = st.number_input("Pendiente (%)", min_value=0.0, step=0.5, value=st.session_state.slope_pct)
        st.session_state.slope_pct = sp

        st.markdown("<hr style='border: none; border-top: 1px solid #d3d3d3; margin: 15px 0;'>", unsafe_allow_html=True)
        st.subheader("Apoyos Base")
        apoyo = st.radio("Tipo de Apoyo", ["Empotrado", "Articulado"], index=0 if st.session_state.support_type == "FIXED" else 1)
        st.session_state.support_type = "FIXED" if apoyo == "Empotrado" else "PINNED"

    elif panel == "Cargas":
        st.button("⬅", type="secondary", on_click=go_panel, args=("Main",))
        st.header("Cargas")
        st.subheader("Gravitacionales")
        st.number_input("Carga Muerta (kg/m²)", min_value=0.0, step=5.0, value=st.session_state.c_muerta, key="_c_muerta", on_change=update_c_muerta)
        st.number_input("Carga Viva (kg/m²)", min_value=0.0, step=5.0, value=st.session_state.c_viva, key="_c_viva", on_change=update_c_viva)
        st.number_input("Granizo (kg/m²)", min_value=0.0, step=5.0, value=st.session_state.c_granizo, key="_c_granizo", on_change=update_val, args=("c_granizo",))
        
        st.markdown("<hr style='border: none; border-top: 1px solid #d3d3d3; margin: 5px 0;'>", unsafe_allow_html=True)
        st.subheader("Viento")
        st.session_state.v_barlovento = st.number_input("Barlovento (kg/m²)", min_value=0.0, step=1.0, value=st.session_state.v_barlovento)
        st.session_state.v_sotavento = st.number_input("Sotavento (kg/m²)", min_value=0.0, step=1.0, value=st.session_state.v_sotavento)
        st.session_state.v_laterales = st.number_input("Laterales (kg/m²)", min_value=0.0, step=1.0, value=st.session_state.v_laterales)
        st.session_state.v_succion = st.number_input("Succión (kg/m²)", min_value=0.0, step=1.0, value=st.session_state.v_succion)

        st.markdown("<hr style='border: none; border-top: 1px solid #d3d3d3; margin: 5px 0;'>", unsafe_allow_html=True)
        st.subheader("Sismo")
        st.session_state.coef_sismico = st.number_input("Coeficiente Sísmico", min_value=0.0, step=0.01, value=st.session_state.coef_sismico)
        st.session_state.ductilidad = st.number_input("Ductilidad", min_value=1.0, step=0.5, value=st.session_state.ductilidad)
        
        if st.session_state.cm_sismo is None:
            st.session_state.cm_sismo = st.session_state.c_muerta
        if st.session_state.cv_sismo is None:
            st.session_state.cv_sismo = st.session_state.c_viva * 0.25
            
        st.number_input("Carga Muerta para Sismo (kg/m²)", min_value=0.0, step=5.0, value=st.session_state.cm_sismo, key="_cm_sismo", on_change=update_val, args=("cm_sismo",))
        st.number_input("Carga Viva para Sismo (kg/m²)", min_value=0.0, step=5.0, value=st.session_state.cv_sismo, key="_cv_sismo", on_change=update_val, args=("cv_sismo",))

    elif panel == "Diseño":
        st.button("⬅", type="secondary", on_click=go_panel, args=("Main",))
        st.header("Diseño")
        st.info("Opciones de diseño en construcción...")

# Ensure even subdivisions
if st.session_state.subdiv % 2 != 0:
    st.sidebar.error("Las subdivisiones deben ser un número par.")
    st.stop()

# Build Model
try:
    model = StaadModel(
        st.session_state.larm, 
        st.session_state.ljoist, 
        st.session_state.nbay, 
        st.session_state.nspan, 
        st.session_state.harm, 
        st.session_state.hlib, 
        st.session_state.subdiv, 
        st.session_state.roof_type, 
        st.session_state.slope_pct,
        st.session_state.support_type,
        st.session_state.c_muerta,
        st.session_state.c_viva,
        st.session_state.c_granizo,
        st.session_state.v_barlovento,
        st.session_state.v_sotavento,
        st.session_state.v_laterales,
        st.session_state.v_succion,
        st.session_state.coef_sismico,
        st.session_state.ductilidad,
        st.session_state.cm_sismo,
        st.session_state.cv_sismo
    )
except Exception as e:
    st.error(f"Error generando la geometría: {e}")
    st.stop()

col1, col2 = st.columns([3, 1])

with col1:
    st.markdown("<div style='margin-top: -30px;'></div>", unsafe_allow_html=True)
    st.subheader("Vista 3D")
    show_sup = (st.session_state.current_panel == "Geometría")
    fig = plot_model(model, show_supports=show_sup)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("<div style='margin-top: -60px;'></div>", unsafe_allow_html=True)
    st.subheader("Exportación")
    
    project_name = st.text_input("Nombre del Proyecto:", value="Modelo")
    file_name_export = f"{project_name.strip()}.std" if project_name.strip() else "Modelo.std"
    
    st.markdown("**Ubicación:**")
    
    if 'export_path' not in st.session_state:
        st.session_state.export_path = os.path.expanduser("~")
        
    parts = os.path.normpath(st.session_state.export_path).split(os.sep)
    if len(parts) >= 2:
        display_text = os.path.join(parts[-2], parts[-1])
    else:
        display_text = st.session_state.export_path
        
    path_col, btn_col = st.columns([3, 1])
    with path_col:
        st.code(display_text, language="")
    with btn_col:
        if st.button("📁", help="Examinar..."):
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            folder_selected = filedialog.askdirectory(master=root, title="Seleccionar Carpeta de Exportación", initialdir=st.session_state.export_path)
            root.destroy()
            if folder_selected:
                st.session_state.export_path = folder_selected
                st.rerun()
                
    staad_text = write_staad(model)
    
    if st.button("Guardar Archivo .std", type="primary"):
        # Limpiar el nombre del archivo para evitar caracteres inválidos
        clean_name = "".join(c for c in file_name_export if c.isalnum() or c in " ._-").strip()
        if not clean_name.endswith(".std"):
            clean_name += ".std"
            
        full_path = os.path.join(st.session_state.export_path, clean_name)
        try:
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(staad_text)
            st.success(f"Guardado exitosamente en:\n{full_path}")
            
            # Abrir archivo automáticamente (en Windows usa la app predeterminada para .std)
            if os.name == 'nt':
                os.startfile(full_path)
            else:
                subprocess.call(('open', full_path))
                
        except Exception as e:
            st.error(f"Error al guardar o abrir en '{full_path}': {e}")
    
    st.markdown("<hr style='margin: 15px 0 10px 0;'>", unsafe_allow_html=True)
    st.subheader("Elementos")
    st.markdown(f"""
    <div style='line-height: 1.8;'>
        • Columnas: {(st.session_state.nbay + 1) * (st.session_state.nspan + 1)}<br>
        • Armaduras: {(st.session_state.nbay + 1) * st.session_state.nspan}<br>
        • Contravientos: {len(model.groups.get('_CVH', []))}<br>
        • Largueros: {len(model.groups.get('_LARGUEROS', []))}
    </div>
    """, unsafe_allow_html=True)

