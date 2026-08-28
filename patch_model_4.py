import re

with open('app/model.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Extract joist classification logic
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

content = content.replace(joist_logic, "")

# 2. Insert at the end of generate() before the return self
insert_target = """        if self.wall_type == "Tilt-Up":
            tiltup_base_nodes = set()"""

content = content.replace(insert_target, joist_logic + "\n\n" + insert_target)

# 3. Fix extensions joist logic (remove hardcoded _JOISTGRAL)
old_larg_logic = """                    mem = self.add_member(nid_start, nid_end, '_LARGUEROS')
                    self.groups.setdefault('_JOISTGRAL', []).append(mem)
                    self.rel_larg_start.append(mem)
                    self.rel_larg_end.append(mem)"""

new_larg_logic = """                    mem = self.add_member(nid_start, nid_end, '_LARGUEROS')"""

content = content.replace(old_larg_logic, new_larg_logic)

# 4. Add _COL to the extensions when not is_z_perimeter
old_col_logic = """                # Generar Truss (solo en pórticos interiores, ya que en Z perimetral el Tilt-Up soporta todo)
                if not is_z_perimeter:
                    grp_ci = '_CI'"""

new_col_logic = """                # Generar Truss (solo en pórticos interiores, ya que en Z perimetral el Tilt-Up soporta todo)
                if not is_z_perimeter:
                    # Columnas (Soportando la armadura interior de la extensión)
                    nid_base_ext = self.get_or_create_node(ext_x, 0.0, z)
                    self.add_member(nid_base_ext, nodes_ci[0], '_COL')
                    self.add_member(nodes_ci[0], nodes_cs[0], '_COL')
                    
                    nid_base_int = self.get_or_create_node(base_x, 0.0, z)
                    self.add_member(nid_base_int, nodes_ci[ext_subdiv], '_COL')
                    self.add_member(nodes_ci[ext_subdiv], nodes_cs[ext_subdiv], '_COL')
                    
                    grp_ci = '_CI'"""

content = content.replace(old_col_logic, new_col_logic)

with open('app/model.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Patch 4 successful!")
