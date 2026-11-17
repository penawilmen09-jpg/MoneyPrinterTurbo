"""Escenas 1-4."""
import math
import functools
import numpy as np
from PIL import Image, ImageDraw, ImageChops, ImageFilter
from gfx import *

# ----------------------------------------------------------------- tiempos (sincronía con audio)
S1_WAVES = [0.9, 2.7, 4.3, 5.9]            # impactos de ola contra las rocas (t local)
S2_GUARD = (4.4, 6.9)                      # silueta de guardia pasando
S3_BEATS = 0.5                              # periodo de raspado


def _rng(seed):
    return np.random.RandomState(seed)


# ======================================================================= ESCENA 1
def island_layer(k, palette="night"):
    """Isla de Alcatraz como capa RGBA (mundo 1080x1920, k px/unidad)."""
    ss = 1
    lay = Image.new("RGBA", (int(W * k), int(H * k)), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    K = lambda pts: [(x * k, y * k) for x, y in pts]
    rock = (13, 17, 25) if palette == "night" else (30, 24, 28)
    rock_hi = (26, 34, 48) if palette == "night" else (96, 66, 62)
    bld = (10, 13, 20) if palette == "night" else (44, 32, 36)
    r = _rng(11)
    # masa rocosa
    top = []
    xs = np.linspace(110, 950, 22)
    for i, x in enumerate(xs):
        prof = 1 - abs((x - 530) / 430) ** 1.7
        y = 1190 - 215 * prof - r.rand() * 26
        top.append((x, y))
    poly = [(90, 1215)] + top + [(970, 1215)]
    d.polygon(K(poly), fill=rock)
    # luz de borde en la cresta
    d.line(K(top), fill=rock_hi, width=int(3 * k))
    # grietas / estratos
    for i in range(26):
        x = r.randint(130, 930)
        y0 = 1190 - 215 * (1 - abs((x - 530) / 430) ** 1.7) + 20
        d.line(K([(x, y0), (x + r.randint(-40, 40), y0 + r.randint(30, 120))]), fill=mulc(rock, 0.7), width=int(2 * k))
    # cuerpo de la prisión (celdas)
    d.rectangle(K([(300, 905), (770, 990)]), fill=bld)
    d.polygon(K([(300, 905), (535, 872), (770, 905)]), fill=mulc(bld, 1.15))
    d.line(K([(300, 905), (535, 872), (770, 905)]), fill=rock_hi, width=int(2 * k))
    # ventanas encendidas
    rr = _rng(5)
    for row, y in enumerate((920, 950)):
        for i in range(24):
            x = 318 + i * 18.6
            on = rr.rand() > 0.35
            col = (255, 196, 110) if on else (30, 36, 48)
            if palette != "night":
                col = (255, 214, 140) if on else (60, 46, 52)
            d.rectangle(K([(x, y), (x + 8, y + 14)]), fill=col)
    # edificio auxiliar
    d.rectangle(K([(190, 940), (300, 992)]), fill=mulc(bld, 1.05))
    d.rectangle(K([(770, 925), (850, 992)]), fill=mulc(bld, 1.05))
    for x in (205, 235, 265):
        d.rectangle(K([(x, 958), (x + 10, 972)]), fill=(255, 196, 110) if x != 235 else (40, 46, 58))
    # torre del agua
    d.polygon(K([(805, 925), (812, 860), (830, 860), (837, 925)]), fill=bld)
    d.rectangle(K([(796, 818), (846, 862)]), fill=bld)
    d.polygon(K([(796, 818), (821, 800), (846, 818)]), fill=bld)
    for x in (806, 822, 838):
        d.line(K([(x, 862), (x - 4 + (x - 822) * 0.2, 925)]), fill=bld, width=int(2 * k))
    # faro
    d.polygon(K([(262, 992), (270, 800), (282, 800), (290, 992)]), fill=mulc(bld, 1.5) if palette == "night" else mulc(bld, 1.7))
    d.rectangle(K([(258, 782), (294, 802)]), fill=bld)
    d.rectangle(K([(264, 770), (288, 784)]), fill=(255, 238, 190))
    d.polygon(K([(258, 770), (276, 752), (294, 770)]), fill=bld)
    # torre de guardia
    d.rectangle(K([(906, 940), (914, 1070)]), fill=bld)
    d.rectangle(K([(888, 920), (932, 944)]), fill=bld)
    d.polygon(K([(884, 920), (910, 900), (936, 920)]), fill=bld)
    d.rectangle(K([(896, 927), (924, 937)]), fill=(255, 200, 120))
    # valla / muro perimetral
    d.line(K([(210, 1010), (860, 1010)]), fill=mulc(bld, 0.9), width=int(3 * k))
    for x in range(210, 860, 22):
        d.line(K([(x, 1002), (x, 1014)]), fill=mulc(bld, 0.9), width=int(2 * k))
    return lay


@functools.lru_cache(maxsize=2)
def _s1_bg():
    k = 1.5
    img = vgrad(int(W * k), int(H * k), [(0, (4, 6, 14)), (0.28, (9, 14, 30)), (0.5, (30, 46, 70)), (0.52, (8, 14, 24)),
                                         (0.74, (4, 8, 15)), (1, (1, 3, 7))])
    d = ImageDraw.Draw(img)
    r = _rng(3)
    for i in range(160):
        x, y = r.randint(0, int(W * k)), int(abs(r.randn()) * 380 * k)
        if y > 960 * k:
            continue
        b = int(60 + r.rand() * 140)
        d.point((x, y), fill=(b, b, min(255, b + 20)))
    # luna
    mx, my = 830 * k, 300 * k
    sp = Image.new("RGB", img.size, (0, 0, 0))
    img = img.copy()
    big = Image.new("RGB", img.size, (0, 0, 0))
    ImageDraw.Draw(big).ellipse([mx - 55 * k, my - 55 * k, mx + 55 * k, my + 55 * k], fill=(214, 222, 236))
    img = ImageChops.add(img, big.filter(ImageFilter.GaussianBlur(1.5)))
    gl = Image.new("RGB", img.size, (0, 0, 0))
    gd = ImageDraw.Draw(gl)
    for rad, c in ((330, (14, 20, 30)), (210, (22, 32, 48)), (120, (34, 46, 66))):
        gd.ellipse([mx - rad * k, my - rad * k, mx + rad * k, my + rad * k], fill=c)
    gl = gl.filter(ImageFilter.GaussianBlur(70 * k))
    img = ImageChops.add(img, gl)
    # horizonte: luces de la ciudad
    d = ImageDraw.Draw(img)
    for i in range(90):
        x = 20 + abs(r.randn()) * 220 + r.rand() * 40
        y = 996 - r.rand() * 12
        b = 0.5 + 0.5 * r.rand()
        d.rectangle([x * k, y * k, (x + 2.4) * k, (y + 2.4) * k], fill=(int(255 * b), int(190 * b), int(110 * b)))
    # línea del horizonte brillo tenue
    d.rectangle([0, 998 * k, W * k, 1004 * k], fill=(24, 36, 56))
    return img


@functools.lru_cache(maxsize=2)
def _s1_island():
    return island_layer(1.5, "night")


def draw_waves(img, cam, t, y_h, rows, col, alpha, amp, speed, seed=1, ymax=1920, wid=2, xr=(-200, 1300)):
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    r = _rng(seed)
    for i in range(rows):
        f = (i + 1) / rows
        y_w = y_h + 8 + (ymax - y_h) * f ** 1.9
        a = amp * (0.25 + f * 1.1)
        ph = r.rand() * 6.28
        lam = 80 + 220 * f
        pts = []
        for x in range(xr[0], xr[1], 28):
            yy = y_w + a * math.sin(x / lam * 2 + t * speed * (0.5 + f) + ph) + a * 0.4 * math.sin(x / (lam * 0.45) - t * speed * 0.7 + ph)
            pts.append(cam.p(x, yy))
        d.line(pts, fill=int(255 * (0.35 + 0.65 * f)), width=max(1, int((wid + 4 * f) * cam.z)))
    m = m.filter(ImageFilter.GaussianBlur(1.2))
    return paint_mask(img, m, col, alpha)


def spray(img, cam, t, impacts, x_range, y0, seed=2):
    d = ImageDraw.Draw(img)
    r = _rng(seed)
    for n, ti in enumerate(impacts):
        tau = t - ti
        if tau < 0 or tau > 1.5:
            continue
        x0 = x_range[0] + (x_range[1] - x_range[0]) * ((n * 0.37 + 0.1) % 1)
        for j in range(26):
            vx = (r.rand() - 0.5) * 150
            vy = -(160 + r.rand() * 260)
            px = x0 + vx * tau + (r.rand() - 0.5) * 30
            py = y0 + vy * tau + 520 * tau * tau
            if py > y0 + 6:
                continue
            a = clamp(1 - tau / 1.5)
            q = cam.p(px, py)
            rad = max(1.0, (3.4 - 2 * tau) * cam.z)
            c = (int(200 * a), int(214 * a), int(228 * a))
            d.ellipse([q[0] - rad, q[1] - rad, q[0] + rad, q[1] + rad], fill=c)
    return img


def s1(t):
    bg, isl = _s1_bg(), _s1_island()
    e = sm(t / 7.2)
    cam = Cam(lerp(520, 520, e), lerp(1010, 905, e), lerp(1.0, 1.72, e ** 1.1))
    img = cam.view(bg, 0, 0, 1.5)
    # brillo de la luna en el agua
    gl = Image.new("RGB", (W, H), (0, 0, 0))
    gd = ImageDraw.Draw(gl)
    for i in range(60):
        yy = 1010 + i * i * 0.18 + i * 5
        wd = 6 + i * 1.7
        sx = 830 + math.sin(t * 1.3 + i * 0.7) * (6 + i * 0.5)
        a = int(clamp(1 - i / 62) * 110 * (0.6 + 0.4 * math.sin(t * 2.4 + i * 1.9)))
        q = cam.p(sx, yy)
        gd.ellipse([q[0] - wd * cam.z * 0.5, q[1] - 2 * cam.z, q[0] + wd * cam.z * 0.5, q[1] + 2 * cam.z], fill=(a, a + 8, a + 20))
    img = ImageChops.add(img, gl)
    # olas
    img = draw_waves(img, cam, t, 1004, 16, (88, 112, 140), 0.55, 6, 1.4, seed=4, ymax=1500)
    # isla
    il = cam.view(isl, 0, 0, 1.5)
    img.paste(il, (0, 0), il)
    # espuma en la base de la isla (rompiente)
    d = ImageDraw.Draw(img)
    base = 1206
    for i in range(46):
        x = 95 + i * 19.5
        ph = i * 0.9
        wv = 0.5 + 0.5 * math.sin(t * 2.0 + ph)
        for ti in S1_WAVES:
            wv += 1.2 * math.exp(-((t - ti) * 2.2) ** 2) * (0.6 + 0.4 * math.sin(i))
        q = cam.p(x, base + 4 + 2 * math.sin(t + i))
        rw = (10 + 14 * wv) * cam.z
        rh = (3 + 3.5 * wv) * cam.z
        c = int(clamp(70 + 90 * wv, 0, 235))
        d.ellipse([q[0] - rw, q[1] - rh, q[0] + rw, q[1] + rh], fill=(c, c + 8, c + 18))
    img = spray(img, cam, t, S1_WAVES, (150, 900), base - 4)
    # haz del faro
    th = 0.12 + 0.55 * math.sin(t * 0.85)
    fx, fy = 276, 775
    L = 1500
    a1, a2 = th - 0.030, th + 0.030
    pts = [cam.p(fx, fy), cam.p(fx + L * math.cos(a1), fy + L * math.sin(a1)), cam.p(fx + L * math.cos(a2), fy + L * math.sin(a2))]
    img = beam(img, pts, (190, 210, 235), 0.34, 6, 4)
    pts2 = [cam.p(fx, fy), cam.p(fx - L * math.cos(th * 0.8), fy - L * 0.1 * math.sin(th)), cam.p(fx - L * math.cos(th * 0.8), fy + 60)]
    qx, qy = cam.p(fx, fy)
    add_glow(img, qx, qy, 150 * cam.z, (255, 236, 180), 0.9)
    # ventanas brillo
    wx, wy = cam.p(535, 940)
    add_glow(img, wx, wy, 330 * cam.z, (255, 160, 70), 0.16)
    # niebla
    img = fog(img, t, 0, 700, (20, 28, 46), 0.55, speed=26, seed=21)
    img = fog(img, t + 10, cam.p(0, 1000)[1] - 160, cam.p(0, 1000)[1] + 260, (78, 96, 120), 0.50, speed=-34, seed=22)
    img = fog(img, t + 3, cam.p(0, 1180)[1] - 260, cam.p(0, 1180)[1] + 340, (58, 74, 96), 0.45, speed=48, seed=23)
    return img


# ======================================================================= ESCENA 2
def _bars(d, x0, x1, y0, y1, gap=38, w=13, col=(12, 13, 15), rails=(0.02, 0.5, 0.98)):
    x = x0
    while x <= x1:
        d.rectangle([x, y0, x + w, y1], fill=col)
        x += gap
    for rr in rails:
        yy = y0 + (y1 - y0) * rr
        d.rectangle([x0, yy - 6, x1 + w, yy + 6], fill=col)


@functools.lru_cache(maxsize=2)
def _s2_bg():
    k = 1.4
    img = Image.new("RGB", (int(W * k), int(H * k)), (8, 9, 11))
    d = ImageDraw.Draw(img)
    S = lambda *v: [c * k for c in v]
    # estructura exterior: niveles superior e inferior (celdas lejanas, oscuras)
    for (ya, yb) in ((90, 560), (1500, 1880)):
        d.rectangle(S(0, ya, W, yb), fill=(11, 12, 15))
        for cx in range(20, W, 215):
            d.rectangle(S(cx, ya + 30, cx + 190, yb - 20), fill=(16, 17, 20))
            _bars(d, cx + 8, cx + 180, ya + 30, yb - 20, gap=22, w=8, col=(6, 7, 9))
    # pasarelas
    d.rectangle(S(0, 560, W, 640), fill=(30, 31, 33))
    d.rectangle(S(0, 1440, W, 1500), fill=(26, 27, 29))
    # --- interior de la celda ---
    wall = vgrad(int(640 * k), int(800 * k), [(0, (34, 34, 33)), (0.5, (62, 62, 58)), (1, (40, 39, 36))])
    n = fbm_img(int(640 * k), int(800 * k), 31, 5, 5)
    na = np.asarray(n, np.float32)[:, :, None] / 255
    wa = np.asarray(wall, np.float32) * (0.72 + 0.5 * na)
    # manchas de humedad y vetas verticales
    rr = _rng(9)
    for i in range(14):
        x = rr.randint(0, int(640 * k))
        wa[:, x:x + rr.randint(2, 10), :] *= 0.86
    wall = Image.fromarray(np.clip(wa, 0, 255).astype(np.uint8))
    img.paste(wall, (0, int(640 * k)))
    d = ImageDraw.Draw(img)
    # grietas
    for i in range(6):
        x = rr.randint(60, 600)
        y = rr.randint(700, 1100)
        pts = [(x, y)]
        for j in range(6):
            x += rr.randint(-14, 14)
            y += rr.randint(18, 40)
            pts.append((x, y))
        d.line([(a * k, b * k) for a, b in pts], fill=(24, 24, 24), width=int(2 * k))
    # suelo de la celda
    d.rectangle(S(0, 1440 - 6, 640, 1450), fill=(20, 20, 20))
    # lavabo + tubería
    d.rectangle(S(90, 1084, 280, 1140), fill=(150, 152, 150))
    d.rectangle(S(90, 1084, 280, 1094), fill=(190, 192, 190))
    d.polygon(S(120, 1140, 250, 1140, 220, 1176, 150, 1176), fill=(110, 112, 110))
    d.rectangle(S(170, 1176, 200, 1260), fill=(70, 72, 70))
    d.rectangle(S(160, 1050, 175, 1084), fill=(98, 100, 98))
    # rejilla de ventilación (en la parte baja de la pared)
    vx0, vy0, vx1, vy1 = 110, 1272, 300, 1392
    d.rectangle(S(vx0 - 10, vy0 - 10, vx1 + 10, vy1 + 10), fill=(46, 46, 44))
    d.rectangle(S(vx0, vy0, vx1, vy1), fill=(6, 6, 7))
    for i in range(9):
        y = vy0 + 8 + i * 13
        d.rectangle(S(vx0 + 4, y, vx1 - 4, y + 6), fill=(70, 70, 66))
    for (bx, by) in ((vx0 - 4, vy0 - 4), (vx1 + 4, vy0 - 4), (vx0 - 4, vy1 + 4), (vx1 + 4, vy1 + 4)):
        d.ellipse(S(bx - 5, by - 5, bx + 5, by + 5), fill=(88, 88, 84))
    # catre (litera plegable)
    d.rectangle(S(390, 1196, 640, 1226), fill=(70, 62, 52))
    d.rectangle(S(390, 1226, 640, 1234), fill=(30, 30, 30))
    d.line(S(404, 1234, 404, 1440), fill=(26, 26, 26), width=int(6 * k))
    d.line(S(630, 1234, 630, 1300), fill=(26, 26, 26), width=int(6 * k))
    d.line(S(500, 1234, 560, 1440), fill=(34, 34, 34), width=int(3 * k))
    d.polygon(S(400, 1196, 470, 1196, 460, 1166, 408, 1166), fill=(150, 146, 134))  # almohada
    # barrotes de la celda
    d.rectangle(S(630, 640, 700, 1440), fill=(10, 10, 12))
    _bars(d, 646, 1020 if False else 700, 640, 1440, gap=34, w=14, col=(8, 8, 10), rails=(0.0, 0.34, 0.66, 1.0))
    # pasillo lejano
    cor = vgrad(int(380 * k), int(800 * k), [(0, (22, 20, 20)), (0.5, (52, 46, 42)), (1, (30, 26, 24))])
    ca = np.asarray(cor, np.float32) * (0.7 + 0.5 * np.asarray(fbm_img(int(380 * k), int(800 * k), 41, 4, 4), np.float32)[:, :, None] / 255)
    img.paste(Image.fromarray(np.clip(ca, 0, 255).astype(np.uint8)), (int(700 * k), int(640 * k)))
    d = ImageDraw.Draw(img)
    # celdas de enfrente (lejanas)
    for cx in range(716, 1080, 120):
        d.rectangle(S(cx, 760, cx + 96, 1320), fill=(18, 16, 16))
        _bars(d, cx + 6, cx + 84, 760, 1320, gap=19, w=7, col=(8, 8, 9))
    d.rectangle(S(700, 1380, 1080, 1440), fill=(16, 15, 15))
    d.rectangle(S(700, 1436, 1080, 1444), fill=(60, 52, 44))
    # lámpara
    d.line(S(930, 640, 930, 700), fill=(12, 12, 12), width=int(3 * k))
    d.polygon(S(900, 724, 960, 724, 944, 700, 916, 700), fill=(24, 24, 24))
    return img


def s2(t):
    bg = _s2_bg()
    e = sm(t / 7.0)
    cam = Cam(lerp(560, 430, e), lerp(1050, 1190, e), lerp(1.0, 1.42, e))
    img = cam.view(bg, 0, 0, 1.4)
    # --- luces ---
    lamp = cam.p(930, 712)
    flick = 0.92 + 0.08 * math.sin(t * 9.0) * math.sin(t * 3.1)
    add_glow(img, lamp[0], lamp[1], 520 * cam.z, (255, 170, 80), 0.55 * flick)
    add_glow(img, lamp[0], lamp[1], 130 * cam.z, (255, 224, 160), 0.9 * flick)
    # luz que atraviesa los barrotes sobre la celda
    polys = []
    for i in range(7):
        bx = 640 - i * 84
        polys.append((cam.pts([(bx + 28, 640), (bx + 58, 640), (bx - 170, 1440), (bx - 200, 1440)]), 255))
    m = soft_mask(polys, 6, 2)
    gradm = np.linspace(1.0, 0.0, W)[None, :]
    xs = cam.p(640, 0)[0]
    xe = cam.p(60, 0)[0]
    gx = np.clip((np.arange(W) - xe) / (xs - xe), 0, 1)[None, :] ** 1.5
    ma = (np.asarray(m, np.float32) * gx)
    m = Image.fromarray(ma.astype(np.uint8))
    img = add_light_mask(img, m, (255, 150, 70), 0.32 * flick)
    # --- personajes ---
    u = 6.4
    # Frank
    fx0 = cam.p(325, 1440)
    hpx = 640 * cam.z
    if t < 2.3:
        ph = t / 2.3
        P = pose(lean=4, hip=(0, -50), fF=(7, 0), fB=(-5, 0), hF=(27, -78 + 22 * ph), hB=(2, -50), head=-4)
    elif t < 3.5:
        c = seg(t, 2.3, 3.5)
        P = pose(lean=lerp(4, 40, c), hip=(lerp(0, 2, c), lerp(-50, -27, c)), fF=(lerp(7, 9, c), 0), fB=(-5, 0),
                 hF=(lerp(27, 26, c), lerp(-56, -17, c)), hB=(lerp(2, -9, c), lerp(-50, -24, c)), head=lerp(-4, 14, c))
    elif t < 5.7:
        w = t - 3.5
        tap = math.sin(w * 11) * 1.4 if 3.9 < t < 5.0 else 0
        hy = -17 + (math.sin(w * 3.0) * 2.5)
        P = pose(lean=40, hip=(2, -27), fF=(9, 0), fB=(-5, 0), hF=(26 + tap, hy), hB=(-9, -24), head=lerp(14, 26, seg(t, 3.5, 4.6)), eye=0.7)
    else:
        c = seg(t, 5.7, 6.3)
        P = pose(lean=lerp(40, 24, c), hip=(1, lerp(-27, -33, c)), fF=(9, 0), fB=(-5, 0), hF=(26, -19), hB=(-9, -26),
                 head=lerp(26, -26, c), eye=lerp(0.7, 1.2, c))
    lit = (0.62, 0.56, 0.54)
    draw_man(img, "frank", fx0[0], fx0[1], hpx, P, "side", -1, light=lit, rim=((255, 170, 100), -5, 0, 2.0))
    # silueta de guardia (pared del fondo del pasillo)
    g0, g1 = S2_GUARD
    if g0 - 0.3 < t < g1 + 0.3:
        gp = (t - g0) / (g1 - g0)
        gx = lerp(1130, 700, gp)
        gq = cam.p(gx, 1428)
        draw_man(img, "guard", gq[0], gq[1], 470 * cam.z, walk_pose(t * 6.2, 0.0, 4.0, 11, 6, 4), "side", -1,
                 light=(0.16, 0.16, 0.2), guard=True)
        # linterna
        add_glow(img, gq[0] - 90 * cam.z, gq[1] - 150 * cam.z, 120 * cam.z, (255, 200, 120), 0.4)
    # compañeros (profile) en el pasillo
    def idle(t0, ph):
        return math.sin(t * 2.0 + ph) * 0.5
    for who, x, flips in (("john", 770, (3.0, 5.4)), ("clar", 985, (2.2, 6.0))):
        f = -1 if x < 900 else 1
        if flips[0] < t < flips[1]:
            f = -f
        q = cam.p(x, 1442)
        P = pose(lean=3, hip=(0, -50 + idle(t, x)), fF=(7, 0), fB=(-5, 0), hF=(5, -52), hB=(-3, -53),
                 head=(6 if f > 0 else 6) * math.sin(t * 0.8 + x), eye=1.0)
        draw_man(img, who, q[0], q[1], 640 * cam.z, P, "side", f, light=(0.92, 0.74, 0.62), rim=((255, 190, 120), 5 * f, 0, 2.4))
    # barras primer plano (re-dibujar barrotes sobre los personajes del pasillo): sombra suave
    # polvo flotante en la luz
    d = ImageDraw.Draw(img)
    r = _rng(8)
    for i in range(38):
        x = 80 + r.rand() * 560 + math.sin(t * 0.5 + i) * 18
        y = (640 + r.rand() * 800 - t * 14 * (0.4 + r.rand())) % 800 + 640
        q = cam.p(x, y)
        a = 0.4 + 0.6 * math.sin(t * 1.5 + i) ** 2
        rad = (1.2 + r.rand() * 1.6) * cam.z
        c = (int(200 * a), int(170 * a), int(120 * a))
        d.ellipse([q[0] - rad, q[1] - rad, q[0] + rad, q[1] + rad], fill=c)
    img = fog(img, t, 0, 1100, (16, 14, 14), 0.25, speed=12, seed=31)
    return img


# ======================================================================= ESCENA 3
@functools.lru_cache(maxsize=2)
def _s3_bg():
    k = 1.2
    WW = 1700
    img = Image.new("RGB", (int(WW * k), int(H * k)), (8, 9, 11))
    d = ImageDraw.Draw(img)
    S = lambda *v: [c * k for c in v]
    rr = _rng(12)
    for (ya, yb) in ((60, 540), (1480, 1900)):
        d.rectangle(S(0, ya, WW, yb), fill=(11, 12, 15))
        for cx in range(20, WW, 215):
            d.rectangle(S(cx, ya + 30, cx + 190, yb - 20), fill=(15, 16, 19))
            _bars(d, cx + 8, cx + 180, ya + 30, yb - 20, gap=22, w=8, col=(6, 7, 9))
    d.rectangle(S(0, 540, WW, 600), fill=(28, 29, 31))
    d.rectangle(S(0, 1400, WW, 1480), fill=(24, 25, 27))
    for c in range(3):
        x0 = 50 + c * 530
        w = 500
        wall = vgrad(int(w * k), int(800 * k), [(0, (30, 30, 29)), (0.55, (66, 65, 60)), (1, (38, 37, 34))])
        na = np.asarray(fbm_img(int(w * k), int(800 * k), 50 + c, 5, 5), np.float32)[:, :, None] / 255
        wa = np.asarray(wall, np.float32) * (0.7 + 0.55 * na)
        img.paste(Image.fromarray(np.clip(wa, 0, 255).astype(np.uint8)), (int(x0 * k), int(600 * k)))
        d = ImageDraw.Draw(img)
        for i in range(4):
            x = x0 + rr.randint(30, 470)
            y = rr.randint(640, 1000)
            pts = [(x, y)]
            for j in range(5):
                x += rr.randint(-12, 12)
                y += rr.randint(18, 40)
                pts.append((x, y))
            d.line([(a * k, b * k) for a, b in pts], fill=(24, 24, 24), width=int(2 * k))
        # catre y repisa
        d.rectangle(S(x0 + 20, 1020, x0 + 150, 1040), fill=(40, 36, 30))
        d.rectangle(S(x0 + 360, 1090, x0 + 470, 1110), fill=(46, 42, 36))
        d.rectangle(S(x0 + 380, 1060, x0 + 396, 1090), fill=(120, 110, 90))
        # rejilla
        cx = x0 + w / 2
        vx0, vy0, vx1, vy1 = cx - 95, 1262, cx + 95, 1384
        d.rectangle(S(vx0 - 10, vy0 - 10, vx1 + 10, vy1 + 10), fill=(46, 46, 44))
        d.rectangle(S(vx0, vy0, vx1, vy1), fill=(6, 6, 7))
        for i in range(9):
            y = vy0 + 8 + i * 13
            d.rectangle(S(vx0 + 4, y, vx1 - 4, y + 6), fill=(72, 72, 68))
        d.rectangle(S(x0 + w, 600, x0 + w + 30, 1400), fill=(14, 14, 16))
    d.rectangle(S(0, 600, 50, 1400), fill=(14, 14, 16))
    d.rectangle(S(0, 1394, WW, 1406), fill=(18, 18, 18))
    return img


def s3(t):
    bg = _s3_bg()
    e = sm(t / 7.0)
    cam = Cam(lerp(330, 1190, e), lerp(1140, 1190, e), lerp(1.34, 1.5, e * 0.8))
    img = cam.view(bg, 0, 0, 1.2)
    d = ImageDraw.Draw(img)
    # polvo y fragmentos
    for c in range(3):
        cx = 50 + c * 530 + 250
        # luz tenue
        lp = cam.p(cx, 650)
        add_glow(img, lp[0], lp[1], 420 * cam.z, (255, 175, 90), 0.20 + 0.04 * math.sin(t * 3 + c))
        ph = c * 0.17
        # agujero que crece
        g = 6 + 22 * seg(t, 0, 7)
        q0, q1 = cam.p(cx - 95 - g * 0.5, 1262 - g), cam.p(cx + 95 + g * 0.5, 1384 + g * 0.2)
        d.rectangle([q0[0], q0[1], q1[0], q1[1]], outline=(14, 14, 14), width=max(1, int(g * 0.5 * cam.z)))
        d = ImageDraw.Draw(img)
        # redibujar rejilla encima del borde
        # hombre agachado de espaldas
        base = cam.p(cx, 1398)
        sc = 520 * cam.z
        who = ("frank", "john", "clar")[c]
        w = t * (2 * math.pi / S3_BEATS) + ph * 6
        sc_x = math.sin(w) * 2.4
        sc_y = math.sin(w * 2) * 1.0
        P = pose(lean=22, hip=(0, -31 + 0.6 * math.sin(t * 2.2 + c)), fF=(11, 0), fB=(-11, 0),
                 hF=(11 + sc_x, -19 + sc_y), hB=(-11 - sc_x, -19 - sc_y), head=2.5 * math.sin(t * 0.7 + c), eye=0.8)
        lit = (0.66, 0.58, 0.54)
        r = draw_man(img, who, base[0], base[1], sc, P, "back34" if c != 1 else "back", 1, light=lit,
                     rim=((255, 170, 100), -4, -1, 1.6))
        d = ImageDraw.Draw(img)
        # herramienta improvisada entre las manos
        a, b = r["hF"], r["hB"]
        d.line([a, b], fill=(168, 172, 176), width=max(2, int(4 * cam.z)))
        # polvo cayendo
        rg = _rng(100 + c)
        for i in range(26):
            tt = (t * (0.55 + rg.rand() * 0.5) + rg.rand() * 3) % 1.6
            if t < 0.6 + c * 0.1:
                continue
            x = cx + (rg.rand() - 0.5) * 190 + math.sin(t * 2 + i) * 6
            y = 1280 + tt * 110
            q = cam.p(x, y)
            a_ = clamp(1 - tt / 1.6)
            rad = (1.4 + 2.2 * rg.rand()) * cam.z
            cc = int(150 * a_)
            d.ellipse([q[0] - rad, q[1] - rad, q[0] + rad, q[1] + rad], fill=(cc, cc - 6, cc - 14))
        # fragmentos de pared
        for i in range(8):
            t0 = 0.3 + i * 0.83 + c * 0.27
            tau = (t - t0) % 6.6
            if t < t0 or tau > 0.9:
                continue
            vx = (rg.rand() - 0.5) * 120
            x = cx + (rg.rand() - 0.5) * 120 + vx * tau
            y = 1330 + 500 * tau * tau
            if y > 1396:
                y = 1396 - abs(math.sin((y - 1396) * 0.1)) * 6
            q = cam.p(x, y)
            rad = (2.5 + 2.5 * rg.rand()) * cam.z
            d.rectangle([q[0] - rad, q[1] - rad, q[0] + rad, q[1] + rad], fill=(96, 94, 88))
    # pasos de guardia: sombra que cruza el pasillo (luz que se mueve)
    sx = lerp(-300, 1500, seg(t, 2.0, 6.5))
    pts = cam.pts([(sx - 80, 600), (sx + 80, 600), (sx + 300, 1400), (sx + 100, 1400)])
    img = beam(img, pts, (255, 190, 120), 0.08, 6, 5)
    img = fog(img, t, 300, 1300, (18, 16, 15), 0.25, speed=10, seed=33)
    return img


# ======================================================================= ESCENA 4
def E(d, cam, cx, cy, rx, ry, fill, outline=None, width=1):
    x, y = cam.p(cx, cy)
    d.ellipse([x - rx * cam.z, y - ry * cam.z, x + rx * cam.z, y + ry * cam.z], fill=fill, outline=outline, width=width)


def L(d, cam, a, b, fill, width):
    d.line([cam.p(*a), cam.p(*b)], fill=fill, width=max(1, int(width * cam.z)))


def hand(d, cam, x, y, ang, s=1.0, col=SKIN, sleeve=UNI_SHIRT, grip=0.0):
    """Mano + antebrazo; ang = dirección del brazo hacia la mano (rad)."""
    ca, sa = math.cos(ang), math.sin(ang)
    ex, ey = x - ca * 520 * s, y - sa * 520 * s
    L(d, cam, (ex, ey), (x - ca * 95 * s, y - sa * 95 * s), sleeve, 150 * s)
    L(d, cam, (x - ca * 110 * s, y - sa * 110 * s), (x, y), col, 104 * s)
    E(d, cam, x + ca * 6 * s, y + sa * 6 * s, 62 * s, 54 * s, col)
    for i in range(4):
        o = (i - 1.5) * 26 * s
        px, py = x + ca * 46 * s - sa * o, y + sa * 46 * s + ca * o
        L(d, cam, (px, py), (px + ca * (60 - 28 * grip) * s, py + sa * (60 - 28 * grip) * s), col, 24 * s)
    L(d, cam, (x - sa * 36 * s, y + ca * 36 * s), (x + ca * 40 * s - sa * 62 * s, y + sa * 40 * s + ca * 62 * s), mulc(col, 0.92), 26 * s)


def dummy_head(d, cam, cx, cy, s, prog, lying=False):
    pale, shade = (214, 190, 160), (178, 150, 124)
    E(d, cam, cx, cy, 175 * s, 225 * s, pale, outline=(120, 100, 84), width=3)
    E(d, cam, cx - 40 * s, cy - 30 * s, 100 * s, 150 * s, (222, 200, 172))
    E(d, cam, cx - 178 * s, cy + 5 * s, 28 * s, 50 * s, shade)
    E(d, cam, cx + 178 * s, cy + 5 * s, 28 * s, 50 * s, shade)
    if prog > 0.35:
        for sx in (-1, 1):
            L(d, cam, (cx + sx * 40 * s - 34 * s, cy - 20 * s), (cx + sx * 40 * s + 34 * s, cy - 20 * s), (60, 44, 40), 7 * s)
            L(d, cam, (cx + sx * 40 * s - 38 * s, cy - 54 * s), (cx + sx * 40 * s + 38 * s, cy - 60 * s), (50, 34, 30), 9 * s)
        L(d, cam, (cx, cy - 10 * s), (cx - 14 * s, cy + 55 * s), shade, 8 * s)
        L(d, cam, (cx - 14 * s, cy + 56 * s), (cx + 14 * s, cy + 60 * s), shade, 8 * s)
    if prog > 0.6:
        L(d, cam, (cx - 34 * s, cy + 112 * s), (cx + 34 * s, cy + 112 * s), (130, 70, 66), 9 * s)
    n = int(clamp((prog - 0.15) / 0.8) * 60)
    r = _rng(77)
    for i in range(n):
        a = math.pi * (1.08 + 0.84 * (i / 60.0)) + r.randn() * 0.02
        rr_ = 232 * s * (0.94 + 0.1 * r.rand())
        x0, y0 = cx + math.cos(a) * 170 * s, cy + math.sin(a) * 225 * s
        L(d, cam, (x0, y0), (cx + math.cos(a) * rr_ * 0.78 + r.randn() * 10 * s, cy + math.sin(a) * rr_ * 1.05 - 20 * s), (36, 26, 22), 15 * s)


def s4(t):
    img = Image.new("RGB", (W, H), (10, 8, 8))
    if t < 3.7:
        return _s4_bench(img, t)
    return _s4_bed(img, t)


def _s4_bench(img, t):
    img = vgrad(W, H, [(0, (14, 10, 9)), (0.62, (34, 24, 18)), (0.7, (50, 36, 26)), (1, (24, 16, 12))])
    cam = Cam(W / 2 + lerp(0, -40, t / 3.7), H / 2, lerp(1.0, 1.12, t / 3.7))
    d = ImageDraw.Draw(img)
    # mesa
    d.rectangle([0, 1320, W, H], fill=(52, 36, 24))
    for i in range(7):
        d.line([(0, 1360 + i * 80), (W, 1360 + i * 80 + 12)], fill=(40, 28, 18), width=3)
    # cabeza falsa sobre soporte
    d.rectangle([640, 1250, 720, 1330], fill=(70, 50, 36))
    prog = clamp(t / 3.0)
    dummy_head(d, cam, 690, 1010, 1.05, prog)
    # Frank (perfil) a la izquierda
    draw_head_big(img, "frank", 250 - lerp(0, 30, t / 3.7), 960, 700, "side", eye=0.7, light=(0.85, 0.68, 0.55), rim=((255, 190, 120), 5, 0, 2.4))
    d = ImageDraw.Draw(img)
    # pincel y mano
    s = 1.0
    bob = math.sin(t * 5.5) * 20
    hx, hy = 470 + bob, 1100 + math.sin(t * 2.7) * 28
    # pincel
    L(d, cam, (hx, hy), (hx + 100, hy - 30), (110, 80, 50), 12)
    L(d, cam, (hx + 100, hy - 30), (hx + 132, hy - 40), (230, 200, 170), 16)
    # segunda mano (derecha, bajo) pegando cabello
    hand(d, cam, 560 + math.sin(t * 3.1) * 14, 1250, -0.95, 0.8, grip=0.5)
    # mano del pincel encima
    hand(d, cam, hx - 10, hy + 18, -0.28 + 0.07 * math.sin(t * 5.5), 0.85, grip=0.8)
    # pegotes de cabello sobre la mesa
    for i in range(5):
        E(d, cam, 120 + i * 60, 1400 + (i % 2) * 40, 34, 14, (34, 24, 20))
    # lámpara
    img = fog(img, t, 0, 1000, (30, 20, 12), 0.18, speed=8, seed=44)
    lx, ly = 230, 330
    add_glow(img, lx, ly, 780, (255, 168, 80), 0.55)
    add_glow(img, lx, ly, 150, (255, 230, 170), 0.9)
    return img


def _s4_bed(img, t):
    img = vgrad(W, H, [(0, (12, 12, 14)), (0.5, (44, 44, 42)), (0.82, (30, 30, 29)), (1, (16, 16, 16))])
    z0 = 1.95 if t < 4.9 else lerp(1.95, 1.0, seg(t, 4.9, 6.6))
    cam = Cam(lerp(300, 540, seg(t, 4.9, 6.6)), lerp(1130, 1100, seg(t, 4.9, 6.6)), z0)
    d = ImageDraw.Draw(img)
    # pared con vetas
    for i in range(18):
        L(d, cam, (i * 62, 300), (i * 62 + 6, 1300), (34, 34, 33), 5)
    # catre
    floor_y = 1440
    d.rectangle([0, cam.p(0, floor_y)[1], W, H], fill=(22, 22, 22))
    L(d, cam, (90, 1320), (90, floor_y), (20, 20, 20), 22)
    L(d, cam, (990, 1320), (990, floor_y), (20, 20, 20), 22)
    L(d, cam, (60, 1318), (1020, 1318), (26, 26, 26), 26)
    # colchón
    p = cam.pts([(70, 1300), (1010, 1300), (1020, 1240), (60, 1240)])
    d.polygon(p, fill=(86, 88, 82))
    # almohada
    E(d, cam, 220, 1215, 150, 46, (176, 176, 166))
    E(d, cam, 210, 1200, 110, 22, (196, 196, 186))
    # cabeza falsa (llega a t=3.4..4.6)
    hp = seg(t, 3.6, 4.5)
    hx_, hy_ = lerp(-150, 235, hp), lerp(900, 1150, hp ** 1.6)
    if t > 3.5:
        dummy_head(d, cam, hx_, hy_, 0.55, 1.0)
    # manta (aparece t>4.4 tirada hacia arriba)
    bp = seg(t, 4.5, 5.2)
    if bp > 0:
        ex = lerp(1000, 340, bp)
        pts = [(ex, 1242)]
        for i in range(0, 21):
            x = lerp(ex, 1000, i / 20)
            lump = 52 * math.sin(math.pi * (i / 20) ** 0.8) + 8 * math.sin(i * 1.3)
            pts.append((x, 1250 - lump * (0.5 + 0.5 * bp)))
        pts += [(1010, 1300), (ex, 1300)]
        d.polygon(cam.pts(pts), fill=(94, 88, 76))
        for i in range(5):
            xx = lerp(ex + 40, 960, i / 5)
            L(d, cam, (xx, 1236), (xx + 18, 1296), (66, 62, 54), 5)
        # bulto de ropa
        d.polygon(cam.pts([(ex, 1240), (ex + 40, 1200), (ex + 120, 1192), (ex + 160, 1240)]), fill=(100, 94, 82))
    # manos en escena
    if 3.4 < t < 4.7:
        hh = seg(t, 3.5, 4.4)
        ox = lerp(-300, 120, hh)
        hand(d, cam, hx_ - 120, hy_ - 150, -0.2, 0.7, grip=0.9) if False else None
        hand(d, cam, hx_ - 175 * 0.55 - 20, hy_ - 120, 0.9, 0.6, grip=1.0)
    if 4.4 < t < 5.5:
        hand(d, cam, lerp(1000, 520, seg(t, 4.4, 5.0)) + 50, 1160, 3.0, 0.7, grip=0.7) if False else None
        hand(d, cam, lerp(40, 380, seg(t, 4.4, 5.0)), 1160, 0.05, 0.7, grip=0.6)
    # luz base (lámpara pasillo tenue)
    add_glow(img, 1000, 220, 700, (255, 170, 90), 0.22)
    # haz de linterna del guardia que pasa (t>5.4)
    if t > 5.2:
        bp = seg(t, 5.2, 6.9)
        ox = lerp(1500, 200, bp)
        pts = [(1400, 700), (ox - 140, 1120), (ox + 160, 1330), (1400, 820)]
        img = beam(img, cam_pts(cam, pts) if False else pts, (255, 240, 200), 0.55, 6, 5)
        add_glow(img, 1230, 760, 160, (255, 240, 200), 0.8)
    img = fog(img, t, 0, 1100, (14, 14, 14), 0.22, speed=9, seed=45)
    return img
