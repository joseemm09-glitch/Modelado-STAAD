import os
from fpdf import FPDF

class PDF(FPDF):
    def header(self):
        self.set_font("helvetica", "B", 12)
        self.cell(0, 10, "Software: Automatización de Modelado para STAAD.Pro", border=False, align="C")
        self.ln(20)
        
    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.cell(0, 10, f"Página {self.page_no()}", align="C")

def main():
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # --- CARÁTULA ---
    pdf.add_page()
    pdf.set_font("helvetica", "B", 24)
    pdf.ln(50)
    pdf.cell(0, 15, "Automatización de Modelado para STAAD.Pro", align="C")
    pdf.ln(10)
    pdf.set_font("helvetica", "", 16)
    pdf.cell(0, 10, "Autor: Jose Enrique ... (Completar con nombre real)", align="C")
    pdf.ln(10)
    pdf.cell(0, 10, "Año: 2026", align="C")
    pdf.ln(10)
    pdf.cell(0, 10, "Lugar: México", align="C")
    
    # --- FICHA TÉCNICA ---
    pdf.add_page()
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, "Ficha Técnica y Síntesis", ln=True)
    pdf.ln(5)
    pdf.set_font("helvetica", "", 12)
    sintesis = (
        "El presente software es una herramienta informática desarrollada con el objetivo principal "
        "de automatizar y optimizar el proceso de modelado geométrico y estructural de naves industriales. "
        "Su función central consiste en generar de manera automatizada y eficiente los modelos "
        "tridimensionales requeridos para su integración y análisis en el software de ingeniería estructural "
        "STAAD.Pro, reduciendo significativamente el tiempo de modelado manual y minimizando la posibilidad "
        "de errores operativos."
    )
    pdf.multi_cell(0, 10, sintesis)
    
    # --- DIAGRAMA DE ARQUITECTURA (Texto descriptivo para INDAUTOR) ---
    pdf.add_page()
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, "Diagrama de Arquitectura y Flujo", ln=True)
    pdf.ln(5)
    pdf.set_font("helvetica", "", 12)
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
    pdf.multi_cell(0, 10, diagrama)
    
    # --- CÓDIGO FUENTE ---
    def add_code_section(title, filepath, max_lines=450):
        pdf.add_page()
        pdf.set_font("helvetica", "B", 14)
        pdf.cell(0, 10, title, ln=True)
        pdf.ln(5)
        pdf.set_font("courier", "", 8)
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for i, line in enumerate(lines[:max_lines]):
                    # Remover caracteres nulos y evitar errores de codificación
                    clean_line = line.replace('\n', '').replace('\r', '').replace('\0', '')
                    # FPDF1/2 a veces tiene problemas con caracteres raros en latin-1 por defecto,
                    # así que los escapamos o ignoramos
                    clean_line = clean_line.encode("latin-1", "ignore").decode("latin-1")
                    pdf.cell(0, 4, clean_line, ln=True)
        except Exception as e:
            pdf.cell(0, 4, f"Error leyendo {filepath}: {str(e)}", ln=True)
            
    # Asumimos que los archivos están en app/
    app_dir = "app"
    main_py = os.path.join(app_dir, "main.py")
    model_py = os.path.join(app_dir, "model.py")
    
    add_code_section("Muestra de Código - Interfaz de Usuario (Primeras páginas)", main_py, 450)
    add_code_section("Muestra de Código - Motor Lógico (Últimas páginas)", model_py, 450)
    
    output_path = "INDAUTOR_Registro_STAAD.pdf"
    pdf.output(output_path)
    print(f"PDF generado exitosamente en: {output_path}")

if __name__ == "__main__":
    main()
