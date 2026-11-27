"""Escena 4 (37.5–45.8): la visión de Bezos — de libros a un enorme mercado digital."""
from amz import *
import a1
DUR = 8.3
CUT = 4.0
WH = .45
CATS = [("LIBROS", "book"), ("ELECTRÓNICA", "laptop"), ("JUGUETES", "toy"), ("ROPA", "shirt"), ("HOGAR", "lamp"), ("DEPORTE", "shoe")]
_c = {}


def store_img(w, h, t, mix_k):
    """Tienda: sólo libros -> se transforma en un catálogo variado (flip de tarjetas)."""
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=26, fill=(250, 252, 255, 255), outline=(40, 44, 60, 255), width=6)
    d.rectangle([0, 0, w, 90], fill=(30, 40, 70, 255)); d.text((30, 45), "amazon", font=ImageFont.truetype(FONT_BOLD, 52), fill=(255, 255, 255, 255), anchor="lm")
    for i, (lab, _) in enumerate(CATS):
        a = ease(prog(mix_k, .05 * i + (0 if i == 0 else .12), .05 * i + .3))
        if i == 0 or a > 0.01:
            x = 30 + i * 128; d.rounded_rectangle([x, 106, x + 118, 146], radius=10, fill=(255, 190, 70, 255) if i == 0 else (70, 130, 230, 255))
            d.text((x + 59, 126), lab[:7], font=ImageFont.truetype(FONT_BOLD, 17), fill=(20, 20, 40, 255), anchor="mm")
    bookcols = [(210, 70, 70), (70, 130, 210), (230, 190, 70), (90, 170, 120), (170, 100, 200), (240, 130, 70), (80, 190, 190), (200, 90, 150), (110, 120, 220)]
    for i in range(9):
        r, c = divmod(i, 3); x = 30 + c * ((w - 60) // 3); y = 176 + r * 250; ww = (w - 60) // 3 - 16
        k = clamp(mix_k * 1.6 - i * .09)                 # cada tarjeta se voltea en cadena
        flip = abs(math.cos(k * math.pi)) if k < 1 else 1.0
        hh = int(220 * max(flip, .06))
        d.rounded_rectangle([x, y + (220 - hh) / 2, x + ww, y + (220 - hh) / 2 + hh], radius=14, fill=(236, 240, 248, 255))
        if k < .5:
            if hh > 44: d.rounded_rectangle([x + 14, y + 14 + (220 - hh) / 2, x + ww - 14, y + (220 - hh) / 2 + hh - 14], radius=8, fill=bookcols[i] + (255,))
        elif i > 0:
            kind = ["", "laptop", "toy", "shirt", "lamp", "shoe", "headphones", "watch", "game"][i]
            pi = cached(("pr", kind, 120), lambda kind=kind: product(kind, 120)).resize((int(120 * .9), int(120 * .9)), Image.LANCZOS)
            im.alpha_composite(pi, (int(x + ww / 2 - 54), int(y + 220 / 2 - 54 + (220 - hh) / 2)))
        else:
            d.rounded_rectangle([x + 14, y + 14, x + ww - 14, y + 206], radius=8, fill=bookcols[0] + (255,))
    return im


def sub_vision(t, base, f):
    C = a1.build()
    cam = Cam(600, 1040, 1.0 + .10 * ease_io(prog(t, 0, 4.2)))
    C["S"].blit(base, cam)
    mk_ = ease_io(prog(t, 1.4, 3.6))
    st = store_img(600, 840, t, mk_)
    sx, sy = cam.p(700, 760); put_icon(base, st, sx, sy, scale=cam.z * 1.0)
    # Jeff piensa en grande: brazos cruzados -> señala la pantalla
    ge = ease(prog(t, 1.2, 2.0))
    pose = mk(turn=.3, smile=.9, brow=.5, head=lerp(-2, -7, ge), lookx=1.4, looky=-.6, sf=lerp(30, 110, ge), ef=lerp(110, 20, ge), sb=-8, eb=40, eyes=blink(t, 3, .2), lean=2)
    place_person(base, "bezos_young", pose, 270, 1200, cam, k=1.1)
    # destello de idea / halo detrás de la pantalla al transformarse
    if 1.4 < t < 3.8:
        a = math.sin(math.pi * prog(t, 1.4, 3.8))
        for q in range(14):
            ang = q / 14 * 6.28 + t; r0 = 340
            f.L.line([sx + math.cos(ang) * r0, sy + math.sin(ang) * r0 * 1.3, sx + math.cos(ang) * (r0 + 80 * a), sy + math.sin(ang) * (r0 + 80 * a) * 1.3], fill=sc((255, 220, 120), .8 * a), width=5)
    pe = ease(prog(t, 2.8, 3.4))
    if pe > .01:
        x = 90; y = 1300
        pass


def sub_grow(t, base, f):
    """Trabajadores preparan pedidos distintos, clientes compran y las instalaciones crecen."""
    C = a1.build()
    cam = Cam(540, 1040, 1.0 + .05 * prog(t, 0, 4.4))
    C["S"].blit(base, cam)
    kinds = ["headphones", "toy", "shirt", "laptop", "watch", "shoe"]
    bo = cached(("box",), lambda: box_icon(140))
    # fila de cajas con productos distintos avanzando
    for i in range(6):
        u = ((t * .35 + i / 6) % 1)
        x = 140 + u * 880; y = 1150 + 12 * math.sin(i)
        put_icon(base, bo, *cam.p(x, y), scale=cam.z * .8)
        pi = cached(("pr", kinds[i], 120), lambda i=i: product(kinds[i], 120)); put_icon(base, pi, *cam.p(x, y - 70), scale=cam.z * .5)
    for (nm, hx, flip, off, kind) in (("tech_w", 300, False, 0, "toy"), ("dev_f", 560, True, .4, "shirt"), ("dev_m", 800, True, .9, "laptop")):
        ph = (t * 1.0 + off) % 1
        pose = mk(sf=50 + 40 * math.sin(ph * 6.28), ef=40 + 30 * math.sin(ph * 6.28 + 1), sb=20, eb=30, smile=.5, turn=.2, eyes=blink(t, 3, off), head=-3, lean=10)
        place_person(base, nm, pose, hx, 1290, cam, k=1.0, flip=flip)
    # clientes comprando desde sus computadoras (recuadros en la parte superior)
    for (cx0, nm, off) in ((280, "cust_f", 0), (800, "cust_m", .6)):
        pan = Image.new("RGBA", (440, 330), (0, 0, 0, 0)); d = ImageDraw.Draw(pan)
        d.rounded_rectangle([0, 0, 439, 329], radius=24, fill=(255, 236, 214, 255), outline=(255, 255, 255, 255), width=5)
        paste_np(base, pan, cx0 - 220, 190, ease(prog(t, .3 + off, .8 + off)))
        al = ease(prog(t, .3 + off, .8 + off))
        mon = flat_monitor(170, t + off, "code"); put_icon(base, mon, cx0 + 80, 350, scale=1.0, alpha=al)
        pose = mk(sf=60 + 4 * math.sin(t * 8 + off), ef=20, turn=.3, smile=.7, eyes=blink(t, 3, off), head=-2, lean=6, hf=86, kf=84, hb=82, kb=80)
        place_person(base, nm, pose, cx0 - 60, 410, cam if False else Cam(540, 960, 1.0), k=.55, alpha=al)
        if int(t * 2 + off * 3) % 3 == 0:
            f.L.ellipse([cx0 + 40, 300, cx0 + 120, 380], outline=sc((120, 240, 160), al), width=5)
    # instalaciones que crecen: se agregan alas al edificio (línea de tiempo en miniatura)
    g = ease(prog(t, 2.2, 4.1))
    pn = Image.new("RGBA", (900, 250), (0, 0, 0, 0)); d = ImageDraw.Draw(pn)
    d.rounded_rectangle([0, 0, 899, 249], radius=24, fill=(12, 18, 44, 210), outline=(120, 200, 255, 255), width=4)
    for k in range(4):
        wd = 120 + 60 * k * g
        x = 40 + sum(150 + 50 * j * g for j in range(k))
        d.rounded_rectangle([x, 210 - (70 + 30 * k * g), x + wd, 210], radius=6, fill=(255, 190, 70, 255) if k == 3 else (70, 130, 230, 255))
    paste_np(base, pn, 90, 540, ease(prog(t, 2.0, 2.6)))


def scene(t):
    f = Frame(bg=False); base = f.base
    if t < CUT - WH / 2: sub_vision(t, base, f)
    elif t < CUT + WH / 2:
        a = np.zeros_like(base); b = np.zeros_like(base); fa = Frame(bg=False); fb = Frame(bg=False)
        sub_vision(t, a, fa); sub_grow(t - CUT, b, fb); p = (t - (CUT - WH / 2)) / WH
        base[:] = a * (1 - ease(p)) + b * ease(p) + 70 * math.sin(math.pi * p); return base
    else: sub_grow(t - CUT, base, f)
    dust(f, t, seed=63, n=26, tint=(255, 236, 200), alpha=.3)
    return f.finish()
