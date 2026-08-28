import re

with open('app/model.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_larg = """                    mem = self.add_member(nid_start, nid_end, '_LARGUEROS')"""
new_larg = """                    j_target = 0 if is_left else self.nSpan - 1
                    mem = self.add_member(nid_start, nid_end, f'_LARGUEROS_{j_target}')"""

content = content.replace(old_larg, new_larg)

with open('app/model.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Model larg patch successful!")
