import math, random
import kit
from kit import *
from kit import _paste_clip
from world import *
from shots_a import put, donkey, mountains, mist, DR_MTN, HT_MTN, citadelle, city_layer, cathedral

PAL_C = [(240, 90, 90), (250, 220, 80), (80, 170, 220), (250, 250, 250), (90, 190, 120), (230, 130, 190), (250, 150, 50)]
PAL_P = [(60, 80, 140), (240, 240, 240), (60, 60, 70), (200, 90, 80), (50, 120, 90), (90, 60, 50)]
def beat(period_beats=1.0): return (kit.GT * kit.BPM / 60.0) / period_beats

# ============ S4a FRONTERA DESDE EL AIRE ============
TH = 4600
def border_terrain():
    img = Image.new('RGB', (W, TH), (70, 140, 60)); d = ImageDraw.Draw(img); r = random.Random(12)
    base = fbm_arr(W // 4, TH // 4, 21, 5, 5); b = Image.fromarray((base * 255).astype(np.uint8)).resize((W, TH), Image.BICUBIC)
    riv = lambda y: 540 + 70 * math.sin(y * .0042) + 34 * math.sin(y * .011 + 1)
    for y in range(0, TH, 4):       # fondo por lado con ruido
        pass
    arr = np.asarray(b, np.float32) / 255
    xs = np.arange(W)[None, :]; ys = np.arange(TH); rx = np.array([riv(y) for y in ys])[:, None]
    east = (xs > rx)[..., None]
    gdr = np.array([54, 150, 62], np.float32) + (arr[..., None] - .5) * np.array([40, 60, 30], np.float32)
    ght = np.array([140, 160, 74], np.float32) + (arr[..., None] - .5) * np.array([60, 60, 34], np.float32)
    img = Image.fromarray(np.clip(np.where(east, gdr, ght), 0, 255).astype(np.uint8)); d = ImageDraw.Draw(img)
    for side in (0, 1):   # campos rectangulares
        for _ in range(260):
            y = r.uniform(0, TH); xc = (r.uniform(40, 460) if side == 0 else r.uniform(640, 1040)); xc = xc if abs(xc - riv(y)) > 120 else xc + (200 if side else -200)
            if side == 1: w, h = r.uniform(90, 230), r.uniform(70, 190); cols = [(34, 130, 52), (92, 176, 66), (60, 150, 60), (140, 190, 70), (26, 100, 44), (190, 200, 90)]
            else: w, h = r.uniform(40, 120), r.uniform(30, 90); cols = [(170, 160, 78), (120, 160, 64), (206, 172, 96), (96, 144, 60), (190, 120, 70), (150, 170, 80), (224, 190, 110)]
            a = r.uniform(-.3, .3); c = cols[r.randrange(len(cols))]
            pts = [(xc + (px * math.cos(a) - py * math.sin(a)), y + (px * math.sin(a) + py * math.cos(a))) for px, py in ((-w, -h), (w, -h), (w, h), (-w, h))]
            d.polygon(pts, fill=c)
            for k in range(0, int(h * 2), 10 if side else 7):     # surcos
                kk = k - h; d.line([(xc + (-w) * math.cos(a) - kk * math.sin(a), y + (-w) * math.sin(a) + kk * math.cos(a)), (xc + w * math.cos(a) - kk * math.sin(a), y + w * math.sin(a) + kk * math.cos(a))], fill=shade(c, .88), width=1)
        for _ in range(900 if side == 0 else 500):    # árboles
            y = r.uniform(0, TH); x = r.uniform(0, 480) if side == 0 else r.uniform(600, W)
            if abs(x - riv(y)) < 95: continue
            s = r.uniform(7, 16); d.ellipse([x - s, y - s, x + s, y + s], fill=shade((28, 100, 46), r.uniform(.8, 1.2))); d.ellipse([x - s * .5 - 2, y - s * .5 - 2, x + s * .2, y + s * .2], fill=(60, 140, 66))
        for _ in range(70 if side == 0 else 36):     # casas
            y = r.uniform(0, TH); x = r.uniform(30, 470) if side == 0 else r.uniform(620, 1040)
            if abs(x - riv(y)) < 120: continue
            c = [(220, 90, 70), (70, 150, 220), (250, 200, 60), (240, 240, 235), (190, 90, 150)][r.randrange(5)]; d.rectangle([x, y, x + 22, y + 16], fill=c); d.rectangle([x + 22, y + 2, x + 26, y + 18], fill=(40, 40, 40, 120))
    for sd, x0, x1 in ((0, 0, 540), (1, 540, W)):   # caminos de tierra
        pass
    pts = [(riv(y), y) for y in range(-20, TH + 20, 10)]
    d.line([(x + 6, y) for x, y in pts], fill=(34, 40, 30), width=118); d.line(pts, fill=(214, 194, 142), width=108); d.line(pts, fill=(60, 160, 178), width=74); d.line([(x + 3, y) for x, y in pts], fill=(90, 190, 200), width=40)
    img = img.filter(ImageFilter.GaussianBlur(.8)); d = ImageDraw.Draw(img)
    return img, riv

def shot_border_air(t):
    img, riv = cached('border_air', border_terrain); f = sm(seg(t, -0.2, 3.7)); oy = lerp(200, 2750, f * .85 + .15 * f)
    fr = img.crop((0, int(oy), W, int(oy) + H)).convert('RGBA'); d = ImageDraw.Draw(fr)
    by = 2420 - oy    # puente
    cx = riv(2420) 
    d.rectangle([cx - 150, by - 22, cx + 150, by + 22], fill=(150, 150, 156)); d.rectangle([cx - 150, by - 24, cx + 150, by - 18], fill=(230, 230, 230)); d.rectangle([cx - 150, by + 18, cx + 150, by + 24], fill=(230, 230, 230))
    for x0, x1 in ((0, cx - 150), (cx + 150, W)): d.rectangle([x0, by - 12, x1, by + 12], fill=(190, 172, 130))
    r = random.Random(5)
    for i in range(14):     # camiones y gente cruzando
        sp = (60 + i * 7) * (1 if i % 2 else -1); x = ((r.random() * 1400 + t * sp) % 1300) - 110; c = [(230, 60, 50), (240, 240, 240), (60, 100, 200), (250, 190, 40)][i % 4]
        if i < 5: d.rectangle([x, by - 9 + (i % 2) * 10 - 4, x + 54, by + 1 + (i % 2) * 10 - 4], fill=c)
        else: d.ellipse([x, by - 8 + (i % 2) * 9, x + 8, by + (i % 2) * 9], fill=c)
    for side, (fx, col) in enumerate(((cx - 190, 'HT'), (cx + 190, 'DR'))):     # banderas vistas desde arriba (pequeñas)
        d.rectangle([fx - 24, by - 150, fx + 24, by - 100], fill=HT_BLUE if side == 0 else DR_BLUE); d.rectangle([fx - 24, by - 125, fx + 24, by - 100], fill=HT_RED if side == 0 else DR_RED)
    for i in range(46):      # destellos del río
        y = (i * 211 + t * 70) % H; x = riv(y + oy) + math.sin(i * 2.3) * 26; d.line([(x, y), (x + 3, y + 22)], fill=(255, 255, 255, 150), width=2)
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0)); cl = new_rgba()
    clouds(cl, t, 300, 3, 12, 1.4, (255, 255, 255), 2, 120)
    shad = Image.new('RGBA', (W, H), (10, 40, 30, 0)); shad.putalpha(cl.getchannel('A').point(lambda v: int(v * .35)).transform((W, H), Image.AFFINE, (1, 0, -40, 0, 1, -70)))
    fr.alpha_composite(shad); fr.alpha_composite(cl)
    return camera(fr.convert('RGB'), 1 + .03 * t, .5, .5)

# ============ S4b MERCADO FRONTERIZO ============
def shot_border_gate(t):
    img = cached('bg_sky', lambda: sky('day', (540, 220, 64))).copy(); clouds(img, t, 90, 4, 9, 1.2, (255, 255, 255), 3, 230)
    put(img, cached('bg_l', lambda: mount_layer(820, 260, (160, 158, 100), (140, 150, 90), 61, .0045, 'broad', (110, 130, 64), w=W + 400)), 0)
    d = ImageDraw.Draw(img)
    gr = new_rgba(); gd = ImageDraw.Draw(gr)
    # colinas: izq más seca, der más verde
    left = Image.new('RGBA', (W, H), (0, 0, 0, 0)); 
    put(img, cached('bg_m', lambda: mount_layer(980, 220, (100, 170, 80), (60, 130, 62), 62, .0055, 'broad', (40, 120, 52))), 0)
    hz = 1020; d = ImageDraw.Draw(img)
    d.rectangle([0, hz, 540, H], fill=(196, 176, 112)); d.rectangle([540, hz, W, H], fill=(72, 160, 74))
    for x in range(0, 540, 90): d.polygon([(x, hz + 30), (x + 60, hz + 30), (x + 30, hz)], fill=(176, 158, 98))
    # puente y río
    d.rectangle([0, 1480, W, 1740], fill=(56, 156, 176))
    for i in range(14):
        y = 1500 + i * 17; d.line([(0, y + 4 * math.sin(t * 2 + i)), (W, y + 4 * math.cos(t * 1.6 + i))], fill=(150, 220, 226, 90), width=2)
    d.rectangle([0, 1440, W, 1500], fill=(170, 160, 150)); d.rectangle([0, 1380, W, 1445], fill=(120, 120, 128)); d.rectangle([0, 1372, W, 1382], fill=(235, 235, 235))
    for x in range(0, W, 40): d.rectangle([x, 1340, x + 8, 1380], fill=(235, 235, 235))
    d.rectangle([0, 1340, W, 1350], fill=(235, 235, 235))
    for i in range(8): d.rectangle([i * 160 - 6, 1500, i * 160 + 24, 1740], fill=(120, 116, 110))
    # mercados a cada lado
    items = [(244, 80, 50), (250, 200, 40), (70, 160, 70), (240, 130, 40)]
    for i, (x, c1) in enumerate(((20, (50, 90, 200)), (250, (214, 50, 60)), (590, (250, 200, 50)), (820, (40, 130, 200)))): umbrella_stall(d, x, 1200, 210, c1, (255, 255, 250), items, i + 3)
    # arco de la frontera
    d.rectangle([420, 780, 456, 1340], fill=(236, 236, 240)); d.rectangle([624, 780, 660, 1340], fill=(236, 236, 240)); d.rectangle([400, 760, 680, 800], fill=(236, 236, 240))
    d.rectangle([420, 800, 540, 830], fill=HT_BLUE); d.rectangle([420, 830, 540, 860], fill=HT_RED); d.rectangle([540, 800, 660, 830], fill=DR_BLUE); d.rectangle([540, 830, 660, 860], fill=DR_RED)
    flag(d, 100, 640, 210, 'HT', t); flag(d, 880, 640, 210, 'DR', t)
    # tránsito
    tx = ((t * 240 + 300) % (W + 700)) - 500; d.rectangle([tx, 1180 + 5, tx + 200, 1310], fill=(236, 236, 240)); d.rectangle([tx + 200, 1230, tx + 290, 1310], fill=(60, 110, 190)); d.rectangle([tx + 205, 1240, tx + 268, 1272], fill=(170, 215, 235))
    for cx in (tx + 40, tx + 120, tx + 240): d.ellipse([cx - 26, 1286, cx + 26, 1338], fill=(24, 24, 28)); d.ellipse([cx - 12, 1300, cx + 12, 1324], fill=(190, 190, 200))
    for i in range(10):
        dirn = 1 if i % 2 else -1; x = ((i * 190 + t * 95 * dirn) % (W + 300)) - 150
        person(d, x, 1425 + (i % 3) * 18, 310 - (i % 3) * 16, SKINS[i % 6], PAL_C[i % 7], PAL_P[i % 6], t * 4.4 + i * 1.7 * dirn, carry=['head', 'bag', None, 'head', 'jug', 'bag', None][i % 7], facing=dirn, hat=[None, 'straw', None, 'scarf', 'cap'][i % 5], skirt=i % 4 == 3)
    # carretilla
    wx = ((t * 120 + 700) % (W + 400)) - 200; d.polygon([(wx, 1360), (wx + 120, 1360), (wx + 100, 1410), (wx + 20, 1410)], fill=(200, 140, 40)); d.ellipse([wx + 118, 1392, wx + 152, 1426], fill=(25, 25, 28))
    for k in range(4): d.ellipse([wx + 12 + k * 26, 1325, wx + 44 + k * 26, 1362], fill=[(250, 200, 40), (60, 170, 70), (240, 80, 50), (250, 160, 40)][k])
    # primer plano: apretón de manos central entre dos comerciantes
    person(d, 430, 1900, 560, SKINS[0], (250, 220, 80), (60, 80, 140), 0, walk=False, dance=t * 1.5, hat='straw'); person(d, 690, 1900, 560, SKINS[4], (60, 150, 220), (240, 240, 240), 0, walk=False, dance=t * 1.5 + 2, hat='cap', facing=-1)
    for i in range(5): bird(d, 150 + i * 190 + 20 * math.sin(t + i), 480 + 30 * math.cos(i), 20, t + i * .3)
    return camera(img.convert('RGB'), 1 + .03 * t, .5, .55)

# ============ S5 CULTURA ============
def bokeh(img, t, n, seed, cols, y0, y1, size=(18, 60)):
    r = random.Random(seed)
    for i in range(n):
        x = r.random() * W; y = lerp(y0, y1, r.random()); s = int(lerp(size[0], size[1], r.random())); c = cols[r.randrange(len(cols))]; a = (math.sin(t * 2 + i * 1.3) + 1.6) / 2.6
        glow(img, x, y, s * 2, c, .8 * a, 1.6)

def shot_dance_dr(t):
    b = beat()
    img = vgrad([(0, (22, 18, 70)), (.45, (96, 36, 110)), (1, (240, 110, 80))]).convert('RGBA')
    d = ImageDraw.Draw(img)
    # fachada de colmado
    d.rectangle([0, 560, W, 1500], fill=(250, 214, 80)); d.rectangle([0, 560, W, 600], fill=(214, 40, 60))
    for i, x in enumerate((60, 380, 700)): d.rectangle([x, 700, x + 280, 1060], fill=(60, 120, 190)); d.rectangle([x + 10, 710, x + 270, 1050], fill=(255, 210, 120)); d.line([(x + 140, 710), (x + 140, 1050)], fill=(60, 120, 190), width=8)
    for i in range(13): d.polygon([(i * 90, 600), (i * 90 + 90, 600), (i * 90 + 45, 690)], fill=(214, 40, 60) if i % 2 else (255, 255, 255))
    for i in range(3): bunting(d, 0, 300 + i * 60, W, 330 + i * 60, [(214, 40, 60), (40, 70, 190), (250, 200, 40), (255, 255, 255)], 60, 16)
    d.rectangle([0, 1500, W, H], fill=(150, 100, 70))
    for i in range(14): d.line([(0, 1500 + i * 32), (W, 1500 + i * 32)], fill=(120, 78, 52), width=3)
    glow(img, 540, 1450, 1300, (255, 160, 60), .5, 2.0); d = ImageDraw.Draw(img)
    palm(d, 50, 1560, 760, t, .1, 4, (30, 20, 30), (20, 40, 30), (24, 54, 36)); palm(d, 1040, 1580, 700, t + 1, -.1, 5, (30, 20, 30), (20, 40, 30), (24, 54, 36))
    # músicos (acordeón, tambora, güira)
    bounce = abs(math.sin(math.pi * b)) 
    for (x, kind, ph) in ((190, 'accordion', 0), (900, 'tambora', 1), (780, 'guira', 2)):
        yb = 1640
        person(d, x, yb, 340, SKINS[(ph * 2 + 1) % 6], PAL_C[(ph + 2) % 7], PAL_P[ph % 6], 0, walk=False, dance=b * TAU * (1 if ph != 1 else 2), hat='straw' if ph == 0 else ('cap' if ph == 1 else None), facing=-1 if x > 540 else 1)
        if kind == 'accordion':
            sq = 30 + 22 * math.sin(b * TAU); d.rectangle([x - 50, yb - 190, x - 50 + 38, yb - 90], fill=(30, 30, 40)); d.rectangle([x + 70 - 38 + sq, yb - 190, x + 70 + sq, yb - 90], fill=(30, 30, 40)); d.rectangle([x - 12, yb - 182, x + 32 + sq, yb - 98], fill=(200, 50, 50))
            for k in range(7): d.line([(x - 12 + k * (44 + sq) / 7, yb - 182), (x - 12 + k * (44 + sq) / 7, yb - 98)], fill=(240, 240, 230), width=2)
        elif kind == 'tambora':
            d.ellipse([x - 90, yb - 150, x - 6, yb - 62], fill=(140, 84, 50), outline=(240, 230, 200), width=6); d.ellipse([x - 98, yb - 150, x - 76, yb - 62], fill=(240, 230, 200))
            hx = x - 120 + 28 * abs(math.sin(math.pi * b * 2)); d.line([(x - 60, yb - 245), (hx, yb - 150)], fill=(200, 160, 100), width=7)
        else:
            d.rectangle([x - 70, yb - 205, x - 40, yb - 120], fill=(205, 205, 215), outline=(120, 120, 130), width=3)
            for k in range(6): d.line([(x - 70, yb - 205 + k * 14), (x - 40, yb - 205 + k * 14)], fill=(120, 120, 130), width=1)
            sx_ = x - 100 + 36 * math.sin(b * TAU * 2); d.line([(sx_, yb - 190), (sx_ + 70, yb - 160)], fill=(200, 160, 100), width=6)
    # pareja bailando merengue (centro)
    cx = 540 + 90 * math.sin(b * TAU / 4); yb = 1860; sw = math.sin(b * TAU)
    person(d, cx - 50, yb, 640, SKINS[1], (30, 40, 90), (30, 30, 50), 0, walk=False, dance=b * TAU, hat=None)
    # vestido que gira
    dx = cx + 70; sk = 150 + 40 * math.sin(b * TAU * 2)
    d.polygon([(dx - 52, yb - 280), (dx + 52, yb - 280), (dx + sk, yb - 80), (dx - sk, yb - 80 + 12 * sw)], fill=(220, 30, 60)); d.polygon([(dx - 30, yb - 280), (dx + 30, yb - 280), (dx + sk * .5, yb - 90), (dx - sk * .5, yb - 90)], fill=(250, 250, 250))
    person(d, dx, yb, 600, SKINS[4], (250, 250, 250), (220, 30, 60), 0, walk=False, dance=b * TAU + 1, skirt=True, hair=(20, 12, 10), arms_up=False)
    for k in range(18):      # confeti
        x = (k * 97 + t * 40 * (1 + k % 3 * .3)) % W; y = (k * 211 + t * 150) % 1900; c = [(250, 200, 40), (220, 30, 60), (60, 140, 230), (255, 255, 255)][k % 4]; d.rectangle([x, y, x + 10, y + 5], fill=c)
    bokeh(img, t, 26, 8, [(255, 210, 90), (255, 90, 100), (120, 190, 255)], 120, 760)
    return camera(img.convert('RGB'), 1 + .03 * t, .5, .6)

def shot_dance_ht(t):
    b = beat()
    img = vgrad([(0, (255, 214, 120)), (.5, (255, 150, 90)), (1, (200, 60, 90))]).convert('RGBA'); d = ImageDraw.Draw(img)
    # mural de arte naíf
    d.rectangle([0, 220, W, 1560], fill=(40, 150, 200)); r = random.Random(9)
    for i in range(9):      # sol, aves, árboles, flores
        pass
    d.ellipse([380, 300, 700, 620], fill=(255, 220, 60)); [d.line([(540 + math.cos(a) * 180, 460 + math.sin(a) * 180), (540 + math.cos(a) * 250, 460 + math.sin(a) * 250)], fill=(255, 220, 60), width=14) for a in [i * TAU / 16 for i in range(16)]]
    for i in range(9):
        x = 80 + i * 115; hh = r.uniform(280, 520); d.rectangle([x - 10, 1100 - hh, x + 10, 1100], fill=(110, 70, 40)); [d.ellipse([x - 70 + k * 36, 1100 - hh - 60 + (k % 2) * 30, x + k * 36 + 10, 1100 - hh + 40 + (k % 2) * 30], fill=[(30, 160, 80), (60, 200, 100), (20, 120, 70)][k % 3]) for k in range(3)]
        for k in range(5): d.ellipse([x - 22 + k * 8, 1100 - hh * .5 + k * 40, x - 6 + k * 8, 1100 - hh * .5 + 16 + k * 40], fill=[(250, 60, 80), (255, 190, 40), (255, 255, 255)][k % 3])
    for i in range(6): bird(d, 120 + i * 170, 680 + 60 * math.sin(i * 2), 30 + i % 3 * 8, t * .6 + i, (230, 40, 60))
    d.rectangle([0, 1560, W, H], fill=(120, 70, 50)); [d.line([(0, 1560 + i * 30), (W, 1560 + i * 30)], fill=(96, 56, 40), width=3) for i in range(14)]
    for i in range(3): bunting(d, 0, 140 + i * 50, W, 160 + i * 50, [(0, 32, 159), (210, 16, 52), (250, 200, 40), (255, 255, 255)], 50, 16)
    glow(img, 540, 1400, 1400, (255, 190, 90), .5, 2.0); d = ImageDraw.Draw(img)
    # tambores cónicos (tanbou) y tamborileros
    for (x, ph) in ((220, 0), (860, 1)):
        yb = 1700; hit = abs(math.sin(math.pi * (b + ph * .5)))
        person(d, x, yb, 380, SKINS[(ph * 3) % 6], [(0, 32, 159), (210, 16, 52)][ph], PAL_P[ph], 0, walk=False, dance=b * TAU * (1 + ph), hat=['cap', 'scarf'][ph])
        d.polygon([(x - 62, yb - 220), (x + 62, yb - 220), (x + 40, yb - 40), (x - 40, yb - 40)], fill=(200, 110, 50)); d.ellipse([x - 62, yb - 236, x + 62, yb - 204], fill=(240, 230, 200))
        for k in range(5): d.line([(x - 55 + k * 28, yb - 212), (x - 38 + k * 22, yb - 46)], fill=(130, 70, 36), width=3)
        hx = x - 70 * (1 if ph == 0 else -1) * .0 + 40 * hit * (1 if ph else -1); d.line([(x + (60 if ph == 0 else -60), yb - 300), (x + 10 * (1 if ph == 0 else -1), yb - 245 + hit * 14)], fill=(220, 180, 110), width=8)
    # bailarinas con madras azul/roja
    for k, (x, ph) in enumerate(((410, 0), (560, 1.3), (710, 2.1))):
        sk = 130 + 50 * math.sin(b * TAU * 2 + ph); yb = 1850 - k % 2 * 20; hh = 560 - k % 2 * 30; sw = math.sin(b * TAU + ph)
        a, c = [((0, 32, 159), (210, 16, 52)), ((210, 16, 52), (250, 220, 60)), ((250, 250, 250), (0, 32, 159))][k]
        d.polygon([(x - 46, yb - hh * .52), (x + 46, yb - hh * .52), (x + sk + 20 * sw, yb - 70), (x - sk + 20 * sw, yb - 70)], fill=a)
        for z in range(5): d.polygon([(x - 40 + z * 20, yb - hh * .5), (x - 30 + z * 20, yb - hh * .5), (x - sk * .9 + z * sk * .4 + 20 * sw, yb - 72), (x - sk * .9 + z * sk * .4 - 12 + 20 * sw, yb - 72)], fill=c)
        person(d, x, yb, hh, SKINS[(k * 2 + 1) % 6], c if k != 1 else (250, 250, 250), a, 0, walk=False, dance=b * TAU + ph, skirt=True, arms_up=True, hat='scarf')
    for k in range(20):
        x = (k * 83 + t * 30) % W; y = (k * 197 + t * 140) % 1900; c = [(0, 32, 159), (210, 16, 52), (250, 220, 60), (255, 255, 255)][k % 4]; d.rectangle([x, y, x + 11, y + 5], fill=c)
    bokeh(img, t, 16, 4, [(255, 230, 120), (255, 100, 120)], 100, 700)
    return camera(img.convert('RGB'), 1 + .03 * t, .5, .6)

def fireworks(img, t, bursts, seed=1):
    d = ImageDraw.Draw(img); r = random.Random(seed)
    for (t0, x, y, col) in bursts:
        u = t - t0
        if u < 0 or u > 1.6: continue
        n = 28
        for i in range(n):
            a = i * TAU / n + r.random() * .2; sp = 330 * (1 - math.exp(-u * 3.2)); fade = clamp(1 - u / 1.5)
            for tr in range(4):
                uu = max(0, u - tr * .05); s2 = 330 * (1 - math.exp(-uu * 3.2)); px = x + math.cos(a) * s2; py = y + math.sin(a) * s2 + 90 * uu * uu
                d.ellipse([px - 4, py - 4, px + 4, py + 4], fill=col + (int(255 * fade * (1 - tr * .22)),))
        glow(img, x, y, int(520 * clamp(1 - abs(u - .15) * 3)), col, .8, 2.0) if u < .5 else None
FW = [(.3, 270, 360, (255, 80, 90)), (.7, 800, 280, (90, 150, 255)), (1.2, 540, 440, (255, 220, 90)), (1.7, 220, 560, (255, 255, 255)), (2.1, 860, 500, (255, 90, 90)), (2.4, 520, 260, (90, 150, 255))]

def plate(d, x, y, r, kind, t):
    d.ellipse([x - r - 10, y - r - 4, x + r + 14, y + r + 18], fill=(0, 0, 0, 70)); d.ellipse([x - r, y - r, x + r, y + r], fill=(250, 250, 248), outline=(200, 200, 205), width=4); d.ellipse([x - r * .86, y - r * .86, x + r * .86, y + r * .86], outline=(225, 225, 230), width=3)
    if kind == 'DR':     # la bandera dominicana
        d.ellipse([x - r * .72, y - r * .6, x - r * .12, y + r * .15], fill=(252, 252, 246)); [d.ellipse([x - r * .66 + i * 7, y - r * .5 + (i % 3) * 9, x - r * .6 + i * 7, y - r * .44 + (i % 3) * 9], fill=(235, 235, 225)) for i in range(0, 14)]
        d.ellipse([x + r * .05, y - r * .68, x + r * .74, y + r * .02], fill=(120, 50, 36)); [d.ellipse([x + r * .15 + (i % 6) * 14, y - r * .55 + (i // 6) * 14, x + r * .15 + (i % 6) * 14 + 10, y - r * .55 + (i // 6) * 14 + 7], fill=(90, 34, 26)) for i in range(18)]
        for i, (dx, dy) in enumerate(((-.5, .5), (-.15, .62), (.2, .58), (.5, .38))): d.ellipse([x + dx * r - 26, y + dy * r - 20, x + dx * r + 26, y + dy * r + 20], fill=(190, 80, 40)); d.ellipse([x + dx * r - 16, y + dy * r - 12, x + dx * r + 12, y + dy * r + 8], fill=(214, 110, 56))
        for i in range(3): d.ellipse([x - r * .75 + i * 30, y + r * .15 + 4 * i, x - r * .75 + i * 30 + 36, y + r * .15 + 22 + 4 * i], fill=(240, 200, 60), outline=(200, 150, 30), width=2)
        d.ellipse([x + r * .55, y - r * .15, x + r * .85, y + r * .1], fill=(90, 170, 70))
    else:                # griot, arroz y pikliz
        d.ellipse([x - r * .75, y - r * .7, x - r * .05, y + r * .05], fill=(60, 44, 36)); [d.ellipse([x - r * .7 + (i % 5) * 12, y - r * .6 + (i // 5) * 12, x - r * .7 + (i % 5) * 12 + 7, y - r * .6 + (i // 5) * 12 + 5], fill=(110, 90, 76)) for i in range(20)]
        for i, (dx, dy) in enumerate(((.15, -.45), (.4, -.25), (.2, -.12), (.5, -.55), (.35, -.4))): d.rectangle([x + dx * r - 24, y + dy * r - 20, x + dx * r + 24, y + dy * r + 20], fill=(196, 120, 46), outline=(130, 70, 24), width=3)
        d.ellipse([x - r * .6, y + r * .15, x + r * .1, y + r * .68], fill=(240, 120, 60)); [d.line([(x - r * .55 + i * 6, y + r * .25 + (i % 4) * 8), (x - r * .45 + i * 6, y + r * .45)], fill=(250, 220, 120), width=3) for i in range(11)]
        for i in range(4): d.ellipse([x + r * .2 + (i % 2) * 40, y + r * .3 + (i // 2) * 28, x + r * .2 + (i % 2) * 40 + 40, y + r * .3 + (i // 2) * 28 + 24], fill=(244, 196, 60), outline=(200, 140, 30), width=2)

def steam(img, x, y, t, n=5, seed=0, w=60):
    for i in range(n):
        u = ((t * .35 + i / n) % 1); a = (1 - u) * .5; yy = y - u * 220; xx = x + 30 * math.sin(u * 6 + i * 2 + seed); s = int(w * (1 + u * 2.2))
        glow(img, xx, yy, s, (255, 255, 255), a, 1.3)

def shot_food(t):
    img = vgrad([(0, (14, 10, 50)), (.3, (40, 20, 90)), (.55, (80, 30, 100)), (.56, (130, 80, 50)), (1, (170, 110, 70))]).convert('RGBA'); d = ImageDraw.Draw(img)
    for i in range(24): d.line([(0, 1060 + i * 38), (W, 1060 + i * 38)], fill=(120, 74, 44, 130), width=3)
    st = cached('fw_stars', lambda: [(random.Random(i).random() * W, random.Random(i + 99).random() * 700, random.Random(i + 7).random() * 6) for i in range(90)])
    for x, y, p in st: v = int(150 + 100 * math.sin(t * 3 + p)); d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=(v, v, v, 255))
    # siluetas: ciudad y montañas
    f1 = ridge_fn(77, .006, 4); pts = [(x, 1010 - 70 * (f1(x) * .5 + .5) * 1.5) for x in range(0, W + 8, 8)]; d.polygon(pts + [(W, 1070), (0, 1070)], fill=(20, 14, 50))
    fireworks(img, t, FW); d = ImageDraw.Draw(img)
    cx_ = [(270, 1330, 'DR'), (810, 1330, 'HT')]
    d.rectangle([0, 1060, W, 1080], fill=(220, 40, 60)); d.rectangle([540, 1060, W, 1080], fill=(210, 16, 52)); d.rectangle([0, 1060, 540, 1080], fill=(0, 45, 130))
    plate(d, 270, 1360, 250, 'DR', t); plate(d, 810, 1360, 250, 'HT', t)
    # bebidas y plátanos
    for x, c in ((130, (250, 170, 40)), (940, (230, 60, 60))): d.rounded_rectangle([x, 1650, x + 90, 1790], 12, fill=c + (230,), outline=(255, 255, 255, 200), width=4); d.ellipse([x + 20, 1640, x + 70, 1670], fill=(255, 255, 255, 160))
    # sopa joumou
    d.ellipse([440, 1630, 700, 1780], fill=(0, 0, 0, 70)); d.ellipse([420, 1590, 680, 1760], fill=(250, 250, 248), outline=(200, 200, 205), width=4); d.ellipse([440, 1606, 660, 1738], fill=(240, 138, 40))
    for i in range(7): d.ellipse([470 + i * 24, 1640 + (i % 3) * 24, 488 + i * 24, 1656 + (i % 3) * 24], fill=(250, 190, 90))
    steam(img, 550, 1620, t, 6, 1, 80); steam(img, 270, 1180, t + .5, 4, 2, 50); steam(img, 810, 1180, t + .2, 4, 3, 50); d = ImageDraw.Draw(img)
    # luces festivas
    for i in range(3): bunting(d, 0, 90 + i * 40, W, 70 + i * 40, [(255, 80, 90), (255, 220, 90), (90, 150, 255), (255, 255, 255)], 50, 16)
    bokeh(img, t, 18, 5, [(255, 220, 120), (255, 100, 120), (120, 180, 255)], 700, 1000)
    return camera(img.convert('RGB'), 1 + .03 * t, .5, .55)
