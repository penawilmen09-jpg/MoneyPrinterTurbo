"""Utilería para el documental de Amazon (iconos vectoriales 2D)."""
from kit import *
from props import cached, coin_icon

CARD = (196, 150, 98)

def box_icon(w=150, tape=True, label=True, col=CARD):
    h = int(w * .8)
    def fn(p):
        s = w / 150.0
        p.poly([(0, 30 * s), (150 * s, 30 * s), (150 * s, 120 * s), (0, 120 * s)], col)
        p.poly([(0, 30 * s), (30 * s, 0), (120 * s, 0), (150 * s, 30 * s)], shade(col, 1.15))
        p.rect(0, 108 * s, 150 * s, 120 * s, shade(col, .82))
        if tape: p.rect(62 * s, 0, 88 * s, 120 * s, (226, 206, 150))
        if label: p.rect(98 * s, 62 * s, 140 * s, 96 * s, (250, 250, 250)); p.rect(104 * s, 70 * s, 134 * s, 74 * s, (60, 60, 70)); p.rect(104 * s, 80 * s, 124 * s, 84 * s, (60, 60, 70))
    return icon_rgba(w, int(w * .8), fn)


def book_icon(w=90, col=(210, 70, 70)):
    def fn(p):
        s = w / 90.0
        p.rrect(0, 0, 70 * s, 100 * s, 5 * s, col); p.rect(0, 0, 10 * s, 100 * s, shade(col, .7))
        p.rect(18 * s, 20 * s, 58 * s, 28 * s, (250, 240, 200)); p.rect(18 * s, 38 * s, 46 * s, 44 * s, (250, 240, 200))
        p.rect(70 * s, 6 * s, 82 * s, 96 * s, (244, 240, 226))
    return icon_rgba(w, int(w * 1.1), fn)


def product(kind, w=110):
    h = w
    def fn(p):
        s = w / 110.0
        if kind == "headphones":
            p.arc((14 * s, 6 * s, 96 * s, 88 * s), 180, 360, (60, 64, 80), 9 * s); p.rrect(8 * s, 50 * s, 32 * s, 88 * s, 8 * s, (60, 64, 80)); p.rrect(78 * s, 50 * s, 102 * s, 88 * s, 8 * s, (60, 64, 80))
            p.rrect(12 * s, 56 * s, 28 * s, 84 * s, 6 * s, (230, 70, 90)); p.rrect(82 * s, 56 * s, 98 * s, 84 * s, 6 * s, (230, 70, 90))
        elif kind == "laptop":
            p.rrect(18 * s, 12 * s, 92 * s, 70 * s, 6 * s, (70, 76, 92)); p.rect(24 * s, 18 * s, 86 * s, 64 * s, (110, 190, 240)); p.poly([(4 * s, 78 * s), (106 * s, 78 * s), (98 * s, 92 * s), (12 * s, 92 * s)], (170, 176, 190))
        elif kind == "shirt":
            p.poly([(30 * s, 12 * s), (80 * s, 12 * s), (104 * s, 30 * s), (92 * s, 48 * s), (82 * s, 40 * s), (82 * s, 98 * s), (28 * s, 98 * s), (28 * s, 40 * s), (18 * s, 48 * s), (6 * s, 30 * s)], (80, 150, 230)); p.arc((44 * s, 4 * s, 66 * s, 30 * s), 0, 180, (60, 120, 200), 4 * s)
        elif kind == "shoe":
            p.poly([(8 * s, 60 * s), (30 * s, 60 * s), (48 * s, 40 * s), (96 * s, 70 * s), (104 * s, 90 * s), (8 * s, 90 * s)], (240, 240, 244)); p.rect(8 * s, 84 * s, 104 * s, 94 * s, (230, 90, 60)); p.line([(48 * s, 46 * s), (70 * s, 62 * s)], (150, 150, 160), 3 * s)
        elif kind == "toy":
            p.ell(55 * s, 62 * s, 32 * s, 34 * s, (196, 140, 86)); p.ell(55 * s, 30 * s, 24 * s, 22 * s, (196, 140, 86)); p.ell(36 * s, 12 * s, 9 * s, 9 * s, (196, 140, 86)); p.ell(74 * s, 12 * s, 9 * s, 9 * s, (196, 140, 86))
            p.ell(48 * s, 28 * s, 3 * s, 3 * s, (30, 24, 24)); p.ell(62 * s, 28 * s, 3 * s, 3 * s, (30, 24, 24)); p.ell(55 * s, 36 * s, 5 * s, 4 * s, (60, 40, 30))
        elif kind == "watch":
            p.rect(40 * s, 4 * s, 70 * s, 104 * s, (60, 64, 80)); p.rrect(26 * s, 30 * s, 84 * s, 82 * s, 14 * s, (230, 232, 240)); p.rrect(32 * s, 36 * s, 78 * s, 76 * s, 10 * s, (20, 26, 50)); p.ell(55 * s, 56 * s, 5 * s, 5 * s, (110, 230, 160))
        elif kind == "game":
            p.rrect(6 * s, 28 * s, 104 * s, 76 * s, 24 * s, (80, 90, 120)); p.rect(24 * s, 46 * s, 44 * s, 52 * s, (230, 230, 240)); p.rect(31 * s, 39 * s, 37 * s, 60 * s, (230, 230, 240)); p.ell(80 * s, 44 * s, 6 * s, 6 * s, (240, 90, 90)); p.ell(92 * s, 56 * s, 6 * s, 6 * s, (90, 200, 120))
        elif kind == "lamp":
            p.poly([(32 * s, 8 * s), (78 * s, 8 * s), (92 * s, 50 * s), (18 * s, 50 * s)], (250, 210, 90)); p.rect(52 * s, 50 * s, 58 * s, 90 * s, (90, 90, 100)); p.rrect(30 * s, 90 * s, 80 * s, 100 * s, 4 * s, (90, 90, 100))
    return icon_rgba(w, h, fn)


PRODUCTS = ["headphones", "laptop", "shirt", "shoe", "toy", "watch", "game", "lamp"]


def phone_icon(w=380, t=0.0, tap=-1, bought=0.0):
    h = int(w * 1.95)
    def fn(p):
        s = w / 380.0
        p.rrect(0, 0, 380 * s, 740 * s, 56 * s, (24, 26, 36)); p.rrect(14 * s, 14 * s, 366 * s, 726 * s, 44 * s, (246, 248, 252))
        p.rrect(130 * s, 26 * s, 250 * s, 44 * s, 10 * s, (24, 26, 36))
        p.rrect(34 * s, 70 * s, 346 * s, 118 * s, 16 * s, (230, 236, 246)); p.text(190 * s, 96 * s, "buscar…", int(26 * s), (150, 156, 176), anchor="mm", bold=False)
        for i in range(6):
            r, c = divmod(i, 2); x = 36 * s + c * 160 * s; y = 150 * s + r * 190 * s
            hl = (tap == i)
            p.rrect(x, y, x + 150 * s, y + 176 * s, 18 * s, (255, 236, 200) if hl else (238, 242, 250))
            p.rrect(x + 22 * s, y + 130 * s, x + 128 * s, y + 160 * s, 10 * s, (255, 170, 40) if hl else (70, 130, 230))
        p.rrect(34 * s, 700 * s, 346 * s, 730 * s, 12 * s, (70, 130, 230)) if False else None
    im = icon_rgba(w, h, fn)
    for i in range(6):
        r, c = divmod(i, 2); x = 36 * w / 380 + c * 160 * w / 380; y = 150 * w / 380 + r * 190 * w / 380
        pi = cached(("prod", PRODUCTS[i], 96), lambda i=i: product(PRODUCTS[i], 96)); sc_ = w / 380
        pi2 = pi.resize((int(96 * sc_ * 1.0), int(96 * sc_ * 1.0)), Image.LANCZOS)
        im.alpha_composite(pi2, (int(x + 27 * sc_), int(y + 12 * sc_)))
    return im


def truck_icon(w=560, wheel=0.0, col=(240, 240, 244), label=True):
    h = int(w * .5)
    def fn(p):
        s = w / 560.0
        p.rrect(0, 20 * s, 380 * s, 230 * s, 14 * s, col); p.rect(0, 190 * s, 380 * s, 206 * s, shade(col, .78))
        p.poly([(380 * s, 70 * s), (470 * s, 70 * s), (540 * s, 140 * s), (550 * s, 230 * s), (380 * s, 230 * s)], (232, 150, 40))
        p.poly([(400 * s, 86 * s), (462 * s, 86 * s), (516 * s, 140 * s), (400 * s, 140 * s)], (140, 200, 240))
        p.rect(0, 232 * s, 550 * s, 246 * s, (60, 62, 74))
        if label: p.text(190 * s, 112 * s, "ENVÍOS", int(64 * s), (40, 90, 170), anchor="mm")
        p.line([(40 * s, 150 * s), (340 * s, 150 * s)], (40, 90, 170), 8 * s)
        for cx in (110, 430):
            p.ell(cx * s, 246 * s, 40 * s, 40 * s, (26, 26, 32)); p.ell(cx * s, 246 * s, 24 * s, 24 * s, (190, 194, 206))
            for k in range(4):
                a = wheel + k * math.pi / 2; p.line([(cx * s, 246 * s), ((cx + 22 * math.cos(a)) * s, (246 + 22 * math.sin(a)) * s)], (100, 104, 116), 5 * s)
        p.ell(545 * s, 214 * s, 10 * s, 7 * s, (255, 244, 190))
    return icon_rgba(w, int(w * .5), fn)


def plane_icon(w=640, prop=0.0):
    h = int(w * .34)
    def fn(p):
        s = w / 640.0
        p.poly([(40 * s, 130 * s), (120 * s, 90 * s), (520 * s, 90 * s), (600 * s, 120 * s), (620 * s, 140 * s), (520 * s, 170 * s), (120 * s, 170 * s)], (246, 248, 252))
        p.poly([(40 * s, 130 * s), (10 * s, 30 * s), (70 * s, 30 * s), (150 * s, 110 * s)], (232, 150, 40))
        p.poly([(260 * s, 150 * s), (340 * s, 150 * s), (250 * s, 240 * s), (200 * s, 240 * s)], (200, 206, 220))
        p.poly([(300 * s, 100 * s), (370 * s, 100 * s), (300 * s, 20 * s), (250 * s, 20 * s)], (206, 212, 226))
        p.rrect(300 * s, 168 * s, 350 * s, 190 * s, 8 * s, (150, 156, 170)); p.rrect(180 * s, 168 * s, 230 * s, 190 * s, 8 * s, (150, 156, 170))
        for x in range(180, 520, 36): p.ell(x * s, 120 * s, 7 * s, 7 * s, (120, 170, 220))
        p.poly([(540 * s, 110 * s), (600 * s, 118 * s), (610 * s, 132 * s), (540 * s, 132 * s)], (130, 190, 240))
        p.rect(0, 136 * s, 640 * s, 140 * s, (0, 0, 0, 0)) if False else None
    return icon_rgba(w, h, fn)


def robot_icon(w=170, shelf=True):
    h = int(w * .9)
    def fn(p):
        s = w / 170.0
        p.rrect(10 * s, 94 * s, 160 * s, 130 * s, 12 * s, (255, 140, 40)); p.ell(40 * s, 134 * s, 12 * s, 12 * s, (40, 44, 56)); p.ell(130 * s, 134 * s, 12 * s, 12 * s, (40, 44, 56))
        p.rect(70 * s, 100 * s, 110 * s, 108 * s, (80, 230, 150))
        if shelf:
            p.rect(20 * s, 20 * s, 150 * s, 94 * s, (120, 130, 150)); p.rect(20 * s, 20 * s, 150 * s, 28 * s, (170, 178, 196))
            for i in range(3): p.rect((26 + i * 42) * s, 36 * s, (60 + i * 42) * s, 90 * s, [(200, 150, 100), (90, 160, 220), (230, 200, 100)][i])
    return icon_rgba(w, h, fn)


def rack_icon(w=170, t=0.0, seed=0):
    h = int(w * 1.7)
    def fn(p):
        s = w / 170.0
        p.rrect(0, 0, 170 * s, 290 * s, 8 * s, (44, 52, 72)); p.rect(10 * s, 10 * s, 160 * s, 280 * s, (26, 32, 48))
        rng = np.random.RandomState(seed)
        for i in range(9):
            y = (18 + i * 29) * s
            p.rect(16 * s, y, 154 * s, y + 22 * s, (60, 70, 96))
            for k in range(6):
                on = math.sin(t * 6 + i * 1.3 + k * 2.1 + seed) > .1
                p.ell((30 + k * 10) * s, y + 11 * s, 3.2 * s, 3.2 * s, (90, 240, 150) if on else (30, 80, 60))
            p.rect(100 * s, y + 7 * s, 148 * s, y + 15 * s, (40, 46, 66))
    return icon_rgba(w, int(w * 1.7), fn)


def cloud_icon(w=260, col=(255, 255, 255)):
    h = int(w * .6)
    def fn(p):
        s = w / 260.0
        for (x, y, r) in ((70, 110, 52), (120, 76, 66), (176, 100, 56), (210, 120, 40), (130, 120, 70)): p.ell(x * s, y * s, r * s, r * s, col)
        p.rrect(40 * s, 110 * s, 230 * s, 160 * s, 24 * s, col)
    return icon_rgba(w, int(w * .65), fn)


def shelf_unit(p, x, y, w, h, rows=4, seed=1):
    rng = np.random.RandomState(seed)
    p.rect(x, y, x + 10, y + h, (70, 90, 130)); p.rect(x + w - 10, y, x + w, y + h, (70, 90, 130))
    for r in range(rows + 1): p.rect(x, y + r * h / rows, x + w, y + r * h / rows + 8, (230, 150, 50))
    for r in range(rows):
        cx = x + 14
        while cx < x + w - 50:
            bw = rng.randint(34, 64); bh = rng.randint(28, int(h / rows) - 18)
            p.rect(cx, y + (r + 1) * h / rows - bh, cx + bw, y + (r + 1) * h / rows, [(196, 150, 98), (170, 126, 80), (210, 170, 120), (90, 150, 220), (230, 200, 100)][rng.randint(0, 5)]); cx += bw + 6


USA = [(.02,.08),(.2,.05),(.38,.06),(.5,.05),(.62,.06),(.7,.09),(.78,.14),(.86,.1),(.92,.04),(.95,.16),(.9,.26),(.9,.36),(.88,.45),(.84,.6),(.86,.78),(.9,.98),(.82,.9),(.76,.7),(.7,.66),(.62,.68),(.52,.64),(.46,.9),(.4,.74),(.3,.72),(.2,.62),(.08,.5),(.04,.3)]
