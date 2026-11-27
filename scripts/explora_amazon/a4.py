"""Escena 5 (45.8–57.13): el imperio — logística, Prime (2005) y AWS (2006)."""
from amz import *
DUR = 11.33
CUTS = [4.35, 6.55]
WH = .45
_c = {}
LW, LH = 1300, 1920


def build():
    if "W" in _c: return _c
    def wh(p):
        p.vgrad(0, 0, LW, 1100, [(0, (40, 48, 70)), (1, (78, 90, 118))])
        for xx in range(0, LW, 130): p.rect(xx, 0, xx + 12, 640, (30, 36, 54)); p.line([(xx, 0), (xx + 130, 220)], (34, 40, 60), 8)
        for xx in (150, 470, 790, 1110): p.ell(xx, 90, 80, 20, (255, 244, 210)); p.poly([(xx - 40, 100), (xx + 40, 100), (xx + 170, 760), (xx - 170, 760)], (255, 244, 210, 24))
        # estanterías en perspectiva (filas de fondo)
        for (y, h_, sx_, n) in ((560, 400, .6, 3), (740, 480, .8, 3)):
            for k in range(n): shelf_unit(p, 40 + k * 420, y, 380, h_, rows=5, seed=k + int(y))
        p.rect(0, 1160, LW, LH, (122, 128, 142)); p.rect(0, 1150, LW, 1166, (64, 70, 86))
        for xx in range(0, LW, 260): p.rect(xx, 1400, xx + 140, 1412, (255, 200, 60))
        p.rect(0, 1560, LW, 1572, (255, 200, 60))
    def porch(p):
        p.vgrad(0, 0, LW, 1300, [(0, (255, 226, 190)), (1, (255, 204, 160))])
        p.rect(0, 1300, LW, LH, (170, 140, 110)); p.rect(0, 1290, LW, 1310, (130, 100, 76))
        p.rrect(560, 380, 940, 1300, 12, (236, 232, 224)); p.rrect(600, 430, 900, 1300, 8, (80, 120, 180)); p.ell(870, 900, 12, 12, (230, 200, 90))
        p.rrect(580, 1270, 920, 1300, 6, (110, 80, 56))
        p.rrect(1000, 1180, 1100, 1300, 12, (190, 110, 80))
        for a in (-50, -25, 0, 25, 50): p.poly([(1050, 1180), (1050 + a * 2.4, 960 - abs(a)), (1050 + a * .6, 1180)], (70, 160, 100))
    def srv(p):
        p.vgrad(0, 0, LW, LH, [(0, (10, 18, 44)), (1, (20, 34, 74))])
        for xx in range(0, LW, 90): p.line([(xx, 1200), (650, 700)], (40, 70, 130, 60), 2)
        for yy in range(700, 1300, 60): p.line([(0, yy), (LW, yy)], (40, 70, 130, 60), 2)
        p.rect(0, 1300, LW, LH, (14, 22, 50)); p.rect(0, 1290, LW, 1304, (60, 110, 190))
    _c["W"] = Layer(bake(LW, LH, wh), LW, LH, ox=-110, par=.9, zpar=.9)
    _c["P"] = Layer(bake(LW, LH, porch), LW, LH, ox=-110, par=.9, zpar=.9)
    _c["R"] = Layer(bake(LW, LH, srv), LW, LH, ox=-110, par=.9, zpar=.9)
    return _c


def sub_logistics(t, base, f):
    C = build()
    zt = ease_io(prog(t, 0, 4.7))
    cam = Cam(lerp(500, 720, zt), 1040, lerp(1.0, 1.18, zt))
    C["W"].blit(base, cam)
    # cintas transportadoras con paquetes
    for (yy, spd, k) in ((1330, 120, 0), (1500, -150, 1)):
        by = cam.p(0, yy)[1]
        rect_np(base, 0, by - 12 * cam.z, W, by + 26 * cam.z, (60, 66, 82)); rect_np(base, 0, by - 12 * cam.z, W, by - 4 * cam.z, (110, 118, 140))
        for q in range(8):
            x = ((t * spd + q * 190) % 1700) - 200
            put_icon(base, cached(("box", 130 + 10 * (q % 3)), lambda q=q: box_icon(130 + 10 * (q % 3))), *cam.p(x, yy - 44), scale=cam.z * .72)
    # robots móviles que transportan estantes
    for q, (yy, spd, off, ps) in enumerate(((1440, 150, 0, 1.25), (1560, -120, 300, 1.45), (1385, 100, 700, 1.05))):
        x = ((t * spd + off) % 1700) - 200
        if spd < 0: x = 1500 - ((t * -spd + off) % 1700)
        ic = cached(("robot", int(170 * ps)), lambda ps=ps: robot_icon(int(170 * ps)))
        put_icon(base, ic, *cam.p(x, yy), scale=cam.z)
        f.L.ellipse([cam.p(x, yy)[0] - 12, cam.p(x, yy)[1] + 10, cam.p(x, yy)[0] + 12, cam.p(x, yy)[1] + 34], fill=sc((80, 240, 150), .5 + .5 * math.sin(t * 6 + q)))
    # personal: escanean, caminan con paquetes, revisan una tableta
    for (nm, hx, flip, off, kind) in (("eng_m", 240, False, 0, "scan"), ("tech_w", 600, True, .3, "walk"), ("eng_f", 930, True, .7, "tablet")):
        ph = (t * 1.0 + off) % 1
        if kind == "scan": pose = mk(sf=70 + 50 * math.sin(ph * 6.28), ef=40, sb=20, eb=30, smile=.5, turn=.3, eyes=blink(t, 3, off), head=-3, lean=6)
        elif kind == "tablet": pose = mk(sf=50, ef=70 + 8 * math.sin(ph * 6.28), sb=30, eb=60, smile=.6, turn=.3, eyes=blink(t, 3, off), head=6, lean=4)
        else: pose = walk_pose(ph, speed=.7, sf=70, ef=20, sb=70, eb=20, smile=.5, turn=.2, eyes=blink(t, 3, off))
        place_person(base, nm, pose, hx + (60 * math.sin(t * .8) if kind == "walk" else 0), 1290, cam, k=1.0, flip=flip)
    # camión que sale y avión por el tragaluz (reparto)
    trk = cached(("trk2",), lambda: truck_icon(380, 0))
    put_icon(base, trk, *cam.p(1150 + 120 * ease_in(prog(t, 2.6, 4.6)), 1480), scale=cam.z)
    pl = cached(("plane",), lambda: plane_icon(420)); put_icon(base, pl, *cam.p(-300 + 1900 * prog(t, .3, 4.6), 200), scale=cam.z * .55, rot=-3)


def sub_prime(t, base, f):
    C = build()
    cam = Cam(560, 1040, 1.0 + .08 * ease_io(prog(t, 0, 2.5)))
    C["P"].blit(base, cam)
    u = ease_out(prog(t, 0, 1.0))
    # camión veloz que llega con líneas de velocidad
    tx = lerp(-300, 380, u)
    put_icon(base, cached(("trk3",), lambda: truck_icon(430, t * 12)), *cam.p(tx, 1360), scale=cam.z)
    for i in range(12):
        y = 1230 + i * 22; f.L.line([(0, y), (tx * .6 - 60 + i * 8, y)], fill=sc((255, 255, 255), .5 * (1 - u * .8)), width=4)
    # repartidor entrega el paquete al cliente
    gv = ease(prog(t, .9, 1.6))
    hx = lerp(380, 680, ease_out(prog(t, .6, 1.5)))
    d = walk_pose((t * 1.6) % 1, speed=.8 * (1 - gv) + .01, sf=70, ef=20, sb=70, eb=20, smile=.6, turn=.2, eyes=blink(t, 3, .2))
    place_person(base, "driver", d, hx, 1230, cam, k=1.05)
    bx, by = cam.p(hx + 150 - 40 * gv, 1160 + 10 * gv)
    put_icon(base, cached(("box",), lambda: box_icon(130)), bx, by, scale=cam.z)
    op = ease(prog(t, 1.1, 1.6))
    place_person(base, "cust_f", mk(sf=lerp(0, 60, gv), ef=lerp(10, 30, gv), smile=.9, mouth=.5 * gv, brow=.5, turn=.5, eyes=blink(t, 3, .4), head=-3), 900, 1230, cam, k=1.0, flip=True, alpha=op)
    chip = ease(prog(t, .2, .8))
    im = text_img("2005 · AMAZON PRIME", 56, (255, 214, 120), stroke=7, stroke_col=(20, 20, 50)); paste_np(base, im, 540 - im.width / 2, 200, chip)
    if gv > .6:
        for q in range(12):
            a = q / 12 * 6.28 + t * 2; f.L.ellipse([bx - 6 + math.cos(a) * 90, by - 6 + math.sin(a) * 90, bx + 6 + math.cos(a) * 90, by + 6 + math.sin(a) * 90], fill=sc((255, 230, 140), gv))


def sub_aws(t, base, f):
    C = build()
    cam = Cam(540, 1040, 1.0 + .08 * ease_io(prog(t, 0, 4.8)))
    C["R"].blit(base, cam)
    # nube central y clientes conectados
    cl = cached(("cloud",), lambda: cloud_icon(420, (225, 240, 255)))
    cx0, cy0 = cam.p(540, 520)
    put_icon(base, cl, cx0, cy0 + 8 * math.sin(t * 2), scale=cam.z)
    at = text_img('AWS', 96, (30, 80, 160)); paste_np(base, at, cx0 - at.width / 2, cy0 - at.height / 2 + 8 * math.sin(t * 2), 1)
    rng = np.random.RandomState(7)
    n = int(10 + 70 * ease(prog(t, .8, 4.2)))
    for i in range(n):
        ang = rng.rand() * 6.28; r = 260 + rng.rand() * 330
        x, y = cx0 + math.cos(ang) * r * 1.5 * .7, cy0 + 60 + math.sin(ang) * r * .75
        f.L.line([(cx0, cy0 + 20), (x, y)], fill=sc((90, 190, 255), .22), width=2)
        s_ = (t * .8 + i * .17) % 1
        f.L.ellipse([lerp(x, cx0, s_) - 5, lerp(y, cy0 + 20, s_) - 5, lerp(x, cx0, s_) + 5, lerp(y, cy0 + 20, s_) + 5], fill=sc((200, 245, 255), .9))
        f.L.ellipse([x - 8, y - 8, x + 8, y + 8], fill=sc(mix((120, 220, 255), (255, 214, 120), (i % 3) / 2), .9))
    # servidores (racks) parpadeando
    for k, x in enumerate((130, 330, 530, 730, 930)):
        put_icon(base, rack_icon(190, t, seed=k), *cam.p(x, 1010), scale=cam.z)
    # ingenieros trabajando
    place_person(base, "dev_m", mk(sf=60, ef=60 + 10 * math.sin(t * 5), sb=30, eb=50, smile=.5, turn=.3, eyes=blink(t, 3, .2), head=4, lean=6), 300, 1480, cam, k=1.0)
    place_person(base, "dev_f", walk_pose((t * .9) % 1, speed=.6, sf=40, ef=90, smile=.6, turn=.2, eyes=blink(t, 3, .6)), 620 + 60 * math.sin(t * .6), 1480, cam, k=1.0, flip=True)
    place_person(base, "eng_m", mk(sf=lerp(0, 130, ease(prog(t, 2.0, 2.8))), ef=20, smile=.8, brow=.4, turn=.4, eyes=blink(t, 3, .9), head=-4), 920, 1480, cam, k=1.0, flip=True)
    chip = ease(prog(t, .2, .8))
    im = text_img("2006 · AMAZON WEB SERVICES", 46, (255, 214, 120), stroke=7, stroke_col=(10, 14, 36)); paste_np(base, im, 540 - im.width / 2, 180, chip)
    im2 = text_img("MILLONES DE CLIENTES", 54, (255, 255, 255), stroke=7, stroke_col=(10, 14, 36)); paste_np(base, im2, 540 - im2.width / 2, 250, ease(prog(t, 3.2, 3.9)))


def scene(t):
    f = Frame(bg=False); base = f.base
    if t < CUTS[0] - WH / 2: sub_logistics(t, base, f)
    elif t < CUTS[0] + WH / 2:
        a = np.zeros_like(base); b = np.zeros_like(base); fa = Frame(bg=False); fb = Frame(bg=False)
        sub_logistics(t, a, fa); sub_prime(t - CUTS[0], b, fb); p = (t - (CUTS[0] - WH / 2)) / WH
        return slide_blend(fa_finish(a, fa), fa_finish(b, fb), p, 1)
    elif t < CUTS[1] - WH / 2: sub_prime(t - CUTS[0], base, f)
    elif t < CUTS[1] + WH / 2:
        a = np.zeros_like(base); b = np.zeros_like(base); fa = Frame(bg=False); fb = Frame(bg=False)
        sub_prime(t - CUTS[0], a, fa); sub_aws(t - CUTS[1], b, fb); p = (t - (CUTS[1] - WH / 2)) / WH
        A = fa_finish(a, fa); B = fa_finish(b, fb); return A * (1 - ease(p)) + B * ease(p) + 80 * math.sin(math.pi * p)
    else: sub_aws(t - CUTS[1], base, f)
    dust(f, t, seed=64, n=24, tint=(255, 236, 200), alpha=.3)
    return f.finish()


def fa_finish(base, fr):
    """Combina la base dibujada con la capa de luz del Frame secundario."""
    fr.base = base
    return fr.finish()
