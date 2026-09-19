import os
import docx
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

def main():
    doc = Document()
    
    # Establecer la fuente predeterminada para el estilo Normal
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Aptos Display'
    font.size = Pt(11)
    
    # Función de ayuda para agregar estilos
    def add_heading(text, level=1):
        h = doc.add_heading(text, level=level)
        for run in h.runs:
            run.font.name = 'Aptos Display'
        return h

    # --- CARÁTULA ---
    doc.add_paragraph("\n\n\n\n\n")
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title.add_run("Automatización de Modelado para STAAD.Pro\nFrameOne")
    title_run.font.name = 'Aptos Display'
    title_run.font.size = Pt(24)
    title_run.bold = True
    
    doc.add_paragraph("\n\n\n\n")
    
    info = doc.add_paragraph()
    info.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run1 = info.add_run("Autor: [Poner Tu Nombre Aquí]\n")
    run2 = info.add_run("Año: 2026\n")
    run3 = info.add_run("Lugar: México")
    for run in (run1, run2, run3):
         run.font.name = 'Aptos Display'
         run.font.size = Pt(14)
         
    doc.add_page_break()

    # --- FICHA TÉCNICA ---
    add_heading('Ficha Técnica y Síntesis', level=1)
    
    sintesis = (
        "El presente software, denominado FrameOne, es una herramienta informática desarrollada con el objetivo principal "
        "de automatizar y optimizar el proceso de modelado geométrico y estructural de naves industriales. "
        "Su función central consiste en generar de manera automatizada y eficiente los modelos "
        "tridimensionales requeridos para su integración y análisis en el software de ingeniería estructural "
        "STAAD.Pro, reduciendo significativamente el tiempo de modelado manual y minimizando la posibilidad "
        "de errores operativos."
    )
    p = doc.add_paragraph(sintesis)
    
    doc.add_page_break()

    # --- DIAGRAMA DE ARQUITECTURA ---
    add_heading('Diagrama de Arquitectura y Flujo', level=1)
    
    diagrama = (
        "1. Interfaz de Usuario (UI - Frontend):\n"
        "   - Captura de parámetros estructurales (dimensiones, marcos, largueros, etc.).\n"
        "   - Validación de datos de entrada.\n\n"
        "2. Motor Lógico (Backend):\n"
        "   - Procesamiento de parámetros y generación de nodos y conectividades.\n"
        "   - Asignación de propiedades y perfiles estructurales.\n\n"
        "3. Integración con STAAD.Pro:\n"
        "   - Exportación de comandos OpenSTAAD y generación de archivos compatibles (.std).\n"
        "   - Visualización 3D del modelo resultante."
    )
    doc.add_paragraph(diagrama)
    
    # Placeholder para las imágenes
    img_p = doc.add_paragraph()
    img_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    img_run = img_p.add_run("\n\n[ PEGA AQUÍ TUS IMÁGENES O CAPTURAS DEL FUNCIONAMIENTO DE FRAMEONE ]\n\n")
    img_run.font.color.rgb = RGBColor(128, 128, 128)
    
    doc.add_page_break()

    # --- CÓDIGO FUENTE ---
    def add_code_section(title_text, filepath, max_lines=450):
        add_heading(title_text, level=2)
        code_p = doc.add_paragraph()
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for i, line in enumerate(lines[:max_lines]):
                    clean_line = line.replace('\n', '').replace('\r', '').replace('\0', '')
                    run = code_p.add_run(clean_line + "\n")
                    run.font.name = 'Courier New' # Courier para el código, para que respete espacios y formato técnico
                    run.font.size = Pt(8)
        except Exception as e:
            code_p.add_run(f"Error leyendo {filepath}: {str(e)}")
            
    app_dir = "app"
    main_py = os.path.join(app_dir, "main.py")
    model_py = os.path.join(app_dir, "model.py")
    
    add_code_section("Muestra de Código - Interfaz de Usuario (Primeras páginas)", main_py, 450)
    doc.add_page_break()
    add_code_section("Muestra de Código - Motor Lógico (Últimas páginas)", model_py, 450)
    
    output_path = "INDAUTOR_Registro_FrameOne.docx"
    doc.save(output_path)
    print(f"Word generado exitosamente en: {output_path}")

if __name__ == "__main__":
    main()
