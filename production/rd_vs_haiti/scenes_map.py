import math, random
from kit import *
import island as I

def shot_s1(t):           # t: 0..~7.4
    u = sm(t / 7.0); e = u ** 1.0
    z = lerp(0.20, 1.42, sm(seg(t, 0, 7.2)) ** 0.9)
    c0 = I.P(-71.3, 19.05); c1 = I.P(-71.76, 19.02)
    f = sm(seg(t, 1.0, 7.2)); cx = lerp(c0[0], c1[0], f); cy = lerp(c0[1], c1[1], f)
    img = I.map_view(cx, cy, z).convert('RGBA')
    # tintes por país
    if False:
        a = sm(seg(t, 3.2, 5.6)) * 0.0
        m = I.M(); land = m['land']; east = m['east']
        lv = I.map_view(cx, cy, z, fill=0).convert('L') if False else None
        lm = land.transform((W, H), Image.EXTENT, (cx - W / z / 2, cy - H / z / 2, cx + W / z / 2, cy + H / z / 2), Image.BILINEAR)
        em = east.transform((W, H), Image.EXTENT, (cx - W / z / 2, cy - H / z / 2, cx + W / z / 2, cy + H / z / 2), Image.BILINEAR)
        hm = ImageChops.multiply(lm, ImageChops.invert(em)).point(lambda v: int(v * a)); dm = ImageChops.multiply(lm, em).point(lambda v: int(v * a))
        for mm, col in ((hm, (30, 80, 255)), (dm, (255, 60, 70))):
            lay = Image.new('RGBA', (W, H), col + (0,)); lay.putalpha(mm); img.alpha_composite(lay)
    # sombras de nubes + nubes
    sh = new_rgba(); I.cloud_layer(sh, cx, cy, z, t, k=1.0, seed=2, drift=22, alpha=1.0)
    blk = Image.new('RGBA', (W, H), (0, 20, 50, 0)); blk.putalpha(sh.getchannel('A').point(lambda v: int(v * .28)).transform((W, H), Image.AFFINE, (1, 0, -34, 0, 1, -50)))
    img.alpha_composite(blk)
    if t > 3.5: I.border_fx(img, cx, cy, z, t, sm(seg(t, 3.5, 5.5)))
    hi = (1 - sm(seg(t, 0, 4.0))) * 1.0 + 0.5 * (1 - sm(seg(t, 4, 7)))
    I.cloud_layer(img, cx, cy, z, t, k=1.0, seed=2, drift=22, alpha=.62 * (1 - .8 * sm(seg(t, 2.5, 5.5))))
    I.cloud_layer(img, cx, cy, z, t, k=1.9, seed=5, drift=55, alpha=min(1, .08 + .5 * (1 - sm(seg(t, 0, 4.0)))))
    glow(img, 900, 120, 1100, (255, 240, 200), .30, 2.2)
    return img.convert('RGB')

_stars = None
def stars_bg(t):
    global _stars
    if _stars is None:
        r = np.random.default_rng(4); bg = vgrad([(0, (2, 4, 18)), (.6, (6, 12, 40)), (1, (16, 22, 60))]).convert('RGBA'); d = ImageDraw.Draw(bg)
        _stars = (bg, [(r.random() * W, r.random() * H, r.random() * 6.28, 1 + int(r.random() * 2.4), 120 + int(r.random() * 135)) for _ in range(420)])
    bg, st = _stars; img = bg.copy(); d = ImageDraw.Draw(img)
    for x, y, ph, s, b in st:
        tw = .6 + .4 * math.sin(t * 2.5 + ph); v = int(b * tw); d.ellipse([x - s, y - s, x + s, y + s], fill=(v, v, min(255, v + 25), 255))
    return img

def caribbean_sunset(t):
    img = vgrad([(0, (36, 24, 86)), (.25, (120, 46, 112)), (.42, (240, 110, 70)), (.52, (255, 190, 100)), (.5, (255, 190, 100)), (1, (255, 190, 100))]).convert('RGBA')
    hy = 1030; d = ImageDraw.Draw(img)
    sx, sy = 540, hy - 120 + 60 * (1 - sm(seg(t, 0, 3)))
    sun_disc(img, sx, sy, 110, (255, 238, 190), (255, 150, 70))
    clouds(img, t, 300, 6, 6, 1.5, (255, 170, 130), 3, 200); clouds(img, t, 560, 5, 10, 1.1, (255, 130, 110), 8, 180)
    # silueta de la isla a lo lejos (dos tonos: oeste y este)
    d = ImageDraw.Draw(img)
    f1 = I.ridge_fn(21, .006, 4); f2 = I.ridge_fn(33, .007, 4)
    pts = [(x, hy - 30 - 58 * max(0, f1(x) + .35)) for x in range(0, 560, 8)]; d.polygon(pts + [(560, hy), (0, hy)], fill=(60, 40, 90, 255))
    pts = [(x, hy - 22 - 46 * max(0, f2(x) + .3)) for x in range(520, W + 8, 8)]; d.polygon(pts + [(W, hy), (520, hy)], fill=(72, 44, 92, 255))
    # mar
    sea = vgrad([(0, (255, 150, 90)), (.15, (210, 90, 100)), (.5, (80, 40, 110)), (1, (20, 20, 70))], W, H - hy); img.paste(sea, (0, hy))
    d = ImageDraw.Draw(img)
    for i in range(60):    # reflejo del sol
        y = hy + 6 + i * 13; ww = 70 + i * 4.6 + 20 * math.sin(t * 2 + i); off = 14 * math.sin(t * 3 + i * .9)
        a = int(210 * (1 - i / 64)); d.rectangle([540 - ww / 2 + off, y, 540 + ww / 2 + off, y + 4], fill=(255, 220, 150, a))
    for i in range(22):
        y = hy + 30 + i * i * 1.9; d.line([(0, y + 3 * math.sin(t + i)), (W, y + 3 * math.cos(t * 1.2 + i))], fill=(255, 170, 130, 22), width=2)
    sailboat(d, 250, hy + 70, 150, t, (20, 12, 30), (30, 18, 40), (34, 20, 44))
    sailboat(d, 800, hy + 40, 90, t + 2, (20, 12, 30), (30, 18, 40), (34, 20, 44))
    # palmeras en silueta (una a cada lado)
    palm(d, 80, 1800, 760, t, .16, 1, (14, 10, 20), (16, 12, 26), (20, 14, 30)); palm(d, 1010, 1850, 640, t + 1, -.18, 2, (14, 10, 20), (16, 12, 26), (20, 14, 30))
    d.rectangle([0, 1830, W, H], fill=(12, 8, 18, 255))
    for i in range(5): bird(d, 330 + i * 70 + t * 20 % 200, 430 + 22 * math.sin(i * 2) - i * 10, 22 - i * 2, t + i * .3, (30, 18, 40))
    glow(img, sx, sy, 1500, (255, 180, 90), .28, 2.0)
    return img.convert('RGB')

def planet_view(t, R, z, cx, cy, pc=(540, 1020)):
    img = stars_bg(t)
    S = 2; mask = Image.new('L', (W * S // 2, H * S // 2), 0); ImageDraw.Draw(mask).ellipse([(pc[0] - R) / 2 * S, (pc[1] - R) / 2 * S, (pc[0] + R) / 2 * S, (pc[1] + R) / 2 * S], fill=255)
    mask = mask.resize((W, H), Image.LANCZOS)
    surf = I.map_view(cx, cy, z, fill=(6, 54, 118)).convert('RGBA')
    # corrige centro: el mapa se centra en el centro de pantalla; desplazamos al centro del planeta
    surf = surf.transform((W, H), Image.AFFINE, (1, 0, -(pc[0] - W / 2), 0, 1, -(pc[1] - H / 2)), Image.BILINEAR, fillcolor=(6, 54, 118, 255))
    sh = new_rgba(); I.cloud_layer(sh, cx, cy, z * .9, t, k=1.0, seed=2, drift=18, alpha=.55); sh = sh.transform((W, H), Image.AFFINE, (1, 0, -(pc[0] - W / 2), 0, 1, -(pc[1] - H / 2)))
    surf.alpha_composite(sh)
    # iluminación de atardecer
    ang = math.radians(200); lx, ly = math.cos(ang), math.sin(ang)
    yy, xx = np.mgrid[0:H:2, 0:W:2].astype(np.float32); proj = ((xx - pc[0]) * lx + (yy - pc[1]) * ly) / R
    lit = np.clip(.5 + proj * 0.65, 0, 1.0); dist = np.hypot(xx - pc[0], yy - pc[1]) / R; limb = np.clip(1 - (dist ** 3) * .75, .25, 1)
    warm = np.clip(1 - np.abs(proj + .05) * 1.5, 0, 1)
    arr = np.asarray(surf.convert('RGB').resize((W // 2, H // 2)), np.float32)
    dark = np.array([.20, .26, .50], np.float32); bright = np.array([1.12, 1.0, .85], np.float32)
    mult = dark + (bright - dark) * lit[..., None]; arr = arr * mult * limb[..., None] + warm[..., None] * np.array([60, 28, 6], np.float32) * (lit[..., None] + .2)
    surf2 = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).resize((W, H), Image.BILINEAR).convert('RGBA')
    # atmósfera
    atm = new_rgba(); da = ImageDraw.Draw(atm); da.ellipse([pc[0] - R - 6, pc[1] - R - 6, pc[0] + R + 6, pc[1] + R + 6], outline=(130, 200, 255, 255), width=14)
    a1 = atm.filter(ImageFilter.GaussianBlur(18)); a2 = atm.filter(ImageFilter.GaussianBlur(5))
    img.alpha_composite(a1); img.alpha_composite(a1); img.alpha_composite(a2)
    # brillo naranja del atardecer en el borde izquierdo
    glow(img, pc[0] + lx * R, pc[1] + ly * R, int(R * 1.2), (255, 140, 60), .55, 2.2)
    img.paste(surf2.convert('RGB'), (0, 0), mask)
    # espejo del sol en el mar
    glow(img, pc[0] + lx * R * .55, pc[1] + ly * R * .55, int(R * .45), (255, 210, 150), .35, 2.4)
    return img.convert('RGB')

def shot_s8(t):           # t 0..8.4  (escena 52..60)
    f = sm(seg(t, 0, 6.2)); R = lerp(1700, 760, f ** .85); z = lerp(.95, .30, f ** .9)
    c = I.P(-71.3, 19.05); c = (lerp(I.P(-71.5, 19.0)[0], c[0], f), lerp(I.P(-71.5, 19.0)[1], c[1], f))
    pc = (540, lerp(900, 840, f))
    a = planet_view(t, R, z, c[0], c[1], pc)
    fin = sm(seg(t, 6.3, 7.4))
    if fin > 0:
        b = caribbean_sunset(t - 6.0); b = camera(b, 1.0 + .03 * (t - 6.0) / 2, .5, .55)
        a = Image.blend(a, b, fin)
    return a
