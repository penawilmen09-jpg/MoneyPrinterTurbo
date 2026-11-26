"""Escena 5 — SpaceX, Tesla, cohetes reutilizables y autos eléctricos."""
from kit import *
from m1 import car_icon, rocket_icon
_c = {}
LW, LH = 1300, 1920


def build():
    if "H" in _c: return _c
    def hangar(p):
        p.vgrad(0, 0, LW, 1260, [(0, (48, 56, 74)), (1, (86, 96, 116))])
        for xx in range(0, LW, 130):
            p.rect(xx, 0, xx + 14, 760, (36, 42, 58)); p.line([(xx, 0), (xx + 130, 300)], (40, 46, 62), 8)
        for xx in (180, 520, 860, 1180): p.ell(xx, 120, 60, 22, (255, 244, 210)); p.poly([(xx - 40, 130), (xx + 40, 130), (xx + 160, 700), (xx - 160, 700)], (255, 244, 210, 22))
        p.rect(0, 1260, LW, LH, (110, 114, 126)); p.rect(0, 1250, LW, 1268, (60, 66, 82))
        for xx in range(0, LW, 200): p.rect(xx, 1262, xx + 90, 1272, (255, 200, 60))
        # estructura de andamios
        for xx in (120, 1180):
            p.rect(xx, 420, xx + 14, 1260, (230, 160, 50))
            for yy in range(440, 1240, 70): p.line([(xx, yy), (xx + 14, yy + 70)], (230, 160, 50), 5)
        p.text(LW / 2 - 60, 380, "SPACEX", 120, (230, 236, 250), anchor="mm")
    def tesla(p):
        p.vgrad(0, 0, LW, 1260, [(0, (236, 240, 246)), (1, (208, 214, 224))])
        for xx in range(0, LW, 160): p.rect(xx, 0, xx + 12, 1260, (196, 202, 214))
        for xx in (150, 550, 950): p.ell(xx, 90, 120, 26, (255, 255, 255)); p.poly([(xx - 60, 100), (xx + 60, 100), (xx + 190, 760), (xx - 190, 760)], (255, 255, 255, 50))
        p.rect(0, 1260, LW, LH, (150, 154, 166))
        p.rrect(LW / 2 - 260, 190, LW / 2 + 260, 320, 26, (196, 30, 44))
        p.text(LW / 2, 256, "TESLA", 100, (255, 255, 255), anchor="mm")
        # cinta transportadora
        p.rect(0, 1130, LW, 1160, (80, 84, 96)); p.rect(0, 1160, LW, 1260, (110, 114, 126))
        for xx in range(0, LW, 80): p.rect(xx, 1160, xx + 6, 1260, (96, 100, 112))
    _c["H"] = Layer(bake(LW, LH, hangar), LW, LH, ox=-110, par=.9, zpar=.9)
    _c["T"] = Layer(bake(LW, LH, tesla), LW, LH, ox=-110, par=.9, zpar=.9)
    _c["rocket"] = rocket_icon(1150)
    return _c


def sparks(f, base, cam, x, y, t, n=18, seed=1):
    rng = np.random.RandomState(seed)
    for i in range(n):
        u = ((t * 2.2 + rng.rand()) % 1.0); a = -math.pi / 2 + rng.uniform(-1.3, 1.3); v = rng.uniform(80, 260)
        px, py = cam.p(x + math.cos(a) * v * u, y + math.sin(a) * v * u + 340 * u * u)
        f.L.ellipse([px - 3, py - 3, px + 3, py + 3], fill=sc((255, 220, 120), 1 - u))
    px, py = cam.p(x, y); f.L.ellipse([px - 26, py - 26, px + 26, py + 26], fill=sc((255, 240, 200), .5 + .3 * math.sin(t * 40)))


def sub_hangar(t, base, f):
    C = build()
    zt = ease_io(prog(t, 0, 3.8))
    cam = Cam(540, lerp(1000, 900, zt), lerp(0.98, 1.08, zt))
    C["H"].blit(base, cam)
    rk = C["rocket"]
    rx, ry = cam.p(860, 1240)
    z = cam.z
    paste_np(base, rk.resize((int(rk.width * z), int(rk.height * z)), Image.LANCZOS), rx - rk.width * z / 2, ry - rk.height * z)
    # ingeniero soldando en la base (agachado) y otra ingeniera con tableta
    pose = mk(lean=22, hf=40, kf=70, hb=-20, kb=50, sf=70, ef=20, sb=60, eb=10, head=10, smile=0, brow=-.2, eyes=blink(t, 3, .4))
    place_person(base, "eng_m", pose, 640, 1140, cam, k=1.0)
    sparks(f, base, cam, 710, 1220, t, seed=3)
    ph = t * .55
    place_person(base, "eng_f", walk_pose(ph % 1, speed=.7, smile=.3, turn=.2), 180 + 110 * t, 1180, cam, k=1.0)
    # Elon observa el cohete, brazos cruzados
    pose = mk(smile=.35, turn=.3, head=-10 + 2 * math.sin(t), lookx=1.0, looky=-1.6, eyes=blink(t, 3.4, .1), sf=30, ef=112, sb=20, eb=100, brow=.3, lean=-2)
    place_person(base, "elon_adult", pose, 380, 1190, cam, k=1.05)
    tag = text_img("2002", 96, (255, 214, 120), stroke=7, stroke_col=(20, 24, 50))
    ya = ease_back(prog(t, .4, 1.0))
    if ya > .05: paste_np(base, tag.resize((max(int(tag.width * ya), 2), max(int(tag.height * ya), 2)), Image.LANCZOS), 540 - tag.width * ya / 2, 1330 - tag.height * ya / 2, ya)


def sub_factory(t, base, f):
    C = build()
    cam = Cam(540 + 30 * math.sin(t * .6), 1000, 1.05 + .06 * prog(t, 0, 2.8))
    C["T"].blit(base, cam)
    # autos moviéndose por la línea de ensamblaje, con brazo robótico soldando
    for q in range(3):
        x = ((t * 110 + q * 520) % 1800) - 300
        ic = car_icon(0, [(232, 236, 244), (196, 30, 44), (60, 70, 96)][q], w=460)
        sx, sy = cam.p(x, 1090)
        put_icon(base, ic, sx, sy, scale=cam.z * .95)
    # brazos robóticos
    for (bx, ph) in ((300, 0), (800, 1.2)):
        a1 = -60 + 30 * math.sin(t * 2 + ph); a2 = 70 + 40 * math.sin(t * 2.6 + ph)
        p0 = cam.p(bx, 1130)
        p1 = (p0[0] + 240 * math.sin(math.radians(a1)) * cam.z * 0.8, p0[1] - 240 * math.cos(math.radians(a1)) * cam.z)
        p2 = (p1[0] + 210 * math.sin(math.radians(a1 + a2)) * cam.z, p1[1] - 210 * math.cos(math.radians(a1 + a2)) * cam.z * .6 + 120 * cam.z)
        for (u, v, w_) in ((p0, p1, 30), (p1, p2, 22)):
            ImageDraw.Draw(Image.new("RGB", (1, 1)))
            n = 14
            for i in range(n + 1):
                px, py = lerp(u[0], v[0], i / n), lerp(u[1], v[1], i / n)
                f.L.ellipse([px - w_ * cam.z / 2, py - w_ * cam.z / 2, px + w_ * cam.z / 2, py + w_ * cam.z / 2], fill=(255, 140, 40))
        f.L.ellipse([p0[0] - 36, p0[1] - 20, p0[0] + 36, p0[1] + 30], fill=(70, 74, 88))
        px, py = p2; f.L.ellipse([px - 14, py - 14, px + 14, py + 14], fill=(255, 250, 220))
        for i in range(10):
            u = (t * 3 + i * .17) % 1
            f.L.ellipse([px + (i - 5) * 14 * u - 3, py + 50 * u * u + 10 * u - 3, px + (i - 5) * 14 * u + 3, py + 50 * u * u + 10 * u + 3], fill=sc((255, 220, 120), 1 - u))
    # trabajadores y Elon recorriendo la línea
    place_person(base, "tech_w", mk(sf=50, ef=40, lean=14, hf=14, kf=20, smile=0, eyes=blink(t, 3, .2), head=10), 150, 1170, cam, k=1.0)
    place_person(base, "eng_f", mk(sf=20, ef=100, smile=.3, turn=.3, eyes=blink(t, 3.4, .6)), 470, 1190, cam, k=1.0, flip=True)
    ex = 820 + 70 * math.sin(t * .5)
    place_person(base, "elon_adult", walk_pose((t * .7) % 1, speed=.6, sf=-5, ef=20, smile=.5, turn=.3, head=-1, eyes=blink(t, 3.2)), ex, 1180, cam, k=1.05, flip=True)


def sub_launch(t, base, f):
    """Despegue espectacular + el propulsor regresa (reutilizable)."""
    # cielo del atardecer que se oscurece al subir
    rise = ease_in(prog(t, 1.0, 3.4)) if t > 1.0 else 0
    alt = 4200 * rise
    cam_y = 960 - 0.55 * alt
    sky = np.zeros((H, 1, 3), np.float32)
    ty = np.linspace(0, 1, H)[:, None]
    top = np.array((10, 16, 46), np.float32); mid = np.array((120, 70, 120), np.float32); low = np.array((255, 170, 100), np.float32)
    k = np.clip(ty + .0, 0, 1)
    dark = clamp(alt / 3200)
    g = np.where(k < .55, top + (mid - top) * (k / .55), mid + (low - mid) * ((k - .55) / .45))
    g = g * (1 - .75 * dark) + top * .75 * dark
    base[:] = g[:, None, :] if g.ndim == 2 else g
    base[:] = np.broadcast_to(g[:, None, :], (H, W, 3)) if False else base
    # estrellas
    rng = np.random.RandomState(5)
    for i in range(70):
        x, y = rng.rand() * W, rng.rand() * H * .6
        f.L.ellipse([x - 2, y - 2, x + 2, y + 2], fill=sc((255, 255, 230), .3 + .7 * dark))
    # suelo + torre (se alejan al subir)
    gy = 1560 + .55 * alt
    if gy < H + 100:
        f.L.rectangle([0, gy, W, H + 200], fill=(40, 34, 56))
        f.L.rectangle([60, gy - 640, 90, gy], fill=(60, 52, 80))
        for yy in range(int(gy - 620), int(gy), 50): f.L.line([(60, yy), (90, yy + 50)], fill=(60, 52, 80), width=5)
    # cohete
    rk = _c["rocket_l"] if "rocket_l" in _c else None
    if rk is None:
        _c["rocket_l"] = rocket_icon(640); rk = _c["rocket_l"]
    sep = t > 2.6
    shake = (4 * math.sin(t * 60) * (1 if t < 3.0 else .3))
    rx = 540 + shake
    ry = 1560 - alt * .45 + (0)
    ry = min(ry, 1560)
    ry_screen = 1560 - (alt * .45)
    ry_screen = max(ry_screen, 700) if t < 3.4 else 700 - 1200 * ease_in(prog(t, 3.4, 4.2))
    # llamas
    if t > .3:
        fl = 1 + .25 * math.sin(t * 50)
        L_ = 260 * fl * (0.6 + 1.2 * min(1, (t - .3) / 1.2)) * (1 if not sep else 1.1)
        yb = ry_screen
        for (wd, ln, col) in ((70, L_, (255, 120, 30)), (46, L_ * .8, (255, 210, 90)), (24, L_ * .55, (255, 255, 240))):
            f.L.polygon([(rx - wd, yb), (rx + wd, yb), (rx + wd * .3, yb + ln), (rx - wd * .3, yb + ln)], fill=sc(col, .95))
        f.add_glow_layer(Image.new("RGB", (W, H)), 1, 0)
    paste_np(base, rk, rx - rk.width / 2, ry_screen - rk.height + 10)
    # humo y nubes de vapor en el suelo
    rng = np.random.RandomState(12)
    for i in range(46):
        st = .6 + rng.rand() * 2.0
        u = prog(t, st, st + 1.6 + rng.rand())
        if 0 < u < 1:
            side = (-1) ** i
            x = 540 + side * (60 + 520 * ease_out(u)) * rng.uniform(.4, 1.0); y = gy - 20 - 40 * u - rng.rand() * 60 + (.55 * alt)
            r = 46 + 150 * u
            col = (255, 232, 214) if u < .4 else (210, 200, 216)
            f.L.ellipse([x - r, y - r * .7, x + r, y + r * .7], fill=sc(col, .30 * (1 - u)))
    # líneas de velocidad al subir
    if 1.6 < t:
        for i in range(30):
            x = rng.rand() * W; y = ((t * 2400 * (.5 + rng.rand()) + rng.rand() * 2000) % 2200) - 200
            f.L.line([(x, y), (x, y + 160)], fill=sc((255, 240, 220), .22 * ease(prog(t, 1.6, 2.4))), width=3)
    # PIP: el propulsor aterriza (cohetes reutilizables)
    if t > 2.7:
        pa = ease(prog(t, 2.7, 3.1))
        px0, py0, pw, ph = 640, 520, 380, 520
        d = ImageDraw.Draw(Image.new("RGB", (1, 1)))
        pim = Image.new("RGBA", (pw, ph), (12, 16, 40, 255)); pd = ImageDraw.Draw(pim)
        for yy in range(ph): pd.line([(0, yy), (pw, yy)], fill=(int(30 + 60 * yy / ph), int(30 + 40 * yy / ph), int(70 + 40 * yy / ph), 255))
        pd.rectangle([0, ph - 70, pw, ph], fill=(50, 44, 70)); pd.rectangle([pw / 2 - 90, ph - 76, pw / 2 + 90, ph - 66], fill=(110, 110, 124))
        u = prog(t, 2.8, 4.1)
        by = lerp(60, ph - 76 - 170, ease_out(u)) if u < 1 else ph - 76 - 170
        bx = pw / 2
        pd.rectangle([bx - 22, by, bx + 22, by + 170], fill=(244, 246, 250)); pd.rectangle([bx - 22, by + 40, bx + 22, by + 58], fill=(30, 32, 40))
        pd.polygon([(bx - 22, by + 6), (bx - 46, by + 14), (bx - 22, by + 24)], fill=(30, 32, 40)); pd.polygon([(bx + 22, by + 6), (bx + 46, by + 14), (bx + 22, by + 24)], fill=(30, 32, 40))
        legs = ease(prog(t, 3.5, 3.9))
        for sd in (-1, 1):
            pd.line([(bx + sd * 22, by + 160), (bx + sd * (22 + 40 * legs), by + 160 + 30 * legs + 10)], fill=(240, 240, 244), width=6)
        if u < 1:
            fl = 40 + 50 * (1 - u) + 10 * math.sin(t * 50)
            pd.polygon([(bx - 12, by + 170), (bx + 12, by + 170), (bx, by + 170 + fl)], fill=(255, 190, 70, 255))
        pd2 = ImageDraw.Draw(pim); pd2.rounded_rectangle([0, 0, pw - 1, ph - 1], radius=26, outline=(255, 255, 255, 255), width=6)
        m = Image.new("L", (pw, ph), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, pw - 1, ph - 1], radius=26, fill=255); pim.putalpha(m)
        paste_np(base, pim, px0, py0 - 40 * (1 - pa), pa)


def scene(t):
    f = Frame(bg=False); base = f.base
    if t < 3.5:
        sub_hangar(t, base, f)
    elif t < 4.0:
        a = np.zeros_like(base); b = np.zeros_like(base); fa = Frame(bg=False); fb = Frame(bg=False)
        sub_hangar(t, a, fa); sub_factory(t - 3.5, b, fb)
        base[:] = slide_blend(a, b, (t - 3.5) / .5, 1)
    elif t < 6.0:
        sub_factory(t - 3.5, base, f)
    elif t < 6.4:
        a = np.zeros_like(base); b = np.zeros_like(base); fa = Frame(bg=False); fb = Frame(bg=False)
        sub_factory(t - 3.5, a, fa); sub_launch(t - 6.0, b, fb)
        p = (t - 6.0) / .4
        base[:] = a * (1 - ease(p)) + b * ease(p) + 80 * math.sin(math.pi * p)
    else:
        sub_launch(t - 6.0, base, f)
    dust(f, t, seed=11, n=24, tint=(255, 230, 190), alpha=.3)
    return f.finish()
