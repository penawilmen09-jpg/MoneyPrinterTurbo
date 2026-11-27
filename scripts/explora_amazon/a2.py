"""Escena 3 (27.55–37.5): nace Amazon como librería online; el equipo prepara los pedidos a mano."""
from amz import *
import a1
DUR = 9.95
CUT = 3.9
WH = .45


def site_img(w, h, t, n_orders):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=24, fill=(250, 252, 255, 255), outline=(40, 44, 60, 255), width=6)
    d.rectangle([0, 0, w, 90], fill=(30, 40, 70, 255))
    d.text((34, 45), "amazon", font=ImageFont.truetype(FONT_BOLD, 52), fill=(255, 255, 255, 255), anchor="lm")
    d.text((w - 34, 45), f"PEDIDOS: {n_orders}", font=ImageFont.truetype(FONT_BOLD, 38), fill=(255, 200, 90, 255), anchor="rm")
    cols = [(210, 70, 70), (70, 130, 210), (230, 190, 70), (90, 170, 120), (170, 100, 200), (240, 130, 70)]
    for i in range(6):
        r, c = divmod(i, 3); x = 30 + c * ((w - 60) // 3); y = 120 + r * 300; ww = (w - 60) // 3 - 20
        sel = (int(t * 2.2) % 6 == i)
        d.rounded_rectangle([x, y, x + ww, y + 270], radius=16, fill=(255, 244, 214, 255) if sel else (236, 240, 248, 255))
        d.rounded_rectangle([x + 16, y + 16, x + ww - 16, y + 180], radius=8, fill=cols[i] + (255,)); d.rectangle([x + 16, y + 16, x + 34, y + 180], fill=tuple(int(v * .7) for v in cols[i]) + (255,))
        d.rounded_rectangle([x + 16, y + 200, x + ww - 16, y + 250], radius=12, fill=(255, 160, 40, 255) if sel else (70, 130, 230, 255))
    return im


def sub_launch(t, base, f):
    C = a1.build()
    zt = ease_io(prog(t, 0, 4.2))
    cam = Cam(lerp(560, 640, zt), lerp(1040, 960, zt), lerp(1.0, 1.25, zt))
    C["S"].blit(base, cam)
    n = int(max(0, t - 1.4) * 2.2)
    sw = site_img(560, 800, t, n)
    sx, sy = cam.p(640, 800)
    put_icon(base, sw, sx, sy, scale=cam.z * 1.0)
    ch = cached(("chair",), lambda: chair(170)); cxx, cyy = cam.p(300, 1090); put_icon(base, ch, cxx, cyy + 18 * cam.z, scale=cam.z * .95)
    cheer = ease(prog(t, 1.6, 2.2))
    pose = seated(t, 0, head=-3, turn=.3, smile=lerp(.4, 1.0, cheer), mouth=.5 * cheer * (.5 + .5 * math.sin(t * 8)), brow=.5 * cheer, eyes=blink(t, 3, .3), lean=lerp(8, 2, cheer))
    pose["sf"] = lerp(pose["sf"], 150, cheer); pose["ef"] = lerp(pose["ef"], 10, cheer)
    place_person(base, "bezos_young", pose, 300, 1030, cam, k=1.0)
    pose = mk(sf=lerp(0, 160, cheer) + 8 * math.sin(t * 9) * cheer, ef=lerp(10, 20, cheer), sb=lerp(0, -150, cheer), eb=10, smile=.9, mouth=.5 * cheer, brow=.5 * cheer, turn=.3, eyes=blink(t, 3, .6))
    place_person(base, "dev_m", pose, 950, 1190, cam, k=1.0, flip=True)
    # confeti y hitos
    if t > 1.6:
        rng = np.random.RandomState(3)
        for i in range(40):
            u = prog(t, 1.6 + rng.rand() * .6, 3.4); x = 200 + rng.rand() * 800; y = 300 + 900 * u + 40 * math.sin(i + t * 5)
            f.L.rectangle([x, y, x + 12, y + 18], fill=sc([(255, 90, 100), (90, 200, 255), (255, 214, 90), (120, 240, 150)][i % 4], 1 - u ** 2 * .9))
    # etiquetas históricas: fundación 1994 y lanzamiento 1995 (no confundirlas)
    a = ease(prog(t, .2, .7))
    c1 = text_img("1994 · FUNDACIÓN", 44, (200, 210, 235), stroke=6, stroke_col=(10, 14, 36)); paste_np(base, c1, 540 - c1.width / 2, 130, a * (1 - .55 * ease(prog(t, 1.5, 2.0))))
    b = ease(prog(t, 1.5, 2.1))
    c2 = text_img("1995 · LIBRERÍA ONLINE", 54, (255, 214, 120), stroke=7, stroke_col=(10, 14, 36)); paste_np(base, c2, 540 - c2.width / 2, 196 - 20 * (1 - b), b)


def sub_packing(t, base, f):
    C = a1.build()
    cam = Cam(lerp(540, 700, ease_io(prog(t, 0, 6.2))), 1040, 1.0 + .06 * prog(t, 0, 6.2))
    C["S"].blit(base, cam)
    bo = cached(("box",), lambda: box_icon(150)); bk = cached(("bk0",), lambda: book_icon(70))
    # Jeff toma libros de la estantería
    cyc = (t * .8) % 1
    pose = mk(sf=lerp(30, 130, ease(math.sin(cyc * 6.28) * .5 + .5)), ef=20, smile=.9, turn=.3, eyes=blink(t, 3, .2), head=-3, lean=3, sb=-10)
    place_person(base, "bezos_young", pose, 940, 1190, cam, k=1.0, flip=True)
    # mesa de empaque
    for i, (nm, hx, flip, off) in enumerate((("dev_f", 480, False, 0), ("dev_m", 700, True, .5))):
        ph = (t * 1.1 + off) % 1
        pose = mk(sf=40 + 30 * math.sin(ph * 6.28), ef=50 + 20 * math.sin(ph * 6.28 + 1), sb=30, eb=40, smile=.6, turn=.2, eyes=blink(t, 3, off), head=-4 + 3 * math.sin(ph * 6.28), lean=10)
        place_person(base, nm, pose, hx, 1190, cam, k=1.0, flip=flip)
    mesa = cam.p(590, 1090)
    rect_np(base, mesa[0] - 260 * cam.z, mesa[1] - 6, mesa[0] + 260 * cam.z, mesa[1] + 22, (210, 170, 120))
    rect_np(base, mesa[0] - 230 * cam.z, mesa[1] + 22, mesa[0] - 205 * cam.z, mesa[1] + 220 * cam.z, (120, 90, 62)); rect_np(base, mesa[0] + 205 * cam.z, mesa[1] + 22, mesa[0] + 230 * cam.z, mesa[1] + 220 * cam.z, (120, 90, 62))
    # cajas sobre la mesa, cinta adhesiva y etiquetas
    for k in range(3):
        u = (t * .6 + k / 3) % 1
        x, y = mesa[0] - 150 * cam.z + u * 300 * cam.z, mesa[1] - 40 * cam.z
        put_icon(base, bo, x, y, scale=cam.z * .8)
        if .35 < u < .6:
            rect_np(base, x - 60 * cam.z, y - 36 * cam.z, x + 60 * cam.z, y - 28 * cam.z, (236, 214, 150))
        if .6 < u < .75: rect_np(base, x + 20 * cam.z, y + 4, x + 60 * cam.z, y + 30 * cam.z, (250, 250, 250))
    # mensajero que lleva paquetes a la camioneta
    cyc2 = (t * .32) % 1
    wx = lerp(980, 1500, cyc2) if cyc2 < .5 else lerp(1500, 980, (cyc2 - .5) * 2)
    face_r = cyc2 < .5
    w = walk_pose((t * 1.2) % 1, speed=.8, sf=70, ef=20, sb=70, eb=20, smile=.5, turn=.2, eyes=blink(t, 3, .9), head=-2)
    place_person(base, "tech_w", w, wx, 1200, cam, k=1.0, flip=not face_r)
    bx, by = cam.p(wx + (130 if face_r else -130), 1200 - 120)
    if face_r or cyc2 > .5: put_icon(base, bo, bx, by, scale=cam.z * .85) if face_r else None
    # camioneta
    trk = cached(("trk",), lambda: truck_icon(360, 0)); tx, ty = cam.p(1230, 1330); put_icon(base, trk, tx, ty, scale=cam.z)
    # crecimiento de pedidos (barras)
    g = ease(prog(t, 1.0, 5.6))
    pn = Image.new("RGBA", (860, 330), (0, 0, 0, 0)); d = ImageDraw.Draw(pn)
    d.rounded_rectangle([0, 0, 859, 329], radius=26, fill=(12, 18, 44, 205), outline=(120, 200, 255, 255), width=4)
    d.text((40, 40), "PEDIDOS", font=ImageFont.truetype(FONT_BOLD, 38), fill=(255, 255, 255, 255), anchor="lm")
    for i in range(10):
        hh = 18 + (i + 1) ** 1.5 * 8 * g * (1 + .1 * math.sin(t * 4 + i))
        x = 60 + i * 76
        d.rounded_rectangle([x, 300 - hh, x + 52, 300], radius=8, fill=(255, 190, 70, 255) if i < 9 else (120, 240, 160, 255))
    paste_np(base, pn, 110, 150, ease(prog(t, .5, 1.1)))


def scene(t):
    f = Frame(bg=False); base = f.base
    if t < CUT - WH / 2: sub_launch(t, base, f)
    elif t < CUT + WH / 2:
        a = np.zeros_like(base); b = np.zeros_like(base); fa = Frame(bg=False); fb = Frame(bg=False)
        sub_launch(t, a, fa); sub_packing(t - CUT, b, fb); base[:] = slide_blend(a, b, (t - (CUT - WH / 2)) / WH, 1)
        f = None
    else: sub_packing(t - CUT, base, f)
    if f is not None: dust(f, t, seed=62, n=26, tint=(255, 236, 200), alpha=.3); return f.finish()
    return base
