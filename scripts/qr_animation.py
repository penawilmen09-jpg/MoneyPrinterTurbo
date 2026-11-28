"""Animated 2D explainer renderer ("¿Cómo funcionan los códigos QR?").

Draws every frame in code with Skia (free, CPU only), pipes the frames to
FFmpeg and outputs a silent 1080x1920 (9:16) MP4. Scene timing follows the
Whisper subtitle timeline of the ElevenLabs narration.

Usage: python scripts/qr_animation.py OUT.mp4 [--frames A:B] [--png DIR T1,T2..]
"""
import math
import os
import random
import subprocess
import sys

import numpy as np
import qrcode
import skia

W, H, FPS = 1080, 1920, 30
DURATION = 55.0
FONT_PATH = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
FONT_HEAVY = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"

# global scene starts (seconds) -- from the narration subtitle timeline
SCENES = [0.0, 7.3, 14.0, 22.9, 32.1, 42.7, 55.5]

# ------------------------------------------------------------------ helpers
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def pr(t, a, b):
    return clamp((t - a) / (b - a))


def eo(x):
    return 1 - (1 - x) ** 3


def eio(x):
    return x * x * (3 - 2 * x)


def eb(x):
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def lerp(a, b, x):
    return a + (b - a) * x


def col(h, a=1.0):
    h = h.lstrip("#")
    return skia.ColorSetARGB(int(clamp(a) * 255), int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


NAVY, NAVY2 = "#0B1230", "#1D2D68"
CYAN, AMBER, PINK, GREEN, WHITE, RED = "#3DE0FF", "#FFC53D", "#FF5C93", "#5CFFB0", "#FFFFFF", "#FF4D4D"
VIOLET = "#9B7BFF"


def P(color=WHITE, a=1.0, stroke=0, blur=0, cap=True, shader=None):
    p = skia.Paint(AntiAlias=True)
    if shader is not None:
        p.setShader(shader)
    else:
        p.setColor(col(color, a))
    if stroke:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(stroke)
        if cap:
            p.setStrokeCap(skia.Paint.kRound_Cap)
            p.setStrokeJoin(skia.Paint.kRound_Join)
    if blur:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p


_fonts = {}


def font(size, heavy=False):
    k = (round(size), heavy)
    if k not in _fonts:
        tf = skia.Typeface.MakeFromFile(FONT_HEAVY if heavy else FONT_PATH)
        _fonts[k] = skia.Font(tf, size)
    return _fonts[k]


def text(c, s, x, y, size, color=WHITE, a=1.0, align="c", heavy=False):
    f = font(size, heavy)
    w = f.measureText(s)
    if align == "c":
        x -= w / 2
    elif align == "r":
        x -= w
    c.drawString(s, x, y, f, P(color, a))
    return w


def rrect(c, x, y, w, h, r, paint):
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r), paint)


def chip(c, s, cx, cy, color=CYAN, a=1.0, size=44, scale=1.0, fill_dark=True):
    if a <= 0.01 or scale <= 0.01:
        return
    c.save()
    c.translate(cx, cy)
    c.scale(scale, scale)
    f = font(size, True)
    w = f.measureText(s) + size * 1.4
    h = size * 1.9
    rrect(c, -w / 2, -h / 2, w, h, h / 2, P("#0B1230" if fill_dark else color, 0.85 * a))
    rrect(c, -w / 2, -h / 2, w, h, h / 2, P(color, a, stroke=4))
    text(c, s, 0, size * 0.36, size, color if fill_dark else NAVY, a, heavy=True)
    c.restore()


def line(c, x0, y0, x1, y1, paint):
    c.drawLine(x0, y0, x1, y1, paint)


def glow_circle(c, x, y, r, color, a=0.6):
    c.drawCircle(x, y, r, P(color, a, blur=r * 0.45))


def star(c, x, y, r, color, a=1.0, rot=0):
    path = skia.Path()
    for i in range(8):
        ang = rot + i * math.pi / 4
        rr = r if i % 2 == 0 else r * 0.22
        px, py = x + math.cos(ang) * rr, y + math.sin(ang) * rr
        path.moveTo(px, py) if i == 0 else path.lineTo(px, py)
    path.close()
    c.drawPath(path, P(color, a))


def gear(c, x, y, r, teeth, rot, color, a=1.0):
    c.save()
    c.translate(x, y)
    c.rotate(math.degrees(rot))
    for i in range(teeth):
        c.save()
        c.rotate(360 / teeth * i)
        rrect(c, -r * 0.14, -r * 1.12, r * 0.28, r * 0.3, 4, P(color, a))
        c.restore()
    c.drawCircle(0, 0, r, P(color, a))
    c.drawCircle(0, 0, r * 0.42, P(NAVY, a))
    c.restore()


def bezier(p0, p1, p2, u):
    return (
        (1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * p1[0] + u * u * p2[0],
        (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * p1[1] + u * u * p2[1],
    )


# ------------------------------------------------------------------ QR data
_q = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, border=0, box_size=1)
_q.add_data("https://qr.es/hi")
_q.make(fit=False)
M = _q.get_matrix()
N = len(M)  # 21
URL_TEXT = "https://qr.es/hi"


def zone(r, c):
    if (r < 7 and c < 7) or (r < 7 and c >= N - 7) or (r >= N - 7 and c < 7):
        return "finder"
    if (r < 8 and c < 8) or (r < 8 and c >= N - 8) or (r >= N - 8 and c < 8):
        return "sep"
    if (r == 6 or c == 6) and 8 <= max(r, c) <= N - 9:
        return "timing"
    if (r == 8 and (c < 9 or c >= N - 8)) or (c == 8 and (r < 9 or r >= N - 7)):
        return "format"
    return "data"


ZCOL = {"finder": CYAN, "sep": CYAN, "timing": AMBER, "format": PINK, "data": WHITE}


def qr_geom(cx, cy, cell):
    s = N * cell
    return cx - s / 2, cy - s / 2


def draw_qr(c, cx, cy, cell, fn=None, card=True, pad=None, card_a=1.0):
    """fn(r, col, x, y, cell, v) draws a module; return True if handled."""
    pad = cell * 1.6 if pad is None else pad
    x0, y0 = qr_geom(cx, cy, cell)
    if card:
        s = N * cell + 2 * pad
        rrect(c, cx - s / 2, cy - s / 2, s, s, cell * 1.2, P("#000000", 0.35 * card_a, blur=cell * 0.9))
        rrect(c, cx - s / 2, cy - s / 2, s, s, cell * 1.2, P("#FFFFFF", card_a))
    for r in range(N):
        for k in range(N):
            v = M[r][k]
            x, y = x0 + k * cell, y0 + r * cell
            if fn and fn(r, k, x, y, cell, v):
                continue
            if v:
                c.drawRect(skia.Rect.MakeXYWH(x, y, cell + 0.6, cell + 0.6), P("#0B1230"))


# ------------------------------------------------------------------ background
_bg_cache = {}


def bg(c, t, top=NAVY, bottom=NAVY2, accent=CYAN):
    k = (top, bottom)
    if k not in _bg_cache:
        _bg_cache[k] = skia.GradientShader.MakeLinear(
            [skia.Point(0, 0), skia.Point(0, H)], [col(top), col(bottom)]
        )
    c.drawRect(skia.Rect.MakeWH(W, H), P(shader=_bg_cache[k]))
    # drifting soft blobs
    for i, (bx, by, br, bc) in enumerate([(200, 400, 420, accent), (900, 1100, 480, VIOLET), (500, 1500, 400, PINK)]):
        ox = math.sin(t * 0.35 + i * 2) * 60
        oy = math.cos(t * 0.3 + i) * 60
        c.drawCircle(bx + ox, by + oy, br, P(bc, 0.07, blur=140))
    # parallax dot grid
    off = (t * 18) % 90
    p = P(WHITE, 0.07)
    for gx in range(-1, 14):
        for gy in range(-1, 24):
            c.drawCircle(gx * 90 + off, gy * 90 + off * 0.6, 3, p)


def title(c, s, t, t0=0.0, y=150, color=WHITE):
    k = eb(pr(t, t0, t0 + 0.6))
    if k <= 0.01:
        return
    c.save()
    c.translate(W / 2, y)
    c.scale(k, k)
    text(c, s, 0, 0, 62, color, clamp(k), heavy=True)
    c.restore()


# ------------------------------------------------------------------ scene 1
def phone(c, cx, cy, w, h, rot=0, screen=None, glow=0.0):
    c.save()
    c.translate(cx, cy)
    c.rotate(rot)
    rrect(c, -w / 2 - 6, -h / 2 - 6, w + 12, h + 12, w * 0.16, P("#000000", 0.45, blur=18))
    rrect(c, -w / 2, -h / 2, w, h, w * 0.14, P("#1B1F33"))
    rrect(c, -w / 2, -h / 2, w, h, w * 0.14, P("#8FA0E8", 0.8, stroke=5))
    sw, sh = w * 0.88, h * 0.93
    rrect(c, -sw / 2, -sh / 2, sw, sh, w * 0.1, P("#0A0F25"))
    if glow:
        rrect(c, -sw / 2, -sh / 2, sw, sh, w * 0.1, P(CYAN, glow * 0.25))
    c.drawCircle(0, -h / 2 + h * 0.035, w * 0.03, P("#3A4170"))
    if screen:
        c.save()
        c.clipRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-sw / 2, -sh / 2, sw, sh), w * 0.1, w * 0.1), skia.ClipOp.kIntersect, True)
        screen(c, sw, sh)
        c.restore()
    c.restore()


def brackets(c, cx, cy, size, color, a=1.0, sw=10, k=1.0):
    h = size / 2 * k
    L = size * 0.2
    p = P(color, a, stroke=sw)
    for sx in (-1, 1):
        for sy in (-1, 1):
            c.drawPath(
                skia.Path().moveTo(cx + sx * h, cy + sy * (h - L)).lineTo(cx + sx * h, cy + sy * h).lineTo(cx + sx * (h - L), cy + sy * h),
                p,
            )


def hand_phone_scene(c, t):
    pass


def scene1(c, t):
    bg(c, t, "#17102E", "#3A1F4F", AMBER)
    # camera push toward the QR card
    zoom = 1.0 + 0.85 * eio(pr(t, 3.0, 6.0))
    fx = lerp(W / 2, 560, eio(pr(t, 3.0, 6.0)))
    fy = lerp(H / 2, 1010, eio(pr(t, 3.0, 6.0)))
    fade_out = 1 - eio(pr(t, 6.3, 7.1))
    c.save()
    c.translate(W / 2, H / 2)
    c.scale(zoom, zoom)
    c.translate(-fx, -fy)

    # pendant lamp
    sw = math.sin(t * 1.4) * 0.06
    c.save()
    c.translate(540, 0)
    c.rotate(math.degrees(sw))
    line(c, 0, 0, 0, 330, P("#C9B8E8", 0.7, stroke=4))
    path = skia.Path().moveTo(-130, 440).lineTo(-50, 330).lineTo(50, 330).lineTo(130, 440).close()
    c.drawPath(path, P("#FFC53D"))
    c.drawCircle(0, 450, 150, P("#FFD97A", 0.28, blur=60))
    c.drawOval(skia.Rect.MakeXYWH(-120, 430, 240, 26), P("#FFF3C4"))
    c.restore()
    # window
    rrect(c, 60, 560, 280, 400, 24, P("#0B1230", 0.8))
    rrect(c, 60, 560, 280, 400, 24, P("#8FA0E8", 0.5, stroke=6))
    line(c, 200, 560, 200, 960, P("#8FA0E8", 0.5, stroke=5))
    line(c, 60, 760, 340, 760, P("#8FA0E8", 0.5, stroke=5))
    for i in range(9):
        c.drawCircle(100 + (i * 83) % 220, 600 + (i * 47) % 130, 3.5, P(WHITE, 0.4 + 0.4 * math.sin(t * 2 + i)))
    # person (bust)
    bob = math.sin(t * 2.0) * 4
    c.drawOval(skia.Rect.MakeXYWH(400, 720 + bob, 280, 360), P("#4A6CF7"))
    rrect(c, 495, 690 + bob, 90, 70, 20, P("#E8B08E"))
    c.drawOval(skia.Rect.MakeXYWH(440, 480 + bob, 200, 240), P("#F2C29F"))
    c.drawOval(skia.Rect.MakeXYWH(428, 455 + bob, 224, 140), P("#3A2A22"))
    look = eio(pr(t, 1.2, 2.6))
    for ex in (500, 580):
        c.drawOval(skia.Rect.MakeXYWH(ex - 20, 590 + bob, 40, 46), P(WHITE))
        c.drawCircle(ex + 3, 614 + bob + 8 * look, 11, P("#1B1F33"))
    # blink
    if (t % 3.2) < 0.12:
        for ex in (500, 580):
            c.drawOval(skia.Rect.MakeXYWH(ex - 20, 590 + bob, 40, 46), P("#F2C29F"))
            line(c, ex - 20, 614 + bob, ex + 20, 614 + bob, P("#1B1F33", stroke=5))
    line(c, 520, 670 + bob, 560, 670 + bob + 4 * look, P("#7A3F34", stroke=6))
    # table
    rrect(c, -100, 1040, W + 200, 520, 40, P("#8A5A3B"))
    rrect(c, -100, 1040, W + 200, 36, 18, P("#B77E57"))
    for i in range(6):
        line(c, -100, 1120 + i * 70, W + 100, 1120 + i * 70, P("#7A4C30", 0.6, stroke=3))
    # plate + cup
    c.drawOval(skia.Rect.MakeXYWH(110, 1120, 250, 70), P("#F5F5FF"))
    c.drawOval(skia.Rect.MakeXYWH(150, 1132, 170, 44), P("#DADCF2"))
    rrect(c, 770, 1060, 130, 120, 22, P("#F5F5FF"))
    c.drawOval(skia.Rect.MakeXYWH(770, 1050, 130, 36), P("#5B3A29"))
    c.drawPath(skia.Path().addArc(skia.Rect.MakeXYWH(880, 1085, 54, 62), -90, 180), P("#F5F5FF", stroke=12))
    for i in range(3):
        sp = skia.Path().moveTo(805 + i * 28, 1040)
        for k in range(1, 7):
            sp.lineTo(805 + i * 28 + math.sin(t * 2.5 + k * 0.9 + i) * 10, 1040 - k * 22)
        c.drawPath(sp, P(WHITE, 0.35, stroke=6))
    # QR tent card
    cell = 11.5
    pop = eb(pr(t, 0.1, 0.8))
    c.save()
    c.translate(560, 1060)
    c.scale(pop, pop)
    c.translate(-560, -1060)
    cx, cy = 560, 905
    s = N * cell + 36
    path = skia.Path().moveTo(cx - s / 2 - 20, 1070).lineTo(cx - s / 2, cy - s / 2).lineTo(cx + s / 2, cy - s / 2).lineTo(cx + s / 2 + 20, 1070).close()
    c.drawPath(path, P("#000000", 0.3, blur=14))
    rrect(c, cx - s / 2, cy - s / 2, s, s + 110, 14, P("#F5F5FF"))
    draw_qr(c, cx, cy, cell, card=False, pad=0)
    text(c, "MENÚ", cx, cy + s / 2 + 70, 40, "#0B1230", heavy=True)
    # scan line across QR
    sp_ = pr(t, 4.6, 6.1)
    if 0 < sp_ < 1:
        y = lerp(cy - s / 2 + 10, cy + s / 2 - 10, (math.sin(sp_ * math.pi * 3 - math.pi / 2) + 1) / 2)
        c.drawRect(skia.Rect.MakeXYWH(cx - s / 2, y - 6, s, 12), P(CYAN, 0.9, blur=6))
        c.drawRect(skia.Rect.MakeXYWH(cx - s / 2, y - 2, s, 4), P(WHITE, 0.95))
    c.restore()
    # phone with beam
    pk = eo(pr(t, 2.2, 3.4))
    if pk > 0:
        px, py = lerp(900, 800, pk), lerp(2000, 1330, pk) + math.sin(t * 2.4) * 6
        rot = -12
        # beam
        a = 0.22 * pk
        beam = skia.Path().moveTo(px - 10, py - 190).lineTo(560 - 120, 905).lineTo(560 + 120, 905).lineTo(px + 40, py - 190).close()
        c.drawPath(beam, P(CYAN, a, blur=3))
        # hand
        c.drawOval(skia.Rect.MakeXYWH(px - 80, py + 130, 190, 150), P("#F2C29F"))

        def scr(cc, sw_, sh_):
            cc.drawRect(skia.Rect.MakeXYWH(-sw_ / 2, -sh_ / 2, sw_, sh_), P("#101830"))
            draw_qr(cc, 0, 0, 7.2, card=False, pad=0)
            brackets(cc, 0, 0, 210, CYAN, 1.0, 6, 1.0 + 0.08 * math.sin(t * 6))

        phone(c, px, py, 250, 500, rot, scr if pk > 0.5 else None, 0.6 if sp_ > 0 else 0)
        c.drawOval(skia.Rect.MakeXYWH(px - 90, py + 60, 90, 70), P("#F2C29F"))
    c.restore()

    # HUD (screen space)
    # thought bubble with question marks
    qa = fade_out * (1 - eio(pr(t, 3.4, 4.4)))
    if qa > 0.01:
        for i, (qx, qy, qs) in enumerate([(230, 470, 120), (840, 400, 150), (680, 270, 100), (330, 300, 90)]):
            k = eb(pr(t, 0.4 + i * 0.35, 1.0 + i * 0.35))
            yy = qy + math.sin(t * 2.5 + i) * 12
            text(c, "?", qx, yy, qs * k, [AMBER, PINK, CYAN, GREEN][i], qa, heavy=True)
    # counter of modules
    ca = eio(pr(t, 3.2, 3.9)) * fade_out
    if ca > 0.01:
        n = int(441 * eio(pr(t, 3.4, 5.6)))
        chip(c, f"{n} cuadritos", W / 2, 1340, AMBER, ca, 56)
    # web page pops out
    wk = eb(pr(t, 6.0, 6.8))
    if wk > 0:
        c.save()
        c.translate(W / 2, 760)
        c.scale(wk, wk)
        rrect(c, -380, -330, 760, 660, 36, P("#000000", 0.4, blur=24))
        rrect(c, -380, -330, 760, 660, 36, P("#F5F7FF"))
        rrect(c, -380, -330, 760, 90, 36, P("#DCE2FF"))
        for i, cc in enumerate(["#FF5C93", "#FFC53D", "#5CFFB0"]):
            c.drawCircle(-330 + i * 44, -285, 13, P(cc))
        rrect(c, -190, -310, 540, 50, 25, P(WHITE))
        text(c, "https://qr.es/hi", 60, -275, 32, "#3B4A8A", heavy=True)
        rrect(c, -330, -190, 660, 230, 24, P("#3D6BFF"))
        c.drawCircle(-230, -75, 60, P("#FFD97A"))
        c.drawPath(skia.Path().moveTo(-330, 40).lineTo(-120, -110).lineTo(40, -10).lineTo(150, -90).lineTo(330, 40).close(), P("#2548C9"))
        for i in range(3):
            rrect(c, -330, 80 + i * 70, 660 - i * 140, 36, 18, P("#C5CCEE"))
        c.restore()
    # flying modules into the page
    fp = pr(t, 5.9, 6.9)
    if 0 < fp < 1:
        rnd = random.Random(5)
        for i in range(70):
            u = clamp(fp * 1.4 - rnd.random() * 0.4)
            if u <= 0 or u >= 1:
                continue
            sx, sy = rnd.uniform(400, 700), rnd.uniform(850, 1250)
            ex, ey = W / 2 + rnd.uniform(-250, 250), 760 + rnd.uniform(-200, 200)
            x, y = bezier((sx, sy), (sx + rnd.uniform(-200, 200), 500), (ex, ey), eio(u))
            rrect(c, x - 9, y - 9, 18, 18, 4, P(CYAN if i % 2 else WHITE, 1 - u * 0.6))


# ------------------------------------------------------------------ scene 2
def scene2(c, t):
    bg(c, t, "#0B1230", "#22337A", CYAN)
    cell = 30.0
    cx, cy = W / 2, 770
    k = eb(pr(t, 0.0, 0.7))
    title_txt = "¿Solo un dibujo?" if t < 4.7 else "¡Cada módulo tiene una función!"
    if t < 2.0:
        title_txt = "Parece un dibujo..."
    if 2.0 <= t < 4.7:
        title_txt = "Información codificada"
    title(c, title_txt, t, 0.0, 190, WHITE if t < 4.7 else AMBER)
    c.save()
    c.translate(cx, cy)
    c.scale(k, k)
    c.rotate(math.sin(t * 1.1) * 1.6)
    c.translate(-cx, -cy)

    def fn(r, kk, x, y, cell, v):
        ap = pr(t, 0.2 + (r + kk) * 0.02, 0.5 + (r + kk) * 0.02)
        fl = pr(t, 2.0 + (r + kk) * 0.045, 2.5 + (r + kk) * 0.045)
        fl2 = pr(t, 4.7 + (r * 0.5 + kk * 0.5) * 0.03, 5.1 + (r * 0.5 + kk * 0.5) * 0.03)
        if ap <= 0:
            return True
        z = zone(r, kk)
        mx, my = x + cell / 2, y + cell / 2
        if fl2 > 0 and t >= 4.7:
            base = ZCOL[z]
            pulse = 0.5 + 0.5 * math.sin(t * 5 - (r + kk) * 0.4) if z != "data" else 0
            s = cell * (0.92 + 0.08 * pulse)
            if v:
                c.drawRect(skia.Rect.MakeXYWH(mx - s / 2, my - s / 2, s, s), P(base, 0.95))
                if z != "data":
                    c.drawRect(skia.Rect.MakeXYWH(mx - s / 2, my - s / 2, s, s), P(base, 0.55 * pulse, blur=8))
            else:
                c.drawRect(skia.Rect.MakeXYWH(mx - s / 2, my - s / 2, s, s), P(base, 0.12 if z == "data" else 0.22))
            return True
        if fl > 0:
            # flip to a bit glyph
            sx = abs(math.cos(fl * math.pi))
            c.drawRect(skia.Rect.MakeXYWH(x, y, cell + 0.6, cell + 0.6), P("#101A45", 0.95))
            if fl < 0.5:
                if v:
                    c.drawRect(skia.Rect.MakeXYWH(mx - cell / 2 * sx, y, cell * sx, cell), P("#0B1230"))
                else:
                    c.drawRect(skia.Rect.MakeXYWH(mx - cell / 2 * sx, y, cell * sx, cell), P(WHITE))
            else:
                text(c, "1" if v else "0", mx, my + 10, 28 * sx + 2, CYAN if v else "#6C7DB8", 1.0, heavy=True)
            return True
        if v:
            c.drawRect(skia.Rect.MakeXYWH(x, y, cell + 0.6, cell + 0.6), P("#0B1230", clamp(ap)))
        return True

    show_card = t < 4.7
    draw_qr(c, cx, cy, cell, fn, card=True, card_a=1.0 if show_card else 0.0)
    if not show_card:
        s = N * cell + 2 * cell * 1.6
        rrect(c, cx - s / 2, cy - s / 2, s, s, cell * 1.2, P("#0A1030", 0.9))
        rrect(c, cx - s / 2, cy - s / 2, s, s, cell * 1.2, P(CYAN, 0.35, stroke=4))
        draw_qr(c, cx, cy, cell, fn, card=False)
    c.restore()
    # legend
    leg = [("Posición", CYAN), ("Sincronía", AMBER), ("Formato", PINK), ("Datos", WHITE)]
    for i, (s, cc) in enumerate(leg):
        lx = 290 + (i % 2) * 500
        ly = 1250 + (i // 2) * 110
        kk = eb(pr(t, 5.0 + i * 0.28, 5.6 + i * 0.28))
        if kk > 0:
            chip(c, s, lx, ly, cc, 1.0, 40, kk)


# ------------------------------------------------------------------ scene 3
def scene3(c, t):
    bg(c, t, "#0A1030", "#1E2C6B", CYAN)
    cell = 28.0
    cx, cy = W / 2, 760
    if t < 4.0:
        ang = 28 + math.sin(t * 1.5) * 2.5
    elif t < 6.3:
        ang = lerp(28, 0, eio(pr(t, 4.0, 6.3)))
    elif t < 7.7:
        ang = 0
    else:
        u = t - 7.7
        ang = 34 * math.sin(u * math.pi * 2.0) * (1 - pr(t, 8.4, 8.9))
    if t < 3.9:
        ttl, tc = "Tres cuadrados grandes", CYAN
    elif t < 7.6:
        ttl, tc = "Posición y orientación", AMBER
    else:
        ttl, tc = "¡Aunque esté inclinado!", GREEN
    title(c, ttl, t, 0.0, 190, tc)
    x0, y0 = qr_geom(cx, cy, cell)
    centers = {
        "TL": (x0 + 3.5 * cell, y0 + 3.5 * cell),
        "TR": (x0 + (N - 3.5) * cell, y0 + 3.5 * cell),
        "BL": (x0 + 3.5 * cell, y0 + (N - 3.5) * cell),
    }
    c.save()
    c.translate(cx, cy)
    c.rotate(ang)
    c.translate(-cx, -cy)
    pulse_t = {"TL": 0.4, "TR": 1.4, "BL": 2.4}

    def fn(r, kk, x, y, cell, v):
        if zone(r, kk) != "finder":
            return False
        key = "TL" if (r < 7 and kk < 7) else ("TR" if kk >= N - 7 else "BL")
        glow = clamp(1 - abs(t - pulse_t[key] - 0.4) / 0.9) if t < 3.9 else (0.5 + 0.5 * math.sin(t * 4)) * 0.6
        if v:
            c.drawRect(skia.Rect.MakeXYWH(x, y, cell + 0.6, cell + 0.6), P(lerp_hex("#0B1230", CYAN, 0.9 if t > pulse_t[key] else 0.0) if glow >= 0 else "#0B1230"))
        return True

    draw_qr(c, cx, cy, cell, fn)
    # rings expanding on finders (in rotated space)
    for i, key in enumerate(("TL", "TR", "BL")):
        u = (t - pulse_t[key]) / 1.1
        if 0 < u < 1:
            px, py = centers[key]
            c.drawCircle(px, py, lerp(60, 190, eo(u)), P(CYAN, 1 - u, stroke=8))
            c.drawCircle(px, py, lerp(30, 120, eo(u)), P(WHITE, (1 - u) * 0.8, stroke=4))
        if t > pulse_t[key] + 0.2:
            kk = eb(pr(t, pulse_t[key] + 0.2, pulse_t[key] + 0.7))
            px, py = centers[key]
            bx, by = (px - 100, py - 100) if key == "TL" else ((px + 100, py - 100) if key == "TR" else (px - 100, py + 100))
            c.save()
            c.translate(bx, by)
            c.rotate(-ang)
            c.scale(kk, kk)
            c.drawCircle(0, 0, 36, P(AMBER))
            text(c, str(i + 1), 0, 14, 44, NAVY, heavy=True)
            c.restore()
    # triangle + axes
    tp = eio(pr(t, 4.0, 5.2))
    if tp > 0:
        a_, b_, c_ = centers["TL"], centers["TR"], centers["BL"]
        dash = skia.DashPathEffect.Make([22, 16], -t * 60)
        pt = P(WHITE, 0.8 * tp, stroke=5)
        pt.setPathEffect(dash)
        pth = skia.Path().moveTo(*a_).lineTo(a_[0] + (b_[0] - a_[0]) * tp, a_[1] + (b_[1] - a_[1]) * tp)
        c.drawPath(pth, pt)
        pth = skia.Path().moveTo(*a_).lineTo(a_[0] + (c_[0] - a_[0]) * tp, a_[1] + (c_[1] - a_[1]) * tp)
        c.drawPath(pth, pt)
        pth = skia.Path().moveTo(*b_).lineTo(b_[0] + (c_[0] - b_[0]) * tp, b_[1] + (c_[1] - b_[1]) * tp)
        c.drawPath(pth, pt)
        ap = eio(pr(t, 5.2, 6.2))
        if ap > 0:
            ex = (a_[0] + (b_[0] - a_[0]) * ap, a_[1])
            ey = (a_[0], a_[1] + (c_[1] - a_[1]) * ap)
            line(c, a_[0], a_[1], ex[0], ex[1], P(AMBER, 1, stroke=10))
            line(c, a_[0], a_[1], ey[0], ey[1], P(PINK, 1, stroke=10))
            c.drawPath(skia.Path().moveTo(ex[0] - 22, ex[1] - 20).lineTo(ex[0] + 14, ex[1]).lineTo(ex[0] - 22, ex[1] + 20).close(), P(AMBER))
            c.drawPath(skia.Path().moveTo(ey[0] - 20, ey[1] - 22).lineTo(ey[0], ey[1] + 14).lineTo(ey[0] + 20, ey[1] - 22).close(), P(PINK))
    c.restore()
    # viewfinder brackets (screen space), scanning confirmation
    brackets(c, cx, cy, N * cell + 150, WHITE, 0.9, 9, 1.0 + 0.02 * math.sin(t * 5))
    if t > 6.2:
        chip(c, "Posición ✓", 300, 1230, AMBER, eio(pr(t, 6.2, 6.7)), 42)
        chip(c, "Orientación ✓", 730, 1230, PINK, eio(pr(t, 6.5, 7.0)), 42)
    if t > 7.7:
        chip(c, "Lectura correcta", W / 2, 1350, GREEN, eio(pr(t, 7.9, 8.4)), 46)


def lerp_hex(a, b, x):
    a, b = a.lstrip("#"), b.lstrip("#")
    r = [int(int(a[i:i + 2], 16) * (1 - x) + int(b[i:i + 2], 16) * x) for i in (0, 2, 4)]
    return "#%02x%02x%02x" % tuple(r)


# ------------------------------------------------------------------ scene 4
_rnd4 = random.Random(11)
_jit = [[(_rnd4.uniform(-90, 90), _rnd4.uniform(0, 160)) for _ in range(N)] for _ in range(N)]


def scene4(c, t):
    bg(c, t, "#0A0F2E", "#1A2A63", VIOLET)
    cell = 25.0
    cx, cy = W / 2, 540
    if t < 2.4:
        ttl, tc = "Una cuadrícula de módulos", WHITE
    elif t < 6.7:
        ttl, tc = "Módulos → 0 y 1", CYAN
    else:
        ttl, tc = "Datos reconstruidos", GREEN
    title(c, ttl, t, 0.0, 160, tc)
    x0, y0 = qr_geom(cx, cy, cell)
    scan_start, row_dt = 2.1, 0.21
    cur_row = (t - scan_start) / row_dt

    def fn(r, kk, x, y, cell, v):
        done = t >= scan_start + (r + 1) * row_dt
        if v:
            c.drawRect(skia.Rect.MakeXYWH(x, y, cell + 0.6, cell + 0.6), P("#0B1230" if not done else "#13214F"))
            if done:
                c.drawRect(skia.Rect.MakeXYWH(x + 3, y + 3, cell - 6, cell - 6), P(CYAN, 0.35))
        elif done:
            c.drawRect(skia.Rect.MakeXYWH(x + 6, y + 6, cell - 12, cell - 12), P("#6C7DB8", 0.25))
        return True

    draw_qr(c, cx, cy, cell, fn)
    # grid lines drawing in
    gp = eio(pr(t, 0.4, 2.0))
    if gp > 0 and t < 6.5:
        gp_ = P(CYAN, 0.55 * (1 - pr(t, 5.8, 6.5)), stroke=2)
        for i in range(N + 1):
            line(c, x0, y0 + i * cell, x0 + N * cell * gp, y0 + i * cell, gp_)
            line(c, x0 + i * cell, y0, x0 + i * cell, y0 + N * cell * gp, gp_)
    # scanner bar
    if 0 <= cur_row <= N:
        y = y0 + cur_row * cell
        c.drawRect(skia.Rect.MakeXYWH(x0 - 30, y - 7, N * cell + 60, 14), P(CYAN, 0.9, blur=7))
        c.drawRect(skia.Rect.MakeXYWH(x0 - 30, y - 2.5, N * cell + 60, 5), P(WHITE))
    # processor chip
    chx, chy = W / 2, 1130
    ck = eb(pr(t, 0.8, 1.6))
    energy = 0.0
    c.save()
    c.translate(chx, chy)
    c.scale(ck, ck)
    glow_t = pr(t, 2.4, 6.6) * (1 - pr(t, 6.6, 7.4) * 0.3)
    c.drawCircle(0, 0, 150, P(VIOLET, 0.25 * glow_t + 0.1 * math.sin(t * 6) * glow_t, blur=40))
    for i in range(-3, 4):
        rrect(c, i * 40 - 7, -124, 14, 26, 4, P("#8FA0E8"))
        rrect(c, i * 40 - 7, 98, 14, 26, 4, P("#8FA0E8"))
        rrect(c, -124, i * 40 - 7, 26, 14, 4, P("#8FA0E8"))
        rrect(c, 98, i * 40 - 7, 26, 14, 4, P("#8FA0E8"))
    rrect(c, -100, -100, 200, 200, 26, P("#1B2352"))
    rrect(c, -100, -100, 200, 200, 26, P(VIOLET, 1, stroke=6))
    rrect(c, -60, -60, 120, 120, 14, P("#0B1230"))
    text(c, "CPU", 0, 14, 44, VIOLET if t < 6.6 else GREEN, 1.0, heavy=True)
    c.restore()
    # bit particles
    for r in range(N):
        for kk in range(N):
            ts = scan_start + r * row_dt + kk * 0.006
            u = (t - ts) / 1.15
            if u <= 0 or u >= 1:
                continue
            sx, sy = x0 + kk * cell + cell / 2, y0 + r * cell + cell / 2
            j = _jit[r][kk]
            ex, ey = chx + (kk - N / 2) * 4, chy - 105
            x, y = bezier((sx, sy), (sx + j[0] * 1.6, sy + 240 + j[1]), (ex, ey), eio(u))
            fa = (1 - pr(u, 0.8, 1.0))
            text(c, "1" if M[r][kk] else "0", x, y, 26, CYAN if M[r][kk] else "#9FB0F0", fa, heavy=True)
    # output text
    ok = eio(pr(t, 6.7, 7.2))
    if ok > 0:
        rrect(c, 130, 1290, 820, 120, 28, P("#071022", 0.95 * ok))
        rrect(c, 130, 1290, 820, 120, 28, P(GREEN, ok, stroke=5))
        n = int(len(URL_TEXT) * pr(t, 7.1, 8.6))
        shown = URL_TEXT[:n] + ("▍" if int(t * 3) % 2 == 0 and n < len(URL_TEXT) else "")
        text(c, shown, 160, 1366, 54, GREEN, ok, align="l", heavy=True)
    # arrow from chip to output
    if ok > 0:
        c.drawPath(skia.Path().moveTo(W / 2 - 22, 1250).lineTo(W / 2 + 22, 1250).lineTo(W / 2, 1282).close(), P(GREEN, ok))


# ------------------------------------------------------------------ scene 5
def _damage():
    lost = set()
    for r in range(N):
        for k in range(N):
            if zone(r, k) in ("finder", "sep"):
                continue
            d1 = math.hypot(r - 14.0, k - 14.5)
            d2 = abs((k - 9.0) - (r - 3.0) * 0.8) / math.sqrt(1 + 0.64)
            if d1 < 3.6 or (d2 < 1.2 and 3 <= r <= 12 and 8 <= k <= 18):
                lost.add((r, k))
    return lost


LOST = _damage()
LOST_ORDER = sorted(LOST, key=lambda rc: (rc[0] * 1.0 + rc[1] * 0.5))


def scene5(c, t):
    bg(c, t, "#1A0B2E", "#43206B", PINK)
    cell = 30.0
    cx, cy = W / 2, 780
    # shock burst
    if t < 2.2:
        bu = eo(pr(t, 0.0, 1.0))
        c.save()
        c.translate(W / 2, 780)
        c.rotate(t * 40)
        for i in range(16):
            c.save()
            c.rotate(i * 360 / 16)
            c.drawPath(skia.Path().moveTo(0, 0).lineTo(-40 * bu, -900 * bu).lineTo(40 * bu, -900 * bu).close(), P(AMBER if i % 2 else PINK, 0.18 * (1 - pr(t, 1.4, 2.2))))
            c.restore()
        c.restore()
    if t < 2.0:
        kk = eb(pr(t, 0.1, 0.8))
        title(c, "¡Lo sorprendente!", t, 0.0, 190, AMBER)
    elif t < 7.7:
        title(c, "Corrección de errores", t, 1.8, 190, CYAN)
    else:
        title(c, "¡Sigue funcionando!", t, 7.7, 190, GREEN)
    k = eb(pr(t, 0.0, 0.8))
    c.save()
    c.translate(cx, cy)
    c.scale(k, k)
    c.rotate(math.sin(t * 1.3) * 1.2)
    c.translate(-cx, -cy)
    x0, y0 = qr_geom(cx, cy, cell)
    rec_start, rec_dt = 4.0, 0.045
    rec_time = {rc: rec_start + i * rec_dt for i, rc in enumerate(LOST_ORDER)}
    dmg = eio(pr(t, 2.0, 3.4))

    def fn(r, kk, x, y, cell, v):
        if (r, kk) in LOST and dmg > 0:
            tr = rec_time[(r, kk)]
            if t < tr:
                # lost module: red hatch
                c.drawRect(skia.Rect.MakeXYWH(x, y, cell + 0.6, cell + 0.6), P(RED, 0.35 * dmg))
                return True
            u = pr(t, tr, tr + 0.5)
            s = cell * (1 + 0.5 * math.sin(u * math.pi))
            colr = "#0B1230" if v else "#FFFFFF"
            c.drawRect(skia.Rect.MakeXYWH(x + cell / 2 - s / 2, y + cell / 2 - s / 2, s, s), P(colr))
            if u < 1:
                c.drawRect(skia.Rect.MakeXYWH(x - 4, y - 4, cell + 8, cell + 8), P(CYAN, 0.8 * (1 - u), blur=8))
            else:
                c.drawRect(skia.Rect.MakeXYWH(x + 2, y + 2, cell - 4, cell - 4), P(CYAN, 0.22))
            return True
        return False

    draw_qr(c, cx, cy, cell, fn)
    # damage overlays (stain, scratch)
    rec_end = rec_start + len(LOST_ORDER) * rec_dt + 0.5
    ov = dmg * (1 - 0.65 * pr(t, rec_start, rec_end))
    if ov > 0:
        sx, sy = x0 + 14.5 * cell, y0 + 14.0 * cell
        for i, (dx, dy, rr) in enumerate([(0, 0, 3.7), (1.9, -1.2, 1.7), (-1.6, 1.8, 1.4)]):
            c.drawCircle(sx + dx * cell, sy + dy * cell, rr * cell * dmg, P("#6B3E26", 0.55 * ov))
            c.drawCircle(sx + dx * cell, sy + dy * cell, rr * cell * dmg, P("#3B1E10", 0.7 * ov, stroke=5))
        p0 = (x0 + 9.0 * cell, y0 + 3.0 * cell)
        p1 = (x0 + 18.6 * cell, y0 + 12.3 * cell)
        c.drawLine(p0[0], p0[1], lerp(p0[0], p1[0], dmg), lerp(p0[1], p1[1], dmg), P("#D9D9E8", 0.9 * ov, stroke=9))
    c.restore()
    # ERROR label + meter
    if 2.4 < t < 4.0:
        flick = 0.5 + 0.5 * math.sin(t * 18)
        chip(c, "¡DAÑADO!", W / 2, 1230, RED, 0.5 + 0.5 * flick, 54)
    if t >= 4.0:
        done = sum(1 for rc in LOST_ORDER if t >= rec_time[rc])
        frac = done / max(1, len(LOST_ORDER))
        if t < 7.7:
            rrect(c, 130, 1200, 820, 40, 20, P("#0B1230", 0.8))
            rrect(c, 130, 1200, max(20, 820 * frac), 40, 20, P(CYAN))
            text(c, f"Datos recuperados {int(frac * 100)}%", W / 2, 1185, 40, WHITE, 1.0, heavy=True)
            chip(c, "Reed-Solomon", W / 2, 1320, VIOLET, eio(pr(t, 4.2, 4.8)), 42)
    if t >= 7.7:
        k2 = eb(pr(t, 7.7, 8.4))
        c.save()
        c.translate(W / 2, 1230)
        c.scale(k2, k2)
        c.drawCircle(0, 0, 70, P(GREEN, 0.25, blur=26))
        c.drawCircle(0, 0, 64, P(GREEN))
        c.drawPath(skia.Path().moveTo(-28, 2).lineTo(-8, 24).lineTo(32, -22), P(NAVY, 1, stroke=14))
        c.restore()
        chip(c, "Hasta ≈30% se puede recuperar", W / 2, 1360, CYAN, eio(pr(t, 8.4, 9.0)), 38)


# ------------------------------------------------------------------ scene 6
def bulb(c, cx, cy, s, t):
    glow = 0.5 + 0.5 * math.sin(t * 3)
    c.drawCircle(cx, cy, 230 * s, P(AMBER, 0.2 + 0.1 * glow, blur=70 * s))
    for i in range(14):
        a = i * math.pi * 2 / 14 + t * 0.5
        r0, r1 = 215 * s, (265 + 25 * math.sin(t * 4 + i)) * s
        line(c, cx + math.cos(a) * r0, cy + math.sin(a) * r0, cx + math.cos(a) * r1, cy + math.sin(a) * r1, P(AMBER, 0.9, stroke=10 * s))
    c.drawCircle(cx, cy, 160 * s, P("#FFE08A"))
    c.drawCircle(cx, cy, 160 * s, P(AMBER, 1, stroke=8 * s))
    rrect(c, cx - 70 * s, cy + 140 * s, 140 * s, 70 * s, 18 * s, P("#9AA6D8"))
    for i in range(3):
        line(c, cx - 62 * s, cy + (158 + i * 20) * s, cx + 62 * s, cy + (158 + i * 20) * s, P("#5E6AA0", 1, stroke=5 * s))
    # tiny QR in the bulb
    mini = 17 * s
    for r in range(N):
        for k in range(N):
            if M[r][k]:
                c.drawRect(skia.Rect.MakeXYWH(cx - N * mini / 2 * 0.38 + k * mini * 0.38 * 1.0, cy - N * mini / 2 * 0.38 - 8 * s + r * mini * 0.38, mini * 0.38 + 0.4, mini * 0.38 + 0.4), P("#0B1230", 0.9))


NODES = [("Cámara", "cam"), ("Detecta 3 esquinas", "tri"), ("Lee ceros y unos", "bits"), ("Corrige errores", "shield"), ("Abre la web", "web")]


def node_icon(c, kind, x, y, color):
    p = P(color, 1, stroke=6)
    if kind == "cam":
        rrect(c, x - 26, y - 18, 52, 38, 8, p)
        c.drawCircle(x, y + 1, 11, p)
    elif kind == "tri":
        for dx, dy in ((-16, -14), (16, -14), (-16, 16)):
            rrect(c, x + dx - 9, y + dy - 9, 18, 18, 3, P(color))
    elif kind == "bits":
        text(c, "01", x, y + 14, 38, color, 1.0, heavy=True)
    elif kind == "shield":
        c.drawPath(skia.Path().moveTo(x, y - 26).lineTo(x + 24, y - 14).lineTo(x + 20, y + 14).lineTo(x, y + 28).lineTo(x - 20, y + 14).lineTo(x - 24, y - 14).close(), p)
        c.drawPath(skia.Path().moveTo(x - 10, y + 2).lineTo(x - 2, y + 12).lineTo(x + 12, y - 8), p)
    else:
        c.drawCircle(x, y, 24, p)
        line(c, x - 24, y, x + 24, y, p)
        c.drawOval(skia.Rect.MakeXYWH(x - 11, y - 24, 22, 48), p)


def scene6(c, t):
    bg(c, t, "#0B1230", "#243777", AMBER)
    # phase A: lightbulb (0 - 4.6)
    la = 1 - eio(pr(t, 4.2, 5.0))
    if la > 0.01:
        k = eb(pr(t, 0.0, 0.9))
        c.save()
        c.translate(W / 2, 700)
        c.scale(k * (0.9 + 0.1 * la), k * (0.9 + 0.1 * la))
        c.translate(-W / 2, -700)
        bulb(c, W / 2, 700, 1.0, t)
        c.restore()
        gear(c, 190, 1040, 90, 10, t * 0.8, "#6C7DB8", 0.8 * la * k)
        gear(c, 880, 1000, 70, 8, -t * 1.0, "#8FA0E8", 0.8 * la * k)
        for i in range(6):
            sx = 160 + (i * 173) % 780
            sy = 400 + (i * 211) % 800
            star(c, sx, sy + math.sin(t * 2 + i) * 14, 16 + 6 * math.sin(t * 3 + i), [AMBER, CYAN, PINK][i % 3], 0.8 * la, t)
        text(c, "Más inteligentes", W / 2, 1230, 70, WHITE, la * eio(pr(t, 0.8, 1.4)), heavy=True)
        text(c, "de lo que parecen", W / 2, 1320, 70, AMBER, la * eio(pr(t, 1.2, 1.8)), heavy=True)
    # phase B: pipeline (4.6 - 8.8)
    pa = eio(pr(t, 4.4, 5.0)) * (1 - eio(pr(t, 8.2, 8.9)))
    if pa > 0.01:
        text(c, "Detrás de la pantalla", W / 2, 230, 64, WHITE, pa, heavy=True)
        for i, (label, kind) in enumerate(NODES):
            on = pr(t, 4.9 + i * 0.7, 5.4 + i * 0.7)
            y = 420 + i * 175
            kx = eb(pr(t, 4.6 + i * 0.12, 5.2 + i * 0.12))
            c.save()
            c.translate(W / 2, y)
            c.scale(kx, kx)
            colr = [CYAN, AMBER, VIOLET, PINK, GREEN][i]
            rrect(c, -340, -62, 680, 124, 62, P("#0B1230", 0.9 * pa))
            rrect(c, -340, -62, 680, 124, 62, P(colr, (0.35 + 0.65 * on) * pa, stroke=6))
            if on > 0:
                rrect(c, -340, -62, 680, 124, 62, P(colr, 0.18 * on * pa, blur=10))
            node_icon(c, kind, -250, 0, colr)
            text(c, label, -190, 16, 46, WHITE, pa, align="l", heavy=True)
            c.restore()
            if i < len(NODES) - 1:
                ar = P(colr, (0.4 + 0.6 * on) * pa, stroke=6)
                line(c, W / 2, y + 66, W / 2, y + 108, ar)
                c.drawPath(skia.Path().moveTo(W / 2 - 14, y + 96).lineTo(W / 2, y + 112).lineTo(W / 2 + 14, y + 96), ar)
    # phase C: globe + follow (8.4 - 12.3)
    ga = eio(pr(t, 8.6, 9.4))
    if ga > 0.01:
        gx, gy, gr = W / 2, 640, 200
        k = eb(pr(t, 8.6, 9.4))
        c.save()
        c.translate(gx, gy)
        c.scale(k, k)
        c.drawCircle(0, 0, gr + 40, P(CYAN, 0.18, blur=50))
        sh = skia.GradientShader.MakeRadial(skia.Point(-60, -60), gr * 1.4, [col("#5FA8FF"), col("#1C3FA8")])
        c.drawCircle(0, 0, gr, P(shader=sh))
        c.save()
        c.clipPath(skia.Path().addCircle(0, 0, gr), skia.ClipOp.kIntersect, True)
        for i in range(6):
            a = t * 0.9 + i * math.pi / 6
            w_ = gr * abs(math.cos(a))
            c.drawOval(skia.Rect.MakeXYWH(-w_, -gr, 2 * w_, 2 * gr), P(WHITE, 0.35, stroke=3))
        for yy in (-120, -60, 0, 60, 120):
            hw = math.sqrt(max(0, gr * gr - yy * yy))
            line(c, -hw, yy, hw, yy, P(WHITE, 0.3, stroke=3))
        c.restore()
        c.drawCircle(0, 0, gr, P(WHITE, 0.6, stroke=5))
        # orbiting gear
        oa = t * 1.2
        gear(c, math.cos(oa) * 290, math.sin(oa) * 90 + 10, 44, 8, t * 2, AMBER)
        c.restore()
        text(c, "¿Cómo funciona", W / 2, 1010, 74, WHITE, ga, heavy=True)
        text(c, "el mundo?", W / 2, 1100, 74, CYAN, ga, heavy=True)
        bk = eb(pr(t, 10.2, 10.9))
        pulse = 1 + 0.04 * math.sin(t * 6)
        if bk > 0:
            c.save()
            c.translate(W / 2, 1260)
            c.scale(bk * pulse, bk * pulse)
            rrect(c, -230, -62, 460, 124, 62, P(PINK, 0.35, blur=20))
            rrect(c, -230, -62, 460, 124, 62, P(PINK))
            text(c, "SÍGUENOS", 0, 18, 56, WHITE, 1.0, heavy=True)
            c.restore()


SCENE_FUNCS = [scene1, scene2, scene3, scene4, scene5, scene6]


def draw_frame(c, T):
    idx = 0
    for i in range(6):
        if T >= SCENES[i]:
            idx = i
    # transition: iris reveal of the next scene during the last 0.55s
    nxt = idx + 1
    if nxt < 6 and T >= SCENES[nxt] - 0.55:
        u = pr(T, SCENES[nxt] - 0.55, SCENES[nxt])
        SCENE_FUNCS[idx](c, T - SCENES[idx])
        c.save()
        r = lerp(0, 1500, eio(u))
        c.clipPath(skia.Path().addCircle(W / 2, 820, r), skia.ClipOp.kIntersect, True)
        SCENE_FUNCS[nxt](c, 0.0 + (T - SCENES[nxt]) if T >= SCENES[nxt] else 0.0)
        c.restore()
        c.drawCircle(W / 2, 820, r, P(WHITE, 0.55 * (1 - u), stroke=10))
    else:
        SCENE_FUNCS[idx](c, T - SCENES[idx])
    # fade in / out
    if T < 0.4:
        c.drawRect(skia.Rect.MakeWH(W, H), P("#000000", 1 - T / 0.4))
    if T > DURATION - 0.5:
        c.drawRect(skia.Rect.MakeWH(W, H), P("#000000", clamp((T - (DURATION - 0.5)) / 0.5)))


def render_range(out_path, f0, f1):
    surf = skia.Surface(W, H)
    canvas = surf.getCanvas()
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}",
        "-r", str(FPS), "-i", "-", "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "17",
        "-pix_fmt", "yuv420p", out_path,
    ]
    pr_ = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(f0, f1):
        canvas.clear(skia.ColorBLACK)
        draw_frame(canvas, f / FPS)
        arr = surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kUnpremul_AlphaType)
        pr_.stdin.write(np.ascontiguousarray(arr).tobytes())
    pr_.stdin.close()
    pr_.wait()


def render_png(dirpath, times):
    os.makedirs(dirpath, exist_ok=True)
    surf = skia.Surface(W, H)
    canvas = surf.getCanvas()
    for T in times:
        canvas.clear(skia.ColorBLACK)
        draw_frame(canvas, T)
        surf.makeImageSnapshot().save(os.path.join(dirpath, f"t{T:05.2f}.png"), skia.kPNG)


if __name__ == "__main__":
    if sys.argv[1] == "--png":
        render_png(sys.argv[2], [float(x) for x in sys.argv[3].split(",")])
    else:
        a, b = sys.argv[2].split(":")
        render_range(sys.argv[1], int(a), int(b))
