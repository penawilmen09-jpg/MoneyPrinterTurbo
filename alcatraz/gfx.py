"""Motor gráfico 2D procedural: utilidades, cámara, luz, niebla y personajes."""
import math
import functools
import numpy as np
from PIL import Image, ImageDraw, ImageChops, ImageFilter, ImageOps

W, H = 1080, 1920


# ----------------------------------------------------------------- utilidades
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def sm(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def lerp(a, b, t):
    return a + (b - a) * t


def seg(t, a, b):
    return sm((t - a) / (b - a))


def mix(c1, c2, t):
    return tuple(int(lerp(a, b, t)) for a, b in zip(c1, c2))


def mulc(c, k):
    if isinstance(k, (tuple, list)):
        return tuple(int(clamp(v * kk, 0, 255)) for v, kk in zip(c, k))
    return tuple(int(clamp(v * k, 0, 255)) for v in c)


def vgrad(w, h, stops):
    ys = np.linspace(0, 1, h)
    out = np.zeros((h, 3), np.float32)
    for c in range(3):
        out[:, c] = np.interp(ys, [s[0] for s in stops], [s[1][c] for s in stops])
    arr = np.repeat(out[:, None, :], w, 1)
    return Image.fromarray(arr.astype(np.uint8))


@functools.lru_cache(maxsize=64)
def fbm(w, h, seed, octaves=5, base=3):
    rng = np.random.RandomState(seed)
    acc = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        gw = base * 2 ** o
        gh = max(2, int(gw * h / w))
        g = rng.rand(gh, gw).astype(np.float32)
        im = Image.fromarray((g * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
        acc += np.asarray(im, np.float32) / 255 * amp
        tot += amp
        amp *= 0.55
    acc /= tot
    acc = (acc - acc.min()) / (acc.max() - acc.min() + 1e-6)
    return acc


def fbm_img(w, h, seed, octaves=5, base=3):
    return Image.fromarray((fbm(w, h, seed, octaves, base) * 255).astype(np.uint8))


class Cam:
    def __init__(s, cx=W / 2, cy=H / 2, z=1.0, rot=0.0):
        s.cx, s.cy, s.z = cx, cy, z

    def p(s, x, y):
        return ((x - s.cx) * s.z + W / 2, (y - s.cy) * s.z + H / 2)

    def pts(s, l):
        return [s.p(*q) for q in l]

    def view(s, img, ox=0.0, oy=0.0, k=1.0):
        """Recorta una trama de mundo (colocada en ox,oy; k px por unidad)."""
        hw, hh = W / 2 / s.z, H / 2 / s.z
        box = ((s.cx - hw - ox) * k, (s.cy - hh - oy) * k, (s.cx + hw - ox) * k, (s.cy + hh - oy) * k)
        iw, ih = img.size
        bx0, by0, bx1, by1 = box
        bx0, by0 = max(0.0, bx0), max(0.0, by0)
        bx1, by1 = min(float(iw), bx1), min(float(ih), by1)
        return img.resize((W, H), Image.BICUBIC, box=(bx0, by0, bx1, by1))


# ----------------------------------------------------------------- luz / niebla
@functools.lru_cache(maxsize=128)
def _glow_sprite(r):
    y, x = np.mgrid[-r:r, -r:r].astype(np.float32)
    d = np.sqrt(x * x + y * y) / r
    a = np.exp(-(d * 2.4) ** 2) * np.clip(1 - d, 0, 1) ** 0.5
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))


def add_glow(img, x, y, r, color, k=1.0):
    r = max(4, int(r // 4 * 4))
    spr = _glow_sprite(r)
    x0, y0 = int(x - r), int(y - r)
    if x0 > W or y0 > H or x0 + 2 * r < 0 or y0 + 2 * r < 0:
        return
    region = img.crop((x0, y0, x0 + 2 * r, y0 + 2 * r))
    col = Image.new("RGB", (2 * r, 2 * r), tuple(int(clamp(c * k, 0, 255)) for c in color))
    add = ImageChops.multiply(col, Image.merge("RGB", (spr, spr, spr)))
    region = ImageChops.add(region, add)
    img.paste(region, (x0, y0))


def soft_mask(polys, down=6, blur=3, size=(W, H)):
    sw, sh = size[0] // down, size[1] // down
    m = Image.new("L", (sw, sh), 0)
    d = ImageDraw.Draw(m)
    for pts, v in polys:
        d.polygon([(x / down, y / down) for x, y in pts], fill=v)
    if blur:
        m = m.filter(ImageFilter.GaussianBlur(blur))
    return m.resize(size, Image.BILINEAR)


def add_light_mask(img, mask, color, k=1.0):
    col = Image.new("RGB", img.size, tuple(int(clamp(c * k, 0, 255)) for c in color))
    black = Image.new("RGB", img.size, (0, 0, 0))
    lit = Image.composite(col, black, mask)
    return ImageChops.add(img, lit)


def beam(img, pts, color, k=1.0, down=6, blur=3):
    m = soft_mask([(pts, 255)], down, blur)
    return add_light_mask(img, m, color, k)


def paint_mask(img, mask, color, alpha=1.0):
    if alpha < 1.0:
        mask = mask.point(lambda v: int(v * alpha))
    col = Image.new("RGB", img.size, color)
    return Image.composite(col, img, mask)


@functools.lru_cache(maxsize=16)
def _fogtex(seed, w, h):
    return fbm(w, h, seed, 5, 3)


def fog(img, t, y0, y1, color, alpha, speed=20.0, seed=1, scale=1.0, cam=None):
    """Niebla a la deriva en banda vertical [y0,y1] (px de pantalla)."""
    sw, sh = W // 4, H // 4
    tw = sw + 260
    tex = _fogtex(seed, tw, sh)
    off = int((t * speed / 4) % 250)
    win = tex[:, off:off + sw]
    ys = np.arange(sh)[:, None] * 4.0
    prof = np.clip(1 - np.abs((ys - (y0 + y1) / 2) / ((y1 - y0) / 2 + 1e-6)), 0, 1)
    prof = prof * prof * (3 - 2 * prof)
    a = np.clip((win - 0.25) * 1.9, 0, 1) * prof * alpha
    m = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)
    return paint_mask(img, m, color)


@functools.lru_cache(maxsize=1)
def _grain_bank():
    rng = np.random.RandomState(7)
    return [(rng.randn(H // 2, W // 2) * 9).astype(np.float32) for _ in range(6)]


@functools.lru_cache(maxsize=1)
def _vignette():
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((x - W / 2) / (W * 0.72)) ** 2 + ((y - H / 2) / (H * 0.66)) ** 2)
    v = 1 - np.clip(d - 0.38, 0, 1) ** 1.6 * 0.95
    return v[:, :, None]


def post(img, frame, fade=1.0, tint=(1.0, 1.0, 1.0), grain=1.0):
    a = np.asarray(img, np.float32)
    a = a * _vignette() * np.array(tint, np.float32)
    g = _grain_bank()[frame % 6]
    g = np.repeat(np.repeat(g, 2, 0), 2, 1)[:H, :W, None] * grain
    a = a + g * (0.35 + 0.65 * (a.mean(axis=2, keepdims=True) / 255))
    a = a * fade
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


# ----------------------------------------------------------------- personajes
UNI_SHIRT = (92, 106, 126)
UNI_PANTS = (62, 70, 88)
SHOE = (30, 28, 30)
SKIN = (210, 164, 132)
GUARD_SHIRT = (44, 56, 84)
GUARD_PANTS = (36, 44, 64)

LOOK = {
    "frank": dict(hair=(20, 17, 17), hw=0.80, style="back", jaw=0.74, nose=1.15),
    "john": dict(hair=(30, 24, 22), hw=0.90, style="fringe", jaw=1.0, nose=1.0),
    "clar": dict(hair=(40, 31, 26), hw=0.93, style="short", jaw=0.96, nose=0.95),
    "guard": dict(hair=(48, 40, 34), hw=0.92, style="cap", jaw=1.0, nose=1.0),
}


def pose(**kw):
    p = dict(hip=(0, -50), lean=0.0, head=0.0, fF=(8, 0), fB=(-8, 0), hF=(8, -52), hB=(-8, -52),
             eye=1.0, look=0.0)
    p.update(kw)
    return p


def _ik(a, b, l1, l2, bend):
    dx, dy = b[0] - a[0], b[1] - a[1]
    dist = math.hypot(dx, dy)
    dist = min(dist, l1 + l2 - 0.02)
    dist = max(dist, abs(l1 - l2) + 0.02)
    ang = math.atan2(dy, dx)
    c = (l1 * l1 + dist * dist - l2 * l2) / (2 * l1 * dist)
    A = math.acos(clamp(c, -1, 1))
    j = ang + bend * A
    jx, jy = a[0] + l1 * math.cos(j), a[1] + l1 * math.sin(j)
    ex, ey = a[0] + dx / max(math.hypot(dx, dy), 1e-6) * dist, a[1] + dy / max(math.hypot(dx, dy), 1e-6) * dist
    return (jx, jy), (ex, ey)


def _limb(d, T, S, a, b, l1, l2, bend, w1, w2, col, endc=None):
    j, e = _ik(a, b, l1, l2, bend)
    A, J, E = T(*a), T(*j), T(*e)
    d.line([A, J], fill=col, width=int(w1 * S))
    d.line([J, E], fill=col, width=int(w2 * S))
    for q, w in ((A, w1), (J, (w1 + w2) / 2), (E, w2)):
        r = w * S / 2
        d.ellipse([q[0] - r, q[1] - r, q[0] + r, q[1] + r], fill=col)
    return e


def _ell(d, c, rx, ry, fill):
    d.ellipse([c[0] - rx, c[1] - ry, c[0] + rx, c[1] + ry], fill=fill)


def _head(d, T, S, c, who, view, eye=1.0, look=0.0):
    """Cabeza centrada en c (unidades de modelo)."""
    L = LOOK[who]
    hw, hair = L["hw"], L["hair"]
    skin, skin_d = SKIN, mulc(SKIN, 0.78)
    cx, cy = c
    P = lambda dx, dy: T(cx + dx, cy + dy)
    def E(dx, dy, rx, ry, col):
        q = P(dx, dy)
        _ell(d, q, rx * S, ry * S, col)
    style = L["style"]
    if view == "side":
        rx, ry = 8.2 * hw, 10.4
        # pelo (detrás y arriba)
        E(-1.4, -1.4, rx + 0.9, ry + 1.0, hair)
        # nuca / cuello cae al fondo (ya dibujado por torso)
        # cara
        E(0.9, 1.4, rx - 0.2, ry - 0.6, skin)
        # mandíbula
        jw = L["jaw"]
        pts = [P(-3, 5), P(rx * 0.95, 4.5), P(rx * 0.78 + 1.0 * jw, 9.2), P(rx * 0.3, 11.2 * (0.9 + 0.1 * jw)), P(-4.5, 8.2)]
        d.polygon(pts, fill=skin)
        # nariz
        n = L["nose"]
        d.polygon([P(rx - 0.6, -0.8), P(rx + 3.4 * n, 3.4), P(rx - 0.8, 4.2)], fill=skin)
        # oreja
        E(-1.2, 1.5, 2.1, 3.1, skin_d)
        # pelo frontal
        if style == "back":
            d.polygon([P(-8, -4), P(-2, -11.6), P(5, -11.4), P(rx - 0.8, -5.6), P(rx - 1.0, -7.8), P(2, -12.8), P(-8.5, -8)], fill=hair)
        elif style == "fringe":
            d.polygon([P(-8, -3), P(-1, -11.8), P(6, -11.2), P(rx + 0.6, -4.6), P(rx - 1.2, -7.4), P(2, -9.2), P(-8.5, -7)], fill=hair)
        elif style == "short":
            d.polygon([P(-8, -3), P(-2, -11.7), P(5, -11.2), P(rx - 0.6, -6.6), P(rx - 2.2, -8.3), P(0, -9.5)], fill=hair)
        elif style == "cap":
            d.polygon([P(-9.2, -4), P(-6, -12.8), P(4, -13.6), P(rx - 1, -8.6), P(rx + 5.8, -6.6), P(rx - 1.0, -5.2), P(-9, -5)], fill=(26, 34, 54))
            d.polygon([P(rx - 1.0, -5.0), P(rx + 5.8, -6.2), P(rx - 1.0, -6.0)], fill=(14, 18, 28))
        # ojo y ceja
        ey = max(0.35, eye)
        E(rx * 0.55, -0.9, 1.15, 1.05 * ey, (22, 18, 18))
        d.line([P(rx * 0.55 - 2.4, -3.1 - 0.2 * (1 - eye)), P(rx * 0.55 + 2.2, -3.4 + 0.5 * (1 - eye))], fill=hair, width=max(1, int(1.1 * S)))
        # boca
        d.line([P(rx * 0.5, 6.2), P(rx * 0.95, 6.0)], fill=mulc(skin, 0.5), width=max(1, int(0.7 * S)))
        # sombra mejilla (pómulo marcado en Frank)
        d.line([P(rx * 0.2, 2.2), P(rx * 0.62, 5.8)], fill=mulc(skin, 0.86), width=max(1, int(0.9 * S)))
    elif view == "front":
        rx, ry = 7.7 * hw, 10.2
        E(-7.4 * hw, 1.2, 1.9, 2.9, skin_d)
        E(7.4 * hw, 1.2, 1.9, 2.9, skin_d)
        E(0, -0.6, rx + 0.9, ry + 0.9, hair)
        E(0, 1.8, rx, ry - 0.8, skin)
        jw = L["jaw"]
        d.polygon([P(-rx, 3), P(rx, 3), P(rx * 0.72 * jw, 9), P(0, 11.6), P(-rx * 0.72 * jw, 9)], fill=skin)
        # pelo
        if style == "back":
            d.polygon([P(-rx - 0.6, -2), P(-rx * 0.8, -9.5), P(0, -12), P(rx * 0.8, -9.5), P(rx + 0.6, -2), P(rx - 1, -5.8), P(0, -8.0), P(-rx + 1, -5.8)], fill=hair)
        elif style == "fringe":
            d.polygon([P(-rx - 0.6, -2), P(-rx * 0.8, -9.5), P(0, -12), P(rx * 0.8, -9.5), P(rx + 0.6, -2), P(rx - 1, -4.6), P(2, -6.4), P(-rx + 1.4, -5.0)], fill=hair)
        else:
            d.polygon([P(-rx - 0.6, -2), P(-rx * 0.8, -9.5), P(0, -12), P(rx * 0.8, -9.5), P(rx + 0.6, -2), P(rx - 1, -6.2), P(0, -7.2), P(-rx + 1, -6.2)], fill=hair)
        if style == "cap":
            d.polygon([P(-rx - 1.3, -3), P(-rx, -11.2), P(0, -13.5), P(rx, -11.2), P(rx + 1.3, -3), P(0, -5.0)], fill=(26, 34, 54))
        ey = max(0.35, eye)
        for sx in (-1, 1):
            E(sx * 3.5 * hw + look, -0.4, 1.2, 0.95 * ey, (22, 18, 18))
            d.line([P(sx * 3.5 * hw - 2, -2.9), P(sx * 3.5 * hw + 2, -2.9 - 0.4 * sx)], fill=hair, width=max(1, int(1.0 * S)))
        d.line([P(0, 0.5), P(-0.5, 4.2), P(0.9, 4.6)], fill=mulc(skin, 0.72), width=max(1, int(0.8 * S)))
        d.line([P(-2.2, 7.0), P(2.2, 7.0)], fill=mulc(skin, 0.5), width=max(1, int(0.8 * S)))
    else:  # back / back34
        rx, ry = 7.9 * hw, 10.2
        E(-7.4 * hw, 1.6, 1.8, 2.8, skin_d)
        E(7.4 * hw, 1.6, 1.8, 2.8, skin_d)
        E(0, 0, rx + 0.8, ry + 0.8, hair)
        d.polygon([P(-3, 8.4), P(3, 8.4), P(2.6, 11.5), P(-2.6, 11.5)], fill=skin_d)
        if view == "back34":
            E(rx * 0.72, 2.2, 2.7, 6.2, skin)
            d.polygon([P(rx * 0.9, 1), P(rx + 2.6, 3.8), P(rx * 0.9, 4.6)], fill=skin)
            E(rx * 0.35, 6.8, 1.5, 0.5, mulc(skin, 0.6))


def draw_head_big(img, who, cx, cy, hpx, view="side", eye=1.0, look=0.0, light=(1, 1, 1), rim=None, flip=False):
    """Cabeza grande para primeros planos (hpx = alto de la cabeza en px)."""
    S0 = hpx / 23.0
    ss = 2
    S = S0 * ss
    size = int(hpx * 1.7)
    lay = Image.new("RGBA", (size * ss, size * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    o = size * ss / 2
    T = lambda x, y: (o + x * S, o + y * S)
    # cuello
    d.polygon([T(-4.6, 6), T(4.6, 6), T(5.4, 22), T(-5.4, 22)], fill=mulc(SKIN, 0.85))
    d.polygon([T(-14, 20), T(14, 20), T(20, 30), T(-20, 30)], fill=UNI_SHIRT)
    _head(d, T, S, (0, 0), who, view, eye, look)
    lay = lay.reduce(ss)
    if flip:
        lay = ImageOps.mirror(lay)
    lay = _lit(lay, light, rim)
    img.paste(lay, (int(cx - size / 2), int(cy - size / 2)), lay)


def _lit(lay, light, rim):
    r, g, b, a = lay.split()
    rgb = Image.merge("RGB", (r, g, b))
    if light != (1, 1, 1):
        col = Image.new("RGB", rgb.size, tuple(int(clamp(c * 255, 0, 255)) for c in light))
        rgb = ImageChops.multiply(rgb, col)
    if rim:
        rc, dx, dy, k = rim
        sh = ImageChops.offset(a, int(dx), int(dy))
        edge = ImageChops.subtract(a, sh).point(lambda v: int(clamp(v * k, 0, 255)))
        colr = Image.new("RGB", rgb.size, rc)
        rgb = Image.composite(colr, rgb, edge)
    r, g, b = rgb.split()
    return Image.merge("RGBA", (r, g, b, a))


def draw_man(img, who, sx, sy, hpx, P, view="side", facing=1, light=(1, 1, 1), rim=None, guard=False,
             alpha=1.0, extra=None):
    """Dibuja un hombre de pie en (sx,sy)=pies. hpx = altura total en px.
    Devuelve posiciones de pantalla de manos / cabeza."""
    u = hpx / 100.0
    ss = 2
    S = u * ss
    lw, lh = 150, 140
    lay = Image.new("RGBA", (int(lw * S), int(lh * S)), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    ox, oy = lw * S / 2, 118 * S
    T = lambda x, y: (ox + x * S, oy + y * S)
    shirt, pants = (GUARD_SHIRT, GUARD_PANTS) if guard else (UNI_SHIRT, UNI_PANTS)
    out = {}
    hx, hy = P["hip"]
    l = math.radians(P["lean"])
    up = (math.sin(l), -math.cos(l))
    fw = (math.cos(l), math.sin(l))
    Hc = (hx, hy)
    loc = lambda a, b: (Hc[0] + a * fw[0] + b * up[0], Hc[1] + a * fw[1] + b * up[1])
    dark = lambda c: mulc(c, 0.72)
    sh = loc(-0.4, 30.0)
    nk = loc(0.5, 32.5)
    ht = math.radians(P["head"]) + l
    hc = (nk[0] + 10.5 * math.sin(ht), nk[1] - 10.5 * math.cos(ht))
    if view == "side":
        # brazo y pierna traseros
        _limb(d, T, S, (hx - 0.5, hy), P["fB"], 25, 25, 1, 8.6, 7.2, dark(pants))
        e = P["fB"]
        d.line([T(e[0] - 1, e[1] - 1.4), T(e[0] + 5.5, e[1] - 1.2)], fill=dark(SHOE), width=int(4.6 * S))
        _limb(d, T, S, sh, P["hB"], 17, 16.5, -1, 6.8, 5.8, dark(shirt))
        eb = _ik(sh, P["hB"], 17, 16.5, -1)[1]
        _ell(d, T(*eb), 3.1 * S, 3.1 * S, dark(SKIN))
        # torso
        tor = [loc(-6.2, -4), loc(6.4, -4), loc(7.4, 12), loc(8.2, 26), loc(6.0, 33), loc(-5.6, 33), loc(-8.0, 22), loc(-7.0, 6)]
        d.polygon([T(*q) for q in tor], fill=shirt)
        d.polygon([T(*q) for q in [loc(-6.2, -4), loc(6.4, -4), loc(6.6, 1.5), loc(-6.4, 1.5)]], fill=pants)
        d.line([T(*loc(-7.6, 14)), T(*loc(-6.4, 30))], fill=dark(shirt), width=int(2.2 * S))  # sombra espalda
        d.polygon([T(*q) for q in [loc(5.8, 33), loc(2.0, 30.0), loc(0.4, 33.6)]], fill=mulc(shirt, 1.12))  # cuello camisa
        # cuello + cabeza
        d.polygon([T(*loc(-2.6, 30)), T(*loc(3.6, 30)), T(*loc(3.0, 37)), T(*loc(-2.2, 37))], fill=mulc(SKIN, 0.82))
        # pierna delantera
        _limb(d, T, S, (hx + 0.8, hy), P["fF"], 25, 25, 1, 8.8, 7.4, pants)
        e = P["fF"]
        d.line([T(e[0] - 1, e[1] - 1.5), T(e[0] + 6.2, e[1] - 1.3)], fill=SHOE, width=int(4.8 * S))
        _head(d, T, S, hc, who, "side", P["eye"], P["look"])
        _limb(d, T, S, sh, P["hF"], 17, 16.5, -1, 7.2, 6.0, shirt)
        ef = _ik(sh, P["hF"], 17, 16.5, -1)[1]
        _ell(d, T(*ef), 3.2 * S, 3.2 * S, SKIN)
        out["hF"] = ef
        out["hB"] = eb
    else:
        # vista frontal / trasera : x lateral
        hipw = 4.2
        _limb(d, T, S, (hx - hipw, hy), P["fB"], 25, 25, 1 if P["fB"][0] > hx - hipw else -1, 8.6, 7.4, pants)
        _limb(d, T, S, (hx + hipw, hy), P["fF"], 25, 25, 1 if P["fF"][0] < hx + hipw else -1, 8.6, 7.4, pants)
        for e in (P["fB"], P["fF"]):
            _ell(d, T(e[0], e[1] - 1.2), 4.4 * S, 2.6 * S, SHOE)
        ln = 31.0 * math.cos(l)
        shy = hy - ln
        shw = 9.2
        tor = [(hx - 7.0, hy + 3), (hx + 7.0, hy + 3), (hx + 8.2, hy - ln * 0.4), (hx + shw, shy + 1.5), (hx + 4, shy - 1.2),
               (hx - 4, shy - 1.2), (hx - shw, shy + 1.5), (hx - 8.2, hy - ln * 0.4)]
        d.polygon([T(*q) for q in tor], fill=shirt)
        d.polygon([T(*q) for q in [(hx - 7.0, hy + 3), (hx + 7.0, hy + 3), (hx + 7.2, hy - 1.5), (hx - 7.2, hy - 1.5)]], fill=pants)
        d.line([T(hx, shy + 3), T(hx, hy - 2)], fill=dark(shirt), width=max(1, int(0.9 * S)))
        d.polygon([T(hx - 2.8, shy - 0.5), T(hx + 2.8, shy - 0.5), T(hx + 2.4, shy - 5.5), T(hx - 2.4, shy - 5.5)], fill=mulc(SKIN, 0.82))
        hcx, hcy = hx + P["head"] * 0.25, shy - 14.5 + abs(P["head"]) * 0.05
        _head(d, T, S, (hcx, hcy), who, view, P["eye"], P["look"])
        eb = _limb(d, T, S, (hx - shw + 0.6, shy + 3), P["hB"], 16, 15, 1, 6.8, 5.8, shirt)
        ef = _limb(d, T, S, (hx + shw - 0.6, shy + 3), P["hF"], 16, 15, -1, 6.8, 5.8, shirt)
        for e in (eb, ef):
            _ell(d, T(*e), 3.2 * S, 3.2 * S, SKIN)
        out["hF"], out["hB"] = ef, eb
        hc = (hcx, hcy)
    out["head"] = hc
    lay = lay.reduce(ss)
    if facing < 0:
        lay = ImageOps.mirror(lay)
    lay = _lit(lay, light, rim)
    if alpha < 1:
        r, g, b, a = lay.split()
        a = a.point(lambda v: int(v * alpha))
        lay = Image.merge("RGBA", (r, g, b, a))
    lw_px, lh_px = lay.size
    px, py = sx - lw_px / 2, sy - 118 * u
    img.paste(lay, (int(px), int(py)), lay)

    def conv(q):
        x = lw / 2 + q[0]
        if facing < 0:
            x = lw - x
        return (px + x * u, py + (118 + q[1]) * u)
    res = {k: conv(v) for k, v in out.items()}
    return res


# ----------------------------------------------------------------- poses
def stand_pose(**kw):
    return pose(**kw)


def walk_pose(phase, crouch=0.0, lean=8.0, stride=13.0, lift=7.0, armswing=6.0, head=0.0):
    """Ciclo de caminar (phase en radianes). crouch 0..1 baja la cadera."""
    hy = -50 + 17 * crouch + 1.2 * abs(math.sin(phase))
    hx = 0.0
    def foot(ph):
        x = stride * math.sin(ph) * 0.9
        y = -lift * max(0.0, math.cos(ph)) ** 1.5 if math.cos(ph) > 0 else 0
        return (x, y)
    fF = foot(phase)
    fB = foot(phase + math.pi)
    lean_t = lean + 18 * crouch
    sh_x = math.sin(math.radians(lean_t)) * 30
    sh_y = hy - math.cos(math.radians(lean_t)) * 30
    hF = (sh_x + 8 - armswing * math.sin(phase) * 0.6 + 6 * crouch, sh_y + 22 - 4 * crouch)
    hB = (sh_x + 5 + armswing * math.sin(phase) * 0.6 + 4 * crouch, sh_y + 23 - 3 * crouch)
    return pose(hip=(hx, hy), lean=lean_t, fF=fF, fB=fB, hF=hF, hB=hB, head=head)


def shade_rect(img, box, color, alpha):
    m = Image.new("L", img.size, 0)
    ImageDraw.Draw(m).rectangle(box, fill=int(255 * alpha))
    return paint_mask(img, m, color)
