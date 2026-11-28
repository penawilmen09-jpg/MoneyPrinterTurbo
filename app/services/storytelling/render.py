"""Renderizador de escenas: composición, cámara, animación y exportación de clips."""

from __future__ import annotations

import math
import os
import random
import subprocess
from dataclasses import dataclass, field

import numpy as np
from PIL import Image, ImageChops, ImageDraw

from . import fx
from .gfx import aa_layer, ease, vignette
from .models import Scene, StoryPlan
from .motion import MotionCtx, compute_pose
from .props import draw_prop, prop_anim
from .rig import Anchors, draw_character
from .sets import BG_SCALE, DynCanvas, H, SLOTS, W, get_set, render_background
from .subtitles import Caption, CaptionRenderer, active_caption

ENV_HZ = 50
SHOT_ZOOM = {"wide": 1.0, "medium": 1.32, "close_up": 2.0, "extreme_close": 3.0}
FOCUS_Y = {"wide": 0.55, "medium": 0.60, "close_up": 0.84, "extreme_close": 0.87}
WALK_SPEED = 380.0  # px de mundo por segundo
STRIDE = 150.0  # px de mundo por ciclo de paso
UNIT = 1.7  # px de mundo por unidad de prop (100 u ≈ 170 px)

# Figurantes: variantes de apariencia fijas (también se dibujan con el rig)
_EXTRAS = None


def extras_specs():
    global _EXTRAS
    if _EXTRAS is None:
        from .models import CharacterSpec

        defs = [
            ("e1", "f", "bun", (90, 60, 40), "dress", (218, 92, 130), "light"),
            ("e2", "m", "short", (40, 30, 26), "tshirt", (84, 170, 120), "tan"),
            ("e3", "f", "long", (50, 36, 30), "hoodie", (120, 100, 190), "brown"),
            ("e4", "m", "bald", (60, 50, 40), "shirt", (230, 160, 60), "fair"),
            ("e5", "m", "curly", (30, 24, 20), "tshirt", (70, 140, 210), "dark"),
            ("e6", "f", "ponytail", (150, 90, 50), "tshirt", (230, 90, 80), "light"),
        ]
        _EXTRAS = [
            CharacterSpec(id=i, name="Figurante", gender=g, hair_style=hs, hair_color=hc, outfit=o, top_color=tc,
                          bottom_color=(60, 66, 96), skin=sk, accent_color=(240, 200, 80))
            for i, g, hs, hc, o, tc, sk in defs
        ]
    return _EXTRAS


@dataclass
class Cam:
    z: float
    cx: float
    cy: float
    px: float  # factor de escala de resolución de salida

    def w2s(self, x, y):
        return ((x - self.cx) * self.z + W / 2) * self.px, ((y - self.cy) * self.z + H * 0.44) * self.px

    def ws(self, length):
        return length * self.z * self.px


@dataclass
class SceneJob:
    plan: dict
    scene_index: int
    duration: float  # duración de la escena (hasta el siguiente inicio de narración)
    pre_roll: float
    fps: int
    out_path: str
    size: tuple[int, int]
    speech_start: float = 0.0
    speech_end: float = 0.0
    env: list[float] = field(default_factory=list)
    captions: list[tuple[float, float, list[tuple[str, bool]]]] = field(default_factory=list)
    hook_text: str = ""
    hook_duration: float = 2.8
    disclaimer_text: str = ""
    disclaimer_windows: list[tuple[float, float]] = field(default_factory=list)
    show_subtitles: bool = True
    crf: int = 17
    max_frames: int = 0  # para pruebas rápidas


class SceneRenderer:
    def __init__(self, plan: StoryPlan, scene: Scene, job: SceneJob):
        self.plan, self.scene, self.job = plan, scene, job
        self.out_w, self.out_h = job.size
        self.px = self.out_w / W
        self.set = get_set(scene.location)
        self.info = self.set.info
        self.variant = scene.number % 3
        self.bg, self.fg = render_background(scene.location, self.variant, scene.time_of_day)
        self.captions = [Caption(a, b, [tuple(w) for w in ws]) for a, b, ws in job.captions]
        self.cap_renderer = CaptionRenderer(self.out_w, self.out_h)
        self.vig = vignette(self.out_w, self.out_h, 0.30 if scene.time_of_day == "day" else 0.42)
        self.rng_seed = scene.number * 101
        self.last_anchors: dict = {}
        self._layout()
        self._plan_camera()

    # ------------------------------------------------------------------ layout
    def _layout(self):
        sc = self.scene
        self.cues = []
        slot_x = {}
        for i, cue in enumerate(sc.characters):
            x = SLOTS.get(cue.position, 540)
            slot_x[cue.id] = x
        self.slot_x = slot_x
        for i, cue in enumerate(sc.characters):
            spec = self.plan.character(cue.id)
            if spec is None:
                continue
            behind = False
            floor = self.info.floor_y
            if self.info.has_fg and self.info.counter_top and getattr(cue, "depth", "") == "behind":
                behind = True
                floor = self.info.behind_floor_y
            self.cues.append((i, cue, spec, behind, floor))

        # prop positions (mundo)
        self.prop_pos = {}
        for pc in sc.props:
            x = SLOTS.get(pc.position, 540)
            u = UNIT * pc.scale
            if pc.anchor == "counter" and self.info.counter_top:
                y = self.info.counter_top - 62 * u
            elif pc.anchor == "wall":
                y = 560
            elif pc.anchor == "screen":
                y = 760
            else:
                y = self.info.floor_y - 58 * u
            self.prop_pos[pc.name] = (x, y, u)

    def _char_height(self, spec, behind=False):
        return self.info.char_scale * (0.95 if behind else 1.0) * 1000 * spec.normalized().height

    def _plan_camera(self):
        sc = self.scene
        z0 = SHOT_ZOOM.get(sc.shot, 1.32)
        fx_, fy_ = 540.0, 900.0
        focus = sc.focus or ""
        target = None
        if focus.startswith("char:"):
            cid = focus[5:]
            for _, cue, spec, behind, floor in self.cues:
                if cue.id == cid:
                    hc = self._char_height(spec, behind)
                    target = (self.slot_x[cid], floor - FOCUS_Y.get(sc.shot, 0.6) * hc)
        elif focus.startswith("prop:") and focus[5:] in self.prop_pos:
            x, y, _ = self.prop_pos[focus[5:]]
            target = (x, y)
        if target is None and self.cues:
            xs = [self.slot_x[c[1].id] for c in self.cues]
            hc = max(self._char_height(c[2], c[3]) for c in self.cues)
            floor = self.cues[0][4]
            target = (sum(xs) / len(xs), floor - FOCUS_Y.get(sc.shot, 0.6) * hc)
        if target:
            fx_, fy_ = target
        if sc.shot == "wide":
            fx_, fy_ = 540.0, 844.0
        self.z0, self.focus0 = z0, (fx_, fy_)

    def camera(self, t: float) -> Cam:
        sc = self.scene
        d = max(0.5, self.job.duration)
        u = ease(max(0.0, min(1.0, t / d)))
        z, cx, cy = self.z0, self.focus0[0], self.focus0[1]
        mv = sc.camera_move
        if mv == "push_in":
            z *= 1.0 + 0.16 * u
        elif mv == "pull_out":
            z *= 1.16 - 0.16 * u
        elif mv == "pan_left":
            cx += 60 - 120 * u
        elif mv == "pan_right":
            cx += -60 + 120 * u
        elif mv == "shake":
            k = max(0.0, 1.0 - t / 1.4)
            cx += math.sin(t * 47) * 7 * k
            cy += math.cos(t * 39) * 7 * k
            z *= 1.0 + 0.03 * u
        else:
            z *= 1.0 + 0.012 * math.sin(t * 0.8)
        # deriva sutil de cámara (vida)
        cx += math.sin(t * 0.7 + self.rng_seed) * 3
        cy += math.cos(t * 0.5 + self.rng_seed) * 3
        z = max(1.0, z)
        cx = min(max(cx, W / (2 * z)), W - W / (2 * z))
        lo, hi = H * 0.44 / z, H - H * 0.56 / z
        cy = min(max(cy, lo), hi)
        return Cam(z, cx, cy, self.px)

    # ------------------------------------------------------------ trayectorias
    def _traj(self, cue, t: float):
        """(x, facing, moving, walk_phase) en coordenadas de mundo."""
        tt = max(0.0, t)
        slot = self.slot_x[cue.id]
        facing = self._static_facing(cue, slot)
        moving, phase = False, 0.0
        x = slot
        if cue.enters_from in ("left", "right"):
            sgn = 1 if cue.enters_from == "left" else -1
            start = -190.0 if sgn == 1 else W + 190.0
            dist = abs(slot - start)
            T = dist / WALK_SPEED
            if tt < T:
                x = start + sgn * WALK_SPEED * tt
                facing, moving, phase = sgn, True, WALK_SPEED * tt / STRIDE
        if cue.action == "walk_out":
            T0 = max(0.4, self.job.duration - 1.8)
            if tt > T0:
                sgn = -1 if slot < 540 else 1
                x = slot + sgn * WALK_SPEED * (tt - T0)
                facing, moving, phase = sgn, True, WALK_SPEED * (tt - T0) / STRIDE
        elif cue.action == "walk" and not moving:
            x = slot + 110 * math.sin(0.8 * tt)
            facing = 1 if math.cos(0.8 * tt) >= 0 else -1
            moving, phase = True, tt * 1.25
        elif cue.action == "walk_in" and not cue.enters_from:
            sgn = 1 if slot > 540 else -1
            start = slot - sgn * 420
            T = 420 / WALK_SPEED
            if tt < T:
                x = start + sgn * WALK_SPEED * tt
                facing, moving, phase = sgn, True, WALK_SPEED * tt / STRIDE
        return x, facing, moving, phase

    def _static_facing(self, cue, slot) -> int:
        tgt = None
        if cue.look_at and cue.look_at in self.slot_x:
            tgt = self.slot_x[cue.look_at]
        elif cue.look_at.startswith("prop:") and cue.look_at[5:] in self.prop_pos:
            tgt = self.prop_pos[cue.look_at[5:]][0]
        else:
            others = [x for cid, x in self.slot_x.items() if cid != cue.id]
            if others:
                tgt = sum(others) / len(others)
        if tgt is None or abs(tgt - slot) < 5:
            tgt = 540.0 if abs(slot - 540) > 5 else slot + 1
        return 1 if tgt >= slot else -1

    def speech_level(self, t: float) -> float:
        env = self.job.env
        if not env:
            return 0.7
        idx = int((t - self.job.speech_start) * ENV_HZ)
        if idx < 0 or idx >= len(env):
            return 0.0
        return float(env[idx])

    # --------------------------------------------------------------- fotograma
    def frame(self, t: float) -> Image.Image:
        sc, job = self.scene, self.job
        cam = self.camera(max(0.0, t))
        px = self.px
        # fondo
        x0 = (cam.cx - W / (2 * cam.z)) * BG_SCALE
        y0 = (cam.cy - H * 0.44 / cam.z) * BG_SCALE
        x1 = x0 + W / cam.z * BG_SCALE
        y1 = y0 + H / cam.z * BG_SCALE
        box = (x0, y0, x1, y1)
        frame = self.bg.resize((self.out_w, self.out_h), Image.BILINEAR, box=box)
        d = ImageDraw.Draw(frame, "RGBA")
        self.set.dynamic(DynCanvas(d, cam), max(0.0, t) + sc.number * 7.0)

        # figurantes
        self._draw_extras(frame, cam, t)

        # personajes y props en capas
        draw_list = []  # (orden_y, 'char'|'prop', datos)
        anchors: dict[str, Anchors] = {}
        speaking_ids = self._speaking_ids(t)
        behind_chars, front_chars = [], []
        for i, cue, spec, behind, floor in self.cues:
            (behind_chars if behind else front_chars).append((i, cue, spec, behind, floor))
        for group in (behind_chars,):
            for item in group:
                self._draw_char(frame, cam, item, t, speaking_ids, anchors)
        if self.fg is not None:
            fg = self.fg.resize((self.out_w, self.out_h), Image.BILINEAR, box=box)
            frame.paste(fg, (0, 0), fg)
        # props anclados al mostrador (encima del mostrador)
        for pc in sc.props:
            if pc.anchor == "counter":
                self._draw_prop(frame, cam, pc, t)
        for item in sorted(front_chars, key=lambda it: it[4]):
            self._draw_char(frame, cam, item, t, speaking_ids, anchors)
        for pc in sc.props:
            if pc.anchor != "counter":
                self._draw_prop(frame, cam, pc, t, anchors)
        # props sostenidos
        for i, cue, spec, behind, floor in self.cues:
            if cue.holding and cue.id in anchors:
                hx, hy = anchors[cue.id].hand_front
                size = 64 * UNIT * cam.z * px / 1.7 * 1.0
                self._blit_prop(frame, cue.holding, hx, hy - 20 * cam.z * px, UNIT * 0.62 * cam.z, t, {})

        self.last_anchors = anchors
        # iluminación
        if sc.time_of_day == "night":
            frame = ImageChops.multiply(frame, Image.new("RGB", frame.size, (165, 175, 225)))
        elif sc.time_of_day == "evening":
            frame = ImageChops.multiply(frame, Image.new("RGB", frame.size, (255, 226, 190)))
        frame.paste(self.vig, (0, 0), self.vig)

        # popups
        self._draw_popups(frame, cam, t, anchors)

        # flash de transición de tensión (revelación)
        if sc.label in ("descubrimiento",) and 0 <= t < 0.25:
            frame = fx.flash(frame, t, 0.25)

        # superposiciones de pantalla
        if job.hook_text and 0 <= t <= job.hook_duration:
            fx.hook_title(frame, job.hook_text, t, job.hook_duration, px)
        fx.brand_tag(frame, px)
        for a, b in job.disclaimer_windows:
            if a <= t <= b and job.disclaimer_text:
                fx.disclaimer(frame, job.disclaimer_text, t - a, px)
        if job.show_subtitles:
            cap = active_caption(self.captions, t)
            if cap is not None:
                self.cap_renderer.paste(frame, cap, t)
        return frame

    # ------------------------------------------------------------------ piezas
    def _speaking_ids(self, t: float) -> dict[str, float]:
        ids = {}
        for i, cue, *_ in self.cues:
            if cue.speaking and t >= 0:
                ids[cue.id] = self.speech_level(t)
        for pc in self.scene.popups:
            if pc.type == "speech" and pc.target.startswith("char:") and pc.at <= t <= pc.at + pc.duration:
                cid = pc.target[5:]
                ids[cid] = max(ids.get(cid, 0), 0.55 + 0.35 * math.sin(t * 7.0) ** 2)
        return ids

    def _draw_char(self, frame, cam, item, t, speaking_ids, anchors):
        i, cue, spec, behind, floor = item
        x, facing, moving, phase = self._traj(cue, t)
        # mirada
        look_dir = 0.0
        if cue.look_at in self.slot_x:
            look_dir = 1.0 if self.slot_x[cue.look_at] >= x else -1.0
        elif cue.look_at.startswith("prop:") and cue.look_at[5:] in self.prop_pos:
            look_dir = 1.0 if self.prop_pos[cue.look_at[5:]][0] >= x else -1.0
        pdir = 1.0
        tgt = None
        if cue.look_at in self.slot_x:
            tgt = self.slot_x[cue.look_at]
        elif cue.look_at.startswith("prop:") and cue.look_at[5:] in self.prop_pos:
            tgt = self.prop_pos[cue.look_at[5:]][0]
        if tgt is not None:
            pdir = 1.0 if tgt >= x else -1.0
        else:
            pdir = float(facing)
        speaking = cue.id in speaking_ids
        ctx = MotionCtx(
            action=cue.action, expression=cue.expression, speaking=speaking, facing=facing,
            look_dir=0.0 if cue.look_at == "camera" else look_dir * 0.0,
            speech_level=speaking_ids.get(cue.id, 0.0), seed=self.rng_seed + i * 13 + 1,
            walk_phase=phase, moving=moving, point_dir=pdir,
        )
        pose = compute_pose(max(0.0, t) + i * 0.31, ctx)
        scale_w = self.info.char_scale * (0.95 if behind else 1.0)
        sx, sy = cam.w2s(x, floor)
        s = scale_w * cam.z * cam.px
        # sombra
        if not behind:
            sh = ImageDraw.Draw(frame, "RGBA")
            rx, ry = 150 * s * 1.0, 26 * s
            sh.ellipse([sx - rx, sy - ry * 0.6, sx + rx, sy + ry * 1.3], fill=(0, 0, 0, 60))
        hscale = spec.normalized().height
        box = (
            int(max(0, sx - 430 * s * hscale)), int(max(0, sy - 1060 * s * hscale)),
            int(min(self.out_w, sx + 430 * s * hscale)), int(min(self.out_h, sy + 50 * s)),
        )
        if box[2] - box[0] < 4 or box[3] - box[1] < 4:
            anchors[cue.id] = Anchors()
            return
        layer, an = draw_character(spec, pose, origin=(sx, sy), scale=s, facing=facing, canvas_box=box, ss=2 if s < 1.4 else 1)
        frame.paste(layer, (box[0], box[1]), layer)
        anchors[cue.id] = an

    def _draw_extras(self, frame, cam, t):
        n = self.scene.background_extras
        if n <= 0:
            return
        specs = extras_specs()
        rng = random.Random(self.scene.number * 7)
        for k in range(n):
            spec = specs[(self.scene.number + k) % len(specs)]
            direction = 1 if (k + self.scene.number) % 2 == 0 else -1
            speed = rng.uniform(70, 120)
            start = rng.uniform(0, W + 300)
            x = ((start + direction * speed * (max(0.0, t) + 2.0)) % (W + 300)) - 150
            phase = (start + direction * speed * (max(0.0, t) + 2.0)) / 70.0
            ctx = MotionCtx(action="walk", expression="neutral", speaking=False, facing=direction, look_dir=0.0,
                            speech_level=0.0, seed=k + 3, walk_phase=abs(phase), moving=True)
            pose = compute_pose(t + k, ctx)
            ey = self.info.extras_y + (k % 3) * 14
            sx, sy = cam.w2s(x, ey)
            s = self.info.extras_scale * cam.z * cam.px
            box = (int(max(0, sx - 430 * s)), int(max(0, sy - 1060 * s)), int(min(self.out_w, sx + 430 * s)), int(min(self.out_h, sy + 40 * s)))
            if box[2] - box[0] < 4 or box[3] - box[1] < 4:
                continue
            layer, _ = draw_character(spec, pose, origin=(sx, sy), scale=s, facing=direction, canvas_box=box, ss=2)
            frame.paste(layer, (box[0], box[1]), layer)

    def _blit_prop(self, frame, name, sx, sy, unit_screen, t, extra, rot=0.0):
        size = int(150 * unit_screen * 1.6)
        size = max(8, min(size, 2400))

        def draw(d, ss):
            draw_prop(name, d, size * ss / 2, size * ss / 2, unit_screen * ss, t, extra)

        layer = aa_layer((size, size), draw, ss=2 if size < 900 else 1)
        if rot:
            layer = layer.rotate(rot, resample=Image.BILINEAR)
        frame.paste(layer, (int(sx - size / 2), int(sy - size / 2)), layer)

    def _draw_prop(self, frame, cam, pc, t, anchors=None):
        if pc.anchor.startswith("hand:"):
            cid = pc.anchor[5:]
            if not anchors or cid not in anchors:
                return
            hx, hy = anchors[cid].hand_front
            self._blit_prop(frame, pc.name, hx, hy - 18 * cam.z * cam.px, UNIT * 0.62 * pc.scale * cam.z * cam.px / cam.px, t, {})
            return
        x, y, u = self.prop_pos[pc.name]
        dx, dy, sk, rot = prop_anim(pc.animation, max(0.0, t))
        sx, sy = cam.w2s(x + dx * u, y + dy * u)
        extra = {"alert": self.scene.label in ("tension", "descubrimiento")}
        self._blit_prop(frame, pc.name, sx, sy, u * sk * cam.z * cam.px, t, extra, rot=rot)

    def _draw_popups(self, frame, cam, t, anchors):
        px = self.px
        for pc in self.scene.popups:
            tl = t - pc.at
            if tl < 0 or tl > pc.duration:
                continue
            center = (self.out_w / 2, 560 * px)
            kind = pc.target.split(":")[0] if pc.target else ""
            tid = pc.target.split(":", 1)[1] if ":" in pc.target else ""
            if kind == "char" and tid in anchors:
                an = anchors[tid]
                center = (an.top[0], an.top[1] - 30 * px)
                mouth = an.mouth
            elif kind == "prop" and tid in self.prop_pos:
                x, y, u = self.prop_pos[tid]
                center = cam.w2s(x, y)
                mouth = center
            else:
                mouth = center
            if pc.type == "speech":
                side = 1 if mouth[0] < self.out_w / 2 else -1
                fx.speech_bubble(frame, mouth, pc.text, tl, px, side=side)
            elif pc.type == "counter":
                fx.popup(frame, (center[0], center[1] - 120 * px), pc.text, pc.style, tl, pc.duration, px, counter=True)
            elif pc.type == "highlight":
                r = 150 * cam.z * px * (0.6 if kind == "prop" else 0.9)
                fx.highlight_ring(frame, center if kind != "char" else anchors[tid].head, r, tl, pc.duration, pc.style)
            elif pc.type == "arrow":
                fx.arrow(frame, (center[0], center[1] - 40 * px), tl, pc.duration, pc.style, px)
            else:
                fx.popup(frame, (center[0], center[1] - 110 * px), pc.text, pc.style, tl, pc.duration, px)


# --------------------------------------------------------------------------
# Exportación
# --------------------------------------------------------------------------
def render_scene_clip(job: SceneJob) -> dict:
    """Renderiza una escena a un MP4 (sin audio).  Se ejecuta en un proceso aparte."""
    plan = StoryPlan.from_dict(job.plan)
    scene = plan.scenes[job.scene_index]
    renderer = SceneRenderer(plan, scene, job)
    w, h = job.size
    n_frames = int(round((job.duration + job.pre_roll) * job.fps))
    if job.max_frames:
        n_frames = min(n_frames, job.max_frames)
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}",
        "-r", str(job.fps), "-i", "-", "-an", "-c:v", "libx264", "-preset", "veryfast",
        "-crf", str(job.crf), "-pix_fmt", "yuv420p", "-movflags", "+faststart", job.out_path,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    try:
        for n in range(n_frames):
            t = n / job.fps - job.pre_roll
            img = renderer.frame(t)
            proc.stdin.write(img.convert("RGB").tobytes())
    finally:
        proc.stdin.close()
        rc = proc.wait()
    if rc != 0:
        raise RuntimeError(f"ffmpeg falló al renderizar la escena {scene.number} (código {rc})")
    return {"scene": scene.number, "frames": n_frames, "path": job.out_path}
