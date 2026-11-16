"""Motor de animación: evalúa el estado de una escena en el tiempo t y compone el fotograma."""

from __future__ import annotations

from dataclasses import dataclass, field
import math

import numpy as np
from PIL import Image, ImageChops, ImageDraw

from . import backgrounds as bgm
from .backgrounds import H, W, font
from .characters import (EXPRESSIONS, POSE_HANDS, SWEATY, blend_dict, head_anchor,
                         render_character, resolve_spec)
from .easing import clamp, ease_in_out, ease_out, ease_out_back, keyframes, lerp
from .script import Scene

FPS = 30
BLEND_EXPR = 0.28
BLEND_POSE = 0.38


# --------------------------------------------------------------------------- actores
@dataclass
class Actor:
    cid: str
    spec: dict
    place: object                      # Placement
    expr_ev: list = field(default_factory=list)    # [(t, nombre)]
    pose_ev: list = field(default_factory=list)
    moves: list = field(default_factory=list)      # [(t0, t1, (x0,y0), (x1,y1))]
    looks: list = field(default_factory=list)      # [(t, (lx,ly))]
    emotes: list = field(default_factory=list)     # [(t0, t1, tipo)]
    phase: float = 0.0


def _last(events, t, default):
    cur, prev, tc = default, default, -1e9
    for et, v in events:
        if et <= t:
            prev, cur, tc = cur, v, et
    return prev, cur, tc


class SceneRenderer:
    """Renderiza fotogramas de una escena. Es determinista y apto para multiproceso."""

    def __init__(self, scene: Scene, characters: dict, duration: float, speech_env: np.ndarray,
                 speech_start: float, words: list, fps: int = FPS):
        self.scene, self.duration, self.fps = scene, duration, fps
        self.env, self.speech_start, self.words = speech_env, speech_start, words
        self.specs = {cid: resolve_spec(d) for cid, d in characters.items()}
        self.backdrop = bgm.build(scene.setting)
        self.actors: list[Actor] = []
        self.speaker_ev = [(0.0, scene.speaker)] if scene.speaker else []
        self.labels: list[dict] = []
        self.shakes: list[tuple[float, float]] = []
        self._plan()
        self._vignette = _vignette()

    # ---- planificación de eventos
    def _plan(self):
        sc, D = self.scene, self.duration
        by_id = {}
        for i, p in enumerate(sc.placements):
            a = Actor(p.id, self.specs[p.id], p, phase=i * 1.7)
            a.expr_ev = [(0.0, p.expression)]
            a.pose_ev = [(0.0, p.pose)]
            by_id.setdefault(p.id, a)
            self.actors.append(a)
        for ev in sorted(sc.events, key=lambda e: e["at"]):
            t = ev["at"] * D
            et = ev["type"]
            a = by_id.get(ev.get("who"))
            if et == "expression" and a:
                a.expr_ev.append((t, ev["value"]))
            elif et == "pose" and a:
                a.pose_ev.append((t, ev["value"]))
            elif et == "move" and a:
                dur = float(ev.get("dur", 0.25)) * D
                x1, y1 = ev.get("to", [a.place.x, a.place.y])
                x0, y0 = (a.moves[-1][3] if a.moves else (a.place.x, a.place.y))
                a.moves.append((t, t + max(dur, 0.2), (x0, y0), (x1, y1), bool(ev.get("walk", True))))
            elif et == "look" and a:
                to = ev.get("to", [0, 0])
                a.looks.append((t, (float(to[0]), float(to[1]))))
            elif et == "emote" and a:
                a.emotes.append((t, t + float(ev.get("dur", 0.25)) * D, ev["value"]))
            elif et == "label":
                self.labels.append(dict(ev, t0=t, t1=t + float(ev.get("dur", 0.2)) * D))
            elif et == "shake":
                self.shakes.append((t, float(ev.get("amount", 18))))
            elif et == "speaker":
                self.speaker_ev.append((t, ev["who"]))

    # ---- estado de un actor
    def _position(self, a: Actor, t: float):
        x, y, walking = a.place.x, a.place.y, False
        for m in a.moves:
            t0, t1, (x0, y0), (x1, y1), walk = m
            if t >= t1:
                x, y = x1, y1
            elif t >= t0:
                u = ease_in_out((t - t0) / (t1 - t0))
                x, y, walking = lerp(x0, x1, u), lerp(y0, y1, u), walk
                break
        return x, y, walking

    def _mouth(self, t_audio: float, speaking: bool) -> float:
        if not speaking:
            return 0.0
        if self.env is not None and len(self.env) and self.env.max() > 0.01:
            i = int(t_audio * self.fps)
            return float(self.env[min(max(i, 0), len(self.env) - 1)]) * 0.95
        # sin audio: aleteo de boca guiado por el tiempo de las palabras
        for _, s, e in self.words:
            if s <= t_audio <= e:
                return 0.25 + 0.55 * abs(math.sin((t_audio - s) * 22))
        return 0.0

    def _actor_state(self, a: Actor, t: float, speaker: str):
        p0, p1, tc = _last(a.expr_ev, t, "neutral")
        u = ease_in_out((t - tc) / BLEND_EXPR) if tc > -1e8 else 1.0
        expr = blend_dict(EXPRESSIONS[p0], EXPRESSIONS[p1], u)
        pa, pb, tp = _last(a.pose_ev, t, "stand")
        up = ease_in_out((t - tp) / BLEND_POSE) if tp > -1e8 else 1.0
        x, y, walking = self._position(a, t)
        sit = a.place.pose == "sit"
        speaking = (a.cid == speaker)
        ta = t - self.speech_start
        mouth = self._mouth(ta, speaking and ta >= 0)
        # manos
        hr = POSE_HANDS[pa], POSE_HANDS[pb]
        hands = [tuple(lerp(hr[0][side][k], hr[1][side][k], up) for k in (0, 1)) for side in (0, 1)]
        walk = None
        if walking or pb == "walk":
            walk = t * 9.5 + a.phase
            sw = math.sin(walk)
            hands = [(hands[0][0], hands[0][1] + 22 * sw), (hands[1][0], hands[1][1] - 22 * sw)]
        elif speaking and mouth > 0.02 and pb in ("stand", "present", "sit", "point"):
            osc = math.sin(t * 5.2 + a.phase)
            hands = [(hands[0][0] + 10 * osc, hands[0][1] - 20 - 16 * abs(osc)),
                     (hands[1][0] - 8 * osc, hands[1][1] - 6 + 6 * osc)]
        if pb == "wipe" and up > 0.9:
            hands[0] = (hands[0][0] + 26 * math.sin(t * 9), hands[0][1] + 4 * math.cos(t * 9))
        # parpadeo / mirada
        bt = (t + a.phase * 0.7) % 3.4
        blink = max(0.0, 1 - abs(bt - 3.3) / 0.07) if bt > 3.23 else 0.0
        look = (0.0, 0.0)
        for lt, lv in a.looks:
            if lt <= t:
                look = lv
        bob = math.sin(t * 2.1 + a.phase) * 3.0 + (abs(math.sin(walk)) * -10 if walk is not None else 0)
        tilt = math.sin(t * 1.3 + a.phase) * 1.6 + (math.sin(t * 6) * 2.2 if mouth > 0.2 else 0)
        loose = 1.0 if (pb == "loosen_tie" or any(e[1] == "loosen_tie" for e in a.pose_ev if e[0] <= t)) else 0.0
        return dict(x=x, y=y, state=dict(
            hands=hands, expr=expr, mouth=mouth, blink=blink, look=look, tilt=tilt, bob=bob,
            walk=walk, sit=sit, tie_loose=loose, flip=a.place.flip), sweat=(p1 in SWEATY and u > 0.5))

    # ---- cámara
    def _camera(self, t: float):
        D = self.duration
        frames = self.scene.camera or [{"at": 0.0, "zoom": 1.0, "cx": 0.5, "cy": 0.5},
                                       {"at": 1.0, "zoom": 1.07, "cx": 0.5, "cy": 0.5}]
        c = keyframes(frames, clamp(t / D), ("zoom", "cx", "cy", "roll"))
        zoom, cx, cy, roll = c.get("zoom", 1.0), c.get("cx", 0.5), c.get("cy", 0.5), c.get("roll", 0.0)
        # cámara en mano: ruido suave
        sx = math.sin(t * 1.7) * 3 + math.sin(t * 3.1 + 1) * 1.5
        sy = math.sin(t * 1.3 + 2) * 3 + math.sin(t * 2.7) * 1.5
        for st, amt in self.shakes:
            if 0 <= t - st < 0.6:
                k = (1 - (t - st) / 0.6) ** 2
                sx += math.sin((t - st) * 70) * amt * k
                sy += math.cos((t - st) * 83) * amt * k
        return zoom, cx, cy, roll, sx, sy

    @staticmethod
    def _xform(layer: Image.Image, zoom, cx, cy, roll, sx, sy, depth: float, resample):
        z = 1 + (zoom - 1) * depth
        pcx = W / 2 + (cx - 0.5) * W * min(depth, 1.0) * 1.0
        pcy = H / 2 + (cy - 0.5) * H * min(depth, 1.0) * 1.0
        # clamp para no mostrar bordes vacíos
        half_w, half_h = W / (2 * z), H / (2 * z)
        pcx = min(max(pcx, half_w), W - half_w)
        pcy = min(max(pcy, half_h), H - half_h)
        a = math.radians(roll)
        ca, sa = math.cos(a) / z, math.sin(a) / z
        # mapea píxel de salida (x,y) -> entrada
        ox, oy = W / 2 + sx * depth, H / 2 + sy * depth
        c = pcx - ca * ox + sa * oy
        f = pcy - sa * ox - ca * oy
        return layer.transform((W, H), Image.AFFINE, (ca, -sa, c, sa, ca, f), resample)

    # ---- composición
    def frame(self, idx: int) -> Image.Image:
        t = idx / self.fps
        D = self.duration
        speaker = _last(self.speaker_ev, t, "")[1]
        states = [(a, self._actor_state(a, t, speaker)) for a in self.actors]
        world = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        bd = self.backdrop

        def draw_actor(a, st, target):
            p = a.place
            if not p.visible:
                return
            sprite, ox, oy = render_character(a.spec, st["state"], p.scale)
            px, py = st["x"] * W, st["y"] * H
            target.alpha_composite(sprite, (int(px - ox), int(py - oy)), ) if (
                0 <= px - ox and 0 <= py - oy and px - ox + sprite.width <= W
                and py - oy + sprite.height <= H) else _paste_clipped(target, sprite, int(px - ox), int(py - oy))
            self._emotes(target, a, st, t, px, py)

        small = [(a, s) for a, s in states if a.place.scale <= 0.62 and bd.window]
        big = [(a, s) for a, s in states if not (a.place.scale <= 0.62 and bd.window)]
        if small:
            win = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            for a, s in small:
                draw_actor(a, s, win)
            x0, y0, x1, y1 = bd.window
            mask = Image.new("L", (W, H), 0)
            ImageDraw.Draw(mask).rectangle([x0, y0, x1, y1], fill=255)
            win.putalpha(ImageChops.multiply(win.getchannel("A"), mask))
            world.alpha_composite(win)
        if bd.mid is not None:
            world.alpha_composite(bd.mid)
        for a, s in sorted(big, key=lambda it: it[1]["y"]):
            draw_actor(a, s, world)
        if bd.fg is not None:
            world.alpha_composite(bd.fg)
        if self.scene.setting == "strategy":
            _draw_strategy(world, self.scene, t / D, t)

        zoom, cx, cy, roll, sx, sy = self._camera(t)
        base = self._xform(bd.bg, zoom, cx, cy, roll, sx, sy, 0.62, Image.BILINEAR).convert("RGBA")
        base.alpha_composite(self._xform(world, zoom, cx, cy, roll, sx, sy, 1.0, Image.BILINEAR))
        out = base.convert("RGB")
        # etiquetas en pantalla (no sufren la cámara)
        out = self._labels(out, t)
        out = ImageChops.multiply(out, self._vignette)
        return out

    # ---- emotes y etiquetas
    def _emotes(self, target, a: Actor, st, t, px, py):
        hx, hy = head_anchor(a.place.scale, st["state"]["sit"])
        hx += px
        hy += py + st["state"]["bob"]
        active = [k for t0, t1, k in a.emotes if t0 <= t <= t1]
        t_e = [(t - t0, t1 - t0, k) for t0, t1, k in a.emotes if t0 <= t <= t1]
        if st["sweat"] and "sweat" not in active:
            t_e.append((t, 99.0, "sweat"))
        for lt, total, kind in t_e:
            spr = emote_sprite(kind, lt, total, 1.0 * max(a.place.scale, 0.8))
            if spr is None:
                continue
            side = -1 if a.place.flip else 1
            ex = hx + side * (95 * a.place.scale) - spr.width / 2
            ey = hy - 120 * a.place.scale - spr.height / 2
            _paste_clipped(target, spr, int(ex), int(ey))

    def _labels(self, img: Image.Image, t: float) -> Image.Image:
        if not self.labels:
            return img
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        for lb in self.labels:
            if not (lb["t0"] <= t <= lb["t1"]):
                continue
            u_in = ease_out_back((t - lb["t0"]) / 0.35)
            u_out = clamp((lb["t1"] - t) / 0.25)
            size = int(lb.get("size", 78) * (0.4 + 0.6 * u_in))
            x, y = lb.get("pos", [0.5, 0.22])
            col = lb.get("color", "#FFD23F").lstrip("#")
            rgb = tuple(int(col[i:i + 2], 16) for i in (0, 2, 4))
            f = font(max(8, size))
            alpha = int(255 * u_out)
            txt = lb["text"]
            tw = d.textlength(txt, font=f)
            pad = 26
            box = [x * W - tw / 2 - pad, y * H - size * 0.75, x * W + tw / 2 + pad, y * H + size * 0.75]
            d.rounded_rectangle(box, radius=28, fill=(20, 16, 40, int(200 * u_out)),
                                outline=rgb + (alpha,), width=5)
            d.text((x * W, y * H), txt, font=f, fill=rgb + (alpha,), anchor="mm")
        out = img.convert("RGBA")
        out.alpha_composite(layer)
        return out.convert("RGB")


def _paste_clipped(target: Image.Image, spr: Image.Image, x: int, y: int):
    x0, y0 = max(0, -x), max(0, -y)
    x1, y1 = min(spr.width, target.width - x), min(spr.height, target.height - y)
    if x1 <= x0 or y1 <= y0:
        return
    target.alpha_composite(spr.crop((x0, y0, x1, y1)), (x + x0, y + y0))


_VIG = None


def _vignette() -> Image.Image:
    global _VIG
    if _VIG is None:
        yy, xx = np.mgrid[0:H:4, 0:W:4].astype(np.float32)
        d = np.sqrt(((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H / 2) / (H * 0.75)) ** 2)
        v = np.clip(1.08 - 0.42 * d ** 2.2, 0.62, 1.0)
        img = Image.fromarray((v * 255).astype(np.uint8), "L").resize((W, H), Image.BILINEAR)
        _VIG = Image.merge("RGB", (img, img, img))
    return _VIG


# --------------------------------------------------------------------------- emotes
def emote_sprite(kind: str, lt: float, total: float, s: float = 1.0):
    S = 2
    size = int(150 * s)
    img = Image.new("RGBA", (size * S, size * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = size * S / 2
    pop = ease_out_back(lt / 0.25) if total < 90 else 1.0
    fade = clamp((total - lt) / 0.2) if total < 90 else 1.0
    a = int(255 * fade)
    if pop <= 0.02 or a <= 0:
        return None
    k = size * S / 150 * pop
    if kind == "sweat":
        for i, (ox, ph) in enumerate(((-30, 0.0), (22, 0.5), (45, 0.25))):
            cyc = (lt * 0.9 + ph) % 1.0
            y = (10 + cyc * 80) * k
            x = c + ox * k
            r = 11 * k * (1 - 0.4 * cyc)
            al = int(a * (1 - cyc ** 3))
            d.polygon([(x, y - 22 * k * (1 - 0.3 * cyc)), (x - r, y + 2 * k), (x + r, y + 2 * k)],
                      fill=(110, 190, 255, al))
            d.ellipse([x - r, y - r * 0.4, x + r, y + r * 1.7], fill=(110, 190, 255, al),
                      outline=(40, 110, 200, al), width=max(1, int(2 * k)))
    elif kind in ("question", "exclaim"):
        ch, col = ("?", (80, 150, 255, a)) if kind == "question" else ("!", (255, 70, 70, a))
        f = font(int(120 * k))
        bob = math.sin(lt * 9) * 5 * k
        d.text((c, c + bob), ch, font=f, fill=col, anchor="mm", stroke_width=int(6 * k),
               stroke_fill=(255, 255, 255, a))
    elif kind == "idea":
        d.ellipse([c - 36 * k, c - 50 * k, c + 36 * k, c + 22 * k], fill=(255, 226, 80, a),
                  outline=(200, 150, 20, a), width=int(4 * k))
        d.rectangle([c - 16 * k, c + 20 * k, c + 16 * k, c + 40 * k], fill=(150, 150, 160, a))
        for ang in range(-60, 61, 30):
            r = math.radians(ang - 90)
            d.line([(c + math.cos(r) * 52 * k, c - 14 * k + math.sin(r) * 52 * k),
                    (c + math.cos(r) * 70 * k, c - 14 * k + math.sin(r) * 70 * k)],
                   fill=(255, 210, 60, a), width=int(5 * k))
    elif kind == "anger":
        col = (230, 40, 50, a)
        for ang in (0, 90):
            r = math.radians(ang)
            for sgn in (-1, 1):
                pass
        d.line([(c - 40 * k, c - 10 * k), (c - 10 * k, c - 10 * k), (c - 10 * k, c - 40 * k)], fill=col, width=int(9 * k))
        d.line([(c + 40 * k, c - 10 * k), (c + 10 * k, c - 10 * k), (c + 10 * k, c - 40 * k)], fill=col, width=int(9 * k))
        d.line([(c - 40 * k, c + 10 * k), (c - 10 * k, c + 10 * k), (c - 10 * k, c + 40 * k)], fill=col, width=int(9 * k))
        d.line([(c + 40 * k, c + 10 * k), (c + 10 * k, c + 10 * k), (c + 10 * k, c + 40 * k)], fill=col, width=int(9 * k))
    elif kind == "heart":
        col = (255, 80, 130, a)
        d.ellipse([c - 44 * k, c - 40 * k, c, c + 4 * k], fill=col)
        d.ellipse([c, c - 40 * k, c + 44 * k, c + 4 * k], fill=col)
        d.polygon([(c - 42 * k, c - 8 * k), (c + 42 * k, c - 8 * k), (c, c + 46 * k)], fill=col)
    elif kind == "dots":
        d.rounded_rectangle([c - 60 * k, c - 30 * k, c + 60 * k, c + 30 * k], radius=int(26 * k),
                            fill=(255, 255, 255, a), outline=(60, 60, 80, a), width=int(4 * k))
        for i in range(3):
            on = int(lt * 3) % 3 >= i
            r = 8 * k
            d.ellipse([c - 32 * k + i * 32 * k - r, c - r, c - 32 * k + i * 32 * k + r, c + r],
                      fill=(60, 60, 80, a if on else a // 4))
    elif kind == "clock":
        d.ellipse([c - 44 * k, c - 44 * k, c + 44 * k, c + 44 * k], fill=(255, 255, 255, a),
                  outline=(60, 60, 80, a), width=int(5 * k))
        ang = lt * 3
        d.line([(c, c), (c + math.sin(ang) * 30 * k, c - math.cos(ang) * 30 * k)], fill=(60, 60, 80, a), width=int(5 * k))
        d.line([(c, c), (c + math.sin(ang / 12) * 20 * k, c - math.cos(ang / 12) * 20 * k)], fill=(200, 40, 40, a), width=int(5 * k))
    else:
        return None
    return img.resize((size, size), Image.LANCZOS)


# --------------------------------------------------------------------------- infografía
def _icon(d: ImageDraw.ImageDraw, kind: str, cx, cy, r, col):
    if kind in ("person", "boss"):
        d.ellipse([cx - r * 0.38, cy - r * 0.9, cx + r * 0.38, cy - r * 0.16], fill=col)
        d.pieslice([cx - r * 0.78, cy - r * 0.05, cx + r * 0.78, cy + r * 1.6], 180, 360, fill=col)
        if kind == "boss":
            d.polygon([(cx - r * 0.5, cy - r * 1.0), (cx - r * 0.3, cy - r * 1.45), (cx, cy - r * 1.1),
                       (cx + r * 0.3, cy - r * 1.45), (cx + r * 0.5, cy - r * 1.0)], fill=(255, 210, 60, 255))
    elif kind == "lock":
        d.rounded_rectangle([cx - r * 0.7, cy - r * 0.1, cx + r * 0.7, cy + r * 0.9], radius=int(r * 0.15), fill=col)
        d.arc([cx - r * 0.45, cy - r * 0.95, cx + r * 0.45, cy + r * 0.15], 180, 360, fill=col, width=max(3, int(r * 0.18)))
    elif kind == "tag":
        d.polygon([(cx - r * 0.9, cy), (cx - r * 0.2, cy - r * 0.7), (cx + r * 0.9, cy - r * 0.7),
                   (cx + r * 0.9, cy + r * 0.7), (cx - r * 0.2, cy + r * 0.7)], fill=col)
        d.ellipse([cx - r * 0.45, cy - r * 0.12, cx - r * 0.2, cy + r * 0.13], fill=(30, 20, 60, 255))
    elif kind == "check":
        d.line([(cx - r * 0.7, cy), (cx - r * 0.15, cy + r * 0.55), (cx + r * 0.8, cy - r * 0.6)], fill=col, width=max(4, int(r * 0.3)))
    elif kind == "cross":
        d.line([(cx - r * 0.6, cy - r * 0.6), (cx + r * 0.6, cy + r * 0.6)], fill=col, width=max(4, int(r * 0.3)))
        d.line([(cx - r * 0.6, cy + r * 0.6), (cx + r * 0.6, cy - r * 0.6)], fill=col, width=max(4, int(r * 0.3)))
    elif kind == "coin":
        d.ellipse([cx - r * 0.8, cy - r * 0.8, cx + r * 0.8, cy + r * 0.8], fill=(255, 205, 60, 255), outline=(190, 140, 20, 255), width=4)
        d.text((cx, cy), "$", font=font(int(r * 1.1)), fill=(150, 100, 10, 255), anchor="mm")


def _hex3(c: str):
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def _draw_strategy(world: Image.Image, scene: Scene, u: float, t: float):
    D = 1.0
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    total = scene.items and max((it.get("at", 0) for it in scene.items), default=0)
    nodes = {}
    for it in scene.items:
        if it.get("type") == "node":
            nodes[it["id"]] = it
    # título
    if scene.title:
        k = ease_out_back(u / 0.08)
        size = int(86 * (0.5 + 0.5 * k)) + int(3 * math.sin(t * 3))
        lines = scene.title.split("\n")
        for i, ln in enumerate(lines):
            col = (255, 220, 70, 255) if i == 0 else (255, 255, 255, 255)
            d.text((W / 2, 210 + i * 110), ln, font=font(size), fill=col, anchor="mm",
                   stroke_width=7, stroke_fill=(30, 10, 80, 255))
    for it in scene.items:
        at = it.get("at", 0.0)
        if u < at:
            continue
        lt = (u - at)
        k = clamp(ease_out_back(lt / 0.06))
        typ = it.get("type")
        if typ == "node":
            x, y = it["x"] * W, it["y"] * H
            w, h = it.get("w", 0.52) * W * k, it.get("h", 0.105) * H * k
            col = _hex3(it.get("color", "#6C5CE7"))
            alpha = int(255 * it.get("opacity", 1.0))
            d.rounded_rectangle([x - w / 2 + 8, y - h / 2 + 10, x + w / 2 + 8, y + h / 2 + 10], radius=34, fill=(0, 0, 0, 90))
            d.rounded_rectangle([x - w / 2, y - h / 2, x + w / 2, y + h / 2], radius=34,
                                fill=col + (alpha,), outline=(255, 255, 255, alpha), width=5)
            if k > 0.7:
                _icon(d, it.get("icon", "person"), x, y - h * 0.2, h * 0.27, (255, 255, 255, alpha))
                d.text((x, y + h * 0.34), it.get("label", ""), font=font(int(it.get("size", 40))),
                       fill=(255, 255, 255, alpha), anchor="mm")
        elif typ == "link":
            a_, b_ = nodes.get(it["from"]), nodes.get(it["to"])
            if not (a_ and b_):
                continue
            p = ease_out(lt / 0.07)
            x0, y0 = a_["x"] * W, a_["y"] * H
            x1, y1 = b_["x"] * W, b_["y"] * H
            dx, dy = x1 - x0, y1 - y0
            ln = math.hypot(dx, dy) + 1e-6
            ux, uy = dx / ln, dy / ln
            gap = it.get("gap", it.get("gap_default", 0)) or (nodes[it["from"]].get("h", 0.105) * H / 2 + 6)
            sx_, sy_ = x0 + ux * gap, y0 + uy * gap
            ex_, ey_ = x1 - ux * gap, y1 - uy * gap
            cx_, cy_ = lerp(sx_, ex_, p), lerp(sy_, ey_, p)
            col = _hex3(it.get("color", "#FFD23F")) + (255,)
            dash = it.get("dashed", False)
            if dash:
                n = 12
                for i in range(n):
                    if i % 2 == 0 and i / n <= p:
                        d.line([(lerp(sx_, ex_, i / n), lerp(sy_, ey_, i / n)),
                                (lerp(sx_, ex_, (i + 1) / n), lerp(sy_, ey_, (i + 1) / n))], fill=col, width=9)
            else:
                d.line([(sx_, sy_), (cx_, cy_)], fill=col, width=10)
            if p > 0.95:
                d.polygon([(ex_, ey_), (ex_ - ux * 34 - uy * 20, ey_ - uy * 34 + ux * 20),
                           (ex_ - ux * 34 + uy * 20, ey_ - uy * 34 - ux * 20)], fill=col)
            if it.get("label") and p > 0.6:
                mx, my = (sx_ + ex_) / 2, (sy_ + ey_) / 2 - it.get("lift", 0)
                f = font(it.get("size", 34))
                tw = d.textlength(it["label"], font=f)
                d.rounded_rectangle([mx - tw / 2 - 18, my - 30, mx + tw / 2 + 18, my + 30], radius=22,
                                    fill=(25, 15, 60, 235), outline=col, width=3)
                d.text((mx, my), it["label"], font=f, fill=(255, 255, 255, 255), anchor="mm")
        elif typ == "badge":
            x, y = it["x"] * W, it["y"] * H
            f = font(int(it.get("size", 44) * (0.6 + 0.4 * k)))
            tw = d.textlength(it["label"], font=f)
            col = _hex3(it.get("color", "#FF4757"))
            rot_off = math.sin(t * 4) * 3
            d.rounded_rectangle([x - tw / 2 - 30, y - 44 + rot_off, x + tw / 2 + 30, y + 44 + rot_off],
                                radius=44, fill=col + (255,), outline=(255, 255, 255, 255), width=5)
            d.text((x, y + rot_off), it["label"], font=f, fill=(255, 255, 255, 255), anchor="mm")
        elif typ == "icon":
            x, y = it["x"] * W, it["y"] * H
            _icon(d, it.get("icon", "check"), x, y, it.get("r", 60) * k, _hex3(it.get("color", "#FFFFFF")) + (255,))
        elif typ == "text":
            x, y = it["x"] * W, it["y"] * H
            d.text((x, y), it["text"], font=font(int(it.get("size", 44) * (0.7 + 0.3 * k))),
                   fill=_hex3(it.get("color", "#FFFFFF")) + (int(255 * min(1, k * 1.5)),), anchor="mm",
                   stroke_width=4, stroke_fill=(20, 10, 60, 255))
    world.alpha_composite(layer)
