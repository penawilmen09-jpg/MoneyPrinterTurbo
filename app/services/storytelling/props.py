"""Objetos (props) cartoon.  Cada uno se dibuja centrado en (0,0) con ~100 u de ancho."""

from __future__ import annotations

import math

from .gfx import font, shade

OUT = (34, 28, 44)


class P:
    """Pequeño pincel que transforma unidades de prop a píxeles (con supersampling)."""

    def __init__(self, d, x, y, s):
        self.d, self.x, self.y, self.s = d, x, y, s

    def pt(self, px, py):
        return (self.x + px * self.s, self.y + py * self.s)

    def w(self, v):
        return max(1, int(v * self.s))

    def rect(self, x0, y0, x1, y1, fill, r=0, outline=OUT, width=3):
        a, b = self.pt(x0, y0), self.pt(x1, y1)
        if r:
            self.d.rounded_rectangle([a[0], a[1], b[0], b[1]], radius=r * self.s, fill=fill, outline=outline, width=self.w(width) if outline else 0)
        else:
            self.d.rectangle([a[0], a[1], b[0], b[1]], fill=fill, outline=outline, width=self.w(width) if outline else 0)

    def ell(self, cx, cy, rx, ry, fill, outline=OUT, width=3):
        a, b = self.pt(cx - rx, cy - ry), self.pt(cx + rx, cy + ry)
        self.d.ellipse([a[0], a[1], b[0], b[1]], fill=fill, outline=outline, width=self.w(width) if outline else 0)

    def poly(self, pts, fill, outline=OUT, width=3):
        P_ = [self.pt(*p) for p in pts]
        self.d.polygon(P_, fill=fill)
        if outline:
            self.d.line(P_ + [P_[0]], fill=outline, width=self.w(width), joint="curve")

    def line(self, pts, fill, width=3):
        self.d.line([self.pt(*p) for p in pts], fill=fill, width=self.w(width), joint="curve")

    def text(self, px, py, s, size, fill, anchor="mm"):
        self.d.text(self.pt(px, py), s, font=font(size * self.s), fill=fill, anchor=anchor)


def _screen_text(t: float, base: int = 0) -> str:
    v = (base + int(t * 7.3)) % 90 + 10
    return f"${v}.{(int(t * 31) % 99):02d}"


def draw_prop(name: str, d, x: float, y: float, s: float, t: float, extra: dict | None = None) -> None:
    """Dibuja ``name`` con el centro en (x,y), escala s (px por unidad)."""
    p = P(d, x, y, s)
    extra = extra or {}
    fn = _PROPS.get(name, _generic)
    fn(p, t, extra)


# ---------------------------------------------------------------------------
def _cash_register(p, t, ex):
    p.rect(-62, 10, 62, 52, (86, 90, 108), r=6)  # base
    p.poly([(-56, 10), (56, 10), (44, -26), (-44, -26)], (112, 118, 140))  # cuerpo
    p.rect(-50, -86, 50, -34, (30, 40, 50), r=6)  # pantalla
    p.rect(-44, -80, 44, -40, (20, 52, 44), r=3, outline=None)
    col = (255, 90, 90) if ex.get("alert") else (120, 255, 160)
    p.text(0, -60, ex.get("text") or _screen_text(t), 24, col)
    for r in range(2):
        for k in range(4):
            p.rect(-40 + k * 22, -20 + r * 17, -24 + k * 22, -8 + r * 17, (200, 205, 220), r=2, width=2)
    p.rect(-62, 52, 62, 66, (60, 64, 78), r=4)
    # cajón abierto?
    if ex.get("open"):
        p.rect(-56, 52, 56, 82, (150, 154, 170), r=4)


def _receipt(p, t, ex):
    g = min(1.0, (t * 0.8) % 2.0) if ex.get("grow", True) else 1.0
    hh = 40 + 90 * g
    p.rect(-34, -hh, 34, 60, (252, 252, 248), r=2)
    for i in range(int(hh / 14)):
        p.line([(-22, -hh + 14 + i * 14), (22 - (i % 3) * 8, -hh + 14 + i * 14)], (120, 120, 130), 3)
    p.rect(-34, 56, 34, 66, (230, 230, 226), r=1, width=2)


def _money(p, t, ex):
    for i in range(3):
        a = (i - 1) * 7
        p.poly([(-56 + i * 8, -18 + i * 10), (52 + i * 8, -22 + i * 10 + a), (56 + i * 8, 26 + i * 10 + a), (-52 + i * 8, 30 + i * 10)], (112, 190, 120))
        p.ell(i * 8, 4 + i * 10, 16, 16, (160, 224, 160), width=2)
        p.text(i * 8, 4 + i * 10, "$", 20, (30, 90, 50))


def _coins(p, t, ex):
    for i, (cx, cy) in enumerate(((-24, 14), (20, 18), (-2, -10))):
        p.ell(cx, cy, 26, 26, (250, 214, 72))
        p.ell(cx, cy, 17, 17, (252, 232, 130), width=2)
        p.text(cx, cy, "$", 20, (150, 110, 20))


def _magnifier(p, t, ex):
    p.line([(26, 26), (64, 66)], (110, 70, 40), 16)
    p.ell(0, 0, 44, 44, (190, 230, 250, 170), width=7)
    p.ell(-14, -14, 10, 6, (255, 255, 255, 220), outline=None)


def _clipboard(p, t, ex):
    p.rect(-44, -58, 44, 58, (150, 108, 74), r=6)
    p.rect(-36, -46, 36, 50, (252, 252, 248), r=2, width=2)
    p.rect(-18, -66, 18, -48, (170, 174, 190), r=4)
    for i in range(5):
        p.line([(-26, -26 + i * 18), (24 - (i % 2) * 12, -26 + i * 18)], (130, 130, 150), 3)
    p.line([(-28, -4), (-22, 4), (-12, -10)], (60, 170, 90), 5)


def _document(p, t, ex):
    p.rect(-40, -54, 40, 54, (252, 252, 248), r=3)
    for i in range(6):
        p.line([(-26, -34 + i * 14), (26 - (i % 3) * 10, -34 + i * 14)], (130, 130, 150), 3)
    p.ell(26, 36, 12, 12, (232, 72, 60), width=2)


def _tablet(p, t, ex):
    p.rect(-48, -62, 48, 62, (40, 44, 56), r=10)
    p.rect(-40, -52, 40, 52, (60, 140, 210), r=4, outline=None)
    for i in range(4):
        h = 14 + 10 * math.sin(t * 2 + i)
        p.rect(-30 + i * 16, 36 - h * 2, -20 + i * 16, 36, (250, 214, 72), outline=None)


def _phone(p, t, ex):
    p.rect(-26, -50, 26, 50, (36, 38, 48), r=8)
    p.rect(-21, -42, 21, 38, (90, 170, 230), r=3, outline=None)
    p.ell(0, 44, 4, 4, (180, 180, 190), outline=None)


def _cctv(p, t, ex):
    p.rect(-26, -50, 26, -36, (90, 96, 112), r=3)
    p.poly([(-34, -34), (46, -26), (46, 20), (-34, 26)], (210, 214, 224))
    p.ell(44, -2, 12, 24, (60, 66, 82), width=3)
    p.ell(44, -2, 6, 12, (130, 200, 255), outline=None)
    if int(t * 2) % 2 == 0:
        p.ell(-18, -12, 5, 5, (255, 50, 50), outline=None)


def _box(p, t, ex):
    p.poly([(-50, -20), (0, -44), (50, -20), (0, 4)], (224, 176, 116))
    p.poly([(-50, -20), (0, 4), (0, 56), (-50, 32)], (200, 150, 96))
    p.poly([(0, 4), (50, -20), (50, 32), (0, 56)], (182, 134, 84))
    p.line([(-25, -32), (25, -8)], (240, 220, 180), 8)


def _cart(p, t, ex):
    p.line([(-70, -56), (-48, -56), (-30, 24), (48, 24)], (150, 156, 172), 7)
    p.poly([(-44, -40), (66, -40), (50, 20), (-30, 20)], (190, 196, 212, 160), width=4)
    for i in range(1, 4):
        p.line([(-44 + i * 28, -40), (-36 + i * 24, 20)], (150, 156, 172), 3)
    p.ell(-18, 46, 11, 11, (50, 52, 64))
    p.ell(40, 46, 11, 11, (50, 52, 64))


def _basket(p, t, ex):
    p.poly([(-56, -20), (56, -20), (44, 40), (-44, 40)], (232, 72, 60))
    p.line([(-52, -20), (-26, -50), (26, -50), (52, -20)], (170, 40, 36), 8)
    for i in range(1, 5):
        p.line([(-56 + i * 22, -20), (-48 + i * 19, 40)], (190, 50, 46), 3)


def _calculator(p, t, ex):
    p.rect(-40, -56, 40, 56, (70, 76, 96), r=8)
    p.rect(-32, -48, 32, -22, (160, 230, 190), r=3, width=2)
    p.text(0, -35, ex.get("text") or "100", 20, (30, 70, 50))
    for r in range(3):
        for k in range(3):
            p.rect(-30 + k * 22, -10 + r * 20, -14 + k * 22, 6 + r * 20, (210, 214, 228), r=3, width=2)


def _laptop(p, t, ex):
    p.rect(-62, -52, 62, 22, (50, 54, 66), r=6)
    p.rect(-54, -44, 54, 14, (70, 150, 220), r=2, outline=None)
    for i in range(5):
        p.line([(-44, -34 + i * 11), (-8 + (i % 3) * 30, -34 + i * 11)], (230, 240, 255), 3)
    p.poly([(-76, 22), (76, 22), (66, 38), (-66, 38)], (170, 176, 192))


def _scanner(p, t, ex):
    p.rect(-18, -30, 22, 10, (50, 54, 68), r=6)
    p.rect(-6, 8, 14, 52, (50, 54, 68), r=4)
    p.poly([(-18, 10), (-54, 70), (-4, 70)], (255, 60, 60, 120), outline=None) if int(t * 4) % 2 == 0 else None


def _can(p, t, ex):
    p.rect(-26, -40, 26, 42, (232, 72, 60), r=8)
    p.rect(-26, -14, 26, 14, (255, 255, 255), outline=None)
    p.ell(0, -40, 26, 8, (200, 205, 215))


def _alarm(p, t, ex):
    p.rect(-30, 6, 30, 30, (90, 96, 112), r=4)
    p.poly([(-24, 6), (24, 6), (18, -34), (-18, -34)], (232, 72, 60) if int(t * 4) % 2 == 0 else (255, 140, 120))
    p.line([(-44, -40), (-62, -48)], (255, 90, 80), 5)
    p.line([(44, -40), (62, -48)], (255, 90, 80), 5)


def _price_tag(p, t, ex):
    p.poly([(-50, -26), (24, -26), (56, 0), (24, 26), (-50, 26)], (250, 214, 72))
    p.ell(-34, 0, 6, 6, (255, 255, 255), width=2)
    p.text(2, 0, ex.get("text") or "$1.99", 24, (120, 50, 30))


def _lightbulb(p, t, ex):
    p.ell(0, -12, 30, 32, (255, 236, 130))
    p.rect(-14, 16, 14, 40, (170, 176, 192), r=3)
    for a in range(-60, 61, 30):
        r = math.radians(a - 90)
        p.line([(math.cos(r) * 44, -12 + math.sin(r) * 44), (math.cos(r) * 60, -12 + math.sin(r) * 60)], (250, 214, 72), 5)


def _check(p, t, ex):
    p.ell(0, 0, 44, 44, (96, 190, 110))
    p.line([(-20, 2), (-6, 18), (22, -16)], (255, 255, 255), 12)


def _question(p, t, ex):
    p.text(0, 0, "?", 150, (250, 214, 72))


def _exclam(p, t, ex):
    p.text(0, 0, "!", 150, (232, 72, 60))


def _generic(p, t, ex):
    p.rect(-40, -40, 40, 40, (200, 200, 210), r=6)


_PROPS = {
    "cash_register": _cash_register, "receipt": _receipt, "money": _money, "coins": _coins,
    "magnifier": _magnifier, "clipboard": _clipboard, "document": _document, "tablet": _tablet,
    "phone": _phone, "cctv_camera": _cctv, "box": _box, "cart": _cart, "basket": _basket,
    "calculator": _calculator, "laptop": _laptop, "scanner": _scanner, "can": _can,
    "alarm": _alarm, "price_tag": _price_tag, "lightbulb": _lightbulb, "check_mark": _check,
    "question_mark": _question, "exclamation": _exclam,
}


def prop_anim(animation: str, t: float, appear: float = 0.0) -> tuple[float, float, float, float]:
    """(dx, dy, escala, rotación) unidades de prop para una animación."""
    lt = t - appear
    if animation == "bounce":
        return 0.0, -abs(math.sin(lt * 5)) * 18, 1.0, 0.0
    if animation == "shake":
        return math.sin(lt * 40) * 4, 0.0, 1.0, math.sin(lt * 30) * 4
    if animation == "grow":
        k = min(1.0, max(0.0, lt / 0.45))
        k = 1 + 2.70158 * (k - 1) ** 3 + 1.70158 * (k - 1) ** 2
        return 0.0, 0.0, max(0.01, k), 0.0
    if animation == "slide_in":
        k = min(1.0, max(0.0, lt / 0.5))
        return (1 - (1 - (1 - k) ** 3)) * -160, 0.0, 1.0, 0.0
    if animation == "blink":
        return 0.0, 0.0, 1.0 if int(lt * 3) % 2 == 0 else 0.88, 0.0
    return 0.0, 0.0, 1.0, 0.0
