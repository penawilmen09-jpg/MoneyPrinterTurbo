"""Escena 2 — Sus comienzos (Sudáfrica + joven Elon programando en los 80)."""
from stage import *
from stage import _font
from props import *

AFRICA = [(.30,.05),(.42,.03),(.55,.07),(.66,.12),(.78,.18),(.86,.30),(.95,.38),(.97,.45),(.88,.50),(.82,.62),(.74,.76),(.64,.90),(.55,.98),(.48,.97),(.44,.86),(.42,.74),(.38,.62),(.38,.52),(.42,.46),(.30,.42),(.20,.38),(.10,.30),(.08,.24),(.16,.14),(.24,.09)]
SA = [(.44,.86),(.50,.78),(.58,.76),(.64,.80),(.64,.88),(.55,.98),(.48,.97)]
_c = {}


def build():
    if "L" in _c: return _c
    LW, LH = 1500, 1920
    def room(p):
        # pared con papel tapiz de los 80
        p.vgrad(0, 0, LW, 1300, [(0, (74, 58, 104)), (1, (112, 84, 120))])
        for xx in range(0, LW, 90):
            p.rect(xx, 0, xx + 44, 1300, (86, 66, 114, 120))
        p.rect(0, 1300, LW, LH, (96, 66, 52))       # piso de madera
        for xx in range(0, LW, 140): p.rect(xx, 1300, xx + 4, LH, (74, 50, 40))
        p.rect(0, 1286, LW, 1304, (60, 44, 60))      # zócalo
        window_box(p, 960, 380, 340, 460, ((16, 20, 60), (110, 70, 120)))
        for (x, y) in ((1010, 450), (1120, 520), (1200, 440), (1060, 620), (1240, 700)): p.ell(x, y, 3, 3, (255, 255, 220))
        p.ell(1230, 520, 30, 30, (255, 244, 200))
        # póster del transbordador espacial
        p.rect(150, 300, 400, 640, (24, 32, 76), (230, 230, 240), 6)
        p.rrect(236, 380, 266, 560, 14, (240, 240, 246)); p.poly([(236, 500), (200, 560), (236, 548)], (60, 70, 90)); p.poly([(266, 500), (302, 560), (266, 548)], (60, 70, 90))
        p.poly([(251, 340), (236, 400), (266, 400)], (240, 240, 246))
        for (x, y) in ((190, 340), (350, 360), (320, 600), (180, 600)): p.ell(x, y, 3, 3, (255, 255, 220))
        p.text(275, 620, "SPACE", 26, (255, 214, 120), anchor="mm")
        # estantería con libros
        p.rect(470, 470, 900, 482, (110, 80, 58)); p.rect(470, 640, 900, 652, (110, 80, 58))
        rng = np.random.RandomState(4)
        for r, yy in enumerate((482, 652)):
            x = 480
            while x < 880:
                bw = rng.randint(18, 34); bh = rng.randint(100, 156)
                p.rect(x, yy - bh + 0, x + bw, yy, [(206, 80, 80), (80, 150, 210), (230, 190, 80), (96, 180, 130), (170, 110, 200)][rng.randint(0, 5)]); x += bw + 2
        # escritorio
        p.rect(620, 950, 1480, 982, (150, 112, 76)); p.rect(660, 982, 690, 1300, (120, 88, 60)); p.rect(1430, 982, 1460, 1300, (120, 88, 60))
        p.rect(0, 1090, 500, 1100, (0, 0, 0, 0))
        # cama
        p.rrect(-60, 1050, 420, 1290, 20, (200, 90, 90)); p.rrect(-60, 1010, 120, 1130, 30, (240, 236, 224))
    _c["room"] = Layer(bake(LW, LH, room), LW, LH, ox=-120, par=.85, zpar=.9)
    def mapbg(p):
        p.vgrad(0, 0, 1200, 1920, [(0, (6, 12, 34)), (1, (22, 40, 88))])
        for r in range(14, 0, -1): p.ell(600, 960, r * 60, r * 60, None, (40, 70, 130, 90), 2)
        for ang in range(0, 360, 15):
            a = math.radians(ang); p.line([(600, 960), (600 + 900 * math.cos(a), 960 + 900 * math.sin(a))], (40, 70, 130, 70), 2)
    _c["map"] = Layer(bake(1200, 1920, mapbg), 1200, 1920, ox=-60, par=.6, zpar=.8)
    return _c


def africa_pts(cx, cy, size):
    return [(cx + (x - .5) * size, cy + (y - .5) * size * 1.15) for x, y in AFRICA]


def scene(t):
    C = build()
    f = Frame(bg=False); base = f.base
    base[:] = (10, 14, 34)
    # ---------- Parte A: mapa y Sudáfrica (0 – 3.2)
    ma = 1 - ease(prog(t, 2.6, 3.4))
    if ma > .01:
        cam = Cam(540, 960, 1.0 + .1 * prog(t, 0, 3.2))
        tmp = np.zeros_like(base); C["map"].blit(tmp, cam); base[:] = base * (1 - ma) + tmp * ma if ma < 1 else tmp
        pen_im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        pd = ImageDraw.Draw(pen_im)
        size = 760 * (1 + .6 * ease_io(prog(t, 0.8, 2.6)))
        cx, cy = 540 - 130 * ease_io(prog(t, .8, 2.6)), 900 - 170 * ease_io(prog(t, .8, 2.6))
        # el zoom se centra hacia el sur (Sudáfrica)
        k = ease_io(prog(t, .8, 2.6))
        cxm = 540 + (.5 - .55) * size * 0; sx = lambda x, y: (540 + (x - .53) * size * (1 + 0) , 900 + (y - .5 - (.42 * k)) * size * 1.15)
        pts = [sx(x, y) for x, y in AFRICA]
        pa = ease(prog(t, 0, .8))
        pd.polygon(pts, fill=(60, 110, 190, int(255 * pa)), outline=(150, 210, 255, int(255 * pa)))
        spts = [sx(x, y) for x, y in SA]
        sa_k = ease(prog(t, 1.4, 2.2))
        pd.polygon(spts, fill=(255, 190, 70, int(255 * sa_k)))
        paste_np(base, pen_im, 0, 0, ma)
        # pin con rebote
        if t > 1.6:
            px, py = sx(.55, .85)
            drop = (1 - ease_back(prog(t, 1.6, 2.2))) * -240
            f.L.ellipse([px - 26, py + drop - 70, px + 26, py + drop - 18], fill=sc((255, 80, 80), ma))
            f.L.polygon([(px - 24, py + drop - 34), (px + 24, py + drop - 34), (px, py + drop + 6)], fill=sc((255, 80, 80), ma))
            f.L.ellipse([px - 10, py + drop - 54, px + 10, py + drop - 34], fill=sc((255, 255, 255), ma))
            for q in range(3):
                kk = ((t - 2.0) * .8 + q / 3) % 1
                if t > 2.0:
                    r = 20 + 130 * kk; f.L.ellipse([px - r, py - r * .4, px + r, py + r * .4], outline=sc((255, 200, 90), (1 - kk) * ma), width=4)
    # ---------- Parte B: habitación de los 80 (2.6 →)
    rb = ease(prog(t, 2.5, 3.5))
    if rb > .01:
        tmp = np.zeros_like(base)
        zt = ease_io(prog(t, 2.6, 8.6))
        cam = Cam(lerp(560, 800, zt), lerp(1020, 1060, zt), lerp(0.96, 1.5, zt))
        C["room"].blit(tmp, cam)
        # silla y escritorio -> dinámicos
        ch = cached(("chair",), lambda: chair(170))
        hx, hy = 770, 1010         # cadera
        sx, sy = cam.p(hx, hy + 64)
        put_icon(tmp, ch, sx, sy + 20 * cam.z, scale=cam.z * .95)
        game = 1.0 if t > 5.2 else 0.0
        mon = desk_set(t, game=game, seed=3, w=340)
        mx, my = cam.p(1140, 790)
        put_icon(tmp, mon, mx, my, scale=cam.z * 1.0)
        kb = cached(("kb",), lambda: keyboard(250))
        kx, ky = cam.p(975, 942)
        put_icon(tmp, kb, kx, ky, scale=cam.z)
        # joven Elon (tecleando)
        a = t * 9
        focus = ease(prog(t, 3.0, 4.0))
        happy = ease(prog(t, 7.2, 8.2))
        pose = mk(lean=8, hf=86, kf=84, hb=82, kb=80, sf=62 + 2 * math.sin(a), ef=18 + 5 * math.sin(a * 1.3), sb=58, eb=22 + 4 * math.sin(a + 1),
                  head=lerp(4, -3, ease(prog(t, 4, 6))), turn=0.1, smile=lerp(.05, .8, happy), brow=lerp(-.2, .3, happy), eyes=blink(t, 2.8, .5), lookx=1.5, looky=.4,
                  mouth=.15 * (1 - happy) * (0.5 + .5 * math.sin(t * 5)))
        place_person(tmp, "elon_teen", pose, hx, hy, cam, k=1.0)
        # monedas al vender
        if t > 6.9:
            u = prog(t, 6.9, 8.4)
            cn = cached(("coin",), lambda: coin_icon(30))
            for q in range(7):
                uu = clamp(u - q * .06)
                x, y = cam.p(1140 + 150 * math.sin(q * 1.6) * uu, 790 - 420 * ease_out(uu) + 160 * uu * uu * (q % 3))
                put_icon(tmp, cn, x, y, scale=cam.z * (.8 + .5 * (1 - uu)), alpha=1 - uu ** 3)
        base[:] = base * (1 - rb) + tmp * rb
        # resplandor del monitor
        gl = .5 + .2 * math.sin(t * 7)
        f.L.ellipse([mx - 260 * cam.z, my - 210 * cam.z, mx + 260 * cam.z, my + 210 * cam.z], fill=sc((70, 200, 110), .10 * rb * gl))
    dust(f, t, seed=6, n=30, tint=(200, 255, 220), alpha=.35)
    return f.finish()
