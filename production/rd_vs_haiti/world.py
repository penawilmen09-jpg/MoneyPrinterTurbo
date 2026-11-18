"""Componentes reutilizables de paisaje 2D."""
import math, random
from kit import *

_cache = {}
def cached(key, fn):
    if key not in _cache: _cache[key] = fn()
    return _cache[key]

SKY = {
 'day':  [(0, (52, 140, 232)), (.45, (132, 200, 248)), (.8, (214, 238, 250)), (1, (255, 244, 214))],
 'gold': [(0, (70, 130, 220)), (.4, (150, 200, 240)), (.75, (255, 226, 170)), (1, (255, 200, 130))],
 'haze': [(0, (90, 160, 226)), (.5, (170, 214, 244)), (1, (240, 240, 226))],
}

def mount_layer(base, amp, ctop, cbot, seed, f0=.005, trees=None, tcol=(30, 100, 44), w=W + 400, hi=None, ntree=700, power=1.4):
    f = ridge_fn(seed, f0, 5); xs = np.arange(0, w + 4, 4)
    ys = base - amp * (0.5 + 0.5 * f(xs)) ** power * 1.5
    mask = Image.new('L', (w, H), 0); pts = list(zip(xs.tolist(), ys.tolist())); ImageDraw.Draw(mask).polygon(pts + [(w, H), (0, H)], fill=255)
    layer = Image.new('RGBA', (w, H), (0, 0, 0, 0)); layer.paste(vgrad([(0, ctop), (min(1, (H - ys.min()) / H + .05), cbot), (1, cbot)], w, H), (0, 0), mask)
    d = ImageDraw.Draw(layer); r = random.Random(seed)
    if trees:
        for _ in range(ntree):
            i = r.randrange(len(xs)); x = xs[i]; y = ys[i] + r.random() ** 1.5 * min(320, (H - ys[i])) * .55; s = r.uniform(.8, 1.4) * (14 + (y - ys[i]) * .05)
            c = shade(tcol, r.uniform(.75, 1.25))
            if trees == 'pine': d.polygon([(x, y - s * 1.8), (x - s * .6, y), (x + s * .6, y)], fill=c)
            else: d.ellipse([x - s * .8, y - s * 1.1, x + s * .8, y + s * .2], fill=c)
    if hi: d.line(pts, fill=hi, width=3)
    return layer

def put_layer(img, layer, shift=0):
    img.alpha_composite(layer.crop((200, 0, 200 + W, H)) if shift == 0 else layer.crop((int(200 + shift), 0, int(200 + shift) + W, H)))

def sky(kind='day', sun=None, cl=None, t=0, haze=None):
    img = vgrad(SKY[kind]).convert('RGBA')
    if sun: sun_disc(img, sun[0], sun[1], sun[2] if len(sun) > 2 else 70)
    if cl: clouds(img, t, cl[0], cl[1], cl[2], cl[3] if len(cl) > 3 else 1.0, (255, 255, 255), 1)
    return img

def flag(d, x, y, w, kind, t, pole=True):
    h = w * .66; wave = lambda px: math.sin(px * .05 + t * 6) * 4
    if pole: d.rectangle([x - 5, y - 20, x, y + h + 380], fill=(200, 200, 205))
    cols = 14
    for i in range(cols):
        x0 = x + i * w / cols; x1 = x + (i + 1) * w / cols; o0 = wave(x0 - x); o1 = wave(x1 - x)
        def q(y0, y1, c): d.polygon([(x0, y + y0 * h + o0), (x1, y + y0 * h + o1), (x1, y + y1 * h + o1), (x0, y + y1 * h + o0)], fill=c)
        if kind == 'HT': q(0, .5, HT_BLUE); q(.5, 1, HT_RED)
        else:
            u0, u1 = i / cols, (i + 1) / cols
            wc = (255, 255, 255); q(0, 1, wc)
            for (a, b, c) in ((0, .42, DR_BLUE), (.58, 1, DR_RED)):
                pass
            if u1 <= .42 / 1.0 * 1.0 and False: pass
            # cuartos: azul/rojo arriba, rojo/azul abajo, cruz blanca central
            xa = (i + .5) / cols
            if xa < .42: q(0, .4, DR_BLUE); q(.6, 1, DR_RED)
            elif xa > .58: q(0, .4, DR_RED); q(.6, 1, DR_BLUE)
            else: pass
    return

def gable_house(d, x, yb, w, h, body, trim, roof, seed=0, shutter=(40, 130, 90), t=0, porch=True):
    r = random.Random(seed); rh = h * .42
    d.rectangle([x, yb - h, x + w, yb], fill=body)
    d.polygon([(x - w * .08, yb - h), (x + w / 2, yb - h - rh), (x + w * 1.08, yb - h)], fill=roof)
    d.polygon([(x + w * .25, yb - h - rh * .02), (x + w / 2, yb - h - rh * .58), (x + w * .75, yb - h - rh * .02)], fill=trim)
    d.ellipse([x + w * .42, yb - h - rh * .36, x + w * .58, yb - h - rh * .2], fill=shutter)
    for i in range(int(w // 14)):      # encaje decorativo (gingerbread)
        px = x - w * .06 + i * (w * 1.12 / int(w // 14)); d.polygon([(px, yb - h), (px + 6, yb - h), (px + 3, yb - h + 12)], fill=trim)
    nw = 2 if w < 160 else 3; ww = w / (nw * 2 + 1)
    for j in range(2 if h > 150 else 1):
        for i in range(nw):
            wx = x + ww * (1 + i * 2); wy = yb - h + 24 + j * h * .42
            d.rectangle([wx - 4, wy - 4, wx + ww + 4, wy + h * .3 + 4], fill=trim); d.rectangle([wx, wy, wx + ww, wy + h * .3], fill=(70, 100, 120))
            d.rectangle([wx - ww * .45, wy, wx - 4, wy + h * .3], fill=shutter); d.rectangle([wx + ww + 4, wy, wx + ww * 1.45, wy + h * .3], fill=shutter)
    d.rectangle([x + w * .42, yb - h * .35, x + w * .58, yb], fill=shade(roof, .8))
    if porch:
        d.rectangle([x - 6, yb - h * .38, x + w + 6, yb - h * .34], fill=trim)
        for i in range(0, int(w), 18): d.rectangle([x + i, yb - h * .34, x + i + 4, yb], fill=trim)
    d.rectangle([x, yb - 6, x + w, yb], fill=shade(body, .7))

def umbrella_stall(d, x, yb, w, c1, c2, items, seed=0, t=0):
    r = random.Random(seed); n = 8
    d.rectangle([x + 6, yb - w * .7, x + 12, yb], fill=(90, 70, 50)); d.rectangle([x + w - 12, yb - w * .7, x + w - 6, yb], fill=(90, 70, 50))
    for i in range(n):
        x0 = x - 14 + i * (w + 28) / n; x1 = x - 14 + (i + 1) * (w + 28) / n
        d.polygon([(x0, yb - w * .5), (x1, yb - w * .5), (x1 + 6 * (1 if i >= n / 2 else -1) * 0, yb - w * .78), (x0, yb - w * .78)], fill=c1 if i % 2 else c2)
        d.pieslice([x0 - 2, yb - w * .6, x1 + 2, yb - w * .4], 0, 180, fill=c1 if i % 2 else c2)
    d.rectangle([x, yb - w * .24, x + w, yb], fill=(120, 80, 48)); d.rectangle([x, yb - w * .26, x + w, yb - w * .22], fill=(150, 100, 60))
    for i in range(int(w / 22)):
        px = x + 12 + i * 22; col = items[r.randrange(len(items))]
        for k in range(3): d.ellipse([px + k * 5 - 2, yb - w * .26 - 20 - k * 4 * 0 + (k % 2) * -6, px + k * 5 + 16, yb - w * .26 + (k % 2) * -6], fill=shade(col, r.uniform(.85, 1.1)))

def bunting(d, x0, y0, x1, y1, cols, sag=40, n=14):
    pts = [(lerp(x0, x1, i / 40), lerp(y0, y1, i / 40) + sag * math.sin(math.pi * i / 40)) for i in range(41)]; d.line(pts, fill=(60, 50, 40), width=2)
    for i in range(n):
        p = pts[int(2 + i * 36 / n)]; c = cols[i % len(cols)]; d.polygon([(p[0] - 10, p[1]), (p[0] + 10, p[1]), (p[0], p[1] + 28)], fill=c)

def cypress(d, x, yb, h, col=(28, 90, 44)):
    d.ellipse([x - h * .22, yb - h, x + h * .22, yb], fill=col); d.ellipse([x - h * .16, yb - h * .95, x + h * .08, yb - h * .55], fill=shade(col, 1.25))

def broadtree(d, x, yb, h, col=(40, 130, 56), trunk=(90, 62, 40), sway=0):
    d.rectangle([x - h * .04, yb - h * .5, x + h * .04, yb], fill=trunk)
    for dx, dy, rr in ((0, .7, .32), (-.22, .55, .22), (.22, .55, .22), (.0, .9, .22)):
        d.ellipse([x + dx * h - rr * h + sway, yb - dy * h - rr * h, x + dx * h + rr * h + sway, yb - dy * h + rr * h], fill=shade(col, 1 + dx * .5))
    d.ellipse([x - h * .15 + sway, yb - h * .95, x + h * .05 + sway, yb - h * .75], fill=shade(col, 1.3))

def reflect_ripple(img, y0, y1, t, alpha=40):
    d = ImageDraw.Draw(img)
    for i in range(int((y1 - y0) / 18)):
        y = y0 + i * 18; d.line([(0, y + 4 * math.sin(t * 2 + i)), (W, y + 4 * math.cos(t * 1.7 + i * .8))], fill=(255, 255, 255, alpha), width=2)

def vignette_cache():
    yy, xx = np.mgrid[0:H // 4, 0:W // 4].astype(np.float32); d = np.hypot((xx - W / 8) / (W / 8), (yy - H / 8) / (H / 8))
    v = np.clip(1 - np.clip(d - .55, 0, 2) * .38, .45, 1)
    return np.asarray(Image.fromarray((v * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), np.float32)[..., None] / 255
