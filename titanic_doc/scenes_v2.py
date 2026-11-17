# -*- coding: utf-8 -*-
"""VERSIÓN CINEMATOGRÁFICA (v2). Reutiliza el motor y los sprites del proyecto original (scenes.py / gfx.py)
y mejora: cámara, profundidad, agua, humo, banderas, ventanas, personajes animados, evacuación,
hundimiento en dos secciones y rescate. Sigue siendo 2D por capas, 60 s, 1080x1920, 30 fps."""
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import scenes as S
from scenes import *
from scenes import _cache, _blit

FPS = 30
BOUNDS = S.BOUNDS


# ====================================================================== CÁMARA / ATMÓSFERA
def camera(img, z, pan=(0.0, 0.0), roll=0.0):
    """Cámara 2D: zoom, paneo y balanceo suave sobre el fotograma ya compuesto."""
    if abs(z - 1) < 1e-4 and not roll and not pan[0] and not pan[1]:
        return img
    cx, cy = W / 2, H / 2
    th = math.radians(roll)
    cs, sn = math.cos(th), math.sin(th)
    a, b, d, e = cs / z, sn / z, -sn / z, cs / z
    c0 = cx + pan[0] - a * cx - b * cy
    f0 = cy + pan[1] - d * cx - e * cy
    return img.transform((W, H), Image.AFFINE, (a, b, c0, d, e, f0), Image.BICUBIC)


def mist(c, t, y0, h, alpha=40, speed=14, seed=1, col=(150, 176, 215)):
    key = ('mist', h, seed)
    if key not in _cache:
        rnd = random.Random(seed)
        lay = Image.new('L', (2 * W, h), 0)
        d = ImageDraw.Draw(lay)
        for k in range(16):
            x = rnd.uniform(0, W)
            y = rnd.uniform(h * 0.3, h * 0.7)
            r = rnd.uniform(220, 420)
            v = rnd.randint(50, 120)
            for xx in (x, x + W, x - W):
                d.ellipse([xx - r, y - h * 0.22, xx + r, y + h * 0.22], fill=v)
        _cache[key] = lay.filter(ImageFilter.GaussianBlur(h * 0.12))
    tex = _cache[key]
    off = int((t * speed) % W)
    m = tex.crop((off, 0, off + W, h)).point(lambda v: int(v * alpha / 100.0))
    c.paste(Image.new('RGB', (W, h), col), (0, int(y0)), m)


def flag(c, anchor, scr, s, ang, t, top, length, hgt, col, ph=0.0):
    x0, y0 = to_screen(anchor, scr, s, ang, top)
    d = ImageDraw.Draw(c)
    n = 10
    up, dn = [], []
    for i in range(n + 1):
        u = i / n
        wob = math.sin(t * 7.0 - u * 5 + ph) * hgt * 0.35 * u * s
        up.append((x0 - u * length * s, y0 + wob))
        dn.append((x0 - u * length * s, y0 + hgt * s * (1 - 0.35 * u) + wob))
    d.polygon(up + dn[::-1], fill=col)
    m = len(up) // 2
    d.ellipse([up[m][0] - 3 * s - 1, up[m][1] + hgt * s * 0.3, up[m][0] + 3 * s + 1, up[m][1] + hgt * s * 0.3 + 6 * s + 2], fill=(245, 245, 240, 255))


def ship_extras(c, anchor, scr, s, ang, t, windows=True, flags=True):
    if flags and s > 0.45:
        flag(c, anchor, scr, s, ang, t, (862, 196), 30, 12, (186, 28, 36, 255))
        flag(c, anchor, scr, s, ang, t, (138, 172), 26, 10, (186, 28, 36, 255), 1.3)
    if windows:
        d = ImageDraw.Draw(c)
        rnd = random.Random(5)
        rows = [(66, 160, 828, 11, 8), (88, 186, 812, 11, 8), (118, 272, 664, 12, 6)]
        for k in range(40):
            row = rows[k % 3]
            ux = row[1] + rnd.randint(0, int((row[2] - row[1]) / row[3])) * row[3]
            per = rnd.uniform(2.2, 5.0)
            phs = rnd.uniform(0, per)
            ph = (t + phs) % per
            if ph < 0.45 or (0.7 < ph < 0.85):
                x, y = to_screen(anchor, scr, s, ang, (ux + 3, row[0] + row[4] / 2))
                r = max(1.2, 3.3 * s)
                d.rectangle([x - r, y - r * 1.25, x + r, y + r * 1.25], fill=(46, 30, 18, 235))


def reflection(c, anchor, scr, s, ang, t, wl, alpha=120):
    d = ImageDraw.Draw(c)
    rnd = random.Random(8)
    for k in range(110):
        ux = rnd.uniform(60, 940)
        x, _ = to_screen(anchor, scr, s, ang, (ux, 0))
        ln = rnd.uniform(10, 46) * (0.6 + s * 0.5)
        y0 = wl + 8 + rnd.uniform(0, 70) * s
        xs = x + 6 * math.sin(t * 2.2 + k * 0.7) * s
        v = 0.5 + 0.5 * math.sin(t * 3.0 + k)
        d.line([xs, y0, xs + 2, y0 + ln * 0.4], fill=(255, 196, 110, int(alpha * v)), width=2)


def funnel_smoke2(c, anchor, screen, s, ang, t, color, alpha=0.6, seed=0, wind=(-1.0, -0.1), which=(0, 1, 2)):
    for i in which:
        o = to_screen(anchor, screen, s, ang, (FUNNELS[i] - 9, 194))
        smoke(c, o, t + i * 0.7, color, scale=max(0.55, s * 1.15), wind=wind, rate=13, life=5.5, seed=seed + i * 13, alpha=alpha)


S.funnel_smoke = funnel_smoke2  # el humo del proyecto original pasa a ser más denso


# ====================================================================== PERSONAJES ANIMADOS
SKIN = (214, 176, 146)


def figure(d, x, y, h, t, ph=0.0, vx=0.0, pose='walk', coat=(30, 30, 36), hat='bowler', lum=1.0, female=False, crew=False):
    """Persona dibujada (anónima) con ciclo de caminata. (x, y) = pies; h = altura en px."""
    f = 1 if vx >= 0 else -1

    def L(c):
        return tuple(int(v * lum) for v in c) + (255,)
    walking = abs(vx) > 0.05 and pose == 'walk'
    sw = math.sin(t * 8.0 + ph) if walking else 0.0
    bob_ = abs(math.sin(t * 8.0 + ph)) * h * 0.018 if walking else 0.0
    y = y - bob_
    hip = (x, y - h * 0.44)
    trouser = (22, 22, 28) if not crew else (18, 26, 44)
    lw = max(2, int(h * 0.11))
    for sgn in (-1, 1):
        a = sw * sgn * 0.5
        d.line([hip[0], hip[1], hip[0] + math.sin(a) * h * 0.44 * f, hip[1] + math.cos(a) * h * 0.44], fill=L(trouser), width=lw)
    sh_y = y - h * 0.80
    bw = h * 0.20
    if female:
        d.polygon([(x - bw * 0.7, sh_y), (x + bw * 0.7, sh_y), (x + bw * 1.5, y - h * 0.04), (x - bw * 1.5, y - h * 0.04)], fill=L(coat))
    else:
        d.polygon([(x - bw, sh_y), (x + bw, sh_y), (x + bw * 0.8, hip[1] + h * 0.04), (x - bw * 0.8, hip[1] + h * 0.04)], fill=L(coat))
    if crew:
        d.line([x, sh_y + h * 0.04, x, hip[1]], fill=L((200, 170, 70)), width=max(1, int(h * 0.02)))
    # brazos
    sh = (x, sh_y + h * 0.04)
    alw = max(2, int(h * 0.075))
    for sgn in (-1, 1):
        if pose == 'wave' and sgn == 1:
            a = 2.4 + math.sin(t * 6 + ph) * 0.55
            ex, ey = sh[0] + math.sin(a) * h * 0.34 * f, sh[1] - math.cos(a) * -h * 0.34
            ex, ey = sh[0] + math.sin(2.6 + math.sin(t * 6 + ph) * 0.5) * h * 0.32 * f * -1, sh[1] - h * 0.30 * abs(math.cos(math.sin(t * 6 + ph) * 0.5 + 0.2))
        elif pose == 'point' and sgn == 1:
            ex, ey = sh[0] + h * 0.40 * f, sh[1] + math.sin(t * 2 + ph) * h * 0.02
        elif pose == 'pull':
            ex, ey = sh[0] + h * 0.30 * f, sh[1] + h * 0.12 + math.sin(t * 3 + ph + sgn) * h * 0.06
        else:
            a = -sw * sgn * 0.5
            ex, ey = sh[0] + math.sin(a) * h * 0.34, sh[1] + math.cos(a) * h * 0.34
        d.line([sh[0], sh[1], ex, ey], fill=L(coat), width=alw)
        d.ellipse([ex - alw * 0.6, ey - alw * 0.6, ex + alw * 0.6, ey + alw * 0.6], fill=L(SKIN))
    # cabeza y sombrero
    hr = h * 0.095
    hy = y - h * 0.93
    d.ellipse([x - hr, hy - hr, x + hr, hy + hr], fill=L(SKIN))
    if hat == 'bowler':
        d.ellipse([x - hr * 1.15, hy - hr * 1.4, x + hr * 1.15, hy - hr * 0.1], fill=L((18, 18, 22)))
        d.rectangle([x - hr * 1.7, hy - hr * 0.35, x + hr * 1.7, hy - hr * 0.05], fill=L((18, 18, 22)))
    elif hat == 'cap':
        d.pieslice([x - hr * 1.2, hy - hr * 1.4, x + hr * 1.2, hy + hr * 0.7], 180, 360, fill=L((20, 30, 52)))
        d.rectangle([x - hr * 1.2 + (hr * 0.6 if f > 0 else 0), hy - hr * 0.3, x + hr * 1.2 + (hr * 0.6 if f > 0 else -hr * 0.6) * 0, hy - hr * 0.05], fill=L((14, 14, 18)))
        d.rectangle([x - hr * 0.3, hy - hr * 1.15, x + hr * 0.3, hy - hr * 0.8], fill=L((220, 200, 120)))
    elif hat == 'hair':
        d.pieslice([x - hr * 1.15, hy - hr * 1.25, x + hr * 1.15, hy + hr * 0.9], 180, 360, fill=L((40, 28, 20)))
        d.ellipse([x - hr * 0.7 - f * hr * 0.9, hy - hr * 0.4, x + hr * 0.7 - f * hr * 0.9, hy + hr * 0.9], fill=L((40, 28, 20)))


PASSENGER_COATS = [(30, 30, 38), (70, 50, 44), (46, 56, 80), (98, 70, 62), (26, 34, 30), (84, 40, 50), (60, 60, 70)]


def tri(u):
    return 1 - abs(2 * (u % 1.0) - 1)


# ====================================================================== ESCENA 1
def title_line(c, txt, y, size, a, col=(255, 255, 255), spacing=0, slide=46, glow=False, fontname='LiberationSerif-Bold.ttf'):
    if a <= 0:
        return
    yy = y + (1 - a) * slide
    if glow:
        key = ('glow', txt, size)
        if key not in _cache:
            lay = Image.new('RGBA', (W, int(size * 1.9)), (0, 0, 0, 0))
            ImageDraw.Draw(lay).text(((W - font(fontname, size).getlength(txt)) / 2, size * 0.25), txt, font=font(fontname, size), fill=(255, 190, 40, 255))
            _cache[key] = lay.filter(ImageFilter.GaussianBlur(22))
        blit_alpha(c, _cache[key], (0, yy - size * 0.2), a * 0.75)
    text_center(c, txt, yy, size, col=col, fontname=fontname, alpha=a, spacing=spacing, stroke=5 if size > 120 else 4)


def scene1(t):
    old = S.text_center
    S.text_center = lambda *a, **k: None
    try:
        c = S.scene1(t)
    finally:
        S.text_center = old
    A = S.assets()
    p = clamp01(t / 5.0)
    pe = ease(p) * 0.55 + p * 0.45
    s = lerp(0.7, 1.12, pe)
    wl = lerp(1085, 1185, pe)
    sx = lerp(610, 520, pe)
    dy, ang = bob(t, 2.2 * s)
    anchor, scr = (500, 0), (sx, wl + dy)
    ship_extras(c, anchor, scr, s, ang, t)
    reflection(c, anchor, scr, s, ang, t, wl + dy)
    mist(c, t, 880, 300, 34, 16, 2)
    # entrada del título: aparece con deslizamiento, brillo y espaciado que se cierra
    a1 = ease((t - 0.7) / 0.9)
    a2 = ease((t - 1.4) / 0.9)
    a3 = ease((t - 2.6) / 0.9)
    out = 1 - ease((t - 4.75) / 0.25)
    title_line(c, 'ASÍ FUE COMO SE', 150, 94, a1 * out)
    title_line(c, 'HUNDIÓ EL', 262, 94, a1 * out)
    title_line(c, 'TITANIC', 360, 200, a2 * out, col=(255, 214, 10), glow=True)
    title_line(c, 'UNA TRAGEDIA QUE CAMBIÓ LA HISTORIA', 625, 36, a3 * out, spacing=int(12 - 10 * a3), slide=20, fontname='LiberationSans-Bold.ttf')
    return c


# ====================================================================== ESCENA 2
def scene2(t):
    old = S.deck_people
    S.deck_people = lambda *a, **k: None
    try:
        c = S.scene2(t)
    finally:
        S.deck_people = old
    p = clamp01(t / 7.0)
    e = ease(p)
    s = 0.6 * (3.1 ** e)
    wl = lerp(960, 1190, e)
    ux = lerp(500, 640, e)
    sx = lerp(520, 540, e)
    dy, ang = bob(t, 2.0 * s)
    anchor, scr = (ux, 0), (sx, wl + dy)
    d = ImageDraw.Draw(c)
    rnd = random.Random(21)
    for k in range(30):
        a_, b_ = rnd.uniform(230, 520), rnd.uniform(540, 780)
        v = rnd.uniform(5, 11)
        u = (t * v / max(40, b_ - a_) + rnd.random())
        xu = a_ + (b_ - a_) * tri(u)
        vx = 1 if (u % 1.0) < 0.5 else -1
        stand = (k % 3 == 0)
        pose = 'wave' if (k % 4 == 1) else 'walk'
        if stand or pose == 'wave':
            xu, vx = a_ + (b_ - a_) * rnd.random(), 0
        x, y = to_screen(anchor, scr, s, ang, (xu, 112))
        figure(d, x, y, 15 * s, t, ph=k, vx=vx * (0 if stand or pose == 'wave' else 1), pose=pose, coat=PASSENGER_COATS[k % 7],
               hat=('hair' if k % 5 == 2 else 'bowler'), female=(k % 5 == 2))
    for k in range(8):
        xu = rnd.uniform(895, 975)
        x, y = to_screen(anchor, scr, s, ang, (xu, 62))
        figure(d, x, y, 14 * s, t, ph=k * 2, vx=0, pose='wave' if k % 2 == 0 else 'walk', coat=PASSENGER_COATS[(k + 2) % 7], hat='cap' if k % 3 == 0 else 'bowler')
    ship_extras(c, anchor, scr, s, ang, t, windows=False)
    return c


# ====================================================================== ESCENA 3
def scene3(t):
    A = assets()
    c = canvas()
    hz = 930
    sky_ocean(c, hz, NIGHT_SKY, NIGHT_SEA)
    stars_scene(c, t, hz)
    p = clamp01(t / 7.0)
    e = ease(p)
    s = lerp(1.25, 1.7, e)
    ux = lerp(640, 840, e)
    sx = lerp(520, 400, e)
    anchor = (ux, 100)
    ay = 960
    wl = ay + 100 * s
    dy, ang = bob(t, 1.4 * s)
    scr = (sx, ay + dy)
    d = ImageDraw.Draw(c)
    for k in range(40):
        d.rectangle([0, hz - k * 3, W, hz - k * 3 + 3], fill=(70, 100, 150, int(32 * (1 - k / 40))))
    layers = sea_layers(hz, wl, amp=1.8, c0=(22, 42, 72), c1=(12, 26, 50), crest=lambda f: (90, 125, 175, 100) if f < 0.85 else None, spd=0.6, n=11)
    back, front = split_layers(layers, wl)
    # iceberg claramente delante del barco: crece y se oscurece contra el cielo estrellado
    ap = ease((t - 0.6) / 1.6)
    q = clamp01(t / 7.0)
    isc = lerp(0.30, 0.62, q ** 1.2)
    ibx = lerp(900, 840, q)
    iby = lerp(hz + 20, hz + 70, q)
    draw_waves(c, back[:3], t, xoff=t * 70)
    if ap > 0:
        draw_iceberg(c, ibx, iby, isc, alpha=ap, under=False, dark=(0.5, 0.6, 0.85))
        # destellos de hielo
        d = ImageDraw.Draw(c)
        rnd = random.Random(2)
        for k in range(16):
            gx = ibx + rnd.uniform(-300, 300) * isc * 1.1
            gy = iby - rnd.uniform(30, 300) * isc
            v = 0.5 + 0.5 * math.sin(t * 3 + k)
            r = 2.5 * v + 1
            d.line([gx - r * 3, gy, gx + r * 3, gy], fill=(230, 244, 255, int(180 * v * ap)), width=1)
            d.line([gx, gy - r * 3, gx, gy + r * 3], fill=(230, 244, 255, int(180 * v * ap)), width=1)
    draw_waves(c, back[3:], t, xoff=t * 70)
    shimmer(c, t, hz + 4, wl + 200, (170, 200, 245), n=200, seed=15, maxlen=70)
    mist(c, t, hz - 30, 200, 70 * ap, 10, 3)
    for k, (fx, fy, r) in enumerate(((1040, wl - 60, 54), (760, wl - 30, 30), (960, hz + 110, 24), (640, hz + 60, 16))):
        floe(d, (fx - t * 30 * (0.4 + 0.2 * k)) % 1200 - 60, fy, r, t, k, int(255 * ap))
    place(c, A['night'], anchor, scr, s, ang)
    ship_extras(c, anchor, scr, s, ang, t)
    mid = to_screen(anchor, scr, s, ang, (500, 172))
    for k in range(4):
        ph = ((t * 0.55 + k * 0.25) % 1.0)
        r = 30 + 330 * ph
        a = int(160 * (1 - ph) * (1 - ease((t - 4.6) / 1.5)))
        if a > 0:
            d.arc([mid[0] - r, mid[1] - r, mid[0] + r, mid[1] + r], 215, 325, fill=(150, 210, 255, a), width=4)
    nest = to_screen(anchor, scr, s, ang, (862, 140))
    hh = 20 * s
    d.ellipse([nest[0] - hh * 0.22, nest[1] - hh * 0.95, nest[0] + hh * 0.22, nest[1] - hh * 0.5], fill=(10, 10, 14, 255))
    d.rectangle([nest[0] - hh * 0.26, nest[1] - hh * 1.0, nest[0] + hh * 0.26, nest[1] - hh * 0.86], fill=(10, 10, 14, 255))
    d.polygon([(nest[0] - hh * 0.4, nest[1]), (nest[0] - hh * 0.3, nest[1] - hh * 0.5), (nest[0] + hh * 0.3, nest[1] - hh * 0.5), (nest[0] + hh * 0.4, nest[1])], fill=(12, 12, 16, 255))
    d.rectangle([nest[0] - hh * 0.5, nest[1] - hh * 0.28, nest[0] + hh * 0.5, nest[1] + hh * 0.08], fill=(30, 26, 22, 255))
    for k in range(5):
        ph = (t * 0.9 + k * 0.2) % 1.0
        pr = 3 + 10 * ph
        d.ellipse([nest[0] + hh * 0.3 + 24 * ph - pr, nest[1] - hh * 0.78 - 12 * ph - pr, nest[0] + hh * 0.3 + 24 * ph + pr, nest[1] - hh * 0.78 - 12 * ph + pr], fill=(220, 235, 255, int(110 * (1 - ph))))
    funnel_smoke2(c, anchor, scr, s, ang, t, (34, 40, 54), alpha=0.5)
    draw_waves(c, front, t, xoff=t * 70)
    reflection(c, anchor, scr, s, ang, t, wl + dy, 90)
    foam(c, to_screen(anchor, scr, s, ang, (975, 0))[0], wl + 2 + dy, 60 * s, t, 130)
    rnd = random.Random(31)
    for k in range(80):
        x = (rnd.uniform(0, W) - t * rnd.uniform(40, 120)) % W
        y = (rnd.uniform(0, H * 0.75) + t * rnd.uniform(20, 60)) % (H * 0.75)
        r = rnd.uniform(1, 2.6)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(220, 235, 255, int(rnd.uniform(60, 150))))
    top_dark(c, 420, 100)
    chip(c, 'NOCHE DEL 14 DE ABRIL DE 1912 · ATLÁNTICO NORTE', 150, ease((t - 0.2) / 0.6) * (1 - ease((t - 6.6) / 0.4)), 28)
    return c


# ====================================================================== ESCENA 4
def damage_view(u, t):
    """Ilustración 2D del daño en el casco (a estribor, bajo la línea de flotación)."""
    A = assets()
    c = canvas()
    wl = 940
    arr = np.zeros((H, W, 3), np.uint8)
    arr[:wl] = vgrad(wl, [(0, (3, 6, 18)), (1, (22, 38, 70))])
    arr[wl:] = vgrad(H - wl, [(0, (14, 60, 92)), (0.4, (8, 36, 64)), (1, (3, 14, 30))])
    c.paste(Image.fromarray(arr, 'RGB'), (0, 0))
    s = 3.4
    anchor = (880, 0)
    scr = (540, wl + 3 * math.sin(t * 1.4))
    stars_scene(c, t, wl)
    place(c, A['night'], anchor, scr, s, 0.0)
    d = ImageDraw.Draw(c)
    # iceberg sumergido deslizándose por el casco
    off = u * 130
    ice = [(1180, wl + 10), (1010 - off * 0.0, wl + 26)]
    pts = [(1180 + 60, wl + 8), (1060, wl + 30), (980, wl + 72), (900, wl + 118), (840, wl + 190), (800, wl + 300), (760, wl + 460), (720, wl + 700), (1300, wl + 760)]
    sh = (off * 0.6) % 90
    pts = [(x - sh * 0.0, y) for x, y in pts]
    d.polygon(pts, fill=(176, 212, 236, 150))
    d.line(pts[:7], fill=(235, 248, 255, 200), width=4)
    # superficie del agua translúcida sobre el casco sumergido
    ov = Image.new('RGBA', (W, H - wl), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    od.rectangle([0, 0, W, H - wl], fill=(16, 78, 118, 140))
    c.alpha_composite(ov, (0, wl))
    xs = np.arange(-10, W + 20, 12)
    ys = wl + 4 * np.sin(xs * 0.03 + t * 2.0) + 2 * np.sin(xs * 0.09 - t * 3)
    d = ImageDraw.Draw(c)
    d.line(list(zip(xs, ys)), fill=(210, 236, 252, 255), width=3)
    # aberturas discontinuas bajo la línea de flotación (placas deformadas, remaches saltados)
    gashes = [(965, 0.2), (938, 0.55), (910, 0.9), (878, 1.3), (846, 1.7), (812, 2.1), (775, 2.5)]
    for k, (xu, t0) in enumerate(gashes):
        a = ease((u - t0) / 0.5)
        if a <= 0:
            continue
        L = 12 + (k * 7 % 12)
        x1, y1 = to_screen(anchor, scr, s, 0, (xu, -12 - (k % 3) * 4))
        x2, y2 = x1 - L * s, y1 + 2 * s
        d.line([x1, y1, x2, y2], fill=(8, 12, 18, 255), width=int(5 + 3 * a))
        d.line([x1, y1 - 3, x2, y2 - 3], fill=(150, 160, 176, int(255 * a)), width=2)
        for j in range(3):
            rx = x1 - (j + 0.5) * L * s / 3
            d.ellipse([rx - 3, y1 - 12, rx + 3, y1 - 6], fill=(120, 126, 140, int(255 * a)))
        # chorros de agua entrando
        for j in range(5):
            ph = (u * 1.7 + j * 0.2 + k * 0.13) % 1.0
            jx = x1 - L * s * 0.5 + (j - 2) * 7
            d.line([jx, y1 + 22 * (1 - ph) + 8, jx - 6 * ph, y1 - 70 * ph], fill=(222, 244, 255, int(230 * (1 - ph) * a)), width=3)
        for j in range(4):
            ph = (u * 1.2 + j * 0.27 + k * 0.17) % 1.0
            d.ellipse([x1 - L * s * 0.5 + (j - 2) * 14 - 3, y1 - 90 * ph - 3, x1 - L * s * 0.5 + (j - 2) * 14 + 3, y1 - 90 * ph + 3], outline=(220, 244, 255, int(220 * (1 - ph))), width=2)
    rnd = random.Random(9)
    for k in range(70):
        x = (rnd.uniform(0, W) + 10 * math.sin(t + k)) % W
        y = wl + 30 + ((rnd.uniform(0, H - wl) - t * rnd.uniform(10, 30)) % (H - wl - 30))
        d.ellipse([x - 1.5, y - 1.5, x + 1.5, y + 1.5], fill=(200, 230, 245, int(rnd.uniform(40, 120))))
    top_dark(c, 340, 110)
    return c


def scene4(t):
    A = assets()
    TC = 3.4
    if t >= 4.6:
        v = damage_view(t - 4.6, t)
        out = v
        k = ease((t - 4.6) / 0.7)
        if k < 1:
            ext = exterior4(min(t, 5.4))
            out = Image.blend(ext, v, k)
    else:
        out = exterior4(t)
    chip(out, '11:40 P. M. · 14 DE ABRIL DE 1912', 140, ease((t - 2.4) / 0.5), 36)
    kk = ease((t - 5.2) / 0.5)
    if kk > 0:
        text_center(out, 'ILUSTRACIÓN DEL DAÑO EN EL CASCO · COSTADO DE ESTRIBOR', 232, 28, alpha=kk, spacing=1, stroke=3)
        text_center(out, 'AGUA ENTRANDO BAJO LA LÍNEA DE FLOTACIÓN', 1130, 30, col=(255, 214, 10), alpha=kk, spacing=1, stroke=3)
    return out


def exterior4(t):
    A = assets()
    c = canvas()
    hz = 960
    sky_ocean(c, hz, NIGHT_SKY, NIGHT_SEA)
    stars_scene(c, t, hz)
    s = 1.45
    ux = 700
    wl = 1180
    TC = 3.4
    dy, ang = bob(t, 1.3 * s)
    shx, shy = shake_offset(t, TC, 9.0)
    anchor = (ux, 0)
    scr = (500 + shx, wl + dy + shy)
    ang += shx * 0.06
    layers = sea_layers(hz, wl, amp=1.8, c0=(22, 42, 72), c1=(12, 26, 50), crest=lambda f: (90, 125, 175, 100) if f < 0.85 else None, spd=0.6, n=11)
    back, front = split_layers(layers, wl)
    d = ImageDraw.Draw(c)
    for k in range(40):
        d.rectangle([0, hz - k * 3, W, hz - k * 3 + 3], fill=(70, 100, 150, int(32 * (1 - k / 40))))
    draw_waves(c, back, t, xoff=t * 70)
    shimmer(c, t, hz + 4, wl + 200, (170, 200, 245), n=160, seed=15, maxlen=70)
    bow_x = 500 + (992 - ux) * s
    if t < TC:
        q = t / TC
        e = ease(q) ** 1.3 * 0.7 + q ** 3 * 0.3
        sc = lerp(0.28, 1.25, e)
        by = lerp(hz + 26, wl + 62, e)
        cx = lerp(1020, bow_x + 420 * 1.25 + 14, e)
        ibx, iby, isc = cx, by, sc
        draw_iceberg(c, ibx, iby, isc, under=True, dark=(0.62, 0.72, 0.9) if t < 2.5 else None)
    else:
        ibx = bow_x + 420 * 1.25 + 14 - 400 * (t - TC)
        iby, isc = wl + 62, 1.25
    place(c, A['night'], anchor, scr, s, ang)
    ship_extras(c, anchor, scr, s, ang, t)
    funnel_smoke2(c, anchor, scr, s, ang, t, (34, 40, 54), alpha=0.5)
    if t >= TC:
        draw_iceberg(c, ibx, iby, isc, under=True)
    draw_waves(c, front, t, xoff=t * 70)
    d = ImageDraw.Draw(c)
    if t >= TC - 0.05:
        u = t - TC
        foam(c, bow_x - 40 + (-60 * u), wl + 70, 90, t, int(230 * math.exp(-u * 0.4)), 9)
        foam(c, bow_x - 100 + (-70 * u), wl + 52, 70, t + 1, int(200 * math.exp(-u * 0.4)), 4)
        rnd = random.Random(77)
        for k in range(34):
            life = 1.6
            t0 = 0.05 + rnd.uniform(0, 1.2)
            a = u - t0
            if 0 < a < life:
                x0 = bow_x - 120 + rnd.uniform(-60, 100)
                y0 = wl - 250 + rnd.uniform(-20, 40)
                vx = rnd.uniform(-60, 40)
                x = x0 + vx * a
                y = y0 + 380 * a * a + 40 * a
                if y < wl - 62 * s + 10:
                    r = rnd.uniform(4, 11)
                    d.polygon([(x - r, y), (x, y - r), (x + r, y - r * 0.2), (x + r * 0.5, y + r)], fill=(232, 244, 252, int(255 * (1 - a / life))))
        fl = max(0.0, 1 - u / 0.25) * 0.34
        if fl > 0:
            c.alpha_composite(Image.new('RGBA', (W, H), (255, 255, 255, int(255 * fl))))
        # señal de contacto
        ring = (u * 260) % 260
        if u < 1.4:
            ra = int(200 * (1 - u / 1.4))
            d.ellipse([bow_x - 20 - ring * 0.4, wl + 40 - ring * 0.12, bow_x - 20 + ring * 0.4, wl + 40 + ring * 0.12], outline=(255, 255, 255, ra), width=4)
    mist(c, t, hz - 30, 220, 30, 12, 5)
    top_dark(c, 300, 110)
    return c


# ====================================================================== ESCENA 5
def scene5(t):
    A = assets()
    c = canvas()
    hz = 940
    sky_ocean(c, hz, NIGHT_SKY, NIGHT_SEA)
    stars_scene(c, t, hz)
    ph = clamp01(t / 8.0)
    e = ease(ph)
    s = lerp(1.35, 1.95, e)
    ux = lerp(760, 800, e)
    wl = lerp(1060, 1100, e)
    ang = 2.8 * ease(ph * 1.15)
    dy, _ = bob(t, 1.2 * s)
    anchor = (ux, 0)
    scr = (540, wl + dy)
    layers = sea_layers(hz, wl, amp=1.8, c0=(22, 42, 72), c1=(12, 26, 50), crest=lambda f: (90, 125, 175, 100) if f < 0.85 else None, spd=0.6, n=11)
    back, front = split_layers(layers, wl)
    d = ImageDraw.Draw(c)
    for k in range(40):
        d.rectangle([0, hz - k * 3, W, hz - k * 3 + 3], fill=(70, 100, 150, int(30 * (1 - k / 40))))
    draw_waves(c, back, t, xoff=t * 50)
    place(c, A['night'], anchor, scr, s, ang)
    ship_extras(c, anchor, scr, s, ang, t, flags=False)
    cw = cutaway(ph, t)
    place(c, {2.0: cw}, anchor, scr, s, ang)
    funnel_smoke2(c, anchor, scr, s, ang, t, (34, 40, 54), alpha=0.45)
    d = ImageDraw.Draw(c)
    # numeración de los primeros cinco compartimentos
    edges = [992] + S.BULK
    for i in range(5):
        cx = (edges[i] + edges[i + 1]) / 2
        a_ = ease((ph - 0.04 - 0.1 * i) / 0.18)
        x, y = to_screen(anchor, scr, s, ang, (cx, 70))
        if a_ > 0 and -50 < x < W + 50:
            r = 24
            d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 214, 10, int(255 * a_)))
            f = font('LiberationSans-Bold.ttf', 30)
            d.text((x - f.getlength(str(i + 1)) / 2, y - 18), str(i + 1), font=f, fill=(10, 10, 14, int(255 * a_)))
            d.line([x, y + r, x, to_screen(anchor, scr, s, ang, (cx, 36))[1]], fill=(255, 214, 10, int(200 * a_)), width=3)
    # el agua desborda los mamparos
    ov_a = ease((ph - 0.6) / 0.2)
    if ov_a > 0:
        for k, bx in enumerate((735, 675, 615)):
            x, y = to_screen(anchor, scr, s, ang, (bx, 44))
            if 0 < x < W:
                for j in range(6):
                    q = (t * 0.9 + j / 6 + k * 0.3) % 1.0
                    d.ellipse([x - 5 - 30 * q * s * 0.2, y - 40 * q * (1 - q) * 3 + 18 * q - 4, x + 3, y - 40 * q * (1 - q) * 3 + 18 * q + 4], fill=(180, 225, 255, int(220 * (1 - q) * ov_a)))
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    draw_waves(ov, front, t, xoff=t * 50)
    ov.putalpha(ov.getchannel('A').point(lambda v: int(v * 0.30)))
    c.alpha_composite(ov)
    reflection(c, anchor, scr, s, ang, t, wl + dy, 60)
    top_dark(c, 300, 110)
    chip(c, '5 DE 16 COMPARTIMENTOS ESTANCOS INUNDADOS', 150, ease((t - 0.2) / 0.6), 28)
    text_center(c, 'CORTE ILUSTRADO DEL CASCO', 1215, 30, alpha=0.9 * ease(t / 0.8), spacing=3, stroke=2)
    if ov_a > 0:
        text_center(c, 'EL AGUA DESBORDA LOS MAMPAROS', 1170, 30, col=(255, 214, 10), alpha=ov_a, spacing=2, stroke=3)
    return c


# ====================================================================== ESCENA 6
_walkers = None


def walkers():
    global _walkers
    if _walkers is None:
        rnd = random.Random(14)
        _walkers = []
        for k in range(20):
            a_ = rnd.uniform(330, 560)
            b_ = a_ + rnd.uniform(70, 170)
            _walkers.append(dict(a=a_, b=min(b_, 790), v=rnd.uniform(7, 13), ph=rnd.random(), kind=k, hat=('hair' if k % 4 == 1 else 'bowler'),
                                 female=(k % 4 == 1), still=(k % 6 == 5)))
    return _walkers


def splash_fx(d, x, y, u, big=1.0):
    if u < 0 or u > 1.1:
        return
    rnd = random.Random(int(x))
    for k in range(18):
        ang = -math.pi * (0.15 + 0.7 * rnd.random())
        sp = rnd.uniform(90, 240) * big
        px = x + math.cos(ang) * sp * u
        py = y + math.sin(ang) * sp * u + 380 * u * u
        d.ellipse([px - 4, py - 4, px + 4, py + 4], fill=(225, 244, 255, int(230 * (1 - u / 1.1))))
    for r in (40, 80, 120):
        rr = r * (0.3 + u)
        d.ellipse([x - rr, y - rr * 0.18, x + rr, y + rr * 0.18], outline=(230, 246, 255, int(180 * (1 - u / 1.1))), width=3)


def scene6(t):
    A = assets()
    c = canvas()
    hz = 640
    sky_ocean(c, hz, NIGHT_SKY, NIGHT_SEA)
    stars_scene(c, t, hz)
    ph = clamp01(t / 8.0)
    s = lerp(2.7, 3.0, ease(ph))
    ang = lerp(3.0, 6.0, ph)
    anchor = (565, 60)
    scr = (540 + lerp(30, -20, ph), 880 + 1.5 * math.sin(t * 0.9))
    wl_here = to_screen(anchor, scr, s, ang, (565, 0))[1]
    layers = sea_layers(hz, wl_here + 20, amp=2.4, c0=(20, 40, 70), c1=(10, 22, 44), crest=lambda f: (90, 125, 175, 110) if f < 0.85 else None, spd=0.7, n=11)
    back, front = split_layers(layers, wl_here)
    draw_waves(c, back, t, xoff=t * 30)
    place(c, A['night6'], anchor, scr, s, ang)
    ship_extras(c, anchor, scr, s, ang, t, flags=False)
    d = ImageDraw.Draw(c)
    # --- personas caminando por la cubierta de botes (pasajeros anónimos) ---
    for w in walkers():
        if w['still']:
            xu, vx = (w['a'] + w['b']) / 2, 0.0
        else:
            u = t * w['v'] / max(40.0, w['b'] - w['a']) + w['ph']
            xu = w['a'] + (w['b'] - w['a']) * tri(u)
            vx = 1.0 if (u % 1.0) < 0.5 else -1.0
        # algunos se dirigen hacia el costado de los botes (derecha) con el avance del tiempo
        xu += 18 * ph * (w['kind'] % 3)
        x, y = to_screen(anchor, scr, s, ang, (xu, 103 + (w['kind'] % 3) * 0.6))
        figure(d, x, y, 28 * s, t, ph=w['kind'] * 1.3, vx=vx, pose='walk', coat=PASSENGER_COATS[w['kind'] % 7], hat=w['hat'], lum=0.82, female=w['female'])
    # --- botes dinámicos ---
    slots = [(8, 0.0, 7), (9, 0.0, 8), (10, 1.4, 4), (11, 0.0, 6), (12, 2.8, 2), (13, 0.0, 8)]
    boats = []
    for si, tl, npeople in slots:
        ux = 212 + 33 * si + 14
        DUR = 3.8
        q = ease((t - tl) / DUR) if tl > 0 else 0.0
        land = tl + DUR
        start = to_screen(anchor, scr, s, ang, (ux, 105))
        water_y = to_screen(anchor, scr, s, ang, (ux + 40, 0))[1] + 8
        cy = lerp(start[1], water_y, q)
        sway = math.sin(t * 2.2 + si) * 5 * (1 - q) * (1 if tl > 0 else 0.3)
        cx = start[0] + 16 * q + sway
        away = max(0.0, t - land)
        cx += away * 70
        loaded = npeople
        if tl > 0:
            loaded = npeople + int(min(5, max(0, (t - (tl - 1.8)) / 0.35)))
        boats.append((si, ux, tl, q, cx, cy, loaded, land, away))
    # cargadores: pasajeros que caminan hacia los botes que se bajan y suben a bordo
    for si, ux, tl, q, cx, cy, loaded, land, away in boats:
        if tl <= 0:
            continue
        for k in range(5):
            t_arr = tl - 1.8 + 0.35 * k
            x0 = ux - 60 - 16 * k
            if t > t_arr:
                continue
            u = clamp01((t - (t_arr - 2.0)) / 2.0)
            xu = lerp(x0, ux, ease(u))
            x, y = to_screen(anchor, scr, s, ang, (xu, 103))
            figure(d, x, y, 28 * s, t, ph=k * 2 + si, vx=(1 if 0 < u < 1 else 0), pose='walk', coat=PASSENGER_COATS[(k + si) % 7], hat=('hair' if k % 2 else 'bowler'), lum=0.82, female=(k % 2 == 1))
    # tripulación: organiza la evacuación y ayuda con las cuerdas de los pescantes
    crew = [(520, 'point', 1), (578, 'wave', 1), (618, 'pull', 1), (665, 'point', -1), (470, 'pull', 1), (700, 'wave', -1)]
    for k, (xu, pose, fdir) in enumerate(crew):
        x, y = to_screen(anchor, scr, s, ang, (xu, 103.5))
        figure(d, x, y, 29 * s, t, ph=k * 1.7, vx=0.01 * fdir, pose=pose, coat=(20, 30, 54), hat='cap', lum=0.95, crew=True)
    for si, ux, tl, q, cx, cy, loaded, land, away in boats:
        size = 28 * s * 2.0
        top1 = to_screen(anchor, scr, s, ang, (ux - 10, 128))
        top2 = to_screen(anchor, scr, s, ang, (ux + 10, 128))
        start_y = to_screen(anchor, scr, s, ang, (ux, 105))[1]
        d = ImageDraw.Draw(c)
        if away <= 0:
            d.line([top1[0], top1[1], top1[0] + 8, start_y - 20], fill=(14, 14, 18, 255), width=5)
            d.line([top2[0], top2[1], top2[0] - 8, start_y - 20], fill=(14, 14, 18, 255), width=5)
            d.line([top1[0], top1[1], cx - size * 0.42, cy - size * 0.22], fill=(150, 140, 120, 230), width=2)
            d.line([top2[0], top2[1], cx + size * 0.42, cy - size * 0.22], fill=(150, 140, 120, 230), width=2)
        rock = math.sin(t * 2.4 + si) * (4 * (1 - q) + (3 if away > 0 else 0))
        lifeboat(c, cx, cy + size * 0.12, size, ang=ang * 0.4 * (1 - q) + rock, n_people=loaded if (tl == 0 or t > tl - 1.8) else 0, t=t, seed=si, oars=(away > 0.3))
        d = ImageDraw.Draw(c)
        splash_fx(d, cx, cy + size * 0.2, t - land, 1.0)
    rocket(c, t, 1.0, 960, 560, 900, 410)
    rocket(c, t, 3.6, 860, 560, 800, 380)
    rocket(c, t, 5.6, 980, 560, 930, 420)
    draw_waves(c, front, t, xoff=t * 30)
    reflection(c, anchor, scr, s, ang, t, wl_here, 40)
    gp = ease((t - 2.2) / 1.2)
    if gp > 0:
        ov = Image.new('RGBA', (W, 300), (0, 0, 0, 0))
        od = ImageDraw.Draw(ov)
        od.rounded_rectangle([60, 0, W - 60, 230], radius=22, fill=(4, 8, 16, 170))
        f = font('LiberationSans-Bold.ttf', 32)
        od.text((100, 18), 'PERSONAS A BORDO: más de 2.200', font=f, fill=(255, 255, 255, 255))
        od.rounded_rectangle([100, 64, 100 + 880 * gp, 94], radius=8, fill=(120, 170, 235, 255))
        od.text((100, 118), 'PLAZAS EN LOS BOTES: aprox. la mitad', font=f, fill=(255, 214, 10, 255))
        od.rounded_rectangle([100, 164, 100 + 880 * 0.54 * gp, 194], radius=8, fill=(255, 214, 10, 255))
        od.rounded_rectangle([100, 164, 980, 194], radius=8, outline=(255, 255, 255, 120), width=2)
        blit_alpha(c, ov, (0, 110), gp)
    return c


# ====================================================================== ESCENA 7
T_LIGHT = 1.3
T_BREAK = 2.0


def scene7(t):
    A = assets()
    c = canvas()
    hz = 880
    sky_ocean(c, hz, NIGHT_SKY, NIGHT_SEA)
    stars_scene(c, t, hz)
    s = 1.15
    pivot = (BREAK_X, 0)
    base = (610.0, 1070.0)
    wl = base[1]
    layers = sea_layers(hz, wl, amp=2.2, c0=(20, 40, 70), c1=(10, 22, 44), crest=lambda f: (90, 125, 175, 100) if f < 0.85 else None, spd=0.7, n=11)
    back, front = split_layers(layers, wl)
    d = ImageDraw.Draw(c)
    for k in range(30):
        d.rectangle([0, hz - k * 3, W, hz - k * 3 + 3], fill=(70, 100, 150, int(28 * (1 - k / 30))))
    draw_waves(c, back, t, xoff=t * 25)
    shimmer(c, t, hz + 4, wl + 220, (170, 200, 245), n=150, seed=15, maxlen=70)
    if t < T_LIGHT:
        lit = 1.0
    elif t < T_LIGHT + 0.7:
        u = (t - T_LIGHT) / 0.7
        lit = max(0.0, 0.5 + 0.5 * math.sin((t - T_LIGHT) * 38)) * (1 - u) * 0.9 + (0.25 if u < 0.2 else 0)
    else:
        lit = 0.0
    if t < T_BREAK:
        q = ease(t / T_BREAK)
        ang = lerp(2.5, 19.0, q ** 0.9)
        off_y = 26 * q
        scr = (base[0], base[1] + off_y)
        place(c, A['dark'], pivot, scr, s, ang)
        if lit > 0:
            place(c, A['night'], pivot, scr, s, ang, alpha=min(1.0, lit))
        funnel_smoke2(c, pivot, scr, s, ang, t, (34, 40, 54), alpha=0.4)
        bp = to_screen(pivot, scr, s, ang, (960, -10))
        foam(c, bp[0], bp[1], 70, t, 190, 4)
    else:
        u = t - T_BREAK
        qb = ease(u / 2.7)
        ang_b = lerp(19.0, 54.0, qb)
        offb = (lerp(0, 110, qb), lerp(26, 760, qb ** 1.2))
        settle = ease(clamp01(u / 0.8))
        up = ease(clamp01((u - 0.9) / 1.7))
        ang_s = lerp(19.0, 9.0, settle) if u < 0.9 else lerp(9.0, 80.0, up)
        slide = ease(clamp01((u - 2.2) / 1.4))
        offs = (lerp(0, -22, settle), lerp(26, 44, settle) + 80 * up + 900 * slide)
        sb = (base[0] + offb[0], base[1] + offb[1])
        ss = (base[0] + offs[0], base[1] + offs[1])
        place(c, A['dark_p']['stern'], pivot, ss, s, ang_s)
        place(c, A['dark_p']['bow'], pivot, sb, s, ang_b)
        d = ImageDraw.Draw(c)
        if u < 2.6:
            for k in range(14):
                phh = (u * 0.9 + k * 0.07) % 1.0
                r = 20 + 80 * phh
                x = base[0] + 10 + 9 * k - 80 * phh
                y = base[1] - 30 - 190 * phh + 4 * k
                d.ellipse([x - r, y - r, x + r, y + r], fill=(205, 216, 230, int(60 * (1 - phh) * (1 - u / 2.6))))
        # espuma y salpicaduras en la ruptura
        if u < 1.4:
            rnd = random.Random(3)
            for k in range(26):
                a_ = u - rnd.uniform(0, 0.4)
                if a_ > 0:
                    px = base[0] + rnd.uniform(-60, 80) + rnd.uniform(-120, 120) * a_
                    py = base[1] - 20 - 260 * a_ * (1 - a_ * 0.9) + rnd.uniform(-10, 10)
                    d.ellipse([px - 4, py - 4, px + 4, py + 4], fill=(230, 244, 255, int(220 * (1 - a_ / 1.2))))
    draw_waves(c, front, t, xoff=t * 25)
    d = ImageDraw.Draw(c)
    if t > T_BREAK:
        u = t - T_BREAK
        for k in range(6):
            rr = 80 + 58 * k + u * 40
            a_ = int(130 * max(0, 1 - (k * 0.15 + u * 0.09)))
            d.ellipse([base[0] - rr - 40, base[1] - rr * 0.07 + 8, base[0] + rr + 40, base[1] + rr * 0.07 + 20], outline=(220, 238, 250, a_), width=3)
        for k in range(26):
            ph_ = (u * 0.9 + k * 0.13) % 1.0
            bx = base[0] + (k * 41 % 220) - 110
            by = base[1] + 20 + 60 * ph_
            d.ellipse([bx - 3, by - 3, bx + 3, by + 3], outline=(220, 244, 255, int(180 * (1 - ph_))), width=2)
    if t > 4.5:
        k = ease((t - 4.5) / 1.4)
        rnd = random.Random(4)
        for i in range(30):
            x = base[0] + rnd.gauss(-20, 230)
            y = base[1] + 22 + rnd.uniform(0, 100) + 3 * math.sin(t * 1.5 + i)
            w_ = rnd.uniform(10, 36)
            d.line([x - w_, y, x + w_, y + rnd.uniform(-3, 3)], fill=(78, 60, 44, int(255 * k)), width=3)
    mist(c, t, hz + 20, 260, 36, 8, 7)
    top_dark(c, 300, 110)
    chip(c, '2:20 A. M. · 15 DE ABRIL DE 1912', 140, ease((t - 2.2) / 0.6) if t > 2.2 else 0, 36)
    return c


# ====================================================================== ESCENA 8
def lerp_stops(a, b, k):
    return [(p, lerpc(c1, c2, k)) for (p, c1), (_, c2) in zip(a, b)]


DAWN2_SKY = [(0, (38, 58, 112)), (0.55, (150, 120, 150)), (0.88, (255, 170, 100)), (1, (255, 226, 160))]
DAWN2_SEA = [(0, (240, 176, 120)), (0.12, (130, 112, 140)), (0.4, (34, 52, 88)), (1, (6, 14, 30))]


def scene8a(t):
    A = assets()
    c = canvas()
    hz = 900
    k = clamp01(t / 5.0)
    sky_ocean(c, hz, lerp_stops(DAWN_SKY, DAWN2_SKY, k), lerp_stops(DAWN_SEA, DAWN2_SEA, k))
    draw_stars(c, t, hz, 0.35 * (1 - k))
    d = ImageDraw.Draw(c)
    glow = Image.new('RGBA', (W, 600), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    sun_y = 560 - 70 * k
    for j in range(36):
        r = 50 + j * 24
        gd.ellipse([280 - r, sun_y - r * 0.45, 280 + r, sun_y + r * 0.45], fill=(255, 196, 120, int(7 + 3 * k)))
    gd.ellipse([280 - 54, sun_y - 54, 280 + 54, sun_y + 54], fill=(255, 238, 190, 255))
    c.alpha_composite(glow, (0, hz - 560))
    for (x, sc_) in ((820, 0.26), (180, 0.2), (560, 0.14)):
        draw_iceberg(c, x, hz + 5, sc_, alpha=0.9, under=False, dark=(1.0, 0.86, 0.82))
    layers = sea_layers(hz, 1200, amp=3.4, c0=(150, 118, 134), c1=(12, 24, 46), crest=lambda f: (255, 205, 150, 120) if f < 0.5 else None, spd=0.7, n=11)
    draw_waves(c, [L for L in layers if L['y'] < 1150], t, xoff=t * 20)
    shimmer(c, t, hz + 4, 1120, (255, 214, 150), n=130, seed=22, xc=280, spread=170, maxlen=110)
    # RMS Carpathia llegando
    q = ease(t / 4.6)
    cs = 1.5
    csx = lerp(-520, 330, q)
    cwl = 1050
    ca = (475, 0)
    pos = (csx, cwl + 2.2 * math.sin(t * 1.2))
    cang = 0.3 * math.sin(t)
    place(c, A['carp'], ca, pos, cs, cang)
    ship_flag = to_screen(ca, pos, cs, cang, (730, 140))
    flag(c, ca, pos, cs, cang, t, (730, 140), 22, 9, (186, 28, 36, 255), 0.5)
    o = to_screen(ca, pos, cs, cang, (470, 152))
    smoke(c, o, t, (44, 46, 56), scale=1.2, wind=(-1.1, -0.1), rate=12, life=5.5, seed=3, alpha=0.6)
    # botes remando hacia el Carpathia
    boats = [(900, 1110, 130, 12, 1, 640), (780, 1180, 150, 11, 2, 540), (600, 1130, 120, 10, 3, 420),
             (980, 1200, 160, 14, 5, 760), (330, 1128, 130, 9, 4, 300), (700, 1090, 86, 8, 6, 560)]
    for bx0, by, bs_, npx, sd, bx1 in sorted(boats, key=lambda b: b[1]):
        bx = lerp(bx0, bx1, ease(t / 5.0))
        lifeboat(c, bx + 5 * math.sin(t * 0.7 + sd), by + 4 * math.sin(t * 1.1 + sd * 2), bs_, ang=3 * math.sin(t * 0.9 + sd), n_people=npx, t=t, seed=sd, oars=True)
    # bote junto al casco: escala de cuerda por la que suben los supervivientes
    if t > 2.5:
        d = ImageDraw.Draw(c)
        alx = csx + (360 - 475) * cs
        lx0, ly0 = alx, cwl - 44 * cs
        bxs, bys = alx + 28, cwl + 58
        a_ = ease((t - 2.5) / 0.8)
        lifeboat(c, bxs, bys + 4 * math.sin(t * 1.3), 150, ang=2 * math.sin(t * 1.1), n_people=8, t=t, seed=11, oars=False)
        d = ImageDraw.Draw(c)
        d.line([lx0, ly0, bxs - 8, bys - 34], fill=(180, 160, 120, int(255 * a_)), width=3)
        d.line([lx0 + 16, ly0, bxs + 8, bys - 34], fill=(180, 160, 120, int(255 * a_)), width=3)
        for r in range(1, 6):
            fr = r / 6
            d.line([lerp(lx0, bxs - 8, fr), lerp(ly0, bys - 34, fr), lerp(lx0 + 16, bxs + 8, fr), lerp(ly0, bys - 34, fr)], fill=(180, 160, 120, int(255 * a_)), width=2)
        for j in range(3):
            fr = 1 - ((t * 0.12 + j / 3) % 1.0)
            fx = lerp(lx0 + 8, bxs, fr)
            fy = lerp(ly0, bys - 34, fr)
            figure(d, fx, fy + 22, 34, t, ph=j, vx=0.0, pose='pull', coat=PASSENGER_COATS[(j + 3) % 7], hat='hair' if j == 1 else 'bowler', lum=0.9, female=(j == 1))
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    draw_waves(ov, [L for L in layers if L['y'] >= 1150], t, xoff=t * 20)
    c.alpha_composite(ov)
    d = ImageDraw.Draw(c)
    for kk, (fx, fy, r) in enumerate(((100, 1050, 38), (740, 1250, 52), (990, 1020, 30), (440, 1020, 26))):
        floe(d, fx, fy, r, t, kk)
    mist(c, t, hz - 60, 240, 36, 9, 9, (255, 214, 190))
    top_dark(c, 300, 60)
    return c


def scene8(t):
    a = scene8a(min(t, 5.2))
    if t < 4.0:
        return a
    s_ = S.sunk_scene(t)
    k = ease((t - 4.0) / 1.0)
    out = Image.blend(a, s_, k) if k < 1 else s_
    f1 = ease((t - 5.1) / 0.5)
    if f1 > 0:
        lay = subtitle_layer('MÁS DE [[1.500 VIDAS]] PERDIDAS.', 78, 940)
        blit_alpha(out, lay, (0, 190), f1)
        lay2 = subtitle_layer('UNA TRAGEDIA QUE EL MUNDO [[NUNCA OLVIDARÁ.]]', 66, 940)
        blit_alpha(out, lay2, (0, 190 + lay.height + 24), ease((t - 5.7) / 0.5))
    f2 = ease((t - 7.3) / 0.45)
    if f2 > 0:
        lay3 = subtitle_layer('[[¿QUÉ OTRA HISTORIA REAL DEBERÍAMOS CONTAR?]]', 62, 940)
        blit_alpha(out, lay3, (0, 1270), f2)
    return out


SCENES = [scene1, scene2, scene3, scene4, scene5, scene6, scene7, scene8]

# (zoom inicial, zoom final, paneo x ini, x fin, paneo y ini, y fin, balanceo en grados)
CAM = [
    (1.00, 1.07, 0, -10, 0, 30, 0.35),   # 1: empuje lento hacia el barco
    (1.00, 1.07, 0, 25, 0, -10, 0.30),   # 2
    (1.00, 1.08, 0, -30, 0, -20, 0.25),  # 3: tensión creciente
    (1.00, 1.05, 0, 0, 0, 0, 0.0),       # 4
    (1.00, 1.06, 0, 20, 0, 0, 0.2),      # 5
    (1.00, 1.07, 0, -10, 0, 10, 0.3),    # 6
    (1.10, 1.00, 0, 0, -40, 0, 0.4),     # 7: se aleja para ver todo
    (1.04, 1.00, 0, 0, 0, 0, 0.2),       # 8
]

SUBS = [
    (5.35, 11.8, 'El [[10 de abril de 1912]], el Titanic inició su viaje inaugural rumbo a Nueva York con [[más de 2.200 personas]] a bordo.'),
    (12.3, 15.8, 'La noche del [[14 de abril]], el Titanic navegaba por aguas del Atlántico Norte.'),
    (15.8, 18.8, 'Durante el viaje se habían recibido [[advertencias sobre hielo]].'),
    (19.3, 23.0, 'A las [[11:40 de la noche]], el Titanic chocó contra un [[iceberg]].'),
    (23.0, 26.8, 'El casco sufrió daños que permitieron la [[entrada de agua]].'),
    (27.3, 30.8, 'El agua comenzó a [[inundar]] varios compartimentos.'),
    (30.8, 34.6, 'El barco [[no podía mantenerse a flote]].'),
    (35.3, 42.6, 'Los pasajeros comenzaron a evacuar el barco, pero los botes salvavidas [[no tenían capacidad suficiente]] para todos.'),
    (43.3, 47.6, 'A las [[2:20 de la madrugada]] del 15 de abril, el Titanic desapareció bajo las aguas.'),
    (47.6, 50.8, '[[Más de 1.500 personas]] perdieron la vida.'),
    (51.2, 53.4, 'El RMS [[Carpathia]] rescató a los supervivientes.'),
    (53.4, 55.8, 'La tragedia cambió para siempre las normas de [[seguridad marítima]].'),
]
S.SUBS = SUBS


def shot(si, tl):
    c = SCENES[si](tl)
    z0, z1, px0, px1, py0, py1, roll = CAM[si]
    q = ease(clamp01((tl + 0.3) / (BOUNDS[si + 1] - BOUNDS[si] + 0.6)))
    z = lerp(z0, z1, q)
    sway = roll * math.sin((tl + si) * 0.55)
    return camera(c, z, (lerp(px0, px1, q), lerp(py0, py1, q)), sway)


def render_frame(i):
    T = i / FPS
    si = 0
    for k in range(8):
        if BOUNDS[k] <= T < BOUNDS[k + 1]:
            si = k
    XF = 0.3
    nxt, prv = si + 1, si - 1
    if nxt < 8 and T > BOUNDS[nxt] - XF:
        a = ease((T - (BOUNDS[nxt] - XF)) / (2 * XF))
        c = Image.blend(shot(si, T - BOUNDS[si]), shot(nxt, T - BOUNDS[nxt]), a)
    elif prv >= 0 and T < BOUNDS[si] + XF:
        a = ease((T - (BOUNDS[si] - XF)) / (2 * XF))
        c = Image.blend(shot(prv, T - BOUNDS[prv]), shot(si, T - BOUNDS[si]), a)
    else:
        c = shot(si, T - BOUNDS[si])
    S.overlay_subs(c, T)
    arr = np.asarray(c.convert('RGB')).astype(np.float32)
    arr = vignette(arr, 0.55)
    rng = np.random.RandomState(i)
    arr += rng.randn(H // 2, W // 2, 1).repeat(2, 0).repeat(2, 1) * 2.0
    if T < 0.5:
        arr *= ease(T / 0.5)
    return np.clip(arr, 0, 255).astype(np.uint8)
