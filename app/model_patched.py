import math

class StaadModel:
    def __init__(self, span_lengths_m, bay_lengths_m, HArmad_m, HLibre_m, numSubdiv,
                 wall_type="Metálico", roof_type="2 Aguas", slope_pct=10.0,
                 support_type="PINNED",
                 c_muerta=39.5, c_viva=100.0, c_granizo=60.0,
                 v_barlovento=32.0, v_sotavento=24.0, v_laterales=30.0, v_succion=45.0,
                 coef_sismico=0.10, ductilidad=2.0,
                 add_wind_cols=False, max_wind_dist_m=6.0,
                 sec_trusses_j=None,
                 cm_sismo=None, cv_sismo=None):
        self.scale = 100.0
        self.span_lengths_m = span_lengths_m if isinstance(span_lengths_m, list) else [span_lengths_m]
        self.bay_lengths_m = bay_lengths_m if isinstance(bay_lengths_m, list) else [bay_lengths_m]
        self.nSpan = len(self.span_lengths_m)
        self.nBay = len(self.bay_lengths_m)
        self.Lx_list = [l * self.scale for l in self.span_lengths_m]
        self.Lz_list = [l * self.scale for l in self.bay_lengths_m]
        self.total_width = sum(self.Lx_list)
        self.total_depth = sum(self.Lz_list)
        
        self.HArmad_m = float(HArmad_m)
        self.HLibre_m = float(HLibre_m)
        self.HtArmad = self.HArmad_m * self.scale
        self.HtLibre = self.HLibre_m * self.scale
        self.get_span_subdiv(j) = int(numSubdiv)
        
        self.roof_type = roof_type
        self.slope_pct = float(slope_pct)
        self.support_type = support_type
        self.wall_type = wall_type
        self.sec_trusses_j = sec_trusses_j if sec_trusses_j else []
        
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
        
        # We process loads per member later!
        self.nodes = {}  # node_id: (x, y, z)
        self.members = {}  # member_id: (node1_id, node2_id)
        self.groups = {
            '_COL': [],
            '_COLVIENTO': [],
            '_CS': [],
            '_CI': [],
            '_MONTANTES': [],
            '_DIAG': [],
            '_LARGUEROS': [],
            '_CVH': [],
            '_JOISTGRAL': [],
            '_JPUNTAL': [],
            '_CS_SEC': [],
            '_CI_SEC': [],
            '_MONTANTES_SEC': [],
            '_DIAG_SEC': []
        }
        
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
        self.base_nodes = []
        self.wind_base_nodes = []
        self.node_id = 0
        self.mem_id = 0
        self.plates = {}
        
        # New load tracking
        self.member_loads_cm = {}
        self.member_loads_cv = {}
        self.member_loads_granizo = {}
        self.member_loads_succion = {}
        self.wind_member_loads = {'X+': {}, 'X-': {}, 'Z+': {}, 'Z-': {}} # {mid: {'dir': 'GX', 'val': val}}
        self.seismic_loads = {'corner': 0, 'edge_x': 0, 'edge_z': 0, 'interior': 0}
        
        self.generate()

    def add_node(self, x, y, z, is_wind_base=False):
        self.node_id += 1
        self.nodes[self.node_id] = (x, y, z)
        if y == 0:
            if is_wind_base:
                self.wind_base_nodes.append(self.node_id)
            else:
                self.base_nodes.append(self.node_id)
        return self.node_id

    def add_plate(self, n1, n2, n3, n4):
        self.mem_id += 1
        self.plates[self.mem_id] = (n1, n2, n3, n4)
        return self.mem_id

    def add_member(self, n1, n2, group):
        self.mem_id += 1
        self.members[self.mem_id] = (n1, n2)
        if group in self.groups:
            self.groups[group].append(self.mem_id)
        return self.mem_id

    def get_x(self, j):
        return sum(self.Lx_list[:j])

    def get_z(self, i):
        return sum(self.Lz_list[:i])

    def get_span_subdiv(self, j):
        if j >= self.nSpan: j = self.nSpan - 1
        avg_Lx = sum(self.Lx_list) / self.nSpan
        target_panel = avg_Lx / self.base_numSubdiv if hasattr(self, 'base_numSubdiv') else avg_Lx / 10
        n = round(self.Lx_list[j] / target_panel)
        if n % 2 != 0: n += 1
        return int(max(2, n))
        
    def get_bay_subdiv(self, i):
        if i >= self.nBay: i = self.nBay - 1
        min_n = self.Lz_list[i] / (1.60 * self.scale)
        n = math.ceil(min_n)
        if n % 2 != 0: n += 1
        return int(max(2, n))
        
    def get_upper_node(self, nL3, upperSub, i, j, k):
        if k == 0:
            return nL3[(i, j)]
        elif k == self.get_span_subdiv(j):
            return nL3[(i, j + 1)]
        else:
            return upperSub[(i, j, k)]

    def get_y_offset(self, global_x):
        slope = self.slope_pct / 100.0
        if self.roof_type == "1 Agua":
            return global_x * slope
        elif self.roof_type == "2 Aguas":
            return min(global_x, self.total_width - global_x) * slope
        return 0.0



    def get_or_create_node(self, x, y, z):
        tol = 1e-4
        for nid, (nx, ny, nz) in self.nodes.items():
            if abs(nx - x) < tol and abs(ny - y) < tol and abs(nz - z) < tol:
                return nid
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
        
        halfSub = self.get_span_subdiv(j) // 2

        # --- Nivel 1 (Base) ---
        for j in range(self.nSpan + 1):
            for i in range(self.nBay + 1):
                x = self.get_x(j)
                y = 0.0
                z = self.get_z(i)
                nL1[(i, j)] = self.add_node(x, y, z)

        # --- Nivel 2 (Eaves) ---
        for j in range(self.nSpan + 1):
            for i in range(self.nBay + 1):
                x = self.get_x(j)
                y = self.HtLibre + self.get_y_offset(x)
                z = self.get_z(i)
                nL2[(i, j)] = self.add_node(x, y, z)

        # --- Nivel 3 (Ridge / Top) ---
        for j in range(self.nSpan + 1):
            for i in range(self.nBay + 1):
                x = self.get_x(j)
                y = self.HtLibre + self.HtArmad + self.get_y_offset(x)
                z = self.get_z(i)
                nL3[(i, j)] = self.add_node(x, y, z)

        # --- Columnas (Niveles 1 -> 2 y 2 -> 3) ---
        for j in range(self.nSpan + 1):
            for i in range(self.nBay + 1):
                is_perimeter = (j == 0 or j == self.nSpan or i == 0 or i == self.nBay)
                if self.wall_type == "Tilt-Up" and is_perimeter:
                    pass
                else:
                    col1 = self.add_member(nL1[(i, j)], nL2[(i, j)], '_COL')
                    col2 = self.add_member(nL2[(i, j)], nL3[(i, j)], '_COL')
                    
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
                    self.seismic_nodes['corner'].append(top_node)
                elif is_x_edge and not is_z_edge:
                    self.seismic_nodes['edge_z'].append(top_node) # Borde en X (j=0, j=nSpan), varía i (dirección Z) -> Su área tributaria se reduce en Z, oh wait.
                    # Corrección: si estamos en el borde X (j=0 o j=nSpan), el ancho en X es Larm_m/2. 
                    # Entonces corresponde a edge_z (donde usamos Larm_m/2 * Ljoist_m). 
                    # El nombre edge_z aquí significa que el área tributaria se basa en el perímetro en Z. 
                    # Vamos a llamarlo correctamente según la fórmula:
                    # Si is_x_edge, estamos en j=0 o j=nSpan. Aquí el ancho tributario en X es (self.Lx / scale / 2) = Larm_m/2. 
                    # En Z es completo = Ljoist_m.
                    # a_edge_z era (self.Larm_m / 2.0) * self.Ljoist_m. Esto coincide.
                elif is_z_edge and not is_x_edge:
                    self.seismic_nodes['edge_x'].append(top_node) # Borde en Z (i=0, i=nBay).
                else:
                    self.seismic_nodes['interior'].append(top_node)


        # --- Cuerda Superior (Nivel 3) e intermedios ---
        for i in range(self.nBay + 1):
            for j in range(self.nSpan):
                prev = nL3[(i, j)]
                is_first = True
                for k in range(1, self.get_span_subdiv(j)):
                    xn = self.get_x(j) + k * (self.Lx_list[j] / self.get_span_subdiv(j))
                    yn = self.HtLibre + self.HtArmad + self.get_y_offset(xn)
                    zn = self.get_z(i)
                    nid = self.add_node(xn, yn, zn)
                    upperSub[(i, j, k)] = nid
                    
                    if not (self.wall_type == "Tilt-Up" and (i == 0 or i == self.nBay)):
                        mid = self.add_member(prev, nid, '_CS')
                        if is_first:
                            self.rel_csci_start.append(mid)
                            is_first = False
                    prev = nid
                if not (self.wall_type == "Tilt-Up" and (i == 0 or i == self.nBay)):
                    mid2 = self.add_member(prev, nL3[(i, j + 1)], '_CS')
                    self.rel_csci_end.append(mid2)

        # --- Cuerda Inferior (Nivel 2) ---
        L0 = self.Lx_list[j] / self.get_span_subdiv(j)
        for i in range(self.nBay + 1):
            for j in range(self.nSpan):
                baseX = self.get_x(j)
                z2 = self.get_z(i)
                leftN = nL2[(i, j)]

                for t in range(1, halfSub + 1):
                    oddK = 2 * t - 1
                    x = baseX + oddK * L0
                    yn = self.HtLibre + self.get_y_offset(x)
                    nid = self.add_node(x, yn, z2)
                    lowerInter[(i, j, t)] = nid
                    
                    if not (self.wall_type == "Tilt-Up" and (i == 0 or i == self.nBay)):
                        mid = self.add_member(leftN, nid, '_CI')
                        if t == 1:
                            self.rel_csci_start.append(mid)
                        else:
                            self.ci_int.append(mid)
                    leftN = nid

                if not (self.wall_type == "Tilt-Up" and (i == 0 or i == self.nBay)):
                    mid2 = self.add_member(leftN, nL2[(i, j + 1)], '_CI')
                    self.rel_csci_end.append(mid2)

        # --- Montantes ---
        for i in range(self.nBay + 1):
            if self.wall_type == "Tilt-Up" and (i == 0 or i == self.nBay):
                continue
            for j in range(self.nSpan):
                for t in range(1, halfSub + 1):
                    oddK = 2 * t - 1
                    self.add_member(lowerInter[(i, j, t)], upperSub[(i, j, oddK)], '_MONTANTES')

        # --- Diagonales (V) ---
        for i in range(self.nBay + 1):
            if self.wall_type == "Tilt-Up" and (i == 0 or i == self.nBay):
                continue
            for j in range(self.nSpan):
                for t in range(1, halfSub + 1):
                    # izquierda
                    u_left = self.get_upper_node(nL3, upperSub, i, j, 2 * (t - 1))
                    self.add_member(u_left, lowerInter[(i, j, t)], '_DIAG')
                    # derecha
                    u_right = self.get_upper_node(nL3, upperSub, i, j, 2 * t)
                    self.add_member(u_right, lowerInter[(i, j, t)], '_DIAG')
        # --- Largueros ---
        if self.nBay >= 1:
            for j in range(self.nSpan + 1):
                is_wind_col_axis = (self.add_wind_cols and self.wind_col_N > 1 and (j == 0 or j == self.nSpan) and self.wall_type != "Tilt-Up")
                if self.wall_type == "Tilt-Up" and (j == 0 or j == self.nSpan):
                    continue
                has_sec_truss = (j in self.sec_trusses_j)
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
                            
                            if j == 0:
                                self.wind_cols['X0_WINDCOL'].append(col_wind)
                            else:
                                self.wind_cols['XMAX_WINDCOL'].append(col_wind)
                                
                            A[k] = nid_roof
                            
                            # Generate horizontal truss node
                            x_next = L0 if j == 0 else (self.total_width - L0)
                            y_next = self.HtLibre + self.HtArmad + self.get_y_offset(x_next)
                            
                            nid_new = self.add_node(x_next, y_next, z)
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
                        baseZ = self.get_z(i)
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
                                mem_id = self.add_member(A[p], A[p+1], '_LARGUEROS')
                                if p == 0:
                                    self.split_purlin_first.append(mem_id)
                                elif p == N - 1:
                                    self.split_purlin_last.append(mem_id)
                                else:
                                    self.split_purlin_middle.append(mem_id)
                    elif has_sec_truss:
                        # Secondary truss on interior axis without wind columns
                        baseZ = self.get_z(i)
                        start_rel = True
                        end_rel = True
                        self._add_sec_truss_segment(j, nL3[(i, j)], nL3[(i + 1, j)], nL2[(i, j)], nL2[(i + 1, j)], baseZ, self.Lz, start_rel, end_rel)
                    else:
                        # Standard larguero
                        self.add_member(nL3[(i, j)], nL3[(i + 1, j)], '_LARGUEROS')
            
            for j in range(self.nSpan):
                for k in range(1, self.get_span_subdiv(j)):
                    for i in range(self.nBay):
                        self.add_member(upperSub[(i, j, k)], upperSub[(i + 1, j, k)], '_LARGUEROS')

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
                        half_sub = self.get_span_subdiv(j) // 2
                        half_lx = self.Lx / 2.0
                        chunks_half = max(1, round(half_lx / self.Lz))
                        
                        left_pts = [int(round(c * half_sub / chunks_half)) for c in range(chunks_half)]
                        right_pts = [half_sub + int(round(c * half_sub / chunks_half)) for c in range(chunks_half + 1)]
                        k_points = left_pts + right_pts
                    else:
                        if self.Lx > self.Lz:
                            chunks = max(2, round(self.Lx / self.Lz))
                        else:
                            chunks = 1
                        k_points = [int(round(c * self.get_span_subdiv(j) / chunks)) for c in range(chunks + 1)]
                    
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
        if self.add_wind_cols and self.wind_col_Z_M > 1:
            for i in [0, self.nBay]:
                if self.wall_type == "Tilt-Up":
                    continue
                for j in range(self.nSpan):
                    # Existing nodes on Cuerda Inferior in this span j and bay i
                    ci_nodes_in_span = []
                    # 1. Start node
                    ci_nodes_in_span.append((nL2[(i, j)], self.get_x(j)))
                    # 2. Intermediate lowerInter nodes
                    for t in range(1, halfSub + 1):
                        oddK = 2 * t - 1
                        x_coord = self.get_x(j) + oddK * L0
                        if (i, j, t) in lowerInter:
                            ci_nodes_in_span.append((lowerInter[(i, j, t)], x_coord))
                    # 3. End node
                    ci_nodes_in_span.append((nL2[(i, j+1)], (j+1) * self.Lx))
                    
                    # For each wind column position
                    for k in range(1, self.wind_col_Z_M):
                        x_wind = self.get_x(j) + k * (self.Lx / self.wind_col_Z_M)
                        
                        # Find the closest existing node on the Cuerda Inferior
                        closest_node, x_node = min(ci_nodes_in_span, key=lambda node_info: abs(node_info[1] - x_wind))
                        
                        # Only add wind column if the closest node is not a main column (i.e. not at j*Lx or (j+1)*Lx)
                        if closest_node not in [nL2[(i, j)], nL2[(i, j+1)]]:
                            # Create base node at ground level (y=0) at x_node
                            nid_base = self.add_node(x_node, 0.0, self.get_z(i), is_wind_base=True)
                            
                            col_wind = self.add_member(nid_base, closest_node, '_COLVIENTO')
                            
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
            
        # Classify joists and set releases
        for mem_id in self.groups.get('_LARGUEROS', []):
            n1, n2 = self.members[mem_id]
            is_puntal = (n1 in puntal_nodes or n2 in puntal_nodes)
            
            # Add to the correct group
            if is_puntal:
                self.groups['_JPUNTAL'].append(mem_id)
            else:
                self.groups['_JOISTGRAL'].append(mem_id)
                
            # Releases logic
            if mem_id in self.split_purlin_first:
                self.rel_larg_start.append(mem_id)
            elif mem_id in self.split_purlin_last:
                self.rel_larg_end.append(mem_id)
            elif mem_id in self.split_purlin_middle:
                # No release
                pass
            else:
                # Not split: release both start and end
                self.rel_larg_start.append(mem_id)
                self.rel_larg_end.append(mem_id)
                
        # --- Generación de Placas para Tilt-Up ---
        if self.wall_type == "Tilt-Up":
            # 1. Caras Z=0 y Z=ZMAX (A lo largo de X)
            for i in [0, self.nBay]:
                for j in range(self.nSpan):
                    baseZ = self.get_z(i)
                    # En estas caras, generamos 2 placas por cada separación de la armadura
                    for k in range(self.get_span_subdiv(j)):
                        xn1 = self.get_x(j) + k * (self.Lx_list[j] / self.get_span_subdiv(j))
                        xn2 = self.get_x(j) + (k + 1) * (self.Lx_list[j] / self.get_span_subdiv(j))
                        
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
                        self.add_plate(n_b1, n_b2, n_ci2, n_ci1)
                        
                        # Placa Superior (CI a CS)
                        self.add_plate(n_ci1, n_ci2, n_cs2, n_cs1)
                        
                        # Nodos base requieren soporte PINNED
                        if n_b1 not in self.wind_base_nodes:
                            self.wind_base_nodes.append(n_b1)
                        if n_b2 not in self.wind_base_nodes:
                            self.wind_base_nodes.append(n_b2)

            # 2. Caras X=0 y X=XMAX (A lo largo de Z)
            for j in [0, self.nSpan]:
                baseX = self.get_x(j)
                yn_bot = self.HtLibre + self.get_y_offset(baseX)
                yn_top = self.HtLibre + self.HtArmad + self.get_y_offset(baseX)
                
                for i in range(self.nBay):
                    Nz = math.ceil(self.Ljoist_m / 4.0)
                    step_z = self.Lz / Nz
                    for nz in range(Nz):
                        zn1 = self.get_z(i) + nz * step_z
                        zn2 = self.get_z(i) + (nz + 1) * step_z
                        
                        n_b1 = self.get_or_create_node(baseX, 0.0, zn1)
                        n_b2 = self.get_or_create_node(baseX, 0.0, zn2)
                        
                        n_ci1 = self.get_or_create_node(baseX, yn_bot, zn1)
                        n_ci2 = self.get_or_create_node(baseX, yn_bot, zn2)
                        
                        n_cs1 = self.get_or_create_node(baseX, yn_top, zn1)
                        n_cs2 = self.get_or_create_node(baseX, yn_top, zn2)
                        
                        p1 = self.add_plate(n_b1, n_b2, n_ci2, n_ci1)
                        p2 = self.add_plate(n_ci1, n_ci2, n_cs2, n_cs1)
                        
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

        return self
