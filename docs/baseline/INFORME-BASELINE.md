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

Discrepancias con el conteo del prompt (a confirmar contigo, no se corrigió nada):
- El prompt indica 40 columnas principales y 32 armaduras; el modelo da `_COL` = 80 y no hay un grupo único de "armaduras" (se reparte en `_CS/_CI/_MONTANTES/_DIAG`). Coinciden 22 viento, 88 contravientos y 315 largueros.
- Perfiles elegidos por defecto: solo `CV-1` y `_CVH` → `W12X65`. `prediseno.clasificar_columnas` no devuelve selección para C-1..C-4 en el modelo por defecto sin análisis.

## Qué funciona en local
Los 5 paneles abren con 0 excepciones y 0 errores de UI: Main, Geometría, Cargas, Prediseño, Cimentación (probado con AppTest). Solo aparecen avisos de deprecación de Streamlit (`use_container_width`, `st.components.v1.html`), no son errores.

## Qué no se pudo comprobar
- Captura visual del visor 3D (AppTest no renderiza Plotly en pantalla).
- Comportamiento en web (stlite/Vercel): se verifica en la Fase 2.
