"""Escena 7 — Cierre: horizonte, cámara que se aleja y marca Explora Ciencia 360."""
from kit import *
from m1 import skyline, rocket_icon
from people import blend as blend_pose
_c = {}
LW, LH = 1600, 2100


def build():
    if "S" in _c: return _c
    def sky(p):
        p.vgrad(0, 0, LW, LH, [(0, (30, 36, 96)), (.35, (140, 84, 140)), (.55, (255, 150, 100)), (.7, (255, 206, 140)), (1, (255, 226, 170))])
        p.ell(1000, 1180, 170, 170, (255, 244, 210)); p.ell(1000, 1180, 300, 300, (255, 230, 180, 70))
        for (cx, cy, s_) in ((300, 420, 1.3), (900, 300, 1.0), (1300, 560, 1.2), (500, 760, 1.0)):
            for dx, dy, r in ((-60, 8, 50), (0, -14, 66), (70, 6, 54), (16, 14, 56)):
                p.ell(cx + dx * s_, cy + dy * s_, r * s_, r * .5 * s_, (255, 190, 170, 110))
    def far(p):
        skyline(p, LW, LH, 1330, 31, (150, 96, 140, 255), (255, 220, 160), 120, 380, 50, 100, .2)
        p.poly([(0, 1330), (300, 1250), (700, 1300), (1100, 1230), (1600, 1310), (1600, 1400), (0, 1400)], (122, 76, 124))
    def hill(p):
        p.poly([(0, 1560), (300, 1500), (700, 1470), (1100, 1500), (1600, 1540), (1600, 2100), (0, 2100)], (70, 52, 88))
        p.poly([(0, 1640), (400, 1590), (800, 1600), (1200, 1580), (1600, 1620), (1600, 2100), (0, 2100)], (46, 36, 68))
        for xx in range(60, 1600, 170): p.ell(xx, 1618 + (xx % 3) * 8, 30, 14, (58, 44, 80))
    _c["S"] = Layer(bake(LW, LH, sky), LW, LH, ox=-260, oy=-90, par=.3, zpar=.35)
    _c["F"] = Layer(bake(LW, LH, far), LW, LH, ox=-260, oy=-90, par=.5, zpar=.55)
    _c["H"] = Layer(bake(LW, LH, hill), LW, LH, ox=-260, oy=-90, par=.85, zpar=.9)
    return _c


def logo(base, f, t, a):
    """Marca: órbitas atómicas + wordmark + mensaje."""
    cx, cy = 540, 800
    lay = Image.new("RGB", (W, H), (0, 0, 0)); d = ImageDraw.Draw(lay)
    for k in range(3):
        ang = math.radians(60 * k) + t * .35
        pts = []
        for i in range(91):
            u = i / 90 * 2 * math.pi
            ex, ey = 250 * math.cos(u), 86 * math.sin(u)
            pts.append((cx + ex * math.cos(ang) - ey * math.sin(ang), cy + ex * math.sin(ang) + ey * math.cos(ang)))
        d.line(pts, fill=sc(mix(CYAN, VIOLET, k / 2), .9 * a), width=6, joint="curve")
        e = (t * (.6 + .15 * k) + k / 3) % 1.0; px, py = pts[int(e * 89)]
        d.ellipse([px - 12, py - 12, px + 12, py + 12], fill=sc(WHITE, a))
    rr = 58 * (1 + .05 * math.sin(t * 4))
    for i in range(10):
        r = rr * (1 - i / 10); d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=sc(mix(BLUE, (255, 200, 90), i / 9), .95 * a))
    d.ellipse([cx - rr * .32, cy - rr * .32, cx + rr * .32, cy + rr * .32], fill=(0, 0, 0))
    f.add_glow_layer(lay, 16, 1.0)
    return lay


def scene(t):
    C = build()
    f = Frame(bg=False); base = f.base
    zt = ease_io(prog(t, 0, 7.5))
    cam = Cam(lerp(700, 700, zt), lerp(1420, 1030, zt), lerp(1.5, .86, zt))
    for k in ("S", "F", "H"): C[k].blit(base, cam)
    # cohete lejano despegando (estela)
    u = prog(t, 1.0, 9.0)
    rx, ry = cam.p(1280, 1500 - 700 * ease_in(u), .6)
    for j in range(26):
        v = j / 26
        px, py = cam.p(1280 + 6 * math.sin(j + t * 3), 1500 - 700 * ease_in(u) + 40 * j * (1 + .4 * u), .6)
        r = 4 + 14 * v
        f.L.ellipse([px - r, py - r, px + r, py + r], fill=sc((255, 236, 214), .45 * (1 - v) * ease(prog(t, .6, 1.4))))
    f.L.ellipse([rx - 8, ry - 8, rx + 8, ry + 8], fill=sc((255, 240, 200), ease(prog(t, .6, 1.4))))
    # pájaros
    for i in range(5):
        bx = (200 + i * 150 + t * 40) % 1400 - 100; by = 500 + 40 * math.sin(t * 2 + i) + i * 30
        sx, sy = cam.p(bx, by, .7)
        w_ = 16 * cam.z
        f.L.line([(sx - w_, sy + 4 * math.sin(t * 8 + i)), (sx, sy - 6 + 3 * math.sin(t * 8 + i)), (sx + w_, sy + 4 * math.sin(t * 8 + i))], fill=sc((70, 40, 70), .9), width=3)
    # Elon mirando al horizonte (manos en los bolsillos), brisa en el cabello/ropa -> leve oscilación
    look = ease(prog(t, 0, 2.0))
    pose = mk(turn=.1, smile=.35, head=lerp(2, -4, look), lookx=1.6, looky=-.3, eyes=blink(t, 3.5, .3), sf=14, ef=40, sb=10, eb=40, lean=1 + .6 * math.sin(t * .7), bob=1.5 * math.sin(t * 1.2), brow=.1)
    place_person(base, "elon_adult", pose, 560, 1590, cam, k=1.25, depth=1.0)
    # luz cálida a contraluz
    for i in range(6):
        f.L.polygon([(1000, 1180), (-200, 700 + i * 110), (-200, 760 + i * 110)], fill=sc((255, 200, 130), .05))
    clouds(f, t, seed=5, n=5, y0=200, y1=700, col=(255, 190, 170), alpha=.15)
    dust(f, t, seed=14, n=36, tint=(255, 220, 170), alpha=.5)
    # transición a la marca
    ba = ease(prog(t, 5.8, 6.8))
    out_base = f.base
    if ba > 0:
        out_base *= (1 - .78 * ba)
        logo(base, f, t - 6.0, ba)
    out = f.finish()
    if ba > 0:
        lay2 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        n1 = text_img("EXPLORA", 140, WHITE, stroke=0); n2 = text_img("CIENCIA 360", 84, CYAN, stroke=0)
        # wordmark con aparición por letras
        def spaced(img_txt, size, color, y, sp, t0):
            fo = ImageFont.truetype(FONT_BOLD, size); widths = [fo.getlength(c) for c in img_txt]
            total = sum(widths) + sp * (len(img_txt) - 1); x = 540 - total / 2
            for i, c in enumerate(img_txt):
                a_ = ease(prog(t, t0 + i * .05, t0 + .4 + i * .05))
                if a_ > .01:
                    ci = text_img(c, size, color)
                    paste_np(out, ci, x - 6, y + (1 - a_) * 30, a_)
                x += widths[i] + sp
        spaced("EXPLORA", 140, (240, 248, 255), 950, 10, 7.5)
        spaced("CIENCIA 360", 84, (54, 214, 255), 1110, 14, 7.9)
        cta = ease(prog(t, 8.7, 9.4))
        if cta > .01:
            pill = Image.new("RGBA", (560, 120), (0, 0, 0, 0)); pd = ImageDraw.Draw(pill)
            pd.rounded_rectangle([0, 0, 559, 119], radius=60, fill=(255, 190, 70, 255))
            pd.text((280, 60), "SÍGUENOS", font=ImageFont.truetype(FONT_BOLD, 54), fill=(30, 24, 50, 255), anchor="mm")
            sc_ = 1 + .04 * math.sin(t * 5)
            pill = pill.resize((int(560 * sc_), int(120 * sc_)), Image.LANCZOS)
            paste_np(out, pill, 540 - pill.width / 2, 1290 - pill.height / 2 + (1 - cta) * 30, cta)
    return out
