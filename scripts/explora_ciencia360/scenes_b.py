"""Escenas 3 (completar información) y 4 (punto ciego)."""
import math
import numpy as np
from PIL import Image, ImageDraw
from common import *
from assets import *
from scenes_a import bez, poly_at, draw_poly, pulse_on


def mini_brain(f, cx, cy, w, t, glow=1.0, wave=None):
    im = brain_image(t, wave=wave if wave is not None else ((t * 0.5) % 1.4) - .1, glow=glow, occ=0.0)
    h = int(w * im.height / im.width)
    im2 = im.resize((int(w), h), Image.LANCZOS)
    put_icon(f, im2, cx, cy, glow=.5, glow_r=12)
    return im2


# ===================================================== ESCENA 3 — COMPLETAR INFORMACIÓN
def pacman(R, mouth_deg, a_dir):
    sz = int(2 * R + 8)

    def d(dr, s):
        c = sz * s / 2
        dr.ellipse([c - R * s, c - R * s, c + R * s, c + R * s], fill=(238, 244, 255, 255))
        L = R * s * 1.6
        a0 = a_dir - math.radians(mouth_deg / 2); a1 = a_dir + math.radians(mouth_deg / 2)
        dr.polygon([(c, c), (c + L * math.cos(a0), c + L * math.sin(a0)), (c + L * math.cos(a_dir), c + L * math.sin(a_dir)),
                    (c + L * math.cos(a1), c + L * math.sin(a1))], fill=(0, 0, 0, 0))
    return icon(sz, sz, d)


def scene_completar(t):
    f = Frame(); L = f.L
    zc = 1.0 + 0.10 * ease(prog(t, 0, 4.6))
    cam = Cam(540, 860, zc, rot=0.035 * math.sin(t * .8) * 0 + 0.02 * ease(prog(t, 0, 4.6)))
    Rc = 340
    cen = (540, 860)
    verts = [(cen[0], cen[1] - Rc), (cen[0] - Rc * math.sin(math.radians(60)), cen[1] + Rc / 2), (cen[0] + Rc * math.sin(math.radians(60)), cen[1] + Rc / 2)]
    # lo que "llega": inductores que giran hasta quedar alineados
    k_in = ease_io(prog(t, 0.15, 1.5))
    aprog = ease_back(prog(t, 0.0, 0.8))
    R = 112
    for i, (vx, vy) in enumerate(verts):
        # entran desde fuera
        ox = (vx - cen[0]) * (1 + 1.3 * (1 - aprog)); oy = (vy - cen[1]) * (1 + 1.3 * (1 - aprog))
        x, y = cam.p(cen[0] + ox, cen[1] + oy)
        a_dir = math.atan2(cen[1] - vy, cen[0] - vx) + (1 - k_in) * math.radians(150 + 40 * i) + cam.rot
        ic = pacman(int(R * cam.z), 60, a_dir)
        al = ic.getchannel("A").point(lambda v: int(v * clamp(aprog * 1.6)))
        ic.putalpha(al)
        put_icon(f, ic, x, y, glow=.25, glow_r=12)
    # triángulo ilusorio: relleno percibido (muy sutil) + bordes que "se completan"
    fill_k = ease(prog(t, 1.35, 2.3))
    if fill_k > 0:
        lay, ld = f.new_layer()
        pts = [cam.p(*v) for v in verts]
        ld.polygon(pts, fill=sc((70, 100, 160), .07 * fill_k * (0.85 + 0.15 * math.sin(t * 4))))
        f.add_glow_layer(lay, 30, 1.0, raw=True)
    # bordes: tramos discontinuos que aparecen y se desvanecen (lo que añade el cerebro)
    edge_k = ease(prog(t, 1.5, 2.6)) * (1 - ease(prog(t, 3.2, 4.2))) * 0.0 + 0
    lay, ld = f.new_layer()
    for i in range(3):
        a, b = verts[i], verts[(i + 1) % 3]
        ux, uy = b[0] - a[0], b[1] - a[1]; ln = math.hypot(ux, uy); ux /= ln; uy /= ln
        # tramo visible entre los inductores
        s0, s1 = R * 1.0, ln - R * 1.0
        grow = ease_out(prog(t, 1.7 + i * .25, 2.7 + i * .25))
        fade = 1 - 0.65 * ease(prog(t, 3.4, 4.4))
        n_d = 18
        for q in range(n_d):
            u0 = s0 + (s1 - s0) * (q / n_d) ; u1 = s0 + (s1 - s0) * ((q + .55) / n_d)
            if (q / n_d) > grow: break
            p0 = cam.p(a[0] + ux * u0, a[1] + uy * u0); p1 = cam.p(a[0] + ux * u1, a[1] + uy * u1)
            ld.line([p0, p1], fill=sc(CYAN, .95 * fade), width=int(5 * cam.z))
    f.add_glow_layer(lay, 12, 1.0)
    # cerebro mini que completa
    mb_a = ease(prog(t, 1.0, 1.7))
    bx, by = 540, 250
    if mb_a > 0:
        wv = ((t - 1.0) * 0.55) % 1.5 - .1
        im = brain_image(t, wave=wv, glow=1.2)
        w_ = int(210 * (0.9 + 0.1 * mb_a))
        im2 = im.resize((w_, int(w_ * im.height / im.width)), Image.LANCZOS)
        im2.putalpha(im2.getchannel("A").point(lambda v: int(v * mb_a)))
        put_icon(f, im2, bx, by, glow=.55 * mb_a, glow_r=14)
        # rayos que bajan a los tres bordes
        for i in range(3):
            a, b = verts[i], verts[(i + 1) % 3]
            mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            pts = bez((bx + (i - 1) * 40, by + 140), (bx + (i - 1) * 140, by + 320), (mx, my - 220 if i else my - 120), (mx, my))
            if t > 1.7 + i * .2:
                for q in range(2):
                    s_ = ((t - 1.7) * .7 + q * .5 + i * .2) % 1
                    pulse_on(L, [cam.p(*p) for p in pts] and pts, cam, s_, color=sc(CYAN, 1), r=8)
    # partículas / cierre
    particles(L, t, seed=8, n=60, tint=CYAN, alpha=.7)
    out = f.finish()
    return out


# ===================================================== ESCENA 4 — EL PUNTO CIEGO
def eyeball_icon(R, side):
    """Sección horizontal del ojo (vista superior), frente hacia arriba. side=+1: ojo izquierdo (nervio hacia la derecha)."""
    sz = int(2 * R * 1.55)

    def d(dr, s):
        c = sz * s / 2
        r = R * s
        dr.ellipse([c - r, c - r, c + r, c + r], fill=(16, 34, 72, 255), outline=(54, 214, 255, 255), width=int(5 * s))
        # córnea (abombamiento frontal)
        dr.arc([c - r * .55, c - r * 1.22, c + r * .55, c - r * .34], 205, 335, fill=(120, 230, 255, 255), width=int(6 * s))
        # cristalino
        dr.ellipse([c - r * .26, c - r * .50, c + r * .26, c - r * .12], fill=(150, 225, 255, 230), outline=(230, 250, 255, 255), width=int(3 * s))
        # iris
        dr.line([c - r * .62, c - r * .28, c - r * .27, c - r * .30], fill=(255, 190, 70, 255), width=int(7 * s))
        dr.line([c + r * .62, c - r * .28, c + r * .27, c - r * .30], fill=(255, 190, 70, 255), width=int(7 * s))
        # humor vítreo
        for q in range(5):
            dr.ellipse([c - r * (.55 - q * .1), c + r * (-.05 + q * .1), c - r * (.45 - q * .1), c + r * (.05 + q * .1)], fill=(24, 54, 110, 255))
    return icon(sz, sz, d)


def eye_geom(cx, cy, R, side):
    th = math.radians(24)
    rr = R * .93
    disc = (cx + side * rr * math.sin(th), cy + rr * math.cos(th))
    fov = (cx, cy + rr)
    return disc, fov, th, rr


def draw_retina(L, cam, cx, cy, R, side, t, a=1.0):
    disc, fov, th, rr = eye_geom(cx, cy, R, side)
    # fotorreceptores: puntos a lo largo del fondo del ojo, ausentes en el disco óptico
    for deg in range(28, 153, 4):
        ang = math.radians(deg)
        x = cx + rr * math.cos(ang); y = cy + rr * math.sin(ang)
        # ángulo respecto al fondo (90°) hacia el lado nasal
        off = (deg - 90) * (-side)       # + hacia nasal
        if abs(off - math.degrees(th)) < 9:
            continue
        px, py = cam.p(x, y)
        r = cam.r(5.0)
        L.ellipse([px - r, py - r, px + r, py + r], fill=sc((255, 120, 190), .9 * a))
    return disc, fov


def scene_punto_ciego(t):
    f = Frame(); L = f.L
    # ---------------- Fase 1: anatomía (0 – 3.9)
    p1 = 1 - ease(prog(t, 3.3, 3.95))
    if p1 > 0.01:
        cam = Cam(540, 800, 1.12 + .08 * prog(t, 0, 3.9) - .12 * (1 - p1), rot=0)
        R = 170
        eyes = [(300, 800, +1), (780, 800, -1)]
        for (ex, ey, sd) in eyes:
            sx, sy = cam.p(ex, ey)
            ea = ease(prog(t, 0.0 + (0.12 if sd < 0 else 0), 0.7)) * p1
            ic = eyeball_icon(int(R * cam.z), sd)
            ic.putalpha(ic.getchannel("A").point(lambda v: int(v * ea)))
            put_icon(f, ic, sx, sy, glow=.4 * ea, glow_r=12)
            lay, ld = f.new_layer()
            disc, fov = draw_retina(ld, cam, ex, ey, R, sd, t, a=ea)
            # rayos de luz que entran y convergen en la fóvea
            for q, off in enumerate((-70, 0, 70)):
                a0 = (ex + off * 1.1, ey - R * 2.2); a1 = (ex + off * .22, ey - R * .30); a2 = fov
                path = [a0, a1, a2]
                pa = [cam.p(*p) for p in path]
                ld.line(pa, fill=sc(AMBER, .6 * ea), width=int(3 * cam.z))
                s_ = ((t * .9 + q * .3) % 1.0)
                pulse_on(ld, path, cam, s_, color=(255, 225, 150), r=8, trail=.2)
            # nervio óptico saliendo del disco hacia el centro
            dpx, dpy = disc
            nerve = bez((dpx, dpy), (dpx + sd * 40, dpy + 90), (540 + sd * 30 * 0 + (ex - 540) * 0.25, 1060), (540 + (ex - 540) * .12, 1180))
            draw_poly(ld, nerve, cam, sc(CYAN, .7 * ea), 16 * cam.z)
            draw_poly(ld, nerve, cam, sc((10, 40, 80), .0), 6 * cam.z)
            f.add_glow_layer(lay, 10, .9)
            # destaque del punto ciego
            hl = prog(t, 1.75 + (0.45 if sd < 0 else 0.0), 2.4 + (0.45 if sd < 0 else 0.0))
            if hl > 0:
                dx_, dy_ = cam.p(*disc)
                lay2, l2 = f.new_layer()
                for rr_, gain in ((30, 1.0), (30 + 55 * ease_out(hl), .5 * (1 - hl)), (30 + 100 * ease_out(hl), .3 * (1 - hl))):
                    rr_ = cam.r(rr_)
                    l2.ellipse([dx_ - rr_, dy_ - rr_, dx_ + rr_, dy_ + rr_], outline=sc(AMBER, gain * p1 * ea), width=int(5 * cam.z))
                # "sin sensores": zona oscura sobre el disco
                rr0 = cam.r(14)
                l2.ellipse([dx_ - rr0, dy_ - rr0, dx_ + rr0, dy_ + rr0], fill=sc(AMBER, .9 * ea * p1))
                f.add_glow_layer(lay2, 16, 1.1)
        # quiasma: los dos nervios confluyen
    # ---------------- Fase 2/3: campo visual con patrón
    pv = ease(prog(t, 3.35, 4.0))
    if pv > 0.001:
        zoom3 = 1.0 + 0.30 * ease_io(prog(t, 7.2, 10.8))
        fx = lerp(540, 800, ease_io(prog(t, 7.2, 10.8))); fy = lerp(780, 770, ease_io(prog(t, 7.2, 10.8)))
        zs = zoom3 * (0.88 + 0.12 * pv)
        cam = Cam(fx, fy, zs)
        # panel (pantalla) en coordenadas de mundo: x 70..1010, y 440..1100
        PX0, PY0, PX1, PY1 = 70, 440, 1010, 1100
        x0s, y0s = cam.p(PX0, PY0); x1s, y1s = cam.p(PX1, PY1)
        bx0, by0 = int(max(x0s, 0)), int(max(y0s, 0)); bx1, by1 = int(min(x1s, W)), int(min(y1s, H))
        if bx1 > bx0 and by1 > by0:
            Xs, Ys = np.meshgrid(np.arange(bx0, bx1, dtype=np.float32), np.arange(by0, by1, dtype=np.float32))
            wx = (Xs - W / 2) / zs + fx; wy = (Ys - H / 2) / zs + fy
            per = 64.0
            sph = (wx * .7071 + wy * .7071) / per + t * .22
            v = 0.5 + 0.5 * np.sin(2 * np.pi * sph)
            m = np.clip((v - 0.40) / 0.2, 0, 1)[..., None]
            cA = np.array((12, 28, 66), np.float32); cB = np.array((24, 88, 140), np.float32)
            pat = cA * (1 - m) + cB * m
            pat = pat * (0.92 + 0.08 * np.sin(wy / 90.0))[..., None]
            HX, HY = 800.0, 770.0
            dist = np.hypot(wx - HX, wy - HY)
            R0 = 84.0
            # progreso del relleno
            fillp = ease_io(prog(t, 7.7, 10.2))
            rf = R0 * (1 - fillp)
            hole_on = 0.0
            if 7.0 <= t:
                hole_on = ease(prog(t, 7.0, 7.45))
            hole = np.zeros_like(dist)
            if hole_on > 0 and rf > 0.5:
                hole = np.clip((rf - dist) * zs + 0.5, 0, 1) * hole_on
            hcol = np.array((6, 8, 20), np.float32)
            # fantasma negro (fase 2) "agujero negro" que NO vemos
            ghost = 0.0
            if 5.15 < t < 6.7:
                ghost = ease(prog(t, 5.15, 5.6)) * (1 - ease(prog(t, 6.2, 6.7)))
                hole = np.maximum(hole, np.clip((R0 - dist) * zs + .5, 0, 1) * ghost)
            pat = pat * (1 - hole[..., None]) + hcol * hole[..., None]
            # esquinas redondeadas del panel
            rr = 38.0
            qx = np.minimum(wx - PX0, PX1 - wx); qy = np.minimum(wy - PY0, PY1 - wy)
            cx_ = np.clip(rr - qx, 0, None); cy_ = np.clip(rr - qy, 0, None)
            dd = np.hypot(cx_, cy_)
            ma = np.clip((rr - dd) * zs + 0.5, 0, 1)
            f.base[by0:by1, bx0:bx1] = f.base[by0:by1, bx0:bx1] * (1 - (ma * pv)[..., None]) + pat * (ma * pv)[..., None]
        # contorno del panel
        lay, ld = f.new_layer()
        ld.rounded_rectangle([x0s, y0s, x1s, y1s], radius=cam.r(38), outline=sc(CYAN, .85 * pv), width=int(5 * cam.z))
        f.add_glow_layer(lay, 12, .9)
        # --- elementos del demo
        lay, ld = f.new_layer()
        CX_, CY_ = 250.0, 770.0
        cxs, cys = cam.p(CX_, CY_)
        a_ = pv
        cr = cam.r(34)
        ld.line([cxs - cr, cys, cxs + cr, cys], fill=sc(WHITE, a_), width=int(8 * cam.z))
        ld.line([cxs, cys - cr, cxs, cys + cr], fill=sc(WHITE, a_), width=int(8 * cam.z))
        # anillo de fijación (se cierra sobre la cruz)
        lock = prog(t, 3.9, 4.45)
        if lock > 0:
            rrl = cam.r(150 - 92 * ease_out(lock))
            ld.ellipse([cxs - rrl, cys - rrl, cxs + rrl, cys + rrl], outline=sc(CYAN, .95 * (0.6 + 0.4 * lock) * a_), width=int(5 * cam.z))
        # punto objetivo
        dot_vis = 1.0 - ease(prog(t, 4.75, 5.0))
        if t > 4.45 and t < 4.95:
            dot_vis *= 0.65 + 0.35 * (int(t * 18) % 2)    # parpadeo antes de desaparecer
        HXs, HYs = cam.p(800, 770)
        if dot_vis > 0.02 and t < 5.0:
            rd = cam.r(36) * (1 if t < 4.75 else (1 - ease(prog(t, 4.75, 5.0))))
            ld.ellipse([HXs - rd, HYs - rd, HXs + rd, HYs + rd], fill=sc(AMBER, a_ * dot_vis))
        # destello cuando desaparece
        if 4.95 < t < 5.7:
            kk = prog(t, 4.95, 5.7)
            rr_ = cam.r(40 + 180 * ease_out(kk))
            ld.ellipse([HXs - rr_, HYs - rr_, HXs + rr_, HYs + rr_], outline=sc(AMBER, (1 - kk)), width=int(5 * cam.z))
            rng = np.random.RandomState(4)
            for i in range(24):
                ang = rng.rand() * 6.28; sp = rng.uniform(60, 190)
                r_ = cam.r(sp) * ease_out(kk)
                q = cam.r(5)
                ld.ellipse([HXs + math.cos(ang) * r_ - q, HYs + math.sin(ang) * r_ - q, HXs + math.cos(ang) * r_ + q, HYs + math.sin(ang) * r_ + q], fill=sc(AMBER, 1 - kk))
        # señal de prohibido sobre el agujero negro
        if 5.4 < t < 6.7:
            ka = ease(prog(t, 5.4, 5.8)) * (1 - ease(prog(t, 6.2, 6.7)))
            Rr = cam.r(112)
            ld.ellipse([HXs - Rr, HYs - Rr, HXs + Rr, HYs + Rr], outline=sc(RED, .95 * ka), width=int(9 * cam.z))
            dd_ = Rr * .707
            ld.line([HXs - dd_, HYs - dd_, HXs + dd_, HYs + dd_], fill=sc(RED, .95 * ka), width=int(10 * cam.z))
        # relleno: borde brillante + pulsos que entran
        if 7.2 < t < 10.6:
            fillp = ease_io(prog(t, 7.7, 10.2))
            rf = 84 * (1 - fillp)
            if rf > 2:
                rrf = cam.r(rf)
                ld.ellipse([HXs - rrf, HYs - rrf, HXs + rrf, HYs + rrf], outline=sc(AMBER, .95), width=int(5 * cam.z))
            for q in range(18):
                ang = q / 18 * 6.2832 + .3
                s_ = ((t - 7.6) * .55 + (q % 6) / 6.0) % 1.0
                rin = 260 * (1 - s_) + max(rf, 0) * s_
                px, py = cam.p(800 + math.cos(ang) * rin, 770 + math.sin(ang) * rin)
                r_ = cam.r(7)
                ld.ellipse([px - r_, py - r_, px + r_, py + r_], fill=sc((255, 235, 170), (1 - abs(s_ - .5) * 1.4) * (0.9 if 7.7 < t < 10.4 else .4)))
        if 10.15 < t < 10.9:
            kk = prog(t, 10.15, 10.9)
            rr_ = cam.r(60 + 240 * ease_out(kk))
            ld.ellipse([HXs - rr_, HYs - rr_, HXs + rr_, HYs + rr_], outline=sc(WHITE, (1 - kk)), width=int(6 * cam.z))
        f.add_glow_layer(lay, 14, 1.0)
        # ojos (abajo) y línea de mirada, sólo en fase 2
        eyes_a = ease(prog(t, 3.7, 4.3)) * (1 - ease(prog(t, 6.8, 7.3)))
        if eyes_a > 0.01:
            ey = 1230
            # ojo izquierdo cerrado
            lay2, l2 = f.new_layer()
            for (ex) in (400,):
                pts = [(ex + math.cos(a) * 80, ey + math.sin(a) * 26 - 8) for a in np.linspace(0.1, math.pi - 0.1, 24)]
                l2.line(pts, fill=sc(CYAN, .95 * eyes_a), width=7, joint="curve")
                for q in range(-3, 4):
                    xx = ex + q * 24; l2.line([xx, ey + 14, xx + q * 3, ey + 36], fill=sc(CYAN, .8 * eyes_a), width=4)
            f.add_glow_layer(lay2, 10, 1.0)
            ic = eye_icon(170, gaze=(-18, 0))
            ic.putalpha(ic.getchannel("A").point(lambda v: int(v * eyes_a)))
            put_icon(f, ic, 680, ey - 10, glow=.4 * eyes_a, glow_r=10)
            # línea de mirada punteada hacia la cruz
            lay3, l3 = f.new_layer()
            sx_, sy_ = 640, ey - 30
            ex_, ey_ = cam.p(CX_, CY_ + 40)
            n = 22
            for q in range(n):
                if q % 2: continue
                p0 = (lerp(sx_, ex_, q / n), lerp(sy_, ey_, q / n)); p1 = (lerp(sx_, ex_, (q + 1) / n), lerp(sy_, ey_, (q + 1) / n))
                l3.line([p0, p1], fill=sc(CYAN, .75 * eyes_a * lock), width=4)
            f.add_glow_layer(lay3, 8, 1.0)
        # cerebro (aparece en la fase de relleno)
        ba = ease(prog(t, 6.9, 7.5))
        if ba > 0:
            wv = ((t - 7.0) * .6) % 1.5 - .1
            im = brain_image(t, wave=wv, glow=1.3)
            w_ = 200
            im2 = im.resize((w_, int(w_ * im.height / im.width)), Image.LANCZOS)
            im2.putalpha(im2.getchannel("A").point(lambda v: int(v * ba)))
            put_icon(f, im2, 540, 285, glow=.6 * ba, glow_r=14)
            path = bez((580, 340), (700, 360), (760, 520), (800, 690))
            if t > 7.5:
                for q in range(3):
                    s_ = ((t - 7.5) * .6 + q / 3.0) % 1.0
                    # pulso en coordenadas de pantalla (la cámara empuja hacia el agujero)
                    pulse_on(L, path, Cam(540, 960, 1.0), s_, color=(255, 230, 160), r=9)
    particles(L, t, seed=12, n=50, tint=CYAN, alpha=.6)
    return f.finish()
