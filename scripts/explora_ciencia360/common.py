"""Motor 2D procedural (Pillow + numpy) — Explora Ciencia 360.
Todas las escenas son funciones puras f(t) -> frame RGB, así se renderizan en paralelo."""
import math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FONT_BOLD = os.path.join(ROOT, "resource", "fonts", "BeVietnamPro-Bold.ttf")
FONT_MED = os.path.join(ROOT, "resource", "fonts", "BeVietnamPro-Medium.ttf")

# Paleta
BG0 = (4, 6, 16)
BG1 = (10, 16, 42)
CYAN = (54, 214, 255)
BLUE = (60, 110, 255)
VIOLET = (150, 100, 255)
MAGENTA = (255, 90, 190)
AMBER = (255, 190, 70)
WHITE = (240, 248, 255)
RED = (255, 80, 80)

# Línea de tiempo (segundos) — definida a partir de la alineación real de la voz.
# (nombre, inicio, fin)
SCENES = [
    ("gancho", 0.0, 10.95),
    ("cerebro", 10.95, 20.00),
    ("completar", 20.00, 24.70),
    ("punto_ciego", 24.70, 35.85),
    ("ceguera", 35.85, 47.00),
    ("conclusion", 47.00, 55.25),
    ("marca", 55.25, 59.40),
]
TOTAL = SCENES[-1][2]
TRANS = 0.5  # duración de transiciones


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def prog(t, a, b):
    return clamp((t - a) / (b - a)) if b > a else (1.0 if t >= b else 0.0)


def ease(x):  # smoothstep
    x = clamp(x); return x * x * (3 - 2 * x)


def ease_out(x):
    x = clamp(x); return 1 - (1 - x) ** 3


def ease_in(x):
    x = clamp(x); return x ** 3


def ease_io(x):
    x = clamp(x)
    return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2


def ease_back(x):
    x = clamp(x); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def lerp(a, b, k):
    return a + (b - a) * k


def mix(c1, c2, k):
    return tuple(lerp(a, b, k) for a, b in zip(c1, c2))


def sc(color, k):
    return tuple(int(clamp(c * k, 0, 255)) for c in color)


_fonts = {}
def font(size, bold=True):
    key = (size, bold)
    if key not in _fonts:
        _fonts[key] = ImageFont.truetype(FONT_BOLD if bold else FONT_MED, size)
    return _fonts[key]


# ---------- fondo ----------
_bg_cache = {}
def _bg_base():
    if "b" not in _bg_cache:
        y, x = np.mgrid[0:H, 0:W].astype(np.float32)
        d = np.sqrt(((x - W / 2) / (W * 0.75)) ** 2 + ((y - H * 0.42) / (H * 0.62)) ** 2)
        k = np.clip(1 - d, 0, 1) ** 1.4
        c0 = np.array(BG0, np.float32); c1 = np.array(BG1, np.float32)
        base = c0[None, None, :] * (1 - k[..., None]) + c1[None, None, :] * k[..., None]
        vig = np.clip(1.0 - 0.35 * (d ** 2.0), 0.55, 1)
        _bg_cache["b"] = (base * vig[..., None]).astype(np.float32)
        rng = np.random.RandomState(7)
        _bg_cache["noise"] = rng.randn(H // 2, W // 2).astype(np.float32)
    return _bg_cache["b"]


def particles(frame_light, t, seed=1, n=70, tint=CYAN, speed=14.0, depth_blur=True, alpha=1.0):
    """Partículas flotantes con paralaje (polvo luminoso)."""
    rng = np.random.RandomState(seed)
    dr = frame_light
    for i in range(n):
        x0 = rng.rand() * W; y0 = rng.rand() * H
        z = 0.3 + rng.rand() * 1.2
        ph = rng.rand() * 6.28
        x = (x0 + math.sin(t * 0.4 + ph) * 25 * z) % W
        y = (y0 - t * speed * z) % H
        r = 1.2 + 2.6 * z * rng.rand()
        tw = 0.55 + 0.45 * math.sin(t * 2 + ph * 3)
        c = sc(tint, 0.55 * tw * alpha * (0.4 + z * 0.6))
        dr.ellipse([x - r, y - r, x + r, y + r], fill=c)


class Frame:
    """Superficie sólida + superficie de luz aditiva (con resplandor)."""
    def __init__(self, bg=True):
        base = _bg_base()
        self.base = base.copy() if bg else np.zeros((H, W, 3), np.float32)
        self.solid = None  # PIL RGBA opcional (se crea bajo demanda)
        self.light = Image.new("RGB", (W, H), (0, 0, 0))
        self.L = ImageDraw.Draw(self.light)
        self.glows = []  # (imagen, radio, ganancia)
        self._layers = []

    def new_layer(self):
        im = Image.new("RGB", (W, H), (0, 0, 0))
        return im, ImageDraw.Draw(im)

    def add_glow_layer(self, im, radius=14, gain=1.0, soft=True, raw=True):
        self.glows.append((im, radius, gain, soft, raw))

    def add_np(self, arr, gain=1.0):
        self.base += arr * gain

    def paste_rgba(self, im_rgba, xy):
        """Composición alfa sobre la base."""
        x, y = int(xy[0]), int(xy[1])
        a = np.asarray(im_rgba, np.float32)
        h, w = a.shape[:2]
        x0, y0 = max(x, 0), max(y, 0); x1, y1 = min(x + w, W), min(y + h, H)
        if x1 <= x0 or y1 <= y0:
            return
        sub = a[y0 - y:y1 - y, x0 - x:x1 - x]
        al = sub[..., 3:4] / 255.0
        self.base[y0:y1, x0:x1] = self.base[y0:y1, x0:x1] * (1 - al) + sub[..., :3] * al

    def finish(self):
        out = self.base
        out = out + np.asarray(self.light, np.float32)
        layers = [(self.light, 16, 0.9, True, False)] + self.glows
        for im, radius, gain, soft, raw in layers:
            small = im.resize((W // 4, H // 4), Image.BOX)
            if radius > 0:
                small = small.filter(ImageFilter.GaussianBlur(max(radius / 4.0, 0.5)))
            g = np.asarray(small.resize((W, H), Image.BILINEAR), np.float32)
            out = out + g * gain
            if soft:
                small2 = im.resize((W // 8, H // 8), Image.BOX).filter(ImageFilter.GaussianBlur(max(radius / 2.0, 1)))
                g2 = np.asarray(small2.resize((W, H), Image.BILINEAR), np.float32)
                out = out + g2 * gain * 0.55
        for im, radius, gain, soft, raw in self.glows:
            if raw:
                out = out + np.asarray(im, np.float32)
        return out


def to_uint8(arr):
    return np.clip(arr, 0, 255).astype(np.uint8)


class Cam:
    """Cámara 2D: zoom + paneo + rotación sobre coordenadas de mundo."""
    def __init__(self, cx=W / 2, cy=H / 2, zoom=1.0, rot=0.0, sx=W / 2, sy=H / 2):
        self.cx, self.cy, self.z, self.rot, self.sx, self.sy = cx, cy, zoom, rot, sx, sy
        self.c, self.s = math.cos(rot), math.sin(rot)

    def p(self, x, y, depth=1.0):
        dx, dy = (x - self.cx), (y - self.cy)
        z = self.z ** depth
        rx = (dx * self.c - dy * self.s) * z
        ry = (dx * self.s + dy * self.c) * z
        return self.sx + rx, self.sy + ry

    def r(self, r, depth=1.0):
        return r * (self.z ** depth)


def blur_np(arr, k):
    """Desenfoque rápido en numpy→PIL (por canal en resolución reducida)."""
    im = Image.fromarray(to_uint8(arr))
    s = max(int(k), 1)
    small = im.resize((W // 2, H // 2), Image.BOX).filter(ImageFilter.GaussianBlur(s / 2))
    return np.asarray(small.resize((W, H), Image.BILINEAR), np.float32)


def grain(arr, t, amount=3.0):
    _bg_base()
    rng = np.random.RandomState(int(t * 30) % 97 + 1)
    n = rng.randn(H // 2, W // 2).astype(np.float32)
    n = np.repeat(np.repeat(n, 2, 0), 2, 1)
    return arr + n[..., None] * amount
