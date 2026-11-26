"""Escenas 5 (ceguera al cambio), 6 (conclusión) y 7 (marca)."""
import math, os
import numpy as np
from PIL import Image, ImageDraw
from common import *
from assets import *
from scenes_a import bez, poly_at, draw_poly, pulse_on, nerve_paths, paste_brain, brain_rim, BRAIN_C, EYE_L, EYE_R
import words as _w

ALIGN = os.path.join(ROOT, "storage", "explora_ciencia360", "audio", "alignment.json")

# ===================================================== ESCENA 5
AW, AH = 960, 680
_art = {}
def landscape(with_balloon):
    key = with_balloon
    if key in _art:
        return _art[key]
    ss = 2
    im = Image.new("RGBA", (AW * ss, AH * ss))
    d = ImageDraw.Draw(im)
    for y in range(AH * ss):
        k = y / (AH * ss * .62)
        c = mix((24, 34, 110), (255, 150, 105), clamp(k) ** 1.4)
        d.line([0, y, AW * ss, y], fill=tuple(int(v) for v in c) + (255,))
    d.ellipse([(300 - 80) * ss, (380 - 80) * ss, (300 + 80) * ss, (380 + 80) * ss], fill=(255, 226, 150, 255))
    rng = np.random.RandomState(3)
    for (cx_, cy_, s_) in ((150, 140, 1.0), (520, 90, .8), (860, 170, 1.1)):
        for dx, dy, r in ((-40, 6, 34), (0, -10, 44), (46, 4, 36), (14, 12, 38)):
            d.ellipse([(cx_ + dx * s_ - r * s_) * ss, (cy_ + dy * s_ - r * .7 * s_) * ss, (cx_ + dx * s_ + r * s_) * ss, (cy_ + dy * s_ + r * .7 * s_) * ss], fill=(255, 220, 215, 200))
    def ridge(base, amp, col, seed, step=60):
        r = np.random.RandomState(seed); pts = [(0, AH)]
        for x in range(0, AW + step, step):
            pts.append((x, base - amp * r.rand()))
        pts.append((AW, AH)); d.polygon([(x * ss, y * ss) for x, y in pts], fill=col)
    ridge(400, 150, (96, 70, 150, 255), 1)
    ridge(450, 110, (62, 56, 128, 255), 2, 80)
    ridge(520, 70, (34, 70, 110, 255), 3, 100)
    # lago
    d.rectangle([0, 560 * ss, AW * ss, AH * ss], fill=(30, 90, 140, 255))
    for i in range(10):
        y = (575 + i * 11) * ss
        d.line([(60 + i * 70) * ss, y, (170 + i * 70) * ss, y], fill=(255, 190, 150, 160), width=3 * ss)
    # colina y casa
    d.ellipse([-200 * ss, 520 * ss, 700 * ss, 800 * ss], fill=(36, 120, 90, 255))
    d.rectangle([380 * ss, 470 * ss, 520 * ss, 552 * ss], fill=(245, 230, 205, 255))
    d.polygon([(365 * ss, 472 * ss), (450 * ss, 405 * ss), (535 * ss, 472 * ss)], fill=(220, 50, 55, 255))
    d.rectangle([435 * ss, 505 * ss, 465 * ss, 552 * ss], fill=(110, 70, 40, 255))
    d.rectangle([397 * ss, 485 * ss, 425 * ss, 510 * ss], fill=(255, 210, 100, 255))
    d.rectangle([478 * ss, 485 * ss, 506 * ss, 510 * ss], fill=(255, 210, 100, 255))
    # árboles
    for (tx, ty, sz) in ((250, 540, 1.0), (640, 530, 1.25), (120, 555, .8)):
        d.rectangle([(tx - 8 * sz) * ss, ty * ss, (tx + 8 * sz) * ss, (ty + 60 * sz) * ss], fill=(90, 55, 35, 255))
        for dx, dy, r in ((0, -20, 46), (-28, 4, 34), (28, 4, 34)):
            d.ellipse([(tx + dx * sz - r * sz) * ss, (ty + dy * sz - r * sz) * ss, (tx + dx * sz + r * sz) * ss, (ty + dy * sz + r * sz) * ss], fill=(28, 150, 90, 255))
    if with_balloon:
        bx, by, R = 735, 235, 88
        d.ellipse([(bx - R) * ss, (by - R * 1.12) * ss, (bx + R) * ss, (by + R * 1.0) * ss], fill=(255, 205, 60, 255))
        for i, col in enumerate(((235, 55, 70), (40, 120, 235), (235, 55, 70))):
            x0 = bx - R + i * R * 2 / 3 * 1.0 + (R * 2 / 3) * .0
        d.pieslice([(bx - R) * ss, (by - R * 1.12) * ss, (bx + R) * ss, (by + R) * ss], 230, 310, fill=(235, 55, 70, 255))
        d.pieslice([(bx - R) * ss, (by - R * 1.12) * ss, (bx + R) * ss, (by + R) * ss], 310, 350, fill=(40, 120, 235, 255))
        d.pieslice([(bx - R) * ss, (by - R * 1.12) * ss, (bx + R) * ss, (by + R) * ss], 190, 230, fill=(40, 120, 235, 255))
        d.polygon([((bx - R * .55) * ss, (by + R * .75) * ss), ((bx + R * .55) * ss, (by + R * .75) * ss), ((bx + 24) * ss, (by + R * 1.45) * ss), ((bx - 24) * ss, (by + R * 1.45) * ss)], fill=(235, 55, 70, 255))
        d.rectangle([(bx - 28) * ss, (by + R * 1.45) * ss, (bx + 28) * ss, (by + R * 1.75) * ss], fill=(120, 75, 40, 255))
        d.line([(bx - 26) * ss, (by + R * 1.45) * ss, (bx - R * .5) * ss, (by + R * .8) * ss], fill=(60, 40, 30, 255), width=3 * ss)
        d.line([(bx + 26) * ss, (by + R * 1.45) * ss, (bx + R * .5) * ss, (by + R * .8) * ss], fill=(60, 40, 30, 255), width=3 * ss)
    im = im.resize((AW, AH), Image.LANCZOS)
    m = Image.new("L", (AW * 2, AH * 2), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, AW * 2, AH * 2], radius=70, fill=255)
    im.putalpha(m.resize((AW, AH), Image.LANCZOS))
    _art[key] = im
    return im


def _panel(f, im, cx, cy, s, alpha=1.0):
    w, h = int(AW * s), int(AH * s)
    r = im.resize((w, h), Image.LANCZOS)
    if alpha < 1:
        r.putalpha(r.getchannel("A").point(lambda v: int(v * alpha)))
    f.paste_rgba(r, (cx - w / 2, cy - h / 2))


def _frame_outline(f, cx, cy, s, a=1.0, color=CYAN):
    lay, ld = f.new_layer()
    w, h = AW * s, AH * s
    ld.rounded_rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], radius=70 * s, outline=sc(color, .9 * a), width=5)
    f.add_glow_layer(lay, 12, .9)


def _badge(f, txt, x, y, a):
    lay, ld = f.new_layer()
    ld.ellipse([x - 34, y - 34, x + 34, y + 34], outline=sc(CYAN, a), width=4)
    fo = font(40)
    wd = fo.getlength(txt)
    ld.text((x - wd / 2, y - 27), txt, font=fo, fill=sc(WHITE, a))
    f.add_glow_layer(lay, 8, .8)


def scene_ceguera(t):
    f = Frame(); L = f.L
    A, B = landscape(True), landscape(False)
    cx = 540
    # fase 1/2: A aparece; luego A y B apiladas (casi idénticas)
    stack = ease_io(prog(t, 1.0, 1.9)) * (1 - ease_io(prog(t, 4.3, 5.0)))
    ap = ease_back(prog(t, 0.0, 0.7))
    if t < 5.1:
        s = lerp(1.0, .73, stack) * (0.85 + .15 * ap)
        yA = lerp(800, 560, stack); yB = lerp(800, 1100, stack)
        if stack > 0.01:
            _panel(f, B, cx, yB, s, alpha=stack)
            _frame_outline(f, cx, yB, s, stack)
            _badge(f, "B", 120, yB - AH * s / 2 + 20, stack)
        _panel(f, A, cx, yA, s, alpha=clamp(ap * 1.5))
        _frame_outline(f, cx, yA, s, ap)
        if stack > 0.01:
            _badge(f, "A", 120, yA - AH * s / 2 + 20, stack)
        # retícula de exploración
        if 1.9 < t < 4.5:
            rt = (t - 1.9) / 2.6
            for (yy, k) in ((yA, 0), (yB, 1)):
                px = cx - 330 + 660 * ((rt * 1.3 + k * .4) % 1.0); py = yy + 70 * math.sin(rt * 9 + k)
                rr = 46
                L.ellipse([px - rr, py - rr, px + rr, py + rr], outline=sc(CYAN, .8 * stack), width=3)
                L.line([px - rr - 12, py, px - rr + 14, py], fill=sc(CYAN, .8 * stack), width=3)
                L.line([px + rr - 14, py, px + rr + 12, py], fill=sc(CYAN, .8 * stack), width=3)
    else:
        pcx, pcy = 540, 800
        s = 1.0
        shown = A
        blank = 0.0
        if t < 9.2:
            ph = (t - 5.0) % 1.36
            if ph < .5: shown = A
            elif ph < .68: blank = 1.0
            elif ph < 1.18: shown = B
            else: blank = 1.0
        elif t < 9.75:
            shown = A
        elif t < 10.2:
            shown = B
        else:
            shown = A if (int((t - 10.2) / 0.5) % 2 == 0) else B
        s = 1.0 + 0.04 * math.sin(t * .5)
        _panel(f, shown, pcx, pcy, s)
        if blank > 0:
            w_, h_ = int(AW * s), int(AH * s)
            gl = Image.new("RGBA", (w_, h_), (205, 214, 235, 245))
            m = Image.new("L", (w_, h_), 0)
            ImageDraw.Draw(m).rounded_rectangle([0, 0, w_, h_], radius=int(70 * s), fill=255)
            gl.putalpha(m.point(lambda v: int(v * .96)))
            f.paste_rgba(gl, (pcx - w_ / 2, pcy - h_ / 2))
        _frame_outline(f, pcx, pcy, s)
        px0, py0 = pcx - AW * s / 2, pcy - AH * s / 2
        # distracciones: orbes brillantes
        if 5.6 < t < 10.3:
            lay, ld = f.new_layer()
            for q in range(4):
                u = (t * (.45 + q * .13) + q * .27) % 2.0
                u = u if u < 1 else 2 - u
                ox = px0 + 80 + (AW - 160) * u
                oy = py0 + 120 + 420 * (0.5 + 0.5 * math.sin(t * (2.2 + q * .6) + q))
                col = (AMBER, MAGENTA, CYAN, VIOLET)[q]
                for j in range(6):
                    uu = max(0, u - j * .012)
                    rr = 20 - j * 2.5
                    ld.ellipse([ox - rr - j * 5 * (1 if q % 2 else -1), oy - rr, ox + rr - j * 5 * (1 if q % 2 else -1), oy + rr], fill=sc(col, .85 - j * .13))
            f.add_glow_layer(lay, 14, 1.1)
        # fogonazo mientras ocurre el cambio
        if 9.2 < t < 10.3:
            kk = 1 - abs((t - 9.75) / .55)
            if kk > 0:
                lay, ld = f.new_layer()
                rr = 60 + 160 * (1 - kk)
                ld.ellipse([pcx - rr, pcy - rr, pcx + rr, pcy + rr], fill=sc(WHITE, .55 * kk))
                f.add_glow_layer(lay, 40, 1.2, raw=False)
        # revelación: círculo sobre el globo
        if t > 10.2:
            kk = ease(prog(t, 10.2, 10.6))
            bxs, bys = px0 + 735 * s, py0 + 235 * s
            lay, ld = f.new_layer()
            rr = 150 * s * (1.15 - .15 * kk) + 6 * math.sin(t * 9)
            ld.ellipse([bxs - rr, bys - rr, bxs + rr, bys + rr], outline=sc(AMBER, kk), width=7)
            f.add_glow_layer(lay, 16, 1.2)
    particles(L, t, seed=21, n=50, tint=CYAN, alpha=.6)
    return f.finish()


# ===================================================== ESCENA 6 — CONCLUSIÓN
def scene_conclusion(t):
    f = Frame(); L = f.L
    z = lerp(0.86, 0.98, ease_io(prog(t, 0, 8.2)))
    cam = Cam(540, 940, z, rot=.05 * math.sin(t * .45))
    bx, by = BRAIN_C
    wave = ((t * .35) % 1.5) - .1
    occ = 0.35 + 0.15 * math.sin(t * 3)
    burst = ease(prog(t, 7.0, 7.6))
    if t > 7.05:
        wave = prog(t, 7.1, 8.4) * 1.4 - .1
        occ = 0.5 + 0.9 * burst
    paste_brain(f, t, cam, bx, by, wave=wave, occ=occ, glow=1.1 + burst)
    brain_rim(f, cam, bx, by, color=mix(CYAN, MAGENTA, burst), k=.6 + .3 * burst)
    pa = nerve_paths()
    lay, ld = f.new_layer()
    for key, pts in pa.items():
        draw_poly(ld, pts, cam, sc(CYAN, .6 + .3 * burst), 6 * cam.z)
    f.add_glow_layer(lay, 14, 1.0)
    for key, pts in pa.items():
        for q in range(4):
            s_ = (t * (.5 + .4 * burst) + q / 4.0 + (0 if key[0] == "e" else .25)) % 1.0
            pulse_on(L, pts, cam, s_, r=10)
    for (ex, ey, g) in ((EYE_L[0], EYE_L[1], 8), (EYE_R[0], EYE_R[1], -8)):
        x, y = cam.p(ex, ey)
        ic = eye_icon(int(400 * cam.z ** .5), gaze=(g + 10 * math.sin(t * .8), 10), open_=1 - .9 * math.sin(math.pi * prog(t, 3.1, 3.3)) ** 2)
        put_icon(f, ic, x, y, glow=.5, glow_r=14)
    # "observa el mundo": ondas que salen de los ojos
    if 4.5 < t < 7.4:
        lay, ld = f.new_layer()
        for (ex, ey) in (EYE_L, EYE_R):
            x, y = cam.p(ex, ey)
            for q in range(4):
                k = ((t - 4.5) * .55 + q / 4.0) % 1.0
                rr = cam.r(80 + 520 * k)
                a_ = (1 - k) * ease(prog(t, 4.5, 5.0)) * (1 - ease(prog(t, 6.9, 7.4)))
                ld.arc([x - rr, y - rr, x + rr, y + rr], 205, 335, fill=sc(CYAN, .9 * a_), width=4)
        f.add_glow_layer(lay, 10, 1.0)
    if burst > 0:
        lay, ld = f.new_layer()
        x, y = cam.p(bx, by + 100)
        rr = cam.r(120 + 700 * ease_out(prog(t, 7.0, 8.2)))
        ld.ellipse([x - rr, y - rr, x + rr, y + rr], outline=sc(MAGENTA, (1 - prog(t, 7.0, 8.2)) * .9), width=8)
        f.add_glow_layer(lay, 20, 1.2)
    # bokeh en primer plano (profundidad)
    rng = np.random.RandomState(31)
    lay, ld = f.new_layer()
    for i in range(14):
        x = (rng.rand() * W + t * 14 * (i % 3 + 1)) % W; y = (rng.rand() * H - t * 20 * (i % 4 + 1)) % H
        r = 22 + rng.rand() * 40
        ld.ellipse([x - r, y - r, x + r, y + r], fill=sc(mix(CYAN, VIOLET, rng.rand()), .13))
    f.add_glow_layer(lay, 10, .9, raw=True)
    particles(L, t, seed=33, n=60, tint=CYAN, alpha=.8)
    return f.finish()


# ===================================================== ESCENA 7 — MARCA
_msg = None
def _words():
    global _msg
    if _msg is None:
        ws = _w.load(ALIGN)
        _msg = [(w[0], w[1] - 55.25) for w in ws[157:]]
    return _msg


def spaced(L, txt, cx, y, fo, fill, sp, alpha_fn=None, t=0):
    widths = [fo.getlength(c) for c in txt]
    total = sum(widths) + sp * (len(txt) - 1)
    x = cx - total / 2
    for i, c in enumerate(txt):
        a = alpha_fn(i) if alpha_fn else 1.0
        if a > .01:
            off = (1 - ease_out(a)) * 30
            L.text((x, y + off), c, font=fo, fill=sc(fill, a))
        x += widths[i] + sp


def scene_marca(t):
    f = Frame(); L = f.L
    # fondo: ondas suaves
    cx, cy = 540, 700
    grow = ease_out(prog(t, 0.0, 1.2))
    lay, ld = f.new_layer()
    for k in range(3):
        a = math.radians(60 * k) + t * .35
        pts = []
        for i in range(91):
            u = i / 90 * 2 * math.pi
            ex, ey = 250 * math.cos(u), 86 * math.sin(u)
            pts.append((cx + ex * math.cos(a) - ey * math.sin(a), cy + ex * math.sin(a) + ey * math.cos(a)))
        # trazo progresivo
        n = int(len(pts) * grow)
        if n > 2:
            ld.line(pts[:n], fill=sc(mix(CYAN, VIOLET, k / 2), .85), width=5, joint="curve")
        e = (t * (.6 + .15 * k) + k / 3) % 1.0
        px, py = pts[int(e * 89)]
        ld.ellipse([px - 11, py - 11, px + 11, py + 11], fill=sc(WHITE, grow))
    # núcleo: iris luminoso
    rr = 56 * grow * (1 + .05 * math.sin(t * 4))
    for i in range(10):
        r = rr * (1 - i / 10)
        ld.ellipse([cx - r, cy - r, cx + r, cy + r], fill=sc(mix(BLUE, (255, 200, 90), i / 9), .95))
    ld.ellipse([cx - rr * .32, cy - rr * .32, cx + rr * .32, cy + rr * .32], fill=(0, 0, 0))
    f.add_glow_layer(lay, 16, 1.0)
    # onda de entrada
    if t < 1.2:
        kk = prog(t, 0, 1.2)
        lay2, l2 = f.new_layer()
        r_ = 80 + 800 * ease_out(kk)
        l2.ellipse([cx - r_, cy - r_, cx + r_, cy + r_], outline=sc(CYAN, (1 - kk) * .8), width=6)
        f.add_glow_layer(lay2, 14, 1.0)
    # wordmark
    lay3, l3 = f.new_layer()
    spaced(l3, "EXPLORA", 540, 930, font(140), WHITE, 10, lambda i: prog(t, .5 + i * .07, .9 + i * .07))
    spaced(l3, "CIENCIA 360", 540, 1090, font(84), CYAN, 14, lambda i: prog(t, 1.0 + i * .05, 1.4 + i * .05))
    f.add_glow_layer(lay3, 14, .7, soft=True)
    # línea decorativa
    wl = ease_out(prog(t, 1.4, 2.0)) * 250
    L.line([540 - wl, 1070, 540 + wl, 1070], fill=sc(CYAN, .7), width=3)
    # mensaje final, palabra a palabra sincronizado con la voz
    lay4, l4 = f.new_layer()
    ws = _words()
    line1, line2 = ws[:5], ws[5:]
    fo = font(54)
    for line, y in ((line1, 1290), (line2, 1380)):
        txt = " ".join(w for w, _ in line)
        total = fo.getlength(txt); x = 540 - total / 2
        for w, tw in line:
            a = ease(prog(t, tw - .05, tw + .25))
            hi = w in ("Explora", "Ciencia", "360")
            col = AMBER if hi else WHITE
            l4.text((x, y + (1 - a) * 18), w, font=fo, fill=sc(col, a))
            x += fo.getlength(w + " ")
    f.add_glow_layer(lay4, 8, .55, soft=False)
    particles(L, t, seed=41, n=70, tint=CYAN, alpha=.9)
    return f.finish()
