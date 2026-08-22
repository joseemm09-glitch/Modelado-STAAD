# Reglas y Estándares para Integración de OpenStaad en Python

Este documento define las reglas de arquitectura y buenas prácticas para integrar la comunicación directa y en tiempo real con STAAD.Pro utilizando la librería `openstaad`. 

## 1. Independencia y Modularidad

Dado que esta integración podría convertirse eventualmente en una herramienta "standalone" (independiente del generador actual), **todo el código relacionado con la comunicación en tiempo real con STAAD.Pro debe mantenerse estrictamente separado**.

- **Carpeta dedicada**: Todo el código de OpenSTAAD vivirá en un módulo o subcarpeta separada (ej. `app/staad_link/` o similar).
- **Desacoplamiento de UI**: La interfaz de Streamlit (`main.py`) sólo debe importar funciones de "alto nivel" de este módulo. La interfaz gráfica no debe manejar directamente objetos de OpenSTAAD ni conexiones COM.
- **Sin estado global acoplado**: El módulo de OpenSTAAD debe poder instanciarse y usarse en cualquier script (no dependerá de `st.session_state`).

## 2. Conexión y Sesiones (Librería `openstaad`)

Utilizaremos la librería oficial open-source `openstaad` para Python, la cual simplifica el código boilerplate de COM.

- **Inicialización**: La conexión a la instancia activa de STAAD.Pro siempre se realizará usando:
  ```python
  from openstaad import ops
  
  def conectar_staad():
      try:
          sesion = ops.connect()
          return sesion
      except Exception as e:
          # Manejo de error estructurado si STAAD no está abierto
          return None
  ```
- **Gestión de la sesión**: Nunca guardaremos la sesión activa cruda en cachés globales si no podemos asegurar su persistencia. Se debe validar que `s.GetSTAADFile()` retorne algo válido antes de ejecutar operaciones pesadas.

## 3. Flujo de Trabajo: Diseño y Prediseño en Tiempo Real

- **Lectura de estado**: Al presionar un botón (ej. "Obtener resultados" o "Prediseño en vivo"), el módulo independiente leerá fuerzas, desplazamientos o información de secciones directamente del modelo abierto.
- **Escritura (Edición en vivo)**: Cuando el programa proponga perfiles nuevos, se enviarán a STAAD usando funciones nativas de la librería, sin reescribir todo el archivo `.std` (a menos que el usuario opte por la exportación estática tradicional).
- **Sincronización de un solo sentido a la vez**:
  - *Lectura*: `STAAD.Pro -> Python -> UI de Streamlit`
  - *Escritura*: `UI de Streamlit -> Python -> STAAD.Pro`

## 4. Dependencias

Se deberá asegurar que el archivo `requirements.txt` o entorno incluya:
```text
openstaad>=0.0.15
```
*(Nota: basándonos en la documentación actual que ya soporta `AssignSupportToNodes` y `ops.connect()`).*

## 5. Integración futura en la Interfaz Actual

Se creará un panel o sección específica dentro de `main.py` (quizás una nueva pestaña "STAAD en vivo") que, bajo el capó, invocará el módulo independiente para realizar la lectura/escritura de propiedades. Todo funcionará aquí primero como prueba de concepto, con la tranquilidad de que el backend será completamente exportable a otra aplicación.
