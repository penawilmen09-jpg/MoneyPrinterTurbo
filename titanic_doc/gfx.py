# -*- coding: utf-8 -*-
"""Motor gráfico 2D (PIL + numpy). Todo se dibuja con primitivas vectoriales;
no hay fotografías, ni modelos 3D, ni imágenes estáticas."""
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

W, H = 1080, 1920

# --- Lienzos RGB con dibujo que mezcla alfa (los trazos translúcidos se funden correctamente)
_orig_draw = ImageDraw.Draw
_orig_ac = Image.Image.alpha_composite


def _draw(im, mode=None):
    if mode is None and im.mode == 'RGB':
        mode = 'RGBA'
    return _orig_draw(im, mode)


def _ac(self, im, dest=(0, 0), source=(0, 0)):
    if self.mode == 'RGBA':
        return _orig_ac(self, im, dest, source)
    self.paste(im.convert('RGB'), dest, im.getchannel('A'))


ImageDraw.Draw = _draw
Image.Image.alpha_composite = _ac
FD = '/usr/share/fonts/truetype/liberation/'
_fc = {}


def font(name, size):
    k = (name, size)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(FD + name, size)
    return _fc[k]


def ease(x):
    x = min(1, max(0, x))
    return x * x * (3 - 2 * x)


def clamp01(x):
    return min(1.0, max(0.0, x))


def lerp(a, b, t):
    return a + (b - a) * t


def lerpc(c1, c2, t):
    return tuple(int(lerp(a, b, t)) for a, b in zip(c1, c2))


# ---------------------------------------------------------------- SPRITES
# Sistema de unidades del barco: x 0..1000 (proa a la derecha), y hacia arriba
# desde la línea de flotación. Origen del sprite: x+40, WLY - y.
WLY = 262
SPR_W, SPR_H = 1080, 300
MASTER = 4.0
LEVELS = [4.0, 2.0, 1.0, 0.5, 0.25]
FUNNELS = [290, 400, 510, 620]
BREAK_X = 565


def hull_poly():
    return [(20, 52), (36, 4), (70, -30), (860, -30), (935, -6), (978, 34), (992, 64),
            (900, 53), (500, 49), (20, 52)]


def build_liner(lit=True, day=False, boats_skip=()):
    """Dibuja el Titanic completo (2D vectorial, 4x). Casco negro, superestructura blanca,
    cuatro chimeneas ocre con parte superior negra."""
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

    if day:
        WHITE, SHADE, HULL = (238, 236, 228), (206, 204, 196), (22, 22, 26)
        OCHRE, OCHRE2 = (218, 164, 66), (190, 138, 48)
        WIN, DECK = (52, 66, 82), (150, 120, 84)
        RAIL = (120, 120, 120)
    else:
        WHITE, SHADE, HULL = (156, 166, 186), (118, 128, 150), (10, 12, 18)
        OCHRE, OCHRE2 = (150, 112, 52), (120, 88, 40)
        WIN, DECK = (30, 36, 50), (70, 62, 52)
        RAIL = (90, 96, 112)
    LIGHT = (255, 214, 120)
    glow_mask = Image.new('L', im.size, 0)
    gd = ImageDraw.Draw(glow_mask)

    # casco
    poly(hull_poly(), HULL)
    # franja roja de la obra viva (visible cuando el barco se levanta)
    hm = Image.new('L', im.size, 0)
    ImageDraw.Draw(hm).polygon([P(*p) for p in hull_poly()], fill=255)
    red = Image.new('RGBA', im.size, (118, 28, 26, 255))
    cut = Image.new('L', im.size, 0)
    ImageDraw.Draw(cut).rectangle([P(0, -6)[0], P(0, -6)[1], P(1000, -6)[0], im.size[1]], fill=255)
    im.paste(red, (0, 0), ImageChops.multiply(hm, cut))
    d = ImageDraw.Draw(im)
    line([(26, 47), (500, 45), (900, 50), (985, 60)], (225, 225, 220) if day else (120, 126, 140), 0.9)
    # portillos
    for x in np.arange(60, 945, 13.5):
        r = 2.0
        c = (LIGHT if lit else WIN)
        cx, cy = P(x, 33)
        d.ellipse([cx - r * m, cy - r * m, cx + r * m, cy + r * m], fill=c)
        if lit:
            gd.ellipse([cx - 2.6 * m, cy - 2.6 * m, cx + 2.6 * m, cy + 2.6 * m], fill=170)
    for x in np.arange(240, 860, 17):
        r = 1.8
        cx, cy = P(x, 19)
        d.ellipse([cx - r * m, cy - r * m, cx + r * m, cy + r * m], fill=(LIGHT if lit else WIN))
        if lit:
            gd.ellipse([cx - 2.4 * m, cy - 2.4 * m, cx + 2.4 * m, cy + 2.4 * m], fill=140)

    # cubierta de proa, castillo, popa
    rect(880, 50, 988, 62, SHADE)
    rect(40, 50, 160, 60, SHADE)
    line([(40, 66), (160, 66)], RAIL, 0.6)
    line([(880, 68), (985, 70)], RAIL, 0.6)
    # grúas de carga y escotillas
    for x in (800, 862):
        rect(x, 52, x + 3, 80, (60, 60, 64))
    line([(802, 80), (860, 62)], (60, 60, 64), 0.8)
    # superestructura
    rect(150, 50, 838, 80, WHITE)            # cubierta B/A
    rect(175, 80, 822, 102, WHITE)           # cubierta de paseo
    rect(150, 79, 838, 81, SHADE)
    rect(175, 101, 822, 103, SHADE)
    rect(200, 102, 800, 112, SHADE)          # cubierta de botes
    rect(262, 112, 672, 128, WHITE)          # casetas bajo chimeneas
    rect(790, 102, 852, 126, WHITE)          # puente
    rect(802, 126, 838, 136, SHADE)
    line([(200, 114), (800, 114)], RAIL, 0.5)
    # botes salvavidas colgando de pescantes
    for bi, x in enumerate(np.arange(212, 790, 33.0)):
        if bi in boats_skip:
            continue
        d.pieslice([P(x, 112)[0], P(x, 118)[1], P(x + 28, 104)[0], P(x + 28, 104)[1]], 180, 360,
                   fill=(235, 232, 224) if day else (150, 150, 160))
        rect(x, 110, x + 28, 114, (180, 120, 60) if day else (110, 80, 50))
    # ventanas
    for x in np.arange(160, 828, 11.0):
        c = LIGHT if lit else WIN
        rect(x, 62, x + 6, 70, c)
        if lit:
            gd.rectangle([P(x - 2, 72)[0], P(x - 2, 72)[1], P(x + 8, 60)[0], P(x + 8, 60)[1]], fill=190)
    for x in np.arange(300, 520, 14.0):  # salón comedor, ventanas altas
        c = LIGHT if lit else WIN
        rect(x, 66, x + 8, 78, c)
    for x in np.arange(186, 812, 11.0):
        c = LIGHT if lit else WIN
        rect(x, 88, x + 6, 96, c)
        if lit:
            gd.rectangle([P(x - 2, 98)[0], P(x - 2, 98)[1], P(x + 8, 86)[0], P(x + 8, 86)[1]], fill=170)
    for x in np.arange(272, 664, 12.0):
        c = LIGHT if lit else WIN
        rect(x, 118, x + 5, 124, c)
    for x in np.arange(796, 848, 9.0):
        c = LIGHT if lit else WIN
        rect(x, 112, x + 5, 120, c)
        rect(x, 128, x + 5, 134, c)
    # palos y aparejo
    for mx, top, base in ((862, 196, 62), (138, 172, 60)):
        poly([(mx - 2.2, base), (mx + 2.2, base), (mx + 1.2, top), (mx - 1.2, top)], (54, 50, 46) if day else (60, 64, 76))
    d.ellipse([*P(856, 146), *P(868, 138)], fill=(38, 34, 30) if day else (22, 24, 30))  # nido de cuervo
    rect(855, 139, 869, 147, (38, 34, 30) if day else (22, 24, 30))
    line([(862, 196), (992, 66)], (50, 50, 52) if day else (70, 76, 90), 0.35)
    line([(862, 196), (800, 126)], (50, 50, 52) if day else (70, 76, 90), 0.35)
    line([(862, 196), (138, 172)], (50, 50, 52) if day else (70, 76, 90), 0.3)  # antena inalámbrica
    line([(138, 172), (30, 58)], (50, 50, 52) if day else (70, 76, 90), 0.35)
    line([(138, 172), (300, 126)], (50, 50, 52) if day else (70, 76, 90), 0.35)
    # chimeneas: ocre con parte superior negra, inclinadas hacia popa
    for i, fx in enumerate(FUNNELS):
        base_y, top_y = 126, 192
        lean = 9
        wb, wt = 56, 50
        pts = [(fx - wb / 2, base_y), (fx + wb / 2, base_y), (fx + wt / 2 - lean, top_y), (fx - wt / 2 - lean, top_y)]
        poly(pts, OCHRE)
        # sombreado lateral
        poly([(fx + wb / 2 - 12, base_y), (fx + wb / 2, base_y), (fx + wt / 2 - lean, top_y), (fx + wt / 2 - 11 - lean, top_y)], OCHRE2)
        # parte superior negra
        tb = 170
        k = (tb - base_y) / (top_y - base_y)
        xl = lerp(fx - wb / 2, fx - wt / 2 - lean, k)
        xr = lerp(fx + wb / 2, fx + wt / 2 - lean, k)
        poly([(xl, tb), (xr, tb), (fx + wt / 2 - lean, top_y), (fx - wt / 2 - lean, top_y)], (14, 14, 16))
        d.ellipse([*P(fx - wt / 2 - lean, top_y + 3), *P(fx + wt / 2 - lean, top_y - 3)], fill=(30, 30, 32))
        # tubos de vapor
        line([(fx + 4 - 4, base_y), (fx + 4 - 6, 150)], (200, 200, 196) if day else (110, 112, 120), 0.8)
    # barandillas finas
    line([(160, 82), (832, 82)], RAIL, 0.4)

    # halo de luz (se coloca bajo el barco)
    if lit:
        gm = glow_mask.filter(ImageFilter.GaussianBlur(11 * m / 2))
        glow = Image.new('RGBA', im.size, (255, 188, 84, 0))
        glow.putalpha(gm.point(lambda v: int(v * 0.85)))
        base = Image.new('RGBA', im.size, (0, 0, 0, 0))
        base = Image.alpha_composite(base, glow)
        im = Image.alpha_composite(base, im)
    return im


def pyramid(master, levels=None):
    out = {}
    for L in (levels or LEVELS):
        if L == MASTER:
            out[L] = master
        else:
            sz = (int(master.width * L / MASTER), int(master.height * L / MASTER))
            out[L] = master.resize(sz, Image.LANCZOS)
    return out


def split_pieces(pyr):
    """Corta el barco en proa y popa con borde irregular (ruptura)."""
    res = {}
    zig = [(BREAK_X + dx, y) for y, dx in zip(
        [-40, -26, -14, 0, 14, 28, 42, 56, 70, 88, 110, 140, 170, 210, 260],
        [0, 6, -4, 5, -6, 4, -5, 6, -3, 5, -6, 3, -4, 5, 0])]
    for L, im in pyr.items():
        def P(x, y):
            return ((x + 40) * L, (WLY - y) * L)
        mb = Image.new('L', im.size, 0)
        pts = [P(*p) for p in zig] + [P(1100, 260), P(1100, -40)]
        ImageDraw.Draw(mb).polygon(pts, fill=255)
        ms = Image.new('L', im.size, 0)
        pts = [P(*p) for p in zig] + [P(-100, 260), P(-100, -40)]
        ImageDraw.Draw(ms).polygon(pts, fill=255)
        bow = im.copy(); bow.putalpha(ImageChops.multiply(im.getchannel('A'), mb))
        stern = im.copy(); stern.putalpha(ImageChops.multiply(im.getchannel('A'), ms))
        res[L] = (bow, stern)
    return {'bow': {L: res[L][0] for L in res}, 'stern': {L: res[L][1] for L in res}}


def place(canvas, pyr, anchor, screen, scale, angle=0.0, alpha=1.0, flip=False):
    """Coloca un sprite con anclaje (ux, y_up) en la pantalla, con escala (px/unidad) y rotación (grados,
    sentido horario). Usa una transformación afín directa (una sola pasada, sin zonas vacías)."""
    # nivel de la pirámide: el menor >= escala (o el mayor)
    keys = sorted(pyr)
    lv = [k for k in keys if k >= scale]
    L = min(lv) if lv else max(keys)
    im = pyr[L]
    Ax, Ay = anchor[0], WLY - anchor[1]
    Sx, Sy = screen
    th = math.radians(angle)
    c, s = math.cos(th), math.sin(th)
    # esquinas -> caja de salida
    corners = [(-40, 0), (1040, 0), (1040, SPR_H), (-40, SPR_H)]
    xs, ys = [], []
    for ux, uy in corners:
        dx, dy = (ux - Ax) * scale, (uy - Ay) * scale
        xs.append(Sx + c * dx - s * dy)
        ys.append(Sy + s * dx + c * dy)
    x0, x1 = int(max(0, min(xs))), int(min(W, max(xs)) + 1)
    y0, y1 = int(max(0, min(ys))), int(min(H, max(ys)) + 1)
    if x1 <= x0 or y1 <= y0:
        return
    ox, oy = Sx - x0, Sy - y0
    k = L / scale
    a, b = k * c, k * s
    d_, e = -k * s, k * c
    c0 = L * (Ax + 40) - a * ox - b * oy
    f0 = L * Ay - d_ * ox - e * oy
    layer = im.transform((x1 - x0, y1 - y0), Image.AFFINE, (a, b, c0, d_, e, f0), Image.BICUBIC)
    if alpha < 1.0:
        layer.putalpha(layer.getchannel('A').point(lambda v: int(v * alpha)))
    canvas.alpha_composite(layer, (x0, y0))


def to_screen(anchor, screen, scale, angle, pt):
    """Convierte un punto del barco (x, y_up) a coordenadas de pantalla."""
    th = math.radians(angle)
    c, s = math.cos(th), math.sin(th)
    dx, dy = (pt[0] - anchor[0]) * scale, -(pt[1] - anchor[1]) * scale
    return (screen[0] + c * dx - s * dy, screen[1] + s * dx + c * dy)


# ---------------------------------------------------------------- GENÉRICOS
_cache = {}


def vgrad(h, stops, w=W):
    """Gradiente vertical (array uint8 h x w x 3) con paradas [(pos0..1, rgb)]."""
    key = ('vg', h, w, tuple((p, tuple(c)) for p, c in stops))
    if key in _cache:
        return _cache[key]
    ys = np.linspace(0, 1, h)
    out = np.zeros((h, 3))
    for ch in range(3):
        out[:, ch] = np.interp(ys, [p for p, _ in stops], [c[ch] for _, c in stops])
    arr = np.repeat(out[:, None, :], w, axis=1).astype(np.uint8)
    _cache[key] = arr
    return arr


def sky_ocean(canvas, horizon, sky_stops, sea_stops):
    arr = np.zeros((H, W, 3), np.uint8)
    arr[:horizon] = vgrad(horizon, sky_stops)
    arr[horizon:] = vgrad(H - horizon, sea_stops)
    canvas.paste(Image.fromarray(arr, 'RGB'), (0, 0))


def starfield():
    if 'stars' in _cache:
        return _cache['stars']
    rnd = random.Random(7)
    im = Image.new('RGBA', (W, 1100), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # banda tenue de la Vía Láctea
    band = Image.new('L', (W, 1100), 0)
    bd = ImageDraw.Draw(band)
    for _ in range(2600):
        t = rnd.random()
        cx = lerp(-100, W + 100, t)
        cy = lerp(900, 120, t) + rnd.gauss(0, 95)
        bd.ellipse([cx - 1, cy - 1, cx + 1, cy + 1], fill=rnd.randint(40, 120))
    band = band.filter(ImageFilter.GaussianBlur(2))
    glow = Image.new('RGBA', band.size, (150, 170, 220, 0))
    glow.putalpha(band.point(lambda v: min(90, v)))
    im = Image.alpha_composite(im, glow)
    d = ImageDraw.Draw(im)
    stars = []
    for _ in range(380):
        x, y = rnd.uniform(0, W), rnd.uniform(0, 1050)
        r = rnd.choice([0.7, 0.9, 1.1, 1.4, 1.8, 2.3])
        b = rnd.randint(150, 255)
        col = rnd.choice([(b, b, b), (b, b, 255), (255, 240, b - 30)])
        d.ellipse([x - r, y - r, x + r, y + r], fill=col + (rnd.randint(140, 255),))
        if r >= 1.8:
            stars.append((x, y, r, rnd.uniform(0, 6)))
    _cache['stars'] = (im, stars)
    return _cache['stars']


def draw_stars(canvas, t, horizon, alpha=1.0):
    im, big = starfield()
    layer = im.crop((0, 0, W, horizon))
    if alpha < 1:
        layer.putalpha(layer.getchannel('A').point(lambda v: int(v * alpha)))
    canvas.alpha_composite(layer, (0, 0))
    d = ImageDraw.Draw(canvas)
    for x, y, r, ph in big:
        if y > horizon - 10:
            continue
        tw = 0.55 + 0.45 * math.sin(t * 2.1 + ph)
        rr = r * (1.2 + 0.5 * tw)
        a = int(200 * tw * alpha)
        ov = (255, 255, 255, a)
        d.line([x - rr * 2.2, y, x + rr * 2.2, y], fill=ov, width=1)
        d.line([x, y - rr * 2.2, x, y + rr * 2.2], fill=ov, width=1)


def wave_pts(ybase, amp, wl, speed, t, phase, step=10, xoff=0.0):
    xs = np.arange(-20, W + 40, step, dtype=np.float64)
    y = (ybase + amp * np.sin(2 * math.pi * (xs + xoff) / wl + speed * t + phase)
         + 0.45 * amp * np.sin(2 * math.pi * (xs + xoff) / (wl * 0.47) + speed * 1.7 * t + phase * 2.3)
         + 0.2 * amp * np.sin(2 * math.pi * (xs + xoff) / (wl * 0.21) - speed * 2.1 * t + phase * 0.7))
    return xs, y


def draw_waves(canvas, layers, t, xoff=0.0):
    """layers: lista de dict(y, amp, wl, sp, ph, col, crest)"""
    d = ImageDraw.Draw(canvas)
    for L in layers:
        xs, y = wave_pts(L['y'], L['amp'], L['wl'], L['sp'], t, L.get('ph', 0), xoff=xoff * L.get('par', 1.0))
        pts = list(zip(xs, y)) + [(W + 40, H + 10), (-20, H + 10)]
        d.polygon(pts, fill=L['col'])
        if L.get('crest'):
            d.line(list(zip(xs, y)), fill=L['crest'], width=L.get('cw', 2), joint='curve')


def shimmer(canvas, t, y0, y1, color, n=140, seed=3, xc=None, spread=None, maxlen=70):
    """Destellos horizontales sobre el agua (reflejo de estrellas/luces)."""
    rnd = random.Random(seed)
    d = ImageDraw.Draw(canvas)
    for _ in range(n):
        yy = y0 + (y1 - y0) * rnd.random() ** 1.6
        if xc is None:
            x = rnd.uniform(0, W)
        else:
            x = xc + rnd.gauss(0, spread or 200)
        ph = rnd.uniform(0, 6.28)
        v = 0.5 + 0.5 * math.sin(t * rnd.uniform(1.5, 3.5) + ph)
        ln = rnd.uniform(8, maxlen) * (0.4 + (yy - y0) / max(1, (y1 - y0)))
        a = int(190 * v)
        if a < 25:
            continue
        d.line([x - ln / 2, yy, x + ln / 2, yy], fill=color[:3] + (a,), width=2 if yy > y0 + (y1 - y0) * 0.4 else 1)


def puff():
    if 'puff' in _cache:
        return _cache['puff']
    n = 128
    yy, xx = np.mgrid[0:n, 0:n]
    r = np.sqrt((xx - n / 2) ** 2 + (yy - n / 2) ** 2) / (n / 2)
    rnd = np.random.RandomState(5)
    noise = np.random.RandomState(2).rand(n, n)
    a = np.clip(1 - r, 0, 1) ** 1.6
    arr = np.zeros((n, n, 4), np.uint8)
    arr[..., 0:3] = 255
    arr[..., 3] = (a * 255).astype(np.uint8)
    im = Image.fromarray(arr, 'RGBA').filter(ImageFilter.GaussianBlur(2))
    _cache['puff'] = im
    return im


def smoke(canvas, origin, t, color, scale=1.0, wind=(-1.0, -0.12), rate=14, life=5.0, seed=0, alpha=0.5, spread=1.0):
    """Humo: partículas desplazándose desde la chimenea."""
    pf = puff()
    rnd = random.Random(seed)
    n = int(rate * life)
    for i in range(n):
        phase = rnd.random()
        age = ((t * 0.35 + phase) % 1.0)
        a = age * life
        sz = (22 + 90 * age ** 0.8) * scale
        x = origin[0] + wind[0] * 52 * a * scale * 1.0 + rnd.gauss(0, 4) * scale
        y = origin[1] - (28 * a * (1 - age * 0.5) + wind[1] * 60 * a) * scale * spread
        al = alpha * (1 - age) ** 1.4 * min(1, age * 9)
        if al < 0.02:
            continue
        p = pf.resize((int(sz), int(sz)), Image.BILINEAR)
        a_ch = p.getchannel('A').point(lambda v: int(v * al))
        col = Image.new('RGBA', p.size, color + (0,))
        col.putalpha(a_ch)
        xi, yi = int(x - sz / 2), int(y - sz / 2)
        if xi > W or yi > H or xi + sz < 0 or yi + sz < 0:
            continue
        canvas.alpha_composite(col, (max(0, xi), max(0, yi)), (max(0, -xi), max(0, -yi))) if False else _blit(canvas, col, xi, yi)


def _blit(canvas, layer, x, y):
    w, h = layer.size
    sx, sy = max(0, -x), max(0, -y)
    ex, ey = min(w, W - x), min(h, H - y)
    if ex <= sx or ey <= sy:
        return
    canvas.alpha_composite(layer.crop((sx, sy, ex, ey)), (x + sx, y + sy))


# ---------------------------------------------------------------- PERSONAS / BOTES
def person(d, x, y, h, col=(14, 14, 18), arm=0.0, hat=False, wave=False, t=0.0, ph=0.0):
    """Silueta humana dibujada (anónima). (x,y) = pies; h = altura en px."""
    w = h * 0.34
    head = h * 0.13
    d.ellipse([x - head, y - h, x + head, y - h + head * 2], fill=col)
    if hat:
        d.rectangle([x - head * 1.2, y - h - head * 0.15, x + head * 1.2, y - h + head * 0.2], fill=col)
    body = [(x - w * 0.55, y - h * 0.7), (x + w * 0.55, y - h * 0.7), (x + w * 0.7, y - h * 0.3), (x + w * 0.45, y), (x - w * 0.45, y), (x - w * 0.7, y - h * 0.3)]
    d.polygon(body, fill=col)
    d.rectangle([x - w * 0.5, y - h * 0.3, x + w * 0.5, y], fill=col)
    if wave:
        a = math.sin(t * 5 + ph) * 0.35
        ax, ay = x + w * 0.55, y - h * 0.68
        d.line([ax, ay, ax + math.sin(0.9 + a) * h * 0.38, ay - math.cos(0.9 + a) * h * 0.38], fill=col, width=max(2, int(h * 0.1)))


def lifeboat(canvas, cx, cy, size, ang=0.0, n_people=6, t=0.0, seed=1, lit_alpha=1.0, day=False, oars=False):
    """Bote salvavidas ilustrado, centrado en (cx,cy)=línea de flotación del bote; size=largo en px."""
    L = int(size)
    hh = int(size * 0.34 + 4 + size * 0.5)
    layer = Image.new('RGBA', (int(L * 1.5), int(L * 1.4)), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    ox, oy = layer.width / 2, layer.height * 0.7
    hull = [(ox - L / 2, oy - L * 0.16), (ox - L * 0.3, oy + L * 0.1), (ox + L * 0.3, oy + L * 0.1), (ox + L / 2, oy - L * 0.16),
            (ox + L * 0.25, oy - L * 0.1), (ox - L * 0.25, oy - L * 0.1)]
    d.polygon([(ox - L / 2, oy - L * 0.16), (ox - L * 0.3, oy + L * 0.1), (ox + L * 0.3, oy + L * 0.1), (ox + L / 2, oy - L * 0.16)],
              fill=(70, 50, 36))
    d.polygon([(ox - L / 2, oy - L * 0.16), (ox + L / 2, oy - L * 0.16), (ox + L * 0.47, oy - L * 0.10), (ox - L * 0.47, oy - L * 0.10)], fill=(225, 222, 214))
    d.line([ox - L / 2, oy - L * 0.16, ox + L / 2, oy - L * 0.16], fill=(240, 238, 230), width=max(1, L // 40))
    rnd = random.Random(seed)
    cols = [(18, 18, 22), (34, 26, 24), (22, 24, 32), (44, 36, 30), (16, 20, 26)]
    for i in range(n_people):
        px = ox - L * 0.38 + (L * 0.76) * (i + 0.5) / max(1, n_people) + rnd.uniform(-2, 2)
        person(d, px, oy - L * 0.12 + L * 0.014 * math.sin(t * 3.1 + i * 1.7), L * 0.28 * rnd.uniform(0.9, 1.05), col=rnd.choice(cols), hat=rnd.random() < 0.3)
    if oars:
        for sgn in (-1, 1):
            a = math.sin(t * 1.4 + sgn) * 0.12
            x0, y0 = ox + sgn * L * 0.1, oy - L * 0.13
            d.line([x0, y0, x0 + sgn * L * 0.55, y0 + L * 0.28 + a * L], fill=(60, 44, 30), width=max(1, L // 55))
    layer = layer.rotate(-ang, resample=Image.BICUBIC, center=(ox, oy))
    if lit_alpha < 1:
        layer.putalpha(layer.getchannel('A').point(lambda v: int(v * lit_alpha)))
    _blit(canvas, layer, int(cx - ox), int(cy - oy))


def iceberg_poly(seed=4):
    """Contorno del iceberg (coordenadas relativas, base en y=0, y hacia arriba)."""
    rnd = random.Random(seed)
    pts = [(-420, 0), (-380, 40), (-330, 62), (-300, 120), (-240, 150), (-190, 210), (-150, 190), (-90, 260), (-30, 300),
           (20, 285), (60, 340), (120, 300), (175, 255), (230, 262), (290, 195), (340, 150), (390, 70), (430, 30), (470, 0)]
    return pts


def draw_iceberg(canvas, cx, base_y, sc, alpha=1.0, under=True, t=0.0, dark=None):
    layer = Image.new('RGBA', (int(1100 * sc), int(1500 * sc)), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    ox, oy = layer.width / 2, 400 * sc
    pts = iceberg_poly()
    top = [(ox + x * sc, oy - y * sc) for x, y in pts]
    # parte sumergida (azulada)
    sub = [(ox + x * sc, oy + y * sc) for x, y in [(-420, 0), (-470, 160), (-380, 340), (-190, 520), (60, 600), (260, 480), (440, 300), (500, 120), (470, 0)]]
    if under:
        d.polygon(sub, fill=(40, 100, 150, 120))
    d.polygon(top, fill=(214, 230, 242, 255))
    # sombras (caras)
    shade = [(ox + x * sc, oy - y * sc) for x, y in [(-30, 300), (20, 285), (60, 340), (30, 200), (-10, 120), (-60, 60), (-40, 0), (-190, 0), (-150, 190), (-90, 260)]]
    d.polygon(shade, fill=(150, 176, 204, 255))
    shade2 = [(ox + x * sc, oy - y * sc) for x, y in [(120, 300), (175, 255), (230, 262), (290, 195), (340, 150), (390, 70), (430, 30), (470, 0), (200, 0), (150, 120)]]
    d.polygon(shade2, fill=(120, 150, 184, 255))
    hl = [(ox + x * sc, oy - y * sc) for x, y in [(60, 340), (120, 300), (150, 120), (90, 150), (60, 200)]]
    d.polygon(hl, fill=(246, 252, 255, 255))
    rl = [(ox + x * sc, oy - y * sc) for x, y in [(-300, 120), (-240, 150), (-190, 210), (-150, 190), (-190, 100), (-260, 70)]]
    d.polygon(rl, fill=(236, 246, 252, 255))
    layer = layer.filter(ImageFilter.GaussianBlur(0.6))
    if dark is not None:
        a_ = np.array(layer).astype(np.float32)
        a_[..., 0] *= dark[0]; a_[..., 1] *= dark[1]; a_[..., 2] *= dark[2]
        layer = Image.fromarray(np.clip(a_, 0, 255).astype(np.uint8), 'RGBA')
    if alpha < 1:
        layer.putalpha(layer.getchannel('A').point(lambda v: int(v * alpha)))
    _blit(canvas, layer, int(cx - ox), int(base_y - oy))


# ---------------------------------------------------------------- TEXTO
def wrap_words(tokens, fnt, maxw):
    """tokens: [(palabra, amarillo?)] -> líneas"""
    sp = fnt.getlength(' ')
    lines, cur, w = [], [], 0
    for wd, yel in tokens:
        ww = fnt.getlength(wd)
        add = ww if not cur else sp + ww
        if cur and w + add > maxw:
            lines.append(cur)
            cur, w = [(wd, yel)], ww
        else:
            cur.append((wd, yel))
            w += add
    if cur:
        lines.append(cur)
    return lines


def parse_markup(s):
    toks = []
    yel = False
    for part in s.replace('[[', '\x01').replace(']]', '\x02').split(' '):
        if not part:
            continue
        w = part
        start_y = '\x01' in w
        end_y = '\x02' in w
        w = w.replace('\x01', '').replace('\x02', '')
        if start_y:
            yel = True
        toks.append((w, yel))
        if end_y:
            yel = False
    return toks


_sub_cache = {}


def subtitle_layer(text, size=56, maxw=900):
    key = (text, size, maxw)
    if key in _sub_cache:
        return _sub_cache[key]
    fnt = font('LiberationSans-Bold.ttf', size)
    lines = wrap_words(parse_markup(text), fnt, maxw)
    lh = int(size * 1.28)
    bh = lh * len(lines) + 56
    layer = Image.new('RGBA', (W, bh + 4), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    bw = max(sum(fnt.getlength(w) for w, _ in ln) + fnt.getlength(' ') * (len(ln) - 1) for ln in lines) + 80
    d.rounded_rectangle([(W - bw) / 2, 0, (W + bw) / 2, bh], radius=26, fill=(4, 6, 12, 165))
    y = 28
    sp = fnt.getlength(' ')
    for ln in lines:
        tw = sum(fnt.getlength(w) for w, _ in ln) + sp * (len(ln) - 1)
        x = (W - tw) / 2
        for w, yel in ln:
            col = (255, 214, 10, 255) if yel else (255, 255, 255, 255)
            d.text((x + 2, y + 3), w, font=fnt, fill=(0, 0, 0, 200))
            d.text((x, y), w, font=fnt, fill=col)
            x += fnt.getlength(w) + sp
        y += lh
    _sub_cache[key] = layer
    return layer


def blit_alpha(canvas, layer, pos, alpha):
    if alpha <= 0:
        return
    if alpha < 1:
        layer = layer.copy()
        layer.putalpha(layer.getchannel('A').point(lambda v: int(v * alpha)))
    _blit(canvas, layer, int(pos[0]), int(pos[1]))


def text_center(canvas, txt, y, size, col=(255, 255, 255), fontname='LiberationSans-Bold.ttf', alpha=1.0, spacing=0, stroke=3, shadow=True):
    fnt = font(fontname, size)
    if spacing:
        tw = sum(fnt.getlength(ch) + spacing for ch in txt) - spacing
    else:
        tw = fnt.getlength(txt)
    layer = Image.new('RGBA', (W, int(size * 1.6)), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    x = (W - tw) / 2
    yy = size * 0.2
    if spacing:
        for ch in txt:
            if shadow:
                d.text((x + 3, yy + 4), ch, font=fnt, fill=(0, 0, 0, 190))
            d.text((x, yy), ch, font=fnt, fill=col + (255,), stroke_width=stroke if stroke else 0, stroke_fill=(0, 0, 0, 255))
            x += fnt.getlength(ch) + spacing
    else:
        if shadow:
            d.text((x + 4, yy + 5), txt, font=fnt, fill=(0, 0, 0, 190))
        d.text((x, yy), txt, font=fnt, fill=col + (255,), stroke_width=stroke if stroke else 0, stroke_fill=(0, 0, 0, 255))
    blit_alpha(canvas, layer, (0, y - size * 0.2), alpha)


def chip(canvas, txt, y, alpha=1.0, size=40, col=(255, 255, 255)):
    fnt = font('LiberationSans-Bold.ttf', size)
    tw = fnt.getlength(txt)
    layer = Image.new('RGBA', (W, size * 2 + 10), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle([(W - tw) / 2 - 30, 4, (W + tw) / 2 + 30, size * 1.6 + 4], radius=16, fill=(0, 0, 0, 140))
    d.rectangle([(W - tw) / 2 - 30, 4, (W - tw) / 2 - 24, size * 1.6 + 4], fill=(255, 214, 10, 255))
    d.text(((W - tw) / 2, 10 + size * 0.1), txt, font=fnt, fill=col + (255,))
    blit_alpha(canvas, layer, (0, y), alpha)


_vig = None


def vignette(arr, strength=0.55):
    global _vig
    if _vig is None:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.sqrt(((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H / 2) / (H * 0.68)) ** 2)
        _vig = np.clip(1 - 0.55 * np.clip(r - 0.35, 0, 1) ** 1.6, 0.35, 1)[..., None].astype(np.float32)
    v = 1 - (1 - _vig) * (strength / 0.55)
    return arr * v
