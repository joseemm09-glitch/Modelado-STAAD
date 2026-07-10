import streamlit as st
import math
import os
import subprocess
import importlib
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

icono_path = os.path.join(os.path.dirname(__file__), "..", "staad_green.ico")
st.set_page_config(page_title="Naves Industriales STAAD.Pro", page_icon=icono_path, layout="wide")

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
</style>
""", unsafe_allow_html=True)


# CSS para botones
st.markdown("""
    <style>
    /* Botones principales (Azul oscurecido) */
    section[data-testid="stSidebar"] button[kind="primary"] {
        background: linear-gradient(180deg, #2472A6 0%, #17537A 100%) !important;
        color: white !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px !important;
        border-radius: 6px !important;
        width: 100% !important;
        margin: 0 auto !important;
        display: block !important;
        border: 1px solid #144769 !important;
        text-align: center !important;
        justify-content: center !important;
        box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.2) !important;
        transition: all 0.2s ease-in-out !important;
    }
    section[data-testid="stSidebar"] button[kind="primary"]:hover {
        background: linear-gradient(180deg, #297FB8 0%, #1D6799 100%) !important;
        box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.3) !important;
        transform: translateY(-1px) !important;
        border: 1px solid #17537A !important;
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
        margin-bottom: -20px !important;
        margin-top: 15px !important;
        position: relative !important;
        z-index: 10 !important;
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
    /* Descomentar para ocultar el header (Deploy/Menu) en producción: */
    /* header {visibility: hidden !important; display: none !important;} */
    footer {visibility: hidden !important; display: none !important;}
    </style>
""", unsafe_allow_html=True)

st.title("Generador Naves Industriales STAAD.Pro")
st.markdown("<div style='color: gray; margin-top: -10px; margin-bottom: 10px;'>&emsp;&emsp;M.I. José Ramón Márquez Montes</div>", unsafe_allow_html=True)

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

# Ensure even subdivisions
if st.session_state.subdiv % 2 != 0:
    st.sidebar.error("Las subdivisiones deben ser un número par.")
    st.stop()

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
    sec_trusses_j = st.session_state.get('sec_truss_custom_ejes', [])

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


with st.sidebar:
    panel = st.session_state.current_panel
    
    if panel == "Main":
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center;'>Menú Principal</h2>", unsafe_allow_html=True)
        st.button("Geometría", type="primary", width="stretch", on_click=go_panel, args=("Geometría",))
        st.button("Cargas", type="primary", width="stretch", on_click=go_panel, args=("Cargas",))
        st.button("Prediseño", type="primary", width="stretch", on_click=go_panel, args=("Prediseño",))
        
    elif panel == "Geometría":
        st.button("⬅", type="secondary", on_click=go_panel, args=("Main",))
        st.header("Geometría")
        
        wt_idx = 0 if st.session_state.get("wall_type", "Metálico") == "Metálico" else 1
        st.radio("Tipo de Muros", ["Metálico", "Tilt-Up"], index=wt_idx, key="_wall_type", on_change=update_val, args=("wall_type",), horizontal=True)
        
        with st.expander("Dimensiones Generales", expanded=False):
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
                new_selected = []
                for j in interior_j:
                    chk = st.checkbox(f"X = {j * st.session_state.larm:.2f} m", value=(j in selected_ejes), key=f"sec_eje_{j}")
                    if chk:
                        new_selected.append(j)
                st.session_state.sec_truss_custom_ejes = new_selected

        if st.session_state.wall_type != "Tilt-Up":
            with st.expander("Columnas de Viento", expanded=False):
                st.checkbox("Columnas de Viento", value=st.session_state.add_wind_cols, key="_add_wind_cols", on_change=update_val, args=("add_wind_cols",))
                if st.session_state.add_wind_cols:
                    st.number_input("Separación Máxima (m)", min_value=1.0, step=0.1, value=float(st.session_state.max_wind_dist), key="_max_wind_dist", on_change=update_val, args=("max_wind_dist",))
        else:
            st.session_state.add_wind_cols = False

    elif panel == "Cargas":
        st.button("⬅", type="secondary", on_click=go_panel, args=("Main",))
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

    elif panel == "Prediseño":
        st.button("⬅", type="secondary", on_click=go_panel, args=("Main",))
        st.header("Prediseño")
        
        with st.expander("Columnas", expanded=True):
            grupos_cols = prediseno.clasificar_columnas(model)
            
            if not grupos_cols:
                st.warning("No se encontraron columnas para diseñar.")
            else:
                st.radio("Resaltar en 3D:", list(sorted(grupos_cols.keys())), key="highlight_grupo_col")
                for nombre_grupo in sorted(grupos_cols.keys()):
                    top_5 = prediseno.predisenar_grupo(nombre_grupo, model)
                    
                    if top_5:
                        opciones = [p['perfil']['nombre'] for p in top_5]
                        st.selectbox(nombre_grupo, options=opciones, key=f"sel_{nombre_grupo}")
                    else:
                        st.error(f"No se encontraron perfiles óptimos.")

col1, col2 = st.columns([3, 1])

with col1:
    st.markdown("<div style='margin-top: -30px;'></div>", unsafe_allow_html=True)
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
        st.subheader("Exportación")
        
        project_name = st.text_input("Nombre del Proyecto:", value="Modelo")
        file_name_export = f"{project_name.strip()}.std" if project_name.strip() else "Modelo.std"
        
        st.markdown("**Ubicación:**")
        
        if 'export_path' not in st.session_state:
            st.session_state.export_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
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
        db_or = prediseno.generar_base_datos_or()
        db_w = prediseno.generar_base_datos_w()
        name_to_staad = {p['nombre']: p['nombre_staad'] for p in db_or + db_w}
        
        selected_profiles = {}
        grupos_cols = prediseno.clasificar_columnas(model)
        for g in grupos_cols.keys():
            ui_name = st.session_state.get(f"sel_{g}")
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
                    subprocess.call(('open', full_path))
                    
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

