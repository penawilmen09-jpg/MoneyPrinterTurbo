"""Las 12 escenas del documental. Cada escena es una funcion pura s<n>(t) -> imagen RGB."""
import functools
import math
import random

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

from engine import *  # noqa: F401,F403
from engine import (PAL, W, H, TAU, add_glow, clamp, draw_back, draw_front, draw_ptero, draw_sky, draw_tree, glow_sprite,
                    lerp, mix, multiply_color, prog, put_actor, put_clouds, put_haze, put_puff, rock_sprite, sky_img,
                    sm, vgrad)


def new_ov():
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))


def flush(img, ov):
    img.paste(ov, (0, 0), ov)


def sun(img, x, y, r, disc=(255, 246, 214), glow=(255, 200, 120), k=1.0):
    add_glow(img, x, y, r * 7, tuple(int(c * .55) for c in glow), 2.2, k)
    add_glow(img, x, y, r * 3, glow, 1.8, k)
    ImageDraw.Draw(img).ellipse((x - r, y - r, x + r, y + r), fill=disc)


def flash(img, a, col=(255, 255, 255)):
    if a > 0.01:
        img.paste(Image.blend(img, Image.new("RGB", img.size, col), clamp(a)))


def hz(pal, k=1.0):
    P = PAL[pal]
    return (P["haze"][0], P["haze"][1], P["haze"][2], P["hz"] * k)


def particles(ov, t, n, seed, color, speed, drift, size=(2, 5), alpha=200, loop=True):
    rnd = random.Random(seed)
    d = ImageDraw.Draw(ov)
    for _ in range(n):
        x0, y0 = rnd.uniform(0, W), rnd.uniform(0, H)
        sp = rnd.uniform(.6, 1.4)
        r = rnd.uniform(*size)
        x = (x0 + drift * t * sp) % W
        y = (y0 + speed * t * sp) % H
        d.ellipse((x - r, y - r, x + r, y + r), fill=color + (int(alpha * rnd.uniform(.5, 1)),))


def pteros(img, t, specs, col=(36, 30, 44, 235)):
    ov = new_ov()
    d = ImageDraw.Draw(ov)
    for (x0, y0, vx, vy, s, ph) in specs:
        x = x0 + vx * t
        y = y0 + vy * t + 14 * math.sin(t * 2 + ph)
        draw_ptero(d, x, y, s, t + ph, col, flip=vx < 0)
    flush(img, ov)


# =========================================================== ESCENA 1
def s1(t):
    cam = 170 * t / 5
    P = PAL["gold"]
    img = draw_sky(P["sky"])
    sun(img, 760 - cam * .05, 640, 95)
    put_clouds(img, 1, (255, 236, 206), 380, cam * .2 + t * 16)
    put_clouds(img, 2, (255, 226, 190), 660, cam * .1 + t * 9)
    pteros(img, t, [(1250, 330, -250, 0, .75, 0), (1400, 410, -260, 0, .6, 1.2), (1520, 300, -240, 0, .55, 2.1),
                    (-120, 560, 150, 0, .45, 3)])
    # humo del volcan
    vx = 900 - cam * .12 - 0
    for i in range(10):
        a = (t * .22 + i / 10) % 1
        put_puff(img, vx + a * 120 + 10 * math.sin(a * 6 + i), 568 - a * 430, 36 + a * 110, (150, 126, 116), .55 * (1 - a) ** 1.2)
    draw_back(img, cam, "gold")
    acts = [("brachio", 60 + 20 * t, 1262, .3, 0, .0), ("brachio", 330 + 20 * t, 1268, .26, 0, .3), ("brachio", 620 + 18 * t, 1262, .28, 0, .6),
            ("trex", 900 - 22 * t, 1292, .34, 1, .1),
            ("tric", 560 - 34 * t, 1340, .5, 1, .2), ("tric", 940 - 30 * t, 1352, .48, 1, .6),
            ("brachio", 360 + 26 * t, 1400, .64, 0, .5)]
    for kind, x, y, sc, fl, ph in sorted(acts, key=lambda a: a[2]):
        sp = .62 if y < 1330 else .85
        put_actor(img, kind, x - cam * sp, y, sc, t, flip=bool(fl), ph0=ph, cyc=1.5, hz=hz("gold", 1.0 if y < 1300 else .45 if y < 1360 else .1))
    draw_front(img, cam, "gold")
    return img


# =========================================================== ESCENA 2
def s2(t):
    cam = 230 * t / 5
    P = PAL["day"]
    img = draw_sky(P["sky"])
    sun(img, 280 - cam * .04, 330, 70, (255, 252, 226), (255, 244, 200), .9)
    put_clouds(img, 3, (255, 255, 255), 300, cam * .2 + t * 12)
    put_clouds(img, 4, (240, 248, 255), 620, cam * .1 + t * 7)
    pteros(img, t, [(1300, 380, -200, 0, .5, 0.4), (-140, 470, 170, 0, .42, 2.2)], (40, 52, 62, 220))
    draw_back(img, cam, "day")
    acts = [("brachio", 140 + 22 * t, 1292, .42, 0, .1), ("brachio", 520 + 24 * t, 1300, .5, 0, .5),
            ("trex", 880 - 28 * t, 1322, .52, 1, .2),
            ("raptor", -60 + 150 * t, 1368, .4, 0, .0), ("raptor", -190 + 150 * t, 1385, .36, 0, .4), ("raptor", -300 + 148 * t, 1372, .38, 0, .7),
            ("tric", 130 + 70 * t, 1452, .92, 0, .2), ("tric", -250 + 68 * t, 1472, .84, 0, .6)]
    for kind, x, y, sc, fl, ph in sorted(acts, key=lambda a: a[3] if a[2] > 1400 else -a[2]):
        sp = .85
        cy = .62 if kind == "raptor" else 1.4
        put_actor(img, kind, x - cam * sp, y, sc, t, flip=bool(fl), ph0=ph, cyc=cy, hz=hz("day", .5 if y < 1340 else .0))
    draw_front(img, cam, "day")
    return img


# =========================================================== ESCENA 3
def roar_curve(t):
    r = sm(prog(t, .5, 1.3)) * (1 - sm(prog(t, 3.9, 4.7)))
    if 1.3 < t < 3.9:
        r = clamp(.9 + .1 * math.sin(t * 22))
    return r


def s3(t):
    cam = 40 * t / 5
    img = draw_sky(PAL["gold"]["sky"])
    sun(img, 240, 600, 120, (255, 248, 220), (255, 190, 110), 1.15)
    put_clouds(img, 1, (255, 226, 190), 330, cam * .2 + t * 10)
    draw_back(img, cam, "gold")
    # aves que huyen del bosque tras el rugido
    if t > 1.0:
        tt = t - 1.0
        specs = [(760 + i * 55, 1090 - i * 15, -(150 + i * 55), -(190 + i * 45), .5 + .05 * i, i) for i in range(6)]
        ov = new_ov()
        d = ImageDraw.Draw(ov)
        for (x0, y0, vx, vy, s, ph) in specs:
            draw_ptero(d, x0 + vx * tt, y0 + vy * tt, s, t + ph, (30, 24, 34, 235), flip=True)
        flush(img, ov)
    ro = roar_curve(t)
    X0, FY, SC = 650, 1490, 2.55
    spr, ax, ay = put_actor(img, "trex", X0, FY, SC, t, flip=True, idle=True, a=ro, hz=(255, 200, 130, .08))
    # ondas sonoras desde la boca
    tilt = -ro * .32
    pv = (92, -172)
    mx, my = rot([(196, -160)], pv, tilt)[0]
    mx_s, my_s = X0 - mx * SC, FY + my * SC
    if 1.0 < t < 4.4:
        ov = new_ov()
        d = ImageDraw.Draw(ov)
        for j in range(4):
            age = ((t - 1.0) * 1.7 - j * .25) % 1.0
            rr = 40 + age * 420
            al = int(200 * (1 - age) ** 1.5)
            d.arc((mx_s - rr, my_s - rr, mx_s + rr, my_s + rr), 145, 215, fill=(255, 244, 214, al), width=7)
        flush(img, ov)
    draw_front(img, cam, "gold")
    ov = new_ov()
    particles(ov, t, 60, 5, (255, 236, 190), -30, -160, (1.5, 3.5), 150)
    flush(img, ov)
    return img


def rot(pts, piv, a):
    c, s = math.cos(a), math.sin(a)
    return [(piv[0] + (x - piv[0]) * c - (y - piv[1]) * s, piv[1] + (x - piv[0]) * s + (y - piv[1]) * c) for x, y in pts]


# =========================================================== ESCENA 4
def s4(t):
    cam = 120 * t / 5
    d_ = prog(t, 0, 5)
    P = PAL["gold"]
    img = draw_sky(P["sky"])
    sun(img, 700 - cam * .05, 650, 90, (255, 214, 160), (255, 150, 90), 1 - .35 * d_)
    put_clouds(img, 1, (255, 200, 170), 380, cam * .2 + t * 16)
    put_clouds(img, 2, (230, 170, 160), 640, cam * .1 + t * 9)
    # estela del asteroide lejano
    ax, ay = 300 + 40 * t, 260 + 52 * t
    add_glow(img, ax, ay, 70, (255, 190, 120), 1.6, .4 + .5 * d_)
    ImageDraw.Draw(img).ellipse((ax - 4, ay - 4, ax + 4, ay + 4), fill=(255, 250, 230))
    ov = new_ov()
    dd = ImageDraw.Draw(ov)
    for i in range(14):
        dd.ellipse((ax - 3 - i * 5, ay - 3 - i * 8, ax + 3 - i * 5, ay + 3 - i * 8), fill=(255, 200, 140, int(180 * (1 - i / 14))))
    flush(img, ov)
    pteros(img, t, [(1300, 330, -330, -20, .6, 0), (1450, 450, -350, -30, .5, 1.1), (1600, 280, -300, 0, .48, 2)], (50, 30, 44, 230))
    draw_back(img, cam, "gold")
    acts = [("brachio", 200, 1275, .34, 0, 1.0, "b"), ("brachio", 640, 1282, .3, 1, 1.0, "b"),
            ("tric", 420, 1345, .56, 0, 1.0, "t"), ("tric", 800, 1355, .6, 1, 1.0, "t"),
            ("brachio", 520, 1420, .72, 0, 1.0, "b"), ("trex", 880, 1332, .42, 1, .0, "r")]
    for kind, x, y, sc, fl, look, _ in sorted(acts, key=lambda a: a[2]):
        sp = .62 if y < 1330 else .85
        put_actor(img, kind, x - cam * sp, y, sc, t, flip=bool(fl), idle=True, a=look * sm(prog(t, .3, 1.6)),
                  hz=hz("gold", 1.0 if y < 1300 else .45 if y < 1360 else .1))
    draw_front(img, cam, "gold")
    img = multiply_color(img, (150, 112, 150), sm(d_))
    add_glow(img, 540, 1250, 900, (90, 24, 8), 2.0, .4 * d_)
    return img


# =========================================================== ESCENA 5 (espacio)
@functools.lru_cache(maxsize=1)
def earth_img():
    Rr = 1150
    S = 1210
    ww, hh = 2420, 1360
    yy, xx = np.mgrid[0:hh, 0:ww].astype(np.float32)
    nx, ny = (xx - S) / Rr, (yy - S) / Rr
    r = np.sqrt(nx * nx + ny * ny)
    nz = np.sqrt(np.clip(1 - r * r, 0, 1))
    L = np.array([-.35, -.6, .7], np.float32)
    L /= np.linalg.norm(L)
    lam = np.clip(nx * L[0] + ny * L[1] + nz * L[2], 0, 1)
    u, v = nx * 3.2 + .7, ny * 3.2
    f = np.sin(2.1 * u + .5) * np.cos(1.7 * v + 1.2) + .6 * np.sin(3.7 * u + v * 2.1) + .4 * np.sin(5.3 * v - u * 1.3) + .25 * np.sin(11 * u + 3 * v)
    land = f > .55
    ocean = np.stack([20 + 20 * lam, 70 + 60 * lam, 140 + 80 * lam], -1)
    green = np.stack([60 + 60 * lam, 110 + 60 * lam, 50 + 30 * lam], -1)
    base = np.where(land[..., None], green, ocean)
    cl = (np.sin(7 * u + 2 * np.sin(3 * v)) + np.sin(5 * v + u * 3.1) + .5 * np.sin(13 * u - 7 * v)) > 1.7
    base = np.where(cl[..., None], base * .45 + (235 * lam[..., None] ** .6 + 14) * .55, base)
    base *= (.15 + .85 * lam)[..., None] ** .8 * 1.1
    rim = np.clip((r - .86) / .14, 0, 1) ** 2.2
    base += rim[..., None] * np.array([70, 130, 230], np.float32) * (.4 + .6 * lam[..., None])
    alpha = np.where(r <= 1, 255, 0).astype(np.float32)
    halo = np.clip(1 - (r - 1) / .07, 0, 1) ** 2
    halo_mask = (r > 1) & (r < 1.07)
    out_rgb = np.where(halo_mask[..., None], np.array([90, 160, 255], np.float32), base)
    alpha = np.where(halo_mask, 190 * halo, alpha)
    rgba = np.concatenate([np.clip(out_rgb, 0, 255), alpha[..., None]], -1).astype(np.uint8)
    return Image.fromarray(rgba, "RGBA")


@functools.lru_cache(maxsize=1)
def starfield():
    rnd = random.Random(9)
    return [(rnd.uniform(0, W), rnd.uniform(0, 1500), rnd.uniform(.8, 2.6), rnd.uniform(0, TAU), rnd.uniform(.4, 1)) for _ in range(380)]


def s5(t):
    img = vgrad(W, H, [(0, (2, 3, 10)), (.6, (6, 10, 28)), (1, (10, 22, 54))])
    ov = new_ov()
    d = ImageDraw.Draw(ov)
    for (x, y, r, ph, b) in starfield():
        al = int(255 * b * (.7 + .3 * math.sin(t * 2.5 + ph)))
        yy = (y + t * 5) % 1500
        d.ellipse((x - r, yy - r, x + r, yy + r), fill=(235, 240, 255, al))
    flush(img, ov)
    e = earth_img()
    img.paste(e, (int((W - e.width) / 2), int(1090 - t * 6)), e)
    p = prog(t, -.1, 5.1)
    path = p ** 1.5
    sx, sy, ex, ey = 150, 180, 600, 1000
    x, y = lerp(sx, ex, path), lerp(sy, ey, path)
    R = 34 + 300 * p ** 1.9
    ux, uy = sx - ex, sy - ey
    L = math.hypot(ux, uy)
    ux, uy = ux / L, uy / L
    heat = sm(prog(t, 2.8, 5.0))
    n = 26
    for i in range(n, 0, -1):
        f = i / n
        add_glow(img, x + ux * f * R * 7, y + uy * f * R * 7, R * (1.05 - .5 * f), (255, 130 + int(80 * (1 - f)), 40), 1.5, (.12 + .5 * heat) * (1 - f))
    add_glow(img, x, y, R * 2.6, (255, 150, 70), 1.8, .12 + .7 * heat)
    rk = rock_sprite(512).resize((int(2 * R * 1.0), int(2 * R * 1.0)), Image.LANCZOS).rotate(-t * 16, resample=Image.BICUBIC)
    img.paste(rk, (int(x - rk.width / 2), int(y - rk.height / 2)), rk)
    add_glow(img, x - ux * R * .6, y - uy * R * .6, R * 1.1, (255, 120, 40), 1.4, .25 + .55 * heat)
    return img


# =========================================================== ESCENA 6 (impacto)
@functools.lru_cache(maxsize=1)
def coast_bg():
    """Mar + costa (RGBA) con horizonte en y=1150."""
    hy = 1150
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sea = vgrad(W, H - hy, [(0, (84, 156, 170)), (.25, (44, 120, 150)), (1, (14, 54, 88))])
    im.paste(sea, (0, hy))
    d = ImageDraw.Draw(im)
    rnd = random.Random(4)
    for _ in range(140):
        y = hy + 8 + (rnd.random() ** 1.7) * (H - hy - 20)
        x = rnd.uniform(-80, W)
        ln = 20 + (y - hy) * .35
        d.line([(x, y), (x + ln, y)], fill=(210, 240, 240, int(70 + 90 * (1 - (y - hy) / (H - hy)))), width=int(2 + (y - hy) / 160))
    # montanas lejanas y costa
    pts = [(0, hy)]
    for x in range(0, W + 40, 20):
        pts.append((x, hy - 26 - 18 * math.sin(x / 130 + 1) - 10 * math.sin(x / 47)))
    pts += [(W, hy), (0, hy)]
    d.polygon(pts, fill=(86, 116, 130, 255))
    land = [(560, hy + 2)]
    for x in range(560, W + 60, 20):
        land.append((x, hy - 14 - 28 * (x - 560) / 520 - 8 * math.sin(x / 40)))
    land += [(W + 60, hy + 160), (900, hy + 120), (700, hy + 60), (580, hy + 14)]
    d.polygon(land, fill=(70, 120, 82, 255))
    sand = [(540, hy + 6), (700, hy + 62), (900, hy + 122), (W + 60, hy + 170), (W + 60, hy + 140), (900, hy + 96), (700, hy + 44), (560, hy + 4)]
    d.polygon(sand, fill=(222, 204, 150, 255))
    for i in range(9):
        x = 640 + i * 55 + rnd.uniform(-10, 10)
        yy = hy - 14 - 28 * (x - 560) / 520 + 4
        draw_tree(d, "palm", x, yy, rnd.uniform(70, 120), (40, 86, 56), rnd)
    return im


@functools.lru_cache(maxsize=1)
def map_inset():
    S = 360
    big = Image.new("RGBA", (S * 2, S * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    k = S * 2 / 100
    mask = Image.new("L", (S * 2, S * 2), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, S * 2 - 1, S * 2 - 1), fill=255)
    sea = Image.new("RGB", (S * 2, S * 2), (28, 78, 128))
    dd = ImageDraw.Draw(sea)

    def poly(pts, col):
        dd.polygon([(x * k, y * k) for x, y in pts], fill=col)
    poly([(0, 42), (12, 48), (24, 58), (33, 62), (36, 46), (44, 28), (53, 21), (64, 19), (70, 23), (69, 40), (66, 56), (70, 66),
          (80, 72), (100, 76), (100, 100), (0, 100)], (214, 190, 132))
    poly([(74, 6), (90, 4), (98, 10), (94, 14), (80, 12)], (214, 190, 132))
    sea.putalpha(mask)
    big.paste(sea, (0, 0), sea)
    d = ImageDraw.Draw(big)
    d.ellipse((6, 6, S * 2 - 7, S * 2 - 7), outline=(255, 255, 255, 255), width=14)
    return big.resize((S, S), Image.LANCZOS)


def s6(t):
    ti = 3.0
    imp = (540, 1138)
    post = max(0.0, t - ti)
    pre = t < ti
    a = sm(prog(t, ti, ti + .5))
    sky = Image.blend(sky_img(((0, (60, 120, 186)), (.45, (150, 196, 214)), (.7, (252, 214, 160)), (1, (255, 236, 190)))),
                      sky_img(((0, (60, 18, 12)), (.45, (170, 56, 22)), (.7, (255, 140, 40)), (1, (255, 214, 120)))), a)
    img = sky.copy()
    if a < .3:
        sun(img, 880, 560, 70, (255, 248, 220), (255, 214, 150), 1 - a)
    put_clouds(img, 3, (255, 240, 220), 420, t * 10)
    bg = coast_bg()
    img.paste(bg, (0, 0), bg)
    # asteroide
    if pre or t < ti + .05:
        p = prog(t, 0, ti)
        path = p ** 1.35
        sx, sy = -90, 30
        x, y = lerp(sx, imp[0], path), lerp(sy, imp[1], path)
        R = 26 + 70 * path
        ux, uy = sx - imp[0], sy - imp[1]
        L = math.hypot(ux, uy)
        ux, uy = ux / L, uy / L
        n = 34
        for i in range(n, 0, -1):
            f = i / n
            add_glow(img, x + ux * f * 700 * path - ux * 0, y + uy * f * 700 * path, R * (1.4 - .9 * f), (255, 120 + int(100 * (1 - f)), 40), 1.5, .6 * (1 - f) + .1)
        add_glow(img, x, y, R * 3.2, (255, 190, 100), 1.8, .8)
        rk = rock_sprite(512).resize((int(2 * R), int(2 * R)), Image.LANCZOS).rotate(-t * 60, resample=Image.BICUBIC)
        img.paste(rk, (int(x - rk.width / 2), int(y - rk.height / 2)), rk)
        add_glow(img, x, y, R * 1.5, (255, 170, 80), 1.3, .9)
    else:
        pass
    if post > 0:
        # anillos en el mar
        ov = new_ov()
        d = ImageDraw.Draw(ov)
        for j in range(3):
            age = post * .38 - j * .16
            if age > 0:
                rr = age * 1500
                al = int(220 * max(0, 1 - age * 1.1))
                d.ellipse((imp[0] - rr, imp[1] - rr * .16, imp[0] + rr, imp[1] + rr * .16), outline=(255, 236, 200, al), width=8)
        flush(img, ov)
        # bola de fuego
        gr = 150 + 650 * sm(prog(post, 0, 2.2))
        add_glow(img, imp[0], imp[1] - 60, gr * 1.6, (255, 120, 40), 1.4, .9 * (1 - .4 * prog(post, 1, 2)))
        add_glow(img, imp[0], imp[1] - 40, gr, (255, 210, 120), 1.2, 1)
        add_glow(img, imp[0], imp[1] - 30, gr * .5, (255, 255, 235), 1.2, 1)
        # columna de fuego, vapor y escombros
        for i in range(15):
            g = clamp(post * .5 - i * .035)
            if g <= 0:
                continue
            f = i / 14
            yy = imp[1] - 40 - g * 1500 * (f * .8 + .15)
            put_puff(img, imp[0] + 50 * math.sin(i * 1.7) * g, yy, 70 + g * 120, mix((255, 170, 70), (190, 100, 56), f), .7 - .3 * f)
            add_glow(img, imp[0] + 50 * math.sin(i * 1.7) * g, yy, 160 * (1 - f * .5), (255, 120, 40), 1.6, .35 * (1 - f))
        # eyecciones
        ov = new_ov()
        d = ImageDraw.Draw(ov)
        rnd = random.Random(8)
        for _ in range(90):
            vx = rnd.uniform(-520, 520)
            vy = -rnd.uniform(500, 1500)
            tt = post * rnd.uniform(.85, 1.05)
            x = imp[0] + vx * tt
            y = imp[1] - 20 + vy * tt + 760 * tt * tt
            if y < imp[1] + 40:
                r = rnd.uniform(3, 7)
                d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 170 + int(60 * rnd.random()), 60, int(255 * (1 - prog(post, 1.6, 2))))
                          )
        flush(img, ov)
        flash(img, 1.0 - prog(post, 0, .9))
    # mapa
    m = map_inset()
    fa = sm(prog(t, .2, .8))
    if fa > 0:
        mm = m.copy()
        mm.putalpha(mm.getchannel("A").point(lambda v: int(v * fa)))
        px, py = 700, 130
        img.paste(mm, (px, py), mm)
        ov = new_ov()
        d = ImageDraw.Draw(ov)
        cx, cy = px + 360 * .53, py + 360 * .21
        pul = (t * 1.4) % 1
        d.ellipse((cx - 8 - pul * 30, cy - 8 - pul * 30, cx + 8 + pul * 30, cy + 8 + pul * 30), outline=(255, 70, 50, int(255 * (1 - pul) * fa)), width=4)
        d.ellipse((cx - 8, cy - 8, cx + 8, cy + 8), fill=(255, 60, 40, int(255 * fa)))
        flush(img, ov)
    return img


# =========================================================== ESCENA 7 (explosion)
def s7(t):
    P = PAL["fire"]
    base = (540, 1190)
    img = draw_sky(P["sky"])
    img = Image.blend(img, sky_img(((0, (70, 20, 16)), (.5, (210, 80, 26)), (.72, (255, 170, 60)), (1, (255, 236, 160)))), .65)
    e = sm(prog(t, 0, 3.8))
    # cuerpo de la explosion detras del horizonte
    add_glow(img, base[0], base[1] - 200, 1500 * (.5 + .5 * e), (255, 110, 30), 1.4, .9)
    add_glow(img, base[0], base[1] - 150, 900 * (.4 + .6 * e), (255, 190, 90), 1.3, 1)
    # columna + hongo
    top_y = base[1] - 120 - 1050 * sm(prog(t, 0, 4.2))
    ov = new_ov()
    d = ImageDraw.Draw(ov)
    sw = 90 + 80 * e
    d.polygon([(base[0] - sw * 1.4, base[1]), (base[0] - sw * .5, top_y + 160), (base[0] + sw * .5, top_y + 160), (base[0] + sw * 1.4, base[1])], fill=(150, 56, 24, 230))
    flush(img, ov)
    rnd = random.Random(3)
    for i in range(34):
        ang = rnd.uniform(0, TAU)
        rr = rnd.uniform(0, 1) ** .6 * (210 + 330 * e)
        cx = base[0] + math.cos(ang) * rr * 1.15
        cy = top_y + 90 + math.sin(ang) * rr * .55
        c = mix((255, 190, 90), (70, 30, 24), clamp(rr / (210 + 330 * e) * 1.15 + rnd.uniform(-.2, .2)))
        put_puff(img, cx, cy, 70 + 90 * e, c, .85)
    add_glow(img, base[0], top_y + 140, 420 * e + 60, (255, 170, 70), 1.4, .8)
    add_glow(img, base[0], base[1] - 20, 600, (255, 240, 190), 1.4, 1.0 * (1 - .4 * e))
    cam = 60 * t / 5
    draw_back(img, cam, "fire")
    # siluetas de dinosaurios oscuros mirando
    for kind, x, y, sc, fl, a in (("brachio", 220, 1400, .72, 0, 1.0), ("tric", 800, 1380, .66, 1, .8), ("tric", 640, 1440, .8, 1, .6)):
        put_actor(img, kind, x - cam * .85, y, sc, t, flip=bool(fl), idle=True, a=a, hz=(36, 10, 10, .78), shadow=False)
    draw_front(img, cam, "fire")
    # onda expansiva
    ov = new_ov()
    d = ImageDraw.Draw(ov)
    for j in range(3):
        age = t * .42 - j * .13
        if age > 0:
            rr = age * 1900
            al = int(230 * max(0, 1 - age * .85))
            d.ellipse((base[0] - rr, base[1] + 40 - rr * .12, base[0] + rr, base[1] + 40 + rr * .12), outline=(255, 238, 200, al), width=9)
    flush(img, ov)
    ov = new_ov()
    rnd2 = random.Random(21)
    d = ImageDraw.Draw(ov)
    for _ in range(80):
        x0, v = rnd2.uniform(-300, 300), rnd2.uniform(200, 800)
        x = base[0] + x0 * (.3 + t * .6)
        y = base[1] - v * t * (1.1 - .1 * t) + 90 * t * t
        r = rnd2.uniform(2, 5)
        d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 190, 80, 220))
    flush(img, ov)
    flash(img, 1.0 - prog(t, 0, .9))
    return img


# =========================================================== ESCENA 8 (fuego y sismos)
def flame(d, x, y, h, w, t, seed):
    h = h * (1 + .16 * math.sin(t * 12 + seed))
    sw = math.sin(t * 8 + seed * 1.7) * w * .25
    for col, k in (((200, 40, 10, 235), 1.0), ((255, 120, 24, 240), .72), ((255, 224, 100, 250), .42)):
        hh, ww = h * k, w * k
        d.polygon([(x - ww / 2, y), (x - ww * .62, y - hh * .4), (x - ww * .2 + sw * .4, y - hh * .78), (x + sw * k, y - hh),
                   (x + ww * .24 + sw * .4, y - hh * .68), (x + ww * .58, y - hh * .38), (x + ww / 2, y)], fill=col)


@functools.lru_cache(maxsize=1)
def cracks():
    rnd = random.Random(12)
    out = []
    for i in range(7):
        x, y = rnd.uniform(60, 1020), rnd.uniform(1380, 1520)
        pts = [(x, y)]
        ang = rnd.uniform(-.4, .4) + math.pi / 2 * rnd.choice((-1, 1)) * .3 + (math.pi / 2)
        for _ in range(16):
            ang += rnd.uniform(-.7, .7)
            x += math.cos(ang) * rnd.uniform(24, 52) * 1.4
            y += math.sin(ang) * rnd.uniform(10, 24)
            pts.append((x, y))
        out.append(pts)
    return out


def s8(t):
    cam = 90 * t / 5
    img = draw_sky(PAL["fire"]["sky"])
    sun(img, 700, 560, 80, (255, 170, 90), (255, 90, 30), .8)
    put_clouds(img, 5, (40, 20, 18), 230, cam * .2 + t * 22)
    put_clouds(img, 6, (70, 32, 22), 560, cam * .1 + t * 15)
    draw_back(img, cam, "fire")
    # fuego en distintas capas
    ov = new_ov()
    d = ImageDraw.Draw(ov)
    rnd = random.Random(5)
    for lay, (yy, sp, hh, ww, n) in enumerate(((1130, .28, 70, 36, 18), (1230, .5, 110, 52, 14), (1315, .85, 160, 78, 11))):
        for i in range(n):
            x = (i + rnd.uniform(0, .7)) * (W + 160) / n - cam * sp
            flame(d, x, yy + rnd.uniform(-10, 14), hh * rnd.uniform(.7, 1.3), ww * rnd.uniform(.8, 1.2), t, rnd.uniform(0, 9))
        if lay == 1:
            flush(img, ov)
            for i in range(14):
                add_glow(img, ((i + .3) * (W + 160) / 14 - cam * .5), 1190, 150, (255, 120, 30), 2, .35)
            ov = new_ov()
            d = ImageDraw.Draw(ov)
    flush(img, ov)
    # humo
    for i in range(22):
        a = (t * .3 + i / 22) % 1
        x = (i * 71 % W) - cam * .5 - a * 120
        put_puff(img, x, 1150 - a * 800, 50 + a * 120, (36 + int(30 * a), 24 + int(14 * a), 22), .5 * (1 - a))
    # dinosaurios huyendo
    for kind, x0, v, y, sc, fl, cy in (("tric", 1250, -190, 1420, .72, 1, .62), ("brachio", 1500, -120, 1360, .56, 1, .9), ("trex", 1800, -240, 1450, .6, 1, .5)):
        put_actor(img, kind, x0 + v * t - cam * .85, y, sc, t, flip=bool(fl), cyc=cy, hz=(40, 12, 8, .66), shadow=False)
    # onda de choque / polvo
    sx = 1500 - 1900 * prog(t, 0.2, 3.6)
    for i in range(14):
        put_puff(img, sx + i * 26, 1340 + 60 * math.sin(i * 2.1), 120, (110, 60, 36), .35 * sm(1 - abs(prog(t, .2, 3.6) - .5) * 2))
    # grietas incandescentes
    ov = new_ov()
    d = ImageDraw.Draw(ov)
    gp = prog(t, .2, 3.4)
    for pts in cracks():
        n = max(2, int(len(pts) * gp))
        pp = [(x - cam * 1.2, y) for x, y in pts[:n]]
        d.line(pp, fill=(255, 90, 20, 255), width=11, joint="curve")
        d.line(pp, fill=(255, 220, 110, 255), width=4, joint="curve")
    flush(img, ov)
    glow_pts = [(p[0] - cam * 1.2, p[1]) for pts in cracks() for p in pts[::3]]
    for gx, gy in glow_pts[:20]:
        add_glow(img, gx, gy, 70, (255, 100, 30), 2, .25 * gp)
    draw_front(img, cam, "fire")
    ov = new_ov()
    d = ImageDraw.Draw(ov)
    rnd = random.Random(31)
    for _ in range(160):
        x0, y0, sp = rnd.uniform(0, W), rnd.uniform(0, 1500), rnd.uniform(80, 300)
        x = (x0 + t * rnd.uniform(-30, 80)) % W
        y = (y0 - t * sp) % 1500
        r = rnd.uniform(1.5, 4.2)
        d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 170 + int(80 * rnd.random()), 60, 230))
    flush(img, ov)
    return img


# =========================================================== ESCENA 9 (polvo)
def s9(t):
    cam = 80 * t / 5
    d_ = prog(t, 0, 4.5)
    P = PAL["ash"]
    img = draw_sky(P["sky"])
    sun(img, 560 - cam * .05, 520 - 20 * d_, 70, (255, 190, 120), (255, 130, 70), 1 - .9 * sm(d_))
    for i, (sd, y, col, sp) in enumerate(((7, 120, (58, 50, 48), 18), (8, 340, (74, 62, 56), 25), (9, 560, (90, 74, 62), 33))):
        put_clouds(img, sd, col, y, cam * .2 + t * sp)
    draw_back(img, cam, "ash")
    for kind, x, y, sc, fl in (("tric", 300, 1350, .55, 0), ("tric", 520, 1362, .5, 0), ("brachio", 760, 1300, .38, 1), ("tric", 880, 1400, .66, 1)):
        put_actor(img, kind, x - cam * .85, y, sc, t, flip=bool(fl), idle=True, a=.7, hz=hz("ash", .5))
    draw_front(img, cam, "ash")
    # capas gruesas de polvo cayendo sobre todo
    cover = sm(prog(t, .2, 4.2))
    for i, (sd, y, col, sp) in enumerate(((10, 0, (60, 50, 46), 38), (11, 220, (84, 68, 58), 48), (12, 520, (100, 84, 70), 52))):
        c = cloud_layer_alpha(sd, col, cover * (.9 - i * .1))
        v = c.transform((W, c.height), Image.AFFINE, (1, 0, (cam * .4 + t * sp) % (c.width - W), 0, 1, 0), resample=Image.BILINEAR)
        img.paste(v, (0, int(y - 120 + 60 * (1 - cover))), v)
    img = multiply_color(img, (170, 150, 140), cover * .8)
    ov = new_ov()
    particles(ov, t, 230, 14, (205, 190, 176), 260, -90, (1.5, 3.6), 210)
    flush(img, ov)
    # relampago volcanico
    lf = max(0, 1 - abs(t - 2.5) * 6) + max(0, 1 - abs(t - 2.72) * 8) * .7
    if lf > 0:
        flash(img, .3 * lf, (200, 200, 255))
        ov = new_ov()
        d = ImageDraw.Draw(ov)
        x, y = 720, 220
        pts = [(x, y)]
        rnd = random.Random(2)
        for _ in range(9):
            x += rnd.uniform(-50, 40)
            y += rnd.uniform(50, 90)
            pts.append((x, y))
        d.line(pts, fill=(235, 235, 255, int(255 * lf)), width=6)
        flush(img, ov)
    return img


@functools.lru_cache(maxsize=24)
def cloud_layer_alpha(seed, col, a):
    c = Image.new("RGBA", (2300, 700), tuple(col) + (0,))
    rnd = random.Random(seed)
    m = Image.new("L", (2300, 700), 0)
    d = ImageDraw.Draw(m)
    for _ in range(46):
        cx, cy = rnd.uniform(0, 2300), rnd.uniform(120, 580)
        for _ in range(5):
            r = rnd.uniform(60, 170)
            ox, oy = rnd.uniform(-180, 180), rnd.uniform(-40, 40)
            d.ellipse((cx + ox - r * 1.7, cy + oy - r * .7, cx + ox + r * 1.7, cy + oy + r * .7), fill=rnd.randint(150, 255))
    m = m.filter(ImageFilter.GaussianBlur(34)).point(lambda v: int(v * clamp(round(a * 10) / 10)))
    c.putalpha(m)
    return c


# =========================================================== ESCENA 10 (plantas mueren, frio)
def wilting_ferns(img, t, cam):
    w = sm(prog(t, .2, 4.2))
    ov = new_ov()
    d = ImageDraw.Draw(ov)
    green, brown = (52, 112, 58), (112, 84, 54)
    col = mix(green, brown, w) + (255,)
    for bx in (90, 300, 520, 760, 980):
        x = bx - cam * 1.4
        y = 1640
        rnd = random.Random(bx)
        for a in range(-160, -19, 18):
            ar = math.radians(a + rnd.uniform(-5, 5))
            Ln = 190 * rnd.uniform(.8, 1.15)
            droop = lerp(.35, 1.9, w) * rnd.uniform(.85, 1.15)
            pts = [(x + math.cos(ar) * Ln * s * (1 - .25 * w), y + math.sin(ar) * Ln * s * (1 - .55 * w) + Ln * droop * s * s * .6) for s in [i / 10 for i in range(11)]]
            d.line(pts, fill=col, width=7, joint="curve")
            for j in range(2, 11):
                px, py = pts[j]
                ll = 26 * (1 - j / 12)
                d.line([(px, py), (px - ll * .6, py + ll)], fill=col, width=3)
                d.line([(px, py), (px + ll * .6, py + ll)], fill=col, width=3)
    flush(img, ov)


def thermometer(img, t):
    x, y, hh = 930, 250, 380
    lvl = lerp(.88, .12, sm(prog(t, .3, 4.4)))
    ov = new_ov()
    d = ImageDraw.Draw(ov)
    d.rounded_rectangle((x - 22, y, x + 22, y + hh), 22, fill=(20, 24, 30, 170), outline=(255, 255, 255, 255), width=5)
    d.ellipse((x - 44, y + hh - 22, x + 44, y + hh + 66), fill=(20, 24, 30, 190), outline=(255, 255, 255, 255), width=5)
    col = mix((235, 70, 50), (90, 170, 255), 1 - lvl)
    top = y + 20 + (hh - 40) * (1 - lvl)
    d.rounded_rectangle((x - 11, top, x + 11, y + hh), 11, fill=col + (255,))
    d.ellipse((x - 32, y + hh - 10, x + 32, y + hh + 54), fill=col + (255,))
    for i in range(6):
        yy = y + 30 + i * (hh - 60) / 5
        d.line([(x + 30, yy), (x + 52, yy)], fill=(255, 255, 255, 220), width=4)
    flush(img, ov)


def s10(t):
    cam = 90 * t / 5
    k = sm(prog(t, .3, 4.2))
    # estado vivo (ceniza) -> muerto (frio)
    a = draw_sky(PAL["ash"]["sky"])
    sun(a, 560, 500, 66, (255, 200, 140), (255, 140, 80), .5)
    draw_back(a, cam, "ash")
    b = draw_sky(PAL["dead"]["sky"])
    sun(b, 560, 500, 66, (255, 240, 220), (255, 230, 200), .5)
    draw_back(b, cam, "dead", trees="dead")
    img = Image.blend(a, b, k)
    draw_front(img, cam, "dead", trees="dead")
    wilting_ferns(img, t, cam)
    # tinte frio progresivo y escarcha
    img = multiply_color(img, (170, 190, 230), .65 * k)
    ov = new_ov()
    particles(ov, t, int(40 + 160 * k), 17, (240, 246, 255), 120, -40, (1.5, 3.6), int(120 + 120 * k))
    flush(img, ov)
    fr = np.zeros((H, W), np.float32)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    dist = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    fr = np.clip((dist - .75) / .6, 0, 1) ** 1.5 * k * 200
    frost = Image.new("RGBA", (W, H), (205, 230, 255, 0))
    frost.putalpha(Image.fromarray(fr.astype(np.uint8), "L"))
    img.paste(frost, (0, 0), frost)
    thermometer(img, t)
    return img


# =========================================================== ESCENA 11 (colapso)
def donut(img, cx, cy, r, frac, t):
    S = 2
    n = int(r * 2 * S + 40)
    big = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    c = n / 2
    rr = r * S
    wd = int(26 * S)
    d.ellipse((c - rr - 14, c - rr - 14, c + rr + 14, c + rr + 14), fill=(10, 14, 20, 120))
    d.arc((c - rr, c - rr, c + rr, c + rr), -90, 270, fill=(120, 200, 140, 255), width=wd)
    if frac > 0.002:
        d.arc((c - rr, c - rr, c + rr, c + rr), -90, -90 + 360 * frac, fill=(230, 70, 56, 255), width=wd)
    big = big.resize((n // S, n // S), Image.LANCZOS)
    img.paste(big, (int(cx - big.width / 2), int(cy - big.height / 2)), big)


def s11(t):
    cam = 70 * t / 5
    P = PAL["cold"]
    img = draw_sky(P["sky"])
    sun(img, 300 - cam * .05, 560, 60, (250, 250, 246), (235, 240, 250), .55)
    put_clouds(img, 13, (190, 200, 210), 300, cam * .2 + t * 10)
    put_clouds(img, 14, (210, 218, 224), 640, cam * .1 + t * 6)
    draw_back(img, cam, "cold", trees="dead")
    put_haze(img, 1330, 300, (214, 224, 230), .5)
    put_actor(img, "tric", 780 - 16 * t - cam * .85, 1352, .52, t, flip=True, cyc=2.4, hz=hz("cold", .5))
    put_actor(img, "brachio", 420 + 14 * t - cam * .85, 1415, .74, t, flip=False, cyc=2.6, hz=hz("cold", .15))
    # costillas de esqueleto en primer plano
    ov = new_ov()
    d = ImageDraw.Draw(ov)
    bx, by = 880 - cam * 1.3, 1560
    d.line([(bx - 330, by + 10), (bx + 20, by - 2)], fill=(226, 222, 206, 255), width=16)
    for i in range(7):
        x = bx - 280 + i * 46
        d.arc((x - 40, by - 150 - i * 4, x + 120, by + 20), 190, 330, fill=(226, 222, 206, 255), width=13)
    flush(img, ov)
    draw_front(img, cam, "cold", trees="dead")
    img = multiply_color(img, (190, 204, 226), .5)
    put_haze(img, 1000, 700, (214, 224, 232), .35)
    ov = new_ov()
    particles(ov, t, 200, 19, (245, 248, 255), 90, -50, (1.5, 3.8), 200)
    flush(img, ov)
    donut(img, 880, 300, 110, .75 * sm(prog(t, .3, 3.2)), t)
    return img


# =========================================================== ESCENA 12 (amanecer)
def s12(t):
    cam = 130 * t / 5
    P = PAL["dawn"]
    img = draw_sky(P["sky"])
    sy = lerp(1210, 860, sm(prog(t, 0, 5)))
    sx = 560 - cam * .05
    # rayos de luz
    ov = new_ov()
    d = ImageDraw.Draw(ov)
    for i in range(14):
        a0 = -math.pi + (i + .2) * math.pi / 14 + .08 * math.sin(t * .8 + i)
        a1 = a0 + .09
        d.polygon([(sx, sy), (sx + math.cos(a0) * 2400, sy + math.sin(a0) * 2400), (sx + math.cos(a1) * 2400, sy + math.sin(a1) * 2400)], fill=(255, 220, 150, 20))
    flush(img, ov)
    sun(img, sx, sy, 120, (255, 250, 230), (255, 200, 120), 1.35)
    put_clouds(img, 21, (255, 190, 170), 420, cam * .2 + t * 10)
    put_clouds(img, 22, (255, 214, 180), 700, cam * .1 + t * 6)
    draw_back(img, cam, "dawn")
    put_haze(img, 1250, 240, (255, 196, 140), .22)
    draw_front(img, cam, "dawn")
    for x0, v, y, sc, ph in ((-120, 74, 1395, 2.8, 0), (-460, 66, 1440, 3.1, .4), (-760, 80, 1365, 2.5, .7)):
        put_actor(img, "mammal", x0 + v * t * 1.5 + 420 - cam * 1.0, y, sc, t, flip=False, ph0=ph, cyc=.55, hz=(255, 190, 140, .0))
    # reflejos de rocio
    ov = new_ov()
    d = ImageDraw.Draw(ov)
    rnd = random.Random(7)
    for _ in range(46):
        x, y = rnd.uniform(0, W), rnd.uniform(1380, 1700)
        a = max(0, math.sin(t * 3 + rnd.uniform(0, TAU)))
        r = 2 + 4 * a
        d.line([(x - r * 2, y), (x + r * 2, y)], fill=(255, 250, 225, int(230 * a)), width=2)
        d.line([(x, y - r * 2), (x, y + r * 2)], fill=(255, 250, 225, int(230 * a)), width=2)
    flush(img, ov)
    return img


SCENES = [s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12]


# camara por escena: (zoom0, zoom1, foco_x, foco_y, sy0, sy1, shake_fn)
def _shake(amp, t0, dur):
    def f(t):
        if t < t0:
            return 0, 0
        k = amp * max(0, 1 - (t - t0) / dur)
        return k * math.sin(t * 55), k * math.cos(t * 47)
    return f


CAMS = [
    (1.0, 1.07, 540, 1100, 0, 0, None),
    (1.0, 1.07, 300, 1200, 0, 0, None),
    (1.0, 1.15, 330, 1000, 0, 0, lambda t: (3 * math.sin(t * 60), 3 * math.cos(t * 52)) if .9 < t < 4 else (0, 0)),
    (1.04, 1.1, 540, 1000, 20, -70, None),
    (1.0, 1.1, 540, 900, 0, 0, None),
    (1.0, 1.04, 540, 1100, 0, 0, _shake(18, 3.0, 2.0)),
    (1.0, 1.06, 540, 1100, 0, 0, _shake(26, 0.0, 2.5)),
    (1.04, 1.08, 540, 1100, 0, 0, lambda t: (8 * math.sin(t * 38), 6 * math.cos(t * 31))),
    (1.02, 1.08, 540, 1000, 0, 0, None),
    (1.03, 1.08, 540, 1100, 0, 0, None),
    (1.0, 1.08, 540, 1100, 0, 0, None),
    (1.12, 1.0, 540, 1100, -40, 20, None),
]


def scene_cam(k, t):
    img = SCENES[k](t)
    z0, z1, fx, fy, s0, s1_, shk = CAMS[k]
    u = prog(t, 0, 5)
    z = lerp(z0, z1, u)
    sy = lerp(s0, s1_, u)
    sx_off, sy_off = shk(t) if shk else (0, 0)
    if z == 1.0 and sy == 0 and not sx_off and not sy_off:
        return img
    a = 1 / z
    c = fx - fx / z + sx_off
    f = fy - fy / z + sy + sy_off
    return img.transform((W, H), Image.AFFINE, (a, 0, c, 0, a, f), resample=Image.BILINEAR)
