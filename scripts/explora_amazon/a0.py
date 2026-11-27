"""Gancho (0–14.85 s): compras con el móvil -> garaje de 1994 -> pedidos de libros -> el imperio que vendrá."""
from amz import *

_c = {}
LW, LH = 1300, 1920
DUR = 14.85
CUTS = [3.15, 7.0, 11.2]
WH = .4


def build():
    if "L" in _c: return _c
    def living(p):
        p.vgrad(0, 0, LW, 1300, [(0, (255, 236, 214)), (1, (255, 214, 190))])
        p.rrect(80, 260, 520, 760, 18, (150, 150, 160)); p.vgrad(96, 276, 504, 744, [(0, (170, 226, 255)), (1, (230, 246, 255))])
        p.rect(296, 276, 304, 744, (150, 150, 160)); p.rect(96, 506, 504, 514, (150, 150, 160))
        p.rect(0, 1300, LW, LH, (226, 190, 150))
        for xx in range(0, LW, 170): p.rect(xx, 1300, xx + 4, LH, (206, 170, 130))
        # sofá
        p.rrect(120, 1010, 760, 1320, 40, (84, 120, 190)); p.rrect(150, 1130, 730, 1320, 30, (104, 140, 210)); p.rrect(100, 1100, 190, 1320, 30, (74, 108, 176))
        # planta y lámpara
        p.rrect(1000, 1180, 1100, 1310, 14, (190, 110, 80))
        for a in (-50, -25, 0, 25, 50): p.poly([(1050, 1180), (1050 + a * 2.4, 960 - abs(a)), (1050 + a * .6, 1180)], (70, 160, 100))
        p.rect(900, 860, 908, 1300, (90, 90, 100)); p.poly([(850, 860), (960, 860), (940, 790), (870, 790)], (255, 220, 120))
        p.rrect(880, 1230, 1220, 1300, 10, (120, 90, 70))
    def garage(p):
        p.vgrad(0, 0, LW, 1330, [(0, (120, 84, 56)), (1, (92, 64, 44))])
        for xx in range(0, LW, 70): p.rect(xx, 0, xx + 4, 1330, (70, 48, 34))
        p.rect(0, 1330, LW, LH, (110, 108, 112)); p.rect(0, 1318, LW, 1336, (70, 62, 56))
        # puerta del garaje abierta
        p.rect(760, 360, 1220, 1330, (255, 238, 190))
        p.vgrad(776, 376, 1204, 1330, [(0, (170, 220, 255)), (.7, (210, 236, 255)), (1, (120, 170, 100))])
        for (x, y, r) in ((880, 700, 70), (1060, 640, 90), (1160, 760, 60)): p.ell(x, y, r, r * 1.2, (60, 130, 80))
        p.rect(760, 340, 1220, 400, (176, 176, 184)); [p.rect(760, 340 + i * 14, 1220, 342 + i * 14, (150, 150, 160)) for i in range(5)]
        # estantes con libros y cajas
        shelf_unit(p, 60, 420, 420, 700, rows=4, seed=2)
        # banco de trabajo
        p.rect(480, 1020, 1000, 1050, (150, 110, 76)); p.rect(500, 1050, 530, 1330, (110, 80, 56)); p.rect(950, 1050, 980, 1330, (110, 80, 56))
        # bombilla
        p.line([(560, 0), (560, 260)], (30, 30, 36), 4); p.ell(560, 276, 22, 26, (255, 236, 160))
        p.ell(560, 276, 120, 120, (255, 226, 140, 40))
        # cajas apiladas
        for (x, y, w_, h_) in ((60, 1190, 170, 130), (200, 1210, 130, 110), (90, 1100, 120, 92)): p.rect(x, y, x + w_, y + h_, (196, 150, 98)); p.rect(x + w_ * .4, y, x + w_ * .6, y + h_, (226, 206, 150))
    def exterior(p):
        p.vgrad(0, 0, LW, LH, [(0, (22, 30, 78)), (.4, (110, 76, 140)), (.65, (250, 160, 110)), (1, (255, 200, 140))])
        p.ell(280, 1000, 120, 120, (255, 232, 180))
        skyline(p, LW, LH, 1250, 23, (110, 80, 130, 255), (255, 224, 150), 160, 360, 60, 110, .3)
        # grandes almacenes
        for (x0, w_, h_) in ((40, 420, 300), (520, 520, 340), (1000, 360, 280)):
            p.rect(x0, 1290 - h_, x0 + w_, 1290, (92, 82, 126)); p.rect(x0, 1290 - h_, x0 + w_, 1290 - h_ + 14, (60, 54, 90))
            for k in range(int(w_ // 90)): p.rect(x0 + 24 + k * 88, 1290 - 150, x0 + 24 + k * 88 + 64, 1290, (50, 46, 76)); p.rect(x0 + 24 + k * 88, 1290 - 150, x0 + 24 + k * 88 + 64, 1290 - 140, (255, 200, 100))
        p.rect(0, 1290, LW, LH, (56, 48, 82)); p.rect(0, 1290, LW, 1312, (96, 84, 124))
        for xx in range(-40, LW, 120): p.rect(xx, 1500, xx + 70, 1510, (255, 214, 150, 160))
    _c["L"] = Layer(bake(LW, LH, living), LW, LH, ox=-110, par=.9, zpar=.9)
    _c["G"] = Layer(bake(LW, LH, garage), LW, LH, ox=-110, par=.9, zpar=.9)
    _c["E"] = Layer(bake(LW, LH, exterior), LW, LH, ox=-110, par=.6, zpar=.8)
    return _c


def retro(arr, k):
    """Look noventas: sepia suave, viñeta y líneas de barrido."""
    g = arr.mean(2, keepdims=True)
    sep = g * np.array((1.12, .98, .78), np.float32)
    out = arr * (1 - k) + sep * k
    out[::3] *= (1 - .10 * k)
    return out


# ------------------------------------------------------------------ H1 compras con el móvil
def sub_shop(t, base, f):
    C = build()
    cam = Cam(560, 1040, 1.0 + .12 * ease_io(prog(t, 0, 3.4)))
    C["L"].blit(base, cam)
    hx, hy = 440, 1190
    sx, sy = cam.p(hx, hy + 60)
    pose = seated(t, 0, head=-3 + 3 * math.sin(t * 3), turn=.35, smile=.8, brow=.3, mouth=.2, eyes=blink(t, 3, .3), lean=6)
    pose["sf"] = 66 + 6 * math.sin(t * 8); pose["ef"] = 22
    place_person(base, "cust_f", pose, hx, hy, cam, k=1.2)
    # teléfono en la mano
    ti = int(t / .42) % 6; ph = (t % .42) / .42
    pi = phone_icon(260, t, tap=ti if ph < .45 else -1)
    px, py = cam.p(hx + 280, hy - 130)
    put_icon(base, pi, px, py, scale=cam.z, rot=-8)
    # productos que salen de la pantalla y vuelan a su sitio
    order = [("box", 0), ("headphones", 1), ("shirt", 2), ("laptop", 3), ("shoe", 4), ("toy", 5), ("watch", 6), ("game", 7), ("box", 8), ("lamp", 9)]
    dest = [(900, 1230), (980, 980), (820, 1000), (1060, 1170), (700, 920), (1100, 880), (940, 820), (780, 1150), (1000, 1260), (860, 900)]
    for kind, i in order:
        t0 = .25 + i * .30
        u = prog(t, t0, t0 + .8)
        if u <= 0: continue
        icn = cached(("pr", kind, 120), lambda kind=kind: box_icon(130) if kind == "box" else product(kind, 120))
        a = (px, py - 40); b = cam.p(*dest[i])
        x = lerp(a[0], b[0], ease_out(u)); y = lerp(a[1], b[1], ease_out(u)) - 260 * math.sin(math.pi * u) * (1 - .3 * u)
        put_icon(base, icn, x, y, scale=cam.z * (.3 + .9 * ease_out(min(1, u * 1.4))), rot=30 * (1 - u) * (-1) ** i, alpha=1)
        if u < .35:
            f.L.ellipse([x - 40, y - 40, x + 40, y + 40], fill=sc((255, 240, 180), .5 * (1 - u / .35)))
    # destello de "compra"
    if ph < .2 and t > .2:
        ck = 1 - ph / .2
        f.L.ellipse([px - 120 * (1 + ph), py - 120 * (1 + ph), px + 120 * (1 + ph), py + 120 * (1 + ph)], outline=sc((120, 240, 160), ck), width=6)
    return cam


# ------------------------------------------------------------------ H2/H3 garaje de 1994
def sub_garage(t, base, f, phase=0):
    C = build()
    if phase == 0:
        cam = Cam(520, 1040, 1.0 + .10 * ease_io(prog(t, 0, 3.9)))
    else:
        cam = Cam(lerp(560, 760, ease_io(prog(t, 0, 4.2))), 1040, lerp(1.0, 1.35, ease_io(prog(t, 0, 4.2))))
    C["G"].blit(base, cam)
    # monitor CRT + teclado sobre el banco
    scr = desk_set(t, game=0.0, seed=7, w=300)
    mx, my = cam.p(720, 880)
    if phase == 1:
        # pantalla con pedidos de libros
        w = 300; im = Image.new("RGBA", (w, int(w * .95)), (0, 0, 0, 0))
        base_crt = cached(("crt", w), lambda: crt(w)).copy()
        sw, sh_ = int(w * .76), int(w * .5)
        sc_im = Image.new("RGB", (sw, sh_), (8, 20, 12)); d = ImageDraw.Draw(sc_im)
        n = int(t * 1.7) + 1
        for i in range(min(n, 5)):
            y = 8 + (min(n, 5) - 1 - i) * 36
            d.rounded_rectangle([8, y, sw - 8, y + 30], radius=6, fill=(20, 60, 36)); d.rectangle([14, y + 6, 40, y + 24], fill=(210, 70, 70)); d.rectangle([48, y + 9, 130 + (i * 23) % 60, y + 14], fill=(110, 240, 150)); d.rectangle([48, y + 18, 100, y + 22], fill=(70, 160, 100))
            d.ellipse([sw - 30, y + 8, sw - 14, y + 24], fill=(255, 210, 90))
        sc_im = sc_im.convert("RGBA"); m = Image.new("L", sc_im.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, sw, sh_], radius=12, fill=255); sc_im.putalpha(m)
        base_crt.alpha_composite(sc_im, (int(w * .1), int(w * .08))); scr = base_crt
    put_icon(base, scr, mx, my, scale=cam.z)
    kb = cached(("kb",), lambda: keyboard(250)); kx, ky = cam.p(700, 1010); put_icon(base, kb, kx, ky, scale=cam.z)
    ch = cached(("chair",), lambda: chair(170)); cx_, cy_ = cam.p(560, 1090); put_icon(base, ch, cx_, cy_ + 18 * cam.z, scale=cam.z * .95)
    # Jeff joven
    if phase == 0:
        # teclea, luego empaca un libro en una caja
        pk = ease(prog(t, 1.6, 2.3))
        pose = seated(t, 0, head=-2, turn=.15, smile=.5, eyes=blink(t, 3, .3), lookx=1.4, brow=.1)
        pose["sf"] = lerp(pose["sf"], 40, pk); pose["ef"] = lerp(pose["ef"], 60, pk)
    else:
        react = ease(prog(t, 1.2, 2.2))
        pose = seated(t, .3, head=lerp(-2, -6, react), turn=.2, smile=lerp(.4, .95, react), brow=.4 * react, mouth=.3 * react * (.5 + .5 * math.sin(t * 6)), eyes=blink(t, 3, .3), lookx=1.6)
    place_person(base, "bezos_young", pose, 560, 1040, cam, k=1.0)
    if phase == 0:
        bi = cached(("book",), lambda: book_icon(74)); bx, by = cam.p(820, 990 - 40 * math.sin(t * 2))
        bo = cached(("box",), lambda: box_icon(130)); ox, oy = cam.p(900, 990)
        put_icon(base, bo, ox, oy, scale=cam.z)
        if t > 2.3:
            u = prog(t, 2.3, 3.2); put_icon(base, bi, lerp(bx, ox, ease(u)), lerp(by, oy - 30, ease(u)) - 50 * math.sin(math.pi * u), scale=cam.z * (1 - .3 * u))
        # año 1994 con "regreso en el tiempo"
        ya = ease(prog(t, .5, 1.1))
        im = text_img("1994", 130, (255, 214, 120), stroke=8, stroke_col=(40, 24, 10))
        if ya > .02: paste_np(base, im, 540 - im.width / 2, 210 - 40 * (1 - ya), ya)
    else:
        # escépticos en la puerta del garaje: niegan con la cabeza
        sa = ease(prog(t, 1.9, 2.6))
        for (nm, hx, off) in (("exec1", 880, 0), ("exec2", 1010, .6)):
            tap = ease(prog(t, 2.8 + off * .3, 3.2)) if nm == "exec2" else 0
            pose = mk(smile=-.2, brow=-.3, turn=.1, head=4 * math.sin(t * 7 + off * 3) * sa, eyes=blink(t, 3.4, off), sf=lerp(0, 150, tap) if nm == "exec2" else 20, ef=lerp(10, 80, tap) if nm == "exec2" else 70)
            place_person(base, nm, pose, hx, 1180, cam, k=.95, flip=True, alpha=sa)
        # bombilla de idea sobre Jeff
        ia = ease(prog(t, 1.0, 1.6))
        if ia > .01:
            lx, ly = cam.p(640, 560)
            f.L.ellipse([lx - 70 * ia, ly - 70 * ia, lx + 70 * ia, ly + 70 * ia], fill=sc((255, 236, 140), .9 * ia))
            for q in range(10):
                a = q / 10 * 6.28 + t; f.L.line([lx + math.cos(a) * 90 * ia, ly + math.sin(a) * 90 * ia, lx + math.cos(a) * 130 * ia, ly + math.sin(a) * 130 * ia], fill=sc((255, 220, 120), ia), width=5)
        if 1.4 < t < 2.4: base += 0
    return cam


# ------------------------------------------------------------------ H4 primer plano + imperio futuro
def sub_future(t, base, f):
    C = build()
    zt = ease_io(prog(t, 0, 3.7))
    cam = Cam(560 + 20 * math.sin(t * .4), 960 - 20 * zt, 1.08 + .2 * zt)
    C["E"].blit(base, cam)
    # camiones y avión de reparto cruzando
    for q, (sp, yy, off) in enumerate(((240, 1450, 0), (-190, 1560, 500))):
        x = ((t * sp + off) % 1900) - 300 if sp > 0 else 1500 - ((t * -sp + off) % 1900)
        ic = truck_icon(420, t * 9 * (1 if sp > 0 else -1), label=(sp > 0))
        if sp < 0: ic = ic.transpose(Image.FLIP_LEFT_RIGHT)
        sx, sy = cam.p(x, yy, 1.0); put_icon(base, ic, sx, sy, scale=cam.z * .9)
    pl = cached(("plane",), lambda: plane_icon(520))
    px, py = cam.p(-200 + 1500 * ease_in(prog(t, .6, 3.7)), 420 - 90 * prog(t, .6, 3.7), .7)
    put_icon(base, pl, px, py, scale=cam.z * .7, rot=-6)
    for j in range(14):
        f.L.ellipse([px - 250 * cam.z - j * 26, py + 10 - j, px - 250 * cam.z - j * 26 + 22, py + 22 - j], fill=sc((255, 240, 230), .35 * (1 - j / 14)))
    # humo/luces
    zk = zt
    turn = lerp(1.0, .2, ease(prog(t, 1.4, 2.8)))
    pose = mk(turn=turn, smile=lerp(.5, .95, ease(prog(t, 0, 2))), brow=.4 + .2 * math.sin(t * 2), eyes=blink(t, 3.1, .4), head=lerp(2, -5, ease(prog(t, 1, 3))), lookx=lerp(0, 1.4, ease(prog(t, 1.4, 2.8))),
              sf=-6, ef=14, sb=3, eb=8, lean=1.5 * math.sin(t * .9), bob=2 * math.sin(t * 1.6))
    place_person(base, "bezos_adult", pose, 420, 1600 + 30 * (1 - zk), cam, k=1.75)
    for i in range(5):
        a = -.25 + i * .12 + .03 * math.sin(t * .5 + i); x0, y0 = 860, 780
        f.L.polygon([(x0, y0), (x0 + 1400 * math.cos(a + math.pi / 2 + .5), y0 + 1400 * math.sin(a + math.pi / 2 + .5)), (x0 + 1400 * math.cos(a + math.pi / 2 + .62), y0 + 1400 * math.sin(a + math.pi / 2 + .62))], fill=sc((255, 200, 130), .08))
    clouds(f, t, seed=2, n=4, y0=160, y1=500, col=(255, 190, 180), alpha=.14)


def title_overlay(out, t, t0):
    ta = ease(prog(t, t0, t0 + .5))
    if ta > .01:
        for i, (txt, col) in enumerate((("CÓMO JEFF BEZOS CONVIRTIÓ", (255, 255, 255)), ("UNA PEQUEÑA LIBRERÍA", (255, 205, 90)), ("EN AMAZON", (255, 255, 255)))):
            im = text_img(txt, 62, col, stroke=7, stroke_col=(10, 14, 36))
            paste_np(out, im, (W - im.width) / 2, 150 + i * 80 + (1 - ta) * -30, ta)


PARTS = [lambda t, b, f: sub_shop(t, b, f), lambda t, b, f: sub_garage(t - CUTS[0], b, f, 0), lambda t, b, f: sub_garage(t - CUTS[1], b, f, 1), lambda t, b, f: sub_future(t - CUTS[2], b, f)]


def render_part(i, t):
    f = Frame(bg=False); base = f.base
    PARTS[i](t, base, f)
    dust(f, t, seed=50 + i, n=30, tint=(255, 230, 190), alpha=.35)
    out = f.finish()
    if i in (1, 2):                      # el pasado se ve con look de los 90
        out = retro(out, .55)
    return out


def scene(t):
    idx = 0
    for i, c in enumerate(CUTS):
        if t >= c: idx = i + 1
    out = None
    for ci, c in enumerate(CUTS):
        if c - WH / 2 <= t < c + WH / 2:
            p = (t - (c - WH / 2)) / WH
            A = render_part(ci, t); B = render_part(ci + 1, t)
            if ci == 0:   # rebobinado hacia el pasado: líneas, ruido y cuenta atrás de años
                e = ease(p)
                out = A * (1 - e) + B * e
                rng = np.random.RandomState(int(t * 30))
                for _ in range(14):
                    y = rng.randint(0, H - 40); out[y:y + rng.randint(4, 30)] += 60 * math.sin(math.pi * p)
                yr = int(lerp(2025, 1994, ease(p)))
                im = text_img(str(yr), 200, (255, 255, 255), stroke=10, stroke_col=(20, 20, 40)); paste_np(out, im, 540 - im.width / 2, 760, math.sin(math.pi * p))
            elif ci == 1:
                out = slide_blend(A, B, p, 1) if False else A * (1 - ease(p)) + B * ease(p)
            else:
                out = A * (1 - ease(p)) + B * ease(p) + 90 * math.sin(math.pi * p)
            break
    if out is None: out = render_part(idx, t)
    title_overlay(out, t, 12.6)
    return out
