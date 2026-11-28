"""Fondos y escenas de «El hombre que recibió una llamada de su propio número»."""
import json
import math
import random
from PIL import Image, ImageFilter, ImageDraw
from lib import *
from chars import *

FLOOR = 1350
_cache = {}


class Cam:
    def __init__(s, cx, cy, z, bgw, bgh):
        z = max(z, 1.0)
        s.z = z
        s.cx = clamp(cx, W / 2 / z, bgw - W / 2 / z)
        s.cy = clamp(cy, H / 2 / z, bgh - H / 2 / z)
        s.x0 = s.cx - W / 2 / z
        s.y0 = s.cy - H / 2 / z

    def m(s, x, y):
        return ((x - s.x0) * s.z, (y - s.y0) * s.z)

    def canvas(s, bg):
        BS = S
        base = bg.resize((W * S, H * S), Image.BILINEAR,
                         box=(s.x0 * BS, s.y0 * BS, (s.x0 + W / s.z) * BS, (s.y0 + H / s.z) * BS))
        c = Cv(base=base)
        c.M = [(s.z, 0.0, 0.0, s.z, -s.x0 * s.z, -s.y0 * s.z)]
        return c


def hand_shake(t, z=1.0, a=2.0):
    return (math.sin(t * 1.9) * a * z, math.cos(t * 2.3) * a * z)


# ===========================================================================
# FONDOS
# ===========================================================================
def room_bg():
    if "room" in _cache:
        return _cache["room"]
    w, h = 2200, 1920
    c = Cv(w, h)
    c.im.paste(vgrad(w * S, FLOOR * S, [(0, (20, 22, 48)), (1, (38, 38, 72))]), (0, 0))
    c.im.paste(vgrad(w * S, (h - FLOOR) * S, [(0, (34, 28, 48)), (1, (14, 12, 24))]), (0, FLOOR * S))
    for i in range(16):
        x = i * 150
        c.line([(x, FLOOR), (x - 160 + i * 20, h)], 2, (10, 9, 18, 120), cap=False)
    c.rr(0, FLOOR - 30, w, FLOOR + 14, 2, (54, 52, 82))
    # ventana
    c.rr(1660, 240, 2100, 1110, 8, (78, 74, 108))
    gl = vgrad(int(380 * S), int(840 * S), [(0, (96, 134, 206)), (0.6, (52, 80, 150)), (1, (30, 46, 100))])
    c.im.paste(gl, (1680 * S, 260 * S))
    c.ell(1960, 470, 54, 54, (236, 240, 255))
    c.ell(1944, 456, 46, 46, (250, 252, 255))
    for (sx, sy) in ((1760, 360), (1830, 520), (2010, 340), (1730, 640), (2040, 700), (1900, 300)):
        c.ell(sx, sy, 3, 3, (255, 255, 255, 200), 8)
    c.poly([(1680, 880), (2060, 760), (2060, 1090), (1680, 1090)], (22, 28, 60))
    for hx, hh in ((1690, 120), (1760, 200), (1850, 150), (1950, 230), (2020, 170)):
        c.rr(hx, 1090 - hh - 60, hx + 80, 1090, 2, (16, 20, 44))
    c.rr(1676, 672, 2084, 686, 2, (78, 74, 108))
    c.rr(1872, 255, 1888, 1105, 2, (78, 74, 108))
    c.rr(1650, 1096, 2112, 1130, 6, (94, 90, 124))
    # cortinas
    for (x0, x1) in ((1570, 1735), (2030, 2170)):
        c.rr(x0, 190, x1, 1360, 6, (64, 40, 88))
        for i in range(1, 6):
            xx = x0 + (x1 - x0) * i / 6
            c.line([(xx, 200), (xx - 6, 1350)], 5, (44, 28, 64, 200), cap=False)
            c.line([(xx + 12, 200), (xx + 6, 1350)], 3, (96, 66, 124, 80), cap=False)
    c.rr(1520, 170, 2220, 200, 10, (30, 24, 40))
    # librero
    c.rr(1230, 420, 1540, 1342, 6, (54, 42, 60))
    rng = random.Random(3)
    for r in range(5):
        y0 = 440 + r * 180
        c.rr(1246, y0 + 168, 1524, y0 + 178, 2, (74, 58, 82))
        x = 1252
        while x < 1510:
            bw = rng.randint(18, 34)
            bh = rng.randint(100, 150)
            col = rng.choice([(110, 60, 70), (70, 90, 130), (150, 120, 70), (80, 120, 100), (120, 90, 150), (60, 66, 96)])
            c.rr(x, y0 + 168 - bh, x + bw, y0 + 168, 2, col)
            x += bw + 3
    # cuadro
    c.rr(380, 480, 600, 740, 6, (92, 70, 58))
    c.rr(396, 496, 584, 724, 2, (28, 36, 84))
    c.ell(500, 580, 28, 28, (232, 220, 170))
    c.poly([(396, 724), (460, 640), (520, 700), (560, 650), (584, 690), (584, 724)], (14, 18, 40))
    # cama
    c.rr(50, 640, 160, FLOOR, 16, (60, 40, 46))
    c.rr(50, 640, 160, 700, 16, (74, 52, 58))
    c.rr(120, 1180, 920, FLOOR - 12, 10, (62, 44, 68))
    c.rr(120, 1180, 920, 1210, 10, (92, 72, 98))
    c.rr(110, FLOOR - 20, 140, FLOOR + 20, 4, (40, 28, 34))
    c.rr(900, FLOOR - 20, 930, FLOOR + 20, 4, (40, 28, 34))
    c.ell(360, 1060, 160, 66, (186, 190, 214))
    c.ell(360, 1050, 140, 52, (212, 216, 236))
    # mesa de noche + lámpara
    c.rr(900, 1100, 1140, FLOOR + 8, 6, (66, 48, 56))
    c.rr(890, 1086, 1150, 1112, 6, (88, 66, 74))
    c.rr(920, 1160, 1120, 1190, 6, (50, 36, 44))
    c.ell(1020, 1176, 8, 8, (170, 140, 90))
    c.rr(950, 940, 960, 1086, 3, (150, 130, 110))
    c.ell(955, 1086, 34, 10, (120, 100, 90))
    c.poly([(895, 940), (1015, 940), (1000, 820), (910, 820)], (196, 148, 96))
    c.poly([(960, 940), (1015, 940), (1000, 820), (975, 820)], (170, 124, 82))
    # alfombra
    c.ell(1000, 1640, 640, 120, (58, 42, 82, 180))
    c.ell(1000, 1640, 560, 90, (74, 54, 100, 180))
    # haz de luna sobre el piso
    c.poly([(1700, 1110), (2080, 1110), (1960, FLOOR), (1560, FLOOR), (1250, 1920), (1900, 1920), (2160, 1920), (2200, FLOOR)],
           (150, 180, 255, 14))
    _cache["room"] = c.im
    return c.im


def blanket(c):
    c.poly([(380, 1080), (520, 1074), (700, 1118), (920, 1176), (920, FLOOR - 12), (420, FLOOR - 12), (330, 1200)], (86, 56, 124))
    c.poly([(380, 1080), (520, 1074), (700, 1118), (920, 1176), (920, 1196), (700, 1140), (520, 1096), (390, 1100)], (118, 82, 160))
    for (x0, y0, x1, y1) in ((470, 1130, 440, 1330), (600, 1150, 590, 1340), (740, 1190, 740, 1340)):
        c.line([(x0, y0), (x1, y1)], 6, (62, 38, 96, 180), cap=False)


def closeup_bg(kind="bed"):
    key = "cl_" + kind
    if key in _cache:
        return _cache[key]
    w, h = 1200, 2100
    c = Cv(w, h)
    c.im.paste(vgrad(w * S, h * S, [(0, (18, 22, 52)), (0.6, (28, 30, 62)), (1, (12, 12, 28))]), (0, 0))
    if kind == "bed":
        c.rr(-40, 520, 330, 2200, 30, (46, 32, 44))
        c.rr(-40, 520, 330, 600, 30, (66, 46, 58))
        c.ell(930, 560, 70, 70, (255, 200, 120, 190))
        c.ell(1060, 700, 36, 36, (255, 190, 110, 150))
        c.ell(780, 420, 44, 44, (255, 210, 140, 120))
        c.rr(760, 380, 1140, 1060, 8, (62, 94, 160, 150))
        c.ell(150, 300, 50, 50, (150, 190, 255, 100))
    elif kind == "table":
        c.rr(-40, 1500, 1300, 2200, 8, (30, 22, 30))
        c.ell(950, 600, 90, 90, (255, 190, 110, 160))
        c.ell(220, 480, 60, 60, (130, 170, 255, 120))
    im = c.im.filter(ImageFilter.GaussianBlur(14 * S))
    _cache[key] = im
    return im


def draw_car(c, police=False, driver=False, t=0.0, flash=0, lights=False):
    """Origen = centro del piso bajo el auto. Mira hacia la izquierda."""
    body = (232, 236, 244) if police else (20, 23, 38)
    hl = (255, 255, 255) if police else (66, 74, 108)
    c.ell(0, 6, 300, 24, (4, 4, 10, 200))
    for wx in (-165, 168):
        c.ell(wx, -44, 54, 54, (8, 8, 12))
        c.ell(wx, -44, 30, 30, (96, 100, 124))
        c.ell(wx, -44, 12, 12, (30, 30, 40))
    c.poly([(-285, -50), (-278, -108), (-230, -126), (-140, -140), (-80, -210), (30, -228), (150, -222), (216, -140),
            (275, -128), (290, -90), (284, -50), (222, -50), (200, -62), (136, -98), (-110, -98), (-122, -50)], body)
    c.poly([(-285, -50), (-278, -108), (-230, -126), (-140, -140), (-80, -210), (30, -228), (150, -222), (216, -140),
            (275, -128), (290, -90)], body)
    c.rr(-280, -112, 286, -92, 8, body)
    c.line([(-230, -126), (-140, -140), (-80, -210), (30, -228), (150, -222), (216, -140)], 4, hl)
    # ventanas
    c.poly([(-120, -142), (-70, -202), (-20, -212), (-20, -142)], (8, 10, 20))
    c.poly([(0, -142), (0, -212), (132, -206), (186, -142)], (8, 10, 20))
    c.poly([(-120, -142), (-70, -202), (-48, -204), (-100, -142)], (60, 80, 130, 150))
    if police:
        c.rr(-270, -100, 280, -78, 6, (40, 92, 210))
        c.text(20, -58, "POLICÍA", 20, (20, 30, 70))
        c.rr(-40, -250, 70, -226, 6, (30, 30, 40))
        rr_, bb = (255, 40, 40), (50, 110, 255)
        c.rr(-40, -250, 14, -226, 6, rr_ if flash else (110, 20, 20))
        c.rr(16, -250, 70, -226, 6, (110, 20, 20) if flash else bb)
    else:
        c.line([(-90, -160), (60, -160)], 3, (50, 60, 90))
        c.ell(279, -100, 7, 7, (190, 30, 30, 200) if lights else (110, 20, 30))
    if driver:
        # silueta al volante
        c.ell(70, -170, 24, 28, (3, 3, 7))
        c.poly([(34, -146), (110, -146), (118, -120), (28, -120)], (3, 3, 7))
        c.poly([(46, -190), (96, -190), (92, -182), (50, -182)], (3, 3, 7))
        c.ell(63, -168, 3, 3, (210, 232, 255))
        c.ell(80, -168, 3, 3, (210, 232, 255))


def street_bg():
    if "street" in _cache:
        return _cache["street"]
    w, h = 1080, 1920
    c = Cv(w, h)
    c.im.paste(vgrad(w * S, 1050 * S, [(0, (6, 10, 28)), (0.7, (22, 28, 66)), (1, (46, 50, 96))]), (0, 0))
    rng = random.Random(5)
    for _ in range(70):
        c.ell(rng.randint(0, w), rng.randint(0, 700), rng.choice([1.5, 2, 2.5]), 2, (255, 255, 255, rng.randint(80, 220)), 8)
    c.ell(820, 310, 92, 92, (210, 222, 255, 40))
    c.ell(820, 310, 66, 66, (240, 244, 255))
    c.ell(800, 296, 56, 56, (252, 253, 255))
    # casas
    for (x0, x1, y0, col) in ((-20, 300, 700, (24, 28, 58)), (300, 620, 760, (20, 24, 52)), (620, 900, 690, (26, 30, 62)), (900, 1120, 760, (22, 26, 54))):
        c.rr(x0, y0, x1, 1050, 4, col)
        c.poly([(x0 - 20, y0), ((x0 + x1) / 2, y0 - 120), (x1 + 20, y0)], (14, 16, 38))
        for wx in range(int(x0) + 50, int(x1) - 60, 110):
            lit = rng.random() < 0.4
            c.rr(wx, y0 + 70, wx + 56, y0 + 140, 3, (255, 205, 120) if lit else (36, 44, 90))
            if lit:
                c.rr(wx, y0 + 70, wx + 56, y0 + 140, 3, (255, 205, 120))
    # árboles
    for tx_, ty_, r_ in ((90, 820, 120), (990, 860, 100)):
        c.rr(tx_ - 12, ty_, tx_ + 12, 1070, 3, (14, 12, 20))
        c.ell(tx_, ty_ - 30, r_, r_ * 0.9, (10, 18, 30))
    # acera y calle
    c.rr(0, 1040, w, 1130, 2, (60, 62, 90))
    c.rr(0, 1124, w, 1140, 2, (92, 94, 126))
    c.im.paste(vgrad(w * S, (h - 1140) * S, [(0, (34, 36, 54)), (1, (10, 10, 18))]), (0, 1140 * S))
    for i in range(6):
        c.rr(60 + i * 190, 1620, 150 + i * 190, 1640, 4, (150, 150, 100, 120))
    # farola
    c.rr(166, 560, 182, 1120, 4, (16, 18, 30))
    c.rr(166, 556, 260, 574, 6, (16, 18, 30))
    c.ell(246, 584, 34, 14, (255, 226, 160))
    c.poly([(210, 590), (282, 590), (460, 1130), (30, 1130)], (255, 220, 150, 26))
    c.ell(150, 1126, 150, 20, (255, 220, 150, 40))
    _cache["street"] = c.im
    return c.im


# ===========================================================================
# ESCENAS
# ===========================================================================
def finish(c, lights=()):
    img = c.small()
    for (x, y, r, col, st) in lights:
        add_light(img, x, y, r, col, st)
    return img


def ring_waves(img_cv, cx, cy, t, n=3, maxr=160, color=(150, 200, 255)):
    for i in range(n):
        ph = ((t * 1.4) + i / n) % 1.0
        r = 40 + ph * maxr
        img_cv.d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color + (int(140 * (1 - ph)),), width=4)


# --- 1 · plano general ------------------------------------------------------
def s_hook_wide(t, d):
    cam = Cam(640 + 12 * t / d, 1030, 1.1, 2200, 1920)
    c = cam.canvas(room_bg())
    surprise = ease((t - 0.9) / 0.6)
    vib = 0 if (t % 1.2) > 0.8 else math.sin(t * 90) * 1.8
    ex = ex_mix("neutral", "surprise", surprise)
    with c.push(380, 1020, 0.56):
        draw_bust(c, ex, gaze=(lerp(0, 0.9, ease(t / 0.8)), lerp(0.1, 0.6, ease(t / 0.8))), tilt=lerp(0, 0.08, surprise),
                  breath=math.sin(t * 2.2))
    blanket(c)
    with c.push(1050 + vib, 975, 0.4):
        phone_screen(c, "incoming", t)
    img = c.small()
    sx, sy = cam.m(1050, 975)
    ring = ImageDraw.Draw(img, "RGBA")
    for i in range(3):
        ph = ((t * 1.4) + i / 3) % 1.0
        r = (70 + ph * 130) * cam.z
        ring.ellipse([sx - r, sy - r, sx + r, sy + r], outline=(150, 200, 255, int(130 * (1 - ph))), width=4)
    for (x, y, r, col, st) in ((1050, 975, 330, (80, 130, 255), 0.38), (955, 900, 480, (255, 170, 90), 0.30),
                              (1880, 700, 760, (70, 100, 190), 0.34)):
        px, py = cam.m(x, y)
        add_light(img, px, py, r * cam.z, col, st)
    return img


# --- busto genérico ------------------------------------------------------------
def bust_scene(t, d, ex, zoom=(1.0, 1.06), hold=None, gaze=(0, 0), tilt=0.0, talk=0.0, sweat=0.0, glow=None,
               bg="bed", blink=0.0, k=1.5, tremor=0.0, cx=600):
    z = lerp(zoom[0], zoom[1], t / max(d, 0.01))
    cam = Cam(cx + 14 * t / d, 1050, z, 1200, 2100)
    c = cam.canvas(closeup_bg(bg))
    sh = hand_shake(t, 1.0, 1.4)
    with c.push(600 + sh[0] * 0.6, 1360 + sh[1], k):
        draw_bust(c, ex, gaze=gaze, tilt=tilt, breath=math.sin(t * 2.4), hold=hold, talk=talk, sweat=sweat,
                  blink=blink, tremor=tremor)
    img = c.small()
    if glow:
        px, py = cam.m(*glow[0])
        add_light(img, px, py, glow[1] * cam.z, glow[2], glow[3])
    return img


def blink_at(t, times=(1.6, 4.1, 6.7)):
    for b in times:
        if abs(t - b) < 0.1:
            return 1 - abs(t - b) / 0.1
    return 0.0


# --- 2 · rostro sorprendido ---------------------------------------------------------
def s_hook_bust(t, d):
    ex = ex_mix("neutral", "surprise", t / 0.5)
    return bust_scene(t, d, ex, zoom=(1.0, 1.12), hold="front", gaze=(0.55, 0.8), tilt=0.05, glow=((560, 1500), 520, (90, 140, 255), 0.55),
                      blink=blink_at(t, (1.8,)), k=1.4)


# --- teléfono (cierres) --------------------------------------------------------------
def phone_scene(t, d, state, k=(2.0, 2.4), flash=0.0, tt=None, vibrate=0.0, bg="table", dy=-90, extra=None, waves=False):
    kk = lerp(k[0], k[1], ease(t / max(d, 0.01)))
    cam = Cam(600, 1050, 1.0, 1200, 2100)
    c = cam.canvas(closeup_bg(bg))
    vx = math.sin(t * 95) * 5 * vibrate if (t % 0.9) < 0.55 else 0
    vy = math.cos(t * 83) * 3 * vibrate if (t % 0.9) < 0.55 else 0
    sh = hand_shake(t, 1.0, 3.0)
    with c.push(600 + vx + sh[0], 1050 + dy + vy + sh[1], kk):
        phone_screen(c, state, t if tt is None else tt, flash=flash)
        if extra:
            extra(c, t, d)
    img = c.small()
    if waves:
        dr = ImageDraw.Draw(img, "RGBA")
        for i in range(3):
            ph = ((t * 1.3) + i / 3) % 1.0
            r = 330 + ph * 330
            cx_, cy_ = W / 2, 960 + dy
            dr.rounded_rectangle([cx_ - 170 - ph * 190, cy_ - 340 - ph * 190, cx_ + 170 + ph * 190, cy_ + 340 + ph * 190],
                                 radius=70 + int(ph * 120), outline=(150, 190, 255, int(110 * (1 - ph))), width=5)
    pc = (W / 2, 960 + dy)
    add_light(img, pc[0], pc[1], 900, (70, 100, 200), 0.34)
    return img


def s_hook_phone(t, d):
    return phone_scene(t, d, "incoming", k=(1.2, 2.2), vibrate=0.8, bg="table", waves=True)


def s_number(t, d):
    fl = 0.5 + 0.5 * math.sin(t * 7)
    return phone_scene(t, d, "incoming", k=(2.1, 2.45), flash=fl, vibrate=0.2, bg="table")


def s_skeptic(t, d):
    ex = ex_mix("neutral", "skeptic", t / 0.6)
    return bust_scene(t, d, ex, zoom=(1.0, 1.1), hold="front", gaze=(0.3, 0.75), tilt=-0.05,
                      glow=((560, 1500), 520, (90, 140, 255), 0.5), blink=blink_at(t, (1.4,)), k=1.4)


def s_decide(t, d):
    def thumb(c, tt, dd):
        u = ease(tt / (dd * 0.85))
        tx = lerp(240, 82, u)
        ty = lerp(560, 310 - 118 + 118, u) if False else lerp(700, 248 + 10, u)
        c.limb((330, 760), (tx + 14, ty + 14), 84, 64, SKIN)
        c.ell(tx, ty, 34, 38, SKIN)
        c.ell(tx - 6, ty - 12, 20, 14, (240, 200, 170))
        if u >= 1:
            pass
    st = "incoming" if t < d - 0.25 else "connected"
    return phone_scene(t, d, st, k=(2.2, 2.2), flash=0, vibrate=0.2, extra=thumb if st == "incoming" else None, tt=t)


def s_listen(t, d):
    ex = ex_mix("worry", "fear", t / 0.7)
    img = bust_scene(t, d, ex, zoom=(1.0, 1.14), hold="ear", gaze=(-0.2, 0.15), tilt=0.07, sweat=clamp((t - 1.5) / 1.6),
                     tremor=math.sin(t * 30) * 0.006, blink=0.0, k=1.5)
    dr = ImageDraw.Draw(img, "RGBA")
    # susurro: ondas que salen del teléfono hacia el oído
    for i in range(4):
        ph = ((t * 1.1) + i / 4) % 1.0
        rx = 40 + ph * 120
        cx_, cy_ = 775 - ph * 40, 640
        dr.arc([cx_ - rx, cy_ - rx * 1.6, cx_ + rx, cy_ + rx * 1.6], 130, 230, fill=(170, 210, 255, int(190 * (1 - ph))), width=6)
    return img


def s_speak(t, d):
    talk = 0.5 + 0.5 * math.sin(t * 14) if t < d - 0.2 else 0
    ex = ex_mix("fear", "worry", t / 0.5)
    return bust_scene(t, d, ex, zoom=(1.08, 1.0), hold="ear", gaze=(0.0, 0.2), tilt=0.1 * math.sin(t * 3), talk=talk * 0.9,
                      sweat=0.9, k=1.5, blink=blink_at(t, (0.7,)))


def s_ended(t, d):
    st = "ended" if t < d - 0.45 else "dark"
    return phone_scene(t, d, st, k=(2.2, 2.0), bg="table")


def s_msg(t, d):
    return phone_scene(t, d, "msg", k=(2.0, 2.35), vibrate=0.9, tt=t, bg="table")


def s_read(t, d):
    ex = ex_mix("worry", "fear", t / 0.8)
    gx = lerp(0.3, 1.0, ease((t - 1.0) / 0.5))
    return bust_scene(t, d, ex, zoom=(1.0, 1.12), hold="front", gaze=(gx, 0.5 - 0.5 * ease((t - 1.0) / 0.5)),
                      tilt=0.05 + 0.05 * ease((t - 1.0) / 0.5), glow=((560, 1500), 520, (90, 140, 255), 0.45), k=1.4,
                      sweat=0.8)


# --- caminata hacia la ventana ------------------------------------------------------
def s_walk(t, d):
    hold_t = 0.9
    walk_d = max(d - hold_t, 0.5)
    u = clamp(t / walk_d)
    x = lerp(740, 1330, u)
    moving = t < walk_d
    phase = t * 2 * math.pi / 1.5
    amp = 0.24 if moving else lerp(0.24, 0.0, ease((t - walk_d) / 0.4))
    if not moving:
        phase = walk_d * 2 * math.pi / 1.5
    k = 0.86
    ground = 1640
    hy = ground - figure_height(phase, amp) * k
    ar = ease((t - walk_d - 0.2) / 0.9) if not moving else 0.0
    cam = Cam(clamp(x + 260, 640, 1500), 1000, 1.22, 2200, 1920)
    c = cam.canvas(room_bg())
    # sombra
    c.ell(x + 30, ground + 8, 150, 20, (4, 4, 10, 150))
    with c.push(x, hy, k):
        draw_figure(c, phase=phase, amp=amp, lean=0.04 + 0.04 * ar, head_turn=1, arm_raise=ar, hold_phone=True,
                    breath=math.sin(t * 3))
    img = c.small()
    lights = ((1900, 640, 900, (70, 105, 200), 0.42 + 0.18 * u), (955, 880, 520, (255, 170, 90), 0.3 * (1 - u)))
    for (x_, y_, r, col, st) in lights:
        px, py = cam.m(x_, y_)
        add_light(img, px, py, r * cam.z, col, st)
    return img


# --- ventana: la calle ----------------------------------------------------------------
def window_frame(img, a=1.0):
    dr = ImageDraw.Draw(img, "RGBA")
    al = int(255 * a)
    for (x0, x1) in ((0, 120), (W - 120, W)):
        dr.rectangle([x0, 0, x1, H], fill=(46, 28, 66, al))
        for i in range(1, 5):
            xx = x0 + (x1 - x0) * i / 5
            dr.line([(xx, 0), (xx - 8, H)], fill=(28, 16, 44, int(al * 0.8)), width=6)
    dr.rectangle([0, 0, W, 34], fill=(26, 18, 36, al))
    dr.rectangle([0, H - 20, W, H], fill=(26, 18, 36, al))


def s_street(t, d):
    u = ease(t / d)
    cam = Cam(lerp(540, 770, u), lerp(960, 1060, u), lerp(1.0, 1.7, u), 1080, 1920)
    c = cam.canvas(street_bg())
    with c.push(790, 1238, 1.0):
        draw_car(c, driver=False)
    img = c.small()
    px, py = cam.m(246, 584)
    add_light(img, px, py, 460 * cam.z, (255, 210, 140), 0.45)
    px, py = cam.m(820, 310)
    add_light(img, px, py, 700 * cam.z, (110, 140, 230), 0.22)
    window_frame(img, 1 - ease(t / (d * 0.9)))
    return img


def s_silhouette(t, d):
    u = t / d
    z = lerp(1.0, 1.1, u)
    w, h = 1080, 1920
    img = Image.new("RGB", (w, h), (10, 12, 22))
    gl = vgrad(w, h, [(0, (34, 46, 88)), (0.5, (14, 20, 44)), (1, (6, 8, 18))])
    img.paste(gl)
    c = Cv(base=img.resize((w * S, h * S), Image.BILINEAR))
    c.M = [(1, 0, 0, 1, 0, 0)]
    # marco de la ventanilla
    c.rr(-40, -40, W + 40, 360, 2, (12, 13, 22))
    c.rr(-40, 1500, W + 40, H + 40, 2, (12, 13, 22))
    c.rr(-40, -40, 110, H + 40, 2, (12, 13, 22))
    c.rr(970, -40, W + 40, H + 40, 2, (12, 13, 22))
    # reflejos
    for i, x0 in enumerate((220, 520, 800)):
        c.poly([(x0, 360), (x0 + 90, 360), (x0 - 200, 1500), (x0 - 290, 1500)], (150, 190, 255, 16))
    with c.push(540 + math.sin(t * 0.8) * 8, 1180, lerp(1.35, 1.6, u)):
        # hombros + cabeza + gorra (casi negros)
        c.poly([(-420, 520), (-380, 120), (-250, 20), (-90, -20), (90, -20), (250, 20), (380, 120), (420, 520)], (4, 4, 9))
        c.rr(-40, -150, 40, 10, 6, (4, 4, 9))
        turn = math.sin(clamp(u * 1.6) * 1.0) * 12 * (1 - clamp(u * 1.6 - 0.3))
        c.ell(turn, -260, 128, 150, (4, 4, 9))
        c.poly([(-140 + turn, -300), (140 + turn, -300), (120 + turn, -400), (-120 + turn, -400)], (3, 3, 7))
        c.poly([(-150 + turn, -300), (200 + turn, -300), (206 + turn, -286), (-150 + turn, -280)], (3, 3, 7))
        # contorno de luz de farola
        c.line([(-250, 20), (-380, 120), (-420, 520)], 5, (255, 214, 150, 90), cap=False)
        c.line([(-126 + turn, -290), (-126 + turn, -200)], 4, (255, 214, 150, 80), cap=False)
        # ojos
        ea = clamp((t - 0.5) / 0.7)
        for s_ in (-1, 1):
            c.ell(turn + s_ * 48, -250, 14, 7, (226, 240, 255, int(255 * ea)))
        # brasa de cigarro / respiración
        c.ell(turn - 20, -190, 3, 3, (255, 130, 40, int(220 * (0.5 + 0.5 * math.sin(t * 5)))))
    img = c.small()
    add_light(img, 540, 600, 900, (80, 120, 220), 0.14)
    fog = Image.new("RGB", (w, h), (24, 32, 60))
    mask = vgrad(w, h, [(0, (40, 40, 40)), (0.5, (14, 14, 14)), (1, (40, 40, 40))]).convert("L")
    img = Image.composite(fog, img, mask.point(lambda v: int(v * 0.6)))
    return img


def s_call_police(t, d):
    ex = ex_mix("fear", "worry", t / d)
    return bust_scene(t, d, ex, zoom=(1.12, 1.0), hold="ear", gaze=(0.7, 0.1), tilt=0.08, talk=0.0,
                      sweat=1.0, tremor=math.sin(t * 40) * 0.007, k=1.5)


def s_patrol(t, d):
    arrive = min(2.6, d * 0.6)
    u = ease(t / arrive) if t < arrive else 1.0
    x = lerp(-320, 330, 1 - (1 - clamp(t / arrive)) ** 2)
    pan = ease((t - arrive) / (d - arrive))
    cam = Cam(lerp(420, 790, pan), lerp(1020, 1090, pan), lerp(1.05, 1.5, pan), 1080, 1920)
    c = cam.canvas(street_bg())
    flash = int(t / 0.16) % 2
    with c.push(x, 1250, 1.05):
        draw_car(c, police=True, flash=flash)
    img = c.small()
    px, py = cam.m(246, 584)
    add_light(img, px, py, 460 * cam.z, (255, 210, 140), 0.35)
    col_a, col_b = ((255, 50, 50), (60, 110, 255))
    px, py = cam.m(x - 10, 1010)
    add_light(img, px, py, 640 * cam.z, col_a if flash else col_b, 0.55)
    add_light(img, px, py + 200, 900 * cam.z, col_b if flash else col_a, 0.20)
    if t < arrive:
        px, py = cam.m(x - 330, 1190)
        add_light(img, px, py, 260 * cam.z, (255, 250, 220), 0.5)
    return img


def s_watch(t, d):
    u = t / d
    cam = Cam(lerp(1560, 1620, u), 1000, lerp(1.2, 1.5, u), 2200, 1920)
    c = cam.canvas(room_bg())
    x, ground, k = 1330, 1640, 0.86
    hy = ground - figure_height(0.0, 0.0) * k
    c.ell(x + 30, ground + 8, 150, 20, (4, 4, 10, 150))
    with c.push(x, hy + math.sin(t * 2.0) * 2, k):
        draw_figure(c, phase=0.0, amp=0.0, lean=0.06, head_turn=1, arm_raise=1.0, hold_phone=True, breath=math.sin(t * 3))
    img = c.small()
    px, py = cam.m(1900, 640)
    add_light(img, px, py, 900 * cam.z, (70, 105, 200), 0.55)
    # destellos lejanos de patrulla a través del vidrio
    fl = int(t / 0.3) % 2
    px, py = cam.m(1880, 900)
    add_light(img, px, py, 300 * cam.z, (255, 60, 60) if fl else (70, 120, 255), 0.16)
    return img


def s_unknown(t, d):
    return phone_scene(t, d, "unknown", k=(2.1, 2.4), vibrate=1.0, waves=True, bg="table")


def s_glance(t, d):
    ex = ex_mix("neutral", "uneasy", t / 0.7)
    # primero mira el teléfono (abajo-izq), luego la ventana (derecha)
    u1 = ease((t - d * 0.45) / 0.5)
    gaze = (lerp(-0.2, 1.0, u1), lerp(0.7, -0.05, u1))
    return bust_scene(t, d, ex, zoom=(1.0, 1.1), hold=None, gaze=gaze, tilt=lerp(-0.03, 0.1, u1),
                      glow=((300, 1500), 520, (90, 140, 255), 0.25), k=1.5, sweat=0.4, blink=blink_at(t, (d * 0.4,)))


def s_final_phone(t, d):
    return phone_scene(t, d, "unknown", k=(2.2, 1.6), vibrate=1.1, waves=True, bg="table", dy=-90)


def s_final_bust(t, d):
    u = t / d
    ex = ex_mix("uneasy", "fear", clamp(u * 1.2 - 0.2) * 0.45)
    gx = 0.9 if (t % 3.0) < 1.6 else -0.1
    return bust_scene(t, d, ex, zoom=(1.0, 1.28), hold=None, gaze=(gx * 0.8, 0.1), tilt=0.05, k=1.5,
                      glow=((1000, 1500), 620, (80, 110, 200), 0.18), sweat=0.5, blink=blink_at(t, (1.2, 3.4)))
