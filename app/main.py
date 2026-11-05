import streamlit as st
import math
import os
import sys
import subprocess
import importlib

# Silenciar advertencia de valores por defecto en widgets con Session State
try:
    import streamlit.elements.lib.policies as _policies
    _policies._shown_default_value_warning = True
except Exception:
    pass


# Ensure app directory and root directory are in sys.path for both local and web environments
app_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(app_dir)
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import streamlit.components.v1 as components

# Force reload of custom modules to ensure Streamlit hot-reloads them (Only in Local Dev)
if os.environ.get("LOCAL_DEV") == "1":
    import model
    import staad_writer
    import visualizer
    import prediseno
    importlib.reload(model)
    importlib.reload(staad_writer)
    importlib.reload(visualizer)
    importlib.reload(prediseno)
import model
import staad_writer
import visualizer
import prediseno
try:
    import cimentacion_cad
except Exception:
    pass
try:
    import Catalogo
    import Catalogo.catalogo_ui
    import Catalogo.catalogo_state
    importlib.reload(Catalogo)
    importlib.reload(Catalogo.catalogo_ui)
    importlib.reload(Catalogo.catalogo_state)
except Exception:
    pass


from model import StaadModel
from staad_writer import write_staad
from visualizer import plot_model

# Import configurations
is_mobile_client = False
try:
    import js
    if js.window.innerWidth <= 768:
        is_mobile_client = True
except Exception:
    pass


# Configuración de icono: "black", "dark_slate" o "blue" (cambiar aquí para alternar color)
ICONO_COLOR = "blue"
icono_filename = {
    "black": "staad_black.ico",
    "dark_slate": "staad_darkslate.ico",
    "blue": "FrameOne2.jpg"
}.get(ICONO_COLOR, "FrameOne2.jpg")

icono_path = os.path.join(os.path.dirname(__file__), "..", icono_filename)
if not os.path.exists(icono_path):
    icono_path = os.path.join(os.path.dirname(__file__), "..", "FrameOne2.jpg")

icono_small_path = os.path.join(os.path.dirname(__file__), "..", "FrameOne3.png")

page_icon = icono_small_path if os.path.exists(icono_small_path) else "🏢"
st.set_page_config(page_title="FrameOne", page_icon=page_icon, layout="wide")

# Forzar Tema Light por defecto y Puente de Mensajes (ESC, Minimizar)
components.html("""
<script>
try {
    const themeVal = JSON.stringify('Light');
    const pathKey = 'stActiveTheme-' + window.parent.location.pathname + '-v2';
    const rootKey = 'stActiveTheme-/-v2';
    const currentTheme = window.parent.localStorage.getItem(pathKey) || window.parent.localStorage.getItem(rootKey);
    if (currentTheme !== themeVal) {
        window.parent.localStorage.setItem(pathKey, themeVal);
        window.parent.localStorage.setItem(rootKey, themeVal);
        window.parent.localStorage.setItem('stActiveTheme', themeVal);
        window.parent.location.reload();
    }
} catch (e) {}

// Escuchar tecla ESC dentro de Streamlit y notificar a la ventana superior
window.parent.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        window.top.postMessage('pywebview:restore', '*');
        try {
            if (window.top.pywebview && window.top.pywebview.api) {
                window.top.pywebview.api.restore();
            }
        } catch(err) {}
    }
});

document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        window.top.postMessage('pywebview:restore', '*');
        try {
            if (window.top.pywebview && window.top.pywebview.api) {
                window.top.pywebview.api.restore();
            }
        } catch(err) {}
    }
});
</script>
""", height=0, width=0)

if st.session_state.get("minimize_next"):
    st.session_state.minimize_next = False
    components.html("""
    <script>
    try {
        window.top.postMessage('pywebview:minimize', '*');
        const api = (window.top && window.top.pywebview && window.top.pywebview.api) || 
                    (window.parent && window.parent.pywebview && window.parent.pywebview.api);
        if (api && api.minimize) {
            api.minimize();
        }
    } catch(e) {}
    </script>
    """, height=0, width=0)

st.markdown("""
<style>
/* Forzar Colores de Tema Claro en todo el contenedor de la App */
:root, [data-testid="stAppViewContainer"], .stApp {
    background-color: #ffffff !important;
    color: #1e293b !important;
}

[data-testid="stSidebar"] {
    background-color: #f8fafc !important;
    border-right: 1px solid #e2e8f0 !important;
}

/* Ocultar barra superior completa de Streamlit (Deploy y menú de 3 puntos) */
header[data-testid="stHeader"] {
    display: none !important;
}
#MainMenu {
    visibility: hidden !important;
    display: none !important;
}
footer {
    visibility: hidden !important;
    display: none !important;
}
[data-testid="stToolbar"] {
    display: none !important;
}
[data-testid="stDecoration"] {
    display: none !important;
}
[data-testid="stStatusWidget"] {
    display: none !important;
}
.stDeployButton,
[data-testid="stDeployButton"],
div[data-testid="stToolbarActions"],
button[title="Deploy this app"],
button[title="View app in Streamlit Community Cloud"] {
    display: none !important;
}

/* Mobile layout adjustments for Plotly 3D Viewer */
@media screen and (max-width: 768px) {
    div[data-testid="stPlotlyChart"],
    div[data-testid="stPlotlyChart"] iframe,
    div[data-testid="stPlotlyChart"] .js-plotly-plot, 
    div[data-testid="stPlotlyChart"] .plot-container.plotly, 
    div[data-testid="stPlotlyChart"] .svg-container {
        height: 450px !important;
        min-height: 450px !important;
        max-height: 450px !important;
    }
}

/* iOS Liquid Glass Effect for containers */
div[data-testid="stVerticalBlock"]:has(> div.element-container div.ios-glass-marker) {
    background: rgba(255, 255, 255, 0.45);
    backdrop-filter: blur(15px);
    -webkit-backdrop-filter: blur(15px);
    border-radius: 16px;
    padding: 12px 16px;
    box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.8);
    margin-bottom: 10px;
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
    width: 79% !important;
    margin: 0 auto 15px auto !important;
    display: block !important;
}
[data-testid="stSidebar"] [data-testid="stImage"] button {
    display: none !important;
}
/* Make the divider faint grey */
hr {
    margin: 15px 0 !important;
    border-top: 1px solid rgba(0,0,0,0.1) !important;
}
/* Reduce overall top padding to avoid scroll */
.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 1rem !important;
}
</style>
""", unsafe_allow_html=True)


# CSS para botones
st.markdown("""
    <style>
    /* Variables globales de tema */
    :root, html, body, #root, [data-testid="stAppViewContainer"] {
        --primary-color: #005cb2 !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
    }

    /* Reducción general de fuentes para la barra lateral y controles */
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2 {
        font-size: 18px !important;
        font-weight: 600 !important;
        color: #0f172a !important;
        margin-top: 4px !important;
        margin-bottom: 8px !important;
        letter-spacing: -0.2px !important;
    }

    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] label p,
    section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
    section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] span {
        font-size: 12px !important;
        font-weight: 500 !important;
        color: #334155 !important;
        margin-bottom: 2px !important;
        line-height: 1.25 !important;
    }

    section[data-testid="stSidebar"] div[role="radiogroup"] label p,
    section[data-testid="stSidebar"] [data-testid="stCheckbox"] label p {
        font-size: 12.5px !important;
        font-weight: normal !important;
        color: #1e293b !important;
    }

    /* Inputs numéricos y textos en sidebar */
    section[data-testid="stSidebar"] input {
        font-size: 12.5px !important;
        padding: 4px 8px !important;
        height: 34px !important;
        color: #0f172a !important;
    }

    /* Forzar accent-color nativo azul */
    input[type="checkbox"], input[type="radio"] {
        accent-color: #005cb2 !important;
    }

    /* ======================================================== */
    /* Tema Azul (#005cb2) SOLO para Iconos de Checkboxes y Radios */
    /* ======================================================== */

    /* Reset estricto: Nunca aplicar fondo a textos, etiquetas o contenedores de opciones */
    div[data-testid="stCheckbox"] label,
    div[data-testid="stCheckbox"] label p,
    div[data-testid="stCheckbox"] label span,
    div[data-testid="stCheckbox"] [data-testid="stWidgetLabel"],
    div[data-testid="stRadio"] label,
    div[data-testid="stRadio"] label p,
    div[data-testid="stRadio"] label span,
    div[data-testid="stRadio"] [data-testid="stWidgetLabel"],
    div[data-testid="stRadioOption"],
    div[data-testid="stRadioOption"] p,
    div[data-testid="stRadioOption"] span,
    div[data-testid="stRadioOption"] > div,
    div[data-testid="stRadioOption"] > div > div {
        background: transparent !important;
        background-color: transparent !important;
    }

    /* 1. Checkbox: SOLO la cajita con la palomita */
    div[data-testid="stCheckbox"] label > div:first-child:has(svg),
    div[data-testid="stCheckbox"] label > span:first-child:has(svg),
    div[data-testid="stCheckbox"] label > div:first-child > div:has(svg),
    div[data-testid="stCheckbox"] div:has(> svg[viewBox="0 0 10 8"]) {
        background-color: #005cb2 !important;
        border-color: #005cb2 !important;
    }

    div[data-testid="stCheckbox"] svg {
        fill: #ffffff !important;
        stroke: #ffffff !important;
    }
    div[data-testid="stCheckbox"] svg polyline {
        stroke: #ffffff !important;
        fill: none !important;
    }

    /* 2. Radio Button: SOLO el círculo indicador de selección */
    div[data-testid="stRadioOption"][data-selected="true"] > div > div > div:first-child,
    div[data-testid="stRadio"] label[data-selected="true"] > div > div > div:first-child,
    div[data-testid="stRadio"] div[role="radiogroup"] label[data-selected="true"] > div > div > div:first-child {
        background-color: #005cb2 !important;
        border-color: #005cb2 !important;
    }

    /* Punto interior blanco del radio seleccionado */
    div[data-testid="stRadioOption"][data-selected="true"] > div > div > div:first-child > div,
    div[data-testid="stRadio"] label[data-selected="true"] > div > div > div:first-child > div,
    div[data-testid="stRadio"] div[role="radiogroup"] label[data-selected="true"] > div > div > div:first-child > div {
        background-color: #ffffff !important;
    }

    /* 3. Toggles activos */
    div[data-testid="stToggle"] label > div[aria-checked="true"],
    div[data-testid="stToggle"] [aria-checked="true"]:not(label):not(p):not(span) {
        background-color: #005cb2 !important;
        border-color: #005cb2 !important;
    }

    /* 4. Sliders */
    div[data-testid="stSlider"] [role="slider"] {
        background-color: #005cb2 !important;
        border-color: #005cb2 !important;
    }

    /* 5. Pestañas activas */
    div[data-testid="stTabs"] button[aria-selected="true"] {
        color: #005cb2 !important;
        border-bottom-color: #005cb2 !important;
    }

    div[data-testid="stNumberInputStepDown"],
    div[data-testid="stNumberInputStepUp"],
    div[data-testid="stNumberInput"] button {
        width: 1.5rem !important;
        height: 1.5rem !important;
        min-width: 1.5rem !important;
        padding: 0 !important;
        display: inline-flex !important;
    }
    div[data-testid="stNumberInputStepDown"] svg,
    div[data-testid="stNumberInputStepUp"] svg,
    div[data-testid="stNumberInput"] button svg {
        width: 12px !important;
        height: 12px !important;
    }

    /* Botones de incremento y decremento (+ y -) de stNumberInput */
    div[data-testid="stNumberInput"] button:hover,
    div[data-testid="stNumberInput"] button:focus,
    div[data-testid="stNumberInput"] button:active,
    div[data-testid="stNumberInputStepDown"]:hover,
    div[data-testid="stNumberInputStepDown"]:focus,
    div[data-testid="stNumberInputStepDown"]:active,
    div[data-testid="stNumberInputStepUp"]:hover,
    div[data-testid="stNumberInputStepUp"]:focus,
    div[data-testid="stNumberInputStepUp"]:active {
        background-color: #005cb2 !important;
        color: #ffffff !important;
        border-color: #005cb2 !important;
    }
    div[data-testid="stNumberInput"] button:hover svg,
    div[data-testid="stNumberInput"] button:focus svg,
    div[data-testid="stNumberInput"] button:active svg,
    div[data-testid="stNumberInputStepDown"]:hover svg,
    div[data-testid="stNumberInputStepDown"]:focus svg,
    div[data-testid="stNumberInputStepDown"]:active svg,
    div[data-testid="stNumberInputStepUp"]:hover svg,
    div[data-testid="stNumberInputStepUp"]:focus svg,
    div[data-testid="stNumberInputStepUp"]:active svg {
        fill: #ffffff !important;
        stroke: #ffffff !important;
    }

    /* ========================================================= */
    /* Submenús / Expanders con apariencia de tarjetas redondeadas */
    /* ========================================================= */
    div[data-testid="stExpander"],
    .stExpander {
        border: none !important;
        background: transparent !important;
        box-shadow: none !important;
        margin-bottom: 7px !important;
        margin-right: 15px !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stExpander"] details,
    div[data-testid="stExpander"] details {
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 8px !important;
        background-color: #f8fafc !important;
        overflow: hidden !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03) !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stExpander"] details:hover,
    div[data-testid="stExpander"] details:hover {
        border-color: #94a3b8 !important;
        background-color: #f1f5f9 !important;
    }

    /* Submenú activo / desplegado (Borde azul continuo) */
    section[data-testid="stSidebar"] div[data-testid="stExpander"] details[open],
    div[data-testid="stExpander"] details[open] {
        border: 2px solid #5b92cb !important;
        background-color: #f8fafc !important;
        box-shadow: 0 2px 8px rgba(0, 92, 178, 0.12) !important;
    }

    /* Encabezado del Submenú */
    section[data-testid="stSidebar"] div[data-testid="stExpander"] details summary,
    div[data-testid="stExpander"] details summary {
        padding: 7px 12px !important;
        background-color: #f8fafc !important;
        color: #1e293b !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        border-radius: 6px !important;
        display: flex !important;
        align-items: center !important;
        cursor: pointer !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stExpander"] details summary:hover,
    div[data-testid="stExpander"] details summary:hover {
        background-color: #f1f5f9 !important;
    }

    /* Encabezado cuando está abierto (fondo azul tenue y borde inferior divisorio) */
    section[data-testid="stSidebar"] div[data-testid="stExpander"] details[open] summary,
    div[data-testid="stExpander"] details[open] summary {
        background-color: #e8f1fa !important;
        border-bottom: 1px solid #cbd5e1 !important;
        border-radius: 6px 6px 0 0 !important;
        font-weight: 600 !important;
        color: #0f172a !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stExpander"] details summary p,
    div[data-testid="stExpander"] details summary p {
        font-size: 13px !important;
        font-weight: inherit !important;
        color: inherit !important;
        margin: 0 !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stExpander"] details summary svg,
    div[data-testid="stExpander"] details summary svg {
        color: #475569 !important;
        width: 14px !important;
        height: 14px !important;
    }

    /* Contenido dentro del Submenú */
    section[data-testid="stSidebar"] div[data-testid="stExpander"] [data-testid="stExpanderDetails"],
    div[data-testid="stExpander"] [data-testid="stExpanderDetails"] {
        padding: 8px 10px 10px 10px !important;
        background-color: #f8fafc !important;
        border-radius: 0 0 6px 6px !important;
    }

    /* Ajuste de fuente para los botones */
    button, button p, button div, button span {
        font-weight: 600 !important;
        font-size: 13.5px !important;
    }

    /* Botones principales (Azul Sólido) */
    section[data-testid="stSidebar"] button[kind="primary"] {
        background: #005cb2 !important;
        color: white !important;
        font-weight: 600 !important;
        font-size: 13.5px !important;
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
        padding: 3px 10px !important;
        width: auto !important;
        font-size: 13px !important;
        font-weight: 600 !important;
        box-shadow: 0px 1px 2px rgba(0,0,0,0.05) !important;
        border-radius: 4px !important;
        margin-bottom: 4px !important;
        margin-top: 4px !important;
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
        font-weight: 600 !important;
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
        font-weight: 600 !important;
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
        min-width: 275px !important;
        max-width: 300px !important;
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
    
    /* Ocultar la barra decorativa superior multicolor */
    [data-testid="stDecoration"], .stDecoration, div[class*="stDecoration"] {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
    }
    
    /* Estilos para títulos de widgets en submenús (expanders) y sidebar */
    div[data-testid="stExpander"] label p, section[data-testid="stSidebar"] label p {
        font-size: 15px !important;
        font-weight: bold !important;
        color: #0F172A !important;
    }

    /* Estilos para "Consideraciones Especiales" */
    div[data-testid="stVerticalBlock"]:has(> div > div > div > div > span#extremos-border) {
        border: 1px solid #3b82f6;
        border-radius: 8px;
        padding: 10px;
        margin-bottom: 15px;
        margin-top: -5px;
    }
    div[data-testid="stVerticalBlock"]:has(> div > div > div > div > span#extremos-border) input[type="number"] {
        pointer-events: none;
    }
    .widget-title { font-size: 12px; font-weight: 600; margin-bottom: 5px; color: #0F172A; }
    
    /* Ocultar el icono de hipervinculo que aparece junto a los titulos */
    .stHeadingContainer a {
        display: none !important;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<div style='color: gray; margin-bottom: -30px; margin-left: 10px; padding-top: 5px; position: relative; z-index: 10;'>Tensor Systems</div>", unsafe_allow_html=True)
st.title("FrameOne", anchor=False)
st.markdown("<div style='color: gray; margin-top: -15px; margin-bottom: 20px; margin-left: 10px;'>Modelado de Naves Industriales para STAAD.Pro</div>", unsafe_allow_html=True)

# Inicializar estado para variables por defecto
defaults = {
    "larm": 15.24, "ljoist": 12.192, "nbay": 7, "nspan": 4, 
    "harm": 1.30, "hlib": 9.75, "subdiv": 10,
    "roof_type": "2 Aguas", "slope_pct": 5.0, "support_type": "FIXED",
    "c_muerta": 30.0, "c_viva": 100.0, "c_granizo": 60.0,
    "v_barlovento": 86.0, "v_sotavento": 50.0, "v_laterales": 78.0, "v_succion": 95.0,
    "coef_sismico": 0.08, "ductilidad": 2.0, "cm_sismo": None, "cv_sismo": None,
    "add_wind_cols": True,
    "max_wind_dist": 8.0,
    "wall_type": "Metálico",
    "current_panel": "Main",
    "subdiv_warning": False,
    "dif_lengths": False,
    "larm_ext1": 15.24,
    "larm_ext2": 15.24,
    "subdiv_ext1": 10,
    "subdiv_ext2": 10,
    "ext_bays_active": False,
    "ext_bl": False,
    "ext_br": False,
    "ext_tl": False,
    "ext_tr": False,
    "ext_height_mode": "Primer Entre-Eje completo",
    "ext_larm": 15.24,
    "ext_subdiv": 10,
    "ext_depth": 2,
    "junta_constructiva_tipo": "Ninguna",
    "junta_max_dist_ft": 600,
    "reglamento_cargas": "Chihuahua / IBC",
    "metodo_diseno": "ASD",
    "grupo_importancia": "Grupo B",
    "sismo_bidireccional": False
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

def go_panel(p):
    st.session_state.current_panel = p

def update_val(key):
    st.session_state[key] = st.session_state["_" + key]

def update_dif_lengths():
    st.session_state.dif_lengths = st.session_state._dif_lengths
    if st.session_state.dif_lengths:
        st.session_state.larm_ext1 = st.session_state.larm
        st.session_state.larm_ext2 = st.session_state.larm
        st.session_state.subdiv_ext1 = st.session_state.subdiv
        st.session_state.subdiv_ext2 = st.session_state.subdiv

def update_ext_bays_active():
    active = st.session_state["_ext_bays_active"]
    st.session_state["ext_bays_active"] = active
    if active:
        st.session_state.ext_bl = True
        st.session_state.ext_br = True
        st.session_state.ext_tl = True
        st.session_state.ext_tr = True
        st.session_state._ext_bl = True
        st.session_state._ext_br = True
        st.session_state._ext_tl = True
        st.session_state._ext_tr = True
        
        if st.session_state.dif_lengths:
            st.session_state.ext_larm = st.session_state.larm_ext1
            st.session_state.ext_subdiv = st.session_state.subdiv_ext1
        else:
            st.session_state.ext_larm = st.session_state.larm
            st.session_state.ext_subdiv = st.session_state.subdiv

def update_subdiv():
    val = int(st.session_state['_subdiv'])
    if val % 2 != 0:
        val += 1
        st.session_state.subdiv_warning = True
    else:
        st.session_state.subdiv_warning = False
    st.session_state.subdiv = val
    st.session_state['_subdiv'] = val

def update_subdiv_ext1():
    val = int(st.session_state['_subdiv_ext1'])
    if val % 2 != 0:
        val += 1
    st.session_state.subdiv_ext1 = val
    st.session_state['_subdiv_ext1'] = val

def update_subdiv_ext2():
    val = int(st.session_state['_subdiv_ext2'])
    if val % 2 != 0:
        val += 1
    st.session_state.subdiv_ext2 = val
    st.session_state['_subdiv_ext2'] = val

def update_larm():
    st.session_state.larm = st.session_state._larm
    # Auto-actualizar
    length = st.session_state.larm
    needed = math.ceil(length / 1.525)
    if needed % 2 != 0:
        needed += 1
    st.session_state.subdiv = max(2, int(needed))
    st.session_state['_subdiv'] = st.session_state.subdiv
    st.session_state.subdiv_warning = False
    
    # Auto-actualizar Peralte de Armadura
    avg_harm = (length / 10.0 + length / 15.0) / 2.0
    st.session_state.harm = max(0.5, round(avg_harm, 1))
    st.session_state['_harm'] = st.session_state.harm

def update_larm_ext1():
    st.session_state.larm_ext1 = st.session_state._larm_ext1
    length = st.session_state.larm_ext1
    needed = math.ceil(length / 1.525)
    if needed % 2 != 0:
        needed += 1
    st.session_state.subdiv_ext1 = max(2, int(needed))
    st.session_state['_subdiv_ext1'] = st.session_state.subdiv_ext1

def update_larm_ext2():
    st.session_state.larm_ext2 = st.session_state._larm_ext2
    length = st.session_state.larm_ext2
    needed = math.ceil(length / 1.525)
    if needed % 2 != 0:
        needed += 1
    st.session_state.subdiv_ext2 = max(2, int(needed))
    st.session_state['_subdiv_ext2'] = st.session_state.subdiv_ext2
    
    st.session_state.harm = max(0.5, math.ceil((length / 12.5) * 10) / 10.0)
    st.session_state['_harm'] = st.session_state.harm

def update_larm_ext_bays():
    st.session_state.ext_larm = st.session_state._ext_larm
    length = st.session_state.ext_larm
    needed = math.ceil(length / 1.525)
    if needed % 2 != 0:
        needed += 1
    st.session_state.ext_subdiv = max(2, int(needed))
    st.session_state['_ext_subdiv'] = st.session_state.ext_subdiv

def update_subdiv_ext_bays():
    val = int(st.session_state['_ext_subdiv'])
    if val % 2 != 0:
        val += 1
    st.session_state.ext_subdiv = val
    st.session_state['_ext_subdiv'] = val

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
    actual_nspan = st.session_state.nspan
    shift_j = 0
    if st.session_state.get('ext_bays_active', False):
        if st.session_state.get('ext_bl', False) or st.session_state.get('ext_tl', False):
            actual_nspan += 1
            shift_j = 1
        if st.session_state.get('ext_br', False) or st.session_state.get('ext_tr', False):
            actual_nspan += 1
            
    mid_j = actual_nspan / 2.0
    
    if st.session_state.wall_type == "Tilt-Up":
        interior_j = list(range(1, st.session_state.nspan))
    else:
        interior_j = list(range(0, st.session_state.nspan + 1))
        
    interior_j.sort(key=lambda j: (abs(j - mid_j), j))
    interior_j = interior_j[:10]
    
    sec_trusses_j = [j for j in interior_j if st.session_state.get(f"sec_eje_{j}", False)]
    st.session_state.sec_truss_custom_ejes = sec_trusses_j

# Build Model
@st.cache_resource(max_entries=10)
def get_cached_model(
    larm, ljoist, nbay, nspan, harm, hlib, subdiv, roof_type, slope_pct, support_type, 
    c_muerta, c_viva, c_granizo, v_barlovento, v_sotavento, v_laterales, v_succion, 
    coef_sismico, ductilidad, cm_sismo, cv_sismo, add_wind_cols, max_wind_dist, 
    wall_type, sec_trusses_j, resorte_val, dif_lengths, larm_ext1, larm_ext2, 
    subdiv_ext1, subdiv_ext2, ext_bays_active, ext_bl, ext_br, ext_tl, ext_tr, 
    ext_height_mode, ext_larm, ext_subdiv, ext_depth, junta_constructiva_tipo, junta_max_dist_ft
):
    return StaadModel(
        larm, ljoist, nbay, nspan, harm, hlib, subdiv, roof_type, slope_pct,
        support_type, c_muerta, c_viva, c_granizo, v_barlovento, v_sotavento,
        v_laterales, v_succion, coef_sismico, ductilidad, cm_sismo, cv_sismo,
        add_wind_cols, max_wind_dist, wall_type, list(sec_trusses_j), resorte_val,
        dif_lengths=dif_lengths, larm_ext1=larm_ext1, larm_ext2=larm_ext2,
        subdiv_ext1=subdiv_ext1, subdiv_ext2=subdiv_ext2,
        ext_bays_active=ext_bays_active, ext_bl=ext_bl, ext_br=ext_br,
        ext_tl=ext_tl, ext_tr=ext_tr, ext_height_mode=ext_height_mode,
        ext_larm=ext_larm, ext_subdiv=ext_subdiv, ext_depth=ext_depth,
        junta_constructiva_tipo=junta_constructiva_tipo, junta_max_dist_ft=junta_max_dist_ft
    )

try:
    model = get_cached_model(
        st.session_state.larm, st.session_state.ljoist, st.session_state.nbay, st.session_state.nspan, 
        st.session_state.harm, st.session_state.hlib, st.session_state.subdiv, st.session_state.roof_type, 
        st.session_state.slope_pct, st.session_state.support_type, st.session_state.c_muerta, 
        st.session_state.c_viva, st.session_state.c_granizo, st.session_state.v_barlovento, 
        st.session_state.v_sotavento, st.session_state.v_laterales, st.session_state.v_succion, 
        st.session_state.coef_sismico, st.session_state.ductilidad, st.session_state.cm_sismo, 
        st.session_state.cv_sismo, st.session_state.add_wind_cols, st.session_state.max_wind_dist, 
        st.session_state.wall_type, tuple(sec_trusses_j), st.session_state.get('resorte_val', '1,000,000').replace(',', ''), 
        st.session_state.dif_lengths, st.session_state.larm_ext1, st.session_state.larm_ext2, 
        st.session_state.subdiv_ext1, st.session_state.subdiv_ext2, st.session_state.ext_bays_active, 
        st.session_state.ext_bl, st.session_state.ext_br, st.session_state.ext_tl, st.session_state.ext_tr, 
        st.session_state.ext_height_mode, st.session_state.ext_larm, st.session_state.ext_subdiv, 
        st.session_state.ext_depth, st.session_state.junta_constructiva_tipo, st.session_state.junta_max_dist_ft
    )
except Exception as e:
    st.error(f"Error generando la geometría: {e}")
    st.stop()

# Asignar atributos normativos y de método de diseño al modelo activo
model.reglamento_cargas = st.session_state.get("reglamento_cargas", "Chihuahua / IBC (Actual)")
model.metodo_diseno = "LRFD" if "LRFD" in st.session_state.get("metodo_diseno", "ASD").upper() else "ASD"
model.grupo_importancia = "A" if "GRUPO A" in st.session_state.get("grupo_importancia", "Grupo B").upper() else "B"
model.sismo_bidireccional = bool(st.session_state.get("sismo_bidireccional", False))


def render_siblings_top(group, current):
    for name in group:
        if name == current: break
        c1, c2, c3 = st.columns([1, 6, 1])
        is_dis = False
        if name == "Diseño" and not st.session_state.get("file_generated", False):
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
            if name == "Diseño" and not st.session_state.get("file_generated", False):
                is_dis = True
            with c2:
                if name in ["Diseño", "Catálogo"]:
                    st.markdown("<div class='grey-btn-marker'></div>", unsafe_allow_html=True)
                st.button(name, type="primary", use_container_width=True, on_click=go_panel, args=(name,), key=f"nav_bot_{name}", disabled=is_dis)
        if name == current: found = True

nav_group1 = ["Geometría", "Cargas", "Prediseño", "Cimentación"]
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
        st.button("Geometría", type="primary", use_container_width=True, on_click=go_panel, args=("Geometría",))
        st.button("Cargas", type="primary", use_container_width=True, on_click=go_panel, args=("Cargas",))
        st.button("Prediseño", type="primary", use_container_width=True, on_click=go_panel, args=("Prediseño",))
        st.button("Cimentación", type="primary", use_container_width=True, on_click=go_panel, args=("Cimentación",))
        st.divider()
        is_disabled = not st.session_state.get("file_generated", False)
        st.markdown("<div class='grey-btn-marker'></div>", unsafe_allow_html=True)
        st.button("Diseño", type="primary", use_container_width=True, on_click=go_panel, args=("Diseño",), disabled=is_disabled)
        # st.button("Catálogo", type="primary", use_container_width=True, on_click=go_panel, args=("Catálogo",))
        
        st.markdown(
            "<div style='text-align: center; color: #888; font-size: 11px; margin-top: 24vh; padding-top: 15px; border-top: 1px solid #ddd;'>"
            "&reg; 2026 Tensor Systems<br>Todos los derechos reservados.<br>v1.0.0 | <a href='mailto:admintensorsystems@gmail.com' style='color: inherit; text-decoration: none;'>Contáctanos</a>"
            "</div>",
            unsafe_allow_html=True
        )
    elif panel == "Geometría":
        c1, c2 = st.columns([5, 3])
        with c1:
            st.button("⬅ Volver", type="secondary", use_container_width=True, on_click=go_panel, args=("Main",))
        with c2:
            try:
                st.image(icono_small_path, use_container_width=True)
            except:
                pass
        render_siblings_top(nav_group1, "Geometría")
        st.header("Geometría")
        
        wt_idx = 0 if st.session_state.get("wall_type", "Metálico") == "Metálico" else 1
        st.radio("Tipo de Muros", ["Metálico", "Tilt-Up"], index=wt_idx, key="_wall_type", on_change=update_val, args=("wall_type",), horizontal=True)
        
        with st.expander("Dimensiones Generales", expanded=False):
            st.number_input("Longitud de Armaduras (m) (Principal)", min_value=1.0, step=3.048, format="%.2f", value=st.session_state.larm, key="_larm", on_change=update_larm)
            
            st.number_input("Longitud de Joists (m)", min_value=1.0, step=3.048, format="%.2f", value=st.session_state.ljoist, key="_ljoist", on_change=update_val, args=("ljoist",))
            
            st.number_input("Número de Bahías (Profundidad)", min_value=1, step=1, value=st.session_state.nbay, key="_nbay", on_change=update_val, args=("nbay",))
            st.number_input("Número de Entre-ejes (Ancho)", min_value=1, step=1, value=st.session_state.nspan, key="_nspan", on_change=update_val, args=("nspan",))
            
            st.number_input("Peralte Armadura (m)", min_value=0.5, step=0.1, value=st.session_state.harm, key="_harm", on_change=update_val, args=("harm",))
            
            # Relaciones L/10 y L/15
            l_10 = st.session_state.larm / 10.0
            l_15 = st.session_state.larm / 15.0
            st.markdown(f"<div style='font-size: 11px; color: #64748b; margin-top: -6px; margin-bottom: 8px; line-height: 1.4;'>L/10 = {l_10:.2f} m.<br>L/15 = {l_15:.2f} m.</div>", unsafe_allow_html=True)
            
            st.number_input("Altura Libre (m)", min_value=1.0, step=0.1, value=st.session_state.hlib, key="_hlib", on_change=update_val, args=("hlib",))
            st.number_input("Subdivisiones (Debe ser par)", min_value=2, step=2, value=st.session_state.subdiv, key="_subdiv", on_change=update_subdiv)
            if st.session_state.get("subdiv_warning", False):
                st.markdown("<div style='font-size: 11px; color: #e11d48; margin-top: -6px; margin-bottom: 8px;'>Debe ser número par. Se ajustó automáticamente.</div>", unsafe_allow_html=True)
            
            # Relación de Separación (Sep)
            sep_val = st.session_state.larm / st.session_state.subdiv
            st.markdown(f"<div style='font-size: 11px; color: #64748b; margin-top: -6px; margin-bottom: 8px;'>Sep = {sep_val:.2f} m.</div>", unsafe_allow_html=True)


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
                mid_j = model.nSpan / 2.0
                shift_eje = 0
                if st.session_state.get('ext_bays_active', False) and (st.session_state.get('ext_bl', False) or st.session_state.get('ext_tl', False)):
                    shift_eje = 1
                    
                if st.session_state.wall_type == "Tilt-Up":
                    interior_j = list(range(1, st.session_state.nspan))
                else:
                    interior_j = list(range(0, st.session_state.nspan + 1))
                interior_j.sort(key=lambda j: (abs(j - mid_j), j))
                interior_j = interior_j[:10] # Limitar a 10 ejes máximo
                
                selected_ejes = st.session_state.get('sec_truss_custom_ejes', [])
                for j in interior_j:
                    st.checkbox(f"Eje {j + 1 + shift_eje} (X = {model.get_x(j) / 100.0:.2f} m)", value=(j in selected_ejes), key=f"sec_eje_{j}")

        with st.expander("Juntas Constructivas", expanded=False):
            junta_opts = ["Ninguna", "Marco doble", "En Cubierta"]
            curr_junta = st.session_state.get("junta_constructiva_tipo", "Ninguna")
            junta_idx = junta_opts.index(curr_junta) if curr_junta in junta_opts else 0
            st.radio(
                "Tipo de Junta",
                junta_opts,
                index=junta_idx,
                key="_junta_constructiva_tipo",
                on_change=update_val,
                args=("junta_constructiva_tipo",),
                label_visibility="collapsed"
            )
            
            if st.session_state.junta_constructiva_tipo != "Ninguna":
                st.number_input(
                    "Separación máxima (ft)",
                    min_value=50,
                    step=50,
                    value=int(st.session_state.junta_max_dist_ft),
                    key="_junta_max_dist_ft",
                    on_change=update_val,
                    args=("junta_max_dist_ft",)
                )
                junta_m = st.session_state.junta_max_dist_ft * 0.3048
                st.markdown(f"<div style='font-size: 11px; color: #64748b; margin-top: -6px; margin-bottom: 8px;'>({junta_m:.2f} m)</div>", unsafe_allow_html=True)

        st.markdown("<hr style='border-top: 1px solid #cce5ff;'>", unsafe_allow_html=True)
        
        if st.session_state.wall_type != "Tilt-Up":
            with st.expander("Columnas de Viento", expanded=False):
                st.checkbox("Columnas de Viento", value=st.session_state.add_wind_cols, key="_add_wind_cols", on_change=update_val, args=("add_wind_cols",))
                if st.session_state.add_wind_cols:
                    st.number_input("Separación Máxima (m)", min_value=1.0, step=0.1, value=float(st.session_state.max_wind_dist), key="_max_wind_dist", on_change=update_val, args=("max_wind_dist",))
        else:
            st.session_state.add_wind_cols = False
            
        with st.expander("Armaduras diferentes (Extremos)", expanded=False):
            if st.session_state.nspan >= 2:
                st.checkbox("Diferentes longitudes (Extremos)", value=st.session_state.dif_lengths, key="_dif_lengths", on_change=update_dif_lengths)
                if st.session_state.dif_lengths:
                    with st.container():
                        st.markdown("<span id='extremos-border'></span><p class='widget-title' style='margin-top: -5px;'>Extremo 1 (X=0)</p>", unsafe_allow_html=True)
                        st.number_input("Longitud (m)", min_value=1.0, step=3.048, format="%.2f", value=st.session_state.larm_ext1, key="_larm_ext1", on_change=update_larm_ext1)
                        st.number_input("Subdivisiones", min_value=2, step=2, value=st.session_state.subdiv_ext1, key="_subdiv_ext1", on_change=update_subdiv_ext1)
                        sep_val1 = st.session_state.larm_ext1 / st.session_state.subdiv_ext1
                        st.markdown(f"<div style='font-size: 11px; color: #64748b; margin-top: -6px; margin-bottom: 8px;'>Sep = {sep_val1:.2f} m.</div>", unsafe_allow_html=True)
                        
                        if st.session_state.nspan > 2:
                            st.markdown("<p class='widget-title' style='margin-top: 10px;'>Extremo 2 (X=MAX)</p>", unsafe_allow_html=True)
                            st.number_input("Longitud (m)", min_value=1.0, step=3.048, format="%.2f", value=st.session_state.larm_ext2, key="_larm_ext2", on_change=update_larm_ext2)
                            st.number_input("Subdivisiones", min_value=2, step=2, value=st.session_state.subdiv_ext2, key="_subdiv_ext2", on_change=update_subdiv_ext2)
                            sep_val2 = st.session_state.larm_ext2 / st.session_state.subdiv_ext2
                            st.markdown(f"<div style='font-size: 11px; color: #64748b; margin-top: -6px; margin-bottom: 8px;'>Sep = {sep_val2:.2f} m.</div>", unsafe_allow_html=True)

        if st.session_state.wall_type == "Tilt-Up":
            with st.expander("Bahías de Extensión", expanded=False):
                st.checkbox("Incluir Bahías de Extensión", value=st.session_state.ext_bays_active, key="_ext_bays_active", on_change=update_ext_bays_active)
                if st.session_state.ext_bays_active:
                    st.radio("Profundidad (Entre-ejes Z)", [1, 2], index=1 if st.session_state.ext_depth == 2 else 0, key="_ext_depth", on_change=update_val, args=("ext_depth",), horizontal=True)
                    
                    st.markdown("<p class='widget-title' style='margin-top: 10px;'>Geometría de la Armadura</p>", unsafe_allow_html=True)
                    st.number_input("Longitud (m)", min_value=1.0, step=3.048, format="%.2f", value=st.session_state.ext_larm, key="_ext_larm", on_change=update_larm_ext_bays)
                    st.number_input("Subdivisiones", min_value=2, step=2, value=st.session_state.ext_subdiv, key="_ext_subdiv", on_change=update_subdiv_ext_bays)

                    sep_ext = st.session_state.ext_larm / st.session_state.ext_subdiv
                    st.markdown(f"<div style='font-size: 11px; color: #64748b; margin-top: -6px; margin-bottom: 8px;'>Sep = {sep_ext:.2f} m.</div>", unsafe_allow_html=True)
                    
                    st.radio("Altura Libre", ["Primer Entre-Eje completo", "Altura mínima en esquinas"], index=0 if st.session_state.ext_height_mode == "Primer Entre-Eje completo" else 1, key="_ext_height_mode", on_change=update_val, args=("ext_height_mode",))
                    st.markdown("<p class='widget-title' style='margin-top: 5px;'>Esquinas con Extensión:</p>", unsafe_allow_html=True)
                    col1, col2 = st.columns(2)
                    with col1:
                        st.checkbox("1", value=st.session_state.ext_bl, key="_ext_bl", on_change=update_val, args=("ext_bl",))
                        st.checkbox("2", value=st.session_state.ext_tl, key="_ext_tl", on_change=update_val, args=("ext_tl",))
                    with col2:
                        st.checkbox("3", value=st.session_state.ext_br, key="_ext_br", on_change=update_val, args=("ext_br",))
                        st.checkbox("4", value=st.session_state.ext_tr, key="_ext_tr", on_change=update_val, args=("ext_tr",))

        render_siblings_bottom(nav_group1, "Geometría")

    elif panel == "Cargas":
        c1, c2 = st.columns([5, 3])
        with c1:
            st.button("⬅ Volver", type="secondary", use_container_width=True, on_click=go_panel, args=("Main",))
        with c2:
            try:
                st.image(icono_small_path, use_container_width=True)
            except:
                pass
        render_siblings_top(nav_group1, "Cargas")
        st.header("Cargas")
        with st.expander("Normativa y Método de Diseño", expanded=True):
            from reglamentos import REGLAMENTOS_DISPONIBLES, METODOS_DISENO, GRUPOS_IMPORTANCIA

            def _on_change_reglamento():
                reg_val = st.session_state["_reglamento_cargas"]
                st.session_state["reglamento_cargas"] = reg_val
                if "NTC" in reg_val.upper() or "CFE" in reg_val.upper():
                    st.session_state["sismo_bidireccional"] = True
                    st.session_state["_sismo_bidireccional"] = True

            reg_curr = st.session_state.get("reglamento_cargas", REGLAMENTOS_DISPONIBLES[0])
            if reg_curr not in REGLAMENTOS_DISPONIBLES:
                for r in REGLAMENTOS_DISPONIBLES:
                    if r.split()[0] in reg_curr:
                        reg_curr = r
                        break
                else:
                    reg_curr = REGLAMENTOS_DISPONIBLES[0]
                st.session_state["reglamento_cargas"] = reg_curr

            reg_idx = REGLAMENTOS_DISPONIBLES.index(reg_curr)
            
            # Segmented Control / Toggle Buttons para Reglamentos
            try:
                st.segmented_control(
                    "Reglamento de Cargas",
                    options=REGLAMENTOS_DISPONIBLES,
                    default=reg_curr,
                    key="_reglamento_cargas",
                    on_change=_on_change_reglamento
                )
            except AttributeError:
                st.radio(
                    "Reglamento de Cargas",
                    options=REGLAMENTOS_DISPONIBLES,
                    index=reg_idx,
                    key="_reglamento_cargas",
                    on_change=_on_change_reglamento
                )

            met_curr = st.session_state.get("metodo_diseno", "ASD")
            met_curr = "LRFD" if "LRFD" in met_curr.upper() else "ASD"
            st.session_state["metodo_diseno"] = met_curr
            met_idx = METODOS_DISENO.index(met_curr) if met_curr in METODOS_DISENO else 0
            
            # Segmented Control / Toggle Buttons para ASD y LRFD
            try:
                st.segmented_control(
                    "Método de Diseño en Acero",
                    options=METODOS_DISENO,
                    default=met_curr,
                    key="_metodo_diseno",
                    on_change=update_val,
                    args=("metodo_diseno",)
                )
            except AttributeError:
                st.radio(
                    "Método de Diseño en Acero",
                    options=METODOS_DISENO,
                    index=met_idx,
                    key="_metodo_diseno",
                    on_change=update_val,
                    args=("metodo_diseno",),
                    horizontal=True
                )

            reg_up = st.session_state.get("reglamento_cargas", "").upper()
            if "NTC" in reg_up or "CFE" in reg_up:
                grp_curr = st.session_state.get("grupo_importancia", "Grupo B")
                grp_curr = "Grupo A" if "GRUPO A" in grp_curr.upper() else "Grupo B"
                grp_idx = GRUPOS_IMPORTANCIA.index(grp_curr) if grp_curr in GRUPOS_IMPORTANCIA else 0
                try:
                    st.segmented_control(
                        "Grupo de Importancia",
                        options=GRUPOS_IMPORTANCIA,
                        default=grp_curr,
                        key="_grupo_importancia",
                        on_change=update_val,
                        args=("grupo_importancia",)
                    )
                except AttributeError:
                    st.radio(
                        "Grupo de Importancia",
                        options=GRUPOS_IMPORTANCIA,
                        index=grp_idx,
                        key="_grupo_importancia",
                        on_change=update_val,
                        args=("grupo_importancia",),
                        horizontal=True
                    )

            st.checkbox(
                "Incluir Sismo Bidireccional (100% + 30%)",
                value=st.session_state.get("sismo_bidireccional", False),
                key="_sismo_bidireccional",
                on_change=update_val,
                args=("sismo_bidireccional",)
            )

        with st.expander("Gravitacionales", expanded=False):
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
        c1, c2 = st.columns([5, 3])
        with c1:
            st.button("⬅ Volver", type="secondary", use_container_width=True, on_click=go_panel, args=("Main",))
        with c2:
            try:
                st.image(icono_small_path, use_container_width=True)
            except:
                pass
        render_siblings_top(nav_group1, "Prediseño")
        st.header("Prediseño")
        _met_badge = "LRFD (AISC 360)" if getattr(model, "metodo_diseno", "ASD") == "LRFD" else "ASD (AISC)"
        _reg_badge = getattr(model, "reglamento_cargas", "Chihuahua / IBC (Actual)")
        st.markdown(
            f"<div style='font-size: 11.5px; color: #334155; background: #f8fafc; padding: 6px 10px; border-radius: 6px; border-left: 3px solid #005cb2; margin-bottom: 10px;'>"
            f"<b>Norma:</b> {_reg_badge}<br><b>Método Activo:</b> {_met_badge}</div>",
            unsafe_allow_html=True
        )
        
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

    elif panel == "Cimentación":
        c1, c2 = st.columns([5, 3])
        with c1:
            st.button("⬅ Volver", type="secondary", use_container_width=True, on_click=go_panel, args=("Main",))
        with c2:
            try:
                st.image(icono_small_path, use_container_width=True)
            except:
                pass
        render_siblings_top(nav_group1, "Cimentación")
        st.header("Cimentación")
        st.markdown("<div style='font-size: 12px; color: #64748b; margin-top:-8px; margin-bottom: 12px;'>Prediseño de Cimentación</div>", unsafe_allow_html=True)

        import cimentacion_cad

        def _on_change_geotech():
            st.session_state["q_adm_zapata"] = st.session_state["_q_adm_zapata"]
            st.session_state["df_zapata"] = st.session_state["_df_zapata"]
            st.session_state["gamma_s_zapata"] = st.session_state["_gamma_s_zapata"]
            st.session_state["recalc_zapatas_flag"] = True

        with st.expander("Parámetros Geotécnicos de Sitio", expanded=True):
            q_adm = st.number_input(
                "Capacidad Admisible q_adm (Ton/m²)",
                min_value=5.0,
                max_value=60.0,
                value=float(st.session_state.get("q_adm_zapata", 15.0)),
                step=1.0,
                key="_q_adm_zapata",
                on_change=_on_change_geotech
            )
            df_val = st.number_input(
                "Profundidad de Desplante Df (m)",
                min_value=0.80,
                max_value=5.00,
                value=float(st.session_state.get("df_zapata", 1.50)),
                step=0.10,
                key="_df_zapata",
                on_change=_on_change_geotech
            )
            gamma_s = st.number_input(
                "Peso Volumétrico Suelo (Ton/m³)",
                min_value=1.0,
                max_value=2.5,
                value=float(st.session_state.get("gamma_s_zapata", 1.80)),
                step=0.10,
                key="_gamma_s_zapata",
                on_change=_on_change_geotech
            )

        # Cálculo de Reacciones y Dimensiones
        reacs_cim, modo_reac = cimentacion_cad.obtener_reacciones_envolventes(model)
        
        # Perfiles asignados en prediseño
        perfiles_asignados = {}
        import prediseno
        for g in reacs_cim.keys():
            ui_p = st.session_state.get(f"sel_{g}")
            if not ui_p:
                top_p = prediseno.predisenar_grupo(g, model, False)
                if top_p:
                    ui_p = top_p[0]['perfil']['nombre']
            perfiles_asignados[g] = ui_p if ui_p else "Auto"

        zaps_calculadas = cimentacion_cad.predimensionar_zapatas(
            reacciones=reacs_cim,
            q_adm_ton_m2=q_adm,
            gamma_s_ton_m3=gamma_s,
            df_m=df_val,
            perfiles_por_grupo=perfiles_asignados
        )

        import pandas as pd
        if "tabla_zapatas_df" not in st.session_state or st.session_state.get("recalc_zapatas_flag", False):
            df_raw = pd.DataFrame(zaps_calculadas)
            if "Tipo Zapata" in df_raw.columns:
                df_raw["Z"] = df_raw["Tipo Zapata"]
            st.session_state.tabla_zapatas_df = df_raw
            st.session_state.recalc_zapatas_flag = False

        st.markdown("<div style='font-size: 13px; font-weight: 600; color: #1e293b; margin-top: 10px; margin-bottom: 5px;'>Dimensiones de Zapatas y Dados:</div>", unsafe_allow_html=True)
        
        # Mostrar únicamente la columna Z y dimensiones, omitiendo columnas de superestructura
        if "Z" not in st.session_state.tabla_zapatas_df.columns and "Tipo Zapata" in st.session_state.tabla_zapatas_df.columns:
            st.session_state.tabla_zapatas_df["Z"] = st.session_state.tabla_zapatas_df["Tipo Zapata"]

        cols_display = [c for c in ["Z", "B_ancho (m)", "L_largo (m)", "Hz_espesor (m)", "Dado_x (m)", "Dado_z (m)"] if c in st.session_state.tabla_zapatas_df.columns]
        
        edited_df = st.data_editor(
            st.session_state.tabla_zapatas_df[cols_display],
            num_rows="fixed",
            use_container_width=True,
            key="editor_zapatas_sidebar",
            column_config={
                "Z": st.column_config.TextColumn("Z", disabled=True),
                "B_ancho (m)": st.column_config.NumberColumn("B (m)", format="%.2f"),
                "L_largo (m)": st.column_config.NumberColumn("L (m)", format="%.2f"),
                "Hz_espesor (m)": st.column_config.NumberColumn("Hz (m)", format="%.2f"),
                "Dado_x (m)": st.column_config.NumberColumn("Dado X", format="%.2f"),
                "Dado_z (m)": st.column_config.NumberColumn("Dado Z", format="%.2f"),
            }
        )
        for col in edited_df.columns:
            st.session_state.tabla_zapatas_df[col] = edited_df[col]
        if "Z" in st.session_state.tabla_zapatas_df.columns:
            st.session_state.tabla_zapatas_df["Tipo Zapata"] = st.session_state.tabla_zapatas_df["Z"]

        render_siblings_bottom(nav_group1, "Cimentación")

    elif panel == "Diseño":
        c1, c2 = st.columns([5, 3])
        with c1:
            st.button("⬅ Menú Principal", type="secondary", use_container_width=True, on_click=go_panel, args=("Main",))
        with c2:
            try:
                st.image(icono_small_path, use_container_width=True)
            except:
                pass
        
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
        c1, c2 = st.columns([5, 3])
        with c1:
            st.button("⬅ Menú Principal", type="secondary", use_container_width=True, on_click=go_panel, args=("Main",))
        with c2:
            try:
                st.image(icono_small_path, use_container_width=True)
            except:
                pass
        
        st.markdown("<h3 style='margin-top: 10px; margin-bottom: 30px;'>Catálogo de Conceptos</h3>", unsafe_allow_html=True)
        
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
        
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        st.markdown("<div class='grey-btn-marker'></div>", unsafe_allow_html=True)
        is_dis = not st.session_state.get("file_generated", False)
        st.button("Diseño", type="primary", use_container_width=True, on_click=go_panel, args=("Diseño",), key="cat_sidebar_diseno", disabled=is_dis)

if st.session_state.current_panel == "Diseño":
    if st.session_state.pop("minimize_next", False):
        import streamlit.components.v1 as components
        components.html("""
            <script>
                if (window.parent && window.parent.pywebview && window.parent.pywebview.api) {
                    window.parent.pywebview.api.minimize();
                }
            </script>
        """, height=0)
    
    col_izq, col_der = st.columns([2, 1])
    
    with col_izq:
        import sys, os
        if os.path.join(os.path.dirname(__file__), 'staad_link') not in sys.path:
            sys.path.append(os.path.join(os.path.dirname(__file__), 'staad_link'))
        from link import check_staad_status, run_analysis
        
        staad_info = check_staad_status()
        
        expected_filename = st.session_state.get("active_staad_file", "Modelo.std")
        actual_filename = staad_info.get("filename") or ""
        
        is_connected_to_target = False
        if staad_info["status"] != "disconnected" and actual_filename.lower() == expected_filename.lower():
            is_connected_to_target = True
            
        is_disabled = not is_connected_to_target
        
        if not is_connected_to_target:
            from streamlit_autorefresh import st_autorefresh
            st_autorefresh(interval=2000, key="staad_poll")
            st.info(f"⏳ Esperando conexión con **{expected_filename}** en STAAD.Pro...")
            if actual_filename:
                st.warning(f"STAAD.Pro está abierto con otro archivo: {actual_filename}")
        else:
            st.success(f"✅ Conectado a STAAD.Pro ({expected_filename})")
            
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
                        with open(full_path, "w", encoding="windows-1252", errors="replace") as f:
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
                                    with open(full_path, "w", encoding="windows-1252", errors="replace") as f:
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

        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
        # =====================================================================
        # MÓDULO ADITIVO: PREDISEÑO DE CIMENTACIÓN Y EXPORTACIÓN CAD (.DXF)
        # =====================================================================


    with col_der:
        st.markdown("<b style='font-size: 14px;'>Visualizador 3D</b>", unsafe_allow_html=True)
        
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
        cam_zoom = 3.6 if is_mobile_client else 1.8
        fig.update_layout(
            scene_camera=dict(eye=dict(x=cam_zoom, y=cam_zoom, z=cam_zoom)),
            margin=dict(l=0, r=0, b=0, t=0),
            scene=dict(aspectmode='data')
        )
        st.plotly_chart(fig, use_container_width=True, config={'displaylogo': False})

elif st.session_state.current_panel == "Catálogo":
    from Catalogo import render_catalogo
    render_catalogo(model)

else:
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if st.session_state.current_panel == "Cargas":
            st.markdown("<div style='margin-top: -15px;'></div>", unsafe_allow_html=True)
            from reglamentos import construir_lista_combinaciones
            _met_sh = "LRFD" if "LRFD" in st.session_state.get("metodo_diseno", "ASD").upper() else "ASD"
            _grp_sh = "A" if "GRUPO A" in st.session_state.get("grupo_importancia", "Grupo B").upper() else "B"
            _lista_c = construir_lista_combinaciones(
                st.session_state.get("reglamento_cargas", "Chihuahua / IBC"),
                _met_sh,
                _grp_sh,
                st.session_state.get("sismo_bidireccional", False)
            )

            cargas_primarias = [
                (1, "CM", "Carga Muerta"),
                (2, "CMP", "Carga Muerta Disminuida (0.6 CM)"),
                (3, "CV", "Carga Viva de Piso"),
                (4, "CVR", "Carga Viva Reducida"),
                (5, "CVT", "Carga Viva de Techo Máxima"),
                (6, "CVRT", "Carga Viva Instantánea de Techo (0.7 CVT)"),
                (7, "VX+", "Viento en X+"),
                (8, "VX-", "Viento en X-"),
                (9, "VZ+", "Viento en Z+"),
                (10, "VZ-", "Viento en Z-"),
                (11, "SX+", "Sismo en X+"),
                (12, "SX-", "Sismo en X-"),
                (13, "SZ+", "Sismo en Z+"),
                (14, "SZ-", "Sismo en Z-"),
                (15, "N", "Carga de Granizo / Nieve"),
                (16, "MASA", "Masa de Sismo (1.0 CM + 1.0 CVR + 1.0 CVRT)")
            ]

            col_cargas_p, col_combs_p = st.columns([1, 1.45])

            with col_cargas_p:
                st.markdown(
                    "<div style='font-family: Aptos Display, Segoe UI, sans-serif; font-size: 16px; font-weight: 700; color: #0f172a; margin-bottom: 10px;'>"
                    "📋 Cargas Primarias (STAAD.Pro)"
                    "</div>",
                    unsafe_allow_html=True
                )
                html_cargas = "<div style='height: 72vh; max-height: 760px; overflow-y: auto; background: #ffffff; border: 1px solid #cbd5e1; border-radius: 10px; padding: 12px 16px; font-size: 13px; line-height: 2.1; box-shadow: 0 1px 3px rgba(0,0,0,0.05);'>"
                for cid, ccode, cdesc in cargas_primarias:
                    html_cargas += f"<div style='border-bottom: 1px solid #f1f5f9; padding: 4px 0;'><span style='color: #005cb2; font-weight: 700; font-family: Consolas, monospace;'>LOAD {cid:02d}:</span> <b style='color: #1e293b; margin-left: 4px;'>{ccode}</b> <span style='color: #64748b; font-size: 12px;'>— {cdesc}</span></div>"
                html_cargas += "</div>"
                st.markdown(html_cargas, unsafe_allow_html=True)

            with col_combs_p:
                st.markdown(
                    f"<div style='font-family: Aptos Display, Segoe UI, sans-serif; font-size: 16px; font-weight: 700; color: #0f172a; margin-bottom: 10px;'>"
                    f"⚙️ Combinaciones de Diseño ({len(_lista_c)} Activas)"
                    f"</div>",
                    unsafe_allow_html=True
                )
                html_combs = "<div style='height: 72vh; max-height: 760px; overflow-y: auto; background: #ffffff; border: 1px solid #cbd5e1; border-radius: 10px; padding: 12px 16px; font-size: 13px; line-height: 2.1; box-shadow: 0 1px 3px rgba(0,0,0,0.05);'>"
                start_id = 17
                for idx, (cat, title, pairs) in enumerate(_lista_c):
                    cid = start_id + idx
                    badge_color = "#0369a1" if cat == "GRAVITACIONALES" else ("#b45309" if cat == "VIENTO" else "#6d28d9")
                    badge_bg = "#f0f9ff" if cat == "GRAVITACIONALES" else ("#fffbeb" if cat == "VIENTO" else "#f5f3ff")
                    html_combs += (
                        f"<div style='border-bottom: 1px solid #f1f5f9; padding: 4px 0; display: flex; justify-content: space-between; align-items: center;'>"
                        f"<div><span style='color: #005cb2; font-weight: 700; font-family: Consolas, monospace;'>COMB {cid:02d}:</span> "
                        f"<b style='color: #0f172a; margin-left: 4px;'>{title}</b></div>"
                        f"<span style='font-size: 11px; font-weight: 600; color: {badge_color}; background: {badge_bg}; padding: 2px 8px; border-radius: 4px; border: 1px solid #e2e8f0; white-space: nowrap;'>{cat}</span>"
                        f"</div>"
                    )
                html_combs += "</div>"
                st.markdown(html_combs, unsafe_allow_html=True)
        elif st.session_state.current_panel == "Cimentación":
            st.markdown("<div style='margin-top: -15px;'></div>", unsafe_allow_html=True)
            import cimentacion_cad

            col_toggle, col_empty = st.columns([1.6, 2.4])
            with col_toggle:
                try:
                    tipo_vista_cim = st.segmented_control(
                        "Vista",
                        options=["Cimentación Preliminar", "Corte por Marco"],
                        default="Cimentación Preliminar",
                        key="sel_vista_cim_2d",
                        label_visibility="collapsed"
                    )
                except AttributeError:
                    tipo_vista_cim = st.radio(
                        "Vista",
                        options=["Cimentación Preliminar", "Corte por Marco"],
                        index=0,
                        key="sel_vista_cim_2d",
                        horizontal=True,
                        label_visibility="collapsed"
                    )

            if tipo_vista_cim is None:
                tipo_vista_cim = "Cimentación Preliminar"

            if "tabla_zapatas_df" in st.session_state:
                tabla_zaps_act = st.session_state.tabla_zapatas_df.to_dict(orient="records")
            else:
                reacs_tmp, _ = cimentacion_cad.obtener_reacciones_envolventes(model)
                tabla_zaps_act = cimentacion_cad.predimensionar_zapatas(
                    reacs_tmp,
                    q_adm_ton_m2=float(st.session_state.get("q_adm_zapata", 15.0)),
                    df_m=float(st.session_state.get("df_zapata", 1.50))
                )

            fig_cim = cimentacion_cad.generar_figura_previsualizacion_cimentacion(
                model=model,
                tabla_zapatas=tabla_zaps_act,
                view_type=tipo_vista_cim,
                df_m=float(st.session_state.get("df_zapata", 1.50))
            )
            st.plotly_chart(fig_cim, use_container_width=True, config={'displaylogo': False})
        else:
            st.markdown("<div style='margin-top: -15px;'></div>", unsafe_allow_html=True)
            st.markdown("<div style='font-size: 20px; font-weight: 600; margin-bottom: 0.5rem;'>Visualizador 3D</div>", unsafe_allow_html=True)
            show_sup = (st.session_state.current_panel == "Geometría")
            highlight_col = st.session_state.get("highlight_grupo_col", "C-1") if st.session_state.current_panel == "Prediseño" else "Ninguno"
            highlight_ids = None
            if highlight_col != "Ninguno" and highlight_col in prediseno.clasificar_columnas(model):
                highlight_ids = prediseno.clasificar_columnas(model).get(highlight_col, [])
            fig = plot_model(model, show_supports=show_sup, highlight_ids=highlight_ids)
            
            if is_mobile_client:
                fig.update_layout(
                    scene_camera=dict(eye=dict(x=-5.0, y=-5.0, z=4.0))
                )
                
            st.plotly_chart(fig, use_container_width=True, config={
                'displaylogo': False,
                'modeBarButtonsToRemove': ['resetCameraDefault3d', 'resetCameraLastSave3d', 'hoverClosest3d', 'tableRotation']
            })

    with col2:
        with st.container():
            st.markdown("<div class='ios-glass-marker'></div>", unsafe_allow_html=True)
        
            st.markdown("<div style=\"font-family: 'Aptos Display', 'Segoe UI', sans-serif; font-size: 1.1rem; font-weight: 700; color: #0f172a; margin-bottom: 0px; margin-top: -5px;\">Nombre Proyecto:</div>", unsafe_allow_html=True)
            
            # Contenedor para simular el sufijo
            col_in1, col_in2 = st.columns([3.2, 1.2])
            with col_in1:
                file_name_export = st.text_input("proj_name", value="Modelo", label_visibility="collapsed")
            with col_in2:
                _suf = ".dwg" if st.session_state.current_panel == "Cimentación" else ".std"
                st.markdown(f"<div style='color: #aaa; margin-top: 8px; font-weight: 500; font-family: \"Aptos Display\", sans-serif; white-space: nowrap;'>{_suf}</div>", unsafe_allow_html=True)
                
            # Detectar si estamos en entorno web (stlite/Pyodide) o escritorio
            _is_web = False
            try:
                import sys
                if 'pyodide' in sys.modules or 'micropip' in sys.modules:
                    _is_web = True
            except:
                pass
        
            if not _is_web:
                # ─── Modo Escritorio: selector de carpeta + guardar al disco ───
                st.markdown("<div style=\"font-family: 'Aptos Display', 'Segoe UI', sans-serif; font-size: 1rem; font-weight: 700; color: #1e293b; margin-bottom: 5px;\">Ubicación:</div>", unsafe_allow_html=True)
            
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
            else:
                # ─── Modo Web: UI completa en JS (dirHandle vive en JS) ───
                pass  # El bloque web se renderiza abajo con components.html

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

            if _is_web:
                # ─── Modo Web: Ubicación + Guardar completo en un solo componente JS ───
                clean_name = "".join(c for c in file_name_export if c.isalnum() or c in " ._-").strip()
                if not clean_name.endswith(".std"):
                    clean_name += ".std"

                import base64 as _b64
                staad_b64 = _b64.b64encode(staad_text.encode("windows-1252", errors="replace")).decode("ascii")

                web_ui = f"""
                <style>
                  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
                  body {{ font-family: 'Aptos Display', 'Segoe UI', sans-serif;
                         background: transparent; }}
                  .label {{ font-family: 'Aptos Display', 'Segoe UI', sans-serif; font-size: 1.1rem; font-weight: 700; color: #0f172a; margin-bottom: 10px; margin-top: -5px; display: block; }}
                  .row {{ display: flex; position: relative; margin-bottom: 10px; width: 78%; align-items: center; }}
                  .path-input {{
                    width: 100%; padding: 8px 32px 8px 12px; font-size: 0.85rem; color: #374151;
                    border: 1px solid rgba(49, 51, 63, 0.2); border-radius: 8px;
                    background: #f9fafb; outline: none; height: 38px;
                    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
                  }}
                  .btn-container {{
                    position: absolute; right: 4px; height: 28px; width: 28px; padding: 0;
                  }}
                  .folder-btn {{
                    width: 100%; height: 100%; border: none; border-radius: 4px; background: transparent; cursor: pointer;
                    font-size: 1rem; display: flex; align-items: center;
                    justify-content: center; transition: background 0.15s;
                    color: #31333f;
                  }}
                  .folder-btn:hover {{ background: rgba(0,0,0,0.05); }}
                  .save-btn {{
                    padding: 0.5rem 1rem; background: #ba281b; color: white;
                    border: none; border-radius: 4px; font-size: 14px; font-weight: 600;
                    cursor: pointer; box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.1);
                    transition: all 0.2s ease-in-out; font-family: 'Aptos Display', 'Segoe UI', sans-serif;
                  }}
                  .save-btn:hover {{ background: #9d2116; }}
                  .save-btn:disabled {{ opacity: 0.8; cursor: not-allowed; }}
                  .status {{ font-size: 0.85rem; display: none; }}
                  .status.ok {{ color: #16a34a; display: block; }}
                  .status.err {{ color: #dc2626; display: block; }}
                  .action-row {{ display: flex; align-items: center; gap: 12px; margin-top: 15px; }}
                </style>

                <span class="label">Ubicación:</span>
                <div class="row">
                  <input id="pathDisplay" class="path-input" readonly value="Selecciona una carpeta..." />
                  <div class="btn-container">
                    <button class="folder-btn" id="folderBtn" title="Examinar...">📁</button>
                  </div>
                </div>
                <div class="action-row">
                  <button class="save-btn" id="saveBtn" disabled>Guardar Archivo .std</button>
                  <div id="status" class="status"></div>
                </div>

                <script>
                  const FILE_NAME = "{clean_name}";
                  const FILE_B64  = "{staad_b64}";

                  let dirHandle = null;

                  function b64ToBytes(b64) {{
                    const bin = atob(b64);
                    const buf = new Uint8Array(bin.length);
                    for (let i = 0; i < bin.length; i++) buf[i] = bin.charCodeAt(i);
                    return buf;
                  }}

                  // ── Botón carpeta ──
                  document.getElementById("folderBtn").addEventListener("click", async () => {{
                    try {{
                      dirHandle = await window.showDirectoryPicker({{ mode: "readwrite" }});
                      document.getElementById("pathDisplay").value = dirHandle.name;
                      document.getElementById("saveBtn").disabled = false;
                      setStatus("", "");
                    }} catch (e) {{
                      if (e.name !== "AbortError") setStatus("Error al seleccionar carpeta.", "err");
                    }}
                  }});

                  // ── Botón guardar ──
                  document.getElementById("saveBtn").addEventListener("click", async () => {{
                    if (!dirHandle) {{ setStatus("Primero selecciona una carpeta.", "err"); return; }}
                    try {{
                      const fileHandle = await dirHandle.getFileHandle(FILE_NAME, {{ create: true }});
                      const writable   = await fileHandle.createWritable();
                      await writable.write(b64ToBytes(FILE_B64));
                      await writable.close();
                      setStatus("✓ Guardado en: " + dirHandle.name + "\\\\" + FILE_NAME, "ok");
                    }} catch (e) {{
                      setStatus("Error al guardar: " + e.message, "err");
                    }}
                  }});

                  function setStatus(msg, cls) {{
                    const el = document.getElementById("status");
                    el.textContent = msg;
                    el.className = "status " + cls;
                  }}
                </script>
                """
                components.html(web_ui, height=135)
            else:
                # ─── Modo Escritorio ───
                if st.session_state.current_panel == "Cimentación":
                    # Botón Exportar DWG / DXF (Azul) exclusivo de la pestaña Cimentación
                    st.markdown("<div class='blue-btn-marker'></div>", unsafe_allow_html=True)
                    if st.button("Exportar DWG", key="btn_export_dwg_cimentacion", use_container_width=True):
                        try:
                            clean_proj = "".join(c for c in file_name_export if c.isalnum() or c in " ._-").strip()
                            if clean_proj.lower().endswith(".std"):
                                clean_proj = clean_proj[:-4]
                            if not clean_proj:
                                clean_proj = "Modelo"

                            cad_filename = f"[{clean_proj}] Cimentación Preliminar.dxf"
                            export_dir = st.session_state.get("export_path", r"C:\Users\josee\OneDrive\Escritorio\MODELOS GENERADOS")
                            os.makedirs(export_dir, exist_ok=True)
                            full_cad_path = os.path.join(export_dir, cad_filename)

                            import cimentacion_cad
                            if "tabla_zapatas_df" in st.session_state:
                                tabla_zaps_exp = st.session_state.tabla_zapatas_df.to_dict(orient="records")
                            else:
                                reacs_tmp, _ = cimentacion_cad.obtener_reacciones_envolventes(model)
                                tabla_zaps_exp = cimentacion_cad.predimensionar_zapatas(
                                    reacs_tmp,
                                    q_adm_ton_m2=float(st.session_state.get("q_adm_zapata", 15.0)),
                                    df_m=float(st.session_state.get("df_zapata", 1.50))
                                )

                            gen_dxf = cimentacion_cad.GeneradorPlanoEstructuralDXF(
                                model=model,
                                tabla_zapatas=tabla_zaps_exp,
                                q_adm=float(st.session_state.get("q_adm_zapata", 15.0)),
                                df=float(st.session_state.get("df_zapata", 1.50))
                            )
                            saved_path = gen_dxf.exportar(full_cad_path)
                            saved_filename = os.path.basename(saved_path)

                            if saved_filename.lower() != cad_filename.lower():
                                st.warning(f"⚠️ El archivo anterior estaba abierto en AutoCAD. Se guardó una nueva versión:\n**{saved_filename}**")
                            else:
                                st.success(f"✅ Archivo exportado exitosamente:\n**{saved_filename}**")

                            # Abrir inmediatamente en AutoCAD
                            opened = cimentacion_cad.abrir_en_autocad(saved_path)
                            if opened:
                                st.info(f"Abriendo {saved_filename} en AutoCAD...")
                        except Exception as e_cad_save:
                            st.error(f"Error generando plano DWG/DXF: {e_cad_save}")
                else:
                    if st.button("Guardar Archivo .std", type="primary"):
                        # Limpiar el nombre del archivo para evitar caracteres inválidos
                        clean_name = "".join(c for c in file_name_export if c.isalnum() or c in " ._-").strip()
                        if not clean_name.endswith(".std"):
                            clean_name += ".std"
                        
                        full_path = os.path.join(st.session_state.export_path, clean_name)
                        try:
                            with open(full_path, "w", encoding="windows-1252", errors="replace") as f:
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
                            st.session_state.minimize_next = True
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"Error al guardar o abrir en '{full_path}': {e}")


        with st.container():
            st.markdown("<div class='ios-glass-marker'></div>", unsafe_allow_html=True)
            num_wind_cols = len(model.groups.get('_COLVIENTO', []))
            num_purlins = (st.session_state.nspan + 1) * st.session_state.nbay + st.session_state.nspan * (st.session_state.subdiv - 1) * st.session_state.nbay
        
            # Deduct purlins replaced by secondary trusses
            num_sec_trusses_axes = len(model.sec_trusses_j)
            num_purlins -= (num_sec_trusses_axes * st.session_state.nbay)
        
            num_sec_trusses_total = num_sec_trusses_axes * st.session_state.nbay
            wind_cols_line = f"&emsp;<span style='font-weight:700; color:#1e293b;'>• Columnas (Viento):</span> <span style='font-weight:700; color:#1e3a8a;'>{num_wind_cols}</span><br>" if num_wind_cols > 0 else ""
            sec_trusses_line = f"&emsp;<span style='font-weight:700; color:#1e293b;'>• Armaduras (Secundarias):</span> <span style='font-weight:700; color:#1e3a8a;'>{num_sec_trusses_total}</span><br>" if num_sec_trusses_total > 0 else ""
            
            num_md_juntas = len(getattr(model, 'joint_axes', [])) if getattr(model, 'has_marco_doble', False) else 0
            md_line = f"<span style='font-weight:700; color:#1e293b;'>• Marcos Dobles:</span> <span style='font-weight:700; color:#1e3a8a;'>{num_md_juntas}</span><br>" if num_md_juntas > 0 else ""

            num_jc_juntas = len(getattr(model, 'joint_axes', [])) if getattr(model, 'has_junta_cubierta', False) else 0
            jc_line = f"<span style='font-weight:700; color:#1e293b;'>• Juntas en Cubierta:</span> <span style='font-weight:700; color:#1e3a8a;'>{num_jc_juntas}</span><br>" if num_jc_juntas > 0 else ""

            total_armaduras = model.nSpan * getattr(model, 'num_frames', model.nBay + 1)
            if getattr(model, 'ext_bays_active', False):
                ext_depth = getattr(model, 'ext_depth', 1)
                extra_per_corner = max(0, ext_depth - 1)
                if getattr(model, 'ext_bl', False): total_armaduras += extra_per_corner
                if getattr(model, 'ext_tl', False): total_armaduras += extra_per_corner
                if getattr(model, 'ext_br', False): total_armaduras += extra_per_corner
                if getattr(model, 'ext_tr', False): total_armaduras += extra_per_corner
            
            num_purlins = len(model.groups.get('_LARGUEROS', []))
            
            elementos_html = f"""
            <div style="font-family: 'Aptos Display', 'Segoe UI', sans-serif; font-size: 1.1rem; font-weight: 700; color: #0f172a; margin-bottom: 10px; margin-top: -5px;">Elementos</div>
            <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 0 0 12px 0 !important;">
            <div style="font-family: 'Aptos Display', 'Segoe UI', sans-serif; line-height: 1.8; color: #334155; font-size: 13px; padding-bottom: 15px; padding-left: 15px;">
                {md_line}{jc_line}<span style='font-weight:700; color:#1e293b;'>• Columnas Principales:</span> <span style='font-weight:700; color:#1e3a8a;'>{len(model.groups.get('_COL', [])) // 2}</span><br>
                {wind_cols_line}<span style='font-weight:700; color:#1e293b;'>• Armaduras:</span> <span style='font-weight:700; color:#1e3a8a;'>{total_armaduras}</span><br>
                {sec_trusses_line}<span style='font-weight:700; color:#1e293b;'>• Contravientos:</span> <span style='font-weight:700; color:#1e3a8a;'>{len(model.groups.get('_CVH', []))}</span><br>
                <span style='font-weight:700; color:#1e293b;'>• Largueros:</span> <span style='font-weight:700; color:#1e3a8a;'>{num_purlins}</span>
            </div>
            """
            
            st.markdown(elementos_html, unsafe_allow_html=True)
            
        with st.container():
            st.markdown("<div class='ios-glass-marker'></div>", unsafe_allow_html=True)
            
            largo_total = st.session_state.ljoist * st.session_state.nbay
            
            ancho_total = model.total_width / model.scale
                
            hlib = st.session_state.hlib
            harm = st.session_state.harm
            slope_pct = st.session_state.slope_pct
            
            y_shift_ext = 0.0
            if st.session_state.get('ext_bays_active', False) and st.session_state.get('ext_height_mode', "") == "Altura mínima en esquinas":
                w_left = st.session_state.get('ext_larm', 15.24) if (st.session_state.get('ext_bl', False) or st.session_state.get('ext_tl', False)) else 0.0
                w_right = st.session_state.get('ext_larm', 15.24) if (st.session_state.get('ext_br', False) or st.session_state.get('ext_tr', False)) else 0.0
                if st.session_state.roof_type == "1 Agua":
                    y_shift_ext = w_left * (slope_pct / 100.0)
                else:
                    y_shift_ext = max(w_left, w_right) * (slope_pct / 100.0)

            if st.session_state.roof_type == "2 Aguas":
                h_max = hlib + harm + (ancho_total / 2.0) * (slope_pct / 100.0) + y_shift_ext
            else:
                h_max = hlib + harm + ancho_total * (slope_pct / 100.0) + y_shift_ext
                
            geometria_html = f"""
            <div style="font-family: 'Aptos Display', 'Segoe UI', sans-serif; font-size: 1.1rem; font-weight: 700; color: #0f172a; margin-bottom: 10px; margin-top: -5px;">Geometría</div>
            <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 0 0 12px 0 !important;">
            <div style="font-family: 'Aptos Display', 'Segoe UI', sans-serif; line-height: 1.8; color: #334155; font-size: 13px; padding-bottom: 15px; padding-left: 15px;">
                <span style='font-weight:700; color:#1e293b;'>• Largo:</span> <span style='font-weight:700; color:#1e3a8a;'>{largo_total:.2f} m</span><br>
                <span style='font-weight:700; color:#1e293b;'>• Ancho:</span> <span style='font-weight:700; color:#1e3a8a;'>{ancho_total:.2f} m</span><br>
                <span style='font-weight:700; color:#1e293b;'>• Altura Libre:</span> <span style='font-weight:700; color:#1e3a8a;'>{hlib:.2f} m</span><br>
                <span style='font-weight:700; color:#1e293b;'>• Altura Máxima:</span> <span style='font-weight:700; color:#1e3a8a;'>{h_max:.2f} m</span><br>
                <span style='font-weight:700; color:#1e293b;'>• Pendiente:</span> <span style='font-weight:700; color:#1e3a8a;'>{slope_pct:.1f} %</span>
            </div>
            """
            
            st.markdown(geometria_html, unsafe_allow_html=True)

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

