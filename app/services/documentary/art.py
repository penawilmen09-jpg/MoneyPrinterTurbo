"""Primitivas de ilustración 2D vectorial (Skia, solo gráficos planos 2D).

Nada de 3D: todo son trazados vectoriales planos, degradados y capas con
paralaje. Los personajes son rigs 2D articulados (cinemática directa de ángulos).
"""
from __future__ import annotations

import math
from functools import lru_cache

import numpy as np
import skia

W, H = 1080, 1920
TAU = math.tau


# --------------------------------------------------------------------------
# color / paint helpers
# --------------------------------------------------------------------------
def rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def C(h: str, a: float = 1.0) -> int:
    r, g, b = rgb(h)
    return skia.Color(r, g, b, int(max(0, min(1, a)) * 255))


def mix(h1: str, h2: str, k: float) -> str:
    a, b = rgb(h1), rgb(h2)
    k = max(0.0, min(1.0, k))
    return "#%02x%02x%02x" % tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3))


def lit(h: str, light: tuple[float, float] | None) -> str:
    """light = (calidez 0..1, oscurecimiento 0..1)."""
    if not light:
        return h
    warm, dim = light
    h = mix(h, "#ffb36b", warm * 0.22)
    return mix(h, "#0b1830", dim)


def P(h: str, a: float = 1.0) -> skia.Paint:
    return skia.Paint(AntiAlias=True, Color=C(h, a))


def S(h: str, w: float, a: float = 1.0, cap=skia.Paint.kRound_Cap) -> skia.Paint:
    return skia.Paint(AntiAlias=True, Color=C(h, a), Style=skia.Paint.kStroke_Style,
                      StrokeWidth=w, StrokeCap=cap, StrokeJoin=skia.Paint.kRound_Join)


def vgrad(y0: float, y1: float, stops: list[tuple[float, str]], a: float = 1.0) -> skia.Paint:
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeLinear(
        [skia.Point(0, y0), skia.Point(0, y1)], [C(c, a) for _, c in stops], [s for s, _ in stops]))
    return p


def rgrad(cx: float, cy: float, r: float, stops: list[tuple[float, str, float]],
          blend=None) -> skia.Paint:
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeRadial(
        skia.Point(cx, cy), max(r, 1), [C(c, a) for _, c, a in stops], [s for s, _, _ in stops]))
    if blend is not None:
        p.setBlendMode(blend)
    return p


def poly(pts, close=True) -> skia.Path:
    path = skia.Path()
    path.moveTo(*pts[0])
    for p in pts[1:]:
        path.lineTo(*p)
    if close:
        path.close()
    return path


def smooth(pts) -> skia.Path:
    """Curva suave (Catmull-Rom → béziers) por los puntos."""
    path = skia.Path()
    path.moveTo(*pts[0])
    n = len(pts)
    for i in range(n - 1):
        p0, p1, p2 = pts[max(i - 1, 0)], pts[i], pts[i + 1]
        p3 = pts[min(i + 2, n - 1)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        path.cubicTo(*c1, *c2, *p2)
    return path


def ease(x: float) -> float:
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def seg(u: float, a: float, b: float) -> float:
    """0→1 entre a y b (lineal, acotado)."""
    return max(0.0, min(1.0, (u - a) / (b - a))) if b > a else float(u >= a)


# --------------------------------------------------------------------------
# paisaje
# --------------------------------------------------------------------------
@lru_cache(maxsize=64)
def _ridge_params(seed: int):
    r = np.random.default_rng(seed)
    return r.uniform(0, TAU, 5)


def ridge_values(xs: np.ndarray, seed: int, sharp: float = 1.0) -> np.ndarray:
    ph = _ridge_params(seed)
    f = np.array([0.0042, 0.0105, 0.0231, 0.049, 0.097])
    a = np.array([1.0, 0.55, 0.26, 0.12, 0.05])
    v = np.zeros_like(xs, dtype=float)
    for i in range(5):
        wave = 1 - np.abs(np.sin(f[i] * xs + ph[i]))
        v += a[i] * (wave ** sharp)
    return v / a.sum()


def draw_ridge(c: skia.Canvas, base: float, amp: float, seed: int, off: float,
               top: str, bot: str, *, shade: float = 0.18, sharp: float = 1.4,
               haze: str | None = None, haze_k: float = 0.0, y_bot: float | None = None):
    step = 10
    xs = np.arange(-30, W + 30 + step, step, dtype=float)
    v = ridge_values(xs + off, seed, sharp)
    ys = base - amp * v
    path = poly([(x, y) for x, y in zip(xs, ys)] + [(xs[-1], H), (xs[0], H)])
    top_c, bot_c = (mix(top, haze, haze_k), mix(bot, haze, haze_k)) if haze else (top, bot)
    ymin = float(ys.min())
    c.drawPath(path, vgrad(ymin, base + 40, [(0, top_c), (0.55, mix(top_c, bot_c, 0.7)), (1, bot_c)]))
    if shade > 0:
        # caras sombreadas (facetas planas) en la vertiente derecha de cada pico
        for i in range(2, len(xs) - 2):
            if v[i] > v[i - 1] and v[i] >= v[i + 1] and v[i] > 0.42:
                j = i
                while j + 1 < len(xs) and ys[j + 1] > ys[j] - 0.01 and j - i < 14:
                    j += 1
                if j > i + 1:
                    tri = [(xs[i], ys[i])] + [(xs[k], ys[k]) for k in range(i + 1, j + 1)] + [(xs[i], min(base + 40, ys[j] + (base - ys[j]) * 0.9))]
                    c.drawPath(poly(tri), P("#14305a", shade))


def draw_glacier(c: skia.Canvas, base: float, amp: float, seed: int, off: float, *,
                 light="#a8e2f2", mid="#59a4c8", dark="#2d6a96", step_px: int = 90):
    """Muro de hielo: bloques angulosos con caras iluminadas/sombreadas."""
    r = np.random.default_rng(seed)
    n = int((W + 400) / step_px) + 3
    # alturas deterministas en coordenadas de mundo
    k0 = int(math.floor((off - 200) / step_px))
    pts = []
    for k in range(k0, k0 + n):
        rr = np.random.default_rng(seed * 7919 + k)
        h = base - amp * (0.35 + 0.65 * rr.random())
        x = k * step_px - off + rr.uniform(-20, 20)
        pts.append((x, h))
    top = [(p[0], p[1]) for p in pts]
    path = poly(top + [(top[-1][0], H), (top[0][0], H)])
    c.drawPath(path, vgrad(base - amp, base + 60, [(0, light), (0.5, mid), (1, dark)]))
    for i in range(len(top) - 1):
        (x0, y0), (x1, y1) = top[i], top[i + 1]
        if y1 > y0:  # pendiente descendente: cara sombreada
            c.drawPath(poly([(x0, y0), (x1, y1), (x1, base + 60), (x0, base + 60)]), P("#173f6b", 0.22))
        else:        # pendiente ascendente: cara iluminada
            c.drawPath(poly([(x0, y0), (x1, y1), (x1, y1 + (base - y1) * 0.45), (x0, y0 + (base - y0) * 0.45)]), P("#ffffff", 0.14))
        c.drawLine(x0, y0, x1, y1, S("#eafcff", 3, 0.55))


def draw_ground(c: skia.Canvas, y: float, off: float, top: str, bot: str, seed: int = 3):
    c.drawRect(skia.Rect.MakeLTRB(-40, y, W + 40, H + 40), vgrad(y, H, [(0, top), (1, bot)]))
    # ondulaciones de ventisca (curvas planas)
    for k in range(5):
        yy = y + 70 + k * 120
        pts = [(x, yy + 18 * math.sin((x + off * (0.6 + 0.15 * k)) * 0.006 + k * 1.7)) for x in range(-40, W + 80, 60)]
        path = smooth(pts)
        path.lineTo(W + 80, yy + 130)
        path.lineTo(-40, yy + 130)
        path.close()
        c.drawPath(path, P("#ffffff", 0.10))
        c.drawPath(smooth(pts), S("#ffffff", 3, 0.22))


def draw_sky(c: skia.Canvas, stops, t: float, *, stars: float = 0.0, aurora: float = 0.0, h: float = H * 0.9):
    c.drawRect(skia.Rect.MakeLTRB(-60, -700, W + 60, h), vgrad(0, h, stops))
    if stars > 0:
        r = np.random.default_rng(11)
        for i in range(70):
            x, y = r.random() * W, r.random() * H * 0.45
            tw = 0.55 + 0.45 * math.sin(t * (1.2 + r.random() * 2) + i)
            c.drawCircle(x, y, 1 + r.random() * 1.6, P("#ffffff", stars * tw))
    if aurora > 0:
        sw, sh = 270, 170
        surf = skia.Surface(sw, sh)
        sc = surf.getCanvas()
        sc.clear(skia.ColorTRANSPARENT)
        for k, (c1, c2, y0, ph) in enumerate([("#38f2b4", "#2a6bd6", 50, 0.0), ("#5ad8ff", "#8a58d8", 80, 2.1), ("#7dffcf", "#2f86d9", 28, 4.0)]):
            top = [(x, y0 + 22 * math.sin(x * 0.03 + t * 0.55 + ph) + 14 * math.sin(x * 0.011 - t * 0.3 + ph)) for x in range(-10, sw + 20, 10)]
            thick = [34 + 14 * math.sin(x * 0.02 + t * 0.4 + ph * 2) for x in range(-10, sw + 20, 10)]
            path = poly(top + [(x, y + th) for (x, y), th in zip(reversed(top), reversed(thick))])
            p = skia.Paint(AntiAlias=True)
            p.setShader(skia.GradientShader.MakeLinear([skia.Point(0, y0 - 10), skia.Point(0, y0 + 60)],
                                                      [C(c1, 0.0), C(c1, 0.9), C(c2, 0.0)], [0, 0.35, 1]))
            p.setAlphaf(aurora * (0.75 + 0.25 * math.sin(t * 0.7 + k)))
            sc.drawPath(path, p)
        img = surf.makeImageSnapshot()
        c.drawImageRect(img, skia.Rect.MakeWH(sw, sh), skia.Rect.MakeLTRB(-20, 90, W + 20, 90 + sh * (W + 40) / sw),
                        skia.SamplingOptions(skia.FilterMode.kLinear), None)


# --------------------------------------------------------------------------
# partículas: nieve, ventisca, fuego, chispas, vaho
# --------------------------------------------------------------------------
@lru_cache(maxsize=32)
def _snow_state(seed: int, n: int):
    r = np.random.default_rng(seed)
    return r.random(n), r.random(n), r.random(n) * TAU, r.random(n)


def draw_snow(c: skia.Canvas, t: float, *, seed=1, n=220, fall=90.0, wind=40.0, alpha=0.85,
              size=(1.5, 5.0), sway=14.0):
    x0, y0, ph, sz = _snow_state(seed, n)
    spd = 0.6 + 0.8 * sz
    x = (x0 * (W + 300) + wind * t * spd + np.sin(t * (0.6 + sz) + ph) * sway) % (W + 300) - 150
    y = (y0 * (H + 200) + fall * t * spd) % (H + 200) - 100
    s = size[0] + (size[1] - size[0]) * sz
    for lo, hi in ((0, 0.34), (0.34, 0.67), (0.67, 1.01)):
        m = (sz >= lo) & (sz < hi)
        if not m.any():
            continue
        pts = [skia.Point(float(a), float(b)) for a, b in zip(x[m], y[m])]
        p = S("#ffffff", float(s[m].mean()), alpha * (0.55 + 0.45 * (lo + 0.17)))
        c.drawPoints(skia.Canvas.kPoints_PointMode, pts, p)


def draw_streaks(c: skia.Canvas, t: float, *, seed=5, n=50, speed=900.0, alpha=0.35, length=(120, 360), slope=0.12):
    r = np.random.default_rng(seed)
    x0, y0, ln, a = r.random(n), r.random(n), r.uniform(*length, n), r.uniform(0.4, 1, n)
    sp = speed * (0.7 + 0.6 * r.random(n))
    for i in range(n):
        x = (x0[i] * (W + 800) + sp[i] * t) % (W + 800) - 400
        y = y0[i] * H + 20 * math.sin(t * 2 + i)
        c.drawLine(x, y, x - ln[i], y - ln[i] * slope, S("#ffffff", 2 + 2 * a[i], alpha * a[i]))


def draw_fire(c: skia.Canvas, x: float, y: float, size: float, t: float, power: float = 1.0, seed: int = 0):
    """Hoguera 2D: leños, llamas animadas de 3 capas, brasas y chispas."""
    if power <= 0.02:
        return
    s = size * (0.35 + 0.65 * power)
    # resplandor
    glow = rgrad(x, y - s * 0.5, s * 3.2, [(0, "#ff9a3c", 0.55 * power), (0.4, "#ff6a1a", 0.2 * power), (1, "#ff6a1a", 0.0)],
                 blend=skia.BlendMode.kPlus)
    c.drawCircle(x, y - s * 0.5, s * 3.2, glow)
    # leños
    c.drawLine(x - size * 0.5, y + size * 0.05, x + size * 0.45, y - size * 0.12, S("#3b261c", size * 0.17))
    c.drawLine(x + size * 0.5, y + size * 0.05, x - size * 0.45, y - size * 0.12, S("#4a2f22", size * 0.17))
    c.drawLine(x - size * 0.42, y + size * 0.03, x + size * 0.36, y - size * 0.13, S("#5a3a2a", 3, 0.7))
    layers = [(1.0, "#ff5a1f", 0.95), (0.78, "#ff9d1f", 0.97), (0.5, "#ffe27a", 1.0)]
    nt = 5
    for k, (sc, colr, al) in enumerate(layers):
        for j in range(nt):
            ph = seed + j * 1.7 + k * 0.6
            fx = x + (j - (nt - 1) / 2) * s * 0.26 * sc
            hh = s * (0.9 + 0.5 * math.sin(t * 7 + ph) * 0.35 + 0.25 * math.sin(t * 11.3 + ph * 2)) * sc * (1.0 - 0.18 * abs(j - 2))
            sway = math.sin(t * 5.1 + ph) * s * 0.12 + math.sin(t * 2.3 + ph) * s * 0.06
            wbase = s * 0.20 * sc
            path = skia.Path()
            path.moveTo(fx - wbase, y)
            path.cubicTo(fx - wbase * 1.3, y - hh * 0.45, fx + sway * 0.4 - wbase * 0.2, y - hh * 0.7, fx + sway, y - hh)
            path.cubicTo(fx + sway * 0.4 + wbase * 0.5, y - hh * 0.62, fx + wbase * 1.3, y - hh * 0.4, fx + wbase, y)
            path.close()
            c.drawPath(path, P(colr, al * min(1, power * 1.5)))
    # chispas
    r = np.random.default_rng(seed + 99)
    for i in range(14):
        life = (t * (0.35 + 0.5 * r.random()) + r.random() * 5) % 1.0
        px = x + (r.random() - 0.5) * s * 0.9 + math.sin(t * 2 + i) * s * 0.35 * life
        py = y - s * 0.6 - life * s * (1.4 + 1.8 * r.random())
        c.drawCircle(px, py, max(0.8, (1 - life) * (2.2 + 2 * r.random())), P("#ffc15a", (1 - life) * power))
    # humo suave
    for i in range(5):
        life = (t * 0.22 + i / 5) % 1.0
        c.drawCircle(x + math.sin(life * 6 + i) * s * 0.3 + life * 40, y - s * 1.2 - life * s * 2.4, s * (0.25 + life * 0.55),
                     P("#7f93ab", 0.14 * (1 - life) * power))


def draw_breath(c: skia.Canvas, t: float, mx: float, my: float, f: int, *, period: float = 2.4, seed: float = 0.0, size: float = 1.0):
    k = ((t + seed) % period) / period
    if k > 0.7:
        return
    k = k / 0.7
    r = (6 + 26 * k) * size
    c.drawCircle(mx + f * (10 + 55 * k) * size, my - 30 * k * size, r, P("#eaf6ff", 0.38 * (1 - k)))
    c.drawCircle(mx + f * (22 + 70 * k) * size, my - 44 * k * size, r * 0.7, P("#eaf6ff", 0.22 * (1 - k)))


def vignette(c: skia.Canvas, strength: float = 0.5, tint: str = "#06101f"):
    c.drawRect(skia.Rect.MakeWH(W, H), rgrad(W / 2, H * 0.52, H * 0.78, [(0.5, tint, 0.0), (1.0, tint, strength)]))


# --------------------------------------------------------------------------
# PERSONAJES — mismos 3 personajes en las 6 escenas
# --------------------------------------------------------------------------
KINDS = {
    "man":   dict(k=1.00, head=0.082, coat="#6a5340", coat_f="#54402f", trim="#d6cab2", pants="#3a3946", boot="#2c262b",
                  skin="#d8a584", hair="#241a14", beard=True),
    "woman": dict(k=0.92, head=0.078, coat="#8c5246", coat_f="#6f3f37", trim="#e6dfcf", pants="#44394a", boot="#312729",
                  skin="#e0b093", hair="#3a2316", beard=False),
    "child": dict(k=0.56, head=0.105, coat="#b88e46", coat_f="#966f33", trim="#f1e8d3", pants="#4a4352", boot="#3a2f2d",
                  skin="#e4b79b", hair="#4c2f1c", beard=False),
}


def _pt(o, a, l, f):
    return (o[0] + math.sin(a) * f * l, o[1] + math.cos(a) * l)


def blink(t: float, seed: float = 0.0) -> float:
    k = (t * 0.37 + seed) % 1.0
    return 0.1 if k < 0.03 else 1.0


def pose_walk(ph: float, *, amp=0.42, arm=1.0, lean=0.06, carry=False):
    sn, cs = math.sin(ph), math.cos(ph)
    p = dict(lean=lean + 0.015 * math.sin(2 * ph),
             tn=amp * sn, tf=-amp * sn,
             cn=amp * sn - 1.0 * amp * max(0, cs), cf=-amp * sn - 1.0 * amp * max(0, -cs),
             head=0.0)
    if carry:
        p.update(an1=0.9, an2=1.55, af1=0.55, af2=1.4)
    else:
        p.update(an1=-0.5 * arm * sn, an2=-0.5 * arm * sn + 0.35, af1=0.5 * arm * sn, af2=0.5 * arm * sn + 0.35)
    return p


def pose_stand(t: float, *, lean=0.0, arms="rest", sway=0.012):
    b = math.sin(t * 1.6) * sway
    p = dict(lean=lean + b, tn=0.05, tf=-0.08, cn=0.05, cf=-0.08, head=0.0 + 0.02 * math.sin(t * 0.9))
    if arms == "rest":
        p.update(an1=0.08 + b, an2=0.35, af1=-0.05, af2=0.2)
    elif arms == "warm":      # manos extendidas hacia el fuego
        p.update(an1=1.35 + 0.05 * math.sin(t * 2), an2=1.55, af1=1.15, af2=1.45)
    return p


def pose_sit(t: float, *, lean=0.02, arms="rest"):
    p = dict(lean=lean, hip_h=0.085, tn=1.38, tf=1.25, cn=0.15, cf=0.05, head=0.0 + 0.02 * math.sin(t * 0.8))
    if arms == "rest":
        p.update(an1=0.55, an2=1.2, af1=0.4, af2=1.1)
    return p


def pose_kneel(t: float, *, lean=0.35):
    return dict(lean=lean, hip_h=0.25, tn=1.25, cn=-0.1, tf=-0.45, cf=-1.55, head=0.15,
                an1=0.95, an2=1.55, af1=0.75, af2=1.4)


def draw_person(c: skia.Canvas, kind: str, x: float, gy: float, size: float, face: int, pose: dict, t: float, *,
                light: tuple[float, float] | None = None, mood: float = 0.0, look: float = 0.0,
                prop: str | None = None, prop_angle: float = 0.0, seed: float = 0.0, wind: float = 0.0):
    """Dibuja un personaje (x,gy = punto entre los pies, size = altura de adulto en px).

    Devuelve (boca_x, boca_y, mano_cercana(x,y), mano_lejana(x,y))."""
    K = KINDS[kind]
    u = size * K["k"]
    f = face
    L = lambda col: lit(col, light)
    l1 = l2 = 0.235 * u
    lean = pose.get("lean", 0.0)

    tn, cn, tf, cf = pose.get("tn", 0), pose.get("cn", 0), pose.get("tf", 0), pose.get("cf", 0)
    depth = lambda a, b: math.cos(a) * l1 + math.cos(b) * l2
    if "hip_h" in pose:
        hh = pose["hip_h"] * u
    else:
        hh = max(depth(tn, cn), depth(tf, cf)) + 0.01 * u
    hip = (x, gy - hh)

    # --- piernas
    def leg(th, ca, col, dx=0.0):
        o = (hip[0] + dx * u * f, hip[1])
        knee = _pt(o, th, l1, f)
        ank = _pt(knee, ca, l2, f)
        c.drawPath(poly([o, knee, ank], close=False), S(col, 0.075 * u))
        # bota
        toe = (ank[0] + f * 0.07 * u, ank[1] + 0.012 * u)
        c.drawLine(ank[0] - f * 0.01 * u, ank[1], toe[0], toe[1], S(L(K["boot"]), 0.058 * u))
        c.drawLine(ank[0] - f * 0.005 * u, ank[1] - 0.045 * u, ank[0] + f * 0.015 * u, ank[1] - 0.02 * u, S(L(K["trim"]), 0.062 * u))
        return knee, ank

    leg(tf, cf, L(K["pants"]), dx=-0.012)
    leg(tn, cn, L(mix(K["pants"], "#ffffff", 0.07)), dx=0.012)

    # --- brazos lejano (detrás del torso)
    sh = (hip[0] + math.sin(lean) * f * 0.30 * u, hip[1] - math.cos(lean) * 0.30 * u)

    def arm(a1, a2, col, cuff, hand_col):
        o = (sh[0] - f * 0.004 * u, sh[1] + 0.012 * u)
        el = _pt(o, a1, 0.15 * u, f)
        hd = _pt(el, a2, 0.14 * u, f)
        c.drawPath(poly([o, el, hd], close=False), S(col, 0.07 * u))
        c.drawLine(*_pt(el, a2, 0.1 * u, f), *hd, S(cuff, 0.074 * u))
        c.drawCircle(hd[0], hd[1], 0.032 * u, P(hand_col))
        return hd

    hand_f = arm(pose.get("af1", 0), pose.get("af2", 0.2), L(K["coat_f"]), L(mix(K["trim"], "#000000", 0.2)), L(mix(K["skin"], "#000000", 0.12)))

    # --- abrigo (torso + falda de piel)
    # trazado explícito (sin rotaciones complicadas): hombros, cintura y borde
    hw = 0.082 * u
    back_s = (sh[0] - f * hw, sh[1] + 0.005 * u)
    front_s = (sh[0] + f * hw * 0.85, sh[1] + 0.005 * u)
    waist_b = (hip[0] - f * 0.075 * u, hip[1] - 0.01 * u)
    waist_f = (hip[0] + f * 0.07 * u, hip[1] - 0.01 * u)
    hem_b = (hip[0] - f * 0.115 * u, hip[1] + 0.12 * u)
    hem_f = (hip[0] + f * 0.105 * u, hip[1] + 0.12 * u)
    coat = skia.Path()
    coat.moveTo(*back_s)
    coat.quadTo(sh[0] - f * hw * 0.2, sh[1] - 0.04 * u, *front_s)
    coat.lineTo(*waist_f)
    coat.lineTo(*hem_f)
    coat.quadTo(hip[0], hip[1] + 0.145 * u, *hem_b)
    coat.lineTo(*waist_b)
    coat.close()
    c.drawPath(coat, P(L(K["coat"])))
    # costuras / sombra
    c.drawLine(hip[0] - f * 0.01 * u, hip[1] + 0.12 * u, sh[0] - f * 0.005 * u, sh[1] + 0.03 * u, S(L(K["coat_f"]), 0.012 * u, 0.6))
    c.drawLine(waist_b[0], waist_b[1] + 0.012 * u, waist_f[0], waist_f[1] + 0.012 * u, S(L("#2a1f1a"), 0.02 * u))
    # borde de piel
    for i in range(7):
        k = i / 6
        px = hem_b[0] + (hem_f[0] - hem_b[0]) * k
        py = hem_b[1] + 0.012 * u * math.sin(k * math.pi) * -1 + 0.006 * u
        c.drawCircle(px, py, 0.026 * u, P(L(K["trim"])))
    # cuello de piel
    c.drawCircle(sh[0] + f * 0.01 * u, sh[1] - 0.012 * u, 0.05 * u, P(L(K["trim"])))
    c.drawCircle(sh[0] - f * 0.03 * u, sh[1] - 0.005 * u, 0.04 * u, P(L(mix(K["trim"], "#000000", 0.1))))

    # --- cabeza
    hr = K["head"] * u
    tilt = pose.get("head", 0.0) + look
    hc = (sh[0] + math.sin(lean + tilt) * f * (0.045 * u + hr) + f * 0.012 * u,
          sh[1] - math.cos(lean + tilt) * (0.032 * u + hr))
    sway_w = wind * 0.02 * u
    if kind == "woman":
        # trenza (detrás) con balanceo
        bx, by = hc[0] - f * hr * 0.9, hc[1] + hr * 0.2
        pts = [(bx, by), (bx - f * (0.04 * u + sway_w), by + 0.07 * u), (bx - f * (0.05 * u + sway_w * 1.6), by + 0.15 * u),
               (bx - f * (0.04 * u + sway_w * 2.0), by + 0.22 * u + 0.0)]
        c.drawPath(smooth(pts), S(L(K["hair"]), 0.045 * u))
        c.drawCircle(*pts[-1], 0.03 * u, P(L("#a94a3c")))
    c.drawCircle(*hc, hr, P(L(K["skin"])))
    # nariz
    c.drawPath(poly([(hc[0] + f * hr * 0.92, hc[1] - hr * 0.08), (hc[0] + f * hr * 1.22, hc[1] + hr * 0.2), (hc[0] + f * hr * 0.9, hc[1] + hr * 0.28)]),
               P(L(mix(K["skin"], "#a05a46", 0.25))))
    # pelo / capucha / gorro
    if kind == "man":
        hat = skia.Path()
        hat.addArc(skia.Rect.MakeLTRB(hc[0] - hr * 1.12, hc[1] - hr * 1.18, hc[0] + hr * 1.12, hc[1] + hr * 0.92),
                   180 if f == 1 else 180, 180)
        c.drawPath(hat, P(L("#4b392c")))
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(hc[0] - hr * 1.1, hc[1] - hr * 0.35, hc[0] + hr * 1.1, hc[1] - hr * 0.02), hr * 0.15, hr * 0.15),
                    P(L(K["trim"])))
        c.drawCircle(hc[0] - f * hr * 0.85, hc[1] + hr * 0.35, hr * 0.5, P(L(K["hair"])))   # pelo largo atrás
        # barba
        beard = poly([(hc[0] + f * hr * 0.15, hc[1] + hr * 0.22), (hc[0] + f * hr * 0.98, hc[1] + hr * 0.3), (hc[0] + f * hr * 0.9, hc[1] + hr * 0.95),
                      (hc[0] + f * hr * 0.25, hc[1] + hr * 1.5), (hc[0] - f * hr * 0.4, hc[1] + hr * 0.8)])
        c.drawPath(beard, P(L("#3b2a1f")))
    else:
        hood_col = L(K["coat"])
        ring = S(L(K["trim"]), hr * 0.42)
        hood = skia.Path()
        hood.addCircle(hc[0] - f * hr * 0.12, hc[1] - hr * 0.02, hr * 1.3)
        c.drawPath(hood, P(hood_col))
        # abertura de la capucha (cara) – círculo de piel encima, con aro de piel
        c.drawCircle(hc[0] + f * hr * 0.2, hc[1] + hr * 0.05, hr * 0.98, P(L(K["skin"])))
        c.drawCircle(hc[0] + f * hr * 0.2, hc[1] + hr * 0.05, hr * 1.05, S(L(K["trim"]), hr * 0.38))
        # flequillo
        c.drawPath(smooth([(hc[0] - f * hr * 0.5, hc[1] - hr * 0.8), (hc[0] + f * hr * 0.25, hc[1] - hr * 0.98), (hc[0] + f * hr * 0.85, hc[1] - hr * 0.72)]),
                   S(L(K["hair"]), hr * 0.26))
        # nariz sobre la capucha
        c.drawPath(poly([(hc[0] + f * hr * 1.1, hc[1] - hr * 0.02), (hc[0] + f * hr * 1.38, hc[1] + hr * 0.24), (hc[0] + f * hr * 1.08, hc[1] + hr * 0.32)]),
                   P(L(mix(K["skin"], "#a05a46", 0.25))))
    # cara
    fx = hc[0] + f * hr * (0.55 if kind == "man" else 0.72)
    ey = hc[1] - hr * 0.08
    bl = blink(t, seed)
    c.drawOval(skia.Rect.MakeLTRB(fx - hr * 0.13, ey - hr * 0.16 * bl, fx + hr * 0.13, ey + hr * 0.16 * bl), P("#1b1512"))
    c.drawCircle(fx + f * hr * 0.04, ey - hr * 0.05 * bl, hr * 0.04, P("#ffffff"))
    bb = ey - hr * (0.32 + 0.06 * max(mood, 0))
    c.drawLine(fx - f * hr * 0.2, bb, fx + f * hr * 0.24, bb - hr * 0.1 * max(-mood, 0) + hr * 0.05 * max(mood, 0), S(L(K["hair"]), hr * 0.1, 0.9))
    my = hc[1] + hr * 0.52
    mx0, mx1 = fx - hr * 0.15 + f * hr * 0.08, fx + hr * 0.35
    mp = skia.Path()
    mp.moveTo(mx0, my)
    mp.quadTo((mx0 + mx1) / 2, my + hr * 0.22 * mood, mx1, my - hr * 0.05 * mood)
    c.drawPath(mp, S("#5b2f28", hr * 0.075))
    if mood > 0.4:
        c.drawCircle(fx + f * hr * 0.05, hc[1] + hr * 0.38, hr * 0.17, P("#ff8f7a", 0.28 * mood))   # mejilla

    # --- brazo cercano + props
    hand_n = arm(pose.get("an1", 0), pose.get("an2", 0.2), L(K["coat"]), L(K["trim"]), L(K["skin"]))
    if prop == "spear":
        a = prop_angle
        base = (hand_n[0] - math.sin(a) * f * 0.28 * u, hand_n[1] + math.cos(a) * 0.28 * u)
        tip = (hand_n[0] + math.sin(a) * f * 0.62 * u, hand_n[1] - math.cos(a) * 0.62 * u)
        c.drawLine(*base, *tip, S("#5a4030", 0.014 * u))
        d = (tip[0] - base[0], tip[1] - base[1])
        n = math.hypot(*d)
        d = (d[0] / n, d[1] / n)
        c.drawPath(poly([(tip[0] + d[0] * 0.07 * u, tip[1] + d[1] * 0.07 * u), (tip[0] - d[1] * 0.022 * u, tip[1] + d[0] * 0.022 * u),
                         (tip[0] + d[1] * 0.022 * u, tip[1] - d[0] * 0.022 * u)]), P("#b9c9d6"))
    elif prop == "bundle":
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(hand_n[0] - 0.06 * u, hand_n[1] - 0.02 * u, 0.12 * u, 0.1 * u), 0.03 * u, 0.03 * u), P(L("#7b6247")))
        c.drawLine(hand_n[0] - 0.06 * u, hand_n[1] + 0.03 * u, hand_n[0] + 0.06 * u, hand_n[1] + 0.03 * u, S(L("#3d2d22"), 0.012 * u))
    elif prop == "stick_meat":
        a = prop_angle
        tip = (hand_n[0] + math.sin(a) * f * 0.42 * u, hand_n[1] - math.cos(a) * 0.42 * u)
        c.drawLine(hand_n[0] - math.sin(a) * f * 0.1 * u, hand_n[1] + math.cos(a) * 0.1 * u, *tip, S("#6a4a33", 0.014 * u))
        c.drawOval(skia.Rect.MakeXYWH(tip[0] - 0.045 * u, tip[1] - 0.03 * u, 0.09 * u, 0.06 * u), P("#a8543a"))
    elif prop == "scraper":
        a = prop_angle
        c.drawLine(hand_n[0], hand_n[1], hand_n[0] + math.sin(a) * f * 0.12 * u, hand_n[1] + math.cos(a) * 0.12 * u, S("#efe8d6", 0.03 * u))
    elif prop == "flint":
        c.drawCircle(hand_n[0], hand_n[1], 0.026 * u, P("#7e8a99"))
        c.drawCircle(hand_f[0], hand_f[1], 0.026 * u, P("#9aa5b2"))
    return hc[0] + f * hr, hc[1] + hr * 0.5, hand_n, hand_f


# --------------------------------------------------------------------------
# MAMUT
# --------------------------------------------------------------------------
def draw_mammoth(c: skia.Canvas, x: float, gy: float, size: float, face: int, t: float, *,
                 body="#4c3d3a", body_f="#382d2b", fur="#6a5750", tusk="#f1ead4", haze: tuple[str, float] | None = None,
                 speed: float = 1.0, trunk_up: float = 0.0, seed: float = 0.0):
    f = face
    s = size
    col = lambda h: mix(h, haze[0], haze[1]) if haze else h
    ph = t * 2.2 * speed + seed
    bob = math.sin(ph * 2) * s * 0.006

    def legs(far: bool):
        for i, (lx, off) in enumerate([(-0.34, 0.0), (-0.18, math.pi), (0.2, math.pi), (0.36, 0.0)]):
            if (i in (1, 2)) != far:
                continue
            sw = math.sin(ph + off) * 0.1 * s
            lift = max(0.0, math.cos(ph + off)) * 0.05 * s
            top = (x + f * lx * s, gy - 0.5 * s + bob)
            bot = (top[0] + sw, gy - lift)
            c.drawLine(*top, *bot, S(col(body_f if far else body), 0.15 * s))
            c.drawOval(skia.Rect.MakeXYWH(bot[0] - 0.095 * s, bot[1] - 0.03 * s, 0.19 * s, 0.05 * s), P(col("#2b2220")))
            c.drawLine(top[0], top[1] + 0.2 * s, bot[0], bot[1] - 0.06 * s, S(col(fur), 0.05 * s, 0.6))

    legs(True)
    # cuerpo
    cx, cy = x, gy - 0.62 * s + bob
    bodyp = skia.Path()
    bodyp.moveTo(cx - f * 0.52 * s, cy + 0.12 * s)
    bodyp.cubicTo(cx - f * 0.55 * s, cy - 0.28 * s, cx - f * 0.2 * s, cy - 0.4 * s, cx + f * 0.05 * s, cy - 0.38 * s)   # lomo
    bodyp.cubicTo(cx + f * 0.3 * s, cy - 0.5 * s, cx + f * 0.58 * s, cy - 0.34 * s, cx + f * 0.6 * s, cy - 0.05 * s)  # joroba/frente
    bodyp.cubicTo(cx + f * 0.62 * s, cy + 0.2 * s, cx + f * 0.4 * s, cy + 0.26 * s, cx + f * 0.1 * s, cy + 0.26 * s)
    bodyp.cubicTo(cx - f * 0.2 * s, cy + 0.28 * s, cx - f * 0.5 * s, cy + 0.26 * s, cx - f * 0.52 * s, cy + 0.12 * s)
    bodyp.close()
    c.drawPath(bodyp, P(col(body)))
    c.save()
    c.clipPath(bodyp, skia.ClipOp.kIntersect, True)
    # faldón de pelo (flecos)
    fr = [(cx - f * 0.5 * s + f * i * 0.075 * s, cy + (0.24 + (0.07 if i % 2 else 0.02) + 0.01 * math.sin(t * 2 + i)) * s) for i in range(15)]
    c.drawPath(poly([(cx - f * 0.5 * s, cy + 0.2 * s)] + fr + [(cx + f * 0.58 * s, cy + 0.2 * s)]), P(col(fur), 0.9))
    for i in range(6):
        yy = cy - 0.3 * s + i * 0.06 * s
        c.drawPath(smooth([(cx - f * 0.35 * s, yy), (cx, yy - 0.03 * s), (cx + f * 0.35 * s, yy + 0.01 * s)]), S(col(fur), 0.012 * s, 0.5))
    c.restore()
    # cabeza + trompa
    hx, hy = cx + f * 0.62 * s, cy + 0.0 * s
    c.drawCircle(hx, hy, 0.2 * s, P(col(body)))
    c.drawCircle(hx - f * 0.02 * s, hy - 0.16 * s, 0.17 * s, P(col(body)))   # frente abombada
    # oreja
    c.drawPath(poly([(hx - f * 0.12 * s, hy - 0.12 * s), (hx - f * 0.3 * s, hy - 0.02 * s), (hx - f * 0.2 * s, hy + 0.14 * s), (hx - f * 0.08 * s, hy + 0.06 * s)]), P(col(body_f)))
    # trompa
    tr = [(hx + f * 0.14 * s, hy + 0.05 * s)]
    sway = math.sin(ph * 0.9) * 0.05 * s
    up = trunk_up
    tr.append((hx + f * (0.2 + 0.1 * up) * s, hy + (0.22 - 0.3 * up) * s))
    tr.append((hx + f * (0.2 + 0.15 * up) * s + sway, hy + (0.42 - 0.55 * up) * s))
    tr.append((hx + f * (0.14 + 0.2 * up) * s + sway * 1.5, hy + (0.56 - 0.8 * up) * s))
    path = smooth(tr)
    c.drawPath(path, S(col(body), 0.12 * s))
    c.drawPath(smooth(tr[1:]), S(col(body), 0.085 * s))
    c.drawPath(path, S(col(fur), 0.012 * s, 0.4))
    # colmillos
    for dz, wd in ((0.0, 0.034), (0.05, 0.028)):
        tp = [(hx + f * 0.1 * s, hy + (0.1 + dz) * s), (hx + f * 0.3 * s, hy + (0.25 + dz) * s), (hx + f * 0.45 * s, hy + (0.12 + dz) * s), (hx + f * 0.42 * s, hy + (-0.08 + dz) * s)]
        c.drawPath(smooth(tp), S(col(tusk), wd * s))
    # ojo
    c.drawCircle(hx + f * 0.09 * s, hy - 0.04 * s, 0.014 * s, P("#120d0c"))
    legs(False)


# --------------------------------------------------------------------------
# TIENDA de huesos y pieles
# --------------------------------------------------------------------------
def draw_tent(c: skia.Canvas, cx: float, gy: float, size: float, t: float, glow: float = 0.0, wind: float = 0.0):
    s = size
    apex = (cx + 0.02 * s, gy - 0.9 * s)
    L, R = (cx - 0.6 * s, gy), (cx + 0.6 * s, gy)
    for sgn in (-1, 1):   # colmillos cruzados en el vértice
        tusk = smooth([(apex[0] - sgn * 0.01 * s, apex[1] + 0.02 * s), (apex[0] + sgn * 0.05 * s, apex[1] - 0.1 * s), (apex[0] + sgn * 0.13 * s, apex[1] - 0.15 * s)])
        c.drawPath(tusk, S("#efe8d3", 0.028 * s))
    body = skia.Path()
    body.moveTo(*L)
    body.quadTo(cx - 0.42 * s, gy - 0.55 * s, *apex)
    body.quadTo(cx + 0.45 * s, gy - 0.55 * s, *R)
    body.quadTo(cx, gy + 0.05 * s, *L)
    c.drawPath(body, vgrad(apex[1], gy, [(0, "#8d7864"), (1, "#5d4a3d")]))
    # paneles de piel y costuras
    for k in range(-2, 3):
        c.drawPath(smooth([apex, (cx + k * 0.16 * s, gy - 0.45 * s), (cx + k * 0.24 * s, gy - 0.02 * s)]), S("#3f3128", 0.012 * s, 0.7))
    for k in range(3):
        yy = gy - (0.2 + k * 0.22) * s
        half = 0.58 * s * (1 - (0.2 + k * 0.22) / 0.9)
        c.drawPath(smooth([(cx - half, yy), (cx, yy + 0.04 * s), (cx + half, yy)]), S("#4a392e", 0.01 * s, 0.55))
    # sombra derecha
    c.drawPath(poly([apex, R, (cx + 0.1 * s, gy)]), P("#1a2d4a", 0.22))
    # puerta (resplandor cálido)
    door = skia.Path()
    door.moveTo(cx - 0.17 * s, gy)
    door.lineTo(cx - 0.12 * s, gy - 0.34 * s)
    door.lineTo(cx + 0.12 * s, gy - 0.34 * s)
    door.lineTo(cx + 0.17 * s, gy)
    door.close()
    c.drawPath(door, vgrad(gy - 0.34 * s, gy, [(0, mix("#2a1c16", "#ff9a3c", glow * 0.8)), (1, mix("#3b2418", "#ffc065", glow))]))
    # humo por el vértice
    for i in range(6):
        life = (t * 0.28 + i / 6) % 1.0
        c.drawCircle(apex[0] + 0.06 * s + life * s * 0.5 * (0.5 + wind), apex[1] - 0.05 * s - life * s * 0.7, s * (0.04 + life * 0.1),
                     P("#aab9c8", 0.35 * (1 - life)))
    # nieve acumulada
    c.drawPath(smooth([(L[0] - 0.05 * s, gy + 0.01 * s), (cx - 0.3 * s, gy - 0.04 * s), (cx + 0.3 * s, gy - 0.04 * s), (R[0] + 0.05 * s, gy + 0.01 * s)]), S("#f2f9ff", 0.05 * s, 0.9))
