"""Protagonista (busto y cuerpo entero), teléfono y pantallas."""
import math
import random
from lib import *

SKIN = (226, 170, 132)
SKIN_D = (190, 128, 98)
HAIR = (30, 24, 30)
SHIRT = (104, 114, 142)
SHIRT_D = (74, 82, 108)
PANTS = (42, 46, 72)
PANTS_D = (30, 33, 54)
SHOE = (22, 22, 30)

EXPR = {
    "neutral":  dict(eye=1.0, bl=0.0, br=0.0, tilt=0.0, mo=0.0, mw=1.0, mc=0.0, pup=1.0),
    "surprise": dict(eye=1.4, bl=1.0, br=1.0, tilt=0.15, mo=0.7, mw=0.65, mc=0.0, pup=0.8),
    "skeptic":  dict(eye=0.82, bl=-0.1, br=0.9, tilt=-0.15, mo=0.0, mw=0.9, mc=0.35, pup=1.0),
    "fear":     dict(eye=1.45, bl=0.7, br=0.7, tilt=1.0, mo=0.4, mw=1.1, mc=-0.6, pup=0.62),
    "worry":    dict(eye=1.15, bl=0.35, br=0.35, tilt=0.8, mo=0.1, mw=1.0, mc=-0.5, pup=0.85),
    "uneasy":   dict(eye=0.95, bl=0.1, br=0.1, tilt=0.65, mo=0.0, mw=0.95, mc=-0.45, pup=0.9),
}


def ex_mix(a, b, u):
    A, B = EXPR[a], EXPR[b]
    u = ease(u)
    return {k: lerp(A[k], B[k], u) for k in A}


_rng = random.Random(11)
STUBBLE = []
while len(STUBBLE) < 110:
    x, y = _rng.uniform(-112, 112), _rng.uniform(-235, -92)
    if (x / 116) ** 2 + ((y + 215) / 132) ** 2 < 0.93 and y > -215 + 5 - 0 and not (abs(x) < 38 and -190 < y < -150):
        STUBBLE.append((x, y))


def phone_back(c, w=120, h=250, glow=False):
    c.rr(-w / 2, -h / 2, w / 2, h / 2, 22, (24, 26, 40))
    c.rr(-w / 2 + 6, -h / 2 + 6, w / 2 - 6, h / 2 - 6, 18, (34, 37, 56))
    c.ell(-w / 2 + 32, -h / 2 + 34, 17, 17, (14, 15, 24))
    c.ell(-w / 2 + 32, -h / 2 + 34, 8, 8, (50, 70, 120))
    if glow:
        c.line([(-w / 2 + 3, -h / 2 + 30), (-w / 2 + 3, h / 2 - 30)], 4, (140, 190, 255, 160))


def hand_fingers(c, x, y, n=4, gap=34, ang=0):
    for i in range(n):
        c.rr(x - 20, y + i * gap - 17, x + 24, y + i * gap + 17, 15, SKIN)
        c.line([(x - 12, y + i * gap + 15), (x + 16, y + i * gap + 15)], 3, SKIN_D, cap=False)


def draw_bust(c, ex, gaze=(0.0, 0.0), tilt=0.0, breath=0.0, blink=0.0, hold=None,
              talk=0.0, sweat=0.0, tremor=0.0, shake=(0, 0), phone_glow=True):
    """c: lienzo ya transformado: origen = base del cuello, 1 unidad ≈ 1 px a k=1."""
    sx, sy = shake
    with c.push(sx, sy + breath * 6):
        # --- torso -----------------------------------------------------------
        c.poly([(-390, 520), (-372, 150), (-290, 44), (-96, 4), (96, 4), (290, 44), (372, 150), (390, 520)], SHIRT)
        c.poly([(150, 20), (290, 44), (372, 150), (390, 520), (230, 520), (230, 200)], SHIRT_D)
        c.poly([(-290, 44), (-150, 20), (-230, 200), (-230, 520), (-390, 520), (-372, 150)], (120, 130, 160))
        c.line([(-200, 130), (-150, 330)], 4, SHIRT_D, cap=False)
        # --- cuello ---------------------------------------------------------
        c.poly([(-58, -130), (58, -130), (66, 8), (-66, 8)], SKIN_D)
        c.ell(0, 10, 112, 40, SKIN_D)
        c.ell(0, 14, 104, 34, (60, 64, 86))      # cuello redondo de la camiseta
        c.ell(0, 4, 100, 30, SKIN_D)

        # --- cabeza ----------------------------------------------------------
        with c.push(0, -110, 1, tilt + tremor):
            with c.push(0, 110):
                c.ell(-150, -275, 20, 36, SKIN_D)
                c.ell(150, -275, 20, 36, SKIN_D)
                # base oscura + parte clara => media luna de sombra a la derecha
                c.ell(0, -300, 152, 172, SKIN_D)
                c.ell(0, -215, 120, 134, SKIN_D)
                c.ell(-9, -300, 143, 170, SKIN)
                c.ell(-7, -215, 112, 132, SKIN)
                for (x, y) in STUBBLE:
                    c.ell(x, y, 1.5, 1.5, (92, 64, 58, 105), 6)
                # cabello
                arc = [(160 * math.cos(math.radians(a)), -335 + 152 * math.sin(math.radians(a))) for a in range(180, 361, 10)]
                c.poly(arc + [(150, -290), (138, -330), (100, -312), (60, -338), (10, -310), (-40, -336),
                              (-90, -312), (-128, -322), (-150, -285)], HAIR)
                c.poly([(-160, -335), (-150, -285), (-140, -255), (-128, -300)], HAIR)
                c.poly([(160, -335), (150, -285), (140, -255), (128, -300)], HAIR)
                c.poly(arc[:6] + [(-60, -430)], (48, 42, 58))
                # nariz
                c.line([(-8, -292), (-17, -232), (2, -226), (16, -234)], 5, SKIN_D)
                c.ell(-9, -226, 8, 5, SKIN_D)
                c.ell(10, -226, 8, 5, SKIN_D)
                # ojos
                gx, gy = gaze
                for s in (-1, 1):
                    exx, eyy = s * 56, -283
                    ry = max(1.5, 22 * ex["eye"] * (1 - blink))
                    c.ell(exx, eyy, 31, ry, (244, 240, 236))
                    if ry > 4:
                        ir = min(14.5 * (0.7 + 0.3 * ex["pup"]) * 1.0, ry - 0.5)
                        px_, py_ = exx + gx * 11, eyy + gy * 8
                        c.ell(px_, py_, min(ir, 15), ir, (56, 36, 28))
                        c.ell(px_, py_, ir * ex["pup"] * 0.5 + 2, ir * ex["pup"] * 0.5 + 2, (8, 8, 10))
                        c.ell(px_ - 4, py_ - 4, 3.4, 3.4, (255, 255, 255))
                    c.line([(exx - 32, eyy - ry * 0.35), (exx - 14, eyy - ry), (exx + 14, eyy - ry), (exx + 32, eyy - ry * 0.35)],
                           5.5, (120, 74, 62))
                    # ojeras
                    c.line([(exx - 24, eyy + ry + 9), (exx + 24, eyy + ry + 9)], 3, (190, 128, 110, 140), cap=False)
                    # ceja
                    b = ex["bl"] if s < 0 else ex["br"]
                    base = -338 - b * 24
                    inner_y = base - ex["tilt"] * 20
                    outer_y = base + ex["tilt"] * 12 + 4
                    c.line([(s * 24, inner_y), (s * 56, base - 9 * (b > 0.4)), (s * 98, outer_y)], 12, HAIR)
                # boca
                my = -171
                w = 46 * ex["mw"]
                op = (ex["mo"] + talk) * 36
                pts_top, pts_bot = [], []
                for i in range(11):
                    u = i / 10
                    x = -w + 2 * w * u
                    cur = ((x / w) ** 2)
                    yt = my - ex["mc"] * 15 * (cur - 0.2) * (-1) - ex["mc"] * 0
                    yt = my + ex["mc"] * -16 * (cur - 0.35) * (-1) * (-1)
                    pts_top.append((x, my - ex["mc"] * 14 * cur + ex["mc"] * 4))
                    pts_bot.append((x, my - ex["mc"] * 14 * cur + ex["mc"] * 4 + op * (1 - cur) ** 0.8))
                if op > 3:
                    c.poly(pts_top + pts_bot[::-1], (66, 22, 30))
                    th = min(11, op * 0.34)
                    c.poly([(x, y) for x, y in pts_top[1:-1]] + [(x, y + th) for x, y in pts_top[1:-1][::-1]], (240, 236, 230))
                    c.ell(0, pts_bot[5][1] - op * 0.18, w * 0.42, op * 0.2, (150, 60, 66))
                    c.line(pts_top, 5, (150, 86, 78), cap=True)
                    c.line(pts_bot, 5, (160, 92, 82), cap=True)
                else:
                    c.line(pts_top, 6, (150, 78, 72))
                # sudor
                if sweat > 0:
                    yy = -380 + sweat * 90
                    c.poly([(128, yy - 28), (118, yy + 6), (128, yy + 18), (138, yy + 6)], (168, 214, 255, 220))
                # arrugas de preocupación
                if ex["tilt"] > 0.5:
                    for j in (-1, 1):
                        c.line([(j * 30, -378), (j * 6, -372)], 3, (170, 112, 92, 140), cap=False)
                c.line([(-22, -370), (22, -370)], 3, (170, 112, 92, 90 + int(60 * ex["bl"])), cap=False)

        # --- brazo/mano con teléfono ------------------------------------------
        if hold == "ear":
            c.limb((300, 520), (262, 70), 150, 130, SHIRT_D)
            c.limb((262, 70), (236, -120), 104, 84, SKIN)
            with c.push(212, -250, 1, 0.07):
                phone_back(c, 92, 250)
            c.rr(196, -218, 262, -176, 20, SKIN)
            hand_fingers(c, 234, -330, 3, 33)
            c.limb((240, -170), (252, -128), 60, 52, SKIN)
        elif hold == "front":
            c.limb((330, 520), (280, 250), 150, 120, SHIRT_D)
            c.limb((280, 250), (150, 150), 100, 84, SKIN)
            with c.push(100, 66, 1, -0.12):
                phone_back(c, 150, 300, glow=phone_glow)
            c.ell(40, 126, 30, 22, SKIN)
            c.rr(30, 80, 70, 170, 16, SKIN)
            hand_fingers(c, 36, 20, 3, 36)


# ---------------------------------------------------------------------------
# Cuerpo entero (perfil, mirando a la derecha). Origen = cadera.
# ---------------------------------------------------------------------------
def leg_pts(th, kf, L1=270, L2=260):
    kx, ky = L1 * math.sin(th), L1 * math.cos(th)
    a2 = th - kf
    return (kx, ky), (kx + L2 * math.sin(a2), ky + L2 * math.cos(a2))


def figure_height(phase, amp, kfl=0.55):
    ys = []
    for off in (0, math.pi):
        th = amp * math.sin(phase + off)
        kf = kfl * max(0, math.cos(phase + off + 0.35))
        _, an = leg_pts(th, kf)
        ys.append(an[1] + 34)
    return max(ys)


def draw_figure(c, phase=0.0, amp=0.28, lean=0.05, head_turn=0.0, arm=None, hold_phone=False,
                breath=0.0, arm_raise=0.0, head_down=0.0):
    """Dibuja el personaje; el llamante posiciona con c.push(x, y_cadera, k)."""
    swing = 0.16 if amp > 0.05 else 0.02

    def legs(back):
        off = math.pi if back else 0
        th = amp * math.sin(phase + off)
        kf = 0.55 * max(0, math.cos(phase + off + 0.35))
        kn, an = leg_pts(th, kf)
        col, colS = (PANTS_D, (16, 16, 22)) if back else (PANTS, SHOE)
        c.limb((0, 0), kn, 134, 104, col)
        c.limb(kn, an, 100, 76, col)
        ft = th - kf
        c.rr(an[0] - 34, an[1] - 14, an[0] + 84, an[1] + 36, 22, colS)

    def arm_draw(back):
        off = math.pi if back else 0
        sh = (-4, -305)
        base = -swing * math.sin(phase + off)
        up = base
        low = base + 0.28
        if not back and arm_raise > 0:
            up = lerp(base, 1.45, arm_raise)
            low = lerp(base + 0.28, 1.2, arm_raise)
        if not back and hold_phone and arm_raise <= 0:
            up, low = 0.25, 1.15
        el = (sh[0] + 195 * math.sin(up), sh[1] + 195 * math.cos(up))
        wr = (el[0] + 185 * math.sin(low), el[1] + 185 * math.cos(low))
        shirt = SHIRT_D if back else SHIRT
        skin = SKIN_D if back else SKIN
        c.limb(sh, el, 84, 68, shirt)
        c.limb(el, wr, 62, 46, skin)
        c.ell(wr[0] + 8, wr[1] + 12, 30, 34, skin)
        if not back and hold_phone and arm_raise <= 0:
            with c.push(wr[0] + 26, wr[1] - 10, 1, 0.5):
                phone_back(c, 54, 110)
        return wr

    legs(True)
    arm_draw(True)
    # torso
    with c.push(0, 0, 1, lean):
        c.poly([(-70, 20), (-82, -150), (-62, -300), (62, -318), (86, -160), (74, 20)], SHIRT)
        c.poly([(22, 20), (40, -318), (62, -318), (86, -160), (74, 20)], SHIRT_D)
        c.poly([(-74, -20), (74, -20), (82, 74), (-80, 74)], PANTS)
        c.rr(-78, -26, 80, -10, 6, (24, 24, 34))
        # cuello + cabeza
        with c.push(0, -318, 1, lean * -0.6 + head_down):
            c.limb((0, 0), (12, -52), 50, 46, SKIN_D)
            with c.push(14, -140, 1, head_turn * 0.0):
                c.ell(-4, 0, 74, 92, SKIN)
                c.ell(38, 22, 40, 56, SKIN)
                # nariz y barbilla (perfil)
                c.poly([(66, -6), (102, 22), (64, 34)], SKIN)
                c.ell(58, 62, 22, 18, SKIN)
                c.ell(-34, 8, 14, 22, SKIN_D)  # oreja
                arc = [(-78 * math.cos(math.radians(a)), -18 + 94 * math.sin(math.radians(a))) for a in range(180, 361, 12)]
                c.poly([(-78 * math.cos(math.radians(a)) * -1, -18 + 96 * math.sin(math.radians(a))) for a in range(180, 361, 12)]
                       + [(66, -18), (40, -4), (10, -26), (-30, -4), (-76, 30), (-80, 0)], HAIR)
                c.ell(-52, 6, 24, 54, HAIR)
                c.ell(46, -10, 11, 8 - 3 * breath, (240, 236, 230))
                c.ell(49 + head_turn * 2, -10, 5.5, 5.5, (20, 14, 16))
                c.line([(30, -30), (66, -28 - 6 * (1 if hold_phone else 0.5))], 8, HAIR)
                c.line([(44, 58), (66, 58)], 4, (150, 80, 74))
    legs(False)
    wr = arm_draw(False)
    return wr


def phone_screen(c, state, t, w=300, h=620, flash=0.0):
    """Pantalla del teléfono en coordenadas locales (origen = centro). t: segundos."""
    c.rr(-w / 2 - 12, -h / 2 - 12, w / 2 + 12, h / 2 + 12, 50, (14, 15, 22))
    c.rr(-w / 2 - 6, -h / 2 - 6, w / 2 + 6, h / 2 + 6, 46, (44, 46, 64))
    top, bot = {"incoming": ((18, 30, 70), (8, 10, 28)), "connected": ((20, 44, 64), (6, 14, 26)),
                "ended": ((34, 28, 48), (10, 8, 18)), "msg": ((22, 34, 78), (6, 8, 24)),
                "unknown": ((44, 26, 64), (10, 6, 22)), "dark": ((6, 6, 10), (4, 4, 8))}[state]
    n = 24
    for i in range(n):
        y0 = -h / 2 + h * i / n
        c.rr(-w / 2, y0, w / 2, y0 + h / n + 2, 0.1, mix(top, bot, i / n))
    # recorte redondeado de la pantalla
    c.rr(-w / 2, -h / 2, w / 2, -h / 2 + 4, 2, mix(top, bot, 0))
    c.rr(-w / 2 + 120, -h / 2 + 12, w / 2 - 120, -h / 2 + 34, 11, (6, 6, 10))
    c.text(-w / 2 + 30, -h / 2 + 24, "2:47", 17, (230, 236, 255), anchor="lm")
    c.text(w / 2 - 28, -h / 2 + 24, "5G ▮▮▮", 13, (230, 236, 255), anchor="rm")
    pulse = 0.5 + 0.5 * math.sin(t * 6.0)
    if state in ("incoming", "unknown"):
        lab = "Llamada entrante" if state == "incoming" else "Llamada entrante"
        c.text(0, -h / 2 + 100, lab, 24, (190, 205, 240), bold=False)
        for i, a in enumerate((0.0, 0.5)):
            ph = ((t * 0.9 + a) % 1.0)
            c.ell(0, -h / 2 + 232, 62 + ph * 62, 62 + ph * 62, (120, 160, 255, int(70 * (1 - ph))))
        c.ell(0, -h / 2 + 232, 60, 60, (70, 96, 170) if state == "incoming" else (90, 70, 130))
        if state == "incoming":
            c.ell(0, -h / 2 + 214, 20, 20, (210, 220, 245))
            c.ell(0, -h / 2 + 262, 40, 28, (210, 220, 245))
            c.text(0, -h / 2 + 340, "555 0142", 56, (255, 255, 255))
            col = mix((190, 210, 255), (255, 235, 130), flash)
            c.text(0, -h / 2 + 392, "Mi número · móvil", 24, col, bold=False)
        else:
            c.text(0, -h / 2 + 232, "?", 80, (230, 220, 250))
            c.text(0, -h / 2 + 340, "Número", 46, (255, 255, 255))
            c.text(0, -h / 2 + 392, "desconocido", 46, (255, 255, 255))
        yb = h / 2 - 118
        c.ell(-82, yb, 44, 44, (226, 62, 62))
        c.line([(-98, yb + 6), (-82, yb - 6), (-66, yb + 6)], 8, (255, 255, 255))
        gs = 44 + 6 * pulse
        c.ell(82, yb, gs, gs, (52, 200, 100))
        c.line([(66, yb - 6), (82, yb + 6), (98, yb - 6)], 8, (255, 255, 255))
        c.text(-82, yb + 76, "Rechazar", 17, (210, 215, 235), bold=False)
        c.text(82, yb + 76, "Contestar", 17, (210, 215, 235), bold=False)
    elif state == "connected":
        c.text(0, -h / 2 + 100, "En llamada", 24, (190, 230, 240), bold=False)
        c.ell(0, -h / 2 + 222, 60, 60, (70, 120, 150))
        c.ell(0, -h / 2 + 204, 20, 20, (210, 235, 245))
        c.ell(0, -h / 2 + 252, 40, 28, (210, 235, 245))
        c.text(0, -h / 2 + 330, "555 0142", 48, (255, 255, 255))
        c.text(0, -h / 2 + 380, "00:0%d" % min(9, int(t * 1.0) + 1), 28, (190, 230, 240), bold=False)
        for i in range(21):
            a = 8 + 34 * abs(math.sin(t * 7 + i * 0.7)) * abs(math.sin(i * 0.45 + 1))
            c.rr(-100 + i * 10 - 3, -h / 2 + 450 - a, -100 + i * 10 + 3, -h / 2 + 450 + a, 3, (120, 230, 255, 220))
        c.ell(0, h / 2 - 118, 44, 44, (226, 62, 62))
        c.line([(-20, h / 2 - 112), (0, h / 2 - 124), (20, h / 2 - 112)], 8, (255, 255, 255))
    elif state == "ended":
        c.text(0, -h / 2 + 110, "Llamada", 36, (230, 225, 245))
        c.text(0, -h / 2 + 158, "finalizada", 36, (230, 225, 245))
        c.ell(0, -h / 2 + 270, 56, 56, (86, 70, 120))
        c.text(0, -h / 2 + 370, "555 0142", 44, (255, 255, 255))
        c.text(0, -h / 2 + 420, "00:07", 28, (190, 180, 210), bold=False)
    elif state == "msg":
        c.text(0, -h / 2 + 170, "2:47", 100, (240, 244, 255))
        c.text(0, -h / 2 + 236, "jueves, 28 de noviembre", 20, (200, 212, 245), bold=False)
        slide = ease(clamp(t / 0.45))
        yy = lerp(-h / 2 - 80, -h / 2 + 330, slide)
        c.rr(-w / 2 + 14, yy, w / 2 - 14, yy + 150, 26, (236, 240, 250))
        c.rr(-w / 2 + 28, yy + 16, -w / 2 + 70, yy + 58, 10, (70, 110, 220))
        c.text(-w / 2 + 84, yy + 36, "Mensajes", 17, (60, 70, 100), anchor="lm")
        c.text(w / 2 - 28, yy + 36, "ahora", 15, (110, 120, 150), bold=False, anchor="rm")
        c.text(-w / 2 + 30, yy + 82, "555 0142", 24, (20, 24, 40), anchor="lm")
        c.text(-w / 2 + 30, yy + 120, "Mira por la ventana", 26, (30, 34, 54), bold=False, anchor="lm")
    elif state == "dark":
        pass
