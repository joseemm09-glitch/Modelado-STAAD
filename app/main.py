import streamlit as st
import math
import os
import tempfile
import subprocess
from model import StaadModel
from staad_writer import write_staad
from visualizer import plot_model

st.set_page_config(page_title="Generador STAAD", layout="wide")

# CSS para botones
st.markdown("""
    <style>
    /* Botones principales (Navy Blue) */
    section[data-testid="stSidebar"] button[kind="primary"] {
        background-color: navy !important;
        color: white !important;
        font-weight: bold !important;
        border-radius: 10px !important;
        width: 200% !important;
        margin: 0 auto !important;
        display: block !important;
        border: none !important;
        text-align: center !important;
        justify-content: center !important;
    }
    section[data-testid="stSidebar"] button[kind="primary"]:hover {
        background-color: #1a1a99 !important;
        opacity: 0.9 !important;
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

    /* Botón de Exportar (Rojo oscuro STAAD) */
    div[data-testid="stMainBlockContainer"] button[kind="primary"] {
        background-color: darkred !important;
        border-color: darkred !important;
        color: white !important;
        font-weight: bold !important;
        border-radius: 10px !important;
    }
    div[data-testid="stMainBlockContainer"] button[kind="primary"]:hover {
        background-color: firebrick !important;
        border-color: firebrick !important;
        opacity: 0.9 !important;
    }
    
    /* Reducir ancho de la barra lateral */
    section[data-testid="stSidebar"] {
        min-width: 220px !important;
        max-width: 240px !important;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<div style='color: gray; margin-bottom: -15px;'>&emsp;&emsp;M.I. José Ramón Márquez Montes</div>", unsafe_allow_html=True)
st.title("Generador Paramétrico STAAD.Pro")
st.markdown("Generador automático de naves industriales para STAAD.Pro")

# Inicializar estado para variables por defecto
defaults = {
    "larm": 15.24, "ljoist": 12.20, "nbay": 10, "nspan": 5, 
    "harm": 1.30, "hlib": 9.75, "subdiv": 10,
    "roof_type": "2 Aguas", "slope_pct": 3.0, "support_type": "FIXED",
    "c_muerta": 30.0, "c_viva": 100.0, "c_granizo": 60.0,
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
    st.session_state.harm = math.ceil((length / 12.5) * 10) / 10.0

with st.sidebar:
    panel = st.session_state.current_panel
    
    if panel == "Main":
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center;'>Menú Principal</h2>", unsafe_allow_html=True)
        st.button("Geometría", type="primary", on_click=go_panel, args=("Geometría",))
        st.button("Pendiente", type="primary", on_click=go_panel, args=("Pendiente",))
        st.button("Apoyos", type="primary", on_click=go_panel, args=("Apoyos",))
        st.button("Cargas", type="primary", on_click=go_panel, args=("Cargas",))
        
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

    elif panel == "Pendiente":
        st.button("⬅", type="secondary", on_click=go_panel, args=("Main",))
        st.header("Cubierta")
        rt = st.radio("Tipo de Cubierta", ["1 Agua", "2 Aguas"], index=["1 Agua", "2 Aguas"].index(st.session_state.roof_type) if st.session_state.roof_type in ["1 Agua", "2 Aguas"] else 1)
        st.session_state.roof_type = rt
        sp = st.number_input("Pendiente (%)", min_value=0.0, step=0.5, value=st.session_state.slope_pct)
        st.session_state.slope_pct = sp

    elif panel == "Apoyos":
        st.button("⬅", type="secondary", on_click=go_panel, args=("Main",))
        st.header("Apoyos Base")
        apoyo = st.radio("Tipo de Apoyo", ["Empotrado", "Articulado"], index=0 if st.session_state.support_type == "FIXED" else 1)
        st.session_state.support_type = "FIXED" if apoyo == "Empotrado" else "PINNED"

    elif panel == "Cargas":
        st.button("⬅", type="secondary", on_click=go_panel, args=("Main",))
        st.header("Cargas")
        st.session_state.c_muerta = st.number_input("Carga Muerta (kg/m²)", min_value=0.0, step=5.0, value=st.session_state.c_muerta)
        st.session_state.c_viva = st.number_input("Carga Viva (kg/m²)", min_value=0.0, step=5.0, value=st.session_state.c_viva)
        st.session_state.c_granizo = st.number_input("Granizo (kg/m²)", min_value=0.0, step=5.0, value=st.session_state.c_granizo)

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
        st.session_state.c_granizo
    )
except Exception as e:
    st.error(f"Error generando la geometría: {e}")
    st.stop()

col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("Vista 3D")
    show_sup = (st.session_state.current_panel == "Apoyos")
    fig = plot_model(model, show_supports=show_sup)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Exportación")
    
    staad_text = write_staad(model)
    
    st.download_button(
        label="Descargar Archivo .std",
        data=staad_text,
        file_name="Modelo_Nave_Industrial.std",
        mime="text/plain",
        type="primary"
    )
    
    st.markdown("---")
    st.markdown("**Resumen de Elementos:**")
    st.write(f"- Nodos: {model.node_id}")
    st.write(f"- Miembros: {model.mem_id}")
    for k, v in model.groups.items():
        if v:
            st.write(f"  - {k}: {len(v)}")
