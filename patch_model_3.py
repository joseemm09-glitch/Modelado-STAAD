import re

with open('app/model.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_loop_logic = """            for i_val in i_range:
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
                            self.add_member(u_right, nodes_ci[oddK], grp_diag)
                            
            # Largueros (Corren en Z). Conectan los pórticos dentro de la extensión.
            for i_idx in range(len(i_range) - 1):
                z1 = i_range[i_idx] * self.Lz
                z2 = i_range[i_idx + 1] * self.Lz
                
                for k in range(ext_subdiv):
                    x_node = ext_x + k * L0_ext if is_left else ext_x - k * L0_ext
                    y_top = self.HtLibre + self.HtArmad + self.get_y_offset(x_node)
                    
                    nid_start = self.get_or_create_node(x_node, y_top, z1)
                    nid_end = self.get_or_create_node(x_node, y_top, z2)
                    mem = self.add_member(nid_start, nid_end, '_LARGUEROS')
                    self.groups.setdefault('_JOISTGRAL', []).append(mem)
                    self.rel_larg_start.append(mem)
                    self.rel_larg_end.append(mem)"""

new_loop_logic = """            ext_nodes_cs = {}
            for i_val in i_range:
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
                    ext_nodes_cs[(i_val, k)] = nid_cs
                    
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
                            self.add_member(u_right, nodes_ci[oddK], grp_diag)
                            
            # Largueros (Corren en Z) y Contravientos
            if ext_larm > self.Lz:
                chunks = max(2, round(ext_larm / self.Lz))
            else:
                chunks = 1
            k_points = [int(round(c * ext_subdiv / chunks)) for c in range(chunks + 1)]
            
            for i_idx in range(len(i_range) - 1):
                i_val1 = i_range[i_idx]
                i_val2 = i_range[i_idx + 1]
                
                # Largueros
                for k in range(ext_subdiv):
                    nid_start = ext_nodes_cs[(i_val1, k)]
                    nid_end = ext_nodes_cs[(i_val2, k)]
                    mem = self.add_member(nid_start, nid_end, '_LARGUEROS')
                    self.groups.setdefault('_JOISTGRAL', []).append(mem)
                    self.rel_larg_start.append(mem)
                    self.rel_larg_end.append(mem)
                
                # Contravientos
                for c in range(len(k_points) - 1):
                    k1 = k_points[c]
                    k2 = k_points[c+1]
                    
                    n1 = ext_nodes_cs[(i_val1, k1)]
                    n2 = ext_nodes_cs[(i_val2, k2)]
                    n3 = ext_nodes_cs[(i_val2, k1)]
                    n4 = ext_nodes_cs[(i_val1, k2)]
                    
                    self.add_member(n1, n2, '_CVH')
                    self.add_member(n3, n4, '_CVH')"""

content = content.replace(old_loop_logic, new_loop_logic)

with open('app/model.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Patch 3 successful!")
