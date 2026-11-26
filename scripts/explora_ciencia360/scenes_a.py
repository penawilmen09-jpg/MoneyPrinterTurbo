"""Escenas 1 (gancho) y 2 (cerebro)."""
import math
import numpy as np
from PIL import Image, ImageDraw
from common import *
from assets import *

# ===================================================== utilidades compartidas
def bez(p0, p1, p2, p3, n=40):
    out = []
    for i in range(n + 1):
        s = i / n; q = 1 - s
        out.append((q**3 * p0[0] + 3 * q * q * s * p1[0] + 3 * q * s * s * p2[0] + s**3 * p3[0],
                    q**3 * p0[1] + 3 * q * q * s * p1[1] + 3 * q * s * s * p2[1] + s**3 * p3[1]))
    return out


def poly_at(pts, s):
    """Punto a lo largo de una polilínea (s en 0..1)."""
    n = len(pts) - 1
    f = clamp(s) * n; i = min(int(f), n - 1); k = f - i
    return (pts[i][0] + (pts[i + 1][0] - pts[i][0]) * k, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * k)


def draw_poly(dr, pts, cam, color, width, upto=1.0, frm=0.0):
    n = len(pts) - 1
    a, b = int(frm * n), max(int(upto * n), 1)
    sp = [cam.p(*p) for p in pts[a:b + 1]]
    if len(sp) > 1:
        dr.line(sp, fill=color, width=max(int(width), 1), joint="curve")


def pulse_on(dr, pts, cam, s, color=(200, 245, 255), r=9, trail=0.12):
    if s < 0 or s > 1:
        return
    for j in range(5):
        k = s - trail * j / 5
        if k < 0:
            break
        x, y = cam.p(*poly_at(pts, k))
        rr = cam.r(r) * (1 - j * 0.13)
        c = sc(color, 1 - j * 0.2)
        dr.ellipse([x - rr, y - rr, x + rr, y + rr], fill=c)


# ===================================================== ESCENA 1 — GANCHO
_net = {}
def _network():
    if "n" in _net:
        return _net["n"]
    rng = np.random.RandomState(5)
    N, ZL = 340, 2600.0
    P = np.stack([rng.uniform(-1250, 1250, N), rng.uniform(-1700, 1700, N), rng.uniform(0, ZL, N)], 1)
    cols = [CYAN, BLUE, VIOLET, (120, 230, 255), MAGENTA]
    ncol = [cols[i] for i in rng.choice(len(cols), N, p=[.34, .24, .24, .12, .06])]
    edges = []
    for i in range(N):
        d = []
        for j in range(N):
            if i == j: continue
            dz = abs(P[i, 2] - P[j, 2]); dz = min(dz, ZL - dz)
            if abs(P[i, 2] - P[j, 2]) > 900: continue
            dd = math.sqrt((P[i, 0] - P[j, 0])**2 + (P[i, 1] - P[j, 1])**2 + (P[i, 2] - P[j, 2])**2)
            d.append((dd, j))
        d.sort()
        for dd, j in d[:2]:
            if dd < 900 and (j, i) not in [(a, b) for a, b, *_ in edges]:
                edges.append((i, j, rng.rand(), 0.35 + rng.rand() * 0.55))
    # cuadrados "información que falta"
    sq = []
    for k in range(34):
        sq.append((rng.uniform(80, W - 80), rng.uniform(280, 1250), rng.uniform(34, 70), rng.rand()))
    _net["n"] = (P, ncol, edges, ZL, sq)
    return _net["n"]


def _radial_streaks(L, t, intensity, seed=3):
    rng = np.random.RandomState(seed)
    cx, cy = W / 2, 900
    for i in range(90):
        ang = rng.rand() * 6.2832
        r0 = rng.uniform(60, 500); sp = rng.uniform(.6, 2.2)
        ph = rng.rand()
        k = (t * sp * 0.9 + ph) % 1.0
        ra = r0 + k * 1600 * sp; rb = ra + 160 + 500 * k * intensity
        c = sc(mix(CYAN, WHITE, rng.rand() * .5), intensity * (1 - k) ** .6 * .9)
        L.line([cx + math.cos(ang) * ra, cy + math.sin(ang) * ra, cx + math.cos(ang) * rb, cy + math.sin(ang) * rb],
               fill=c, width=int(2 + 4 * k))


def scene_gancho(t):
    f = Frame()
    L = f.L
    # ---------- Fase A: ojo con zoom hacia la pupila
    tA = 3.45
    if t < tA:
        zt = ease_io(prog(t, 0.0, 3.15))
        z = math.exp(lerp(math.log(1.12), math.log(17.0), zt ** 1.12))
        ecx, ecy = 540.0, 900.0
        gaze = (math.sin(t * 2.2) * 10 * (1 - zt), math.sin(t * 1.7) * 6)
        cx = lerp(ecx, ecx + gaze[0], ease(prog(t, 0, 2.2)))
        cy = lerp(ecy, ecy + gaze[1], ease(prog(t, 0, 2.2)))
        bl = math.sin(math.pi * prog(t, 0.95, 1.18)) ** 2
        op = 1 - 0.96 * bl
        shock = prog(t, 0.88, 1.9)
        pupil = 66 - 20 * math.sin(math.pi * clamp(shock * 1.3)) * (shock < 0.77) + 30 * ease(prog(t, 1.3, 3.0))
        rgb, al, geo = eye_closeup(z, cx, cy, t, open_=op, pupil=pupil, gaze=gaze, spin=t * 0.05, ecx=ecx, ecy=ecy)
        cam = Cam(cx, cy, z)
        fade = 1.0
        f.base = f.base * (1 - al) + rgb * al
        # contorno neón de los párpados
        up, lo = eye_outline_pts(geo)
        a = clamp(1 - zt * 1.3)
        if a > 0.02:
            L.line([cam.p(*p) for p in up], fill=sc(CYAN, .95 * a), width=max(int(5 * min(z, 2)), 3), joint="curve")
            L.line([cam.p(*p) for p in lo], fill=sc(CYAN, .95 * a), width=max(int(5 * min(z, 2)), 3), joint="curve")
        # onda de choque en "engañarte"
        if 0.88 < t < 1.9:
            k = ease_out(prog(t, 0.88, 1.9))
            x, y = cam.p(ecx, ecy)
            for rr, g in ((k * 900, 1.0), (k * 650, .6)):
                L.ellipse([x - rr, y - rr * .62, x + rr, y + rr * .62], outline=sc(CYAN, (1 - k) * g), width=5)
        # túnel de velocidad
        _radial_streaks(L, t, ease(prog(t, 1.4, 2.5)) * (1 - ease(prog(t, 3.0, 3.45))))
    # ---------- Fase B: red neuronal (vuelo hacia delante) y "relleno" de información
    if t > 2.7:
        P, ncol, edges, ZL, sq = _network()
        appear = ease(prog(t, 2.9, 4.1))
        tb = t - 2.7
        camz = 160.0 * tb + 1100.0 * (1 - math.exp(-tb * 1.5)) * 0.9
        fl = 900.0
        cxs, cys = W / 2 + math.sin(t * 0.5) * 30, 880 + math.cos(t * 0.37) * 20
        dz = (P[:, 2] - camz) % ZL
        k = fl / (dz + 80.0)
        X = cxs + P[:, 0] * k; Y = cys + P[:, 1] * k
        vis = np.clip((dz - 90) / 300.0, 0, 1) * np.clip((ZL * 0.92 - dz) / 800.0, 0, 1)
        lay, ld = f.new_layer()
        for (i, j, ph, spd) in edges:
            if abs(dz[i] - dz[j]) > 1000: continue
            v = min(vis[i], vis[j]) * appear
            if v < 0.03: continue
            kk = (k[i] + k[j]) / 2
            c = sc(mix(ncol[i], ncol[j], .5), .85 * v)
            ld.line([X[i], Y[i], X[j], Y[j]], fill=c, width=max(2, int(2.6 * kk + .8)))
            s_ = (t * spd + ph) % 1.0
            px, py = lerp(X[i], X[j], s_), lerp(Y[i], Y[j], s_)
            rr = max(3.0, 8.5 * kk)
            ld.ellipse([px - rr, py - rr, px + rr, py + rr], fill=sc((190, 245, 255), min(1, v * 1.3)))
            s2 = max(0, s_ - .10)
            ld.line([lerp(X[i], X[j], s2), lerp(Y[i], Y[j], s2), px, py], fill=sc(ncol[i], .75 * v), width=max(2, int(3 * kk)))
        for n_ in range(len(P)):
            v = vis[n_] * appear
            if v < 0.03: continue
            rr = max(3.0, 11.0 * k[n_])
            ld.ellipse([X[n_] - rr, Y[n_] - rr, X[n_] + rr, Y[n_] + rr], fill=sc(mix(ncol[n_], WHITE, .35), min(1, v * 1.1)))
        f.add_glow_layer(lay, 18, 1.05)
        # información que falta -> se rellena (7.0 s en adelante)
        if t > 6.6:
            lay2, l2 = f.new_layer()
            for (x0, y0, size, r_) in sq:
                x = x0 + math.sin(t * .6 + r_ * 9) * 10; y = y0 + math.cos(t * .5 + r_ * 7) * 10
                tf = 7.1 + (math.hypot(x0 - W / 2, y0 - 780) / 800.0) * 2.4 + r_ * .4
                a_in = ease(prog(t, 6.6, 7.1 + r_ * .5))
                s = size / 2
                if t < tf:
                    # cuadrado hueco = dato ausente
                    c = sc(mix(VIOLET, WHITE, .2), .55 * a_in)
                    for q in range(4):
                        pass
                    l2.rectangle([x - s, y - s, x + s, y + s], outline=c, width=3)
                    l2.line([x - s * .35, y, x + s * .35, y], fill=sc(c, .6), width=2)
                else:
                    kf = prog(t, tf, tf + .35)
                    fillc = mix(AMBER, MAGENTA, (r_ * .7))
                    sz = s * (0.85 + .15 * ease_back(kf))
                    l2.rectangle([x - sz, y - sz, x + sz, y + sz], fill=sc(fillc, .88 * min(1, kf * 3)))
                    ring = prog(t, tf, tf + .7)
                    if ring < 1:
                        rr = s * (1 + 3 * ease_out(ring))
                        l2.ellipse([x - rr, y - rr, x + rr, y + rr], outline=sc(AMBER, (1 - ring) * .9), width=3)
            f.add_glow_layer(lay2, 16, 0.9)
        # destello final hacia la escena 2
        fl_ = ease(prog(t, 10.2, 11.2))
        if fl_ > 0:
            lay3, l3 = f.new_layer()
            rr = 120 + 900 * fl_
            l3.ellipse([W / 2 - rr, 900 - rr, W / 2 + rr, 900 + rr], fill=sc((90, 130, 255), .55 * fl_))
            f.add_glow_layer(lay3, 120, 1.0, soft=True, raw=False)
    particles(L, t, seed=2, n=40, alpha=0.6)
    out = f.finish()
    # glitch RGB al inicio (gancho inmediato)
    if t < 0.45:
        sh = int(26 * (1 - t / 0.45) ** 2)
        if sh > 0:
            out[..., 0] = np.roll(out[..., 0], sh, axis=1)
            out[..., 2] = np.roll(out[..., 2], -sh, axis=1)
    if t < 0.12:
        out = out + 22 * (1 - t / 0.12)
    return out


# ===================================================== ESCENA 2 — EL CEREBRO
BRAIN_C = (540, 1020)
EYE_L, EYE_R = (360, 330), (720, 330)
CHI = (540, 760)
OCC_L, OCC_R = (390, 1400), (690, 1400)


def nerve_paths():
    return dict(
        eL=bez((360, 370), (360, 540), (470, 640), CHI),
        eR=bez((720, 370), (720, 540), (610, 640), CHI),
        oL=bez(CHI, (540, 960), (400, 1100), OCC_L),
        oR=bez(CHI, (540, 960), (680, 1100), OCC_R),
    )


def paste_brain(f, t, cam, bx, by, **kw):
    im = brain_image(t, **kw)
    z = cam.z
    sz = (int(im.width / 1.5 * z), int(im.height / 1.5 * z))
    im2 = im.resize(sz, Image.BICUBIC)
    if abs(cam.rot) > 1e-4:
        im2 = im2.rotate(-math.degrees(cam.rot), resample=Image.BICUBIC, expand=True)
    cxs, cys = cam.p(bx, by + 30.6)
    f.paste_rgba(im2, (cxs - im2.width / 2, cys - im2.height / 2))
    # contorno neón
    pts = brain_outline_pts()
    return pts


def brain_rim(f, cam, bx, by, color=CYAN, k=0.55):
    pts = brain_outline_pts()
    half = len(pts) // 2
    lay, ld = f.new_layer()
    for chunk in (pts[:half], pts[half:]):
        sp = [cam.p(bx + x, by + y) for x, y in chunk]
        ld.line(sp, fill=sc(color, k), width=max(int(3 * cam.z), 2), joint="curve")
    f.add_glow_layer(lay, 14, 1.0)


def cam_icon(w=470, rec=True, k=1.0):
    h = int(w * .72)

    def d(dr, s):
        cx, cy = w * s / 2, h * s / 2 + 12 * s
        bw, bh = w * s * .94, h * s * .78
        dr.rounded_rectangle([cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2], radius=34 * s, fill=(14, 24, 54, 255), outline=(54, 214, 255, 255), width=int(7 * s))
        dr.rounded_rectangle([cx - bw * .22, cy - bh / 2 - 38 * s, cx + bw * .12, cy - bh / 2 + 4 * s], radius=10 * s, fill=(14, 24, 54, 255), outline=(54, 214, 255, 255), width=int(6 * s))
        for i, (r, col) in enumerate(((118, (26, 40, 92)), (96, (20, 70, 140)), (66, (40, 150, 230)), (34, (10, 14, 40)))):
            dr.ellipse([cx - r * s, cy - r * s, cx + r * s, cy + r * s], fill=col + (255,), outline=(54, 214, 255, 255) if i == 0 else None, width=int(5 * s))
        dr.ellipse([cx - 62 * s, cy - 70 * s, cx - 24 * s, cy - 40 * s], fill=(255, 255, 255, 220))
        dr.rounded_rectangle([cx + bw * .30, cy - bh / 2 + 22 * s, cx + bw * .44, cy - bh / 2 + 44 * s], radius=6 * s, fill=(255, 190, 70, 255))
        if rec:
            dr.ellipse([cx - bw / 2 + 28 * s, cy - bh / 2 + 24 * s, cx - bw / 2 + 56 * s, cy - bh / 2 + 52 * s], fill=(255, 60, 60, 255))
    return icon(w, h + 40, d)


def scene_cerebro(t):
    f = Frame()
    L = f.L
    # cámara: empuja desde un primer plano y se abre; ligero balanceo
    zt = ease_out(prog(t, 0.0, 4.5))
    z = lerp(1.7, 0.94, zt) + 0.012 * math.sin(t * 0.6)
    cam = Cam(cx=lerp(540, 540, zt), cy=lerp(900, 900, zt), zoom=z, rot=0.04 * math.sin(t * 0.35) * (1 - zt * .4) + .09 * (1 - zt))
    bx, by = BRAIN_C
    # señal de fondo (picos) + ola de interpretación
    wave = None
    occ = 0.0
    if t > 7.45:
        wave = prog(t, 7.5, 9.2) * 1.35 - 0.1
        occ = ease(prog(t, 7.7, 8.6)) * (0.8 + 0.2 * math.sin(t * 6))
    else:
        wave = ((t * 0.18) % 1.4) - 0.1
    paste_brain(f, t, cam, bx, by, wave=wave, occ=occ)
    brain_rim(f, cam, bx, by)
    # ---- cámara fotográfica (no funciona así)
    tc = t - 2.45
    ca = prog(t, 2.45, 2.95) * (1 - ease(prog(t, 4.85, 5.4)))
    if ca > 0.01:
        sc_ = ease_back(prog(t, 2.45, 3.0)) * (1 + 0.55 * ease(prog(t, 4.85, 5.4)))
        rec = (int(t * 2.2) % 2 == 0)
        ic = cam_icon(int(470 * cam.z ** 0.0), rec=rec)
        ic2 = ic.resize((max(int(ic.width * sc_ * .9), 4), max(int(ic.height * sc_ * .9), 4)), Image.LANCZOS)
        al = ic2.getchannel("A").point(lambda v: int(v * ca))
        ic2.putalpha(al)
        pos = (W / 2, 880)
        put_icon(f, ic2, pos[0], pos[1], glow=0.5 * ca, glow_r=14)
        # flash de obturador
        if 2.95 < t < 3.25:
            fl = 1 - prog(t, 2.95, 3.25)
            f.base += 70 * fl
        # tachado "no" (círculo y diagonal rojos)
        sk = ease_out(prog(t, 3.95, 4.4))
        if sk > 0:
            lay, ld = f.new_layer()
            R = 300 * sc_
            x0, y0 = pos
            a_ = prog(t, 3.95, 4.3)
            ld.arc([x0 - R, y0 - R, x0 + R, y0 + R], 0, 360 * a_, fill=sc(RED, .95), width=18)
            if sk > .4:
                kk = ease_out((sk - .4) / .6)
                ca_, sa_ = math.cos(math.radians(135)), math.sin(math.radians(135))
                ld.line([x0 - ca_ * R * 0.97 * 0 + R * .707 * -1 * 0 + (-R * .707), y0 + (-R * .707),
                         x0 + (-R * .707) + (2 * R * .707) * kk, y0 + (-R * .707) + (2 * R * .707) * kk], fill=sc(RED, .95), width=20)
            f.add_glow_layer(lay, 16, 1.0)
        # partículas al romperse
        if t > 4.85:
            kb = prog(t, 4.85, 5.7)
            rng = np.random.RandomState(9)
            for i in range(46):
                ang = rng.rand() * 6.28; sp = rng.uniform(150, 520)
                x = pos[0] + math.cos(ang) * sp * ease_out(kb); y = pos[1] + math.sin(ang) * sp * ease_out(kb)
                r = 4 + rng.rand() * 5
                L.ellipse([x - r, y - r, x + r, y + r], fill=sc(mix(CYAN, RED, rng.rand()), (1 - kb)))
    # ---- ojos + nervios ópticos
    pa = nerve_paths()
    ea = ease(prog(t, 5.9, 6.7))
    if ea > 0:
        lay, ld = f.new_layer()
        for key, pts in pa.items():
            frm_t = 6.3 if key[0] == "e" else 6.9
            up = ease(prog(t, frm_t, frm_t + .7))
            draw_poly(ld, pts, cam, sc(CYAN, .55), 5 * cam.z, upto=up)
        f.add_glow_layer(lay, 14, 1.0)
        # pulsos (ojo -> quiasma -> corteza occipital)
        for key, pts in pa.items():
            for q in range(3):
                if key[0] == "e":
                    s_ = ((t - 6.6) * .55 + q / 3.0) % 1.0 if t > 6.6 else -1
                else:
                    s_ = ((t - 6.6) * .55 + q / 3.0 - 0.0) % 1.0 if t > 7.2 else -1
                pulse_on(L, pts, cam, s_, r=10)
        for (ex, ey, g) in ((EYE_L[0], EYE_L[1], (8, 0)), (EYE_R[0], EYE_R[1], (-8, 0))):
            drop = (1 - ease_out(prog(t, 5.9, 6.8))) * -160
            ic = eye_icon(int(400 * cam.z ** .5), gaze=(g[0], 14))
            x, y = cam.p(ex, ey + drop / z)
            put_icon(f, ic, x, y, glow=.45 * ea, glow_r=14)
    # resplandor occipital
    if occ > 0:
        lay, ld = f.new_layer()
        x, y = cam.p(bx, by + 360)
        rr = cam.r(210 + 40 * math.sin(t * 7))
        ld.ellipse([x - rr, y - rr * .6, x + rr, y + rr * .6], fill=sc(MAGENTA, .5 * occ))
        f.add_glow_layer(lay, 60, 1.3, raw=False)
    particles(L, t, seed=4, n=55, tint=VIOLET, alpha=.7)
    return f.finish()
