"""
Paquete Catalogo: Módulo independiente para el Catálogo de Conceptos de Naves Industriales STAAD.Pro.
"""

from .catalogo_ui import render_catalogo
from .catalogo_state import compute_catalogo_from_model, SOBER_PALETTE
from .staad_sync import get_staad_connection, sync_profiles_from_staad
from .excel_exporter import export_catalogo_to_excel

__all__ = [
    "render_catalogo",
    "compute_catalogo_from_model",
    "SOBER_PALETTE",
    "get_staad_connection",
    "sync_profiles_from_staad",
    "export_catalogo_to_excel"
]
