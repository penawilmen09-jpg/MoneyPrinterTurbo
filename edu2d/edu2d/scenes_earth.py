"""Video 4: ¿Qué pasaría si la Tierra dejara de girar durante 5 segundos? (experimento hipotético)"""
import math
import random
from .core import W, H, n, clamp, lerp, prog, smooth, ease_out, ease_in_out, ease_out_back
from .svgkit import layer, cam_at, text
from .art import earth as ea
from .art import ocean as oc
from .art import world as wd
from .art import heli as hl

SCENES = {}
SPIN = 48.0            # °/s dibujados (la Tierra real: 15°/h; es una simulación didáctica)


def scene(fn):
    SCENES[fn.__name__.replace("scene_", "")] = fn
    return fn


def pop(t, start, dur=.5):
    return max(ease_out_back(prog(t, start, start + dur)), .001)


def pill(x, y, w, label, fill="#1B1B2F", stroke="#FFE14D", color="#FFE14D", size=38, s=1.0, op=1.0):
    return (f'<g transform="translate({x},{y}) scale({s})" opacity="{op:.2f}"><rect x="{-w/2:.0f}" y="-36" width="{w}" height="72" rx="36" fill="{fill}" stroke="{stroke}" stroke-width="5"/>'
            + text(0, size * .35, label, size, color) + '</g>')


def space(t):
    return '<rect width="1080" height="1920" fill="url(#space)"/>' + ea.stars(t)


def rot_at(t, t_stop, spin=SPIN):
    return spin * min(t, t_stop)


def spin_arrow(cx, cy, R, t, op=1.0):
    a0 = math.radians(200 + (t * 120) % 360)
    pts = " ".join(f"{cx+(R*1.18)*math.cos(a0+k*.05):.0f},{cy+(R*1.18*.45)*math.sin(a0+k*.05):.0f}" for k in range(0, 24))
    return f'<polyline points="{pts}" fill="none" stroke="#FFE14D" stroke-width="10" stroke-linecap="round" opacity="{.8*op:.2f}"/>'


def shock(cx, cy, R, tau, col="#fff"):
    if tau < 0 or tau > .9:
        return ""
    k = tau / .9
    return (f'<circle cx="{cx}" cy="{cy}" r="{R*(1+1.6*k):.0f}" fill="none" stroke="{col}" stroke-width="{18*(1-k)+2:.0f}" opacity="{1-k:.2f}"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{R*(1+.9*k):.0f}" fill="none" stroke="#FFE14D" stroke-width="{10*(1-k)+1:.0f}" opacity="{.8*(1-k):.2f}"/>')


# ------------------------------------------------------------------ 1. gancho
@scene
def scene_hook(t, d):
    ts = d * .78
    z = 1.0 + .45 * smooth(prog(t, 0, ts))
    sh = 16 * math.exp(-(t - ts) * 7) * math.sin(t * 80) if t >= ts else 0
    cam = cam_at(z, 540 + sh, 960 + sh)
    out = layer(space(t), cam, .3)
    main = ea.earth(540, 990, 360, rot_at(t, ts, 70 if t < ts else 0)) + (spin_arrow(540, 990, 360, t) if t < ts else "")
    main += shock(540, 990, 360, t - ts)
    out += layer(main, cam)
    if ts <= t < ts + .1:
        out += '<rect width="1080" height="1920" fill="#fff" opacity=".65"/>'
    for i, (s_, c) in enumerate([("¿QUÉ PASARÍA", "#fff"), ("SI LA TIERRA DEJARA", "#fff"), ("DE GIRAR DURANTE", "#fff"), ("5 SEGUNDOS?", "#FFE14D")]):
        k = pop(t, .05 + i * .1) * (1 + .03 * math.sin(t * 7) * (t > 1.2))
        out += text(540, 180 + i * 88, s_, 70 if i < 3 else 82, c, sw=14, scale=k, opacity=min(1, k * 3))
    if t > ts + .15:
        out += pill(540, 1290, 640, "¡LA TIERRA SE DETIENE!", "#4A1020", "#FF4D6D", "#FF8FA3", 38, pop(t, ts + .15, .4))
    return out


# --------------------------------------------------------------- 2. experimento
@scene
def scene_experiment(t, d):
    ts = d * .66
    out = space(t)
    sh = 14 * math.exp(-(t - ts) * 7) * math.sin(t * 80) if t >= ts else 0
    ex, ey = 540 + sh, 840 + sh
    out += ea.earth(ex, ey, 300, rot_at(t, ts), view_tilt=18)
    if t < ts:
        out += spin_arrow(ex, ey, 300, t)
    out += shock(ex, ey, 300, t - ts)
    out += pill(540, 190, 760, "EXPERIMENTO IMAGINARIO", "#10305F", "#7CD3FF", "#CFF1FF", 40, pop(t, 0, .5))
    for i, label in enumerate(("3", "2", "1")):
        t0 = d * .2 + i * d * .13
        if t0 <= t < t0 + d * .13:
            k = pop(t, t0, .3)
            out += text(540, 470, label, 260, "#FF4D6D", sw=18, scale=k) + f'<circle cx="540" cy="395" r="{190*k:.0f}" fill="none" stroke="#FF4D6D" stroke-width="10" opacity=".5"/>'
    if ts <= t < ts + .1:
        out += '<rect width="1080" height="1920" fill="#fff" opacity=".6"/>'
    if t >= ts:
        out += text(540, 470, "¡STOP!", 150, "#FFE14D", sw=18, scale=pop(t, ts, .4))
        out += text(540, 1240, "(imposible en la vida real)", 42, "#fff", sw=10, opacity=prog(t, ts + .6, ts + 1.1))
    return out


# --------------------------------------------------------------------- 3. velocidad
@scene
def scene_speed(t, d):
    out = space(t)
    cx, cy, R = 400, 830, 280
    out += ea.earth(cx, cy, R, SPIN * t, view_tilt=0, axis_tilt=0)
    out += text(540, 190, "VELOCIDAD DEL SUELO", 70, "#fff", sw=14, scale=pop(t, 0, .5))
    rows = [(0, "ECUADOR: 1 670 km/h", "#FF4D6D", .15, 830), (30, "A 30°: 1 450 km/h", "#FFA94D", .3, 700), (60, "A 60°: 835 km/h", "#FFE14D", .45, 570)]
    for lat, label, col, tstart, py in rows:
        y = cy - R * math.sin(math.radians(lat))
        L = 250 * math.cos(math.radians(lat))
        k = ease_out(prog(t, d * tstart, d * tstart + .6))
        x0 = cx - 130
        out += f'<ellipse cx="{cx}" cy="{y:.0f}" rx="{R*math.cos(math.radians(lat)):.0f}" ry="{9*math.cos(math.radians(lat)):.0f}" fill="none" stroke="#fff" stroke-width="3" stroke-dasharray="10 8" opacity="{.5*k:.2f}"/>'
        if L * k > 6:
            out += hl.arrow(x0, y, x0 + L * k, y, col, 14, 40)
        pk = pop(t, d * tstart + .2, .4)
        out += f'<line x1="{x0 + L*k:.0f}" y1="{y:.0f}" x2="690" y2="{py}" stroke="{col}" stroke-width="3" opacity="{min(1,pk):.2f}"/>'
        out += pill(865, py, 340, label, "#0B1030", col, col, 25, pk)
    k = pop(t, d * .65, .4)
    out += f'<line x1="{cx}" y1="{cy-R}" x2="690" y2="450" stroke="#7CF0B3" stroke-width="3" opacity="{min(1,k):.2f}"/>'
    out += pill(865, 450, 340, "POLOS: casi 0 km/h", "#0B1030", "#7CF0B3", "#7CF0B3", 25, k)
    out += hl.arrow(240, 1190, 800, 1190, "#7CD3FF", 18, 46) + text(540, 1150, "GIRA DE OESTE A ESTE", 40, "#CFF1FF", sw=9)
    return out


# ----------------------------------------------------------------- ciudad lateral
BUILD = [(30, 150, 430, "#5B6FB5"), (200, 120, 300, "#7C8BC9"), (340, 170, 520, "#4B5CA3"), (530, 130, 360, "#6A7CBF"),
         (680, 190, 470, "#3F4E94"), (890, 150, 330, "#7584C6")]
GROUND = 1180


def _skyline(color_shift=0):
    out = ""
    rnd = random.Random(5)
    for (x, w, h, col) in BUILD:
        out += f'<rect x="{x}" y="{GROUND-h}" width="{w}" height="{h}" fill="{col}"/><rect x="{x}" y="{GROUND-h}" width="{w}" height="10" fill="#fff" opacity=".18"/>'
        for wy in range(GROUND - h + 26, GROUND - 40, 40):
            for wx in range(x + 14, x + w - 22, 30):
                if rnd.random() < .55:
                    out += f'<rect x="{wx}" y="{wy}" width="16" height="22" fill="#FFE9A0" opacity=".9"/>'
                else:
                    out += f'<rect x="{wx}" y="{wy}" width="16" height="22" fill="#2B3A6E" opacity=".7"/>'
    return out


_SKY = {}


def city_side(t, scroll=0.0, shake=(0, 0), cloud_speed=20, sky="skyDay"):
    out = '<rect x="-300" y="-300" width="1700" height="2600" fill="url(#%s)"/>' % sky
    out += '<circle cx="880" cy="330" r="220" fill="url(#sun)"/><circle cx="880" cy="330" r="50" fill="#FFF3B0"/>'
    for i, (x0, y, sc) in enumerate([(100, 330, 1.3), (620, 500, 1.0), (950, 250, .8)]):
        out += oc_cloud((x0 + cloud_speed * t * (1 + .3 * i)) % 1500 - 200, y, sc)
    off = scroll % 1080
    for o in (-off, 1080 - off):
        out += f'<g transform="translate({o + shake[0]:.1f},{shake[1]:.1f})">{_skyline()}</g>'
    out += f'<rect x="-100" y="{GROUND}" width="1300" height="40" fill="#C8CEDC"/><rect x="-100" y="{GROUND+40}" width="1300" height="130" fill="#3A3F58"/>'
    out += f'<rect x="-100" y="{GROUND+170}" width="1300" height="900" fill="#2B2F48"/>'
    for k in range(-1, 10):
        x = (k * 150 - scroll * 1.0) % 1500 - 100
        out += f'<rect x="{x:.0f}" y="{GROUND+98}" width="70" height="8" fill="#F3F3F3" opacity=".8"/>'
    return out


def oc_cloud(x, y, sc):
    return (f'<g transform="translate({x:.0f},{y}) scale({sc})" fill="#fff" opacity=".9"><ellipse cx="0" cy="0" rx="120" ry="36"/>'
            '<circle cx="-40" cy="-26" r="40"/><circle cx="22" cy="-38" r="50"/><circle cx="72" cy="-12" r="34"/></g>')


def car(x, y, col, rot=0, s=1.0, t=0):
    sp = t * 600
    wheel = lambda cx: (f'<circle cx="{cx}" cy="0" r="22" fill="#1B1B2F"/><circle cx="{cx}" cy="0" r="11" fill="#9AA6BA"/>'
                        f'<line x1="{cx}" y1="-9" x2="{cx}" y2="9" stroke="#1B1B2F" stroke-width="3" transform="rotate({sp:.0f} {cx} 0)"/>')
    return (f'<g transform="translate({x:.1f},{y:.1f}) rotate({rot:.1f}) scale({s})">'
            f'<rect x="-95" y="-62" width="190" height="46" rx="16" fill="{col}" stroke="#1B1B2F" stroke-width="4"/>'
            f'<path d="M-52,-62 Q-40,-104 0,-104 Q42,-104 56,-62 Z" fill="{col}" stroke="#1B1B2F" stroke-width="4"/>'
            '<path d="M-38,-66 Q-30,-96 -2,-96 L-2,-66 Z M6,-66 L6,-96 Q36,-96 46,-66 Z" fill="#CFEAFF"/>' + wheel(-56) + wheel(58) + '</g>')


def person(x, y, t, rot=0, col="#E4572E", flail=0.0, s=1.0):
    a = math.sin(t * 14) * 50 * flail
    return (f'<g transform="translate({x:.1f},{y:.1f}) rotate({rot:.1f}) scale({s})">'
            f'<rect x="-14" y="-70" width="12" height="70" rx="6" fill="#27374D" transform="rotate({-a*.4:.0f} -8 -70)"/>'
            f'<rect x="2" y="-70" width="12" height="70" rx="6" fill="#27374D" transform="rotate({a*.4:.0f} 8 -70)"/>'
            f'<rect x="-22" y="-150" width="44" height="86" rx="16" fill="{col}"/>'
            f'<rect x="-34" y="-142" width="12" height="64" rx="6" fill="{col}" transform="rotate({-40-a:.0f} -28 -142)"/>'
            f'<rect x="22" y="-142" width="12" height="64" rx="6" fill="{col}" transform="rotate({40+a:.0f} 28 -142)"/>'
            '<circle cx="0" cy="-174" r="24" fill="#F2C29B"/><path d="M-24,-182 Q0,-212 24,-182 Z" fill="#4A2F1B"/>'
            + ('<ellipse cx="8" cy="-168" rx="6" ry="9" fill="#fff" stroke="#222" stroke-width="2"/><circle cx="9" cy="-168" r="2.5" fill="#222"/><ellipse cx="0" cy="-152" rx="5" ry="7" fill="#6B2A2A"/>' if flail > 0 else
               '<circle cx="8" cy="-172" r="3" fill="#222"/><path d="M0,-160 Q8,-155 14,-160" fill="none" stroke="#6B2A2A" stroke-width="3"/>')
            + '</g>')


def crate(x, y, rot, s=1.0, col="#B07A3F"):
    return (f'<g transform="translate({x:.1f},{y:.1f}) rotate({rot:.1f}) scale({s})"><rect x="-34" y="-68" width="68" height="68" fill="{col}" stroke="#4A2F1B" stroke-width="4"/>'
            '<path d="M-34,-68 L34,0 M34,-68 L-34,0" stroke="#4A2F1B" stroke-width="4"/></g>')


def cone(x, y, rot, s=1.0):
    return (f'<g transform="translate({x:.1f},{y:.1f}) rotate({rot:.1f}) scale({s})"><polygon points="0,-80 28,0 -28,0" fill="#FF7A1A"/>'
            '<rect x="-14" y="-44" width="28" height="12" fill="#fff"/><rect x="-36" y="0" width="72" height="8" fill="#C95A0A"/></g>')


def streak(x, y, L, op=.7):
    return f'<line x1="{x-L:.0f}" y1="{y:.0f}" x2="{x:.0f}" y2="{y:.0f}" stroke="#fff" stroke-width="5" stroke-linecap="round" opacity="{op:.2f}"/>'


# ----------------------------------------------------------- 4. el paron (ciudad)
@scene
def scene_stop(t, d):
    ts = d * .34
    sh = (6 * math.exp(-(t - ts) * 5) * math.sin(t * 70), 4 * math.exp(-(t - ts) * 5) * math.cos(t * 90)) if t >= ts else (0, 0)
    out = city_side(t, 0, sh)
    tau = max(0, t - ts)
    # objetos sueltos: conservan la velocidad (hacia el este = derecha)
    items = [("car", 230, 1118, "#E4572E", 1.0), ("car", 640, 1118, "#4C6EF5", 1.1), ("person", 470, 1160, "#2FBF71", 1.2),
             ("crate", 840, 1160, "", 1.3), ("cone", 960, 1160, "", 1.0), ("person", 120, 1160, "#F3A712", .9)]
    for (kind, x0, y0, col, vm) in items:
        V = 900 * vm
        x = x0 + (V * tau * (1 - .12 * tau) if t >= ts else 0)
        up = (-90 * math.sin(min(tau * 2.2, math.pi)) * (1 if kind in ("crate", "cone") else .4)) if t >= ts else 0
        rot = (tau * 160 * vm if kind in ("crate", "cone") else (-8 * min(tau * 3, 1) if kind == "car" else 20 * min(tau * 3, 1)))
        if t >= ts and tau < 3:
            out += "".join(streak(x - 50 - i * 14, y0 - 40 - 24 * i + up, 160 + 120 * vm, .55 - .1 * i) for i in range(3))
        if kind == "car":
            out += car(x, y0 + up, col, rot, 1.0, tau)
        elif kind == "person":
            out += person(x, y0 + up, t, rot, col, flail=1.0 if t >= ts else 0, s=1.0)
        elif kind == "crate":
            out += crate(x, y0 + up, rot)
        else:
            out += cone(x, y0 + up, rot)
    # polvo y hojas arrastrados por el aire
    if t >= ts:
        rnd = random.Random(2)
        for i in range(28):
            y = rnd.uniform(560, 1150); sp = rnd.uniform(700, 1500)
            x = (rnd.uniform(0, 1100) + sp * tau) % 1400 - 150
            out += streak(x, y, rnd.uniform(60, 200), .4)
    # velocímetro del suelo
    v = 1670 * (1 - smooth(prog(t, ts, ts + .15)))
    out += (f'<rect x="270" y="270" width="540" height="130" rx="28" fill="#0B1030" stroke="#7CF0B3" stroke-width="6" opacity=".95"/>'
            + text(540, 320, "VELOCIDAD DEL SUELO", 30, "#9FD0FF", sw=0)
            + text(540, 378, f"{v:,.0f} km/h".replace(",", " "), 58, "#FF8FA3" if t >= ts else "#7CF0B3", sw=0))
    if t < ts:
        out += text(540, 200, "TODO VIAJA CON LA TIERRA", 56, "#fff", sw=12, scale=pop(t, 0, .5))
    else:
        out += text(540, 200, "¡EL SUELO SE DETIENE!", 66, "#FFE14D", sw=14, scale=pop(t, ts, .4))
        out += pill(540, 470, 780, "EDIFICIOS: QUIETOS · OBJETOS: SIGUEN", "#10305F", "#7CD3FF", "#CFF1FF", 30, pop(t, ts + .6, .4))
    if ts <= t < ts + .1:
        out += '<rect width="1080" height="1920" fill="#fff" opacity=".6"/>'
    return out


# --------------------------------------------------------------- 5. inercia
@scene
def scene_inertia(t, d):
    sp = 700 * ease_out(prog(t, 0, .6)) + 300
    scroll = sp * t * .8
    out = city_side(t, scroll, cloud_speed=40)
    out += text(540, 200, "INERCIA", 100, "#fff", sw=18, scale=pop(t, 0, .5))
    # objetos que avanzan hacia el este respecto al suelo (cámara que los sigue)
    out += streak(300, 940, 260, .5) + streak(380, 1000, 300, .5) + streak(500, 700, 340, .4)
    out += car(330 + 10 * math.sin(t * 3), 1150, "#E4572E", -4 + 3 * math.sin(t * 5), 1.2, t)
    out += person(680, 1020 + 30 * math.sin(t * 4), t, 80 + 12 * math.sin(t * 5), "#2FBF71", 1.0, 1.1)
    out += crate(870, 1010 + 30 * math.sin(t * 5 + 1), t * 140, 1.0) + cone(150, 1000 + 20 * math.sin(t * 4), t * 190, 1.0)
    out += hl.arrow(120, 480, 640, 480, "#FFA94D", 18, 50) + text(380, 440, "SIGUEN HACIA EL ESTE", 36, "#FFD9A8", sw=9)
    out += pill(540, 570, 600, "EL SUELO YA SE DETUVO", "#10305F", "#7CD3FF", "#CFF1FF", 34, pop(t, d * .35, .4))
    out += text(540, 660, "lo que se mueve, sigue moviéndose", 36, "#fff", sw=9, opacity=prog(t, d * .55, d * .55 + .5))
    return out


# ---------------------------------------------------------------- 6. vientos
@scene
def scene_wind(t, d):
    out = city_side(t, 0, (2 * math.sin(t * 60), 2 * math.cos(t * 70)), cloud_speed=1100, sky="skyDusk")
    # ráfagas: cintas de aire a velocidad extrema
    rnd = random.Random(9)
    for i in range(46):
        y = rnd.uniform(520, 1150); L = rnd.uniform(160, 420); sp = rnd.uniform(1400, 2600)
        x = (rnd.uniform(0, 1500) + sp * t) % 1700 - 300
        out += f'<line x1="{x-L:.0f}" y1="{y:.0f}" x2="{x:.0f}" y2="{y+rnd.uniform(-14,14):.0f}" stroke="#fff" stroke-width="{rnd.choice([4,6,9])}" stroke-linecap="round" opacity="{rnd.uniform(.35,.8):.2f}"/>'
    # árboles doblados por el viento
    for tx in (90, 520, 1000):
        b = ease_out(prog(t, .2, .9))
        out += (f'<g transform="translate({tx},{GROUND}) skewX({-62*b:.0f})"><rect x="-14" y="-130" width="28" height="130" fill="#6B4423"/>'
                '<circle cx="0" cy="-170" r="62" fill="#2F8F57"/><circle cx="-34" cy="-146" r="42" fill="#35A265"/></g>')
    # escombros
    for i in range(10):
        x = (i * 160 + 1500 * t) % 1500 - 200
        y = 700 + 40 * (i % 5) + 30 * math.sin(t * 6 + i)
        out += f'<rect x="{x:.0f}" y="{y:.0f}" width="34" height="14" rx="3" fill="#B07A3F" transform="rotate({t*400+i*40:.0f} {x:.0f} {y:.0f})"/>'
    # velocímetro de viento
    cx, cy, r = 540, 560, 190
    kk = ease_out(prog(t, .3, d * .6))
    ang = lerp(180, 0, kk * .96)
    out += (f'<path d="M{cx-r},{cy} A{r} {r} 0 0 1 {cx+r},{cy}" fill="#0B1030" stroke="#fff" stroke-width="8" opacity=".92"/>'
            f'<path d="M{cx-r+22},{cy} A{r-22} {r-22} 0 0 1 {cx-r+22+2*(r-22)*.15:.0f},{cy-(r-22)*.55:.0f}" fill="none" stroke="#7CF0B3" stroke-width="14"/>')
    for (frac, lab, col) in ((.15, "HURACÁN", "#FFA94D"), (.96, "MÁXIMO", "#FF4D6D")):
        a = math.radians(180 - 180 * frac)
        out += f'<line x1="{cx+(r-30)*math.cos(a):.0f}" y1="{cy-(r-30)*math.sin(a):.0f}" x2="{cx+r*math.cos(a):.0f}" y2="{cy-r*math.sin(a):.0f}" stroke="{col}" stroke-width="8"/>'
    na = math.radians(ang)
    out += f'<line x1="{cx}" y1="{cy}" x2="{cx+(r-26)*math.cos(na):.0f}" y2="{cy-(r-26)*math.sin(na):.0f}" stroke="#FF4D6D" stroke-width="10" stroke-linecap="round"/><circle cx="{cx}" cy="{cy}" r="16" fill="#fff"/>'
    kmh = 1670 * kk
    out += text(cx, cy + 70, f"{kmh:,.0f} km/h".replace(",", " "), 52, "#FFE14D", sw=10)
    out += text(cx - 150, cy + 28, "HURACÁN: 250", 22, "#FFA94D", sw=0, anchor="start") if False else ""
    out += text(540, 200, "¡VIENTOS EXTREMOS!", 70, "#fff", sw=14, scale=pop(t, 0, .5))
    out += text(540, 830, "en el ecuador, hasta ≈1 670 km/h", 34, "#fff", sw=9, opacity=prog(t, d * .5, d * .5 + .5))
    out += text(540, 872, "(más rápido que cualquier huracán)", 30, "#FFD9A8", sw=8, opacity=prog(t, d * .6, d * .6 + .5))
    return out


# --------------------------------------------------------------- 7. océanos
@scene
def scene_ocean(t, d):
    y0 = 1010
    xf = lerp(-250, 1250, ease_in_out(prog(t, d * .18, d * .85)))
    amp = 330 * smooth(prog(t, d * .15, d * .5)) * (1 - .3 * smooth(prog(t, d * .8, d)))
    out = city_side(t, 0, (0, 0), cloud_speed=60, sky="skyDusk")
    # el nivel del mar sube con el avance de la ola
    def surf(x):
        base = y0 + 7 * math.sin(x / 80 + t * 3) + 5 * math.sin(x / 33 - t * 4)
        if x < xf:
            h = amp * (1 - math.exp(-(xf - x) / 380)) * smooth(clamp((xf - x) / 60))
        else:
            h = 0
        return base - h
    xs = list(range(-60, 1141, 12))
    pts = " ".join(f"{x},{surf(x):.1f}" for x in xs)
    out += (f'<polygon points="{pts} 1140,2000 -60,2000" fill="#1E80C8" opacity=".86"/>'
            f'<polygon points="{pts} 1140,2000 -60,2000" fill="url(#seaDeep)" opacity=".35"/>'
            f'<polyline points="{pts}" fill="none" stroke="#fff" stroke-width="8" stroke-linejoin="round" opacity=".85"/>')
    # espuma y gotas en la cresta
    if amp > 40:
        rnd = random.Random(6)
        for i in range(26):
            px = xf - rnd.uniform(-40, 260)
            py = surf(px) - rnd.uniform(0, 70) - 25 * abs(math.sin(t * 5 + i))
            out += f'<circle cx="{px:.0f}" cy="{py:.0f}" r="{rnd.choice([5,7,9])}" fill="#fff" opacity=".8"/>'
    # barco zarandeado cabalgando la ola
    bx = clamp(xf - 280, 120, 900)
    out += oc.ship_g(bx, surf(bx) + 6, .22, -12 * smooth(prog(t, d * .2, d * .6)) + 4 * math.sin(t * 4), oc.ship_exterior())
    out += text(540, 200, "LOS OCÉANOS", 80, "#fff", sw=15, scale=pop(t, 0, .5))
    out += hl.arrow(120, 330, 700, 330, "#FFA94D", 18, 50) + text(410, 300, "EL AGUA SIGUE AL ESTE", 38, "#FFD9A8", sw=9)
    out += pill(540, 460, 760, "OLAS GIGANTES: LA TIERRA SE PARÓ, EL MAR NO", "#10305F", "#7CD3FF", "#CFF1FF", 24, pop(t, d * .4, .4))
    return out


# --------------------------------------------------------- 8. los cinco segundos
@scene
def scene_five(t, d):
    unit = min(1.0, (d - 1.7) / 5.0)
    t0 = .5
    t_end = t0 + 5 * unit
    out = space(t)
    cx, cy, R = 540, 840, 200
    # rotación: detenida durante la cuenta, se reanuda de golpe al final
    rot = 0.0 if t < t_end else SPIN * (t - t_end)
    out += ea.earth(cx, cy, R, 130 + rot, view_tilt=18, night_boost=1.0)
    # anillo de progreso de 5 s
    frac = clamp((t - t0) / (5 * unit)) if t >= t0 else 0
    a1 = -90 + 360 * frac
    rr = 262
    out += f'<circle cx="{cx}" cy="{cy}" r="{rr}" fill="none" stroke="#2B3A6E" stroke-width="22"/>'
    if frac > 0 and frac < 1:
        x2, y2 = cx + rr * math.cos(math.radians(a1)), cy + rr * math.sin(math.radians(a1))
        out += (f'<path d="M{cx},{cy-rr} A{rr} {rr} 0 {1 if frac>.5 else 0} 1 {x2:.1f},{y2:.1f}" fill="none" stroke="#FF4D6D" stroke-width="22" stroke-linecap="round"/>')
    elif frac >= 1:
        out += f'<circle cx="{cx}" cy="{cy}" r="{rr}" fill="none" stroke="#7CF0B3" stroke-width="22"/>'
    if t >= t0 and t < t_end:
        k = int((t - t0) / unit)
        num = 5 - k
        lt = (t - t0) - k * unit
        s = 1 + .35 * math.exp(-lt * 6)
        out += text(540, 410, str(num), 230, "#FF4D6D", sw=20, scale=s)
        out += text(540, 1200, "5 SEGUNDOS DE PAUSA", 44, "#fff", sw=10)
    else:
        out += text(540, 190, "LA CUENTA ATRÁS", 64, "#fff", sw=13, scale=pop(t, 0, .5)) if t < t0 else ""
    if t >= t_end:
        out += shock(cx, cy, R * 1.2, t - t_end, "#FFE14D")
        if t < t_end + .1:
            out += '<rect width="1080" height="1920" fill="#fff" opacity=".55"/>'
        out += text(540, 330, "¡VUELVE A GIRAR!", 78, "#FFE14D", sw=15, scale=pop(t, t_end, .4))
        out += pill(540, 1200, 820, "OTRO CAMBIO BRUSCO Y DESTRUCTIVO", "#4A1020", "#FF4D6D", "#FF8FA3", 32, pop(t, t_end + .3, .4))
    return out


# ------------------------------------------------------------------- 9. final
@scene
def scene_final(t, d):
    out = space(t)
    out += ea.earth(540, 700, 290, 40 + SPIN * t, view_tilt=18)
    out += text(540, 190, "NO HAY BOTÓN", 82, "#fff", sw=15, scale=pop(t, .3, .5))
    out += text(540, 285, "DE PAUSA", 82, "#FFE14D", sw=15, scale=pop(t, .6, .5))
    # botón de pausa que no funciona + cursor
    bx, by = 540, 1110
    press = prog(t, d * .42, d * .5)
    shake = 8 * math.sin(t * 40) * (1 if d * .5 < t < d * .62 else 0)
    out += (f'<g transform="translate({bx+shake:.1f},{by}) scale({1-.08*(press>0 and t<d*.55)})"><circle r="96" fill="#1B1B2F" stroke="#fff" stroke-width="8"/>'
            '<rect x="-34" y="-44" width="24" height="88" rx="6" fill="#fff"/><rect x="10" y="-44" width="24" height="88" rx="6" fill="#fff"/></g>')
    cxp = lerp(900, bx + 30, ease_out(prog(t, d * .15, d * .42)))
    cyp = lerp(1320, by + 40, ease_out(prog(t, d * .15, d * .42)))
    out += f'<polygon points="{cxp:.0f},{cyp:.0f} {cxp:.0f},{cyp+64:.0f} {cxp+18:.0f},{cyp+50:.0f} {cxp+32:.0f},{cyp+80:.0f} {cxp+44:.0f},{cyp+74:.0f} {cxp+30:.0f},{cyp+44:.0f} {cxp+54:.0f},{cyp+42:.0f}" fill="#fff" stroke="#1B1B2F" stroke-width="4"/>'
    if t > d * .5:
        k = pop(t, d * .5, .4)
        out += (f'<g transform="translate({bx},{by}) scale({k})"><circle r="124" fill="none" stroke="#FF4D6D" stroke-width="14"/>'
                '<line x1="-88" y1="-88" x2="88" y2="88" stroke="#FF4D6D" stroke-width="14" stroke-linecap="round"/></g>')
    s3 = pop(t, d * .66, .5)
    out += (f'<g transform="translate(540,1300) scale({s3*(1+.05*math.sin(t*8)):.3f})"><rect x="-290" y="-62" width="580" height="124" rx="62" fill="#FF3D6B" stroke="#fff" stroke-width="8"/>'
            + text(0, 22, "¿LO SABÍAS? SÍGUEME", 44, "#fff") + '</g>')
    return out


SFX = {
    "hook": [("riser", lambda d: .0, lambda d: d * .78, 1.0), ("boom", lambda d: d * .78), ("pop", lambda d: .05)],
    "experiment": [("tick", lambda d: d * .2), ("tick", lambda d: d * .33), ("tick", lambda d: d * .46), ("boom", lambda d: d * .66), ("pop", lambda d: .05)],
    "speed": [("pop", lambda d: .05), ("click", lambda d: d * .18), ("click", lambda d: d * .36), ("click", lambda d: d * .54)],
    "stop": [("boom", lambda d: d * .34), ("rumble", lambda d: d * .34, lambda d: d * .5, .4), ("wind", lambda d: d * .38, lambda d: d * .55, .3)],
    "inertia": [("wind", lambda d: 0, lambda d: d, .55), ("pop", lambda d: .05)],
    "wind": [("wind", lambda d: 0, lambda d: d, .8), ("pop", lambda d: .05)],
    "ocean": [("rumble", lambda d: d * .15, lambda d: d * .7, .6), ("crash", lambda d: d * .5), ("pop", lambda d: .05)],
    "five": [("tick", lambda d: .5 + i * min(1.0, (d - 1.7) / 5.0)) for i in range(5)] + [("boom", lambda d: .5 + 5 * min(1.0, (d - 1.7) / 5.0)), ("rumble", lambda d: .5 + 5 * min(1.0, (d - 1.7) / 5.0), lambda d: 1.2, .6)],
    "final": [("pop", lambda d: .3), ("click", lambda d: d * .42), ("boom", lambda d: d * .5), ("ding", lambda d: d * .66)],
}
