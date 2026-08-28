import re

with open('app/model.py', 'r', encoding='utf-8') as f:
    content = f.read()
    
joist_logic = """        # Collect all nodes connected to a wind bracing or horizontal truss member
        puntal_nodes = set()
        for mem_id in self.groups.get('_CVH', []):
            n1, n2 = self.members[mem_id]
            puntal_nodes.add(n1)
            puntal_nodes.add(n2)
        for mem_id in self.horizontal_truss_members:
            n1, n2 = self.members[mem_id]
            puntal_nodes.add(n1)
            puntal_nodes.add(n2)
            
        # Classify joists and set releases
        for mem_id in self.groups.get('_LARGUEROS', []):
            n1, n2 = self.members[mem_id]
            is_puntal = (n1 in puntal_nodes or n2 in puntal_nodes)
            if hasattr(self, 'wind_strut_members') and mem_id in self.wind_strut_members:
                is_puntal = True
            
            # Add to the correct group
            if is_puntal:
                self.groups.setdefault('_JPUNTAL', []).append(mem_id)
            else:
                self.groups.setdefault('_JOISTGRAL', []).append(mem_id)
                
            # Releases logic
            if is_puntal:
                # No release for JPUNTAL
                pass
            elif mem_id in self.split_purlin_first:
                self.rel_larg_start.append(mem_id)
            elif mem_id in self.split_purlin_last:
                self.rel_larg_end.append(mem_id)
            elif mem_id in self.split_purlin_middle:
                # No release
                pass
            else:
                self.rel_larg_start.append(mem_id)
                self.rel_larg_end.append(mem_id)"""
                
# Remove all occurrences!
content = content.replace(joist_logic + "\n\n", "")
content = content.replace(joist_logic + "\n", "")
content = content.replace(joist_logic, "")

# Insert exactly once at the end of generate()
insert_idx = content.rfind("        return self")

content = content[:insert_idx] + joist_logic + "\n\n" + content[insert_idx:]

with open('app/model.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patch 5 successful!")
