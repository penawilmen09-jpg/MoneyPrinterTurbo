"""Personajes 2D vectoriales con rig simple (Pillow, sin dependencias de pago).

Cada personaje se define por una *especificación* (colores, peinado, ropa). Como
todos los fotogramas se dibujan desde la misma especificación, el personaje
conserva exactamente el mismo aspecto en todas las escenas.
"""

from __future__ import annotations

import math
from typing import Any

from PIL import Image, ImageDraw

SS = 2  # factor de supersampling para antialias

# --------------------------------------------------------------------------- presets
PRESETS: dict[str, dict[str, Any]] = {
    "vendedor": dict(
        skin="#E8B48A", hair="#3A2616", hair_style="slick", outfit="suit",
        jacket="#1F3A6B", shirt="#FFFFFF", tie="#D92B3A", pants="#18274A",
        shoes="#1A1A1A", glasses=False, facial="none", build=1.0, badge=True,
        eye="#3B2A1C",
    ),
    "cliente": dict(
        skin="#B87A4B", hair="#14110F", hair_style="short", outfit="casual",
        jacket="#2F9E8F", shirt="#F2EBDD", tie=None, pants="#4A5568",
        shoes="#E5E5E5", glasses=False, facial="stubble", build=1.04, badge=False,
        eye="#2A1B10",
    ),
    "jefe": dict(
        skin="#F0C8A0", hair="#9AA0A6", hair_style="gray", outfit="suit",
        jacket="#4B4F58", shirt="#DCE6F2", tie="#2E7D5B", pants="#33363D",
        shoes="#111111", glasses=True, facial="mustache", build=1.2, badge=False,
        eye="#3A3A3A",
    ),
}
PRESETS["presentador"] = dict(PRESETS["vendedor"])

# --------------------------------------------------------------------------- expresiones
EXPRESSIONS: dict[str, dict[str, float]] = {
    #            ojos  ceja  inclin asim  sonrisa ancho abierta rubor  curva párpado
    "neutral":    dict(eo=1.0, bh=0, bt=0.0, ba=0, sm=0.15, mw=24, mo=0.0, bl=0.0, ec=0, lid=0.0),
    "happy":      dict(eo=0.9, bh=6, bt=0.1, ba=0, sm=0.85, mw=34, mo=0.25, bl=0.5, ec=0.6, lid=0.0),
    "nervous":    dict(eo=1.15, bh=12, bt=0.7, ba=0, sm=0.45, mw=30, mo=0.12, bl=0.25, ec=0, lid=0.0),
    "worried":    dict(eo=1.1, bh=8, bt=0.85, ba=0, sm=-0.55, mw=24, mo=0.05, bl=0.0, ec=0, lid=0.0),
    "surprised":  dict(eo=1.4, bh=24, bt=0.0, ba=0, sm=0.0, mw=15, mo=0.9, bl=0.0, ec=0, lid=0.0),
    "suspicious": dict(eo=0.6, bh=0, bt=-0.45, ba=14, sm=-0.1, mw=22, mo=0.0, bl=0.0, ec=0, lid=0.2),
    "grateful":   dict(eo=0.85, bh=8, bt=0.3, ba=0, sm=1.0, mw=38, mo=0.35, bl=0.8, ec=1.0, lid=0.0),
    "impatient":  dict(eo=0.8, bh=-2, bt=-0.35, ba=0, sm=-0.35, mw=20, mo=0.0, bl=0.0, ec=0, lid=0.3),
    "serious":    dict(eo=0.95, bh=0, bt=-0.2, ba=0, sm=-0.05, mw=22, mo=0.0, bl=0.0, ec=0, lid=0.0),
    "smug":       dict(eo=0.75, bh=0, bt=-0.1, ba=10, sm=0.6, mw=26, mo=0.0, bl=0.1, ec=0, lid=0.2),
    "tired":      dict(eo=0.55, bh=-4, bt=0.3, ba=0, sm=-0.2, mw=22, mo=0.0, bl=0.0, ec=0, lid=0.45),
    "laugh":      dict(eo=0.6, bh=10, bt=0.1, ba=0, sm=1.0, mw=40, mo=0.85, bl=0.6, ec=1.0, lid=0.0),
}
SWEATY = {"nervous", "worried"}

# --------------------------------------------------------------------------- poses
# Objetivos de mano (derecha) relativos al origen del personaje; la izquierda se
# refleja. Un IK de dos huesos calcula el codo.
POSE_HANDS: dict[str, tuple[tuple[float, float], tuple[float, float]]] = {
    #               mano derecha          mano izquierda (ya en coords locales)
    "stand":        ((108, -262), (-108, -262)),
    "sit":          ((72, -300), (-72, -300)),
    "walk":         ((100, -268), (-100, -268)),
    "point":        ((250, -540), (-108, -262)),
    "present":      ((185, -470), (-185, -470)),
    "arms_crossed": ((-45, -392), (45, -372)),
    "wipe":         ((52, -560), (-108, -262)),
    "loosen_tie":   ((14, -446), (-108, -262)),
}
L1, L2 = 112.0, 108.0


def _hex(c: str, a: int = 255) -> tuple[int, int, int, int]:
    c = c.lstrip("#")
    return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16), a


def shade(c: str, f: float) -> tuple[int, int, int, int]:
    r, g, b, _ = _hex(c)
    if f >= 1:
        return (min(255, int(r + (255 - r) * (f - 1))), min(255, int(g + (255 - g) * (f - 1))),
                min(255, int(b + (255 - b) * (f - 1))), 255)
    return int(r * f), int(g * f), int(b * f), 255


def _ik(shoulder, target, side: int):
    """Codo para una cadena de dos huesos. side=+1 derecha, -1 izquierda."""
    sx, sy = shoulder
    dx, dy = target[0] - sx, target[1] - sy
    d = math.hypot(dx, dy)
    d = max(30.0, min(d, L1 + L2 - 0.5))
    base = math.atan2(dy, dx)
    cos_a = (L1 * L1 + d * d - L2 * L2) / (2 * L1 * d)
    a = math.acos(max(-1.0, min(1.0, cos_a)))
    best = None
    for sgn in (1, -1):
        ex = sx + L1 * math.cos(base + sgn * a)
        ey = sy + L1 * math.sin(base + sgn * a)
        score = side * ex * 1.0 + ey * 0.6  # codos hacia afuera y abajo
        if best is None or score > best[0]:
            best = (score, ex, ey)
    ux, uy = dx / max(math.hypot(dx, dy), 1e-6), dy / max(math.hypot(dx, dy), 1e-6)
    hx, hy = sx + ux * d, sy + uy * d
    return (best[1], best[2]), (hx, hy)


def blend_dict(a: dict, b: dict, t: float) -> dict:
    return {k: a[k] + (b[k] - a[k]) * t for k in a}


class _P:
    """Pintor con transformación unidades->píxeles."""

    def __init__(self, img: Image.Image, ox: float, oy: float, k: float):
        self.img, self.d = img, ImageDraw.Draw(img, "RGBA")
        self.ox, self.oy, self.k = ox, oy, k

    def pt(self, x, y):
        return (self.ox + x * self.k, self.oy + y * self.k)

    def poly(self, pts, fill, outline=None, w=3):
        pp = [self.pt(*p) for p in pts]
        self.d.polygon(pp, fill=fill)
        if outline:
            self.d.line(pp + [pp[0]], fill=outline, width=max(1, int(w * self.k)), joint="curve")

    def ell(self, cx, cy, rx, ry, fill, outline=None, w=3):
        self.d.ellipse([*self.pt(cx - rx, cy - ry), *self.pt(cx + rx, cy + ry)],
                       fill=fill, outline=outline, width=max(1, int(w * self.k)) if outline else 0)

    def limb(self, a, b, width, fill, outline=None):
        (x0, y0), (x1, y1) = self.pt(*a), self.pt(*b)
        if outline:
            ow = width + 6
            self.d.line([(x0, y0), (x1, y1)], fill=outline, width=int(ow * self.k))
            r = ow * self.k / 2
            for x, y in ((x0, y0), (x1, y1)):
                self.d.ellipse([x - r, y - r, x + r, y + r], fill=outline)
        self.d.line([(x0, y0), (x1, y1)], fill=fill, width=int(width * self.k))
        r = width * self.k / 2
        for x, y in ((x0, y0), (x1, y1)):
            self.d.ellipse([x - r, y - r, x + r, y + r], fill=fill)

    def alpha(self, fn):
        """Dibuja formas translúcidas en una capa aparte y las mezcla (alpha_composite)."""
        layer = Image.new("RGBA", self.img.size, (0, 0, 0, 0))
        fn(_P(layer, self.ox, self.oy, self.k))
        self.img.alpha_composite(layer)

    def line(self, pts, fill, w):
        self.d.line([self.pt(*p) for p in pts], fill=fill, width=max(1, int(w * self.k)),
                    joint="curve")


# --------------------------------------------------------------------------- cabeza
HEAD_W, HEAD_H = 380, 380  # unidades; centro = centro de la cabeza


def _draw_head(spec: dict, p: dict, k: float) -> Image.Image:
    img = Image.new("RGBA", (int(HEAD_W * k), int(HEAD_H * k)), (0, 0, 0, 0))
    g = _P(img, HEAD_W / 2 * k, HEAD_H / 2 * k, k)
    skin, sk_d = _hex(spec["skin"]), shade(spec["skin"], 0.8)
    ol = (35, 25, 25, 255)
    hair, hair_d = _hex(spec["hair"]), shade(spec["hair"], 0.7)
    style = spec["hair_style"]
    rx, ry = 76.0, 88.0

    # pelo trasero
    if style in ("slick", "short"):
        g.ell(0, -8, rx + 6, ry + 6, hair, ol)
    elif style == "gray":
        g.ell(0, -4, rx + 5, ry + 3, hair, ol)
    # orejas
    for s in (-1, 1):
        g.ell(s * (rx - 2), 6, 13, 21, skin, ol)
        g.ell(s * (rx - 2), 6, 6, 12, sk_d)
    # cara
    g.ell(0, 0, rx, ry, skin, ol, w=4)
    # barba
    if spec["facial"] == "stubble":
        g.alpha(lambda a: a.d.pieslice([*a.pt(-rx + 4, -ry + 20), *a.pt(rx - 4, ry - 1)], 20, 160,
                                       fill=_hex(spec["hair"], 55)))
    # nariz
    g.poly([(-4, 2), (4, 2), (9, 22), (0, 27), (-9, 22)], sk_d)
    g.ell(0, 22, 11, 5, sk_d)

    # rubor
    if p["bl"] > 0.02:
        a = int(110 * min(1, p["bl"]))
        def _blush(q):
            for s in (-1, 1):
                q.ell(s * 46, 22, 17, 10, (240, 110, 110, a))
        g.alpha(_blush)

    # ojos
    look_x, look_y = p.get("lx", 0.0) * 6, p.get("ly", 0.0) * 4
    eo = max(0.05, p["eo"] * (1 - p["blink"] * 0.95))
    for s in (-1, 1):
        ex, ey = s * 31, -14
        if p["ec"] > 0.55 and p["blink"] < 0.5:  # ojos felices (arco)
            g.line([(ex - 15, ey + 4), (ex - 7, ey - 6), (ex + 7, ey - 6), (ex + 15, ey + 4)],
                   ol, 5)
        else:
            h = 17 * min(eo, 1.35)
            g.ell(ex, ey, 15, h, (255, 255, 255, 255), ol, w=3)
            if eo > 0.12:
                pr = 8.5 * (1.15 if p["eo"] > 1.2 else 1.0)
                g.ell(ex + look_x, ey + look_y, pr, min(pr, h - 1), _hex(spec["eye"]))
                g.ell(ex + look_x, ey + look_y, pr * 0.45, pr * 0.45, (15, 12, 10, 255))
                g.ell(ex + look_x + 3, ey + look_y - 3, 2.6, 2.6, (255, 255, 255, 255))
            lid = max(p["lid"], 0.0) + (0.0)
            if lid > 0.02 and p["blink"] < 0.5:
                top = ey - h
                bot = top + 2 * h * lid
                g.poly([(ex - 16, top - 2), (ex + 16, top - 2), (ex + 16, bot), (ex - 16, bot)],
                       skin)
                g.line([(ex - 16, bot), (ex + 16, bot)], ol, 3)

    # cejas
    bh, bt, ba = p["bh"], p["bt"], p["ba"]
    for s in (-1, 1):
        raise_ = bh + (ba if s == 1 else 0)
        yb = -46 - raise_
        inner = yb - bt * 13
        outer = yb + bt * 9
        pts = [(s * 12, inner), (s * 28, (inner + outer) / 2 - 4), (s * 47, outer)]
        g.line(pts, hair_d if style != "gray" else (110, 110, 112, 255), 9)

    # boca
    mw = p["mw"]
    base = 52
    smile = p["sm"]
    opn = max(0.0, p["open"])
    n = 18
    top, bot = [], []
    for i in range(n + 1):
        u = -1 + 2 * i / n
        x = u * mw
        yt = base - smile * 15 * u * u + smile * 4
        top.append((x, yt))
        bot.append((x, yt + opn * 34 * (1 - u * u) + 0.0))
    if opn < 0.06:
        g.line(top, (120, 40, 40, 255), 6)
        if smile > 0.6:  # sonrisa con dientes
            g.poly(top + [(x, y + 9 * (1 - (x / mw) ** 2) + 1) for x, y in reversed(top)],
                   (255, 255, 255, 255), (120, 40, 40, 255), 2)
    else:
        g.poly(top + list(reversed(bot)), (95, 20, 30, 255), (70, 20, 25, 255), 3)
        # dientes superiores
        teeth = [(x, y) for x, y in top]
        tb = [(x, y + min(12.0, (b[1] - y) * 0.55)) for (x, y), b in zip(top, bot)]
        g.poly(teeth + list(reversed(tb)), (255, 255, 255, 255))
        # lengua
        g.ell(0, bot[n // 2][1] - 6, mw * 0.45, max(2.0, opn * 9), (214, 96, 104, 255))

    # bigote
    if spec["facial"] == "mustache":
        mc = (95, 98, 102, 255)
        g.poly([(-30, 40), (-4, 36), (0, 40), (4, 36), (30, 40), (22, 48), (4, 43),
                (0, 45), (-4, 43), (-22, 48)], mc, ol, 2)

    # pelo frontal
    if style == "short":
        g.poly([(-rx - 4, -18), (-rx + 2, -64), (-40, -ry - 4), (0, -ry - 10),
                (46, -ry - 2), (rx - 2, -60), (rx + 4, -18), (rx - 14, -48), (40, -70),
                (0, -66), (-40, -70), (-rx + 14, -48)], hair, ol)
    elif style == "slick":
        g.poly([(-rx - 4, -14), (-rx + 3, -66), (-34, -ry - 8), (10, -ry - 14),
                (56, -ry - 2), (rx - 1, -62), (rx + 4, -14), (rx - 12, -52), (30, -64),
                (-8, -74), (-44, -58), (-rx + 12, -44)], hair, ol)
        g.line([(-30, -ry - 4), (6, -ry + 4), (46, -ry + 12)], shade(spec["hair"], 1.5), 4)
    elif style == "gray":
        g.poly([(-rx - 3, -10), (-rx + 3, -50), (-52, -ry + 4), (-12, -ry - 4),
                (-rx + 10, -36)], hair, ol)
        g.poly([(rx + 3, -10), (rx - 3, -50), (52, -ry + 4), (12, -ry - 4),
                (rx - 10, -36)], hair, ol)
    # gafas
    if spec["glasses"]:
        fr = (40, 40, 48, 255)
        def _lenses(q):
            for s in (-1, 1):
                q.d.rounded_rectangle([*q.pt(s * 31 - 23, -34), *q.pt(s * 31 + 23, 8)],
                                      radius=11 * k, fill=(180, 220, 255, 40))
        g.alpha(_lenses)
        for s in (-1, 1):
            g.d.rounded_rectangle([*g.pt(s * 31 - 23, -34), *g.pt(s * 31 + 23, 8)],
                                  radius=11 * k, outline=fr, width=int(4 * k))
        g.line([(-8, -14), (8, -14)], fr, 4)
        for s in (-1, 1):
            g.line([(s * 54, -14), (s * (rx - 2), -18)], fr, 4)
    return img


# --------------------------------------------------------------------------- cuerpo
CANVAS_W, CANVAS_H = 620, 860
ORIGIN = (310.0, 830.0)  # píxel (en unidades) del punto (0,0)


def head_anchor(scale: float = 1.0, sit: bool = False) -> tuple[float, float]:
    """Posición (dx, dy) de la cabeza respecto al origen del personaje (unidades*escala)."""
    dy = -575 + (215 if sit else 0)
    return 0.0, dy * scale


def render_character(spec: dict, state: dict, scale: float = 1.0) -> tuple[Image.Image, float, float]:
    """Dibuja un personaje. Devuelve (imagen RGBA, ox, oy) con el origen en píxeles.

    ``state`` claves: hands(R,L), expr(dict), mouth, blink, look(lx,ly), tilt, bob,
    walk(phase|None), sit, tie_loose, flip, sweat.
    """
    k = SS * scale
    img = Image.new("RGBA", (int(CANVAS_W * k), int(CANVAS_H * k)), (0, 0, 0, 0))
    ox, oy = ORIGIN[0] * k, ORIGIN[1] * k
    b = spec["build"]
    sit = state.get("sit", False)
    bob = state.get("bob", 0.0)
    dy = (215 if sit else 0) + bob
    g = _P(img, ox, oy + dy * k, k)
    ol = (35, 25, 25, 255)
    skin = _hex(spec["skin"])

    # silla
    if sit:
        g.d.rounded_rectangle([*g.pt(-100 * b, -520), *g.pt(100 * b, -250)], radius=32 * k,
                              fill=(60, 60, 70, 255), outline=ol, width=int(3 * k))

    # piernas
    walk = state.get("walk")
    if not sit:
        for s, ph in ((-1, 0.0), (1, math.pi)):
            sw = math.sin(walk + ph) if walk is not None else 0.0
            lift = max(0.0, math.cos(walk + ph)) * 18 if walk is not None else 0.0
            hip = (s * 40 * b, -255)
            foot = (s * 42 * b + sw * 55, -16 - lift)
            g.limb(hip, foot, 66 * b, _hex(spec["pants"]), ol)
            g.ell(foot[0] + s * 4 + sw * 6, foot[1] + 6, 44, 20, _hex(spec["shoes"]), ol)

    # brazo trasero (izq. del personaje) detrás del torso no hace falta: se dibuja después
    sh_r, sh_l = (82 * b - 4, -452), (-82 * b + 4, -452)
    hands = state["hands"]
    elbows = []
    for side, sh, hand in ((1, sh_r, hands[0]), (-1, sh_l, hands[1])):
        elbow, hnd = _ik(sh, hand, side)
        elbows.append((side, sh, elbow, hnd))

    # torso
    casual = spec["outfit"] == "casual"
    jc = _hex(spec["jacket"])
    jd = shade(spec["jacket"], 0.78)
    sw_, ww = 92 * b, 74 * b
    g.poly([(-sw_ + 6, -468), (-30, -490), (30, -490), (sw_ - 6, -468), (sw_, -440),
            (ww, -250), (-ww, -250), (-sw_, -440)], jc, ol, 4)
    g.poly([(sw_ - 14, -462), (sw_, -440), (ww, -250), (ww - 22, -250)], jd)  # sombra lateral
    # cuello / camisa
    g.limb((0, -500), (0, -480), 34, skin, ol)
    loose = state.get("tie_loose", 0.0)
    if casual:
        g.poly([(-34, -490), (34, -490), (26, -430), (-26, -430)], _hex(spec["shirt"]), ol, 3)
        g.poly([(-34, -492), (-8, -492), (-2, -468), (-26, -470)], shade(spec["shirt"], 0.9), ol, 3)
        g.poly([(34, -492), (8, -492), (2, -468), (26, -470)], shade(spec["shirt"], 0.9), ol, 3)
        g.line([(0, -470), (0, -250)], jd, 5)
    else:
        v = 38 + loose * 14
        g.poly([(-v, -490), (v, -490), (0, -330)], _hex(spec["shirt"]), ol, 3)
        # solapas
        g.poly([(-v - 4, -490), (-20, -490), (0, -330), (-34, -300), (-sw_ + 20, -440)], jd, ol, 3)
        g.poly([(v + 4, -490), (20, -490), (0, -330), (34, -300), (sw_ - 20, -440)], jd, ol, 3)
        # cuello de camisa
        g.poly([(-v, -492), (-6, -484), (-12, -468)], (255, 255, 255, 255), ol, 2)
        g.poly([(v, -492), (6, -484), (12, -468)], (255, 255, 255, 255), ol, 2)
        if spec["tie"]:
            tc = _hex(spec["tie"])
            tdx = loose * 14
            ky = -470 + loose * 30
            g.poly([(-11 + tdx * 0.3, ky), (11 + tdx * 0.3, ky), (13 + tdx * 0.5, ky + 24),
                    (-13 + tdx * 0.5, ky + 24)], tc, ol, 2)
            g.poly([(-13 + tdx * 0.5, ky + 22), (13 + tdx * 0.5, ky + 22),
                    (24 + tdx, -300 + loose * 22), (tdx * 1.2, -272 + loose * 22),
                    (-24 + tdx, -300 + loose * 22)], tc, ol, 3)
        if spec["badge"]:
            g.d.rounded_rectangle([*g.pt(40, -400), *g.pt(76, -380)], radius=3 * k,
                                  fill=(255, 255, 255, 255), outline=ol, width=int(2 * k))
            g.line([(45, -392), (70, -392)], (60, 60, 70, 255), 3)

    # brazos
    sleeve = jc
    for side, sh, elbow, hnd in elbows:
        g.limb(sh, elbow, 44 * (0.95 + 0.05 * b), sleeve, ol)
        g.limb(elbow, hnd, 40, sleeve, ol)
        # puño de camisa y mano
        ux, uy = hnd[0] - elbow[0], hnd[1] - elbow[1]
        ln = max(math.hypot(ux, uy), 1)
        cuff = (hnd[0] - ux / ln * 8, hnd[1] - uy / ln * 8)
        g.limb(cuff, hnd, 38, _hex(spec["shirt"]) if not casual else shade(spec["jacket"], 1.1), None)
        g.ell(hnd[0] + ux / ln * 14, hnd[1] + uy / ln * 14, 21, 22, skin, ol, w=3)

    # cabeza
    p = dict(state["expr"])
    p.update(open=state.get("mouth", 0.0), blink=state.get("blink", 0.0),
             lx=state.get("look", (0, 0))[0], ly=state.get("look", (0, 0))[1])
    head = _draw_head(spec, p, k)
    tilt = state.get("tilt", 0.0)
    if abs(tilt) > 0.05:
        head = head.rotate(tilt, resample=Image.BICUBIC, expand=False)
    hx, hy = ox, oy + (dy - 575) * k
    img.alpha_composite(head, (int(hx - head.width / 2), int(hy - head.height / 2)))

    # reducir (antialias)
    out = img.resize((int(CANVAS_W * scale), int(CANVAS_H * scale)), Image.LANCZOS)
    if state.get("flip"):
        out = out.transpose(Image.FLIP_LEFT_RIGHT)
        return out, (CANVAS_W - ORIGIN[0]) * scale, ORIGIN[1] * scale
    return out, ORIGIN[0] * scale, ORIGIN[1] * scale


def resolve_spec(definition: dict) -> dict:
    """Combina un preset con sobreescrituras del guion."""
    base = dict(PRESETS.get(definition.get("preset", "vendedor"), PRESETS["vendedor"]))
    base.update({k: v for k, v in definition.items() if k != "preset"})
    return base
