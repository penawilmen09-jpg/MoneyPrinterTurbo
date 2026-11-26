"""Kit de oficinas / salas y utilidades de sub-escenas."""
from stage import *
from stage import _font
from props import *

SEAT = dict(lean=8, hf=86, kf=84, hb=82, kb=80, sf=62, ef=18, sb=58, eb=22)

def seated(t, ph=0.0, **kw):
    a = t * 9 + ph
    p = mk(**SEAT); p["sf"] += 2 * math.sin(a); p["ef"] += 5 * math.sin(a * 1.3); p["eb"] += 4 * math.sin(a + 1)
    p.update(kw); return p


def slide_blend(A, B, p, direction=1):
    e = ease_io(p)
    sh = int(W * e)
    out = np.empty_like(A)
    if direction > 0:
        out[:, :W - sh] = A[:, sh:]; out[:, W - sh:] = B[:, :sh]
    else:
        out[:, sh:] = A[:, :W - sh]; out[:, :sh] = B[:, W - sh:]
    return out


def office_bg(p, LW, LH, wall=(224, 210, 186), floor=(120, 104, 96), window=True, sign=None, whiteboard=True, theme="zip"):
    p.vgrad(0, 0, LW, 1260, [(0, wall), (1, shade(wall, .86))])
    p.rect(0, 1260, LW, LH, floor)
    for xx in range(0, LW, 160): p.rect(xx, 1260, xx + 3, LH, shade(floor, .86))
    p.rect(0, 1248, LW, 1266, shade(wall, .6))
    if window:
        for (x, y, w_, h_) in ((60, 300, 300, 520), (LW - 380, 300, 300, 520)):
            p.rect(x, y, x + w_, y + h_, (90, 90, 100))
            p.vgrad(x + 10, y + 10, x + w_ - 10, y + h_ - 10, [(0, (150, 200, 245)), (1, (214, 232, 248))])
            rng = np.random.RandomState(x)
            xx = x + 10
            while xx < x + w_ - 40:
                bw = rng.randint(36, 70); bh = rng.randint(120, 330)
                p.rect(xx, y + h_ - 10 - bh, xx + bw, y + h_ - 10, (120, 140, 176)); xx += bw + 4
            p.rect(x + w_ / 2 - 3, y + 10, x + w_ / 2 + 3, y + h_ - 10, (90, 90, 100))
    if whiteboard:
        bx = LW / 2 - 260
        p.rrect(bx, 330, bx + 520, 700, 10, (248, 248, 250), (150, 150, 160), 8)
        if theme == "zip":
            p.line([(bx + 40, 640), (bx + 150, 560), (bx + 220, 600), (bx + 330, 480), (bx + 470, 520)], (60, 120, 220), 7)
            for (x, y) in ((bx + 150, 560), (bx + 330, 480)): p.ell(x, y, 14, 14, (230, 70, 70))
            p.rect(bx + 40, 380, bx + 230, 410, (120, 190, 120)); p.rect(bx + 40, 430, bx + 170, 452, (190, 190, 200)); p.rect(bx + 40, 468, bx + 200, 490, (190, 190, 200))
        else:
            p.text(bx + 260, 520, "X", 220, (60, 120, 220), anchor="mm")
    if sign:
        p.rrect(LW / 2 - 200, 150, LW / 2 + 200, 270, 24, (28, 34, 70), (255, 200, 90), 6)
        p.text(LW / 2, 212, sign, 88, (255, 214, 120), anchor="mm")
    # plantas
    for x in (28, LW - 60):
        p.rrect(x, 1130, x + 40, 1260, 8, (140, 92, 70))
        for a in (-40, -20, 0, 20, 40):
            p.poly([(x + 20, 1130), (x + 20 + a * 1.4, 1030 - abs(a)), (x + 20 + a * .4, 1130)], (60, 150, 90))


def desk_row(p, x0, x1, y, col=(160, 120, 84)):
    p.rect(x0, y, x1, y + 28, col); p.rect(x0 + 20, y + 28, x0 + 44, 1260, shade(col, .8)); p.rect(x1 - 44, y + 28, x1 - 20, 1260, shade(col, .8))
