"""Intro v2 (0–12.6 s): bóveda con dinero, un millón por día, calendario veloz, y la industria de Elon."""
from kit import *
from m1 import skyline, car_icon, rocket_icon
import m1
from people import blend as blend_pose

_c = {}
LW, LH = 1300, 1920
DUR = 12.62


def bill_stack(p, x, y, w, h, col=(84, 168, 100)):
    p.rect(x, y, x + w, y + h, col); p.rect(x, y, x + w, y + h * .22, shade(col, 1.25))
    p.rect(x + w * .38, y, x + w * .62, y + h, (232, 226, 190)); p.rect(x, y + h - 4, x + w, y + h, shade(col, .65))


def gold_bar(p, x, y, w, h):
    p.poly([(x, y + h), (x + w, y + h), (x + w - 10, y), (x + 10, y)], (236, 190, 70)); p.poly([(x + 10, y), (x + w - 10, y), (x + w - 16, y + h * .3), (x + 16, y + h * .3)], (255, 232, 140))


def build():
    if "V" in _c: return _c
    def vault(p):
        p.vgrad(0, 0, LW, LH, [(0, (20, 26, 44)), (.6, (34, 42, 66)), (1, (22, 24, 38))])
        for yy in range(60, 1500, 90):
            for xx in range(30, LW, 110): p.ell(xx, yy, 5, 5, (60, 72, 100))
        # arco de la bóveda con luz dorada
        p.rrect(150, 240, 1010, 1330, 90, (255, 214, 130))
        p.vgrad(170, 260, 990, 1310, [(0, (255, 232, 160)), (.5, (255, 196, 96)), (1, (200, 130, 50))])
        # estantes con fajos
        for row, yy in enumerate((420, 640, 860)):
            p.rect(170, yy + 120, 990, yy + 136, (110, 78, 48))
            xx = 190
            while xx < 960:
                bill_stack(p, xx, yy + 20, 62, 100, [(84, 168, 100), (96, 180, 112), (74, 150, 92)][(xx // 62 + row) % 3]); xx += 64
        # montañas de dinero y oro en el piso
        for k in range(7):
            for j in range(7 - k):
                bill_stack(p, 230 + k * 40 + j * 82, 1180 - k * 46, 80, 44, [(84, 168, 100), (96, 180, 112)][(j + k) % 2])
        for k in range(5):
            for j in range(5 - k):
                gold_bar(p, 640 + k * 28 + j * 74, 1210 - k * 36, 70, 34)
        # marco de la puerta
        p.rrect(110, 200, 1050, 1370, 110, None, (150, 160, 178), 38)
        p.rrect(110, 200, 1050, 1370, 110, None, (96, 106, 126), 10)
        # gran puerta circular abierta (a la derecha)
        p.ell(1120, 780, 130, 520, (118, 128, 150)); p.ell(1120, 780, 96, 470, (84, 94, 116))
        for a in range(8): p.line([(1120, 780), (1120 + 110 * math.cos(a * .785), 780 + 460 * math.sin(a * .785))], (150, 160, 178), 14)
        p.ell(1120, 780, 56, 56, (176, 186, 204))
        # piso reflectante
        p.rect(0, 1370, LW, LH, (26, 28, 42)); p.vgrad(0, 1370, LW, 1500, [(0, (92, 76, 56)), (1, (26, 28, 42))])
    _c["V"] = Layer(bake(LW, LH, vault), LW, LH, ox=-110, par=.85, zpar=.9)
    return _c


def bill_icon(w=120):
    def fn(p):
        s = w / 120.0
        p.rrect(0, 0, 120 * s, 56 * s, 6 * s, (96, 176, 108), (50, 120, 70), 3)
        p.ell(60 * s, 28 * s, 20 * s, 20 * s, (70, 150, 88)); p.text(60 * s, 29 * s, "$", int(30 * s), (225, 248, 225), anchor="mm")
    return icon_rgba(w, int(w * .47), fn)


def bundle_icon(w=360):
    def fn(p):
        s = w / 360.0
        for r in range(3):
            for c in range(3):
                x, y = (20 + c * 106) * s, (24 + r * 64) * s
                bill_stack(p, x, y, 98 * s, 58 * s, [(84, 168, 100), (96, 180, 112), (74, 150, 92)][(r + c) % 3])
        p.rrect(70 * s, 100 * s, 290 * s, 170 * s, 14 * s, (248, 246, 232), (60, 130, 80), 5)
        p.text(180 * s, 136 * s, "US$ 1.000.000", int(36 * s), (30, 100, 60), anchor="mm")
    return icon_rgba(w, int(w * .56), fn)


def calendar_page(day_txt, mon="DÍA", w=520):
    h = int(w * 1.05)
    def fn(p):
        s = w / 520.0
        p.rrect(0, 0, 520 * s, 546 * s, 26 * s, (248, 248, 250), (170, 174, 190), 6)
        p.rrect(0, 0, 520 * s, 130 * s, 26 * s, (210, 50, 62)); p.rect(0, 90 * s, 520 * s, 130 * s, (210, 50, 62))
        for x in (110, 410): p.ell(x * s, 40 * s, 14 * s, 14 * s, (255, 255, 255))
        p.text(260 * s, 86 * s, mon, int(64 * s), (255, 255, 255), anchor="mm")
        p.text(260 * s, 330 * s, day_txt, int(150 * s if len(day_txt) < 5 else 100 * s), (40, 44, 60), anchor="mm")
    return icon_rgba(w, int(w * 1.05), fn)


def fmt(n): return f"{n:,}".replace(",", ".")


def spend_bar(base, f, k, a, remain_glow=0.0):
    """Barra: gastado vs restante (89 % cuando se gastan 2.000 años a US$1M/día sobre la fortuna estimada)."""
    x0, y0, x1, y1 = 110, 1290, 970, 1336
    im = Image.new("RGBA", (W, 120), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([x0, 20, x1, 66], radius=23, fill=(20, 28, 56, 230), outline=(160, 200, 255, 255), width=3)
    sp = (x1 - x0) * .887 * k
    if sp > 6: d.rounded_rectangle([x0, 20, x0 + sp, 66], radius=23, fill=(255, 150, 60, 255))
    d.rounded_rectangle([x0 + sp + 4, 20, x1, 66], radius=23, fill=(90, 220, 130, int(120 + 135 * remain_glow))) if sp < (x1 - x0) - 8 else None
    d.text((x0, 98), "GASTADO", font=ImageFont.truetype(FONT_BOLD, 30), fill=(255, 190, 120, 255), anchor="lm")
    d.text((x1, 98), "TODAVÍA TE SOBRA", font=ImageFont.truetype(FONT_BOLD, 30), fill=(120, 240, 160, 255), anchor="rm")
    paste_np(base, im, 0, y0 - 20, a)


# ----------------------------------------------------------------- sub-escenas
def sub_vault(t, base, f, back=False):
    C = build()
    cam = Cam(560, 1040, 1.0 + .10 * ease_io(prog(t, 0, 3.0)) if not back else 1.12 - .05 * prog(t, 0, 2.6))
    C["V"].blit(base, cam)
    # destellos de oro y billetes flotando
    rng = np.random.RandomState(5)
    for i in range(38):
        x0, y0 = rng.uniform(220, 940), rng.uniform(420, 1250)
        a = .5 + .5 * math.sin(t * 4 + i * 1.7)
        sx, sy = cam.p(x0, y0)
        f.L.ellipse([sx - 4, sy - 4, sx + 4, sy + 4], fill=sc((255, 250, 210), a * .8))
        if a > .9: f.L.line([(sx - 16, sy), (sx + 16, sy)], fill=sc((255, 250, 210), .7), width=2); f.L.line([(sx, sy - 16), (sx, sy + 16)], fill=sc((255, 250, 210), .7), width=2)
    bi = cached(("bill",), lambda: bill_icon(110))
    for i in range(14):
        u = (t * (.2 + .1 * (i % 3)) + i * .31) % 1
        x = 260 + (i * 97) % 720 + 40 * math.sin(t * 2 + i); y = 1200 - 900 * u
        sx, sy = cam.p(x, y)
        put_icon(base, bi, sx, sy, scale=cam.z * (.8 + .4 * (i % 2)), rot=40 * math.sin(t * 3 + i) + 90 * u, alpha=min(1, u * 5, (1 - u) * 3))
    ph = (t * .85)
    if not back:
        walk_in = 1 - ease(prog(t, 1.1, 1.5))
        ex = lerp(-120, 560, ease_out(prog(t, 0, 1.3)))
        wow = ease(prog(t, 1.3, 1.9))
        pose = blend_pose(walk_pose(ph % 1, speed=1.0 * walk_in + .01, smile=.4, turn=.2, head=-2, eyes=blink(t, 3, .5)),
                          mk(sf=lerp(0, 74, wow) + 4 * math.sin(t * 5) * wow, ef=-10, sb=-72 * wow, eb=0, smile=.95, mouth=.5 * wow, brow=.6, head=-6 * wow, turn=.5, lookx=1.0, looky=-.8, eyes=blink(t, 3, .5), lean=-2), wow)
    else:
        ex = 560
        sh = ease(prog(t, .4, 1.2))
        pose = mk(sf=lerp(0, 52, sh) + 3 * math.sin(t * 4), ef=lerp(10, 70, sh), sb=-30 * sh, eb=50 * sh, smile=.7 + .2 * math.sin(t * 2), brow=.5 * sh, head=lerp(0, 6, sh), turn=lerp(.2, .9, sh), mouth=.0, eyes=blink(t, 3, .5), lean=1.5 * math.sin(t))
    place_person(base, "elon_adult", pose, ex, 1560, cam, k=1.3)
    return cam


def sub_daily(t, base, f):
    cam = Cam(540, 960, 1.0)
    base[:] = np.asarray(Image.fromarray(np.uint8(np.clip(np.tile(np.array([[(16, 22, 44)]]), (1, 1, 1)), 0, 255))).resize((W, H)), np.float32)
    g = np.linspace(0, 1, H)[:, None]
    base[:] = np.array((14, 20, 40), np.float32) * (1 - g[..., None]) + np.array((30, 40, 74), np.float32) * g[..., None]
    for i in range(14): f.L.line([(540, 760), (540 + 900 * math.cos(i * .45 + t * .3), 760 + 900 * math.sin(i * .45 + t * .3))], fill=sc((70, 110, 190), .10), width=18)
    period = .30
    n = int(t / period) + 1
    ph = (t % period) / period
    bd = cached(("bundle",), lambda: bundle_icon(420))
    # un fajo de US$ 1.000.000 aparece y se esfuma cada "día"
    sc_in = ease_back(clamp(ph / .35)); fade = 1 - ease(clamp((ph - .55) / .45))
    put_icon(base, bd, 540, 760 - 20 * ph, scale=sc_in * (1 - .25 * ease(clamp((ph - .55) / .45))), alpha=fade)
    rng = np.random.RandomState(n)
    if ph > .55:
        u = (ph - .55) / .45
        for i in range(36):
            a = rng.rand() * 6.28; v = rng.uniform(120, 420)
            x, y = 540 + math.cos(a) * v * u, 760 + math.sin(a) * v * u - 80 * u
            f.L.ellipse([x - 7, y - 7, x + 7, y + 7], fill=sc(mix((120, 240, 140), (255, 230, 120), rng.rand()), (1 - u)))
    # contador de días
    lab = text_img("DÍA " + fmt(n), 120, (255, 255, 255), stroke=8, stroke_col=(10, 16, 40))
    paste_np(base, lab, 540 - lab.width / 2, 250, 1)
    sub = text_img("−US$ 1.000.000 cada día", 54, (255, 190, 120), stroke=6, stroke_col=(10, 16, 40))
    paste_np(base, sub, 540 - sub.width / 2, 400, 1)
    spend_bar(base, f, 0.0004 * n, 1.0)
    return cam


def sub_calendar(t, base, f, T=1.7):
    g = np.linspace(0, 1, H)[:, None]
    base[:] = np.array((20, 14, 36), np.float32) * (1 - g[..., None]) + np.array((54, 34, 76), np.float32) * g[..., None]
    u = clamp(t / T)
    days = int(730500 * ease_in(u) ** .8) if u < 1 else 730500
    years = days / 365.25
    for i in range(16): f.L.line([(540, 800), (540 + 1100 * math.cos(i * .4 + t * 2), 800 + 1100 * math.sin(i * .4 + t * 2))], fill=sc((150, 90, 200), .08), width=16)
    # páginas que vuelan
    rate = 14 + 36 * u
    last = int(t * rate)
    for q in range(last - 7, last + 1):
        if q < 0: continue
        age = t - q / rate
        if age < 0 or age > .5: continue
        a = age / .5
        pg = cached(("pg", q % 31), lambda q=q: calendar_page(str((q * 37) % 31 + 1), "DÍA", 520))
        x = 540 + 620 * ease_in(a) * (1 if q % 2 else -1); y = 760 - 260 * a
        put_icon(base, pg, x, y, scale=.9 - .25 * a, rot=(q % 2 * 2 - 1) * 70 * a, alpha=1 - a ** 2)
    pg = cached(("pgf",), lambda: calendar_page("2000", "AÑOS", 520))
    put_icon(base, pg, 540, 780, scale=1.0 + .03 * math.sin(t * 20), alpha=1 if u < .98 else 1)
    # reloj/contadores
    tx = text_img("DÍA " + fmt(days), 86, (255, 214, 120), stroke=8, stroke_col=(20, 10, 40)); paste_np(base, tx, 540 - tx.width / 2, 150, 1)
    ty = text_img(f"AÑO {int(years) + 1 if years < 2000 else 2000}", 96, (255, 255, 255), stroke=8, stroke_col=(20, 10, 40)); paste_np(base, ty, 540 - ty.width / 2, 1120, 1)
    spend_bar(base, f, ease_in(u) ** .8, 1.0, 0)
    if u >= 1:
        pl = text_img("más de 2.000 años", 60, (255, 255, 255), stroke=6, stroke_col=(20, 10, 40)); paste_np(base, pl, 540 - pl.width / 2, 1225, ease(prog(t, T, T + .25)))


def sub_close(t, base, f):
    L = m1.build()
    zt = ease_io(prog(t, 0, 4.2))
    cam = Cam(560 + 30 * math.sin(t * .4), 960 - 30 * zt, 1.08 + .25 * zt)
    for ly in L: ly.blit(base, cam)
    for i in range(3):
        cx0 = 180 + 150 * i + 22
        for j in range(8):
            u = (t * .22 + j / 8 + i * .13) % 1
            x, y = cam.p(cx0 + 40 * u + math.sin(u * 6 + i) * 10, 940 - 330 * u, .85)
            r = (14 + 46 * u) * cam.z ** .85
            f.L.ellipse([x - r, y - r, x + r, y + r], fill=sc((200, 150, 170), .22 * (1 - u)))
    # coches eléctricos
    for q, (sp, yy, off, col) in enumerate(((260, 1440, 0, (232, 236, 244)), (-200, 1540, 300, (200, 60, 70)))):
        x = ((t * sp + off) % 1900) - 300 if sp > 0 else 1500 - ((t * -sp + off) % 1900)
        ic = car_icon(t * 8 * (1 if sp > 0 else -1), col)
        if sp < 0: ic = ic.transpose(Image.FLIP_LEFT_RIGHT)
        sx, sy = cam.p(x, yy, 1.0); put_icon(base, ic, sx, sy, scale=cam.z * .8)
    # cohete: aparece en la plataforma y despega al final
    rk = m1._c["rocket"]
    lift = prog(t, 2.4, 4.4)
    rx, ry = cam.p(880, 1290 - 900 * ease_in(lift), .85)
    zz = cam.z ** .85
    if lift > 0:
        fl = 1 + .25 * math.sin(t * 50)
        for (wd, ln, col) in ((40, 220 * fl, (255, 120, 30)), (26, 170 * fl, (255, 210, 90)), (14, 110 * fl, (255, 255, 240))):
            f.L.polygon([(rx - wd * zz, ry + 14 * zz), (rx + wd * zz, ry + 14 * zz), (rx + wd * .3 * zz, ry + 14 * zz + ln * zz), (rx - wd * .3 * zz, ry + 14 * zz + ln * zz)], fill=sc(col, .95))
        for i in range(10):
            u2 = (t * 1.6 + i * .1) % 1
            f.L.ellipse([rx - 60 - 40 * u2, ry + 200 * zz * u2 - 30, rx + 60 + 40 * u2, ry + 200 * zz * u2 + 50], fill=sc((255, 236, 220), .18 * (1 - u2)))
    paste_np(base, rk.resize((int(rk.width * zz), int(rk.height * zz)), Image.LANCZOS), rx - rk.width * zz / 2, ry - rk.height * zz + 14 * zz)
    zk = ease_io(prog(t, 0, 4.2))
    turn = lerp(1.0, .15, ease(prog(t, 1.4, 2.8)))
    pose = mk(turn=turn, smile=lerp(.4, .9, ease(prog(t, 0, 2))), brow=.4 + .2 * math.sin(t * 2), eyes=blink(t, 3.1, .4), head=lerp(2, -5, ease(prog(t, 1, 3))), lookx=lerp(0, 1.4, ease(prog(t, 1.4, 2.8))),
              sf=-6 + 3 * math.sin(t * 1.3), ef=14, sb=3, eb=8, lean=1.5 * math.sin(t * .9), bob=2 * math.sin(t * 1.6))
    place_person(base, "elon_adult", pose, 400, 1580 + 30 * (1 - zk), cam, k=1.75)
    clouds(f, t, seed=7, n=5, y0=120, y1=560, col=(255, 190, 180), alpha=.14)
    for i in range(5):
        a = -.25 + i * .12 + .03 * math.sin(t * .5 + i)
        x0, y0 = 860, 780
        f.L.polygon([(x0, y0), (x0 + 1400 * math.cos(a + math.pi / 2 + .5), y0 + 1400 * math.sin(a + math.pi / 2 + .5)), (x0 + 1400 * math.cos(a + math.pi / 2 + .62), y0 + 1400 * math.sin(a + math.pi / 2 + .62))], fill=sc((255, 200, 130), .08))


def title_overlay(out, t, t0, t1):
    ta = ease(prog(t, t0, t0 + .5)) * (1 - ease(prog(t, t1 - .4, t1)))
    if ta > .01:
        for i, (txt, col) in enumerate((("¿CÓMO SE CONVIRTIÓ", (255, 255, 255)), ("ELON MUSK EN EL HOMBRE", (255, 205, 90)), ("MÁS RICO DEL MUNDO?", (255, 255, 255)))):
            im = text_img(txt, 66, col, stroke=7, stroke_col=(10, 14, 36))
            paste_np(out, im, (W - im.width) / 2, 150 + i * 84 + (1 - ta) * -30, ta)


# ----------------------------------------------------------------- escena
CUTS = [2.2, 4.0, 5.7, 8.3]          # alineados con la narración
WH = .32


def render_part(i, t):
    f = Frame(bg=False); base = f.base
    if i == 0: sub_vault(t, base, f)
    elif i == 1: sub_daily(t - CUTS[0], base, f)
    elif i == 2: sub_calendar(t - CUTS[1], base, f, T=CUTS[2] - CUTS[1] - .15)
    elif i == 3: sub_vault(t - CUTS[2], base, f, back=True)
    else: sub_close(t - CUTS[3], base, f)
    dust(f, t, seed=40 + i, n=34, tint=(255, 226, 170), alpha=.4)
    out = f.finish()
    return out


def scene(t):
    edges = [0.0] + CUTS + [DUR + 1]
    idx = 0
    for i in range(len(edges) - 1):
        if t >= edges[i]: idx = i
    out = None
    for ci, c in enumerate(CUTS):
        if c - WH / 2 <= t < c + WH / 2:
            p = (t - (c - WH / 2)) / WH
            A = render_part(ci, t); B = render_part(ci + 1, t)
            if ci in (0, 3):
                out = slide_blend(A, B, p, 1)
            elif ci == 1:
                out = A * (1 - ease(p)) + B * ease(p) + 140 * math.sin(math.pi * p)
            else:
                e = ease(p); sz = 1 + .12 * math.sin(math.pi * p)
                out = (A * (1 - e) + B * e)
            break
    if out is None:
        out = render_part(idx, t)
    title_overlay(out, t, 9.0, 12.0)
    return out
