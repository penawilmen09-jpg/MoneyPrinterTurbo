"""Video 5: ¿Por qué los aviones dejan líneas blancas en el cielo? (estelas de condensación)"""
import math
import random
from .core import W, H, n, clamp, lerp, prog, smooth, ease_out, ease_in_out, ease_out_back
from .svgkit import layer, cam_at, text
from .art import world as wd
from .art import plane as pl
from .art import heli as hl
from .art import ocean as oc
from .art.pigeon import pigeon

SCENES = {}


def scene(fn):
    SCENES[fn.__name__.replace("scene_", "")] = fn
    return fn


def pop(t, start, dur=.5):
    return max(ease_out_back(prog(t, start, start + dur)), .001)


def hg(x, y, s, rot, body, op=1.0):
    return f'<g transform="translate({x:.1f},{y:.1f}) rotate({rot:.2f}) scale({s})" opacity="{op:.2f}">{body}</g>'


def pill(x, y, w, label, fill="#10305F", stroke="#7CD3FF", color="#CFF1FF", size=36, s=1.0, op=1.0):
    return (f'<g transform="translate({x},{y}) scale({s})" opacity="{op:.2f}"><rect x="{-w/2:.0f}" y="-36" width="{w}" height="72" rx="36" fill="{fill}" stroke="{stroke}" stroke-width="5"/>'
            + text(0, size * .35, label, size, color) + '</g>')


def sky(kind="skyHi"):
    return '<rect x="-300" y="-300" width="1700" height="2600" fill="url(#%s)"/>' % kind


def cloud(x, y, sc=1.0, op=.92):
    return (f'<g transform="translate({x:.0f},{y:.0f}) scale({sc})" fill="#fff" opacity="{op}">'
            '<ellipse cx="0" cy="0" rx="130" ry="40"/><circle cx="-45" cy="-30" r="45"/><circle cx="25" cy="-44" r="56"/><circle cx="80" cy="-14" r="38"/></g>')


def clouds(t, speed, items, span=1700):
    return "".join(cloud((x0 - speed * mul * t) % span - 300, y, sc) for (x0, y, sc, mul) in items)


CL = [(100, 1000, 1.6, .5), (700, 1200, 1.3, .8), (1000, 900, 1.1, .6), (350, 1350, 1.4, 1.0), (1300, 1100, 1.5, .7)]


def fly(t, a=1.0):
    return 6 * a * math.sin(t * 1.3), 8 * a * math.sin(t * 1.9 + 1), 1.2 * a * math.sin(t * 1.1)


# ------------------------------------------------------------------ 1. gancho
@scene
def scene_hook(t, d):
    dx, dy, rot = fly(t)
    px, py = 640, 760
    z = 1.0 + .25 * ease_in_out(t / d)
    cam = cam_at(z, 560, 800)
    out = layer(sky(), cam, .15) + layer(clouds(t, 160, CL), cam, .5)
    main = pl.trail(px - 250 + dx, py + 20 + dy, t, 420, "young", x_left=-300, seed=3, grow=1.0)
    main += hg(px + dx, py + dy, 1.0, rot - 1, pl.airliner(t))
    out += layer(main, cam)
    for i, (s_, c) in enumerate([("¿POR QUÉ LOS AVIONES", "#fff"), ("DEJAN LÍNEAS BLANCAS", "#fff"), ("EN EL CIELO?", "#FFE14D")]):
        k = pop(t, .05 + i * .12) * (1 + .03 * math.sin(t * 6) * (t > 1))
        out += text(540, 190 + i * 90, s_, 62 if i < 2 else 78, c, sw=14, scale=k, opacity=min(1, k * 3))
    return out


# ------------------------------------------------------------------ 2. crucero
@scene
def scene_cruise(t, d):
    dx, dy, rot = fly(t)
    out = sky() + clouds(t, 90, CL)
    out += '<circle cx="860" cy="330" r="220" fill="url(#sun)"/><circle cx="860" cy="330" r="50" fill="#FFF3B0"/>'
    px, py = 700, 720
    out += pl.trail(px - 250 + dx, py + 20 + dy, t, 330, "persist", x_left=-200, seed=5)
    out += hg(px + dx, py + dy, .95, rot, pl.airliner(t))
    k = pop(t, .8, .5)
    out += (f'<g opacity="{min(1,k):.2f}"><line x1="900" y1="860" x2="900" y2="1090" stroke="#fff" stroke-width="5" stroke-dasharray="12 10"/>'
            '<polygon points="900,1100 886,1070 914,1070" fill="#fff"/>' + pill(850, 1160, 440, "≈ 10 000 m DE ALTURA", "#0B1030", "#FFE14D", "#FFE14D", 32) + '</g>')
    out += text(540, 190, "A GRAN ALTURA", 76, "#fff", sw=14, scale=pop(t, 0, .5))
    out += text(540, 280, "una línea blanca lo sigue", 40, "#fff", sw=9, opacity=prog(t, 1.2, 1.8))
    return out


# ------------------------------------------------------------------ 3. motores
@scene
def scene_engine(t, d):
    k = ease_in_out(t / d)
    cam = cam_at(1.0 + .2 * k, lerp(500, 600, k), 800)
    out = layer('<rect x="-300" y="-300" width="1700" height="2600" fill="url(#skyHi)"/>' + clouds(t, 120, CL), cam, .2)
    cx, cy, S = 320, 780, 1.3
    main = f'<rect x="-100" y="{cy-S*70-210}" width="760" height="150" fill="#E9EEF6" stroke="#5B6578" stroke-width="4"/>'
    main += f'<g transform="translate({cx},{cy}) scale({S})">'
    main += '<rect x="-30" y="-120" width="40" height="60" fill="#9AA6BA"/>' + pl.engine_cutaway(t)
    main += '</g>'
    # chorro de gases calientes (naranja → blanco azulado al enfriarse) con vapor de agua
    rnd = random.Random(8)
    for i in range(70):
        ph = (t * .75 + i * .071) % 1
        x = cx + 228 * S + ph * 560
        spread = 30 * S + ph * 150
        y = cy + (rnd.uniform(-1, 1)) * spread * (.4 + ph)
        r = 7 + 14 * ph
        col = ("#FF7A1A" if ph < .25 else "#FFC88A" if ph < .55 else "#EAF6FF")
        main += f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.0f}" fill="{col}" opacity="{.8*(1-ph*.6):.2f}"/>'
    for i in range(9):
        ph = (t * .5 + i * .113) % 1
        x = cx + 228 * S + 40 + ph * 520
        y = cy + math.sin(i * 2.3) * (40 + ph * 110)
        main += pl.molecule(x, y, 1.1, t * 60 + i * 40, hot=ph < .6)
    out += layer(main, cam)
    out += text(540, 190, "LOS MOTORES", 78, "#fff", sw=14, scale=pop(t, 0, .5))
    out += pill(400, 1010, 560, "GASES MUY CALIENTES", "#4A1E05", "#FF7A1A", "#FFC88A", 32, pop(t, d * .3, .4))
    out += pill(640, 1100, 640, "CON VAPOR DE AGUA (H₂O)", "#10305F", "#7CD3FF", "#CFF1FF", 32, pop(t, d * .55, .4))
    return out


# ------------------------------------------------------------------ 4. aire frío
@scene
def scene_cold(t, d):
    out = sky("skyDark") if False else '<rect width="1080" height="1920" fill="url(#blueprint)"/>'
    out += '<rect width="1080" height="1920" fill="#6FD0FF" opacity=".10"/>'
    rnd = random.Random(4)
    for i in range(60):                                     # copos de escarcha a la deriva
        x = (rnd.uniform(0, 1080) + 30 * t * rnd.uniform(.4, 1)) % 1100 - 10
        y = (rnd.uniform(0, 1500) + 40 * t * rnd.uniform(.4, 1.2)) % 1500 + 150
        out += pl.sparkle(x, y, rnd.choice([6, 9, 12]), t, i)
    # termómetro y altímetro
    k = ease_in_out(prog(t, .6, d * .7))
    alt = 10000 * k
    temp = lerp(15, -50, k)
    tx, ty0, ty1 = 220, 1100, 520
    out += (f'<rect x="{tx-34}" y="{ty1-30}" width="68" height="{ty0-ty1+90}" rx="34" fill="#0B1030" stroke="#fff" stroke-width="6"/>'
            f'<circle cx="{tx}" cy="{ty0+50}" r="52" fill="{"#FF4D6D" if temp>0 else "#4DB8FF"}" stroke="#fff" stroke-width="6"/>')
    h = lerp(ty0 - ty1, 20, k)
    out += f'<rect x="{tx-14}" y="{ty0 - h:.0f}" width="28" height="{h + 40:.0f}" rx="14" fill="{"#FF4D6D" if temp>0 else "#4DB8FF"}"/>'
    out += text(tx, ty1 - 60, "TEMPERATURA", 26, "#CFF1FF", sw=0) + text(tx + 260, ty0 - h + 6, f"{temp:.0f} °C".replace("-", "−"), 58, "#7CD3FF" if temp < 0 else "#FFC88A", sw=10, anchor="middle")
    # altura: el avión sube y el aire se enfría
    ax = 760
    ay = lerp(1040, 560, k)
    out += f'<line x1="{ax}" y1="1160" x2="{ax}" y2="500" stroke="#fff" stroke-width="3" stroke-dasharray="10 12" opacity=".5"/>'
    out += hg(ax, ay, .3, -8, pl.airliner(t))
    out += text(ax, 1130, f"{alt:,.0f} m".replace(",", " "), 46, "#FFE14D", sw=9)
    # corrientes de aire frío (lentas, discretas)
    for i in range(6):
        y = 380 + i * 170
        x = (i * 230 + 60 * t) % 1300 - 150
        out += f'<line x1="{x:.0f}" y1="{y}" x2="{x+160:.0f}" y2="{y}" stroke="#9FE3FF" stroke-width="5" stroke-linecap="round" opacity=".45"/>'
    out += text(540, 190, "AIRE EXTREMADAMENTE FRÍO", 58, "#fff", sw=13, scale=pop(t, 0, .5))
    if t > d * .72:
        out += pill(540, 1285, 720, "UNOS −50 °C A 10 000 m", "#0B1030", "#7CD3FF", "#7CD3FF", 38, pop(t, d * .72, .4))
    return out


# ------------------------------------------------------------------ 5. condensación (microscópico)
@scene
def scene_condense(t, d):
    out = '<rect width="1080" height="1920" fill="url(#blueprint)"/>'
    cx, cy, R = 540, 740, 400
    s1, s2 = d * .30, d * .62
    out += f'<defs><clipPath id="lens"><circle cx="{cx}" cy="{cy}" r="{R}"/></clipPath></defs><circle cx="{cx}" cy="{cy}" r="{R+14}" fill="#7CD3FF" opacity=".25"/>'
    g = f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="#0B1F4A"/>'
    rnd = random.Random(12)
    centers = [(cx + 170 * math.cos(a), cy + 150 * math.sin(a)) for a in [i * 1.05 + .4 for i in range(6)]]
    centers = [(x + 16 * math.sin(t * 1.7 + i * 1.3), y + 16 * math.cos(t * 1.4 + i)) for i, (x, y) in enumerate(centers)]
    kc = ease_in_out(prog(t, s1, s1 + 1.6))
    kf = ease_in_out(prog(t, s2, s2 + 1.4))
    # moléculas de aire frío (azules, pequeñas y lentas) y vapor (rojo caliente → azul al enfriar)
    for i in range(40):
        bx, by = rnd.uniform(cx - R, cx + R), rnd.uniform(cy - R, cy + R)
        sp = 140 if t < s1 else 70
        px = bx + 60 * math.sin(t * (1 + i % 3) * (sp / 90) + i)
        py = by + 60 * math.cos(t * (1.2 + i % 4) * (sp / 90) + i * 2)
        gi = i % 6
        gx, gy = centers[gi]
        px, py = lerp(px, gx + 24 * math.cos(i), kc), lerp(py, gy + 24 * math.sin(i), kc)
        if kc < .95:
            g += pl.molecule(px, py, .9, t * 80 + i * 30, hot=(t < s1))
    for i, (gx, gy) in enumerate(centers):
        if kc > .2:
            r = 62 * kc * (1 - .1 * kf)
            g += (f'<circle cx="{gx:.0f}" cy="{gy:.0f}" r="{r:.0f}" fill="#4DB8FF" opacity="{(1-kf)*.9:.2f}" stroke="#CFF1FF" stroke-width="4"/>'
                  f'<circle cx="{gx-r*.3:.0f}" cy="{gy-r*.3:.0f}" r="{r*.22:.0f}" fill="#fff" opacity="{(1-kf)*.8:.2f}"/>')
        if kf > .05:
            g += pl.crystal(gx, gy, 66 * kf, t * 25 + i * 20, kf)
            g += pl.sparkle(gx + 40, gy - 40, 14, t, i) if kf > .6 else ""
    out += f'<g clip-path="url(#lens)">{g}</g><circle cx="{cx}" cy="{cy}" r="{R}" fill="none" stroke="#fff" stroke-width="8"/>'
    # 3 etapas
    stage = 0 if t < s1 else 1 if t < s2 else 2
    for i, (lab, col) in enumerate((("VAPOR", "#FF7A5C"), ("GOTAS", "#4DB8FF"), ("CRISTALES", "#E8FAFF"))):
        x = 200 + i * 340
        on = i <= stage
        out += pill(x, 1230, 300, f"{i+1}  {lab}", "#0B1030", col if on else "#3B4A7A", col if on else "#7C89B0", 32, 1.0 if on else .95, 1.0 if on else .55)
    out += text(540, 190, "VAPOR → GOTAS → HIELO", 58, "#fff", sw=13, scale=pop(t, 0, .5))
    out += text(540, 1310, "(vista ampliada, esquemática)", 28, "#9FD0FF", sw=0)
    return out


# ------------------------------------------------------------------ 6. línea desde el suelo
@scene
def scene_line(t, d):
    k = prog(t, 0, d * .6)
    out = sky() + clouds(t, 20, [(100, 330, .9, .5), (800, 520, .7, .8), (500, 250, .6, .6)])
    px = lerp(-100, 1000, k); py = lerp(640, 330, k)
    # estela lejana hacia abajo-izquierda
    pts = [(lerp(-100, px, u), lerp(640, py, u)) for u in [i / 90 for i in range(91)]]
    for i, (x, y) in enumerate(pts):
        u = i / 90
        out += f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{5 + 12*(1-u)*k:.1f}" fill="#fff" opacity="{.9 - .2*(1-u):.2f}"/>'
    out += hg(px, py, .2, -17, pl.airliner(t))
    # suelo
    out += ('<path d="M-50,1180 Q200,1090 480,1160 T1150,1120 L1150,1930 L-50,1930 Z" fill="#6DBE7B"/>'
            '<path d="M-50,1300 Q300,1230 700,1290 T1150,1270 L1150,1930 L-50,1930 Z" fill="#4FA36A"/>')
    out += oc.captain(190, 1330, .75, t, "happy", "point")
    out += pigeon(900, 1250, .8, flip=True, t=t, expr="happy")
    # lupa con cristales de hielo
    a = pop(t, d * .45, .6)
    mx, my, mr = 540, 850, 250 * min(a, 1)
    out += (f'<defs><clipPath id="mag"><circle cx="{mx}" cy="{my}" r="{mr:.0f}"/></clipPath></defs>'
            f'<circle cx="{mx}" cy="{my}" r="{mr+10:.0f}" fill="#fff" opacity=".35"/><g clip-path="url(#mag)"><circle cx="{mx}" cy="{my}" r="{mr:.0f}" fill="#BFE3FF"/>')
    rnd = random.Random(2)
    for i in range(14):
        x = mx + rnd.uniform(-1, 1) * mr * .85 + 12 * math.sin(t * 1.3 + i)
        y = my + rnd.uniform(-1, 1) * mr * .85 + 12 * math.cos(t * 1.1 + i)
        out += pl.crystal(x, y, rnd.choice([26, 34, 44]), t * 20 + i * 30)
    out += f'</g><circle cx="{mx}" cy="{my}" r="{mr:.0f}" fill="none" stroke="#fff" stroke-width="8"/>' if a > .05 else '</g>'
    out += text(540, 190, "LA LÍNEA BLANCA", 76, "#fff", sw=14, scale=pop(t, 0, .5))
    if t > d * .55:
        out += pill(540, 1140, 760, "NO ES HUMO: ES HIELO", "#10305F", "#FFE14D", "#FFE14D", 40, pop(t, d * .55, .4))
    return out


# ------------------------------------------------------------------ 7. dos estelas
@scene
def scene_compare(t, d):
    speed = 260
    k = prog(t, .3, d * .92)
    out = '<rect width="1080" height="1920" fill="#0B1F4A"/>'
    for (y0, label, sub, mode, col, hum) in ((190, "AIRE SECO", "la estela desaparece en segundos", "dry", "#FFA94D", .18),
                                               (690, "AIRE MUY HÚMEDO", "la estela persiste y se extiende", "persist", "#7CF0B3", .9)):
        out += f'<g transform="translate(0,{y0})"><rect x="30" y="0" width="1020" height="460" rx="30" fill="url(#skyHi)"/>'
        px = lerp(-120, 1200, k) if True else 0
        out += pl.trail(px - 160, 280, t, 500, mode, x_left=40, seed=7 if mode == "dry" else 9, grow=1.2)
        out += hg(px, 280, .55, 0, pl.airliner(t))
        out += pill(300, 60, 500, label, "#0B1030", col, col, 34)
        out += text(540, 430, sub, 32, "#fff", sw=8, opacity=prog(t, d * .35, d * .35 + .5))
        # medidor de humedad
        out += (f'<rect x="900" y="40" width="40" height="190" rx="14" fill="#0B1030" stroke="#fff" stroke-width="4"/>'
                f'<rect x="906" y="{40+190*(1-hum)+6:.0f}" width="28" height="{190*hum-12:.0f}" rx="8" fill="{col}"/>')
        out += text(920, 262, "humedad", 20, "#fff", sw=0)
        out += '</g>'
    out += text(540, 130, "¿SE QUEDA O DESAPARECE?", 54, "#fff", sw=12, scale=pop(t, 0, .5))
    out += text(540, 1250, "depende de la humedad del aire", 38, "#FFE14D", sw=9, opacity=prog(t, d * .6, d * .6 + .5))
    return out


# ------------------------------------------------------------------ 8. final
@scene
def scene_final(t, d):
    k = ease_in_out(prog(t, 0, d * .9))
    cam = cam_at(lerp(1.4, 1.0, k), 560, 760)
    out = layer(sky("skySunset") + '<circle cx="780" cy="560" r="240" fill="url(#sun)"/>', cam, .15) + layer(clouds(t, 60, [(c[0], c[1] - 300, c[2], c[3]) for c in CL]), cam, .5)
    px = lerp(520, 1000, k); py = lerp(760, 470, k); s = lerp(.9, .35, k)
    main = pl.trail(px - 250 * s, py + 20 * s, t, 330, "persist", x_left=-250, seed=5, grow=1.0 * s + .3)
    main += hg(px, py, s, -6 * k, pl.airliner(t))
    out += layer(main, cam)
    # nubes delante: el avión se aleja entre las nubes
    for i, (cx0, cy0, sc) in enumerate([(150, 1050, 2.4), (850, 1180, 2.0), (500, 1330, 2.8)]):
        out += cloud(cx0 - 70 * k * (1 + i * .2), cy0 - 120 * k, sc, .8)
    lines = [("¡LO QUE PARECE HUMO", "#fff", 52), ("ES, EN REALIDAD,", "#fff", 52), ("UNA NUBE ARTIFICIAL", "#FFE14D", 56), ("DE CRISTALES DE HIELO!", "#FFE14D", 56)]
    for i, (s_, c, sz) in enumerate(lines):
        out += text(540, 190 + i * 76, s_, sz, c, sw=13, scale=pop(t, .6 + i * .45, .5))
    pulse = 1 + .05 * math.sin(t * 8)
    s3 = pop(t, d * .7, .5)
    out += (f'<g transform="translate(540,1130) scale({s3*pulse:.3f})"><rect x="-290" y="-62" width="580" height="124" rx="62" fill="#FF3D6B" stroke="#fff" stroke-width="8"/>'
            + text(0, 22, "¿LO SABÍAS? SÍGUEME", 44, "#fff") + '</g>')
    return out


SFX = {
    "hook": [("pop", lambda d: .05), ("whoosh", lambda d: .2)],
    "cruise": [("pop", lambda d: .8)],
    "engine": [("pop", lambda d: d * .3), ("pop", lambda d: d * .55)],
    "cold": [("pop", lambda d: d * .72)],
    "condense": [("click", lambda d: d * .30), ("ding", lambda d: d * .62)],
    "line": [("pop", lambda d: d * .45), ("pop", lambda d: d * .55)],
    "compare": [("click", lambda d: .3), ("pop", lambda d: d * .6)],
    "final": [("pop", lambda d: .6), ("ding", lambda d: d * .7)],
}
