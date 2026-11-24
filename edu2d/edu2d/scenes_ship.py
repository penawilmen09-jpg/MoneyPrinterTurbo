"""Video 2: ¿Cómo puede flotar un barco gigante?  Escenas f(t, d) -> SVG."""
import math
import random
from .core import W, H, n, clamp, lerp, prog, smooth, ease_out, ease_in_out, ease_out_back
from .svgkit import layer, cam_at, text
from .art import world as wd
from .art import ocean as oc

SCENES = {}


def scene(fn):
    SCENES[fn.__name__.replace("scene_", "")] = fn
    return fn


def pop(t, start, dur=.5):
    return max(ease_out_back(prog(t, start, start + dur)), .001)


def horizon(t, y0, col="#6E8FB8", speed=14):
    out = ""
    for i, (x0, w, h) in enumerate([(100, 300, 70), (620, 380, 100), (1000, 240, 55)]):
        x = (x0 - speed * t) % (W + 700) - 350
        out += f'<path d="M{x-w/2:.0f},{y0} Q{x:.0f},{y0-h*2} {x+w/2:.0f},{y0} Z" fill="{col}" opacity=".7"/>'
    return out


def bob(t, x=540, y0=980, A=8):
    return wave_off(t, x, y0, A), 1.6 * math.sin(t * 1.3 + x)


def wave_off(t, x, y0, A):
    return oc.wave_y(x, t, y0, A)


def pill(x, y, w, s, fill="#1B1B2F", stroke="#FFE14D", size=40, color="#FFE14D", op=1.0, label=""):
    return (f'<rect x="{x-w/2:.0f}" y="{y-34:.0f}" width="{w}" height="68" rx="34" fill="{fill}" stroke="{stroke}" stroke-width="5" opacity="{op:.2f}"/>'
            + text(x, y + size * .35, label, size, color, opacity=op))


# ----------------------------------------------------------------- 1. gancho
@scene
def scene_hook(t, d):
    y0 = 1000
    z = 1.0 + .55 * ease_in_out(prog(t, 0, d * .85))
    cam = cam_at(z, 560, 900)
    out = layer(wd.sky("skyDay", t, sun_xy=(820, 330)), cam, .15) + layer(horizon(t, y0 - 10), cam, .4)
    sy, rot = bob(t, 560, y0, 8)
    main = oc.sea_back(t, y0, 8)
    # estela
    for i in range(6):
        main += f'<ellipse cx="{150 - i*70 + 25*math.sin(t*2+i):.0f}" cy="{y0+14+i*3}" rx="{50+i*8}" ry="8" fill="#fff" opacity="{.5-i*.07:.2f}"/>'
    main += oc.ship_g(560, sy, .78, rot * 1.0, oc.ship_exterior())
    main += oc.sea_front(t, y0, 8)
    out += layer(main, cam)
    for k in range(3):
        out += oc.gull((300 + k * 260 + 40 * math.sin(t + k)) % 1100, 380 + k * 60 + 15 * math.sin(t * 2 + k), t, 1.2 - k * .2, k)
    for i, (s_, c) in enumerate([("¿CÓMO PUEDE FLOTAR", "#fff"), ("ALGO QUE PESA", "#fff"), ("MILES DE TONELADAS?", "#FFE14D")]):
        k = pop(t, .05 + i * .14)
        out += text(540, 190 + i * 88, s_, 66 if i == 2 else 74, c, sw=14, scale=k, opacity=min(1, k * 3))
    return out


# ---------------------------------------------------------------- 2. problema
@scene
def scene_problem(t, d):
    y0, floor = 720, 1235
    out = '<rect width="1080" height="1920" fill="url(#skyDay)"/>' + wd.sky("skyDay", t, sun=False, clouds=True)
    out += horizon(t, y0 - 6, speed=6)
    # cuerpo de agua con rayos de luz, fondo y algas
    water = f'<polygon points="{oc._poly(t, y0, 6, 0, H + 60)}" fill="url(#seaDeep)"/>'
    for i in range(5):
        a = .10 + .05 * math.sin(t * 1.5 + i)
        x = 120 + i * 220
        water += f'<polygon points="{x},{y0} {x+70},{y0} {x+190},{floor} {x+60},{floor}" fill="#fff" opacity="{a:.2f}"/>'
    sand = f'<path d="M-20,{floor} Q300,{floor-40} 560,{floor-10} T1100,{floor-30} L1100,{H+50} L-20,{H+50} Z" fill="url(#sand)"/>'
    weed = ""
    for bx in (180, 620, 940):
        pts = " ".join(f"{bx + 18*math.sin(t*1.7 + yy/40 + bx):.1f},{floor-8-yy}" for yy in range(0, 190, 15))
        weed += f'<polyline points="{pts}" fill="none" stroke="#2FBF71" stroke-width="12" stroke-linecap="round"/>'
    # muelle y capitán
    dock = ('<rect x="-20" y="%d" width="300" height="26" fill="#8B5A2B"/>' % (y0 - 28) +
            ''.join(f'<rect x="{x}" y="{y0-2}" width="22" height="{floor-y0}" fill="#5A3A1E" opacity=".8"/>' for x in (20, 220)))
    TF = 1.5
    t_imp, t_set = TF + .7, 5.0
    x_blk = 400
    if t < TF:
        by, rot = -200, 0
    elif t < t_imp:
        by = lerp(-200, y0 - 75, ((t - TF) / (t_imp - TF)) ** 2)
        rot = 18 * (t - TF)
    elif t < t_set:
        k = (t - t_imp) / (t_set - t_imp)
        by = lerp(y0 - 75, floor - 85, ease_out(k) * .35 + k * .65)
        rot = 3.5 + 10 * math.sin(k * 6) * (1 - k)
    else:
        by, rot = floor - 78, 4
    out_ship = ""
    # barco entra y flota a la derecha
    k = ease_out(prog(t, 5.4, 7.4))
    sx = lerp(1450, 810, k)
    sy = oc.wave_y(sx, t, y0, 6)
    out_ship = oc.ship_g(sx, sy + 8, .36, 2 * math.sin(t * 1.3), oc.ship_exterior())
    out += water + sand + weed
    # burbujas del bloque hundiéndose
    if t_imp < t < t_set + 1.5:
        for i in range(9):
            bt = (t * .8 + i * .21) % 1
            out += f'<circle cx="{x_blk + 30*math.sin(i*2+t*3):.0f}" cy="{by - 60 - bt*260:.0f}" r="{5+i%3*3}" fill="#fff" opacity="{(1-bt)*.7:.2f}"/>'
    out += oc.iron_block(x_blk, by, 150, rot)
    if t_set - .1 < t < t_set + .8:                      # polvo al tocar el fondo
        pk = prog(t, t_set - .1, t_set + .8)
        for i in range(8):
            out += f'<circle cx="{x_blk + (i-4)*28*(.4+pk):.0f}" cy="{floor-20-30*pk:.0f}" r="{16+10*pk:.0f}" fill="#E8D08A" opacity="{.6*(1-pk):.2f}"/>'
    out += out_ship
    out += f'<polygon points="{oc._poly(t, y0, 6, 0, floor)}" fill="#3AA8EA" opacity=".18"/>'
    out += f'<polyline points="{" ".join(f"{x},{oc.wave_y(x + 0, t, y0, 6):.1f}" for x in range(-60, W+61, 18))}" fill="none" stroke="#fff" stroke-width="5" opacity=".75"/>'
    # salpicadura
    if t_imp <= t < t_imp + 1.2:
        tau = t - t_imp
        rnd = random.Random(4)
        for i in range(16):
            a = math.radians(rnd.uniform(35, 145)); v = rnd.uniform(220, 520)
            px, py = x_blk + v * math.cos(a) * tau * .7, y0 - v * math.sin(a) * tau + 700 * tau * tau
            out += f'<circle cx="{px:.0f}" cy="{py:.0f}" r="{7:.0f}" fill="#CFF2FF" opacity="{max(0,1-tau/1.1):.2f}"/>'
        for r in (1, 2):
            out += f'<ellipse cx="{x_blk}" cy="{y0}" rx="{(tau*260)*r:.0f}" ry="{(tau*34)*r:.0f}" fill="none" stroke="#fff" stroke-width="5" opacity="{max(0,1-tau)*.8:.2f}"/>'
    out += dock
    expr = "surprised" if t_imp - .1 < t < t_set else "neutral"
    out += oc.captain(120, y0 - 28, .95, t, expr, "think" if t > t_set + .3 else "idle")
    out += text(540, 330, "EL PROBLEMA", 78, "#fff", sw=14, scale=pop(t, 0, .5))
    if t > t_set:
        s = pop(t, t_set, .5)
        out += text(x_blk, floor - 180, "SE HUNDE", 54, "#FF8FA3", sw=12, scale=s)
        out += text(x_blk, floor - 130, "(hierro macizo)", 34, "#fff", sw=8, opacity=prog(t, t_set + .3, t_set + .8))
    if t > 7.4:
        s = pop(t, 7.4, .5)
        out += text(810, y0 - 260, "¡FLOTA!", 60, "#7CF0B3", sw=12, scale=s)
        out += text(810, y0 - 205, "(también es de acero)", 32, "#fff", sw=8, opacity=prog(t, 7.7, 8.2))
    return out


# ----------------------------------------------------------------- 3. secreto
@scene
def scene_secret(t, d):
    y0 = 1030
    rx = lerp(-460, 490, ease_in_out(prog(t, 1.0, d * .62)))
    out = '<rect width="1080" height="1920" fill="url(#skyDay)"/>' + wd.sky("skyDay", t, sun_xy=(850, 330))
    out += horizon(t, y0 - 10, speed=8) + oc.sea_back(t, y0, 8)
    sy = oc.wave_y(540, t, y0, 8)
    out += oc.ship_g(540, sy, .95, 1.4 * math.sin(t * 1.3), oc.ship_section(t, rx))
    out += oc.sea_front(t, y0, 8, alpha=.42)
    # línea de barrido
    if 1.0 < t < d * .62:
        sx = 540 + rx * .95
        out += (f'<rect x="{sx-6:.0f}" y="{sy-170:.0f}" width="12" height="300" fill="#fff" opacity=".7"/>'
                f'<rect x="{sx-30:.0f}" y="{sy-170:.0f}" width="60" height="300" fill="url(#glowC)" opacity=".5"/>')
    out += text(540, 290, "EL SECRETO", 78, "#fff", sw=14, scale=pop(t, 0, .5))
    if t > d * .5:
        a = min(1, pop(t, d * .5, .5))
        out += (f'<line x1="330" y1="1116" x2="330" y2="{sy-25:.0f}" stroke="#7CF0B3" stroke-width="6" opacity="{a:.2f}"/>'
                f'<circle cx="330" cy="{sy-25:.0f}" r="12" fill="#7CF0B3" opacity="{a:.2f}"/>')
        out += pill(330, 1150, 330, 1, "#0F3D6E", "#7CF0B3", 40, "#7CF0B3", a, "AIRE")
        out += text(330, 1222, "casi no pesa", 30, "#fff", sw=7, opacity=a)
    if t > d * .75:
        a = min(1, pop(t, d * .75, .5))
        out += (f'<line x1="770" y1="1116" x2="770" y2="{sy+95:.0f}" stroke="#FFE14D" stroke-width="6" opacity="{a:.2f}"/>'
                f'<circle cx="770" cy="{sy+95:.0f}" r="12" fill="#FFE14D" opacity="{a:.2f}"/>')
        out += pill(770, 1150, 330, 1, "#3A2A0A", "#FFE14D", 38, "#FFE14D", a, "ACERO")
        out += text(770, 1222, "capa delgada", 30, "#fff", sw=7, opacity=a)
    return out


# ---------------------------------------------------------------- 4. ciencia
@scene
def scene_science(t, d):
    y0 = 960
    sink_k = ease_in_out(prog(t, 1.0, d * .48))
    off = lerp(-205, 0, sink_k)
    out = '<rect width="1080" height="1920" fill="url(#skyDay)"/>' + wd.sky("skyDay", t, sun=False)
    # mar visto en corte (hasta y=1280)
    out += f'<polygon points="{oc._poly(t, y0, 7, 0, H + 60)}" fill="url(#seaDeep)"/>'
    for i in range(4):
        x = 140 + i * 260
        out += f'<polygon points="{x},{y0} {x+60},{y0} {x+170},1290 {x+40},1290" fill="#fff" opacity="{.08+.04*math.sin(t*1.4+i):.2f}"/>'
    sy = y0 + off
    S = .9
    # agua desplazada (fantasma con forma del casco bajo la línea de flotación)
    sub = max(0.0, (sy + 112 * S) - y0) / (112 * S)
    ghost = ""
    if sub > 0.02:
        ghost = (f'<g transform="translate(540,{sy:.1f}) scale({S})"><defs><clipPath id="below"><rect x="-500" y="{(y0-sy)/S:.1f}" width="1000" height="400"/></clipPath></defs>'
                 f'<g clip-path="url(#below)"><path d="{oc.HULL}" fill="#E6F8FF" opacity="{.35 if sub<.99 else .55}"/>'
                 f'<path d="{oc.HULL}" fill="none" stroke="#fff" stroke-width="6" stroke-dasharray="16 12"/></g></g>')
    # corrientes alrededor del casco
    flow = ""
    if .15 * d < t < d * .8:
        for ring in range(3):
            for i in range(7):
                u = (t * .28 + i / 7 + ring * .09) % 1
                th = math.pi * (1 - u)
                rx_, ry_ = 520 + ring * 70, 210 + ring * 60
                px, py = 540 + rx_ * math.cos(th) * .9, y0 + 20 + ry_ * math.sin(th)
                flow += f'<circle cx="{px:.0f}" cy="{py:.0f}" r="7" fill="#fff" opacity="{.75*math.sin(math.pi*u):.2f}"/>'
    out += flow
    out += oc.ship_g(540, sy, S, 1.0 * math.sin(t * 1.3), oc.ship_section(t, 490))
    out += ghost
    out += f'<polygon points="{oc._poly(t, y0, 7, 0, H + 60)}" fill="#3AA8EA" opacity=".3"/>'
    out += f'<polyline points="{" ".join(f"{x},{oc.wave_y(x, t, y0, 7):.1f}" for x in range(-60, W+61, 18))}" fill="none" stroke="#fff" stroke-width="5" opacity=".75"/>'
    out += text(540, 290, "ARQUÍMEDES", 78, "#fff", sw=14, scale=pop(t, 0, .5))
    # flechas: peso (rojo, constante) y empuje (verde, crece con el volumen desplazado)
    L = 220
    if t > .8:
        a = prog(t, .8, 1.3)
        wy0 = sy - 40 * S
        out += (f'<line x1="400" y1="{wy0:.0f}" x2="400" y2="{wy0+L*a:.0f}" stroke="#FF4D6D" stroke-width="16"/>'
                f'<polygon points="400,{wy0+L*a+36:.0f} 372,{wy0+L*a-6:.0f} 428,{wy0+L*a-6:.0f}" fill="#FF4D6D" opacity="{a:.2f}"/>')
        out += text(400, wy0 - 30, "PESO", 40, "#FF8FA3", sw=9, opacity=a)
        by0 = sy + 112 * S + 90
        up = L * min(1, sub) if sub > .02 else 0
        if up > 12:
            out += (f'<line x1="680" y1="{by0:.0f}" x2="680" y2="{by0-up:.0f}" stroke="#35E08A" stroke-width="16"/>'
                    f'<polygon points="680,{by0-up-36:.0f} 652,{by0-up+6:.0f} 708,{by0-up+6:.0f}" fill="#35E08A"/>')
        out += text(680, by0 + 48, "EMPUJE", 40, "#7CF0B3", sw=9, opacity=min(1, sub * 3))
    if t > d * .5:
        a = pop(t, d * .5, .5)
        out += text(540, 1195, "EMPUJE = PESO DEL", 46, "#FFE14D", sw=11, scale=a)
        out += text(540, 1252, "AGUA DESPLAZADA", 46, "#FFE14D", sw=11, scale=a)
    return out


# -------------------------------------------------------------- 5. comparación
@scene
def scene_compare(t, d):
    out = '<rect width="1080" height="1920" fill="url(#blueprint)"/>'
    from .art import diagram as dg
    out += dg.grid(t)
    split = d * .55
    if t < split + .4:
        a = 1 - prog(t, split, split + .4)
        kfill = ease_in_out(prog(t, 1.2, split - 1.2))
        osc = 5 * math.exp(-max(0, t - (split - 1.2)) * 2) * math.sin(t * 7) if kfill >= 1 else 0
        th = -11 * (1 - kfill) + osc
        cx, cy, L = 540, 720, 300
        c, s_ = math.cos(math.radians(th)), math.sin(math.radians(th))
        lx, ly, rx, ry = cx - L * c, cy - L * s_ * -1 * -1 * 1, cx + L * c, cy + L * s_
        ly = cy - L * s_
        g = f'<g opacity="{a:.2f}">'
        g += (f'<polygon points="{cx},{cy} {cx-70},1160 {cx+70},1160" fill="#CFE3FF"/><rect x="{cx-170}" y="1150" width="340" height="30" rx="12" fill="#8FB8FF"/>'
              f'<line x1="{lx:.0f}" y1="{ly:.0f}" x2="{rx:.0f}" y2="{ry:.0f}" stroke="#EAF2FF" stroke-width="16" stroke-linecap="round"/>'
              f'<circle cx="{cx}" cy="{cy}" r="22" fill="#F3C623"/>')
        for (px, py) in ((lx, ly), (rx, ry)):
            g += (f'<line x1="{px:.0f}" y1="{py:.0f}" x2="{px-110:.0f}" y2="{py+170:.0f}" stroke="#CFE3FF" stroke-width="4"/>'
                  f'<line x1="{px:.0f}" y1="{py:.0f}" x2="{px+110:.0f}" y2="{py+170:.0f}" stroke="#CFE3FF" stroke-width="4"/>'
                  f'<path d="M{px-135:.0f},{py+170:.0f} L{px+135:.0f},{py+170:.0f} Q{px+110:.0f},{py+205:.0f} {px:.0f},{py+205:.0f} Q{px-110:.0f},{py+205:.0f} {px-135:.0f},{py+170:.0f} Z" fill="#8FB8FF"/>')
        # barco en plato izq., agua en plato der.
        g += oc.ship_g(lx, ly + 170 - 112 * .27 + 5, .27, 0, oc.ship_exterior())
        wx, wy = rx, ry + 170 - 112 * .27 + 5
        g += (f'<g transform="translate({wx:.0f},{wy:.0f}) scale(.27)"><defs><clipPath id="wf"><rect x="-440" y="{112 - 262*kfill:.0f}" width="900" height="300"/></clipPath></defs>'
              f'<path d="{oc.HULL}" fill="#0A2A55" stroke="#8FB8FF" stroke-width="8" stroke-dasharray="22 14"/>'
              f'<g clip-path="url(#wf)"><path d="{oc.HULL}" fill="#4DB8FF"/></g></g>')
        g += text(lx, ly - 70, "BARCO", 44, "#fff", sw=0) + text(rx, ry - 70, "AGUA DESPLAZADA", 36, "#7CD3FF", sw=0)
        g += '</g>'
        out += g
        out += text(540, 330, "SE EQUILIBRAN", 74, "#fff", scale=pop(t, 0, .5))
        if kfill >= 1:
            out += text(540, 1250, "PESO = EMPUJE", 54, "#7CF0B3", sw=0, scale=pop(t, split - 1.2, .5))
    if t > split:
        b = ease_out(prog(t, split + .1, split + 1.5))
        base, u = 1120, 58
        out += f'<g opacity="{prog(t, split, split+.5):.2f}">'
        out += text(540, 330, "DENSIDAD MEDIA", 74, "#fff")
        for (x, val, col, lab, vtxt) in ((220, 7.8, "#9AA6BA", "ACERO", "7,8"), (540, 1.0, "#4DB8FF", "AGUA", "1"), (860, .6, "#FF8A5C", "BARCO ENTERO", "< 1")):
            h = val * u * b * (1 + .025 * math.sin(t * 3 + x) * (b >= 1))
            out += f'<rect x="{x-80}" y="{base-h:.0f}" width="160" height="{h:.0f}" rx="10" fill="{col}" stroke="#fff" stroke-width="4"/>'
            out += text(x, base + 46, lab, 32 if len(lab) < 8 else 28, "#fff") + text(x, base - max(h, u * 1.0) - 26, vtxt, 50, "#FFE14D", sw=8)
        ly_ = base - 1.0 * u
        out += f'<line x1="70" y1="{ly_:.0f}" x2="1010" y2="{ly_:.0f}" stroke="#FFE14D" stroke-width="5" stroke-dasharray="16 10"/>'
        for i in range(10):                                   # partículas que "flotan" sobre el nivel del agua
            px = 70 + (i * 97 + t * 60) % 940
            out += f'<circle cx="{px:.0f}" cy="{ly_ + 12 * math.sin(t * 3 + i):.0f}" r="6" fill="#FFE14D" opacity=".8"/>'
        out += text(540, 470, "MÁS DENSO QUE EL AGUA: SE HUNDE", 34, "#FF8FA3", sw=0, opacity=prog(t, split + 1.5, split + 2))
        out += text(540, 1230, "MENOS DENSO (acero + aire): FLOTA", 36, "#7CF0B3", sw=0, opacity=prog(t, split + 2.2, split + 2.8))
        out += text(540, 400, "(en g/cm³)", 34, "#9FD0FF", sw=0)
        out += '</g>'
    return out


# ------------------------------------------------------------------ 6. carga
@scene
def scene_load(t, d):
    y0 = 1010
    cyc = (d - 1.0) / 3
    ex = [(7, 3, "#F3A712"), (8, 2, "#8E5CF7"), (8, 3, "#2FBF71")]
    landed = [i for i in range(3) if t >= 1.0 + cyc * (i + 1) - .1]
    sink = sum(14 * ease_out(prog(t, 1.0 + cyc * (i + 1) - .1, 1.0 + cyc * (i + 1) + .7)) for i in range(3))
    S = .8
    out = '<rect width="1080" height="1920" fill="url(#skyDay)"/>' + wd.sky("skyDay", t, sun_xy=(250, 330))
    out += horizon(t, y0 - 10, speed=5)
    sy = oc.wave_y(500, t, y0, 5) + sink
    out += oc.sea_back(t, y0, 5)
    out += oc.ship_g(500, sy, S, .8 * math.sin(t * 1.2), oc.ship_exterior([ex[i] for i in landed]))
    out += oc.sea_front(t, y0, 5, alpha=.5)
    # muelle a la derecha
    out += f'<rect x="850" y="{y0-70}" width="300" height="600" fill="#9AA3B2"/><rect x="850" y="{y0-80}" width="300" height="16" fill="#C4CAD6"/>'
    # pila de contenedores en el muelle
    pile = [i for i in range(3) if t < 1.0 + cyc * i + .4]       # aún no recogidos
    for j, i in enumerate(pile):
        out += oc._box(880 + 60 * j, y0 - 118, 50, 38, ex[i][2])
    # grúa
    bt = 560
    out += ('<rect x="870" y="%d" width="22" height="%d" fill="#F3C623" stroke="#1B1B2F" stroke-width="3"/>' % (bt, y0 - 70 - bt) +
            '<rect x="940" y="%d" width="22" height="%d" fill="#F3C623" stroke="#1B1B2F" stroke-width="3"/>' % (bt, y0 - 70 - bt) +
            f'<rect x="410" y="{bt-26}" width="600" height="30" fill="#F3C623" stroke="#1B1B2F" stroke-width="3"/>')
    for xx in range(430, 1000, 40):
        out += f'<line x1="{xx}" y1="{bt-24}" x2="{xx+20}" y2="{bt+2}" stroke="#1B1B2F" stroke-width="2"/>'
    # ciclo de carga: recoger -> subir -> mover -> bajar
    hook_x, hook_y, carry = 905, bt + 30, None
    for i in range(3):
        t0 = 1.0 + cyc * i
        if t0 <= t < t0 + cyc:
            u = (t - t0) / cyc
            tx_ship = 500 + S * (oc.COL_X[ex[i][0]] + 25)
            ty_ship = sy - S * (150 + (ex[i][1] + 1) * oc.CH) + S * 0
            py0 = y0 - 118
            if u < .2:
                hook_x, hook_y = lerp(905, 905, 0), lerp(bt + 30, py0 - 20, ease_in_out(u / .2))
                carry = (hook_x, hook_y + 0)
            elif u < .4:
                k = ease_in_out((u - .2) / .2)
                hook_x, hook_y = 905, lerp(py0 - 20, bt + 90, k); carry = (hook_x, hook_y)
            elif u < .7:
                k = ease_in_out((u - .4) / .3)
                hook_x, hook_y = lerp(905, tx_ship, k), bt + 90; carry = (hook_x, hook_y)
            else:
                k = ease_in_out((u - .7) / .3)
                hook_x, hook_y = tx_ship, lerp(bt + 90, ty_ship - 8 * S, k); carry = (hook_x, hook_y)
            out += f'<line x1="{hook_x:.0f}" y1="{bt+4}" x2="{hook_x:.0f}" y2="{hook_y:.0f}" stroke="#1B1B2F" stroke-width="4"/>'
            out += f'<rect x="{hook_x-24:.0f}" y="{bt-30}" width="48" height="34" rx="6" fill="#E4572E" stroke="#1B1B2F" stroke-width="3"/>'
            out += f'<g transform="translate({hook_x-25*S*1.2:.0f},{hook_y:.0f}) scale({S*1.2})">{oc._box(0, 0, 50, 38, ex[i][2])}</g>'
    if not carry:
        out += f'<rect x="{hook_x-24:.0f}" y="{bt-30}" width="48" height="34" rx="6" fill="#E4572E" stroke="#1B1B2F" stroke-width="3"/>'
    # marca de flotación original
    out += f'<line x1="60" y1="{y0+0}" x2="470" y2="{y0}" stroke="#FFE14D" stroke-width="4" stroke-dasharray="14 10" opacity="{prog(t, 2, 3):.2f}"/>'
    out += text(540, 290, "MÁS CARGA", 78, "#fff", sw=14, scale=pop(t, 0, .5))
    if t > 3.2:
        out += text(300, y0 + 130, "SE HUNDE UN POCO MÁS", 40, "#fff", sw=10, opacity=prog(t, 3.2, 3.8))
        out += text(300, y0 + 180, "y desplaza más agua", 34, "#7CD3FF", sw=8, opacity=prog(t, 3.8, 4.3))
    out += oc.captain(960, y0 - 80, .8, t, "happy", "point", flip=True)
    return out


# ------------------------------------------------------------------- 7. final
@scene
def scene_final(t, d):
    y0 = 1010
    z = lerp(1.45, 1.0, ease_in_out(t / d))
    cam = cam_at(z, 540, 900)
    out = layer(wd.sky("skySunset", t, sun_xy=(780, 560), clouds=True), cam, .15)
    out += layer(horizon(t, y0 - 10, "#8A5A8E", 22), cam, .4)
    sy, rot = bob(t, 540, y0, 9)
    main = oc.sea_back(t, y0, 9)
    for i in range(6):
        main += f'<ellipse cx="{140 - i*62 + 25*math.sin(t*2+i):.0f}" cy="{y0+14+i*3}" rx="{50+i*8}" ry="8" fill="#fff" opacity="{.5-i*.07:.2f}"/>'
    body = oc.ship_exterior() + oc.captain(-296, -150, .42, t, "happy", "wave")
    main += oc.ship_g(540, sy, .78, rot, body)
    main += oc.sea_front(t, y0, 9)
    out += layer(main, cam)
    for k in range(3):
        out += oc.gull((900 - 60 * t + k * 200) % 1200 - 60, 400 + k * 55 + 14 * math.sin(t * 2 + k), t, 1.1, k)
    out += text(540, 250, "NO FLOTA POR SER LIGERO", 56, "#fff", sw=12, scale=pop(t, .9, .5))
    out += text(540, 340, "FLOTA POR SU FORMA", 66, "#FFE14D", sw=13, scale=pop(t, 1.2, .5))
    out += text(540, 425, "Y SU AIRE", 66, "#FFE14D", sw=13, scale=pop(t, 1.5, .5))
    pulse = 1 + .05 * math.sin(t * 8)
    s3 = pop(t, d * .55, .5)
    out += (f'<g transform="translate(540,1130) scale({s3*pulse:.3f})"><rect x="-290" y="-62" width="580" height="124" rx="62" fill="#FF3D6B" stroke="#fff" stroke-width="8"/>'
            + text(0, 22, "¿LO SABÍAS? SÍGUEME", 44, "#fff") + '</g>')
    return out


SFX = {
    "hook": [("horn", lambda d: .1), ("pop", lambda d: .05)],
    "problem": [("splash", lambda d: 2.2), ("clank", lambda d: 5.0), ("pop", lambda d: 7.4)],
    "secret": [("pop", lambda d: .05), ("pop", lambda d: d * .5)],
    "science": [("pop", lambda d: .05), ("pop", lambda d: d * .5)],
    "compare": [("pop", lambda d: .05), ("click", lambda d: d * .5)],
    "load": [("clank", lambda d: 1.0 + (d - 1) / 3 * (i + 1)) for i in range(3)] + [("pop", lambda d: .05)],
    "final": [("pop", lambda d: .9), ("ding", lambda d: d * .55)],
}
