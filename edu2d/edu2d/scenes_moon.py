"""Video 6 · Explora Ciencia 360 — ¿Qué pasaría si la Luna desapareciera de repente? (escenario hipotético)"""
import math
import random
from .core import W, H, n, clamp, lerp, prog, smooth, ease_out, ease_in_out, ease_out_back
from .svgkit import layer, cam_at, text
from .art import earth as ea
from .art import moon as mn
from .art import world as wd
from .art import ocean as oc
from .art import heli as hl

SCENES = {}


def scene(fn):
    SCENES[fn.__name__.replace("scene_", "")] = fn
    return fn


def pop(t, start, dur=.5):
    return max(ease_out_back(prog(t, start, start + dur)), .001)


def pill(x, y, w, label, fill="#10305F", stroke="#7CD3FF", color="#CFF1FF", size=36, s=1.0, op=1.0):
    return (f'<g transform="translate({x},{y}) scale({s})" opacity="{op:.2f}"><rect x="{-w/2:.0f}" y="-36" width="{w}" height="72" rx="36" fill="{fill}" stroke="{stroke}" stroke-width="5"/>'
            + text(0, size * .35, label, size, color) + '</g>')


def space(t):
    return '<rect width="1080" height="1920" fill="url(#space)"/>' + ea.stars(t)


def nsky(t, stars=90):
    return '<rect x="-300" y="-300" width="1700" height="2600" fill="url(#night)"/>' + ea.stars(t, stars, seed=11, h=1100)


def vanish_fx(cx, cy, R, tau):
    """Destello al desaparecer algo (tau = segundos desde la desaparición)."""
    if tau < 0 or tau > 1.2:
        return ""
    k = tau / 1.2
    out = f'<circle cx="{cx}" cy="{cy}" r="{R*(.4+1.6*k):.0f}" fill="none" stroke="#fff" stroke-width="{16*(1-k)+1:.0f}" opacity="{1-k:.2f}"/>'
    for i in range(10):
        a = i * 36 + k * 30
        x1, y1 = cx + R * (.5 + k) * math.cos(math.radians(a)), cy + R * (.5 + k) * math.sin(math.radians(a))
        out += mn_spark(x1, y1, 16 * (1 - k) + 3, tau * 5 + i, 1 - k)
    return out


def mn_spark(x, y, r, t, op=1.0):
    return (f'<g opacity="{op:.2f}"><line x1="{x-r:.0f}" y1="{y:.0f}" x2="{x+r:.0f}" y2="{y:.0f}" stroke="#fff" stroke-width="4" stroke-linecap="round"/>'
            f'<line x1="{x:.0f}" y1="{y-r:.0f}" x2="{x:.0f}" y2="{y+r:.0f}" stroke="#fff" stroke-width="4" stroke-linecap="round"/></g>')


def hills_night(dark=0.0):
    c1, c2 = ("#1D3A5C", "#12284A") if dark < .5 else ("#0B1830", "#070F22")
    return (f'<path d="M-100,1130 Q200,1010 520,1100 T1200,1060 L1200,2000 L-100,2000 Z" fill="{c1}"/>'
            f'<path d="M-100,1240 Q300,1180 640,1230 T1200,1210 L1200,2000 L-100,2000 Z" fill="{c2}"/>')


# ------------------------------------------------------------------ 1. gancho
@scene
def scene_hook(t, d):
    tv = d * .46
    moon_on = t < tv
    out = nsky(t)
    k_out = prog(t, d * .8, d)
    tau = t - tv
    if moon_on:
        pulse = 1 + .015 * math.sin(t * 3)
        out += mn.moon(720, 520, 330 * pulse, glow=1.0)
    elif tau < .5:
        sc = 1 + .1 * math.sin(tau / .5 * math.pi) - tau / .5 * 1.0
        out += mn.moon(720, 520, max(1, 330 * sc), glow=1 - tau / .5, op=1 - tau / .5)
    out += vanish_fx(720, 520, 330, tau)
    dark = 0.0 if moon_on else smooth(prog(tau, 0, .6))
    out += hills_night(dark)
    for i, x in enumerate((90, 940, 1030)):                     # árboles
        out += f'<polygon points="{x},{1050-i*20} {x-50},{1180} {x+50},{1180}" fill="#0D2438"/><polygon points="{x},{1100-i*20} {x-64},{1230} {x+64},{1230}" fill="#0D2438"/>'
    # la persona
    out += mn.person(300, 1250, 1.45, t, "surprised" if not moon_on else "neutral", "cheeks" if not moon_on else "point",
                     -22 if moon_on else -8 + 3 * math.sin(t * 9))
    out += f'<rect width="1080" height="1920" fill="#000a1f" opacity="{.45*dark:.2f}"/>'
    if tau > .2:
        out += text(480, 820, "!", 160, "#FFE14D", sw=14, scale=pop(t, tv + .2, .35))
    # hacia el espacio: la Tierra aparece y crece
    if k_out > 0:
        out += f'<rect width="1080" height="1920" fill="url(#space)" opacity="{k_out:.2f}"/>'
        out += ea.earth(540, 760, 40 + 230 * ease_out(k_out), 60 + 40 * t, view_tilt=18)
    return out


# ------------------------------------------------------------------ 2. preguntas
@scene
def scene_questions(t, d):
    out = space(t)
    ex, ey = 540, 760
    out += ea.earth(ex, ey, 250, 40 + 25 * t, view_tilt=18)
    out += (f'<ellipse cx="{ex}" cy="{ey}" rx="440" ry="120" fill="none" stroke="#9FB4E8" stroke-width="4" stroke-dasharray="14 12" opacity=".55" transform="rotate(-12 {ex} {ey})"/>')
    k1, k2, k3, k4 = (pop(t, d * f, .5) for f in (.02, .27, .47, .72))
    out += text(540, 330, "¿QUÉ LE PASARÍA", 66, "#fff", sw=14, scale=k1) + text(540, 410, "A LA TIERRA?", 66, "#FFE14D", sw=14, scale=k1)
    if t > d * .27:                                                  # ¿mareas?
        wv = " ".join(f"{-60+x*4},{14*math.sin(x/3 + t*5):.1f}" for x in range(0, 31))
        out += (f'<g transform="translate(220,990) scale({k2})"><circle r="100" fill="#0B3A78" stroke="#7CD3FF" stroke-width="7"/>'
                f'<polyline points="{wv}" fill="none" stroke="#7CD3FF" stroke-width="10" stroke-linecap="round" transform="translate(0,-10)"/>'
                f'<polyline points="{wv}" fill="none" stroke="#4DB8FF" stroke-width="10" stroke-linecap="round" transform="translate(0,30)"/></g>')
        out += text(220, 1130, "¿MAREAS?", 40, "#CFF1FF", sw=9, scale=k2)
    if t > d * .47:                                                  # ¿vida?
        sway = 6 * math.sin(t * 3)
        out += (f'<g transform="translate(860,990) scale({k3})"><circle r="100" fill="#0F3F2A" stroke="#7CF0B3" stroke-width="7"/>'
                f'<path d="M0,60 Q{-10+sway},0 0,-60" fill="none" stroke="#2FBF71" stroke-width="9" stroke-linecap="round"/>'
                f'<path d="M0,10 Q-52,-6 -58,-46 Q-6,-44 0,10 Z" fill="#35E08A"/><path d="M0,-10 Q50,-26 56,-64 Q4,-60 0,-10 Z" fill="#7CF0B3"/></g>')
        out += text(860, 1130, "¿VIDA?", 40, "#CFFFE5", sw=9, scale=k3)
    if t > d * .72:
        out += text(540, 1230, "MÁS SORPRENDENTE", 52, "#FFE14D", sw=12, scale=k4) + text(540, 1288, "DE LO QUE IMAGINAS", 52, "#FFE14D", sw=12, scale=k4)
    return out


# ------------------------------------------------------------------ 3. la Luna desaparece
@scene
def scene_vanish(t, d):
    tv = d * .24
    out = space(t)
    ex, ey = 540, 820
    out += ea.earth(ex, ey, 230, 30 + 22 * t, view_tilt=18)
    orb = lambda: (f'<ellipse cx="{ex}" cy="{ey}" rx="440" ry="130" fill="none" stroke="#9FB4E8" stroke-width="4" stroke-dasharray="14 12" opacity=".6" transform="rotate(-12 {ex} {ey})"/>')
    out = out.replace(ea.earth(ex, ey, 230, 30 + 22 * t, view_tilt=18), orb() + ea.earth(ex, ey, 230, 30 + 22 * t, view_tilt=18))
    th = math.radians(200 + 30 * min(t, tv))
    ang = math.radians(-12)
    mx, my = 440 * math.cos(th), 130 * math.sin(th)
    px, py = ex + mx * math.cos(ang) - my * math.sin(ang), ey + mx * math.sin(ang) + my * math.cos(ang)
    if t < tv:
        out += mn.moon(px, py, 62, glow=.6)
    else:
        tau = t - tv
        if tau < .5:
            out += mn.moon(px, py, 62 * (1 - tau / .5), glow=.4 * (1 - tau / .5), op=1 - tau / .5)
        out += vanish_fx(int(px), int(py), 62, tau)
        if tau > .6:
            out += f'<text x="{px:.0f}" y="{py+14:.0f}" text-anchor="middle" font-family="DejaVu Sans" font-weight="bold" font-size="46" fill="#9FB4E8" opacity="{.5+.4*math.sin(t*4):.2f}">?</text>'
    out += pill(540, 190, 760, "SITUACIÓN HIPOTÉTICA", "#10305F", "#7CD3FF", "#CFF1FF", 40, pop(t, 0, .5))
    if t > d * .5:
        out += text(540, 1130, "LA TIERRA NO SE DESTRUIRÍA DE GOLPE", 38, "#fff", sw=9, scale=pop(t, d * .5, .5))
    if t > d * .75:
        out += text(540, 1190, "LOS CAMBIOS LLEGAN POCO A POCO", 38, "#FFE14D", sw=9, scale=pop(t, d * .75, .5))
        a = prog(t, d * .75, d * .98)
        out += f'<rect x="240" y="1235" width="600" height="14" rx="7" fill="#2B3A6E"/><rect x="240" y="1235" width="{600*a:.0f}" height="14" rx="7" fill="#7CD3FF"/>'
    return out


# ------------------------------------------------------------------ 4. mareas (costa)
@scene
def scene_tides(t, d):
    T = 4.2
    lvl = math.sin(2 * math.pi * t / T - 1.2)
    y0 = 1010 - 95 * lvl
    out = nsky(t, 70)
    out += mn.moon(190, 330, 120, glow=1.0)
    # gravedad: líneas curvas de la Luna hacia el mar
    for i in range(5):
        ph = (t * .7 + i * .2) % 1
        x = lerp(250, 360 + i * 90, ph); y = lerp(420, y0 - 20, ph)
        out += f'<circle cx="{x:.0f}" cy="{y:.0f}" r="7" fill="#CFE0FF" opacity="{.8*math.sin(math.pi*ph):.2f}"/>'
    out += text(540, 190, "LAS MAREAS", 80, "#fff", sw=15, scale=pop(t, 0, .5))
    # playa y mar
    out += '<path d="M560,1130 Q760,1060 1100,1000 L1100,2000 L560,2000 Z" fill="#3B3358"/><path d="M560,1130 Q760,1060 1100,1000 L1100,1040 Q760,1100 560,1170 Z" fill="#6A5C94"/>'
    pts = " ".join(f"{x},{oc.wave_y(x, t, y0, 9):.1f}" for x in range(-60, 1141, 18))
    out += f'<polygon points="{pts} 1140,2000 -60,2000" fill="#1E6FB8" opacity=".92"/><polyline points="{pts}" fill="none" stroke="#CFE8FF" stroke-width="6" opacity=".8"/>'
    out += oc.ship_g(260, oc.wave_y(260, t, y0, 9) + 4, .2, 2 * math.sin(t * 2), oc.ship_exterior())
    # regla de marea
    out += '<rect x="650" y="880" width="30" height="330" fill="#E8D8B0" stroke="#4A2F1B" stroke-width="4"/>'
    for k in range(7):
        out += f'<rect x="{650}" y="{890+k*48}" width="{22 if k%2==0 else 14}" height="4" fill="#4A2F1B"/>'
    out += f'<polygon points="700,{y0:.0f} 740,{y0-16:.0f} 740,{y0+16:.0f}" fill="#FFE14D" stroke="#7A5A00" stroke-width="3"/>'
    hi = lvl > .75; lo = lvl < -.75
    if hi:
        out += pill(840, 800, 330, "MAREA ALTA", "#10305F", "#7CD3FF", "#CFF1FF", 34)
    if lo:
        out += pill(840, 800, 330, "MAREA BAJA", "#4A2F1B", "#FFE14D", "#FFE14D", 34)
    # cangrejo en la orilla
    cx = 880 + 60 * math.sin(t * .8)
    out += (f'<g transform="translate({cx:.0f},1075)"><ellipse rx="26" ry="16" fill="#E4572E"/><circle cx="-12" cy="-16" r="5" fill="#fff"/><circle cx="12" cy="-16" r="5" fill="#fff"/>'
            '<line x1="-26" y1="-4" x2="-44" y2="-18" stroke="#E4572E" stroke-width="6"/><line x1="26" y1="-4" x2="44" y2="-18" stroke="#E4572E" stroke-width="6"/></g>')
    if t > d * .45:
        out += pill(540, 1230, 880, "LA LUNA TIRA DEL AGUA CON SU GRAVEDAD", "#0B1030", "#FFE14D", "#FFE14D", 28, pop(t, d * .45, .4))
    return out


# ------------------------------------------------------------------ 5. mareas: Luna y Sol
@scene
def scene_tides2(t, d):
    tv = d * .34
    k = smooth(prog(t, tv + .3, tv + 2.0))
    out = space(t)
    cx, cy, R = 540, 800, 185
    th_m, th_s = 0.0, math.radians(-150)
    am = .30 * (1 - k); a_s = .13
    pts = []
    for i in range(121):
        th = i / 120 * 2 * math.pi
        rr = R * (1.22 + am * math.cos(2 * (th - th_m)) + a_s * math.cos(2 * (th - th_s)))
        pts.append(f"{cx + rr*math.cos(th):.1f},{cy + rr*math.sin(th):.1f}")
    out += f'<polygon points="{" ".join(pts)}" fill="#2E9BFF" opacity=".85" stroke="#CFF1FF" stroke-width="5"/>'
    out += ea.earth(cx, cy, R, 20 + 20 * t, view_tilt=90 * 0 + 60)
    # Sol (arriba-izquierda) y Luna (derecha)
    sx, sy = 170, 320
    out += f'<circle cx="{sx}" cy="{sy}" r="230" fill="url(#sun)"/><circle cx="{sx}" cy="{sy}" r="80" fill="#FFE48A"/>'
    out += pill(sx + 20, sy + 140, 160, "SOL", "#4A3A05", "#FFE14D", "#FFE14D", 30)
    if t < tv:
        out += mn.moon(900, cy, 80, glow=.8) + text(900, cy + 130, "LUNA", 32, "#fff", sw=8)
    else:
        tau = t - tv
        if tau < .5:
            out += mn.moon(900, cy, 80 * (1 - tau / .5), glow=.5 * (1 - tau / .5), op=1 - tau / .5)
        out += vanish_fx(900, cy, 80, tau)
    out += text(540, 190, "MAREAS: LUNA Y SOL", 62, "#fff", sw=13, scale=pop(t, 0, .5))
    if t > tv + 1.8:
        out += text(540, 1130, "MAREAS MUCHO MÁS DÉBILES", 46, "#FFE14D", sw=11, scale=pop(t, tv + 1.8, .5))
        out += text(540, 1190, "pero no desaparecen: el Sol sigue", 34, "#fff", sw=8, opacity=prog(t, tv + 2.3, tv + 2.9))
    out += text(540, 1290, "(dibujo exagerado, no está a escala)", 26, "#9FB4E8", sw=0)
    return out


# ------------------------------------------------------------------ 6. noches oscuras: bosque
@scene
def scene_forest(t, d):
    tv = d * .36
    on = t < tv
    tau = t - tv
    out = nsky(t, 60)
    if on:
        out += mn.moon(780, 330, 150, glow=1.0)
    elif tau < .5:
        out += mn.moon(780, 330, 150 * (1 - tau / .5), glow=1 - tau / .5, op=1 - tau / .5)
    out += vanish_fx(780, 330, 150, tau)
    # bosque en capas
    out += hills_night(0)
    rnd = random.Random(3)
    for layer_i, (base, col, sc) in enumerate(((1130, "#0F2A3F", .8), (1230, "#0A1D30", 1.1))):
        for k in range(9):
            x = 60 + k * 125 + 30 * layer_i + 5 * math.sin(t * 1.3 + k)
            h = 220 * sc
            out += (f'<polygon points="{x},{base-h} {x-60*sc},{base-h*.45} {x+60*sc},{base-h*.45}" fill="{col}"/>'
                    f'<polygon points="{x},{base-h*.7} {x-80*sc},{base} {x+80*sc},{base}" fill="{col}"/>')
    # luz de luna sobre el claro
    if on:
        out += '<polygon points="640,380 900,380 1000,1240 520,1240" fill="#CFE0FF" opacity=".10"/>'
    # rama con búho, zorro caminando, luciérnagas
    out += '<rect x="-20" y="620" width="520" height="22" rx="10" fill="#3B2A1A"/>'
    out += mn.owl(300, 622, 1.2, t, look=math.sin(t * .8))
    fx = lerp(-120, 1200, prog(t, 0, d * .95))
    out += mn.fox(fx, 1215, .8, t)
    if not on:                                                      # ojos que brillan en la oscuridad
        out += f'<g opacity="{smooth(prog(tau,0,.8)):.2f}"><circle cx="{fx+95:.0f}" cy="1150" r="6" fill="#FFE14D"/><circle cx="{fx+70:.0f}" cy="1150" r="6" fill="#FFE14D"/></g>'
    for i in range(14):
        x = (i * 83 + 40 * math.sin(t * .9 + i)) % 1100; y = 760 + (i * 41) % 380 + 30 * math.sin(t * 1.2 + i * 2)
        a = .4 + .6 * abs(math.sin(t * 2.2 + i))
        out += f'<circle cx="{x:.0f}" cy="{y:.0f}" r="14" fill="url(#glowY)" opacity="{a:.2f}"/><circle cx="{x:.0f}" cy="{y:.0f}" r="3.5" fill="#FFFBD1"/>'
    dark = 0 if on else smooth(prog(tau, 0, .8))
    out += f'<rect width="1080" height="1920" fill="#00030f" opacity="{.5*dark:.2f}"/>'
    out += text(540, 190, "NOCHES MÁS OSCURAS", 64, "#fff", sw=13, scale=pop(t, 0, .5))
    for i, lab in enumerate(("ORIENTARSE", "CAZAR", "ESCONDERSE")):
        if t > d * (.5 + .13 * i):
            out += pill(540, 1000 + i * 82 if False else 1110 + i * 0, 10, "", "#000", "#000", "#000", 1, 0.001) if False else ""
    if t > d * .5:
        labs = ["ORIENTARSE", "CAZAR", "ESCONDERSE"]
        for i, lab in enumerate(labs):
            if t > d * (.5 + .12 * i):
                out += pill(200 + i * 340, 1290 - 40, 310, lab, "#0B1030", "#FFE14D", "#FFE14D", 28, pop(t, d * (.5 + .12 * i), .4))
    return out


# ------------------------------------------------------------------ 7. arrecife (sincronía con la Luna)
@scene
def scene_reef(t, d):
    tv = d * .5
    on = t < tv
    tau = t - tv
    out = nsky(t, 50)
    out += mn.moon(870, 250, 100, glow=1.0, op=(1.0 if on else max(0, 1 - tau / .5)))
    out += vanish_fx(870, 250, 100, tau)
    y0 = 520
    pts = " ".join(f"{x},{oc.wave_y(x, t, y0, 8):.1f}" for x in range(-60, 1141, 18))
    out += f'<polygon points="{pts} 1140,2000 -60,2000" fill="url(#seaDeep)"/><polyline points="{pts}" fill="none" stroke="#CFE8FF" stroke-width="6" opacity=".8"/>'
    for i in range(4):
        x = 130 + i * 260
        out += f'<polygon points="{x},{y0} {x+70},{y0} {x+190},1250 {x+40},1250" fill="#fff" opacity="{.05+.03*math.sin(t*1.4+i):.2f}"/>'
    out += '<path d="M-30,1250 Q300,1190 600,1240 T1130,1220 L1130,2000 L-30,2000 Z" fill="url(#sand)"/>'
    # corales
    cols = ["#FF6B9D", "#FFA94D", "#B07CFF", "#FF6B6B"]
    for i, x in enumerate((120, 330, 560, 790, 980)):
        c = cols[i % 4]
        for k in range(5):
            a = -70 + k * 35 + 4 * math.sin(t * 1.5 + i + k)
            L = 120 + 30 * ((i + k) % 3)
            x2, y2 = x + L * math.sin(math.radians(a)) * .6, 1235 - L * math.cos(math.radians(a))
            out += f'<line x1="{x}" y1="1240" x2="{x2:.0f}" y2="{y2:.0f}" stroke="{c}" stroke-width="22" stroke-linecap="round"/><circle cx="{x2:.0f}" cy="{y2:.0f}" r="17" fill="{c}"/>'
    # desove: sincronizado con la luna, o disperso y escaso sin ella
    rnd = random.Random(9)
    for i in range(70):
        sx = rnd.choice((120, 330, 560, 790, 980)) + rnd.uniform(-60, 60)
        speed = rnd.uniform(90, 160)
        if on:
            ph = ((t * speed / 700) + (i % 7) * .02) % 1
            act = prog(t, d * .12, d * .2)
            sx2 = sx + 12 * math.sin(t * 2 + i)
        else:
            if i % 5:
                continue
            ph = ((t * speed / 900) + i * .13) % 1
            act = 1.0
            sx2 = sx + 90 * math.sin(i) * ph
        y = 1200 - ph * 640
        out += f'<circle cx="{sx2:.0f}" cy="{y:.0f}" r="{5 + (i % 3)*2}" fill="#FFB3D1" opacity="{act*.9*math.sin(math.pi*ph):.2f}"/>'
    for i in range(7):                                              # peces
        x = (i * 190 + 70 * t * (1 + i % 2)) % 1300 - 100; y = 760 + (i * 97) % 380
        out += (f'<g transform="translate({x:.0f},{y + 14*math.sin(t*2+i):.0f})"><ellipse rx="30" ry="14" fill="#FFD43B"/><polygon points="-28,0 -50,-14 -50,14" fill="#FFD43B"/><circle cx="16" cy="-3" r="3.5" fill="#111"/></g>')
    out += text(540, 190, "EN EL MAR", 78, "#fff", sw=14, scale=pop(t, 0, .5))
    if on and t > d * .22:
        out += pill(540, 1330 - 60, 720, "LOS CORALES SE SINCRONIZAN", "#0F3F2A", "#7CF0B3", "#CFFFE5", 32, pop(t, d * .22, .4))
    if not on and tau > .8:
        out += pill(540, 1330 - 60, 760, "SIN LA SEÑAL, SE DESORDENA", "#4A1020", "#FF4D6D", "#FF8FA3", 32, pop(t, tv + .8, .4))
    return out


# ------------------------------------------------------------------ 8. inclinación del eje
@scene
def scene_axis(t, d):
    out = space(t)
    R = 190
    ts = d * .18
    # izquierda: con Luna (casi estable); derecha: sin Luna (puede variar mucho)
    tilt_l = 23.4 + 1.2 * math.sin(t * 1.5)
    tilt_r = 23.4 + 26 * math.sin(t * .8) * smooth(prog(t, d * .35, d * .6)) + 2 * math.sin(t * 1.5) * (1 - smooth(prog(t, d * .35, d * .6)))
    for (cx, tl, lab, col, moon_on) in ((290, tilt_l, "CON LUNA", "#7CF0B3", True), (790, tilt_r, "SIN LUNA", "#FF8FA3", False)):
        cy = 700
        out += ea.earth(cx, cy, R, 50 * t, view_tilt=0, axis_tilt=-round(tl * 2) / 2)
        a = math.radians(tl)
        out += (f'<line x1="{cx - 290*math.sin(a):.0f}" y1="{cy - 290*math.cos(a):.0f}" x2="{cx + 290*math.sin(a):.0f}" y2="{cy + 290*math.cos(a):.0f}" stroke="#FFE14D" stroke-width="6" stroke-dasharray="14 10"/>'
                f'<circle cx="{cx - 290*math.sin(a):.0f}" cy="{cy - 290*math.cos(a):.0f}" r="12" fill="#FFE14D"/>')
        out += f'<line x1="{cx}" y1="{cy-300}" x2="{cx}" y2="{cy+300}" stroke="#fff" stroke-width="2" opacity=".35"/>'
        out += pill(cx, 1050, 340, lab, "#0B1030", col, col, 34)
        out += text(cx, 1135, f"{tl:.0f}°".replace(".", ","), 52, "#fff", sw=10)
        if moon_on:
            out += mn.moon(cx + 150, 420, 46, glow=.5)
    out += text(540, 190, "EL EJE DE LA TIERRA", 62, "#fff", sw=13, scale=pop(t, 0, .5))
    out += text(540, 270, "su inclinación hoy: 23,4°", 34, "#CFF1FF", sw=8, opacity=prog(t, .8, 1.3))
    if t > d * .4:
        a = pop(t, d * .4, .4)
        out += pill(540, 1235, 900, "DURANTE MILLONES DE AÑOS…", "#3A2A0A", "#FFE14D", "#FFE14D", 34, a)
        out += text(540, 1270 - 200 + 0, "", 1)
    if t > d * .62:
        out += text(540, 1090 - 40, "podría variar mucho más", 36, "#FFD2DA", sw=8, opacity=prog(t, d * .62, d * .62 + .5)) if False else ""
    return out


# ------------------------------------------------------------------ 9. línea de tiempo
@scene
def scene_timeline(t, d):
    out = '<rect width="1080" height="1920" fill="url(#blueprint)"/>'
    out += text(540, 190, "¿QUÉ CAMBIARÍA Y CUÁNDO?", 60, "#fff", sw=13, scale=pop(t, 0, .5))
    y = 820
    xs = (180, 540, 900)
    out += f'<line x1="90" y1="{y}" x2="990" y2="{y}" stroke="#9FB4E8" stroke-width="12" stroke-linecap="round"/>'
    prog_x = lerp(90, 990, prog(t, .4, d * .92))
    out += f'<line x1="90" y1="{y}" x2="{prog_x:.0f}" y2="{y}" stroke="#FFE14D" stroke-width="12" stroke-linecap="round"/><circle cx="{prog_x:.0f}" cy="{y}" r="22" fill="#FFE14D" stroke="#fff" stroke-width="5"/>'
    items = [("AL INSTANTE", "noches más oscuras", "mareas más débiles", "#7CD3FF", .12), ("CON EL TIEMPO", "cambian los", "ecosistemas", "#7CF0B3", .42), ("MILLONES DE AÑOS", "clima menos", "estable", "#FF8FA3", .68)]
    for i, (lab, l1, l2, col, tstart) in enumerate(items):
        x = xs[i]
        k = pop(t, d * tstart, .5)
        out += f'<circle cx="{x}" cy="{y}" r="{30*k:.0f}" fill="#0B1030" stroke="{col}" stroke-width="8"/>'
        out += f'<g transform="translate({x},{y-230}) scale({k*1.35})">'
        if i == 0:                                                  # luna apagada + marea
            out += '<circle r="64" fill="#0B1030" stroke="#7CD3FF" stroke-width="6"/><circle r="40" fill="none" stroke="#5B6B8C" stroke-width="5" stroke-dasharray="8 8"/>'
            out += "".join(f'<polyline points="-44,{10+14*j} -22,{2+14*j+4*math.sin(t*4+j)} 0,{10+14*j} 22,{2+14*j-4*math.sin(t*4+j)} 44,{10+14*j}" fill="none" stroke="#7CD3FF" stroke-width="5" stroke-linecap="round"/>' for j in range(2))
        elif i == 1:
            sw = 5 * math.sin(t * 3)
            out += f'<circle r="64" fill="#0F3F2A" stroke="#7CF0B3" stroke-width="6"/><path d="M0,40 Q{sw},0 0,-34" fill="none" stroke="#2FBF71" stroke-width="8" stroke-linecap="round"/><path d="M0,0 Q-40,-8 -44,-38 Q-4,-34 0,0 Z" fill="#35E08A"/><path d="M0,-12 Q38,-22 42,-52 Q4,-48 0,-12 Z" fill="#7CF0B3"/>'
        else:
            out += mn.__dict__.get("noop", lambda: "")() + ea.earth(0, 0, 62, 40 * t, view_tilt=0, axis_tilt=-(23 + 22 * math.sin(t * 1.2)))
        out += '</g>'
        out += text(x, y + 104, lab, 32 if i != 2 else 26, col, sw=8, opacity=min(1, k))
        out += text(x, y + 156, l1, 32, "#fff", sw=7, opacity=min(1, k)) + text(x, y + 198, l2, 32, "#fff", sw=7, opacity=min(1, k))
    out += text(540, 1160, "(escala de tiempo no proporcional)", 28, "#9FB4E8", sw=0, opacity=prog(t, d * .7, d * .7 + .5))
    return out


# ------------------------------------------------------------------ 10. la gran revelación
@scene
def scene_reveal(t, d):
    k = ease_in_out(t / d)
    out = space(t)
    z = lerp(1.0, 1.25, k)
    cam = cam_at(z, 540, 760)
    main = ea.earth(540, 780, 300, 30 + 18 * t, view_tilt=15)
    main += (f'<ellipse cx="540" cy="780" rx="520" ry="150" fill="none" stroke="#9FB4E8" stroke-width="4" stroke-dasharray="14 12" opacity=".45" transform="rotate(-12 540 780)"/>')
    out += layer(main, cam)
    # estrella fugaz para dar vida
    sp = prog(t, d * .35, d * .55)
    if 0 < sp < 1:
        sx, sy = lerp(900, 100, sp), lerp(220, 520, sp)
        out += f'<line x1="{sx:.0f}" y1="{sy:.0f}" x2="{sx+140:.0f}" y2="{sy-60:.0f}" stroke="#fff" stroke-width="5" stroke-linecap="round" opacity="{1-sp:.2f}"/>'
    out += text(540, 190, "SIN LUNA, PERO ENTERA", 60, "#fff", sw=13, scale=pop(t, 0, .5))
    out += text(540, 1130, "NO ES UNA DESTRUCCIÓN INSTANTÁNEA", 38, "#FFE14D", sw=9, scale=pop(t, d * .22, .5))
    out += text(540, 1190, "ES UNA GRAN TRANSFORMACIÓN", 40, "#fff", sw=9, scale=pop(t, d * .5, .5))
    out += text(540, 1250, "océanos · ecosistemas · equilibrio a largo plazo", 28, "#9FD0FF", sw=7, opacity=prog(t, d * .7, d * .7 + .6))
    return out


# ------------------------------------------------------------------ 11. final + logotipo
def logo(cx, cy, s, t, op=1.0):
    ring = f'<ellipse cx="0" cy="0" rx="120" ry="38" fill="none" stroke="#7CD3FF" stroke-width="9" transform="rotate(-18)"/>'
    return (f'<g transform="translate({cx},{cy}) scale({s})" opacity="{op:.2f}">'
            '<circle r="84" fill="#0A2A66" stroke="#fff" stroke-width="8"/><circle r="66" fill="url(#neck)" opacity=".9"/>'
            '<path d="M-40,-10 Q-10,-50 30,-30 Q50,-10 20,10 Q-20,26 -40,-10 Z" fill="#35E08A" opacity=".9"/>'
            + ring +
            f'<circle cx="{120*math.cos(t*1.2):.0f}" cy="{38*math.sin(t*1.2):.0f}" r="12" fill="#E8EEFF" transform="rotate(-18)"/>'
            '<g transform="translate(0,150)">' + text(0, 0, "EXPLORA", 78, "#fff", sw=12) + text(0, 80, "CIENCIA 360", 58, "#FFE14D", sw=11) + '</g></g>')


@scene
def scene_final(t, d):
    k = ease_in_out(prog(t, 0, d * .55))
    out = space(t)
    ex, ey = 540, lerp(820, 400, smooth(prog(t, d * .62, d * .8)))
    R = lerp(330, 150, smooth(prog(t, d * .62, d * .8)))
    z = lerp(1.15, 1.0, k)
    cam = cam_at(z, 540, 820)
    out += layer(ea.earth(ex, ey, R, 20 + 16 * t, view_tilt=15) + (f'<ellipse cx="{ex}" cy="{ey}" rx="{R*1.7:.0f}" ry="{R*.5:.0f}" fill="none" stroke="#9FB4E8" stroke-width="4" stroke-dasharray="14 12" opacity=".4" transform="rotate(-12 {ex} {ey})"/>'), cam)
    if t < d * .6:
        out += text(540, 190, "SU INFLUENCIA", 66, "#fff", sw=14, scale=pop(t, .4, .5)) + text(540, 275, "LLEGA HASTA LOS OCÉANOS", 50, "#FFE14D", sw=12, scale=pop(t, 1.2, .5))
        out += text(540, 1190, "y ayuda a mantener estable al planeta", 36, "#fff", sw=9, opacity=prog(t, d * .3, d * .3 + .6))
    if t > d * .72:
        k2 = pop(t, d * .72, .7)
        out += logo(540, 800, k2 * 1.5, t, min(1, k2))
    return out


SFX = {
    "hook": [("hoot", lambda d: .5), ("vanish", lambda d: d * .46), ("shimmer", lambda d: d * .8)],
    "questions": [("pop", lambda d: .1), ("pop", lambda d: d * .27), ("pop", lambda d: d * .47), ("shimmer", lambda d: d * .72)],
    "vanish": [("vanish", lambda d: d * .24), ("pop", lambda d: d * .5)],
    "tides": [("swell", lambda d: .3, lambda d: 1.8, 1.0), ("pop", lambda d: d * .45)],
    "tides2": [("vanish", lambda d: d * .34), ("pop", lambda d: d * .34 + 1.8)],
    "forest": [("vanish", lambda d: d * .36), ("hoot", lambda d: d * .55), ("pop", lambda d: d * .5)],
    "reef": [("swell", lambda d: .2, lambda d: 1.8, 1.0), ("vanish", lambda d: d * .5), ("pop", lambda d: d * .22)],
    "axis": [("pop", lambda d: d * .4)],
    "timeline": [("pop", lambda d: d * .12), ("pop", lambda d: d * .42), ("pop", lambda d: d * .68)],
    "reveal": [("pop", lambda d: d * .22), ("pop", lambda d: d * .5)],
    "final": [("pop", lambda d: .4), ("shimmer", lambda d: d * .72), ("ding", lambda d: d * .76)],
}
