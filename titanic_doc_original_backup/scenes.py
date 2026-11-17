# -*- coding: utf-8 -*-
"""Las 8 escenas del documental (60 s, 30 fps, 1080x1920). Todo 2D, dibujado por capas."""
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
from gfx import *
from gfx import _cache, _blit

FPS = 30
TOTAL = 60.0
BOUNDS = [0, 5, 12, 19, 27, 35, 43, 51, 60]

# ------------------------------------------------------------------ recursos (por proceso)
_A = {}


def assets():
    if _A:
        return _A
    _A['night'] = pyramid(build_liner(True, False))
    _A['dark'] = pyramid(build_liner(False, False))
    _A['day'] = pyramid(build_liner(False, True))
    # S6/S7: botes dinámicos -> huecos en cubierta
    skip = {8, 9, 10, 11, 12, 13}
    _A['night6'] = pyramid(build_liner(True, False, skip))
    lv = [2.0, 1.0, 0.5, 0.25]
    n7 = pyramid(build_liner(True, False, skip), lv)
    d7 = pyramid(build_liner(False, False, skip), lv)
    _A['lit_p'] = split_pieces(n7)
    _A['dark_p'] = split_pieces(d7)
    _A['wreck_p'] = split_pieces(pyramid(build_liner(False, False), lv))
    _A['carp'] = build_carpathia()
    return _A


def build_carpathia():
    m = MASTER
    im = Image.new('RGBA', (int(SPR_W * m), int(SPR_H * m)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    def P(x, y):
        return ((x + 40) * m, (WLY - y) * m)

    def poly(pts, fill):
        d.polygon([P(*p) for p in pts], fill=fill)

    def rect(x0, y0, x1, y1, fill):
        d.rectangle([P(x0, y1), P(x1, y0)], fill=fill)

    def line(pts, fill, w=1.0):
        d.line([P(*p) for p in pts], fill=fill, width=max(1, int(w * m)))
    poly([(160, 40), (172, 0), (200, -26), (700, -26), (790, 0), (840, 36), (850, 48), (700, 43), (160, 42)], (14, 14, 18))
    rect(172, -26, 790, -8, (110, 30, 28))
    poly([(160, 40), (172, 0), (200, -26), (700, -26), (790, 0), (840, 36), (850, 48), (700, 43), (160, 42)], (14, 14, 18))
    rect(172, -26, 760, -10, (110, 30, 28))
    for x in np.arange(190, 800, 14):
        cx, cy = P(x, 28)
        d.ellipse([cx - 2 * m, cy - 2 * m, cx + 2 * m, cy + 2 * m], fill=(255, 210, 120))
    rect(270, 42, 640, 66, (220, 216, 206))
    rect(300, 66, 600, 84, (206, 202, 192))
    rect(610, 42, 700, 92, (222, 218, 208))
    rect(625, 92, 690, 104, (200, 196, 186))
    for x in np.arange(280, 620, 12):
        rect(x, 50, x + 5, 58, (255, 214, 120))
    for x in np.arange(310, 590, 12):
        rect(x, 71, x + 5, 78, (255, 214, 120))
    for x in np.arange(618, 695, 11):
        rect(x, 78, x + 5, 86, (255, 214, 120))
    fx = 470
    poly([(fx - 22, 84), (fx + 22, 84), (fx + 18, 150), (fx - 18, 150)], (196, 50, 36))
    poly([(fx - 21, 134), (fx + 21, 134), (fx + 18, 150), (fx - 18, 150)], (16, 16, 18))
    for mx, top in ((250, 150), (730, 140)):
        poly([(mx - 2, 44), (mx + 2, 44), (mx + 1, top), (mx - 1, top)], (60, 64, 76))
    line([(250, 150), (160, 44)], (70, 76, 90), 0.35)
    line([(250, 150), (470, 150), (730, 140)], (70, 76, 90), 0.3)
    line([(730, 140), (850, 52)], (70, 76, 90), 0.35)
    line([(250, 70), (320, 130)], (70, 76, 90), 0.5)
    return pyramid(im, [4.0, 2.0, 1.0, 0.5, 0.25])


# ------------------------------------------------------------------ utilidades de escena
NIGHT_SKY = [(0, (2, 5, 16)), (0.62, (8, 17, 42)), (1, (24, 42, 76))]
NIGHT_SEA = [(0, (34, 58, 94)), (0.4, (20, 40, 72)), (1, (11, 24, 46))]


def canvas():
    return Image.new('RGB', (W, H), (0, 0, 0))


def sea_layers(horizon, ylimit, amp=5.0, c0=(18, 38, 66), c1=(12, 26, 50), crest=None, wlscale=1.0, n=9, spd=1.0):
    layers = []
    for j in range(n):
        f = j / (n - 1)
        y = horizon + (ylimit - horizon + 60) * (f ** 1.6)
        layers.append(dict(y=y, amp=amp * (0.25 + 1.7 * f), wl=(150 + 460 * f) * wlscale, sp=(0.9 + 0.5 * (1 - f)) * spd,
                           ph=j * 1.7, col=lerpc(c0, c1, f), crest=crest(f) if crest else None, par=0.4 + f * 1.4))
    return layers


def split_layers(layers, wl_y):
    back = [L for L in layers if L['y'] < wl_y - 6]
    front = [L for L in layers if L['y'] >= wl_y - 6]
    return back, cover(back, front, wl_y)


def cover(back, front, wl_y):
    ref = front[0] if front else back[-1]
    extra = dict(ref)
    extra.update(y=wl_y - 2, amp=2.0, wl=330, ph=0.6, par=1.0, col=lerpc(ref['col'], (0, 0, 0), 0.08), crest=(120, 160, 210, 110))
    return [extra] + front


def bob(t, a=2.0):
    return a * math.sin(t * 1.25) + 0.7 * a * math.sin(t * 2.3 + 1), 0.25 * math.sin(t * 1.1 + 0.5)


def top_dark(c, h=760, a=150):
    key = ('topdark', h, a)
    if key not in _cache:
        arr = np.zeros((h, W, 4), np.uint8)
        arr[..., 3] = (np.linspace(1, 0, h) ** 1.5 * a).astype(np.uint8)[:, None]
        _cache[key] = Image.fromarray(arr, 'RGBA')
    c.alpha_composite(_cache[key], (0, 0))


def foam(c, x, y, w, t, alpha=150, seed=1):
    d = ImageDraw.Draw(c)
    rnd = random.Random(seed)
    for i in range(14):
        xx = x + rnd.uniform(-w, w)
        ph = rnd.uniform(0, 6)
        yy = y + 4 * math.sin(t * 3 + ph) + rnd.uniform(-6, 6)
        ln = rnd.uniform(10, 40)
        d.line([xx - ln / 2, yy, xx + ln / 2, yy], fill=(235, 245, 255, int(alpha * (0.5 + 0.5 * math.sin(t * 4 + ph)))), width=3)


def funnel_smoke(c, anchor, screen, s, ang, t, color, alpha=0.5, seed=0, wind=(-1.0, -0.1), which=(0, 1, 2)):
    for i in which:
        fx = FUNNELS[i] - 9
        o = to_screen(anchor, screen, s, ang, (fx, 194))
        smoke(c, o, t + i * 0.7, color, scale=max(0.45, s * 0.95), wind=wind, rate=9, life=5.0, seed=seed + i * 13, alpha=alpha)


def deck_people(d, anchor, screen, s, ang, t, items, col_choices, h_units=14.0):
    for k, (ux, uy, wave, ph) in enumerate(items):
        x, y = to_screen(anchor, screen, s, ang, (ux, uy))
        person(d, x, y, h_units * s, col=col_choices[k % len(col_choices)], wave=wave, t=t, ph=ph, hat=(k % 3 == 0))


def stars_scene(c, t, hz, a=1.0):
    draw_stars(c, t, hz, a)


# ------------------------------------------------------------------ ESCENA 1
def scene1(t):
    A = assets()
    c = canvas()
    hz = 980
    sky_ocean(c, hz, NIGHT_SKY, NIGHT_SEA)
    stars_scene(c, t, hz)
    p = clamp01(t / 5.0)
    pe = ease(p) * 0.55 + p * 0.45
    s = lerp(0.7, 1.12, pe)
    wl = lerp(1085, 1185, pe)
    sx = lerp(610, 520, pe)
    dy, ang = bob(t, 2.2 * s)
    anchor = (500, 0)
    scr = (sx, wl + dy)
    # bruma en el horizonte
    d = ImageDraw.Draw(c)
    for k in range(40):
        a = int(34 * (1 - k / 40))
        d.rectangle([0, hz - k * 3, W, hz - k * 3 + 3], fill=(70, 100, 150, a))
    layers = sea_layers(hz, wl, amp=2.6, c0=(22, 42, 72), c1=(12, 26, 50), crest=lambda f: (90, 125, 175, 130) if f < 0.85 else None)
    back, front = split_layers(layers, wl)
    draw_waves(c, back, t, xoff=t * 55)
    shimmer(c, t, hz + 4, wl + 40, (150, 180, 230), n=120, seed=5, maxlen=60)
    shimmer(c, t, wl + 6, wl + 160, (255, 196, 110), n=70, seed=9, xc=sx, spread=230 * s, maxlen=90)
    place(c, A['night'], anchor, scr, s, ang)
    funnel_smoke(c, anchor, scr, s, ang, t, (34, 40, 54), alpha=0.5)
    draw_waves(c, front, t, xoff=t * 55)
    foam(c, to_screen(anchor, scr, s, ang, (930, 0))[0], wl + 2 + dy, 60 * s, t)
    top_dark(c, 800, 170)
    # títulos
    a1 = ease((t - 0.5) / 0.8)
    a2 = ease((t - 1.2) / 0.8)
    a3 = ease((t - 2.4) / 0.8)
    out = 1 - ease((t - 4.75) / 0.25)
    sc = 1 + 0.03 * (1 - a1)
    text_center(c, 'ASÍ FUE COMO SE', 150, 94, fontname='LiberationSerif-Bold.ttf', alpha=a1 * out, stroke=4)
    text_center(c, 'HUNDIÓ EL', 262, 94, fontname='LiberationSerif-Bold.ttf', alpha=a2 * out, stroke=4)
    text_center(c, 'TITANIC', 360, 196, col=(255, 214, 10), fontname='LiberationSerif-Bold.ttf', alpha=a2 * out, stroke=6)
    text_center(c, 'UNA TRAGEDIA QUE CAMBIÓ LA HISTORIA', 620, 40, alpha=a3 * out, spacing=3, stroke=3)
    d = ImageDraw.Draw(c)
    d.rectangle([W / 2 - 160 * a3, 596, W / 2 + 160 * a3, 599], fill=(255, 214, 10, int(255 * out)))
    return c


# ------------------------------------------------------------------ ESCENA 2
DAY_SKY = [(0, (112, 164, 212)), (0.65, (200, 222, 234)), (1, (246, 228, 204))]
DAY_SEA = [(0, (112, 158, 176)), (0.2, (58, 108, 134)), (1, (18, 54, 82))]


def cloud(c, x, y, sc, a=0.85):
    pf = puff()
    for dx, dy, r in ((0, 0, 1.0), (60, -10, 1.2), (130, 0, 1.0), (40, 18, 0.9), (95, 16, 1.0), (-40, 14, 0.7), (170, 12, 0.7)):
        sz = int(190 * r * sc)
        p = pf.resize((sz, sz), Image.BILINEAR)
        col = Image.new('RGBA', p.size, (255, 255, 255, 0))
        col.putalpha(p.getchannel('A').point(lambda v: int(v * a)))
        _blit(c, col, int(x + dx * sc - sz / 2), int(y + dy * sc - sz / 2))


def gull(d, x, y, sz, t, ph):
    f = math.sin(t * 7 + ph)
    d.line([x - sz, y + f * sz * 0.5, x, y, x + sz, y + f * sz * 0.5], fill=(250, 250, 250, 255), width=2)


def scene2(t):
    A = assets()
    c = canvas()
    hz = 780
    sky_ocean(c, hz, DAY_SKY, DAY_SEA)
    p = clamp01(t / 7.0)
    e = ease(p)
    # nubes
    for i, (cx, cy, sc) in enumerate(((100, 220, 0.9), (620, 130, 1.2), (880, 380, 0.8), (330, 480, 0.7))):
        cloud(c, (cx - t * (8 + i * 3)) % (W + 500) - 250, cy, sc, 0.8)
    d = ImageDraw.Draw(c)
    # puerto de Southampton al fondo: silueta de grúas y edificios (parallax)
    shift = p * 420
    for k in range(9):
        bx = -120 + k * 95 - shift * 0.3
        bh = 40 + (k * 37 % 70)
        d.rectangle([bx, hz - bh, bx + 70, hz + 2], fill=(128, 140, 152, 255))
        d.rectangle([bx + 8, hz - bh + 8, bx + 18, hz - bh + 20], fill=(150, 160, 170, 255))
    for gx in (60, 300):
        gx2 = gx - shift * 0.34
        d.line([gx2, hz, gx2, hz - 150], fill=(96, 104, 116, 255), width=7)
        d.line([gx2 - 20, hz - 150, gx2 + 140, hz - 130], fill=(96, 104, 116, 255), width=6)
        d.line([gx2 + 140, hz - 130, gx2 + 140, hz - 60], fill=(96, 104, 116, 255), width=2)
    for k in range(8):
        d.rectangle([W - 140 - k * 130 - shift * 0.25, hz - 10, W - 40 - k * 130 - shift * 0.25, hz + 2], fill=(140, 152, 162, 255))
    s = 0.6 * (3.1 ** e)
    wl = lerp(960, 1190, e)
    ux = lerp(500, 640, e)
    sx = lerp(520, 540, e)
    dy, ang = bob(t, 2.0 * s)
    anchor = (ux, 0)
    scr = (sx, wl + dy)
    layers = sea_layers(hz, wl, amp=3.6, c0=(96, 150, 172), c1=(14, 46, 72), crest=lambda f: (200, 230, 240, 150) if f > 0.15 else None)
    back, front = split_layers(layers, wl)
    draw_waves(c, back, t, xoff=t * 70)
    # muelle y multitud a la izquierda (se aleja)
    px = -p * 1500 * (1 if True else 0)
    pier_y = lerp(940, 1015, 0)
    if p < 0.62:
        px0 = 120 + px
        d = ImageDraw.Draw(c)
        d.polygon([(px0 - 700, pier_y), (px0 + 330, pier_y), (px0 + 330, pier_y + 130), (px0 - 700, pier_y + 130)], fill=(70, 58, 50, 255))
        d.rectangle([px0 - 700, pier_y - 6, px0 + 330, pier_y + 8], fill=(104, 88, 72, 255))
        for k in range(6):
            d.rectangle([px0 - 640 + k * 170, pier_y - 110, px0 - 590 + k * 170, pier_y - 6], fill=(92, 74, 64, 255))
        rnd = random.Random(11)
        for k in range(26):
            xx = px0 - 600 + k * 34 + rnd.uniform(-8, 8)
            person(d, xx, pier_y - 6, rnd.uniform(52, 66), col=rnd.choice([(30, 30, 36), (64, 46, 40), (40, 48, 64), (80, 62, 52)]),
                   wave=(k % 3 == 0), t=t, ph=k, hat=(k % 2 == 0))
    # barco (diurno)
    place(c, A['day'], anchor, scr, s, ang)
    d = ImageDraw.Draw(c)
    rnd = random.Random(21)
    items = []
    for k in range(34):
        ux = rnd.uniform(215, 770)
        items.append((ux, 112, k % 4 == 0, rnd.uniform(0, 6)))
    for k in range(8):
        items.append((rnd.uniform(890, 975), 62, k % 2 == 0, rnd.uniform(0, 6)))
        items.append((rnd.uniform(50, 150), 60, k % 2 == 1, rnd.uniform(0, 6)))
    cols = [(34, 34, 42), (74, 52, 46), (44, 54, 76), (96, 70, 60), (26, 30, 38)]
    deck_people(d, anchor, scr, s, ang, t, items, cols, h_units=13.0)
    funnel_smoke(c, anchor, scr, s, ang, t, (72, 74, 82), alpha=0.6, wind=(-1.2, -0.1))
    draw_waves(c, front, t, xoff=t * 70)
    # estela y espuma de proa
    bowp = to_screen(anchor, scr, s, ang, (975, 0))
    foam(c, bowp[0] - 20 * s, wl + dy + 3, 70 * s, t, 200, 3)
    for k in range(5):
        foam(c, to_screen(anchor, scr, s, ang, (60 - k * 60, 0))[0], wl + dy + 4 + k * 5, 60 * s, t + k, 140, 7 + k)
    d = ImageDraw.Draw(c)
    rnd = random.Random(3)
    for k in range(7):
        gull(d, (rnd.uniform(0, W) + t * (30 + 10 * k)) % (W + 200) - 100, 230 + rnd.uniform(0, 340) + 20 * math.sin(t + k), 16 + rnd.uniform(0, 10), t, k)
    # leve calidez
    top_dark(c, 420, 70)
    chip(c, 'SOUTHAMPTON, INGLATERRA · 10 DE ABRIL DE 1912', 140, ease(t / 0.6) * (1 - ease((t - 6.6) / 0.4)), 36)
    return c


# ------------------------------------------------------------------ ESCENA 3
def floe(d, x, y, r, t, ph, a=255):
    o = 2.5 * math.sin(t * 1.3 + ph)
    pts = [(x - r, y + o), (x - r * 0.6, y - r * 0.35 + o), (x - r * 0.1, y - r * 0.5 + o), (x + r * 0.5, y - r * 0.3 + o), (x + r, y + o)]
    d.polygon(pts, fill=(200, 224, 240, a))
    d.polygon([(x + r * 0.1, y - r * 0.5 + o), (x + r * 0.5, y - r * 0.3 + o), (x + r, y + o), (x + r * 0.2, y + o)], fill=(140, 172, 200, a))


def scene3(t):
    A = assets()
    c = canvas()
    hz = 930
    sky_ocean(c, hz, NIGHT_SKY, NIGHT_SEA)
    stars_scene(c, t, hz)
    p = clamp01(t / 7.0)
    e = ease(p)
    s = lerp(1.25, 1.85, e)
    ux = lerp(620, 860, e)
    sx = lerp(540, 420, e)
    anchor = (ux, 100)
    ay = 980
    wl = ay + 100 * s
    dy, ang = bob(t, 1.4 * s)
    scr = (sx, ay + dy)
    layers = sea_layers(hz, wl, amp=1.8, c0=(22, 42, 72), c1=(12, 26, 50), crest=lambda f: (90, 125, 175, 100) if f < 0.85 else None, spd=0.6)
    back, front = split_layers(layers, wl)
    d = ImageDraw.Draw(c)
    for k in range(40):
        d.rectangle([0, hz - k * 3, W, hz - k * 3 + 3], fill=(70, 100, 150, int(30 * (1 - k / 40))))
    draw_waves(c, back, t, xoff=t * 70)
    shimmer(c, t, hz + 4, wl + 200, (170, 200, 245), n=200, seed=15, maxlen=70)
    # hielo adelante (derecha)
    appear = ease((t - 2.0) / 2.0)
    d = ImageDraw.Draw(c)
    if appear > 0:
        draw_iceberg(c, 930, hz + 6, 0.15, alpha=0.8 * appear, under=False)
        for k, (fx, fy, r) in enumerate(((820, hz + 40, 22), (1000, hz + 70, 32), (700, hz + 95, 18), (900, wl - 80, 44), (1040, wl - 20, 56), (760, wl - 36, 30))):
            floe(d, fx - t * 40 * (0.3 + 0.2 * k) % 400 + 200, fy, r, t, k, int(255 * appear))
    place(c, A['night'], anchor, scr, s, ang)
    # radio: advertencias por telegrafía inalámbrica
    mid = to_screen(anchor, scr, s, ang, (500, 172))
    for k in range(4):
        ph = ((t * 0.55 + k * 0.25) % 1.0)
        r = 30 + 330 * ph
        a = int(160 * (1 - ph) * (1 - ease((t - 5.0) / 1.5)))
        if a > 0:
            d.arc([mid[0] - r, mid[1] - r, mid[0] + r, mid[1] + r], 215, 325, fill=(150, 210, 255, a), width=4)
    # vigía en el nido de cuervo (silueta anónima)
    nest = to_screen(anchor, scr, s, ang, (862, 140))
    hh = 20 * s
    d.ellipse([nest[0] - hh * 0.22, nest[1] - hh * 0.95, nest[0] + hh * 0.22, nest[1] - hh * 0.5], fill=(10, 10, 14, 255))
    d.rectangle([nest[0] - hh * 0.26, nest[1] - hh * 1.0, nest[0] + hh * 0.26, nest[1] - hh * 0.86], fill=(10, 10, 14, 255))
    d.polygon([(nest[0] - hh * 0.4, nest[1]), (nest[0] - hh * 0.3, nest[1] - hh * 0.5), (nest[0] + hh * 0.3, nest[1] - hh * 0.5), (nest[0] + hh * 0.4, nest[1])], fill=(12, 12, 16, 255))
    d.rectangle([nest[0] - hh * 0.5, nest[1] - hh * 0.28, nest[0] + hh * 0.5, nest[1] + hh * 0.08], fill=(30, 26, 22, 255))
    # aliento helado
    for k in range(5):
        ph = (t * 0.9 + k * 0.2) % 1.0
        pr = 3 + 10 * ph
        d.ellipse([nest[0] + hh * 0.3 + 40 * ph * 0.6 - pr, nest[1] - hh * 0.78 - 12 * ph - pr, nest[0] + hh * 0.3 + 40 * ph * 0.6 + pr, nest[1] - hh * 0.78 - 12 * ph + pr], fill=(220, 235, 255, int(110 * (1 - ph))))
    funnel_smoke(c, anchor, scr, s, ang, t, (34, 40, 54), alpha=0.5)
    draw_waves(c, front, t, xoff=t * 70)
    foam(c, to_screen(anchor, scr, s, ang, (975, 0))[0], wl + 2 + dy, 60 * s, t, 120)
    # nieve fina / partículas de hielo en el aire
    rnd = random.Random(31)
    d = ImageDraw.Draw(c)
    for k in range(70):
        x = (rnd.uniform(0, W) - t * rnd.uniform(40, 120)) % W
        y = (rnd.uniform(0, H * 0.75) + t * rnd.uniform(20, 60)) % (H * 0.75)
        r = rnd.uniform(1, 2.6)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(220, 235, 255, int(rnd.uniform(60, 150))))
    top_dark(c, 420, 90)
    chip(c, 'NOCHE DEL 14 DE ABRIL DE 1912 · ATLÁNTICO NORTE', 140, ease((t - 0.2) / 0.6) * (1 - ease((t - 6.6) / 0.4)), 34)
    return c


# ------------------------------------------------------------------ ESCENA 4
def shake_offset(t, t0, amp=7.0):
    if t < t0:
        return 0.0, 0.0
    k = math.exp(-(t - t0) * 2.4)
    return amp * k * math.sin(t * 47), amp * 0.6 * k * math.sin(t * 61 + 1)


def inset_contact(c, t, u):
    """Recuadro circular: vista en planta del contacto del hielo con el costado de estribor."""
    R = 250
    lay = Image.new('RGBA', (2 * R, 2 * R), (0, 0, 0, 255))
    d = ImageDraw.Draw(lay)
    arr = vgrad(2 * R, [(0, (8, 40, 72)), (1, (14, 76, 110))], w=2 * R)
    lay.paste(Image.fromarray(arr, 'RGB'), (0, 0))
    d = ImageDraw.Draw(lay)
    # hielo (derecha) deslizándose hacia popa (abajo)
    off = (u * 190) % 120
    ice = [(2 * R, -50)]
    xs = []
    y = -60
    rnd = random.Random(5)
    while y < 2 * R + 130:
        xs.append((320 + 16 * math.sin((y + off * 0) * 0.07) + ((int((y + 600 - u * 190) / 60) * 37) % 41) - 8 + (rnd.random() * 0), y))
        y += 30
    # silueta del hielo moviéndose: shift vertical de textura
    pts = [(2 * R + 40, -60)] + [(x, y - ((u * 190) % 60) + 30) for x, y in xs] + [(2 * R + 40, 2 * R + 130)]
    d.polygon(pts, fill=(222, 238, 248, 255))
    d.polygon([(x + 36, y) for x, y in pts[1:-1]] + [(2 * R + 40, 2 * R + 130), (2 * R + 40, -60)], fill=(160, 190, 214, 255))
    # casco (izquierda): planchas negras con remaches
    press = ease(u / 0.8) * 22 + 6 * math.sin(u * 9)
    d.polygon([(0, 0), (255 - press, 0), (255 - press * 0.6, 2 * R), (0, 2 * R)], fill=(20, 20, 26, 255))
    d.line([255 - press, 0, 255 - press * 0.6, 2 * R], fill=(110, 116, 130, 255), width=5)
    for yy in range(20, 2 * R, 44):
        d.line([0, yy, 252 - press, yy], fill=(36, 38, 46, 255), width=2)
        d.ellipse([240 - press - 4, yy - 4, 240 - press + 4, yy + 4], fill=(90, 94, 106, 255))
    # remaches saltando + chorros de agua entrando
    ramp = ease((u - 0.3) / 1.2)
    for k in range(10):
        ph = (u * 1.4 + k * 0.1) % 1.0
        yy = 40 + k * 46
        x0 = 248 - press
        d.line([x0, yy, x0 - 80 * ph * ramp, yy + 12 * ph], fill=(150, 220, 255, int(220 * (1 - ph) * ramp)), width=4)
        d.line([x0 + 50 * ph * ramp, yy - 18 * ph, x0 + 10, yy], fill=(255, 255, 255, int(180 * (1 - ph) * ramp)), width=3)
    for k in range(14):
        ph = (u * 1.8 + k * 0.071) % 1.0
        xx = 250 + 40 * ph * ((k % 3) - 1)
        yy = (k * 37 + u * 120) % (2 * R)
        d.ellipse([xx - 3, yy - 3, xx + 3, yy + 3], fill=(255, 230, 160, int(230 * (1 - ph))))
    mask = Image.new('L', lay.size, 0)
    ImageDraw.Draw(mask).ellipse([0, 0, 2 * R - 1, 2 * R - 1], fill=255)
    lay.putalpha(mask)
    ring = Image.new('RGBA', lay.size, (0, 0, 0, 0))
    ImageDraw.Draw(ring).ellipse([2, 2, 2 * R - 3, 2 * R - 3], outline=(255, 255, 255, 255), width=7)
    lay = Image.alpha_composite(lay, ring)
    return lay


def scene4(t):
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
    shx, shy = shake_offset(t, TC)
    anchor = (ux, 0)
    scr = (500 + shx, wl + dy + shy)
    ang += shx * 0.05
    layers = sea_layers(hz, wl, amp=1.8, c0=(22, 42, 72), c1=(12, 26, 50), crest=lambda f: (90, 125, 175, 100) if f < 0.85 else None, spd=0.6)
    back, front = split_layers(layers, wl)
    d = ImageDraw.Draw(c)
    for k in range(40):
        d.rectangle([0, hz - k * 3, W, hz - k * 3 + 3], fill=(70, 100, 150, int(30 * (1 - k / 40))))
    draw_waves(c, back, t, xoff=t * 70)
    shimmer(c, t, hz + 4, wl + 200, (170, 200, 245), n=160, seed=15, maxlen=70)
    # iceberg: se aproxima y luego se desliza por el costado
    bow_x = 500 + (992 - ux) * s
    if t < TC:
        q = (t / TC)
        e = ease(q) ** 1.3 * 0.7 + q ** 3 * 0.3
        sc = lerp(0.28, 1.25, e)
        by = lerp(hz + 26, wl + 62, e)
        cx = lerp(1020, bow_x + 420 * 1.25 + 14, e)
        ibx, iby, isc = cx, by, sc
        draw_iceberg(c, ibx, iby, isc, under=True)
    else:
        ibx = bow_x + 420 * 1.25 + 14 - 400 * (t - TC)
        iby, isc = wl + 62, 1.25
    place(c, A['night'], anchor, scr, s, ang)
    funnel_smoke(c, anchor, scr, s, ang, t, (34, 40, 54), alpha=0.5)
    if t >= TC:
        draw_iceberg(c, ibx, iby, isc, under=True)
    draw_waves(c, front, t, xoff=t * 70)
    d = ImageDraw.Draw(c)
    if t >= TC - 0.05:
        u = t - TC
        # espuma en el punto de contacto y trozos de hielo que caen sobre la cubierta de proa
        foam(c, bow_x - 40 + (-60 * u), wl + 70, 90, t, int(230 * math.exp(-u * 0.5)), 9)
        rnd = random.Random(77)
        for k in range(26):
            life = 1.6
            t0 = 0.05 + rnd.uniform(0, 0.9)
            a = u - t0
            if 0 < a < life:
                x0 = bow_x - 120 + rnd.uniform(-50, 90)
                y0 = wl - 250 + rnd.uniform(-20, 40)
                vx = rnd.uniform(-60, 40)
                x = x0 + vx * a
                y = y0 + 380 * a * a + 40 * a
                if y < wl - 62 * s + 10:
                    r = rnd.uniform(4, 11)
                    d.polygon([(x - r, y), (x, y - r), (x + r, y - r * 0.2), (x + r * 0.5, y + r)], fill=(232, 244, 252, int(255 * (1 - a / life))))
        # destello
        fl = max(0.0, 1 - u / 0.25) * 0.34
        if fl > 0:
            c.alpha_composite(Image.new('RGBA', (W, H), (255, 255, 255, int(255 * fl))))
        ip = ease(u / 0.5)
        inset = inset_contact(c, t, u)
        if ip > 0.01:
            sz = int(inset.width * (0.5 + 0.5 * ip))
            im2 = inset.resize((sz, sz), Image.LANCZOS)
            im2.putalpha(im2.getchannel('A').point(lambda v: int(v * ip)))
            _blit(c, im2, int(540 - sz / 2), int(460 - sz / 2))
            if ip > 0.9:
                text_center(c, 'COSTADO DE ESTRIBOR', 740, 34, alpha=(ip - 0.9) * 10, spacing=2, stroke=3)
    top_dark(c, 300, 110)
    chip(c, '11:40 P. M. · 14 DE ABRIL DE 1912', 140, ease((t - 2.4) / 0.5), 36)
    return c


# ------------------------------------------------------------------ ESCENA 5 (corte ilustrado)
BULK = [945, 900, 850, 795, 735, 675, 615, 555, 495, 435, 375, 315, 255, 195, 140]


def cutaway(ph, t):
    m = 2.0
    im = Image.new('RGBA', (int(SPR_W * m), int(SPR_H * m)), (0, 0, 0, 0))

    def P(x, y):
        return ((x + 40) * m, (WLY - y) * m)
    hp = [P(*p) for p in hull_poly()]
    inner = Image.new('RGBA', im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(inner)
    d.rectangle([P(0, 60)[0], P(0, 60)[1], P(1000, -40)[0], P(1000, -40)[1]], fill=(22, 32, 44, 255))
    for yy in (36, 20, 4):
        d.line([P(20, yy), P(990, yy)], fill=(48, 62, 78, 255), width=2)
    d.rectangle([P(60, -20)[0], P(60, -20)[1], P(900, -30)[0], P(900, -30)[1]], fill=(14, 20, 30, 255))
    edges = [992] + BULK + [20]
    # contenido: bodegas, calderas, máquinas
    for i in range(len(edges) - 1):
        xl, xr = edges[i + 1], edges[i]
        if 1 <= i <= 3:
            for k in range(3):
                d.rectangle([P(xl + 6 + k * (xr - xl) / 3.2, -6)[0], P(xl + 6 + k * (xr - xl) / 3.2, 8)[1], P(xl + 6 + k * (xr - xl) / 3.2 + 12, 8)[0], P(0, -6)[1]], fill=(98, 76, 54, 255))
        if 4 <= i <= 9:
            cx = (xl + xr) / 2
            d.rounded_rectangle([P(cx - 20, 14)[0], P(cx - 20, 14)[1], P(cx + 20, -14)[0], P(cx + 20, -14)[1]], radius=18, fill=(70, 78, 90, 255))
            d.ellipse([P(cx - 5, 0)[0], P(cx - 5, 0)[1] - 1, P(cx + 5, -8)[0], P(cx + 5, -8)[1]], fill=(230, 120, 40, 255))
            d.line([P(cx - 8, 14), P(cx - 8, 36)], fill=(60, 66, 76, 255), width=4)
        if 10 <= i <= 12:
            cx = (xl + xr) / 2
            d.rectangle([P(cx - 22, 28)[0], P(cx - 22, 28)[1], P(cx + 22, -14)[0], P(cx + 22, -14)[1]], fill=(86, 94, 108, 255))
            d.rectangle([P(cx - 6, 36)[0], P(cx - 6, 36)[1], P(cx + 6, 28)[0], P(cx + 6, 28)[1]], fill=(120, 128, 140, 255))
    # mamparos estancos
    for bx in BULK:
        d.line([P(bx, 38), P(bx, -30)], fill=(150, 160, 176, 255), width=4)
    # agua en compartimentos
    water = Image.new('RGBA', im.size, (0, 0, 0, 0))
    wd = ImageDraw.Draw(water)
    for i in range(len(edges) - 1):
        xl, xr = edges[i + 1], edges[i]
        if i < 5:
            a = ease((ph - 0.03 - 0.1 * i) / 0.3) * (0.97 if i < 4 else 0.9)
        elif i < 8:
            a = 0.55 * ease((ph - 0.52 - 0.1 * (i - 5)) / 0.4)
        else:
            a = 0.0
        if a <= 0.001:
            continue
        top = -28 + a * 68
        pts = [P(xl, -30), P(xr, -30)]
        for k in range(0, 21):
            x = xr - (xr - xl) * k / 20
            pts.append(P(x, top + 1.6 * math.sin(t * 3 + x * 0.35) * (0.4 + 0.6 * a)))
        wd.polygon(pts, fill=(48, 138, 214, 205))
        wd.line(pts[2:], fill=(200, 235, 255, 255), width=3)
        for k in range(5):
            bxp = xl + 6 + ((k * 37 + i * 11) % max(8, int(xr - xl - 10)))
            by = -28 + ((t * 18 + k * 13 + i * 7) % max(4, (top + 28)))
            wd.ellipse([P(bxp - 1.5, by)[0], P(bxp - 1.5, by)[1], P(bxp + 1.5, by - 3)[0], P(bxp + 1.5, by - 3)[1]], outline=(220, 245, 255, 220), width=2)
    inner = Image.alpha_composite(inner, water)
    # recorte con el casco + contorno
    mask = Image.new('L', im.size, 0)
    ImageDraw.Draw(mask).polygon(hp, fill=255)
    inner.putalpha(ImageChops.multiply(inner.getchannel('A'), mask))
    out = Image.alpha_composite(im, inner)
    ImageDraw.Draw(out).line(hp + [hp[0]], fill=(180, 190, 206, 255), width=5)
    return out


def scene5(t):
    A = assets()
    c = canvas()
    hz = 940
    sky_ocean(c, hz, NIGHT_SKY, NIGHT_SEA)
    stars_scene(c, t, hz)
    ph = clamp01(t / 8.0)
    e = ease(ph)
    s = lerp(1.0, 1.3, e)
    ux = lerp(540, 690, e)
    sx = 540
    wl = lerp(1100, 1130, e)
    ang = 2.6 * ease(ph * 1.2)
    dy, _ = bob(t, 1.2 * s)
    anchor = (ux, 0)
    scr = (sx, wl + dy)
    layers = sea_layers(hz, wl, amp=1.8, c0=(22, 42, 72), c1=(12, 26, 50), crest=lambda f: (90, 125, 175, 100) if f < 0.85 else None, spd=0.6)
    back, front = split_layers(layers, wl)
    d = ImageDraw.Draw(c)
    for k in range(40):
        d.rectangle([0, hz - k * 3, W, hz - k * 3 + 3], fill=(70, 100, 150, int(30 * (1 - k / 40))))
    draw_waves(c, back, t, xoff=t * 50)
    place(c, A['night'], anchor, scr, s, ang)
    cw = cutaway(ph, t)
    place(c, {2.0: cw}, anchor, scr, s, ang)
    funnel_smoke(c, anchor, scr, s, ang, t, (34, 40, 54), alpha=0.45)
    # agua exterior semitransparente por delante
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    draw_waves(ov, front, t, xoff=t * 50)
    a = ov.getchannel('A').point(lambda v: int(v * 0.30))
    ov.putalpha(a)
    c.alpha_composite(ov)
    top_dark(c, 300, 110)
    chip(c, '5 DE 16 COMPARTIMENTOS ESTANCOS INUNDADOS', 140, ease((t - 0.2) / 0.6), 32)
    # etiquetas del corte
    text_center(c, 'CORTE ILUSTRADO DEL CASCO', 1215, 30, alpha=0.9 * ease(t / 0.8), spacing=3, stroke=2)
    return c


# ------------------------------------------------------------------ ESCENA 6
def rocket(c, t, t0, x0, y0, x1, y1):
    d = ImageDraw.Draw(c)
    u = t - t0
    if u < 0 or u > 2.6:
        return
    if u < 1.0:
        q = ease(u / 1.0)
        x, y = lerp(x0, x1, q), lerp(y0, y1, q)
        for k in range(14):
            qq = max(0, q - k * 0.02)
            xx, yy = lerp(x0, x1, qq), lerp(y0, y1, qq)
            d.ellipse([xx - 4 + k * 0.3, yy - 4, xx + 4 - k * 0.3, yy + 4], fill=(255, 230, 170, int(220 * (1 - k / 14))))
    else:
        b = u - 1.0
        for k in range(26):
            ang = k / 26 * 6.283
            r = 130 * (1 - math.exp(-b * 2.2))
            x = x1 + math.cos(ang) * r
            y = y1 + math.sin(ang) * r + 60 * b * b
            al = int(255 * max(0, 1 - b / 1.6))
            d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=(255, 250, 230, al))
            d.line([x1 + math.cos(ang) * r * 0.7, y1 + math.sin(ang) * r * 0.7 + 40 * b * b, x, y], fill=(255, 235, 190, al // 2), width=2)
    return


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
    wob = 1.5 * math.sin(t * 0.9)
    scr = (540 + lerp(30, -20, ph), 880 + wob)
    wl_here = to_screen(anchor, scr, s, ang, (565, 0))[1]
    layers = sea_layers(hz, wl_here + 20, amp=2.4, c0=(20, 40, 70), c1=(10, 22, 44), crest=lambda f: (70, 100, 140, 110) if f < 0.5 else None, spd=0.7)
    back, front = split_layers(layers, wl_here)
    draw_waves(c, back, t, xoff=t * 30)
    place(c, A['night6'], anchor, scr, s, ang)
    d = ImageDraw.Draw(c)
    # personas en la cubierta de botes (siluetas anónimas, sin acciones concretas)
    rnd = random.Random(8)
    cols = [(10, 10, 14), (26, 20, 18), (16, 18, 26), (34, 28, 24)]
    for k in range(17):
        ux = 330 + k * 24 + rnd.uniform(-6, 6)
        x, y = to_screen(anchor, scr, s, ang, (ux, 103 + (k % 3)))
        person(d, x, y, 15 * s, col=cols[k % 4], hat=(k % 3 == 0))
    # botes dinámicos
    slots = [(8, 0.0, 0, 7), (9, 0.0, 0, 8), (10, 1.6, 7, 9), (11, 0.0, 0, 6), (12, 3.3, 5, 10), (13, 0.0, 0, 8)]
    for si, tl, tlow, npeople in [(a_, b_, c_, d_) for a_, b_, c_, d_ in slots]:
        ux = 212 + 33 * si + 14
        start = to_screen(anchor, scr, s, ang, (ux, 105))
        low_t0 = tl
        if tl > 0:
            q = ease((t - low_t0) / 4.6)
        else:
            q = 0.0
        water_y = to_screen(anchor, scr, s, ang, (ux + 40, 0))[1] + 6
        cy = lerp(start[1], water_y, q)
        cx = start[0] + 18 * q * (1 if si == 10 else 0.6) + 3 * math.sin(t * 1.3 + si) * (1 - q)
        n_p = npeople if (tl == 0 or t > tl - 0.6) else 0
        n_show = int(n_p * min(1.0, max(0.0, (t - (tl - 1.2)) / 0.8))) if tl > 0 else n_p
        size = 28 * s * 1.5
        # pescantes y cuerdas
        top1 = to_screen(anchor, scr, s, ang, (ux - 10, 128))
        top2 = to_screen(anchor, scr, s, ang, (ux + 10, 128))
        d = ImageDraw.Draw(c)
        d.line([top1[0], top1[1], top1[0] + 8, start[1] - 100 * 0], fill=(14, 14, 18, 255), width=5)
        d.line([top2[0], top2[1], top2[0] - 8, start[1] - 100 * 0], fill=(14, 14, 18, 255), width=5)
        d.line([top1[0], top1[1], cx - size * 0.42, cy - size * 0.22], fill=(150, 140, 120, 230), width=2)
        d.line([top2[0], top2[1], cx + size * 0.42, cy - size * 0.22], fill=(150, 140, 120, 230), width=2)
        lifeboat(c, cx, cy + size * 0.12, size, ang=ang * 0.4 * (1 - q), n_people=max(0, n_show), t=t, seed=si)
    # cohetes de socorro
    rocket(c, t, 1.0, 960, 560, 900, 410)
    rocket(c, t, 3.6, 860, 560, 800, 380)
    rocket(c, t, 5.6, 980, 560, 930, 420)
    draw_waves(c, front, t, xoff=t * 30)
    # gráfico: capacidad de botes vs. personas a bordo
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


# ------------------------------------------------------------------ ESCENA 7
def piece_place(c, pieces, key, anchor, screen, s, ang, alpha=1.0):
    place(c, pieces[key], anchor, screen, s, ang, alpha)


def scene7(t):
    A = assets()
    c = canvas()
    hz = 880
    sky_ocean(c, hz, NIGHT_SKY, NIGHT_SEA)
    stars_scene(c, t, hz)
    s = 0.88
    pivot = (BREAK_X, 0)
    base = (560.0, 1110.0)
    # fases
    T_L = 1.9    # luces parpadean
    T_B0, T_B1 = 2.3, 3.0   # ruptura
    wl = base[1]
    layers = sea_layers(hz, wl, amp=2.0, c0=(20, 40, 70), c1=(10, 22, 44), crest=lambda f: (70, 100, 140, 100) if f < 0.5 else None, spd=0.7)
    back, front = split_layers(layers, wl)
    for k in range(30):
        ImageDraw.Draw(c).rectangle([0, hz - k * 3, W, hz - k * 3 + 3], fill=(70, 100, 150, int(26 * (1 - k / 30))))
    draw_waves(c, back, t, xoff=t * 25)
    shimmer(c, t, hz + 4, wl + 220, (170, 200, 245), n=150, seed=15, maxlen=70)
    # luz
    if t < T_L:
        lit = 1.0
    elif t < T_L + 0.45:
        lit = 0.5 + 0.5 * math.sin((t - T_L) * 40)
        lit = max(0.0, lit) * (1 - (t - T_L) / 0.5)
    else:
        lit = 0.0
    d = ImageDraw.Draw(c)
    if t < T_B0:
        q = ease(t / T_B0)
        ang = lerp(2.5, 17.0, q ** 0.9)
        off_y = 18 * q
        scr = (base[0], base[1] + off_y)
        place(c, A['dark'], pivot, scr, s, ang)
        if lit > 0:
            place(c, A['night'], pivot, scr, s, ang, alpha=lit)
        funnel_smoke(c, pivot, scr, s, ang, t, (34, 40, 54), alpha=0.4)
        foam(c, to_screen(pivot, scr, s, ang, (960, -10))[0], to_screen(pivot, scr, s, ang, (960, -10))[1], 70, t, 190, 4)
    else:
        u = t - T_B0
        # popa: se asienta y luego se levanta casi vertical; proa: se hunde
        qb = ease(u / 2.0)
        ang_b = lerp(17.0, 46.0, qb)
        offb = (lerp(0, 90, qb), lerp(18, 650, qb ** 1.2))
        up = clamp01((u - 0.7) / 1.9)
        settle = ease(clamp01(u / 0.7))
        ang_s = lerp(17.0, 5.0, settle) if u < 0.9 else lerp(5.0, 72.0, ease(up))
        slide = ease(clamp01((u - 2.5) / 1.5))
        offs = (lerp(0, -14, settle), lerp(18, 40, settle) + 40 * ease(up) + 800 * slide)
        sb = (base[0] + offb[0], base[1] + offb[1])
        ss = (base[0] + offs[0], base[1] + offs[1])
        # popa
        place(c, A['dark_p']['stern'], pivot, ss, s, ang_s)
        # proa
        place(c, A['dark_p']['bow'], pivot, sb, s, ang_b)
        # vapor / espuma en la ruptura
        if u < 2.4:
            d = ImageDraw.Draw(c)
            for k in range(10):
                ph = (u * 0.8 + k * 0.1) % 1.0
                r = 18 + 70 * ph
                x = base[0] + 20 + 10 * k - 70 * ph
                y = base[1] - 30 - 160 * ph + 4 * k
                d.ellipse([x - r, y - r, x + r, y + r], fill=(210, 220, 232, int(70 * (1 - ph) * (1 - u / 2.4))))
    draw_waves(c, front, t, xoff=t * 25)
    # espuma / remolino alrededor de la zona del hundimiento
    d = ImageDraw.Draw(c)
    if t > T_B0:
        u = t - T_B0
        for k in range(5):
            rr = 80 + 55 * k + u * 30
            d.ellipse([base[0] - rr - 40, base[1] - rr * 0.07 + 8, base[0] + rr + 40, base[1] + rr * 0.07 + 18], outline=(220, 238, 250, int(120 * max(0, 1 - (k * 0.18 + u * 0.1)))), width=3)
    # restos flotantes tras el hundimiento
    if t > 4.6:
        k = ease((t - 4.6) / 1.4)
        rnd = random.Random(4)
        for i in range(26):
            x = base[0] + rnd.gauss(-20, 220)
            y = base[1] + 22 + rnd.uniform(0, 90) + 3 * math.sin(t * 1.5 + i)
            w = rnd.uniform(10, 36)
            d.line([x - w, y, x + w, y + rnd.uniform(-3, 3)], fill=(78, 60, 44, int(255 * k)), width=3)
    top_dark(c, 300, 110)
    chip(c, '2:20 A. M. · 15 DE ABRIL DE 1912', 140, ease((t - 3.0) / 0.6) if t > 3 else 0, 36)
    return c


# ------------------------------------------------------------------ ESCENA 8
DAWN_SKY = [(0, (16, 26, 58)), (0.55, (78, 76, 118)), (0.88, (232, 138, 96)), (1, (255, 202, 134))]
DAWN_SEA = [(0, (214, 150, 108)), (0.12, (92, 88, 120)), (0.4, (22, 36, 66)), (1, (4, 10, 24))]


def scene8a(t):
    A = assets()
    c = canvas()
    hz = 900
    sky_ocean(c, hz, DAWN_SKY, DAWN_SEA)
    draw_stars(c, t, hz, 0.35)
    d = ImageDraw.Draw(c)
    # resplandor del amanecer
    glow = Image.new('RGBA', (W, 500), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for k in range(30):
        r = 60 + k * 22
        gd.ellipse([300 - r, 480 - r * 0.45, 300 + r, 480 + r * 0.45], fill=(255, 190, 120, 9))
    c.alpha_composite(glow, (0, hz - 480))
    # icebergs lejanos
    for (x, sc_) in ((820, 0.26), (180, 0.2), (560, 0.14)):
        draw_iceberg(c, x, hz + 5, sc_, alpha=0.85, under=False)
    wl_far = 1050
    layers = sea_layers(hz, 1200, amp=3.0, c0=(120, 100, 130), c1=(6, 14, 30), crest=lambda f: (255, 200, 150, 110) if f < 0.45 else None, spd=0.7)
    draw_waves(c, [L for L in layers if L['y'] < 1150], t, xoff=t * 20)
    shimmer(c, t, hz + 4, 1100, (255, 210, 150), n=100, seed=22, xc=300, spread=170, maxlen=90)
    # Carpathia llegando
    q = ease(t / 4.4)
    cs = 1.15
    csx = lerp(-330, 330, q)
    cwl = 1035
    ca = (475, 0)
    place(c, A['carp'], ca, (csx, cwl + 2 * math.sin(t * 1.2)), cs, 0.3 * math.sin(t))
    for fxs in [(470, 152)]:
        o = to_screen(ca, (csx, cwl), cs, 0, fxs)
        smoke(c, o, t, (46, 48, 58), scale=0.9, wind=(-1.1, -0.1), rate=9, life=5.0, seed=3, alpha=0.5)
    # botes salvavidas (siluetas ilustradas)
    boats = [(660, 1140, 150, 12, 1), (880, 1100, 118, 10, 2), (480, 1190, 140, 11, 3), (170, 1160, 120, 9, 4),
             (950, 1190, 160, 14, 5), (790, 1050, 80, 7, 6), (330, 1105, 84, 8, 7)]
    for bx, by, bs_, npx, sd in sorted(boats, key=lambda b: b[1]):
        lifeboat(c, bx + 6 * math.sin(t * 0.7 + sd), by + 4 * math.sin(t * 1.1 + sd * 2), bs_, ang=3 * math.sin(t * 0.9 + sd), n_people=npx, t=t, seed=sd, oars=(sd % 2 == 0))
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    draw_waves(ov, [L for L in layers if L['y'] >= 1150], t, xoff=t * 20)
    c.alpha_composite(ov)
    # témpanos pequeños
    d = ImageDraw.Draw(c)
    for k, (fx, fy, r) in enumerate(((100, 1050, 38), (740, 1230, 52), (990, 1020, 30), (440, 1020, 26))):
        floe(d, fx, fy, r, t, k)
    top_dark(c, 300, 60)
    return c


def sunk_scene(t):
    """Imagen ilustrada del Titanic hundido en el fondo del Atlántico."""
    A = assets()
    c = canvas()
    arr = vgrad(H, [(0, (4, 36, 62)), (0.35, (2, 24, 46)), (0.75, (2, 14, 30)), (1, (2, 8, 16))])
    c.paste(Image.fromarray(arr, 'RGB'), (0, 0))
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    for k in range(9):
        x0 = 120 + k * 120 + 40 * math.sin(t * 0.5 + k)
        od.polygon([(x0, 0), (x0 + 90, 0), (x0 + 260 + 60 * math.sin(t * 0.4 + k), 1200), (x0 + 60, 1200)], fill=(120, 190, 220, 14))
    c.alpha_composite(ov)
    # popa lejana (la ruptura dejó dos secciones separadas)
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    place(lay, A['wreck_p']['stern'], (300, 0), (170, 1110), 0.62, 16, 1.0)
    place(lay, A['wreck_p']['bow'], (780, 0), (590, 1075), 1.32, -3, 1.0)
    la = np.array(lay).astype(np.float32)
    al = la[..., 3:4] / 255.0
    rng = np.random.RandomState(3)
    noise = rng.rand(H // 40, W // 40).astype(np.float32)
    noise = np.array(Image.fromarray((noise * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)).astype(np.float32) / 255.0
    rust = np.clip((noise - 0.52) * 1.2, 0, 1)[..., None]
    la[..., :3] = la[..., :3] * np.array([0.38, 0.55, 0.62]) + rust * np.array([70, 36, 14]) * al
    la[..., 3:4] = al * 255
    wreck = Image.fromarray(np.clip(la, 0, 255).astype(np.uint8), 'RGBA')
    c.alpha_composite(wreck)
    # lecho marino
    d = ImageDraw.Draw(c)
    pts = [(0, 1120)] + [(x, 1108 + 14 * math.sin(x * 0.01) + 8 * math.sin(x * 0.037 + 1)) for x in range(0, W + 40, 40)] + [(W, H), (0, H)]
    pts = [(0, 1150)] + [(x, 1115 + 16 * math.sin(x * 0.009 + 0.5) + 7 * math.sin(x * 0.04)) for x in range(0, W + 40, 40)] + [(W, H), (0, H)]
    d.polygon(pts, fill=(14, 22, 26, 255))
    d.polygon([(0, 1190)] + [(x, 1170 + 10 * math.sin(x * 0.013 + 2)) for x in range(0, W + 40, 40)] + [(W, H), (0, H)], fill=(8, 14, 18, 255))
    # niebla de profundidad
    fog = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fog)
    for k in range(60):
        fd.rectangle([0, 820 + k * 7, W, 820 + k * 7 + 7], fill=(10, 50, 80, int(40 * math.sin(k / 60 * math.pi))))
    c.alpha_composite(fog)
    # nieve marina
    rnd = random.Random(17)
    d = ImageDraw.Draw(c)
    for k in range(160):
        x = (rnd.uniform(0, W) + 12 * math.sin(t * 0.6 + k)) % W
        y = (rnd.uniform(0, H) - t * rnd.uniform(8, 26)) % H
        r = rnd.uniform(0.8, 2.4)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(190, 220, 235, int(rnd.uniform(40, 130))))
    return c


def scene8(t):
    # t: 0..9 (T=51..60)
    a = scene8a(min(t, 5.2))
    if t < 5.2 and t < 4.0:
        return a
    s = sunk_scene(t)
    k = ease((t - 4.0) / 1.0)
    if k < 1:
        out = Image.blend(a, s, k)
    else:
        out = s
    # textos finales
    d = ImageDraw.Draw(out)
    f1 = ease((t - 5.1) / 0.5)
    if f1 > 0:
        top = Image.new('RGBA', (W, 640), (0, 0, 0, 0))
        arr = np.zeros((640, W, 4), np.uint8)
        arr[..., 3] = (np.linspace(1, 0, 640) ** 1.3 * 140).astype(np.uint8)[:, None]
        out.alpha_composite(Image.fromarray(arr, 'RGBA'), (0, 0)) if False else None
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

# ------------------------------------------------------------------ SUBTÍTULOS (tiempos absolutos)
SUBS = [
    (5.35, 11.8, 'El [[10 de abril de 1912]], el Titanic inició su viaje inaugural rumbo a Nueva York con [[más de 2.200 personas]] a bordo.'),
    (12.3, 15.8, 'La noche del [[14 de abril]], el Titanic navegaba por aguas del Atlántico Norte.'),
    (15.8, 18.8, 'Durante el viaje se habían recibido [[advertencias sobre hielo]].'),
    (19.3, 23.0, 'A las [[11:40 de la noche]], el Titanic chocó contra un [[iceberg]].'),
    (23.0, 26.8, 'El casco sufrió daños que permitieron la [[entrada de agua]].'),
    (27.3, 30.8, 'El agua comenzó a [[inundar]] varios compartimentos.'),
    (30.8, 34.6, 'El barco [[no podía mantenerse a flote]].'),
    (35.3, 42.6, 'Los pasajeros comenzaron a evacuar el barco, pero los botes salvavidas [[no tenían capacidad suficiente]] para todos.'),
    (43.3, 47.0, 'A las [[2:20 de la madrugada]] del 15 de abril, el Titanic desapareció bajo las aguas.'),
    (47.0, 50.8, '[[Más de 1.500 personas]] perdieron la vida.'),
    (51.2, 53.4, 'El RMS [[Carpathia]] rescató a los supervivientes.'),
    (53.4, 55.8, 'La tragedia cambió para siempre las normas de [[seguridad marítima]].'),
]
SUB_Y = 1270


def overlay_subs(c, T):
    for t0, t1, txt in SUBS:
        if t0 - 0.01 <= T <= t1 + 0.01:
            a = min(ease((T - t0) / 0.25), 1 - ease((T - (t1 - 0.2)) / 0.2))
            lay = subtitle_layer(txt)
            blit_alpha(c, lay, (0, SUB_Y), a)


def render_frame(i):
    T = i / FPS
    # escena activa
    si = 0
    for k in range(8):
        if BOUNDS[k] <= T < BOUNDS[k + 1]:
            si = k
    XF = 0.25
    out = None
    for k in range(8):
        pass
    # transición con disolvencia centrada en la frontera
    nxt = si + 1
    prv = si - 1
    c = None
    if nxt < 8 and T > BOUNDS[nxt] - XF:
        a = ease((T - (BOUNDS[nxt] - XF)) / (2 * XF))
        c0 = SCENES[si](T - BOUNDS[si])
        c1 = SCENES[nxt](T - BOUNDS[nxt])
        c = Image.blend(c0, c1, a)
    elif prv >= 0 and T < BOUNDS[si] + XF:
        a = ease((T - (BOUNDS[si] - XF)) / (2 * XF))
        c0 = SCENES[prv](T - BOUNDS[prv])
        c1 = SCENES[si](T - BOUNDS[si])
        c = Image.blend(c0, c1, a)
    else:
        c = SCENES[si](T - BOUNDS[si])
    if si == 7 and T - 51 > 5.0:
        pass
    overlay_subs(c, T)
    arr = np.asarray(c.convert('RGB')).astype(np.float32)
    arr = vignette(arr, 0.5)
    rng = np.random.RandomState(i)
    arr += rng.randn(H // 2, W // 2, 1).repeat(2, 0).repeat(2, 1) * 2.2
    if T < 0.5:
        arr *= ease(T / 0.5)
    return np.clip(arr, 0, 255).astype(np.uint8)
