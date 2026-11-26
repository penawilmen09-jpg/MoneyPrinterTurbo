"""Rig de personajes humanos 2D (esqueleto + animación por capas), dibujo vectorial con supersampling."""
import math, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "explora_ciencia360"))
import numpy as np
from PIL import Image, ImageDraw, ImageOps

CW, CH, HX, HY = 640, 760, 320, 400   # lienzo (unidades) y posición de la cadera
SKIN = (236, 190, 156)

def shade(c, k): return tuple(int(max(0, min(255, v * k))) for v in c)
def lerp(a, b, k): return a + (b - a) * k
def rot(x, y, a):
    c, s = math.cos(a), math.sin(a); return x * c - y * s, x * s + y * c

# ---------------- definiciones de personajes
PEOPLE = {
    "elon_teen":  dict(skin=(238, 196, 160), hair=(58, 40, 30), hairstyle="shaggy", glasses=True, top=(206, 74, 70), top2=(246, 226, 200), stripes=True, pants=(60, 84, 140), shoes=(240, 240, 240), sleeve="short", beard=0, build=.9, hr=1.0),
    "elon_young": dict(skin=(236, 190, 156), hair=(48, 34, 28), hairstyle="short", glasses=False, top=(120, 170, 220), top2=None, pants=(64, 66, 84), shoes=(40, 40, 48), sleeve="long", beard=0, build=1.0, hr=1.0, tie=False),
    "elon_adult": dict(skin=(232, 186, 152), hair=(44, 32, 26), hairstyle="swept", glasses=False, top=(30, 32, 40), top2=None, pants=(36, 38, 48), shoes=(24, 24, 28), sleeve="long", beard=1, build=1.08, hr=1.02, jacket=(26, 28, 36)),
    "kimbal":     dict(skin=(232, 184, 150), hair=(92, 62, 40), hairstyle="short", glasses=False, top=(70, 150, 120), top2=None, pants=(70, 70, 90), shoes=(50, 40, 40), sleeve="long", beard=1, build=1.0, hr=1.0),
    "exec1":      dict(skin=(226, 176, 142), hair=(150, 150, 156), hairstyle="neat", glasses=False, top=(40, 52, 90), top2=(240, 240, 244), pants=(40, 52, 90), shoes=(24, 24, 28), sleeve="long", beard=0, build=1.1, hr=1.0, suit=True),
    "exec2":      dict(skin=(190, 140, 110), hair=(30, 24, 22), hairstyle="neat", glasses=True, top=(70, 72, 80), top2=(240, 240, 244), pants=(70, 72, 80), shoes=(24, 24, 28), sleeve="long", beard=0, build=1.0, hr=1.0, suit=True),
    "dev_f":      dict(skin=(240, 200, 170), hair=(120, 60, 40), hairstyle="bun", glasses=False, top=(160, 110, 200), top2=None, pants=(50, 56, 80), shoes=(40, 40, 50), sleeve="long", beard=0, build=.92, hr=.98),
    "dev_m":      dict(skin=(170, 120, 92), hair=(24, 20, 20), hairstyle="short", glasses=True, top=(90, 160, 140), top2=None, pants=(60, 62, 76), shoes=(40, 40, 50), sleeve="short", beard=0, build=1.0, hr=1.0),
    "eng_m":      dict(skin=(226, 176, 142), hair=(60, 44, 34), hairstyle="hardhat", hat=(250, 250, 250), glasses=False, top=(255, 130, 40), top2=(60, 70, 90), pants=(60, 66, 84), shoes=(70, 56, 40), sleeve="long", beard=0, build=1.05, hr=1.0, vest=True),
    "eng_f":      dict(skin=(200, 150, 120), hair=(30, 24, 22), hairstyle="hardhat", hat=(250, 210, 60), glasses=False, top=(255, 130, 40), top2=(240, 240, 244), pants=(60, 66, 84), shoes=(70, 56, 40), sleeve="long", beard=0, build=.92, hr=.98, vest=True),
    "tech_w":     dict(skin=(214, 164, 130), hair=(40, 30, 26), hairstyle="hardhat", hat=(240, 240, 240), glasses=False, top=(235, 235, 240), top2=(60, 70, 90), pants=(60, 66, 84), shoes=(60, 50, 40), sleeve="long", beard=0, build=1.0, hr=1.0, vest=True),
}

POSE0 = dict(lean=0.0, bob=0.0, head=0.0, turn=0.0, sf=0.0, ef=0.0, sb=0.0, eb=0.0, hf=0.0, kf=0.0, hb=0.0, kb=0.0,
             mouth=0.0, smile=0.3, eyes=1.0, brow=0.0, lookx=0.0, looky=0.0, bx=0.0, handf=0.0, handb=0.0)


def mk(**kw):
    p = dict(POSE0); p.update(kw); return p


def blend(a, b, k):
    return {key: lerp(a[key], b[key], k) for key in a}


def limb(d, p0, p1, r0, r1, col, ss):
    (x0, y0), (x1, y1) = p0, p1
    dx, dy = x1 - x0, y1 - y0; L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L, dx / L
    pts = [(x0 + nx * r0, y0 + ny * r0), (x1 + nx * r1, y1 + ny * r1), (x1 - nx * r1, y1 - ny * r1), (x0 - nx * r0, y0 - ny * r0)]
    d.polygon([(a * ss, b * ss) for a, b in pts], fill=col)
    d.ellipse([(x0 - r0) * ss, (y0 - r0) * ss, (x0 + r0) * ss, (y0 + r0) * ss], fill=col)
    d.ellipse([(x1 - r1) * ss, (y1 - r1) * ss, (x1 + r1) * ss, (y1 + r1) * ss], fill=col)


def poly(d, pts, col, ss): d.polygon([(x * ss, y * ss) for x, y in pts], fill=col)
def ell(d, cx, cy, rx, ry, col, ss, outline=None, w=0):
    d.ellipse([(cx - rx) * ss, (cy - ry) * ss, (cx + rx) * ss, (cy + ry) * ss], fill=col, outline=outline, width=int(w * ss))


def smooth(pts, n=10):
    """Catmull-Rom abierto."""
    out = []
    P = [pts[0]] + list(pts) + [pts[-1]]
    for i in range(1, len(P) - 2):
        for j in range(n):
            t = j / n
            def f(k):
                return 0.5 * ((2 * P[i][k]) + (-P[i - 1][k] + P[i + 1][k]) * t + (2 * P[i - 1][k] - 5 * P[i][k] + 4 * P[i + 1][k] - P[i + 2][k]) * t * t + (-P[i - 1][k] + 3 * P[i][k] - 3 * P[i + 1][k] + P[i + 2][k]) * t ** 3)
            out.append((f(0), f(1)))
    out.append(P[-2])
    return out


def draw_head(d, spec, cx, cy, pose, ss, R=80):
    turn = pose["turn"]; skin = spec["skin"]; hr = spec["hr"]; R = R * hr
    hair = spec["hair"]; style = spec["hairstyle"]
    # pelo trasero
    if style in ("shaggy",):
        poly(d, [(cx - R * 1.05, cy - R * .2), (cx - R * 1.1, cy + R * .6), (cx - R * .5, cy + R * .55), (cx, cy - R * .6)], hair, ss)
    if style == "bun":
        ell(d, cx - R * .95, cy - R * .75, R * .42, R * .42, hair, ss)
    # cuello / mandíbula
    jaw = 1.0 + .06 * spec["beard"]
    ell(d, cx, cy, R, R * 1.04, skin, ss)
    # mandíbula cuadrada (rasgo distintivo en el adulto)
    poly(d, [(cx - R * .78, cy + R * .25), (cx + R * .85, cy + R * .2), (cx + R * .72, cy + R * 1.05 * jaw), (cx + R * .3, cy + R * 1.14 * jaw), (cx - R * .45, cy + R * 1.08 * jaw)], skin, ss)
    if spec["beard"]:
        bc = shade(hair, 1.1) if spec["beard"] == 1 else hair
        # sombra de barba (barba corta)
        sh = (int(lerp(skin[0], bc[0], .22)), int(lerp(skin[1], bc[1], .22)), int(lerp(skin[2], bc[2], .22)))
        poly(d, [(cx - R * .72, cy + R * .3), (cx + R * .8, cy + R * .3), (cx + R * .7, cy + R * 1.0 * jaw), (cx + R * .3, cy + R * 1.12 * jaw), (cx - R * .45, cy + R * 1.05 * jaw), (cx - R * .7, cy + R * .7)], sh, ss)
        # zona del mentón más clara hacia la boca
        ell(d, cx + lerp(R * .5, 0, turn), cy + R * .52, R * .42, R * .2, skin, ss)
    # orejas
    ell(d, cx + lerp(-R * .22, -R * .98, turn), cy + R * .08, R * .17, R * .24, shade(skin, .9), ss)
    if turn > .4:
        ell(d, cx + R * .98, cy + R * .08, R * .17 * turn, R * .24, shade(skin, .86), ss)
    # pelo frontal
    if style == "short":
        poly(d, smooth([(cx - R * 1.04, cy + R * .1), (cx - R * 1.0, cy - R * .6), (cx - R * .5, cy - R * 1.08), (cx + R * .3, cy - R * 1.12), (cx + R * .85, cy - R * .78), (cx + R * .95, cy - R * .42), (cx + R * .5, cy - R * .62), (cx - R * .2, cy - R * .5), (cx - R * .55, cy - R * .1)], 8), hair, ss)
    elif style == "swept":      # Elon adulto: castaño oscuro, peinado hacia atrás, entradas marcadas
        poly(d, smooth([(cx - R * 1.06, cy + R * .15), (cx - R * 1.04, cy - R * .55), (cx - R * .6, cy - R * 1.06), (cx + R * .1, cy - R * 1.18), (cx + R * .75, cy - R * .95), (cx + R * .98, cy - R * .5), (cx + R * .66, cy - R * .6), (cx + R * .3, cy - R * .78), (cx - R * .1, cy - R * .62), (cx - R * .55, cy - R * .25)], 8), hair, ss)
    elif style == "neat":
        poly(d, smooth([(cx - R * 1.04, cy + R * .1), (cx - R * 1.0, cy - R * .55), (cx - R * .4, cy - R * 1.06), (cx + R * .5, cy - R * 1.02), (cx + R * .95, cy - R * .5), (cx + R * .6, cy - R * .72), (cx - R * .3, cy - R * .6), (cx - R * .6, cy - R * .2)], 8), hair, ss)
    elif style == "shaggy":
        poly(d, smooth([(cx - R * 1.1, cy + R * .3), (cx - R * 1.08, cy - R * .5), (cx - R * .5, cy - R * 1.12), (cx + R * .4, cy - R * 1.16), (cx + R * 1.0, cy - R * .62), (cx + R * 1.02, cy - R * .2), (cx + R * .62, cy - R * .5), (cx + R * .3, cy - R * .26), (cx - R * .15, cy - R * .5), (cx - R * .5, cy - R * .1), (cx - R * .8, cy + R * .3)], 8), hair, ss)
    elif style == "bun":
        poly(d, smooth([(cx - R * 1.05, cy + R * .1), (cx - R * 1.02, cy - R * .6), (cx - R * .4, cy - R * 1.08), (cx + R * .5, cy - R * 1.04), (cx + R * .98, cy - R * .5), (cx + R * .5, cy - R * .7), (cx - R * .2, cy - R * .55), (cx - R * .55, cy - R * .1)], 8), hair, ss)
    elif style == "hardhat":
        poly(d, smooth([(cx - R * 1.04, cy + R * .1), (cx - R * 1.0, cy - R * .5), (cx - R * .4, cy - R * .8), (cx + R * .3, cy - R * .8), (cx + R * .9, cy - R * .5), (cx + R * .5, cy - R * .5), (cx - R * .3, cy - R * .4), (cx - R * .55, cy - R * .1)], 8), hair, ss)
        hc = spec["hat"]
        poly(d, smooth([(cx - R * 1.12, cy - R * .42), (cx - R * 1.04, cy - R * .95), (cx - R * .4, cy - R * 1.35), (cx + R * .4, cy - R * 1.36), (cx + R * 1.0, cy - R * .95), (cx + R * 1.12, cy - R * .46)], 8), hc, ss)
        poly(d, [(cx - R * 1.16, cy - R * .42), (cx + R * 1.3, cy - R * .42), (cx + R * 1.3, cy - R * .56), (cx - R * 1.16, cy - R * .56)], shade(hc, .86), ss)
        poly(d, [(cx - R * .1, cy - R * 1.36), (cx + R * .16, cy - R * 1.36), (cx + R * .14, cy - R * .56), (cx - R * .08, cy - R * .56)], shade(hc, .92), ss)
    # rasgos faciales
    e1 = cx + lerp(R * .22, -R * .36, turn); e2 = cx + lerp(R * .68, R * .36, turn)
    ey = cy - R * .04 + pose["looky"] * 1.5
    op = max(pose["eyes"], 0.0)
    for k, ex in enumerate((e1, e2)):
        rx = R * (.17 if k == 0 else .14 * (1 - .15 * (1 - turn)))
        ry = R * .15 * op
        if op > .12:
            ell(d, ex, ey, rx, ry, (252, 252, 252), ss)
            ell(d, ex + pose["lookx"] * 3.0 + R * .05, ey + pose["looky"] * 2.0, rx * .62, min(ry, rx * .62), (56, 40, 30), ss)
            ell(d, ex + pose["lookx"] * 3.0 + R * .05, ey + pose["looky"] * 2.0, rx * .32, min(ry, rx * .32), (10, 10, 14), ss)
            ell(d, ex + pose["lookx"] * 3.0 + R * .1, ey + pose["looky"] * 2.0 - R * .04, rx * .13, rx * .13, (255, 255, 255), ss)
        else:
            d.line([(ex - rx) * ss, ey * ss, (ex + rx) * ss, ey * ss], fill=(60, 40, 34), width=int(3 * ss))
        # cejas
        br = pose["brow"]; by = ey - R * (.30 + .10 * max(br, 0) - .04 * min(br, 0))
        tilt = -pose["brow"] * 0.0
        bt = R * .075 * (1 + (.3 if spec["hairstyle"] in ("swept",) else 0))
        a0 = (ex - rx * 1.2, by + (R * .06 * (-br if k == 1 else br) * 0 + (0 if br >= 0 else R * .05)))
        a1 = (ex + rx * 1.2, by + (R * .0 if br >= 0 else -R * .04))
        d.line([a0[0] * ss, a0[1] * ss, a1[0] * ss, a1[1] * ss], fill=shade(hair, .9), width=int(bt * ss))
    if spec.get("glasses"):
        for ex in (e1, e2):
            ell(d, ex, ey, R * .27, R * .24, None, ss, outline=(30, 30, 40), w=3)
        d.line([(e1 + R * .27) * ss, ey * ss, (e2 - R * .27) * ss, ey * ss], fill=(30, 30, 40), width=int(3 * ss))
        d.line([(e1 - R * .27) * ss, ey * ss, (cx - R * 1.0) * ss, (ey - 2) * ss], fill=(30, 30, 40), width=int(3 * ss))
    # nariz
    nx = cx + lerp(R * .86, 0, turn)
    nose = shade(skin, .93)
    if turn < .6:
        poly(d, [(nx - R * .02, ey + R * .02), (nx + R * .2 * (1 - turn), ey + R * .38), (nx - R * .1, ey + R * .42)], nose, ss)
    else:
        ell(d, nx, ey + R * .36, R * .12, R * .09, nose, ss)
    # boca
    mx = cx + lerp(R * .52, 0, turn); my = cy + R * .52
    mw = R * .26; sm = pose["smile"]; op_m = pose["mouth"]
    left = (mx - mw, my - sm * R * .05); right = (mx + mw, my - sm * R * .09)
    ctrl = (mx, my + R * .06 + sm * R * .10)
    top = [(left[0] + (right[0] - left[0]) * t, (1 - t) ** 2 * left[1] + 2 * t * (1 - t) * (my - R * .01) + t * t * right[1]) for t in np.linspace(0, 1, 12)]
    bot = [(left[0] + (right[0] - left[0]) * t, (1 - t) ** 2 * left[1] + 2 * t * (1 - t) * (ctrl[1] + op_m * R * .26) + t * t * right[1]) for t in np.linspace(0, 1, 12)]
    poly(d, top + bot[::-1], (120, 40, 48) if op_m > .08 else (170, 90, 90), ss)
    if op_m > .3:
        poly(d, top + [(x, y + R * .06 * min(op_m, 1)) for x, y in top[::-1]], (252, 252, 252), ss)
    d.line([(x * ss, y * ss) for x, y in top], fill=(150, 70, 70), width=int(2.5 * ss))
    if sm > .5:
        ell(d, right[0] + 2, right[1] - 2, R * .05, R * .05, shade(skin, .86), ss)


def draw_person(name, pose=None, k=1.0, flip=False, ss=2, role=None):
    """Devuelve RGBA (CW*k × CH*k); la cadera está en (HX*k, HY*k)."""
    spec = PEOPLE[name]; P = dict(POSE0); P.update(pose or {})
    S = ss * k
    im = Image.new("RGBA", (int(CW * S), int(CH * S)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    b = spec["build"]; skin = spec["skin"]
    top, pants, shoes = spec["top"], spec["pants"], spec["shoes"]
    rad = lambda a: math.radians(a)
    hip = (HX + P["bx"], HY + P["bob"])
    lean = rad(P["lean"])
    def fk(origin, a, L):
        return (origin[0] + L * math.sin(a), origin[1] + L * math.cos(a))
    # esqueleto
    TL = 150 * spec["hr"]
    sh = (hip[0] + TL * math.sin(lean), hip[1] - TL * math.cos(lean))
    shf = (sh[0] + 9 * math.cos(lean) + 6 * math.sin(lean), sh[1] + 20); shb = (sh[0] - 9 * math.cos(lean), sh[1] + 20)
    hipf = (hip[0] + 9, hip[1]); hipb = (hip[0] - 9, hip[1])
    # piernas
    def leg(hp, a, kn, col, colp):
        knee = fk(hp, rad(a), 122); ank = fk(knee, rad(a - kn), 120)
        limb(d, hp, knee, 40 * b, 31 * b, col, S); limb(d, knee, ank, 31 * b, 23 * b, col, S)
        # zapato
        fa = rad(a - kn)
        toe = (ank[0] + 56 * math.cos(0.0) , ank[1] + 18)
        poly(d, [(ank[0] - 20, ank[1] - 8), (ank[0] + 22, ank[1] - 10), (toe[0] + 6, toe[1] - 8), (toe[0] + 4, toe[1] + 10), (ank[0] - 24, ank[1] + 16)], colp, S)
        poly(d, [(ank[0] - 24, ank[1] + 12), (toe[0] + 4, toe[1] + 6), (toe[0] + 4, toe[1] + 14), (ank[0] - 24, ank[1] + 20)], (235, 235, 235) if spec["glasses"] and spec.get("stripes") else shade(colp, .6), S)
        return knee, ank
    leg(hipb, P["hb"], P["kb"], shade(pants, .78), shade(shoes, .78))
    # brazo trasero
    def arm(sp, a, el, colS, colF, handcol, hand_open):
        elb = fk(sp, rad(a), 92); wr = fk(elb, rad(a + el), 86)
        limb(d, sp, elb, 28 * b, 24 * b, colS, S); limb(d, elb, wr, 24 * b, 19 * b, colF, S)
        ell(d, wr[0], wr[1], 22, 24, handcol, S)
        return elb, wr
    sleeve_s = top if spec["sleeve"] == "long" or spec.get("suit") else top
    fore_b = shade(top, .78) if spec["sleeve"] == "long" else shade(skin, .86)
    arm(shb, P["sb"], P["eb"], shade(top, .78), fore_b, shade(skin, .86), 0)
    leg(hipf, P["hf"], P["kf"], pants, shoes)
    # torso
    tw = 104 * b
    torso = [(hip[0] - 62 * b, hip[1] + 6), (hip[0] + 62 * b, hip[1] + 6), (sh[0] + tw * .62 + 6, sh[1] + 4), (sh[0] + 8, sh[1] - 8), (sh[0] - 8, sh[1] - 8), (sh[0] - tw * .62 - 6, sh[1] + 4)]
    poly(d, torso, top, S)
    ell(d, sh[0], sh[1] + 6, tw * .62 + 8, 26, top, S)
    if spec.get("suit"):
        # camisa y corbata
        poly(d, [(sh[0] - 22, sh[1] - 6), (sh[0] + 22, sh[1] - 6), (hip[0] + 6, hip[1] - 40), (hip[0] - 6, hip[1] - 40)], spec["top2"], S)
        poly(d, [(sh[0] - 7, sh[1] - 4), (sh[0] + 7, sh[1] - 4), (sh[0] + 9, sh[1] + 70), (sh[0], sh[1] + 86), (sh[0] - 9, sh[1] + 70)], (200, 50, 60), S)
    elif spec.get("jacket"):
        poly(d, [(sh[0] - 20, sh[1] - 6), (sh[0] + 20, sh[1] - 6), (hip[0] + 4, hip[1] - 20), (hip[0] - 4, hip[1] - 20)], (40, 42, 52), S)
    elif spec.get("vest"):
        poly(d, [(hip[0] - 62 * b, hip[1] + 6), (hip[0] + 62 * b, hip[1] + 6), (sh[0] + tw * .62 + 6, sh[1] + 4), (sh[0] - tw * .62 - 6, sh[1] + 4)], spec["top"], S)
        d.polygon([(x * S, y * S) for x, y in [(hip[0] - 62 * b, hip[1] - 60), (hip[0] + 62 * b, hip[1] - 60), (hip[0] + 62 * b, hip[1] - 42), (hip[0] - 62 * b, hip[1] - 42)]], fill=(245, 245, 200))
    elif spec.get("stripes"):
        for i in range(6):
            yy = sh[1] + 20 + i * 26
            poly(d, [(hip[0] - 62 * b, yy), (hip[0] + 62 * b, yy), (hip[0] + 62 * b, yy + 11), (hip[0] - 62 * b, yy + 11)], spec["top2"], S)
        # recorte: re-dibujar las esquinas fuera del torso con el fondo transparente no es necesario (franjas dentro del ancho)
    # cinturón / pantalón
    poly(d, [(hip[0] - 60 * b, hip[1] + 10), (hip[0] + 60 * b, hip[1] + 10), (hip[0] + 60 * b, hip[1] + 40), (hip[0] - 60 * b, hip[1] + 40)], pants, S)
    # cuello
    neck = (sh[0] + 4 * math.sin(rad(P["head"])), sh[1] - 14)
    limb(d, (sh[0], sh[1] - 4), neck, 21, 19, shade(skin, .92), S)
    # cabeza
    hc = (neck[0] + 6 * math.sin(rad(P["head"])), neck[1] - 92 * spec["hr"])
    # cabeza rotada por inclinación: se dibuja en un sub-lienzo y se pega rotada
    HW = int(380 * S)
    hd = Image.new("RGBA", (HW, HW), (0, 0, 0, 0)); dd = ImageDraw.Draw(hd)
    draw_head(dd, spec, 150 * S / S, 150 * S / S, P, S) if False else None
    draw_head(dd, spec, HW / 2 / S, HW / 2 / S + 20, P, S)
    if abs(P["head"]) > .4:
        hd = hd.rotate(-P["head"], resample=Image.BILINEAR, center=(HW / 2, HW / 2 + 70 * S))
    im.alpha_composite(hd, (int((hc[0]) * S - HW / 2), int((hc[1] - 20) * S - HW / 2)))
    # brazo delantero (encima del torso)
    ef = arm(shf, P["sf"], P["ef"], shade(top, 1.12) if sum(top) < 300 else top, shade(top, 1.12) if (spec["sleeve"] == "long" and sum(top) < 300) else (top if spec["sleeve"] == "long" else skin), skin, 0)
    out = im.resize((int(CW * k), int(CH * k)), Image.LANCZOS)
    if flip:
        out = ImageOps.mirror(out)
    return out


# ---------------- ciclos de animación
def walk_pose(ph, speed=1.0, **extra):
    a = 2 * math.pi * ph
    amp = 26 * speed
    p = mk(hf=amp * math.sin(a), hb=-amp * math.sin(a),
           kf=8 + 34 * max(0, math.sin(a + 1.6)) * speed, kb=8 + 34 * max(0, math.sin(a + 1.6 + math.pi)) * speed,
           sf=-amp * .9 * math.sin(a), sb=amp * .9 * math.sin(a), ef=14 + 10 * speed, eb=14 + 10 * speed,
           bob=-5 * abs(math.sin(a)) * speed, lean=3 * speed, head=-1.5)
    p.update(extra); return p


def run_pose(ph, **extra):
    a = 2 * math.pi * ph
    p = mk(hf=48 * math.sin(a), hb=-48 * math.sin(a), kf=20 + 70 * max(0, math.sin(a + 1.4)), kb=20 + 70 * max(0, math.sin(a + 1.4 + math.pi)),
           sf=-55 * math.sin(a), sb=55 * math.sin(a), ef=80, eb=80, bob=-16 * abs(math.sin(a)), lean=12, head=-3)
    p.update(extra); return p


def blink(t, period=3.4, off=0.0):
    x = (t + off) % period
    return 1 - (math.sin(math.pi * x / 0.16) if x < 0.16 else 0)
