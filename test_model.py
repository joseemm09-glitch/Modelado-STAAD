import sys
import os
sys.path.append(os.path.abspath('app'))
from model import StaadModel

m = StaadModel(
    Larm_m=10.0, Ljoist_m=5.0, nBay=4, nSpan=3, HArmad_m=1.0, HLibre_m=6.0, numSubdiv=2,
    roof_type="1 Agua", slope_pct=10.0, add_wind_cols=False
)
m.generate()

print("nSpan =", m.nSpan)
for j in range(m.nSpan + 1):
    grp = f'_LARGUEROS_{j}'
    print(f"{grp}: {m.groups.get(grp, [])}")

print("_JOISTGRAL:", m.groups.get('_JOISTGRAL', []))
print("_JPUNTAL:", m.groups.get('_JPUNTAL', []))
