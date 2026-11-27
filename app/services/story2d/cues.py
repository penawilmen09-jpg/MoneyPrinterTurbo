"""Efectos de sonido sincronizados con las acciones de cada escena.

Las anclas usan los tiempos reales de las palabras de la narración (T.word).
"""


def build_cues(T):
    sc = T.scene_times
    W = T.word
    c = []

    def add(t, n, g=0.3, p=0.0):
        c.append((t, n, g, p))

    # ---- transiciones
    for sid, (a, b) in sc.items():
        kind = T.transitions.get(sid)
        if kind == "whip":
            add(a - 0.3, "whoosh", 0.30)
        elif kind == "flash":
            add(a - 0.25, "whoosh_dn", 0.28)
        elif kind == "iris":
            add(a - 0.25, "whoosh", 0.26)
        elif kind == "glitch":
            add(a - 0.25, "static", 0.17)

    # ---- S1 gancho
    h = T.start("h1")
    add(h + 0.12, "door", 0.30, -0.3)
    add(W("h1", "supermercado") + 0.9, "beep", 0.26, -0.4)
    add(W("h1", "durante") + 0.5, "beep", 0.26, 0.4)
    add(W("h1", "semanas") + 0.2, "pop", 0.30)
    # ---- S2
    add(T.start("h2") + 0.02, "door", 0.28)
    add(sc["s2"][0] + 1.1, "pop", 0.30)
    add(W("h2", "robar") + 0.05, "stamp", 0.40)
    # ---- S3 el dinero desaparece
    a = sc["s3"][0]
    add(W("h3", "dinero") - 0.1, "drawer", 0.45, 0.2)
    t_s = W("h3", "desaparec")
    for i in range(6):
        add(t_s + 0.1 + i * 0.22, "ding", 0.20, -0.3 + i * 0.12)
    add(W("h3", "cajas") - 0.1, "error", 0.34)
    # ---- S4 el gerente investiga
    a, b = sc["s4"]
    t1, t2 = W("d1", "interrog") - 0.1, W("d1", "comprob") - 0.1
    add(W("d1", "gerente"), "beep2", 0.26, -0.4)
    add(W("d1", "cámaras"), "static", 0.22)
    add(t1 - 0.05, "whoosh", 0.30)
    add(t1 + 0.35, "pop", 0.30)
    add(t1 + 0.9, "pop", 0.26, 0.3)
    add(t1 + 1.3, "pop", 0.26, 0.5)
    add(t2 - 0.05, "paper", 0.40)
    for i in range(4):
        add(t2 + 0.7 + i * 0.28, "click", 0.28)
    # ---- S5
    h = T.start("d2")
    for i, t0 in enumerate((0.15, 0.45, 0.75)):
        add(h + t0 + 0.2, "click", 0.30)
    add(h + 1.05, "stamp", 0.42)
    # ---- S6
    a = sc["s6"][0]
    add(W("d3", "cajero") - 0.1, "step", 0.20)
    add(W("d3", "pagaba"), "paper", 0.30)
    add(W("d3", "efectivo") + 0.3, "cash", 0.34)
    add(W("d3", "ped") + 0.3, "coin", 0.22)
    add(W("d3", "ped") + 0.6, "coin2", 0.20)
    add(W("d3", "ped") + 1.3, "error", 0.26)
    ta = W("d3", "aparec") - 0.15
    add(ta + 0.1, "beep", 0.26)
    for i in range(3):
        add(ta + 0.25 + i * 0.5, "error", 0.24)
    add(ta + 0.45, "pop", 0.30)
    # ---- S7
    a, b = sc["s7"]
    for i, t0 in enumerate((0.2, 0.9, 1.2, 1.5)):
        add(a + t0, "click", 0.14)
    add(T.start("d5") - 2.05, "riser", 0.20)
    # ---- S8 la noche y el descubrimiento
    a, b = sc["s8"]
    ta = W("d5", "revis") - 0.1
    tb = W("d5", "descubri") - 0.1
    tc = W("d5", "utiliz") - 0.1
    tm = W("d5", "quedarse")
    for i in range(4):
        add(a + 0.2 + i * 0.5, "tick", 0.07)
    add(ta, "rewind", 0.38)
    add(tb + 0.15, "beep", 0.26)
    add(tb + (tc - tb) * 0.4 + 0.1, "pop", 0.30)
    add(tc - 0.05, "whoosh", 0.30)
    ts = tm - tc
    add(tc + ts * 0.42, "drawer", 0.40)
    add(tc + ts * 0.52, "paper", 0.28)
    add(tm, "reveal", 0.55)
    # ---- S9 semanas
    a, b = sc["s9"]
    for i in range(6):
        add(a + 0.62 * (i + 1) - 0.05, "paper", 0.16)
    for i in range(5):
        add(a + 0.2 + i * 0.62 + 0.45, "coin", 0.18, -0.3)
    # ---- S10 la suma
    a, b = sc["s10"]
    tr = W("c1", "enorme") - 0.15
    n = int((tr - a - 0.2) / 0.4)
    for i in range(max(0, n)):
        add(a + 0.3 + i * 0.4, "tick", 0.16)
    add(tr + 0.1, "reveal", 0.52)
    add(tr + 0.12, "sting", 0.30)
    # ---- S11
    a, b = sc["s11"]
    tdesc = W("c2", "descubierto")
    split = W("c2", "supermercado") - 0.2
    add(tdesc, "stamp", 0.45)
    add(split + 0.1, "tada", 0.30)
    for i in range(3):
        add(split + 0.5 + i * 0.3, "click", 0.28)
    add(split + 1.25, "lock", 0.42)
    # ---- S12 final
    a, b = sc["s12"]
    tz0 = W("c3", "sino") - 0.6
    for i in range(6):
        add(tz0 - 1.2 + i * 0.7, "coin" if i % 2 else "coin2", 0.18 + 0.01 * i, -0.4 + 0.15 * i)
    add(tz0 + 1.9, "boom", 0.40)
    add(T.total - 2.0, "tada", 0.32)
    return c
