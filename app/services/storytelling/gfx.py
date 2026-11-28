"""Utilidades de dibujo: lienzo con escala, degradados, fuentes y capas AA."""

from __future__ import annotations

import math
import os
import random
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

Color = tuple[int, int, int]

_FONT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    "resource", "fonts",
)
_FALLBACKS = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
)


@lru_cache(maxsize=64)
def font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    name = "BeVietnamPro-Bold.ttf" if bold else "BeVietnamPro-Medium.ttf"
    candidates = [os.path.join(_FONT_DIR, name), *_FALLBACKS]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, max(6, int(size)))
            except OSError:
                continue
    return ImageFont.load_default()


def shade(c: Color, f: float) -> Color:
    return tuple(max(0, min(255, int(v * f))) for v in c)  # type: ignore[return-value]


def mix(a: Color, b: Color, t: float) -> Color:
    return tuple(int(a[i] * (1 - t) + b[i] * t) for i in range(3))  # type: ignore[return-value]


def ease(x: float) -> float:
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def ease_out_back(x: float) -> float:
    x = max(0.0, min(1.0, x))
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


class Canvas:
    """Lienzo que acepta coordenadas del 'mundo' (1080x1920) y las escala por K."""

    def __init__(self, w: int, h: int, k: float, mode="RGB", bg=(255, 255, 255)):
        self.k = k
        self.img = Image.new(mode, (int(w * k), int(h * k)), bg)
        self.d = ImageDraw.Draw(self.img, "RGBA" if mode == "RGB" else mode)
        self.w, self.h = w, h

    # coordenadas
    def _b(self, x0, y0, x1, y1):
        return [x0 * self.k, y0 * self.k, x1 * self.k, y1 * self.k]

    def rect(self, x0, y0, x1, y1, fill=None, outline=None, width=0):
        self.d.rectangle(self._b(x0, y0, x1, y1), fill=fill, outline=outline, width=int(width * self.k))

    def rrect(self, x0, y0, x1, y1, r, fill=None, outline=None, width=0):
        self.d.rounded_rectangle(self._b(x0, y0, x1, y1), radius=r * self.k, fill=fill,
                                 outline=outline, width=int(width * self.k))

    def ellipse(self, cx, cy, rx, ry, fill=None, outline=None, width=0):
        self.d.ellipse(self._b(cx - rx, cy - ry, cx + rx, cy + ry), fill=fill, outline=outline, width=int(width * self.k))

    def poly(self, pts, fill=None, outline=None, width=2):
        P = [(x * self.k, y * self.k) for x, y in pts]
        self.d.polygon(P, fill=fill)
        if outline:
            self.d.line(P + [P[0]], fill=outline, width=max(1, int(width * self.k)))

    def line(self, pts, fill, width=2):
        P = [(x * self.k, y * self.k) for x, y in pts]
        self.d.line(P, fill=fill, width=max(1, int(width * self.k)))

    def text(self, x, y, s, size, fill, anchor="mm", bold=True, stroke=0, stroke_fill=None):
        self.d.text((x * self.k, y * self.k), s, font=font(size * self.k, bold), fill=fill, anchor=anchor,
                    stroke_width=int(stroke * self.k), stroke_fill=stroke_fill)

    def gradient_v(self, x0, y0, x1, y1, c0: Color, c1: Color):
        w, h = int((x1 - x0) * self.k), int((y1 - y0) * self.k)
        if w <= 0 or h <= 0:
            return
        t = np.linspace(0, 1, h)[:, None, None]
        arr = (np.array(c0)[None, None, :] * (1 - t) + np.array(c1)[None, None, :] * t)
        arr = np.repeat(arr, w, axis=1).astype(np.uint8)
        self.img.paste(Image.fromarray(arr, "RGB"), (int(x0 * self.k), int(y0 * self.k)))

    def glow(self, cx, cy, r, color: Color, alpha=120):
        """Halo radial suave."""
        size = int(2 * r * self.k)
        if size < 4:
            return
        yy, xx = np.mgrid[0:size, 0:size]
        dist = np.sqrt((xx - size / 2) ** 2 + (yy - size / 2) ** 2) / (size / 2)
        a = np.clip(1 - dist, 0, 1) ** 2 * alpha
        layer = Image.new("RGBA", (size, size), color + (0,))
        layer.putalpha(Image.fromarray(a.astype(np.uint8), "L"))
        x, y = int(cx * self.k - size / 2), int(cy * self.k - size / 2)
        if self.img.mode == "RGBA":
            self.img.alpha_composite(layer, (max(0, x), max(0, y))) if x >= 0 and y >= 0 else self.img.paste(layer, (x, y), layer)
        else:
            self.img.paste(layer.convert("RGB"), (x, y), layer.split()[3])

    def finish(self, out_w: int, out_h: int) -> Image.Image:
        return self.img.resize((out_w, out_h), Image.LANCZOS)


def aa_layer(size: tuple[int, int], draw_fn, ss: int = 2) -> Image.Image:
    """Crea una capa RGBA suavizada: ``draw_fn(draw, ss)`` dibuja a escala ss."""
    w, h = size
    layer = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(layer), ss)
    return layer.resize((w, h), Image.LANCZOS) if ss > 1 else layer


def vignette(w: int, h: int, strength: float = 0.35) -> Image.Image:
    """Capa RGBA negra con bordes oscuros (profundidad)."""
    yy, xx = np.mgrid[0:h, 0:w]
    dx = (xx - w / 2) / (w / 2)
    dy = (yy - h / 2) / (h / 2)
    d = np.clip(np.sqrt(dx * dx * 0.9 + dy * dy * 0.7) - 0.55, 0, 1)
    a = (d ** 1.6 * 255 * strength * 1.6).clip(0, 200).astype(np.uint8)
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    layer.putalpha(Image.fromarray(a, "L"))
    return layer


PALETTE = [
    (232, 72, 60), (245, 160, 50), (250, 214, 72), (96, 184, 96), (64, 168, 200),
    (70, 110, 210), (150, 90, 190), (236, 110, 160), (240, 240, 235), (140, 90, 60),
]


def products_row(c: Canvas, x0, x1, y_bottom, h, seed, density=1.0):
    """Fila de productos (cajas, latas, botellas) sobre un estante."""
    rng = random.Random(seed)
    x = x0 + 4
    while x < x1 - 10:
        kind = rng.choice(("box", "can", "bottle", "box", "bag"))
        col = rng.choice(PALETTE)
        pw = rng.randint(22, 44) * density
        ph = h * rng.uniform(0.62, 0.98)
        if x + pw > x1:
            break
        if kind == "box":
            c.rect(x, y_bottom - ph, x + pw, y_bottom, fill=col, outline=shade(col, 0.6), width=1.5)
            c.rect(x + 3, y_bottom - ph * 0.62, x + pw - 3, y_bottom - ph * 0.28, fill=(255, 255, 255, 215))
        elif kind == "can":
            c.rrect(x, y_bottom - ph * 0.8, x + pw * 0.8, y_bottom, 4, fill=col, outline=shade(col, 0.6), width=1.5)
            c.rect(x + 2, y_bottom - ph * 0.56, x + pw * 0.8 - 2, y_bottom - ph * 0.28, fill=(255, 255, 255, 200))
            x -= pw * 0.15
        elif kind == "bottle":
            c.rrect(x + pw * 0.15, y_bottom - ph * 0.7, x + pw * 0.85, y_bottom, 6, fill=col, outline=shade(col, 0.6), width=1.5)
            c.rect(x + pw * 0.38, y_bottom - ph, x + pw * 0.62, y_bottom - ph * 0.7, fill=shade(col, 0.85), outline=shade(col, 0.6), width=1.2)
        else:
            c.poly([(x, y_bottom), (x + pw, y_bottom), (x + pw * 0.92, y_bottom - ph * 0.9), (x + pw * 0.08, y_bottom - ph * 0.9)],
                   fill=col, outline=shade(col, 0.6), width=1.5)
        x += pw + rng.randint(2, 7)
