"""Escena 4 — X.com / PayPal / eBay."""
from kit import *
from m1 import skyline
_c = {}
LW, LH = 1300, 1920


def build():
    if "A" in _c: return _c
    def office(p):
        office_bg(p, LW, LH, wall=(206, 214, 226), floor=(96, 104, 120), sign="X.COM", theme="x")
        desk_row(p, 60, 560, 1030, (176, 184, 196)); desk_row(p, 740, 1240, 1030, (176, 184, 196))
    def office2(p):
        office_bg(p, LW, LH, wall=(206, 214, 226), floor=(96, 104, 120), sign="PayPal", theme="x")
        desk_row(p, 60, 560, 1030, (176, 184, 196)); desk_row(p, 740, 1240, 1030, (176, 184, 196))
    def ebay(p):
        p.vgrad(0, 0, LW, 1260, [(0, (70, 84, 130)), (1, (48, 58, 98))])
        p.rect(0, 1260, LW, LH, (80, 76, 92)); p.rect(0, 1248, LW, 1266, (34, 38, 60))
        for x in (80, LW - 360):
            p.rect(x, 300, x + 280, 640, (70, 90, 130)); p.vgrad(x + 10, 310, x + 270, 630, [(0, (150, 200, 245)), (1, (210, 230, 250))])
        p.rrect(LW / 2 - 230, 170, LW / 2 + 230, 290, 20, (240, 240, 246))
        for i, (ch, col) in enumerate((("e", (230, 50, 60)), ("B", (40, 100, 220)), ("a", (250, 190, 40)), ("y", (110, 190, 60)))):
            p.text(LW / 2 - 135 + i * 78, 238, ch, 96, col, anchor="mm")
        p.rrect(200, 1040, LW - 200, 1075, 12, (150, 110, 76))
    _c["A"] = Layer(bake(LW, LH, office), LW, LH, ox=-110, par=.9, zpar=.9)
    _c["A2"] = Layer(bake(LW, LH, office2), LW, LH, ox=-110, par=.9, zpar=.9)
    _c["E"] = Layer(bake(LW, LH, ebay), LW, LH, ox=-110, par=.9, zpar=.9)
    return _c


def arc_pt(a, b, u, h=240):
    return (lerp(a[0], b[0], u), lerp(a[1], b[1], u) - h * math.sin(math.pi * u))


def sub_office(t, base, f, logo2=0.0):
    C = build()
    cam = Cam(540 + 25 * math.sin(t * .6), 1020, 1.0 + .07 * prog(t, 0, 4.0))
    C["A"].blit(base, cam)
    if logo2 > 0:
        tmp = np.zeros_like(base); C["A2"].blit(tmp, cam); base[:] = base * (1 - logo2) + tmp * logo2
    ch = cached(("chair3",), lambda: chair(150))
    desks = [(160, "dev_f", False, 0.0), (520, "dev_m", False, .8), (1120, "dev_f", True, 1.6)]
    monpos = []
    for i, (hx, name, flip, off) in enumerate(desks):
        mx = hx + (170 if not flip else -170)
        mxx, myy = cam.p(mx, 880)
        mon = flat_monitor(250, t + off, "x" if i % 2 == 0 else "code", seed=i)
        put_icon(base, mon, mxx, myy, scale=cam.z * 1.0)
        monpos.append((mx, 880))
        sx, sy = cam.p(hx, 1090); put_icon(base, ch, sx, sy + 20 * cam.z, scale=cam.z * .9)
        place_person(base, name, seated(t, off, head=-2, turn=.1, smile=.2, eyes=blink(t, 3.2, off)), hx, 1030, cam, k=1.0, flip=flip)
    # Elon de pie junto a la pizarra, explica y señala
    up = ease(prog(t, .6, 1.4))
    pose = mk(smile=.5, sf=lerp(0, 120, up) + 6 * math.sin(t * 4) * up, ef=lerp(10, 20, up), turn=.2, mouth=.6 * up * (.5 + .5 * math.sin(t * 11)), brow=.3, eyes=blink(t, 3, .3), head=-3, lean=3, bx=0)
    pose["sb"] = 6; pose["eb"] = 14
    place_person(base, "elon_young", pose, 800, 1020, cam, k=1.05, flip=True)
    monpos.append((800, 880))
    # pagos digitales: monedas/sobres que viajan entre monitores
    cn = cached(("coin",), lambda: coin_icon(26))
    for q in range(5):
        a = monpos[q % 3]; b = monpos[(q + 1) % 3]
        u = ((t * .5 + q * .21) % 1.0)
        pa, pb = cam.p(*a), cam.p(*b)
        x, y = arc_pt(pa, pb, u, 280 * cam.z)
        put_icon(base, cn, x, y, scale=.9 + .2 * math.sin(u * 3.14) , alpha=min(1, u * 6, (1 - u) * 6))
        f.L.ellipse([x - 40, y - 40, x + 40, y + 40], fill=sc((255, 220, 120), .06))
    return cam


def sub_ebay(t, base, f):
    C = build()
    cam = Cam(540, 1020, 1.0 + .06 * prog(t, 0, 3.6))
    C["E"].blit(base, cam)
    hs = ease(prog(t, 1.0, 1.6))
    place_person(base, "exec1", mk(sf=lerp(0, 76, hs), ef=lerp(10, 4, hs), smile=.5, turn=.2, head=-2, eyes=blink(t, 3.3)), 770, 1200, cam, k=1.0, flip=True)
    place_person(base, "elon_young", mk(sf=lerp(0, 76, hs), ef=lerp(10, 4, hs), smile=.6, turn=.2, head=2, eyes=blink(t, 3.0, .6), lean=3 * hs), 420, 1200, cam, k=1.0)
    place_person(base, "dev_m", mk(smile=.7, sf=-5, eb=10, eyes=blink(t, 3.2, 1)), 250, 1200, cam, k=1.0)
    place_person(base, "exec2", mk(smile=.5, sf=-8, ef=30, eyes=blink(t, 3.5, .2)), 920, 1200, cam, k=1.0, flip=True)
    # 2002 y cifra
    ya = ease_back(prog(t, .2, .8))
    im = text_img("2002", 120, (255, 214, 120), stroke=8, stroke_col=(20, 24, 50))
    if ya > .05: paste_np(base, im.resize((max(int(im.width * ya), 2), max(int(im.height * ya), 2)), Image.LANCZOS), 540 - im.width * ya / 2, 560 - im.height * ya / 2, ya)
    k = ease_out(prog(t, 1.4, 3.0))
    if k > .02:
        val = int(1500 * k)
        pill = text_img(f"US$ {val:,}".replace(",", ".") + " millones", 64, (255, 255, 255), stroke=7, stroke_col=(20, 80, 40))
        paste_np(base, pill, 540 - pill.width / 2, 700 - 30 * ease_out(prog(t, 1.4, 2.0)) , ease(prog(t, 1.4, 1.9)))
    cn = cached(("coin",), lambda: coin_icon(30))
    for q in range(14):
        u = prog(t, 1.8 + q * .06, 3.3)
        if 0 < u < 1:
            put_icon(base, cn, 560 + (q - 7) * 50, 1000 - 500 * ease_out(u) + 620 * u * u * .3, scale=.7 + .4 * (q % 3) / 2, alpha=1 - u ** 2)


def scene(t):
    f = Frame(bg=False); base = f.base
    if t < 4.0:
        sub_office(t, base, f)
    elif t < 4.5:
        # X.com -> PayPal con destello
        sub_office(t, base, f, logo2=ease(prog(t, 4.0, 4.4)))
        base += 90 * math.sin(math.pi * prog(t, 4.0, 4.5))
    elif t < 7.2:
        sub_office(t, base, f, logo2=1.0)
        # festejo: salto de equipo
    elif t < 7.7:
        a = np.zeros_like(base); b = np.zeros_like(base)
        fa = Frame(bg=False); fb = Frame(bg=False)
        sub_office(t, a, fa, logo2=1.0); sub_ebay(t - 7.2, b, fb)
        base[:] = slide_blend(a, b, (t - 7.2) / .5, 1)
    else:
        sub_ebay(t - 7.2, base, f)
    dust(f, t, seed=10, n=26, tint=(200, 230, 255), alpha=.3)
    return f.finish()
