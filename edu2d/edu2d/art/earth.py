"""Tierra en '3D simulado': textura equirectangular procedural proyectada sobre una esfera con numpy."""
import base64
import io
import math
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

TW, TH = 2048, 1024

LAND = {
 "namerica": [(-168,66),(-160,70),(-140,70),(-125,70),(-95,72),(-80,70),(-62,60),(-55,50),(-67,45),(-70,42),(-76,37),(-81,31),(-80,25),(-83,29),(-90,30),(-97,26),(-97,21),(-92,18),(-88,21),(-87,16),(-83,10),(-78,8),(-86,12),(-92,15),(-105,20),(-112,28),(-117,32),(-124,40),(-124,48),(-130,55),(-140,60),(-152,59),(-165,55),(-160,60),(-166,64)],
 "greenland": [(-55,60),(-45,60),(-20,70),(-20,80),(-60,82),(-72,78),(-55,70)],
 "samerica": [(-78,8),(-72,12),(-62,10),(-52,5),(-50,0),(-35,-5),(-35,-9),(-40,-22),(-48,-26),(-58,-35),(-62,-40),(-66,-46),(-69,-52),(-72,-54),(-74,-47),(-73,-38),(-71,-30),(-70,-18),(-76,-14),(-81,-5),(-80,0),(-77,4)],
 "europe": [(-10,36),(-9,43),(-2,44),(-4,48),(2,51),(8,54),(10,57),(5,60),(10,64),(20,70),(30,70),(40,66),(42,60),(30,55),(38,46),(30,45),(28,41),(24,38),(20,40),(16,38),(12,44),(8,44),(3,43),(-5,37)],
 "africa": [(-17,21),(-16,12),(-9,5),(5,5),(9,4),(12,-5),(14,-17),(18,-33),(25,-34),(32,-28),(35,-20),(40,-12),(40,-3),(51,11),(43,12),(35,28),(32,31),(20,32),(10,37),(-5,36),(-12,28)],
 "asia": [(28,41),(36,36),(35,30),(44,13),(56,17),(60,25),(67,25),(73,20),(77,8),(80,15),(88,22),(92,20),(98,10),(100,2),(104,1),(108,12),(106,21),(120,23),(122,30),(121,40),(130,43),(142,50),(155,60),(160,62),(180,66),(180,70),(140,72),(110,77),(80,73),(60,70),(45,60),(42,60),(40,66),(45,50),(52,45),(48,40),(40,42)],
 "australia": [(114,-22),(122,-18),(131,-12),(137,-12),(142,-11),(146,-19),(153,-26),(150,-37),(141,-38),(135,-34),(129,-32),(115,-34)],
 "antarctica": [(lo, -72) for lo in range(-180, 181, 20)] + [(180, -90), (-180, -90)],
 "uk": [(-5,50),(1,51),(2,53),(-2,57),(-5,58),(-6,55),(-3,54)],
 "japan": [(130,31),(135,34),(140,36),(142,40),(141,45),(138,40),(132,34)],
 "indonesia": [(95,5),(105,-6),(115,-8),(120,-9),(108,-6),(100,-1)],
 "madagascar": [(44,-25),(47,-25),(50,-15),(49,-12),(44,-17)],
 "newzealand": [(172,-35),(178,-38),(175,-41),(167,-46),(170,-43)],
}
DESERT = [(-10, 12, 30, 28), (35, 12, 60, 32), (118, -32, 140, -22), (-115, 28, -105, 36), (60, 38, 90, 44), (-70, -30, -66, -20)]


def _xy(lon, lat):
    return ((lon + 180) / 360 * TW, (90 - lat) / 180 * TH)


def _pnoise(rng, h, w):
    """Ruido de baja frecuencia periódico en longitud (sin costura en el antimeridiano)."""
    a = rng.random((h, w + 1)); a[:, -1] = a[:, 0]
    im = Image.fromarray((a * 255).astype(np.uint8)).resize((TW + TW // w, TH), Image.BICUBIC)
    return np.asarray(im, dtype=np.float32)[:, :TW] / 255


@lru_cache(maxsize=1)
def textures():
    rng = np.random.default_rng(42)
    land = Image.new("L", (TW, TH), 0)
    dr = ImageDraw.Draw(land)
    for name, pts in LAND.items():
        dr.polygon([_xy(*p) for p in pts], fill=255)
    land = land.filter(ImageFilter.GaussianBlur(1.2))
    L = np.asarray(land, dtype=np.float32) / 255
    # ruido de baja frecuencia para variar colores
    nz = _pnoise(rng, 64, 128)
    lat = (90 - (np.arange(TH) + .5) / TH * 180)[:, None]
    ocean = np.zeros((TH, TW, 3), np.float32)
    deep = np.array([8, 55, 120], np.float32); shallow = np.array([30, 125, 190], np.float32)
    k = (.55 + .45 * np.cos(np.radians(lat)))[..., None] * (.8 + .2 * nz[..., None])
    ocean = deep * (1 - k) + shallow * k
    green = np.array([52, 150, 78], np.float32); dark = np.array([30, 105, 60], np.float32); tan = np.array([214, 180, 105], np.float32)
    landc = green * nz[..., None] + dark * (1 - nz[..., None])
    des = Image.new("L", (TW, TH), 0); dd = ImageDraw.Draw(des)
    for (a, b, c, d) in DESERT:
        x0, y0 = _xy(a, d); x1, y1 = _xy(c, b)
        dd.ellipse([x0, y0, x1, y1], fill=210)
    des = np.asarray(des.filter(ImageFilter.GaussianBlur(14)), dtype=np.float32)[..., None] / 255
    landc = landc * (1 - des) + tan * des
    gm = Image.new("L", (TW, TH), 0); ImageDraw.Draw(gm).polygon([_xy(*p) for p in LAND["greenland"]], fill=255)
    gm = np.asarray(gm.filter(ImageFilter.GaussianBlur(1.5)), dtype=np.float32) / 255
    ice = np.maximum(np.maximum(np.clip((lat - 74) / 6, 0, 1), np.clip((-lat - 62) / 4, 0, 1)), gm)[..., None]
    col = ocean * (1 - L[..., None]) + landc * L[..., None]
    col = col * (1 - ice) + np.array([240, 246, 255], np.float32) * ice
    # luces de ciudades (solo tierra, sin hielo)
    lights = (rng.random((TH, TW)) > .9965).astype(np.float32) * L * (np.abs(lat[:, 0:1]) < 62)
    lights = np.asarray(Image.fromarray((lights * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2.2)), dtype=np.float32) / 255 * 6
    # nubes
    c = _pnoise(rng, 40, 80)
    c2 = _pnoise(rng, 90, 180)
    cl = np.clip(((c * .6 + c2 * .4) - .6) * 4.5, 0, 1)
    cl = np.asarray(Image.fromarray((cl * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(5)), dtype=np.float32) / 255
    return col, np.clip(lights, 0, 1), cl, L


@lru_cache(maxsize=8)
def _geom(size, view_tilt, axis_tilt):
    r = size / 2
    ys, xs = np.mgrid[0:size, 0:size]
    x = (xs + .5 - r) / r; y = -(ys + .5 - r) / r
    rr = x * x + y * y
    inside = rr < 1
    z = np.sqrt(np.clip(1 - rr, 0, 1))
    # normal en pantalla (para luz)
    n = np.stack([x, y, z], -1)
    # inclinación del eje (en el plano de pantalla) y de la vista (hacia el polo norte)
    a = math.radians(axis_tilt); b = math.radians(view_tilt)
    xr = x * math.cos(a) - y * math.sin(a)     # rota el sistema para inclinar el eje
    yr = x * math.sin(a) + y * math.cos(a)
    y2 = yr * math.cos(b) + z * math.sin(b)
    z2 = -yr * math.sin(b) + z * math.cos(b)
    lat = np.arcsin(np.clip(y2, -1, 1))
    lon0 = np.arctan2(xr, z2)
    Lv = np.array([-.55, .45, .7]); Lv /= np.linalg.norm(Lv)
    lam = n @ Lv
    alpha = np.clip((1 - np.sqrt(rr)) * r * .9, 0, 1)
    return inside, z, lat, lon0, lam, alpha


def earth_uri(rot_deg, size=720, view_tilt=18, axis_tilt=-23, cloud_extra=1.0, night_boost=1.0, tint=None):
    col, lights, cl, L = textures()
    inside, z, lat, lon0, lam, alpha = _geom(size, view_tilt, axis_tilt)
    lon = lon0 - math.radians(rot_deg)
    u = (((lon / (2 * math.pi)) % 1.0) * TW).astype(np.int32) % TW
    v = np.clip(((.5 - lat / math.pi) * TH).astype(np.int32), 0, TH - 1)
    c = col[v, u]
    land = L[v, u]
    lc = cl[v, (u + int(rot_deg * 3.0)) % TW] * .7   # nubes giran algo más rápido
    c = c * (1 - lc[..., None]) + 255 * lc[..., None]
    day = np.clip(lam * 1.15 + .2, 0, 1) ** .85
    shade = .16 + .84 * day
    out = c * shade[..., None]
    # reflejo solar en el océano
    spec = np.clip(lam, 0, 1) ** 24 * (1 - land) * (1 - lc) * .75
    out += spec[..., None] * 255
    # luces nocturnas
    ln = lights[v, u] * np.clip(-lam * 2.2 + .25, 0, 1) * night_boost
    out += ln[..., None] * np.array([255, 205, 110])
    # halo atmosférico
    rim = (1 - z) ** 2.6
    out += rim[..., None] * np.array([90, 170, 255]) * (.35 + .9 * np.clip(lam + .4, 0, 1))[..., None]
    if tint is not None:
        out = out * (1 - tint[3]) + np.array(tint[:3]) * tint[3]
    rgba = np.zeros((size, size, 4), np.uint8)
    rgba[..., :3] = np.clip(out, 0, 255).astype(np.uint8)
    rgba[..., 3] = (alpha * 255).astype(np.uint8)
    buf = io.BytesIO()
    Image.fromarray(rgba, "RGBA").save(buf, "PNG", compress_level=1)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def earth(cx, cy, R, rot_deg, **kw):
    """SVG: halo atmosférico + esfera texturizada centrada en (cx,cy) con radio R."""
    size = int(min(max(2 * R, 200), 760))
    uri = earth_uri(rot_deg, size=size, **kw)
    return (f'<circle cx="{cx}" cy="{cy}" r="{R*1.28:.0f}" fill="url(#atmo)"/>'
            f'<image href="{uri}" x="{cx-R:.1f}" y="{cy-R:.1f}" width="{2*R:.1f}" height="{2*R:.1f}"/>')


def stars(t, n_=90, seed=3, h=1920):
    import random
    rnd = random.Random(seed); out = ""
    for i in range(n_):
        x, y, r = rnd.uniform(0, 1080), rnd.uniform(0, h), rnd.choice([1.3, 1.8, 2.4, 3])
        op = .35 + .65 * abs(math.sin(t * rnd.uniform(.6, 2.0) + i))
        out += f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r}" fill="#fff" opacity="{op:.2f}"/>'
    return out
