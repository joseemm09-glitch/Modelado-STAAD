import math

def generar_base_datos_or():
    perfiles = []
    tamanos = [6, 8, 10, 12, 14, 16, 18, 20, 22, 24]
    espesores = [
        ("3/16", 0.1875), ("1/4", 0.25), ("5/16", 0.3125),
        ("3/8", 0.375), ("1/2", 0.5), ("5/8", 0.625),
        ("3/4", 0.75), ("7/8", 0.875), ("1", 1.0)
    ]
    for B in tamanos:
        for t_name, t_in in espesores:
            if t_in > B / 10.0 and B > 10: pass
            B_cm = B * 2.54
            t_cm = t_in * 2.54
            b_int = B_cm - 2 * t_cm
            A = (B_cm**2) - (b_int**2)
            if A <= 0: continue
            Ix = (B_cm**4 - b_int**4) / 12.0
            Sx = Ix / (B_cm / 2.0)
            peso = A * 100 * 0.00785
            nombre = f"OR {B}\"x{B}\"x{t_name}\""
            perfiles.append({"nombre": nombre, "A": A, "Sx": Sx, "peso": peso})
    return sorted(perfiles, key=lambda x: x["peso"])

perfiles = generar_base_datos_or()
print(f"Total perfiles: {len(perfiles)}")

def predisenar(L_span, L_bay, H, CM, CV, viento, At_vert, L_trib_viento):
    P_kg = At_vert * (CM + CV)
    w_viento = viento * L_trib_viento
    M_viento_kg_m = (w_viento * H**2) / 8.0
    M_viento_kg_cm = M_viento_kg_m * 100.0
    Fy = 3230.0
    resultados = []
    for perfil in perfiles:
        A = perfil["A"]
        Sx = perfil["Sx"]
        fa = P_kg / A
        fb = M_viento_kg_cm / Sx
        ratio = (fa / (0.6 * Fy)) + (fb / (0.6 * Fy))
        if 0.6 <= ratio <= 0.95:
            resultados.append({"perfil": perfil, "ratio": ratio})
            
    if len(resultados) < 5:
        for perfil in perfiles:
            A = perfil["A"]
            Sx = perfil["Sx"]
            fa = P_kg / A
            fb = M_viento_kg_cm / Sx
            ratio = (fa / (0.6 * Fy)) + (fb / (0.6 * Fy))
            if 0.3 <= ratio <= 1.2:
                resultados.append({"perfil": perfil, "ratio": ratio})
                
    resultados.sort(key=lambda x: abs(0.8 - x["ratio"]))
    vistos = set()
    top_5 = []
    for r in resultados:
        if r["perfil"]["nombre"] not in vistos:
            vistos.add(r["perfil"]["nombre"])
            top_5.append(r)
        if len(top_5) == 5: break
    top_5.sort(key=lambda x: x["perfil"]["peso"])
    if not top_5:
        return [{"perfil": p, "ratio": 0.0} for p in perfiles[-5:]]
    return top_5

print("C-1 (Interiores):")
res = predisenar(15.24, 12.20, 9.75, 30, 100, 86, 15.24*12.20, max(15.24, 12.20))
for r in res:
    print(f"  {r['perfil']['nombre']}: {r['ratio']:.3f} | {r['perfil']['peso']:.1f} kg/m")
