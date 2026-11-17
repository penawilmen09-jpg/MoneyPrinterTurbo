"""Motor 2D: utilidades, sprites de dinosaurios y paisajes (Pillow + numpy)."""
import functools
import math
import random

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps

W, H = 1080, 1920
TAU = math.tau


# ----------------------------------------------------------------- utilidades
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def sm(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def prog(t, a, b):
    return clamp((t - a) / (b - a))


def lerp(a, b, t):
    return a + (b - a) * t


def mix(c1, c2, t):
    return tuple(int(round(lerp(a, b, t))) for a, b in zip(c1, c2))


def vgrad(w, h, stops):
    ys = np.linspace(0, 1, max(h, 2))
    pos = [s[0] for s in stops]
    arr = np.zeros((max(h, 2), 1, 3), np.float32)
    for c in range(3):
        arr[:, 0, c] = np.interp(ys, pos, [s[1][c] for s in stops])
    return Image.fromarray(arr.astype(np.uint8), "RGB").resize((w, max(h, 2)), Image.NEAREST)


@functools.lru_cache(maxsize=16)
def sky_img(stops):
    return vgrad(W, H, list(stops))


def bez(p0, p1, p2, n=24):
    out = []
    for i in range(n):
        t = i / (n - 1)
        out.append(((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
                    (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]))
    return out


def bez3(p0, p1, p2, p3, n=30):
    out = []
    for i in range(n):
        t = i / (n - 1)
        u = 1 - t
        out.append((u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
                    u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1]))
    return out


def taper(n, a, b):
    return [lerp(a, b, i / (n - 1)) for i in range(n)]


def ell(cx, cy, rx, ry, n=40, rot=0.0):
    c, s = math.cos(rot), math.sin(rot)
    pts = []
    for i in range(n):
        a = TAU * i / n
        x, y = rx * math.cos(a), ry * math.sin(a)
        pts.append((cx + x * c - y * s, cy + x * s + y * c))
    return pts


def rot(pts, piv, a):
    c, s = math.cos(a), math.sin(a)
    return [(piv[0] + (x - piv[0]) * c - (y - piv[1]) * s,
             piv[1] + (x - piv[0]) * s + (y - piv[1]) * c) for x, y in pts]


def mixpal(p, hz):
    """Mezcla los colores de una paleta de sprite con la neblina hz=(r,g,b,amt)."""
    if not hz or hz[3] <= 0:
        return p
    out = {}
    for k, v in p.items():
        out[k] = mix(v, hz[:3], hz[3])
    return out


def multiply_color(img, col, k=1.0):
    """Tinte multiplicativo con mezcla k."""
    tint = Image.new("RGB", img.size, tuple(int(c) for c in col))
    mult = ImageChops.multiply(img, tint)
    return mult if k >= 1 else Image.blend(img, mult, k)


# ------------------------------------------------------------- brillos aditivos
@functools.lru_cache(maxsize=300)
def glow_sprite(r, color, power):
    yy, xx = np.mgrid[-r:r, -r:r].astype(np.float32) + 0.5
    d = np.sqrt(xx * xx + yy * yy) / r
    a = np.clip(1 - d, 0, 1) ** power
    arr = (a[..., None] * np.array(color, np.float32)[None, None, :]).clip(0, 255).astype(np.uint8)
    return Image.fromarray(arr, "RGB")


def add_glow(img, cx, cy, r, color, power=2.0, k=1.0):
    r = max(8, int(round(r / 8)) * 8)
    kk = round(k * 10) / 10
    if kk <= 0:
        return
    c = tuple(int(min(255, v * kk)) for v in color)
    spr = glow_sprite(r, c, power)
    x0, y0 = int(cx - r), int(cy - r)
    bx0, by0 = max(0, x0), max(0, y0)
    bx1, by1 = min(img.width, x0 + 2 * r), min(img.height, y0 + 2 * r)
    if bx1 <= bx0 or by1 <= by0:
        return
    reg = img.crop((bx0, by0, bx1, by1))
    s = spr.crop((bx0 - x0, by0 - y0, bx1 - x0, by1 - y0))
    img.paste(ImageChops.add(reg, s), (bx0, by0))


@functools.lru_cache(maxsize=200)
def puff_sprite(r, color, alpha):
    pad = int(r * 0.6)
    s = int(r * 2 + pad * 2)
    im = Image.new("L", (s, s), 0)
    d = ImageDraw.Draw(im)
    rnd = random.Random(r * 7 + color[0])
    for _ in range(7):
        ox, oy = rnd.uniform(-r * .45, r * .45), rnd.uniform(-r * .35, r * .35)
        rr = r * rnd.uniform(.55, .9)
        d.ellipse((s / 2 + ox - rr, s / 2 + oy - rr, s / 2 + ox + rr, s / 2 + oy + rr), fill=255)
    im = im.filter(ImageFilter.GaussianBlur(r * 0.28))
    im = im.point(lambda v: int(v * alpha))
    out = Image.new("RGBA", (s, s), tuple(color) + (0,))
    out.putalpha(im)
    return out


def put_puff(img, cx, cy, r, color, alpha):
    r = max(8, int(round(r / 6)) * 6)
    a = round(clamp(alpha) * 20) / 20
    if a <= 0:
        return
    spr = puff_sprite(r, tuple(color), a)
    img.paste(spr, (int(cx - spr.width / 2), int(cy - spr.height / 2)), spr)


# --------------------------------------------------------------------- paisaje
class Ridge:
    def __init__(self, base, amp, seed, kind, scale):
        r = random.Random(seed)
        self.p = [r.uniform(0, TAU) for _ in range(5)]
        self.base, self.amp, self.kind, self.scale = base, amp, kind, scale

    def y(self, x):
        p, s = self.p, self.scale
        if self.kind == "mountain":
            v = (0.55 * (1 - abs(math.sin(x / s + p[0]))) ** 1.3
                 + 0.28 * (1 - abs(math.sin(x / (s * .45) + p[1])))
                 + 0.12 * math.sin(x / (s * .17) + p[2]) + 0.05 * math.sin(x / (s * .06) + p[3]))
        else:
            v = (0.5 + 0.32 * math.sin(x / s + p[0]) + 0.2 * math.sin(x / (s * .43) + p[1])
                 + 0.1 * math.sin(x / (s * .17) + p[2]))
        return self.base - self.amp * v


def vary(col, rnd, k=0.14):
    f = 1 + rnd.uniform(-k, k)
    return tuple(int(clamp(c * f, 0, 255)) for c in col)


def draw_tree(d, kind, x, y, h, col, rnd):
    if kind == "conifer":
        tw = max(2, h * .05)
        d.rectangle((x - tw, y - h * .25, x + tw, y + 4), fill=col)
        for i in range(4):
            ty = y - h * .12 - i * h * .2
            w = h * .3 * (1 - i * .2)
            d.polygon([(x - w, ty), (x + w, ty), (x, ty - h * .36)], fill=col)
    elif kind == "palm":
        lean = rnd.uniform(-.12, .12) * h
        tx, ty = x + lean, y - h
        d.line([(x, y + 4), (x + lean * .4, y - h * .5), (tx, ty)], fill=col, width=int(max(3, h * .07)), joint="curve")
        for a in range(-170, -5, 24):
            ar = math.radians(a + rnd.uniform(-6, 6))
            L = h * rnd.uniform(.48, .62)
            pts = [(tx + math.cos(ar) * L * s, ty + math.sin(ar) * L * s * .8 + L * .55 * s * s)
                   for s in [i / 8 for i in range(9)]]
            d.line(pts, fill=col, width=int(max(2, h * .035)), joint="curve")
            for j in range(2, 9, 2):
                px, py = pts[j]
                d.line([(px, py), (px - 4, py + L * .17 * (1 - j / 10))], fill=col, width=2)
                d.line([(px, py), (px + 4, py + L * .17 * (1 - j / 10))], fill=col, width=2)
    elif kind == "round":
        tw = max(3, h * .06)
        d.polygon([(x - tw, y + 4), (x - tw * .6, y - h * .6), (x + tw * .6, y - h * .6), (x + tw, y + 4)], fill=col)
        for _ in range(7):
            cx, cy = x + rnd.uniform(-h * .28, h * .28), y - h * .72 + rnd.uniform(-h * .2, h * .16)
            r = h * rnd.uniform(.17, .27)
            d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=col)
    elif kind in ("dead", "burnt"):
        def br(x0, y0, ang, L, wd, depth):
            x1, y1 = x0 + math.cos(ang) * L, y0 + math.sin(ang) * L
            d.line([(x0, y0), (x1, y1)], fill=col, width=int(max(1, wd)))
            if depth > 0:
                n = 2 if depth > 1 else rnd.choice((1, 2))
                for _ in range(n):
                    br(x1, y1, ang + rnd.uniform(-.7, .7), L * rnd.uniform(.6, .78), wd * .62, depth - 1)
        br(x, y + 4, -math.pi / 2 + rnd.uniform(-.12, .12), h * .42, max(3, h * .06), 3 if kind == "dead" else 1)
    elif kind == "fern":
        for a in range(-175, -4, 14):
            ar = math.radians(a + rnd.uniform(-5, 5))
            L = h * rnd.uniform(.5, .85)
            droop = rnd.uniform(.5, 1.0)
            pts = [(x + math.cos(ar) * L * s, y + math.sin(ar) * L * s * 1.05 + L * droop * s * s * .5)
                   for s in [i / 12 for i in range(13)]]
            d.line(pts, fill=col, width=int(max(3, h * .022)), joint="curve")
            for j in range(2, 13):
                px, py = pts[j]
                ll = L * .14 * (1 - j / 14) + 3
                d.line([(px, py), (px - ll * .5, py + ll)], fill=col, width=3)
                d.line([(px, py), (px + ll * .5, py + ll)], fill=col, width=3)
    elif kind == "grass":
        for i in range(5):
            ar = math.radians(-90 + rnd.uniform(-35, 35))
            d.line([(x, y + 2), (x + math.cos(ar) * h, y + math.sin(ar) * h)], fill=col, width=3)


LW = 1750


@functools.lru_cache(maxsize=24)
def ridge_layer(base, amp, seed, kind, scale, c_top, c_bot, trees, extra=None):
    rg = Ridge(base, amp, seed, kind, scale)
    tall = 420 if trees else 80
    y0 = int(max(0, base - amp * 1.15 - tall))
    h = H - y0
    pts = [(x, rg.y(x) - y0) for x in range(0, LW + 1, 5)]
    mask = Image.new("L", (LW, h), 0)
    ImageDraw.Draw(mask).polygon(pts + [(LW, h), (0, h)], fill=255)
    top_y = min(p[1] for p in pts)
    grad = vgrad(LW, h, [(0, c_top), (clamp(top_y / h + 0.05, 0.01, 0.9), c_top), (1, c_bot)])
    layer = Image.new("RGBA", (LW, h), (0, 0, 0, 0))
    layer.paste(grad, (0, 0), mask)
    d = ImageDraw.Draw(layer)
    rnd = random.Random(seed * 31 + 5)
    if trees:
        for kind_t, spacing, col, size in trees:
            x = rnd.uniform(0, spacing)
            while x < LW:
                yy = rg.y(x) - y0 + rnd.uniform(0, 5)
                draw_tree(d, kind_t, x, yy, size * rnd.uniform(.65, 1.3), vary(col, rnd), rnd)
                x += spacing * rnd.uniform(.6, 1.5)
    if extra == "volcano":
        vx, vb = 900, base - amp * .4
        cone = [(vx - 560, base - y0 + 160), (vx - 150, vb - 250 - y0), (vx - 48, vb - 300 - y0), (vx + 48, vb - 300 - y0),
                (vx + 150, vb - 250 - y0), (vx + 560, base - y0 + 160)]
        d.polygon(cone, fill=c_top)
        d.polygon([(vx - 48, vb - 300 - y0), (vx - 8, vb - 284 - y0), (vx + 48, vb - 300 - y0)], fill=tuple(int(c * .7) for c in c_top))
    return layer, y0


def put_layer(img, layer, dx, dy=0):
    im, y0 = layer
    v = im.transform((W, H), Image.AFFINE, (1, 0, dx, 0, 1, -y0 + dy), resample=Image.BILINEAR)
    img.paste(v, (0, 0), v)


@functools.lru_cache(maxsize=24)
def haze_band(yc, hh, color, alpha):
    a = np.zeros((H, 1), np.float32)
    ys = np.arange(H)
    a[:, 0] = np.exp(-((ys - yc) / (hh / 2.2)) ** 2) * alpha * 255
    al = Image.fromarray(a.astype(np.uint8), "L").resize((W, H), Image.NEAREST)
    out = Image.new("RGBA", (W, H), tuple(color) + (0,))
    out.putalpha(al)
    return out


def put_haze(img, yc, hh, color, alpha):
    b = haze_band(int(yc), int(hh), tuple(color), round(alpha, 2))
    img.paste(b, (0, 0), b)


@functools.lru_cache(maxsize=6)
def cloud_layer(seed, color, width=2300, hgt=520, n=26):
    rnd = random.Random(seed)
    im = Image.new("L", (width, hgt), 0)
    d = ImageDraw.Draw(im)
    for _ in range(n):
        cx, cy = rnd.uniform(0, width), rnd.uniform(hgt * .25, hgt * .75)
        for _ in range(6):
            r = rnd.uniform(40, 110)
            ox, oy = rnd.uniform(-150, 150), rnd.uniform(-24, 24)
            d.ellipse((cx + ox - r * 1.6, cy + oy - r * .55, cx + ox + r * 1.6, cy + oy + r * .55), fill=rnd.randint(80, 150))
    im = im.filter(ImageFilter.GaussianBlur(22))
    out = Image.new("RGBA", (width, hgt), tuple(color) + (0,))
    out.putalpha(im)
    return out


def put_clouds(img, seed, color, y, dx):
    c = cloud_layer(seed, tuple(color))
    v = c.transform((W, c.height), Image.AFFINE, (1, 0, dx % (c.width - W), 0, 1, 0), resample=Image.BILINEAR)
    img.paste(v, (0, int(y)), v)


# ---- paletas del paisaje --------------------------------------------------------
PAL = {
    "gold": dict(sky=((0, (40, 96, 148)), (.4, (122, 168, 180)), (.62, (247, 198, 130)), (1, (255, 226, 172))),
                 far=((118, 148, 170), (176, 190, 184)), h1=((74, 126, 112), (54, 98, 84)),
                 h2=((52, 108, 72), (36, 80, 52)), gr=((78, 124, 58), (42, 76, 36)), fg=((24, 54, 34), (12, 30, 20)),
                 haze=(255, 216, 166), hz=.34, glow=(255, 220, 150)),
    "day": dict(sky=((0, (52, 124, 190)), (.45, (128, 190, 214)), (.7, (206, 228, 214)), (1, (240, 240, 200))),
                far=((120, 160, 180), (176, 204, 196)), h1=((82, 142, 110), (60, 112, 86)),
                h2=((64, 128, 70), (44, 98, 52)), gr=((98, 148, 62), (56, 100, 40)), fg=((28, 66, 36), (14, 38, 22)),
                haze=(226, 240, 220), hz=.3, glow=(255, 250, 210)),
    "fire": dict(sky=((0, (26, 12, 14)), (.4, (110, 30, 16)), (.68, (240, 110, 30)), (1, (255, 190, 80))),
                 far=((70, 30, 24), (120, 50, 28)), h1=((52, 22, 18), (38, 16, 14)),
                 h2=((38, 16, 14), (26, 12, 10)), gr=((46, 22, 16), (24, 12, 10)), fg=((14, 8, 8), (8, 5, 5)),
                 haze=(255, 120, 40), hz=.34, glow=(255, 140, 50)),
    "ash": dict(sky=((0, (28, 26, 28)), (.5, (66, 58, 54)), (.78, (116, 88, 66)), (1, (150, 112, 80))),
                far=((78, 70, 66), (112, 96, 84)), h1=((70, 66, 56), (52, 48, 42)),
                h2=((64, 58, 46), (46, 42, 34)), gr=((72, 62, 48), (44, 38, 30)), fg=((26, 22, 20), (14, 12, 12)),
                haze=(130, 106, 86), hz=.4, glow=(220, 150, 90)),
    "dead": dict(sky=((0, (70, 78, 86)), (.5, (130, 128, 120)), (.8, (186, 168, 140)), (1, (206, 186, 150))),
                 far=((112, 112, 110), (160, 154, 140)), h1=((106, 98, 78), (84, 78, 62)),
                 h2=((98, 86, 62), (76, 66, 48)), gr=((106, 90, 62), (70, 58, 40)), fg=((40, 34, 28), (22, 20, 18)),
                 haze=(190, 176, 150), hz=.34, glow=(255, 230, 190)),
    "cold": dict(sky=((0, (72, 90, 112)), (.5, (140, 160, 178)), (.8, (196, 208, 214)), (1, (222, 228, 226))),
                 far=((132, 146, 162), (180, 192, 200)), h1=((118, 130, 134), (96, 108, 114)),
                 h2=((104, 114, 116), (84, 94, 98)), gr=((136, 146, 150), (92, 102, 108)), fg=((44, 52, 60), (26, 32, 40)),
                 haze=(214, 224, 230), hz=.46, glow=(235, 240, 250)),
    "dawn": dict(sky=((0, (30, 52, 104)), (.32, (96, 100, 150)), (.56, (240, 140, 120)), (.8, (255, 196, 120)), (1, (255, 230, 170))),
                 far=((120, 112, 150), (200, 150, 140)), h1=((88, 110, 110), (64, 92, 88)),
                 h2=((64, 120, 78), (44, 92, 58)), gr=((94, 150, 70), (52, 104, 44)), fg=((26, 70, 40), (14, 44, 26)),
                 haze=(255, 190, 140), hz=.34, glow=(255, 210, 140)),
}


def tcol(c, k=.78):
    return tuple(int(v * k) for v in c)


def layer_set(pal, trees):
    """(base,amp,seed,kind,scale,speed) por capa."""
    P = PAL[pal]
    live = trees == "live"
    ts = {
        "far": None,
        "h1": ((("conifer", 40, tcol(P["h1"][0], .82), 96),) if live else (("dead", 60, tcol(P["h1"][0], .7), 120),)),
        "h2": ((("palm", 74, tcol(P["h2"][0], .85), 120), ("conifer", 120, tcol(P["h2"][0], .75), 150)) if live
               else (("dead", 70, tcol(P["h2"][0], .6), 150),)),
        "gr": ((("round", 220, tcol(P["gr"][0], .8), 180), ("grass", 40, tcol(P["gr"][0], .9), 24)) if live
               else (("dead", 190, tcol(P["gr"][0], .55), 200),)),
        "fg": ((("fern", 150, P["fg"][0], 300),) if live else (("dead", 210, P["fg"][0], 340), ("grass", 70, P["fg"][0], 40))),
    }
    return [
        (("far", (1040, 150, 16, "hill", 520), P["far"], ts["far"], .12, None) if pal == "dawn" else
         ("far", (1000, 330, 11, "mountain", 420), P["far"], ts["far"], .12, "volcano" if pal in ("gold", "day") else None)),
        ("h1", (1105, 130, 12, "hill", 520), P["h1"], ts["h1"], .28, None),
        ("h2", (1215, 80, 13, "hill", 380), P["h2"], ts["h2"], .5, None),
        ("gr", (1300, 26, 14, "hill", 300), P["gr"], ts["gr"], .85, None),
        ("fg", (1590, 55, 15, "hill", 260), P["fg"], ts["fg"], 1.5, None),
    ]


def _lay(spec, pal):
    name, (base, amp, seed, kind, scale), (ct, cb), trees, speed, extra = spec
    return ridge_layer(base, amp, seed, kind, scale, ct, cb, trees, extra)


def draw_sky(img_stops):
    return sky_img(tuple(img_stops)).copy()


def draw_back(img, camx, pal, trees="live", upto=None):
    """Capas lejanas (montañas, colinas, suelo). Devuelve nada."""
    P = PAL[pal]
    specs = layer_set(pal, trees)
    for spec in specs[:4]:
        name = spec[0]
        put_layer(img, _lay(spec, pal), camx * spec[4])
        if name == "far":
            put_haze(img, 1000, 380, P["haze"], P["hz"])
        elif name == "h1":
            put_haze(img, 1130, 260, P["haze"], P["hz"] * .8)
        elif name == "h2":
            put_haze(img, 1250, 180, P["haze"], P["hz"] * .55)


def draw_front(img, camx, pal, trees="live"):
    spec = layer_set(pal, trees)[4]
    put_layer(img, _lay(spec, pal), camx * spec[4])


def far_layer_info(pal, trees="live"):
    return layer_set(pal, trees)


# --------------------------------------------------------------------- sprites
class Sprite:
    def __init__(self, w, h, k, ox, oy):
        self.k, self.ox, self.oy = k, ox, oy
        self.size = (int(w * k), int(h * k))
        self.masks = {}

    def pt(self, x, y):
        return ((self.ox + x) * self.k, (self.oy + y) * self.k)

    def m(self, name):
        if name not in self.masks:
            im = Image.new("L", self.size, 0)
            self.masks[name] = (im, ImageDraw.Draw(im))
        return self.masks[name][1]

    def poly(self, name, pts):
        self.m(name).polygon([self.pt(*p) for p in pts], fill=255)

    def limb(self, name, pts, ws):
        d = self.m(name)
        P = [self.pt(*p) for p in pts]
        for i, (p, w) in enumerate(zip(P, ws)):
            r = w * self.k / 2
            d.ellipse((p[0] - r, p[1] - r, p[0] + r, p[1] + r), fill=255)
            if i < len(P) - 1:
                q = P[i + 1]
                r2 = ws[i + 1] * self.k / 2
                dx, dy = q[0] - p[0], q[1] - p[1]
                L = math.hypot(dx, dy) or 1
                nx, ny = -dy / L, dx / L
                d.polygon([(p[0] + nx * r, p[1] + ny * r), (q[0] + nx * r2, q[1] + ny * r2),
                           (q[0] - nx * r2, q[1] - ny * r2), (p[0] - nx * r, p[1] - ny * r)], fill=255)

    def finish(self, order, rim_dir=(1, -1), ss=2):
        """order: lista de (mask, top, bottom, rim|None). Devuelve RGBA reducido."""
        out = Image.new("RGBA", self.size, (0, 0, 0, 0))
        for name, top, bot, rim in order:
            if name not in self.masks:
                continue
            mk = self.masks[name][0]
            bb = mk.getbbox()
            if not bb:
                continue
            grad = vgrad(self.size[0], bb[3] - bb[1], [(0, top), (1, bot)])
            full = Image.new("RGB", self.size, bot)
            full.paste(grad, (0, bb[1]))
            out.paste(full, (0, 0), mk)
            if rim:
                dd = int(3.5 * self.k)
                sh = ImageChops.offset(mk, -rim_dir[0] * dd, -rim_dir[1] * dd)
                rm = ImageChops.subtract(mk, sh).filter(ImageFilter.GaussianBlur(self.k * .6))
                out.paste(Image.new("RGB", self.size, rim), (0, 0), rm)
        return out

    def clipped(self, name, clip):
        if name not in self.masks:
            return None
        return ImageChops.multiply(self.masks[name][0], self.masks[clip][0])

    def paint(self, out, mask, color):
        if mask is not None:
            out.paste(Image.new("RGB", self.size, color), (0, 0), mask)

    def reduce(self, out, ss):
        w, h = out.size
        sm_ = out.resize((w // ss, h // ss), Image.LANCZOS)
        return sm_, int(self.ox * self.k / ss), int(self.oy * self.k / ss)


def ik2(hip, tgt, l1, l2):
    dx, dy = tgt[0] - hip[0], tgt[1] - hip[1]
    d = max(abs(l1 - l2) + .01, min(math.hypot(dx, dy), l1 + l2 - .01))
    a = math.atan2(dy, dx)
    b = math.acos(clamp((l1 * l1 + d * d - l2 * l2) / (2 * l1 * d), -1, 1))
    ang = a - b
    return (hip[0] + l1 * math.cos(ang), hip[1] + l1 * math.sin(ang))


PALS = {
    "rex": dict(top=(138, 68, 44), bot=(210, 132, 70), rim=(255, 214, 150), belly=(232, 198, 140), stripe=(88, 40, 30),
                far_top=(92, 44, 32), far_bot=(150, 90, 54)),
    "raptor": dict(top=(70, 104, 68), bot=(150, 168, 90), rim=(255, 236, 160), belly=(220, 218, 150), stripe=(44, 70, 48),
                   far_top=(46, 70, 46), far_bot=(100, 122, 64)),
    "brachio": dict(top=(86, 126, 96), bot=(158, 176, 112), rim=(255, 236, 170), belly=(214, 212, 156), stripe=(56, 92, 70),
                    far_top=(56, 88, 66), far_bot=(106, 126, 82)),
    "tric": dict(top=(132, 100, 74), bot=(194, 156, 104), rim=(255, 224, 160), belly=(226, 206, 156), stripe=(92, 66, 48),
                 far_top=(88, 66, 50), far_bot=(140, 108, 74), frill=(186, 96, 82), frill2=(228, 160, 112)),
    "mammal": dict(top=(98, 72, 56), bot=(176, 136, 96), rim=(255, 226, 170), belly=(226, 200, 160), stripe=(70, 50, 40),
                   far_top=(70, 52, 40), far_bot=(120, 92, 66)),
}


def _walk_phase(ph):
    return ph / 12 * TAU


def build_trex(ph, sc, hz, variant="rex", roar=0.0, idle=False):
    P = mixpal(PALS[variant], hz)
    SS = 2
    k = sc * SS
    s = Sprite(470, 300, k, 220, 292)
    bob = 0.0
    if idle:
        phis = [1.2, 2.5]
        bob = 2.0 * math.sin(roar * 6.0)
    else:
        f = _walk_phase(ph)
        phis = [f, f + math.pi]
        bob = 3.0 * math.sin(2 * f)
    hip = (0, -88 + bob)
    for far, f in ((True, phis[1]), (False, phis[0])):
        lift = 0 if idle else 26 * max(0, -math.sin(f))
        ax = (22 if idle else 34) * math.cos(f) + (12 if far and idle else 0)
        ank = (ax - 4, -20 - lift)
        knee = ik2(hip, ank, 62, 60)
        nm = "legF" if far else "legN"
        s.limb(nm, [hip, knee, ank], [46, 28, 16])
        s.limb(nm, [ank, (ank[0] + 14, ank[1] + 9), (ank[0] + 36, ank[1] + 15 + (0 if lift else 3))], [16, 14, 9])
    # torso + cola
    s.poly("body", [(-165, -82 + bob), (-120, -96 + bob), (-70, -112 + bob), (-25, -122 + bob), (10, -128 + bob), (40, -130 + bob),
                    (62, -142 + bob), (78, -166 + bob), (92, -182 + bob), (104, -160 + bob), (88, -135 + bob), (78, -112 + bob),
                    (68, -92 + bob), (50, -70 + bob), (20, -62 + bob), (-20, -64 + bob), (-60, -72 + bob), (-100, -78 + bob),
                    (-140, -84 + bob)])
    jaw = roar * .6
    tilt = -roar * .32
    piv = (92, -172 + bob)
    head = [(84, -190), (100, -198), (128, -203), (160, -197), (188, -186), (199, -178), (201, -168), (190, -163), (150, -158),
            (112, -158), (92, -150), (84, -165)]
    head = rot([(x, y + bob) for x, y in head], piv, tilt)
    s.poly("body", head)
    jawp = [(100, -160), (150, -157), (190, -163), (194, -154), (170, -143), (130, -138), (104, -146)]
    jawp = rot(rot([(x, y + bob) for x, y in jawp], (104, -158 + bob), jaw), piv, tilt)
    s.poly("body", jawp)
    s.limb("legN", [(54, -112 + bob), (72, -98 + bob), (84, -104 + bob)], [12, 9, 6])
    belly = [(-60, -76 + bob), (-20, -88 + bob), (30, -96 + bob), (74, -108 + bob), (100, -158 + bob), (88, -135 + bob), (78, -112 + bob),
             (68, -92 + bob), (50, -70 + bob), (20, -62 + bob), (-20, -64 + bob)]
    s.poly("belly", belly)
    for i in range(6):
        x0 = -110 + i * 26
        s.poly("stripe", [(x0, -150 + bob), (x0 + 12, -150 + bob), (x0 + 22, -112 + bob), (x0 + 6, -112 + bob)])
    out = s.finish([("legF", P["far_top"], P["far_bot"], None), ("body", P["top"], P["bot"], P["rim"]),
                    ("legN", P["top"], P["bot"], P["rim"])])
    s.paint(out, s.clipped("belly", "body"), P["belly"])
    ms = s.clipped("stripe", "body")
    if ms is not None:
        ms = ImageChops.multiply(ms, Image.eval(s.masks["body"][0], lambda v: 0 if v < 255 else 255))
        # franjas suaves
        out.paste(Image.new("RGB", s.size, P["stripe"]), (0, 0), ms.point(lambda v: int(v * .45)))
    d = ImageDraw.Draw(out)

    def sp(x, y):
        return s.pt(x, y)
    ey = rot([(128, -186 + bob)], piv, tilt)[0]
    e = sp(*ey)
    r = 6 * k
    d.ellipse((e[0] - r, e[1] - r, e[0] + r, e[1] + r), fill=(255, 226, 120))
    d.ellipse((e[0] - r * .45, e[1] - r * .5, e[0] + r * .45, e[1] + r * .5), fill=(30, 14, 10))
    d.line([sp(*rot([(112, -194 + bob)], piv, tilt)[0]), sp(*rot([(146, -196 + bob)], piv, tilt)[0])], fill=P["stripe"], width=int(4 * k))
    # dientes
    for i in range(7):
        x = 126 + i * 10
        pa = rot([(x, -158 + bob)], piv, tilt)[0]
        pb = rot([(x + 5, -158 + bob)], piv, tilt)[0]
        pc = rot([(x + 2.5, -149 + bob)], piv, tilt)[0]
        d.polygon([sp(*pa), sp(*pb), sp(*pc)], fill=(250, 244, 226))
    return s.reduce(out, SS)


def build_brachio(ph, sc, hz, look=0.0, idle=False):
    P = mixpal(PALS["brachio"], hz)
    SS = 2
    k = sc * SS
    s = Sprite(860, 580, k, 430, 566)
    f = 0 if idle else _walk_phase(ph)
    bob = 0 if idle else 2.5 * math.sin(2 * f)
    for far, x, off in ((True, -64, 0), (True, 66, math.pi), (False, -100, math.pi), (False, 96, 0)):
        a = 0 if idle else .24 * math.sin(f + off)
        lift = 0 if idle else 16 * max(0, math.cos(f + off))
        top = (x, -165 + bob)
        bot = (x + math.sin(a) * 160, -165 + math.cos(a) * 160 + bob * .0 - lift + 0)
        nm = "legF" if far else "legN"
        s.limb(nm, [top, bot], [76, 54])
        s.poly(nm, ell(bot[0] + 6, bot[1] - 4, 36, 15))
    s.poly("body", ell(0, -208 + bob, 168, 74))
    tail = bez3((-130, -210 + bob), (-250, -220 + bob), (-330, -160 + bob), (-430, -100 + bob), 36)
    s.limb("body", tail, taper(36, 86, 6))
    e = (250 + look * -45, -470 - look * 30 + bob)
    neck = bez3((105, -240 + bob), (200, -280 + bob), (230 + look * -40, -380 - look * 20 + bob), e, 36)
    s.limb("body", neck, taper(36, 66, 22))
    hd = [(-12, -16), (24, -20), (56, -8), (60, 4), (26, 14), (-8, 10)]
    hd = rot([(e[0] + x, e[1] + y) for x, y in hd], e, .35 - look * .45)
    s.poly("body", hd)
    s.poly("belly", ell(20, -150 + bob, 150, 34))
    for i in range(8):
        cx = -120 + i * 36
        s.poly("stripe", ell(cx, -246 + bob + 8 * math.sin(i), 11, 7))
    out = s.finish([("legF", P["far_top"], P["far_bot"], None), ("body", P["top"], P["bot"], P["rim"]),
                    ("legN", P["top"], P["bot"], P["rim"])])
    s.paint(out, s.clipped("belly", "body"), P["belly"])
    ms = s.clipped("stripe", "body")
    if ms is not None:
        out.paste(Image.new("RGB", s.size, P["stripe"]), (0, 0), ms.point(lambda v: int(v * .55)))
    d = ImageDraw.Draw(out)
    ec = rot([(e[0] + 30, e[1] - 4)], e, .35 - look * .45)[0]
    p = s.pt(*ec)
    r = 4.5 * k
    d.ellipse((p[0] - r, p[1] - r, p[0] + r, p[1] + r), fill=(255, 232, 150))
    d.ellipse((p[0] - r * .5, p[1] - r * .5, p[0] + r * .5, p[1] + r * .5), fill=(24, 14, 10))
    return s.reduce(out, SS)


def build_tric(ph, sc, hz, look=0.0, idle=False):
    P = mixpal(PALS["tric"], hz)
    SS = 2
    k = sc * SS
    s = Sprite(560, 330, k, 240, 316)
    f = 0 if idle else _walk_phase(ph)
    bob = 0 if idle else 2.0 * math.sin(2 * f)
    for far, x, off in ((True, -62, math.pi), (True, 58, 0), (False, -92, 0), (False, 92, math.pi)):
        a = 0 if idle else .3 * math.sin(f + off)
        lift = 0 if idle else 10 * max(0, math.cos(f + off))
        top = (x, -90 + bob)
        bot = (x + math.sin(a) * 78, -90 + math.cos(a) * 78 - lift)
        nm = "legF" if far else "legN"
        s.limb(nm, [top, bot], [46, 36])
        s.poly(nm, ell(bot[0] + 5, bot[1] - 2, 27, 11))
    s.poly("body", ell(0, -128 + bob, 148, 66))
    tail = bez((-130, -132 + bob), (-200, -120 + bob), (-250, -70 + bob), 20)
    s.limb("body", tail, taper(20, 58, 6))
    piv = (128, -128 + bob)
    ang = -look * .5
    skull = [(120, -90), (140, -170), (210, -168), (262, -128), (272, -104), (244, -88), (190, -82), (140, -92)]
    s.poly("body", rot([(x, y + bob) for x, y in skull], piv, ang))
    beak = [(250, -134), (288, -108), (272, -86), (240, -92)]
    s.poly("body", rot([(x, y + bob) for x, y in beak], piv, ang))
    # volante (frill): disco festoneado inclinado hacia atras
    fr = []
    for i in range(36):
        a = TAU * i / 36
        rr = 1.0 + (0.07 if i % 2 else 0.0)
        fr.append((112 + math.cos(a) * 66 * rr, -158 + math.sin(a) * 104 * rr))
    fr = rot([(x, y + bob) for x, y in fr], (112, -120 + bob), -0.45)
    fr = rot(fr, piv, ang)
    s.poly("frill", fr)
    for hx, hy, hx2, hy2 in ((205, -160, 296, -226), (180, -164, 268, -236)):
        h1 = rot([(hx - 14, hy + 10 + bob), (hx2, hy2 + bob), (hx + 12, hy - 18 + bob)], piv, ang)
        s.poly("horn", h1)
    s.poly("horn", rot([(254, -128 + bob), (268, -160 + bob), (270, -124 + bob)], piv, ang))
    s.poly("belly", ell(10, -70 + bob, 130, 20))
    out = s.finish([("legF", P["far_top"], P["far_bot"], None), ("body", P["top"], P["bot"], P["rim"]),
                    ("frill", P["frill"], P["frill2"], P["rim"]), ("legN", P["top"], P["bot"], P["rim"]),
                    ("horn", (236, 228, 200), (250, 244, 226), None)])
    s.paint(out, s.clipped("belly", "body"), P["belly"])
    d = ImageDraw.Draw(out)
    ec = rot([(196, -140 + bob)], piv, ang)[0]
    p = s.pt(*ec)
    r = 5.5 * k
    d.ellipse((p[0] - r, p[1] - r, p[0] + r, p[1] + r), fill=(255, 228, 140))
    d.ellipse((p[0] - r * .5, p[1] - r * .5, p[0] + r * .5, p[1] + r * .5), fill=(24, 14, 10))
    # puntos del volante
    for i in range(7):
        a = math.radians(i * 51)
        q = rot(rot([(112 + math.cos(a) * 40, -158 + math.sin(a) * 66 + bob)], (112, -120 + bob), -0.45), piv, ang)[0]
        pp = s.pt(*q)
        rr = 5 * k
        d.ellipse((pp[0] - rr, pp[1] - rr, pp[0] + rr, pp[1] + rr), fill=(250, 212, 150))
    return s.reduce(out, SS)


def build_mammal(ph, sc, hz):
    P = mixpal(PALS["mammal"], hz)
    SS = 2
    k = sc * SS
    s = Sprite(80, 50, k, 38, 46)
    f = _walk_phase(ph)
    for far, off in ((True, math.pi), (False, 0)):
        a = .6 * math.sin(f + off)
        nm = "legF" if far else "legN"
        for x in (-9, 9):
            s.limb(nm, [(x, -12), (x + math.sin(a + (x > 0) * math.pi) * 6, -1)], [5, 3.5])
    s.poly("body", ell(0, -15 + 0.8 * math.sin(2 * f), 17, 9.5))
    s.poly("body", ell(18, -19, 8, 7))
    s.poly("body", [(22, -23), (33, -16), (23, -13)])
    s.poly("body", ell(15, -27, 3.6, 4.6))
    s.limb("body", bez3((-15, -15), (-26, -17), (-32, -28), (-28, -36), 14), taper(14, 5, 2))
    out = s.finish([("legF", P["far_top"], P["far_bot"], None), ("body", P["top"], P["bot"], P["rim"]),
                    ("legN", P["top"], P["bot"], P["rim"])])
    d = ImageDraw.Draw(out)
    p = s.pt(21, -21)
    r = 2 * k
    d.ellipse((p[0] - r, p[1] - r, p[0] + r, p[1] + r), fill=(20, 12, 10))
    p = s.pt(33, -16)
    d.ellipse((p[0] - r * .6, p[1] - r * .6, p[0] + r * .6, p[1] + r * .6), fill=(30, 18, 16))
    return s.reduce(out, SS)


@functools.lru_cache(maxsize=96)
def get_sprite(kind, ph, sc, hz, flip, a=0.0, idle=False):
    if kind == "trex":
        img, ax, ay = build_trex(ph, sc, hz, "rex", a, idle)
    elif kind == "raptor":
        img, ax, ay = build_trex(ph, sc, hz, "raptor", a, idle)
    elif kind == "brachio":
        img, ax, ay = build_brachio(ph, sc, hz, a, idle)
    elif kind == "tric":
        img, ax, ay = build_tric(ph, sc, hz, a, idle)
    else:
        img, ax, ay = build_mammal(ph, sc, hz)
    if flip:
        img = ImageOps.mirror(img)
        ax = img.width - ax
    return img, ax, ay


def put_actor(img, kind, x, y, sc, t, flip=False, ph0=0.0, cyc=1.4, hz=None, a=0.0, idle=False, shadow=True):
    hzq = None
    if hz:
        hzq = (hz[0], hz[1], hz[2], round(hz[3] * 8) / 8)
    scq = round(sc * 20) / 20
    ph = int(((t / cyc + ph0) % 1) * 12)
    spr, ax, ay = get_sprite(kind, ph, scq, hzq, flip, round(a * 5) / 5 if a else 0.0, idle)
    if shadow:
        sw = spr.width * .55
        sh = Image.new("RGBA", (int(sw * 2.2), int(sw * .5)), (0, 0, 0, 0))
        ImageDraw.Draw(sh).ellipse((0, 0, sh.width - 1, sh.height - 1), fill=(10, 8, 6, 90))
        sh = sh.filter(ImageFilter.GaussianBlur(4))
        img.paste(sh, (int(x - sh.width / 2), int(y - sh.height / 2 + 2)), sh)
    img.paste(spr, (int(x - ax), int(y - ay)), spr)
    return spr, ax, ay


# --------------------------------------------------------------- pteranodon, roca
def draw_ptero(d, x, y, s, t, col, flip=False):
    """Pteranodon plano. d: ImageDraw sobre RGBA."""
    c = math.sin(t * 7.0)
    sg = -1 if flip else 1
    def P(px, py):
        return (x + sg * px * s, y + py * s)
    d.polygon([P(*p) for p in ell(0, 0, 26, 8, 14)], fill=col)
    d.polygon([P(24, -3), P(78, 2), P(24, 4)], fill=col)          # pico
    d.polygon([P(18, -5), P(-6, -22), P(8, -2)], fill=col)        # cresta
    d.polygon([P(-22, 0), P(-48, 6), P(-26, 4)], fill=col)        # cola
    wing = [P(8, -4), P(-6, -70 * c - 8), P(-18, -112 * c - 14), P(-62, -78 * c + 4), P(-44, -36 * c + 8), P(-30, 4)]
    d.polygon(wing, fill=col)
    wing2 = [P(4, 2), P(-14, 40 * c + 6), P(-30, 60 * c + 8), P(-48, 26 * c + 8), P(-26, 8)]
    d.polygon(wing2, fill=tuple(int(v * .8) for v in col[:3]) + (col[3],))


@functools.lru_cache(maxsize=4)
def rock_sprite(size, seed=3):
    rnd = random.Random(seed)
    R = size / 2
    pts = []
    n = 26
    for i in range(n):
        a = TAU * i / n
        rr = R * rnd.uniform(.78, 1.0) * (1 + .1 * math.sin(a * 3 + 1))
        pts.append((R + math.cos(a) * rr * .96, R + math.sin(a) * rr * .96))
    mk = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mk).polygon(pts, fill=255)
    base = Image.new("RGB", (size, size))
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    light = np.clip(1.0 - (np.sqrt((xx - R * .55) ** 2 + (yy - R * .45) ** 2) / (R * 1.5)), 0, 1)
    col = np.zeros((size, size, 3), np.float32)
    for c, (dark, bright) in enumerate(((38, 150), (30, 124), (28, 110))):
        col[..., c] = dark + (bright - dark) * light
    base = Image.fromarray(col.astype(np.uint8), "RGB")
    d = ImageDraw.Draw(base)
    for _ in range(14):
        cx, cy = R + rnd.uniform(-R * .75, R * .75), R + rnd.uniform(-R * .75, R * .75)
        r = rnd.uniform(R * .06, R * .18)
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(26, 20, 20))
        d.ellipse((cx - r * .8, cy - r * .7, cx + r * .8, cy + r * .9), fill=(58, 46, 42))
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(base, (0, 0), mk)
    return out
