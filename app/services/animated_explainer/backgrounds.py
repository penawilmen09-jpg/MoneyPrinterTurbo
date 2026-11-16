"""Escenarios 2D por capas (fondo / medio / primer plano) dibujados con Pillow."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .characters import _P, shade

W, H = 1080, 1920
SS = 2
FONT_PATH = str(Path(__file__).resolve().parents[3] / "resource" / "fonts" / "BeVietnamPro-Bold.ttf")


@dataclass
class Backdrop:
    bg: Image.Image                      # RGB W×H
    fg: Image.Image | None = None        # RGBA, se dibuja sobre los personajes
    mid: Image.Image | None = None       # RGBA, entre personajes "de ventana" y los demás
    window: tuple[int, int, int, int] | None = None  # recorte para personajes pequeños
    props: dict | None = None            # coordenadas útiles (reloj, puerta...)


def font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_PATH, size)


def gradient(w: int, h: int, top, bottom) -> Image.Image:
    t = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
    a = np.array(top, np.float32)[None, None, :]
    b = np.array(bottom, np.float32)[None, None, :]
    arr = (a + (b - a) * t) * np.ones((1, w, 1), np.float32)
    return Image.fromarray(arr.astype(np.uint8), "RGB")


def _canvas(top, bottom):
    img = gradient(W * SS, H * SS, top, bottom).convert("RGBA")
    return img, _P(img, 0, 0, SS)


def _finish(img: Image.Image, mode: str = "RGB") -> Image.Image:
    out = img.resize((W, H), Image.LANCZOS)
    return out.convert(mode)


def _layer():
    img = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    return img, _P(img, 0, 0, SS)


OL = (30, 28, 40, 255)


def _rrect(g: _P, x0, y0, x1, y1, r, fill, outline=None, w=3):
    g.d.rounded_rectangle([*g.pt(x0, y0), *g.pt(x1, y1)], radius=r * SS, fill=fill,
                          outline=outline, width=int(w * SS) if outline else 0)


def _text(g: _P, xy, text, size, fill, anchor="mm", stroke=0, stroke_fill=(0, 0, 0, 255)):
    g.d.text(g.pt(*xy), text, font=font(int(size * SS)), fill=fill, anchor=anchor,
             stroke_width=int(stroke * SS), stroke_fill=stroke_fill)


def car(g: _P, cx, base_y, w, color, flip=False):
    """Sedán estilizado de perfil. cx,base_y: centro y suelo."""
    s = w / 560.0
    sgn = -1 if flip else 1

    def pts(lst):
        return [(cx + sgn * x * s, base_y + y * s) for x, y in lst]

    body = pts([(-270, -40), (-262, -92), (-190, -108), (-120, -176), (60, -184), (150, -112),
                (250, -96), (276, -52), (270, -30), (-270, -30)])
    g.poly(body, color, OL, 4)
    g.poly(pts([(-108, -166), (-60, -166), (-60, -112), (-180, -112)]), (170, 215, 240, 255), OL, 3)
    g.poly(pts([(-48, -166), (50, -168), (118, -112), (-48, -112)]), (170, 215, 240, 255), OL, 3)
    g.poly(pts([(-270, -62), (270, -62), (270, -48), (-270, -48)]), shade_rgba(color, 0.78))
    for wx in (-165, 165):
        g.ell(cx + sgn * wx * s, base_y - 22 * s, 48 * s, 48 * s, (28, 28, 34, 255), OL, 3)
        g.ell(cx + sgn * wx * s, base_y - 22 * s, 26 * s, 26 * s, (190, 195, 205, 255), OL, 2)
        g.ell(cx + sgn * wx * s, base_y - 22 * s, 8 * s, 8 * s, (90, 95, 105, 255))
    g.ell(cx + sgn * 262 * s, base_y - 66 * s, 11 * s, 9 * s, (255, 236, 150, 255), OL, 2)
    g.ell(cx - sgn * 262 * s, base_y - 66 * s, 8 * s, 9 * s, (230, 60, 60, 255), OL, 2)


def shade_rgba(color, f):
    r, gg, b = color[:3]
    return (int(r * f), int(gg * f), int(b * f), 255)


def _reflection(img: Image.Image, y0: int, strength=0.22):
    """Refleja la franja superior sobre el suelo brillante."""
    h = img.height - y0
    src = img.crop((0, max(0, y0 - h), img.width, y0)).transpose(Image.FLIP_TOP_BOTTOM)
    mask = Image.linear_gradient("L").resize((img.width, src.height)).transpose(Image.FLIP_TOP_BOTTOM)
    mask = mask.point(lambda v: int(v * strength))
    img.paste(src.convert("RGB"), (0, y0), mask)


def _skyline(g: _P, x0, y0, x1, y1, seed=3, col=(120, 150, 190, 255)):
    rng = np.random.RandomState(seed)
    x = x0
    while x < x1:
        bw = int(rng.randint(50, 120))
        bh = int(rng.randint(80, max(120, (y1 - y0) - 20)))
        c = tuple(int(v * rng.uniform(0.82, 1.0)) for v in col[:3]) + (255,)
        g.d.rectangle([*g.pt(x, y1 - bh), *g.pt(min(x + bw, x1), y1)], fill=c)
        for wy in range(y1 - bh + 12, y1 - 8, 26):
            for wx in range(x + 8, min(x + bw, x1) - 14, 22):
                if rng.rand() > 0.55:
                    g.d.rectangle([*g.pt(wx, wy), *g.pt(wx + 9, wy + 12)], fill=(255, 245, 200, 255))
        x += bw + 4


def _plant(g: _P, x, y, s=1.0, leaf=(46, 150, 90, 255)):
    _rrect(g, x - 38 * s, y - 70 * s, x + 38 * s, y, 10 * s, (200, 120, 70, 255), OL, 3)
    for ang, ln in ((-60, 190), (-30, 230), (0, 250), (30, 230), (60, 190), (-80, 130), (80, 130)):
        a = math.radians(ang)
        tip = (x + math.sin(a) * ln * s, y - 70 * s - math.cos(a) * ln * s)
        mid = (x + math.sin(a) * ln * s * 0.5 + math.cos(a) * 26 * s,
               y - 70 * s - math.cos(a) * ln * s * 0.5 + math.sin(a) * 26 * s)
        mid2 = (x + math.sin(a) * ln * s * 0.5 - math.cos(a) * 26 * s,
                y - 70 * s - math.cos(a) * ln * s * 0.5 - math.sin(a) * 26 * s)
        g.poly([(x, y - 70 * s), mid, tip, mid2], leaf, OL, 3)


def _desk(g: _P, top_y, wood=(150, 96, 58), items=True, x0=-10):
    g.d.rectangle([*g.pt(x0, top_y), *g.pt(W, H)], fill=shade_rgba(wood, 0.72))
    g.d.rectangle([*g.pt(x0, top_y), *g.pt(W + 10, top_y + 34)], fill=shade_rgba(wood, 1.12))
    g.d.line([g.pt(x0, top_y + 34), g.pt(W + 10, top_y + 34)], fill=OL, width=int(4 * SS))
    g.d.line([g.pt(x0, top_y), g.pt(W + 10, top_y)], fill=OL, width=int(4 * SS))
    g.d.line([g.pt(x0, top_y), g.pt(x0, H)], fill=OL, width=int(4 * SS))
    for gx in range(max(80, int(x0) + 90), W, 260):
        g.d.line([g.pt(gx, top_y + 70), g.pt(gx, H)], fill=shade_rgba(wood, 0.6), width=int(4 * SS))
    if items:
        if x0 < 130:
            _rrect(g, 120, top_y - 18, 260, top_y + 4, 4, (245, 245, 240, 255), OL, 2)   # papeles
        if x0 < 430:
            _rrect(g, 440, top_y - 28, 640, top_y + 6, 6, (30, 30, 36, 255), OL, 3)   # portátil
        _rrect(g, 780, top_y - 40, 880, top_y + 6, 8, (235, 235, 240, 255), OL, 3)   # placa
        _rrect(g, 940, top_y - 62, 1000, top_y + 2, 10, (240, 240, 235, 255), OL, 3)  # taza
        g.ell(970, top_y - 62, 30, 8, (110, 70, 40, 255), OL, 2)


# --------------------------------------------------------------------------- escenarios
def _showroom_bg(with_cars=True):
    img, g = _canvas((232, 240, 250), (196, 206, 222))
    # techo con luces
    g.d.rectangle([*g.pt(0, 0), *g.pt(W, 190)], fill=(240, 243, 250, 255))
    for lx in range(60, W, 180):
        _rrect(g, lx, 70, lx + 120, 92, 10, (255, 253, 235, 255), (190, 190, 200, 255), 2)
        g.alpha(lambda a, lx=lx: a.poly([(lx + 10, 92), (lx + 110, 92), (lx + 220, 700), (lx - 100, 700)],
                                        (255, 250, 220, 26)))
    # ventanal con ciudad
    g.d.rectangle([*g.pt(0, 190), *g.pt(W, 1030)], fill=(170, 205, 240, 255))
    sky = gradient(W * SS, 840 * SS, (120, 180, 240), (225, 238, 252)).convert("RGBA")
    img.paste(sky, (0, 190 * SS))
    _skyline(g, 0, 650, W, 1030, 5, (112, 142, 186, 255))
    for fx in range(0, W + 1, 270):
        g.d.line([g.pt(fx, 190), g.pt(fx, 1030)], fill=(70, 82, 104, 255), width=int(10 * SS))
    g.d.line([g.pt(0, 640), g.pt(W, 640)], fill=(70, 82, 104, 255), width=int(8 * SS))
    # rótulo
    _rrect(g, 290, 205, 790, 290, 16, (210, 40, 60, 255), OL, 4)
    _text(g, (540, 248), "SUPER OFERTAS", 54, (255, 255, 255, 255))
    # suelo brillante
    floor = gradient(W * SS, 890 * SS, (205, 210, 222), (150, 158, 178)).convert("RGBA")
    img.paste(floor, (0, 1030 * SS))
    for i in range(0, 12):
        yy = 1030 + i * i * 7
        g.d.line([g.pt(0, yy), g.pt(W, yy)], fill=(255, 255, 255, 60), width=int(2 * SS))
    if with_cars:
        car(g, 250, 1130, 520, (222, 56, 62, 255))
        car(g, 830, 1150, 540, (56, 120, 222, 255), flip=True)
    return img, g


@lru_cache(maxsize=16)
def build(setting: str) -> Backdrop:
    fn = _BUILDERS.get(setting, _BUILDERS["showroom"])
    return fn()


def _build_showroom():
    img, g = _showroom_bg(True)
    out = _finish(img)
    return Backdrop(bg=out, props={"floor_y": 1450})


def _build_dealership_desk():
    img, g = _showroom_bg(True)
    out = _finish(img)
    fgi, fg = _layer()
    _desk(fg, 1420)
    return Backdrop(bg=out, fg=_finish(fgi, "RGBA"), props={"desk_y": 1420, "seat_y": 1540})


def _build_manager_office():
    img, g = _canvas((88, 62, 44), (66, 46, 34))
    g.d.rectangle([*g.pt(0, 0), *g.pt(W, 1100)], fill=(214, 190, 150, 255))
    g.d.rectangle([*g.pt(0, 880), *g.pt(W, 1100)], fill=(172, 130, 92, 255))  # zócalo/panel
    for px in range(0, W, 180):
        g.d.line([g.pt(px, 880), g.pt(px, 1100)], fill=(140, 100, 70, 255), width=int(5 * SS))
    # librero
    _rrect(g, 30, 300, 410, 880, 8, (110, 74, 48, 255), OL, 4)
    cols = [(200, 60, 60), (60, 120, 200), (230, 190, 60), (70, 160, 110), (150, 90, 170)]
    for row in range(4):
        y0 = 320 + row * 140
        g.d.line([g.pt(40, y0 + 130), g.pt(400, y0 + 130)], fill=OL, width=int(4 * SS))
        bx = 50
        i = row
        while bx < 380:
            bw = 24 + (i * 7) % 18
            bh = 70 + (i * 13) % 45
            c = cols[i % 5]
            g.poly([(bx, y0 + 130 - bh), (bx + bw, y0 + 130 - bh), (bx + bw, y0 + 130), (bx, y0 + 130)],
                   c + (255,), OL, 2)
            bx += bw + 3
            i += 1
    # ventana con persianas
    _rrect(g, 560, 230, 1030, 760, 10, (150, 200, 240, 255), (80, 60, 45, 255), 10)
    _skyline(g, 566, 520, 1024, 755, 9, (120, 150, 190, 255))
    for sy in range(236, 760, 26):
        g.d.rectangle([*g.pt(566, sy), *g.pt(1024, sy + 15)], fill=(236, 236, 232, 255))
        g.d.line([g.pt(566, sy + 15), g.pt(1024, sy + 15)], fill=(150, 150, 150, 255), width=int(2 * SS))
    # diplomas
    for dx in (440, 480):
        pass
    _rrect(g, 440, 330, 540, 430, 4, (250, 245, 225, 255), (120, 80, 40, 255), 6)
    g.line([(455, 360), (525, 360)], (150, 150, 150, 255), 4)
    g.line([(455, 385), (525, 385)], (150, 150, 150, 255), 4)
    # puerta
    _rrect(g, 0, 250, 0 + 20, 880, 2, (110, 74, 48, 255))
    # suelo
    g.d.rectangle([*g.pt(0, 1100), *g.pt(W, H)], fill=(96, 70, 52, 255))
    for i in range(0, 14):
        g.d.line([g.pt(0, 1100 + i * 60), g.pt(W, 1100 + i * 60)], fill=(84, 60, 44, 255), width=int(3 * SS))
    _plant(g, 990, 1130, 1.1)
    out = _finish(img)
    fgi, fg = _layer()
    _desk(fg, 1450, wood=(120, 76, 48), x0=470)
    # lámpara
    fg.line([(980, 1450), (1000, 1330), (940, 1280)], (60, 60, 66, 255), 8)
    fg.poly([(895, 1295), (985, 1295), (960, 1240), (920, 1240)], (255, 200, 60, 255), OL, 3)
    return Backdrop(bg=out, fg=_finish(fgi, "RGBA"), props={"door_x": 60})


def _waiting_bg():
    img, g = _canvas((236, 232, 224), (176, 170, 160))
    g.d.rectangle([*g.pt(0, 0), *g.pt(W, 1160)], fill=(230, 226, 214, 255))
    g.d.rectangle([*g.pt(0, 930), *g.pt(W, 1160)], fill=(150, 170, 160, 255))
    g.d.line([g.pt(0, 930), g.pt(W, 930)], fill=OL, width=int(4 * SS))
    # reloj grande
    cx, cy, r = 250, 420, 150
    g.ell(cx, cy, r + 16, r + 16, (60, 60, 70, 255), OL, 4)
    g.ell(cx, cy, r, r, (252, 252, 248, 255), OL, 3)
    for i in range(12):
        a = math.radians(i * 30)
        g.line([(cx + math.sin(a) * (r - 14), cy - math.cos(a) * (r - 14)),
                (cx + math.sin(a) * (r - 32), cy - math.cos(a) * (r - 32))], OL, 6)
    # sala de espera: sillas
    for sx in (80, 330):
        _rrect(g, sx, 820, sx + 220, 1000, 24, (60, 96, 150, 255), OL, 4)
        _rrect(g, sx - 20, 930, sx + 240, 1010, 18, (74, 114, 172, 255), OL, 4)
    # ventana de oficina (persianas)
    win = (610, 330, 1040, 880)
    _rrect(g, win[0] - 14, win[1] - 14, win[2] + 14, win[3] + 14, 8, (70, 70, 78, 255), OL, 4)
    g.d.rectangle([*g.pt(win[0], win[1]), *g.pt(win[2], win[3])], fill=(54, 46, 62, 255))
    g.alpha(lambda a: a.poly([(win[0], win[1]), (win[2], win[1]), (win[2], win[3] - 200),
                              (win[0], win[3])], (255, 214, 150, 40)))
    # suelo
    floor = gradient(W * SS, 760 * SS, (186, 150, 118), (132, 100, 76)).convert("RGBA")
    img.paste(floor, (0, 1160 * SS))
    _plant(g, 60, 1230, 1.0)
    return img, g, win


def _slats(g: _P, rect, color=(232, 232, 226, 255), gap=24, th=14, opacity=255):
    x0, y0, x1, y1 = rect
    c = color[:3] + (opacity,)
    for sy in range(y0 + 4, y1 - 6, gap):
        g.d.rectangle([*g.pt(x0, sy), *g.pt(x1, sy + th)], fill=c)
        g.d.line([g.pt(x0, sy + th), g.pt(x1, sy + th)], fill=(120, 120, 126, opacity), width=int(2 * SS))


def _build_waiting_area():
    img, g, win = _waiting_bg()
    out = _finish(img)
    midi, mid = _layer()
    _slats(mid, win, gap=26, th=12, opacity=235)
    return Backdrop(bg=out, mid=_finish(midi, "RGBA"), window=win,
                    props={"clock": (250, 420), "window": win})


def _build_blinds_peek():
    img, g, win = _waiting_bg()
    out = _finish(img)
    fgi, fg = _layer()
    # el punto de vista está dentro de la oficina, mirando por las persianas
    fg.d.rectangle([*fg.pt(0, 0), *fg.pt(W, 250)], fill=(40, 34, 46, 255))
    fg.d.rectangle([*fg.pt(0, 1500), *fg.pt(W, H)], fill=(40, 34, 46, 255))
    fg.d.rectangle([*fg.pt(0, 0), *fg.pt(50, H)], fill=(40, 34, 46, 255))
    fg.d.rectangle([*fg.pt(W - 50, 0), *fg.pt(W, H)], fill=(40, 34, 46, 255))
    _slats(fg, (50, 250, W - 50, 1500), color=(60, 52, 70, 255), gap=46, th=24, opacity=235)
    return Backdrop(bg=out, fg=_finish(fgi, "RGBA"), props={"clock": (250, 420)})


def _build_strategy():
    img, g = _canvas((22, 18, 64), (70, 34, 120))
    g.alpha(lambda a: a.ell(540, 760, 520, 520, (120, 90, 255, 38)))
    g.alpha(lambda a: a.ell(540, 760, 340, 340, (255, 90, 160, 30)))
    for gx in range(0, W + 1, 90):
        g.d.line([g.pt(gx, 0), g.pt(gx, H)], fill=(255, 255, 255, 14), width=int(2 * SS))
    for gy in range(0, H + 1, 90):
        g.d.line([g.pt(0, gy), g.pt(W, gy)], fill=(255, 255, 255, 14), width=int(2 * SS))
    rng = np.random.RandomState(11)
    for _ in range(60):
        x, y, r = rng.randint(0, W), rng.randint(0, H), rng.randint(2, 6)
        g.alpha(lambda a, x=x, y=y, r=r: a.ell(x, y, r, r, (255, 255, 255, 90)))
    return Backdrop(bg=_finish(img))


def _build_modern_office():
    img, g = _canvas((246, 248, 252), (220, 226, 236))
    g.d.rectangle([*g.pt(0, 0), *g.pt(W, 1160)], fill=(244, 246, 250, 255))
    # ventanal con ciudad
    g.d.rectangle([*g.pt(0, 150), *g.pt(470, 1060)], fill=(170, 208, 245, 255))
    sky = gradient(470 * SS, 910 * SS, (110, 175, 240), (232, 242, 255)).convert("RGBA")
    img.paste(sky, (0, 150 * SS))
    _skyline(g, 0, 680, 470, 1060, 21, (104, 136, 182, 255))
    g.d.line([g.pt(235, 150), g.pt(235, 1060)], fill=(80, 90, 110, 255), width=int(10 * SS))
    g.d.rectangle([*g.pt(0, 150), *g.pt(470, 1060)], outline=(80, 90, 110, 255), width=int(12 * SS))
    # pizarra con gráfico
    _rrect(g, 520, 260, 1040, 860, 14, (255, 255, 255, 255), (90, 96, 110, 255), 8)
    bars = [(100, (80, 170, 120)), (180, (80, 170, 120)), (150, (230, 110, 90)), (260, (80, 170, 120)),
            (340, (60, 140, 230))]
    for i, (h, c) in enumerate(bars):
        x = 570 + i * 90
        g.poly([(x, 790), (x + 64, 790), (x + 64, 790 - h * 1.4), (x, 790 - h * 1.4)], c + (255,), OL, 3)
    g.line([(560, 800), (1010, 800)], OL, 5)
    _text(g, (780, 305), "LISTA DE PRECIOS", 34, (60, 66, 90, 255))
    g.line([(570, 700), (680, 640), (760, 660), (860, 540), (990, 420)], (230, 80, 90, 255), 7)
    g.d.polygon([g.pt(1005, 412), g.pt(962, 420), g.pt(982, 452)], fill=(230, 80, 90, 255))
    # suelo madera
    wood = gradient(W * SS, 760 * SS, (198, 150, 104), (150, 108, 72)).convert("RGBA")
    img.paste(wood, (0, 1160 * SS))
    for i in range(12):
        g.d.line([g.pt(0, 1160 + i * i * 5), g.pt(W, 1160 + i * i * 5)], fill=(130, 94, 62, 120),
                 width=int(2 * SS))
    _plant(g, 1010, 1190, 1.15)
    out = _finish(img)
    fgi, fg = _layer()
    _plant(fg, 70, 1900, 1.5, leaf=(40, 130, 84, 255))
    return Backdrop(bg=out, fg=_finish(fgi, "RGBA"), props={"floor_y": 1500})


_BUILDERS = {
    "showroom": _build_showroom,
    "dealership_desk": _build_dealership_desk,
    "manager_office": _build_manager_office,
    "waiting_area": _build_waiting_area,
    "blinds_peek": _build_blinds_peek,
    "strategy": _build_strategy,
    "modern_office": _build_modern_office,
}
