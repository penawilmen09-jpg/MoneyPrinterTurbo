import math
import numpy as np
from PIL import Image, ImageChops, ImageFilter
import kit
from kit import *
import scenes_map as SM, shots_a as A, shots_b as B, shots_c as C

SHOTS = [  # nombre, inicio, fin, función(t_local)
 ('s1', 0.0, 7.0, SM.shot_s1),
 ('beach', 7.0, 9.4, A.shot_beach), ('city', 9.4, 11.8, A.shot_city), ('resort', 11.8, 14.0, A.shot_resort),
 ('citadelle', 14.0, 16.3, A.shot_citadelle), ('market', 16.3, 18.8, A.shot_market), ('coastHT', 18.8, 21.0, lambda t: A.shot_beach(t, 'HT')),
 ('border_air', 21.0, 24.4, B.shot_border_air), ('gate', 24.4, 28.0, B.shot_border_gate),
 ('dance_dr', 28.0, 30.3, B.shot_dance_dr), ('dance_ht', 30.3, 32.7, B.shot_dance_ht), ('food', 32.7, 35.0, B.shot_food),
 ('econ_dr', 35.0, 39.0, C.shot_econ_dr), ('econ_ht', 39.0, 43.0, C.shot_econ_ht),
 ('split', 43.0, 52.0, C.shot_split), ('s8', 52.0, 60.0, SM.shot_s8)]
TRANS = {1: ('flash', .7), 2: ('fade', .5), 3: ('fade', .5), 4: ('wipe', .6), 5: ('fade', .5), 6: ('fade', .5), 7: ('zoom', .6), 8: ('wipe', .6),
         9: ('flash', .6), 10: ('fade', .5), 11: ('fade', .5), 12: ('wipe', .6), 13: ('wipe', .6), 14: ('fade', .7), 15: ('fade', .9)}

def render_shot(i, tg):
    nm, a, b, fn = SHOTS[i]; kit.GT = tg; return fn(tg - a)

_wm = {}
def wipe_mask(p):
    k = round(p * 60)
    if k not in _wm:
        yy, xx = np.mgrid[0:H // 8, 0:W // 8].astype(np.float32); x = (xx * 8 + yy * 8 * .35) / (W + H * .35)
        m = np.clip((p * 1.25 - x) * 6 + .0, 0, 1) if False else np.clip(((p * 1.3 - .15) - x) * 7, 0, 1)
        _wm[k] = Image.fromarray((m * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)
    return _wm[k]

def frame_at(tg):
    idx = next(i for i, s in enumerate(SHOTS) if s[1] <= tg < s[2]) if tg < 60 else len(SHOTS) - 1
    img = render_shot(idx, tg)
    # ¿transición con la siguiente?
    for (j, (kind, dur)) in ((idx + 1, TRANS.get(idx + 1)),) if idx + 1 < len(SHOTS) and TRANS.get(idx + 1) else ():
        t0 = SHOTS[j][1]
        if tg > t0 - dur / 2:
            p = sm((tg - (t0 - dur / 2)) / dur); nxt = render_shot(j, tg)
            if kind == 'fade': img = Image.blend(img, nxt, p)
            elif kind == 'flash':
                img = Image.blend(img, nxt, p); f = math.exp(-((p - .5) / .22) ** 2); img = Image.blend(img, Image.new('RGB', (W, H), (255, 250, 235)), clamp(f * .85))
            elif kind == 'wipe':
                img.paste(nxt, (0, 0), wipe_mask(p))
            elif kind == 'zoom':
                a = camera(img, 1 + p * .7, .5, .5); b = camera(nxt, 1.5 - p * .5, .5, .5); img = Image.blend(a, b, p)
    # transición con la anterior
    if idx > 0 and TRANS.get(idx):
        kind, dur = TRANS[idx]; t0 = SHOTS[idx][1]
        if tg < t0 + dur / 2:
            p = sm((tg - (t0 - dur / 2)) / dur); prv = render_shot(idx - 1, tg)
            if kind == 'fade': img = Image.blend(prv, img, p)
            elif kind == 'flash': img = Image.blend(prv, img, p); f = math.exp(-((p - .5) / .22) ** 2); img = Image.blend(img, Image.new('RGB', (W, H), (255, 250, 235)), clamp(f * .85))
            elif kind == 'wipe': prv.paste(img, (0, 0), wipe_mask(p)); img = prv
            elif kind == 'zoom': a = camera(prv, 1 + p * .7, .5, .5); b = camera(img, 1.5 - p * .5, .5, .5); img = Image.blend(a, b, p)
    return post(img, tg)

_vig = None; _grain = None
def post(img, tg):
    global _vig, _grain
    if _vig is None:
        yy, xx = np.mgrid[0:H // 4, 0:W // 4].astype(np.float32); d = np.hypot((xx - W / 8) / (W / 8), (yy - H / 8) / (H / 8))
        v = np.clip(1 - np.clip(d - .5, 0, 2) * .30, .55, 1); _vig = np.asarray(Image.fromarray((v * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), np.float32)[..., None] / 255
        r = np.random.default_rng(1); _grain = [(r.standard_normal((H // 2, W // 2)) * 2.6).astype(np.float32) for _ in range(8)]
    sm_ = img.resize((W // 4, H // 4), Image.BILINEAR).point(lambda v: max(0, v - 170) * 3).filter(ImageFilter.GaussianBlur(9)).resize((W, H), Image.BICUBIC)
    img = ImageChops.add(img, sm_.point(lambda v: int(v * .35)))
    a = np.asarray(img, np.float32) * _vig
    g = _grain[int(tg * FPS) % 8]; g = np.repeat(np.repeat(g, 2, 0), 2, 1)[..., None]
    a = a + g
    # grading cálido suave
    a[..., 0] *= 1.02; a[..., 2] *= .98
    fi = clamp(tg / .5); fo = clamp((60.0 - tg) / .7); a *= min(fi, fo)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
