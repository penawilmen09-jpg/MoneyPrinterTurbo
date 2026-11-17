"""Seis escenas 2D del documental + compositor de fotogramas (Skia, 1080x1920)."""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import skia

from .art import (C, H, P, S, W, draw_breath, draw_fire, draw_glacier, draw_ground, draw_mammoth,
                  draw_person, draw_ridge, draw_sky, draw_snow, draw_streaks, draw_tent, ease, mix,
                  pose_kneel, pose_sit, pose_stand, pose_walk, poly, rgrad, seg, smooth, vgrad,
                  vignette)

FPS = 30
GROUND_Y_DEFAULT = 1400


def camera(c: skia.Canvas, zoom: float, fx: float, fy: float, dy: float = 0.0):
    c.translate(fx, fy + dy)
    c.scale(zoom, zoom)
    c.translate(-fx, -fy)


def _sky(c, stops, t, **kw):
    c.drawRect(skia.Rect.MakeLTRB(-60, -700, W + 60, 40), P(stops[0][1]))
    draw_sky(c, stops, t, **kw)


def _fog(c, y0, y1, color="#e8f2f9", a=0.5):
    c.drawRect(skia.Rect.MakeLTRB(-60, y0, W + 60, y1), vgrad(y0, y1, [(0, color + ""), (1, color)], 0.0) if False else
               _band(y0, y1, color, a))


def _band(y0, y1, color, a):
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeLinear([skia.Point(0, y0), skia.Point(0, y1)], [C(color, 0), C(color, a), C(color, 0)], [0, 0.5, 1]))
    return p


def _ice_shards(c, off, color="#173556", seed=3):
    """Cristales de hielo en primer plano (siluetas)."""
    for side, x0 in ((0, -60), (1, W - 150)):
        for k in range(4):
            r = np.random.default_rng(seed + k + side * 10)
            x = x0 + k * 60 * (1 if side == 0 else 1) + r.uniform(-10, 10) - off
            hgt = 120 + r.uniform(0, 170) * (1.4 - k * 0.25)
            w = 50 + r.uniform(0, 40)
            c.drawPath(poly([(x, H + 20), (x + w * 0.3, H - hgt), (x + w, H - hgt * 0.45), (x + w * 1.1, H + 20)]), P(color, 0.96))
            c.drawLine(x + w * 0.3, H - hgt, x + w * 0.1, H + 20, S("#6fb8de", 3, 0.5))


def _footprints(c, x_of_u, u, gy, off, spacing=0.75, y_jit=6):
    k = 0
    while True:
        uu = u - 0.4 - k * spacing
        if uu < 0 or k > 12:
            break
        x = x_of_u(uu) - off
        c.drawOval(skia.Rect.MakeXYWH(x - 15, gy + (6 if k % 2 else -4) - 2 + y_jit, 30, 9), P("#5c82a8", 0.3 * (1 - k / 14)))
        k += 1


def _hand_at(kind, x, gy, size, face, pose, **kw):
    """Posición de la mano cercana para una pose dada (dibujo en superficie de usar y tirar)."""
    surf = skia.Surface(4, 4)
    return draw_person(surf.getCanvas(), kind, x, gy, size, face, pose, 0.0, **kw)[2]


# ---------------------------------------------------------------------------
# ESCENA 1 — el mundo helado
# ---------------------------------------------------------------------------
def scene1(c, u, D):
    cam = 38 * u
    z = 1.0 + 0.11 * ease(u / D)
    c.save()
    camera(c, z, 540, 1300)
    _sky(c, [(0, "#0c1f44"), (0.4, "#2b5a8d"), (0.75, "#8fbad6"), (1, "#d3ebf5")], u, stars=0.8 * (1 - seg(u, 0, 7)), aurora=1.0, h=1450)
    draw_ridge(c, 1060, 640, 21, cam * 0.06, "#e6f3fb", "#7b9fc2", haze="#bfe0ef", haze_k=0.45, shade=0.12)
    draw_ridge(c, 1230, 520, 34, cam * 0.16, "#f1f9fe", "#4d77a0", haze="#a8cfe3", haze_k=0.25)
    draw_glacier(c, 1420, 330, 5, cam * 0.38)
    draw_ground(c, 1415, cam, "#e5f1f9", "#a6c4dc")
    # manada lejana
    for i in range(3):
        draw_mammoth(c, 930 - i * 170 + 0 * u - cam * 0.5 + u * 8, 1455, 120 - i * 8, -1, u + i, body="#3c566f", body_f="#33495f", fur="#4d6a84", tusk="#d9e6ee", haze=("#9fc2db", 0.4), speed=0.5)
    gy = 1545
    xm = lambda uu: 110 + 150 * uu
    _footprints(c, xm, u, gy, cam)
    ph = TAU_ * 0.65 * u
    walkers = [("woman", xm(u) - 330, 1535, 1), ("child", xm(u) - 170, 1550, 1), ("man", xm(u), 1545, 1)]
    for i, (k, x, g, f) in enumerate(walkers):
        size = 330
        pose = pose_walk(ph + i * 0.7, amp=0.4, lean=0.1, carry=(k == "man"))
        mx, my, _, _ = draw_person(c, k, x - cam, g, size, f, pose, u, mood=0.0, prop=("bundle" if k == "man" else None), seed=i * 0.3, wind=0.5)
        draw_breath(c, u, mx, my, f, seed=i * 0.7, size=1.2)
    _ice_shards(c, cam * 1.4)
    draw_snow(c, u, seed=1, n=170, fall=80, wind=70, alpha=0.8)
    draw_snow(c, u, seed=2, n=70, fall=140, wind=110, alpha=0.9, size=(4, 9), sway=30)
    draw_streaks(c, u, n=22, alpha=0.18, speed=700)
    c.restore()


TAU_ = math.tau


# ---------------------------------------------------------------------------
# ESCENA 2 — caza y pieles
# ---------------------------------------------------------------------------
def scene2(c, u, D):
    cam = 10 + 22 * u
    z = 1.0 + 0.09 * ease(u / D)
    c.save()
    camera(c, z, 640, 1350)
    _sky(c, [(0, "#8fb0cb"), (0.55, "#c5dbe9"), (1, "#eaf4fa")], u, h=1450)
    draw_ridge(c, 1080, 560, 8, cam * 0.07, "#f4fafe", "#8bb0cd", haze="#d6e8f3", haze_k=0.5, shade=0.1)
    draw_ridge(c, 1250, 430, 12, cam * 0.15, "#f6fbff", "#6f98bb", haze="#c3dcec", haze_k=0.3)
    draw_ground(c, 1280, cam, "#eaf4fa", "#aac8de")
    # mamut y cría en plano medio
    mx = 900 - 14 * u - cam * 0.35
    draw_mammoth(c, mx, 1335, 440, -1, u, speed=0.55)
    draw_mammoth(c, mx + 330, 1350, 250, -1, u + 1.3, speed=0.6, body="#54433f", fur="#715d55")
    # lanza clavada
    t_hit = 4.3
    if u > t_hit:
        tip = (mx + 440 * 0.08, 1335 - 0.78 * 440)
        sp_ang = 0.5 + 0.03 * math.sin((u - t_hit) * 9) * math.exp(-(u - t_hit) * 1.2)
        _spear(c, tip[0], tip[1], -2.4 + sp_ang, 150)
    # primer plano
    gy = 1580
    man_x = 140 + 120 * ease(u / 3.2) * 1.0
    man_x = 160 + 110 * seg(u, 0, 2.0)
    size = 410
    release = 3.5
    if u < 2.0:
        pose = pose_walk(TAU_ * 0.55 * u, amp=0.3, lean=0.12, carry=False)
        pose.update(an1=0.9, an2=1.25, af1=-0.2, af2=0.2)
        prop_a = 0.12
        spear = True
    elif u < 2.9:   # apunta y carga
        k = ease(seg(u, 2.0, 2.9))
        pose = pose_stand(u, lean=0.08 * k)
        pose.update(tn=0.35, cn=0.2, tf=-0.45, cf=-0.5, an1=0.9 - 3.3 * k, an2=1.25 - 3.9 * k, af1=0.9 + 0.6 * k, af2=1.2 + 0.4 * k)
        prop_a = 0.12 + 1.15 * k
        spear = True
    elif u < release:  # lanzamiento
        k = ease(seg(u, 2.9, release))
        pose = pose_stand(u, lean=0.08 - 0.25 * k)
        pose.update(tn=0.35, cn=0.2, tf=-0.45, cf=-0.5, an1=-2.4 + 4.6 * k, an2=-2.7 + 5.1 * k, af1=1.5, af2=1.6)
        prop_a = 1.27 - 0.2 * k
        spear = True
    else:
        k = ease(seg(u, release, release + 0.6))
        pose = pose_stand(u, lean=-0.17 * (1 - k))
        pose.update(tn=0.35, cn=0.2, tf=-0.45, cf=-0.5, an1=2.2 - 1.9 * k, an2=2.6 - 2.1 * k, af1=1.5 - 0.9 * k, af2=1.6 - 1.2 * k)
        prop_a = 0
        spear = False
    mx_, my_, hand, _ = draw_person(c, "man", man_x, gy, size, 1, pose, u, mood=-0.1 if u < 3.6 else 0.5,
                                    prop=("spear" if spear else None), prop_angle=prop_a, wind=0.3)
    draw_breath(c, u, mx_, my_, 1, size=1.2)
    if release <= u <= t_hit:
        # vuelo de la lanza
        hx, hy = _hand_at("man", man_x, gy, size, 1, dict(pose, an1=2.2, an2=2.6), prop="spear", prop_angle=0)
        tx, ty = mx + 440 * 0.08, 1335 - 0.78 * 440
        s = (u - release) / (t_hit - release)
        x = hx + (tx - hx) * s
        y = hy + (ty - hy) * s - 190 * math.sin(math.pi * s)
        dx = (tx - hx)
        dy = (ty - hy) - 190 * math.pi * math.cos(math.pi * s)
        ang = math.atan2(dx, -dy)
        _spear(c, x, y, ang - 0.0, 150, tip_angle=True)
    # mujer raspando la piel + niño
    wx = 850 - cam * 0.1
    hide_pts = [(wx - 330, gy + 38), (wx - 120, gy + 12), (wx + 60, gy + 30), (wx + 20, gy + 78), (wx - 200, gy + 90), (wx - 340, gy + 70)]
    c.drawPath(smooth(hide_pts + [hide_pts[0]]), P("#b49b7e"))
    c.drawPath(smooth(hide_pts + [hide_pts[0]]), S("#8e7659", 5))
    for i in range(7):
        c.drawLine(wx - 300 + i * 52, gy + 50, wx - 280 + i * 52, gy + 72, S("#9d8566", 3, 0.6))
    kneel = pose_kneel(u, lean=0.32)
    sc = math.sin(u * 5.2)
    kneel.update(an1=1.15 + 0.22 * sc, an2=1.65 + 0.2 * sc)
    mx_, my_, _, _ = draw_person(c, "woman", wx, gy + 20, 370, -1, kneel, u, mood=0.35, prop="scraper", prop_angle=0.9 + 0.2 * sc, seed=0.4)
    draw_breath(c, u, mx_, my_, -1, seed=0.9, size=1.2)
    ck = pose_stand(u, arms="rest")
    ck.update(an1=1.2 + 0.1 * math.sin(u * 2), an2=1.5)
    mx_, my_, _, _ = draw_person(c, "child", wx - 310, gy + 78, 370, 1, ck, u, mood=1.0, look=0.1, seed=0.7)
    draw_breath(c, u, mx_, my_, 1, seed=1.7, size=1.0)
    # herramientas de hueso
    for (bx, by, a) in ((wx - 150, gy + 120, 0.3), (wx + 20, gy + 140, -0.5)):
        c.drawLine(bx, by, bx + 46 * math.cos(a), by + 46 * math.sin(a), S("#f1ead6", 9))
        c.drawCircle(bx, by, 7, P("#f1ead6"))
    draw_snow(c, u, seed=4, n=130, fall=60, wind=30, alpha=0.8)
    draw_snow(c, u, seed=6, n=45, fall=110, wind=60, alpha=0.9, size=(4, 8))
    c.restore()


def _spear(c, x, y, ang, length, tip_angle=False):
    """Lanza centrada en (x,y). ang = ángulo del eje: 0 = hacia arriba; positivo = hacia la derecha."""
    dx, dy = math.sin(ang), -math.cos(ang)
    p0 = (x - dx * length * 0.5, y - dy * length * 0.5)
    p1 = (x + dx * length * 0.5, y + dy * length * 0.5)
    c.drawLine(*p0, *p1, S("#5a4030", 5))
    n = (-dy, dx)
    c.drawPath(poly([(p1[0] + dx * 22, p1[1] + dy * 22), (p1[0] + n[0] * 8, p1[1] + n[1] * 8), (p1[0] - n[0] * 8, p1[1] - n[1] * 8)]), P("#b9c9d6"))


# ---------------------------------------------------------------------------
# ESCENA 3 — el fuego
# ---------------------------------------------------------------------------
def scene3(c, u, D):
    z = 1.0 + 0.16 * ease(u / D)
    power = ease(seg(u, 1.6, 4.8))
    ember = 0.25 * seg(u, 1.9, 2.4) * (1 - seg(u, 2.4, 4.8))
    pw = max(power, ember)
    flick = 1 + 0.06 * math.sin(u * 13) + 0.04 * math.sin(u * 7.3)
    c.save()
    camera(c, z, 540, 1500)
    _sky(c, [(0, "#06122b"), (0.5, "#16305b"), (1, "#3d6592")], u, stars=0.9, aurora=0.55, h=1450)
    draw_ridge(c, 1130, 520, 52, 40, "#496f99", "#1c3558", haze="#27456d", haze_k=0.35, shade=0.2)
    draw_ridge(c, 1280, 380, 61, 120, "#3a5e86", "#142b49", shade=0.2)
    draw_ground(c, 1330, 0, "#486f97", "#1d3858")
    fx, fy = 540, 1585
    # ojos de fieras en la oscuridad
    eyes_a = seg(u, 0.6, 1.4) * (1 - seg(u, 5.0, 6.6))
    if eyes_a > 0:
        for (ex, ey, k) in ((90, 1360, 0), (150, 1372, 0.2), (960, 1330, 1), (1000, 1338, 1.3)):
            bl = 0.15 if (u * 0.9 + k) % 1.6 < 0.07 else 1.0
            for dx in (-9, 9):
                c.drawOval(skia.Rect.MakeLTRB(ex + dx - 6, ey - 4 * bl, ex + dx + 6, ey + 4 * bl), P("#ffd23d", eyes_a))
    # suelo iluminado por la hoguera
    c.drawOval(skia.Rect.MakeXYWH(fx - 520 * pw, fy - 60 * pw, 1040 * pw, 190 * pw), rgrad(fx, fy + 30, 520 * max(pw, 0.05), [(0, "#ffb15a", 0.55 * pw), (1, "#ffb15a", 0)], blend=skia.BlendMode.kPlus))
    # personajes
    warm = 0.15 + 0.85 * pw
    lt = (warm, 0.30 * (1 - pw))
    man_pose = pose_kneel(u, lean=0.28)
    if u < 2.4:    # golpea el pedernal
        s = math.sin(u * 14)
        man_pose.update(an1=1.1 + 0.18 * s, an2=1.5 + 0.2 * s, af1=1.0 - 0.18 * s, af2=1.4 - 0.2 * s, head=0.25)
    else:          # sopla sobre las brasas
        man_pose.update(an1=1.2, an2=1.6, af1=1.05, af2=1.5, head=0.45 - 0.2 * seg(u, 4.5, 5.5), lean=0.4 - 0.18 * seg(u, 4.5, 5.5))
    mxp, myp, hn, hf = draw_person(c, "man", 335, 1595, 400, 1, man_pose, u, light=lt, mood=0.2 + 0.8 * seg(u, 4.5, 6), prop=("flint" if u < 2.4 else None), seed=0.2)
    if 1.0 < u < 2.4:
        r = np.random.default_rng(int(u * 14))
        for i in range(3):
            c.drawCircle(hn[0] + r.uniform(-14, 22), hn[1] + r.uniform(-30, 8), r.uniform(2, 4), P("#ffe9a0", 0.9))
    if u >= 2.4 and u < 5.5:
        draw_breath(c, u, mxp, myp, 1, period=1.2, size=0.8)
    stand = pose_stand(u, arms="warm")
    stand["an1"] = 1.35 + 0.05 * math.sin(u * 2)
    mx2, my2, _, _ = draw_person(c, "woman", 840, 1590, 400, -1, stand, u, light=lt, mood=0.15 + 0.85 * pw, seed=0.5)
    cp = pose_stand(u, arms="warm")
    cx_, cy_, _, _ = draw_person(c, "child", 735, 1600, 400, -1, cp, u, light=lt, mood=pw, seed=0.9)
    # manta de piel del niño sobre los hombros
    draw_fire(c, fx, fy, 150 * flick, u, pw, seed=3)
    # luz cálida global (parpadeo)
    c.drawRect(skia.Rect.MakeLTRB(-60, -60, W + 60, H + 60), rgrad(fx, fy - 140, 1100, [(0, "#ff8a2a", 0.32 * pw * flick), (0.5, "#ff7a20", 0.10 * pw), (1, "#ff7a20", 0)], blend=skia.BlendMode.kPlus))
    draw_snow(c, u, seed=7, n=140, fall=50, wind=20, alpha=0.75)
    draw_snow(c, u, seed=8, n=40, fall=90, wind=40, alpha=0.85, size=(4, 8))
    c.restore()


# ---------------------------------------------------------------------------
# ESCENA 4 — refugio en la tormenta
# ---------------------------------------------------------------------------
def scene4(c, u, D):
    cam = 0 + 70 * u * 0.5
    z = 1.0 + 0.28 * ease(u / D)
    c.save()
    camera(c, z, 820, 1450)
    storm = 0.9
    _sky(c, [(0, "#5d7792"), (0.6, "#9eb3c6"), (1, "#c7d6e2")], u, h=1450)
    draw_ridge(c, 1100, 560, 71, cam * 0.07, "#cfe0ee", "#7f9bb5", haze="#bccbd8", haze_k=0.6, shade=0.08)
    draw_ridge(c, 1250, 430, 72, cam * 0.15, "#dcebf6", "#6c8aa8", haze="#b3c5d6", haze_k=0.45)
    draw_glacier(c, 1420, 300, 8, cam * 0.4, light="#c5e4f0", mid="#7fb2cf", dark="#4a7c9e")
    # boca de cueva con brasas dentro
    cvx = 250 - cam * 0.4
    cave = skia.Path()
    cave.moveTo(cvx - 130, 1440)
    cave.cubicTo(cvx - 130, 1280, cvx + 130, 1280, cvx + 130, 1440)
    cave.close()
    c.drawPath(cave, rgrad(cvx, 1420, 150, [(0, "#2b1b16", 1), (1, "#0b1422", 1)]))
    c.drawPath(cave, rgrad(cvx, 1430, 130, [(0, "#ff9a3c", 0.38), (1, "#ff9a3c", 0)]))
    draw_ground(c, 1420, cam, "#d6e5f0", "#9cb9cf")
    gy = 1580
    tent_x = 800
    glow = 0.5 + 0.5 * seg(u, 4.5, 7.5)
    draw_tent(c, tent_x - cam * 0.0, gy - 10, 580, u, glow=glow, wind=storm)
    # grupo llegando
    sp = 150
    xm = -230 + sp * u
    items = [("man", xm, 1595, True), ("child", xm - 120, 1605, False), ("woman", xm - 250, 1590, False)]
    for i, (k, x, g, car) in enumerate(items):
        a = 1 - seg(x, tent_x - 130, tent_x - 40)
        if a <= 0:
            continue
        pose = pose_walk(TAU_ * 0.6 * u + i * 0.6, amp=0.36, lean=0.32, carry=car)
        if k == "woman":
            pose.update(an1=0.9, an2=1.2)
        if k == "child":
            pose.update(af1=1.0, af2=1.2)
        c.saveLayerAlpha(None, int(a * 255))
        mxp, myp, _, _ = draw_person(c, k, x, g, 360, 1, pose, u, mood=-0.4, prop=("bundle" if car else None), wind=2.0, seed=i * 0.4)
        draw_breath(c, u, mxp, myp, 1, period=1.6, seed=i * 0.5, size=1.2)
        c.restore()
    # fogonazo de nieve y ráfagas
    draw_snow(c, u, seed=9, n=260, fall=170, wind=520, alpha=0.9, size=(2, 6), sway=8)
    draw_snow(c, u, seed=10, n=70, fall=260, wind=780, alpha=0.95, size=(5, 11), sway=14)
    draw_streaks(c, u, n=60, alpha=0.38, speed=1500, length=(180, 520), slope=0.05)
    c.drawRect(skia.Rect.MakeLTRB(-60, 700, W + 60, 1700), _band(700, 1700, "#dbe8f2", 0.22 + 0.1 * math.sin(u * 0.8)))
    c.restore()


# ---------------------------------------------------------------------------
# ESCENA 5 — comunidad junto a la hoguera (cueva)
# ---------------------------------------------------------------------------
def _cave_wall(c, u, cam, pw):
    c.drawRect(skia.Rect.MakeLTRB(-60, -300, W + 60, H + 60), vgrad(0, H, [(0, "#1a1f33"), (0.45, "#3a3340"), (1, "#2a2026")]))
    r = np.random.default_rng(77)
    for i in range(46):  # bloques de roca
        x = r.uniform(-100, W + 100) - cam * 0.9
        y = r.uniform(40, 1450)
        w, h = r.uniform(80, 260), r.uniform(50, 150)
        shade = r.uniform(-0.06, 0.12)
        c.drawPath(poly([(x, y), (x + w, y + r.uniform(-18, 18)), (x + w * 0.9, y + h), (x + w * 0.1, y + h * 0.9)]), P(mix("#3e3947", "#ffffff" if shade > 0 else "#000000", abs(shade)), 0.55))
    # ventana de la cueva (noche nevada)
    ox = 770 - cam * 0.9
    mouth = poly([(ox - 130, 70), (ox + 190, 40), (ox + 250, 260), (ox + 160, 520), (ox - 40, 560), (ox - 170, 330)])
    c.save()
    c.clipPath(mouth, skia.ClipOp.kIntersect, True)
    c.drawRect(skia.Rect.MakeLTRB(ox - 300, 0, ox + 400, 700), vgrad(0, 600, [(0, "#0e2146"), (1, "#3d6592")]))
    draw_snow(c, u, seed=21, n=60, fall=70, wind=30, alpha=0.8, size=(2, 6))
    c.restore()
    c.drawPath(mouth, S("#22202c", 10))
    # pinturas rupestres (ocre) — flamean con el fuego
    fl = 0.8 + 0.2 * math.sin(u * 9) + 0.1 * math.sin(u * 5.1)
    px = 380 - cam * 0.9
    alpha = 0.55 + 0.4 * pw * fl
    draw_mammoth(c, px, 1060, 400, 1, u * 0.0, body="#b04a25", body_f="#8c3a1d", fur="#d9763a", tusk="#f0d9a8", speed=0)
    c.drawRect(skia.Rect.MakeLTRB(px - 330, 560, px + 330, 1100), P("#2a2026", 0.0))
    for i, hx in enumerate((px - 250, px - 130, px + 20, px + 150, px + 270)):   # cazadores con lanzas
        yy = 1190
        c.drawLine(hx, yy - 80, hx, yy, S("#c9622e", 6, alpha))
        c.drawCircle(hx, yy - 94, 9, P("#c9622e", alpha))
        c.drawLine(hx, yy - 62, hx - 30, yy - 30, S("#c9622e", 5, alpha))
        c.drawLine(hx, yy - 62, hx + 34, yy - 110, S("#c9622e", 5, alpha))
        c.drawLine(hx + 34, yy - 150, hx + 34, yy - 60, S("#c9622e", 3, alpha))
    for (hx, hy) in ((px + 360, 760), (px + 430, 820), (px + 480, 740), (px + 520, 830)):   # manos impresas
        c.drawCircle(hx, hy, 36, P("#b04a25", alpha))
        for a in (-0.6, -0.3, 0, 0.3, 0.6):
            c.drawLine(hx, hy, hx + 64 * math.sin(a), hy - 64 * math.cos(a), S("#b04a25", 11, alpha))
    # suelo de cueva con pieles
    c.drawRect(skia.Rect.MakeLTRB(-60, 1440, W + 60, H + 60), vgrad(1440, H, [(0, "#4b4048"), (1, "#2a2128")]))
    c.drawPath(smooth([(-60, 1450), (300, 1470), (700, 1455), (1140, 1475)]), S("#6b5d63", 6, 0.6))
    for (rx, rw, col) in ((250, 330, "#7b6247"), (880, 300, "#5d6d7e")):
        c.drawOval(skia.Rect.MakeXYWH(rx - rw / 2 - cam * 0.9, 1560, rw, 90), P(col, 0.95))
        c.drawOval(skia.Rect.MakeXYWH(rx - rw / 2 - cam * 0.9, 1560, rw, 90), S("#3a2e24", 4, 0.5))


def scene5(c, u, D):
    cam = 35 * (u / D)
    z = 1.0 + 0.08 * ease(u / D)
    c.save()
    camera(c, z, 560, 1350)
    pw = 1.0
    flick = 1 + 0.05 * math.sin(u * 13) + 0.04 * math.sin(u * 7.3)
    _cave_wall(c, u, cam, pw)
    fx, fy = 600 - cam, 1590
    # anillo de piedras y fuego
    for i in range(9):
        a = i / 9 * math.pi
        c.drawOval(skia.Rect.MakeXYWH(fx + math.cos(a) * 130 - 20, fy + 28 + math.sin(a) * 6 - 14 * (0 if i % 2 else 1), 40, 24), P("#5a5560"))
    lt = (0.85, 0.12)
    # hombre señalando las pinturas
    man = pose_stand(u, arms="rest")
    pointing = seg(u, 6.4, 7.4)
    man.update(an1=0.1 + (2.45 - 0.1) * ease(pointing) + 0.05 * math.sin(u * 2), an2=0.3 + (2.6 - 0.3) * ease(pointing), head=-0.25 * pointing)
    mxp, myp, _, _ = draw_person(c, "man", 250 - cam, 1600, 390, 1, man, u, light=lt, mood=0.6, look=0.0, seed=0.1)
    # niño sentado
    child = pose_sit(u)
    eat = seg(u, 5.6, 6.6)
    wait = 1 - seg(u, 3.0, 4.2)
    child.update(an1=0.55 + 0.9 * seg(u, 3.4, 4.8) * (1 - eat) + 1.5 * eat, an2=1.2 + 0.4 * seg(u, 3.4, 4.8) * (1 - eat) + 1.65 * eat, head=-0.1 + 0.05 * math.sin(u * 3))
    meat_prop = ("stick_meat" if eat > 0.5 else None)
    c_ang = 0.45
    draw_person(c, "child", 480 - cam, 1610, 390, 1, child, u, light=lt, mood=0.5 + 0.5 * seg(u, 5, 7), prop=meat_prop, prop_angle=c_ang, seed=0.7)
    # mujer sentada ofreciendo carne
    wom = pose_sit(u)
    give = ease(seg(u, 2.8, 4.8)) * (1 - seg(u, 6.4, 7.4))
    wom.update(an1=0.8 + 0.75 * give, an2=1.1 + 0.5 * give)
    draw_person(c, "woman", 850 - cam, 1605, 390, -1, wom, u, light=lt, mood=0.8, prop="stick_meat", prop_angle=1.2, seed=0.5)
    draw_fire(c, fx, fy, 160 * flick, u, 1.0, seed=5)
    c.drawRect(skia.Rect.MakeLTRB(-60, -60, W + 60, H + 60), rgrad(fx, fy - 120, 1000, [(0, "#ff8a2a", 0.30 * flick), (0.55, "#ff7a20", 0.08), (1, "#ff7a20", 0)], blend=skia.BlendMode.kPlus))
    for k in range(6):   # polvo flotando
        r = np.random.default_rng(k)
        px = (r.random() * W + 12 * u) % W
        py = (r.random() * H * 0.8 - 30 * u * (0.4 + r.random())) % (H * 0.9)
        c.drawCircle(px, py, 2.0, P("#ffd9a8", 0.35))
    c.restore()


# ---------------------------------------------------------------------------
# ESCENA 6 — amanecer
# ---------------------------------------------------------------------------
def scene6(c, u, D):
    k = ease(u / D * 1.15)
    z = 1.32 - 0.27 * ease(u / D)
    dy = 130 * (1 - ease(u / D))
    c.save()
    camera(c, z, 540, 1350, dy=dy)
    s1 = [mix("#0f2250", "#3d77ad", k), mix("#3d5d96", "#9fc9e0", k), mix("#e8967a", "#ffe1b0", k)]
    _sky(c, [(0, s1[0]), (0.55, s1[1]), (1, s1[2])], u, stars=0.7 * (1 - k), aurora=0.4 * (1 - k), h=1450)
    sx, sy = 770, 1230 - 250 * ease(u / D)
    c.drawCircle(sx, sy, 700, rgrad(sx, sy, 700, [(0, "#fff0c4", 0.75 * (0.4 + 0.6 * k)), (0.35, "#ffc98a", 0.28), (1, "#ffc98a", 0)], blend=skia.BlendMode.kPlus))
    for i in range(9):   # rayos
        a = -math.pi / 2 + (i - 4) * 0.2 + math.sin(u * 0.3 + i) * 0.02
        c.drawPath(poly([(sx, sy), (sx + math.cos(a - 0.05) * 1700, sy + math.sin(a - 0.05) * 1700), (sx + math.cos(a + 0.05) * 1700, sy + math.sin(a + 0.05) * 1700)]),
                   P("#fff3cf", 0.06 * k))
    c.drawCircle(sx, sy, 78, P("#fff7dc"))
    draw_ridge(c, 1180, 560, 91, 30 + u * 6, mix("#f6dcc2", "#ffffff", k * 0.5), "#6d86b0", haze=mix("#e5a58c", "#d7ecf6", k), haze_k=0.45, shade=0.1)
    draw_ridge(c, 1300, 430, 92, 80 + u * 10, "#f7e8e0", "#4f6fa0", haze="#bcd2e6", haze_k=0.2, shade=0.14)
    draw_ground(c, 1330, 0, mix("#eec9b4", "#f4f1ef", k), mix("#6c86b2", "#a8c3dc", k))
    # colina
    hill = [(-80, 1720), (140, 1600), (360, 1520), (540, 1498), (740, 1530), (940, 1610), (1160, 1730)]
    hp = smooth(hill)
    hp.lineTo(1160, 2000)
    hp.lineTo(-80, 2000)
    hp.close()
    c.drawPath(hp, vgrad(1490, 1800, [(0, mix("#ffe7cf", "#f6faff", k)), (1, "#8aa6c6")]))
    c.drawPath(smooth(hill), S("#fff4dd", 5, 0.8))
    # brote verde: el deshielo
    sp_k = ease(seg(u, 4.0, 8.0))
    spx, spy = 700, 1530
    if sp_k > 0:
        c.drawPath(smooth([(spx, spy), (spx + 2, spy - 30 * sp_k), (spx - 2, spy - 62 * sp_k)]), S("#69c47e", 5))
        for sgn in (-1, 1):
            c.drawPath(poly([(spx, spy - 40 * sp_k), (spx + sgn * 34 * sp_k, spy - 54 * sp_k), (spx + sgn * 6 * sp_k, spy - 26 * sp_k)]), P("#7bd68e"))
    lt = (0.35 * k + 0.1, 0.18 * (1 - k))
    gy = 1500
    wom = pose_stand(u, arms="rest")
    wom.update(an1=0.15, an2=0.4)
    mw, mmw, _, _ = draw_person(c, "woman", 380, gy + 5, 360, 1, wom, u, light=lt, mood=0.8 * k + 0.2, look=-0.12, seed=0.3)
    man = pose_stand(u, arms="rest")
    man.update(an1=0.15 + 2.0 * ease(seg(u, 2.0, 3.4)), an2=0.4 + 2.2 * ease(seg(u, 2.0, 3.4)))
    mm, mmm, _, _ = draw_person(c, "man", 500, gy, 370, 1, man, u, light=lt, mood=0.8 * k + 0.2, look=-0.15, seed=0.1)
    ch = pose_stand(u, arms="rest")
    ch.update(an1=1.1, an2=1.4)
    mc, mmc, _, _ = draw_person(c, "child", 625, gy + 14, 370, 1, ch, u, light=lt, mood=1.0, look=-0.2, seed=0.8)
    for (mx_, my_, sd) in ((mw, mmw, 0.2), (mm, mmm, 0.9), (mc, mmc, 1.6)):
        draw_breath(c, u, mx_, my_, 1, seed=sd, size=1.1)
    # aves
    for i in range(5):
        bu = u - 3.0 - i * 0.5
        if bu < 0:
            continue
        bx = -60 + bu * 190
        by = 520 + i * 70 - bu * 18 + 18 * math.sin(bu * 1.3 + i)
        wing = math.sin(bu * 9 + i) * 22
        c.drawPath(smooth([(bx - 34, by - wing), (bx, by), (bx + 34, by - wing)]), S("#3a4b6e", 4))
    draw_snow(c, u, seed=12, n=90 - int(60 * k), fall=40, wind=15, alpha=0.7)
    c.restore()


SCENES = [scene1, scene2, scene3, scene4, scene5, scene6]


# ---------------------------------------------------------------------------
# Compositor
# ---------------------------------------------------------------------------
class Renderer:
    def __init__(self, starts, ends, srt_cues, title, end_card, font_path: Path):
        self.starts, self.ends = starts, ends
        self.cues = srt_cues
        self.title, self.end_card = title, end_card
        self.tf_sub = skia.Font(skia.Typeface.MakeFromFile(str(font_path)), 60)
        self.tf_title = skia.Font(skia.Typeface.MakeFromFile(str(font_path)), 70)
        self.tf_end = skia.Font(skia.Typeface.MakeFromFile(str(font_path)), 78)
        self.surface = skia.Surface(W, H)
        self.total = ends[-1]

    def scene_at(self, t):
        for i in range(len(self.starts)):
            if t < self.ends[i] or i == len(self.starts) - 1:
                return i
        return len(self.starts) - 1

    def _text_center(self, c, text, font, y, paint_fill, outline=None, max_w=960):
        w = font.measureText(text)
        c.save()
        if w > max_w:
            sc = max_w / w
            c.translate(W / 2, y)
            c.scale(sc, sc)
            c.translate(-W / 2, -y)
        x = (W - w) / 2
        if outline:
            c.drawString(text, x, y, font, outline)
        c.drawString(text, x, y, font, paint_fill)
        c.restore()

    def _wrap(self, text, font, max_w):
        words, lines, cur = text.split(), [], ""
        for w in words:
            cand = (cur + " " + w).strip()
            if cur and font.measureText(cand) > max_w:
                lines.append(cur)
                cur = w
            else:
                cur = cand
        lines.append(cur)
        return lines

    def frame(self, t: float) -> np.ndarray:
        c = self.surface.getCanvas()
        i = self.scene_at(t)
        u = t - self.starts[i]
        D = self.ends[i] - self.starts[i]
        c.save()
        c.clipRect(skia.Rect.MakeWH(W, H))
        SCENES[i](c, u, D)
        c.restore()
        # grading frío suave + viñeta
        if i not in (2, 4):
            c.drawRect(skia.Rect.MakeWH(W, H), P("#2a5fa8", 0.05))
        vignette(c, 0.42 if i not in (2, 4) else 0.55)
        # título (escena 1)
        if i == 0:
            a = seg(u, 0.4, 1.3) * (1 - seg(u, 5.2, 6.2))
            if a > 0:
                lines = self._wrap(self.title, self.tf_title, 900)
                y0 = 330 - 40 * (len(lines) - 2)
                c.drawRect(skia.Rect.MakeLTRB(0, y0 - 100, W, y0 + 90 * len(lines) - 40), vgrad(y0 - 100, y0 + 90 * len(lines), [(0, "#04122b"), (1, "#04122b")], 0.0) if False else P("#04122b", 0.35 * a))
                for k, ln in enumerate(lines):
                    self._text_center(c, ln, self.tf_title, y0 + k * 92, P("#ffffff", a),
                                      skia.Paint(AntiAlias=True, Color=C("#000000", 0.6 * a), Style=skia.Paint.kStroke_Style, StrokeWidth=9, StrokeJoin=skia.Paint.kRound_Join))
        if i == len(self.starts) - 1:
            a = seg(u, 6.4, 7.8) * (1 - seg(t, self.total - 1.0, self.total - 0.2))
            if a > 0:
                lines = self._wrap(self.end_card, self.tf_end, 900)
                for k, ln in enumerate(lines):
                    self._text_center(c, ln, self.tf_end, 420 + k * 96, P("#ffffff", a),
                                      skia.Paint(AntiAlias=True, Color=C("#10243f", 0.55 * a), Style=skia.Paint.kStroke_Style, StrokeWidth=9, StrokeJoin=skia.Paint.kRound_Join))
        # subtítulo: UNA sola línea
        for (s, e, lines) in self.cues:
            if s <= t < e:
                text = " ".join(lines)
                a = min(1.0, (t - s) / 0.08, (e - t) / 0.08)
                w = self.tf_sub.measureText(text)
                bx0, bx1 = (W - w) / 2 - 34, (W + w) / 2 + 34
                c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(bx0, 1712, bx1, 1712 + 96), 28, 28), P("#06142c", 0.52 * a))
                self._text_center(c, text, self.tf_sub, 1780, P("#ffffff", a),
                                  skia.Paint(AntiAlias=True, Color=C("#000000", 0.85 * a), Style=skia.Paint.kStroke_Style, StrokeWidth=6, StrokeJoin=skia.Paint.kRound_Join), max_w=960)
                break
        # fundidos entre escenas (a azul noche)
        fade = 0.0
        if i > 0:
            fade = max(fade, 1 - seg(u, 0, 0.45))
        else:
            fade = max(fade, 1 - seg(u, 0, 0.8))
        if i < len(self.starts) - 1:
            fade = max(fade, seg(u, D - 0.45, D))
        else:
            fade = max(fade, seg(t, self.total - 1.0, self.total))
        if fade > 0:
            c.drawRect(skia.Rect.MakeWH(W, H), P("#040c1c", fade))
        img = self.surface.makeImageSnapshot()
        return img.toarray(colorType=skia.kBGRA_8888_ColorType)
