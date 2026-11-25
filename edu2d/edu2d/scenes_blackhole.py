"""Video 8 · Explora Ciencia 360 — ¿Qué pasaría si cayeras dentro de un agujero negro?"""
import math
import random
from .core import W, H, n, clamp, lerp, prog, smooth, ease_out, ease_in_out, ease_out_back
from .svgkit import layer, cam_at, text
from .art import blackhole as bh
from .art import heli as hl
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


def ripples(cx, cy, R, t, n_=3, period=1.6):
    out = ""
    for i in range(n_):
        k = ((t / period) + i / n_) % 1
        out += f'<circle cx="{cx}" cy="{cy}" r="{R*(1.2+3.2*k):.0f}" fill="none" stroke="#9FB4FF" stroke-width="{6*(1-k)+1:.1f}" opacity="{.5*(1-k):.2f}"/>'
    return out


# ------------------------------------------------------------------ 1. gancho
@scene
def scene_hook(t, d):
    appear = ease_out(prog(t, 0, 1.0))
    zoom = 1.0 + .75 * ease_in_out(t / d)
    cx, cy = 540, 640
    R = 170 * (.35 + .65 * appear) * zoom
    sh = 6 * math.exp(-t * 1.5) * math.sin(t * 60)
    out = bh.space_bg(t, (0, 0))
    out += bh.lensed_stars(t, cx + sh, cy, 170, zoom=1.0 / zoom * 1.0 + .0, nstars=140, flow=t * .35)
    out += ripples(cx, cy, R, t)
    out += bh.black_hole(cx + sh, cy, R, t, uid="h", glow=appear)
    # el astronauta cae hacia el agujero negro
    k = ease_in_out(t / d)
    ax, ay = 540 + 22 * math.sin(t * 1.3), lerp(1150, 920, k)
    out += bh.astronaut(ax, ay, lerp(1.05, .8, k), t, rot=8 * math.sin(t * .9) + 6 * k, expr="scared" if t > .5 else "calm")
    # estela de succión
    for i in range(5):
        out += f'<line x1="{ax-10+i*5:.0f}" y1="{ay-150-i*34:.0f}" x2="{ax-10+i*5:.0f}" y2="{ay-185-i*34:.0f}" stroke="#9FB4FF" stroke-width="4" stroke-linecap="round" opacity="{.5-i*.09:.2f}"/>'
    if t < d * .62:
        out += text(540, 190, "¡ESTÁS CAYENDO!", 90, "#fff", sw=16, scale=pop(t, .08, .45) * (1 + .02 * math.sin(t * 25)))
        out += text(540, 285, "HACIA UN AGUJERO NEGRO", 52, "#FFB347", sw=12, scale=pop(t, .3, .45))
    else:
        out += text(540, 190, "¡TE CONVERTIRÍAS EN", 62, "#fff", sw=14, scale=pop(t, d * .62, .45))
        out += text(540, 290, "UN ESPAGUETI HUMANO!", 66, "#FFE14D", sw=15, scale=pop(t, d * .62 + .15, .45))
    return out


# ------------------------------------------------------------------ 2. la atracción
@scene
def scene_pull(t, d):
    k = ease_in(prog(t, 0, d * .95)) if False else (prog(t, 0, d * .95) ** 1.7)
    cam = cam_at(lerp(1.0, 1.2, ease_in_out(t / d)), 700, 760)
    cx, cy, R = 760, 700, 200
    out = layer(bh.space_bg(t, (0, 0)), cam, .3)
    main = bh.lensed_stars(t, cx, cy, R, nstars=130, flow=t * .12)
    main += ripples(cx, cy, R, t, period=2.2)
    main += bh.black_hole(cx, cy, R, t, uid="p")
    # recorrido en espiral hacia el agujero negro
    ax = lerp(220, 560, k); ay = lerp(1010, 790, k) + 36 * math.sin(k * 5) * (1 - k)
    sc = lerp(1.0, .62, k)
    main += "".join(f'<circle cx="{ax-70-i*26:.0f}" cy="{ay+20+i*10:.0f}" r="{4}" fill="#9FB4FF" opacity="{.5-i*.08:.2f}"/>' for i in range(5))
    main += bh.astronaut(ax, ay, sc, t, rot=lerp(-30, 40, k), stretch=1 + .25 * k, squeeze=1 - .08 * k)
    # fotón que intenta escapar y es doblado de vuelta
    tu = prog(t, d * .55, d * .92)
    if 0 < tu < 1:
        pts = []
        for j in range(0, int(tu * 40) + 1):
            u = j / 40
            r = R * (1.06 + .95 * math.sin(math.pi * u)); th = math.radians(-60 + 230 * u)
            pts.append((cx + r * math.cos(th), cy + r * math.sin(th)))
        main += f'<polyline points="{" ".join(f"{x:.0f},{y:.0f}" for x, y in pts)}" fill="none" stroke="#FFF3A8" stroke-width="7" stroke-linecap="round" opacity=".85"/>'
        main += f'<circle cx="{pts[-1][0]:.0f}" cy="{pts[-1][1]:.0f}" r="13" fill="#FFFBD1"/><circle cx="{pts[-1][0]:.0f}" cy="{pts[-1][1]:.0f}" r="30" fill="url(#glowY)"/>'
    out += layer(main, cam)
    out += text(540, 190, "LA ATRACCIÓN", 78, "#fff", sw=14, scale=pop(t, 0, .5))
    # medidor de gravedad
    g = clamp((k ** 1.2))
    out += f'<rect x="120" y="1195" width="840" height="26" rx="13" fill="#1A1F44" stroke="#9FB4FF" stroke-width="4"/><rect x="124" y="1199" width="{832*g:.0f}" height="18" rx="9" fill="{"#7CF0B3" if g<.5 else "#FFB347" if g<.8 else "#FF4D6D"}"/>'
    out += text(540, 1170, "INTENSIDAD DE LA GRAVEDAD", 30, "#CFE0FF", sw=8)
    if tu > 0:
        out += text(540, 290, "NI LA LUZ PUEDE ESCAPAR", 46, "#FFF3A8", sw=11, scale=pop(t, d * .55, .5))
    return out


# ------------------------------------------------------------------ 3. horizonte de sucesos
@scene
def scene_horizon(t, d):
    tc = d * .5
    cx, cy, R = 540, 720, 210
    flash = math.exp(-max(0, t - tc) * 4) if t >= tc else 0
    out = bh.space_bg(t)
    out += bh.lensed_stars(t, cx, cy, R, nstars=120, flow=t * .08)
    out += bh.black_hole(cx, cy, R, t, uid="x")
    # el horizonte de sucesos: frontera brillante
    pulse = .6 + .4 * math.sin(t * 4)
    out += (f'<circle cx="{cx}" cy="{cy}" r="{R*1.0:.0f}" fill="none" stroke="#6AA8FF" stroke-width="10" opacity="{.5+.3*pulse+flash:.2f}" stroke-dasharray="26 14" stroke-dashoffset="{-t*80:.0f}"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{R*1.0:.0f}" fill="none" stroke="#CFE0FF" stroke-width="3" opacity=".9"/>')
    # rayos de luz: afuera escapan, adentro caen
    for i in range(6):
        ph = (t * .5 + i / 6) % 1
        a = math.radians(i * 60 + 20)
        if i % 2 == 0:                                    # fuera del horizonte: escapa
            r = R * (1.15 + 2.2 * ph)
            out += f'<circle cx="{cx + r*math.cos(a):.0f}" cy="{cy + r*math.sin(a):.0f}" r="8" fill="#FFF3A8" opacity="{1-ph:.2f}"/>'
        else:                                              # dentro: curva y cae al centro
            r = R * (.95 - .9 * ph); aa = a + 2.5 * ph
            out += f'<circle cx="{cx + r*math.cos(aa):.0f}" cy="{cy + r*math.sin(aa):.0f}" r="7" fill="#FFB347" opacity="{1-ph*.7:.2f}"/>'
    # astronauta: cruza la frontera
    k = prog(t, 0, d * .92)
    ax = lerp(140, cx, ease_in_out(k) ** 1.2); ay = lerp(1010, cy, ease_in_out(k) ** 1.2)
    dist = math.hypot(ax - cx, ay - cy)
    inside = dist < R
    sc = lerp(1.0, .42, k)
    op = 1.0 if not inside else max(.15, dist / R)
    out += f'<g opacity="{op:.2f}">' + bh.astronaut(ax, ay, sc, t, rot=lerp(-25, 35, k), expr="scared", stretch=1 + .25 * smooth(prog(t, tc, d)), squeeze=1 - .08 * smooth(prog(t, tc, d))) + '</g>'
    # nave de rescate: intenta alejarse pero también es arrastrada
    sk = prog(t, d * .58, d * .95)
    if sk > 0:
        sx = lerp(180, 440, sk ** 1.5); sy = lerp(1170, 1010, sk ** 1.5)
        out += bh.ship(sx, sy, .55, t, rot=180, thrust=1.0)
        out += text(sx, sy - 62, "NAVE DE RESCATE", 26, "#fff", sw=7, opacity=min(1, sk * 4))
    if t >= tc:
        out += f'<circle cx="{cx}" cy="{cy}" r="{R*(1+3*(t-tc)):.0f}" fill="none" stroke="#fff" stroke-width="{max(1,14-12*(t-tc)):.1f}" opacity="{max(0,1-(t-tc)*1.2):.2f}"/>'
        if t < tc + .08:
            out += '<rect width="1080" height="1920" fill="#fff" opacity=".5"/>'
    out += text(540, 190, "EL PUNTO SIN RETORNO", 66, "#fff", sw=14, scale=pop(t, 0, .5))
    out += pill(540, 1030 + 160 * 0, 10, "", "#000", "#000", "#000", 1, 0.001) if False else ""
    out += f'<line x1="{cx + R*.72:.0f}" y1="{cy - R*.72:.0f}" x2="800" y2="430" stroke="#6AA8FF" stroke-width="4" opacity="{min(1,pop(t,.6,.4)):.2f}"/>'
    out += pill(760, 400, 520, "HORIZONTE DE SUCESOS", "#0B1B4A", "#6AA8FF", "#CFE0FF", 30, pop(t, .6, .45))
    if t > tc + .3:
        out += text(540, 1285, "SIN VUELTA ATRÁS", 56, "#FF8FA3", sw=12, scale=pop(t, tc + .3, .5))
    return out


# ------------------------------------------------------------------ 4. espaguetificación
@scene
def scene_stretch(t, d):
    k = smooth(prog(t, d * .3, d * .88))
    st = 1 + 1.7 * k
    sq = lerp(1.0, .62, k)
    cx, cy, R = 540, 1580, 360
    out = bh.space_bg(t)
    out += bh.lensed_stars(t, cx, cy, R, nstars=110, flow=t * .1)
    out += bh.black_hole(cx, cy, R, t, tilt=.22, uid="s")
    ax, ay, s = 540, 780, .85
    top = ay - 180 * st * s; bot = ay + 140 * st * s
    # líneas de tensión
    if k > .05:
        for sx in (-1, 1):
            out += f'<line x1="{ax + sx*(70*sq*s+16):.0f}" y1="{top+30:.0f}" x2="{ax + sx*(70*sq*s+16):.0f}" y2="{bot-10:.0f}" stroke="#FFB347" stroke-width="4" stroke-dasharray="14 12" opacity="{.4+.4*k:.2f}"/>'
    out += bh.astronaut(ax, ay, s, t, rot=0, stretch=st, squeeze=sq, expr="scared", drift=False)
    # fuerzas de marea: más en los pies que en la cabeza
    a = pop(t, d * .2, .5)
    if t > d * .2:
        out += (hl.arrow(ax + 150, top + 20, ax + 150, top + 20 + 70, "#7CF0B3", 14, 34) + pill(ax + 270, top + 20, 330, "CABEZA: TIRA MENOS", "#0F3F2A", "#7CF0B3", "#CFFFE5", 22, min(1, a)))
        out += (hl.arrow(ax + 150, bot - 160, ax + 150, bot - 160 + 190, "#FF4D6D", 22, 50) + pill(ax + 262, bot - 70, 360, "PIES: TIRA MUCHO MÁS", "#4A1020", "#FF4D6D", "#FFD2DA", 22, min(1, a)))
    if t < d * .74:
        out += text(540, 190, "LA GRAVEDAD NO TIRA", 58, "#fff", sw=13, scale=pop(t, 0, .5)) + text(540, 262, "IGUAL EN TODO TU CUERPO", 46, "#FFB347", sw=11, scale=pop(t, .25, .5))
    else:
        out += text(540, 200, "ESPAGUETIFICACIÓN", 66, "#FFE14D", sw=14, scale=pop(t, d * .74, .5))
        # fideo de espagueti (guiño educativo)
        pts = " ".join(f"{250 + u*14:.0f},{262 + 10*math.sin(u*.9 + t*5):.1f}" for u in range(0, 41))
        out += f'<polyline points="{pts}" fill="none" stroke="#FFD27A" stroke-width="12" stroke-linecap="round" opacity="{min(1,pop(t,d*.8,.4)):.2f}"/>'
    return out


# ------------------------------------------------------------------ 5. visto desde fuera
@scene
def scene_outside(t, d):
    cx, cy, R = 720, 680, 230
    tilt = .27 + .06 * math.sin(t * .5)
    tau = d * .32
    out = bh.space_bg(t, (0, 0))
    out += bh.lensed_stars(t, cx, cy, R, nstars=120, flow=0)
    out += bh.black_hole(cx, cy, R, t, tilt=tilt, uid="o")
    edge = cx - R * 1.03
    fall = math.exp(-t / tau)
    ax = edge - 330 * fall - 4
    vis = .25 + .75 * fall
    out += f'<circle cx="{ax:.0f}" cy="{cy}" r="{90*(1-fall)+10:.0f}" fill="url(#glowR)" opacity="{(1-fall)*.9:.2f}"/>'
    out += f'<g opacity="{vis:.2f}">' + bh.astronaut(ax, cy, .62, t * fall, rot=14, expr="scared") + '</g>'
    # observador lejano
    out += bh.ship(190, 940, .55, t, rot=0, thrust=.0) + text(190, 1010, "OBSERVADOR", 26, "#fff", sw=7)
    out += f'<line x1="260" y1="920" x2="{ax-20:.0f}" y2="{cy+40}" stroke="#FFF3A8" stroke-width="3" stroke-dasharray="10 10" opacity=".6"/>'
    # relojes: el del astronauta se va deteniendo (visto desde fuera)
    obs = 360 * t / 1.5 % 360
    ast = 360 / 1.5 * tau * (1 - math.exp(-t / tau)) % 360
    out += bh.clock(250, 1215, 72, obs, "#7CD3FF") + text(250, 1318, "TU RELOJ", 26, "#7CD3FF", sw=7)
    out += bh.clock(830, 1215, 72, ast, "#FF8FA3") + text(830, 1318, "SU RELOJ", 26, "#FF8FA3", sw=7)
    out += text(540, 190, "VISTO DESDE FUERA", 66, "#fff", sw=14, scale=pop(t, 0, .5))
    if t > d * .35:
        out += pill(540, 280, 800, "CADA VEZ MÁS LENTO…", "#4A1020", "#FF8FA3", "#FFD2DA", 36, pop(t, d * .35, .45))
    if t > d * .68:
        out += text(540, 1100, "se va congelando en el horizonte", 34, "#FFE14D", sw=9, opacity=prog(t, d * .68, d * .68 + .6))
    return out


# ------------------------------------------------------------------ 6. cierre y marca
@scene
def scene_close(t, d):
    tm = d * .52
    k = smooth(prog(t, tm, tm + 1.0))
    cx, cy = 540, lerp(700, 420, k)
    R = lerp(300, 120, k)
    zoom = lerp(1.15, 1.0, smooth(prog(t, 0, d * .5)))
    out = bh.space_bg(t)
    out += bh.lensed_stars(t, cx, cy, R, zoom=1.0, nstars=120, flow=0)
    out += ripples(cx, cy, R, t, period=2.4)
    out += bh.black_hole(cx, cy, R, t, tilt=.3, uid="c")
    if t < tm + .4:
        a = 1 - prog(t, tm, tm + .4)
        out += f'<g opacity="{a:.2f}">' + text(540, 190, "¿TE ATREVERÍAS A", 70, "#fff", sw=15, scale=pop(t, .05, .45)) + text(540, 285, "ACERCARTE A UN", 70, "#fff", sw=15, scale=pop(t, .25, .45)) + text(540, 380, "AGUJERO NEGRO?", 78, "#FFB347", sw=16, scale=pop(t, .45, .5)) + '</g>'
    if t > tm + .5:
        k2 = pop(t, tm + .5, .7)
        out += logo(540, 800, k2 * 1.5, t, min(1, k2))
        # aro futurista que gira alrededor del logotipo
        out += (f'<g transform="translate(540,830) rotate({t*40:.0f})" opacity="{min(1,k2)*.8:.2f}">'
                '<circle r="250" fill="none" stroke="#7CD3FF" stroke-width="4" stroke-dasharray="40 30"/><circle r="272" fill="none" stroke="#FFB347" stroke-width="3" stroke-dasharray="10 40"/></g>')
        out += text(540, 1235, "DESCUBRE MÁS MISTERIOS DEL UNIVERSO", 30, "#CFE0FF", sw=8, opacity=prog(t, tm + 1.6, tm + 2.2))
    return out


SFX = {
    "hook": [("riser", lambda d: 0, lambda d: 1.8, 1.0), ("boom", lambda d: .1), ("pop", lambda d: .08), ("vanish", lambda d: d * .62)],
    "pull": [("riser", lambda d: d * .3, lambda d: 1.8, 1.0), ("shimmer", lambda d: d * .55), ("pop", lambda d: .05)],
    "horizon": [("pop", lambda d: .05), ("pop", lambda d: .6), ("boom", lambda d: d * .5), ("vanish", lambda d: d * .5)],
    "stretch": [("pop", lambda d: .05), ("pop", lambda d: d * .2), ("riser", lambda d: d * .35, lambda d: 1.8, 1.0), ("shimmer", lambda d: d * .74)],
    "outside": [("pop", lambda d: .05), ("tick", lambda d: d * .35), ("tick", lambda d: d * .5), ("tick", lambda d: d * .68)],
    "close": [("pop", lambda d: .05), ("shimmer", lambda d: d * .55), ("ding", lambda d: d * .6)],
}
