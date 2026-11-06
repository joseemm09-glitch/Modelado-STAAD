"""Genera el .std con los valores por defecto de la app (replica main.py) y reporta hash/lineas.

Uso: python docs/baseline/gen_baseline.py <salida.std>
El hash se calcula normalizando la linea con la fecha (datetime.now) del encabezado.
"""
import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "app"))
sys.path.insert(0, ROOT)

from model import StaadModel  # noqa: E402
from staad_writer import write_staad  # noqa: E402
import prediseno  # noqa: E402

model = StaadModel(
    15.24, 12.192, 7, 4, 1.30, 9.75, 10, "2 Aguas", 5.0, "FIXED",
    30.0, 100.0, 60.0, 86.0, 50.0, 78.0, 95.0,
    0.08, 2.0, None, None, True, 8.0, "Metálico", [], "1000000",
    dif_lengths=False, larm_ext1=15.24, larm_ext2=15.24,
    subdiv_ext1=10, subdiv_ext2=10, ext_bays_active=False,
    ext_bl=False, ext_br=False, ext_tl=False, ext_tr=False,
    ext_height_mode="Primer Entre-Eje completo", ext_larm=15.24,
    ext_subdiv=10, ext_depth=2, junta_constructiva_tipo="Ninguna",
    junta_max_dist_ft=600,
)
model.reglamento_cargas = "Chihuahua / IBC"
model.metodo_diseno = "ASD"
model.grupo_importancia = "B"
model.sismo_bidireccional = False

db_or = prediseno.cargar_base_datos_excel()
db_w = prediseno.PERFILES_W
name_to_staad = {p["nombre"]: p.get("nombre_staad", p["nombre"]) for p in db_or + db_w}
selected = {}
all_grps = {**prediseno.clasificar_columnas(model),
            **{k: v for k, v in model.groups.items() if k.startswith(("_CS", "_CI", "_CV"))}}
for g in all_grps:
    top = prediseno.predisenar_grupo(g, model, False)
    if top:
        nm = name_to_staad.get(top[0]["perfil"]["nombre"])
        if nm:
            selected[g] = nm

text = write_staad(model, selected_profiles=selected)
out = sys.argv[1] if len(sys.argv) > 1 else "baseline.std"
with open(out, "w", encoding="windows-1252", errors="replace", newline="") as f:
    f.write(text)

norm = re.sub(r"(?m)^(.*\b\d{1,2}-[A-Za-z]{3}-\d{2}\b.*)$", "<FECHA>", text)
print("nodos:", len(model.nodes), "miembros:", len(model.members))
print("grupos:", {k: len(v) for k, v in model.groups.items()})
print("perfiles:", selected)
print("lineas:", text.count("\n") + 1)
print("sha256_normalizado:", hashlib.sha256(norm.encode("utf-8")).hexdigest())
print("sha256_crudo:", hashlib.sha256(text.encode("utf-8")).hexdigest())
