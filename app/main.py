import streamlit as st
import math
import os
import sys
import subprocess
import importlib

# Ensure app directory is in sys.path for both local and web environments
app_dir = os.path.dirname(os.path.abspath(__file__))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

import streamlit.components.v1 as components

# Force reload of custom modules to ensure Streamlit hot-reloads them
import model
import staad_writer
import visualizer
import prediseno
importlib.reload(model)
importlib.reload(staad_writer)
importlib.reload(visualizer)
importlib.reload(prediseno)

from model import StaadModel
from staad_writer import write_staad
from visualizer import plot_model

icono_path = os.path.join(os.path.dirname(__file__), "..", "staad_blue.ico")
page_icon = icono_path if os.path.exists(icono_path) else "🏢"
st.set_page_config(page_title="Naves Industriales STAAD.Pro", page_icon=page_icon, layout="wide")

st.markdown("""
<style>
/* iOS Liquid Glass Effect for containers */
div[data-testid="stVerticalBlock"]:has(> div.element-container div.ios-glass-marker) {
    background: rgba(255, 255, 255, 0.45);
    backdrop-filter: blur(15px);
    -webkit-backdrop-filter: blur(15px);
    border-radius: 16px;
    padding: 15px 20px;
    box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.8);
    margin-bottom: 20px;
    position: relative;
    top: -95px;
    z-index: 99;
}
/* Adjust spacing inside the glass card */
div[data-testid="stVerticalBlock"]:has(> div.element-container div.ios-glass-marker) h3 {
    margin-top: -10px;
    font-weight: 600;
}
/* Tamaño de fuente reducido para la Ubicación */
div[data-testid="stVerticalBlock"]:has(> div.element-container div.path-marker) input {
    font-size: 11px !important;
}
/* Ocultar el contenedor del marcador para que no desalinee el input */
div.element-container:has(div.path-marker) {
    display: none !important;
    margin: 0 !important;
    height: 0 !important;
}
/* Sidebar Logo Styling */
[data-testid="stSidebar"] [data-testid="stImage"] {
    display: flex;
    justify-content: center;
    align-items: center;
    width: 100%;
}
[data-testid="stSidebar"] img {
    border-radius: 18px !important;
    box-shadow: 0 12px 24px rgba(0, 0, 0, 0.25) !important;
    width: 60% !important;
    margin: 0 auto 15px auto !important;
    display: block !important;
}
/* Make the divider faint grey */
hr {
    margin: 15px 0 !important;
    border-top: 1px solid rgba(0,0,0,0.1) !important;
}
</style>
""", unsafe_allow_html=True)


# CSS para botones
st.markdown("""
    <style>
    /* Asegurar que el texto dentro de los botones no sea bold */
    button, button p, button div, button span {
        font-weight: normal !important;
    }

    /* Botones principales (Azul Sólido) */
    section[data-testid="stSidebar"] button[kind="primary"] {
        background: #005cb2 !important;
        color: white !important;
        font-weight: normal !important;
        border-radius: 4px !important;
        width: 100% !important;
        margin: 0 auto !important;
        display: block !important;
        border: none !important;
        text-align: center !important;
        justify-content: center !important;
        box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.1) !important;
        transition: all 0.2s ease-in-out !important;
        padding-top: 0.5rem !important;
        padding-bottom: 0.5rem !important;
    }
    section[data-testid="stSidebar"] button[kind="primary"]:hover {
        background: #004ba0 !important;
        box-shadow: 0px 3px 6px rgba(0, 0, 0, 0.15) !important;
        transform: translateY(-1px) !important;
    }
    section[data-testid="stSidebar"] button[kind="primary"]:active {
        transform: translateY(1px) !important;
        box-shadow: 0px 1px 2px rgba(0, 0, 0, 0.1) !important;
    }
    
    /* Botón de retroceso (Flecha gris) */
    section[data-testid="stSidebar"] button[kind="secondary"] {
        background-color: #f8f9fa !important;
        color: #444 !important;
        border: 1px solid #ddd !important;
        padding: 4px 12px !important;
        width: auto !important;
        font-size: 14px !important;
        font-weight: normal !important;
        box-shadow: 0px 1px 2px rgba(0,0,0,0.05) !important;
        border-radius: 4px !important;
        margin-bottom: 5px !important;
        margin-top: 5px !important;
        position: relative !important;
        z-index: 10 !important;
    }
    section[data-testid="stSidebar"] button[kind="secondary"]:hover {
        background-color: #e9ecef !important;
        color: #111 !important;
    }

    /* Botón de Guardar/Acciones en Panel Derecho (Rojo Sólido) */
    div[data-testid="stMainBlockContainer"] button[kind="primary"] {
        background: #ba281b !important;
        color: white !important;
        font-weight: normal !important;
        border-radius: 4px !important;
        border: none !important;
        box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.1) !important;
        transition: all 0.2s ease-in-out !important;
        padding-top: 0.5rem !important;
        padding-bottom: 0.5rem !important;
    }
    div[data-testid="stMainBlockContainer"] button[kind="primary"]:hover {
        background: #9d2116 !important;
        box-shadow: 0px 3px 6px rgba(0, 0, 0, 0.15) !important;
        transform: translateY(-1px) !important;
    }
    div[data-testid="stMainBlockContainer"] button[kind="primary"]:active {
        transform: translateY(1px) !important;
        box-shadow: 0px 1px 2px rgba(0, 0, 0, 0.1) !important;
    }
    
    /* Marcador para botones grises (Diseño y Catálogo) */
    div.element-container:has(div.grey-btn-marker), div[data-testid="stElementContainer"]:has(div.grey-btn-marker) {
        display: none !important;
        margin: 0 !important;
        height: 0 !important;
    }

    /* Botones de Diseño y Catálogo (Gris siempre) */
    div.element-container:has(div.grey-btn-marker) + div.element-container button,
    div[data-testid="stElementContainer"]:has(div.grey-btn-marker) + div[data-testid="stElementContainer"] button,
    section[data-testid="stSidebar"] div.element-container:has(div.grey-btn-marker) + div.element-container button,
    section[data-testid="stSidebar"] div[data-testid="stElementContainer"]:has(div.grey-btn-marker) + div[data-testid="stElementContainer"] button {
        background: #6c757d !important;
        color: white !important;
        font-weight: normal !important;
        border-radius: 4px !important;
        border: none !important;
        width: 100% !important;
        margin: 0 auto !important;
        display: block !important;
        text-align: center !important;
        justify-content: center !important;
        box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.1) !important;
        transition: all 0.2s ease-in-out !important;
        padding-top: 0.5rem !important;
        padding-bottom: 0.5rem !important;
    }
    div.element-container:has(div.grey-btn-marker) + div.element-container button:hover:not(:disabled),
    div[data-testid="stElementContainer"]:has(div.grey-btn-marker) + div[data-testid="stElementContainer"] button:hover:not(:disabled),
    section[data-testid="stSidebar"] div.element-container:has(div.grey-btn-marker) + div.element-container button:hover:not(:disabled),
    section[data-testid="stSidebar"] div[data-testid="stElementContainer"]:has(div.grey-btn-marker) + div[data-testid="stElementContainer"] button:hover:not(:disabled) {
        background: #5a6268 !important;
        box-shadow: 0px 3px 6px rgba(0, 0, 0, 0.15) !important;
        transform: translateY(-1px) !important;
    }
    div.element-container:has(div.grey-btn-marker) + div.element-container button:disabled,
    div[data-testid="stElementContainer"]:has(div.grey-btn-marker) + div[data-testid="stElementContainer"] button:disabled,
    section[data-testid="stSidebar"] div.element-container:has(div.grey-btn-marker) + div.element-container button:disabled,
    section[data-testid="stSidebar"] div[data-testid="stElementContainer"]:has(div.grey-btn-marker) + div[data-testid="stElementContainer"] button:disabled {
        background: #adb5bd !important;
        color: #f8f9fa !important;
        opacity: 0.65 !important;
        cursor: not-allowed !important;
        box-shadow: none !important;
        transform: none !important;
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
    /* Descomentar para ocultar el header (Deploy/Menu) en producción: */
    /* header {visibility: hidden !important; display: none !important;} */
    footer {visibility: hidden !important; display: none !important;}
    </style>
""", unsafe_allow_html=True)

st.title("Naves Industriales STAAD.Pro")
st.markdown("<div style='color: gray; margin-top: -15px; margin-bottom: 20px; margin-left: 10px;'>M.I. José Ramón Márquez Montes</div>", unsafe_allow_html=True)

# Inicializar estado para variables por defecto
defaults = {
    "larm": 15.24, "ljoist": 12.20, "nbay": 7, "nspan": 4, 
    "harm": 1.30, "hlib": 9.75, "subdiv": 10,
    "roof_type": "2 Aguas", "slope_pct": 5.0, "support_type": "FIXED",
    "c_muerta": 30.0, "c_viva": 100.0, "c_granizo": 60.0,
    "v_barlovento": 86.0, "v_sotavento": 50.0, "v_laterales": 78.0, "v_succion": 95.0,
    "coef_sismico": 0.08, "ductilidad": 2.0, "cm_sismo": None, "cv_sismo": None,
    "add_wind_cols": True,
    "max_wind_dist": 8.0,
    "wall_type": "Metálico",
    "current_panel": "Main",
    "subdiv_warning": False
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

def go_panel(p):
    st.session_state.current_panel = p

def update_val(key):
    st.session_state[key] = st.session_state["_" + key]

def update_subdiv():
    val = st.session_state._subdiv
    if val % 2 != 0:
        val += 1
        st.session_state.subdiv_warning = True
    else:
        st.session_state.subdiv_warning = False
    st.session_state.subdiv = val
    st.session_state._subdiv = val

def update_larm():
    st.session_state.larm = st.session_state._larm
    # Auto-actualizar
    length = st.session_state.larm
    needed = math.ceil(length / 1.524)
    if needed % 2 != 0:
        needed += 1
    st.session_state.subdiv = max(2, int(needed))
    st.session_state['_subdiv'] = st.session_state.subdiv
    st.session_state.subdiv_warning = False
    
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

# Calculate sec_trusses_j
sec_trusses_j = []
sec_mode = st.session_state.get('sec_truss_mode', 'Ninguno')
if sec_mode == "Automático":
    total_width_m = st.session_state.nspan * st.session_state.larm
    if total_width_m >= 91.44:
        extra_width = total_width_m - 91.44
        num_pares = int(extra_width / st.session_state.larm)
        n_trusses = 1 + 2 * num_pares
        mid_j = st.session_state.nspan / 2.0
        interior_j = list(range(1, st.session_state.nspan))
        interior_j.sort(key=lambda j: (abs(j - mid_j), j))
        sec_trusses_j = interior_j[:n_trusses]
elif sec_mode == "Todos los Ejes":
    if st.session_state.wall_type == "Tilt-Up":
        sec_trusses_j = list(range(1, st.session_state.nspan))
    else:
        sec_trusses_j = list(range(0, st.session_state.nspan + 1))
elif sec_mode == "Personalizado":
    mid_j = st.session_state.nspan / 2.0
    if st.session_state.wall_type == "Tilt-Up":
        interior_j = list(range(1, st.session_state.nspan))
    else:
        interior_j = list(range(0, st.session_state.nspan + 1))
    interior_j.sort(key=lambda j: (abs(j - mid_j), j))
    interior_j = interior_j[:10]
    
    sec_trusses_j = [j for j in interior_j if st.session_state.get(f"sec_eje_{j}", False)]
    st.session_state.sec_truss_custom_ejes = sec_trusses_j

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
        st.session_state.cv_sismo,
        st.session_state.add_wind_cols,
        st.session_state.max_wind_dist,
        st.session_state.wall_type,
        sec_trusses_j,
        st.session_state.get('resorte_val', '1,000,000').replace(',', '')
    )
except Exception as e:
    st.error(f"Error generando la geometría: {e}")
    st.stop()


def render_siblings_top(group, current):
    for name in group:
        if name == current: break
        c1, c2, c3 = st.columns([1, 6, 1])
        is_dis = False
        if name in ["Diseño", "Catálogo"] and not st.session_state.get("file_generated", False):
            is_dis = True
        with c2:
            if name in ["Diseño", "Catálogo"]:
                st.markdown("<div class='grey-btn-marker'></div>", unsafe_allow_html=True)
            st.button(name, type="primary", use_container_width=True, on_click=go_panel, args=(name,), key=f"nav_top_{name}", disabled=is_dis)

def render_siblings_bottom(group, current):
    found = False
    first_bot = True
    for name in group:
        if found:
            if first_bot:
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("<hr style='margin: 0px 0px 10px 0px; border: 0; border-top: 1px solid #e0e0e0;'>", unsafe_allow_html=True)
                first_bot = False
            c1, c2, c3 = st.columns([1, 6, 1])
            is_dis = False
            if name in ["Diseño", "Catálogo"] and not st.session_state.get("file_generated", False):
                is_dis = True
            with c2:
                if name in ["Diseño", "Catálogo"]:
                    st.markdown("<div class='grey-btn-marker'></div>", unsafe_allow_html=True)
                st.button(name, type="primary", use_container_width=True, on_click=go_panel, args=(name,), key=f"nav_bot_{name}", disabled=is_dis)
        if name == current: found = True

nav_group1 = ["Geometría", "Cargas", "Prediseño"]
nav_group2 = ["Diseño", "Catálogo"]

with st.sidebar:
    panel = st.session_state.current_panel
    
    if panel == "Main":
        # Logo at the top of the sidebar
        try:
            st.image(icono_path, use_container_width=True)
        except:
            pass
        st.markdown("<h3 style='text-align: center; margin-top: 10px;'>Menú Principal</h3>", unsafe_allow_html=True)
        st.button("Geometría", type="primary", width="stretch", on_click=go_panel, args=("Geometría",))
        st.button("Cargas", type="primary", width="stretch", on_click=go_panel, args=("Cargas",))
        st.button("Prediseño", type="primary", width="stretch", on_click=go_panel, args=("Prediseño",))
        st.divider()
        is_disabled = not st.session_state.get("file_generated", False)
        st.markdown("<div class='grey-btn-marker'></div>", unsafe_allow_html=True)
        st.button("Diseño", type="primary", width="stretch", on_click=go_panel, args=("Diseño",), disabled=is_disabled)
        st.markdown("<div class='grey-btn-marker'></div>", unsafe_allow_html=True)
        st.button("Catálogo", type="primary", width="stretch", on_click=go_panel, args=("Catálogo",), disabled=is_disabled)
        
    elif panel == "Geometría":
        st.button("⬅ Volver", type="secondary", on_click=go_panel, args=("Main",))
        render_siblings_top(nav_group1, "Geometría")
        st.header("Geometría")
        
        wt_idx = 0 if st.session_state.get("wall_type", "Metálico") == "Metálico" else 1
        st.radio("Tipo de Muros", ["Metálico", "Tilt-Up"], index=wt_idx, key="_wall_type", on_change=update_val, args=("wall_type",), horizontal=True)
        
        with st.expander("Dimensiones Generales", expanded=False):
            st.number_input("Longitud de Armaduras (m)", min_value=1.0, step=0.1, value=st.session_state.larm, key="_larm", on_change=update_larm)
            st.number_input("Longitud de Joists (m)", min_value=1.0, step=0.1, value=st.session_state.ljoist, key="_ljoist", on_change=update_val, args=("ljoist",))
            
            st.number_input("Número de Bahías (Profundidad)", min_value=1, step=1, value=st.session_state.nbay, key="_nbay", on_change=update_val, args=("nbay",))
            st.number_input("Número de Entre-ejes (Ancho)", min_value=1, step=1, value=st.session_state.nspan, key="_nspan", on_change=update_val, args=("nspan",))
            
            st.number_input("Peralte Armadura (m)", min_value=0.5, step=0.1, value=st.session_state.harm, key="_harm", on_change=update_val, args=("harm",))
            
            # Relaciones L/10 y L/15
            l_10 = st.session_state.larm / 10.0
            l_15 = st.session_state.larm / 15.0
            st.markdown(f"<div style='font-size: 0.85em; color: gray; margin-top: -10px; margin-bottom: 10px;'>L/10 = {l_10:.2f} m.<br>L/15 = {l_15:.2f} m.</div>", unsafe_allow_html=True)
            
            st.number_input("Altura Libre (m)", min_value=1.0, step=0.1, value=st.session_state.hlib, key="_hlib", on_change=update_val, args=("hlib",))
            st.number_input("Subdivisiones (Debe ser par)", min_value=2, step=2, value=st.session_state.subdiv, key="_subdiv", on_change=update_subdiv)
            if st.session_state.get("subdiv_warning", False):
                st.markdown("<div style='font-size: 0.85em; color: red; margin-top: -10px; margin-bottom: 10px;'>Debe ser número par. Se ajustó automáticamente.</div>", unsafe_allow_html=True)
            
            # Relación de Separación (Sep)
            sep_val = st.session_state.larm / st.session_state.subdiv
            st.markdown(f"<div style='font-size: 0.85em; color: gray; margin-top: -10px; margin-bottom: 10px;'>Sep = {sep_val:.2f} m.</div>", unsafe_allow_html=True)

        with st.expander("Cubierta", expanded=False):
            rt_idx = 1 if st.session_state.roof_type == "2 Aguas" else 0
            st.radio("Tipo de Cubierta", ["1 Agua", "2 Aguas"], index=rt_idx, key="_roof_type", on_change=update_val, args=("roof_type",))
            st.number_input("Pendiente (%)", min_value=0.0, step=0.5, value=st.session_state.slope_pct, key="_slope_pct", on_change=update_val, args=("slope_pct",))

        with st.expander("Apoyos", expanded=False):
            if 'apoyo_ui' not in st.session_state:
                if st.session_state.support_type == "FIXED":
                    st.session_state.apoyo_ui = "Empotrado"
                elif st.session_state.support_type == "PINNED":
                    st.session_state.apoyo_ui = "Articulado"
                else:
                    st.session_state.apoyo_ui = "Resorte"
                    
            def update_apoyo():
                if st.session_state.apoyo_ui == "Empotrado":
                    st.session_state.support_type = "FIXED"
                elif st.session_state.apoyo_ui == "Articulado":
                    st.session_state.support_type = "PINNED"
                else:
                    st.session_state.support_type = "RESORTE"
                    
            st.radio("Tipo de Apoyo", ["Empotrado", "Articulado", "Resorte"], key="apoyo_ui", on_change=update_apoyo)
                
            if st.session_state.support_type == "RESORTE":
                if "resorte_val" not in st.session_state:
                    st.session_state.resorte_val = "1,000,000"
                st.session_state.resorte_val = st.text_input("Rigidez del resorte:", value=st.session_state.resorte_val)

        with st.expander("Armaduras Secundarias", expanded=False):
            sec_mode = st.radio("", ["Ninguno", "Automático", "Todos los Ejes", "Personalizado"], 
                                index=["Ninguno", "Automático", "Todos los Ejes", "Personalizado"].index(st.session_state.get('sec_truss_mode', 'Ninguno')),
                                key="sec_truss_mode", label_visibility="collapsed")
                                
            if sec_mode == "Personalizado":
                st.write("Ejes:")
                # Ordenar del centro hacia afuera
                mid_j = st.session_state.nspan / 2.0
                if st.session_state.wall_type == "Tilt-Up":
                    interior_j = list(range(1, st.session_state.nspan))
                else:
                    interior_j = list(range(0, st.session_state.nspan + 1))
                interior_j.sort(key=lambda j: (abs(j - mid_j), j))
                interior_j = interior_j[:10] # Limitar a 10 ejes máximo
                
                selected_ejes = st.session_state.get('sec_truss_custom_ejes', [])
                for j in interior_j:
                    st.checkbox(f"X = {j * st.session_state.larm:.2f} m", value=(j in selected_ejes), key=f"sec_eje_{j}")

        if st.session_state.wall_type != "Tilt-Up":
            with st.expander("Columnas de Viento", expanded=False):
                st.checkbox("Columnas de Viento", value=st.session_state.add_wind_cols, key="_add_wind_cols", on_change=update_val, args=("add_wind_cols",))
                if st.session_state.add_wind_cols:
                    st.number_input("Separación Máxima (m)", min_value=1.0, step=0.1, value=float(st.session_state.max_wind_dist), key="_max_wind_dist", on_change=update_val, args=("max_wind_dist",))
        else:
            st.session_state.add_wind_cols = False
        render_siblings_bottom(nav_group1, "Geometría")

    elif panel == "Cargas":
        st.button("⬅ Volver", type="secondary", on_click=go_panel, args=("Main",))
        render_siblings_top(nav_group1, "Cargas")
        st.header("Cargas")
        with st.expander("Gravitacionales", expanded=True):
            st.number_input("Carga Muerta (kg/m²)", min_value=0.0, step=5.0, value=st.session_state.c_muerta, key="_c_muerta", on_change=update_c_muerta)
            st.number_input("Carga Viva (kg/m²)", min_value=0.0, step=5.0, value=st.session_state.c_viva, key="_c_viva", on_change=update_c_viva)
            st.number_input("Granizo (kg/m²)", min_value=0.0, step=5.0, value=st.session_state.c_granizo, key="_c_granizo", on_change=update_val, args=("c_granizo",))
            
        with st.expander("Viento", expanded=False):
            st.number_input("Barlovento (kg/m²)", min_value=0.0, step=1.0, value=st.session_state.v_barlovento, key="_v_barlovento", on_change=update_val, args=("v_barlovento",))
            st.number_input("Sotavento (kg/m²)", min_value=0.0, step=1.0, value=st.session_state.v_sotavento, key="_v_sotavento", on_change=update_val, args=("v_sotavento",))
            st.number_input("Laterales (kg/m²)", min_value=0.0, step=1.0, value=st.session_state.v_laterales, key="_v_laterales", on_change=update_val, args=("v_laterales",))
            st.number_input("Succión (kg/m²)", min_value=0.0, step=1.0, value=st.session_state.v_succion, key="_v_succion", on_change=update_val, args=("v_succion",))

        with st.expander("Sismo", expanded=False):
            st.number_input("Coeficiente Sísmico", min_value=0.0, step=0.01, value=st.session_state.coef_sismico, key="_coef_sismico", on_change=update_val, args=("coef_sismico",))
            st.number_input("Ductilidad", min_value=1.0, step=0.5, value=st.session_state.ductilidad, key="_ductilidad", on_change=update_val, args=("ductilidad",))
            
            if st.session_state.cm_sismo is None:
                st.session_state.cm_sismo = st.session_state.c_muerta
            if st.session_state.cv_sismo is None:
                st.session_state.cv_sismo = st.session_state.c_viva * 0.25
                
            st.number_input("Carga Muerta para Sismo (kg/m²)", min_value=0.0, step=5.0, value=st.session_state.cm_sismo, key="_cm_sismo", on_change=update_val, args=("cm_sismo",))
            st.number_input("Carga Viva para Sismo (kg/m²)", min_value=0.0, step=5.0, value=st.session_state.cv_sismo, key="_cv_sismo", on_change=update_val, args=("cv_sismo",))
        render_siblings_bottom(nav_group1, "Cargas")

    elif panel == "Prediseño":
        st.button("⬅ Volver", type="secondary", on_click=go_panel, args=("Main",))
        render_siblings_top(nav_group1, "Prediseño")
        st.header("Prediseño")
        
        def reset_cv_selection():
            for k in list(st.session_state.keys()):
                if k.startswith("sel_CV"):
                    del st.session_state[k]
        
        
        with st.expander("Columnas", expanded=True):
            grupos_cols = prediseno.clasificar_columnas(model)
            
            if not grupos_cols:
                st.warning("No se encontraron columnas para diseñar.")
            else:
                usar_2w = st.session_state.get("usar_2w_checkbox", False)
                
                st.radio("Resaltar en 3D:", list(sorted(grupos_cols.keys())), key="highlight_grupo_col")
                for nombre_grupo in sorted(grupos_cols.keys()):
                    top_5 = prediseno.predisenar_grupo(nombre_grupo, model, usar_2w)
                    
                    if top_5:
                        opciones = [p['perfil']['nombre'] for p in top_5]
                        
                        key_name = f"sel_{nombre_grupo}"
                        if key_name in st.session_state and st.session_state[key_name] not in opciones:
                            del st.session_state[key_name]
                            
                        st.selectbox(nombre_grupo, options=opciones, key=key_name)
                    else:
                        st.error(f"No se encontraron perfiles óptimos para {nombre_grupo}.")
                        
                    if "CV" in nombre_grupo:
                        st.checkbox("Usar perfiles 2W", key="usar_2w_checkbox", on_change=reset_cv_selection)
                        st.markdown("<div style='margin-top:-15px; font-size:12px; color:#888;'>(Requiere Base de Datos WD)</div>", unsafe_allow_html=True)
        render_siblings_bottom(nav_group1, "Prediseño")

    elif panel == "Diseño":
        st.button("⬅ Menú Principal", type="secondary", on_click=go_panel, args=("Main",))
        
        st.markdown("<h3 style='margin-top: 10px; margin-bottom: 30px;'>Diseño Estructural</h3>", unsafe_allow_html=True)
        
        import sys, os
        if os.path.join(os.path.dirname(__file__), 'staad_link') not in sys.path:
            sys.path.append(os.path.join(os.path.dirname(__file__), 'staad_link'))
        from link import check_staad_status
        staad_info = check_staad_status()
        
        target_file = st.session_state.get("active_staad_file", "")
        if staad_info["status"] in ["connected", "connected_no_results"] and target_file and target_file.lower() == str(staad_info["filename"]).lower():
            color = "#005cb2" if staad_info["status"] == "connected" else "#d4b106"
            text = f"Sincronizado a modelo:<br><span style='color: {color}; font-weight: normal;'>{staad_info['filename']}</span>"
        else:
            # Override if disconnected or mismatched
            staad_info["status"] = "disconnected"
            color = "#ba281b" # Red
            text = "No sincronizado al modelo exportado"
            
        st.markdown(f"<div style='margin-bottom: 20px; font-size: 14px; font-weight: 600;'><span style='color: {color}; font-size: 10px;'>●</span> {text}</div>", unsafe_allow_html=True)
        
        render_siblings_bottom(nav_group2, "Diseño")


    elif panel == "Catálogo":
        st.button("⬅ Volver", type="secondary", on_click=go_panel, args=("Main",))
        render_siblings_top(nav_group2, "Catálogo")
        st.header("Catálogo")
        render_siblings_bottom(nav_group2, "Catálogo")

if st.session_state.current_panel == "Diseño":
    
    col_izq, col_der = st.columns([2, 1])
    
    with col_izq:
        import sys, os
        if os.path.join(os.path.dirname(__file__), 'staad_link') not in sys.path:
            sys.path.append(os.path.join(os.path.dirname(__file__), 'staad_link'))
        from link import check_staad_status, run_analysis
        
        staad_info = check_staad_status()
        is_disabled = (staad_info["status"] == "disconnected")
        
        col_btn, col_spin = st.columns([1, 2])
        with col_btn:
            if st.button("Correr Análisis ▶", type="primary", disabled=is_disabled):
                st.session_state.is_analyzing = True
        
        if st.session_state.get("is_analyzing", False):
            with col_spin:
                with st.spinner("Corriendo análisis en STAAD.Pro..."):
                    run_analysis()
                st.session_state.is_analyzing = False
                st.rerun()
                
        st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
        
        def update_highlight(key):
            st.session_state["highlight_diseno_active"] = st.session_state[key]
            
        def render_group_results(tab_name, grupos_dict):
            if not grupos_dict:
                st.info(f"No hay grupos definidos para {tab_name}")
                return
            key_name = f"highlight_diseno_{tab_name}"
            opts = list(sorted(grupos_dict.keys()))
            if key_name not in st.session_state or st.session_state[key_name] not in opts:
                st.session_state[key_name] = opts[0]
            sel_g = st.radio("Seleccionar Grupo:", opts, key=key_name, horizontal=True, on_change=update_highlight, args=(key_name,))
            if "highlight_diseno_active" not in st.session_state:
                st.session_state["highlight_diseno_active"] = sel_g
            m_ids = grupos_dict[sel_g]
            
            st.markdown(f"<div style='margin-top: 10px; padding: 15px; border-radius: 8px; background-color: #f8f9fa; border: 1px solid #e9ecef;'>", unsafe_allow_html=True)
            
            if sel_g == "_CVH":
                DIAMETERS = [1.905, 2.54, 3.175, 3.81, 4.445, 5.08]
                DIAMETERS_STR = ["3/4\"", "1\"", "1 1/4\"", "1 1/2\"", "1 3/4\"", "2\""]
                
                if "cvh_props" not in st.session_state:
                    st.session_state.cvh_props = {m: 1.905 for m in m_ids}
                    
                from link import get_design_results
                ratios = {}
                if staad_info["status"] != "disconnected" and not st.session_state.get("is_analyzing", False):
                    ratios = get_design_results(m_ids)
                
                stats = {}
                for m in m_ids:
                    d = st.session_state.cvh_props.get(m, 1.905)
                    r = ratios.get(m, 0.0)
                    if d not in stats:
                        stats[d] = {'pass': 0, 'fail': 0, 'mids_pass': [], 'mids_fail': []}
                    if r <= 0.5:
                        stats[d]['pass'] += 1
                        stats[d]['mids_pass'].append(m)
                    else:
                        stats[d]['fail'] += 1
                        stats[d]['mids_fail'].append(m)
                
                st.markdown(f"**Grupo _CVH** ({len(m_ids)} elementos)")
                st.markdown("Ratio máximo permitido: **0.50**")
                
                options = []
                options_map = {}
                for d in DIAMETERS:
                    if d in stats:
                        idx = DIAMETERS.index(d)
                        label = f"Redondo {DIAMETERS_STR[idx]} [{stats[d]['pass']} Pasan, {stats[d]['fail']} Fallan]"
                        options.append(label)
                        options_map[label] = d
                        
                if not options:
                    st.info("No hay contravientos horizontales evaluados aún.")
                else:
                    sel_label = st.radio("Inspeccionar en visualizador 3D:", options, key="cvh_inspect")
                    sel_d = options_map[sel_label]
                    
                    h_colors = {}
                    for m in stats[sel_d]['mids_pass']:
                        h_colors[m] = 'green'
                    for m in stats[sel_d]['mids_fail']:
                        h_colors[m] = 'red'
                    st.session_state["highlight_colors_active"] = h_colors
                
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Optimizar CVH ⚡", type="primary"):
                    st.session_state.is_analyzing = True
                    changed = False
                    for m in m_ids:
                        r = ratios.get(m, 0.0)
                        if r > 0.5:
                            curr_d = st.session_state.cvh_props.get(m, 1.905)
                            try:
                                idx = DIAMETERS.index(curr_d)
                                if idx < len(DIAMETERS) - 1:
                                    st.session_state.cvh_props[m] = DIAMETERS[idx+1]
                                    changed = True
                            except ValueError:
                                pass
                    
                    if changed:
                        import staad_writer
                        name_to_staad = {p['nombre']: p.get('nombre_staad', p['nombre']) for p in db_or + db_w}
                        selected_profiles = {}
                        all_groups = {**prediseno.clasificar_columnas(model), **{k: v for k, v in model.groups.items() if k.startswith(('_CS', '_CI', '_DIAG', '_MONT', '_CV'))}}
                        for g in all_groups.keys():
                            if g == "_CVH": continue
                            ui_name = st.session_state.get(f"sel_{g}")
                            if ui_name:
                                staad_name = name_to_staad.get(ui_name)
                                if staad_name:
                                    selected_profiles[g] = staad_name
                                    
                        staad_text = staad_writer.write_staad(model, selected_profiles=selected_profiles, cvh_props=st.session_state.cvh_props)
                        clean_name = st.session_state.get("active_staad_file", "Modelo.std")
                        export_path = st.session_state.get("export_path", ".")
                        import os
                        full_path = os.path.join(export_path, clean_name)
                        with open(full_path, "w", encoding="utf-8") as f:
                            f.write(staad_text)
                            
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
                return

            st.markdown(f"**Grupo {sel_g}** ({len(m_ids)} elementos)")
            
            can_modify = not (sel_g.startswith('_DIAG') or sel_g.startswith('_MONT'))
            es_w = sel_g.startswith('_COL') or sel_g.startswith('_CV')
            
            import prediseno
            db_or = prediseno.cargar_base_datos_excel()
            db_w = prediseno.PERFILES_W
            opciones = [p['nombre'] for p in db_w] if es_w else [p['nombre'] for p in db_or]
            
            curr_key = f"sel_{sel_g}"
            if curr_key not in st.session_state:
                # Inicializar con logica de Prediseño para que empate con la exportacion
                usar_2w = st.session_state.get("usar_2w_checkbox", False)
                top_5 = prediseno.predisenar_grupo(sel_g, model, usar_2w)
                if top_5:
                    st.session_state[curr_key] = top_5[0]['perfil']['nombre']
                else:
                    st.session_state[curr_key] = opciones[0] if opciones else ""
                
            if can_modify:
                st.selectbox("Perfil Asignado:", options=opciones, key=curr_key)
            else:
                st.write(f"Perfil Asignado: Auto (Comando SELECT de STAAD)")
            
            if staad_info["status"] != "disconnected" and not st.session_state.get("is_analyzing", False):
                from link import get_design_results
                ratios = get_design_results(m_ids)
                
                valid_ratios = {k: v for k, v in ratios.items() if v > 0.0}
                if valid_ratios:
                    max_id = max(valid_ratios, key=valid_ratios.get)
                    max_ratio = valid_ratios[max_id]
                    
                    c1, c2 = st.columns([1, 1])
                    with c1:
                        st.metric(label="Ratio Crítico", value=f"{max_ratio:.3f}", delta=f"Barra más crítica: {max_id}", delta_color="off")
                        if max_ratio > 1.0:
                            st.markdown("<span style='color: #ba281b; font-weight: bold;'>⚠️ Falla por capacidad</span>", unsafe_allow_html=True)
                        else:
                            st.markdown("<span style='color: #0b7a0b; font-weight: bold;'>✅ Diseño Adecuado</span>", unsafe_allow_html=True)
                            
                    with c2:
                        if can_modify:
                            st.markdown("<br>", unsafe_allow_html=True)
                            if st.button("Optimizar Grupo ⚡", key=f"btn_opt_{sel_g}", type="primary"):
                                st.session_state.is_analyzing = True
                                nuevo_perfil = prediseno.optimizar_perfil(st.session_state[curr_key], max_ratio, es_w=es_w, ratio_objetivo=0.95)
                                if nuevo_perfil != st.session_state[curr_key]:
                                    st.session_state[curr_key] = nuevo_perfil
                                    
                                    import staad_writer
                                    name_to_staad = {p['nombre']: p.get('nombre_staad', p['nombre']) for p in db_or + db_w}
                                    selected_profiles = {}
                                    all_groups = {**prediseno.clasificar_columnas(model), **{k: v for k, v in model.groups.items() if k.startswith(('_CS', '_CI', '_DIAG', '_MONT', '_CV'))}}
                                    for g in all_groups.keys():
                                        ui_name = st.session_state.get(f"sel_{g}")
                                        if ui_name:
                                            staad_name = name_to_staad.get(ui_name)
                                            if staad_name:
                                                selected_profiles[g] = staad_name
                                                
                                    staad_text = staad_writer.write_staad(model, selected_profiles=selected_profiles)
                                    clean_name = st.session_state.get("active_staad_file", "Modelo.std")
                                    export_path = st.session_state.get("export_path", ".")
                                    import os
                                    full_path = os.path.join(export_path, clean_name)
                                    with open(full_path, "w", encoding="utf-8") as f:
                                        f.write(staad_text)
                                        
                                st.rerun()
                else:
                    st.warning("No se encontraron resultados de diseño. Verifica comandos CHECK CODE.")
            else:
                st.info("Sincroniza y corre el análisis para ver los resultados.")
            st.markdown("</div>", unsafe_allow_html=True)

        tab_col, tab_arm, tab_cv = st.tabs(["Columnas", "Armaduras", "Contravientos"])
        
        with tab_col:
            import prediseno
            grupos_c = {k: v for k, v in prediseno.clasificar_columnas(model).items() if len(v) > 0}
            render_group_results("Columnas", grupos_c)
            
        with tab_arm:
            # Solo Cuerda Superior y Cuerda Inferior por tipo de armadura (sin montantes ni diagonales)
            grupos_a = {k: v for k, v in model.groups.items() if (k.startswith('_CS') or k.startswith('_CI')) and len(v) > 0}
            render_group_results("Armaduras", grupos_a)
            
        with tab_cv:
            grupos_v = {k: v for k, v in model.groups.items() if k.startswith('_CV') and len(v) > 0}
            render_group_results("Contravientos", grupos_v)

    with col_der:
        st.markdown("<b>Visualizador 3D</b>", unsafe_allow_html=True)
        
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        # Using the last active group for highlighting if any
        highlight_col = st.session_state.get("highlight_diseno_active", "Ninguno")
        import prediseno
        all_grps = {**prediseno.clasificar_columnas(model), **model.groups}
        h_ids = all_grps.get(highlight_col, None)
        h_colors = None
        if highlight_col == "_CVH" and "highlight_colors_active" in st.session_state:
            h_colors = st.session_state["highlight_colors_active"]
            h_ids = None # Override to use colors instead of simple highlight
        fig = plot_model(model, show_supports=True, highlight_ids=h_ids, highlight_colors=h_colors)
        
        # Cube aspect ratio to prevent clipping, and zoomed out slightly
        fig.update_layout(
            scene_camera=dict(eye=dict(x=1.8, y=1.8, z=1.8)),
            margin=dict(l=0, r=0, b=0, t=0),
            scene=dict(aspectmode='data')
        )
        st.plotly_chart(fig, use_container_width=True, config={'displaylogo': False})

elif st.session_state.current_panel == "Catálogo":
    st.title("Catálogo de Conceptos")
    st.write("En desarrollo...")

else:
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("<div style='margin-top: -15px;'></div>", unsafe_allow_html=True)
        st.subheader("Visualizador 3D")
        show_sup = (st.session_state.current_panel == "Geometría")
        highlight_col = st.session_state.get("highlight_grupo_col", "C-1") if st.session_state.current_panel == "Prediseño" else "Ninguno"
        highlight_ids = None
        if highlight_col != "Ninguno" and highlight_col in prediseno.clasificar_columnas(model):
            highlight_ids = prediseno.clasificar_columnas(model).get(highlight_col, [])
        fig = plot_model(model, show_supports=show_sup, highlight_ids=highlight_ids)
        st.plotly_chart(fig, use_container_width=True, config={
            'displaylogo': False,
            'modeBarButtonsToRemove': ['resetCameraDefault3d', 'resetCameraLastSave3d', 'hoverClosest3d', 'tableRotation']
        })

    with col2:
        with st.container():
            st.markdown("<div class='ios-glass-marker'></div>", unsafe_allow_html=True)
        
            st.markdown("**Nombre Proyecto:**")
            file_name_export = st.text_input("proj_name", value="Modelo.std", label_visibility="collapsed")
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        
            st.markdown("**Ubicación:**")
        
            if 'export_path' not in st.session_state:
                st.session_state.export_path = r'C:\Users\josee\OneDrive\Escritorio\MODELOS GENERADOS'
            
            parts = os.path.normpath(st.session_state.export_path).split(os.sep)
            if len(parts) >= 2:
                display_text = os.path.join(parts[-2], parts[-1])
            else:
                display_text = st.session_state.export_path
            
            path_col, btn_col = st.columns([3, 1])
            with path_col:
                st.markdown("<div class='path-marker'></div>", unsafe_allow_html=True)
                st.text_input("ub", value=display_text, label_visibility="collapsed")
            with btn_col:
                if st.button("📁", help="Examinar..."):
                    import subprocess, sys
                    code = f"""
    import tkinter as tk
    from tkinter import filedialog
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    folder = filedialog.askdirectory(master=root, title="Seleccionar Carpeta", initialdir=r"{st.session_state.export_path}")
    root.destroy()
    print(folder)
                    """
                    try:
                        result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=30)
                        folder_selected = result.stdout.strip()
                        if folder_selected and folder_selected != "()":
                            st.session_state.export_path = folder_selected
                            st.rerun()
                    except Exception as e:
                        pass
                    
            # Obtener nombres de STAAD
            import prediseno
            db_or = prediseno.cargar_base_datos_excel()
            db_w = prediseno.PERFILES_W
            name_to_staad = {p['nombre']: p.get('nombre_staad', p['nombre']) for p in db_or + db_w}
        
            selected_profiles = {}
            all_grps = {**prediseno.clasificar_columnas(model), **{k: v for k, v in model.groups.items() if k.startswith(('_CS', '_CI', '_CV'))}}
            for g in all_grps.keys():
                ui_name = st.session_state.get(f"sel_{g}")
                if not ui_name:
                    # Forzar calculo de Prediseño si el usuario no paso por esa pestaña
                    usar_2w = st.session_state.get("usar_2w_checkbox", False)
                    top_5 = prediseno.predisenar_grupo(g, model, usar_2w)
                    if top_5:
                        ui_name = top_5[0]['perfil']['nombre']
                        st.session_state[f"sel_{g}"] = ui_name
                
                if ui_name:
                    staad_name = name_to_staad.get(ui_name)
                    if staad_name:
                        selected_profiles[g] = staad_name
                    
            staad_text = write_staad(model, selected_profiles=selected_profiles)
        
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
                        import subprocess
                        subprocess.call(('open', full_path))
                        
                    import time
                    time.sleep(5)
                    st.session_state.file_generated = True
                    st.session_state.active_staad_file = clean_name
                    st.session_state.current_panel = "Diseño"
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error al guardar o abrir en '{full_path}': {e}")


        with st.container():
            st.markdown("<div class='ios-glass-marker'></div>", unsafe_allow_html=True)
            st.subheader("Elementos")
            num_wind_cols = len(model.groups.get('_COLVIENTO', []))
            wind_cols_line = f"&emsp;• Columnas (Viento): {num_wind_cols}<br>" if num_wind_cols > 0 else ""
            num_purlins = (st.session_state.nspan + 1) * st.session_state.nbay + st.session_state.nspan * (st.session_state.subdiv - 1) * st.session_state.nbay
        
            # Deduct purlins replaced by secondary trusses
            num_sec_trusses_axes = len(model.sec_trusses_j)
            num_purlins -= (num_sec_trusses_axes * st.session_state.nbay)
        
            num_sec_trusses_total = num_sec_trusses_axes * st.session_state.nbay
            sec_trusses_line = f"&emsp;• Armaduras (Secundarias): {num_sec_trusses_total}<br>" if num_sec_trusses_total > 0 else ""
        
            st.markdown(f"""
            <div style='line-height: 1.8;'>
                • Columnas: {(st.session_state.nbay + 1) * (st.session_state.nspan + 1)}<br>
                {wind_cols_line}• Armaduras: {(st.session_state.nbay + 1) * st.session_state.nspan}<br>
                {sec_trusses_line}• Contravientos: {len(model.groups.get('_CVH', []))}<br>
                • Largueros: {num_purlins}
            </div>
            <div style='height: 25px;'></div>
            """, unsafe_allow_html=True)

# Javascript para hacer que los expanders funcionen como acordeón
components.html(
    """
    <script>
    const updateExpanders = () => {
        const expanders = window.parent.document.querySelectorAll('details');
        expanders.forEach(exp => {
            exp.removeAttribute('name'); // Quitar para no interferir con Streamlit
            const summary = exp.querySelector('summary');
            if (summary && !summary.dataset.accordionAttached) {
                summary.dataset.accordionAttached = 'true';
                summary.addEventListener('click', (e) => {
                    const isOpen = exp.hasAttribute('open');
                    if (!isOpen) {
                        expanders.forEach(otherExp => {
                            if (otherExp !== exp && otherExp.hasAttribute('open')) {
                                const otherSummary = otherExp.querySelector('summary');
                                if (otherSummary) {
                                    otherSummary.click(); // Cerrarlo simulando un click para que la flecha se actualice
                                }
                            }
                        });
                    }
                });
            }
        });
    };
    updateExpanders();
    const observer = new MutationObserver(updateExpanders);
    observer.observe(window.parent.document.body, { childList: true, subtree: true });
    </script>
    """,
    height=0,
    width=0
)

