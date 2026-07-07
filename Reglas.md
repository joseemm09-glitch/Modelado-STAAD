# Reglas y Mejores Prácticas para Generador STAAD.Pro (Python)

Este documento centraliza las reglas fundamentales que hemos descubierto y decidido aplicar durante el desarrollo de la aplicación de generación de modelos STAAD.Pro en Python. 
**Estas reglas deben ser consultadas y respetadas en futuras actualizaciones.**

## 1. Reglas de Formato de Salida (Archivos `.std`)

### 1.1 Ancho de Línea y Bloques Indivisibles
- **Límite de caracteres:** El archivo `.std` exige un máximo de 79 caracteres por línea (según el comando `INPUT WIDTH 79`).
- **Bloques Indivisibles:** Un bloque lógico como las coordenadas de un nodo (`1 0 10 25;`) o la incidencia de un miembro (`1 1 5;`) **jamás debe dividirse en dos líneas**.
- **Separador:** Los bloques múltiples en una misma línea deben separarse por punto y coma (`;`).

### 1.2 Formato Numérico y Optimización de Caracteres
- **Decimales innecesarios:** Si un valor decimal es exactamente cero (ej. `20.00`), **debe imprimirse como entero** (`20`) para ahorrar caracteres en la línea.
- **Precisión:** Utilizar un máximo de 2 decimales para evitar desbordamientos y mantener el archivo limpio.

### 1.3 Sintaxis de Agrupación (Rangos)
- Cuando se definen grupos (`START GROUP DEFINITION`) o se asignan apoyos (`SUPPORTS`), **siempre deben comprimirse los IDs consecutivos** usando la palabra reservada `TO`. 
- **Correcto:** `1 TO 66 FIXED`
- **Incorrecto:** `1 2 3 4 5 6 7... FIXED`

## 2. Reglas de Geometría y Lógica (Python)

### 2.1 Unidades Consistentes
- **Entrada del Usuario:** La interfaz (Streamlit) pide y muestra todas las dimensiones en **Metros (m)**.
- **Salida STAAD:** El archivo final se inicializa con `UNIT CM KG`.
- **Regla:** El motor de cálculo en Python (clase `StaadModel`) debe multiplicar matemáticamente las coordenadas ingresadas (en metros) por `100` ANTES de pasarlas al motor de escritura de texto, garantizando así congruencia total.

### 2.2 IDs Únicos e Inmutables
- Los IDs de los nodos (`JOINT COORDINATES`) y miembros (`MEMBER INCIDENCES`) deben llevarse mediante contadores globales únicos dentro del objeto del modelo para asegurar que nunca se sobrelapen.

### 2.3 Separación de Responsabilidades (MVC)
- `model.py`: Sólo se encarga de matemáticas y topología (generación de coordenadas 3D e índices).
- `staad_writer.py`: Sólo se encarga de convertir esos datos a texto bajo las reglas estrictas mencionadas en la sección 1.
- `visualizer.py`: Sólo se encarga de consumir el modelo para renderizado 3D en Plotly (devolviendo las coordenadas de cm a m visualmente).
- `main.py`: Sólo maneja la UI de Streamlit.
