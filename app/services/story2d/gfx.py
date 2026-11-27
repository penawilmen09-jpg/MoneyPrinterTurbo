"""Utilidades de dibujo vectorial (Skia) y de interpolación."""
from __future__ import annotations

import math
import random

import skia

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
_tf_cache: dict = {}


def typeface(path):
    if path not in _tf_cache:
        _tf_cache[path] = skia.Typeface.MakeFromFile(path)
    return _tf_cache[path]


# ---------------------------------------------------------------- color
def C(h, a=1.0):
    h = h.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return skia.Color(r, g, b, int(255 * max(0, min(1, a))))


def mix(h1, h2, t):
    a, b = h1.lstrip("#"), h2.lstrip("#")
    c = [int(int(a[i:i + 2], 16) * (1 - t) + int(b[i:i + 2], 16) * t) for i in (0, 2, 4)]
    return "#%02x%02x%02x" % tuple(c)


def shade(h, f):
    """f<0 oscurece, f>0 aclara."""
    return mix(h, "#000000", -f) if f < 0 else mix(h, "#ffffff", f)


# ---------------------------------------------------------------- math
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def lerp(a, b, t):
    return a + (b - a) * t


def prog(t, a, b):
    return clamp((t - a) / (b - a)) if b != a else (1.0 if t >= b else 0.0)


def smooth(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def ease_out(t):
    t = clamp(t)
    return 1 - (1 - t) ** 3


def ease_in(t):
    t = clamp(t)
    return t ** 3


def ease_io(t):
    t = clamp(t)
    return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def out_back(t, s=1.70158):
    t = clamp(t) - 1
    return t * t * ((s + 1) * t + s) + 1


def pulse(t, period=1.0):
    return 0.5 + 0.5 * math.sin(2 * math.pi * t / period)


def rnd(seed):
    return random.Random(seed)


# ---------------------------------------------------------------- paint
def P(color="#000000", a=1.0, style="fill", w=1.0, cap="round", join="round", blur=0):
    p = skia.Paint(AntiAlias=True, Color=C(color, a))
    if style == "stroke":
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(w)
        p.setStrokeCap({"round": skia.Paint.kRound_Cap, "butt": skia.Paint.kButt_Cap,
                        "square": skia.Paint.kSquare_Cap}[cap])
        p.setStrokeJoin(skia.Paint.kRound_Join if join == "round" else skia.Paint.kMiter_Join)
    if blur:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p


def grad(x0, y0, x1, y1, c0, c1, a0=1.0, a1=1.0):
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeLinear(
        [(x0, y0), (x1, y1)], [C(c0, a0), C(c1, a1)]))
    return p


def radial(cx, cy, r, c0, c1, a0=1.0, a1=0.0):
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeRadial(
        (cx, cy), r, [C(c0, a0), C(c1, a1)]))
    return p


# ---------------------------------------------------------------- shapes
def rect(cv, x, y, w, h, color, a=1.0, r=0, sw=None, **kw):
    """sw = grosor de trazo (style='stroke')."""
    if sw is not None:
        kw["w"] = sw
    if r:
        cv.drawRoundRect(skia.Rect.MakeXYWH(x, y, w, h), r, r, P(color, a, **kw))
    else:
        cv.drawRect(skia.Rect.MakeXYWH(x, y, w, h), P(color, a, **kw))


def rectp(cv, x, y, w, h, paint, r=0):
    if r:
        cv.drawRoundRect(skia.Rect.MakeXYWH(x, y, w, h), r, r, paint)
    else:
        cv.drawRect(skia.Rect.MakeXYWH(x, y, w, h), paint)


def circ(cv, x, y, r, color, a=1.0, **kw):
    cv.drawCircle(x, y, r, P(color, a, **kw))


def oval(cv, x, y, rx, ry, color, a=1.0, **kw):
    cv.drawOval(skia.Rect.MakeXYWH(x - rx, y - ry, 2 * rx, 2 * ry), P(color, a, **kw))


def line(cv, x0, y0, x1, y1, color, w=4, a=1.0, cap="round"):
    cv.drawLine(x0, y0, x1, y1, P(color, a, "stroke", w, cap))


def poly(cv, pts, color, a=1.0, closed=True, **kw):
    path = skia.Path()
    path.moveTo(*pts[0])
    for p in pts[1:]:
        path.lineTo(*p)
    if closed:
        path.close()
    cv.drawPath(path, P(color, a, **kw))


def curve(cv, pts, color, w=4, a=1.0):
    """Polilínea suavizada con cuadráticas."""
    path = skia.Path()
    path.moveTo(*pts[0])
    for i in range(1, len(pts) - 1):
        mx = (pts[i][0] + pts[i + 1][0]) / 2
        my = (pts[i][1] + pts[i + 1][1]) / 2
        path.quadTo(pts[i][0], pts[i][1], mx, my)
    path.lineTo(*pts[-1])
    cv.drawPath(path, P(color, a, "stroke", w))


def shadow(cv, x, y, rx, ry, a=0.25):
    cv.drawOval(skia.Rect.MakeXYWH(x - rx, y - ry, 2 * rx, 2 * ry),
                P("#000000", a, blur=ry * 0.5))


def text(cv, s, x, y, size, color="#ffffff", align="center", font=FONT_BOLD,
         a=1.0, outline=None, outline_w=0, spacing=0):
    f = skia.Font(typeface(font), size)
    f.setSubpixel(True)
    blob_w = f.measureText(s)
    if align == "center":
        x -= blob_w / 2
    elif align == "right":
        x -= blob_w
    if outline:
        cv.drawString(s, x, y, f, P(outline, a, "stroke", outline_w, join="round"))
    cv.drawString(s, x, y, f, P(color, a))
    return blob_w


def text_w(s, size, font=FONT_BOLD):
    f = skia.Font(typeface(font), size)
    return f.measureText(s)


class Ctx:
    """Contexto de cuadro: hace la cámara y el estado global reutilizables."""

    def __init__(self, cv, t, W=1080, H=1920):
        self.cv, self.t, self.W, self.H = cv, t, W, H


def camera(cv, cx, cy, zoom=1.0, rot=0.0, W=1080, H=1920):
    """El punto (cx,cy) del mundo queda en el centro de la pantalla."""
    cv.translate(W / 2, H / 2)
    if rot:
        cv.rotate(rot)
    cv.scale(zoom, zoom)
    cv.translate(-cx, -cy)


def shake(t, amp, freq=28.0, seed=0):
    return (amp * math.sin(t * freq + seed) * math.cos(t * freq * 0.73),
            amp * math.cos(t * freq * 1.1 + seed) * math.sin(t * freq * 0.61))
