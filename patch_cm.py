import re

with open('app/model.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update ext_larm in __init__
content = re.sub(
    r"self\.ext_larm = float\(kwargs\.get\('ext_larm', 15\.24\)\)",
    r"self.ext_larm = float(kwargs.get('ext_larm', 15.24)) * 100.0",
    content
)

# 2. Update y_shift_ext logic
content = re.sub(
    r"W_left = 2 \* \(self\.Lx_list\[0\] / self\.subdiv_list\[0\]\) if \(self\.ext_bl or self\.ext_tl\) else 0\.0\s+W_right = 2 \* \(self\.Lx_list\[-1\] / self\.subdiv_list\[-1\]\) if \(self\.ext_br or self\.ext_tr\) else 0\.0",
    r"W_left = self.ext_larm if (self.ext_bl or self.ext_tl) else 0.0\n            W_right = self.ext_larm if (self.ext_br or self.ext_tr) else 0.0",
    content
)

# 3. Update W_ext defaults (just to be safe, not strictly necessary since getattr uses self.ext_larm which is now set)
content = re.sub(
    r"getattr\(self, 'ext_larm', 15\.24\)",
    r"getattr(self, 'ext_larm', 1524.0)",
    content
)

with open('app/model.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched model.py")
