"""Escenario 2D: capas pre-renderizadas con paralaje + personajes/props dinámicos + cámara."""
import math, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "explora_ciencia360"))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from common import (W, H, FPS, Frame, Cam, clamp, prog, ease, ease_out, ease_in, ease_io, ease_back, lerp, mix, sc, to_uint8,
                    blur_np, grain, font as _font, CYAN, AMBER, WHITE, RED, VIOLET, MAGENTA, BLUE, FONT_BOLD, FONT_MED)
from people import draw_person, mk, walk_pose, run_pose, blink, shade, HX, HY, CW, CH

TS = 1.4   # escala de textura de capa respecto al mundo


class Pen:
    def __init__(self, im, S):
        self.im, self.d, self.S = im, ImageDraw.Draw(im), S

    def _p(self, pts): return [(x * self.S, y * self.S) for x, y in pts]
    def _ov(self, pts, draw):
        """Dibuja una forma translúcida mezclando con alpha (ImageDraw sólo sustituye píxeles)."""
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        x0, y0 = max(int(min(xs)) - 2, 0), max(int(min(ys)) - 2, 0); x1, y1 = min(int(max(xs)) + 3, self.im.width), min(int(max(ys)) + 3, self.im.height)
        if x1 <= x0 or y1 <= y0: return
        ov = Image.new("RGBA", (x1 - x0, y1 - y0), (0, 0, 0, 0))
        draw(ImageDraw.Draw(ov), x0, y0)
        self.im.alpha_composite(ov, (x0, y0))

    def poly(self, pts, fill, outline=None):
        if isinstance(fill, tuple) and len(fill) == 4 and fill[3] < 255:
            P = self._p(pts); self._ov(P, lambda d, x0, y0: d.polygon([(x - x0, y - y0) for x, y in P], fill=fill)); return
        self.d.polygon(self._p(pts), fill=fill, outline=outline)
    def rect(self, x0, y0, x1, y1, fill, outline=None, w=0): self.d.rectangle([x0 * self.S, y0 * self.S, x1 * self.S, y1 * self.S], fill=fill, outline=outline, width=int(w * self.S))
    def rrect(self, x0, y0, x1, y1, r, fill, outline=None, w=0): self.d.rounded_rectangle([x0 * self.S, y0 * self.S, x1 * self.S, y1 * self.S], radius=r * self.S, fill=fill, outline=outline, width=int(w * self.S))
    def ell(self, cx, cy, rx, ry, fill=None, outline=None, w=0):
        box = [(cx - rx) * self.S, (cy - ry) * self.S, (cx + rx) * self.S, (cy + ry) * self.S]
        if isinstance(fill, tuple) and len(fill) == 4 and fill[3] < 255:
            self._ov([(box[0], box[1]), (box[2], box[3])], lambda d, x0, y0: d.ellipse([box[0] - x0, box[1] - y0, box[2] - x0, box[3] - y0], fill=fill)); return
        self.d.ellipse(box, fill=fill, outline=outline, width=int(w * self.S))
    def line(self, pts, fill, w=1): self.d.line(self._p(pts), fill=fill, width=max(int(w * self.S), 1), joint="curve")
    def arc(self, box, a0, a1, fill, w=1): self.d.arc([box[0] * self.S, box[1] * self.S, box[2] * self.S, box[3] * self.S], a0, a1, fill=fill, width=int(w * self.S))
    def text(self, x, y, s, size, fill, bold=True, anchor="la"):
        fo = ImageFont.truetype(FONT_BOLD if bold else FONT_MED, int(size * self.S))
        self.d.text((x * self.S, y * self.S), s, font=fo, fill=fill, anchor=anchor)
    def vgrad(self, x0, y0, x1, y1, stops):
        """Degradado vertical con paradas [(pos0..1, color)]."""
        h = int((y1 - y0) * self.S); w = int((x1 - x0) * self.S)
        t = np.linspace(0, 1, h)[:, None]
        out = np.zeros((h, 1, 3), np.float32)
        for (p0, c0), (p1, c1) in zip(stops[:-1], stops[1:]):
            m = ((t >= p0) & (t <= p1))
            k = np.clip((t - p0) / max(p1 - p0, 1e-6), 0, 1)
            out += (np.array(c0, np.float32) * (1 - k) + np.array(c1, np.float32) * k)[:, None, :] * m[:, :, None]
        arr = np.repeat(out, w, axis=1).astype(np.uint8)
        self.im.paste(Image.fromarray(arr, "RGB"), (int(x0 * self.S), int(y0 * self.S)))


def bake(w, h, fn, ss=2, ts=TS):
    S = ss * ts
    im = Image.new("RGBA", (int(w * S), int(h * S)), (0, 0, 0, 0))
    fn(Pen(im, S))
    return im.resize((int(w * ts), int(h * ts)), Image.LANCZOS)


class Layer:
    def __init__(self, img, w, h, ox=0, oy=0, par=1.0, zpar=1.0, ref=(540, 960)):
        self.img, self.w, self.h, self.ox, self.oy, self.par, self.zpar, self.ref = img, w, h, ox, oy, par, zpar, ref

    def blit(self, base, cam, alpha=1.0, dx=0.0, dy=0.0):
        ze = 1 + (cam.z - 1) * self.zpar
        cx = cam.cx * self.par + self.ref[0] * (1 - self.par); cy = cam.cy * self.par + self.ref[1] * (1 - self.par)
        box = ((cx - W / (2 * ze) - self.ox - dx) * TS, (cy - H / (2 * ze) - self.oy - dy) * TS,
               (cx + W / (2 * ze) - self.ox - dx) * TS, (cy + H / (2 * ze) - self.oy - dy) * TS)
        iw, ih = self.img.size
        bw, bh = min(box[2] - box[0], iw), min(box[3] - box[1], ih)
        bx0 = max(min(box[0], iw - bw), 0); by0 = max(min(box[1], ih - bh), 0)
        out = self.img.resize((W, H), Image.BILINEAR, box=(bx0, by0, bx0 + bw, by0 + bh), reducing_gap=None)
        a = np.asarray(out, np.float32)
        al = a[..., 3:4] / 255.0 * alpha
        base[:] = base * (1 - al) + a[..., :3] * al


def paste_np(base, im, x, y, alpha=1.0):
    """Pega un RGBA (PIL) en base (float HxWx3) con la esquina sup. izq. en (x,y)."""
    x, y = int(round(x)), int(round(y))
    a = np.asarray(im, np.float32)
    h, w = a.shape[:2]
    x0, y0 = max(x, 0), max(y, 0); x1, y1 = min(x + w, W), min(y + h, H)
    if x1 <= x0 or y1 <= y0: return
    sub = a[y0 - y:y1 - y, x0 - x:x1 - x]
    al = sub[..., 3:4] / 255.0 * alpha
    base[y0:y1, x0:x1] = base[y0:y1, x0:x1] * (1 - al) + sub[..., :3] * al


def place_person(base, name, pose, wx, wy, cam, k=1.0, flip=False, depth=1.0, alpha=1.0):
    """Dibuja un personaje con la cadera en (wx,wy) del mundo."""
    sx, sy = cam.p(wx, wy, depth)
    kk = k * cam.z ** depth
    im = draw_person(name, pose, k=kk, flip=flip, ss=(2 if kk < 1.3 else 1.35))
    paste_np(base, im, sx - HX * kk, sy - HY * kk, alpha)
    return sx, sy


def icon_rgba(w, h, fn, ss=3):
    im = Image.new("RGBA", (int(w * ss), int(h * ss)), (0, 0, 0, 0))
    fn(Pen(im, ss))
    return im.resize((int(w), int(h)), Image.LANCZOS)


def put_icon(base, im, cx, cy, scale=1.0, rot=0.0, alpha=1.0):
    if scale != 1.0:
        im = im.resize((max(int(im.width * scale), 2), max(int(im.height * scale), 2)), Image.LANCZOS)
    if rot:
        im = im.rotate(-rot, resample=Image.BICUBIC, expand=True)
    paste_np(base, im, cx - im.width / 2, cy - im.height / 2, alpha)


def text_img(txt, size, color, bold=True, stroke=0, stroke_col=(0, 0, 0)):
    fo = ImageFont.truetype(FONT_BOLD if bold else FONT_MED, size)
    l, t, r, b = fo.getbbox(txt)
    im = Image.new("RGBA", (r - l + 12 + stroke * 2, b - t + 16 + stroke * 2), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((6 + stroke - l, 8 + stroke - t), txt, font=fo, fill=tuple(color) + (255,), stroke_width=stroke, stroke_fill=tuple(stroke_col) + (255,))
    return im


def dust(f, t, seed=1, n=40, tint=(255, 230, 190), alpha=.55, rise=-12):
    rng = np.random.RandomState(seed)
    for i in range(n):
        x0, y0 = rng.rand() * W, rng.rand() * H; z = .4 + rng.rand()
        x = (x0 + math.sin(t * .5 + i) * 20 * z) % W; y = (y0 + t * rise * z) % H
        r = 1.5 + 2.5 * z * rng.rand()
        f.L.ellipse([x - r, y - r, x + r, y + r], fill=sc(tint, alpha * (.4 + .6 * z) * (.6 + .4 * math.sin(t * 2 + i))))
