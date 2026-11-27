"""Escena 7 (65.25–77.5): cierre — la cámara se aleja del enorme almacén, un camión sale y aparece la marca Explora Ciencia 360."""
from amz import *
from m7 import logo
DUR = 12.25
_c = {}
LW, LH = 1700, 2100


def build():
    if "C" in _c: return _c
    def campus(p):
        p.vgrad(0, 0, LW, LH, [(0, (22, 30, 78)), (.35, (110, 76, 140)), (.55, (250, 150, 105)), (.7, (255, 206, 140)), (1, (255, 226, 170))])
        p.ell(1150, 1100, 150, 150, (255, 240, 200)); p.ell(1150, 1100, 280, 280, (255, 226, 170, 60))
        for (cx, cy, s_) in ((300, 420, 1.3), (900, 300, 1.0), (1450, 520, 1.2)):
            for dx, dy, r in ((-60, 8, 50), (0, -14, 66), (70, 6, 54), (16, 14, 56)): p.ell(cx + dx * s_, cy + dy * s_, r * s_, r * .5 * s_, (255, 196, 190, 80))
        p.poly([(0, 1330), (400, 1250), (900, 1300), (1400, 1240), (1700, 1300), (1700, 1500), (0, 1500)], (122, 76, 124))
        # gran centro logístico
        p.rect(120, 1060, 1580, 1560, (170, 176, 196)); p.rect(120, 1060, 1580, 1110, (110, 118, 142)); p.rect(120, 1110, 1580, 1124, (80, 88, 112))
        for k in range(9):
            x = 170 + k * 160; p.rect(x, 1330, x + 110, 1560, (70, 78, 98)); p.rect(x, 1330, x + 110, 1346, (255, 200, 60))
            for j in range(4): p.rect(x + 8, 1360 + j * 46, x + 102, 1364 + j * 46, (90, 98, 120))
        p.rrect(560, 1130, 1140, 1240, 18, (255, 255, 255)); p.text(850, 1186, "AMAZON", 84, (30, 40, 70), anchor="mm")
        for xx in range(150, 1560, 220): p.rect(xx, 1170, xx + 120, 1190, (255, 244, 200))
        p.rect(0, 1560, LW, LH, (70, 66, 88)); p.rect(0, 1560, LW, 1584, (110, 104, 132))
        for xx in range(-40, LW, 140): p.rect(xx, 1780, xx + 80, 1792, (255, 214, 150, 170))
        for xx in range(60, LW, 340): p.rect(xx, 1560, xx + 8, 1900, (40, 36, 56)) if False else None
    _c["C"] = Layer(bake(LW, LH, campus), LW, LH, ox=-310, oy=-90, par=.8, zpar=.85)
    return _c


def scene(t):
    C = build()
    f = Frame(bg=False); base = f.base
    zt = ease_io(prog(t, 0, 7.0))
    cam = Cam(lerp(1050, 740, zt), lerp(1560, 1050, zt), lerp(1.75, .86, zt))
    C["C"].blit(base, cam)
    # camión en el muelle: se carga y sale; avión de reparto cruza
    dep = ease_in(prog(t, 1.8, 5.2))
    trk = cached(("trk5",), lambda: truck_icon(520, 0))
    ic = truck_icon(520, t * 10) if dep > 0 else trk
    put_icon(base, ic, *cam.p(1050 + 1100 * dep, 1620), scale=cam.z)
    for q in range(8):
        u = prog(t, 1.9 + q * .05, 5.2) * dep
        if u > 0:
            f.L.ellipse([cam.p(1000 + 1100 * dep - 160 - q * 40, 1700)[0] - 14, cam.p(1000, 1700)[1] - 14, cam.p(1000 + 1100 * dep - 160 - q * 40, 1700)[0] + 14, cam.p(1000, 1700)[1] + 14], fill=sc((255, 250, 240), .22 * (1 - q / 8)))
    # operarios cargando paquetes
    bo = cached(("box",), lambda: box_icon(120))
    for q, nm in enumerate(("eng_m", "tech_w")):
        cyc = (t * .7 + q * .45) % 1
        hx = lerp(420 + q * 520, 700 + q * 520, cyc if cyc < .5 else 1 - cyc)
        w = walk_pose((t * 1.3 + q * .3) % 1, speed=.7, sf=70, ef=20, sb=70, eb=20, smile=.5, turn=.2, eyes=blink(t, 3, q * .4))
        place_person(base, nm, w, hx, 1700 + q * 20, cam, k=1.1, flip=(cyc >= .5) != False)
        if dep < .05: put_icon(base, bo, *cam.p(hx + 120, 1620), scale=cam.z * .7)
    pl = cached(("plane",), lambda: plane_icon(560)); put_icon(base, pl, *cam.p(-300 + 2300 * prog(t, 2.0, 9.0), 560 - 40 * prog(t, 2, 9)), scale=cam.z * .6, rot=-4)
    for q in range(4):
        x = ((t * (90 + 20 * q) + q * 420) % 2000) - 200
        put_icon(base, cached(("trk6", q), lambda: truck_icon(330, 0)), *cam.p(x, 1860 + q * 36), scale=cam.z * .8) if q < 2 else None
    clouds(f, t, seed=8, n=5, y0=200, y1=800, col=(255, 190, 170), alpha=.15)
    dust(f, t, seed=66, n=34, tint=(255, 220, 170), alpha=.45)
    ba = ease(prog(t, 5.8, 6.8))
    if ba > 0:
        f.base *= (1 - .8 * ba)
        logo(base, f, t - 6.0, ba)
    out = f.finish()
    if ba > 0:
        def spaced(txt, size, color, y, sp, t0):
            fo = ImageFont.truetype(FONT_BOLD, size); widths = [fo.getlength(c) for c in txt]
            total = sum(widths) + sp * (len(txt) - 1); x = 540 - total / 2
            for i, c in enumerate(txt):
                a_ = ease(prog(t, t0 + i * .05, t0 + .4 + i * .05))
                if a_ > .01: paste_np(out, text_img(c, size, color), x - 6, y + (1 - a_) * 30, a_)
                x += widths[i] + sp
        spaced("EXPLORA", 140, (240, 248, 255), 950, 10, 7.0)
        spaced("CIENCIA 360", 84, (54, 214, 255), 1110, 14, 7.4)
        cta = ease(prog(t, 8.2, 8.9))
        if cta > .01:
            pill = Image.new("RGBA", (560, 120), (0, 0, 0, 0)); pd = ImageDraw.Draw(pill)
            pd.rounded_rectangle([0, 0, 559, 119], radius=60, fill=(255, 190, 70, 255)); pd.text((280, 60), "SÍGUENOS", font=ImageFont.truetype(FONT_BOLD, 54), fill=(30, 24, 50, 255), anchor="mm")
            s_ = 1 + .04 * math.sin(t * 5); pill = pill.resize((int(560 * s_), int(120 * s_)), Image.LANCZOS)
            paste_np(out, pill, 540 - pill.width / 2, 1290 - pill.height / 2 + (1 - cta) * 30, cta)
    return out
