"""Kit de dibujo 2D procedural (PIL + numpy) para el documental RD vs Haití."""
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops

W, H, FPS = 1080, 1920, 24

def _norm(f):
    def g(self, xy, *a, **k):
        if len(xy) == 4 and not hasattr(xy[0], '__len__'):
            x0, y0, x1, y1 = xy; xy = [min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)]
        return f(self, xy, *a, **k)
    return g
for _n in ('rectangle', 'ellipse', 'pieslice', 'rounded_rectangle'):
    setattr(ImageDraw.ImageDraw, _n, _norm(getattr(ImageDraw.ImageDraw, _n)))
TAU = math.pi * 2
GT = 0.0   # tiempo global (s), lo fija el render
BPM = 96.0

def clamp(x, a=0.0, b=1.0): return a if x < a else (b if x > b else x)
def sm(x): x = clamp(x); return x * x * (3 - 2 * x)
def lerp(a, b, t): return a + (b - a) * t
def seg(t, a, b): return clamp((t - a) / (b - a))
def mix(c1, c2, t): return tuple(int(lerp(a, b, t)) for a, b in zip(c1, c2))
def hexc(s):
    s = s.lstrip('#'); return tuple(int(s[i:i+2], 16) for i in (0, 2, 4))
def shade(c, f): return tuple(int(clamp(v * f, 0, 255)) for v in c)

def vgrad(stops, w=W, h=H):
    ys = np.linspace(0, 1, h); pos = [s[0] for s in stops]
    arr = np.zeros((h, 3))
    for c in range(3): arr[:, c] = np.interp(ys, pos, [s[1][c] for s in stops])
    return Image.fromarray(np.repeat(arr[:, None, :], w, 1).astype(np.uint8))

def fbm_arr(w, h, seed, octs=5, base=4):
    rng = np.random.default_rng(seed); out = np.zeros((h, w), np.float32); amp = 1.0; tot = 0
    for o in range(octs):
        n = base * 2 ** o
        g = rng.random((max(2, int(n * h / w)) + 1, n + 1)).astype(np.float32)
        im = Image.fromarray((g * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
        out += np.asarray(im, np.float32) / 255 * amp; tot += amp; amp *= 0.5
    out /= tot
    return (out - out.min()) / (out.max() - out.min() + 1e-6)

def ridge_fn(seed, f0=0.004, octs=5, g=0.55):
    r = random.Random(seed); comps = [(f0 * 2.1 ** i, g ** i, r.random() * TAU) for i in range(octs)]
    def f(x):
        x = np.asarray(x, np.float64); s = 0
        for fr, a, ph in comps: s = s + a * np.sin(x * fr + ph)
        return s / sum(a for _, a, _ in comps)
    return f

def new_rgba(w=W, h=H): return Image.new('RGBA', (w, h), (0, 0, 0, 0))

def glow_circle(size, color, power=2.2):
    n = size; yy, xx = np.mgrid[0:n, 0:n]; d = np.hypot(xx - n / 2, yy - n / 2) / (n / 2)
    a = np.clip(1 - d, 0, 1) ** power
    arr = np.zeros((n, n, 4), np.uint8); arr[..., 0], arr[..., 1], arr[..., 2] = color
    arr[..., 3] = (a * 255).astype(np.uint8); return Image.fromarray(arr, 'RGBA')

_gc = {}
def glow(img, cx, cy, size, color, strength=1.0, power=2.2):
    k = (size, color, power)
    if k not in _gc: _gc[k] = glow_circle(size, color, power)
    g = _gc[k]
    if strength < 1: g = g.copy(); g.putalpha(g.getchannel('A').point(lambda v: int(v * strength)))
    img.alpha_composite(g, (int(cx - size / 2), int(cy - size / 2))) if (0 <= cx - size/2 and 0 <= cy - size/2 and cx + size/2 <= img.width and cy + size/2 <= img.height) else _paste_clip(img, g, int(cx - size / 2), int(cy - size / 2))

def _paste_clip(img, sp, x, y):
    x0, y0 = max(0, x), max(0, y); x1, y1 = min(img.width, x + sp.width), min(img.height, y + sp.height)
    if x1 <= x0 or y1 <= y0: return
    img.alpha_composite(sp.crop((x0 - x, y0 - y, x1 - x, y1 - y)), (x0, y0))

def camera(img, z=1.0, cx=0.5, cy=0.5, rot=0.0):
    """Cámara: zoom z centrado en (cx,cy) fracciones; devuelve imagen del mismo tamaño."""
    w, h = img.size
    if z == 1.0 and rot == 0: return img
    bw, bh = w / z, h / z
    x0 = clamp(cx * w - bw / 2, 0, w - bw); y0 = clamp(cy * h - bh / 2, 0, h - bh)
    return img.transform((w, h), Image.EXTENT, (x0, y0, x0 + bw, y0 + bh), Image.BILINEAR)

# ---------------- paletas ----------------
DR_BLUE, DR_RED = (0, 45, 98), (206, 17, 38)
HT_BLUE, HT_RED = (0, 32, 159), (210, 16, 52)
SKINS = [(92, 58, 38), (128, 84, 56), (160, 108, 72), (74, 46, 30), (190, 138, 98), (110, 70, 46)]

# ---------------- primitivas ----------------
def bez(p0, p1, p2, n=14):
    return [((1-t)**2*p0[0]+2*(1-t)*t*p1[0]+t*t*p2[0], (1-t)**2*p0[1]+2*(1-t)*t*p1[1]+t*t*p2[1]) for t in [i/n for i in range(n+1)]]

def thick_line(d, pts, w0, w1, color):
    n = len(pts)
    for i in range(n - 1):
        w = lerp(w0, w1, i / max(1, n - 1)); d.line([pts[i], pts[i+1]], fill=color, width=max(1, int(w)))
        d.ellipse([pts[i][0]-w/2, pts[i][1]-w/2, pts[i][0]+w/2, pts[i][1]+w/2], fill=color)

def palm(d, x, y, h, t=0.0, lean=0.0, seed=0, trunk=(112, 78, 46), leaf=(26, 120, 52), leaf2=(54, 160, 66)):
    r = random.Random(seed); sway = math.sin(t * 1.6 + seed) * 0.05 * h
    top = (x + lean * h + sway, y - h)
    pts = bez((x, y), (x + lean * h * 0.15, y - h * 0.55), top, 16)
    thick_line(d, pts, h * 0.07, h * 0.035, trunk)
    for i in range(1, 9, 2): 
        p = pts[i]; d.line([(p[0]-h*0.03, p[1]), (p[0]+h*0.03, p[1]+2)], fill=shade(trunk, .75), width=2)
    for k in range(9):
        a = -math.pi * 0.95 + k * (math.pi * 0.95 / 4.0) + math.sin(t * 1.9 + k + seed) * 0.05
        L = h * (0.52 + 0.1 * r.random()) * (0.62 if abs(math.sin(a)) > .93 else 1); droop = 0.38 + 0.15 * math.sin(t * 1.3 + k)
        tip = (top[0] + math.cos(a) * L, top[1] + math.sin(a) * L * 0.55 + L * droop)
        mid = (top[0] + math.cos(a) * L * 0.55, top[1] + math.sin(a) * L * 0.55 - L * 0.28)
        up = bez(top, mid, tip, 10); wid = h * 0.075
        poly = [(px, py - wid * math.sin(math.pi * i / 10)) for i, (px, py) in enumerate(up)] + \
               [(px, py + wid * 0.5 * math.sin(math.pi * i / 10)) for i, (px, py) in reversed(list(enumerate(up)))]
        d.polygon(poly, fill=leaf if k % 2 else leaf2)
        d.line(up, fill=shade(leaf, .8), width=2)
    for dx, dy in [(-6, 4), (6, 8), (0, 12)]:
        d.ellipse([top[0]+dx-h*.03, top[1]+dy-h*.03, top[0]+dx+h*.03, top[1]+dy+h*.03], fill=(90, 62, 36))

def cloud_sprite(w, h, seed, color=(255, 255, 255), alpha=235):
    r = random.Random(seed); im = Image.new('L', (w, h), 0); d = ImageDraw.Draw(im)
    for _ in range(14):
        cx = r.uniform(w * .15, w * .85); cy = r.uniform(h * .45, h * .8); rr = r.uniform(h * .18, h * .38)
        d.ellipse([cx - rr * 1.5, cy - rr, cx + rr * 1.5, cy + rr], fill=255)
    d.rectangle([0, h * .82, w, h], fill=0)
    im = im.filter(ImageFilter.GaussianBlur(h * 0.06)).point(lambda v: int(v * alpha / 255))
    out = Image.new('RGBA', (w, h), color + (0,)); out.putalpha(im)
    # sombra inferior suave
    sh = Image.new('RGBA', (w, h), shade(color, .82) + (0,)); m = ImageChops.subtract(im, im.transform((w, h), Image.AFFINE, (1, 0, 0, 0, 1, -h * .12)))
    sh.putalpha(m.filter(ImageFilter.GaussianBlur(4))); out = Image.alpha_composite(out, sh)
    return out

_cl = {}
def clouds(img, t, y0, n, speed, scale=1.0, tint=(255, 255, 255), seed=1, alpha=235):
    for i in range(n):
        k = (seed, i % 6, tint)
        if k not in _cl: _cl[k] = cloud_sprite(int(520 * scale), int(190 * scale), seed * 31 + i % 6, tint, alpha)
        sp = _cl[k]; span = W + sp.width * 2
        x = (i * span / n + t * speed) % span - sp.width
        y = y0 + (i * 137 % 260) * scale - 100
        _paste_clip(img, sp, int(x), int(y))

def bird(d, x, y, s, t, color=(40, 40, 50)):
    f = math.sin(t * 9 + x * 0.05) * 0.6
    d.line([(x - s, y - s * f * .6), (x - s * .4, y - s * .35 + s * f * .3), (x, y)], fill=color, width=max(2, int(s * .18)))
    d.line([(x + s, y - s * f * .6), (x + s * .4, y - s * .35 + s * f * .3), (x, y)], fill=color, width=max(2, int(s * .18)))

def person(d, x, yb, h, skin, shirt, pants, ph=0.0, walk=True, hat=None, carry=None, facing=1, hair=(25, 18, 14), skirt=False, arms_up=False, dance=0.0):
    """Figura estilizada. (x,yb)=pies. h=altura total."""
    u = h / 10.0; sw = math.sin(ph) if walk else 0.0
    bob = abs(math.cos(ph)) * u * 0.15 if walk else math.sin(dance) * u * 0.2
    hipy = yb - u * 4.3 - bob; shy = hipy - u * 3.0; hdy = shy - u * 1.35
    sx = x + math.sin(dance * .5) * u * .25 * (1 if dance else 0)
    # piernas
    if skirt:
        d.polygon([(sx - u * 1.3, hipy), (sx + u * 1.3, hipy), (sx + u * 1.9, hipy + u * 2.6), (sx - u * 1.9, hipy + u * 2.6)], fill=pants)
        for s_ in (-1, 1):
            fx = sx + s_ * u * .5 + sw * s_ * u * .9 * facing
            d.line([(sx + s_ * u * .4, hipy + u * 2.6), (fx, yb)], fill=skin, width=int(u * .7))
    else:
        for s_ in (-1, 1):
            fx = sx + s_ * u * .4 + sw * s_ * u * 1.0 * facing
            d.line([(sx + s_ * u * .4, hipy), (fx, yb - u * .3)], fill=pants, width=int(u * .95))
            d.ellipse([fx - u * .5, yb - u * .5, fx + u * .7 * facing + u * .4, yb + u * .1], fill=(30, 24, 22))
    # torso
    d.polygon([(sx - u * 1.2, shy), (sx + u * 1.2, shy), (sx + u * 1.0, hipy + u * .2), (sx - u * 1.0, hipy + u * .2)], fill=shirt)
    # brazos
    for s_ in (-1, 1):
        if arms_up:
            hx = sx + s_ * (u * 1.8 + math.sin(dance + s_) * u * .5); hy = shy - u * 1.9 - math.sin(dance * 1.3 + s_) * u * .5
        else:
            sw2 = -sw * s_ if walk else math.sin(dance + s_) * .5
            hx = sx + s_ * u * 1.3 + sw2 * u * .6 * facing; hy = hipy - u * .3 + abs(sw2) * -u * .2
        if carry == 'head': hx = sx + s_ * u * 1.5; hy = shy - u * 1.6
        d.line([(sx + s_ * u * 1.1, shy + u * .3), (hx, hy)], fill=shirt, width=int(u * .8))
        d.ellipse([hx - u * .4, hy - u * .4, hx + u * .4, hy + u * .4], fill=skin)
    # cabeza
    d.rectangle([sx - u * .35, shy - u * .5, sx + u * .35, shy + u * .1], fill=skin)
    d.ellipse([sx - u * .95, hdy - u * 1.05, sx + u * .95, hdy + u * .95], fill=skin)
    d.pieslice([sx - u * 1.0, hdy - u * 1.15, sx + u * 1.0, hdy + u * .9], 180, 360, fill=hair)
    if hat == 'straw':
        d.ellipse([sx - u * 2.0, hdy - u * .9, sx + u * 2.0, hdy - u * .1], fill=(226, 190, 100))
        d.pieslice([sx - u * 1.0, hdy - u * 1.7, sx + u * 1.0, hdy], 180, 360, fill=(240, 210, 120))
    elif hat == 'cap':
        d.pieslice([sx - u * 1.05, hdy - u * 1.3, sx + u * 1.05, hdy + u * .5], 180, 360, fill=(200, 30, 40))
        d.rectangle([sx, hdy - u * .3, sx + u * 1.5 * facing, hdy - u * .1], fill=(200, 30, 40))
    elif hat == 'scarf':
        d.pieslice([sx - u * 1.05, hdy - u * 1.3, sx + u * 1.05, hdy + u * .5], 180, 360, fill=(230, 170, 30))
    if carry == 'head':
        d.ellipse([sx - u * 1.7, hdy - u * 2.0, sx + u * 1.7, hdy - u * .6], fill=(200, 140, 70))
        for i, c in enumerate([(230, 60, 40), (250, 190, 30), (60, 170, 70)]):
            d.ellipse([sx - u * 1.3 + i * u * .9, hdy - u * 2.6, sx - u * .5 + i * u * .9, hdy - u * 1.8], fill=c)
    elif carry == 'bag':
        d.rectangle([sx + u * .6 * facing, hipy - u * .2, sx + u * 2.0 * facing, hipy + u * 1.8], fill=(210, 180, 120))
    elif carry == 'jug':
        d.rectangle([sx + u * 1.2, hipy - u * .2, sx + u * 2.3, hipy + u * 1.5], fill=(250, 210, 40))

def car(d, x, y, w, color, ph=0.0, flip=False, kind='car'):
    h = w * 0.36
    def fx(px): return x + (w - px) if flip else x + px
    body = [(0, h * .55), (w * .05, h * .35), (w * .25, h * .32), (w * .35, h * .02), (w * .68, h * .02), (w * .82, h * .32), (w * .97, h * .38), (w, h * .6), (w, h * .78), (0, h * .78)]
    d.polygon([(fx(px), y - h + py) for px, py in body], fill=color)
    win = [(w * .37, h * .1), (w * .66, h * .1), (w * .76, h * .32), (w * .3, h * .32)]
    d.polygon([(fx(px), y - h + py) for px, py in win], fill=(170, 215, 235))
    d.line([(fx(w * .52), y - h + h * .1), (fx(w * .52), y - h + h * .32)], fill=color, width=3)
    for cx in (w * .22, w * .78):
        X = fx(cx); R = h * .26
        d.ellipse([X - R, y - R * 1.6 + h * .02, X + R, y + R * .4 + h * .02], fill=(25, 25, 28))
        d.ellipse([X - R * .55, y - R * 1.15 + h * .02, X + R * .55, y - R * .05 + h * .02], fill=(190, 190, 200))
        a = ph * (-1 if flip else 1)
        d.line([(X, y - R * .6 + h * .02), (X + math.cos(a) * R * .5, y - R * .6 + h * .02 + math.sin(a) * R * .5)], fill=(90, 90, 100), width=3)
    d.rectangle([fx(w * .97 if not flip else w * .0) - 6, y - h * .55, fx(w * .97 if not flip else w * .0) + 6, y - h * .42], fill=(255, 240, 160))

def tap_tap(d, x, y, w, base, accent, ph=0.0, flip=False, load=True):
    h = w * 0.62
    def fx(px): return x + (w - px) if flip else x + px
    def poly(pts, c): d.polygon([(fx(px), y - h + py) for px, py in pts], fill=c)
    poly([(0, h * .35), (w * .08, h * .1), (w * .78, h * .1), (w * .92, h * .38), (w, h * .5), (w, h * .86), (0, h * .86)], base)
    poly([(0, h * .55), (w, h * .55), (w, h * .66), (0, h * .66)], accent)
    for i in range(4):
        wx = w * (.1 + i * .17); poly([(wx, h * .2), (wx + w * .13, h * .2), (wx + w * .13, h * .44), (wx, h * .44)], (160, 210, 230))
    poly([(w * .8, h * .14), (w * .9, h * .38), (w * .8, h * .38)], (160, 210, 230))
    for i in range(7):
        poly([(w * i / 7, h * .7), (w * (i + .5) / 7, h * .7), (w * (i + .25) / 7, h * .82)], accent if i % 2 else (255, 255, 255))
    if load:
        poly([(w * .05, h * .1), (w * .75, h * .1), (w * .75, h * .04), (w * .05, h * .04)], (80, 60, 40))
        for i, c in enumerate([(230, 170, 60), (60, 140, 80), (220, 80, 60), (240, 220, 120)]):
            bx = w * (.1 + i * .16); poly([(bx, h * .04), (bx + w * .14, h * .04), (bx + w * .12, -h * .12), (bx + w * .02, -h * .12)], c)
    for cx in (w * .2, w * .78):
        X = fx(cx); R = h * .17
        d.ellipse([X - R, y - R * 1.7 + h * .1, X + R, y + R * .3 + h * .1], fill=(25, 25, 28))
        d.ellipse([X - R * .5, y - R * 1.2 + h * .1, X + R * .5, y - R * .2 + h * .1], fill=(200, 200, 205))
        a = ph * (-1 if flip else 1); d.line([(X, y - R * .7 + h * .1), (X + math.cos(a) * R * .45, y - R * .7 + h * .1 + math.sin(a) * R * .45)], fill=(90, 90, 100), width=3)

def sailboat(d, x, y, s, t, hull=(120, 70, 40), sail=(250, 250, 240), sail2=None, bob=True):
    off = math.sin(t * 1.8 + x * .01) * s * .04 if bob else 0; y += off
    d.polygon([(x - s * .6, y - s * .1), (x + s * .6, y - s * .1), (x + s * .4, y + s * .12), (x - s * .4, y + s * .12)], fill=hull)
    d.line([(x - s * .6, y - s * .1), (x + s * .6, y - s * .1)], fill=shade(hull, 1.4), width=3)
    d.line([(x, y - s * .1), (x, y - s * 1.1)], fill=(70, 50, 30), width=max(2, int(s * .03)))
    d.polygon([(x + s * .04, y - s * 1.05), (x + s * .04, y - s * .18), (x + s * .5, y - s * .18)], fill=sail)
    d.polygon([(x - s * .04, y - s * .95), (x - s * .04, y - s * .18), (x - s * .42, y - s * .18)], fill=sail2 or shade(sail, .93))

def sea_waves(d, y0, y1, t, c1, c2, amp=10, spacing=34, speed=1.0, k=0.02, foam=(255, 255, 255)):
    n = int((y1 - y0) / spacing) + 1
    for i in range(n):
        y = y0 + i * spacing; f = i / max(1, n - 1); col = mix(c1, c2, f)
        pts = [(x, y + amp * (0.4 + f) * math.sin(x * k * (1 + f * .8) + t * speed * (1 + f) + i * 1.7)) for x in range(-20, W + 40, 20)]
        d.polygon(pts + [(W + 40, y1 + 40), (-20, y1 + 40)], fill=col)

def sun_disc(img, x, y, r, c=(255, 240, 190), halo=(255, 200, 120)):
    glow(img, x, y, int(r * 7), halo, .55, 2.0); glow(img, x, y, int(r * 3.2), halo, .8, 2.4)
    d = ImageDraw.Draw(img); d.ellipse([x - r, y - r, x + r, y + r], fill=c + (255,))

def building(d, x, yb, w, h, col, win=(255, 224, 140), lit=0.5, seed=0, roof=None, rows=None):
    r = random.Random(seed); d.rectangle([x, yb - h, x + w, yb], fill=col)
    d.rectangle([x, yb - h, x + w * .06, yb], fill=shade(col, .8))
    d.rectangle([x + w * .94, yb - h, x + w, yb], fill=shade(col, 1.15))
    ww = max(8, int(w / 6.5)); cols = max(1, int((w - ww) / (ww * 1.9))); rws = rows or max(1, int((h - 30) / (ww * 2.1)))
    for i in range(cols):
        for j in range(rws):
            wx = x + ww * .9 + i * ww * 1.9; wy = yb - h + 20 + j * ww * 2.1
            if wx + ww > x + w - 4 or wy + ww * 1.4 > yb - 8: continue
            c = win if r.random() < lit else shade(col, .62)
            d.rectangle([wx, wy, wx + ww, wy + ww * 1.4], fill=c)
    if roof == 'tower': d.rectangle([x + w * .35, yb - h - 28, x + w * .65, yb - h], fill=shade(col, .9)); d.line([(x + w * .5, yb - h - 28), (x + w * .5, yb - h - 70)], fill=(60, 60, 70), width=4)
    if roof == 'dome': d.pieslice([x + w * .15, yb - h - w * .35, x + w * .85, yb - h + w * .35], 180, 360, fill=shade(col, .85))

def texture_overlay(img, amount=10, seed=3):
    """Textura pictórica suave."""
    global _tex
    try: _tex
    except NameError: _tex = None
    if _tex is None: _tex = (fbm_arr(W // 2, H // 2, seed, 4, 12) - .5)
    t = Image.fromarray(((_tex * 255 * amount / 10) + 128).clip(0, 255).astype(np.uint8)).resize(img.size, Image.BICUBIC)
    return ImageChops.overlay(img.convert('RGB'), Image.merge('RGB', (t, t, t))) if amount else img
