"""Las 12 escenas de «El cajero que descubrió un robo imposible».

Cada escena es una función draw(cv, t, sc) con t = segundos locales y
sc = dict(dur, T, t_abs). Las acciones se disparan en tiempos relativos
al inicio/fin de cada frase de narración, así todo queda sincronizado.
"""
from __future__ import annotations

import math

import skia

from .characters import draw_character
from .gfx import (C, P, circ, oval, line, rect, rectp, poly, curve, shadow, shade, mix, text,
                  text_w, clamp, lerp, smooth, ease_out, ease_in, ease_io, out_back, prog, grad,
                  radial, pulse, rnd, camera, shake, FONT_BOLD, FONT_MONO, FONT_REG)
from . import props as pr

GROUND = 1490


# ------------------------------------------------------------------ utilidades
def blur_begin(cv, sigma):
    paint = skia.Paint()
    paint.setImageFilter(skia.ImageFilters.Blur(sigma, sigma))
    cv.saveLayer(None, paint)


def pt_on(a, b, k):
    return (lerp(a[0], b[0], k), lerp(a[1], b[1], k))


def arc_pt(a, b, k, h):
    x, y = pt_on(a, b, k)
    return (x, y - math.sin(math.pi * k) * h)


def cart(cv, x, y, s=1.0):
    cv.save(); cv.translate(x, y); cv.scale(s, s)
    poly(cv, [(-110, -150), (110, -150), (85, -60), (-85, -60)], "#C7CED6")
    for i in range(-90, 100, 30):
        line(cv, i, -150, i * 0.8, -60, "#9AA5B1", 4)
    line(cv, -110, -150, -150, -190, "#6B7580", 8)
    line(cv, -150, -190, -175, -190, "#6B7580", 10)
    rect(cv, -60, -200, 40, 50, "#E74C3C", r=6); rect(cv, 0, -190, 36, 40, "#F1C40F", r=6)
    rect(cv, 40, -184, 36, 34, "#3498DB", r=6)
    circ(cv, -60, -36, 18, "#2B3038"); circ(cv, 60, -36, 18, "#2B3038")
    cv.restore()


def box(cv, x, y, w=80, h=62, col="#C99A5B"):
    rect(cv, x - w / 2, y - h / 2, w, h, col, r=6)
    rect(cv, x - w / 2, y - h / 2, w, 12, shade(col, -0.15), r=4)
    rect(cv, x - 9, y - h / 2, 18, h, shade(col, 0.2), 0.7)


def hud_loss(cv, sc, appear=0.0):
    T = sc["T"]
    t0, t1 = T.start("h1") + 0.3, T.end("h3")
    k = prog(sc["t_abs"], t0, t1)
    val = 7430 * ease_io(k)
    a = smooth(prog(sc["t_abs"], T.start("h1") + 2.6, T.start("h1") + 3.1))
    if a <= 0:
        return
    y = 300 - 40 * (1 - a)
    pr.hud_card(cv, 540, y, 760, 170, "PÉRDIDAS ACUMULADAS", pr.money_fmt(val, "-"),
                "#FF5A5A", a=a, sub="dinero que no aparece en caja")


def dollar_title(cv, sc):
    t = sc["t_abs"]
    T = sc["T"]
    a = 1 - smooth(prog(t, 2.4, 3.0))
    a *= smooth(prog(t, 0.0, 0.4))
    if a <= 0:
        return
    cv.drawRect(skia.Rect.MakeXYWH(0, 0, 1080, 700), grad(0, 0, 0, 700, "#05080F", "#05080F", 0.82 * a, 0.0))
    text(cv, "EL CAJERO QUE DESCUBRIÓ", 540, 230 - 30 * (1 - ease_out(prog(t, 0, 0.6))), 58, "#FFFFFF", a=a, outline="#000000", outline_w=8)
    text(cv, "UN ROBO IMPOSIBLE", 540, 310 - 30 * (1 - ease_out(prog(t, 0.1, 0.7))), 76, "#FFD166", a=a, outline="#000000", outline_w=10)


# ======================================================================
# S1 · GANCHO · supermercado con diferencias de dinero
# ======================================================================
def s1(cv, t, sc):
    d = sc["dur"]
    k = t / d
    cx = lerp(470, 760, ease_io(k))
    camera(cv, cx, 960, lerp(1.0, 1.12, k))
    pr.bg_store(cv, cx, t)
    # Lupe en caja
    draw_character(cv, "lupe", 250, 1360, 1.5, pose={"armL": (30, 20), "armR": (-35, -25 - 12 * math.sin(t * 3))}, t=t, mood="neutral", look=(1, 0))
    pr.register(cv, 250, 1470, 1.0, t, screen="$ 38.60")
    # monedas / billetes saliendo del cajón con el tiempo
    # repositor con caja caminando por el fondo
    rx = lerp(-250, 1500, (t * 0.14) % 1.0)
    draw_character(cv, "repo", rx, 1330, 1.25, pose={"walk": t * 7, "armL": (-30, -60), "armR": (30, 60)}, t=t, holding=lambda c, hr, hl, s: box(c, hr[0] - 40, hr[1] - 20))
    # cliente con carrito cruzando en primer plano
    cx2 = lerp(1500, -250, ((t * 0.2) + 0.1) % 1.0)
    draw_character(cv, "clienta", cx2, 1640, 1.55, pose={"walk": t * 6.5, "armL": (18, 10), "armR": (-60, -55)}, t=t, flip=True, mood="smile")
    cart(cv, cx2 - 170, 1630, 1.6)
    # Mateo atendiendo en segunda caja
    draw_character(cv, "mateo", 900, 1360, 1.5, pose={"armL": (-30, -20 + 8 * math.sin(t * 4)), "armR": (28, 20)}, t=t, mood="neutral", look=(-1, 0))
    pr.register(cv, 900, 1470, 1.0, t, screen="$ 12.90", flip=True)
    # cliente mayor esperando
    draw_character(cv, "cliente", 1190, 1500, 1.5, pose={}, t=t, flip=True, mood="neutral")
    # destello de diferencia sobre la caja 1
    a = smooth(prog(t, 1.0, 1.4)) * (0.6 + 0.4 * pulse(t, 0.8))
    if a > 0:
        pr.bubble(cv, 250, 760, 330, 96, "¿$ faltan?", (0, 50), 40, color="#FFE1E1", tcolor="#C0392B", a=a)


# ======================================================================
# S2 · «nadie entraba a robar»
# ======================================================================
def s2(cv, t, sc):
    d = sc["dur"]; k = t / d
    camera(cv, 540, 960, lerp(1.0, 1.1, k))
    pr.bg_store(cv, 540, t, shelves=False)
    # puertas de vidrio
    rect(cv, 130, 430, 820, 880, "#6B7885", r=18)
    rect(cv, 150, 450, 780, 840, "#BFE6FA", r=10)
    rectp(cv, 150, 450, 780, 840, grad(0, 450, 0, 1290, "#CDEFFF", "#8CCBEA"), r=10)
    rect(cv, 150, 1170, 780, 120, "#7FBF6A", 0.9)  # pasto/exterior
    open_k = 0.5 - 0.5 * math.cos(t * 1.6)
    for sx in (-1, 1):
        w = 390 - 150 * open_k
        x0 = 540 if sx < 0 else 540
        px = 540 + sx * (w / 2 + open_k * 160) - (w / 2 if sx > 0 else w / 2) * 0
        rect(cv, 540 - w if sx < 0 else 540, 450, w, 840, "#E6F6FF", 0.35, r=6)
    line(cv, 540, 450, 540, 1290, "#6B7885", 8, 0.7)
    text(cv, "ABIERTO", 540, 400, 46, "#FFFFFF", outline="#2FA36B", outline_w=10)
    # clientes entran con normalidad
    c1 = ease_io(prog(t, 0.0, 2.4))
    draw_character(cv, "clienta", lerp(380, 980, c1), 1560, 1.4, pose={"walk": t * 6}, t=t, mood="smile")
    c2 = ease_io(prog(t, 1.2, 3.0))
    draw_character(cv, "cliente", lerp(700, 130, c2), 1700, 1.55, pose={"walk": t * 6 + 1}, t=t, flip=True)
    # guardia atento
    draw_character(cv, "guardia", 110, 1470, 1.5, pose={"armL": (35, 120), "armR": (-35, -120)}, t=t, look=(math.sin(t * 1.7), 0))
    # señal «no ladrón»
    a = out_back(prog(t, 1.1, 1.6))
    if a > 0:
        cv.save(); cv.translate(540, 760); cv.scale(a, a)
        circ(cv, 0, 0, 190, "#FFFFFF"); circ(cv, 0, 0, 190, "#E74C3C", style="stroke", w=30)
        # silueta de ladrón (antifaz + camiseta rayada)
        circ(cv, 0, -40, 54, "#2B2B33"); rect(cv, -56, -62, 112, 30, "#111111", r=14)
        circ(cv, -22, -48, 9, "#FFFFFF"); circ(cv, 22, -48, 9, "#FFFFFF")
        rect(cv, -70, 18, 140, 110, "#2B2B33", r=34)
        for i in range(4):
            rect(cv, -70, 38 + i * 24, 140, 8, "#FFFFFF", 0.9)
        line(cv, -135, -135, 135, 135, "#E74C3C", 30)
        cv.restore()
    hud_loss(cv, sc)


# ======================================================================
# S3 · el dinero desaparece de las cajas
# ======================================================================
def s3(cv, t, sc):
    d = sc["dur"]; k = t / d
    camera(cv, 560, lerp(1010, 960, k), lerp(1.0, 1.18, ease_out(k)))
    pr.bg_store(cv, 540, t, dim=0.25)
    draw_character(cv, "lupe", 360, 1350, 1.55, pose={"armR": (-150, -170 + 6 * math.sin(t * 6)), "armL": (20, 10), "head_tilt": 6}, t=t, mood="worry", look=(0.8, 0.4))
    op = ease_out(prog(t, 0.35, 0.9))
    alert = smooth(prog(t, 1.2, 1.5))
    scr = "$ 1,130" if t < 1.2 else ("-$ 120" if int(t * 4) % 2 == 0 else "FALTA!")
    pr.register(cv, 640, 1470, 1.4, t, drawer=op, screen=scr, screen_color="#FF6B6B" if t > 1.2 else "#7CFFB2", alert=alert)
    # billetes que se esfuman
    r_ = rnd(11)
    for i in range(9):
        t0 = 0.8 + i * 0.22
        p = prog(t, t0, t0 + 1.4)
        if p <= 0:
            continue
        bx = 640 + 40 + (i % 3) * 70 + (r_.random() - 0.5) * 30
        by = 1470 - 300 * 1.4 + 10
        x = bx + math.sin(p * 4 + i) * 40
        y = by - 520 * ease_out(p)
        a = 1 - smooth(prog(p, 0.45, 1.0))
        pr.bill(cv, x, y, rot=-20 + p * 120 * (1 if i % 2 else -1), s=0.9 - 0.3 * p, a=a)
        if p > 0.45:
            for j in range(3):
                sp = prog(p, 0.45, 1.0)
                pr.sparkle(cv, x + math.cos(j * 2.1 + i) * 50 * sp, y + math.sin(j * 2.1 + i) * 50 * sp, 12 * (1 - sp), a=1 - sp)
    hud_loss(cv, sc)
    if alert > 0 and int(t * 6) % 2 == 0:
        rect(cv, -200, -200, 1500, 2300, "#FF2B2B", 0.10 * alert)


# ======================================================================
# S4 · el gerente investiga (3 planos en la misma frase)
# ======================================================================
def s4(cv, t, sc):
    d = sc["dur"]; T, a0 = sc["T"], sc["a"]
    sp1 = T.word("d1", "interrog") - a0 - 0.1
    sp2 = T.word("d1", "comprob") - a0 - 0.1
    sc["sp"] = (sp1, sp2)
    if t < sp1:
        # cámaras de seguridad
        lt = t
        camera(cv, 540, 960, lerp(1.0, 1.1, t / sp1))
        pr.bg_office(cv, lt)
        rect(cv, 0, 0, 1080, 1920, "#0B0F14", 0.5)
        labels = ["CAJA 1", "CAJA 2", "PASILLO", "ENTRADA"]
        for i in range(4):
            x = 60 + (i % 2) * 485; y = 130 + (i // 2) * 390
            pr.cctv_feed(cv, x, y, 465, 360, lt + i * 0.7, mode=1 if i == 1 else 0, label=labels[i], night=False)
        # el gerente mira las pantallas
        look = (math.sin(lt * 2.2) * 1.2, -0.4)
        draw_character(cv, "ramirez", 540, 1900, 2.15, pose={"armL": (10, 15), "armR": (-10, -15)}, t=t, mood="focus", look=look)
        rect(cv, 0, 1300, 1080, 24, "#1B2028", 0.9)
    elif t < sp2:
        lt = t - sp1
        camera(cv, 540, 960, lerp(1.0, 1.08, lt / (sp2 - sp1)))
        pr.bg_store(cv, 540, t, dim=0.1, shelves=False)
        rect(cv, 0, 0, 1080, 1250, "#DDE7EE", 0.9)
        # interrogatorio
        draw_character(cv, "ramirez", 260, 1500, 1.55, pose={"armL": (10, 15), "armR": (-95, -110 + 10 * math.sin(lt * 7))}, t=t, mood="angry", talk=0.5 + 0.5 * math.sin(lt * 14), look=(1, 0))
        xs = [610, 800, 990]
        names = ["lupe", "dario", "repo"]
        for i, (x, n) in enumerate(zip(xs, names)):
            a = prog(lt, 0.15 + i * 0.25, 0.5 + i * 0.25)
            pose = {"armL": (-110, -150), "armR": (110, 150)} if n != "dario" else {}
            draw_character(cv, n, x, 1520, 1.25, pose=pose, t=t, flip=True, mood="worry" if n != "dario" else "smirk", look=(-1, 0))
            if a > 0:
                pr.bubble(cv, x, 940 - 20 * (i % 2), 170, 74, "¡Yo no!" if n != "dario" else "...", (0, 44), 34, a=min(1, a * 2), scale=out_back(a))
        a = out_back(prog(lt, 0.05, 0.4))
        pr.bubble(cv, 300, 780, 360, 100, "¿Quién fue?", (-20, 60), 44, a=min(1, a), scale=a, color="#FFF3C4")
        for i in range(3):
            pr.question(cv, 120 + i * 90, 1000 - i * 30 + 6 * math.sin(lt * 5 + i), 70, a=prog(lt, 0.3, 0.6))
    else:
        lt = t - sp2
        camera(cv, 540, 960, 1.0 + 0.06 * (lt / max(0.1, d - sp2)))
        rectp(cv, 0, 0, 1080, 1920, grad(0, 0, 0, 1920, "#7B5A3E", "#5B4029"))
        rect(cv, 0, 200, 1080, 1720, "#8A6445", r=0)
        for i in range(4):
            s_ = out_back(prog(lt, 0.05 + i * 0.22, 0.35 + i * 0.22))
            pr.paper(cv, 330 + (i % 2) * 380, 560 + (i // 2) * 520, 330, 470, rot=(-5, 4, 3, -3)[i], header="RECIBO #%d" % (1180 + i), s=s_, lines=9)
            ck = prog(lt, 0.55 + i * 0.28, 0.85 + i * 0.28)
            if ck > 0:
                pr.check(cv, 330 + (i % 2) * 380 + 70, 700 + (i // 2) * 520, 90, p=ck, w=16)
        # lupa recorre los recibos
        mx = lerp(260, 820, ease_io(prog(lt, 0.2, 1.1)))
        my = 700 + 520 * ease_io(prog(lt, 0.55, 1.1)) * 0.6 + 40 * math.sin(lt * 5)
        pr.magnifier(cv, mx, my, 110)
        draw_character(cv, "ramirez", 880, 2000, 1.4, pose={}, t=t, mood="focus", look=(-1, 0.6))


# ======================================================================
# S5 · «Todo parecía normal»
# ======================================================================
def s5(cv, t, sc):
    d = sc["dur"]
    camera(cv, 540, 960, lerp(1.0, 1.06, t / d))
    pr.bg_office(cv, t)
    rect(cv, 0, 0, 1080, 1920, "#0B0F14", 0.35)
    # tablilla
    rect(cv, 120, 360, 840, 980, "#6B4A2F", r=26)
    rect(cv, 170, 440, 740, 840, "#FFFFFF", r=10)
    rect(cv, 380, 330, 320, 90, "#9AA5B1", r=20)
    rows = [("CÁMARAS", 0.15), ("EMPLEADOS", 0.45), ("RECIBOS", 0.75)]
    for i, (lbl, t0) in enumerate(rows):
        y = 580 + i * 220
        text(cv, lbl, 230, y + 16, 58, "#2B3440", "left")
        line(cv, 230, y + 58, 780, y + 58, "#C9D1D8", 4)
        pr.check(cv, 830, y, 120, p=prog(t, t0, t0 + 0.28), w=22)
    pr.stamp(cv, 540, 1180, "TODO NORMAL", "#2FA36B", -8, out_back(prog(t, 1.0, 1.25)), 1.0 if t > 1.0 else 0, 70)
    draw_character(cv, "ramirez", 880, 1950, 1.5, pose={"armL": (-150, -130), "armR": (150, 130)}, t=t, mood="worry", look=(-0.5, 0))


# ======================================================================
# S6 · el cajero nota la pequeña diferencia
# ======================================================================
def s6(cv, t, sc):
    d = sc["dur"]; T, a0 = sc["T"], sc["a"]
    split = T.word("d3", "aparec") - a0 - 0.15
    tp = T.word("d3", "pagaba") - a0          # el cliente paga
    tc = T.word("d3", "ped") - a0 + 0.2       # pide cambio
    sc["tt"] = (split, tp, tc)
    if t < split:
        camera(cv, 560, 980, lerp(1.0, 1.12, t / split))
        pr.bg_store(cv, 560, t, dim=0.08, shelves=False)
        rect(cv, -400, 0, 2000, 1300, "#E6EEF2", 0.9)
        # mostrador
        pr.register(cv, 360, 1480, 1.35, t, drawer=0.0, screen="" if t < tp else "CAMBIO", screen_color="#7CFFB2")
        draw_character(cv, "mateo", 340, 1380, 1.55, pose={"armR": (-45, -80 + 10 * math.sin(t * 5)), "armL": (40, 30)}, t=t, mood="smile", look=(1, 0))
        # cliente llega, paga con billete, recibe cambio
        a = ease_out(prog(t, 0.0, tp - 0.4))
        cxp = lerp(1350, 800, a)
        draw_character(cv, "cliente", cxp, 1560, 1.55, pose={"walk": t * 6 if a < 1 else None, "armR": (-110, -150) if a >= 1 else (-8, -4)}, t=t, flip=True, mood="smile")
        # billete: cliente -> Mateo
        k = ease_io(prog(t, tp, tp + 0.6))
        if 0 < k < 1:
            x, y = arc_pt((690, 1250), (470, 1240), k, 60)
            pr.bill(cv, x, y, rot=-10, s=0.9)
        if tp + 0.6 <= t < tc + 0.1:
            pr.bill(cv, 470, 1240, rot=-10, s=0.9)
        # cambio: Mateo -> cliente (monedas)
        k2 = ease_io(prog(t, tc, tc + 0.6))
        if 0 < k2 < 1:
            for j in range(3):
                x, y = arc_pt((470, 1240), (690, 1250), k2, 90)
                pr.coin(cv, x + j * 16, y - j * 10, 18, spin=t * 12 + j)
        # globo 'cambio $2.50' + diferencia
        a2 = out_back(prog(t, tp, tp + 0.3))
        pr.bubble(cv, 800, 940, 360, 96, "Paga $20", (0, 50), 42, a=min(1, a2), scale=a2)
        a3 = out_back(prog(t, tc - 0.1, tc + 0.2))
        pr.bubble(cv, 520, 760, 330, 96, "Cambio $2.50", (-60, 50), 38, color="#E8FFF1", a=min(1, a3), scale=a3)
        if t > tc + 0.8:
            ap = out_back(prog(t, tc + 0.8, tc + 1.15))
            pr.bubble(cv, 330, 730, 250, 110, "¿?", (0, 50), 70, color="#FFE1E1", tcolor="#C0392B", a=min(1, ap), scale=ap)
    else:
        lt = t - split
        camera(cv, 540, 960, 1.0)
        rectp(cv, 0, 0, 1080, 1920, grad(0, 0, 0, 1920, "#10161F", "#1D2733"))
        # pantalla del registro con operaciones
        rect(cv, 70, 330, 940, 1020, "#0A130F", r=30)
        rect(cv, 70, 330, 940, 1020, "#2FA36B", 0.8, style="stroke", sw=6, r=30)
        text(cv, "REGISTRO · PAGOS EN EFECTIVO", 540, 410, 36, "#7CFFB2", font=FONT_MONO)
        ops = [("20.00", "2.50", "-0.50"), ("50.00", "11.20", "-0.80"), ("10.00", "3.15", "-1.20"), ("20.00", "6.80", "-0.50")]
        for i, (pay, chg, dif) in enumerate(ops):
            y = 500 + i * 190
            a = out_back(prog(lt, 0.15 + i * 0.45, 0.45 + i * 0.45))
            if a <= 0:
                continue
            cv.save(); cv.translate(540, y); cv.scale(1, a)
            rect(cv, -420, -62, 840, 150, "#13261C", r=16)
            text(cv, f"EFECTIVO ${pay}", -390, -12, 34, "#CFF7E0", "left", font=FONT_MONO)
            text(cv, f"CAMBIO ${chg}", -390, 50, 34, "#CFF7E0", "left", font=FONT_MONO)
            blink = 0.6 + 0.4 * pulse(lt * 2 + i, 1)
            text(cv, f"DIF {dif.replace('-', '−')}", 410, 26, 52, "#FF6B6B", "right", font=FONT_MONO, a=blink)
            cv.restore()
        ring = prog(lt, 0.4, 0.9)
        if ring > 0:
            circ(cv, 800, 560, 120 * ease_out(ring), "#FFD166", style="stroke", w=10)
        pr.magnifier(cv, 790 + 30 * math.sin(lt * 1.5), 600, 100)
        draw_character(cv, "mateo", 190, 2020, 1.5, pose={"head_tilt": -8 if lt > 0.5 else 0}, t=t, mood="focus", look=(1, -0.6))
        a = out_back(prog(lt, 0.6, 1.0))
        pr.bubble(cv, 330, 1540, 240, 110, "¿?", (-30, 50), 70, color="#FFF3C4", a=min(1, a), scale=a)


# ======================================================================
# S7 · «Decidió observar con más atención»
# ======================================================================
def s7(cv, t, sc):
    d = sc["dur"]; k = t / d
    camera(cv, lerp(540, 600, k), 900, lerp(1.7, 2.35, ease_io(k)))
    blur_begin(cv, 14)
    pr.bg_store(cv, 540, t, dim=0.12)
    draw_character(cv, "dario", 760, 1330, 1.0, pose={"armR": (-30, -60)}, t=t, mood="smirk", look=(-1, 0.3))
    cv.restore()
    draw_character(cv, "mateo", 480, 1500, 1.9, pose={"armL": (10, 5), "armR": (-10, -5)}, t=t, mood="focus",
                   look=(lerp(-0.6, 1.0, ease_io(prog(t, 0.2, 1.1))), 0.1))
    # destello de idea / lupa al lado
    a = prog(t, 0.8, 1.2)
    if a > 0:
        for i in range(5):
            ang = -2.2 + i * 0.35
            line(cv, 600 + math.cos(ang) * 190, 720 + math.sin(ang) * 190, 600 + math.cos(ang) * (230 + 25 * a), 720 + math.sin(ang) * (230 + 25 * a), "#FFD166", 8, a)
    # libreta que se llena
    nb = prog(t, 0.2, 0.7)
    if nb > 0:
        rect(cv, 780, 1180 + 120 * (1 - ease_out(nb)), 230, 170, "#FFF8D6", r=10)
        for i in range(4):
            w = 150 * clamp(prog(t, 0.8 + i * 0.3, 1.1 + i * 0.3))
            line(cv, 800, 1220 + i * 32 + 120 * (1 - ease_out(nb)), 800 + w, 1220 + i * 32 + 120 * (1 - ease_out(nb)), "#7A6A3A", 5)


# ======================================================================
# S8 · de noche, revisa las grabaciones y descubre el truco
# ======================================================================
def trick_closeup(cv, lt, ts):
    """Ilustración del fraude: devolución falsa + billete al bolsillo.
    ts = instante (local) del sello ¡FRAUDE!, tomado de la narración."""
    rectp(cv, 0, 0, 1080, 1920, grad(0, 0, 0, 1920, "#1B2A3A", "#0E1620"))
    t_dev, t_open, t_m0, t_m1 = ts * 0.22, ts * 0.42, ts * 0.52, ts * 0.86
    pr.register(cv, 420, 1500, 1.35, lt, drawer=ease_out(prog(lt, t_open, t_open + 0.3)) * (1 - ease_out(prog(lt, t_m1, t_m1 + 0.3))),
                screen="DEVOL -$15" if lt > t_dev else "$ 0.00", screen_color="#FFB86B", alert=0.0)
    k = ease_io(prog(lt, t_m0, t_m1))
    draw_character(cv, "dario", 380, 1390, 1.55,
                   pose={"armR": (lerp(-30, 120, k), lerp(-50, 150, k)), "armL": (30, 40)},
                   t=lt, mood="smirk", look=(0.8, 0.3))
    if t_open <= lt < t_m1 + 0.05:
        a = arc_pt((560, 1130), (330, 1040), k, 140) if lt >= t_m0 else (560, 1130)
        pr.bill(cv, a[0], a[1], rot=lerp(0, -70, k), s=0.95, a=1 - 0.7 * prog(k, 0.85, 1.0))
    a1 = out_back(prog(lt, t_dev, t_dev + 0.3))
    pr.bubble(cv, 620, 500, 560, 110, "DEVOLUCIÓN FALSA", (0, 50), 44, color="#FFE1B8", a=min(1, a1), scale=a1)
    a2 = out_back(prog(lt, ts, ts + 0.3))
    if a2 > 0:
        pr.stamp(cv, 560, 690, "¡FRAUDE!", "#FF3B3B", -10, a2, min(1, a2), 96)


def s8(cv, t, sc):
    d = sc["dur"]; T, a0 = sc["T"], sc["a"]
    ta = T.word("d5", "revis") - a0 - 0.1        # «revisó las grabaciones»
    tb = T.word("d5", "descubri") - a0 - 0.1     # «descubrió…»
    tc = T.word("d5", "utiliz") - a0 - 0.1       # «utilizaba un truco»
    tm = T.word("d5", "quedarse") - a0           # «quedarse con el dinero»
    sc["tt"] = (ta, tb, tc, tm)
    if t < ta:
        lt = t
        camera(cv, 540, 960, lerp(1.0, 1.1, t / ta))
        pr.bg_office(cv, lt, night=True)
        # reloj de pared
        circ(cv, 540, 1000, 120, "#EDEFF2"); circ(cv, 540, 1000, 120, "#2B3038", style="stroke", w=10)
        for i in range(12):
            a = i * math.pi / 6
            line(cv, 540 + math.sin(a) * 100, 1000 - math.cos(a) * 100, 540 + math.sin(a) * 112, 1000 - math.cos(a) * 112, "#2B3038", 5)
        line(cv, 540, 1000, 540 + math.sin(math.radians(352)) * 70, 1000 - math.cos(math.radians(352)) * 70, "#2B3038", 9)
        line(cv, 540, 1000, 540 + math.sin(math.radians(282 + lt * 8)) * 96, 1000 - math.cos(math.radians(282 + lt * 8)) * 96, "#C0392B", 5)
        text(cv, "11:47 PM", 540, 1180, 58, "#F2D27A", font=FONT_MONO)
        rect(cv, 0, 1340, 1080, 580, "#4A3A2C")
        rect(cv, 0, 1340, 1080, 24, "#6B5440")
        draw_character(cv, "mateo", 330, 1700, 1.8, pose={"armR": (-100, -85), "armL": (60, 80)}, t=t, mood="focus", look=(1, 0))
        rect(cv, 580, 1250, 360, 230, "#1F242B", r=14)
        rect(cv, 595, 1265, 330, 190, "#16352B", r=8)
        pr.cctv_feed(cv, 595, 1265, 330, 190, lt, label="CAM 02", clipped=True)
        line(cv, 130, 1340, 190, 1130, "#9AA5B1", 12); line(cv, 190, 1130, 270, 1100, "#9AA5B1", 12)
        poly(cv, [(230, 1070), (340, 1090), (330, 1130), (250, 1130)], "#F2B632")
        poly(cv, [(250, 1130), (330, 1130), (420, 1340), (190, 1340)], "#FFF2B0", 0.14)
    elif t < tb:
        lt = t - ta
        camera(cv, 540, 900, lerp(1.0, 1.04, lt / (tb - ta)))
        rectp(cv, 0, 0, 1080, 1920, grad(0, 0, 0, 1920, "#10161F", "#0A0E14"))
        pr.monitor_frame(cv, 90, 330, 900, 640)
        secs = int((15 * 3600 + 42 * 60 + 18) - lt * 5200)
        hh, mm, ss = secs // 3600 % 24, secs // 60 % 60, secs % 60
        gl = 0.5 + 0.5 * math.sin(lt * 30)
        pr.cctv_feed(cv, 90, 330, 900, 640, lt * 3, label="CAM 02", glitch=gl * 0.8)
        text(cv, f"{hh:02d}:{mm:02d}:{ss:02d}", 540, 920, 52, "#9BFFD1", font=FONT_MONO)
        for i in range(2):
            ox = 540 - 60 + i * 60 - ((lt * 160) % 60)
            poly(cv, [(ox + 40, 600), (ox + 40, 700), (ox - 20, 650)], "#FFFFFF", 0.85)
        draw_character(cv, "mateo", 540, 2060, 1.7, pose={}, t=t, mood="focus", look=(0, -0.5))
    elif t < tc:
        lt = t - tb
        camera(cv, 540, 900, 1.0)
        rectp(cv, 0, 0, 1080, 1920, grad(0, 0, 0, 1920, "#10161F", "#0A0E14"))
        pr.monitor_frame(cv, 90, 330, 900, 640)
        hot = (420 + 20 * math.sin(lt * 4), 620, 360, 250) if lt > (tc - tb) * 0.4 else None
        pr.cctv_feed(cv, 90, 330, 900, 640, lt, mode=1, label="CAM 02", hot=hot)
        secs = 2 * 3600 + 13 * 60 + 44 + int(lt * 4)
        text(cv, f"{secs // 3600:02d}:{secs // 60 % 60:02d}:{secs % 60:02d}", 540, 920, 52, "#9BFFD1", font=FONT_MONO)
        a = out_back(prog(lt, (tc - tb) * 0.4, (tc - tb) * 0.4 + 0.25))
        pr.bubble(cv, 540, 1130, 700, 120, "¡Algo no cuadra!", (0, 50), 52, color="#FFE1E1", tcolor="#C0392B", a=min(1, a), scale=a)
        draw_character(cv, "mateo", 540, 2100, 1.7, pose={}, t=t, mood="shock" if hot else "focus", look=(0, -0.6))
    else:
        lt = t - tc
        camera(cv, 540, 960, 1.0 + 0.03 * (lt / max(0.1, d - tc)))
        trick_closeup(cv, lt, tm - tc)


# ======================================================================
# S9 · semanas de fraude que nadie revisaba
# ======================================================================
def s9(cv, t, sc):
    d = sc["dur"]; k = t / d
    camera(cv, 540, 960, 1.0)
    pr.bg_store(cv, 540, t, dim=0.18, shelves=False)
    rect(cv, 0, 0, 1080, 1250, "#DCE6EC", 0.92)
    # calendario con páginas que se pasan
    wk = int(t / 0.62)
    prog_pg = (t / 0.62) % 1.0
    cv.save(); cv.translate(540, 410)
    rect(cv, -330, -240, 660, 500, "#000000", 0.22, r=24)
    rect(cv, -340, -250, 680, 500, "#FFFFFF", r=24)
    rect(cv, -340, -250, 680, 110, "#E74C3C", r=24)
    rect(cv, -340, -190, 680, 50, "#E74C3C")
    for sx in (-200, 0, 200):
        rect(cv, sx - 12, -285, 24, 70, "#3B4048", r=10)
    text(cv, "SEMANA %d" % min(8, wk + 1), 0, -168, 62, "#FFFFFF")
    for r_ in range(4):
        for c_ in range(7):
            filled = (r_ * 7 + c_) <= (wk * 7 + prog_pg * 7)
            circ(cv, -255 + c_ * 85, -60 + r_ * 75, 25, "#E74C3C" if filled else "#E9EEF2", 0.9 if filled else 1)
    # hoja que voltea
    a = ease_io(prog_pg)
    if wk < 8 and prog_pg > 0.55:
        sq = math.cos(prog(prog_pg, 0.55, 1.0) * math.pi / 2)
        cv.save(); cv.translate(0, -250); cv.scale(1, max(0.02, sq)); rect(cv, -340, 0, 680, 500, "#F3F6F9", r=24); cv.restore()
    cv.restore()
    # Darío repite el truco
    draw_character(cv, "dario", 330, 1370, 1.45, pose={"armR": (lerp(-30, -140, pulse(t, 0.62)), -150 * pulse(t, 0.62)), "armL": (30, 40)}, t=t, mood="smirk", look=(0.8, 0.3))
    pr.register(cv, 360, 1480, 1.2, t, screen="DEVOL", screen_color="#FFB86B", drawer=0.5 * pulse(t, 0.62))
    for i in range(5):
        tt = (t - i * 0.62) % 3.1
        pk = prog(tt, 0, 0.6)
        if 0 < pk < 1 and t > i * 0.62:
            x, y = arc_pt((520, 1070), (230, 1050), pk, 120)
            pr.coin(cv, x, y, 20, spin=t * 14)
    total = min(7430, 7430 * ease_in(prog(t, 0.3, d - 0.3)))
    pr.hud_card(cv, 540, 1740, 700, 150, "ROBADO EN SILENCIO", pr.money_fmt(total, "-"), "#FF5A5A", a=1.0)
    # pila de recibos pequeños sin revisar (con polvo y Zzz)
    cv.save(); cv.translate(850, 1190)
    for i in range(6):
        pr.paper(cv, 0, -i * 22, 200, 150, rot=(i % 3 - 1) * 4, lines=3, a=1.0, color="#E4E0D3")
    rect(cv, -110, -240, 220, 60, "#C0392B", r=10)
    text(cv, "< $20", 0, -197, 36, "#FFFFFF")
    text(cv, "SIN REVISAR", 0, 54, 28, "#5B6670")
    for i in range(3):
        text(cv, "z", 70 + i * 34, -280 - i * 46 - 12 * math.sin(t * 2 + i), 40 + i * 14, "#6B7885", a=0.9)
    cv.restore()
    # gerente pasa de largo sin mirar
    mx = lerp(-250, 1400, prog(t, 1.2, d))
    draw_character(cv, "ramirez", mx, 1840, 1.25, pose={"walk": t * 6, "armL": (-20, -40), "armR": (30, 50)}, t=t, mood="neutral", look=(1, 0))


# ======================================================================
# S10 · la suma revela la pérdida enorme
# ======================================================================
def s10(cv, t, sc):
    d = sc["dur"]; k = t / d
    T, a0 = sc["T"], sc["a"]
    tr = T.word("c1", "enorme") - a0 - 0.15      # revelación de la pérdida
    c0, c1 = 0.2, tr
    camera(cv, 540, 960, lerp(1.0, 1.05, k))
    pr.bg_office(cv, t)
    rect(cv, 0, 0, 1080, 1920, "#0B0F14", 0.45)
    # panel de hoja de cálculo
    rect(cv, 60, 130, 960, 680, "#0F1720", r=30)
    rect(cv, 60, 130, 960, 680, "#4FA3FF", 0.8, style="stroke", sw=5, r=30)
    text(cv, "OPERACIONES PEQUEÑAS", 540, 205, 44, "#9CC9FF")
    r_ = rnd(3)
    n_rows = 7
    shown = int(prog(t, c0, c1) * 60)
    for i in range(n_rows):
        idx = shown - (n_rows - 1) + i
        if idx < 0:
            continue
        amt = [5, 8, 12, 15, 20, 18, 9, 14][idx % 8]
        y = 260 + i * 66
        rect(cv, 90, y, 900, 54, "#16212E" if i % 2 else "#1B2938", r=8)
        text(cv, f"DEVOL #{1000 + idx}", 120, y + 38, 30, "#9CC9FF", "left", font=FONT_MONO)
        text(cv, f"−${amt}.00", 960, y + 38, 32, "#FF8A8A", "right", font=FONT_MONO)
    # contador
    cnt = int(412 * ease_io(prog(t, c0, c1)))
    val = 7430 * ease_io(prog(t, c0, c1))
    rect(cv, 60, 850, 960, 400, "#0F1720", r=30)
    rect(cv, 60, 850, 960, 400, "#FF5A5A", 0.9, style="stroke", sw=6, r=30)
    text(cv, f"{cnt} operaciones sumadas", 540, 925, 40, "#C7D0DA")
    big = prog(t, tr, tr + 0.4)
    scale = 1.0 + 0.16 * math.sin(min(1, big) * math.pi) if big > 0 else 1.0
    cv.save(); cv.translate(540, 1070); cv.scale(scale, scale)
    text(cv, pr.money_fmt(val, "-"), 0, 40, 130, "#FF5A5A", font=FONT_MONO, outline="#2B0A0A", outline_w=10)
    cv.restore()
    # torre de monedas crece
    for i in range(int(40 * ease_io(prog(t, c0, c1)))):
        col, row = i % 5, i // 5
        pr.coin(cv, 150 + col * 44, 1400 - row * 14, 22, spin=0.0)
    # reacciones
    draw_character(cv, "ramirez", 640, 2080, 1.55, pose={"armL": (160, 150), "armR": (-160, -150)} if t > tr else {}, t=t,
                   mood="shock" if t > tr else "worry", look=(0, -0.4))
    draw_character(cv, "mateo", 910, 2060, 1.4, pose={"armR": (-30, -60)}, t=t, mood="focus" if t < tr else "smile", look=(-1, -0.3))
    if t > tr:
        for i in range(3):
            y = 1560 - 40 * ((t * 3 + i) % 3)
            circ(cv, 760 + i * 20, y, 8, "#8FD4FF", 0.9)
    if t > tr + 0.1 and int(t * 5) % 2 == 0:
        rect(cv, -200, -200, 1500, 2300, "#FF2B2B", 0.06)


# ======================================================================
# S11 · el empleado es descubierto · nuevos controles
# ======================================================================
def s11(cv, t, sc):
    d = sc["dur"]; T, a0 = sc["T"], sc["a"]
    split = T.word("c2", "supermercado") - a0 - 0.2
    tdesc = T.word("c2", "descubierto") - a0
    sc["tt"] = (split, tdesc)
    if t < split:
        camera(cv, 560, 960, lerp(1.0, 1.1, t / split))
        pr.bg_store(cv, 560, t, dim=0.15, shelves=False)
        rect(cv, -400, 0, 2000, 1250, "#DCE6EC", 0.92)
        draw_character(cv, "ramirez", 250, 1520, 1.6, pose={"armR": (-100, -115 + 6 * math.sin(t * 8)), "armL": (10, 15)}, t=t, mood="angry", talk=0.4 + 0.5 * math.sin(t * 13), look=(1, 0))
        draw_character(cv, "mateo", 120, 1700, 1.5, pose={"armR": (-10, -5)}, t=t, mood="smile", look=(1, 0))
        draw_character(cv, "dario", 720, 1520, 1.6, pose={"armL": (30, 40), "armR": (-35, -30), "head_tilt": 10, "head_dx": 6}, t=t, flip=True, mood="sad", look=(0, 1))
        draw_character(cv, "guardia", 980, 1510, 1.6, pose={"armL": (35, 120), "armR": (-35, -120)}, t=t, flip=True, mood="neutral", look=(-1, 0))
        # billetes en la mano
        pr.bill(cv, 620, 1040, rot=20 + 6 * math.sin(t * 5), s=1.0)
        pr.bill(cv, 650, 1000, rot=-10, s=0.9)
        a = out_back(prog(t, tdesc - 0.2, tdesc + 0.2))
        pr.stamp(cv, 580, 640, "DESCUBIERTO", "#E74C3C", -9, a, min(1, a), 84)
    else:
        lt = t - split
        camera(cv, 540, 960, lerp(1.0, 1.06, lt / max(0.1, d - split)))
        pr.bg_office(cv, t)
        rect(cv, 0, 0, 1080, 1920, "#0B1A2C", 0.55)
        # escudo
        s = out_back(prog(lt, 0.0, 0.4))
        cv.save(); cv.translate(540, 360); cv.scale(s, s)
        poly(cv, [(-170, -170), (170, -170), (170, 20), (0, 220), (-170, 20)], "#2B78D6")
        poly(cv, [(-140, -140), (140, -140), (140, 10), (0, 180), (-140, 10)], "#3A93F5")
        cv.restore()
        pr.check(cv, 540, 380, 160, "#FFFFFF", prog(lt, 0.3, 0.7), 26)
        items = ["Revisión diaria de devoluciones", "Doble autorización de cambios", "Alertas por montos pequeños"]
        for i, it in enumerate(items):
            a = out_back(prog(lt, 0.45 + i * 0.3, 0.8 + i * 0.3))
            if a <= 0:
                continue
            cv.save(); cv.translate(540, 800 + i * 170); cv.scale(a, a)
            rect(cv, -450, -62, 900, 124, "#102236", r=26)
            rect(cv, -450, -62, 900, 124, "#4FA3FF", 0.9, style="stroke", sw=4, r=26)
            pr.check(cv, -390, 4, 60, "#2ECC71", prog(a, 0.7, 1.0), 12)
            text(cv, it, -330, 16, 36, "#FFFFFF", "left")
            cv.restore()
        # candado
        lk = ease_out(prog(lt, 1.2, 1.6))
        cv.save(); cv.translate(540, 1470)
        path = skia.Path(); path.addArc(skia.Rect.MakeXYWH(-60, -150 - 40 * (1 - lk), 120, 150), 180, 180)
        cv.drawPath(path, P("#B0B8C2", 1, "stroke", 24))
        rect(cv, -110, -30, 220, 170, "#F2B632", r=26)
        circ(cv, 0, 40, 18, "#7A5A0A"); rect(cv, -6, 44, 12, 40, "#7A5A0A")
        cv.restore()
        draw_character(cv, "ramirez", 220, 2040, 1.35, pose={"armR": (-75, -110)}, t=t, mood="smile", look=(1, 0))
        draw_character(cv, "mateo", 860, 2040, 1.35, pose={"armL": (75, 110)}, t=t, flip=True, mood="smile", look=(-1, 0))


# ======================================================================
# S12 · final memorable: una moneda → una montaña
# ======================================================================
def s12(cv, t, sc):
    d = sc["dur"]; k = t / d
    T, a0 = sc["T"], sc["a"]
    tz0 = T.word("c3", "sino") - a0 - 0.6       # comienza el alejamiento
    tz1 = tz0 + 3.4
    sc["tt"] = (tz0, tz1)
    # la cámara se aleja revelando la montaña de monedas
    zoom = lerp(2.6, 0.78, ease_io(prog(t, tz0, tz1)))
    cy = lerp(1190, 1020, ease_io(prog(t, tz0, tz1)))
    camera(cv, 540, cy, zoom)
    pr.bg_store(cv, 540, t, tint=("#FFB45A", 0.12))
    # mostrador
    rect(cv, -600, 1330, 2280, 60, "#C9885A", r=12)
    rect(cv, -600, 1380, 2280, 420, "#8E5A3C")
    # montaña de monedas
    N = 420
    r_ = rnd(21)
    pile = []
    for i in range(N):
        u = r_.random() + r_.random() - 1.0
        x = 540 + u * 430
        h = 1000 * max(0.0, 1 - abs(u)) ** 1.1
        y = 1330 - h * (0.25 + 0.75 * (i / N)) + (r_.random() - 0.5) * 20
        pile.append((x, y, i))
    start = tz0 - 1.4
    for x, y, i in pile:
        t0 = start + (i / N) * (tz1 - 0.2)
        if t < t0:
            continue
        fall = prog(t, t0, t0 + 0.55)
        yy = lerp(y - 1400, y, ease_in(fall) if fall < 1 else 1)
        a = 1.0
        if i == 0:
            continue
        pr.coin(cv, x, yy, 30, spin=(t - t0) * 9 if fall < 1 else 0.3 + (i % 5) * 0.2)
    # moneda protagonista sobre el mostrador
    glow = 0.5 + 0.5 * pulse(t, 1.4)
    cv.drawCircle(540, 1260, 150, radial(540, 1260, 150, "#FFE98A", "#FFE98A", 0.55 * glow * (1 - prog(t, tz0 + 0.6, tz1)), 0.0))
    pr.coin(cv, 540, 1270, 52, spin=t * 3.0)
    # lupa sobre la moneda
    if t < tz0 + 0.6:
        pr.magnifier(cv, 590 + 20 * math.sin(t * 1.3), 1210, 105)
    # Mateo y Ramírez observan
    draw_character(cv, "mateo", 150, 1360, 1.75, pose={"armR": (-30, -50)}, t=t, mood="focus" if t < tz0 + 0.6 else "smile", look=(1, 0))
    draw_character(cv, "ramirez", 930, 1360, 1.75, pose={"armL": (30, 40)}, t=t, flip=True, mood="neutral" if t < tz0 + 0.6 else "smile", look=(-1, 0))
    # texto final (en coordenadas de pantalla)
    cv.resetMatrix()
    tf = T.word('c3', 'nadie') - a0
    ta = smooth(prog(t, tf - 1.0, tf - 0.3))
    if ta > 0:
        cv.drawRect(skia.Rect.MakeXYWH(0, 0, 1080, 1920), grad(0, 0, 0, 1920, "#000000", "#000000", 0.0, 0.0))
        cv.drawRect(skia.Rect.MakeXYWH(0, 250, 1080, 520), grad(0, 250, 0, 770, "#05080F", "#05080F", 0.0, 0.0))
        rect(cv, 60, 330, 960, 330, "#05080F", 0.72 * ta, r=40)
        rect(cv, 60, 330, 960, 330, "#FFD166", 0.9 * ta, style="stroke", sw=5, r=40)
        text(cv, "LAS PEQUEÑAS", 540, 450 + 20 * (1 - ta), 84, "#FFFFFF", a=ta)
        text(cv, "CANTIDADES CUENTAN", 540, 560 + 20 * (1 - ta), 62, "#FFD166", a=ta)
        line(cv, 300, 610, 780, 610, "#FFD166", 6, ta)


SCENES = [
    ("s1", "h1", "h1", s1),
    ("s2", "h2", "h2", s2),
    ("s3", "h3", "h3", s3),
    ("s4", "d1", "d1", s4),
    ("s5", "d2", "d2", s5),
    ("s6", "d3", "d3", s6),
    ("s7", "d4", "d4", s7),
    ("s8", "d5", "d5", s8),
    ("s9", "d6", "d6", s9),
    ("s10", "c1", "c1", s10),
    ("s11", "c2", "c2", s11),
    ("s12", "c3", "c3", s12),
]

# transición de ENTRADA de cada escena (la 1.ª no tiene)
TRANSITIONS = {
    "s2": "whip", "s3": "flash", "s4": "iris", "s5": "fade", "s6": "whip",
    "s7": "iris", "s8": "glitch", "s9": "whip", "s10": "flash", "s11": "whip", "s12": "fade",
}
