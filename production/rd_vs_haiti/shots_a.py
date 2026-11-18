import math, random
from kit import *
from world import *
from kit import _paste_clip

def put(img, layer, shift=0, dy=0):
    _paste_clip(img, layer.crop((int(200 + shift), 0, int(200 + shift) + W, H)), 0, int(dy))

def donkey(d, x, y, s, ph, col=(130, 120, 110), load=True, facing=1):
    f = facing; b = math.sin(ph) * s * .05
    d.ellipse([x - s * .5, y - s * .75 + b, x + s * .5, y - s * .3 + b], fill=col)
    d.polygon([(x + f * s * .4, y - s * .6 + b), (x + f * s * .72, y - s * .95), (x + f * s * .84, y - s * .85), (x + f * s * .6, y - s * .5 + b)], fill=col)
    d.polygon([(x + f * s * .72, y - s * .95), (x + f * s * .68, y - s * 1.12), (x + f * s * .78, y - s * .96)], fill=col)
    for i, (lx, sg) in enumerate(((-.35, 1), (-.2, -1), (.25, 1), (.4, -1))):
        a = math.sin(ph + (0 if sg > 0 else math.pi)) * s * .1; d.line([(x + lx * s, y - s * .4), (x + lx * s + a, y)], fill=shade(col, .7), width=max(3, int(s * .06)))
    if load:
        d.rectangle([x - s * .38, y - s * 1.0 + b, x + s * .3, y - s * .66 + b], fill=(200, 160, 90)); d.rectangle([x - s * .3, y - s * 1.14 + b, x + s * .22, y - s * 1.0 + b], fill=(70, 150, 80))

# ============ S2a PLAYA DOMINICANA ============
def shot_beach(t, mode='DR'):
    hz = 930
    img = cached(('beach_sky', mode), lambda: sky('day' if mode == 'DR' else 'gold', (800, 250, 62) if mode == 'DR' else (260, 420, 70))).copy()
    clouds(img, t, 130, 5, 7, 1.3, (255, 255, 255) if mode == 'DR' else (255, 235, 210), 1)
    put(img, cached(('bm', mode), lambda: mount_layer(hz + 8, 170, (105, 165, 150), (150, 198, 188), 5, .0045, 'broad', (70, 130, 100), hi=(190, 225, 210, 255))), t * 2)
    d = ImageDraw.Draw(img)
    if mode == 'HT':     # ladera con casitas coloridas
        put(img, cached('ht_hill', lambda: mount_layer(hz + 8, 280, (70, 150, 70), (50, 120, 56), 14, .0035, 'broad', (40, 110, 50), ntree=500)), t * 3)
        r = random.Random(3)
        for i in range(38):
            x = 420 + r.random() * 640; y = hz - 40 - r.random() * 150 + (x - 420) * .0; c = [(236, 90, 70), (250, 200, 60), (70, 160, 220), (240, 240, 230), (120, 200, 120), (230, 130, 190)][r.randrange(6)]
            d.rectangle([x, y, x + 34, y + 24], fill=c); d.polygon([(x - 3, y), (x + 17, y - 12), (x + 37, y)], fill=shade(c, .6))
    sea_waves(d, hz - 6, 1430, t, (24, 112, 188), (92, 220, 214), 7, 30, 1.3, 0.013)
    # destellos
    r = random.Random(2)
    for i in range(40):
        x = r.random() * W; y = hz + 20 + r.random() ** .6 * 440; a = (math.sin(t * 5 + i * 1.7) + 1) / 2; L = 14 + (y - hz) * .06
        d.line([(x, y), (x + L, y)], fill=(255, 255, 255, int(200 * a)), width=2)
    # velas
    if mode == 'DR':
        sailboat(d, 300 + t * 6, 1060, 150, t, (230, 230, 230), (255, 255, 255), (230, 240, 255)); sailboat(d, 760, 1005, 90, t + 2, (240, 240, 240), (255, 250, 240))
    else:
        sailboat(d, 280 + t * 5, 1070, 170, t, (50, 100, 150), (235, 140, 70), (200, 90, 70)); sailboat(d, 740, 1010, 100, t + 2, (180, 60, 50), (250, 220, 120), (90, 160, 210))
    # arena + espuma
    sx = lambda x: 1395 + 24 * math.sin(t * .9) + 12 * math.sin(x * .011 + t * 1.1) + (x * .02)
    xs = list(range(-20, W + 40, 20))
    d.polygon([(x, sx(x) - 8) for x in xs] + [(W + 40, H), (-20, H)], fill=(222, 196, 146))
    d.polygon([(x, sx(x) + 30) for x in xs] + [(W + 40, H), (-20, H)], fill=(240, 220, 172))
    d.polygon([(x, sx(x) + 90 + 14 * math.sin(x * .02)) for x in xs] + [(W + 40, H), (-20, H)], fill=(248, 232, 188))
    fo = new_rgba(); fd = ImageDraw.Draw(fo)
    for k, (off, al) in enumerate(((-30, 90), (-14, 160), (-2, 235))):
        fd.polygon([(x, sx(x) + off - 14 - 10 * math.sin(x * .03 + t * 2 + k)) for x in xs] + [(x, sx(x) + off + 6) for x in reversed(xs)], fill=(255, 255, 255, al))
    img.alpha_composite(fo); d = ImageDraw.Draw(img)
    # sombrilla y tumbonas
    ux, uy = 770, 1640
    d.line([(ux, uy), (ux - 10, uy - 320)], fill=(240, 240, 240), width=8)
    for i in range(8):
        a0 = math.pi + i * math.pi / 8; a1 = a0 + math.pi / 8
        d.polygon([(ux - 10, uy - 320), (ux - 10 + math.cos(a0) * 220, uy - 320 + math.sin(a0) * -110 + 60), (ux - 10 + math.cos(a1) * 220, uy - 320 + math.sin(a1) * -110 + 60)], fill=(220, 40, 50) if i % 2 else (250, 250, 250))
    d.rectangle([620, 1640, 700, 1655], fill=(60, 120, 200)); d.polygon([(700, 1640), (740, 1610), (748, 1618), (710, 1655)], fill=(60, 120, 200))
    # pareja caminando por la orilla
    ph = t * 4.2
    person(d, 120 + t * 62, 1540, 200, SKINS[1], (240, 90, 90), (250, 250, 250), ph, hat='straw'); person(d, 200 + t * 62, 1548, 190, SKINS[0], (255, 255, 255), (60, 120, 200), ph + 1, skirt=True, hair=(20, 14, 10))
    # palmeras
    palm(d, 80, 1700, 980, t, .14, 1); palm(d, 990, 1760, 820, t + 1, -.12, 2); palm(d, 470, 1480, 330, t + 2, .08, 3)
    for i in range(5): bird(d, 640 + i * 60 + 40 * math.sin(t + i), 330 + i * 26 + 15 * math.cos(t * .8 + i), 24 - i * 2, t + i * .3, (50, 50, 60))
    img.alpha_composite(sunflare(t)) if False else None
    return camera(img.convert('RGB'), 1 + .035 * t, .52, .55)

# ============ S2b SANTO DOMINGO ============
def city_layer(seed, base, hmin, hmax, wmin, wmax, cols, w=W + 400, lit=.5, hazec=None):
    r = random.Random(seed); layer = new_rgba(w, H); d = ImageDraw.Draw(layer); x = -20
    while x < w:
        bw = r.randint(wmin, wmax); bh = r.randint(hmin, hmax); c = cols[r.randrange(len(cols))]
        building(d, x, base, bw, bh, c, lit=lit, seed=r.randint(0, 999), roof=r.choice([None, None, 'tower']))
        x += bw + r.randint(-6, 12)
    if hazec: layer.alpha_composite(Image.new('RGBA', (w, H), hazec))
    return layer

def cathedral(d, x, yb, w=330, h=330):
    c = (232, 206, 156); d.rectangle([x, yb - h, x + w, yb], fill=c)
    for (a, b) in ((0, .2), (.8, 1)): d.rectangle([x + w * a, yb - h * 1.28, x + w * b, yb - h], fill=shade(c, .96)); d.rectangle([x + w * a, yb - h * 1.28, x + w * b, yb], fill=shade(c, .96))
    d.polygon([(x - 8, yb - h), (x + w / 2, yb - h * 1.2), (x + w + 8, yb - h)], fill=(200, 170, 120))
    for i, cx in enumerate((.18, .5, .82)):
        d.rectangle([x + w * cx - 24, yb - 110 - (30 if i == 1 else 0), x + w * cx + 24, yb], fill=(100, 70, 50)); d.pieslice([x + w * cx - 24, yb - 134 - (30 if i == 1 else 0), x + w * cx + 24, yb - 86 - (30 if i == 1 else 0)], 180, 360, fill=(100, 70, 50))
    d.ellipse([x + w / 2 - 30, yb - h * .86, x + w / 2 + 30, yb - h * .86 + 60], fill=(120, 150, 190), outline=(180, 150, 100), width=5)
    for cx in (.1, .9): d.pieslice([x + w * cx - 30, yb - h * 1.28 - 40, x + w * cx + 30, yb - h * 1.28 + 40], 180, 360, fill=(190, 80, 60)); d.rectangle([x + w * cx - 2, yb - h * 1.28 - 70, x + w * cx + 2, yb - h * 1.28 - 38], fill=(80, 70, 60))

def shot_city(t):
    pan = t * 55
    img = cached('sd_sky', lambda: sky('gold', (830, 650, 90))).copy(); clouds(img, t, 150, 6, 9, 1.2, (255, 236, 205), 4, 220)
    put(img, cached('sd_far', lambda: city_layer(5, 1180, 120, 380, 60, 120, [(150, 175, 205), (162, 186, 212), (140, 168, 198)], lit=.2, hazec=(230, 215, 220, 90))), pan * .25)
    put(img, cached('sd_mid', lambda: city_layer(8, 1290, 90, 260, 80, 150, [(236, 190, 150), (232, 160, 130), (244, 214, 160), (170, 200, 220), (220, 130, 120)], lit=.4)), pan * .6)
    d = ImageDraw.Draw(img); cathedral(d, 330 - pan * .8, 1290)
    put(img, cached('sd_tow', lambda: city_layer(11, 1420, 380, 780, 120, 190, [(110, 150, 190), (130, 160, 200), (96, 130, 170), (170, 190, 205)], lit=.55)), pan * 1.0)
    d = ImageDraw.Draw(img)
    # suelo: malecón
    d.rectangle([0, 1420, W, H], fill=(86, 90, 98)); d.rectangle([0, 1420, W, 1450], fill=(70, 150, 70)); d.rectangle([0, 1450, W, 1480], fill=(200, 194, 180))
    d.rectangle([0, 1790, W, H], fill=(205, 198, 184)); d.rectangle([0, 1784, W, 1794], fill=(160, 155, 145))
    for i in range(-1, 12): d.rectangle([i * 150 - (pan * 1.6 % 150), 1635, i * 150 + 80 - (pan * 1.6 % 150), 1645], fill=(235, 225, 150))
    cols = [(220, 40, 50), (240, 240, 245), (40, 90, 170), (250, 200, 40), (60, 60, 66), (30, 150, 110)]
    for i in range(5):    # carriles lejanos hacia la izq
        x = (W + 400 - ((t * (150 + i * 20) + i * 330) % (W + 500))) - 200; car(d, x, 1585, 230, cols[i % 6], t * 14, flip=True)
    for i in range(4):
        x = ((t * (190 + i * 25) + i * 380) % (W + 600)) - 300; car(d, x, 1745, 300, cols[(i + 2) % 6], t * 16)
    # motoconcho
    mx = ((t * 330 + 200) % (W + 500)) - 250; d.ellipse([mx, 1690, mx + 70, 1760], fill=(25, 25, 28)); d.ellipse([mx + 120, 1690, mx + 190, 1760], fill=(25, 25, 28)); d.polygon([(mx + 35, 1700), (mx + 150, 1690), (mx + 160, 1640), (mx + 70, 1650)], fill=(230, 160, 30)); person(d, mx + 105, 1690, 150, SKINS[2], (40, 100, 190), (40, 40, 50), 0, walk=False)
    for i, x in enumerate((60, 330, 640, 930)): palm(d, (x - pan * 1.2) % (W + 300) - 100, 1462, 360, t + i, (-1) ** i * .08, i + 7)
    for i in range(4): person(d, (150 + i * 280 - pan * 1.6) % (W + 300) - 100, 1900, 250, SKINS[i % 6], [(240, 100, 80), (80, 160, 220), (250, 220, 90), (130, 200, 110)][i], [(60, 60, 80), (230, 230, 235), (50, 90, 150), (90, 60, 50)][i], t * 4 + i, hat=['straw', None, 'cap', None][i], carry=[None, 'bag', None, None][i])
    return camera(img.convert('RGB'), 1 + .02 * t, .5, .5)

# ============ S2c MONTAÑAS + RESORT ============
def mountains(img, t, spec, dy=0, pan=0):
    for i, (nm, kw, par) in enumerate(spec): put(img, cached(nm, lambda kw=kw: mount_layer(**kw)), pan * par, dy * par)

DR_MTN = [('drm1', dict(base=800, amp=360, ctop=(120, 150, 190), cbot=(150, 190, 214), seed=31, f0=.0035, hi=(220, 235, 250, 255)), .12),
          ('drm2', dict(base=930, amp=330, ctop=(70, 130, 110), cbot=(100, 160, 130), seed=32, f0=.004, trees='pine', tcol=(30, 90, 70), ntree=900, hi=(170, 215, 180, 255)), .25),
          ('drm3', dict(base=1070, amp=300, ctop=(38, 112, 70), cbot=(28, 90, 56), seed=33, f0=.005, trees='pine', tcol=(20, 80, 48), ntree=1000, hi=(130, 200, 120, 255)), .5)]

def mist(img, t, y0, y1, a=90, speed=14, seed=0):
    for i in range(4):
        sp = cached(('mist', seed, i), lambda i=i: cloud_sprite(1300, 260, 40 + i + seed, (255, 255, 255), a)); x = (t * speed * (1 + i * .3) + i * 400) % (W + 1300) - 1300
        _paste_clip(img, sp, int(x), int(lerp(y0, y1, i / 3)))

def shot_resort(t):
    pan = t * 40
    img = cached('rs_sky', lambda: sky('haze', (180, 330, 60))).copy(); clouds(img, t, 120, 4, 8, 1.2, (255, 255, 255), 6, 230)
    mountains(img, t, DR_MTN, 0, pan); mist(img, t, 560, 980, 110, 18)
    d = ImageDraw.Draw(img)
    for i in range(6): bird(d, 240 + i * 90 + 30 * math.sin(t + i), 420 + i * 15, 20, t + i * .4)
    # hotel
    hy = 1470
    for i, (x, w, h, c) in enumerate(((-30, 360, 330, (250, 244, 232)), (300, 420, 420, (252, 250, 244)), (700, 400, 300, (248, 238, 222)))):
        d.rectangle([x, hy - h, x + w, hy], fill=c); d.rectangle([x, hy - h, x + w, hy - h + 16], fill=shade(c, .85))
        for r_ in range(int(h // 72)):
            for k in range(int(w // 70)):
                bx = x + 20 + k * 70; by = hy - h + 40 + r_ * 72; d.rectangle([bx, by, bx + 50, by + 46], fill=(120, 180, 210)); d.rectangle([bx - 4, by + 46, bx + 54, by + 54], fill=[(240, 120, 90), (80, 170, 200), (250, 200, 80)][(r_ + i) % 3])
    d.polygon([(320, hy - 420), (720, hy - 420), (700, hy - 470), (340, hy - 470)], fill=(220, 90, 70))
    for x in (10, 880): palm(d, x, hy + 12, 360, t + x, .1, x)
    # piscina
    py0 = 1540; d.rectangle([0, hy, W, H], fill=(236, 226, 200)); pool = new_rgba(); pd = ImageDraw.Draw(pool); pd.rounded_rectangle([60, py0, 1020, 1800], 60, fill=(38, 190, 214, 255))
    for i in range(16):
        y = py0 + 20 + i * 16; pd.line([(70, y + 5 * math.sin(t * 2 + i)), (1010, y + 5 * math.cos(t * 1.7 + i))], fill=(160, 240, 245, 120), width=3)
    for i in range(9):
        a = (math.sin(t * 3 + i * 2.1) + 1) / 2; cx = 120 + i * 105; pd.ellipse([cx, py0 + 60 + 90 * ((i * .37) % 1), cx + 46, py0 + 78 + 90 * ((i * .37) % 1)], fill=(255, 255, 255, int(120 * a)))
    img.alpha_composite(pool); d = ImageDraw.Draw(img); d.rounded_rectangle([60, py0, 1020, 1800], 60, outline=(250, 250, 245), width=14)
    for i, x in enumerate((130, 560, 850)):      # palapas y tumbonas
        d.rectangle([x + 40, 1830, x + 50, 1900], fill=(110, 80, 50)); d.polygon([(x - 40, 1830), (x + 130, 1830), (x + 45, 1770)], fill=(200, 160, 90))
    for i, x in enumerate((150, 410, 700)):
        person(d, x, 1860, 230, SKINS[(i * 2) % 6], [(250, 120, 160), (255, 255, 255), (80, 200, 160)][i], [(240, 220, 80), (40, 120, 200), (255, 140, 80)][i], t * 3 + i, walk=False, dance=t * 2 + i, hat=['straw', None, 'cap'][i])
    person(d, 540, 1700, 180, SKINS[3], (30, 110, 190), (30, 110, 190), 0, walk=False, dance=t * 3)
    return camera(img.convert('RGB'), 1 + .03 * t, .5, .5)

# ============ S3a HAITÍ: MONTAÑAS Y CIUDADELA ============
HT_MTN = [('htm1', dict(base=820, amp=380, ctop=(110, 150, 196), cbot=(150, 190, 214), seed=41, f0=.0036, hi=(230, 240, 250, 255)), .10),
          ('htm2', dict(base=950, amp=340, ctop=(96, 150, 100), cbot=(120, 168, 110), seed=42, f0=.0042, trees='broad', tcol=(52, 120, 66), hi=(200, 228, 160, 255), ntree=500), .25),
          ('htm3', dict(base=1130, amp=330, ctop=(150, 156, 80), cbot=(86, 136, 70), seed=43, f0=.005, trees='broad', tcol=(48, 128, 56), hi=(230, 225, 130, 255), ntree=700), .5),
          ('htm4', dict(base=1330, amp=300, ctop=(52, 140, 66), cbot=(30, 100, 52), seed=44, f0=.006, trees='broad', tcol=(30, 110, 50), hi=(130, 210, 110, 255), ntree=700), .85)]

def citadelle(d, x, y, s):
    st = (168, 156, 136); dk = (118, 108, 94)
    d.polygon([(x - s * .5, y), (x - s * .44, y - s * .22), (x + s * .5, y - s * .26), (x + s * .62, y)], fill=dk)
    d.polygon([(x - s * .44, y - s * .22), (x - s * .28, y - s * .62), (x + s * .34, y - s * .66), (x + s * .5, y - s * .26)], fill=st)
    d.polygon([(x - s * .28, y - s * .62), (x - s * .12, y - s * .88), (x + s * .2, y - s * .9), (x + s * .34, y - s * .66)], fill=shade(st, 1.08))
    for i in range(9): d.rectangle([x - s * .26 + i * s * .066, y - s * .68, x - s * .26 + i * s * .066 + s * .035, y - s * .64], fill=dk)
    for i in range(5): d.rectangle([x - s * .1 + i * s * .06, y - s * .94, x - s * .1 + i * s * .06 + s * .03, y - s * .9], fill=dk)
    for i in range(4): d.rectangle([x - s * .3 + i * s * .2, y - s * .42, x - s * .22 + i * s * .2, y - s * .36], fill=(40, 36, 34))
    d.line([(x + s * .05, y - s * .9), (x + s * .05, y - s * 1.12)], fill=(60, 50, 40), width=4)

def shot_citadelle(t):
    f = sm(seg(t, 0, 2.6)); dy = lerp(-380, 60, f)     # tilt up: capas bajan
    sk = cached('ct_sky', lambda: vgrad([(0, (46, 126, 224)), (.5, (126, 198, 246)), (1, (236, 238, 226))], W, H + 500)).copy().convert('RGBA')
    img = new_rgba(); img.paste(sk, (0, int(-500 + dy * .4)))
    clouds(img, t, 100 + dy * .3, 4, 10, 1.3, (255, 255, 255), 9, 235)
    d = ImageDraw.Draw(img)
    for nm, kw, par in HT_MTN[:2]: put(img, cached(nm, lambda kw=kw: mount_layer(**kw)), t * 6 * par, dy * par)
    d = ImageDraw.Draw(img); peak = (640, 790 + dy * .4)
    d.polygon([(peak[0] - 260, peak[1] + 280), (peak[0] - 60, peak[1] + 10), (peak[0] + 70, peak[1] + 2), (peak[0] + 300, peak[1] + 290)], fill=(106, 150, 92)); citadelle(d, peak[0], peak[1] + 20, 330)
    mist(img, t, 780 + dy * .5, 1100 + dy * .5, 120, 20, 3)
    for nm, kw, par in HT_MTN[2:]: put(img, cached(nm, lambda kw=kw: mount_layer(**kw)), t * 6 * par, dy * par)
    d = ImageDraw.Draw(img); r = random.Random(4)
    for i in range(18):       # casitas de colores en la ladera
        x = 60 + r.random() * 960; y = 1250 + r.random() * 380 + dy * .85; c = [(236, 90, 70), (250, 200, 60), (70, 160, 220), (240, 240, 230), (120, 200, 120), (230, 130, 190)][r.randrange(6)]; w = 48 + y * .02
        d.rectangle([x, y, x + w, y + w * .7], fill=c); d.polygon([(x - 4, y), (x + w / 2, y - w * .45), (x + w + 4, y)], fill=shade(c, .55))
    d.polygon([(0, 1700 + dy * .9), (W, 1620 + dy * .9), (W, H), (0, H)], fill=(34, 104, 54)); d.rectangle([0, 1900 + dy * .9, W, H + 600], fill=(30, 96, 50))
    for i, x in enumerate((90, 920, 40)): broadtree(d, x, 1860 + dy * .9, 400 - i * 60, sway=math.sin(t * 1.5 + i) * 6)
    ph = t * 3.2; donkey(d, 300 + t * 40, 1830 + dy * .9, 300, ph); person(d, 520 + t * 40, 1840 + dy * .9, 300, SKINS[0], (240, 200, 60), (60, 80, 140), ph + .5, hat='straw'); person(d, 700 + t * 40, 1850 + dy * .9, 300, SKINS[4], (230, 90, 90), (250, 250, 250), ph + 1.2, skirt=True, carry='head', hat='scarf')
    for i in range(7): bird(d, 160 + i * 110 + 30 * math.sin(t + i), 360 + 50 * math.sin(i) + dy * .3, 22, t + i * .35)
    return camera(img.convert('RGB'), 1 + .02 * t, .5, .5)

# ============ S3b MERCADO HAITIANO ============
def shot_market(t):
    pan = t * 60
    img = cached('mk_sky', lambda: sky('day', (150, 200, 70))).copy(); clouds(img, t, 60, 4, 9, 1.1, (255, 255, 255), 5, 230)
    put(img, cached('mk_m', lambda: mount_layer(base=600, amp=230, ctop=(96, 156, 110), cbot=(110, 170, 120), seed=51, f0=.004, trees='broad', tcol=(52, 130, 70))), pan * .15)
    d = ImageDraw.Draw(img)
    pal = [((250, 214, 120), (255, 255, 255), (214, 70, 56)), ((126, 196, 226), (255, 250, 230), (60, 130, 90)), ((244, 140, 150), (250, 240, 220), (120, 70, 150)), ((150, 214, 150), (255, 255, 250), (220, 90, 70)), ((250, 180, 90), (255, 250, 235), (60, 100, 170)), ((190, 160, 220), (255, 255, 240), (230, 170, 50))]
    base = 1060
    for i in range(7):
        x = i * 330 - (pan * .45 % 330) - 220 + 0; k = (i + int(pan * .45 // 330)) % 6; b, tr, ro = pal[k]
        gable_house(d, x, base, 260, 330 + (k % 3) * 55, b, tr, ro, k, shutter=(40, 120, 90) if k % 2 else (200, 70, 60))
    bunting(d, 0, 640, W, 620, [(214, 40, 60), (40, 70, 190), (250, 200, 40), (60, 170, 90)], 50, 18); bunting(d, 0, 760, W, 740, [(250, 200, 40), (214, 40, 60), (255, 255, 255), (40, 70, 190)], 40, 16)
    d.rectangle([0, base, W, H], fill=(206, 172, 122)); d.rectangle([0, base, W, base + 14], fill=(176, 142, 98))
    for i in range(30): px = (i * 97 + 20) % W; py = base + 60 + (i * 53) % 700; d.ellipse([px, py, px + 24, py + 7], fill=(190, 156, 108))
    items = [(244, 80, 50), (250, 200, 40), (70, 160, 70), (240, 130, 40)]
    for i in range(4):
        x = (i * 310 - pan * .9) % (W + 330) - 280; umbrella_stall(d, x, 1260, 230, [(214, 50, 60), (250, 200, 50), (50, 120, 200), (60, 170, 90)][i], (255, 255, 250), items, i)
    # tap-tap
    tx = ((t * 260 + 100) % (W + 900)) - 700
    tap_tap(d, tx, 1430, 560, (250, 190, 40), (210, 50, 70), t * 10)
    for i in range(6):
        x = (i * 230 + 60 - pan * 1.2) % (W + 260) - 140; person(d, x, 1380 + (i % 2) * 40, 240, SKINS[i % 6], [(240, 90, 90), (250, 220, 80), (80, 170, 220), (250, 250, 250), (90, 190, 120), (230, 130, 190)][i], [(60, 80, 140), (240, 240, 240), (60, 60, 70), (200, 90, 80), (60, 80, 140), (240, 240, 240)][i], t * 4.5 + i * 1.3, carry=['head', None, 'bag', 'head', None, 'jug'][i], hat=[None, 'straw', None, 'scarf', 'cap', None][i], skirt=i in (0, 3), facing=1 if i % 2 else -1)
    ft = (140, 40)
    umbrella_stall(d, 40 - pan * 1.5 % 1, 1900, 560, (240, 140, 40), (255, 255, 255), items, 9)
    umbrella_stall(d, 600 - pan * 1.5 % 1, 1900, 560, (50, 120, 200), (255, 255, 250), items, 10)
    for i, x in enumerate((180, 760)): person(d, x, 1880, 560, SKINS[i * 2 + 1], [(240, 220, 80), (90, 180, 120)][i], [(60, 80, 140), (200, 90, 80)][i], 0, walk=False, dance=t * 2 + i, skirt=i == 1, hat=['straw', 'scarf'][i])
    return camera(img.convert('RGB'), 1 + .025 * t, .5, .5)
