"""Escena 1 — El gancho."""
from stage import *
from stage import _font

_c = {}
def car_icon(wheel=0.0, color=(230, 232, 240), w=420):
    h = 150
    def fn(p):
        # carrocería de sedán eléctrico (aerodinámico)
        p.poly([(10, 100), (40, 74), (120, 52), (190, 30), (260, 30), (330, 52), (385, 70), (410, 92), (410, 106), (10, 106)], color)
        p.poly([(130, 56), (190, 34), (258, 34), (318, 56)], (60, 90, 130))
        p.poly([(196, 36), (200, 36), (206, 56), (190, 56)], color)
        p.poly([(10, 100), (410, 100), (410, 112), (10, 112)], shade(color, .72))
        p.rect(290, 82, 410, 88, shade(color, .85))
        p.ell(396, 82, 12, 5, (255, 244, 200))
        p.ell(18, 80, 8, 5, (255, 70, 70))
        for cx in (92, 326):
            p.ell(cx, 112, 36, 36, (24, 24, 30))
            p.ell(cx, 112, 24, 24, (200, 205, 215))
            for k in range(5):
                a = wheel + k * 2 * math.pi / 5
                p.line([(cx, 112), (cx + 22 * math.cos(a), 112 + 22 * math.sin(a))], (90, 94, 104), 5)
            p.ell(cx, 112, 7, 7, (60, 64, 72))
    return icon_rgba(w, h, fn)


def rocket_icon(h=700, flame=0.0):
    w = int(h * .22)
    def fn(p):
        s = h / 700.0
        cx = w * .5 / 1  # centro
        X = lambda x: x
        # cuerpo
        p.rrect(cx / 1 - 46 * s, 90 * s, cx + 46 * s, 560 * s, 30 * s, (244, 246, 250))
        p.poly([(cx - 46 * s, 150 * s), (cx, 6 * s), (cx + 46 * s, 150 * s)], (244, 246, 250))
        p.rect(cx - 46 * s, 330 * s, cx + 46 * s, 372 * s, (30, 32, 40))
        p.rect(cx - 46 * s, 90 * s + 150 * s, cx - 20 * s, 560 * s, (206, 210, 222))
        p.rect(cx + 24 * s, 160 * s, cx + 46 * s, 560 * s, (226, 230, 238))
        p.ell(cx, 250 * s, 14 * s, 14 * s, (90, 130, 190))
        # aletas
        p.poly([(cx - 46 * s, 480 * s), (cx - 78 * s, 600 * s), (cx - 46 * s, 560 * s)], (30, 32, 40))
        p.poly([(cx + 46 * s, 480 * s), (cx + 78 * s, 600 * s), (cx + 46 * s, 560 * s)], (30, 32, 40))
        p.rect(cx - 30 * s, 560 * s, cx + 30 * s, 580 * s, (60, 62, 72))
    return icon_rgba(w + 40, int(h * .88), fn, ss=2)


def skyline(p, w, h, base_y, seed, col, win, hmin, hmax, wmin, wmax, lit=.35):
    rng = np.random.RandomState(seed)
    x = -20
    while x < w + 20:
        bw = rng.uniform(wmin, wmax); bh = rng.uniform(hmin, hmax)
        p.rect(x, base_y - bh, x + bw, base_y + 4, col)
        if rng.rand() < .3:
            p.rect(x + bw * .45, base_y - bh - 40, x + bw * .55, base_y - bh, col)
        for yy in np.arange(base_y - bh + 16, base_y - 14, 22):
            for xx in np.arange(x + 10, x + bw - 14, 18):
                if rng.rand() < lit:
                    p.rect(xx, yy, xx + 8, yy + 11, win)
        x += bw + rng.uniform(0, 8)


def build():
    if "L" in _c: return _c["L"]
    LW, LH = 1400, 1920
    ox = -160
    def sky(p):
        p.vgrad(0, 0, LW, LH, [(0, (18, 26, 74)), (.35, (96, 70, 140)), (.6, (236, 120, 118)), (.78, (255, 196, 128)), (1, (255, 214, 150))])
        p.ell(760, 1010, 150, 150, (255, 236, 190))
        p.ell(760, 1010, 230, 230, (255, 220, 170, 60))
        for (cx, cy, s_) in ((200, 360, 1.2), (700, 250, 1.0), (1100, 460, 1.4)):
            for dx, dy, r in ((-60, 8, 50), (0, -14, 66), (70, 6, 54), (16, 14, 56)):
                p.ell(cx + dx * s_, cy + dy * s_, r * s_, r * .55 * s_, (255, 196, 190, 70))
    def far(p):
        skyline(p, LW, LH, 1180, 3, (130, 92, 150, 255), (255, 214, 160), 160, 470, 70, 130, .25)
    def mid(p):
        skyline(p, LW, LH, 1300, 5, (84, 62, 118, 255), (255, 224, 150), 200, 640, 80, 150, .32)
        # fábrica con chimeneas
        p.rect(120, 1160, 560, 1300, (66, 52, 96))
        for i in range(4): p.poly([(120 + i * 110, 1160), (190 + i * 110, 1120), (190 + i * 110, 1160)], (66, 52, 96))
        for cxx in (180, 330, 470): p.rect(cxx, 940, cxx + 44, 1160, (58, 46, 86))
        for xx in range(150, 540, 34): p.rect(xx, 1196, xx + 20, 1226, (255, 214, 130))
        # torre de lanzamiento + cohete (siluetas)
        p.rect(960, 740, 982, 1300, (60, 46, 90))
        for yy in range(760, 1290, 40): p.line([(960, yy), (982, yy + 40)], (60, 46, 90), 4)
        p.rect(780, 1290, 1000, 1306, (50, 40, 76))
    def near(p):
        p.rect(0, 1340, LW, LH, (44, 36, 66))
        p.rect(0, 1340, LW, 1362, (72, 60, 98))
        for xx in range(-40, LW, 120): p.rect(xx, 1480, xx + 70, 1490, (255, 214, 150, 160))
        # árboles / farolas
        for xx in (80, 520, 940):
            p.rect(xx, 1100, xx + 10, 1350, (30, 26, 50)); p.ell(xx + 5, 1096, 16, 10, (255, 230, 170))
    _c["L"] = [Layer(bake(LW, LH, sky), LW, LH, ox=ox, par=.3, zpar=.5), Layer(bake(LW, LH, far), LW, LH, ox=ox, par=.5, zpar=.7),
               Layer(bake(LW, LH, mid), LW, LH, ox=ox, par=.75, zpar=.85), Layer(bake(LW, LH, near), LW, LH, ox=ox, par=1, zpar=1)]
    _c["rocket"] = rocket_icon(640)
    return _c["L"]


def scene(t):
    L = build()
    f = Frame(bg=False); base = f.base
    zt = ease_io(prog(t, 0, 7.6))
    cam = Cam(540 + 18 * math.sin(t * .4), 960 - 40 * zt, 1.0 + .26 * zt)
    for ly in L: ly.blit(base, cam)
    # humo de chimeneas
    for i in range(3):
        cx0 = 180 + 150 * i + 22
        for j in range(8):
            u = (t * .22 + j / 8 + i * .13) % 1
            x, y = cam.p(cx0 + 40 * u + math.sin(u * 6 + i) * 10, 940 - 330 * u, .85)
            r = (14 + 46 * u) * cam.z ** .85
            f.L.ellipse([x - r, y - r, x + r, y + r], fill=sc((200, 150, 170), .22 * (1 - u)))
    # cohete en la plataforma con llama de motores al final
    rk = _c["rocket"]
    rx, ry = cam.p(880, 1290, .85)
    zz = cam.z ** .85
    paste_np(base, rk.resize((int(rk.width * zz), int(rk.height * zz)), Image.LANCZOS), rx - rk.width * zz / 2, ry - rk.height * zz + 14 * zz)
    # autos eléctricos cruzando
    for q, (sp, yy, off, col) in enumerate(((220, 1440, 0, (232, 236, 244)), (-170, 1540, 400, (200, 60, 70)))):
        x = ((t * sp + off) % 1900) - 300 if sp > 0 else 1500 - ((t * -sp + off) % 1900)
        ic = car_icon(t * 8 * (1 if sp > 0 else -1), col)
        if sp < 0: ic = ic.transpose(Image.FLIP_LEFT_RIGHT)
        sx, sy = cam.p(x, yy, 1.0)
        put_icon(base, ic, sx, sy, scale=cam.z * .8)
    # monedas / "$" que suben mientras se habla de la fortuna
    ka = ease(prog(t, 3.2, 4.2)) * (1 - ease(prog(t, 6.2, 7.2)))
    if ka > 0:
        rng = np.random.RandomState(8)
        for i in range(26):
            x0 = rng.uniform(60, 1020); u = (t * rng.uniform(.18, .34) + rng.rand()) % 1
            y = 1500 - 1300 * u; r = rng.uniform(16, 30)
            f.L.ellipse([x0 - r, y - r, x0 + r, y + r], fill=sc((255, 200, 70), ka * .9 * (1 - abs(u - .5) * 1.2)), outline=sc((255, 240, 160), ka))
            f.L.text((x0 - r * .35, y - r * .65), "$", font=_font(int(r * 1.3)), fill=sc((140, 90, 10), ka))
    # Elon primer plano
    zk = ease_io(prog(t, 0, 7.6))
    turn = lerp(1.0, .15, ease(prog(t, 4.6, 6.2)))
    pose = mk(turn=turn, smile=lerp(.2, .75, ease(prog(t, 3.5, 6.0))), brow=lerp(.1, .5, ease(prog(t, 1, 3))), eyes=blink(t, 3.1, .4),
              head=lerp(2, -4, ease(prog(t, 3, 6))), lookx=lerp(0, 1.2, ease(prog(t, 4.6, 6))), sf=-4 + 3 * math.sin(t * 1.3), ef=10, sb=3, eb=8,
              lean=1.5 * math.sin(t * .9), bob=2 * math.sin(t * 1.6))
    place_person(base, "elon_adult", pose, 420, 1560 + 20 * (1 - zk), cam, k=1.65, depth=1.0)
    # luces: resplandor cálido y rayos
    for i in range(5):
        a = -.25 + i * .12 + .03 * math.sin(t * .5 + i)
        x0, y0 = 860, 780
        f.L.polygon([(x0, y0), (x0 + 1400 * math.cos(a + math.pi / 2 + .5), y0 + 1400 * math.sin(a + math.pi / 2 + .5)),
                     (x0 + 1400 * math.cos(a + math.pi / 2 + .62), y0 + 1400 * math.sin(a + math.pi / 2 + .62))], fill=sc((255, 200, 130), .08))
    dust(f, t, seed=3, n=50)
    out = f.finish()
    # título
    ta = ease(prog(t, .3, 1.0)) * (1 - ease(prog(t, 5.8, 6.6)))
    if ta > .01:
        ti = text_img("¿CÓMO SE CONVIRTIÓ", 66, (255, 255, 255), stroke=7, stroke_col=(10, 14, 36))
        t2 = text_img("ELON MUSK EN EL HOMBRE", 66, (255, 205, 90), stroke=7, stroke_col=(10, 14, 36))
        t3 = text_img("MÁS RICO DEL MUNDO?", 66, (255, 255, 255), stroke=7, stroke_col=(10, 14, 36))
        for i, im in enumerate((ti, t2, t3)):
            paste_np(out, im, (W - im.width) / 2, 150 + i * 84 + (1 - ta) * -30, ta)
    return out
