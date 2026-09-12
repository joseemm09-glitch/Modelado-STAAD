import sys
import os
import math

script_dir = os.path.dirname(os.path.abspath(__file__))
model_pre_path = os.path.join(script_dir, 'app', 'model_pre_marco_doble.py')
model_path = os.path.join(script_dir, 'app', 'model.py')

with open(model_pre_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Let's inspect line anchors
def find_line(pattern, start=0):
    for i in range(start, len(lines)):
        if pattern in lines[i]:
            return i
    raise ValueError(f"Pattern '{pattern}' not found after line {start}")

# 1. Groups definition
idx_grp = find_line("'_DIAG_SEC': []")
lines[idx_grp] = "            '_DIAG_SEC': [],\n            '_ARMADURA_MD': []\n"

# 2. Init Marco Doble setup
idx_init = find_line("self.col_heights = {}")
init_block = """        # Marco Doble / Juntas Constructivas
        self.junta_constructiva_tipo = kwargs.get('junta_constructiva_tipo', 'Ninguna')
        self.junta_max_dist_ft = float(kwargs.get('junta_max_dist_ft', 600.0))
        self.junta_max_dist_m = self.junta_max_dist_ft * 0.3048
        
        total_length_m = self.nBay * self.Ljoist_m
        self.has_marco_doble = (self.junta_constructiva_tipo == "Marco doble") and (total_length_m > self.junta_max_dist_m)
        self.joint_axes = []
        if self.has_marco_doble and self.nBay >= 2:
            num_segments = math.ceil(total_length_m / self.junta_max_dist_m)
            num_joints = num_segments - 1
            for k in range(1, num_joints + 1):
                target_i = int(round(k * self.nBay / (num_joints + 1)))
                target_i = max(1, min(self.nBay - 1, target_i))
                if target_i not in self.joint_axes:
                    self.joint_axes.append(target_i)
            self.joint_axes.sort()

        # Construir lista de marcos a lo largo de Z
        self.frames = []
        f_idx = 0
        for i in range(self.nBay + 1):
            if i in self.joint_axes:
                zA = i * self.Lz - 10.0
                self.frames.append({
                    'idx': f_idx,
                    'z': zA,
                    'orig_i': i,
                    'is_md': True,
                    'md_side': 'A',
                    'connect_to_next': False
                })
                f_idx += 1
                zB = i * self.Lz + 10.0
                self.frames.append({
                    'idx': f_idx,
                    'z': zB,
                    'orig_i': i,
                    'is_md': True,
                    'md_side': 'B',
                    'connect_to_next': True
                })
                f_idx += 1
            else:
                self.frames.append({
                    'idx': f_idx,
                    'z': i * self.Lz,
                    'orig_i': i,
                    'is_md': False,
                    'md_side': None,
                    'connect_to_next': True
                })
                f_idx += 1
        self.num_frames = len(self.frames)
        self.dummy_md_members = []
        
"""
lines.insert(idx_init, init_block)

code = "".join(lines)
with open(model_path, 'w', encoding='utf-8') as f:
    f.write(code)

print("Init patch ready.")
