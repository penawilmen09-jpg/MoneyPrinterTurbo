"""Escena 6 — El imperio: patrimonio estimado (no efectivo)."""
from kit import *
from m1 import skyline, rocket_icon, car_icon
_c = {}
LW, LH = 1400, 1920


def build():
    if "B" in _c: return _c
    def campus(p):
        p.vgrad(0, 0, LW, LH, [(0, (22, 30, 78)), (.4, (110, 76, 140)), (.65, (250, 160, 110)), (1, (255, 200, 140))])
        p.ell(300, 960, 130, 130, (255, 232, 180))
        skyline(p, LW, LH, 1250, 21, (96, 78, 132, 255), (255, 224, 150), 200, 520, 70, 120, .35)
        # complejo tecnológico: torres de vidrio
        for (x0, w_, h_, c) in ((140, 240, 700, (60, 80, 140)), (400, 300, 860, (72, 96, 160)), (730, 240, 620, (58, 76, 132)), (1000, 280, 780, (68, 90, 150))):
            p.rect(x0, 1290 - h_, x0 + w_, 1290, c)
            for yy in range(int(1290 - h_ + 20), 1270, 34):
                p.rect(x0 + 12, yy, x0 + w_ - 12, yy + 18, shade(c, 1.35))
            p.rect(x0, 1290 - h_, x0 + w_, 1290 - h_ + 8, shade(c, .7))
        # edificios con rótulos
        p.rrect(170, 900, 550, 996, 18, (196, 30, 44)); p.text(360, 950, "TESLA", 80, (255, 255, 255), anchor="mm")
        p.rrect(780, 900, 1180, 996, 18, (20, 24, 40)); p.text(980, 950, "SPACEX", 80, (240, 244, 255), anchor="mm")
        p.rect(0, 1290, LW, LH, (58, 50, 84)); p.rect(0, 1290, LW, 1312, (100, 86, 126))
    _c["B"] = Layer(bake(LW, LH, campus), LW, LH, ox=-160, par=.6, zpar=.7)
    _c["rocket"] = rocket_icon(520)
    return _c


def fmt(n): return f"{n:,}".replace(",", ".")


def cert_icon(w=200):
    def fn(p):
        s = w / 200.0
        p.rrect(0, 0, 200 * s, 140 * s, 10 * s, (244, 240, 220), (150, 120, 60), 5)
        p.line([(26 * s, 100 * s), (70 * s, 76 * s), (104 * s, 90 * s), (170 * s, 36 * s)], (50, 140, 80), 8)
        p.rect(26 * s, 20 * s, 120 * s, 30 * s, (190, 180, 150))
        p.ell(160 * s, 108 * s, 20 * s, 20 * s, (210, 170, 60))
    return icon_rgba(w, int(w * .7), fn)


def cash_icon(w=200):
    def fn(p):
        s = w / 200.0
        p.rrect(0, 0, 200 * s, 100 * s, 10 * s, (110, 190, 120), (50, 120, 70), 5)
        p.ell(100 * s, 50 * s, 34 * s, 34 * s, (80, 160, 100)); p.text(100 * s, 52 * s, "$", int(56 * s), (230, 250, 230), anchor="mm")
    return icon_rgba(w, int(w * .5), fn)


def scene(t):
    C = build()
    f = Frame(bg=False); base = f.base
    cam = Cam(540, 1000, 1.0 + .07 * ease_io(prog(t, 0, 11.8)))
    C["B"].blit(base, cam)
    rk = C["rocket"]
    for (x, y) in ((470, 1300),):
        pass
    # Elon camina hacia el complejo y luego presenta con los brazos abiertos
    walk = 1 - ease(prog(t, 2.6, 3.4))
    ex = 300 + 120 * ease(prog(t, 0, 3.0))
    ph = (t * .75) % 1
    pres = ease(prog(t, 3.0, 3.8))
    pose = blend_pose(walk_pose(ph, speed=.8 * walk, smile=.4, head=-2, eyes=blink(t, 3.3)),
                      mk(sf=70, ef=-10, sb=-70, eb=0, smile=.8, brow=.3, head=-4, lean=-2, eyes=blink(t, 3.3), turn=.3, mouth=0), pres)
    place_person(base, "elon_adult", pose, ex, 1500, cam, k=1.25)
    # gráfico financiero sobre vidrio (3.4 →)
    ga = ease(prog(t, 3.4, 4.2)) * 1.0
    if ga > .01:
        gp = Image.new("RGBA", (900, 520), (0, 0, 0, 0)); gd = ImageDraw.Draw(gp)
        gd.rounded_rectangle([0, 0, 899, 519], radius=30, fill=(10, 18, 44, 170), outline=(120, 200, 255, 255), width=4)
        for i in range(1, 5): gd.line([(40, 40 + i * 90), (860, 40 + i * 90)], fill=(80, 120, 180, 120), width=2)
        pts = []
        u = prog(t, 3.8, 8.4)
        rng = np.random.RandomState(3)
        for i in range(0, 41):
            xx = 50 + i * 20
            v = (i / 40) ** 1.7 * 360 + 20 * math.sin(i * .9) * (i / 40)
            pts.append((xx, 470 - v))
        n = int(len(pts) * u)
        if n > 1:
            gd.line(pts[:n], fill=(255, 210, 90, 255), width=8)
            gd.ellipse([pts[n - 1][0] - 12, pts[n - 1][1] - 12, pts[n - 1][0] + 12, pts[n - 1][1] + 12], fill=(255, 255, 255, 255))
        paste_np(base, gp, 90, 100 - 30 * (1 - ga), ga * (1 - ease(prog(t, 7.7, 8.3))))
        # etiqueta + cifra creciente
        val = int(823500 * ease_out(prog(t, 4.3, 8.0)))
        num = text_img("US$ " + fmt(val) + " M", 78, (255, 214, 120), stroke=8, stroke_col=(20, 20, 50))
        paste_np(base, num, 540 - num.width / 2, 690, ga)
        lab = text_img("PATRIMONIO ESTIMADO", 50, (255, 255, 255), stroke=6, stroke_col=(20, 20, 50))
        paste_np(base, lab, 540 - lab.width / 2, 630, ga)
        src = text_img("según Forbes · 26 nov 2026", 40, (200, 230, 255), bold=False, stroke=5, stroke_col=(20, 20, 50))
        paste_np(base, src, 540 - src.width / 2, 800, ga)
    # aclaración: valor de participaciones, no efectivo (8.0 →)
    ca = ease(prog(t, 7.9, 8.8))
    if ca > .01:
        pan = Image.new("RGBA", (960, 400), (0, 0, 0, 0)); pd = ImageDraw.Draw(pan)
        pd.rounded_rectangle([0, 0, 959, 399], radius=34, fill=(10, 16, 40, 215), outline=(255, 214, 120, 255), width=4)
        cert = cached(("cert",), lambda: cert_icon(250)); cash = cached(("cash",), lambda: cash_icon(250))
        pan.alpha_composite(cert, (60, 60)); pan.alpha_composite(cash, (650, 90))
        pd.text((480, 175), "≠", font=ImageFont.truetype(FONT_BOLD, 130), fill=(255, 214, 120, 255), anchor="mm")
        f1 = ImageFont.truetype(FONT_BOLD, 34); f2 = ImageFont.truetype(FONT_MED, 30)
        pd.text((185, 290), "Valor de sus", font=f1, fill=(255, 255, 255, 255), anchor="mm"); pd.text((185, 330), "participaciones", font=f1, fill=(255, 255, 255, 255), anchor="mm")
        pd.text((775, 290), "No es dinero", font=f1, fill=(255, 255, 255, 255), anchor="mm"); pd.text((775, 330), "en efectivo", font=f1, fill=(255, 255, 255, 255), anchor="mm")
        # tachado sobre el efectivo
        if ca > .6:
            pd.line([(660, 80), (900, 230)], fill=(255, 80, 80, 255), width=12)
        paste_np(base, pan, 60, 110 - 30 * (1 - ca), ca)
    # humo/luz
    for i in range(4):
        a = .2 + i * .09
        f.L.polygon([(300, 900), (1300, 700 + i * 120), (1300, 760 + i * 120)], fill=sc((255, 210, 140), .06))
    dust(f, t, seed=13, n=40, tint=(255, 230, 180), alpha=.45)
    return f.finish()


from people import blend as blend_pose
from props import cached
