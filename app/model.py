import math

class StaadModel:
    def __init__(self, Larm_m, Ljoist_m, nBay, nSpan, HArmad_m, HLibre_m, numSubdiv, roof_type="Plana", slope_pct=0.0, support_type="FIXED", c_muerta=30.0, c_viva=100.0, c_granizo=60.0):
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
        
        # Cálculo de Cargas Lineales (kg/cm) para los largueros
        self.dist_largueros_m = self.Larm_m / self.numSubdiv
        self.load_cm = (self.c_muerta * self.dist_largueros_m) / 100.0
        self.load_cv = (self.c_viva * self.dist_largueros_m) / 100.0
        self.load_granizo = (self.c_granizo * self.dist_largueros_m) / 100.0
        
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

        # --- Members: Columnas ---
        for j in range(self.nSpan + 1):
            for i in range(self.nBay + 1):
                self.add_member(nL1[(i, j)], nL2[(i, j)], '_COL')
                self.add_member(nL2[(i, j)], nL3[(i, j)], '_COL')

        # --- Cuerda Superior (Nivel 3) e intermedios ---
        for i in range(self.nBay + 1):
            for j in range(self.nSpan):
                prev = nL3[(i, j)]
                for k in range(1, self.numSubdiv):
                    xn = j * self.Lx + k * (self.Lx / self.numSubdiv)
                    yn = self.HtLibre + self.HtArmad + self.get_y_offset(xn)
                    zn = i * self.Lz
                    nid = self.add_node(xn, yn, zn)
                    upperSub[(i, j, k)] = nid
                    
                    self.add_member(prev, nid, '_CS')
                    prev = nid
                self.add_member(prev, nL3[(i, j + 1)], '_CS')

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
                    
                    self.add_member(leftN, nid, '_CI')
                    leftN = nid

                self.add_member(leftN, nL2[(i, j + 1)], '_CI')

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
