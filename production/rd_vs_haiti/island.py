"""Mapa estilizado de La Española: costa, relieve, frontera, nubes y cámara."""
import math, random, os, pickle
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
from kit import *

LON0, LAT0, K = -76.4, 21.3, 470.0
MW, MH = int(9.6 * K), int(5.0 * K * 1.07)
def P(lon, lat): return ((lon - LON0) * K, (LAT0 - lat) * K * 1.07)

COAST = [(-73.38,19.80),(-72.95,19.93),(-72.83,19.94),(-72.45,19.84),(-72.20,19.78),(-71.95,19.76),(-71.80,19.88),(-71.65,19.90),(-71.30,19.88),(-70.95,19.84),
 (-70.69,19.80),(-70.45,19.77),(-70.08,19.67),(-69.95,19.62),(-69.85,19.40),(-69.62,19.35),(-69.50,19.33),(-69.20,19.30),(-69.05,19.31),(-69.15,19.20),(-69.40,19.17),
 (-69.62,19.22),(-69.45,19.08),(-69.05,19.00),(-68.80,18.93),(-68.50,18.80),(-68.32,18.62),(-68.37,18.50),(-68.55,18.36),(-68.84,18.37),(-68.97,18.42),(-69.30,18.45),
 (-69.60,18.43),(-69.90,18.46),(-70.03,18.42),(-70.35,18.25),(-70.73,18.28),(-71.05,18.28),(-71.12,18.12),(-71.25,17.80),(-71.43,17.61),(-71.65,17.76),(-71.75,18.00),
 (-72.00,18.12),(-72.53,18.22),(-73.10,18.17),(-73.75,18.20),(-74.15,18.25),(-74.45,18.40),(-74.12,18.65),(-73.50,18.55),(-73.09,18.44),(-72.87,18.43),(-72.63,18.51),
 (-72.35,18.55),(-72.50,18.78),(-72.70,19.10),(-72.69,19.45),(-73.05,19.62)]
BORDER = [(-71.76,17.70),(-71.76,17.93),(-71.77,18.15),(-71.80,18.35),(-71.86,18.50),(-71.80,18.70),(-71.72,18.88),(-71.80,19.05),(-71.78,19.25),(-71.66,19.40),(-71.70,19.58),(-71.75,19.75),(-71.73,19.99)]
RIDGES = [  # (puntos, sigma_deg, altura)
 ([(-71.5,18.9),(-71.0,19.05),(-70.6,19.0),(-70.3,18.75)], .22, 1.0), ([(-71.3,19.7),(-70.4,19.65)], .1, .45), ([(-71.8,18.65),(-71.2,18.65)], .1, .6),
 ([(-71.7,18.2),(-71.2,18.1)], .1, .7), ([(-69.4,18.95),(-69.0,18.95)], .12, .3), ([(-72.8,19.55),(-72.0,19.4),(-71.8,19.3)], .15, .6),
 ([(-72.4,19.1),(-71.9,18.9)], .14, .55), ([(-72.4,18.4),(-71.9,18.3)], .12, .85), ([(-74.4,18.45),(-73.6,18.35)], .15, .8), ([(-73.3,19.7),(-72.9,19.65)], .1, .4)]
ISLETS = [((-72.95,18.85), .27, .07, -25), ((-72.77,20.03), .22, .05, -10), ((-68.65,18.20), .20, .09, 0)]

def mpd(pts, levels, amp, seed, closed=True):
    r = random.Random(seed); pts = list(pts)
    for lv in range(levels):
        out = []
        for i in range(len(pts)):
            a = pts[i]; b = pts[(i + 1) % len(pts)]
            if not closed and i == len(pts) - 1: out.append(a); break
            L = math.hypot(b[0] - a[0], b[1] - a[1]); nx, ny = -(b[1] - a[1]) / (L + 1e-6), (b[0] - a[0]) / (L + 1e-6)
            o = r.uniform(-1, 1) * L * amp
            out += [a, ((a[0] + b[0]) / 2 + nx * o, (a[1] + b[1]) / 2 + ny * o)]
        pts = out; amp *= 0.8
    return pts

def chaikin(pts, it=2):
    for _ in range(it):
        o = []
        for i in range(len(pts)):
            a = pts[i]; b = pts[(i + 1) % len(pts)]
            o += [(a[0] * .75 + b[0] * .25, a[1] * .75 + b[1] * .25), (a[0] * .25 + b[0] * .75, a[1] * .25 + b[1] * .75)]
        pts = o
    return pts

def build_map():
    cache = 'build/map.pkl'
    if os.path.exists(cache): return pickle.load(open(cache, 'rb'))
    coast = chaikin(mpd([P(*p) for p in COAST], 4, 0.22, 7), 2)
    land = Image.new('L', (MW, MH), 0); d = ImageDraw.Draw(land); d.polygon(coast, fill=255)
    for (c, a, b, ang) in ISLETS:
        cx, cy = P(*c); A, B = a * K / 2, b * K * 1.07 / 2; ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        d.polygon([(cx + A * math.cos(t) * ca - B * math.sin(t) * sa, cy + A * math.cos(t) * sa + B * math.sin(t) * ca) for t in [i * TAU / 40 for i in range(40)]], fill=255)
    land = land.filter(ImageFilter.GaussianBlur(2)).point(lambda v: 255 if v > 127 else 0)
    L = np.asarray(land, np.float32) / 255
    # elevación (1/4 res)
    sw, sh = MW // 4, MH // 4; yy, xx = np.mgrid[0:sh, 0:sw].astype(np.float32)
    ex = (xx * 4 / K + LON0).astype(np.float32); ey = (LAT0 - yy * 4 / (K * 1.07)).astype(np.float32); elev = np.zeros((sh, sw), np.float32)
    for pts, sg, hh in RIDGES:
        for i in range(len(pts) - 1):
            (x0, y0), (x1, y1) = pts[i], pts[i + 1]; vx, vy = x1 - x0, y1 - y0; ll = vx * vx + vy * vy
            tt = np.clip(((ex - x0) * vx + (ey - y0) * vy) / ll, 0, 1); dd = np.hypot(ex - (x0 + tt * vx), ey - (y0 + tt * vy))
            elev = np.maximum(elev, hh * np.exp(-(dd / sg) ** 2))
    nz = fbm_arr(sw, sh, 3, 6, 6); elev = np.clip(elev * (0.65 + 0.7 * nz) + 0.12 * (nz - .5), 0, 1.2)
    elev_full = np.asarray(Image.fromarray(elev).resize((MW, MH), Image.BICUBIC), np.float32)
    hf = np.asarray(Image.fromarray((fbm_arr(MW // 2, MH // 2, 11, 5, 40) * 255).astype(np.uint8)).resize((MW, MH), Image.BICUBIC), np.float32) / 255
    elev_full = np.clip(elev_full + (hf - .5) * .18, 0, 1.2)
    gy, gx = np.gradient(elev_full * 6.0); sh_ = np.clip(.5 + (gx * .7 + gy * .7) * 3.0, 0, 1)
    # frontera -> máscara este (RD)
    bp = [P(*p) for p in BORDER]; east = Image.new('L', (MW, MH), 0); ImageDraw.Draw(east).polygon(bp + [(MW, bp[-1][1]), (MW, bp[0][1])], fill=255)
    E = np.asarray(east, np.float32) / 255
    lowc = np.array([112, 176, 84], np.float32); midc = np.array([58, 138, 62], np.float32); hic = np.array([44, 104, 56], np.float32); rock = np.array([120, 112, 84], np.float32)
    e = elev_full[..., None]
    col = np.where(e < .3, lowc + (midc - lowc) * (e / .3), np.where(e < .7, midc + (hic - midc) * ((e - .3) / .4), hic + (rock - hic) * np.clip((e - .7) / .4, 0, 1)))
    dry = np.array([158, 160, 84], np.float32); wd = (1 - E)[..., None] * 0.30; col = col * (1 - wd) + dry * wd
    rg = np.random.default_rng(9); sp = np.asarray(Image.fromarray((rg.random((MH, MW)) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.6)), np.float32); sp = (sp - sp.mean()) / (sp.std() + 1e-6)
    sp2 = np.asarray(Image.fromarray((rg.random((MH // 3, MW // 3)) * 255).astype(np.uint8)).resize((MW, MH), Image.BICUBIC), np.float32); sp2 = (sp2 - sp2.mean()) / (sp2.std() + 1e-6)
    col = col * (0.62 + 0.8 * sh_[..., None]) * (0.92 + 0.16 * hf[..., None]) * (1 + 0.06 * sp[..., None] * 3 + 0.05 * sp2[..., None]) 
    # mar
    d1 = np.asarray(land.filter(ImageFilter.GaussianBlur(22)), np.float32) / 255; d2 = np.asarray(land.filter(ImageFilter.GaussianBlur(70)), np.float32) / 255
    d3 = np.asarray(land.filter(ImageFilter.GaussianBlur(160)), np.float32) / 255
    deep = np.array([6, 54, 118], np.float32); mid = np.array([8, 112, 176], np.float32); shal = np.array([46, 200, 206], np.float32); lag = np.array([120, 232, 218], np.float32)
    sea = deep + (mid - deep) * np.clip(d3 * 2.2, 0, 1)[..., None]
    sea = sea + (shal - sea) * np.clip(d2 * 1.8, 0, 1)[..., None]; sea = sea + (lag - sea) * np.clip(d1 * 1.2, 0, 1)[..., None]
    swn = np.asarray(Image.fromarray((fbm_arr(MW // 4, MH // 4, 5, 5, 10) * 255).astype(np.uint8)).resize((MW, MH), Image.BICUBIC), np.float32) / 255
    sea *= (0.93 + 0.14 * swn[..., None])
    # playa y espuma
    er = np.asarray(land.filter(ImageFilter.MinFilter(13)).filter(ImageFilter.GaussianBlur(2)), np.float32) / 255
    beach = np.clip(L - er, 0, 1)[..., None]; col = col * (1 - beach * .85) + np.array([236, 222, 170], np.float32) * beach * .85
    foam = np.clip(np.asarray(land.filter(ImageFilter.GaussianBlur(5)), np.float32) / 255 - L, 0, 1)
    out = sea * (1 - L[..., None]) + col * L[..., None]; fm = np.clip(foam * 2.4, 0, .75)[..., None]; out = out * (1 - fm) + 255 * fm
    # lago Enriquillo
    lk = Image.new('L', (MW, MH), 0); cx, cy = P(-71.6, 18.47); ImageDraw.Draw(lk).ellipse([cx - 55, cy - 12, cx + 55, cy + 12], fill=255)
    lk = np.asarray(lk.filter(ImageFilter.GaussianBlur(3)), np.float32)[..., None] / 255; out = out * (1 - lk * .9) + np.array([40, 130, 180], np.float32) * lk * .9
    img = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
    # ríos
    rd = ImageDraw.Draw(img); rr = random.Random(2)
    for (a, b) in [((-70.9, 19.1), (-70.0, 19.5)), ((-70.8, 18.9), (-70.2, 18.4)), ((-72.4, 19.0), (-72.1, 18.6)), ((-72.5, 18.3), (-72.3, 18.5))]:
        pts = mpd([P(*a), P(*b)], 5, .22, rr.randint(0, 99), closed=False); rd.line(pts, fill=(96, 188, 214), width=3)
    res = dict(img=img, land=land, east=east, border=bp, coast=coast)
    pickle.dump(res, open(cache, 'wb')); return res

_M = None
def M():
    global _M
    if _M is None: _M = build_map()
    return _M

def cloud_tex(seed, size=4096):
    a = fbm_arr(size // 2, size // 2, seed, 6, 3); a = np.clip((a - .56) * 4.2, 0, 1)
    im = Image.fromarray((a * 255).astype(np.uint8)).resize((size, size), Image.BICUBIC).filter(ImageFilter.GaussianBlur(6))
    out = Image.new('RGBA', (size, size), (255, 255, 255, 0)); out.putalpha(im.point(lambda v: int(v * .85))); return out

_CT = {}
def map_view(cx, cy, z, size=(W, H), fill=(6, 54, 118)):
    m = M()['img']; bw, bh = size[0] / z, size[1] / z
    return m.transform(size, Image.EXTENT, (cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2), Image.BILINEAR, fillcolor=fill)

def cloud_layer(img, cx, cy, z, t, k=1.5, seed=1, drift=40.0, alpha=1.0):
    if seed not in _CT: _CT[seed] = cloud_tex(seed)
    ct = _CT[seed]; zz = max(z * k, 0.80); bw, bh = W / zz, H / zz
    ox = (cx * 0.35 + t * drift) % (ct.width - bw - 2); oy = (cy * 0.35) % (ct.height - bh - 2)
    layer = ct.transform((W, H), Image.EXTENT, (ox, oy, ox + bw, oy + bh), Image.BILINEAR)
    if alpha < 1: layer.putalpha(layer.getchannel('A').point(lambda v: int(v * alpha)))
    img.alpha_composite(layer)

def to_screen(p, cx, cy, z): return ((p[0] - cx) * z + W / 2, (p[1] - cy) * z + H / 2)

def border_fx(img, cx, cy, z, t, strength=1.0):
    bp = M()['border']; pts = [to_screen(p, cx, cy, z) for p in bp]
    lay = new_rgba(); d = ImageDraw.Draw(lay)
    pulse = .65 + .35 * math.sin(t * 3.2)
    for off, col in ((-12 * z, (40, 110, 255)), (12 * z, (255, 60, 80))):
        l2 = new_rgba(); ImageDraw.Draw(l2).line([(x + off, y) for x, y in pts], fill=col + (int(255 * strength),), width=max(3, int(9 * z)), joint='curve')
        g = l2.filter(ImageFilter.GaussianBlur(12 * z)); a = g.getchannel('A').point(lambda v: int(min(255, v * 3.0 * pulse)))
        rgb = Image.new('RGB', g.size, (0, 0, 0)); rgb.paste(Image.new('RGB', g.size, col), mask=a)
        img.paste(ImageChops.screen(img.convert('RGB'), rgb))
    d2 = ImageDraw.Draw(img); d2.line(pts, fill=(255, 250, 220, int(230 * strength)), width=max(2, int(3 * z / 1.2)), joint='curve')
