# Informe de línea base — 2026-11-05

Commit base: `39ed73d` (etiqueta `v1.0.0-pre-limpieza-2026-11-05`). Rama de trabajo: `chore/limpieza-segura-2026-11-05`.

## Cómo se generó
- `docs/baseline/gen_baseline.py` replica el flujo de `app/main.py` con los valores por defecto del diccionario `defaults` (armaduras 15,24 m, joists 12,192 m, 7 bahías, 4 entre-ejes, peralte 1,30 m, altura libre 9,75 m, subdivisiones 10, cubierta "2 Aguas", pendiente 5 %, apoyos FIXED, CM 30 / CV 100 / granizo 60, viento 86/50/78/95, sismo 0,08, ductilidad 2,0, columnas de viento activas con 8 m, muros Metálico, reglamento "Chihuahua / IBC", ASD, Grupo B) y los perfiles que `main.py` elige por defecto desde `prediseno`.
- `docs/baseline/apptest_panels.py` abre cada panel con `streamlit.testing.AppTest` (headless).
- Entorno: Python 3.14, streamlit 1.59.0, plotly 6.8.0, pandas 3.0.3, ezdxf 1.4.5.

## Referencia de oro
Archivo: `docs/baseline/test-default-2026-11-05.std`

| Dato | Valor |
|---|---|
| Líneas | 1218 |
| SHA-256 del archivo (con fecha del día) | `3F4CEA9B87E595AD92F5F4B0661DD9A0535D5058C1BC1B751B2807BFFDB4E82E` |
| SHA-256 normalizado (línea de fecha reemplazada) | `0eabd6414ba74800b3de5d0bffc207caee82665e0f458eee7166cd820f24bb33` |

El encabezado `ENGINEER DATE` usa `datetime.now()` (`staad_writer.py:111`); por eso la comparación entre fases se hace con el hash **normalizado**. Dos corridas seguidas dieron el mismo hash normalizado (determinista).

## Conteo del modelo por defecto
618 nodos, 1539 miembros. Grupos: `_COL` 80, `_COLVIENTO` 22, `_CS` 160, `_CI` 96, `_MONTANTES` 80, `_DIAG` 160, `_LARGUEROS` 315, `_CVH` 88, `_JOISTGRAL` 210, `_JPUNTAL` 105.

Equivalencia de conteos (aclarada, no es un error y no se corrige nada):
- **40 columnas físicas = 80 miembros `_COL`.** En `app/model.py:554-555` cada columna física se genera como dos miembros (`nL1→nL2` base→alero y `nL2→nL3` alero→cumbrera), ambos en el grupo `_COL`. Con 7 bahías (8 ejes) × 4 entre-ejes (5 ejes) = 8 × 5 = 40 columnas físicas → 80 miembros. Coinciden además 22 de viento, 88 contravientos y 315 largueros. No hay un grupo único de "armaduras": se reparte en `_CS/_CI/_MONTANTES/_DIAG`.
- Perfiles elegidos por defecto: solo `CV-1` y `_CVH` → `W12X65`. `prediseno.clasificar_columnas` no devuelve selección para C-1..C-4 en el modelo por defecto sin análisis (observación, sin cambios).

## Qué funciona en local
Los 5 paneles abren con 0 excepciones y 0 errores de UI: Main, Geometría, Cargas, Prediseño, Cimentación (probado con AppTest). Solo aparecen avisos de deprecación de Streamlit (`use_container_width`, `st.components.v1.html`), no son errores.

## Qué no se pudo comprobar
- Captura visual del visor 3D (AppTest no renderiza Plotly en pantalla).
- Comportamiento en web (stlite/Vercel): se verifica en la Fase 2.


## Aclaración: código de salida del AppTest

**Conclusión:** el código de salida 1 que se vio en dos corridas **no viene de Python ni de la app**; viene de cómo PowerShell/el ejecutor interpreta el texto que Streamlit escribe en stderr. No hubo excepciones.

Cómo se comprobó (2026-11-05, misma máquina, mismos comandos):

| Forma de ejecutar | Código de salida de Python (`$LASTEXITCODE`) | `$?` de PowerShell | Salida del script |
|---|---|---|---|
| `python docs/baseline/apptest_panels.py > out.txt 2> err.txt` (stdout y stderr a archivos) | **0** | verdadero | 5 paneles con `excepciones=0 errores_ui=0` |
| `python … 2>&1 \| Select-Object -First 3` (forma de la 1.ª corrida original) | -1 | falso | el `Select -First` cierra la tubería antes de que Python termine; stderr se convierte en `NativeCommandError` |
| `python … 2>$null \| Select-String …` (forma de la 2.ª corrida original) | 0 | falso | stderr redirigido a `$null` marca `$?` como falso |

El ejecutor de comandos informó "exit code 1" cuando `$?` era falso o la tubería se cortó, no el código real de Python. La corrida con redirección a archivos da 0.

Evidencia concreta en `err.txt` (142 líneas): 0 apariciones de `Traceback`; 12 líneas `WARNING streamlit.runtime.scriptrunner_utils.script_run_context: … missing ScriptRunContext! This warning can be ignored when running in bare mode`; 20 líneas `Please replace …` (avisos de deprecación: `st.components.v1.html` → `st.iframe` y `use_container_width` → `width`); y 1 aviso `label got an empty value` (con un "Stack" informativo del logger, no una excepción). Además, `at.exception` y `at.error` de AppTest estuvieron vacíos en los 5 paneles. Estos avisos ya existían en el código antes de la limpieza.

Aclaración sobre un `exit code 0` posterior: en la corrida de la Fase 2 el comando combinaba AppTest + `git commit` + `git push`; el código reportado fue el del último comando, no el de AppTest. Por eso no se debe usar ese 0 como evidencia: la evidencia válida es la tabla de arriba.

Limitación: no se pudo ver si Streamlit sale con 1 en otros entornos (CI, Linux); solo se verificó en esta máquina con Python 3.14 y streamlit 1.59.0.
