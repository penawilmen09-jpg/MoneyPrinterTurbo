"""Mini motor 2D vectorial (PIL + numpy) para historias animadas verticales.

Independiente del resto del proyecto. Todo se dibuja con supersampling (S=2)
usando una pila de transformaciones, lo que permite esqueletos articulados.
"""
import math
import random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageOps

W, H, FPS, S = 1080, 1920, 24, 2
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
_fc = {}


def font(sz, bold=True):
    k = (int(sz), bold)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(FONT_B if bold else FONT_R, int(sz))
    return _fc[k]


def lerp(a, b, u):
    return a + (b - a) * u


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease(u):
    u = clamp(u)
    return u * u * (3 - 2 * u)


def mix(c1, c2, u):
    return tuple(int(lerp(a, b, u)) for a, b in zip(c1, c2))


class Cv:
    """Lienzo con matrices anidadas. Coordenadas lógicas (1080x1920)."""

    def __init__(self, w=W, h=H, base=None, ss=S):
        self.w, self.h, self.S = w, h, ss
        self.im = base if base is not None else Image.new("RGB", (w * ss, h * ss), (0, 0, 0))
        self.d = ImageDraw.Draw(self.im, "RGBA")
        self.M = [(1.0, 0.0, 0.0, 1.0, 0.0, 0.0)]

    # --- transformaciones -------------------------------------------------
    def push(self, tx=0, ty=0, k=1.0, rot=0.0):
        a, b, c, d, e, f = self.M[-1]
        cs, sn = math.cos(rot) * k, math.sin(rot) * k
        # local: x' = cs*x - sn*y + tx ; y' = sn*x + cs*y + ty
        na = a * cs + c * sn
        nb = b * cs + d * sn
        nc = -a * sn + c * cs
        nd = -b * sn + d * cs
        ne = a * tx + c * ty + e
        nf = b * tx + d * ty + f
        self.M.append((na, nb, nc, nd, ne, nf))
        return self

    def pop(self):
        self.M.pop()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.pop()

    def pt(self, x, y):
        a, b, c, d, e, f = self.M[-1]
        return ((a * x + c * y + e) * self.S, (b * x + d * y + f) * self.S)

    def sc(self):
        a, b = self.M[-1][0], self.M[-1][1]
        return math.hypot(a, b) * self.S

    # --- primitivas --------------------------------------------------------
    def poly(self, pts, fill):
        self.d.polygon([self.pt(x, y) for x, y in pts], fill=fill)

    def ell(self, cx, cy, rx, ry, fill, n=44):
        pts = [(cx + rx * math.cos(2 * math.pi * i / n), cy + ry * math.sin(2 * math.pi * i / n)) for i in range(n)]
        self.poly(pts, fill)

    def rr(self, x0, y0, x1, y1, r, fill, n=7):
        r = min(r, (x1 - x0) / 2, (y1 - y0) / 2)
        pts = []
        for (cx, cy, a0) in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
            for i in range(n + 1):
                a = math.radians(a0 + 90 * i / n)
                pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        self.poly(pts, fill)

    def line(self, pts, w, fill, cap=True):
        P = [self.pt(x, y) for x, y in pts]
        ww = max(1, int(w * self.sc()))
        self.d.line(P, fill=fill, width=ww, joint="curve")
        if cap:
            r = ww / 2
            for (x, y) in (P[0], P[-1]):
                self.d.ellipse([x - r, y - r, x + r, y + r], fill=fill)

    def limb(self, p0, p1, w0, w1, fill):
        (x0, y0), (x1, y1) = p0, p1
        dx, dy = x1 - x0, y1 - y0
        L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L, dx / L
        self.poly([(x0 + nx * w0 / 2, y0 + ny * w0 / 2), (x1 + nx * w1 / 2, y1 + ny * w1 / 2),
                   (x1 - nx * w1 / 2, y1 - ny * w1 / 2), (x0 - nx * w0 / 2, y0 - ny * w0 / 2)], fill)
        self.ell(x0, y0, w0 / 2, w0 / 2, fill, 24)
        self.ell(x1, y1, w1 / 2, w1 / 2, fill, 24)

    def text(self, x, y, txt, size, fill, bold=True, anchor="mm", stroke=0, stroke_fill=(0, 0, 0)):
        px, py = self.pt(x, y)
        f = font(size * self.sc(), bold)
        self.d.text((px, py), txt, font=f, fill=fill, anchor=anchor,
                    stroke_width=int(stroke * self.sc()), stroke_fill=stroke_fill)

    def small(self):
        return self.im.reduce(self.S)


# --- luz aditiva (coordenadas de pantalla) ----------------------------------
_grad = Image.radial_gradient("L")  # 0 centro -> 255 borde


def add_light(img, cx, cy, r, color, strength=1.0, power=2.0):
    r = int(r)
    if r < 4 or strength <= 0:
        return
    x0, y0 = int(cx - r), int(cy - r)
    box = (max(0, x0), max(0, y0), min(img.width, x0 + 2 * r), min(img.height, y0 + 2 * r))
    if box[2] <= box[0] or box[3] <= box[1]:
        return
    m = ImageOps.invert(_grad).resize((2 * r, 2 * r), Image.BILINEAR)
    lut = [int(255 * ((v / 255.0) ** power) * min(1.0, strength)) for v in range(256)]
    m = m.point(lut)
    layer = Image.new("RGB", (2 * r, 2 * r), color)
    black = Image.new("RGB", (2 * r, 2 * r), (0, 0, 0))
    glow = Image.composite(layer, black, m)
    sx, sy = box[0] - x0, box[1] - y0
    glow = glow.crop((sx, sy, sx + box[2] - box[0], sy + box[3] - box[1]))
    region = img.crop(box)
    img.paste(ImageChops.add(region, glow), box)


def tint_layer(layer, cx, cy, r, color, strength=0.6):
    """Ilumina un sprite RGBA (solo donde hay alpha), coordenadas del sprite."""
    rgb = layer.convert("RGB")
    a = layer.getchannel("A")
    tmp = Image.new("RGB", rgb.size, (0, 0, 0))
    add_light(tmp, cx, cy, r, color, strength, 1.6)
    out = ImageChops.add(rgb, tmp)
    out.putalpha(a)
    return out


# --- fondo con degradado -----------------------------------------------------
def vgrad(w, h, stops):
    """stops: [(pos 0..1, (r,g,b)), ...]"""
    ys = np.linspace(0, 1, h)
    arr = np.zeros((h, w, 3), np.uint8)
    for ch in range(3):
        xs = [p for p, _ in stops]
        vs = [c[ch] for _, c in stops]
        arr[:, :, ch] = np.interp(ys, xs, vs)[:, None]
    return Image.fromarray(arr, "RGB")


# --- posproceso ------------------------------------------------------------
_vig = None
_grain = None


def postfx(img, fi):
    global _vig, _grain
    if _vig is None:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        d = np.sqrt(((xx - W / 2) / (W * 0.72)) ** 2 + ((yy - H / 2) / (H * 0.68)) ** 2)
        _vig = np.clip(1.08 - 0.62 * d ** 2.2, 0.28, 1.0)[:, :, None].astype(np.float32)
        rng = np.random.default_rng(7)
        _grain = [rng.normal(0, 4.2, (H // 2, W // 2)).astype(np.float32) for _ in range(6)]
    a = np.asarray(img, np.float32) * _vig
    g = _grain[fi % 6]
    g = np.kron(g, np.ones((2, 2), np.float32))[:H, :W, None]
    a = a + g
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")
