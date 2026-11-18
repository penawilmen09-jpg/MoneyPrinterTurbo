import math, random
import kit
from kit import *
from kit import _paste_clip
from world import *
from shots_a import *
from shots_b import PAL_C, PAL_P, beat

def container_stack(d, x, yb, cols, rows, w=96, h=40, seed=0):
    r = random.Random(seed); pal = [(210, 60, 50), (50, 110, 190), (240, 180, 40), (60, 150, 90), (230, 230, 230), (150, 90, 50)]
    for j in range(rows):
        for i in range(cols):
            c = pal[r.randrange(6)]; d.rectangle([x + i * w, yb - (j + 1) * h, x + (i + 1) * w - 3, yb - j * h - 2], fill=c)
            for k in range(1, 6): d.line([(x + i * w + k * w / 6, yb - (j + 1) * h + 3), (x + i * w + k * w / 6, yb - j * h - 4)], fill=shade(c, .8), width=2)

def gantry(d, x, yb, h, t, trolley=0.0):
    c = (230, 90, 40)
    for dx in (0, 190): d.rectangle([x + dx, yb - h, x + dx + 22, yb], fill=c)
    d.rectangle([x - 60, yb - h, x + 460, yb - h + 26], fill=c); d.rectangle([x - 60, yb - h - 24, x + 460, yb - h], fill=shade(c, 1.15))
    d.line([(x + 11, yb - h), (x + 120, yb - h - 160), (x + 200, yb - h)], fill=c, width=8)
    tx = x + 280 + 120 * trolley; d.rectangle([tx - 24, yb - h + 26, tx + 24, yb - h + 50], fill=(60, 60, 70))
    cy = yb - h + 60 + 190 * abs(math.sin(t * .8)); d.line([(tx, yb - h + 50), (tx, cy)], fill=(30, 30, 36), width=3); d.rectangle([tx - 44, cy, tx + 44, cy + 34], fill=[(210, 60, 50), (50, 110, 190)][int(t) % 2])

def ship(d, x, yb, w, t):
    off = math.sin(t * 1.3) * 3; yb += off
    d.polygon([(x, yb - 120), (x + w, yb - 120), (x + w - 60, yb), (x + 40, yb)], fill=(40, 50, 70)); d.rectangle([x, yb - 100, x + w - 12, yb - 92], fill=(200, 50, 50))
    container_stack(d, x + 60, yb - 120, 6, 4, 90, 40, 3); d.rectangle([x + w - 150, yb - 260, x + w - 20, yb - 120], fill=(240, 240, 244)); d.rectangle([x + w - 130, yb - 240, x + w - 40, yb - 205], fill=(130, 190, 220)); d.rectangle([x + w - 100, yb - 300, x + w - 70, yb - 260], fill=(200, 50, 50))

def build_pano_dr():
    PW = 3400; img = Image.new('RGBA', (PW, H), (0, 0, 0, 0)); sk = vgrad(SKY['day'], PW, H).convert('RGBA'); img.alpha_composite(sk); d = ImageDraw.Draw(img)
    sun_disc(img, 700, 340, 70); d = ImageDraw.Draw(img)
    hz = 1000; d.rectangle([0, hz, PW, 1300], fill=(40, 170, 200)); 
    for i in range(14): d.line([(0, hz + 20 + i * 22), (PW, hz + 20 + i * 22)], fill=(130, 225, 225, 100), width=2)
    # seg1 resort
    for i, (x, w, h, c) in enumerate(((40, 300, 620, (250, 246, 236)), (370, 360, 800, (252, 250, 244)), (760, 320, 540, (246, 236, 220)))):
        d.rectangle([x, 1380 - h, x + w, 1380], fill=c)
        for r_ in range(int(h // 80)):
            for k in range(int(w // 64)):
                bx = x + 16 + k * 64; by = 1380 - h + 30 + r_ * 80; d.rectangle([bx, by, bx + 44, by + 48], fill=(118, 180, 212)); d.rectangle([bx - 4, by + 48, bx + 48, by + 56], fill=[(240, 120, 90), (80, 170, 200), (250, 200, 80)][(r_ + i) % 3])
    d.rectangle([0, 1380, 1180, H], fill=(236, 226, 200)); d.rounded_rectangle([140, 1560, 1000, 1800], 50, fill=(38, 190, 214), outline=(250, 250, 245), width=12)
    # seg2 ciudad + autopista
    img.alpha_composite(city_layer(5, 1250, 220, 640, 100, 170, [(110, 150, 190), (130, 160, 200), (96, 130, 170), (170, 190, 205)], w=1300, lit=.5), (1080, 0)); d = ImageDraw.Draw(img)
    d.rectangle([1150, 1380, 2250, H], fill=(70, 74, 82)); d.rectangle([1150, 1380, 2250, 1410], fill=(210, 210, 215))
    for k in range(10): d.rectangle([1170 + k * 110, 1650, 1240 + k * 110, 1662], fill=(240, 230, 150)); d.rectangle([1170 + k * 110, 1820, 1240 + k * 110, 1832], fill=(240, 230, 150))
    for x in range(1200, 2250, 280): d.rectangle([x, 1330, x + 40, 1380], fill=(150, 150, 156))
    d.rectangle([1150, 1330, 2250, 1345], fill=(150, 150, 156))
    # seg3 puerto
    d.rectangle([2200, 1050, PW, H], fill=(50, 120, 190)); d.rectangle([2200, 1380, PW, H], fill=(150, 150, 150)); [d.rectangle([2200, 1380 + i * 12, PW, 1383 + i * 12], fill=(130, 130, 134)) for i in range(0, 40, 2)]
    container_stack(d, 2420, 1700, 5, 5, 100, 44, 8); container_stack(d, 2980, 1700, 4, 4, 100, 44, 9)
    # campos (banano) al final
    return img

def shot_econ_dr(t):
    kit_t = t; f = sm(seg(t, -0.1, 4.1)); sx = int(lerp(0, 2320, f)); pano = cached('pano_dr', build_pano_dr)
    img = pano.crop((sx, 0, sx + W, H)); d = ImageDraw.Draw(img); ox = -sx
    clouds(img, t, 120, 4, 8, 1.2, (255, 255, 255), 6, 230); d = ImageDraw.Draw(img)
    # dinámicos
    for i in range(7): bird(d, 200 + i * 80 + 30 * math.sin(t + i), 280 + i * 18, 20, t + i * .3)
    d.rectangle([ox + 140, 1580, ox + 1000, 1790], fill=(38, 190, 214)) if False else None
    for i, x in enumerate((220, 520, 840)): person(d, ox + x, 1870, 250, SKINS[i * 2 % 6], PAL_C[i], PAL_P[i], 0, walk=False, dance=t * 2 + i, hat='straw' if i == 1 else None)
    for x in (120, 1120): palm(d, ox + x, 1400, 360, t + x, .1, x)
    cols = [(220, 40, 50), (240, 240, 245), (40, 90, 170), (250, 200, 40), (60, 60, 66), (30, 150, 110)]
    for i in range(6):
        x = ((t * (240 + i * 20) + i * 400) % 1300) + 1000; car(d, ox + x, 1600, 280, cols[i % 6], t * 14)
    for i in range(5):
        x = 2350 - ((t * (200 + i * 30) + i * 330) % 1300); car(d, ox + x, 1820, 280, cols[(i + 3) % 6], t * 14, flip=True)
    gantry(d, ox + 2300, 1380, 560, t, math.sin(t * .8) * .5); gantry(d, ox + 2840, 1380, 520, t + 1.3, math.sin(t * .8 + 1) * .5)
    ship(d, ox + 2200, 1160, 900, t)
    # campos y tractor
    d.rectangle([ox + 3050, 1730, ox + 3400, H], fill=(60, 140, 60))
    for k in range(9): d.line([(ox + 3050 + k * 40, 1730), (ox + 3000 + k * 60, H)], fill=(40, 110, 46), width=6)
    for x in (3080, 3200, 3310):
        for k in range(3): palm(d, ox + x + k * 20, 1790 + k * 40, 150, t + k, .02, k, (80, 60, 40), (50, 150, 60), (80, 180, 70))
    tx = ox + 3000 + 40 * math.sin(t); d.rectangle([tx, 1640, tx + 140, 1720], fill=(60, 140, 70)); d.rectangle([tx + 90, 1590, tx + 130, 1640], fill=(170, 215, 235)); d.ellipse([tx - 10, 1660, tx + 70, 1740], fill=(26, 26, 30)); d.ellipse([tx + 90, 1680, tx + 140, 1730], fill=(26, 26, 30))
    return img.convert('RGB')

def build_pano_ht():
    PW = 3400; img = Image.new('RGBA', (PW, H), (0, 0, 0, 0)); img.alpha_composite(vgrad(SKY['day'], PW, H).convert('RGBA')); d = ImageDraw.Draw(img)
    # seg1: ladera con terrazas
    img.alpha_composite(mount_layer(base=760, amp=330, ctop=(110, 150, 196), cbot=(150, 190, 214), seed=73, f0=.0028, w=PW))
    img.alpha_composite(mount_layer(base=900, amp=330, ctop=(106, 156, 100), cbot=(120, 168, 100), seed=71, f0=.0034, trees='broad', tcol=(52, 120, 66), w=PW, ntree=1500)); d = ImageDraw.Draw(img)
    for i in range(7):
        y = 1000 + i * 120; cols = [(100, 170, 70), (150, 170, 80), (90, 150, 60), (190, 170, 90), (70, 140, 60), (130, 160, 70), (180, 160, 80)]
        pts = [(x, y + 28 * math.sin(x * .006 + i)) for x in range(0, 1250, 20)]; d.polygon(pts + [(1250, y + 180), (0, y + 180)], fill=cols[i]); d.line(pts, fill=shade(cols[i], 1.25), width=5)
        for x in range(30, 1200, 26 + i * 2): d.line([(x, y + 12 + 28 * math.sin(x * .006 + i)), (x - 8, y + 70)], fill=shade(cols[i], .8), width=3)
    # seg2: calle con comercios pequeños
    d.rectangle([1200, 1400, 2300, H], fill=(206, 172, 122)); r = random.Random(7)
    cols = [(250, 214, 120), (126, 196, 226), (244, 140, 150), (150, 214, 150), (250, 180, 90), (190, 160, 220)]
    for i in range(4):
        x = 1230 + i * 270; c = cols[i % 6]; d.rectangle([x, 1020 + (i % 2) * 60, x + 250, 1400], fill=c); d.rectangle([x - 8, 1020 + (i % 2) * 60, x + 258, 1050 + (i % 2) * 60], fill=shade(c, .7))
        d.rectangle([x + 20, 1240, x + 230, 1400], fill=shade(c, .55)); d.polygon([(x + 10, 1240), (x + 240, 1240), (x + 260, 1290), (x - 10, 1290)], fill=[(214, 50, 60), (40, 70, 190), (250, 200, 40), (60, 150, 90)][i])
        for k in range(5): d.ellipse([x + 36 + k * 36, 1330, x + 62 + k * 36, 1356], fill=[(250, 190, 40), (60, 170, 70), (240, 80, 50)][k % 3])
        d.polygon([(x + 30, 1020 + (i % 2) * 60), (x + 150, 940 + (i % 2) * 60), (x + 230, 1020 + (i % 2) * 60)], fill=(60, 80, 100)) if False else None
    for i in range(4):      # paneles solares en techos
        x = 1250 + i * 270; y0 = 1020 + (i % 2) * 60; d.polygon([(x + 30, y0), (x + 140, y0), (x + 160, y0 - 42), (x + 50, y0 - 42)], fill=(30, 56, 120)); [d.line([(x + 30 + k * 27, y0), (x + 50 + k * 27, y0 - 42)], fill=(150, 180, 230), width=2) for k in range(5)]
    for x in range(1240, 2300, 330): d.rectangle([x, 760, x + 14, 1400], fill=(92, 70, 52)); d.rectangle([x - 40, 800, x + 54, 810], fill=(92, 70, 52))
    # seg3: obra vial + pozo solar
    d.rectangle([2250, 1300, PW, H], fill=(196, 168, 124)); d.rectangle([2250, 1500, 3100, 1800], fill=(84, 86, 94)); [d.rectangle([2270 + k * 120, 1640, 2340 + k * 120, 1652], fill=(240, 230, 150)) for k in range(7)]
    d.polygon([(2900, 1500), (3100, 1500), (3100, 1800), (2800, 1800)], fill=(150, 130, 100))
    return img

def shot_econ_ht(t):
    f = sm(seg(t, -0.1, 4.1)); sx = int(lerp(0, 2320, f)); pano = cached('pano_ht', build_pano_ht)
    img = pano.crop((sx, 0, sx + W, H)); ox = -sx; clouds(img, t, 120, 4, 8, 1.2, (255, 255, 255), 6, 230); d = ImageDraw.Draw(img)
    for i in range(6): bird(d, 240 + i * 90 + 30 * math.sin(t + i), 420 + i * 12, 20, t + i * .4)
    # agricultores en terrazas
    for i in range(7):
        x = 120 + i * 160; y = 1150 + (i % 4) * 130; person(d, ox + x, y + 120, 200, SKINS[i % 6], PAL_C[i % 7], PAL_P[i % 6], 0, walk=False, dance=t * 3 + i * 1.3, hat='straw')
    for x in (170, 520, 880): broadtree(d, ox + x, 1140 + (x % 3) * 60, 220, (40, 130, 56), sway=math.sin(t * 1.5 + x) * 5)
    donkey(d, ox + 640 + 30 * math.sin(t * .6), 1860, 300, t * 3, facing=1); person(d, ox + 800 + 30 * math.sin(t * .6), 1860, 300, SKINS[0], (240, 200, 60), (60, 80, 140), t * 3 + 1, hat='straw')
    # motos taxi
    for i in range(3):
        mx = ((t * (260 + i * 40) + i * 500) % 1400) + 1180; d.ellipse([ox + mx, 1740, ox + mx + 70, 1810], fill=(25, 25, 28)); d.ellipse([ox + mx + 120, 1740, ox + mx + 190, 1810], fill=(25, 25, 28)); d.polygon([(ox + mx + 35, 1750), (ox + mx + 150, 1740), (ox + mx + 160, 1690), (ox + mx + 70, 1700)], fill=[(230, 60, 50), (60, 120, 210), (250, 200, 40)][i])
        person(d, ox + mx + 105, 1740, 150, SKINS[(i * 2 + 1) % 6], PAL_C[i], (40, 40, 50), 0, walk=False)
    for i in range(6):
        x = (1260 + i * 170 + 60 * math.sin(t + i)); person(d, ox + x, 1580 + (i % 2) * 40, 230, SKINS[i % 6], PAL_C[i % 7], PAL_P[i % 6], t * 4 + i, carry=['head', None, 'bag', 'head', None, 'jug'][i], hat=[None, 'straw', None, 'scarf', 'cap', None][i], skirt=i in (0, 3))
    # obra vial
    for i in range(4):
        x = 2330 + i * 190; d.polygon([(ox + x, 1610), (ox + x + 36, 1610), (ox + x + 28, 1550), (ox + x + 8, 1550)], fill=(250, 120, 30)); d.rectangle([ox + x + 8, 1575, ox + x + 28, 1584], fill=(255, 255, 255))
    for i in range(4):
        x = 2450 + i * 150; person(d, ox + x, 1720 + (i % 2) * 40, 250, SKINS[i % 6], [(250, 140, 30), (250, 220, 60), (240, 240, 240), (250, 140, 30)][i], (50, 70, 110), 0, walk=False, dance=t * 5 + i * 1.5 * 0 + i, hat='cap')
        d.line([(ox + x + 20, 1620 + (i % 2) * 40), (ox + x + 70, 1700 + (i % 2) * 40)], fill=(150, 150, 150), width=6)
    mx = ox + 3000; d.rectangle([mx, 1560, mx + 250, 1700], fill=(250, 190, 40)); d.rectangle([mx + 250, 1610, mx + 330, 1700], fill=(60, 110, 190)); d.ellipse([mx + 20, 1500, mx + 220, 1620], fill=(220, 220, 224), outline=(150, 150, 155), width=4)
    for k in range(6): a = t * 3 + k; d.line([(mx + 120 + 60 * math.cos(a), 1560 + 36 * math.sin(a)), (mx + 120 + 20 * math.cos(a + 1), 1560 + 12 * math.sin(a + 1))], fill=(190, 190, 196), width=4)
    for cx in (mx + 50, mx + 190, mx + 280): d.ellipse([cx - 32, 1670, cx + 32, 1734], fill=(24, 24, 28)); d.ellipse([cx - 14, 1688, cx + 14, 1716], fill=(190, 190, 200))
    # pozo con panel solar
    wx = ox + 2420; d.polygon([(wx + 560, 1190), (wx + 760, 1190), (wx + 800, 1130), (wx + 600, 1130)], fill=(30, 56, 120)); d.rectangle([wx + 640, 1190, wx + 650, 1380], fill=(120, 120, 126)); d.rectangle([wx + 560, 1380, wx + 740, 1440], fill=(150, 150, 156)); d.rectangle([wx + 590, 1340, wx + 600, 1380], fill=(60, 120, 200))
    wy = 1400
    for i in range(3): person(d, wx + 520 + i * 110, 1860, 270 - i * 8, SKINS[(i + 2) % 6], PAL_C[(i + 4) % 7], PAL_P[(i + 2) % 6], 0, walk=False, dance=t * 1.5 + i, carry='jug' if i != 1 else None, skirt=i == 0, hat='scarf' if i == 0 else None)
    return img.convert('RGB')

# ============ Cascada haitiana (Bassin-Bleu) ============
def shot_waterfall(t):
    img = vgrad([(0, (90, 170, 220)), (.3, (160, 215, 235)), (1, (200, 235, 230))]).convert('RGBA'); d = ImageDraw.Draw(img)
    put(img, cached('wf_m', lambda: mount_layer(base=700, amp=260, ctop=(70, 150, 90), cbot=(50, 120, 70), seed=81, f0=.005, trees='broad', tcol=(30, 110, 50), ntree=500)), 0)
    d = ImageDraw.Draw(img)
    # acantilado
    d.polygon([(250, 520), (880, 520), (940, 1250), (190, 1250)], fill=(120, 106, 90)); d.polygon([(250, 520), (420, 520), (360, 1250), (190, 1250)], fill=(150, 134, 112)); d.polygon([(760, 520), (880, 520), (940, 1250), (800, 1250)], fill=(96, 84, 70))
    r = random.Random(3)
    for i in range(70):
        x = 200 + r.random() * 730; y = 540 + r.random() * 700; s = r.uniform(18, 60); d.ellipse([x, y, x + s, y + s * .6], fill=shade((120, 106, 90), r.uniform(.8, 1.2)))
    for k in range(5):      # vegetación sobre el acantilado
        for i in range(12): broadtree(d, 200 + i * 62 + k * 7, 560 + k * 25, 120 + k * 12, (36 + k * 8, 124 + k * 5, 54))
    for k, (x0, w) in enumerate(((430, 90), (560, 120), (700, 70))):      # cascada animada
        d.polygon([(x0, 540), (x0 + w, 540), (x0 + w + 10, 1250), (x0 - 10, 1250)], fill=(236, 248, 252))
        for i in range(26):
            y = ((i * 41 + t * 520 + k * 60) % 700) + 540; x = x0 + 8 + (i * 17 % max(1, int(w - 16))); d.line([(x, y), (x, y + 70)], fill=(255, 255, 255, 220), width=5); d.line([(x + 14, y + 30), (x + 14, y + 90)], fill=(190, 225, 240, 200), width=4)
    d.rectangle([0, 1240, W, H], fill=(40, 170, 160))
    for i in range(30): d.line([(0, 1260 + i * 22), (W, 1260 + i * 22)], fill=(160, 240, 230, 90), width=3)
    sea_waves(d, 1250, 1700, t, (30, 150, 170), (70, 210, 200), 5, 28, 1.2, .015)
    for i in range(4): u = (t * .5 + i * .25) % 1; glow(img, 600 + 160 * math.sin(i * 2 + t), 1260 + u * 40, 220 + int(160 * u), (255, 255, 255), .5 * (1 - u), 1.5)
    d = ImageDraw.Draw(img)
    for x, y, s in ((80, 1420, 110), (260, 1500, 80), (930, 1380, 140), (860, 1560, 90)): d.ellipse([x - s, y - s * .55, x + s, y + s * .55], fill=shade((130, 120, 105), .9)); d.ellipse([x - s * .7, y - s * .5, x + s * .2, y], fill=(160, 150, 130))
    d.rectangle([0, 1700, W, H], fill=(70, 150, 70)); d.polygon([(0, 1700), (W, 1660), (W, H), (0, H)], fill=(64, 142, 66))
    for x in (60, 1000): palm(d, x, 1860, 700, t, .1 if x < 500 else -.1, x)
    ph = t * 3.4
    person(d, 340, 1700, 260, SKINS[0], (250, 220, 80), (240, 240, 240), 0, walk=False, dance=t * 1.2); person(d, 720, 1780, 300, SKINS[4], (90, 190, 120), (60, 80, 140), ph, skirt=False, carry='bag'); person(d, 560, 1900, 360, SKINS[2], (240, 90, 90), (250, 250, 250), ph + 1, skirt=True, hat='scarf')
    for i in range(6): bird(d, 160 + i * 140 + 20 * math.sin(t + i), 300 + 40 * math.cos(i), 22, t + i * .5)
    return camera(img.convert('RGB'), 1 + .02 * t, .5, .55)

# ============ Ciudad haitiana en la ladera ============
def shot_hillcity(t):
    img = cached('hc_sky', lambda: sky('day', (880, 240, 64))).copy(); clouds(img, t, 100, 4, 8, 1.2, (255, 255, 255), 5, 230); pan = t * 35
    put(img, cached('hc_m1', lambda: mount_layer(base=760, amp=300, ctop=(110, 156, 190), cbot=(140, 190, 200), seed=91, f0=.0038, hi=(230, 240, 250, 255))), pan * .1)
    put(img, cached('hc_m2', lambda: mount_layer(base=1000, amp=420, ctop=(110, 160, 90), cbot=(86, 138, 76), seed=92, f0=.0042, trees='broad', tcol=(50, 120, 60), ntree=400)), pan * .3)
    d = ImageDraw.Draw(img)
    def hill():
        L = new_rgba(W + 400, H); dd = ImageDraw.Draw(L); r = random.Random(6); f = ridge_fn(93, .004, 3)
        for row in range(14):
            y = 1000 + row * 62; x = -40
            while x < W + 440:
                w = r.randint(50, 92); hh = r.randint(44, 80); c = [(236, 90, 70), (250, 200, 60), (70, 160, 220), (240, 240, 230), (120, 200, 120), (230, 130, 190), (250, 150, 60), (150, 120, 220)][r.randrange(8)]
                yy = y - 120 * max(0, f(x)) * (1 - row / 14) ; dd.rectangle([x, yy, x + w, yy + hh], fill=c); dd.polygon([(x - 4, yy), (x + w / 2, yy - hh * .4), (x + w + 4, yy)], fill=shade(c, .6)); dd.rectangle([x + w * .2, yy + hh * .3, x + w * .42, yy + hh * .7], fill=shade(c, .5)); dd.rectangle([x + w * .6, yy + hh * .3, x + w * .8, yy + hh * .7], fill=shade(c, .5))
                x += w + r.randint(-4, 8)
        return L
    put(img, cached('hc_h', hill), pan * .6); d = ImageDraw.Draw(img)
    # iglesia
    d.rectangle([60 - pan * .6, 900, 200 - pan * .6, 1060], fill=(250, 244, 230)); d.polygon([(40 - pan * .6, 900), (130 - pan * .6, 800), (220 - pan * .6, 900)], fill=(200, 70, 60)); d.rectangle([128 - pan * .6, 740, 134 - pan * .6, 800], fill=(60, 50, 40))
    d.rectangle([0, 1870, W, H], fill=(90, 90, 98)) if False else None
    d.rectangle([0, 1520, W, H], fill=(206, 172, 122)); d.rectangle([0, 1500, W, 1530], fill=(180, 150, 108))
    # mar al fondo? calle con tap-taps
    tx = ((t * 230 + 100) % (W + 800)) - 600; tap_tap(d, tx, 1640, 520, (74, 160, 220), (250, 200, 40), t * 10); tx = W + 300 - ((t * 190 + 400) % (W + 800)); tap_tap(d, tx, 1790, 560, (230, 70, 80), (255, 255, 255), t * 10, flip=True)
    for i in range(5): person(d, (i * 250 + 60 - pan * 1.4) % (W + 300) - 100, 1900, 300, SKINS[i % 6], PAL_C[i], PAL_P[i], t * 4.4 + i, carry=['head', None, 'bag', 'head', None][i], hat=[None, 'straw', None, 'scarf', 'cap'][i], skirt=i in (0, 3))
    for x in (90, 930): palm(d, x, 1560, 420, t + x, .1, x)
    return camera(img.convert('RGB'), 1 + .02 * t, .5, .5)

# ============ Paisajes de montaña a pantalla completa ============
def land_mountain(country, t):
    pan = t * 35
    if country == 'DR':
        img = cached('lm_dr_sky', lambda: sky('haze', (850, 240, 60))).copy(); clouds(img, t, 120, 4, 8, 1.2, (255, 255, 255), 6, 230)
        mountains(img, t, DR_MTN, 0, pan); mist(img, t, 650, 1050, 120, 16)
        put(img, cached('lm_dr_f', lambda: mount_layer(base=1350, amp=240, ctop=(26, 98, 54), cbot=(18, 76, 44), seed=34, f0=.006, trees='pine', tcol=(14, 70, 40), ntree=1400)), pan * .9)
        d = ImageDraw.Draw(img); d.polygon([(0, 1620), (W, 1560), (W, H), (0, H)], fill=(20, 84, 48))
        for i in range(10): 
            x = (i * 130 + 20 - pan * 1.2) % (W + 200) - 60; s = 300 + (i % 3) * 90; yb = 1900 - (i % 2) * 60; d.polygon([(x, yb - s), (x - s * .28, yb), (x + s * .28, yb)], fill=shade((18, 86, 50), 1 + (i % 3) * .15)); d.polygon([(x, yb - s * .7), (x - s * .24, yb - s * .15), (x + s * .24, yb - s * .15)], fill=shade((24, 100, 58), 1 + (i % 3) * .1))
        for i in range(6): bird(d, 200 + i * 100, 330 + i * 18, 20, t + i * .4)
    else:
        img = cached('lm_ht_sky', lambda: sky('day', (850, 240, 60))).copy(); clouds(img, t, 120, 4, 8, 1.2, (255, 255, 255), 6, 230)
        for nm, kw, par in HT_MTN[:3]: put(img, cached(nm, lambda kw=kw: mount_layer(**kw)), pan * par)
        d = ImageDraw.Draw(img); citadelle(d, 650 - pan * .25, 800, 300); mist(img, t, 700, 1000, 100, 16, 4)
        for nm, kw, par in HT_MTN[3:]: put(img, cached(nm, lambda kw=kw: mount_layer(**kw)), pan * par)
        d = ImageDraw.Draw(img); r = random.Random(4)
        for i in range(8):
            y = 1450 + i * 60; cols = [(100, 170, 70), (150, 170, 80), (90, 150, 60), (190, 170, 90)]; pts = [(x, y + 20 * math.sin(x * .007 + i)) for x in range(0, W + 20, 20)]
            d.polygon(pts + [(W, H), (0, H)], fill=cols[i % 4]); d.line(pts, fill=shade(cols[i % 4], 1.25), width=4)
        for i in range(6):
            x = 80 + i * 170 - pan * .9 % 1; yy = 1480 + (i % 4) * 90; person(d, x, yy + 150, 260, SKINS[i % 6], PAL_C[i], PAL_P[i], 0, walk=False, dance=t * 3 + i, hat='straw')
        for i in range(5):
            x = (130 + i * 220 - pan * .9) % (W + 200) - 50; y = 1330 + (i % 3) * 25; c = PAL_C[i + 1]; d.rectangle([x, y, x + 70, y + 48], fill=c); d.polygon([(x - 5, y), (x + 35, y - 26), (x + 75, y)], fill=shade(c, .55))
        for i in range(6): bird(d, 160 + i * 130, 330 + 30 * math.cos(i), 20, t + i * .4)
    return camera(img.convert('RGB'), 1 + .02 * t, .5, .5)

def side_water(country, t): return shot_beach(t) if country == 'DR' else shot_waterfall(t)
def side_city(country, t): return shot_city(t) if country == 'DR' else shot_hillcity(t)

# ============ S7 PANTALLA DIVIDIDA ============
def shot_split(t):
    beats = [land_mountain, side_water, side_city]; b = min(2, int(max(t, 0) // 3.0)); lt = t - b * 3.0
    def side(country, tt):
        a = beats[b](country, tt)
        if lt < .4 and b > 0: return Image.blend(beats[b - 1](country, tt + 3.0), a, sm(lt / .4))
        return a
    L = side('HT', lt + 3 * b * 0); R = side('DR', lt)
    # diagonal con oscilación suave
    S = 2; m = Image.new('L', (W // S, H // S), 0); xm = 540 + 36 * math.sin(t * .9); dx = 130
    ImageDraw.Draw(m).polygon([(0, 0), ((xm + dx) / S, 0), ((xm - dx) / S, H / S), (0, H / S)], fill=255); m = m.resize((W, H), Image.BILINEAR)
    out = R.copy(); out.paste(L, (0, 0), m)
    ln = new_rgba(); ImageDraw.Draw(ln).line([(xm + dx, 0), (xm - dx, H)], fill=(255, 255, 255, 255), width=10)
    for col, off in (((40, 100, 255), -16), ((255, 60, 80), 16)):
        l2 = new_rgba(); ImageDraw.Draw(l2).line([(xm + dx + off, 0), (xm - dx + off, H)], fill=col + (255,), width=8); g = l2.filter(ImageFilter.GaussianBlur(10)); rgb = Image.new('RGB', (W, H), (0, 0, 0)); rgb.paste(Image.new('RGB', (W, H), col), mask=g.getchannel('A')); out = ImageChops.screen(out, rgb)
    o = out.convert('RGBA'); o.alpha_composite(ln.filter(ImageFilter.GaussianBlur(1)))
    return o.convert('RGB')
