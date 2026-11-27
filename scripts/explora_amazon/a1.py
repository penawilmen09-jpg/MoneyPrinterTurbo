"""Escena 2 — El hombre detrás de la idea (14.85–27.55): oficina financiera 1994, viaje a Seattle, oficina improvisada con libros."""
from amz import *
_c = {}
LW, LH = 1300, 1920
DUR = 12.7
CUTS = [5.15, 7.75]      # local: 20.0 y 22.6 absolutos
WH = .45


def build():
    if "F" in _c: return _c
    def fin(p):
        office_bg(p, LW, LH, wall=(206, 212, 224), floor=(88, 96, 116), window=True, sign=None, whiteboard=False)
        desk_row(p, 120, 640, 1020, (150, 120, 96)); desk_row(p, 700, 1220, 1020, (150, 120, 96))
        p.rect(640, 360, 700, 700, (180, 186, 200))
        for yy in range(380, 690, 40): p.rect(644, yy, 696, yy + 22, (120, 150, 200))
        p.rrect(520, 160, 800, 250, 14, (30, 40, 70)); p.text(660, 206, "NUEVA YORK · 1994", 36, (255, 214, 120), anchor="mm")
    def sea(p):
        p.vgrad(0, 0, LW, 1330, [(0, (70, 56, 40)), (1, (96, 76, 56))])
        for xx in range(0, LW, 90): p.rect(xx, 0, xx + 4, 1330, (58, 44, 32))
        p.rect(0, 1330, LW, LH, (120, 112, 104)); p.rect(0, 1318, LW, 1336, (80, 70, 60))
        p.rect(60, 280, 300, 640, (240, 240, 244), (130, 130, 140), 6); p.text(180, 340, "SEATTLE", 34, (60, 90, 150), anchor="mm")
        for k in range(4): p.line([(80, 380 + k * 60), (280, 380 + k * 60)], (180, 190, 210), 4)
        shelf_unit(p, 880, 380, 380, 760, rows=4, seed=9)
        # mesas hechas con puertas sobre caballetes
        for (x0, x1) in ((300, 780),):
            p.rrect(x0, 1010, x1, 1040, 6, (200, 170, 130)); p.ell(x0 + 40, 1025, 7, 7, (120, 90, 60)); p.rect(x0 + 30, 1040, x0 + 56, 1330, (110, 84, 56)); p.rect(x1 - 56, 1040, x1 - 30, 1330, (110, 84, 56))
        p.line([(560, 0), (560, 250)], (30, 30, 36), 4); p.ell(560, 266, 22, 26, (255, 236, 160))
    _c["F"] = Layer(bake(LW, LH, fin), LW, LH, ox=-110, par=.9, zpar=.9)
    _c["S"] = Layer(bake(LW, LH, sea), LW, LH, ox=-110, par=.9, zpar=.9)
    def mp(p):
        p.vgrad(0, 0, 1200, 1920, [(0, (10, 18, 44)), (1, (28, 44, 92))])
        for r in range(1, 14): p.ell(600, 960, r * 60, r * 60, None, (40, 70, 130, 70), 2)
    _c["M"] = Layer(bake(1200, 1920, mp), 1200, 1920, ox=-60, par=.6, zpar=.8)
    return _c


def sub_finance(t, base, f):
    C = build()
    cam = Cam(560 + 20 * math.sin(t * .5), 1020, 1.0 + .08 * ease_io(prog(t, 0, 5.4)))
    C["F"].blit(base, cam)
    for (x, sd) in ((300, 1), (900, 2)):
        mx, my = cam.p(x, 890); put_icon(base, flat_monitor(240, t + sd, "code", seed=sd), mx, my, scale=cam.z)
    ch = cached(("chair2",), lambda: chair(150))
    # compañeros (reaccionan)
    react = ease(prog(t, 3.0, 3.6))
    cx_, cy_ = cam.p(860, 1090); put_icon(base, ch, cx_, cy_ + 20 * cam.z, scale=cam.z * .9)
    place_person(base, "exec1", seated(t, .5, turn=.2, smile=lerp(.1, -.3, react), brow=lerp(0, .9, react), mouth=.5 * react, eyes=blink(t, 3.3, .2), head=lerp(-2, 6, react)), 860, 1030, cam, k=1.0, flip=True)
    place_person(base, "dev_f", seated(t, 1.1, turn=.2, smile=lerp(.2, 0, react), brow=lerp(0, .8, react), mouth=.4 * react, eyes=blink(t, 3.1, .6)), 330, 1030, cam, k=1.0)
    cx_, cy_ = cam.p(330, 1090); put_icon(base, ch, cx_, cy_ + 20 * cam.z, scale=cam.z * .9)
    # Jeff: se presenta, teclea, se levanta, recoge su caja y se va
    up = ease(prog(t, 2.2, 3.0)); go = ease(prog(t, 3.6, 5.4))
    hx = lerp(600, 1260, go)
    if go < 0.02:
        cxx, cyy = cam.p(600, 1090); put_icon(base, ch, cxx, cyy + 20 * cam.z, scale=cam.z * .9)
    if t < 2.2:
        pose = seated(t, 0, turn=.25, smile=.2, brow=-.1, eyes=blink(t, 3, .3), head=-2)
        place_person(base, "bezos_fin", pose, 600, 1030, cam, k=1.0)
    else:
        w = walk_pose((t * .9) % 1, speed=.7 * go + .01, sf=lerp(0, 40, up) , ef=lerp(10, 90, up), smile=lerp(.2, .9, go), turn=.3, head=-1, eyes=blink(t, 3, .3), lean=3)
        w["hf"] = lerp(86, w["hf"], up); w["kf"] = lerp(84, w["kf"], up); w["hb"] = lerp(82, w["hb"], up); w["kb"] = lerp(80, w["kb"], up)
        w["sf"] = lerp(62, 50, up); w["ef"] = lerp(18, 70, up)
        place_person(base, "bezos_fin", w, hx, lerp(1030, 1080, up), cam, k=1.0)
        # caja de cartón con sus cosas
        bx, by = cam.p(hx + 150, lerp(1030, 980, up) - 10 + 10 * math.sin(t * 8) * go)
        put_icon(base, cached(("boxopen",), lambda: box_icon(130, tape=False, label=False)), bx, by, scale=cam.z * 1.1 * up)
    # año
    ya = ease(prog(t, .3, .9)) * (1 - ease(prog(t, 4.6, 5.0)))
    im = text_img("1994", 130, (255, 214, 120), stroke=8, stroke_col=(20, 20, 50))
    if ya > .02: paste_np(base, im, 540 - im.width / 2, 1330, ya)


def sub_road(t, base, f):
    C = build()
    cam = Cam(540, 960, 1.0)
    C["M"].blit(base, cam)
    # mapa de EE. UU. con la ruta Nueva York -> Seattle
    mp = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(mp)
    ox, oy, sw_, sh_ = 70, 560, 940, 610
    pts = [(ox + x * sw_, oy + y * sh_) for x, y in USA]
    pa = ease(prog(t, 0, .6))
    d.polygon(pts, fill=(52, 100, 180, int(255 * pa)), outline=(150, 210, 255, int(255 * pa)))
    paste_np(base, mp, 0, 0, 1)
    ny = (ox + .9 * sw_, oy + .3 * sh_); se = (ox + .06 * sw_, oy + .1 * sh_)
    u = ease_io(prog(t, .5, 2.3))
    ctrl = ((ny[0] + se[0]) / 2, min(ny[1], se[1]) - 40)
    def at(k): return ((1 - k) ** 2 * ny[0] + 2 * k * (1 - k) * ctrl[0] + k * k * se[0], (1 - k) ** 2 * ny[1] + 2 * k * (1 - k) * ctrl[1] + k * k * se[1])
    for i in range(40):
        k = i / 40
        if k <= u and i % 2 == 0:
            x, y = at(k); f.L.ellipse([x - 6, y - 6, x + 6, y + 6], fill=sc((255, 214, 120), .95))
    cx_, cy_ = at(u)
    ic = car_icon(t * 9, (230, 70, 70), w=210); put_icon(base, ic, cx_, cy_ - 24, scale=1.0, rot=0)
    for (p_, lab) in ((ny, "NUEVA YORK"), (se, "SEATTLE")):
        f.L.ellipse([p_[0] - 14, p_[1] - 14, p_[0] + 14, p_[1] + 14], fill=sc((255, 255, 255), pa))
        im = text_img(lab, 40, (255, 255, 255), stroke=6, stroke_col=(10, 14, 36)); paste_np(base, im, p_[0] - im.width / 2, p_[1] + 24, pa)
    # Internet: red de nodos que se enciende sobre el mapa (potencial de Internet)
    net = ease(prog(t, 1.9, 2.7))
    if net > .01:
        rng = np.random.RandomState(4); nodes = [(ox + rng.rand() * sw_ * .9, oy + rng.rand() * sh_ * .8) for _ in range(26)]
        for i, a in enumerate(nodes):
            b = nodes[(i * 7 + 3) % 26]; f.L.line([a, b], fill=sc((120, 220, 255), .5 * net), width=3)
        for a in nodes: f.L.ellipse([a[0] - 7, a[1] - 7, a[0] + 7, a[1] + 7], fill=sc((200, 250, 255), net))
    # conductor: carretera con parallax en la parte superior
    for k in range(10):
        x = ((k * 200 - t * 360) % 2200) - 300; f.L.rectangle([x, 380, x + 110, 392], fill=sc((255, 255, 255), .6))
    cr = car_icon(t * 14, (230, 70, 70), w=420); put_icon(base, cr, 540 + 10 * math.sin(t * 6), 300 + 4 * math.sin(t * 9), scale=1.0)
    # cabeza de Jeff en la ventanilla
    f.L.ellipse([575, 215, 625, 265], fill=sc((232, 188, 154), 1))


def sub_seattle(t, base, f):
    C = build()
    cam = Cam(560, 1040, 1.0 + .10 * ease_io(prog(t, 0, 4.9)))
    C["S"].blit(base, cam)
    mx, my = cam.p(600, 870); put_icon(base, desk_set(t, seed=3, w=290), mx, my, scale=cam.z)
    kb = cached(("kb",), lambda: keyboard(240)); kx, ky = cam.p(470, 1000); put_icon(base, kb, kx, ky, scale=cam.z)
    ch = cached(("chair",), lambda: chair(170)); cxx, cyy = cam.p(330, 1090); put_icon(base, ch, cxx, cyy + 18 * cam.z, scale=cam.z * .95)
    pose = seated(t, 0, head=-2, turn=.2, smile=.7, eyes=blink(t, 3, .3), lookx=1.3, brow=.2)
    place_person(base, "bezos_young", pose, 330, 1030, cam, k=1.0)
    # empleado que acomoda libros en la estantería (movimiento de brazos)
    w = ease(prog(t, 1.5, 2.2))
    pose = mk(sf=lerp(0, 120 + 12 * math.sin(t * 5), w), ef=lerp(10, 20, w), turn=.2, smile=.5, eyes=blink(t, 3, .5), head=-3, lean=2)
    place_person(base, "dev_m", pose, 820, 1190, cam, k=1.0, flip=True)
    # libros -> caja -> envío (por qué libros)
    bk = [cached(("bk", i), lambda i=i: book_icon(70, [(210, 70, 70), (70, 130, 210), (230, 190, 70), (90, 170, 120)][i % 4])) for i in range(4)]
    bo = cached(("box",), lambda: box_icon(150))
    t0 = 1.6
    for i in range(4):
        u = prog(t, t0 + i * .45, t0 + i * .45 + 1.0)
        if u <= 0: continue
        a = cam.p(1000, 760 + 60 * i); b = cam.p(520, 1000)
        put_icon(base, bk[i], lerp(a[0], b[0], ease(u)), lerp(a[1], b[1], ease(u)) - 140 * math.sin(math.pi * u), scale=cam.z * (1 - .2 * u), rot=360 * u * (1 if i % 2 else -1) * .3, alpha=1 - ease(clamp((u - .85) / .15)))
    put_icon(base, bo, *cam.p(500, 1000), scale=cam.z * ease_back(prog(t, 2.0, 2.6)))
    if t > 3.4:
        u = prog(t, 3.4, 4.9); trk = truck_icon(330, t * 9)
        put_icon(base, trk, lerp(-200, 1300, ease_in(u)), 1380, scale=1.0)
        f.L.polygon([(0, 1350), (500 * u, 1350), (500 * u, 1360), (0, 1360)], fill=sc((255, 255, 255), .0))


def scene(t):
    f = Frame(bg=False); base = f.base
    if t < CUTS[0] - WH / 2: sub_finance(t, base, f)
    elif t < CUTS[0] + WH / 2:
        a = np.zeros_like(base); b = np.zeros_like(base); fa = Frame(bg=False); fb = Frame(bg=False)
        sub_finance(t, a, fa); sub_road(t - CUTS[0], b, fb); base[:] = slide_blend(a, b, (t - (CUTS[0] - WH / 2)) / WH, 1)
    elif t < CUTS[1] - WH / 2: sub_road(t - CUTS[0], base, f)
    elif t < CUTS[1] + WH / 2:
        a = np.zeros_like(base); b = np.zeros_like(base); fa = Frame(bg=False); fb = Frame(bg=False)
        sub_road(t - CUTS[0], a, fa); sub_seattle(t - CUTS[1], b, fb); base[:] = a * (1 - ease((t - (CUTS[1] - WH / 2)) / WH)) + b * ease((t - (CUTS[1] - WH / 2)) / WH)
    else: sub_seattle(t - CUTS[1], base, f)
    dust(f, t, seed=61, n=26, tint=(255, 236, 200), alpha=.3)
    return f.finish()
