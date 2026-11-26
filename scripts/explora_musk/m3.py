"""Escena 3 — Zip2, la venta a Compaq y Elon sigue adelante."""
from kit import *
_c = {}
LW, LH = 1300, 1920


def build():
    if "A" in _c: return _c
    def office(p):
        office_bg(p, LW, LH, sign="ZIP2", theme="zip")
        desk_row(p, 120, 640, 1010); desk_row(p, 680, 1200, 1010)
        # cajas de pizza y latas
        p.rect(1010, 982, 1120, 1010, (230, 190, 120)); p.rect(580, 986, 600, 1010, (200, 60, 60))
    def meeting(p):
        p.vgrad(0, 0, LW, 1260, [(0, (60, 72, 108)), (1, (44, 54, 86))])
        p.rect(0, 1260, LW, LH, (84, 76, 88))
        p.rect(0, 1248, LW, 1266, (36, 40, 62))
        for x in (80, LW - 360):
            p.rect(x, 300, x + 280, 640, (70, 90, 130)); p.vgrad(x + 10, 310, x + 270, 630, [(0, (150, 200, 245)), (1, (210, 230, 250))])
        p.rrect(LW / 2 - 230, 170, LW / 2 + 230, 290, 20, (230, 232, 240))
        p.text(LW / 2, 232, "COMPAQ", 80, (200, 40, 50), anchor="mm")
        p.rrect(200, 1040, LW - 200, 1075, 12, (150, 110, 76)); p.rect(360, 1075, 400, 1260, (100, 72, 50)); p.rect(LW - 400, 1075, LW - 360, 1260, (100, 72, 50))
    def street(p):
        p.vgrad(0, 0, LW, 1300, [(0, (120, 180, 240)), (1, (232, 240, 250))])
        skyline(p, LW, LH, 1150, 11, (176, 190, 214), (255, 255, 255), 200, 560, 90, 150, .0)
        p.rect(0, 1300, LW, LH, (96, 98, 110)); p.rect(0, 1300, LW, 1340, (170, 170, 176))
        for xx in range(0, LW, 200): p.rect(xx, 1580, xx + 100, 1592, (240, 240, 240))
    def far(p):
        skyline(p, 2400, LH, 1260, 19, (150, 164, 196), (255, 255, 255), 260, 700, 100, 180, .0)
    _c["A"] = Layer(bake(LW, LH, office), LW, LH, ox=-110, par=.9, zpar=.9)
    _c["B"] = Layer(bake(LW, LH, meeting), LW, LH, ox=-110, par=.9, zpar=.9)
    _c["S"] = Layer(bake(LW, LH, street), LW, LH, ox=-110, par=.4, zpar=.8)
    return _c


from m1 import skyline


def sub_office(t, base, f):
    C = build()
    cam = Cam(540 + 30 * math.sin(t * .5), 1020, 1.0 + .08 * prog(t, 0, 3.6))
    C["A"].blit(base, cam)
    mon = desk_set(t, seed=5, w=240)
    for (x, sd) in ((400, 1), (760, 2)):
        mx, my = cam.p(x, 880); put_icon(base, desk_set(t + sd, seed=sd, w=240), mx, my, scale=cam.z)
    ch = cached(("chair2",), lambda: chair(150))
    # Elon (izq) y Kimbal (der): teclean, se giran a hablar, chocan las manos
    talk = ease(prog(t, 1.2, 1.7)) * (1 - ease(prog(t, 2.5, 2.8)))
    hi = ease(prog(t, 2.6, 2.9)) * (1 - ease(prog(t, 3.2, 3.5)))
    for (name, hx, flip, off) in (("elon_young", 290, False, 0), ("kimbal", 860, True, 1.3)):
        sx, sy = cam.p(hx, 1060)
        put_icon(base, ch, sx - (0 if not flip else 0), sy + 20 * cam.z, scale=cam.z * .9)
        pose = seated(t, off, head=-2 + talk * (8 if not flip else -8), turn=.1 + .6 * talk, mouth=(.5 + .5 * math.sin(t * 12 + off * 3)) * talk * .8,
                      smile=.3 + .5 * hi, eyes=blink(t, 3, off), brow=.2 * talk)
        if hi > 0.01:
            pose["sf"] = lerp(pose["sf"], 160, hi); pose["ef"] = lerp(pose["ef"], 0, hi)
        place_person(base, name, pose, hx, 1010, cam, k=1.0, flip=flip)
    # año 1995
    ya = ease_back(prog(t, .2, .8))
    im = text_img("1995", 120, (255, 214, 120), stroke=8, stroke_col=(40, 30, 60))
    paste_np(base, im.resize((int(im.width * ya), int(im.height * ya)), Image.LANCZOS) if ya > .05 else im.resize((4, 4)), 540 - im.width * ya / 2, 1330 - im.height * ya / 2, ya)
    if hi > 0.5:
        for q in range(8):
            a = q / 8 * 6.28; r = 70 + 90 * prog(t, 3.0, 3.5)
            f.L.ellipse([540 + math.cos(a) * r - 6, 860 + math.sin(a) * r * .6 - 6, 540 + math.cos(a) * r + 6, 860 + math.sin(a) * r * .6 + 6], fill=sc(AMBER, hi))


def sub_meeting(t, base, f):
    C = build()
    cam = Cam(540, 1020, 1.0 + .06 * prog(t, 0, 3.6))
    C["B"].blit(base, cam)
    # año -> 1999 (calendario que cambia)
    flipk = prog(t, .3, 1.0)
    txt = "1995" if flipk < .5 else "1999"
    im = text_img(txt, 120, (255, 214, 120), stroke=8, stroke_col=(20, 24, 50))
    sc_y = abs(math.cos(flipk * math.pi)) if flipk < 1 else 1
    im2 = im.resize((im.width, max(int(im.height * max(sc_y, .05)), 2)), Image.LANCZOS)
    paste_np(base, im2, 540 - im2.width / 2, 520 - im2.height / 2)
    # ejecutivos de Compaq y los hermanos; apretón de manos
    hs = ease(prog(t, 1.2, 1.8))
    for (name, hx, flip) in (("exec1", 760, True), ("exec2", 940, True)):
        place_person(base, name, mk(smile=.4, sf=0, brow=.1, eyes=blink(t, 3.3, hx / 500)), hx + 100, 1180, cam, k=1.0, flip=True) if False else None
    place_person(base, "exec1", mk(sf=lerp(0, 76, hs), ef=lerp(10, 4, hs), smile=.5, turn=.2, head=-2, eyes=blink(t, 3.3)), 770, 1200, cam, k=1.0, flip=True)
    place_person(base, "elon_young", mk(sf=lerp(0, 76, hs), ef=lerp(10, 4, hs), smile=.6, turn=.2, head=2, eyes=blink(t, 3.0, .6), lean=3 * hs), 420, 1200, cam, k=1.0)
    place_person(base, "kimbal", mk(smile=.7, sf=-5, eb=10, mouth=.2 * (.5 + .5 * math.sin(t * 6)), eyes=blink(t, 3.2, 1)), 250, 1200, cam, k=1.0)
    place_person(base, "exec2", mk(smile=.5, sf=-8, ef=30, eyes=blink(t, 3.5, .2)), 920, 1200, cam, k=1.0, flip=True)
    # mesa por delante
    # cheque / maletín con dinero
    ck = cached(("check",), lambda: check_icon(420, "CIENTOS DE MILLONES"))
    ca = ease_back(prog(t, 1.9, 2.6))
    if ca > .02: put_icon(base, ck, 590, 1000 - 40 * ease_out(prog(t, 1.9, 2.6)), scale=ca * cam.z)
    mb = cached(("bag",), lambda: money_bag(130))
    cn = cached(("coin",), lambda: coin_icon(30))
    for q in range(14):
        u = prog(t, 2.2 + q * .05, 3.6)
        if 0 < u < 1:
            x = 590 + (q - 7) * 46 + 20 * math.sin(q * 2); y = 900 - 520 * ease_out(u) + 700 * u * u * .35
            put_icon(base, cn if q % 2 else mb, x, y, scale=cam.z * (.7 + .4 * (q % 3) / 2), alpha=1 - u ** 2)


def sub_street(t, base, f):
    C = build()
    wx = 300 + 260 * t                      # Elon avanza
    cam = Cam(wx + 200, 1180, 1.05)
    C["S"].blit(base, cam, dx=-(wx * .0))
    # edificios lejanos con paralaje (desplazamiento por tiempo)
    for k in range(5):
        x0 = ((k * 560 - wx * .55) % 2800) - 500
        bw = 320; bh = 520 + 140 * ((k * 37) % 5)
        f.L.rectangle([x0, 1310 - bh, x0 + bw, 1310], fill=(30, 36, 50)) if False else None
    # raya de carretera que se desliza
    for k in range(14):
        x = ((k * 200 - wx) % 2800) - 300
        sx, sy = cam.p(wx + (x - 300) + 0, 1585)
        base[int(max(sy - 6, 0)):int(min(sy + 6, H)), int(max(sx, 0)):int(min(sx + 100 * cam.z, W))] = (240, 240, 240)
    ph = (t * 1.7)
    pose = walk_pose(ph % 1, speed=1.1, head=-2, smile=.25, brow=-.1, turn=.1, eyes=blink(t, 3, .3), lookx=1.3)
    place_person(base, "elon_young", pose, wx, 1450, cam, k=1.35)
    # destello de determinación
    f.L.ellipse([700, 700, 900, 760], fill=sc((255, 255, 255), 0))


def scene(t):
    f = Frame(bg=False); base = f.base
    A, B, S = (0, 3.7), (3.3, 7.3), (6.9, 10.2)
    if t < 3.4:
        sub_office(t, base, f)
    elif t < 3.9:
        a = np.zeros_like(base); b = np.zeros_like(base)
        fa = Frame(bg=False); fb = Frame(bg=False)
        sub_office(t, a, fa); sub_meeting(t - 3.3, b, fb)
        base[:] = slide_blend(a, b, (t - 3.4) / .5, 1)
    elif t < 7.0:
        sub_meeting(t - 3.3, base, f)
    elif t < 7.5:
        a = np.zeros_like(base); b = np.zeros_like(base)
        fa = Frame(bg=False); fb = Frame(bg=False)
        sub_meeting(t - 3.3, a, fa); sub_street(t - 6.9, b, fb)
        base[:] = slide_blend(a, b, (t - 7.0) / .5, 1)
    else:
        sub_street(t - 6.9, base, f)
    dust(f, t, seed=9, n=26, tint=(255, 240, 200), alpha=.3)
    return f.finish()
