# FrameOne (Modelado-STAAD)

Generador paramétrico de modelos tridimensionales de naves industriales para STAAD.Pro (FrameOne).

---

## 1. Qué hace y qué NO hace

### Qué hace
- **Genera la geometría 3D paramétrica** de naves industriales (marcos principales a 1 o 2 aguas o cubierta plana, armaduras de cubierta, columnas principales y de viento, largueros/joists, contraventeos, bahías de extensión, muros metálicos o Tilt-Up y juntas constructivas).
- **Genera el archivo de entrada `.std`** compatible con STAAD.Pro (`UNIT CM KG`), incluyendo coordenadas de nudos, incidencias, grupos, tablas de usuario (`UPT`), propiedades de secciones, constantes de material, liberaciones, apoyos, casos de carga primarios, combinaciones y parámetros de verificación.
- **Configura cargas y combinaciones normativas** según 4 reglamentos disponibles (`Chihuahua / IBC`, `NTC-CDMX`, `CFE Viento / Sismo`, `ASCE 7 / IBC`), métodos `ASD` o `LRFD`, grupo de importancia (`A` o `B`) y opción de sismo bidireccional (100% + 30%).
- **Realiza prediseño preliminar SOLO de columnas** (`C-1` a `C-4` y columnas de viento `CV-1`) por áreas tributarias y fórmulas analíticas de flexocompresión, sugiriendo perfiles tubulares (`HSS`/`OR`) o `W`.
- **Calcula cimentación preliminar** (zapatas aisladas cuadradas y dados por aplastamiento y levantamiento por succión de viento), muestra vista previa 2D en planta y corte transversal en la interfaz, y **exporta plano preliminar `.dxf`** (en escritorio) sobre plantilla CAD.
- **Muestra un visor 3D interactivo** en Plotly con filtros por grupos estructurales.

### Qué NO hace
- **NO analiza estructuras**: el cálculo matricial de esfuerzos, desplazamientos y reacciones reales lo ejecuta STAAD.Pro.
- **NO calcula presiones de viento ni espectro sísmico**: las presiones de viento (barlovento, sotavento, laterales y succión en kg/m²) y el coeficiente sísmico son entradas directas del usuario; el sismo generado es estático equivalente por coeficiente.
- **NO diseña armaduras, largueros ni contravientos**: les asigna secciones fijas de tablas de usuario (`UPT 1` para cuerdas/celosía, `UPT 2 JOIST30` para joist general, `UPT 3 JPUNTAL` para joist puntal y `PIPE OD 1.905` para `_CVH`).
- **El módulo de Diseño con OpenSTAAD es exclusivo de escritorio Windows**: requiere STAAD.Pro abierto en la misma máquina y comunicación COM (`openstaad` / `win32com`), por lo que no opera en la versión web.
- **`LOAD 3` (CV entrepiso) y `LOAD 4` (CVR) quedan vacíos en la plantilla actual** (`app/templates.py:150-154`): se emiten sus encabezados sin cargas de miembro asociadas (las cargas vivas de cubierta van en `LOAD 5` y `LOAD 6`).

---

## 2. Arquitectura y mapa de módulos

| Archivo | Responsabilidad | Líneas aprox. |
|---|---|---|
| `app/main.py` | Interfaz gráfica en Streamlit, estado de sesión, navegación entre los 5 paneles y flujo de exportación `.std` / `.dxf`. | 2.416 |
| `app/cimentacion_cad.py` | Extracción de reacciones (OpenSTAAD o estimación analítica tributaria), predimensionamiento de zapatas aisladas cuadradas, vista previa 2D en Plotly y exportación de plano `.dxf` con `ezdxf`. | 2.156 |
| `app/model.py` | Clase `StaadModel` y método `generate()`: generación paramétrica de nudos, barras, placas Tilt-Up, grupos estructurales, liberaciones y áreas tributarias. | 1.568 |
| `app/staad_writer.py` | Función `write_staad(model, selected_profiles=None, cvh_props=None)`: serialización completa del modelo al formato de texto `.std` de STAAD.Pro. | 1.006 |
| `app/perfiles_w.py` | Catálogo embebido de 330 perfiles `W` (AISC) con propiedades geométricas para prediseño. | 568 |
| `app/prediseno.py` | Clasificación de columnas (`C-1`..`C-4`, `CV-1`), base embebida de perfiles `HSS`/`OR` y prediseño analítico preliminar de columnas. | 528 |
| `app/reglamentos.py` | Definición de los 4 reglamentos de carga, factores de prediseño, generación de combinaciones (`ASD`/`LRFD`) y comando `CODE AISC`. | 489 |
| `app/templates.py` | Plantillas base de `USER TABLE` (`UPT 1`) y bloque base de casos de carga primarios (`CARGAS_TEMPLATE`). | 438 |
| `app/visualizer.py` | Función `plot_model()`: renderizado 3D interactivo de la nave en Plotly. | 420 |
| `app/staad_link/link.py` | Conexión COM con OpenSTAAD (`check_staad_status`, `run_analysis`, `get_design_results`) para escritorio Windows. | 89 |
| `build_stlite.py` | Empaquetador estático para despliegue web con `@stlite/mountable` (Pyodide): incrusta módulos y recursos en `public/index.html` e `index.html`. | 294 |

Módulos auxiliares en el repositorio (uso en empaquetado de escritorio / administración):
- `Ejecutable/desktop_runner.py`: lanzador de ventana nativa (`pywebview`) con validación de licencia para distribución StandAlone.
- `security/`: cliente y servicios de licenciamiento por hardware ID (`hwid.py`, `client.py`, `admin_service.py`).
- `Catalogo/`: módulo de catálogo AISC (`catalogo_ui.py`, `aisc_loader.py`, `excel_exporter.py`), actualmente oculto en el menú principal.

---

## 3. Cómo ejecutar en local (StandAlone) y cómo se despliega en web (stlite/Vercel)

### Ejecución en local (StandAlone / desarrollo)
1. Requisitos: Python 3.10+ en Windows y dependencias de `app/requirements.txt` (`streamlit`, `plotly`, `ezdxf`, además de `pandas` y `openpyxl` para tablas y exportación).
2. Instalación de dependencias:
   ```bash
   pip install -r app/requirements.txt pandas openpyxl
   ```
3. Arranque directo con el script incluido o con Streamlit:
   ```bash
   Iniciar_App.bat
   # equivalente a:
   python -m streamlit run app/main.py
   ```

### Empaquetado y despliegue en web (stlite / Vercel)
La versión web se ejecuta íntegramente en el navegador mediante `@stlite/mountable@0.73.1` (Pyodide) sin servidor Python en backend:
1. `build_stlite.py` lee los archivos listados en `FILES_TO_INCLUDE` (incluyendo `app/main.py`, `app/model.py`, `app/staad_writer.py`, `app/visualizer.py`, `app/prediseno.py`, `app/templates.py`, `app/reglamentos.py`, `app/cimentacion_cad.py`, `app/perfiles_w.py`, `app/staad_link/*` y las tablas `Archivos/JOISTGRAL.UPT` y `Archivos/JPUNTAL.UPT`) y genera `public/index.html` (y una copia en `index.html` de la raíz) con `entrypoint: "app/main.py"` y `requirements: ["plotly"]`.
2. Para regenerar el bundle estático después de cualquier cambio en `app/`:
   ```bash
   python build_stlite.py
   # o bien: npm run build
   ```
3. `vercel.json` define únicamente `"outputDirectory": "public"`, por lo que Vercel publica directamente `public/index.html`.

---

## 4. Flujo de uso en 5 pasos y valores por defecto

La barra lateral organiza el flujo en 5 paneles:

1. **Geometría**: definición de dimensiones generales, tipo de muros (`Metálico` o `Tilt-Up`), armaduras secundarias, diferentes claros, bahías de extensión y juntas constructivas.
2. **Cargas**: selección de reglamento, método de diseño (`ASD` o `LRFD`), grupo de importancia (`A` o `B`), cargas gravitacionales, presiones de viento, parámetros de sismo y visualización de la lista de combinaciones generadas.
3. **Prediseño**: selección del perfil preliminar para cada grupo de columnas (`C-1`, `C-2`, `C-3`, `C-4`, `CV-1`) a partir del top 5 calculado.
4. **Cimentación Preliminar**: definición de parámetros geotécnicos ($q_{\text{adm}}$, $D_f$, $\gamma_s$), tabla editable de zapatas aisladas (`Z-1`, `Z-2`, …), vista previa 2D (`Cimentación Preliminar` y `Corte Transversal`) y, en escritorio, botón **Exportar DWG** (genera `.dxf` y lo abre en AutoCAD si está disponible).
5. **Diseño** *(solo escritorio Windows con STAAD.Pro abierto)*: conexión en vivo vía OpenSTAAD, ejecución de análisis y consulta de ratios de diseño por grupo.

### Valores por defecto del modelo (`app/main.py`)
- **Geometría**: claro de armaduras `15,24 m`, longitud de joists `12,192 m`, `7` bahías, `4` entre-ejes, peralte de armadura `1,30 m`, altura libre `9,75 m`, `10` subdivisiones, cubierta `2 Aguas`, pendiente `5,0 %`, apoyos `FIXED`, muros `Metálico`, columnas de viento activas con separación máx. `8,0 m`, sin juntas constructivas.
- **Cargas y reglamento**: `Chihuahua / IBC`, método `ASD`, `Grupo B`, sin sismo bidireccional; carga muerta `30,0 kg/m²`, carga viva `100,0 kg/m²`, granizo `60,0 kg/m²`; viento barlovento `86,0 kg/m²`, sotavento `50,0 kg/m²`, laterales `78,0 kg/m²`, succión `95,0 kg/m²`; coeficiente sísmico `0,08`, ductilidad `2,0`.
- **Conteo del modelo por defecto**:
  - **618 nodos** y **1.539 miembros** en total.
  - **Aclaración sobre columnas principales (`40 columnas físicas = 80 miembros _COL`)**: en `app/model.py:554-555`, cada columna física se modela como dos miembros consecutivos (`base → alero` y `alero → cumbrera`), ambos agregados al grupo `_COL`. Con 8 ejes transversales (7 bahías) × 5 ejes longitudinales (4 entre-ejes) se tienen **40 columnas físicas**, equivalentes a **80 miembros en `_COL`**.
  - Resto de grupos del modelo por defecto: `22` columnas de viento (`_COLVIENTO`), `88` contravientos (`_CVH`), `315` largueros (`_LARGUEROS`, divididos en `210` `_JOISTGRAL` + `105` `_JPUNTAL`), `160` cuerda superior (`_CS`), `96` cuerda inferior (`_CI`), `80` montantes (`_MONTANTES`) y `160` diagonales (`_DIAG`).

---

## 5. Cómo se genera el `.std` y cómo se abre en STAAD.Pro

1. En el panel derecho de la interfaz, escribe el **Nombre Proyecto** (por defecto `Modelo`, extensión `.std`).
2. **En escritorio**: elige la carpeta destino (con el botón `📁` que usa `tkinter` en un subproceso local) y pulsa **Generar archivo STAAD.Pro**. El archivo se escribe con codificación `windows-1252` y, si está disponible el ejecutable de STAAD.Pro (` Bentley.Staad.exe` / `SProStaad.exe`), se lanza automáticamente.
3. **En web (stlite / Vercel)**: el selector `tkinter` no existe en el navegador; en su lugar se renderiza el componente JavaScript con la File System Access API (`showDirectoryPicker`) y descarga en base64 para guardar el archivo `.std` directamente en la carpeta local elegida por el usuario, y después abrirlo manualmente desde STAAD.Pro (`File -> Open`).

### Notas técnicas verificadas sobre la generación del `.std`
- **Hallazgo de fallo silencioso corregido en Fase 2 (`reglamentos.py` en web)**: tanto `app/prediseno.py:317` como `app/staad_writer.py:864` importan `reglamentos` dentro de un bloque `try/except`. Antes de incluir `app/reglamentos.py` en `build_stlite.py`, la versión web caía silenciosamente en el `except`, usando factores `1.0` en prediseño y combinaciones estáticas con `CODE AISC` genérico en lugar del reglamento seleccionado. Con la inclusión de `app/reglamentos.py` y `app/cimentacion_cad.py` en `FILES_TO_INCLUDE` (Fase 2), el `.std` generado en web utiliza exactamente los mismos módulos que en escritorio (pendiente de verificación en el preview de Vercel por parte del usuario).
- **Verificación de propiedades de `_LARGUEROS`**: aunque en `app/staad_writer.py:272` la variable `larg_str = group_ranges(group_map.get('_LARGUEROS', []))` no se utiliza posteriormente, **los 315 miembros de `_LARGUEROS` sí tienen propiedad asignada en el `.std`**, ya que todos pertenecen simultáneamente a `_JOISTGRAL` (210 miembros con `UPT 2 JOIST30`) o a `_JPUNTAL` (105 miembros con `UPT 3 JPUNTAL`). El grupo `_LARGUEROS` (y `_LARGUEROS_0..3`) se emplea para la aplicación de cargas distribuidas de cubierta.

---

## 6. Limitaciones conocidas y trabajo futuro

- **`LOAD 3` y `LOAD 4` vacíos en `app/templates.py`**: el bloque `CARGAS_TEMPLATE` declara `LOAD 3 LOADTYPE None TITLE CARGA VIVA (CV)` y `LOAD 4 LOADTYPE None TITLE CARGA VIVA (CVR)` sin cargas asociadas (la carga viva de techo se escribe en `LOAD 5` y `LOAD 6`).
- **Parámetro `cvh_props` sin mapeo en `write_staad`**: en `app/staad_writer.py:106` se aceptó el argumento opcional `cvh_props=None` para evitar un `TypeError` al invocarse desde `app/main.py:1748`, pero actualmente el escritor siempre emite `TABLE ST PIPE OD 1.905 ID 0` para todo el grupo `_CVH`. Mapear diámetros individuales por barra en el `.std` queda como trabajo futuro.
- **Exportación DXF exclusiva de escritorio**: en web el paquete `ezdxf` y las plantillas `.dxf` no se incluyen en el bundle de `stlite`; la pestaña Cimentación Preliminar en web muestra el cálculo y las vistas 2D interactivas en Plotly, mientras que el botón `Exportar DWG` solo se presenta en escritorio.
- **Integración OpenSTAAD solo en Windows local**: depende de la API COM de STAAD.Pro en ejecución local.
- **Trabajo futuro**:
  - Sincronización bidireccional completa con OpenSTAAD (incluyendo reflejo de `cvh_props` en el `.std`).
  - Cálculo automático de presiones de viento y espectro sísmico a partir de velocidad regional / ubicación (CFE / ASCE 7).
  - Prediseño paramétrico de elementos de armadura (`_CS`, `_CI`, `_MONTANTES`, `_DIAG`), largueros y contravientos.

---

## 7. Respaldo y reversión

Antes de la limpieza e integración del fix web se congeló un respaldo íntegro del repositorio en el commit `39ed73d`:

- **Etiqueta anotada**: [`v1.0.0-pre-limpieza-2026-11-05`](https://github.com/joseemm09-glitch/Modelado-STAAD/tree/v1.0.0-pre-limpieza-2026-11-05)
- **Rama de respaldo**: [`backup/pre-limpieza-2026-11-05`](https://github.com/joseemm09-glitch/Modelado-STAAD/tree/backup/pre-limpieza-2026-11-05)
- **Release en GitHub**: [`v1.0.0-pre-limpieza-2026-11-05`](https://github.com/joseemm09-glitch/Modelado-STAAD/releases/tag/v1.0.0-pre-limpieza-2026-11-05)
- **Bundle local completo (fuera del repo)**: `../frameone-backup-2026-11-05.bundle`

Comandos para revertir o recuperar archivos en cualquier momento:
```bash
# Inspeccionar el estado exacto previo a la limpieza:
git checkout v1.0.0-pre-limpieza-2026-11-05

# Crear una rama nueva de restauración a partir del respaldo:
git checkout -b restauracion-YYYY-MM-DD backup/pre-limpieza-2026-11-05

# Recuperar un archivo o carpeta individual eliminado en la Fase 3:
git checkout v1.0.0-pre-limpieza-2026-11-05 -- <ruta>
```

---

## 8. Licencia, autoría e INDAUTOR

Según consta en los documentos del repositorio (`INDAUTOR_Registro_FrameOne.docx`, `INDAUTOR_Registro_STAAD.pdf` y el pie de página de `app/main.py`):
- **Obra / Programa de cómputo**: *FrameOne* (Modelado de Naves Industriales para STAAD.Pro).
- **Autor**: José Ramón Márquez Montes (`INDAUTOR_Registro_FrameOne.docx`, 2026, México).
- **Marca / aviso en interfaz**: `® 2026 Tensor Systems. Todos los derechos reservados. v1.0.0` (`admintensorsystems@gmail.com`).
- No existe un archivo `LICENSE` de código abierto en el repositorio; todos los derechos pertenecen a sus titulares.
