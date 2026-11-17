"""Escenas 5-8."""
import math
import functools
import numpy as np
from PIL import Image, ImageDraw, ImageChops, ImageFilter
from gfx import *
from scenes_a import (_rng, island_layer, draw_waves, _bars, E, L, hand, dummy_head)

S5_STOP = 5.0
S6_INFLATE = (2.6, 6.2)
S8_CUTS = (2.0, 4.6, 6.4)


def xfade(a, b, t, t0, dur):
    """Disuelve de a() a b() en [t0, t0+dur]."""
    if t < t0:
        return a(t)
    if t > t0 + dur:
        return b(t)
    k = sm((t - t0) / dur)
    return Image.blend(a(t), b(t), k)


# ======================================================================= ESCENA 5
def lamp_pos(camx):
    return [(300 + 760 * i - camx) for i in range(-1, 5)]


def s5(t):
    camx = 560 * seg(t, 0.0, S5_STOP) ** 1.0
    rise = 900 * seg(t, 5.15, 7.7)
    yoff = rise * 0.75
    img = vgrad(W, H, [(0, (8, 8, 10)), (0.5, (26, 25, 24)), (1, (12, 11, 11))])
    d = ImageDraw.Draw(img)
    # paneles de muro lejano
    for i in range(-2, 12):
        x = i * 170 - (camx * 0.45) % 170
        d.line([(x, 0), (x, H)], fill=(18, 18, 18), width=4)
    for yy in range(-300, 1600, 210):
        d.line([(0, yy + yoff), (W, yy + yoff)], fill=(18, 18, 17), width=4)
    # eje de luz de luna en la parte alta (escotilla)
    sh = Image.new("L", (W, H), 0)
    ImageDraw.Draw(sh).polygon([(500, -400 + yoff), (840, -400 + yoff), (880, 560 + yoff), (460, 560 + yoff)], fill=255)
    sh = sh.filter(ImageFilter.GaussianBlur(40))
    img = add_light_mask(img, sh, (90, 120, 170), 0.55)
    d = ImageDraw.Draw(img)
    # tuberías gruesas (paralaje)
    for (y, wd, f, col) in ((430, 64, 0.55, (50, 48, 46)), (590, 44, 0.65, (44, 42, 40)), (1180, 90, 0.8, (40, 38, 36))):
        yy = y + yoff * 0.9
        d.rectangle([0, yy - wd / 2, W, yy + wd / 2], fill=col)
        d.rectangle([0, yy - wd / 2, W, yy - wd / 2 + 8], fill=mulc(col, 1.8))
        d.rectangle([0, yy + wd / 2 - 10, W, yy + wd / 2], fill=mulc(col, 0.5))
        for i in range(-1, 6):
            x = i * 360 - (camx * f) % 360
            d.rectangle([x - 12, yy - wd / 2 - 10, x + 12, yy + wd / 2 + 10], fill=mulc(col, 0.6))
    for (x0, wd, f) in ((140, 46, 0.7), (760, 36, 0.6), (1300, 56, 0.75)):
        x = (x0 - camx * f) % 1500 - 200
        d.rectangle([x, 0, x + wd, H], fill=(36, 35, 34))
        d.rectangle([x, 0, x + 8, H], fill=(78, 76, 72))
    # escalera (mundo x=1220)
    lx = 1220 - camx
    d.rectangle([lx - 70, -500 + yoff, lx - 56, 1520 + yoff], fill=(62, 60, 56))
    d.rectangle([lx + 56, -500 + yoff, lx + 70, 1520 + yoff], fill=(62, 60, 56))
    for yy in range(-500, 1520, 62):
        d.rectangle([lx - 70, yy + yoff, lx + 70, yy + yoff + 10], fill=(80, 78, 72))
    # suelo
    fy = 1520 + yoff
    d.rectangle([0, fy, W, H + 900], fill=(16, 15, 14))
    d.rectangle([0, fy, W, fy + 10], fill=(60, 58, 54))
    for i in range(-2, 14):
        x = i * 90 - camx % 90
        d.line([(x, fy + 10), (x - 60, fy + 160)], fill=(26, 25, 24), width=4)
    # lámparas
    lamps = lamp_pos(camx)
    for lxp in lamps:
        ly = 330 + yoff
        d.line([(lxp, ly - 400), (lxp, ly)], fill=(12, 12, 12), width=4)
        d.polygon([(lxp - 30, ly + 14), (lxp + 30, ly + 14), (lxp + 18, ly - 14), (lxp - 18, ly - 14)], fill=(26, 26, 26))
    for lxp in lamps:
        ly = 330 + yoff
        cone = soft_mask([([(lxp - 16, ly + 16), (lxp + 16, ly + 16), (lxp + 340, fy), (lxp - 340, fy)], 255)], 6, 4)
        img = add_light_mask(img, cone, (255, 176, 90), 0.32)
        add_glow(img, lxp, ly + 10, 200, (255, 190, 110), 0.7)
    # personajes
    d = ImageDraw.Draw(img)
    base = 1520 + yoff
    def lf(x):
        b = 0.28
        for lxp in lamps:
            b = max(b, 0.28 + 0.85 * math.exp(-((x - lxp) / 230) ** 2))
        return min(b, 1.1)
    walking = t < S5_STOP + 0.2
    ph = camx * 0.036
    crouch = 0.55
    xs = {"frank": 560, "john": 330, "clar": 100}
    for who, off in (("clar", 0), ("john", 1.6), ("frank", 3.1)):
        x = xs[who]
        if walking:
            mv = clamp((S5_STOP + 0.2 - t) / 0.4)
            P = walk_pose(ph + off, crouch, 10, 12, 7, 5, head=-4)
            P["head"] = -4 + 3 * math.sin(t * 2 + off)
        else:
            P = pose(hip=(0, -35), lean=26, fF=(9, 0), fB=(-7, 0), hF=(26, -35), hB=(8, -33), head=-18 if who != "frank" else 0)
        sy = base
        if who == "frank" and t > 5.1:
            c = seg(t, 5.1, 5.6)
            p = t * 6.0
            P = pose(hip=(-2, -44), lean=lerp(26, 8, c), fF=(12, -3 + 11 * max(0, math.sin(p))), fB=(8, -2 + 11 * max(0, -math.sin(p))),
                     hF=(24, -86 + 10 * math.sin(p)), hB=(22, -92 - 10 * math.sin(p)), head=-8)
            sy = base - rise
        k = lf(x)
        draw_man(img, who, x, sy, 560, P, "side", 1, light=(k, k * 0.86, k * 0.74), rim=((255, 180, 110), -4, 0, 2.2))
    # vapor
    sx = (900 - camx * 1.0) % 1700 - 300
    for i in range(14):
        tt = (t * 0.5 + i / 14.0) % 1.0
        add_glow(img, sx + math.sin(tt * 6 + i) * 20 + tt * 40, 1500 + yoff - tt * 520, 40 + tt * 120, (150, 150, 150), 0.12 * (1 - tt))
    # gotas
    for i in range(3):
        tt = (t * 0.9 + i * 0.37) % 1.0
        if tt < 0.55:
            q = (300 + i * 320 - (camx * 0.2) % 100, 700 + yoff + tt * 1.8 * 800 * tt)
            d = ImageDraw.Draw(img)
            d.ellipse([q[0] - 2, q[1] - 6, q[0] + 2, q[1] + 3], fill=(150, 170, 190))
    img = fog(img, t, 900 + yoff * 0.4, 1700 + yoff * 0.4, (40, 40, 40), 0.35, speed=30, seed=51)
    return img


# ======================================================================= ESCENA 6
@functools.lru_cache(maxsize=1)
def _rocks():
    r = _rng(61)
    pts = [(-100, H + 50)]
    x = -100
    while x < W + 150:
        pts.append((x, 1330 + r.randint(-26, 22) + 40 * math.sin(x / 220)))
        x += r.randint(40, 90)
    pts += [(W + 100, H + 50)]
    return pts


def s6(t):
    z = lerp(1.0, 1.13, t / 8.0)
    cam = Cam(W / 2 + lerp(40, -20, t / 8), 930, z)
    sky = vgrad(W, H, [(0, (4, 6, 12)), (0.36, (8, 14, 26)), (0.5, (24, 38, 58)), (0.505, (7, 12, 20)), (0.76, (3, 6, 11)), (1, (2, 3, 6))])
    img = cam.view(sky.resize((W * 2, H * 2)), -W / 2, -H / 2, 2.0) if False else sky
    # el fondo se dibuja con transformación manual simple (sin cam para el cielo)
    d = ImageDraw.Draw(img)
    r = _rng(62)
    for i in range(110):
        x, y = r.randint(0, W), int(abs(r.randn()) * 220)
        b = int(70 + r.rand() * 130)
        d.point((x, y), fill=(b, b, b + 20))
    gl = cam.p(0, 830)[1]
    # luces de San Francisco
    for i in range(110):
        x = 520 + r.randn() * 330
        y = 956 - r.rand() * 10
        b = 0.4 + 0.6 * r.rand() * (0.8 + 0.2 * math.sin(t * 3 + i))
        d.rectangle([x, y, x + 3, y + 3], fill=(int(255 * b), int(190 * b), int(110 * b)))
    img = draw_waves(img, cam, t, 836, 15, (84, 108, 136), 0.5, 7, 1.6, seed=6, ymax=1400)
    # reflejo de luces
    for i in range(30):
        x = 520 + r.randn() * 300
        d.line([(x, 970), (x + math.sin(t * 2 + i) * 6, 1030 + r.rand() * 80)], fill=(60, 44, 28), width=2)
    # rocas / orilla
    d = ImageDraw.Draw(img)
    rk = cam.pts(_rocks())
    d.polygon(rk, fill=(11, 12, 15))
    d.line(rk, fill=(46, 54, 66), width=3)
    ground = cam.p(0, 1560)[1]
    d.rectangle([0, ground, W, H], fill=(8, 9, 11))
    # espuma contra las rocas
    for i in range(30):
        x = 30 + i * 36
        q = cam.p(x, 1336 + 30 * math.sin(x / 220))
        wv = 0.5 + 0.5 * math.sin(t * 1.9 + i * 0.8)
        rw, rh = (14 + 10 * wv) * cam.z, (4 + 3 * wv) * cam.z
        c = int(110 + 100 * wv)
        d.ellipse([q[0] - rw, q[1] - rh, q[0] + rw, q[1] + rh], fill=(c, c + 8, c + 18))
    # balsa
    p = seg(t, S6_INFLATE[0], S6_INFLATE[1])
    bx0, bx1 = 330 - 40 * p, 880 + 40 * p
    by = 1566
    hh = lerp(12, 150, p)
    ys = by - hh
    q0, q1 = cam.p(bx0, ys), cam.p(bx1, by)
    col = (66, 74, 50)
    rad = (q1[1] - q0[1]) / 2
    d.rounded_rectangle([q0[0], q0[1], q1[0], q1[1]], radius=max(3, rad), fill=col)
    d.rounded_rectangle([q0[0] + 8, q0[1] + 4, q1[0] - 8, q0[1] + 4 + max(3, rad * 0.5)], radius=max(2, rad * 0.25), fill=(98, 110, 76))
    for i in range(1, 6):
        x = lerp(q0[0], q1[0], i / 6)
        d.line([(x, q0[1] + 4), (x - 6, q1[1] - 4)], fill=(44, 50, 34), width=3)
    # manguera + fuelle
    fx = cam.p(228, 1566)
    comp = 0.5 + 0.5 * math.sin(t * 7.0) if p < 1 and t > 2.4 else 0.3
    bw = (120 + 80 * comp) * cam.z
    d.line([(fx[0] + 40 * cam.z, fx[1] - 24 * cam.z), cam.p(bx0 + 20, by - hh * 0.4)], fill=(30, 30, 30), width=int(8 * cam.z))
    d.rectangle([fx[0] - bw, fx[1] - 54 * cam.z, fx[0] + 30 * cam.z, fx[1] - 6 * cam.z], fill=(120, 96, 60))
    for i in range(7):
        x = fx[0] - bw + i * (bw + 30 * cam.z) / 6
        d.line([(x, fx[1] - 54 * cam.z), (x, fx[1] - 6 * cam.z)], fill=(60, 44, 28), width=3)
    # hombres
    u = 430 * cam.z
    arrive = seg(t, 0.0, 2.3)
    def man(who, xfinal, xstart, pk, face):
        x = lerp(xstart, xfinal, arrive)
        walking = arrive < 0.995
        if walking:
            P = walk_pose(t * 5.2 + pk, 0.55, 10, 12, 7, 4)
        else:
            P = None
        return x, P, walking
    # Frank: bombea
    fxm, P, w = man("frank", 150, -140, 0, 1)
    if not w:
        s = math.sin(t * 7.0)
        P = pose(hip=(-2, -27), lean=32, fF=(12, 0), fB=(-10, -2), hF=(22, -30 + 4 * s), hB=(22 + 2 * s, -26), head=10)
    draw_man(img, "frank", cam.p(fxm, 1566)[0], cam.p(fxm, 1566)[1], u, P, "side", 1, light=(0.55, 0.5, 0.5), rim=((140, 170, 220), -4, 0, 2.0))
    jx, P, w = man("john", 600, -300, 1.3, 1)
    if not w:
        P = pose(hip=(-2, -26), lean=30, fF=(14, 0), fB=(-10, -2), hF=(24, -34 + 3 * math.sin(t * 3)), hB=(20, -28), head=8)
    draw_man(img, "john", cam.p(jx, 1566)[0], cam.p(jx, 1566)[1], u, P, "side", 1, light=(0.55, 0.5, 0.5), rim=((140, 170, 220), -4, 0, 2.0))
    cx_, P, w = man("clar", 930, 1500, 2.4, -1)
    if not w:
        P = pose(hip=(-2, -28), lean=26, fF=(12, 0), fB=(-10, -2), hF=(24, -40 + 6 * math.sin(t * 2.2)), hB=(20, -34), head=-6)
    draw_man(img, "clar", cam.p(cx_, 1566)[0], cam.p(cx_, 1566)[1], u, P, "side", -1, light=(0.55, 0.5, 0.5), rim=((140, 170, 220), 4, 0, 2.0))
    # luna invisible: brillo frío del cielo
    img = fog(img, t, cam.p(0, 830)[1] - 130, cam.p(0, 830)[1] + 330, (62, 80, 104), 0.45, speed=-30, seed=62)
    img = fog(img, t, cam.p(0, 1330)[1] - 200, cam.p(0, 1330)[1] + 200, (50, 66, 88), 0.35, speed=40, seed=63)
    return img


# ======================================================================= ESCENA 7
def _behind(t):
    img = vgrad(W, H, [(0, (4, 6, 12)), (0.25, (8, 14, 26)), (0.37, (28, 42, 62)), (0.375, (7, 12, 20)), (0.6, (3, 6, 12)), (1, (2, 3, 7))])
    d = ImageDraw.Draw(img)
    r = _rng(71)
    for i in range(90):
        x, y = r.randint(0, W), int(abs(r.randn()) * 200)
        b = int(70 + r.rand() * 120)
        d.point((x, y), fill=(b, b, b + 20))
    cam = Cam(W / 2, H / 2, 1.0)
    hy = 720
    for i in range(70):
        x = 120 + abs(r.randn()) * 380 + r.rand() * 140
        y = hy - 4 - r.rand() * 10
        b = 0.4 + 0.6 * r.rand()
        d.rectangle([x, y, x + 3, y + 3], fill=(int(255 * b), int(190 * b), int(110 * b)))
    # camino de luna
    gl = Image.new("RGB", (W, H), (0, 0, 0))
    gd = ImageDraw.Draw(gl)
    for i in range(50):
        yy = hy + 10 + i * i * 0.12 + i * 6
        wd = 12 + i * 3
        a = int(clamp(1 - i / 50) * 120 * (0.5 + 0.5 * math.sin(t * 3 + i * 2)))
        gd.ellipse([780 - wd, yy - 2, 780 + wd, yy + 2], fill=(a, a + 8, a + 20))
    img = ImageChops.add(img, gl)
    img = draw_waves(img, cam, -t * 0.9, hy, 18, (90, 114, 140), 0.55, 10, 1.7, seed=7, ymax=1500, wid=2)
    # balsa (parte trasera) con cabeceo
    bob = 10 * math.sin(t * 1.9) + 4 * math.sin(t * 3.3)
    tilt = 0.035 * math.sin(t * 1.5)
    # hombres sentados (de espaldas)
    base = 1460 + bob
    for who, x, ph in (("john", 330, 0.0), ("frank", 540, math.pi), ("clar", 750, 0.0)):
        s = math.sin(t * 2.6 + ph)
        side = -1 if x < 540 else 1
        hF = (11 + 14 * s, -30 + 10 * abs(s) * 0)
        P = pose(hip=(0, -22), lean=12, fF=(11, 0), fB=(-11, 0), hF=(side * 22 + 8 * s * side, -42 + 8 * s), hB=(-side * 6, -40), head=3 * s, eye=0.9)
        # el lado del remo: brazo derecho para x>540, izquierdo para x<540
        P["hF"] = (24 + 4 * s, -38 + 12 * s) if side > 0 else (-8, -38)
        P["hB"] = (-24 - 4 * s, -38 - 12 * s) if side < 0 else (8, -38)
        r_ = draw_man(img, who, x, base, 500, P, "back", 1, light=(0.5, 0.48, 0.5), rim=((140, 170, 220), 0, -4, 2.4))
        d = ImageDraw.Draw(img)
        hand_ = r_["hF"] if side > 0 else r_["hB"]
        tip = (hand_[0] + side * 170, hand_[1] + 120 + 20 * s)
        d.line([hand_, tip], fill=(96, 76, 52), width=8)
        d.ellipse([tip[0] - 30, tip[1] - 12, tip[0] + 30, tip[1] + 14], fill=(110, 86, 58))
        if s > 0.8:
            for k in range(8):
                px = tip[0] + (k - 4) * 8
                d.ellipse([px - 3, tip[1] - 10 - (k % 3) * 8, px + 3, tip[1] - 4 - (k % 3) * 8], fill=(180, 196, 214))
    # borde de la balsa (cubre piernas)
    d.rounded_rectangle([140, base - 20, 940, base + 180], radius=90, fill=(60, 68, 46))
    d.rounded_rectangle([156, base - 16, 924, base + 22], radius=24, fill=(94, 106, 72))
    d.line([(150, base + 40), (930, base + 40)], fill=(42, 48, 32), width=4)
    img = fog(img, t, hy - 80, hy + 260, (62, 80, 104), 0.5, speed=-28, seed=72)
    img = fog(img, t, 1100, 1700, (30, 40, 56), 0.2, speed=40, seed=73)
    return img


def aerial_island(img, cam, t, beam_on=True):
    r = _rng(81)
    pts = []
    n = 26
    for i in range(n):
        a = i / n * math.tau
        rad = 1 + 0.18 * math.sin(a * 3) + 0.1 * math.sin(a * 5 + 1) + r.rand() * 0.07
        pts.append((math.cos(a) * 520 * rad, math.sin(a) * 250 * rad))
    # spume
    d = ImageDraw.Draw(img)
    for sc, col in ((1.14, (30, 62, 74)), (1.08, (92, 124, 134)), (1.03, (170, 190, 196))):
        d.polygon(cam.pts([(x * sc, y * sc) for x, y in pts]), fill=col)
    d.polygon(cam.pts(pts), fill=(52, 58, 54))
    d.polygon(cam.pts([(x * 0.82, y * 0.8) for x, y in pts]), fill=(64, 70, 64))
    # edificio principal
    for (x0, y0, x1, y1, c) in ((-280, -60, 250, 20, (78, 76, 72)), (-340, -20, -280, 60, (70, 68, 64)), (250, -30, 340, 40, (72, 70, 66)),
                                (-160, 40, 100, 90, (66, 64, 60)), (300, 40, 340, 90, (58, 56, 52))):
        d.rectangle(cam.pts([(x0, y0), (x1, y1)]), fill=c)
    d.rectangle(cam.pts([(-280, -60), (250, -48)]), fill=(100, 98, 92))
    for i in range(18):
        x = -260 + i * 28
        q = cam.p(x, -20)
        d.rectangle([q[0], q[1], q[0] + 5 * cam.z, q[1] + 5 * cam.z], fill=(255, 196, 110))
    # faro/torre
    q = cam.p(-380, 30)
    add_glow(img, q[0], q[1], 80 * cam.z, (255, 238, 190), 0.9)
    if beam_on:
        a = t * 0.9
        L_ = 1500
        poly = [cam.p(-380, 30), cam.p(-380 + L_ * math.cos(a - 0.05), 30 + L_ * math.sin(a - 0.05)), cam.p(-380 + L_ * math.cos(a + 0.05), 30 + L_ * math.sin(a + 0.05))]
        img = beam(img, poly, (190, 214, 232), 0.28, 6, 4)
    return img


def _water_top(t, cam):
    tex = fbm(270, 480, 91, 5, 4)
    sx, sy = int(cam.cx * cam.z * 0.1) % 270, int(cam.cy * cam.z * 0.1 + t * 3) % 480
    tex = np.roll(np.roll(tex, sx, 1), sy, 0)
    a = np.asarray(Image.fromarray((tex * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), np.float32) / 255
    base = np.array([6, 20, 30], np.float32)
    hi = np.array([20, 52, 68], np.float32)
    arr = base + (hi - base) * (a[:, :, None] ** 1.6)
    return Image.fromarray(arr.astype(np.uint8))


def _aerial(t):
    e = seg(t, 4.0, 8.0)
    z = lerp(1.35, 0.3, e ** 0.8)
    cam = Cam(lerp(-60, 330, e), lerp(60, 330, e), z)
    img = _water_top(t, cam)
    # balsa y estela
    tr = clamp((t - 4.2) / 3.8)
    rx, ry = lerp(300, 1150, tr), lerp(130, 880, tr)
    ang = math.atan2(880 - 130, 1150 - 300)
    d = ImageDraw.Draw(img)
    for k in range(40):
        f = k / 40
        px, py = rx - math.cos(ang) * f * 500, ry - math.sin(ang) * f * 500
        spread = f * 70
        for s in (-1, 1):
            q = cam.p(px - math.sin(ang) * spread * s, py + math.cos(ang) * spread * s)
            a_ = clamp(1 - f)
            c = int(190 * a_)
            rad = max(1.0, (6 - 4 * f) * cam.z)
            d.ellipse([q[0] - rad, q[1] - rad, q[0] + rad, q[1] + rad], fill=(c, c + 10, c + 18))
    q = cam.p(rx, ry)
    rr = max(3.0, 20 * cam.z)
    d.ellipse([q[0] - rr * 1.6, q[1] - rr * 0.8, q[0] + rr * 1.6, q[1] + rr * 0.8], fill=(66, 74, 50))
    for k in (-1, 0, 1):
        d.ellipse([q[0] + k * rr - rr * 0.35, q[1] - rr * 0.35, q[0] + k * rr + rr * 0.35, q[1] + rr * 0.35], fill=(30, 24, 22))
    img = aerial_island(img, cam, t)
    img = fog(img, t, 300, 1500, (40, 56, 70), 0.22, speed=22, seed=92)
    return img


def s7(t):
    return xfade(_behind, _aerial, t, 3.8, 0.7)


# ======================================================================= ESCENA 8
def _dawn_island(t):
    k = 1.5
    sky = vgrad(W, H, [(0, (40, 44, 80)), (0.30, (120, 78, 110)), (0.46, (238, 150, 96)), (0.52, (250, 190, 120)),
                       (0.525, (122, 84, 80)), (0.7, (62, 44, 56)), (1, (22, 18, 28))])
    cam = Cam(540, 1000, 1.0 + 0.12 * t / 2.2)
    img = sky
    add_glow(img, 520, 990, 460, (255, 200, 120), 0.85)
    img = draw_waves(img, cam, t, 1004, 14, (252, 180, 120), 0.4, 6, 1.4, seed=8, ymax=1600)
    isl = island_layer(1.5, "dawn")
    # zoom manual
    box_z = cam.z
    il = Cam(540, 960, 1.0 + 0.12 * t / 2.2).view(isl, 0, 0, 1.5)
    img.paste(il, (0, 0), il)
    img = fog(img, t, 880, 1500, (230, 170, 140), 0.42, speed=26, seed=101)
    # luz de alarma roja
    ra = 0.5 + 0.5 * math.sin(t * 9)
    add_glow(img, 910, 910, 240, (255, 30, 20), 0.9 * ra)
    add_glow(img, 535, 940, 500, (255, 40, 30), 0.12 * ra)
    # vaivén de gaviotas
    d = ImageDraw.Draw(img)
    for i in range(3):
        x, y = 200 + i * 220 + t * 60, 420 + i * 60 + 12 * math.sin(t * 3 + i)
        d.line([(x - 18, y), (x, y - 8 * math.sin(t * 8 + i)), (x + 18, y)], fill=(40, 30, 40), width=3)
    return img


def _guard_room(t):
    img = vgrad(W, H, [(0, (14, 14, 16)), (0.45, (50, 50, 48)), (0.8, (34, 34, 32)), (1, (14, 14, 14))])
    d = ImageDraw.Draw(img)
    for i in range(18):
        d.line([(i * 62, 200), (i * 62 + 6, 1500)], fill=(36, 36, 35), width=5)
    d.rectangle([0, 1480, W, H], fill=(20, 20, 20))
    # barrotes
    _bars(d, 640, 700, 300, 1480, gap=44, w=16, col=(8, 8, 10), rails=(0.0, 0.5, 1.0))
    d.rectangle([620, 300, 660, 1480], fill=(10, 10, 12))
    # cama
    d.rectangle([80, 1480, 100, 1520], fill=(10, 10, 10))
    L_ = lambda *a: None
    d.rectangle([60, 1330, 560, 1380], fill=(84, 86, 80))
    d.rectangle([60, 1380, 560, 1392], fill=(24, 24, 24))
    d.rectangle([80, 1392, 96, 1480], fill=(20, 20, 20))
    d.rectangle([524, 1392, 540, 1480], fill=(20, 20, 20))
    d.ellipse([70, 1298, 250, 1344], fill=(176, 176, 166))
    tp = t - S8_CUTS[0]
    # manta (se levanta bruscamente en tp 1.25)
    pull = seg(tp, 1.2, 1.55)
    if pull < 0.99:
        lift = 150 * pull
        pts = [(110 + 600 * pull, 1330 - lift)] + [(110 + i * 24 + 700 * pull, 1330 - 70 * math.sin(math.pi * i / 18) * (1 - pull) - lift * (i / 18)) for i in range(19)] + [(560, 1332), (130, 1332)]
        d.polygon(pts, fill=(98, 92, 80))
        d.polygon([(260, 1330), (300, 1280), (420, 1274), (470, 1330)], fill=(104, 98, 86))
    # cabeza falsa
    if tp < 1.25:
        dummy_head(d, Cam(540, 960, 1), 190, 1300, 0.34, 1.0)
        # recorte de la almohada
    else:
        q = tp - 1.25
        hx = 190 + 90 * q - 0 * q
        hx = 190 - 120 * min(q, 0.6) + (-30 * max(0, q - 0.6))
        hy = 1300 + min(200, 560 * q * q) if q < 0.65 else 1500 - abs(math.sin((q - 0.65) * 8)) * 40 * math.exp(-(q - 0.65) * 2)
        dummy_head(d, Cam(540, 960, 1), hx, min(hy, 1500), 0.34, 1.0)
    # guardia
    gx = 840
    P = pose(lean=4, hip=(0, -50), fF=(7, 0), fB=(-5, 0), hF=(22, -66), hB=(8, -50), head=-4)
    if 0.45 < tp < 1.25:
        P = pose(lean=14, hip=(0, -48), fF=(8, 0), fB=(-5, 0), hF=(34, -58 - 8 * math.sin(tp * 10)), hB=(10, -52), head=6)
    elif tp >= 1.25:
        c = seg(tp, 1.25, 1.7)
        P = pose(lean=lerp(14, -10, c), hip=(lerp(0, 5, c), -50), fF=(8, 0), fB=(-5, 0), hF=(lerp(34, 14, c), lerp(-58, -96, c)),
                 hB=(lerp(10, 2, c), lerp(-52, -100, c)), head=lerp(6, -10, c), eye=lerp(1, 1.6, c))
    ra = 0.5 + 0.5 * math.sin(t * 9)
    draw_man(img, "guard", gx, 1480, 700, P, "side", -1, light=(0.62 + 0.4 * ra, 0.5, 0.5), rim=((255, 80, 60), -4, 0, 2.4), guard=True)
    d = ImageDraw.Draw(img)
    # linterna del guardia
    if tp < 1.3:
        beam_pts = [(760, 1250), (160, 1300 + 20 * math.sin(tp * 4)), (160, 1400), (760, 1290)]
        img = beam(img, beam_pts, (255, 240, 200), 0.38, 6, 5)
    # alarma roja
    red = Image.new("RGB", (W, H), (255, 20, 10))
    m = Image.new("L", (W, H), int(80 * ra))
    img = ImageChops.add(img, Image.composite(red, Image.new("RGB", (W, H), (0, 0, 0)), m.point(lambda v: int(v * 0.5))))
    add_glow(img, 540, 160, 520, (255, 30, 20), 0.5 * ra)
    # segundo guardia corriendo en primer plano
    if tp > 1.7:
        rx = lerp(1300, -400, clamp((tp - 1.7) / 1.0))
        draw_man(img, "guard", rx, 1560, 900, walk_pose(t * 11, 0.0, 20, 18, 12, 10), "side", -1, light=(0.1, 0.07, 0.1), guard=True)
    img = fog(img, t, 0, 1200, (30, 12, 12), 0.2, speed=10, seed=111)
    return img


def _empty_sea(t):
    k = (t - S8_CUTS[1]) / 1.9
    hy = lerp(880, 940, k)
    sky = vgrad(W, H, [(0, (70, 74, 110)), (0.22, (150, 104, 120)), (0.38, (240, 168, 112)), (0.46, (252, 206, 140)),
                       (0.47, (156, 112, 100)), (0.62, (74, 58, 70)), (1, (22, 20, 32))])
    cam = Cam(540, 960, 1.0)
    img = sky
    add_glow(img, 600, hy, 520, (255, 214, 150), 0.9)
    gl = Image.new("RGB", (W, H), (0, 0, 0))
    gd = ImageDraw.Draw(gl)
    for i in range(50):
        yy = hy + 10 + i * i * 0.12 + i * 5
        wd = 16 + i * 4
        a = int(clamp(1 - i / 50) * 170 * (0.5 + 0.5 * math.sin(t * 3 + i * 2)))
        gd.ellipse([600 - wd, yy - 2, 600 + wd, yy + 2], fill=(a, int(a * 0.8), int(a * 0.5)))
    img = ImageChops.add(img, gl)
    img = draw_waves(img, cam, t, hy, 22, (255, 200, 150), 0.5, 11, 1.2, seed=9, ymax=1800, wid=2)
    img = fog(img, t, hy - 140, hy + 280, (250, 190, 150), 0.40, speed=-20, seed=121)
    d = ImageDraw.Draw(img)
    for i, (gx, gy) in enumerate(((820, 560), (700, 620))):
        x = gx - 40 * k * 20 + 100 * k
        y = gy + 10 * math.sin(t * 2 + i)
        d.line([(x - 20, y), (x, y - 9 * math.sin(t * 6 + i)), (x + 20, y)], fill=(54, 40, 50), width=3)
    return img


def _fog_aerial(t):
    e = seg(t, S8_CUTS[2], 8.0)
    cam = Cam(0, 0, lerp(0.62, 0.42, e))
    img = _water_top(t, cam)
    img = aerial_island(img, cam, t * 0.5, beam_on=False)
    for s_, a_, sp in ((7, 0.85, 20), (8, 0.75, -26), (9, 0.6, 14)):
        img = fog(img, t, 0, H, (150, 158, 168), a_, speed=sp, seed=130 + s_)
    return img


def s8(t):
    c0, c1, c2 = S8_CUTS
    if t < c0 - 0.35:
        return _dawn_island(t)
    if t < c0 + 0.35:
        return Image.blend(_dawn_island(t), _guard_room(t), sm((t - (c0 - 0.35)) / 0.7))
    if t < c1 - 0.3:
        return _guard_room(t)
    if t < c1 + 0.3:
        return Image.blend(_guard_room(t), _empty_sea(t), sm((t - (c1 - 0.3)) / 0.6))
    if t < c2 - 0.3:
        return _empty_sea(t)
    if t < c2 + 0.4:
        return Image.blend(_empty_sea(t), _fog_aerial(t), sm((t - (c2 - 0.3)) / 0.7))
    return _fog_aerial(t)
