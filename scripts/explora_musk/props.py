"""Utilería 2D reutilizable (iconos vectoriales RGBA)."""
from stage import *

_pc = {}
def cached(key, fn):
    if key not in _pc: _pc[key] = fn()
    return _pc[key]


def crt(w=300, screen=(20, 40, 24), body=(222, 214, 190)):
    h = int(w * .95)
    def fn(p):
        s = w / 300.0
        p.rrect(10 * s, 6 * s, 290 * s, 230 * s, 22 * s, body)
        p.rrect(30 * s, 24 * s, 270 * s, 200 * s, 14 * s, (60, 58, 52))
        p.rect(110 * s, 230 * s, 190 * s, 258 * s, shade(body, .9))
        p.rrect(60 * s, 258 * s, 240 * s, 282 * s, 10 * s, body)
        p.ell(262 * s, 216 * s, 5 * s, 5 * s, (90, 220, 90))
    return icon_rgba(w, h, fn)


def keyboard(w=220):
    def fn(p):
        s = w / 220.0
        p.rrect(0, 14 * s, 220 * s, 44 * s, 6 * s, (206, 198, 176))
        for r in range(2):
            for c in range(14):
                p.rect((8 + c * 15) * s, (19 + r * 12) * s, (20 + c * 15) * s, (28 + r * 12) * s, (236, 230, 212))
    return icon_rgba(w, int(w * .24), fn)


def screen_code(w, h, t, seed=1, color=(90, 255, 120), game=0.0):
    """Contenido de la pantalla: código que se escribe o minijuego."""
    im = Image.new("RGB", (w, h), (8, 20, 12))
    d = ImageDraw.Draw(im)
    if game < .5:
        rng = np.random.RandomState(seed)
        nlines = 11
        for i in range(nlines):
            ln = i - int(t * 2.4) % nlines
            y = 8 + i * (h - 16) / nlines
            L_ = rng.randint(30, w - 40); ind = (rng.randint(0, 3)) * 16
            vis = clamp(t * 2.4 - i * .0, 0, 1)
            d.rectangle([10 + ind, y, 10 + ind + L_ * (0.4 + 0.6 * ((t * 1.7 + i * .37) % 1)), y + 7], fill=color if i % 3 else (255, 210, 90))
        if int(t * 3) % 2 == 0: d.rectangle([w - 30, h - 24, w - 18, h - 10], fill=color)
    else:
        rng = np.random.RandomState(2)
        # minijuego espacial: nave y alienígenas
        d.rectangle([0, 0, w, h], fill=(6, 8, 30))
        for i in range(24): d.point((rng.randint(0, w), (rng.randint(0, h) + int(t * 40)) % h), fill=(200, 200, 255))
        for r in range(3):
            for c in range(6):
                ax = 20 + c * (w - 40) / 6 + 14 * math.sin(t * 2 + r)
                ay = 18 + r * 26 + 6 * math.sin(t * 3 + c)
                d.rectangle([ax, ay, ax + 18, ay + 10], fill=(255, 90, 120)); d.rectangle([ax + 4, ay - 4, ax + 14, ay], fill=(255, 90, 120))
        shipx = w / 2 + (w * .3) * math.sin(t * 1.5)
        d.polygon([(shipx, h - 34), (shipx - 14, h - 10), (shipx + 14, h - 10)], fill=(90, 220, 255))
        by = h - 40 - ((t * 160) % (h - 50))
        d.rectangle([shipx - 2, by, shipx + 2, by + 12], fill=(255, 240, 120))
    return im


def desk_set(t, typing=1.0, game=0.0, seed=1, w=300):
    """Monitor CRT con pantalla animada."""
    base = cached(("crt", w), lambda: crt(w)).copy()
    sw, sh_ = int(w * .76), int(w * .5)
    scr = screen_code(sw, sh_, t, seed, game=game).convert("RGBA")
    # esquinas redondeadas
    m = Image.new("L", scr.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, sw, sh_], radius=12, fill=255); scr.putalpha(m)
    base.alpha_composite(scr, (int(w * .1), int(w * .08)))
    return base


def flat_monitor(w=220, t=0, content="x", seed=1):
    h = int(w * .75)
    def fn(p):
        s = w / 220.0
        p.rrect(0, 0, 220 * s, 150 * s, 10 * s, (40, 44, 56))
        p.rrect(8 * s, 8 * s, 212 * s, 140 * s, 6 * s, (18, 30, 56))
        p.rect(100 * s, 150 * s, 120 * s, 170 * s, (70, 74, 86)); p.rrect(70 * s, 168 * s, 150 * s, 176 * s, 4 * s, (70, 74, 86))
    im = icon_rgba(w, h, fn)
    d = ImageDraw.Draw(im)
    if content == "x":
        xc = (80, 160, 255)
        d.line([(w * .35, h * .2), (w * .65, h * .6)], fill=xc, width=int(w * .06)); d.line([(w * .65, h * .2), (w * .35, h * .6)], fill=xc, width=int(w * .06))
    elif content == "code":
        rng = np.random.RandomState(seed)
        for i in range(7):
            d.rectangle([w * .1, h * .16 + i * h * .075, w * .1 + rng.randint(30, int(w * .7)) * (.5 + .5 * ((t * 1.3 + i * .3) % 1)), h * .16 + i * h * .075 + 5], fill=(110, 230, 150))
    return im


def chair(w=150, color=(60, 70, 96)):
    def fn(p):
        s = w / 150.0
        p.rrect(10 * s, 0, 140 * s, 22 * s, 8 * s, color)
        p.rrect(0, -70 * s, 22 * s, 6 * s, 8 * s, color) if False else None
        p.rect(66 * s, 22 * s, 84 * s, 80 * s, (50, 52, 62))
        for dx in (-50, -20, 0, 20, 50): p.line([(75 * s, 80 * s), ((75 + dx) * s, 100 * s)], (50, 52, 62), 6 * s)
        for dx in (-50, 50): p.ell((75 + dx) * s, 104 * s, 9 * s, 9 * s, (30, 30, 36))
    return icon_rgba(w, int(w * .72), fn)


def coin_icon(r=28):
    def fn(p):
        p.ell(r, r, r - 2, r - 2, (255, 200, 70), (255, 240, 150), 3)
        p.text(r, r, "$", int(r * 1.3), (150, 96, 10), anchor="mm")
    return icon_rgba(2 * r, 2 * r, fn)


def money_bag(w=120):
    def fn(p):
        s = w / 120.0
        p.ell(60 * s, 76 * s, 46 * s, 40 * s, (96, 170, 96))
        p.poly([(38 * s, 40 * s), (82 * s, 40 * s), (70 * s, 60 * s), (50 * s, 60 * s)], (96, 170, 96))
        p.rrect(40 * s, 34 * s, 80 * s, 46 * s, 5 * s, (70, 130, 70))
        p.text(60 * s, 78 * s, "$", int(50 * s), (240, 255, 220), anchor="mm")
    return icon_rgba(w, int(w * .95), fn)


def check_icon(w=360, amount="$$$"):
    def fn(p):
        s = w / 360.0
        p.rrect(0, 0, 360 * s, 160 * s, 12 * s, (240, 246, 235), (90, 140, 100), 4)
        p.rect(20 * s, 30 * s, 160 * s, 40 * s, (190, 210, 190)); p.rect(20 * s, 60 * s, 120 * s, 68 * s, (200, 214, 200))
        p.text(180 * s, 100 * s, amount, int((46 if len(amount) < 8 else 27) * s), (40, 110, 60), anchor="mm")
        p.line([(220 * s, 140 * s), (330 * s, 140 * s)], (120, 140, 120), 3)
    return icon_rgba(w, int(w * .45), fn)


def window_box(p, x, y, w, h, sky=((20, 30, 70), (80, 60, 120))):
    p.rect(x, y, x + w, y + h, (90, 70, 56))
    p.vgrad(x + 8, y + 8, x + w - 8, y + h - 8, [(0, sky[0]), (1, sky[1])])
    p.rect(x + w / 2 - 3, y + 8, x + w / 2 + 3, y + h - 8, (90, 70, 56)); p.rect(x + 8, y + h / 2 - 3, x + w - 8, y + h / 2 + 3, (90, 70, 56))
