"""
Generador y exportador de Excel para el Catálogo de Conceptos.
Toma los datos procesados en la UI y los vuelca en la plantilla Formato.xlsx / Formato Ejemplo.xlsx.
"""

import os
import io
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

def export_catalogo_to_excel(catalogo_data, totals):
    """
    Genera un archivo Excel en memoria (BytesIO) con el formato oficial del Catálogo.
    """
    base_dir = os.path.dirname(__file__)
    formato_path = os.path.join(base_dir, "Formato.xlsx")
    
    if os.path.exists(formato_path):
        wb = openpyxl.load_workbook(formato_path)
        ws = wb.active
    else:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Catálogo"

    meta = catalogo_data["metadata"]
    area = totals["area_m2"]

    # 1. Rellenar Metadatos del Encabezado
    ws["B3"] = "PROYECTO:"
    ws["C3"] = meta.get("proyecto", "PROYECTO")
    
    ws["B4"] = "REFERENCIA:"
    ws["C4"] = meta.get("referencia", "")
    ws["I4"] = "Área:"
    ws["J4"] = round(area, 2)

    ws["B5"] = "UBICACIÓN:"
    ws["C5"] = meta.get("ubicacion", "")
    ws["D5"] = "FECHA:"
    ws["E5"] = meta.get("fecha", "")

    ws["B6"] = "AT'N  A:"
    ws["C6"] = meta.get("atn_a", "")
    ws["D6"] = "ELABORÓ:"
    ws["E6"] = meta.get("elaboro", "")

    # Encabezado de la tabla en fila 8
    ws["A8"] = "CANTIDAD"
    ws["B8"] = "UNIDAD"
    ws["C8"] = "DESCRIPCION"
    ws["D8"] = "PESO UNITARIO (kg)"
    ws["E8"] = "PESO TOTAL (kg)"
    ws["F8"] = "DENSIDAD (kg/m²)"

    # Estilos comunes
    font_bold = Font(name="Calibri", size=10, bold=True)
    font_normal = Font(name="Calibri", size=9)
    align_center = Alignment(horizontal="center", vertical="center")
    align_left = Alignment(horizontal="left", vertical="center")
    align_right = Alignment(horizontal="right", vertical="center")
    fill_header = PatternFill(start_color="E9ECEF", end_color="E9ECEF", fill_type="solid")

    row_idx = 9

    # Recorrer categorías y escribir filas
    cat_order = [
        ("Columnas & Anclajes", "columnas"),
        ("Armaduras", "armaduras"),
        ("Joists & Contraflambeo", "joists"),
        ("Contravientos", "contravientos"),
        ("Conexiones & Accesorios", "conexiones"),
        ("Cubierta & Fachada", "cubierta"),
        ("Mezanine & Varios", "mezanine")
    ]

    conceptos = catalogo_data["conceptos"]
    detalle = totals["detalle_items"]

    for cat_title, cat_key in cat_order:
        items = [it for it in conceptos.get(cat_key, []) if it.get("activo", True)]
        if not items:
            continue

        # Fila separadora de categoría
        ws.cell(row=row_idx, column=3, value=f"-- {cat_title.upper()} --")
        ws.cell(row=row_idx, column=3).font = font_bold
        ws.cell(row=row_idx, column=3).fill = fill_header
        row_idx += 1

        for item in items:
            cant = float(item.get("cant", 0.0))
            p_unit = float(item.get("p_unit", 0.0))
            p_tot = detalle.get(item["id"], round(cant * p_unit, 2))
            dens = round(p_tot / area, 3) if area > 0 else 0.0

            ws.cell(row=row_idx, column=1, value=cant).number_format = "#,##0.00" if cant % 1 != 0 else "#,##0"
            ws.cell(row=row_idx, column=2, value=item.get("unidad", "pza"))
            ws.cell(row=row_idx, column=3, value=item.get("descripcion", ""))
            ws.cell(row=row_idx, column=4, value=p_unit).number_format = "#,##0.00"
            ws.cell(row=row_idx, column=5, value=p_tot).number_format = "#,##0.00"
            ws.cell(row=row_idx, column=6, value=dens).number_format = "#,##0.000"

            ws.cell(row=row_idx, column=1).alignment = align_right
            ws.cell(row=row_idx, column=2).alignment = align_center
            ws.cell(row=row_idx, column=3).alignment = align_left
            ws.cell(row=row_idx, column=4).alignment = align_right
            ws.cell(row=row_idx, column=5).alignment = align_right
            ws.cell(row=row_idx, column=6).alignment = align_right

            for col in range(1, 7):
                ws.cell(row=row_idx, column=col).font = font_normal

            row_idx += 1

    # Placas y ángulos de conexión calculados (3%)
    if totals.get("peso_placas_conex", 0) > 0:
        ws.cell(row=row_idx, column=1, value=1).alignment = align_right
        ws.cell(row=row_idx, column=2, value="lote").alignment = align_center
        ws.cell(row=row_idx, column=3, value=f"Ángulos y placas de conexión ({meta.get('porc_conexiones', 3)}% est.)").alignment = align_left
        ws.cell(row=row_idx, column=4, value=totals["peso_placas_conex"]).number_format = "#,##0.00"
        ws.cell(row=row_idx, column=5, value=totals["peso_placas_conex"]).number_format = "#,##0.00"
        dens_cx = round(totals["peso_placas_conex"] / area, 3)
        ws.cell(row=row_idx, column=6, value=dens_cx).number_format = "#,##0.000"
        for col in range(1, 7):
            ws.cell(row=row_idx, column=col).font = font_normal
        row_idx += 1

    # Fila de Totales
    row_idx += 1
    ws.cell(row=row_idx, column=3, value="TOTAL PESO ACERO ESTRUCTURAL (kg):").alignment = align_right
    ws.cell(row=row_idx, column=3).font = font_bold
    ws.cell(row=row_idx, column=5, value=totals["peso_total_acero"]).number_format = "#,##0.00"
    ws.cell(row=row_idx, column=5).font = font_bold
    ws.cell(row=row_idx, column=6, value=totals["densidad_total"]).number_format = "#,##0.00"
    ws.cell(row=row_idx, column=6).font = font_bold

    # Autoajustar ancho de columnas clave
    ws.column_dimensions["A"].width = 12
    ws.column_dimensions["B"].width = 10
    ws.column_dimensions["C"].width = 65
    ws.column_dimensions["D"].width = 18
    ws.column_dimensions["E"].width = 18
    ws.column_dimensions["F"].width = 16

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer
