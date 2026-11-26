"""Activos procedurales: iconos RGBA con supersampling, ojo, cerebro dorsal, red neuronal."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from common import *

SS = 3


def icon(w, h, draw_fn, ss=SS):
    """Dibuja con supersampling y devuelve RGBA suavizado."""
    im = Image.new("RGBA", (int(w * ss), int(h * ss)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    draw_fn(d, ss)
    return im.resize((int(w), int(h)), Image.LANCZOS)


def put_icon(frame, im, cx, cy, glow=0.0, glow_r=12, tint=None):
    """Pega un RGBA centrado en (cx,cy); opcionalmente emite resplandor."""
    x, y = cx - im.width / 2, cy - im.height / 2
    frame.paste_rgba(im, (x, y))
    if glow > 0:
        a = np.asarray(im, np.float32)
        rgb = a[..., :3] * (a[..., 3:4] / 255.0)
        if tint is not None:
            rgb = rgb * 0 + np.array(tint, np.float32)[None, None, :] * (a[..., 3:4] / 255.0)
        lay = Image.new("RGB", (W, H), (0, 0, 0))
        lay.paste(Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)), (int(x), int(y)))
        frame.add_glow_layer(lay, glow_r, glow, soft=False, raw=False)


# ------------------------------------------------------------------ OJO (primer plano)
def eye_closeup(z, cx, cy, t, open_=1.0, pupil=62.0, gaze=(0.0, 0.0), spin=0.0, ecx=540.0, ecy=800.0):
    """Renderiza el ojo humano de primer plano con cámara (zoom z centrada en cx,cy).
    Devuelve (rgb float32 HxWx3, alpha HxWx1, funciones de contorno)."""
    hw, hh = W // 2, H // 2
    X, Y = np.meshgrid(np.arange(hw, dtype=np.float32), np.arange(hh, dtype=np.float32))
    wx = (X * 2 - W / 2) / z + cx
    wy = (Y * 2 - H / 2) / z + cy
    a = 470.0
    u = (wx - ecx) / a
    shape = np.clip(1 - u * u, 0, 1) ** 0.82
    hu, hl = 265.0 * open_, 205.0 * open_
    yu = ecy - hu * shape
    yl = ecy + hl * shape
    inside = np.clip(np.minimum(wy - yu, yl - wy) * z / 2 + 0.5, 0, 1) * (np.abs(u) < 1)
    dl = np.clip(np.minimum(wy - yu, yl - wy), 0, 400)  # distancia mundo al párpado

    # esclerótica
    k = np.clip(dl / 90.0, 0, 1) ** 0.7
    scl = np.empty((hh, hw, 3), np.float32)
    c_edge = np.array((120, 140, 190), np.float32); c_mid = np.array((236, 241, 250), np.float32)
    scl[:] = c_edge * (1 - k[..., None]) + c_mid * k[..., None]
    corner = np.clip((np.abs(u) - 0.78) / 0.22, 0, 1)[..., None]
    scl = scl * (1 - 0.35 * corner) + np.array((255, 150, 160), np.float32) * 0.35 * corner

    # iris
    ix, iy = ecx + gaze[0], ecy + gaze[1]
    dx, dy = wx - ix, wy - iy
    rho = np.sqrt(dx * dx + dy * dy)
    th = np.arctan2(dy, dx) + spin
    Ri = 205.0
    rt = np.clip(rho / Ri, 0, 1.2)
    f1 = np.sin(th * 38 + 3 * np.sin(th * 7 + rt * 5))
    f2 = np.sin(th * 93 + rt * 14)
    f3 = np.sin(th * 17 - rt * 9)
    fib = 0.5 + 0.22 * f1 + 0.16 * f2 + 0.12 * f3
    inner = np.array((236, 168, 60), np.float32); mid = np.array((42, 150, 205), np.float32)
    outer = np.array((10, 38, 98), np.float32); limb = np.array((4, 12, 34), np.float32)
    s1 = np.clip((rt - 0.30) / 0.30, 0, 1)[..., None]
    s2 = np.clip((rt - 0.62) / 0.30, 0, 1)[..., None]
    s3 = np.clip((rt - 0.90) / 0.10, 0, 1)[..., None]
    ic = inner * (1 - s1) + mid * s1
    ic = ic * (1 - s2) + outer * s2
    ic = ic * (1 - s3) + limb * s3
    ic = ic * (0.55 + 0.9 * fib[..., None])
    ia = np.clip((Ri - rho) * z / 2 + 0.5, 0, 1)[..., None]
    # sombra del párpado superior sobre el iris
    shade = np.clip(0.30 + (wy - yu) / 150.0, 0.3, 1.0)[..., None]
    ic = ic * shade
    col = scl * (1 - ia) + ic * ia
    # pupila
    pa = np.clip((rho - pupil) * z / 2 + 0.5, 0, 1)[..., None]
    pcol = np.array((2, 3, 9), np.float32)
    # leve borde cálido alrededor de la pupila
    rim = np.exp(-((rho - pupil) / 10.0) ** 2)[..., None] * 0.35
    col = pcol * (1 - pa) + col * pa
    col = col + np.array((255, 190, 90), np.float32) * rim * ia * pa
    # reflejos especulares
    for (ox, oy, rx, ry, g) in ((-78, -88, 46, 30, 1.0), (62, 70, 20, 14, 0.55)):
        sp = np.exp(-(((wx - ix - ox) / rx) ** 2 + ((wy - iy - oy) / ry) ** 2) ** 1.6) * g
        col = col + 255 * sp[..., None]
    col = np.clip(col, 0, 255)
    rgb = np.asarray(Image.fromarray(col.astype(np.uint8)).resize((W, H), Image.BICUBIC), np.float32)
    al = np.asarray(Image.fromarray((inside * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), np.float32)[..., None] / 255.0
    return rgb, al, (ecx, ecy, a, hu, hl)


def eye_outline_pts(geo, n=60):
    ecx, ecy, a, hu, hl = geo
    xs = np.linspace(-1, 1, n)
    sh = np.clip(1 - xs ** 2, 0, 1) ** 0.82
    up = [(ecx + x * a, ecy - hu * s) for x, s in zip(xs, sh)]
    lo = [(ecx + x * a, ecy + hl * s) for x, s in zip(xs[::-1], sh[::-1])]
    return up, lo


# ------------------------------------------------------------------ OJO (icono pequeño, RGBA)
def eye_icon(w=300, open_=1.0, gaze=(0, 0), pupil=0.22, tint=CYAN, iris=(40, 150, 220)):
    h = int(w * 0.62)

    def drw(d, s):
        cx, cy = w * s / 2, h * s / 2
        a = w * s * 0.48
        hu, hl = h * s * 0.46 * open_, h * s * 0.36 * open_
        xs = np.linspace(-1, 1, 80)
        sh = np.clip(1 - xs ** 2, 0, 1) ** 0.82
        up = [(cx + x * a, cy - hu * q) for x, q in zip(xs, sh)]
        lo = [(cx + x * a, cy + hl * q) for x, q in zip(xs[::-1], sh[::-1])]
        poly = up + lo
        d.polygon(poly, fill=(226, 236, 250, 255))
        # iris recortado por un lienzo auxiliar
        m = Image.new("L", d._image.size, 0)
        ImageDraw.Draw(m).polygon(poly, fill=255)
        lay = Image.new("RGBA", d._image.size, (0, 0, 0, 0))
        ld = ImageDraw.Draw(lay)
        ri = h * s * 0.36
        gx, gy = cx + gaze[0] * s, cy + gaze[1] * s
        for i in range(24):
            k = i / 23
            col = mix((250, 190, 80), iris, ease(k * 1.3)) if k < 0.9 else (6, 20, 50)
            r = ri * (1 - k * 0.0) * (1 - k) + ri * 0.35 * k * 0 + 0
        # anillos concéntricos del iris (de fuera hacia dentro)
        for i in range(20):
            k = i / 19.0
            r = ri * (1 - k * 0.62)
            col = mix((8, 28, 70), iris, min(1.0, k * 1.25))
            if k > 0.82:
                col = mix(col, (250, 190, 80), (k - 0.82) / 0.18)
            ld.ellipse([gx - r, gy - r, gx + r, gy + r], fill=tuple(int(c) for c in col) + (255,))
        rp = ri * (pupil / 0.22) * 0.38
        ld.ellipse([gx - rp, gy - rp, gx + rp, gy + rp], fill=(2, 4, 10, 255))
        ld.ellipse([gx - ri * .42, gy - ri * .5, gx - ri * .12, gy - ri * .24], fill=(255, 255, 255, 235))
        lay.putalpha(Image.composite(lay.getchannel("A"), Image.new("L", lay.size, 0), m))
        d._image.alpha_composite(lay)
        ln = tuple(int(c) for c in tint) + (255,)
        d.line(up + [lo[0]], fill=ln, width=int(3.2 * s), joint="curve")
        d.line(lo + [up[0]], fill=ln, width=int(3.2 * s), joint="curve")
    return icon(w, h, drw)


# ------------------------------------------------------------------ CEREBRO dorsal
_brain = {}


def _gauss_fft(field, sigma):
    h, w = field.shape
    fy = np.fft.fftfreq(h)[:, None]; fx = np.fft.fftfreq(w)[None, :]
    g = np.exp(-2 * (np.pi ** 2) * (sigma ** 2) * (fx ** 2 + fy ** 2))
    return np.real(np.fft.ifft2(np.fft.fft2(field) * g))


def brain_assets():
    """Textura del cerebro (vista dorsal) a 1.5x: máscara, pliegues, fase de señal."""
    if "t" in _brain:
        return _brain["t"]
    bw, bh = 820, 1020   # lienzo
    S = 1.5
    tw, th = int(bw * S), int(bh * S)
    Y, X = np.mgrid[0:th, 0:tw].astype(np.float32)
    x = (X - tw / 2) / S; y = (Y - th * 0.47) / S
    # hemisferio: superelipse con estrechamiento posterior
    u = (y + 420) / 840.0          # 0 frente → 1 atrás
    halfw = 372 * (1 - 0.20 * np.clip(u - 0.55, 0, 1) ** 1.2) * (0.80 + 0.20 * np.clip(u / 0.25, 0, 1) ** 0.6)
    gap = 9.0
    xr = np.abs(x) - gap
    p = 2.5
    ell = (np.clip(xr, 0, None) / halfw) ** p + (np.abs(y) / 470.0) ** p
    brain_mask = (ell < 1.0) & (np.abs(x) > gap)
    edge = np.clip((1 - ell) * 90 * S / 6, 0, 1)
    mask = np.clip(edge, 0, 1) * (np.abs(x) > gap * 0.9)
    # pliegues: líneas de nivel de ruido suavizado (laberinto cortical)
    rng = np.random.RandomState(11)
    n = rng.randn(th, tw).astype(np.float32)
    f1 = _gauss_fft(n, 7.5 * S / 1.5)
    f1 /= f1.std()
    f2 = _gauss_fft(rng.randn(th, tw).astype(np.float32), 22.0 * S / 1.5); f2 /= f2.std()
    fld = f1 + 0.35 * f2
    sul = np.exp(-(fld / 0.20) ** 2)          # surcos (líneas oscuras)
    gyr = np.clip(1 - np.abs(fld) / 1.1, 0, 1)
    # surcos principales: fisura longitudinal y surco central/lateral
    # volumen
    vol = np.clip(1 - ell, 0, 1) ** 0.55
    # fase de señal (de adelante hacia atrás + ruido) para los pulsos
    phase = (y + 470) / 940.0 + 0.10 * _gauss_fft(rng.randn(th, tw).astype(np.float32), 30.0) / 0.0035
    phase = (y + 470) / 940.0 + 0.12 * np.tanh(f2)
    cb = np.zeros_like(mask)
    # cerebelo: elipse aplanada con estrías horizontales, asoma por detrás
    cby = y - 452
    cbell = (x / 215.0) ** 2 + (cby / 74.0) ** 2
    cb = np.clip((1 - cbell) * 14, 0, 1) * (1 - mask)
    stri = 0.5 + 0.5 * np.sin(cby * 0.55 + 4 * np.sin(x * 0.02))
    _brain["t"] = dict(mask=mask.astype(np.float32), sul=sul.astype(np.float32), gyr=gyr.astype(np.float32),
                       vol=vol.astype(np.float32), phase=phase.astype(np.float32), cb=cb.astype(np.float32),
                       stri=stri.astype(np.float32), S=S, tw=tw, th=th, x=x.astype(np.float32), y=y.astype(np.float32))
    return _brain["t"]


def brain_image(t, wave=None, base_hue=0.0, glow=1.0, occ=0.0, tint2=None):
    """Imagen RGBA del cerebro. wave: progreso (0..1.4) de un frente de señal que recorre los pliegues.
    occ: intensidad de la corteza visual (occipital)."""
    B = brain_assets()
    m, sul, gyr, vol, ph = B["mask"], B["sul"], B["gyr"], B["vol"], B["phase"]
    th, tw = m.shape
    base_a = np.array((34, 28, 92), np.float32); base_b = np.array((88, 70, 190), np.float32)
    col = base_a[None, None, :] * (1 - vol[..., None]) + base_b[None, None, :] * vol[..., None]
    col = col * (0.62 + 0.75 * gyr[..., None]) * (0.55 + 0.75 * vol[..., None])
    col = col * (1 - 0.88 * sul[..., None])            # surcos oscuros
    lit = np.zeros_like(m)
    if wave is not None:
        d = np.abs(ph - wave)
        lit = np.exp(-(d / 0.045) ** 2) * (0.18 + 0.95 * sul)  # el frente ilumina sobre todo los surcos
    ripple = 0.5 + 0.5 * np.sin(t * 2.0 + ph * 18)
    pulse = (0.16 + 0.22 * ripple) * sul * glow          # actividad de fondo en los surcos
    c1 = np.array(CYAN, np.float32); c2 = np.array(MAGENTA, np.float32)
    colsul = c1[None, None, :] * (0.55 + 0.45 * (1 - ph[..., None])) + c2[None, None, :] * (0.45 * ph[..., None])
    col = col + colsul * (pulse + 1.7 * lit)[..., None] * 1.0
    if occ > 0:
        occm = np.exp(-(((B["x"]) / 330.0) ** 2 + ((B["y"] - 340) / 150.0) ** 2) ** 1.0) * m
        col = col + np.array((255, 120, 200), np.float32)[None, None, :] * (occm * occ * (0.6 + 0.4 * sul))[..., None] * 0.9
    # cerebelo
    cbc = (np.array((60, 50, 140), np.float32) * (0.55 + 0.6 * B["stri"][..., None]))
    col = col * m[..., None] + cbc * B["cb"][..., None]
    alpha = np.clip(m + B["cb"], 0, 1)
    # contorno neón
    rim = np.clip(m * (1 - np.clip(m * 1.0, 0, 1)) * 0, 0, 1)
    rgba = np.dstack([np.clip(col, 0, 255), alpha * 255]).astype(np.uint8)
    return Image.fromarray(rgba, "RGBA")


def brain_outline_pts():
    """Contorno aproximado (en coordenadas del lienzo del cerebro, centro en (0,0)) para el neón."""
    pts = []
    for sgn in (-1, 1):
        for a in np.linspace(-math.pi / 2, math.pi / 2, 90):
            yy = math.sin(a) * 470.0
            u = (yy + 420) / 840.0
            halfw = 372 * (1 - 0.20 * max(0.0, min(1.0, u - 0.55)) ** 1.2) * (0.80 + 0.20 * min(1.0, max(0.0, u / 0.25)) ** 0.6)
            xx = 9 + halfw * (abs(math.cos(a)) ** (2 / 2.5))
            pts.append((sgn * xx, yy))
    return pts
