import sys
sys.path.append('app')
from model import StaadModel
model = StaadModel(15.24, 1.5, 2, 1, 1, 8, 10, '2 Aguas', 10, 'PINNED', 20, 20, 0, 30, 20, 0, 0, 0.1, 2, 20, 20, True, 5, 'Tilt-Up', [], '1000000', dif_lengths=False, ext_bays_active=True, ext_bl=True, ext_tl=True, ext_br=True, ext_tr=True, ext_depth=2, ext_larm=15.24, ext_subdiv=10, ext_height_mode='Primer Entre-Eje completo')
print(f'Members: {len(model.members)}')
print(f'Plates: {len(model.plates)}')
print(f'ext_depth: {model.ext_depth}')
print(f'ext_larm: {model.ext_larm}')
print('Trusses (CI):', len(model.groups.get('_CI', [])))
print('Trusses (CS):', len(model.groups.get('_CS', [])))
print('Joists:', len(model.groups.get('_JOISTGRAL', [])))
