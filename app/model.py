import math

import math

class StaadModel:
    def __init__(self, Larm_m, Ljoist_m, nBay, nSpan, HArmad_m, HLibre_m, numSubdiv, roof_type="Plana", slope_pct=0.0, support_type="FIXED", c_muerta=30.0, c_viva=100.0, c_granizo=60.0, v_barlovento=86.0, v_sotavento=50.0, v_laterales=78.0, v_succion=95.0, coef_sismico=0.08, ductilidad=2.0, cm_sismo=None, cv_sismo=None):
        self.Larm_m = float(Larm_m)
        self.Ljoist_m = float(Ljoist_m)
        self.nBay = int(nBay)
        self.nSpan = int(nSpan)
        self.HArmad_m = float(HArmad_m)
        self.HLibre_m = float(HLibre_m)
        self.numSubdiv = int(numSubdiv)
        
        self.roof_type = roof_type
        self.slope_pct = float(slope_pct)
        self.support_type = support_type
        
        # Cargas (kg/m2)
        self.c_muerta = float(c_muerta)
        self.c_viva = float(c_viva)
        self.c_granizo = float(c_granizo)
        
        self.v_barlovento = float(v_barlovento)
        self.v_sotavento = float(v_sotavento)
        self.v_laterales = float(v_laterales)
        self.v_succion = float(v_succion)
        
        # Sismo
        self.coef_sismico = float(coef_sismico)
        self.ductilidad = float(ductilidad)
        self.cm_sismo = float(cm_sismo) if cm_sismo is not None else self.c_muerta
        self.cv_sismo = float(cv_sismo) if cv_sismo is not None else (self.c_viva * 0.25)
        
        self.seismic_v = self.coef_sismico / self.ductilidad
        
        # Cálculo de Cargas Lineales gravitacionales (kg/cm) para los largueros
        self.dist_largueros_m = self.Larm_m / self.numSubdiv
        self.load_cm = (self.c_muerta * self.dist_largueros_m) / 100.0
        self.load_cv = (self.c_viva * self.dist_largueros_m) / 100.0
        self.load_granizo = (self.c_granizo * self.dist_largueros_m) / 100.0
        
        # Carga lineal de viento en largueros
        self.load_succion = (self.v_succion * self.dist_largueros_m) / 100.0
        
        # Anchos tributarios para columnas
        trib_x = self.Ljoist_m
        trib_z = self.Larm_m
        
        # Cargas lineales de viento en columnas (kg/cm)
        self.w_barl_x_in = (self.v_barlovento * trib_x) / 100.0
        self.w_barl_x_co = (self.v_barlovento * (trib_x / 2.0)) / 100.0
        self.w_barl_z_in = (self.v_barlovento * trib_z) / 100.0
        self.w_barl_z_co = (self.v_barlovento * (trib_z / 2.0)) / 100.0
        
        self.w_sot_x_in = (self.v_sotavento * trib_x) / 100.0
        self.w_sot_x_co = (self.v_sotavento * (trib_x / 2.0)) / 100.0
        self.w_sot_z_in = (self.v_sotavento * trib_z) / 100.0
        self.w_sot_z_co = (self.v_sotavento * (trib_z / 2.0)) / 100.0
        
        self.w_lat_x_in = (self.v_laterales * trib_x) / 100.0
        self.w_lat_x_co = (self.v_laterales * (trib_x / 2.0)) / 100.0
        self.w_lat_z_in = (self.v_laterales * trib_z) / 100.0
        self.w_lat_z_co = (self.v_laterales * (trib_z / 2.0)) / 100.0
        
        # Cargas nodales de Sismo (kg)
        w_sismo = self.cm_sismo + self.cv_sismo
        w_total = self.cm_sismo + self.cv_sismo
        a_corner = (self.Larm_m / 2.0) * (self.Ljoist_m / 2.0)
        a_edge_x = self.Larm_m * (self.Ljoist_m / 2.0)
        a_edge_z = (self.Larm_m / 2.0) * self.Ljoist_m
        a_interior = self.Larm_m * self.Ljoist_m
        
        self.seismic_loads = {
            'corner': math.ceil((a_corner * w_total * self.seismic_v) * 10) / 10.0,
            'edge_x': math.ceil((a_edge_x * w_total * self.seismic_v) * 10) / 10.0,
            'edge_z': math.ceil((a_edge_z * w_total * self.seismic_v) * 10) / 10.0,
            'interior': math.ceil((a_interior * w_total * self.seismic_v) * 10) / 10.0
        }
        
        if self.numSubdiv < 2 or self.numSubdiv % 2 != 0:
            raise ValueError("Las subdivisiones deben ser un número par mayor o igual a 2.")

        # Unit Conversion for coordinates in STAAD file (Meters to CM)
        self.scale = 100.0
        self.Lx = self.Larm_m * self.scale
        self.Lz = self.Ljoist_m * self.scale
        self.HtArmad = self.HArmad_m * self.scale
        self.HtLibre = self.HLibre_m * self.scale
        self.total_width = self.Lx * self.nSpan

        self.nodes = {}  # node_id: (x, y, z)
        self.members = {}  # member_id: (node1_id, node2_id)
        self.groups = {
            '_COL': [],
            '_CS': [],
            '_CI': [],
            '_MONTANTES': [],
            '_DIAG': [],
            '_LARGUEROS': [],
            '_CVH': []
        }
        
        self.wind_cols = {
            'X0_CORNER': [], 'X0_INNER': [],
            'XMAX_CORNER': [], 'XMAX_INNER': [],
            'Z0_CORNER': [], 'Z0_INNER': [],
            'ZMAX_CORNER': [], 'ZMAX_INNER': []
        }
        
        self.seismic_nodes = {
            'corner': [],
            'edge_x': [],
            'edge_z': [],
            'interior': []
        }
        
        self.release_start = []
        self.release_end = []
        
        self.col_heights = {}
        self.ci_int = []
        
        self.base_nodes = [] # Nodos en la base para asignar SUPPORTS FIXED

        self.node_id = 0
        self.mem_id = 0
        
        self.generate()

    def add_node(self, x, y, z):
        self.node_id += 1
        self.nodes[self.node_id] = (x, y, z)
        if y == 0:
            self.base_nodes.append(self.node_id)
        return self.node_id

    def add_member(self, n1, n2, group):
        self.mem_id += 1
        self.members[self.mem_id] = (n1, n2)
        if group in self.groups:
            self.groups[group].append(self.mem_id)
        return self.mem_id

    def get_upper_node(self, nL3, upperSub, i, j, k):
        if k == 0:
            return nL3[(i, j)]
        elif k == self.numSubdiv:
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

    def generate(self):
        # Data structures to store node references
        nL1 = {}
        nL2 = {}
        nL3 = {}
        upperSub = {}
        lowerInter = {}
        
        halfSub = self.numSubdiv // 2

        # --- Nivel 1 (Base) ---
        for j in range(self.nSpan + 1):
            for i in range(self.nBay + 1):
                x = j * self.Lx
                y = 0.0
                z = i * self.Lz
                nL1[(i, j)] = self.add_node(x, y, z)

        # --- Nivel 2 (Eaves) ---
        for j in range(self.nSpan + 1):
            for i in range(self.nBay + 1):
                x = j * self.Lx
                y = self.HtLibre + self.get_y_offset(x)
                z = i * self.Lz
                nL2[(i, j)] = self.add_node(x, y, z)

        # --- Nivel 3 (Ridge / Top) ---
        for j in range(self.nSpan + 1):
            for i in range(self.nBay + 1):
                x = j * self.Lx
                y = self.HtLibre + self.HtArmad + self.get_y_offset(x)
                z = i * self.Lz
                nL3[(i, j)] = self.add_node(x, y, z)

        # --- Columnas (Niveles 1 -> 2 y 2 -> 3) ---
        for j in range(self.nSpan + 1):
            for i in range(self.nBay + 1):
                col1 = self.add_member(nL1[(i, j)], nL2[(i, j)], '_COL')
                col2 = self.add_member(nL2[(i, j)], nL3[(i, j)], '_COL')
                
                # Height calculation
                x = j * self.Lx
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
                for k in range(1, self.numSubdiv):
                    xn = j * self.Lx + k * (self.Lx / self.numSubdiv)
                    yn = self.HtLibre + self.HtArmad + self.get_y_offset(xn)
                    zn = i * self.Lz
                    nid = self.add_node(xn, yn, zn)
                    upperSub[(i, j, k)] = nid
                    
                    mid = self.add_member(prev, nid, '_CS')
                    if is_first:
                        self.release_start.append(mid)
                        is_first = False
                    prev = nid
                mid2 = self.add_member(prev, nL3[(i, j + 1)], '_CS')
                self.release_end.append(mid2)

        # --- Cuerda Inferior (Nivel 2) ---
        L0 = self.Lx / self.numSubdiv
        for i in range(self.nBay + 1):
            for j in range(self.nSpan):
                baseX = j * self.Lx
                z2 = i * self.Lz
                leftN = nL2[(i, j)]

                for t in range(1, halfSub + 1):
                    oddK = 2 * t - 1
                    x = baseX + oddK * L0
                    yn = self.HtLibre + self.get_y_offset(x)
                    nid = self.add_node(x, yn, z2)
                    lowerInter[(i, j, t)] = nid
                    
                    mid = self.add_member(leftN, nid, '_CI')
                    if t == 1:
                        self.release_start.append(mid)
                    else:
                        self.ci_int.append(mid)
                    leftN = nid

                mid2 = self.add_member(leftN, nL2[(i, j + 1)], '_CI')
                self.release_end.append(mid2)

        # --- Montantes ---
        for i in range(self.nBay + 1):
            for j in range(self.nSpan):
                for t in range(1, halfSub + 1):
                    oddK = 2 * t - 1
                    self.add_member(lowerInter[(i, j, t)], upperSub[(i, j, oddK)], '_MONTANTES')

        # --- Diagonales (V) ---
        for i in range(self.nBay + 1):
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
                for i in range(self.nBay):
                    self.add_member(nL3[(i, j)], nL3[(i + 1, j)], '_LARGUEROS')
            
            for j in range(self.nSpan):
                for k in range(1, self.numSubdiv):
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
                        half_sub = self.numSubdiv // 2
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
                        k_points = [int(round(c * self.numSubdiv / chunks)) for c in range(chunks + 1)]
                    
                    for c in range(len(k_points) - 1):
                        k1 = k_points[c]
                        k2 = k_points[c+1]
                        
                        n1 = self.get_upper_node(nL3, upperSub, i, j, k1)
                        n2 = self.get_upper_node(nL3, upperSub, i+1, j, k2)
                        
                        n3 = self.get_upper_node(nL3, upperSub, i+1, j, k1)
                        n4 = self.get_upper_node(nL3, upperSub, i, j, k2)
                        
                        self.add_member(n1, n2, '_CVH')
                        self.add_member(n3, n4, '_CVH')
