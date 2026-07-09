import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'app'))
import prediseno

class DummyModel:
    def __init__(self):
        self.Larm_m = 15.24
        self.Ljoist_m = 12.20
        self.HtLibre = 9.75
        self.c_muerta = 30.0
        self.c_viva = 100.0
        self.v_barlovento = 86.0
        self.v_sotavento = 50.0
        self.v_laterales = 78.0
        self.add_wind_cols = False
        self.max_wind_dist = 8.0

m = DummyModel()
for g in ["C-1", "C-2", "C-3", "C-4"]:
    print(f"\n=== {g} ===")
    res = prediseno.predisenar_grupo(g, m)
    for r in res:
        print(f"{r['perfil']['nombre']} - Ratio: {r['ratio']:.3f} - Peso: {r['perfil']['peso']:.1f}")
