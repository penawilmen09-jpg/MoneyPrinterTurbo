"""Video 9 · Explora Ciencia 360 — ¿Por qué las naves espaciales no se queman al regresar a la Tierra?"""
import math
import random
from .core import W, H, n, clamp, lerp, prog, smooth, ease_out, ease_in_out, ease_out_back
from .svgkit import layer, cam_at, text
from .art import capsule as cp
from .art import earth as ea
from .art import heli as hl
from .art import ocean as oc
from .scenes_moon import logo

SCENES = {}


def scene(fn):
    SCENES[fn.__name__.replace("scene_", "")] = fn
    return fn


def pop(t, start, dur=.5):
    return max(ease_out_back(prog(t, start, start + dur)), .001)


def pill(x, y, w, label, fill="#10305F", stroke="#7CD3FF", color="#CFF1FF", size=32, s=1.0, op=1.0):
    return (f'<g transform="translate({x},{y}) scale({s})" opacity="{op:.2f}"><rect x="{-w/2:.0f}" y="-34" width="{w}" height="68" rx="34" fill="{fill}" stroke="{stroke}" stroke-width="5"/>'
            + text(0, size * .35, label, size, color) + '</g>')


def space(t):
    return '<rect width="1080" height="1920" fill="url(#space)"/>' + ea.stars(t, 70)


def limb(t, y, tint=0.0):
    """Borde de la Tierra con atmósfera brillante."""
    return (f'<circle cx="540" cy="{y+1500}" r="1500" fill="#0A2A66"/><circle cx="540" cy="{y+1500}" r="1500" fill="none" stroke="#5CB8FF" stroke-width="60" opacity=".35"/>'
            f'<circle cx="540" cy="{y+1500}" r="1530" fill="none" stroke="#9FD8FF" stroke-width="26" opacity=".5"/>'
            f'<circle cx="540" cy="{y+1500}" r="1500" fill="none" stroke="#FF8A3D" stroke-width="40" opacity="{tint*.45:.2f}"/>')


# ------------------------------------------------------------------ 1. gancho
@scene
def scene_hook(t, d):
    k = ease_in_out(prog(t, 0, d * .78))
    cam = cam_at(1.0 + 1.1 * k, lerp(520, 560, k), lerp(900, 800, k))
    sh = 5 * math.sin(t * 55) * (.4 + k)
    out = layer(space(t), cam, .25) + layer(limb(t, 1130, tint=1), cam, .6)
    main = ""
    for i in range(14):                                          # líneas de velocidad
        x0 = (i * 97 + t * 900) % 1500 - 200; y0 = 300 + (i * 131) % 700
        main += f'<line x1="{x0:.0f}" y1="{y0 - x0*0.0:.0f}" x2="{x0-260:.0f}" y2="{y0-150:.0f}" stroke="#FFD9A0" stroke-width="4" stroke-linecap="round" opacity=".28"/>'
    main += cp.capsule(560 + sh, 760 + sh, 1.0, 62, t, 1.0)
    out += layer(main, cam)
    out += f'<rect width="1080" height="1920" fill="#FF8A3D" opacity="{.06+.04*math.sin(t*20):.2f}"/>'
    if t < d * .66:
        out += text(540, 190, "¡REENTRADA!", 96, "#fff", sw=17, scale=pop(t, .05, .45) * (1 + .02 * math.sin(t * 25)))
        out += pill(540, 290, 920, "≈ 40 000 km/h · REFERENCIA: NAVE ORION (NASA)", "#4A1E05", "#FF8A3D", "#FFD9A8", 26, pop(t, .4, .45))
    else:
        out += text(540, 200, "¿POR QUÉ NO", 90, "#fff", sw=16, scale=pop(t, d * .66, .45)) + text(540, 300, "SE QUEMA?", 100, "#FFE14D", sw=17, scale=pop(t, d * .66 + .15, .45))
    return out


# ------------------------------------------------------------------ 2. ¿de dónde viene el calor?
def _xs(dy):
    return 440 + .0012 * dy * dy


@scene
def scene_heat(t, d):
    cx, cy, s = 800, 740, 1.5
    out = '<rect width="1080" height="1920" fill="#06091C"/>' + ea.stars(t, 40)
    out += f'<circle cx="{cx-130}" cy="{cy}" r="360" fill="url(#plasma)" opacity="{.25+.35*smooth(prog(t,d*.2,d*.6)):.2f}"/>'
    out += cp.capsule(cx, cy, s, 180, t, 0.0, glow=smooth(prog(t, d * .3, d * .7)) * .9)
    # flujo de aire (referencia de la cápsula): se acumula delante del escudo
    rnd = random.Random(8)
    T = 4.2
    for i in range(78):
        dy = rnd.uniform(-300, 300); ph = rnd.uniform(0, T)
        tau = (t + ph) % T; sg = 1 if dy >= 0 else -1
        xs = _xs(dy)
        if tau < .9:
            x = lerp(-20, xs, tau / .9); y = cy + dy; col = "#7CD3FF"; r = 4; op = .85
        elif tau < 2.5:
            u = (tau - .9) / 1.6
            x = xs + 70 * smooth(u) + rnd.uniform(-5, 5); y = cy + dy + 6 * math.sin(tau * 14 + i)
            col = "#FFE28A" if u < .35 else "#FFFFFF" if u < .65 else "#FF8A3D"; r = 5 + 3 * u; op = .95
        else:
            v = (tau - 2.5) / 1.7
            x = xs + 70 + (1000 - xs - 70) * (v ** 1.3); y = cy + sg * (abs(dy) + max(0, 190 - abs(dy)) * smooth(v * 3) + 150 * v)
            col = "#FF6A3D"; r = 6 * (1 - v) + 2; op = max(0, 1 - v)
        out += f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.1f}" fill="{col}" opacity="{op:.2f}"/>'
    pts = " ".join(f"{_xs(dy):.0f},{cy+dy:.0f}" for dy in range(-330, 331, 15))
    out += f'<polyline points="{pts}" fill="none" stroke="#fff" stroke-width="5" stroke-dasharray="18 10" opacity="{.5+.3*math.sin(t*6):.2f}"/>'
    # flechas de velocidad hipersónica
    for i in range(3):
        xx = (i * 150 + t * 400) % 450 + 20
        out += f'<polygon points="{xx+60:.0f},{cy-250+i*0} {xx:.0f},{cy-276} {xx:.0f},{cy-224}" fill="#7CD3FF" opacity=".7"/>'
    out += text(540, 190, "¿DE DÓNDE VIENE EL CALOR?", 56, "#fff", sw=13, scale=pop(t, 0, .5))
    if t > d * .25:
        a = pop(t, d * .25, .4)
        out += f'<line x1="{_xs(-250)+10:.0f}" y1="{cy-250}" x2="300" y2="400" stroke="#fff" stroke-width="3" opacity="{min(1,a):.2f}"/>' + pill(300, 380, 400, "ONDA DE CHOQUE", "#0B1B4A", "#fff", "#fff", 26, a)
    if t > d * .45:
        a = pop(t, d * .45, .4)
        out += pill(380, 1030, 640, "AIRE COMPRIMIDO = MUY CALIENTE", "#4A1E05", "#FF8A3D", "#FFD9A8", 26, a)
    if t > d * .68:
        a = pop(t, d * .68, .4)
        out += pill(540, 1110, 900, "NO ES SOLO ROCE · NO ES COMBUSTIÓN", "#0B1030", "#FFE14D", "#FFE14D", 30, a)
    out += text(250, cy - 190, "velocidad hipersónica →", 28, "#9FD0FF", sw=7, opacity=prog(t, 1, 1.6))
    return out


# ------------------------------------------------------------------ 3. el escudo térmico
@scene
def scene_shield(t, d):
    sw = d * .3
    out = '<rect width="1080" height="1920" fill="#08101F"/>' + ea.stars(t, 30)
    if t < sw + .5:
        a = 1 - prog(t, sw, sw + .5)
        g = cp.capsule(540, 660, 1.9, 90, t, 0.0, glow=.3 + .3 * math.sin(t * 4)) 
        for i in range(7):                                         # calor que llega por debajo
            x = 330 + i * 70; ph = (t * 1.3 + i * .14) % 1
            g += f'<line x1="{x}" y1="{1100 - ph*150:.0f}" x2="{x}" y2="{1050 - ph*150:.0f}" stroke="#FF8A3D" stroke-width="10" stroke-linecap="round" opacity="{(1-ph)*.9:.2f}"/>'
        g += f'<line x1="540" y1="930" x2="540" y2="1010" stroke="#fff" stroke-width="3"/>' + pill(540, 1040, 520, "ESCUDO TÉRMICO", "#4A2F1B", "#FF8A3D", "#FFD9A8", 34, pop(t, .2, .4))
        out += f'<g opacity="{a:.2f}">{g}</g>'
    if t > sw:
        b = prog(t, sw, sw + .6)
        x0, x1 = 110, 690
        g = ""
        # gas caliente
        g += f'<rect x="{x0}" y="370" width="{x1-x0}" height="110" fill="url(#plasma)" opacity=".8"/>'
        for j in range(6):
            xx = x0 + 40 + j * 95
            g += f'<polyline points="{" ".join(f"{xx+14*math.sin(u*.9+t*6+j):.0f},{380+u*8:.0f}" for u in range(0, 13))}" fill="none" stroke="#FFE9A8" stroke-width="5" opacity=".7"/>'
        # superficie, material protector, estructura, interior
        g += f'<rect x="{x0}" y="480" width="{x1-x0}" height="44" fill="#1B1B1B"/><rect x="{x0}" y="478" width="{x1-x0}" height="6" fill="#FF8A3D" opacity="{.6+.3*math.sin(t*8):.2f}"/>'
        g += f'<rect x="{x0}" y="524" width="{x1-x0}" height="190" fill="url(#avcoat)"/>'
        for r in range(5):
            for c in range(11):
                hx, hy = x0 + 25 + c * 50 + (25 if r % 2 else 0), 545 + r * 38
                g += f'<polygon points="{hx},{hy-16} {hx+14},{hy-8} {hx+14},{hy+8} {hx},{hy+16} {hx-14},{hy+8} {hx-14},{hy-8}" fill="none" stroke="#1E140F" stroke-width="2" opacity=".55"/>'
        g += f'<rect x="{x0}" y="714" width="{x1-x0}" height="70" fill="#8A93A8"/>' + "".join(f'<circle cx="{x0+30+i*60}" cy="749" r="6" fill="#5B6578"/>' for i in range(9))
        g += f'<rect x="{x0}" y="784" width="{x1-x0}" height="230" fill="#12335E"/><rect x="{x0}" y="784" width="{x1-x0}" height="230" fill="url(#glowC)" opacity=".15"/>'
        for i in range(3):                                         # asientos vacíos (cabina), sin personas
            g += f'<rect x="{x0+60+i*160}" y="860" width="100" height="120" rx="22" fill="#1D4E8F" stroke="#4DB8FF" stroke-width="3"/>'
        # flechas de calor: fuertes arriba, bloqueadas por el escudo
        for i in range(6):
            xx = x0 + 40 + i * 100; ph = (t * 1.2 + i * .17) % 1
            g += f'<polygon points="{xx},{500+ph*10:.0f} {xx-16},{462+ph*10:.0f} {xx+16},{462+ph*10:.0f}" fill="#FF4D2E" opacity="{.9-.2*ph:.2f}"/>'
        for i in range(4):
            xx = x0 + 90 + i * 130
            g += f'<polygon points="{xx},{930} {xx-9},{905} {xx+9},{905}" fill="#7CD3FF" opacity=".25"/>'
        g += f'<rect x="{x0}" y="370" width="{x1-x0}" height="644" fill="none" stroke="#fff" stroke-width="4" opacity=".5"/>'
        out += f'<g opacity="{b:.2f}" transform="translate(-40,-60) translate(400,690) scale(1.05) translate(-400,-690)">{g}</g>'
        out += '<g transform="translate(-40,-60) translate(400,690) scale(1.05) translate(-400,-690)">'
        for (yy, lab, col, tt) in ((505, "SUPERFICIE", "#FF8A3D", .38), (620, "MATERIAL PROTECTOR", "#FFB347", .5), (749, "ESTRUCTURA", "#AEB8CC", .62), (900, "INTERIOR", "#7CD3FF", .74)):
            a = pop(t, d * tt, .4)
            out += f'<line x1="{x1}" y1="{yy}" x2="700" y2="{yy}" stroke="{col}" stroke-width="3" opacity="{min(1,a):.2f}"/>' + text(705, yy + 9, lab, 25, col, anchor="start", sw=6, opacity=min(1, a)) + (text(705, yy + 36, "expuesta al calor", 20, "#FFD9A8", anchor="start", sw=5, opacity=min(1, a)) if lab == "SUPERFICIE" else "")
        out += '</g>'
        out += text(540, 190, "EL ESCUDO TÉRMICO", 66, "#fff", sw=14, scale=pop(t, sw, .5))
        if t > d * .8:
            out += pill(540, 1110, 880, "EL CALOR NO LLEGA AL INTERIOR", "#0F3F2A", "#35E08A", "#CFFFE5", 34, pop(t, d * .8, .4))
    else:
        out += text(540, 190, "EL ESCUDO TÉRMICO", 66, "#fff", sw=14, scale=pop(t, 0, .5))
    return out


# ------------------------------------------------------------------ 4. ablación
@scene
def scene_ablation(t, d):
    k = smooth(prog(t, d * .22, d * .85))
    x0, x1 = 230, 710
    top = 520 + 130 * k
    out = '<rect width="1080" height="1920" fill="#08101F"/>' + ea.stars(t, 30)
    out += f'<rect x="{x0-30}" y="330" width="{x1-x0+60}" height="{top-330+10:.0f}" fill="url(#plasma)" opacity=".55"/>'
    # bloque de Avcoat con celdas en forma de panal
    out += f'<rect x="{x0}" y="{top:.0f}" width="{x1-x0}" height="{1010-top:.0f}" fill="url(#avcoat)"/>'
    for r in range(11):
        for c in range(9):
            hx, hy = x0 + 28 + c * 54 + (27 if r % 2 else 0), top + 44 + r * 42
            if hy < 990:
                out += f'<polygon points="{hx},{hy-17} {hx+15},{hy-9} {hx+15},{hy+9} {hx},{hy+17} {hx-15},{hy+9} {hx-15},{hy-9}" fill="none" stroke="#1E140F" stroke-width="2" opacity=".5"/>'
    out += f'<rect x="{x0}" y="{top-6:.0f}" width="{x1-x0}" height="26" fill="#1B1B1B"/><rect x="{x0}" y="{top-8:.0f}" width="{x1-x0}" height="6" fill="#FF8A3D" opacity="{.7+.3*math.sin(t*9):.2f}"/>'
    out += f'<rect x="{x0}" y="1010" width="{x1-x0}" height="110" fill="#12335E"/>' + text((x0 + x1) / 2, 1078, "INTERIOR PROTEGIDO", 28, "#7CD3FF", sw=7)
    # trocitos de material y gases que se llevan el calor
    rnd = random.Random(6)
    for i in range(34):
        ph = (t * .55 + rnd.random()) % 1
        px = x0 + rnd.uniform(30, x1 - x0 - 30) + 330 * ph ** 1.4
        py = top - 8 - 330 * ph
        if k > .02:
            sz = 11 * (1 - ph) + 3
            out += f'<rect x="{px:.0f}" y="{py:.0f}" width="{sz:.0f}" height="{sz*.7:.0f}" fill="{"#2A1A12" if ph<.35 else "#FF8A3D"}" opacity="{(1-ph)*.95:.2f}" transform="rotate({ph*400+i*30:.0f} {px:.0f} {py:.0f})"/>'
            out += f'<circle cx="{px+10:.0f}" cy="{py-14:.0f}" r="{18*ph+6:.0f}" fill="#FFD9A8" opacity="{(1-ph)*.35:.2f}"/>'
    # flechas: el calor se va con el material
    for i in range(3):
        ph = (t * .8 + i / 3) % 1
        out += hl.arrow(x1 + 30 + 90 * ph, 470 - 60 * ph + i * 8, x1 + 90 + 150 * ph, 400 - 120 * ph + i * 8, "#FF8A3D", 9, 26) if False else ""
    out += hl.arrow(x1 + 40, 560, x1 + 230, 430, "#FF8A3D", 12, 34) + text(x1 + 140, 395, "calor", 28, "#FFD9A8", sw=7) + text(x1 + 140, 428, "se va con él", 26, "#FFD9A8", sw=7) if k > .05 else ""
    # regla de espesor
    out += f'<line x1="{x1+60}" y1="520" x2="{x1+60}" y2="{top:.0f}" stroke="#fff" stroke-width="5"/><line x1="{x1+44}" y1="520" x2="{x1+76}" y2="520" stroke="#fff" stroke-width="4" stroke-dasharray="6 6"/>'
    out += text(x1 + 130, (520 + top) / 2 + 8, "menos", 26, "#fff", sw=7) if k > .1 else ""
    out += text(540, 190, "ABLACIÓN", 80, "#fff", sw=15, scale=pop(t, 0, .5))
    out += pill(540, 330, 600, "AVCOAT · ESCUDO DE ORION", "#4A2F1B", "#FFB347", "#FFD9A8", 24, pop(t, d * .1, .4))
    if t > d * .5 and t < d * .72:
        out += pill(540, 1215, 920, "NO TODAS LAS NAVES USAN ABLACIÓN", "#0B1030", "#FFE14D", "#FFE14D", 32, pop(t, d * .5, .4))
    if t >= d * .72 and t < d * .88:
        out += pill(540, 1215, 920, "HAY OTROS SISTEMAS DE PROTECCIÓN", "#0B1030", "#7CD3FF", "#CFF1FF", 32, pop(t, d * .72, .4))
    if t >= d * .88:
        out += pill(540, 1215, 920, "EL ESCUDO SE SACRIFICA PARA PROTEGER", "#4A1E05", "#FF8A3D", "#FFD9A8", 30, pop(t, d * .88, .4))
    return out


# ------------------------------------------------------------------ 5. aterrizaje
@scene
def scene_landing(t, d):
    alt = ease_in_out(prog(t, 0, d * .92))
    out = '<rect width="1080" height="1920" fill="url(#space)"/>'
    out += f'<rect width="1080" height="1920" fill="url(#skyHi)" opacity="{smooth(prog(t, 0, d * .5)):.2f}"/>'
    for i, (x0, y0, sc) in enumerate([(120, 1500, 1.4), (800, 1900, 1.2), (480, 1200, 1.0), (950, 1500, 1.3)]):       # nubes que suben (se desciende)
        y = (y0 + 600 * t * (1.2 - .8 * alt) * -1 * .6) % 2300 - 200
        out += f'<g transform="translate({x0},{y:.0f}) scale({sc})" fill="#fff" opacity="{.8*smooth(prog(t,d*.15,d*.5)):.2f}"><ellipse rx="130" ry="40"/><circle cx="-45" cy="-30" r="45"/><circle cx="25" cy="-44" r="56"/></g>'
    cy = lerp(560, 860, alt)
    # mar
    sea = 1180
    out += oc.sea_back(t, sea, 8) if alt > .35 else ""
    drogue = smooth(prog(t, d * .3, d * .4)); main = smooth(prog(t, d * .52, d * .64))
    cxp = 540 + 14 * math.sin(t * 1.2)
    # paracaídas principales y de arrastre
    if main > .01:
        for (dx, col) in ((-210, "#FF7A1A"), (0, "#FFFFFF"), (210, "#FF7A1A")):
            out += f'<line x1="{cxp:.0f}" y1="{cy-60:.0f}" x2="{cxp+dx*main*.9:.0f}" y2="{cy-300*main-110:.0f}" stroke="#E8EEF8" stroke-width="3"/>'
            out += cp.parachute(cxp + dx * main, cy - 300 * main - 110, 150, 90, t, col, main, 14)
    elif drogue > .01:
        for dx in (-70, 70):
            out += f'<line x1="{cxp:.0f}" y1="{cy-60:.0f}" x2="{cxp+dx:.0f}" y2="{cy-210*drogue:.0f}" stroke="#E8EEF8" stroke-width="3"/>'
            out += cp.parachute(cxp + dx, cy - 210 * drogue, 52, 36, t, "#FF7A1A", drogue, 8)
    heat = max(0.0, 1 - prog(t, 0, d * .22))
    phi = 90 if main < .5 else 90
    tilt = 0 if main < .01 else 0
    out += cp.capsule(cxp, cy, 1.25, 90, t, plasma=.55 * heat, glow=.4 * heat) if heat > 0 or True else ""
    # splash final
    sp = prog(t, d * .9, d)
    if sp > 0:
        out += f'<ellipse cx="{cxp:.0f}" cy="{sea+30}" rx="{60+260*sp:.0f}" ry="{14+30*sp:.0f}" fill="none" stroke="#fff" stroke-width="{max(1,10-8*sp):.1f}" opacity="{1-sp:.2f}"/>'
    # barra de velocidad
    v = 1 - ease_out(prog(t, d * .05, d * .75)) * .93
    out += f'<rect x="90" y="1215" width="900" height="26" rx="13" fill="#1A1F44" stroke="#9FB4FF" stroke-width="4"/><rect x="94" y="1219" width="{892*v:.0f}" height="18" rx="9" fill="{"#FF8A3D" if v>.5 else "#FFE14D" if v>.25 else "#7CF0B3"}"/>'
    out += text(540, 1190, "VELOCIDAD", 28, "#CFE0FF", sw=7)
    out += text(540, 190, "¿CÓMO ATERRIZA?", 68, "#fff", sw=14, scale=pop(t, 0, .5))
    if t < d * .3:
        out += pill(540, 300, 780, "FRENA CON LA ATMÓSFERA", "#10305F", "#7CD3FF", "#CFF1FF", 32, pop(t, .3, .4))
    elif t < d * .88:
        out += pill(540, 300, 780, "SE ABREN LOS PARACAÍDAS", "#4A2F1B", "#FF7A1A", "#FFD9A8", 32, pop(t, d * .3, .4))
    else:
        out += pill(540, 300, 780, "AMERIZAJE EN EL OCÉANO", "#0F3F2A", "#35E08A", "#CFFFE5", 32, pop(t, d * .88, .4))
    return out


# ------------------------------------------------------------------ 6. cohetes: etapas y propulsores
@scene
def scene_rockets(t, d):
    split = d * .5
    out = ""
    if t < split + .4:
        a = 1 - prog(t, split, split + .4)
        alt = prog(t, 0, split)
        g = '<rect width="1080" height="1920" fill="url(#skyHi)"/>' + f'<rect width="1080" height="1920" fill="url(#space)" opacity="{smooth(prog(t, split*.4, split)):.2f}"/>'
        for i, (x0, y0, sc) in enumerate([(150, 300, 1.3), (850, 700, 1.1), (500, 1000, 1.0), (950, 1300, 1.2)]):
            y = (y0 + 1100 * t * .5) % 2000 - 100
            g += f'<g transform="translate({x0},{y:.0f}) scale({sc})" fill="#fff" opacity="{.85*(1-smooth(alt)):.2f}"><ellipse rx="130" ry="40"/><circle cx="-45" cy="-30" r="45"/><circle cx="25" cy="-44" r="56"/></g>'
        tsep = d * .26
        if t < tsep:
            g += cp.rocket(540, 1150, 1.2, t, 1.0)
        else:
            u = t - tsep
            g += cp.rocket(540 - 40 * u, 1150 + 330 * u * u + 100 * u, 1.2, t, 0.0, stage1=True, stage2=False, rot=-14 * u * 3)
            g += cp.rocket(540, 1150 - 60 * u, 1.2, t, .5, stage1=False, stage2=True)
            if u < .4:
                g += f'<circle cx="540" cy="{1150-300*1.2:.0f}" r="{40+200*u:.0f}" fill="none" stroke="#fff" stroke-width="{12*(1-u*2.5):.1f}" opacity="{1-u*2.5:.2f}"/>'
        out += f'<g opacity="{a:.2f}">{g}</g>'
        out += pill(540, 250, 900, "LOS COHETES SUELTAN ETAPAS", "#10305F", "#7CD3FF", "#CFF1FF", 34, pop(t, .15, .4)) if t < split else ""
        if t > tsep + .8 and t < split:
            out += pill(540, 1180, 640, "LA CÁPSULA SIGUE AL ESPACIO", "#0B1030", "#FFE14D", "#FFE14D", 28, pop(t, tsep + .8, .4))
    if t > split:
        b = prog(t, split, split + .5)
        u = prog(t, split, d * .95)
        g = '<rect x="0" y="0" width="540" height="1920" fill="url(#skyHi)"/><rect x="540" y="0" width="540" height="1920" fill="url(#space)"/>'
        g += ea.stars(t, 25).replace('<circle', '<circle')
        g += '<rect x="0" y="1090" width="540" height="900" fill="#4A5568"/><rect x="170" y="1086" width="200" height="14" fill="#AEB8CC"/>'
        # propulsor: desciende, despliega patas, aterriza
        by = lerp(380, 1086, ease_in_out(prog(u, 0, .82)))
        legs = smooth(prog(u, .55, .75))
        flame = 1.0 if u < .8 else max(0, 1 - (u - .8) * 8)
        g += cp.booster(270, by, .85, t, legs, flame)
        if u > .8:
            ph = (u - .8) / .2
            for i in range(8):
                g += f'<circle cx="{270 + (i-4)*34*ph:.0f}" cy="{1080 - 10*ph:.0f}" r="{12+14*ph:.0f}" fill="#E8D8B0" opacity="{.6*(1-ph):.2f}"/>'
        # cápsula en reentrada (derecha)
        g += '<g clip-path="url(#rightHalf)">' + limb(t, 1000, 1) + cp.capsule(820 - 70 * math.sin(u * 2), 560 + 260 * u, .55, 125, t, 1.0) + '</g>'
        g += '<defs><clipPath id="rightHalf"><rect x="540" y="0" width="540" height="1920"/></clipPath></defs>'
        g += '<line x1="540" y1="0" x2="540" y2="1920" stroke="#fff" stroke-width="5" opacity=".6"/>'
        out += f'<g opacity="{b:.2f}">{g}</g>'
        out += text(270, 1215, "ALGUNOS PROPULSORES", 26, "#fff", sw=7) + text(270, 1250, "REGRESAN Y ATERRIZAN", 26, "#7CF0B3", sw=7)
        out += text(810, 1215, "LA CÁPSULA HACE", 26, "#fff", sw=7) + text(810, 1250, "UNA REENTRADA", 26, "#FF8A3D", sw=7)
        out += text(540, 190, "NO ES LO MISMO", 70, "#fff", sw=14, scale=pop(t, split, .5))
    return out


# ------------------------------------------------------------------ 7. cierre + marca
@scene
def scene_close(t, d):
    sw = d * .5
    out = ""
    if t < sw + .6:
        a = 1 - prog(t, sw, sw + .6)
        y0 = 1000
        g = '<rect width="1080" height="1920" fill="url(#skySunset)"/><circle cx="780" cy="520" r="240" fill="url(#sun)"/><circle cx="780" cy="520" r="52" fill="#FFF3B0"/>'
        g += oc.sea_back(t, y0, 8)
        bob = oc.wave_y(540, t, y0, 8) - y0
        # cápsula flotando con bolsas de flotación
        g += f'<g transform="translate(540,{y0-60+bob:.0f}) rotate({4*math.sin(t*1.3):.1f}) scale(1.0)">'
        g += cp.capsule_body(0, t)
        for (bx, by) in ((-90, 40), (90, 40), (-60, 62), (60, 62)):
            g += f'<ellipse cx="{bx}" cy="{by}" rx="32" ry="24" fill="#FF7A1A" stroke="#7A2A12" stroke-width="3"/>'
        g += '</g>'
        g += oc.sea_front(t, y0, 8, alpha=.5)
        # helicóptero de recuperación
        hx = lerp(150, 380, ease_out(prog(t, 0, sw)))
        g += f'<g transform="translate({hx:.0f},{520+10*math.sin(t*2):.0f}) scale(.5)">{hl.heli_side(t)}</g>'
        # lancha de recuperación
        bx = lerp(1250, 800, ease_out(prog(t, 0, sw)))
        g += f'<g transform="translate({bx:.0f},{y0+oc.wave_y(bx,t,y0,8)-y0-14:.0f})"><path d="M-110,0 L110,0 Q96,34 60,34 L-80,34 Q-110,20 -110,0 Z" fill="#E4572E" stroke="#7A2A12" stroke-width="4"/><rect x="-40" y="-36" width="80" height="36" rx="8" fill="#F4F6FA" stroke="#5B6578" stroke-width="3"/></g>'
        out += f'<g opacity="{a:.2f}">{g}</g>'
        out += text(540, 190, "CÁPSULA RECUPERADA", 70, "#fff", sw=15, scale=pop(t, 0, .5)) if t < sw else ""
    if t > sw:
        k2 = pop(t, sw + .2, .7)
        sp = '<rect width="1080" height="1920" fill="url(#space)"/>' + ea.stars(t, 70)
        ey = lerp(780, 400, smooth(prog(t, sw + .3, sw + 1.5))); R = lerp(300, 150, smooth(prog(t, sw + .3, sw + 1.5)))
        out += f'<g opacity="{prog(t, sw, sw + .6):.2f}">' + sp + ea.earth(540, ey, R, 30 + 20 * t, view_tilt=15) + '</g>'
        out += logo(540, 800, k2 * 1.5, t, min(1, k2))
        out += text(540, 1235, "INGENIERÍA · FÍSICA · TECNOLOGÍA", 32, "#CFE0FF", sw=8, opacity=prog(t, sw + 1.4, sw + 2.0))
    return out


SFX = {
    "hook": [("rumble", lambda d: 0, lambda d: 1.8, 1.0), ("pop", lambda d: .05), ("pop", lambda d: d * .66)],
    "heat": [("pop", lambda d: d * .25), ("pop", lambda d: d * .45), ("pop", lambda d: d * .68)],
    "shield": [("pop", lambda d: .2), ("click", lambda d: d * .3), ("pop", lambda d: d * .8)],
    "ablation": [("pop", lambda d: .05), ("pop", lambda d: d * .5), ("pop", lambda d: d * .88)],
    "landing": [("pop", lambda d: d * .3), ("pop", lambda d: d * .52), ("swell", lambda d: d * .88, lambda d: 1.8, 1.0), ("pop", lambda d: d * .9)],
    "rockets": [("pop", lambda d: .15), ("boom", lambda d: d * .26), ("pop", lambda d: d * .5)],
    "close": [("swell", lambda d: .2, lambda d: 1.8, 1.0), ("shimmer", lambda d: d * .55), ("ding", lambda d: d * .6)],
}
