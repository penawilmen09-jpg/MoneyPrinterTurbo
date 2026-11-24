"""Escenas animadas del video «palomas y cables». Cada escena = f(t, d) -> SVG.

t = segundo local de la escena, d = duración real (según la narración).
"""
import math
from .core import W, H, n, clamp, lerp, prog, smooth, ease_out, ease_in_out, ease_out_back
from .svgkit import layer, cam_at, text
from .art import world as wd
from .art import diagram as dg
from .art.pigeon import pigeon

PX = 640                      # x donde se posa la paloma
SCENES = {}


def scene(fn):
    SCENES[fn.__name__.replace("scene_", "")] = fn
    return fn


def backdrop(cam, t, sky="skyDay", city=True, stars=False, sun=True, hills=("#6DBE7B", "#4FA36A"), ccol="#5C6BA8"):
    out = layer(wd.sky(sky, t, sun=sun, stars=stars), cam, .15)
    out += layer(wd.hills(*hills), cam, .4)
    if city:
        out += layer(wd.city(col=ccol), cam, .55)
    return out


def rig_world(t, energy=True, hot=1.0, speed=300, transformer=False, nwires=3):
    return (wd.pole(transformer=transformer) +
            "".join(wd.wire(i, t, energy, speed=speed, hot=hot) for i in range(nwires)))


def pop(t, start, dur=.5):
    return ease_out_back(prog(t, start, start + dur))


# ---------------------------------------------------------------- 1. gancho
@scene
def scene_hook(t, d):
    cam = cam_at(1.0 + .22 * ease_in_out(t / d), PX - 60 * prog(t, 0, d), 620)
    out = backdrop(cam, t, "skyDusk")
    world = rig_world(t, hot=1.3, speed=420)
    world += pigeon(PX, wd.wire_y(0, PX), 1.9, t=t, expr="surprised" if t < 2.6 else "neutral")
    out += layer(world, cam)
    # destellos eléctricos de gancho
    if 0.2 < t % 1.6 < 0.5:
        out += layer(wd.bolt(300, 520, 1.6, -15, t=t), cam)
    # título (visible desde el primer instante)
    lines = [("¿POR QUÉ LAS", "#fff"), ("PALOMAS NO SE", "#fff"), ("ELECTROCUTAN?", "#FFE14D")]
    for i, (s, c) in enumerate(lines):
        k = pop(t, .05 + i * .12)
        out += text(540, 205 + i * 92, s, 80, c, sw=14, scale=max(k, .001), opacity=min(1, k * 3))
    k = pop(t, .7, .6)
    out += text(900, 790 + 12 * math.sin(t * 5), "?", 230, "#FFE14D", sw=16, scale=max(k, .001), rot=14)
    return out


# ------------------------------------------------------------ 2. alto voltaje
@scene
def scene_voltage(t, d):
    k = ease_in_out(t / d)
    cam = cam_at(1.15, lerp(300, 640, k), 700)
    out = backdrop(cam, t, "skySunset", ccol="#7C4F8E")
    world = rig_world(t, hot=1.8, speed=520, transformer=True)
    world += pigeon(PX, wd.wire_y(0, PX), 1.5, t=t, expr="neutral" if t < d * .6 else "happy")
    for i in range(3):          # chispas sobre los cables
        if (t * 3 + i * .37) % 1 < .25:
            world += wd.bolt(200 + 380 * i + 40 * math.sin(t * 3), wd.wire_y(i, 400 + 300 * i) - 70, 1.1, 10 * i - 10, t=t)
    out += layer(world, cam)
    s = pop(t, .3, .6)
    out += (f'<g transform="translate(540,300) scale({max(s,.001):.3f})">'
            '<polygon points="0,-120 130,100 -130,100" fill="#FFD21F" stroke="#1B1B2F" stroke-width="14" stroke-linejoin="round"/>'
            '<rect x="-10" y="-50" width="20" height="90" rx="8" fill="#1B1B2F"/><circle cx="0" cy="70" r="12" fill="#1B1B2F"/></g>')
    out += text(540, 510, "MILES DE VOLTIOS", 70, "#FFE14D", sw=14, scale=max(pop(t, .8, .5), .001))
    return out


# --------------------------------------------------------------- 3. circuito
@scene
def scene_circuit(t, d):
    out = '<rect width="1080" height="1920" fill="url(#blueprint)"/>' + dg.grid(t)
    x0, y0, x1, y1 = 200, 480, 880, 1000
    ts = d * .45                                   # instante en que se cierra el interruptor
    closed = t >= ts
    close_k = ease_out(prog(t, ts - .25, ts))
    col, wcol = "#EAF2FF", "#CFE3FF"
    # tramos de cable (con hueco para el interruptor)
    out += (f'<polyline points="{x0},{y0+110} {x0},{y0} {x1},{y0} {x1},{y1} {x1-200},{y1}" fill="none" stroke="{wcol}" stroke-width="12" stroke-linejoin="round"/>'
            f'<polyline points="{x0+200},{y1} {x0},{y1} {x0},{y1-110}" fill="none" stroke="{wcol}" stroke-width="12" stroke-linejoin="round"/>')
    out += dg.battery(x0, (y0 + y1) / 2, t) + dg.bulb(x1, (y0 + y1) / 2, closed, t)
    # interruptor: palanca que gira de abierto a cerrado
    sx = (x0 + x1) / 2
    ang = lerp(-38, 0, close_k)
    out += (f'<circle cx="{sx-200}" cy="{y1}" r="12" fill="{col}"/><circle cx="{sx+200}" cy="{y1}" r="12" fill="{col}"/>'
            f'<line x1="{sx-200}" y1="{y1}" x2="{sx+200}" y2="{y1}" stroke="{col}" stroke-width="12" stroke-linecap="round" '
            f'transform="rotate({ang:.1f} {sx-200} {y1})"/>')
    # electrones
    if closed:
        P = 2 * ((x1 - x0) + (y1 - y0))
        for k in range(16):
            s = (k * P / 16 + 330 * (t - ts)) % P
            ex, ey = dg.rect_point(s, x0, y0, x1, y1)
            if abs(ey - y1) < 1 and abs(ex - sx) < 195 and False:
                continue
            out += f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="17" fill="url(#glowC)"/><circle cx="{ex:.1f}" cy="{ey:.1f}" r="7" fill="#fff"/>'
    else:                                       # abierto: los electrones vibran sin avanzar; terminales pulsan
        P = 2 * ((x1 - x0) + (y1 - y0))
        for k in range(16):
            ex, ey = dg.rect_point(k * P / 16 + 22 * math.sin(t * 4 + k), x0, y0, x1, y1)
            out += f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="14" fill="url(#glowC)" opacity=".7"/><circle cx="{ex:.1f}" cy="{ey:.1f}" r="6" fill="#fff"/>'
        pr = 1 + .25 * math.sin(t * 6)
        out += (f'<circle cx="{x0+95}" cy="{(y0+y1)/2-30}" r="{60*pr:.0f}" fill="url(#glowR)" opacity=".6"/>'
                f'<circle cx="{x0+95}" cy="{(y0+y1)/2+30}" r="{60*pr:.0f}" fill="url(#glowC)" opacity=".6"/>')
    msg = "CIRCUITO CERRADO: ¡fluye la corriente!" if closed else "CIRCUITO ABIERTO: no pasa nada"
    out += text(540, 330, "CIRCUITO" if not closed else "CIRCUITO", 80, "#fff", sw=0, scale=max(pop(t, 0, .5), .001))
    out += text(540, 1160, msg, 42, "#7CF0B3" if closed else "#FF8FA3", sw=0)
    out += text(540, 1085, "Dos puntos con distinto voltaje", 40, "#9FD0FF", sw=0, opacity=prog(t, 1, 1.6))
    return out


# --------------------------------------------------------------- 4. cascada
@scene
def scene_waterfall(t, d):
    out = '<rect width="1080" height="1920" fill="url(#skyDay)"/>' + layer(wd.sky("skyDay", t, sun=False), cam_at(1, 540, 960), 1)
    out += wd.hills("#7BC88A", "#5AB071", 1250)
    ybot, hmax = 1000, 460
    xa0, xa1, xb0, xb1 = 110, 400, 680, 970
    k = ease_in_out(prog(t, d * .38, d * .78))
    hL, hR = lerp(400, 215, k), lerp(30, 215, k)
    diff = hL - hR
    # tuberías
    out += f'<rect x="{xa1-4}" y="{ybot-50}" width="{xb0-xa1+8}" height="34" fill="#9FB0C8" stroke="#6B7A92" stroke-width="5"/>'
    out += dg.tank(xa0, xa1, ybot, hmax, hL) + dg.tank(xb0, xb1, ybot, hmax, hR)
    for (bx0, bx1, lv) in ((xa0, xa1, hL), (xb0, xb1, hR)):      # burbujas y oleaje en el agua
        for j in range(6):
            by = ybot - 14 - ((t * 60 + j * 77) % max(lv - 20, 1))
            bx = bx0 + 30 + (j * 47) % (bx1 - bx0 - 60) + 8 * math.sin(t * 3 + j)
            out += f'<circle cx="{bx:.0f}" cy="{by:.0f}" r="{5+j%3*2}" fill="#E6F8FF" opacity=".6"/>'
        wy = ybot - lv
        pts = " ".join(f"{x},{wy + 4 * math.sin(t * 4 + x / 25):.1f}" for x in range(int(bx0 + 8), int(bx1 - 6), 12))
        out += f'<polyline points="{pts}" fill="none" stroke="#fff" stroke-width="5" opacity=".7"/>'
    if diff > 8:
        for j in range(7):
            px = xa1 + ((j / 7 + t * 1.3) % 1) * (xb0 - xa1)
            out += f'<circle cx="{px:.1f}" cy="{ybot-33}" r="10" fill="#BDEBFF"/>'
    # cota de altura
    if diff > 8:
        y1, y2 = ybot - hL, ybot - hR
        out += (f'<line x1="{xa1+30}" y1="{y1}" x2="{xb0-30}" y2="{y1}" stroke="#FFE14D" stroke-width="5" stroke-dasharray="14 10"/>'
                f'<line x1="{xa1+30}" y1="{y2}" x2="{xb0-30}" y2="{y2}" stroke="#FFE14D" stroke-width="5" stroke-dasharray="14 10"/>'
                f'<line x1="540" y1="{y1+6}" x2="540" y2="{y2-6}" stroke="#FF5C7A" stroke-width="8"/>'
                f'<polygon points="540,{y2-4} 524,{y2-34} 556,{y2-34}" fill="#FF5C7A"/>'
                f'<polygon points="540,{y1+4} 524,{y1+34} 556,{y1+34}" fill="#FF5C7A"/>')
    else:
        out += f'<line x1="{xa1+30}" y1="{ybot-hL}" x2="{xb0-30}" y2="{ybot-hR}" stroke="#FFE14D" stroke-width="5" stroke-dasharray="14 10"/>'
    out += text(540, 330, "COMO EL AGUA", 74, "#fff", sw=14, scale=max(pop(t, 0, .5), .001))
    lab = "DIFERENCIA = FLUJO" if diff > 8 else "SIN DIFERENCIA = SIN FLUJO"
    out += text(540, 1230, lab, 54, "#fff" if diff > 8 else "#FFE14D", sw=12)
    out += text(255, ybot + 62, "voltaje alto" if diff > 8 else "voltaje igual", 34, "#fff", sw=8)
    out += text(825, ybot + 62, "voltaje bajo" if diff > 8 else "voltaje igual", 34, "#fff", sw=8)
    return out


# ------------------------------------------------------- 5. mismo cable
def _screen(cam, x, y):
    z, fx, fy = cam
    return W / 2 + (x - fx) * z, H / 2 + (y - fy) * z


@scene
def scene_samewire(t, d):
    k = ease_in_out(t / (d * .55))
    z = lerp(1.15, 1.5, k)
    cam = cam_at(z, PX, 750 + 160 / z)
    out = backdrop(cam, t, "skyDusk")
    world = rig_world(t, hot=1.1, speed=380)
    world += pigeon(PX, wd.wire_y(0, PX), 1.9, t=t, expr="happy" if t > d * .55 else "neutral")
    out += layer(world, cam)
    fy = wd.wire_y(0, PX)
    lx, ly = _screen(cam, PX - 5 * 1.9 + 5, fy)
    rx, ry = _screen(cam, PX + 20 * 1.9, fy)
    a = prog(t, d * .22, d * .22 + .5)
    # etiquetas de voltaje en cada pata
    for (sx, sy, off) in ((lx, ly, -190), (rx, ry, 190)):
        tx = sx + off
        out += (f'<line x1="{sx:.0f}" y1="{sy:.0f}" x2="{tx:.0f}" y2="{sy+80:.0f}" stroke="#FFE14D" stroke-width="5" opacity="{a:.2f}"/>'
                f'<rect x="{tx-115:.0f}" y="{sy+70:.0f}" width="230" height="74" rx="18" fill="#1B1B2F" stroke="#FFE14D" stroke-width="5" opacity="{a:.2f}"/>'
                + text(tx, sy + 122, "10 000 V", 44, "#FFE14D", opacity=a))
    # voltímetro
    gx, gy = 540, 1230
    b = prog(t, d * .4, d * .4 + .6)
    needle = -90 + 3 * math.sin(t * 25) * 0 + 1.2 * math.sin(t * 31)
    out += (f'<g opacity="{b:.2f}"><rect x="{gx-210}" y="{gy-150}" width="420" height="230" rx="30" fill="#0F1630" stroke="#7CF0B3" stroke-width="6"/>'
            f'<path d="M{gx-140},{gy+10} A140 140 0 0 1 {gx+140},{gy+10}" fill="none" stroke="#3B4A7A" stroke-width="16"/>'
            f'<path d="M{gx-140},{gy+10} A140 140 0 0 1 {gx-122},{gy-52}" fill="none" stroke="#7CF0B3" stroke-width="16"/>'
            f'<line x1="{gx-140}" y1="{gy+10}" x2="{gx-140+10:.0f}" y2="{gy+10}" stroke="none"/>'
            f'<g transform="rotate({-62+needle*0:.1f} {gx} {gy+10})"><line x1="{gx}" y1="{gy+10}" x2="{gx}" y2="{gy-120}" stroke="#FF5C7A" stroke-width="7" stroke-linecap="round"/></g>'
            f'<circle cx="{gx}" cy="{gy+10}" r="14" fill="#fff"/></g>')
    out += f'<rect x="{gx-370}" y="{gy-212}" width="740" height="60" rx="30" fill="#0F1630" opacity="{b*.9:.2f}"/>'
    out += text(gx, gy - 170, "DIFERENCIA ENTRE PATAS: ≈ 0 V", 32, "#7CF0B3", opacity=b)
    return out


# ------------------------------------------------------ 6. camino fácil
@scene
def scene_easypath(t, d):
    out = '<rect width="1080" height="1920" fill="url(#blueprint)"/>' + dg.grid(t)
    yt, yb, xa, xb = 640, 980, 400, 700
    out += text(540, 330, "¿POR DÓNDE PASA?", 70, "#fff", scale=max(pop(t, 0, .5), .001))
    # cable (carril ancho) y rama de la paloma (carril fino)
    out += (f'<rect x="90" y="{yt-34}" width="900" height="68" rx="34" fill="#2B4C8C" stroke="#8FB8FF" stroke-width="5"/>'
            f'<polyline points="{xa},{yt+34} {xa},{yb} {xb},{yb} {xb},{yt+34}" fill="none" stroke="#8FB8FF" stroke-width="10" stroke-linejoin="round"/>')
    for k in range(14):                                   # muchísimos electrones por el cable
        ex = 90 + (k * 70 + 460 * t) % 980
        if ex < 990:
            out += f'<circle cx="{ex:.0f}" cy="{yt}" r="15" fill="url(#glowC)"/><circle cx="{ex:.0f}" cy="{yt}" r="7" fill="#fff"/>'
    # un electrón muy ocasional por la paloma
    ph = (t / 2.6) % 1
    if ph < .55:
        L1, L2, L3 = yb - yt - 34, xb - xa, yb - yt - 34
        s = ph / .55 * (L1 + L2 + L3)
        if s < L1: px, py = xa, yt + 34 + s
        elif s < L1 + L2: px, py = xa + (s - L1), yb
        else: px, py = xb, yb - (s - L1 - L2)
        out += f'<circle cx="{px:.0f}" cy="{py:.0f}" r="9" fill="url(#glowC)"/><circle cx="{px:.0f}" cy="{py:.0f}" r="4" fill="#fff"/>'
    out += pigeon(540, yb, 1.15, t=t, expr="neutral", bob=True)
    a = prog(t, d * .25, d * .25 + .5)
    out += text(540, yt - 90, "CABLE: camino fácil", 44, "#7CF0B3", sw=8, opacity=a)
    b = prog(t, d * .45, d * .45 + .5)
    out += text(540, yb + 100, "PALOMA: camino difícil", 44, "#FF8FA3", sw=8, opacity=b)
    out += text(540, yb + 160, "casi nada de corriente", 34, "#CFE3FF", sw=0, opacity=prog(t, d * .6, d * .6 + .5))
    return out


# --------------------------------------------------- 7. dos cables
RIG2 = dict(xl=130, xr=1230, ys=[640, 706], sag=110)


@scene
def scene_twowires(t, d):
    zap_t = d * .42
    shake = 10 * math.exp(-(t - zap_t) * 3) * math.sin(t * 70) if t >= zap_t else 0
    cam = cam_at(1.3, PX + shake, 740 + shake)
    out = backdrop(cam, t, "skyDark", stars=True, sun=False, ccol="#3B2F6B")
    world = wd.pole(n_arms=2, rig=RIG2)
    world += "".join(wd.wire(i, t, True, rig=RIG2, speed=420, hot=1.4) for i in range(2))
    yA = wd.wire_y(0, PX, RIG2)
    # etiquetas de voltaje
    world += text(260, yA - 70, "10 000 V", 38, "#FF8FA3", sw=8)
    world += text(260, wd.wire_y(1, 260, RIG2) + 70, "0 V", 38, "#8FC8FF", sw=8)
    # paloma: llega volando, se posa y toca el segundo cable con el ala
    fly = prog(t, 0, d * .3)
    if t < d * .3:
        bx = lerp(1250, PX, ease_out(fly))
        by = lerp(380, yA, ease_in_out(fly)) + 25 * math.sin(t * 9) * (1 - fly)
        world += pigeon(bx, by, 1.8, t=t, fly=fly < .95, wing=25 + 45 * math.sin(t * 22), tilt=-10 * (1 - fly), expr="neutral")
    else:
        touch = prog(t, d * .3, zap_t)
        wing = lerp(6, -78, smooth(touch))
        expr = "neutral" if t < zap_t else ("surprised" if t < zap_t + .7 else "dizzy")
        fall = prog(t, zap_t + 1.3, zap_t + 2.4)
        world += pigeon(PX + 140 * fall, yA + 700 * fall ** 2, 1.8, t=t, wing=wing if fall == 0 else 40 * math.sin(t * 20),
                        expr=expr, shake=(6 if zap_t <= t < zap_t + 1.2 else 0), tilt=40 * fall)
        if zap_t <= t < zap_t + 1.4:
            tipx, tipy = PX - 100, yA + 62
            for sd in range(3):
                world += wd.arc(PX + 5, yA, PX + 5, yA - 100, t, seed=sd, amp=16)      # patas->cuerpo
                world += wd.arc(PX + 5, yA - 100, tipx, tipy - 10, t, seed=sd + 7, amp=18)   # cuerpo->ala
            world += wd.arc(tipx, tipy, tipx - 10, wd.wire_y(1, tipx, RIG2), t, seed=3, amp=10)
            world += wd.starburst(tipx, tipy, 70 * ease_out(prog(t, zap_t, zap_t + .25)), t)
    out += layer(world, cam)
    if zap_t <= t < zap_t + .12:
        out += '<rect width="1080" height="1920" fill="#fff" opacity=".7"/>'
    if t > zap_t:
        s = pop(t, zap_t + .1, .5)
        out += text(540, 300, "¡DIFERENCIA DE VOLTAJE!", 56, "#FFE14D", sw=12, scale=max(s, .001))
        out += text(540, 372, "la corriente cruza el cuerpo", 38, "#fff", sw=9, opacity=prog(t, zap_t + .5, zap_t + 1))
    else:
        out += text(540, 300, "DOS CABLES A LA VEZ", 56, "#fff", sw=12, scale=max(pop(t, d * .3, .5), .001) if t > d * .3 else .001)
    if t > zap_t + 1.6:
        out += text(540, 1060, "PELIGRO", 90, "#FF4D6D", sw=16, scale=max(pop(t, zap_t + 1.6, .5), .001), rot=-4)
    return out


# ------------------------------------------------------------- 8. cierre
@scene
def scene_outro(t, d):
    k = ease_in_out(t / d)
    cam = cam_at(lerp(1.35, 1.0, k), PX, 700)
    out = backdrop(cam, t, "skySunset", ccol="#7C4F8E")
    world = rig_world(t, hot=1.0, speed=300)
    leave = prog(t, d - 1.6, d - .2)
    if leave == 0:
        world += pigeon(PX, wd.wire_y(0, PX), 1.7, t=t, expr="happy")
    else:
        e = ease_in_out(leave)
        world += pigeon(PX + 700 * e, wd.wire_y(0, PX) - 380 * e, 1.7, t=t, fly=True, wing=30 + 50 * math.sin(t * 22),
                        expr="happy", tilt=-18 * e)
    out += layer(world, cam)
    s1, s2, s3 = pop(t, .9, .5), pop(t, 1.0, .5), pop(t, d * .52, .5)
    out += text(540, 250, "NO ES INMUNE", 84, "#fff", sw=16, scale=max(s1, .001))
    out += text(540, 345, "NO CIERRA EL CIRCUITO", 56, "#FFE14D", sw=12, scale=max(s2, .001))
    pulse = 1 + .05 * math.sin(t * 8)
    out += (f'<g transform="translate(540,1060) scale({max(s3,.001)*pulse:.3f})"><rect x="-290" y="-62" width="580" height="124" rx="62" fill="#FF3D6B" stroke="#fff" stroke-width="8"/>'
            + text(0, 22, "¿LO SABÍAS? SÍGUEME", 44, "#fff") + '</g>')
    return out


# efectos de sonido sintetizados: nombre -> [(sfx, segundo_local(d))]
SFX = {
    "hook": [("pop", lambda d: .05), ("pop", lambda d: .7)],
    "voltage": [("pop", lambda d: .3), ("zap", lambda d: .9)],
    "circuit": [("click", lambda d: d * .45)],
    "twowires": [("zap", lambda d: d * .42), ("pop", lambda d: d * .42 + .1)],
    "outro": [("pop", lambda d: .9), ("ding", lambda d: d * .52)],
}
