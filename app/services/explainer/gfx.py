"""2D drawing helpers shared by all explainer scenes (Pillow + numpy only)."""

from __future__ import annotations

import math
import os
import random
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from app.utils import utils

W, H = 1080, 1920

# --- Explora Ciencia 360 palette -------------------------------------------
BG_TOP = (9, 14, 32)
BG_BOTTOM = (17, 30, 66)
GRID = (36, 56, 106)
TEXT = (242, 246, 255)
MUTED = (150, 168, 205)
CYAN = (61, 217, 245)
AMBER = (255, 181, 71)
CORAL = (255, 93, 115)
MINT = (92, 242, 179)
VIOLET = (139, 123, 255)
STEEL_L = (160, 178, 208)
STEEL_M = (104, 124, 160)
STEEL_D = (58, 74, 110)
ACCENTS = [CYAN, AMBER, MINT, CORAL, VIOLET]

# Vertical safe zones (platform UI covers the top ~230px and bottom ~330px).
VIZ_TOP, VIZ_BOTTOM = 330, 1290
CAPTION_TOP, CAPTION_BOTTOM = 1330, 1570


def clamp(x: float, a: float = 0.0, b: float = 1.0) -> float:
    return a if x < a else b if x > b else x


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_color(c0, c1, t):
    t = clamp(t)
    return tuple(int(round(lerp(c0[i], c1[i], t))) for i in range(3))


def seg(t: float, a: float, b: float) -> float:
    """Progress of ``t`` through the window [a, b] clamped to 0..1."""
    if b <= a:
        return 1.0 if t >= b else 0.0
    return clamp((t - a) / (b - a))


def ease_out(t: float) -> float:
    t = clamp(t)
    return 1 - (1 - t) ** 3


def ease_in_out(t: float) -> float:
    t = clamp(t)
    return t * t * (3 - 2 * t)


def ease_out_back(t: float) -> float:
    t = clamp(t)
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


@lru_cache(maxsize=32)
def font(weight: str, size: int) -> ImageFont.FreeTypeFont:
    name = "BeVietnamPro-Bold.ttf" if weight == "bold" else "BeVietnamPro-Medium.ttf"
    return ImageFont.truetype(os.path.join(utils.font_dir(), name), size)


def text_size(text: str, fnt) -> tuple[int, int]:
    l, t, r, b = fnt.getbbox(text)
    return r - l, b - t


@lru_cache(maxsize=1)
def _background() -> Image.Image:
    ys = np.linspace(0, 1, H)[:, None, None]
    top = np.array(BG_TOP, dtype=np.float32)[None, None, :]
    bot = np.array(BG_BOTTOM, dtype=np.float32)[None, None, :]
    grad = top + (bot - top) * ys
    grad = np.repeat(grad, W, axis=1)
    # Soft radial glow behind the visual area gives the scene depth.
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - 820) / (H * 0.38)) ** 2)
    glow = np.clip(1 - d, 0, 1) ** 2 * 26
    grad = grad + glow[:, :, None] * np.array([0.35, 0.8, 1.0], dtype=np.float32)
    vig = 1 - 0.28 * np.clip(((yy - H / 2) / (H / 2)) ** 2 + ((xx - W / 2) / (W / 2)) ** 2 - 0.35, 0, 1)
    grad = grad * vig[:, :, None]
    return Image.fromarray(np.clip(grad, 0, 255).astype(np.uint8), "RGB")


def new_frame(t: float, seed: int = 0, grid: bool = True) -> Image.Image:
    """Animated blueprint-style backdrop: gradient + drifting grid + dust."""
    img = _background().copy()
    over = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(over)
    if grid:
        step = 90
        off = (t * 14) % step
        for x in range(-step, W + step, step):
            xx = x + off * 0.6
            d.line([(xx, VIZ_TOP - 40), (xx, VIZ_BOTTOM + 40)], fill=(*GRID, 46), width=1)
        for y in range(VIZ_TOP - 40, VIZ_BOTTOM + 60, step):
            yy = y + off * 0.3
            d.line([(0, yy), (W, yy)], fill=(*GRID, 46), width=1)
    rnd = random.Random(1000 + seed)
    for i in range(34):
        x0, y0 = rnd.uniform(0, W), rnd.uniform(0, H)
        sp = rnd.uniform(6, 26)
        r = rnd.uniform(1.2, 3.2)
        x = (x0 + math.sin(t * 0.4 + i) * 14) % W
        y = (y0 - t * sp) % H
        d.ellipse([x - r, y - r, x + r, y + r], fill=(180, 220, 255, int(rnd.uniform(30, 90))))
    img.paste(over, (0, 0), over)
    return img


def alpha_paste(base: Image.Image, layer: Image.Image, xy=(0, 0), opacity: float = 1.0):
    if opacity < 1.0:
        a = layer.getchannel("A").point(lambda v: int(v * opacity))
        layer = layer.copy()
        layer.putalpha(a)
    base.paste(layer, xy, layer)


def rounded_panel(draw: ImageDraw.ImageDraw, box, radius=28, fill=(10, 18, 40, 200), outline=None, width=2):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def text_center(draw, xy, text, fnt, fill=TEXT, stroke=0, stroke_fill=(0, 0, 0, 255), anchor="mm"):
    draw.text(xy, text, font=fnt, fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=stroke_fill)


def glow(layer: Image.Image, xy, radius, color, strength=1.0):
    """Cheap radial glow built from stacked translucent discs."""
    d = ImageDraw.Draw(layer, "RGBA")
    x, y = xy
    steps = 9
    for i in range(steps, 0, -1):
        r = radius * i / steps
        a = int(clamp(strength * 255 * (1 - i / (steps + 1)) ** 2 * 0.55, 0, 255))
        d.ellipse([x - r, y - r, x + r, y + r], fill=(*color, a))


def arrow(draw, p0, p1, color=CYAN, width=8, head=26, alpha=255, dash_phase: float | None = None):
    x0, y0 = p0
    x1, y1 = p1
    ang = math.atan2(y1 - y0, x1 - x0)
    length = math.hypot(x1 - x0, y1 - y0)
    if length < 4:
        return
    hx, hy = x1 - math.cos(ang) * head * 0.8, y1 - math.sin(ang) * head * 0.8
    col = (*color, alpha)
    if dash_phase is None:
        draw.line([p0, (hx, hy)], fill=col, width=width)
    else:
        dash, gap = 26.0, 16.0
        pos = -(dash_phase % (dash + gap))
        n = math.hypot(hx - x0, hy - y0)
        while pos < n:
            a, b = max(pos, 0.0), min(pos + dash, n)
            if b > a:
                ux, uy = (hx - x0) / n, (hy - y0) / n
                draw.line([(x0 + ux * a, y0 + uy * a), (x0 + ux * b, y0 + uy * b)], fill=col, width=width)
            pos += dash + gap
    left = (x1 - head * math.cos(ang - 0.42), y1 - head * math.sin(ang - 0.42))
    right = (x1 - head * math.cos(ang + 0.42), y1 - head * math.sin(ang + 0.42))
    draw.polygon([p1, left, right], fill=col)


def callout(img: Image.Image, text: str, anchor_xy, label_xy, t_in: float, t: float,
            color=CYAN, size=40):
    """Animated label pill with a leader line to ``anchor_xy``."""
    p = ease_out(seg(t, t_in, t_in + 0.45))
    if p <= 0:
        return
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer, "RGBA")
    fnt = font("bold", size)
    tw, th = text_size(text, fnt)
    pad = 22
    lx, ly = label_xy
    lx = clamp(lx, tw / 2 + pad + 30, W - tw / 2 - pad - 30)
    ax, ay = anchor_xy
    ex, ey = lerp(lx, ax, p), lerp(ly, ay, p)
    d.line([(lx, ly), (ex, ey)], fill=(*color, int(230 * p)), width=4)
    d.ellipse([ex - 9, ey - 9, ex + 9, ey + 9], fill=(*color, int(255 * p)))
    box = [lx - tw / 2 - pad, ly - th / 2 - pad * 0.7, lx + tw / 2 + pad, ly + th / 2 + pad * 0.7]
    d.rounded_rectangle(box, radius=22, fill=(8, 14, 34, int(225 * p)), outline=(*color, int(255 * p)), width=3)
    d.text((lx, ly), text, font=fnt, fill=(*TEXT, int(255 * p)), anchor="mm")
    img.paste(layer, (0, 0), layer)


def brand_tag(img: Image.Image, t: float):
    d = ImageDraw.Draw(img, "RGBA")
    cx, cy = 96, 150
    d.ellipse([cx - 24, cy - 24, cx + 24, cy + 24], outline=(*CYAN, 255), width=4)
    ang = t * 1.6
    d.ellipse([cx + math.cos(ang) * 24 - 6, cy + math.sin(ang) * 24 - 6,
               cx + math.cos(ang) * 24 + 6, cy + math.sin(ang) * 24 + 6], fill=(*AMBER, 255))
    d.text((cx + 44, cy - 2), "EXPLORA CIENCIA 360", font=font("bold", 30), fill=(*TEXT, 235), anchor="lm")


def step_header(img: Image.Image, index: int, title: str, t: float, accent=CYAN):
    """'01  TITULO' headline that slides in at the top of the visual zone."""
    p = ease_out(seg(t, 0.15, 0.7))
    if p <= 0 or not title:
        return
    layer = Image.new("RGBA", (W, 160), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer, "RGBA")
    fnt = font("bold", 56)
    tw, _ = text_size(title.upper(), fnt)
    bw = tw + 150
    x0 = (W - bw) / 2
    d.rounded_rectangle([x0, 30, x0 + bw, 130], radius=50, fill=(8, 14, 34, 215), outline=(*accent, 255), width=3)
    d.ellipse([x0 + 14, 42, x0 + 90, 118], fill=(*accent, 255))
    d.text((x0 + 52, 80), f"{index:02d}", font=font("bold", 36), fill=(8, 14, 34, 255), anchor="mm")
    d.text((x0 + 108, 80), title.upper(), font=fnt, fill=(*TEXT, 255), anchor="lm")
    alpha_paste(img, layer, (0, int(VIZ_TOP - 120 - (1 - p) * 40)), p)


def dust_particles(layer: Image.Image, path_pts, t, n, color, speed=0.35, size=9, seed=1, spread=10):
    """Particles flowing along a polyline in 2D screen space."""
    if len(path_pts) < 2:
        return
    d = ImageDraw.Draw(layer, "RGBA")
    seglens = [math.dist(path_pts[i], path_pts[i + 1]) for i in range(len(path_pts) - 1)]
    total = sum(seglens) or 1.0
    rnd = random.Random(seed)
    for i in range(n):
        u = (i / n + t * speed + rnd.random() * 0.05) % 1.0
        dist = u * total
        acc = 0.0
        for k, sl in enumerate(seglens):
            if acc + sl >= dist:
                f = (dist - acc) / (sl or 1)
                x = lerp(path_pts[k][0], path_pts[k + 1][0], f) + rnd.uniform(-spread, spread)
                y = lerp(path_pts[k][1], path_pts[k + 1][1], f) + rnd.uniform(-spread, spread)
                break
            acc += sl
        else:
            continue
        fade = math.sin(u * math.pi)
        r = size * (0.6 + 0.6 * rnd.random())
        d.ellipse([x - r, y - r, x + r, y + r], fill=(*color, int(220 * fade)))
