import re

with open('app/model.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add PINNED logic at the end of generate()
pinned_logic = """
        if self.wall_type == "Tilt-Up":
            tiltup_base_nodes = set()
            for pid, (n1, n2, n3, n4) in self.plates.items():
                if self.nodes[n1][1] == 0.0: tiltup_base_nodes.add(n1)
                if self.nodes[n2][1] == 0.0: tiltup_base_nodes.add(n2)
                if self.nodes[n3][1] == 0.0: tiltup_base_nodes.add(n3)
                if self.nodes[n4][1] == 0.0: tiltup_base_nodes.add(n4)
            for nid in tiltup_base_nodes:
                if nid in self.base_nodes:
                    self.base_nodes.remove(nid)
                if nid not in self.wind_base_nodes:
                    self.wind_base_nodes.append(nid)

        return self"""

content = content.replace("        return self", pinned_logic)


# 2. Rewrite _generate_extensions truss logic
# Finding the block starting at `for i_val in i_range:` and ending before `# Largueros`
old_truss_logic = """            for i_val in i_range:
                z = i_val * self.Lz
                is_z_perimeter = (i_val == 0 or i_val == self.nBay)
                
                nodes_ci = []
                nodes_cs = []
                
                # Nodos del truss en el eje X, desde ext_x hasta base_x
                for k in range(ext_subdiv + 1):
                    x_node = ext_x + k * L0_ext if is_left else ext_x - k * L0_ext
                    y_bot = self.HtLibre + self.get_y_offset(x_node)
                    y_top = self.HtLibre + self.HtArmad + self.get_y_offset(x_node)
                    
                    if k == ext_subdiv:
                        # base_x
                        nid_ci = self.get_or_create_node(base_x, self.HtLibre + self.get_y_offset(base_x), z)
                        nid_cs = self.get_or_create_node(base_x, self.HtLibre + self.HtArmad + self.get_y_offset(base_x), z)
                    else:
                        nid_ci = self.get_or_create_node(x_node, y_bot, z)
                        nid_cs = self.get_or_create_node(x_node, y_top, z)
                        
                    nodes_ci.append(nid_ci)
                    nodes_cs.append(nid_cs)
                    
                # Generar Truss (solo en pórticos interiores, ya que en Z perimetral el Tilt-Up soporta todo)
                if not is_z_perimeter:
                    grp_ci = '_CI'
                    grp_cs = '_CS'
                    grp_mont = '_MONTANTES'
                    grp_diag = '_DIAG'
                    
                    for k in range(ext_subdiv):
                        self.add_member(nodes_ci[k], nodes_ci[k+1], grp_ci)
                        self.add_member(nodes_cs[k], nodes_cs[k+1], grp_cs)
                        self.add_member(nodes_ci[k], nodes_cs[k], grp_mont)
                        
                        if is_left:
                            self.add_member(nodes_cs[k+1], nodes_ci[k], grp_diag)
                        else:
                            self.add_member(nodes_ci[k+1], nodes_cs[k], grp_diag)"""

new_truss_logic = """            for i_val in i_range:
                z = i_val * self.Lz
                is_z_perimeter = (i_val == 0 or i_val == self.nBay or i_val == ext_depth or i_val == self.nBay - ext_depth)
                
                nodes_ci = {}
                nodes_cs = {}
                
                # Cuerda Superior
                for k in range(ext_subdiv + 1):
                    x_node = ext_x + k * L0_ext if is_left else ext_x - k * L0_ext
                    y_top = self.HtLibre + self.HtArmad + self.get_y_offset(x_node)
                    
                    if k == ext_subdiv:
                        nid_cs = self.get_or_create_node(base_x, self.HtLibre + self.HtArmad + self.get_y_offset(base_x), z)
                    else:
                        nid_cs = self.get_or_create_node(x_node, y_top, z)
                    nodes_cs[k] = nid_cs
                    
                # Cuerda Inferior (Solo en K impares + extremos)
                for k in [0] + list(range(1, ext_subdiv, 2)) + [ext_subdiv]:
                    x_node = ext_x + k * L0_ext if is_left else ext_x - k * L0_ext
                    y_bot = self.HtLibre + self.get_y_offset(x_node)
                    
                    if k == ext_subdiv:
                        nid_ci = self.get_or_create_node(base_x, self.HtLibre + self.get_y_offset(base_x), z)
                    else:
                        nid_ci = self.get_or_create_node(x_node, y_bot, z)
                    nodes_ci[k] = nid_ci
                    
                # Generar Truss (solo en pórticos interiores, ya que en Z perimetral el Tilt-Up soporta todo)
                if not is_z_perimeter:
                    grp_ci = '_CI'
                    grp_cs = '_CS'
                    grp_mont = '_MONTANTES'
                    grp_diag = '_DIAG'
                    
                    # _CS
                    for k in range(ext_subdiv):
                        self.add_member(nodes_cs[k], nodes_cs[k+1], grp_cs)
                        
                    # _CI
                    ci_keys = sorted(nodes_ci.keys())
                    for idx in range(len(ci_keys)-1):
                        self.add_member(nodes_ci[ci_keys[idx]], nodes_ci[ci_keys[idx+1]], grp_ci)
                        
                    # Montantes y Diagonales (Warren con verticales)
                    for t in range(1, (ext_subdiv // 2) + 1):
                        oddK = 2 * t - 1
                        # Montante
                        self.add_member(nodes_ci[oddK], nodes_cs[oddK], grp_mont)
                        # Diagonales
                        u_left = nodes_cs[2*(t-1)]
                        u_right = nodes_cs[2*t]
                        if is_left:
                            self.add_member(u_left, nodes_ci[oddK], grp_diag)
                            self.add_member(u_right, nodes_ci[oddK], grp_diag)
                        else:
                            self.add_member(u_left, nodes_ci[oddK], grp_diag)
                            self.add_member(u_right, nodes_ci[oddK], grp_diag)"""

content = content.replace(old_truss_logic, new_truss_logic)

with open('app/model.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Patch successful!")
