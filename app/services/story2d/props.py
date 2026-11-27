"""Escenarios y utilería 2D reutilizables (todo vectorial, animado por tiempo)."""
from __future__ import annotations

import math

import skia

from .gfx import (C, P, circ, oval, line, rect, rectp, poly, curve, shadow, shade, mix,
                  text, text_w, clamp, lerp, smooth, ease_out, prog, grad, radial, pulse,
                  rnd, FONT_BOLD, FONT_MONO, FONT_REG)

PRODUCT_COLORS = ["#E74C3C", "#F39C12", "#F1C40F", "#2ECC71", "#3498DB", "#9B59B6",
                  "#E67E22", "#1ABC9C", "#ECF0F1", "#FF6B81"]
GREEN = "#2FA36B"


# ----------------------------------------------------------------- fondo súper
def bg_store(cv, cam_x=540, t=0.0, floor_y=1250, tint=None, dim=0.0, shelves=True):
    x0, x1 = cam_x - 1300, cam_x + 1300
    # pared
    rectp(cv, x0, 0, x1 - x0, floor_y, grad(0, 0, 0, floor_y, "#F4F8FA", "#CFE2E8"))
    # techo
    rect(cv, x0, 0, x1 - x0, 210, "#E3EAEE")
    rect(cv, x0, 198, x1 - x0, 14, "#B9C6CD")
    i0, i1 = int(x0 // 360) - 1, int(x1 // 360) + 1
    for i in range(i0, i1):
        lx = i * 360 + 60
        rect(cv, lx, 70, 240, 34, "#FFFEF0", r=10)
        cv.drawRect(skia.Rect.MakeXYWH(lx - 30, 104, 300, 100),
                    radial(lx + 120, 104, 220, "#FFFBD6", "#FFFBD6", 0.0, 0.0))
        poly(cv, [(lx + 20, 104), (lx + 220, 104), (lx + 330, 700), (lx - 90, 700)], "#FFF6C8", 0.07)
    # carteles colgantes
    names = ["LÁCTEOS", "FRUTAS", "PANADERÍA", "ABARROTES", "BEBIDAS", "CARNES"]
    cols = ["#3498DB", "#2ECC71", "#E67E22", "#E74C3C", "#9B59B6", "#C0392B"]
    for i in range(int(x0 // 540) - 1, int(x1 // 540) + 1):
        sx = i * 540 + 270
        k = i % len(names)
        line(cv, sx - 90, 210, sx - 90, 262, "#7C8A93", 4)
        line(cv, sx + 90, 210, sx + 90, 262, "#7C8A93", 4)
        sway = math.sin(t * 0.8 + i) * 2
        rect(cv, sx - 150 + sway, 262, 300, 78, cols[k], r=14)
        text(cv, names[k], sx + sway, 316, 36, "#FFFFFF")
    if shelves:
        for i in range(int(x0 // 270) - 1, int(x1 // 270) + 1):
            sx = i * 270
            r_ = rnd(i * 31 + 7)
            rect(cv, sx + 6, 420, 258, 14, "#8A97A0", r=3)
            for row, y_ in enumerate((690, 940, 1190)):
                if y_ > floor_y - 4:
                    continue
                rect(cv, sx + 6, y_, 258, 14, "#7C8A93", r=3)
                bx = sx + 14
                while bx < sx + 250:
                    w = r_.choice((34, 42, 50, 58))
                    h = r_.choice((70, 96, 120, 150, 176))
                    col = r_.choice(PRODUCT_COLORS)
                    rect(cv, bx, y_ - h, w - 4, h, col, r=6)
                    rect(cv, bx + 5, y_ - h * 0.55, w - 14, h * 0.22, "#FFFFFF", 0.7, r=3)
                    bx += w
            rect(cv, sx - 4, 420, 10, floor_y - 420, "#6A7780")
    # suelo
    rectp(cv, x0, floor_y, x1 - x0, 1000, grad(0, floor_y, 0, 1920, "#C9D1D8", "#98A3AD"))
    for k in range(0, 9):
        y_ = floor_y + 6 + k * k * 9
        line(cv, x0, y_, x1, y_, "#FFFFFF", 2 + k * 0.4, 0.25)
    for i in range(int(x0 // 180) - 1, int(x1 // 180) + 1):
        x_ = i * 180
        cx_ = cam_x
        poly(cv, [(x_, floor_y), (x_ + 2, floor_y), (cx_ + (x_ - cx_) * 3.2 + 4, 1920), (cx_ + (x_ - cx_) * 3.2, 1920)], "#FFFFFF", 0.14)
    rectp(cv, x0, floor_y, x1 - x0, 130, grad(0, floor_y, 0, floor_y + 130, "#FFFFFF", "#FFFFFF", 0.25, 0.0))
    if tint:
        rect(cv, x0, 0, x1 - x0, 1920, tint[0], tint[1])
    if dim:
        rect(cv, x0, 0, x1 - x0, 1920, "#0A0F1F", dim)


def bg_office(cv, t=0.0, night=False):
    sky = ("#0B1330", "#1B2A5A") if night else ("#BFE3F5", "#E9F6FC")
    rectp(cv, 0, 0, 1080, 1920, grad(0, 0, 0, 1920, "#26324A" if night else "#D5DEE6", "#1B2336" if night else "#B7C3CE"))
    # ventana
    rect(cv, 110, 150, 860, 760, "#5B6674", r=16)
    rectp(cv, 130, 170, 820, 720, grad(0, 170, 0, 890, *sky))
    if night:
        r_ = rnd(5)
        for _ in range(40):
            circ(cv, 140 + r_.random() * 800, 180 + r_.random() * 420, r_.random() * 2.4 + 0.6, "#FFFFFF", 0.4 + 0.5 * pulse(t + r_.random() * 5, 2 + r_.random()))
        circ(cv, 780, 300, 62, "#FFF4C2")
        circ(cv, 806, 286, 54, "#0F1A3E")
        for i in range(9):
            h = 120 + (i * 53) % 180
            rect(cv, 130 + i * 92, 890 - h, 80, h, "#101A38")
            for ry in range(int(h // 40)):
                if (i + ry) % 3:
                    rect(cv, 144 + i * 92, 900 - h + ry * 40, 14, 20, "#F2D27A", 0.8)
    else:
        for i in range(8):
            h = 160 + (i * 67) % 220
            rect(cv, 130 + i * 105, 890 - h, 92, h, "#9FB4C4")
    line(cv, 540, 170, 540, 890, "#5B6674", 10)
    line(cv, 130, 530, 950, 530, "#5B6674", 10)
    # suelo y escritorio
    rectp(cv, 0, 1300, 1080, 620, grad(0, 1300, 0, 1920, "#6B5B4B", "#4A3E33"))


def bill(cv, x, y, rot=0.0, s=1.0, a=1.0, val="$"):
    cv.save()
    cv.translate(x, y)
    cv.rotate(rot)
    cv.scale(s, s)
    if a < 1:
        cv.saveLayerAlpha(None, int(255 * a))
    rect(cv, -56, -28, 112, 56, "#59B36B", r=7)
    rect(cv, -50, -22, 100, 44, "#7BCB8A", r=5)
    circ(cv, 0, 0, 17, "#59B36B")
    text(cv, val, 0, 9, 24, "#EAFBEE")
    circ(cv, -38, 0, 5, "#59B36B")
    circ(cv, 38, 0, 5, "#59B36B")
    if a < 1:
        cv.restore()
    cv.restore()


def coin(cv, x, y, r=22, spin=0.0, a=1.0):
    w = abs(math.cos(spin)) * r
    cv.save()
    if a < 1:
        cv.saveLayerAlpha(None, int(255 * a))
    oval(cv, x, y, max(2, w), r, "#E3A71E")
    oval(cv, x, y, max(1, w * 0.78), r * 0.78, "#F7CB45")
    if w > r * 0.5:
        text(cv, "$", x, y + r * 0.34, r * 0.95, "#C98A0B")
    if a < 1:
        cv.restore()
    cv.restore()


def sparkle(cv, x, y, s, a=1.0, color="#FFE98A"):
    pts = []
    for i in range(8):
        r = s if i % 2 == 0 else s * 0.3
        ang = math.pi / 4 * i - math.pi / 2
        pts.append((x + math.cos(ang) * r, y + math.sin(ang) * r))
    poly(cv, pts, color, a)


# ----------------------------------------------------------------- caja registradora
def register(cv, x, y, s=1.0, t=0.0, drawer=0.0, screen="", screen_color="#7CFFB2",
             alert=0.0, bills_in=True, flip=False):
    """Mostrador + caja (vista frontal/lateral). (x,y) = base centro."""
    cv.save()
    cv.translate(x, y)
    cv.scale(-s if flip else s, s)
    # mostrador
    rect(cv, -330, -250, 660, 250, "#8E5A3C", r=14)
    rect(cv, -330, -262, 660, 34, "#C9885A", r=12)
    rect(cv, -310, -210, 620, 190, "#7A4B30", r=10)
    for i in range(4):
        rect(cv, -290 + i * 150, -196, 130, 160, "#8B5535", r=8)
    # cinta transportadora
    rect(cv, -310, -300, 330, 40, "#3B4048", r=10)
    for i in range(10):
        rect(cv, -300 + i * 34 + (t * 40) % 34 - 34, -296, 4, 32, "#52585F")
    # caja
    rect(cv, 40, -420, 230, 130, "#2F3640", r=14)
    rect(cv, 60, -520, 190, 108, "#232A33", r=10)
    rect(cv, 70, -508, 170, 86, "#0C1A14", r=6)
    if alert > 0:
        rect(cv, 70, -508, 170, 86, "#FF3B3B", 0.35 * alert * (0.6 + 0.4 * pulse(t, 0.35)), r=6)
    if screen:
        text(cv, screen, 155, -452, 34 if len(screen) < 9 else 24, screen_color, font=FONT_MONO)
    for r_ in range(2):
        for c_ in range(4):
            rect(cv, 66 + c_ * 44, -392 + r_ * 38, 36, 28, "#9AA5B1", r=5)
    # cajón
    dr = drawer
    rect(cv, 52, -300 + 0, 206, 34 + 20 * dr, "#59616B", r=6)
    if dr > 0.02:
        rect(cv, 58, -270, 194, 12 + 30 * dr, "#1D2128", r=4)
        if bills_in:
            for i in range(3):
                rect(cv, 66 + i * 54, -266 + 6 * dr, 46, 18, "#59B36B", r=3)
    cv.restore()


# ----------------------------------------------------------------- CCTV / pantallas
def cctv_feed(cv, x, y, w, h, t, mode=0, night=True, label="CAM 01", clipped=True, glitch=0.0,
              hot=None):
    """Dibuja una 'cámara de seguridad' animada (vista cenital del súper)."""
    cv.save()
    r = skia.Rect.MakeXYWH(x, y, w, h)
    cv.clipRRect(skia.RRect.MakeRectXY(r, 14, 14), skia.ClipOp.kIntersect, True)
    base = "#14231E" if night else "#27333B"
    rect(cv, x, y, w, h, base)
    # suelo con baldosas
    for i in range(0, int(w), 46):
        line(cv, x + i, y, x + i, y + h, "#1E3A30" if night else "#364652", 2)
    for j in range(0, int(h), 46):
        line(cv, x, y + j, x + w, y + j, "#1E3A30" if night else "#364652", 2)
    # mostrador y empleados (siluetas cenitales)
    cv.save()
    cv.translate(x, y)
    sc = w / 540
    cv.scale(sc, sc)
    hh = h / sc
    rect(cv, 40, hh * 0.52, 460, 70, "#3B5A4D", r=8)
    rect(cv, 330, hh * 0.52 - 40, 120, 60, "#27403A", r=6)
    # cajero (Darío) visto desde arriba
    px = 300 + math.sin(t * 0.8) * 8
    circ(cv, px, hh * 0.52 + 106, 26, "#C9A96B" if night else "#C98F63")
    circ(cv, px, hh * 0.52 + 106, 18, "#F2B632")
    oval(cv, px, hh * 0.52 + 150, 42, 24, "#2FA36B")
    if mode == 1:  # cliente devuelve producto
        cx_ = 120 + 120 * smooth(prog(t, 0, 1.0))
        circ(cv, cx_, hh * 0.52 - 20, 26, "#B77A52")
        oval(cv, cx_, hh * 0.52 - 64, 40, 22, "#3B82C4")
        rect(cv, cx_ + 40, hh * 0.52 - 8, 26, 22, "#E67E22", r=4)
    cv.restore()
    # ruido y líneas de escaneo
    r_ = rnd(int(t * 24))
    for _ in range(int(40 + 160 * glitch)):
        px_, py_ = x + r_.random() * w, y + r_.random() * h
        rect(cv, px_, py_, r_.random() * 14 + 2, 2, "#FFFFFF", 0.07 + 0.2 * glitch)
    for j in range(0, int(h), 6):
        rect(cv, x, y + j, w, 2, "#000000", 0.18)
    if glitch > 0.2:
        for _ in range(3):
            gy = y + r_.random() * h
            rect(cv, x, gy, w, r_.random() * 18 + 4, "#9BFFD1", 0.25 * glitch)
    cv.drawRect(r, radial(x + w / 2, y + h / 2, max(w, h) * 0.75, "#000000", "#000000", 0.0, 0.55))
    cv.restore()
    rect(cv, x, y, w, h, "#0B0E11", style="stroke", sw=8, r=14)
    # REC + etiqueta
    if int(t * 2) % 2 == 0:
        circ(cv, x + 26, y + 28, 8, "#FF3B3B")
    text(cv, "REC", x + 44, y + 36, 22, "#FFFFFF", "left", font=FONT_MONO)
    text(cv, label, x + w - 14, y + 36, 22, "#9BFFD1", "right", font=FONT_MONO)
    if hot:
        hx, hy, hw, hh_ = hot
        rect(cv, hx, hy, hw, hh_, "#FF3B3B", 0.12)
        rect(cv, hx, hy, hw, hh_, "#FF3B3B", style="stroke", sw=6, r=6)


def monitor_frame(cv, x, y, w, h):
    rect(cv, x - 22, y - 22, w + 44, h + 44, "#1F242B", r=22)
    rect(cv, x - 22, y - 22, w + 44, h + 44, "#3A424C", style="stroke", sw=4, r=22)
    rect(cv, x + w / 2 - 40, y + h + 22, 80, 56, "#2B323A")
    rect(cv, x + w / 2 - 130, y + h + 72, 260, 18, "#2B323A", r=9)


def paper(cv, x, y, w, h, rot=0.0, lines=5, a=1.0, header=None, color="#FFFFFF", s=1.0):
    cv.save()
    cv.translate(x, y)
    cv.rotate(rot)
    cv.scale(s, s)
    if a < 1:
        cv.saveLayerAlpha(None, int(255 * a))
    rect(cv, -w / 2 + 6, -h / 2 + 8, w, h, "#000000", 0.18, r=6)
    rect(cv, -w / 2, -h / 2, w, h, color, r=6)
    if header:
        text(cv, header, 0, -h / 2 + 34, 24, "#2B3440")
    for i in range(lines):
        yy = -h / 2 + 62 + i * 26
        if yy > h / 2 - 20:
            break
        line(cv, -w / 2 + 22, yy, w / 2 - 22 - (i % 3) * 30, yy, "#B8C2CC", 5)
    if a < 1:
        cv.restore()
    cv.restore()


def check(cv, x, y, s, color="#2ECC71", p=1.0, w=14):
    pts = [(x - s * 0.5, y), (x - s * 0.12, y + s * 0.42), (x + s * 0.55, y - s * 0.45)]
    path = skia.Path()
    if p <= 0:
        return
    path.moveTo(*pts[0])
    if p < 0.4:
        k = p / 0.4
        path.lineTo(lerp(pts[0][0], pts[1][0], k), lerp(pts[0][1], pts[1][1], k))
    else:
        path.lineTo(*pts[1])
        k = (p - 0.4) / 0.6
        path.lineTo(lerp(pts[1][0], pts[2][0], k), lerp(pts[1][1], pts[2][1], k))
    cv.drawPath(path, P(color, 1, "stroke", w))


def cross(cv, x, y, s, color="#E74C3C", p=1.0, w=14):
    if p <= 0:
        return
    k = min(1, p * 2)
    line(cv, x - s / 2, y - s / 2, x - s / 2 + s * k, y - s / 2 + s * k, color, w)
    if p > 0.5:
        k = (p - 0.5) * 2
        line(cv, x + s / 2, y - s / 2, x + s / 2 - s * k, y - s / 2 + s * k, color, w)


def question(cv, x, y, s, a=1.0, color="#FFD166"):
    text(cv, "?", x, y, s, color, outline="#7A4B00", outline_w=s * 0.1, a=a)


def bubble(cv, x, y, w, h, s_text, tail=(0, 40), size=40, color="#FFFFFF", tcolor="#222831", a=1.0, scale=1.0):
    cv.save()
    cv.translate(x, y)
    cv.scale(scale, scale)
    rect(cv, -w / 2, -h / 2, w, h, "#000000", 0.15 * a, r=h / 2.2)
    rect(cv, -w / 2, -h / 2 - 4, w, h, color, a, r=h / 2.2)
    poly(cv, [(tail[0] - 18, h / 2 - 8), (tail[0] + 18, h / 2 - 8), (tail[0], h / 2 + tail[1])], color, a)
    text(cv, s_text, 0, size * 0.35 - 4, size, tcolor, a=a)
    cv.restore()


def magnifier(cv, x, y, r=70, rot=-40, a=1.0):
    cv.save()
    cv.translate(x, y)
    cv.rotate(rot)
    line(cv, 0, r, 0, r + 120, "#5B3A22", 20)
    line(cv, 0, r + 20, 0, r + 95, "#8A5A35", 14)
    circ(cv, 0, 0, r, "#BDE7FF", 0.28 * a)
    circ(cv, 0, 0, r, "#C9CED6", style="stroke", w=16)
    circ(cv, 0, 0, r + 6, "#6B7280", style="stroke", w=3)
    cv.restore()


def hud_card(cv, x, y, w, h, title, value, color="#FF5A5A", a=1.0, sub=None):
    cv.save()
    if a < 1:
        cv.saveLayerAlpha(None, int(255 * a))
    rect(cv, x - w / 2, y - h / 2, w, h, "#0E141C", 0.86, r=26)
    rect(cv, x - w / 2, y - h / 2, w, h, color, 0.9, style="stroke", sw=4, r=26)
    text(cv, title, x, y - h / 2 + 40, 28, "#C7D0DA", font=FONT_BOLD)
    text(cv, value, x, y + h / 2 - 30 - (18 if sub else 0), 68, color, font=FONT_MONO)
    if sub:
        text(cv, sub, x, y + h / 2 - 20, 22, "#8FA0B3")
    if a < 1:
        cv.restore()
    cv.restore()


def money_fmt(v, sign=""):
    return f"{sign}${int(round(v)):,}"


def vignette(cv, strength=0.45, W=1080, H=1920):
    cv.drawRect(skia.Rect.MakeXYWH(0, 0, W, H),
                radial(W / 2, H / 2, 1250, "#000000", "#000000", 0.0, strength))


def stamp(cv, x, y, label, color="#E74C3C", rot=-12, s=1.0, a=1.0, size=64):
    cv.save()
    cv.translate(x, y)
    cv.rotate(rot)
    cv.scale(s, s)
    w = text_w(label, size) + 70
    rect(cv, -w / 2, -size * 0.8, w, size * 1.5, color, style="stroke", sw=10, r=14, a=a)
    rect(cv, -w / 2 + 12, -size * 0.8 + 12, w - 24, size * 1.5 - 24, color, style="stroke", sw=3, r=8, a=a * 0.8)
    text(cv, label, 0, size * 0.3, size, color, a=a)
    cv.restore()
