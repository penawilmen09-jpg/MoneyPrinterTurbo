"""Video 3: ¿Cómo vuelan los helicópteros si no tienen alas?"""
import math
import random
from .core import W, H, n, clamp, lerp, prog, smooth, ease_out, ease_in_out, ease_out_back
from .svgkit import layer, cam_at, text
from .art import world as wd
from .art import ocean as oc
from .art import heli as hl
from .art import diagram as dg
from .art.pigeon import pigeon

SCENES = {}


def scene(fn):
    SCENES[fn.__name__.replace("scene_", "")] = fn
    return fn


def pop(t, start, dur=.5):
    return max(ease_out_back(prog(t, start, start + dur)), .001)


def hg(x, y, s, rot, body, op=1.0):
    return f'<g transform="translate({x:.1f},{y:.1f}) rotate({rot:.2f}) scale({s})" opacity="{op:.2f}">{body}</g>'


def sky(t, kind="skyHi", sun=True, sun_xy=(850, 300)):
    return '<rect x="-300" y="-300" width="1700" height="2600" fill="url(#%s)"/>' % kind + \
        (f'<circle cx="{sun_xy[0]}" cy="{sun_xy[1]}" r="240" fill="url(#sun)"/><circle cx="{sun_xy[0]}" cy="{sun_xy[1]}" r="56" fill="#FFF3B0"/>' if sun else "")


def cloud(x, y, sc=1.0, op=.9):
    return (f'<g transform="translate({x:.0f},{y:.0f}) scale({sc})" fill="#fff" opacity="{op}">'
            '<ellipse cx="0" cy="0" rx="130" ry="40"/><circle cx="-45" cy="-30" r="45"/><circle cx="25" cy="-44" r="56"/><circle cx="80" cy="-14" r="38"/></g>')


def clouds(t, speed, items, direction=-1, span=1700):
    out = ""
    for (x0, y, sc, mul) in items:
        x = (x0 + direction * speed * mul * t) % span - 300
        out += cloud(x, y, sc)
    return out


CL = [(100, 300, 1.4, .6), (700, 520, 1.0, .9), (950, 200, .9, .7), (350, 760, .8, 1.2), (1200, 900, 1.1, 1.0)]


def streaks(t, speed, n_=10, direction=-1, op=.45, y0=250, y1=1250, seed=5):
    rnd = random.Random(seed); out = ""
    for i in range(n_):
        y = rnd.uniform(y0, y1); L = rnd.uniform(120, 300); sp = speed * rnd.uniform(.7, 1.3)
        x = (rnd.uniform(0, 1500) + direction * sp * t) % 1500 - 200
        out += f'<line x1="{x:.0f}" y1="{y:.0f}" x2="{x+L:.0f}" y2="{y:.0f}" stroke="#fff" stroke-width="5" stroke-linecap="round" opacity="{op}"/>'
    return out


def fly(t, a=1.0):
    return 14 * a * math.sin(t * 1.7), 10 * a * math.sin(t * 2.3 + 1), 2.2 * a * math.sin(t * 1.3)


def pill(x, y, w, label, fill="#1B1B2F", stroke="#FFE14D", color="#FFE14D", size=38, s=1.0):
    return (f'<g transform="translate({x},{y}) scale({s})"><rect x="{-w/2:.0f}" y="-36" width="{w}" height="72" rx="36" fill="{fill}" stroke="{stroke}" stroke-width="5"/>'
            + text(0, size * .35, label, size, color) + '</g>')


def title(t, lines, y=205, step=92, size=72, start=.05):
    out = ""
    for i, (s_, c) in enumerate(lines):
        k = pop(t, start + i * .14)
        out += text(540, y + i * step, s_, size, c, sw=14, scale=k, opacity=min(1, k * 3))
    return out


# ------------------------------------------------------------------ 1. gancho
@scene
def scene_hook(t, d):
    dx, dy, rot = fly(t)
    hx, hy = 560 + dx, 800 + dy
    k = ease_in_out(prog(t, .2, d * .88))
    z = 1.0 + 1.9 * k
    cam = cam_at(z, lerp(540, hx, k), lerp(960, hy - 40, k))
    out = layer(sky(t), cam, .12) + layer(clouds(t, 140, CL), cam, .55)
    main = streaks(t, 900, 12) + hg(hx, hy, 1.0, rot + 4, hl.heli_side(t))
    out += layer(main, cam)
    for i, (s_, c) in enumerate([("¿CÓMO VUELAN LOS", "#fff"), ("HELICÓPTEROS SI NO", "#fff"), ("TIENEN ALAS?", "#FFE14D")]):
        kk = pop(t, .05 + i * .12) * (1 + .03 * math.sin(t * 6) * (t > 1))
        out += text(540, 200 + i * 92, s_, 70, c, sw=14, scale=kk, opacity=min(1, kk * 3))
    return out


# ------------------------------------------------------------------ 2. ciudad
@scene
def scene_city(t, d):
    dx, dy, rot = fly(t, 1.2)
    out = sky(t, "skyDusk", sun_xy=(300, 520)) + clouds(t, 25, CL[:3])
    for (col, base, spd, seed, lit) in (("#6B6FB5", 1060, 28, 3, .3), ("#4C5399", 1160, 70, 5, .4), ("#2F3573", 1290, 150, 9, .5)):
        off = (spd * t) % 1480
        for o in (-off, -off + 1480):
            out += f'<g transform="translate({o:.0f},0)">{wd.city(seed, base, col, "#FFE9A0", lit)}</g>'
    out += '<rect x="-20" y="1330" width="1120" height="600" fill="#2B2F4A"/>'
    for i in range(6):                                  # tráfico en la avenida
        x = (i * 230 + 260 * t) % 1400 - 150
        out += (f'<rect x="{x:.0f}" y="1390" width="110" height="38" rx="14" fill="{["#F3A712","#4C6EF5","#E4572E"][i%3]}"/>'
                f'<rect x="{x+22:.0f}" y="1372" width="60" height="26" rx="10" fill="#CFE3FF"/><circle cx="{x+24:.0f}" cy="1430" r="11" fill="#111"/><circle cx="{x+86:.0f}" cy="1430" r="11" fill="#111"/>')
    out += streaks(t, 500, 8, op=.25, y0=300, y1=1000, seed=8)
    out += hg(540 + dx, 700 + dy, .82, rot + 5, hl.heli_side(t))
    # cameo de la paloma del video 1
    px = (1250 - 170 * (t % 7)) 
    out += pigeon(px, 1050 + 22 * math.sin(t * 3), .6, flip=True, t=t, fly=True, wing=25 + 45 * math.sin(t * 22), bob=False)
    out += text(540, 250, "¿ALAS?", 100, "#fff", sw=16, scale=pop(t, .6, .5) * (1 - prog(t, d * .52, d * .52 + .2)) + .001)
    if t > d * .55:
        out += text(540, 250, "¡SÍ TIENEN ALAS!", 76, "#FFE14D", sw=14, scale=pop(t, d * .55, .5))
    return out


# ------------------------------------------------------------- 3. aspas = alas
@scene
def scene_rotor(t, d):
    k = ease_in_out(t / d)
    cam = cam_at(lerp(1.0, 1.25, k), 540, 760)
    out = layer(sky(t, "skyHi", sun=False), cam, .12) + layer(clouds(t, 60, CL), cam, .5)
    cx, cy, R, kk = 540, 760, 440, .34
    ang = hl.rotor_ang(t)
    # aire que fluye sobre las aspas aunque el helicóptero esté quieto
    main = ""
    for i in range(7):
        a = math.radians(ang * .9 + i * 51)
        main += (f'<ellipse cx="{cx}" cy="{cy}" rx="{R*(.35+.09*i)}" ry="{R*kk*(.35+.09*i)}" fill="none" stroke="#fff" stroke-width="4" '
                 f'stroke-dasharray="40 70" stroke-dashoffset="{-(t*260 + i*30):.0f}" opacity=".5"/>')
    # fuselaje (techo) y mástil
    main += ('<path d="M230,1230 C230,1030 380,940 540,940 C700,940 850,1030 850,1230 Z" fill="url(#heliRed)" stroke="#7A1A12" stroke-width="5"/>'
             '<rect x="515" y="800" width="50" height="170" fill="#3A4256"/><ellipse cx="540" cy="975" rx="180" ry="46" fill="#B8C0CE" stroke="#5B6578" stroke-width="4"/>')
    main += hl.blades(cx, cy, R, kk, ang, nb=4, blur=3)
    # aspa resaltada
    a = math.radians(ang)
    tx, ty = cx + R * math.cos(a), cy + R * kk * math.sin(a)
    gl = .5 + .5 * math.sin(t * 6)
    main += f'<circle cx="{tx:.0f}" cy="{ty:.0f}" r="{34+10*gl:.0f}" fill="url(#glowY)"/>'
    out += layer(main, cam)
    # avión: ala = aspa
    px = lerp(-250, 1350, prog(t, .5, d * .9))
    plane = ('<g transform="translate(%d,%d) scale(.7)">' % (px, 450 + 20 * math.sin(t * 2)) +
             '<ellipse cx="0" cy="0" rx="150" ry="26" fill="#EAF0F8" stroke="#5B6578" stroke-width="4"/>'
             '<polygon points="-30,0 -110,-70 -80,-70 40,0" fill="#EAF0F8" stroke="#5B6578" stroke-width="4"/>'
             '<polygon points="-30,0 -80,60 -110,60 -2,0" fill="#EAF0F8" stroke="#5B6578" stroke-width="4"/>'
             '<polygon points="-128,-4 -150,-50 -132,-50 -100,-4" fill="#E4572E"/>'
             '<polygon points="-20,-4 -95,-76 -78,-76 20,-4" fill="#FFD43B" opacity=".9"/></g>')
    out += plane
    out += title(t, [("LAS ASPAS SON", "#fff"), ("ALAS QUE GIRAN", "#FFE14D")], y=200, size=72)
    if t > d * .55:
        out += text(540, 1230, "¡AUNQUE ESTÉ QUIETO!", 52, "#fff", sw=12, scale=pop(t, d * .55, .5))
    return out


# -------------------------------------------------- 4. aspa de perfil: desvía el aire
def _stream_y(x, y0):
    up = -22 * math.exp(-((x - 300) / 170) ** 2)
    dn = 150 * smooth(((-250) - x) / 420)
    return y0 + up + dn * (1 if y0 > -300 else 1)


@scene
def scene_deflect(t, d):
    out = '<rect width="1080" height="1920" fill="url(#blueprint)"/>' + dg.grid(t)
    cx, cy = 560, 760
    alpha = lerp(2, 13, ease_out(prog(t, .5, 1.8)))
    g = ""
    for i, y0 in enumerate(range(-250, 251, 55)):
        pts = " ".join(f"{x},{_stream_y(x, y0):.1f}" for x in range(520, -541, -20))
        g += f'<polyline points="{pts}" fill="none" stroke="#7CD3FF" stroke-width="3" opacity=".35"/>'
        for j in range(4):
            xx = 520 - ((t * 330 + j * 270 + i * 53) % 1080)
            g += f'<circle cx="{xx:.0f}" cy="{_stream_y(xx, y0):.1f}" r="7" fill="#fff" opacity=".9"/>'
    af = "M260,0 C240,-40 120,-70 -20,-55 C -140,-40 -230,-10 -260,6 C -200,18 -80,30 20,34 C 140,38 235,28 260,0 Z"
    g += (f'<g transform="rotate({-alpha:.1f})"><path d="{af}" fill="#2B3347" stroke="#fff" stroke-width="6"/>'
          '<path d="M-250,4 L255,0" stroke="#FFD43B" stroke-width="3" stroke-dasharray="12 10"/></g>')
    out += f'<g transform="translate({cx},{cy}) scale(1.0)">{g}</g>'
    out += title(t, [("EL ASPA EMPUJA", "#fff"), ("EL AIRE HACIA ABAJO", "#FFE14D")], y=190, size=62)
    # el aspa avanza hacia la derecha; el aire (relativo) va a la izquierda
    out += hl.arrow(700, 540, 930, 540, "#FFD43B", 14, 34) + text(815, 500, "ASPA", 34, "#FFD43B", sw=0)
    out += hl.arrow(930, 640, 690, 640, "#7CD3FF", 10, 28) + text(815, 612, "AIRE", 34, "#7CD3FF", sw=0)
    if t > d * .3:
        a = prog(t, d * .3, d * .3 + .5)
        out += f'<g opacity="{a:.2f}">{text(560, 905, "ASPA INCLINADA", 38, "#FFD43B", sw=0)}</g>'
    if t > d * .45:
        a = prog(t, d * .45, d * .45 + .5)
        out += hl.arrow(150, 860, 150, 1090 * .9 + 100 * math.sin(t * 5) * 0, "#7CF0B3", 22, 52).replace('opacity', 'o') if False else ""
        out += f'<g opacity="{a:.2f}">' + hl.arrow(120, 900, 120, 1130, "#7CF0B3", 22, 52) + text(300, 1190, "AIRE HACIA ABAJO", 38, "#7CF0B3", anchor="middle", sw=0) + '</g>'
    return out


# ----------------------------------------------------- 5. fuerza que eleva
@scene
def scene_lift(t, d):
    gy = 1180
    dx, dy, rot = fly(t, .4)
    out = sky(t, "skyHi", sun=False) + clouds(t, 30, CL[:3])
    out += ('<path d="M-100,1130 Q250,1040 520,1120 T1200,1090 L1200,1930 L-100,1930 Z" fill="#6DBE7B"/>'
            f'<rect x="-100" y="{gy}" width="1300" height="760" fill="#4FA36A"/>')
    for x in (140, 900, 1020):
        out += f'<rect x="{x-10}" y="{gy-90}" width="20" height="100" fill="#6B4423"/><circle cx="{x}" cy="{gy-130}" r="62" fill="#2F8F57"/>'
    hx, hy = 540 + dx, 610 + dy
    out += hl.downwash(t, hx, hy + 20, 300, gy, 26, 620)
    for i in range(10):                                 # polvo radial
        ph = (t * .9 + i * .1) % 1
        side = 1 if i % 2 else -1
        out += f'<ellipse cx="{hx + side*(120+ph*480):.0f}" cy="{gy+10-ph*20:.0f}" rx="{40+ph*50:.0f}" ry="{14+ph*10:.0f}" fill="#E8D8B0" opacity="{.6*(1-ph):.2f}"/>'
    out += hg(hx, hy, .72, rot, hl.heli_side(t))
    a = prog(t, 1.0, 1.6)
    out += (hl.arrow(hx + 40, hy - 40, hx + 40, hy - 40 - 210 * a, "#35E08A", 20, 46) + text(hx + 40, hy - 285 - 210 * a * 0, "EMPUJE", 40, "#7CF0B3", sw=9, opacity=a)
            if a > .02 else "")
    out += (hl.arrow(hx - 120, hy + 170, hx - 120, hy + 170 + 210 * a, "#FF4D6D", 20, 46) + text(hx - 120, hy + 440, "PESO", 40, "#FF8FA3", sw=9, opacity=a)) if a > .02 else ""
    out += title(t, [("NEWTON EN ACCIÓN", "#fff")], y=200, size=70)
    if t > d * .3:
        out += pill(540, 1120, 900, "ACCIÓN: aire hacia abajo", "#10305F", "#7CD3FF", "#CFF1FF", 38, pop(t, d * .3, .4))
    if t > d * .55:
        out += pill(540, 1210, 900, "REACCIÓN: helicóptero hacia arriba", "#0F3F2A", "#35E08A", "#CFFFE5", 36, pop(t, d * .55, .4))
    return out


# ------------------------------------------------------------- 6. suspendido
@scene
def scene_hover(t, d):
    split = d * .55
    up = ease_in_out(prog(t, split + .3, d * .95))
    dx, dy, rot = fly(t, .5 if t < split else .3)
    gy_off = 330 * up                                    # el suelo se aleja al subir
    out = sky(t, "skyHi", sun=False)
    out += f'<g transform="translate(0,{gy_off*.35:.0f})">{clouds(t, 20, CL)}</g>'
    out += f'<g transform="translate(0,{gy_off*.7:.0f})"><path d="M-100,1130 Q200,1010 450,1100 T1000,1070 T1300,1100 L1300,2200 L-100,2200 Z" fill="#7BC88A"/></g>'
    out += f'<g transform="translate(0,{gy_off:.0f})"><path d="M-100,1210 Q300,1160 560,1215 T1200,1200 L1200,2300 L-100,2300 Z" fill="#4FA36A"/>'
    for x in (90, 300, 820, 1000):
        out += f'<rect x="{x-9}" y="1180" width="18" height="90" fill="#6B4423"/><circle cx="{x}" cy="1140" r="56" fill="#2F8F57"/>'
    out += '</g>'
    hy = 640 - 40 * up + dy
    out += hg(540 + dx, hy, .7, rot, hl.heli_side(t))
    # flechas: iguales en suspensión; el empuje gana al subir
    L_w = 190
    L_u = 190 + 70 * ease_in_out(prog(t, split, split + .5)) + 0 * up
    out += hl.arrow(600, hy - 30, 600, hy - 30 - L_u, "#35E08A", 20, 46) + text(600, hy - 60 - L_u, "EMPUJE", 38, "#7CF0B3", sw=9)
    out += hl.arrow(460, hy + 150, 460, hy + 150 + L_w, "#FF4D6D", 20, 46) + text(460, hy + 150 + L_w + 52, "PESO", 38, "#FF8FA3", sw=9)
    if t < split:
        out += text(540, 200, "SUSPENDIDO", 78, "#fff", sw=14, scale=pop(t, 0, .5))
        a = pop(t, 1.0, .5)
        out += pill(540, 1330 - 90, 520, "EMPUJE = PESO", "#0F3F2A", "#35E08A", "#CFFFE5", 44, a)
        out += text(540, 290, "sin subir ni bajar", 40, "#fff", sw=9, opacity=prog(t, 1.2, 1.7))
    else:
        out += text(540, 200, "¿Y PARA SUBIR?", 74, "#FFE14D", sw=14, scale=pop(t, split, .5))
        out += pill(540, 1330 - 90, 880, "MÁS INCLINACIÓN DE LAS ASPAS", "#3A2A0A", "#FFE14D", "#FFE14D", 36, pop(t, split + .3, .4))
    # altímetro
    out += ('<rect x="40" y="520" width="70" height="520" rx="26" fill="#0F1630" stroke="#fff" stroke-width="5" opacity=".9"/>'
            f'<circle cx="75" cy="{1000 - 400*(up*.35 + .0) - 40 + 40:.0f}" r="22" fill="#FFE14D"/>')
    out += text(75, 490, "ALTURA", 26, "#fff", sw=6)
    return out


# ------------------------------------------------------- 7. inclinar el disco
@scene
def scene_tilt(t, d):
    p1, p2 = d * .36, d * .66
    out = sky(t, "skyHi", sun=False)
    if t < p1:
        k = prog(t, .3, 1.2); tilt, vel, ph = 9 * k, 1, 0
    elif t < p2:
        k = prog(t, p1, p1 + .8); tilt, vel, ph = lerp(9, -9, ease_in_out(k)), -1, 1
    else:
        k = prog(t, p2, p2 + .8); tilt, vel, ph = 9 * math.sin(t * 1.4) * 0 + lerp(-9, 9, ease_in_out(k)) if False else (-9 if t < p2 + 1.8 else 9), 1, 2
    scroll = {0: -1, 1: 1, 2: -1}[ph]
    out += clouds(t, 160 * (1 if ph != 2 else .0 + 1), CL, direction=-1 if ph != 1 else 1) if ph != 2 else clouds(t, 160, CL, direction=-1 if t < p2 + 1.8 else 1)
    out += streaks(t, 650, 10, direction=-1 if ph != 1 else 1, op=.4, y0=300, y1=1100)
    dx, dy, rot = fly(t, .6)
    if ph in (0, 1):
        body = hl.heli_side(t, tilt_disc=tilt)
        out += hg(540 + dx, 700 + dy, .74, tilt * .55 + rot * .3, body)
        # vector de fuerza perpendicular al disco: componente vertical (verde) + horizontal (naranja)
        a = math.radians(tilt)
        Fx, Fy = 250 * math.sin(a) * -1 * -1, -250 * math.cos(a)
        hxp, hyp = 540 + dx, 700 + dy - 40
        out += hl.arrow(hxp, hyp, hxp + Fx, hyp + Fy, "#35E08A", 16, 40)
        out += hl.arrow(hxp, hyp, hxp + Fx * 2.6, hyp, "#FFA94D", 16, 40) if abs(Fx) > 20 else ""
        lab = "ADELANTE" if ph == 0 else "ATRÁS"
    else:
        sx = 540 + 150 * math.sin(clamp((t - p2) / (d - p2)) * math.pi * 2.0)
        tl = -9 if t < p2 + 1.8 else 9
        out += hg(sx + dx * .5, 700 + dy, .74, tl * .4, hl.heli_front(t, tilt_disc=tl))
        a = math.radians(tl)
        hxp, hyp = sx, 660
        Fx, Fy = 250 * math.sin(a), -250 * math.cos(a)
        out += hl.arrow(hxp, hyp, hxp + Fx, hyp + Fy, "#35E08A", 16, 40)
        out += hl.arrow(hxp, hyp, hxp + Fx * 2.6, hyp, "#FFA94D", 16, 40)
        lab = "A LOS LADOS"
    out += text(540, 200, "INCLINA EL DISCO", 72, "#fff", sw=14, scale=pop(t, 0, .5))
    out += pill(540, 330, 520, lab, "#3A2A0A", "#FFA94D", "#FFA94D", 46, 1.0)
    out += text(540, 1230, "la fuerza apunta hacia donde se inclina", 34, "#fff", sw=8, opacity=prog(t, 1.0, 1.6))
    return out


# ------------------------------------------------------------- 8. rotor de cola
@scene
def scene_tail(t, d):
    sw = d * .45
    out = ('<rect width="1080" height="1920" fill="#3E7D4F"/>' +
           ''.join(f'<line x1="0" y1="{y}" x2="1080" y2="{y}" stroke="#2F6A40" stroke-width="3"/>' for y in range(0, 1920, 70)) +
           ''.join(f'<line x1="{x}" y1="0" x2="{x}" y2="1920" stroke="#2F6A40" stroke-width="3"/>' for x in range(0, 1080, 70)))
    if t < sw:
        yaw = 155 * (t / sw) ** 2
    else:
        yaw = 155 * math.exp(-(t - sw) * 6) * (1 + 0) + 1.5 * math.sin(t * 2)
    out += f'<g transform="translate(540,790) scale(.95)">{hl.heli_top(t, yaw)}</g>'
    # flecha del rotor (antihorario) y reacción del fuselaje (horario)
    out += (f'<path d="M300,740 A260,260 0 0 0 540,460" fill="none" stroke="#FFD43B" stroke-width="12" stroke-linecap="round" transform="translate(0,0)" opacity=".0"/>')
    out += text(150, 440, "ROTOR", 34, "#FFD43B", sw=8) + f'<path d="M100,520 A60 60 0 1 0 170,460" fill="none" stroke="#FFD43B" stroke-width="10" stroke-linecap="round" transform="rotate(0)"/>'
    if t < sw:
        out += text(540, 200, "SIN ROTOR DE COLA", 66, "#FF8FA3", sw=14, scale=pop(t, 0, .5))
        out += pill(540, 330, 780, "¡EL FUSELAJE GIRA AL REVÉS!", "#4A1020", "#FF4D6D", "#FF8FA3", 38, pop(t, .5, .5))
        out += hl.arrow(880, 600, 900, 880, "#FF4D6D", 16, 40) if False else ""
        out += f'<path d="M880,520 A330,330 0 0 1 930,980" fill="none" stroke="#FF4D6D" stroke-width="14" stroke-linecap="round" opacity="{.5+.5*math.sin(t*6):.2f}"/>'
    else:
        out += text(540, 200, "CON ROTOR DE COLA", 66, "#7CF0B3", sw=14, scale=pop(t, sw, .5))
        out += pill(540, 330, 640, "EMPUJE LATERAL", "#0F3F2A", "#35E08A", "#CFFFE5", 42, pop(t, sw + .4, .5))
        ty = 790 + 326 * .95
        out += hl.arrow(540 + 60, ty, 540 + 60 + 160 * prog(t, sw + .2, sw + .7), ty, "#35E08A", 18, 46)
        out += text(760, ty + 66, "rotor de cola", 34, "#fff", sw=8)
    return out


# -------------------------------------------------------------------- 9. final
@scene
def scene_final(t, d):
    k = ease_in_out(prog(t, 0, d * .8))
    x, y = lerp(380, 800, k), lerp(1080, 560, k)
    s = lerp(1.05, .36, k)
    dx, dy, rot = fly(t, .8)
    out = sky(t, "skySunset", sun_xy=(780, 560)) + clouds(t, 90, CL, direction=-1)
    out += streaks(t, 700, 10, op=.3, y0=300, y1=1300)
    out += hg(x + dx, y + dy, s, -10 * k + rot, hl.heli_side(t, tilt_disc=-4))
    # nubes en primer plano que cruzan (sensación de ascenso entre nubes)
    for i, (cx0, cy0, sc) in enumerate([(100, 1500, 2.6), (900, 1300, 2.2), (500, 1700, 3.0)]):
        cy = (cy0 - 520 * k * (1 + .3 * i)) 
        out += cloud(cx0 - 80 * k, cy, sc, .75)
    fade = prog(t, d * .84, d)
    out += f'<rect width="1080" height="1920" fill="#fff" opacity="{fade*.0:.2f}"/>'
    out += text(540, 250, "ALAS QUE GIRAN", 78, "#fff", sw=15, scale=pop(t, .6, .5))
    out += text(540, 345, "AIRE HACIA ABAJO", 62, "#FFE14D", sw=13, scale=pop(t, 1.0, .5))
    pulse = 1 + .05 * math.sin(t * 8)
    s3 = pop(t, d * .58, .5)
    out += (f'<g transform="translate(540,1130) scale({s3*pulse:.3f})"><rect x="-290" y="-62" width="580" height="124" rx="62" fill="#FF3D6B" stroke="#fff" stroke-width="8"/>'
            + text(0, 22, "¿LO SABÍAS? SÍGUEME", 44, "#fff") + '</g>')
    return out


_R = lambda d: d
SFX = {
    name: [("rotor", lambda d: 0, lambda d: d, .35)] for name in ("hook", "city", "rotor", "lift", "hover", "tilt", "tail", "final")
}
SFX["deflect"] = [("rotor", lambda d: 0, lambda d: d, .18)]
SFX["hook"] += [("pop", lambda d: .05), ("pop", lambda d: .2)]
SFX["city"] += [("pop", lambda d: .6), ("pop", lambda d: d * .55)]
SFX["rotor"] += [("pop", lambda d: .05)]
SFX["deflect"] += [("pop", lambda d: .05), ("click", lambda d: d * .3)]
SFX["lift"] += [("pop", lambda d: d * .3), ("pop", lambda d: d * .55)]
SFX["hover"] += [("pop", lambda d: 1.0), ("pop", lambda d: d * .55)]
SFX["tilt"] += [("pop", lambda d: .05), ("click", lambda d: d * .36), ("click", lambda d: d * .66)]
SFX["tail"] += [("pop", lambda d: .05), ("click", lambda d: d * .45)]
SFX["final"] += [("pop", lambda d: .6), ("ding", lambda d: d * .58)]
