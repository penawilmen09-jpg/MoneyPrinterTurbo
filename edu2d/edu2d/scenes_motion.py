"""Video 7 · Explora Ciencia 360 — ¿Por qué no sentimos que la Tierra se mueve?"""
import math
import random
from .core import W, H, n, clamp, lerp, prog, smooth, ease_out, ease_in_out, ease_out_back
from .svgkit import layer, cam_at, text
from .art import earth as ea
from .art import plane as pl
from .art import heli as hl
from .scenes_earth import city_side, car, GROUND
from .scenes_moon import logo

SCENES = {}


def scene(fn):
    SCENES[fn.__name__.replace("scene_", "")] = fn
    return fn


def pop(t, start, dur=.5):
    return max(ease_out_back(prog(t, start, start + dur)), .001)


def pill(x, y, w, label, fill="#10305F", stroke="#7CD3FF", color="#CFF1FF", size=34, s=1.0, op=1.0):
    return (f'<g transform="translate({x},{y}) scale({s})" opacity="{op:.2f}"><rect x="{-w/2:.0f}" y="-36" width="{w}" height="72" rx="36" fill="{fill}" stroke="{stroke}" stroke-width="5"/>'
            + text(0, size * .35, label, size, color) + '</g>')


def space(t):
    return '<rect width="1080" height="1920" fill="url(#space)"/>' + ea.stars(t)


def walker(x, y, s, t, col="#E4572E", speed=5.0, flip=False):
    a = math.sin(t * speed) * 30
    bob = abs(math.sin(t * speed)) * 4
    return (f'<g transform="translate({x:.1f},{y:.1f}) scale({-s if flip else s},{s})">'
            f'<g transform="translate(0,{-bob:.1f})">'
            f'<rect x="-9" y="0" width="18" height="86" rx="8" fill="#1F2E42" transform="translate(0,-92) rotate({a:.0f} 0 0)"/>'
            f'<rect x="-9" y="0" width="18" height="86" rx="8" fill="#27374D" transform="translate(0,-92) rotate({-a:.0f} 0 0)"/>'
            f'<ellipse cx="{12*math.sin(math.radians(-a))*0+4}" cy="-4" rx="20" ry="8" fill="#111" opacity="0"/>'
            f'<rect x="-26" y="-176" width="52" height="92" rx="20" fill="{col}"/>'
            f'<rect x="-8" y="0" width="16" height="70" rx="8" fill="#C74422" transform="translate(0,-168) rotate({-a*1.2:.0f})"/>'
            f'<rect x="-8" y="0" width="16" height="70" rx="8" fill="{col}" transform="translate(0,-168) rotate({a*1.2:.0f})"/>'
            '<circle cx="4" cy="-206" r="28" fill="#F2C29B"/><path d="M-24,-212 Q-22,-246 6,-244 Q32,-242 32,-216 Q14,-232 -6,-226 Z" fill="#3A2412"/>'
            '<circle cx="16" cy="-208" r="4" fill="#222"/><path d="M12,-192 Q20,-187 28,-193" fill="none" stroke="#6B2A2A" stroke-width="3" stroke-linecap="round"/>'
            '</g></g>')


# ------------------------------------------------------------------ 1. gancho
@scene
def scene_hook(t, d):
    sw = d * .52
    out = ""
    if t < sw + .4:
        k = ease_in_out(prog(t, 0, sw))
        cam = cam_at(1.0 + 1.5 * k, 540, lerp(900, 700, k))
        a = 1 - prog(t, sw - .1, sw + .4)
        out += f'<g opacity="{a:.2f}">' + layer(space(t), cam, .3) + layer(ea.earth(540, 900, 330, 150 * t, view_tilt=18), cam) + '</g>'
    if t > sw - .1:
        b = prog(t, sw - .1, sw + .4)
        sc = 230 * t
        g = city_side(t, sc, cloud_speed=30)
        g += walker(430, GROUND - 2, 1.6, t)
        out += f'<g opacity="{b:.2f}">{g}</g>'
    if t < sw:
        out += text(540, 200, "¡LA TIERRA GIRA", 76, "#fff", sw=15, scale=pop(t, .05, .5)) + text(540, 295, "A MÁS DE 1 600 km/h!", 62, "#FFE14D", sw=14, scale=pop(t, .2, .5))
    else:
        out += text(540, 200, "¿POR QUÉ NO", 82, "#fff", sw=15, scale=pop(t, sw, .5)) + text(540, 300, "SALIMOS VOLANDO?", 72, "#FFE14D", sw=15, scale=pop(t, sw + .15, .5))
    return out


# ------------------------------------------------------------------ 2. la Tierra gira, tú caminas
@scene
def scene_walk(t, d):
    cx, cy, R = 540, 800, 300
    rot = 30 * t
    out = space(t)
    out += ea.earth(cx, cy, R, rot, view_tilt=0, axis_tilt=0)
    # gente "pegada" a la superficie: se desplaza con ella (equator y latitud 60°)
    for (lat, lam0, label, col, tstart) in ((0, -50, "ECUADOR", "#FF4D6D", .1), (60, -10, "60°", "#FFE14D", .4)):
        phi = math.radians(lam0 + rot * 1.0)
        # recorrido continuo: reaparece al pasar por el limbo
        phi = ((phi + math.pi / 2) % math.pi) - math.pi / 2
        c = math.cos(math.radians(lat))
        x = cx + R * c * math.sin(phi); y = cy - R * math.sin(math.radians(lat))
        vis = clamp(math.cos(phi) * 3)
        out += walker(x, y + 12, .42, t, "#E4572E" if lat == 0 else "#2FBF71", speed=6) if vis > .05 else ""
    # flechas de velocidad (longitud ∝ cos(latitud))
    for (lat, label, col, tstart, py) in ((0, "ECUADOR: ≈ 1 670 km/h", "#FF4D6D", .12, 1140), (60, "A 60°: MENOS (≈ 835 km/h)", "#FFE14D", .42, 1070)):
        k = ease_out(prog(t, d * tstart, d * tstart + .6))
        L = 250 * math.cos(math.radians(lat)) * k
        y = cy - R * math.sin(math.radians(lat))
        out += hl.arrow(cx - L / 2, y, cx + L / 2, y, col, 12, 34) if L > 8 else ""
        out += pill(540, py + (0 if lat == 0 else -0), 760, label, "#0B1030", col, col, 28, pop(t, d * tstart + .2, .4))
    k = pop(t, d * .7, .4)
    out += pill(540, 1210, 640, "POLOS: casi 0 km/h", "#0B1030", "#7CF0B3", "#7CF0B3", 28, k)
    out += text(540, 190, "LA TIERRA GIRA…", 66, "#fff", sw=13, scale=pop(t, 0, .5))
    out += text(540, 270, "…y tú caminas tranquilo", 38, "#CFF1FF", sw=9, opacity=prog(t, .6, 1.2))
    return out


# ------------------------------------------------------------------ 3. todo se mueve junto
@scene
def scene_together(t, d):
    out = space(t)
    # estrellas que se desplazan hacia la izquierda: el espacio "ve" pasar a todo el conjunto
    rnd = random.Random(5)
    for i in range(26):
        y = rnd.uniform(200, 1000); L = rnd.uniform(80, 260); sp = rnd.uniform(500, 1100)
        x = (rnd.uniform(0, 1400) - sp * t) % 1500 - 200
        out += f'<line x1="{x:.0f}" y1="{y:.0f}" x2="{x+L:.0f}" y2="{y:.0f}" stroke="#9FB4E8" stroke-width="4" stroke-linecap="round" opacity=".5"/>'
    # superficie de la Tierra (arco grande) y atmósfera
    out += '<circle cx="540" cy="2350" r="1280" fill="#2E7D4F"/><circle cx="540" cy="2350" r="1280" fill="none" stroke="#7CD3FF" stroke-width="40" opacity=".55"/>'
    out += '<circle cx="540" cy="2350" r="1340" fill="none" stroke="#5CB8FF" stroke-width="50" opacity=".25"/>'
    xs = (150, 390, 630, 870)
    labels = ("NOSOTROS", "EDIFICIOS", "OCÉANOS", "ATMÓSFERA")
    for i, x in enumerate(xs):
        gy = 2350 - math.sqrt(1280 ** 2 - (x - 540) ** 2) + 4
        k = pop(t, d * (.08 + .17 * i), .5)
        # pictograma
        if i == 0:
            out += walker(x, gy, .85, t, speed=5)
        elif i == 1:
            out += (f'<rect x="{x-62}" y="{gy-330}" width="124" height="330" fill="#4B5CA3"/>'
                    + "".join(f'<rect x="{x-42+c*48}" y="{gy-310+r*56}" width="26" height="32" fill="#FFE9A0"/>' for r in range(5) for c in range(2)))
        elif i == 2:
            out += f'<rect x="{x-110}" y="{gy-30}" width="220" height="60" fill="#1E80C8"/>' + f'<polyline points="{" ".join(f"{x-110+u*10},{gy-30+8*math.sin(t*4+u)}" for u in range(23))}" fill="none" stroke="#CFE8FF" stroke-width="6"/>'
        else:
            out += f'<g transform="translate({x+14*math.sin(t*.8):.0f},{gy-210})"><g fill="#fff" opacity=".95"><ellipse rx="80" ry="26"/><circle cx="-30" cy="-18" r="30"/><circle cx="20" cy="-28" r="36"/></g></g>'
        ay = 880
        out += (hl.arrow(x - 60, ay, x + 60 + 6 * math.sin(t * 5), ay, "#35E08A", 14, 36) + pill(x, ay - 70, 220 if i != 3 else 240, labels[i], "#0F3F2A", "#35E08A", "#CFFFE5", 24 if i != 3 else 22, k))
    out += text(540, 190, "TODO SE MUEVE", 70, "#fff", sw=14, scale=pop(t, 0, .5)) + text(540, 275, "JUNTO CON LA TIERRA", 56, "#FFE14D", sw=13, scale=pop(t, .2, .5))
    if t > d * .6:
        out += pill(540, 1225, 840, "POR INERCIA, CONSERVAN ESE MOVIMIENTO", "#0B1030", "#FFE14D", "#FFE14D", 28, pop(t, d * .6, .4))
    return out


# ------------------------------------------------------------------ 4. avión: movimiento uniforme
@scene
def scene_plane(t, d):
    out = '<rect width="1080" height="1920" fill="url(#skyHi)"/>'
    for i, (x0, y, sc, mul) in enumerate([(100, 300, 1.2, 1.0), (700, 480, 1.0, 1.4), (950, 360, .8, 1.2)]):
        x = (x0 - 380 * mul * t) % 1700 - 300
        out += (f'<g transform="translate({x:.0f},{y}) scale({sc})" fill="#fff" opacity=".9"><ellipse rx="120" ry="36"/><circle cx="-40" cy="-26" r="40"/><circle cx="22" cy="-38" r="50"/></g>')
    for i in range(8):
        x = (i * 190 - 900 * t) % 1300 - 100
        out += f'<line x1="{x:.0f}" y1="{380+i*30}" x2="{x+200:.0f}" y2="{380+i*30}" stroke="#fff" stroke-width="5" stroke-linecap="round" opacity=".5"/>'
    out += f'<g transform="translate(540,{430+8*math.sin(t*1.3):.0f}) scale(.82)">{pl.airliner(t)}</g>'
    out += pill(540, 680, 640, "GRAN VELOCIDAD", "#10305F", "#7CD3FF", "#CFF1FF", 34, pop(t, .4, .4))
    # corte de la cabina: pasajero y vaso de agua tranquilos
    out += '<rect x="90" y="770" width="900" height="470" rx="40" fill="#E9EEF6" stroke="#5B6578" stroke-width="6"/><rect x="120" y="1090" width="840" height="120" rx="16" fill="#CBD3E3"/>'
    out += '<rect x="640" y="800" width="270" height="200" rx="40" fill="#1B2B4A" stroke="#fff" stroke-width="8"/>'
    out += '<rect x="656" y="816" width="238" height="168" rx="30" fill="url(#skyHi)"/>' + f'<ellipse cx="{(780 - 220*((t*.5)%1))+110:.0f}" cy="900" rx="44" ry="14" fill="#fff" opacity=".9"/>'
    # pasajero (de perfil, sentado)
    out += ('<rect x="330" y="960" width="120" height="150" rx="30" fill="#1F7AE0"/><rect x="330" y="1090" width="260" height="36" rx="14" fill="#1F7AE0"/>'
            '<circle cx="400" cy="900" r="46" fill="#F2C29B"/><path d="M356,894 Q358,848 404,850 Q450,852 448,894 Q420,874 392,880 Z" fill="#3A2412"/>'
            '<circle cx="424" cy="898" r="5" fill="#222"/><path d="M416,922 Q430,932 442,920" fill="none" stroke="#6B2A2A" stroke-width="4" stroke-linecap="round"/>'
            '<rect x="440" y="1000" width="130" height="22" rx="10" fill="#1F7AE0" transform="rotate(-8 440 1010)"/>')
    # vaso de agua sobre la mesa: la superficie apenas se mueve
    out += ('<rect x="560" y="1070" width="180" height="16" rx="6" fill="#8892A8"/><path d="M620,1070 L632,1010 L704,1010 L716,1070 Z" fill="#CFEAFF" opacity=".55" stroke="#fff" stroke-width="3"/>'
            f'<path d="M624,1050 L628,1032 L708,1032 L712,1050 Z" fill="#4DB8FF"/><line x1="628" y1="{1032+1.2*math.sin(t*3):.1f}" x2="708" y2="{1032-1.2*math.sin(t*3):.1f}" stroke="#fff" stroke-width="4"/>')
    out += text(540, 190, "COMO VOLAR EN AVIÓN", 62, "#fff", sw=13, scale=pop(t, 0, .5))
    if t > d * .5:
        out += pill(540, 1285 - 30, 820, "MOVIMIENTO CONSTANTE: NO LO SENTIMOS", "#0F3F2A", "#35E08A", "#CFFFE5", 28, pop(t, d * .5, .4))
    return out


# ------------------------------------------------------------------ 5. gravedad y efectos sutiles
@scene
def scene_gravity(t, d):
    out = space(t)
    cx, cy, R = 540, 640, 250
    rot = 40 * t
    out += ea.earth(cx, cy, R, rot, view_tilt=90, axis_tilt=0)
    # personas pegadas a la superficie (vista desde el polo norte): giran con el planeta
    for i in range(6):
        th = math.radians(i * 60 + rot * -1.0 + 0)
        x, y = cx + (R - 6) * math.cos(th), cy + (R - 6) * math.sin(th)
        ang = math.degrees(th) + 90
        out += f'<g transform="translate({x:.0f},{y:.0f}) rotate({ang:.0f})">' + walker(0, 0, .5, t, "#E4572E", speed=0) + '</g>'
        k = pop(t, d * .06 + i * .03, .4)
        out += (f'<g opacity="{min(1,k):.2f}">' + hl.arrow(cx + (R - 6) * math.cos(th), cy + (R - 6) * math.sin(th), cx + (R - 110) * math.cos(th), cy + (R - 110) * math.sin(th), "#FFE14D", 9, 26) + '</g>')
    out += text(540, 190, "LA GRAVEDAD", 78, "#fff", sw=15, scale=pop(t, 0, .5))
    out += text(540, 1075, "nos mantiene sobre la superficie", 36, "#FFE14D", sw=9, opacity=prog(t, d * .1, d * .1 + .5))
    # efectos sutiles: peso un poco menor en el ecuador (exagerado) y desvío de vientos
    if t > d * .38:
        a = pop(t, d * .38, .5)
        for (x, lab, v, col) in ((300, "POLO", 1.0, "#7CF0B3"), (780, "ECUADOR", .965, "#FFA94D")):
            out += (f'<g transform="translate({x},1215) scale({a})"><rect x="-110" y="-50" width="220" height="100" rx="20" fill="#0B1030" stroke="{col}" stroke-width="5"/>'
                    f'<path d="M-70,10 A70 70 0 0 1 70,10" fill="none" stroke="#3B4A7A" stroke-width="10"/>'
                    f'<line x1="0" y1="10" x2="{62*math.cos(math.radians(180-180*(.5+.45*v)) ):.0f}" y2="{10-62*math.sin(math.radians(180-180*(.5+.45*v))):.0f}" stroke="{col}" stroke-width="6" stroke-linecap="round"/></g>')
            out += text(x, 1290, lab, 28, col, sw=7, opacity=min(1, a))
        out += text(540, 1125, "peso: un poquito menos (dibujo exagerado)", 28, "#fff", sw=7, opacity=prog(t, d * .45, d * .45 + .5))
    if t > d * .72:
        a = pop(t, d * .72, .5)
        out += f'<g opacity="{min(1,a):.2f}">'
        for r, off in ((R + 120, 0), (R + 170, 120)):
            pts = " ".join(f"{cx + r*math.cos(math.radians(a2+ off + t*40)):.0f},{cy + r*math.sin(math.radians(a2+off+t*40)):.0f}" for a2 in range(0, 110, 6))
            out += f'<polyline points="{pts}" fill="none" stroke="#9FE3FF" stroke-width="7" stroke-linecap="round" opacity=".8"/>'
        out += '</g>' + text(540, 300, "VIENTOS Y CORRIENTES SE DESVÍAN", 34, "#9FE3FF", sw=8, opacity=min(1, a))
    return out


# ------------------------------------------------------------------ 6. constante vs brusco
def _car_scene(t, x, y, col, lean, ball, S=1.6):
    out = car(x, y, col, 0, S, t)
    bx, by = x - 5 * S, y - 96 * S
    out += (f'<line x1="{bx:.0f}" y1="{by:.0f}" x2="{bx+70*S*math.sin(ball):.0f}" y2="{by+54*S*math.cos(ball):.0f}" stroke="#1B1B2F" stroke-width="4"/>'
            f'<circle cx="{bx+70*S*math.sin(ball):.0f}" cy="{by+54*S*math.cos(ball):.0f}" r="{12*S:.0f}" fill="#FF4D6D" stroke="#7A1A12" stroke-width="3"/>')
    out += f'<circle cx="{x+22*S+lean:.0f}" cy="{y-74*S:.0f}" r="{20*S:.0f}" fill="#F2C29B"/><circle cx="{x+30*S+lean:.0f}" cy="{y-76*S:.0f}" r="{3*S:.0f}" fill="#222"/>'
    return out


@scene
def scene_sudden(t, d):
    tb = d * .5
    out = '<rect width="1080" height="1920" fill="#0B1F4A"/>'
    for (y0, lab, col, sub) in ((180, "MOVIMIENTO CONSTANTE", "#7CF0B3", "no lo sentimos"), (700, "CAMBIO BRUSCO", "#FF8FA3", "¡sí lo sentimos!")):
        out += f'<rect x="30" y="{y0}" width="1020" height="470" rx="30" fill="url(#skyHi)"/><rect x="30" y="{y0+330}" width="1020" height="140" fill="#3A3F58"/>'
        out += pill(300, y0 + 55, 520 if y0 < 500 else 440, lab, "#0B1030", col, col, 28)
        for i in range(9):                                               # marcas de la carretera
            sp = 520 if y0 < 500 or t < tb else 520 * max(0, 1 - (t - tb) * 2.2)
            pos = (i * 150 - (520 * t if y0 < 500 else (520 * t if t < tb else 520 * tb + 520 * ((t - tb) - (t - tb) ** 2 * 1.1)))) % 1350 - 100
            out += f'<rect x="{pos:.0f}" y="{y0+415}" width="70" height="8" fill="#F3F3F3" opacity=".8"/>'
    # coche de arriba: velocidad uniforme, el péndulo cuelga vertical
    out += _car_scene(t, 500, 180 + 395, "#4C6EF5", 0, .02 * math.sin(t * 3))
    # coche de abajo: frena de golpe en tb
    tau = max(0, t - tb)
    lean = 60 * math.exp(-tau * 1.5) * min(1, tau * 6) if tau > 0 else 0
    ball = (1.1 * math.exp(-tau * 1.2) * math.cos(tau * 8)) if tau > 0 else 0
    out += _car_scene(t, 500, 700 + 395, "#E4572E", lean, ball)
    if tau > 0:
        out += text(540, 700 + 150, "¡FRENAZO!", 70, "#FFE14D", sw=14, scale=pop(t, tb, .3), rot=-4)
        out += "".join(f'<line x1="{330-i*30}" y1="{700+330+i*18}" x2="{260-i*30}" y2="{700+330+i*18}" stroke="#fff" stroke-width="5" stroke-linecap="round" opacity="{max(0,1-tau):.2f}"/>' for i in range(4))
    out += text(540, 130, "¿CUÁNDO SENTIMOS EL MOVIMIENTO?", 46, "#fff", sw=11, scale=pop(t, 0, .5))
    out += text(540, 1230, "sentimos los cambios de velocidad, no la velocidad", 30, "#FFE14D", sw=8, opacity=prog(t, d * .6, d * .6 + .5))
    return out


# ------------------------------------------------------------------ 7. Tierra majestuosa
@scene
def scene_earth(t, d):
    k = ease_in_out(t / d)
    out = space(t)
    cam = cam_at(lerp(1.3, 1.0, k), 540, 780)
    main = ea.earth(540, 790, 320, 20 + 22 * t, view_tilt=15)
    main += hl.arrow(150, 1040, 930, 1040, "#7CD3FF", 14, 40) if False else ""
    out += layer(main, cam)
    sp = prog(t, d * .3, d * .5)
    if 0 < sp < 1:
        sx, sy = lerp(950, 100, sp), lerp(200, 520, sp)
        out += f'<line x1="{sx:.0f}" y1="{sy:.0f}" x2="{sx+150:.0f}" y2="{sy-60:.0f}" stroke="#fff" stroke-width="5" stroke-linecap="round" opacity="{1-sp:.2f}"/>'
    out += text(540, 190, "GIRAMOS RÁPIDO,", 70, "#fff", sw=14, scale=pop(t, 0, .5)) + text(540, 280, "PERO A VELOCIDAD CONSTANTE", 46, "#FFE14D", sw=12, scale=pop(t, .4, .5))
    out += text(540, 1160, "junto con todo lo que nos rodea", 34, "#CFF1FF", sw=8, opacity=prog(t, d * .5, d * .5 + .6))
    return out


# ------------------------------------------------------------------ 8. despedida + logotipo
@scene
def scene_final(t, d):
    out = space(t)
    ey = lerp(780, 400, smooth(prog(t, d * .1, d * .35)))
    R = lerp(300, 140, smooth(prog(t, d * .1, d * .35)))
    out += ea.earth(540, ey, R, 30 + 22 * t, view_tilt=15)
    if t < d * .5:
        out += text(540, 190, "¿TE GUSTA DESCUBRIR", 54, "#fff", sw=12, scale=pop(t, .2, .5)) + text(540, 265, "CÓMO FUNCIONA EL MUNDO?", 54, "#FFE14D", sw=12, scale=pop(t, .6, .5))
    if t > d * .3:
        k2 = pop(t, d * .3, .7)
        out += logo(540, 790, k2 * 1.5, t, min(1, k2))
    if t > d * .62:
        out += pill(540, 1245, 760, "¡SÍGUENOS Y DESCUBRE MÁS!", "#FF3D6B", "#fff", "#fff", 36, pop(t, d * .62, .5) * (1 + .04 * math.sin(t * 8)))
    return out


SFX = {
    "hook": [("whoosh", lambda d: .1), ("pop", lambda d: d * .52)],
    "walk": [("pop", lambda d: .05), ("click", lambda d: d * .12), ("click", lambda d: d * .42)],
    "together": [("pop", lambda d: d * .08), ("pop", lambda d: d * .25), ("pop", lambda d: d * .42), ("pop", lambda d: d * .59)],
    "plane": [("pop", lambda d: .4), ("pop", lambda d: d * .5)],
    "gravity": [("pop", lambda d: .05), ("click", lambda d: d * .38), ("pop", lambda d: d * .72)],
    "sudden": [("brake", lambda d: d * .5), ("pop", lambda d: d * .5)],
    "earth": [("pop", lambda d: .4)],
    "final": [("shimmer", lambda d: d * .3), ("ding", lambda d: d * .36), ("pop", lambda d: d * .62)],
}
