import math

class StaadModel:
    def __init__(self, Larm_m, Ljoist_m, nBay, nSpan, HArmad_m, HLibre_m, numSubdiv, roof_type="Plana", slope_pct=0.0, support_type="FIXED", c_muerta=30.0, c_viva=100.0, c_granizo=60.0, v_barlovento=86.0, v_sotavento=50.0, v_laterales=78.0, v_succion=95.0, coef_sismico=0.08, ductilidad=2.0, cm_sismo=None, cv_sismo=None, add_wind_cols=False, max_wind_dist_m=8.0, wall_type="Metálico", sec_trusses_j=None, resorte_val="1000000", **kwargs):
        self.Larm_m = float(Larm_m)
        self.Ljoist_m = float(Ljoist_m)
        self.nBay = int(nBay)
        self.nSpan = int(nSpan)
        self.HArmad_m = float(HArmad_m)
        self.HLibre_m = float(HLibre_m)
        self.numSubdiv = int(numSubdiv)
        
        self.Larm_list = [self.Larm_m] * self.nSpan
        self.subdiv_list = [self.numSubdiv] * self.nSpan
        
        if kwargs.get('dif_lengths', False) and self.nSpan >= 2:
            self.Larm_list[0] = float(kwargs.get('larm_ext1', self.Larm_m))
            self.subdiv_list[0] = int(kwargs.get('subdiv_ext1', self.numSubdiv))
            if self.nSpan > 2:
                self.Larm_list[-1] = float(kwargs.get('larm_ext2', self.Larm_m))
                self.subdiv_list[-1] = int(kwargs.get('subdiv_ext2', self.numSubdiv))
            elif self.nSpan == 2:
                self.Larm_list[1] = float(kwargs.get('larm_ext2', self.Larm_m))
                self.subdiv_list[1] = int(kwargs.get('subdiv_ext2', self.numSubdiv))
                
        for s in self.subdiv_list:
            if s < 2 or s % 2 != 0:
                raise ValueError("Las subdivisiones deben ser un número par mayor o igual a 2.")

        self.roof_type = roof_type
        self.slope_pct = float(slope_pct)
        self.support_type = support_type
        self.resorte_val = resorte_val
        self.wall_type = wall_type
        
        self.ext_bays_active = kwargs.get('ext_bays_active', False)
        self.ext_bl = kwargs.get('ext_bl', False)
        self.ext_br = kwargs.get('ext_br', False)
        self.ext_tl = kwargs.get('ext_tl', False)
        self.ext_tr = kwargs.get('ext_tr', False)
        self.ext_height_mode = kwargs.get('ext_height_mode', "Primer Entre-Eje completo")
        self.ext_depth = int(kwargs.get('ext_depth', 1))
        self.ext_larm = float(kwargs.get('ext_larm', 15.24)) * 100.0
        self.ext_subdiv = int(kwargs.get('ext_subdiv', 10))
        
        self.sec_trusses_j = sec_trusses_j if sec_trusses_j else []
        if self.sec_trusses_j:
            import math
            min_n = self.Ljoist_m / 1.60
            n = math.ceil(min_n)
            if n % 2 != 0: n += 1
            self.numSubdiv_sec = int(max(2, n))
        else:
            self.numSubdiv_sec = 0
            
        self.c_muerta = float(c_muerta)
        self.c_viva = float(c_viva)
        self.c_granizo = float(c_granizo)
        
        self.v_barlovento = float(v_barlovento)
        self.v_sotavento = float(v_sotavento)
        self.v_laterales = float(v_laterales)
        self.v_succion = float(v_succion)
        
        self.coef_sismico = float(coef_sismico)
        self.ductilidad = float(ductilidad)
        self.cm_sismo = float(cm_sismo) if cm_sismo is not None else self.c_muerta
        self.cv_sismo = float(cv_sismo) if cv_sismo is not None else (self.c_viva * 0.25)
        self.seismic_v = self.coef_sismico / self.ductilidad
        
        self.add_wind_cols = bool(add_wind_cols)
        self.max_wind_dist_m = float(max_wind_dist_m)

        import math
        self.wind_col_N = 1
        if self.add_wind_cols and self.Ljoist_m > self.max_wind_dist_m:
            self.wind_col_N = math.ceil(self.Ljoist_m / self.max_wind_dist_m)
            
        self.wind_col_Z_M_list = []
        for l in self.Larm_list:
            if self.add_wind_cols and l > self.max_wind_dist_m:
                self.wind_col_Z_M_list.append(math.ceil(l / self.max_wind_dist_m))
            else:
                self.wind_col_Z_M_list.append(1)

        self.scale = 100.0
        self.Lx_list = [l * self.scale for l in self.Larm_list]
        self.Lz = self.Ljoist_m * self.scale
        self.HtArmad = self.HArmad_m * self.scale
        self.HtLibre = self.HLibre_m * self.scale
        self.total_width = sum(self.Lx_list)
        self.Lx = self.Lx_list[0] # Legacy fallback if needed outside generate
        
        self.y_shift_ext = 0.0
        if self.ext_bays_active and self.ext_height_mode == "Altura mínima en esquinas":
            slope = self.slope_pct / 100.0
            W_left = self.ext_larm if (self.ext_bl or self.ext_tl) else 0.0
            W_right = self.ext_larm if (self.ext_br or self.ext_tr) else 0.0
            
            if self.roof_type == "1 Agua":
                self.y_shift_ext = W_left * slope
            elif self.roof_type == "2 Aguas":
                self.y_shift_ext = max(W_left * slope, W_right * slope)
        
        self.col_trib_z = {}
        self.col_trib_x = {}
        self.node_seismic_loads = {}
        self.nodes = {}  # node_id: (x, y, z)
        self.members = {}  # member_id: (node1_id, node2_id)
        self.groups = {
            '_COL': [],
            '_COLVIENTO': [],
            '_CS': [],
            '_CI': [],
            '_CS_PERIM': [],
            '_CI_PERIM': [],
            '_MONTANTES': [],
            '_DIAG': [],
            '_MONTANTES_PERIM': [],
            '_DIAG_PERIM': [],
            '_LARGUEROS': [],
            '_CVH': [],
            '_JOISTGRAL': [],
            '_JPUNTAL': [],
            '_CS_SEC': [],
            '_CI_SEC': [],
            '_MONTANTES_SEC': [],
            '_DIAG_SEC': []
        }
        for j in range(self.nSpan + 1):
            self.groups[f"_LARGUEROS_{j}"] = []
        
        self.wind_cols = {
            'X0_CORNER': [], 'X0_INNER': [],
            'X0_WINDCOL': [],
            'XMAX_CORNER': [], 'XMAX_INNER': [],
            'XMAX_WINDCOL': [],
            'Z0_CORNER': [], 'Z0_INNER': [],
            'Z0_WINDCOL': [],
            'ZMAX_CORNER': [], 'ZMAX_INNER': [],
            'ZMAX_WINDCOL': []
        }
        
        self.seismic_nodes = []
        for _ in range(self.nSpan + 1):
            self.seismic_nodes.append({
                'corner': [],
                'edge_x': [],
                'edge_z': [],
                'interior': []
            })
            
        self.seismic_loads = []
        for j in range(self.nSpan + 1):
            if j == 0:
                L_trib = self.Larm_list[0] / 2
            elif j == self.nSpan:
                L_trib = self.Larm_list[-1] / 2
            else:
                L_trib = (self.Larm_list[j-1] + self.Larm_list[j]) / 2
            
            carga_sismo_kg_m2 = (self.c_muerta + self.cv_sismo)
            area_trib_esq = L_trib * (self.Ljoist_m / 2)
            area_trib_int = L_trib * self.Ljoist_m
            self.seismic_loads.append({
                'corner': carga_sismo_kg_m2 * area_trib_esq * self.coef_sismico,
                'edge_x': carga_sismo_kg_m2 * area_trib_esq * self.coef_sismico,
                'edge_z': carga_sismo_kg_m2 * area_trib_int * self.coef_sismico,
                'interior': carga_sismo_kg_m2 * area_trib_int * self.coef_sismico
            })
        
        self.rel_csci_start = []
        self.rel_csci_end = []
        self.rel_horiz_start = []
        self.rel_horiz_end = []
        self.rel_larg_start = []
        self.rel_larg_end = []
        self.rel_cs_sec_start = []
        self.rel_cs_sec_end = []
        self.rel_ci_sec_start = []
        self.rel_ci_sec_end = []
        self.rel_tiltup_start = []
        self.rel_tiltup_end = []
        self.plate_releases_j1_j4 = []
        self.plate_releases_j2_j3 = []
        self.release_end_fx = []
        self.horizontal_truss_members = []
        self.split_purlin_first = []
        self.split_purlin_last = []
        self.split_purlin_middle = []
        
        self.col_heights = {}
        self.ci_int = []
        self.ci_ly_groups = {}
        
        self.base_nodes = [] # Nodos en la base para asignar SUPPORTS FIXED
        self.wind_base_nodes = []
        self.plate_groups = {'X0': [], 'XMAX': [], 'Z0': [], 'ZMAX': []}

        self.node_id = 0
        self.mem_id = 0
        
        self.plates = {} # mem_id: (n1, n2, n3, n4)
        
        self.generate()

    def add_node(self, x, y, z, is_wind_base=False):
        self.node_id += 1
        self.nodes[self.node_id] = (x, y, z)
        if y == 0:
            if is_wind_base:
                self.wind_base_nodes.append(self.node_id)
            else:
                self.base_nodes.append(self.node_id)

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

        return self.node_id

    def add_plate(self, n1, n2, n3, n4):
        self.mem_id += 1
        self.plates[self.mem_id] = (n1, n2, n3, n4)

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

        return self.mem_id

    def add_member(self, n1, n2, group):
        self.mem_id += 1
        self.members[self.mem_id] = (n1, n2)
        if group in self.groups:
            self.groups[group].append(self.mem_id)

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

        return self.mem_id

    def get_upper_node(self, nL3, upperSub, i, j, k):
        if k == 0:
            return nL3[(i, j)]
        elif k == self.subdiv_list[j]:
            return nL3[(i, j + 1)]
        else:
            return upperSub[(i, j, k)]

    def add_ci_ly(self, mem_id, L0_local):
        ly_val = math.ceil(3 * L0_local)
        if ly_val not in self.ci_ly_groups:
            self.ci_ly_groups[ly_val] = []
        self.ci_ly_groups[ly_val].append(mem_id)

    def get_x(self, j):
        return sum(self.Lx_list[:j])

    def get_y_offset(self, global_x):
        slope = self.slope_pct / 100.0
        if self.roof_type == "1 Agua":
            return global_x * slope + self.y_shift_ext
        elif self.roof_type == "2 Aguas":
            return min(global_x, self.total_width - global_x) * slope + self.y_shift_ext

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

        return self.y_shift_ext



    def get_or_create_node(self, x, y, z):
        tol = 1e-4
        for nid, (nx, ny, nz) in self.nodes.items():
            if abs(nx - x) < tol and abs(ny - y) < tol and abs(nz - z) < tol:
                return nid

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

        return self.add_node(x, y, z)
        
    def _add_sec_truss_segment(self, j_span, top_start, top_end, bot_start, bot_end, base_z, L_segment, start_release, end_release):
        min_n = L_segment / (1.60 * self.scale)
        n = math.ceil(min_n)
        if n % 2 != 0: n += 1
        num_subdiv = int(max(2, n))
        L0_sec = L_segment / num_subdiv
        
        sec_upper = {0: top_start}
        for k in range(1, num_subdiv):
            zn = base_z + k * L0_sec
            xn = self.get_x(j_span)
            yn_roof = self.HtLibre + self.HtArmad + self.get_y_offset(xn)
            sec_upper[k] = self.get_or_create_node(xn, yn_roof, zn)
        sec_upper[num_subdiv] = top_end
        
        sec_lower = {}
        halfSub = num_subdiv // 2
        for t in range(1, halfSub + 1):
            oddK = 2 * t - 1
            zn = base_z + oddK * L0_sec
            xn = self.get_x(j_span)
            yn_bot = self.HtLibre + self.get_y_offset(xn)
            sec_lower[t] = self.get_or_create_node(xn, yn_bot, zn)
            
        # _CS_SEC
        prev = sec_upper[0]
        for k in range(1, num_subdiv + 1):
            nid = sec_upper[k]
            mid = self.add_member(prev, nid, '_CS_SEC')
            if k == 1 and start_release:
                self.rel_cs_sec_start.append(mid)
            if k == num_subdiv and end_release:
                self.rel_cs_sec_end.append(mid)
            prev = nid
            
        # _CI_SEC
        leftN = bot_start
        for t in range(1, halfSub + 1):
            nid = sec_lower[t]
            mid = self.add_member(leftN, nid, '_CI_SEC')
            if t == 1 and start_release:
                self.rel_ci_sec_start.append(mid)
            leftN = nid
        mid2 = self.add_member(leftN, bot_end, '_CI_SEC')
        if end_release:
            self.rel_ci_sec_end.append(mid2)
            
        # _MONTANTES_SEC
        for t in range(1, halfSub + 1):
            oddK = 2 * t - 1
            self.add_member(sec_lower[t], sec_upper[oddK], '_MONTANTES_SEC')
            
        # _DIAG_SEC
        for t in range(1, halfSub + 1):
            u_left = sec_upper[2 * (t - 1)]
            self.add_member(u_left, sec_lower[t], '_DIAG_SEC')
            u_right = sec_upper[2 * t]
            self.add_member(u_right, sec_lower[t], '_DIAG_SEC')

    def generate(self):
        # Data structures to store node references
        nL1 = {}
        nL2 = {}
        nL3 = {}
        upperSub = {}
        lowerInter = {}
        
        

        # --- Nivel 1 (Base) ---
        for j in range(self.nSpan + 1):
            for i in range(self.nBay + 1):
                x = self.get_x(j)
                y = 0.0
                z = i * self.Lz
                nL1[(i, j)] = self.add_node(x, y, z)

        # --- Nivel 2 (Eaves) ---
        for j in range(self.nSpan + 1):
            for i in range(self.nBay + 1):
                x = self.get_x(j)
                y = self.HtLibre + self.get_y_offset(x)
                z = i * self.Lz
                nL2[(i, j)] = self.add_node(x, y, z)

        # --- Nivel 3 (Ridge / Top) ---
        for j in range(self.nSpan + 1):
            for i in range(self.nBay + 1):
                x = self.get_x(j)
                y = self.HtLibre + self.HtArmad + self.get_y_offset(x)
                z = i * self.Lz
                nL3[(i, j)] = self.add_node(x, y, z)

        # --- Columnas (Niveles 1 -> 2 y 2 -> 3) ---
        for j in range(self.nSpan + 1):
            for i in range(self.nBay + 1):
                is_perimeter = (j == 0 or j == self.nSpan or i == 0 or i == self.nBay)
                trib_x = self.Ljoist_m / self.wind_col_N
                if j == 0:
                    trib_z = self.Larm_list[0] / self.wind_col_Z_M_list[0] / 2.0
                elif j == self.nSpan:
                    trib_z = self.Larm_list[-1] / self.wind_col_Z_M_list[-1] / 2.0
                else:
                    trib_z = (self.Larm_list[j-1] / self.wind_col_Z_M_list[j-1] / 2.0) + (self.Larm_list[j] / self.wind_col_Z_M_list[j] / 2.0)

                if self.wall_type == "Tilt-Up" and is_perimeter:
                    pass
                else:
                    col1 = self.add_member(nL1[(i, j)], nL2[(i, j)], '_COL')
                    col2 = self.add_member(nL2[(i, j)], nL3[(i, j)], '_COL')

                    if is_perimeter:
                        if i == 0 or i == self.nBay:
                            self.col_trib_z[col1] = trib_z
                            self.col_trib_z[col2] = trib_z
                            self.col_trib_x[col1] = trib_x / 2.0
                            self.col_trib_x[col2] = trib_x / 2.0
                        else:
                            self.col_trib_z[col1] = trib_z
                            self.col_trib_z[col2] = trib_z
                            self.col_trib_x[col1] = trib_x
                            self.col_trib_x[col2] = trib_x
                    
                    # Height calculation
                    x = self.get_x(j)
                    total_h = self.HtLibre + self.HtArmad + self.get_y_offset(x)
                    h_rounded = math.ceil(total_h)
                    if h_rounded not in self.col_heights:
                        self.col_heights[h_rounded] = []
                    self.col_heights[h_rounded].extend([col1, col2])
                    
                    # Face X0
                    if j == 0:
                        if i == 0 or i == self.nBay:
                            self.wind_cols['X0_CORNER'].extend([col1, col2])
                        else:
                            self.wind_cols['X0_INNER'].extend([col1, col2])
                    
                    # Face XMAX
                    if j == self.nSpan:
                        if i == 0 or i == self.nBay:
                            self.wind_cols['XMAX_CORNER'].extend([col1, col2])
                        else:
                            self.wind_cols['XMAX_INNER'].extend([col1, col2])
                            
                    # Face Z0
                    if i == 0:
                        if j == 0 or j == self.nSpan:
                            self.wind_cols['Z0_CORNER'].extend([col1, col2])
                        else:
                            self.wind_cols['Z0_INNER'].extend([col1, col2])
                            
                    # Face ZMAX
                    if i == self.nBay:
                        if j == 0 or j == self.nSpan:
                            self.wind_cols['ZMAX_CORNER'].extend([col1, col2])
                        else:
                            self.wind_cols['ZMAX_INNER'].extend([col1, col2])
                
                
                # Clasificación para Sismo en nodos superiores (Nivel 3)
                top_node = nL3[(i, j)]
                is_x_edge = (j == 0 or j == self.nSpan)
                is_z_edge = (i == 0 or i == self.nBay)
                
                if is_x_edge and is_z_edge:
                    self.seismic_nodes[j]['corner'].append(top_node)
                elif is_x_edge and not is_z_edge:
                    self.seismic_nodes[j]['edge_z'].append(top_node) # Borde en X (j=0, j=nSpan), varía i (dirección Z) -> Su área tributaria se reduce en Z, oh wait.
                    # Corrección: si estamos en el borde X (j=0 o j=nSpan), el ancho en X es Larm_m/2. 
                    # Entonces corresponde a edge_z (donde usamos Larm_m/2 * Ljoist_m). 
                    # El nombre edge_z aquí significa que el área tributaria se basa en el perímetro en Z. 
                    # Vamos a llamarlo correctamente según la fórmula:
                    # Si is_x_edge, estamos en j=0 o j=nSpan. Aquí el ancho tributario en X es ((self.Lx_list[j] / self.scale / 2)) = Larm_m/2. 
                    # En Z es completo = Ljoist_m.
                    # a_edge_z era (self.Larm_m / 2.0) * self.Ljoist_m. Esto coincide.
                elif is_z_edge and not is_x_edge:
                    self.seismic_nodes[j]['edge_x'].append(top_node) # Borde en Z (i=0, i=nBay).
                else:
                    self.seismic_nodes[j]['interior'].append(top_node)

                trib_z_sismo = trib_z
                a_node = trib_x * trib_z_sismo
                w_total = self.cm_sismo + self.cv_sismo
                seismic_load = math.ceil((a_node * w_total * self.seismic_v) * 10) / 10.0
                self.node_seismic_loads[top_node] = seismic_load


        # --- Cuerda Superior (Nivel 3) e intermedios ---
        for i in range(self.nBay + 1):
            for j in range(self.nSpan):
                prev = nL3[(i, j)]
                is_first = True
                for k in range(1, self.subdiv_list[j]):
                    xn = self.get_x(j) + k * ((self.Lx_list[j] / self.subdiv_list[j]))
                    yn = self.HtLibre + self.HtArmad + self.get_y_offset(xn)
                    zn = i * self.Lz
                    nid = self.add_node(xn, yn, zn)
                    upperSub[(i, j, k)] = nid
                    
                    if not (self.wall_type == "Tilt-Up" and (i == 0 or i == self.nBay)):
                        grp = '_CS_PERIM' if (j == 0 or j == self.nSpan - 1) else '_CS'
                        mid = self.add_member(prev, nid, grp)
                        if is_first:
                            self.rel_csci_start.append(mid)
                            is_first = False
                    prev = nid
                if not (self.wall_type == "Tilt-Up" and (i == 0 or i == self.nBay)):
                    grp = '_CS_PERIM' if (j == 0 or j == self.nSpan - 1) else '_CS'
                    mid2 = self.add_member(prev, nL3[(i, j + 1)], grp)
                    self.rel_csci_end.append(mid2)

        # --- Cuerda Inferior (Nivel 2) ---
        for i in range(self.nBay + 1):
            for j in range(self.nSpan):
                L0_local = (self.Lx_list[j] / self.subdiv_list[j])
                baseX = self.get_x(j)
                z2 = i * self.Lz
                leftN = nL2[(i, j)]

                for t in range(1, (self.subdiv_list[j] // 2) + 1):
                    oddK = 2 * t - 1
                    x = baseX + oddK * L0_local
                    yn = self.HtLibre + self.get_y_offset(x)
                    nid = self.add_node(x, yn, z2)
                    lowerInter[(i, j, t)] = nid
                    
                    if not (self.wall_type == "Tilt-Up" and (i == 0 or i == self.nBay)):
                        grp = '_CI_PERIM' if (j == 0 or j == self.nSpan - 1) else '_CI'
                        mid = self.add_member(leftN, nid, grp)
                        if t == 1:
                            self.rel_csci_start.append(mid)
                        else:
                            self.ci_int.append(mid)
                            self.add_ci_ly(mid, L0_local)
                    leftN = nid

                if not (self.wall_type == "Tilt-Up" and (i == 0 or i == self.nBay)):
                    grp = '_CI_PERIM' if (j == 0 or j == self.nSpan - 1) else '_CI'
                    mid2 = self.add_member(leftN, nL2[(i, j + 1)], grp)
                    self.rel_csci_end.append(mid2)

        # --- Montantes ---
        for i in range(self.nBay + 1):
            if self.wall_type == "Tilt-Up" and (i == 0 or i == self.nBay):
                continue
            for j in range(self.nSpan):
                grp = '_MONTANTES_PERIM' if (j == 0 or j == self.nSpan - 1) else '_MONTANTES'
                for t in range(1, (self.subdiv_list[j] // 2) + 1):
                    oddK = 2 * t - 1
                    self.add_member(lowerInter[(i, j, t)], upperSub[(i, j, oddK)], grp)

        # --- Diagonales (V) ---
        for i in range(self.nBay + 1):
            if self.wall_type == "Tilt-Up" and (i == 0 or i == self.nBay):
                continue
            for j in range(self.nSpan):
                grp = '_DIAG_PERIM' if (j == 0 or j == self.nSpan - 1) else '_DIAG'
                for t in range(1, (self.subdiv_list[j] // 2) + 1):
                    # izquierda
                    u_left = self.get_upper_node(nL3, upperSub, i, j, 2 * (t - 1))
                    self.add_member(u_left, lowerInter[(i, j, t)], grp)
                    # derecha
                    u_right = self.get_upper_node(nL3, upperSub, i, j, 2 * t)
                    self.add_member(u_right, lowerInter[(i, j, t)], grp)

        # --- Largueros ---
        if self.nBay >= 1:
            for j in range(self.nSpan + 1):
                has_sec_truss = (j in self.sec_trusses_j)
                is_wind_col_axis = (self.add_wind_cols and self.wind_col_N > 1 and (j == 0 or j == self.nSpan) and self.wall_type != "Tilt-Up")
                for i in range(self.nBay):
                    if is_wind_col_axis:
                        # Split larguero and create wind columns and horizontal wind trusses
                        N = self.wind_col_N
                        
                        # Initialize nodes arrays for this bay segment
                        A = [None] * (N + 1)
                        B = [None] * (N + 1)
                        
                        A[0] = nL3[(i, j)]
                        A[N] = nL3[(i + 1, j)]
                        
                        # Generate intermediate wind columns and horizontal truss nodes/struts
                        for k in range(1, N):
                            x = self.get_x(j)
                            y = self.HtLibre + self.HtArmad + self.get_y_offset(x)
                            z = (i + k / N) * self.Lz
                            
                            nid_roof = self.add_node(x, y, z)
                            nid_base = self.add_node(x, 0.0, z, is_wind_base=True)
                            
                            col_wind = self.add_member(nid_base, nid_roof, '_COLVIENTO')
                            
                            trib_x = self.Ljoist_m / self.wind_col_N
                            self.col_trib_x[col_wind] = trib_x
                            
                            if j == 0:
                                self.wind_cols['X0_WINDCOL'].append(col_wind)
                            else:
                                self.wind_cols['XMAX_WINDCOL'].append(col_wind)
                                
                            A[k] = nid_roof
                            
                            # Generate horizontal truss node
                            span_idx = 0 if j == 0 else self.nSpan - 1
                            L0_local = self.Lx_list[span_idx] / self.subdiv_list[span_idx]
                            x_next = L0_local if j == 0 else (self.total_width - L0_local)
                            y_next = self.HtLibre + self.HtArmad + self.get_y_offset(x_next)
                            
                            nid_new = self.get_or_create_node(x_next, y_next, z)
                            B[k] = nid_new
                            
                            # Strut (Puntal horizontal)
                            mem_strut = self.add_member(nid_roof, nid_new, None)
                            self.horizontal_truss_members.append(mem_strut)
                            self.rel_horiz_start.append(mem_strut)
                            self.rel_horiz_end.append(mem_strut)
                            
                        # Connect horizontal truss diagonals
                        for p in range(N):
                            if p + 1 < N:
                                diag1 = self.add_member(A[p], B[p+1], None)
                                self.horizontal_truss_members.append(diag1)
                                self.rel_horiz_start.append(diag1)
                                self.rel_horiz_end.append(diag1)
                            if p > 0:
                                diag2 = self.add_member(B[p], A[p+1], None)
                                self.horizontal_truss_members.append(diag2)
                                self.rel_horiz_start.append(diag2)
                                self.rel_horiz_end.append(diag2)
                            
                        # Add the perimetric purlin (larguero) segments OR secondary truss segments
                        baseZ = i * self.Lz
                        segment_length = self.Lz / N
                        for p in range(N):
                            if has_sec_truss:
                                xn = self.get_x(j)
                                yn_bot = self.HtLibre + self.get_y_offset(xn)
                                
                                bot_start = nL2[(i, j)] if p == 0 else self.get_or_create_node(xn, yn_bot, baseZ + p * segment_length)
                                bot_end = nL2[(i+1, j)] if p == N - 1 else self.get_or_create_node(xn, yn_bot, baseZ + (p + 1) * segment_length)
                                
                                start_rel = True
                                end_rel = True
                                
                                self._add_sec_truss_segment(j, A[p], A[p+1], bot_start, bot_end, baseZ + p * segment_length, segment_length, start_rel, end_rel)
                            else:
                                mem_id = self.add_member(A[p], A[p+1], f'_LARGUEROS_{j}')
                                if p == 0:
                                    self.split_purlin_first.append(mem_id)
                                elif p == N - 1:
                                    self.split_purlin_last.append(mem_id)
                                else:
                                    self.split_purlin_middle.append(mem_id)
                    elif has_sec_truss:
                        # Secondary truss on interior axis without wind columns
                        baseZ = i * self.Lz
                        start_rel = True
                        end_rel = True
                        self._add_sec_truss_segment(j, nL3[(i, j)], nL3[(i + 1, j)], nL2[(i, j)], nL2[(i + 1, j)], baseZ, self.Lz, start_rel, end_rel)
                    else:
                        # Standard larguero
                        self.add_member(nL3[(i, j)], nL3[(i + 1, j)], f'_LARGUEROS_{j}')
            
            for j in range(self.nSpan):
                for k in range(1, self.subdiv_list[j]):
                    is_segundo = (j == 0 and k == 1)
                    is_penultimo = (j == self.nSpan - 1 and k == self.subdiv_list[j] - 1)
                    is_wind_strut = self.add_wind_cols and self.wind_col_N > 1 and (is_segundo or is_penultimo) and self.wall_type != "Tilt-Up"
                    for i in range(self.nBay):
                        if is_wind_strut:
                            N = self.wind_col_N
                            L0_local = self.Lx_list[j] / self.subdiv_list[j]
                            x = L0_local if is_segundo else (self.total_width - L0_local)
                            y = self.HtLibre + self.HtArmad + self.get_y_offset(x)
                            
                            A = [None] * (N + 1)
                            A[0] = upperSub[(i, j, k)]
                            A[N] = upperSub[(i + 1, j, k)]
                            for p in range(1, N):
                                z = (i + p / N) * self.Lz
                                A[p] = self.get_or_create_node(x, y, z)
                                
                            for p in range(N):
                                mid = self.add_member(A[p], A[p+1], f'_LARGUEROS_{j}')
                                if not hasattr(self, 'wind_strut_members'):
                                    self.wind_strut_members = []
                                self.wind_strut_members.append(mid)
                        else:
                            self.add_member(upperSub[(i, j, k)], upperSub[(i + 1, j, k)], f'_LARGUEROS_{j}')

        # --- Contravientos Horizontales (_CV) ---
        if self.nBay >= 1 and self.nSpan >= 1:
            for i in range(self.nBay):
                for j in range(self.nSpan):
                    is_perimeter = (i == 0) or (i == self.nBay - 1) or (j == 0) or (j == self.nSpan - 1)
                    
                    if not is_perimeter:
                        # Patrón interior: alternar desde el centro hacia afuera
                        if self.nBay % 2 != 0:
                            if i % 2 != 0:
                                continue
                        else:
                            # Si es par, empezar con 2 cruces al centro y alternar hacia los extremos
                            c1 = self.nBay // 2 - 1
                            c2 = self.nBay // 2
                            if i <= c1:
                                d = c1 - i
                            else:
                                d = i - c2
                                
                            if d % 2 != 0:
                                continue
                            
                    # Subdivisión de cruces (buscando ~45° y obligando paso por cumbrera si aplica)
                    if self.roof_type == "2 Aguas":
                        half_sub = (self.subdiv_list[j] // 2)
                        half_lx = (self.Lx_list[j] / 2.0)
                        chunks_half = max(1, round(half_lx / self.Lz))
                        
                        left_pts = [int(round(c * half_sub / chunks_half)) for c in range(chunks_half)]
                        right_pts = [half_sub + int(round(c * half_sub / chunks_half)) for c in range(chunks_half + 1)]
                        k_points = left_pts + right_pts
                    else:
                        if self.Lx_list[j] > self.Lz:
                            chunks = max(2, round(self.Lx_list[j] / self.Lz))
                        else:
                            chunks = 1
                        k_points = [int(round(c * self.subdiv_list[j] / chunks)) for c in range(chunks + 1)]
                    
                    for c in range(len(k_points) - 1):
                        k1 = k_points[c]
                        k2 = k_points[c+1]
                        
                        n1 = self.get_upper_node(nL3, upperSub, i, j, k1)
                        n2 = self.get_upper_node(nL3, upperSub, i+1, j, k2)
                        
                        n3 = self.get_upper_node(nL3, upperSub, i+1, j, k1)
                        n4 = self.get_upper_node(nL3, upperSub, i, j, k2)
                        
                        self.add_member(n1, n2, '_CVH')
                        self.add_member(n3, n4, '_CVH')

        # --- Columnas de Viento en Cabeceras (Eje Z primero y último) ---
        if self.add_wind_cols and any(w > 1 for w in self.wind_col_Z_M_list):
            for i in [0, self.nBay]:
                if self.wall_type == "Tilt-Up":
                    continue
                for j in range(self.nSpan):
                    if self.wind_col_Z_M_list[j] <= 1:
                        continue
                    # Existing nodes on Cuerda Inferior in this span j and bay i
                    ci_nodes_in_span = []
                    # 1. Start node
                    ci_nodes_in_span.append((nL2[(i, j)], self.get_x(j)))
                    # 2. Intermediate lowerInter nodes
                    L0 = self.Lx_list[j] / self.subdiv_list[j]
                    for t in range(1, (self.subdiv_list[j] // 2) + 1):
                        oddK = 2 * t - 1
                        x_coord = self.get_x(j) + oddK * L0
                        if (i, j, t) in lowerInter:
                            ci_nodes_in_span.append((lowerInter[(i, j, t)], x_coord))
                    # 3. End node
                    ci_nodes_in_span.append((nL2[(i, j+1)], self.get_x(j+1)))
                    
                    # For each wind column position
                    for k in range(1, self.wind_col_Z_M_list[j]):
                        x_wind = self.get_x(j) + k * ((self.Lx_list[j] / self.wind_col_Z_M_list[j]))
                        
                        # Find the closest existing node on the Cuerda Inferior
                        closest_node, x_node = min(ci_nodes_in_span, key=lambda node_info: abs(node_info[1] - x_wind))
                        
                        # Only add wind column if the closest node is not a main column (i.e. not at j*Lx or (j+1)*Lx)
                        if closest_node not in [nL2[(i, j)], nL2[(i, j+1)]]:
                            # Create base node at ground level (y=0) at x_node
                            nid_base = self.add_node(x_node, 0.0, i * self.Lz, is_wind_base=True)
                            
                            col_wind = self.add_member(nid_base, closest_node, '_COLVIENTO')
                            
                            trib_z = self.Lx_list[j] / self.wind_col_Z_M_list[j]
                            self.col_trib_z[col_wind] = trib_z
                            
                            # Release at the top: MY, MZ, FX
                            self.release_end_fx.append(col_wind)
                            
                            # Classify for wind loading
                            if i == 0:
                                self.wind_cols['Z0_WINDCOL'].append(col_wind)
                            else:
                                self.wind_cols['ZMAX_WINDCOL'].append(col_wind)

        # Collect all nodes connected to a wind bracing or horizontal truss member
        puntal_nodes = set()
        for mem_id in self.groups.get('_CVH', []):
            n1, n2 = self.members[mem_id]
            puntal_nodes.add(n1)
            puntal_nodes.add(n2)
        for mem_id in self.horizontal_truss_members:
            n1, n2 = self.members[mem_id]
            puntal_nodes.add(n1)
            puntal_nodes.add(n2)
            
        # Collect all joist members
        all_joists = []
        for j in range(self.nSpan + 1):
            all_joists.extend(self.groups.get(f'_LARGUEROS_{j}', []))
        for mem_id in self.groups.get('_LARGUEROS', []):
            all_joists.append(mem_id)
            
        # Classify joists and set releases
        for mem_id in all_joists:
            n1, n2 = self.members[mem_id]
            is_puntal = (n1 in puntal_nodes or n2 in puntal_nodes)
            if hasattr(self, 'wind_strut_members') and mem_id in self.wind_strut_members:
                is_puntal = True
            
            # Add to the correct group
            if is_puntal:
                self.groups['_JPUNTAL'].append(mem_id)
            else:
                self.groups['_JOISTGRAL'].append(mem_id)
                
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
                self.rel_larg_end.append(mem_id)
                
        # --- Generar Bahías de Extensión ---
        self._generate_extensions()

        # --- Generación de Placas para Tilt-Up ---
        if self.wall_type == "Tilt-Up":
            # 1. Caras Z=0 y Z=ZMAX (A lo largo de X)
            for i in [0, self.nBay]:
                is_front = (i == 0)
                ext_left = self.ext_bl if is_front else self.ext_tl
                ext_right = self.ext_br if is_front else self.ext_tr
                
                if getattr(self, 'ext_bays_active', False) and ext_left:
                    baseZ = i * self.Lz
                    W_ext = getattr(self, 'ext_larm', 1524.0)
                    Nx = getattr(self, 'ext_subdiv', 10)
                    step_x = W_ext / Nx
                    for k in range(Nx):
                        xn1 = -W_ext + k * step_x
                        xn2 = -W_ext + (k + 1) * step_x
                        
                        yn_bot1 = self.HtLibre + self.get_y_offset(xn1)
                        yn_top1 = self.HtLibre + self.HtArmad + self.get_y_offset(xn1)
                        yn_bot2 = self.HtLibre + self.get_y_offset(xn2)
                        yn_top2 = self.HtLibre + self.HtArmad + self.get_y_offset(xn2)
                        
                        n_b1 = self.get_or_create_node(xn1, 0.0, baseZ)
                        n_b2 = self.get_or_create_node(xn2, 0.0, baseZ)
                        n_ci1 = self.get_or_create_node(xn1, yn_bot1, baseZ)
                        n_ci2 = self.get_or_create_node(xn2, yn_bot2, baseZ)
                        n_cs1 = self.get_or_create_node(xn1, yn_top1, baseZ)
                        n_cs2 = self.get_or_create_node(xn2, yn_top2, baseZ)
                        
                        p1 = self.add_plate(n_b1, n_b2, n_ci2, n_ci1)
                        p2 = self.add_plate(n_ci1, n_ci2, n_cs2, n_cs1)
                        group_key = 'Z0' if is_front else 'ZMAX'
                        self.plate_groups[group_key].extend([p1, p2])
                
                for j in range(self.nSpan):
                    baseZ = i * self.Lz
                    # En estas caras, generamos 2 placas por cada separación de la armadura
                    for k in range(self.subdiv_list[j]):
                        xn1 = self.get_x(j) + k * ((self.Lx_list[j] / self.subdiv_list[j]))
                        xn2 = self.get_x(j) + (k + 1) * ((self.Lx_list[j] / self.subdiv_list[j]))
                        
                        yn_bot1 = self.HtLibre + self.get_y_offset(xn1)
                        yn_top1 = self.HtLibre + self.HtArmad + self.get_y_offset(xn1)
                        
                        yn_bot2 = self.HtLibre + self.get_y_offset(xn2)
                        yn_top2 = self.HtLibre + self.HtArmad + self.get_y_offset(xn2)
                        
                        # Nodos inferiores en y=0
                        n_b1 = self.get_or_create_node(xn1, 0.0, baseZ)
                        n_b2 = self.get_or_create_node(xn2, 0.0, baseZ)
                        
                        # Nodos en CI
                        n_ci1 = self.get_or_create_node(xn1, yn_bot1, baseZ)
                        n_ci2 = self.get_or_create_node(xn2, yn_bot2, baseZ)
                        
                        # Nodos en CS
                        n_cs1 = self.get_or_create_node(xn1, yn_top1, baseZ)
                        n_cs2 = self.get_or_create_node(xn2, yn_top2, baseZ)
                        
                        # Placa Inferior (y=0 a CI)
                        p1 = self.add_plate(n_b1, n_b2, n_ci2, n_ci1)
                        
                        # Placa Superior (CI a CS)
                        p2 = self.add_plate(n_ci1, n_ci2, n_cs2, n_cs1)
                        
                        group_key = 'Z0' if i == 0 else 'ZMAX'
                        self.plate_groups[group_key].extend([p1, p2])
                        
                        # Nodos base requieren soporte PINNED
                        if n_b1 not in self.wind_base_nodes:
                            self.wind_base_nodes.append(n_b1)
                        if n_b2 not in self.wind_base_nodes:
                            self.wind_base_nodes.append(n_b2)

                if getattr(self, 'ext_bays_active', False) and ext_right:
                    baseZ = i * self.Lz
                    W_ext = getattr(self, 'ext_larm', 1524.0)
                    Nx = getattr(self, 'ext_subdiv', 10)
                    step_x = W_ext / Nx
                    for k in range(Nx):
                        xn1 = self.total_width + k * step_x
                        xn2 = self.total_width + (k + 1) * step_x
                        
                        yn_bot1 = self.HtLibre + self.get_y_offset(xn1)
                        yn_top1 = self.HtLibre + self.HtArmad + self.get_y_offset(xn1)
                        yn_bot2 = self.HtLibre + self.get_y_offset(xn2)
                        yn_top2 = self.HtLibre + self.HtArmad + self.get_y_offset(xn2)
                        
                        n_b1 = self.get_or_create_node(xn1, 0.0, baseZ)
                        n_b2 = self.get_or_create_node(xn2, 0.0, baseZ)
                        n_ci1 = self.get_or_create_node(xn1, yn_bot1, baseZ)
                        n_ci2 = self.get_or_create_node(xn2, yn_bot2, baseZ)
                        n_cs1 = self.get_or_create_node(xn1, yn_top1, baseZ)
                        n_cs2 = self.get_or_create_node(xn2, yn_top2, baseZ)
                        
                        p1 = self.add_plate(n_b1, n_b2, n_ci2, n_ci1)
                        p2 = self.add_plate(n_ci1, n_ci2, n_cs2, n_cs1)
                        group_key = 'Z0' if is_front else 'ZMAX'
                        self.plate_groups[group_key].extend([p1, p2])

            # 2. Caras X=0 y X=XMAX (A lo largo de Z)
            for j in [0, self.nSpan]:
                baseX = self.get_x(j)
                yn_bot = self.HtLibre + self.get_y_offset(baseX)
                yn_top = self.HtLibre + self.HtArmad + self.get_y_offset(baseX)
                
                is_left = (j == 0)
                
                for i in range(self.nBay):
                    is_ext = False
                    if getattr(self, 'ext_bays_active', False):
                        depth = getattr(self, 'ext_depth', 1)
                        if is_left and i < depth and self.ext_bl: is_ext = True
                        elif is_left and i >= self.nBay - depth and self.ext_tl: is_ext = True
                        elif not is_left and i < depth and self.ext_br: is_ext = True
                        elif not is_left and i >= self.nBay - depth and self.ext_tr: is_ext = True
                    
                    if is_ext:
                        depth = getattr(self, 'ext_depth', 1)
                        W_ext = getattr(self, 'ext_larm', 1524.0)
                        Nx = getattr(self, 'ext_subdiv', 10)
                        ext_x = baseX - W_ext if is_left else baseX + W_ext
                        
                        yn_ext_bot = self.HtLibre + self.get_y_offset(ext_x)
                        yn_ext_top = self.HtLibre + self.HtArmad + self.get_y_offset(ext_x)
                        
                        Nz = math.ceil(self.Ljoist_m / 4.0)
                        step_z = self.Lz / Nz
                        
                        for nz in range(Nz):
                            zn1 = i * self.Lz + nz * step_z
                            zn2 = i * self.Lz + (nz + 1) * step_z
                            
                            n_b1 = self.get_or_create_node(ext_x, 0.0, zn1)
                            n_b2 = self.get_or_create_node(ext_x, 0.0, zn2)
                            n_ci1 = self.get_or_create_node(ext_x, yn_ext_bot, zn1)
                            n_ci2 = self.get_or_create_node(ext_x, yn_ext_bot, zn2)
                            n_cs1 = self.get_or_create_node(ext_x, yn_ext_top, zn1)
                            n_cs2 = self.get_or_create_node(ext_x, yn_ext_top, zn2)
                            
                            p1 = self.add_plate(n_b1, n_b2, n_ci2, n_ci1)
                            p2 = self.add_plate(n_ci1, n_ci2, n_cs2, n_cs1)
                            group_key = 'X0' if is_left else 'XMAX'
                            self.plate_groups[group_key].extend([p1, p2])
                            
                        # Return wall (Inner Z face): only if this is the innermost bay of the extension
                        is_front = (i < depth)
                        if (is_front and i == depth - 1) or (not is_front and i == self.nBay - depth):
                            inner_z = depth * self.Lz if is_front else (self.nBay - depth) * self.Lz
                            step_x = W_ext / Nx
                            for nx in range(Nx):
                                x1 = ext_x + nx * step_x if is_left else ext_x - nx * step_x
                                x2 = ext_x + (nx + 1) * step_x if is_left else ext_x - (nx + 1) * step_x
                                
                                y_bot1 = self.HtLibre + self.get_y_offset(x1)
                                y_top1 = self.HtLibre + self.HtArmad + self.get_y_offset(x1)
                                y_bot2 = self.HtLibre + self.get_y_offset(x2)
                                y_top2 = self.HtLibre + self.HtArmad + self.get_y_offset(x2)
                                
                                n_b1 = self.get_or_create_node(x1, 0.0, inner_z)
                                n_b2 = self.get_or_create_node(x2, 0.0, inner_z)
                                n_ci1 = self.get_or_create_node(x1, y_bot1, inner_z)
                                n_ci2 = self.get_or_create_node(x2, y_bot2, inner_z)
                                n_cs1 = self.get_or_create_node(x1, y_top1, inner_z)
                                n_cs2 = self.get_or_create_node(x2, y_top2, inner_z)
                                
                                if is_left:
                                    p1 = self.add_plate(n_b1, n_b2, n_ci2, n_ci1)
                                    p2 = self.add_plate(n_ci1, n_ci2, n_cs2, n_cs1)
                                else:
                                    p1 = self.add_plate(n_b2, n_b1, n_ci1, n_ci2)
                                    p2 = self.add_plate(n_ci2, n_ci1, n_cs1, n_cs2)
                                
                                g_key = 'Z0' if is_front else 'ZMAX'
                                self.plate_groups[g_key].extend([p1, p2])
                        
                        continue
                    Nz = math.ceil(self.Ljoist_m / 4.0)
                    step_z = self.Lz / Nz
                    for nz in range(Nz):
                        zn1 = i * self.Lz + nz * step_z
                        zn2 = i * self.Lz + (nz + 1) * step_z
                        
                        n_b1 = self.get_or_create_node(baseX, 0.0, zn1)
                        n_b2 = self.get_or_create_node(baseX, 0.0, zn2)
                        
                        n_ci1 = self.get_or_create_node(baseX, yn_bot, zn1)
                        n_ci2 = self.get_or_create_node(baseX, yn_bot, zn2)
                        
                        n_cs1 = self.get_or_create_node(baseX, yn_top, zn1)
                        n_cs2 = self.get_or_create_node(baseX, yn_top, zn2)
                        
                        p1 = self.add_plate(n_b1, n_b2, n_ci2, n_ci1)
                        p2 = self.add_plate(n_ci1, n_ci2, n_cs2, n_cs1)
                        
                        group_key = 'X0' if j == 0 else 'XMAX'
                        self.plate_groups[group_key].extend([p1, p2])
                        
                        if i == 0 and nz == 0:
                            self.plate_releases_j1_j4.extend([p1, p2])
                        elif i == self.nBay - 1 and nz == Nz - 1:
                            self.plate_releases_j2_j3.extend([p1, p2])
                        
                        if n_b1 not in self.wind_base_nodes:
                            self.wind_base_nodes.append(n_b1)
                        if n_b2 not in self.wind_base_nodes:
                            self.wind_base_nodes.append(n_b2)
            
            # 3. Liberaciones en armaduras que llegan a placas (X=0 y X=XMAX o Z=0 y Z=ZMAX)
            for mem_id in self.groups.get('_CI', []):
                n1, n2 = self.members[mem_id]
                x1, y1, z1 = self.nodes[n1]
                x2, y2, z2 = self.nodes[n2]
                tol = 1.0 # 1 cm tol
                if abs(x1 - 0) < tol or abs(x1 - self.total_width) < tol:
                    if mem_id not in self.rel_tiltup_start:
                        self.rel_tiltup_start.append(mem_id)
                        if mem_id in self.rel_csci_start:
                            self.rel_csci_start.remove(mem_id)
                if abs(x2 - 0) < tol or abs(x2 - self.total_width) < tol:
                    if mem_id not in self.rel_tiltup_end:
                        self.rel_tiltup_end.append(mem_id)
                        if mem_id in self.rel_csci_end:
                            self.rel_csci_end.remove(mem_id)
                            
            total_depth = self.Lz * self.nBay
            for mem_id in self.groups.get('_CI_SEC', []):
                n1, n2 = self.members[mem_id]
                x1, y1, z1 = self.nodes[n1]
                x2, y2, z2 = self.nodes[n2]
                tol = 1.0 # 1 cm tol
                if abs(z1 - 0) < tol or abs(z1 - total_depth) < tol:
                    if mem_id not in self.rel_tiltup_start:
                        self.rel_tiltup_start.append(mem_id)
                        if mem_id in self.rel_ci_sec_start:
                            self.rel_ci_sec_start.remove(mem_id)
                if abs(z2 - 0) < tol or abs(z2 - total_depth) < tol:
                    if mem_id not in self.rel_tiltup_end:
                        self.rel_tiltup_end.append(mem_id)
                        if mem_id in self.rel_ci_sec_end:
                            self.rel_ci_sec_end.remove(mem_id)

        # Remove wind base nodes from regular base nodes to avoid duplicate/overlapping supports
        for nid in self.wind_base_nodes:
            if nid in self.base_nodes:
                self.base_nodes.remove(nid)


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

        # Collect all nodes connected to a wind bracing or horizontal truss member
        puntal_nodes = set()
        for mem_id in self.groups.get('_CVH', []):
            n1, n2 = self.members[mem_id]
            puntal_nodes.add(n1)
            puntal_nodes.add(n2)
        for mem_id in self.horizontal_truss_members:
            n1, n2 = self.members[mem_id]
            puntal_nodes.add(n1)
            puntal_nodes.add(n2)
            
        # Collect all joist members
        all_joists = []
        for j in range(self.nSpan + 1):
            all_joists.extend(self.groups.get(f'_LARGUEROS_{j}', []))
        for mem_id in self.groups.get('_LARGUEROS', []):
            all_joists.append(mem_id)
            
        # Classify joists and set releases
        for mem_id in all_joists:
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
                self.rel_larg_end.append(mem_id)

        return self
        
    def _generate_extensions(self):
        if not getattr(self, 'ext_bays_active', False) or self.wall_type != "Tilt-Up":
            return
            
        ext_depth = getattr(self, 'ext_depth', 1)
        ext_larm = getattr(self, 'ext_larm', 1524.0)
        ext_subdiv = getattr(self, 'ext_subdiv', 10)
        
        corners = []
        if getattr(self, 'ext_bl', False): corners.append(('bl', 0, range(0, ext_depth + 1)))
        if getattr(self, 'ext_tl', False): corners.append(('tl', 0, range(self.nBay - ext_depth, self.nBay + 1)))
        if getattr(self, 'ext_br', False): corners.append(('br', self.nSpan, range(0, ext_depth + 1)))
        if getattr(self, 'ext_tr', False): corners.append(('tr', self.nSpan, range(self.nBay - ext_depth, self.nBay + 1)))

        L0_ext = ext_larm / ext_subdiv
        
        for corner_name, j_idx, i_range in corners:
            is_left = (j_idx == 0)
            base_x = self.get_x(j_idx)
            ext_x = base_x - ext_larm if is_left else base_x + ext_larm
            
            ext_nodes_cs = {}
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
                    # Columnas (Soportando la armadura interior de la extensión)
                    # En ext_x no hay columna porque va directo al muro Tilt-Up
                    
                    nid_base_int = self.get_or_create_node(base_x, 0.0, z)
                    self.add_member(nid_base_int, nodes_ci[ext_subdiv], '_COL')
                    self.add_member(nodes_ci[ext_subdiv], nodes_cs[ext_subdiv], '_COL')
                    
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
                        mid = self.add_member(nodes_ci[ci_keys[idx]], nodes_ci[ci_keys[idx+1]], grp_ci)
                        if idx > 0 and idx < len(ci_keys) - 2:
                            self.add_ci_ly(mid, L0_ext)
                        
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
                    j_target = 0 if is_left else self.nSpan - 1
                    mem = self.add_member(nid_start, nid_end, f'_LARGUEROS_{j_target}')
                
                # Contravientos
                for c in range(len(k_points) - 1):
                    k1 = k_points[c]
                    k2 = k_points[c+1]
                    
                    n1 = ext_nodes_cs[(i_val1, k1)]
                    n2 = ext_nodes_cs[(i_val2, k2)]
                    n3 = ext_nodes_cs[(i_val2, k1)]
                    n4 = ext_nodes_cs[(i_val1, k2)]
                    
                    self.add_member(n1, n2, '_CVH')
                    self.add_member(n3, n4, '_CVH')
                
