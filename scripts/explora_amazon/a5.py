"""Escena 6 (57.13–65.25): del garaje al gigante mundial; rutas, clientes del mundo y Jeff observando."""
from amz import *
import a0
DUR = 8.12
CUTS = [2.7, 6.4]
WH = .5
_c = {}
LW, LH = 1500, 1920
CONT = [[(.06,.2),(.15,.1),(.28,.08),(.3,.2),(.26,.34),(.2,.42),(.16,.34),(.08,.3)], [(.22,.48),(.3,.46),(.34,.6),(.28,.82),(.24,.7)], [(.44,.16),(.52,.12),(.56,.22),(.5,.28),(.44,.26)],
        [(.46,.32),(.56,.3),(.6,.46),(.54,.68),(.48,.6),(.44,.44)], [(.56,.12),(.76,.1),(.9,.2),(.86,.36),(.74,.42),(.66,.34),(.58,.28)], [(.76,.58),(.88,.56),(.9,.7),(.8,.74)]]
HUB = (.18, .26)
DEST = [(.5, .2), (.76, .22), (.3, .62), (.54, .5), (.84, .62), (.82, .3)]


def build():
    if "X" in _c: return _c
    def ext(p):
        p.vgrad(0, 0, LW, LH, [(0, (22, 30, 78)), (.4, (110, 76, 140)), (.65, (250, 160, 110)), (1, (255, 200, 140))])
        p.ell(1000, 1000, 120, 120, (255, 232, 180))
        p.rect(80, 780, 1420, 1330, (150, 158, 178)); p.rect(80, 780, 1420, 820, (96, 104, 128))
        for k in range(8): p.rect(120 + k * 170, 1100, 120 + k * 170 + 120, 1330, (70, 78, 98)); p.rect(120 + k * 170, 1100, 120 + k * 170 + 120, 1114, (255, 200, 60))
        p.rect(0, 1330, LW, LH, (74, 70, 92)); p.rect(0, 1330, LW, 1352, (110, 104, 132))
        for xx in range(-40, LW, 130): p.rect(xx, 1560, xx + 80, 1570, (255, 214, 150, 170))
        p.rrect(560, 840, 1020, 940, 16, (255, 255, 255)); p.text(790, 890, "AMAZON", 72, (30, 40, 70), anchor="mm")
    def hall(p):
        p.vgrad(0, 0, LW, 1300, [(0, (26, 34, 66)), (1, (44, 56, 90))])
        p.rrect(160, 240, 1340, 1000, 26, (12, 18, 44), (120, 200, 255), 8)
        p.rect(0, 1300, LW, LH, (36, 40, 64)); p.rect(0, 1290, LW, 1304, (60, 110, 190))
    _c["X"] = Layer(bake(LW, LH, ext), LW, LH, ox=-210, par=.7, zpar=.8)
    _c["H"] = Layer(bake(LW, LH, hall), LW, LH, ox=-210, par=.9, zpar=.9)
    return _c


def world(base, f, t, box, a=1.0):
    x0, y0, w, h = box
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for c in CONT: d.polygon([(x0 + x * w, y0 + y * h) for x, y in c], fill=(52, 100, 180, int(235 * a)), outline=(150, 210, 255, int(255 * a)))
    paste_np(base, im, 0, 0, 1)
    hub = (x0 + HUB[0] * w, y0 + HUB[1] * h)
    for i, dst in enumerate(DEST):
        e = ease(prog(t, .2 + i * .25, 1.0 + i * .25))
        b = (x0 + dst[0] * w, y0 + dst[1] * h); mid = ((hub[0] + b[0]) / 2, min(hub[1], b[1]) - 150)
        pts = [((1 - k) ** 2 * hub[0] + 2 * k * (1 - k) * mid[0] + k * k * b[0], (1 - k) ** 2 * hub[1] + 2 * k * (1 - k) * mid[1] + k * k * b[1]) for k in np.linspace(0, 1, 30)]
        n = int(len(pts) * e)
        if n > 2: f.L.line(pts[:n], fill=sc((255, 200, 90), .85 * a), width=4)
        if e > .99:
            f.L.ellipse([b[0] - 12, b[1] - 12, b[0] + 12, b[1] + 12], fill=sc((255, 255, 255), a))
            for q in range(2):
                s_ = ((t * .6 + i * .17 + q * .5) % 1); k = s_ * (len(pts) - 1); px, py = pts[int(k)]
                f.L.ellipse([px - 7, py - 7, px + 7, py + 7], fill=sc((255, 245, 200), a))
    f.L.ellipse([hub[0] - 20, hub[1] - 20, hub[0] + 20, hub[1] + 20], fill=sc((120, 240, 160), a))
    return hub


def sub_morph(t, base, f):
    X = build(); G = a0.build()["G"]
    u = ease_io(prog(t, 0, 2.7))
    zg = lerp(1.4, .85, u)
    cam_g = Cam(560, 1040, zg); cam_x = Cam(750, 1040, lerp(1.7, .9, u))
    tmp = np.zeros_like(base); G.blit(tmp, cam_g)
    a2 = ease(prog(t, .5, 2.2)); tmp2 = np.zeros_like(base); X["X"].blit(tmp2, cam_x)
    base[:] = tmp * (1 - a2) + tmp2 * a2
    # el garaje se convierte en el enorme centro: líneas de "crecimiento"
    for i in range(18):
        ang = i / 18 * 6.28; r = 200 + 900 * u
        f.L.line([540 + math.cos(ang) * r * .5, 960 + math.sin(ang) * r * .5, 540 + math.cos(ang) * r, 960 + math.sin(ang) * r], fill=sc((255, 214, 120), .22 * math.sin(math.pi * u)), width=4)
    # trabajadores/camiones aparecen al agrandarse
    for q in range(3):
        x = ((t * (160 + 30 * q) + q * 500) % 1900) - 300
        put_icon(base, cached(("trk4", q), lambda: truck_icon(360, 0)), *cam_x.p(x, 1460 + q * 60), scale=cam_x.z * .8, alpha=a2)
    for q, nm in enumerate(("eng_m", "tech_w", "eng_f")):
        place_person(base, nm, walk_pose((t * 1.0 + q * .3) % 1, speed=.7, smile=.5, turn=.2), 360 + q * 280 + 40 * math.sin(t), 1560, cam_x, k=1.1, alpha=a2)
    ya = ease(prog(t, .1, .6)) * (1 - ease(prog(t, 1.4, 2.0)))
    im = text_img("1994", 120, (255, 214, 120), stroke=8, stroke_col=(20, 20, 50)); paste_np(base, im, 540 - im.width / 2, 200, ya)
    yb = ease(prog(t, 1.8, 2.4))
    im = text_img("HOY", 120, (255, 255, 255), stroke=8, stroke_col=(20, 20, 50)); paste_np(base, im, 540 - im.width / 2, 200, yb)


def sub_map(t, base, f):
    X = build(); base[:] = np.array((10, 18, 44), np.float32)
    g = np.linspace(0, 1, H)[:, None]; base[:] = np.array((10, 16, 40), np.float32) * (1 - g[..., None]) + np.array((26, 42, 86), np.float32) * g[..., None]
    zt = ease_io(prog(t, 0, 3.7))
    box = (-60 - 40 * zt, 440, 1200 + 80 * zt, 700)
    world(base, f, t, box)
    # clientes de distintos países comprando (recuadros animados)
    spots = [((.5, .2), "cust_f", "headphones"), ((.76, .22), "cust_m", "laptop"), ((.54, .5), "cust_f", "shirt")]
    for i, (dst, nm, kind) in enumerate(spots):
        a = ease(prog(t, 1.2 + i * .6, 1.8 + i * .6))
        if a < .02: continue
        cx = int(box[0] + dst[0] * box[2]); cy = int(box[1] + dst[1] * box[3])
        px = 100 + i * 340; py = 1230
        pan = Image.new("RGBA", (320, 330), (0, 0, 0, 0)); d = ImageDraw.Draw(pan)
        d.rounded_rectangle([0, 0, 319, 329], radius=26, fill=(255, 236, 214, 255), outline=(255, 214, 120, 255), width=5)
        paste_np(base, pan, px, py, a)
        f.L.line([(cx, cy), (px + 160, py)], fill=sc((255, 214, 120), .45 * a), width=3)
        pose = mk(sf=60 + 6 * math.sin(t * 8 + i), ef=40, turn=.4, smile=.8, mouth=.2, eyes=blink(t, 3, i * .3), head=-3, lean=4)
        place_person(base, nm, pose, px + 130, py + 190, Cam(540, 960, 1.0), k=.62, alpha=a)
        phn = phone_icon(90, t, tap=int(t * 2.5 + i) % 6); put_icon(base, phn, px + 220, py + 120, scale=1.0, alpha=a)
        pi = cached(("pr", kind, 120), lambda kind=kind: product(kind, 120))
        u = (t * .8 + i * .3) % 1; put_icon(base, pi, lerp(px + 220, px + 160, u), py + 100 - 90 * math.sin(math.pi * u), scale=.5, alpha=a * (1 - u))


def sub_jeff(t, base, f):
    X = build(); X["H"].blit(base, Cam(700, 1000, 1.0 + .08 * ease_io(prog(t, 0, 1.8))))
    # pared de datos con el mapa y rutas
    box = (100, 340, 880, 470)
    world(base, f, t + 3, box, a=.95)
    nod = math.sin(t * 2.4)
    pose = mk(turn=.1, smile=.95, brow=.4, head=-3 + 2 * nod, lookx=1.5, looky=-.4, sf=-22, ef=-40, sb=-26, eb=-30, eyes=blink(t, 3, .3), lean=1 + .8 * math.sin(t * 1.1))
    place_person(base, "bezos_adult", pose, 540, 1480, Cam(540, 960, 1.0), k=1.3)


def scene(t):
    f = Frame(bg=False); base = f.base
    if t < CUTS[0] - WH / 2: sub_morph(t, base, f)
    elif t < CUTS[0] + WH / 2:
        a = np.zeros_like(base); b = np.zeros_like(base); fa = Frame(bg=False); fb = Frame(bg=False)
        sub_morph(t, a, fa); sub_map(t - CUTS[0], b, fb); p = (t - (CUTS[0] - WH / 2)) / WH
        fa.base = a; fb.base = b; return fa.finish() * (1 - ease(p)) + fb.finish() * ease(p)
    elif t < CUTS[1] - WH / 2: sub_map(t - CUTS[0], base, f)
    elif t < CUTS[1] + WH / 2:
        a = np.zeros_like(base); b = np.zeros_like(base); fa = Frame(bg=False); fb = Frame(bg=False)
        sub_map(t - CUTS[0], a, fa); sub_jeff(t - CUTS[1], b, fb); p = (t - (CUTS[1] - WH / 2)) / WH
        fa.base = a; fb.base = b; return fa.finish() * (1 - ease(p)) + fb.finish() * ease(p) + 70 * math.sin(math.pi * p)
    else: sub_jeff(t - CUTS[1], base, f)
    dust(f, t, seed=65, n=24, tint=(255, 236, 200), alpha=.3)
    return f.finish()
