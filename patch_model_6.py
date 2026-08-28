import re

with open('app/model.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_joist = """        # Classify joists and set releases
        for mem_id in self.groups.get('_LARGUEROS', []):"""

new_joist = """        # Collect all joist members
        all_joists = []
        for j in range(self.nSpan):
            all_joists.extend(self.groups.get(f'_LARGUEROS_{j}', []))
        for mem_id in self.groups.get('_LARGUEROS', []):
            all_joists.append(mem_id)
            
        # Classify joists and set releases
        for mem_id in all_joists:"""

content = content.replace(old_joist, new_joist)

with open('app/model.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patch 6 successful!")
