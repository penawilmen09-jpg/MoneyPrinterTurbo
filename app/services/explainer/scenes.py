"""Scene renderers: turn a Scene + local time into one RGB frame (no captions)."""

from __future__ import annotations

import math
from dataclasses import dataclass

from PIL import Image, ImageDraw

from . import gfx as G
from . import models3d as M
from . import three as T
from .gfx import (AMBER, CORAL, CYAN, H, MINT, MUTED, TEXT, VIOLET, VIZ_BOTTOM, VIZ_TOP, W,
                  clamp, ease_in_out, ease_out, ease_out_back, font, lerp, seg)
from .models import Scene

VIEW_H = 960          # height of the 3D viewport rendered at VIZ_TOP
ACCENT_BY_ROLE = {"hook": AMBER, "problem": CORAL, "step": CYAN, "discovery": MINT, "cta": AMBER}


@dataclass
class Ctx:
    index: int            # 1-based scene number
    total: int
    duration: float
    fast: bool = False    # lower supersampling for previews/tests


def _ss(ctx: Ctx) -> int:
    return 1 if ctx.fast else 2


def _to_abs(pt):  # viewport -> frame coordinates
    return (pt[0], pt[1] + VIZ_TOP)


def _project(fr: M.ModelFrame, name: str):
    p = fr.cam.project([fr.anchors[name]])[0]
    return _to_abs((p[0], p[1]))


def _paste3d(frame: Image.Image, fr: M.ModelFrame, ctx: Ctx, opacity=1.0):
    im = T.render(fr.meshes, fr.cam, (W, VIEW_H), ss=_ss(ctx))
    G.alpha_paste(frame, im, (0, VIZ_TOP), opacity)


def _flow_particles(frame, fr: M.ModelFrame, pts3d, t, color_fn, n=16, speed=0.3, size=10, seed=1, reverse=False):
    scr = fr.cam.project(pts3d)
    path = [_to_abs((p[0], p[1])) for p in scr]
    if reverse:
        path = path[::-1]
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    G.dust_particles(layer, path, t, n, color_fn if isinstance(color_fn, tuple) else (255, 255, 255), speed, size, seed)
    frame.paste(layer, (0, 0), layer)


# ---------------------------------------------------------------------------
# Mechanism: piston engine
# ---------------------------------------------------------------------------
_STROKES = [("ADMISIÓN", 0, 180), ("COMPRESIÓN", 180, 360), ("COMBUSTIÓN", 360, 540), ("ESCAPE", 540, 720)]
_BRAKE_STROKES = [("ADMISIÓN", 0, 180), ("COMPRESIÓN", 180, 346), ("LIBERACIÓN", 346, 372), ("SIN EMPUJE", 372, 540), ("ESCAPE", 540, 720)]


def _engine_theta(stage: str, t: float, dur: float) -> float:
    a, b = M.stage_range(stage)
    if stage in ("full_cycle", "brake_full"):
        # one slow full cycle over the scene (two for long scenes)
        cycles = 1 if dur < 11 else 2
        return (a + (b - a) * cycles * clamp((t - 0.3) / max(dur - 0.9, 1.0))) % 720
    period = clamp((b - a) / 180 * 4.0, 3.0, 8.0)
    u = ((t - 0.3) / period) % 1.0 if t > 0.3 else 0.0
    u = clamp((u - 0.06) / 0.88)
    return a + (b - a) * u


def _stroke_tracker(frame, theta, brake, t):
    items = _BRAKE_STROKES if brake else _STROKES
    d = ImageDraw.Draw(frame, "RGBA")
    fnt = font("bold", 27)
    gap = 10
    widths = [G.text_size(n, fnt)[0] + 34 for n, _, _ in items]
    total = sum(widths) + gap * (len(items) - 1)
    x = (W - total) / 2
    y = VIZ_BOTTOM - 70
    for (name, a, b), w in zip(items, widths):
        active = a <= theta % 720 < b
        col = CORAL if (name in ("LIBERACIÓN",)) else CYAN
        fill = (*col, 255) if active else (14, 24, 52, 215)
        d.rounded_rectangle([x, y, x + w, y + 58], radius=29, fill=fill, outline=(*col, 255 if active else 120), width=3)
        d.text((x + w / 2, y + 29), name, font=fnt, fill=(8, 14, 34, 255) if active else (*MUTED, 255), anchor="mm")
        x += w + gap


def _pressure_gauge(frame, p, color, release):
    d = ImageDraw.Draw(frame, "RGBA")
    x0, y0, x1, y1 = 70, 700, 124, 1120
    d.rounded_rectangle([x0, y0, x1, y1], radius=24, fill=(8, 14, 34, 200), outline=(*MUTED, 200), width=3)
    h = (y1 - y0 - 12) * clamp(p)
    d.rounded_rectangle([x0 + 6, y1 - 6 - h, x1 - 6, y1 - 6], radius=18, fill=(*color, 255))
    d.text(((x0 + x1) / 2, y0 - 34), "PRESIÓN", font=font("bold", 26), fill=(*TEXT, 255), anchor="mm")
    if release > 0.02:
        d.text(((x0 + x1) / 2, y1 + 40), "¡LIBERADA!", font=font("bold", 24), fill=(*CORAL, 255), anchor="mm")


def render_engine(frame, scene: Scene, t: float, ctx: Ctx):
    vis = scene.visual
    stage = vis.stage or "full_cycle"
    brake = stage.startswith("brake")
    theta = _engine_theta(stage, t, ctx.duration)
    yaw = 0.18 + math.sin(t * 0.55) * 0.34
    fr = M.build_piston_engine(theta, brake, yaw)
    st = fr.info["state"]
    _paste3d(frame, fr, ctx)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # flame / release glow
    cx, cy = _project(fr, "chamber")
    if st["flame"] > 0.02:
        G.glow(layer, (cx, cy), 210 * st["flame"] + 60, M.FIRE, 1.0)
    if st["release"] > 0.02:
        ex, ey = _project(fr, "valve_ex")
        G.glow(layer, (ex + 30, ey + 40), 120 + 260 * st["release"], (255, 120, 110), 1.0)
    frame.paste(layer, (0, 0), layer)
    # gas flowing through the ports
    if st["intake_lift"] > 0.03:
        _flow_particles(frame, fr, fr.paths["intake"][0], t, M.AIR, n=16, speed=0.45, size=11, seed=3)
    if st["exh_lift"] > 0.03:
        col = (255, 150, 120) if st["release"] > 0.02 else st["color"]
        _flow_particles(frame, fr, fr.paths["exhaust"][0], t, col, n=20 if st["release"] > 0.02 else 14, speed=0.7, size=13, seed=5)
    # piston direction arrow
    px, py = _project(fr, "piston")
    rising = (math.sin(math.radians(theta)) > 0) == (False)
    d = ImageDraw.Draw(frame, "RGBA")
    ang = math.radians(theta % 720)
    going_down = math.sin(ang) > 0 if (theta % 720) < 360 else math.sin(ang) < 0
    going_down = (piston_vel(theta) < 0)
    ax = 860
    if going_down:
        G.arrow(d, (ax, py - 60), (ax, py + 70), color=CYAN, width=10, head=34)
    else:
        G.arrow(d, (ax, py + 60), (ax, py - 70), color=AMBER, width=10, head=34)
    _pressure_gauge(frame, st["p"], st["color"], st["release"])
    _stroke_tracker(frame, theta, brake, t)
    # labels
    _scene_callouts(frame, scene, fr, t, base=(W // 2, 0), spots=[(270, 440), (810, 440), (270, 640), (820, 640)])
    return fr


def piston_vel(theta_deg: float) -> float:
    return M.piston_pin_y(math.radians(theta_deg + 0.5)) - M.piston_pin_y(math.radians(theta_deg - 0.5))


def _scene_callouts(frame, scene, fr, t, base, spots, start=0.9, gap=1.1):
    """labels are 'anchor|Texto'; anchors resolve to projected 3D points."""
    color = ACCENT_BY_ROLE.get(scene.role, CYAN)
    for i, raw in enumerate(scene.visual.labels):
        if "|" not in raw:
            continue
        anchor, text = raw.split("|", 1)
        if anchor not in fr.anchors:
            continue
        ap = _project(fr, anchor)
        spot = spots[i % len(spots)]
        G.callout(frame, text, ap, (spot[0], spot[1]), start + i * gap, t, color=color)


# ---------------------------------------------------------------------------
# Mechanism: turbofan
# ---------------------------------------------------------------------------
def render_turbofan(frame, scene: Scene, t: float, ctx: Ctx):
    stage = scene.visual.stage or "overview"
    yaw = -0.62 + math.sin(t * 0.45) * 0.25
    fr = M.build_turbofan(t * 6.0, yaw, stage)
    _paste3d(frame, fr, ctx)
    bright = {"overview": None, "intake": "fan", "compression": "compressor", "combustion": "combustor", "exhaust": "turbine"}[stage]
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if bright:
        x, y = _project(fr, bright)
        pulse = 0.65 + 0.35 * math.sin(t * 5)
        G.glow(layer, (x, y), 230 * pulse + 60, {"fan": CYAN, "compressor": AMBER, "combustor": M.FIRE, "turbine": CORAL}[bright], 1.0)
    frame.paste(layer, (0, 0), layer)
    for k, (name, pts, col) in enumerate([("bypass", fr.paths["bypass"][0], None), ("core", fr.paths["core"][0], "core")]):
        scr = fr.cam.project(pts)
        path = [_to_abs((p[0], p[1])) for p in scr]
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        n = 18
        dd = ImageDraw.Draw(lay, "RGBA")
        total = sum(math.dist(path[i], path[i + 1]) for i in range(len(path) - 1))
        for i in range(n):
            u = (i / n + t * (0.22 if col is None else 0.17)) % 1.0
            dist = u * total
            acc = 0.0
            for j in range(len(path) - 1):
                sl = math.dist(path[j], path[j + 1])
                if acc + sl >= dist:
                    f = (dist - acc) / (sl or 1)
                    x = lerp(path[j][0], path[j + 1][0], f)
                    y = lerp(path[j][1], path[j + 1][1], f)
                    mx = lerp(pts[j][0], pts[j + 1][0], f)
                    c = M.AIR if col is None else M.core_temp_color(mx)
                    r = 9 + 3 * math.sin(i * 1.7)
                    dd.ellipse([x - r, y - r, x + r, y + r], fill=(*c, int(230 * math.sin(u * math.pi))))
                    break
                acc += sl
        frame.paste(lay, (0, 0), lay)
    _scene_callouts(frame, scene, fr, t, (W // 2, 0), spots=[(260, 480), (820, 480), (300, 1180), (800, 1180)])
    return fr


# ---------------------------------------------------------------------------
# Generic 3D-icon scenes
# ---------------------------------------------------------------------------
def _icon(shape: str, color, size=1.0) -> T.Mesh:
    if shape == "gear":
        return T.gear(0.7 * size, 1.05 * size, 10, 0.45 * size, color=color)
    if shape == "box":
        return T.box(1.5 * size, 1.1 * size, 1.1 * size, color=color)
    if shape == "cylinder":
        return T.cylinder(0.65 * size, 1.4 * size, axis="y", color=color, z0=-0.7 * size)
    if shape == "cone":
        return T.cone(0.75 * size, 0.05 * size, 1.5 * size, axis="y", color=color, z0=-0.75 * size)
    return T.sphere(0.8 * size, 20, color=color)


_DEFAULT_ICONS = ["sphere", "box", "gear", "cylinder", "cone"]
_NODE_COLORS = [CYAN, AMBER, MINT, CORAL, VIOLET]


def _node_text(raw: str) -> str:
    return raw.split("|", 1)[1] if "|" in raw else raw


def render_flow(frame, scene: Scene, t: float, ctx: Ctx):
    labels = [_node_text(x) for x in scene.visual.labels][:5] or ["Entrada", "Proceso", "Resultado"]
    n = len(labels)
    icons = (scene.visual.icons + _DEFAULT_ICONS)[:n]
    spacing = 2.9
    meshes, pts = [], []
    reveal = [seg(t, 0.4 + i * (ctx.duration - 1.6) / max(n, 1) * 0.8, 0.4 + i * (ctx.duration - 1.6) / max(n, 1) * 0.8 + 0.6) for i in range(n)]
    for i in range(n):
        y = (n - 1) / 2 * spacing - i * spacing
        x = (-1.6 if i % 2 == 0 else 1.6)
        pts.append((x, y, 0.0))
        r = ease_out_back(reveal[i])
        if r <= 0.01:
            continue
        col = _NODE_COLORS[i % 5]
        mesh = _icon(icons[i], tuple(int(c * 0.9) for c in col), 0.9)
        meshes.append(mesh.tf(T.rot_y(t * 0.9 + i) @ T.rot_x(0.35), (x, y, 0.0), s=r))
    cam = T.Camera(yaw=math.sin(t * 0.4) * 0.25, pitch=0.12, dist=15.5, fov_px=1500, target=(0, 0, 0), center_px=(540, 480))
    fr = M.ModelFrame(meshes, cam)
    _paste3d(frame, fr, ctx)
    d = ImageDraw.Draw(frame, "RGBA")
    scr = [_to_abs(tuple(cam.project([p])[0][:2])) for p in pts]
    for i in range(n - 1):
        p = clamp(reveal[i + 1] * 1.4)
        if p > 0:
            a, b = scr[i], scr[i + 1]
            ang = math.atan2(b[1] - a[1], b[0] - a[0])
            a2 = (a[0] + math.cos(ang) * 120, a[1] + math.sin(ang) * 120)
            b2 = (b[0] - math.cos(ang) * 120, b[1] - math.sin(ang) * 120)
            e = (lerp(a2[0], b2[0], p), lerp(a2[1], b2[1], p))
            G.arrow(d, a2, e, color=_NODE_COLORS[i % 5], width=9, head=30, dash_phase=t * 90)
    for i, lab in enumerate(labels):
        a = reveal[i]
        if a <= 0.05:
            continue
        x, y = scr[i]
        lx = x + (-240 if i % 2 == 0 else 240) if False else x
        d.rounded_rectangle([x - 190, y + 92, x + 190, y + 156], radius=30, fill=(8, 14, 34, int(220 * a)),
                            outline=(*_NODE_COLORS[i % 5], int(255 * a)), width=3)
        d.text((x, y + 124), lab, font=font("bold", 36), fill=(*TEXT, int(255 * a)), anchor="mm")
    return fr


def render_cycle(frame, scene: Scene, t: float, ctx: Ctx):
    labels = [_node_text(x) for x in scene.visual.labels][:6] or ["Fase 1", "Fase 2", "Fase 3", "Fase 4"]
    n = len(labels)
    icons = (scene.visual.icons + _DEFAULT_ICONS * 2)[:n]
    rad = 3.1
    active = int(clamp((t - 0.4) / max(ctx.duration - 0.8, 1.0)) * n * 0.999)
    meshes, pts = [], []
    for i in range(n):
        a = -math.pi / 2 + 2 * math.pi * i / n
        x, y = rad * math.cos(a), rad * math.sin(a) * -1
        pts.append((x, y, 0.0))
        on = i <= active
        r = ease_out_back(seg(t, 0.2 + i * 0.25, 0.8 + i * 0.25))
        s = 0.8 * r * (1.25 if i == active else 1.0)
        col = _NODE_COLORS[i % 5] if on else (90, 104, 140)
        if s > 0.01:
            meshes.append(_icon(icons[i], tuple(int(c * 0.9) for c in col), 0.75).tf(T.rot_y(t * 0.8 + i) @ T.rot_x(0.3), (x, y, 0), s=s))
    ring = T.revolve([(rad + 0.04, -0.03), (rad + 0.04, 0.03), (rad - 0.04, 0.03), (rad - 0.04, -0.03)], seg=72, axis="z", color=(70, 90, 140))
    meshes.insert(0, ring)
    cam = T.Camera(yaw=math.sin(t * 0.35) * 0.35, pitch=0.35, dist=15.5, fov_px=1500, target=(0, 0, 0), center_px=(540, 480))
    fr = M.ModelFrame(meshes, cam)
    _paste3d(frame, fr, ctx)
    d = ImageDraw.Draw(frame, "RGBA")
    scr = [_to_abs(tuple(cam.project([p])[0][:2])) for p in pts]
    # rotating chaser on the ring
    ang = -math.pi / 2 + (t * 0.8) % (2 * math.pi)
    cp = _to_abs(tuple(cam.project([(rad * math.cos(ang), -rad * math.sin(ang), 0)])[0][:2]))
    G.glow(frame_layer := Image.new("RGBA", (W, H), (0, 0, 0, 0)), cp, 70, AMBER, 1.0)
    frame.paste(frame_layer, (0, 0), frame_layer)
    for i, lab in enumerate(labels):
        a = seg(t, 0.4 + i * 0.25, 0.9 + i * 0.25)
        if a <= 0.02:
            continue
        x, y = scr[i]
        col = _NODE_COLORS[i % 5] if i <= active else MUTED
        dy = 100 if y > VIZ_TOP + 480 else -110
        d.rounded_rectangle([x - 150, y + dy - 34, x + 150, y + dy + 34], radius=30, fill=(8, 14, 34, int(220 * a)),
                            outline=(*col, int(255 * a)), width=3)
        d.text((x, y + dy), lab, font=font("bold", 32), fill=(*TEXT, int(255 * a)), anchor="mm")
    return fr


def render_layers(frame, scene: Scene, t: float, ctx: Ctx):
    labels = [_node_text(x) for x in scene.visual.labels][:5] or ["Capa 1", "Capa 2", "Capa 3"]
    n = len(labels)
    explode = ease_in_out(seg(t, 0.5, 2.2))
    meshes, ys = [], []
    for i in range(n):
        y = (n - 1) / 2 * (0.5 + 1.0 * explode) - i * (0.5 + 1.0 * explode)
        ys.append(y)
        col = _NODE_COLORS[i % 5]
        slab = T.box(4.4, 0.34, 3.0, color=tuple(int(c * 0.85) for c in col))
        meshes.append(slab.tf(None, (0, y, 0)))
    cam = T.Camera(yaw=0.55 + math.sin(t * 0.4) * 0.2, pitch=0.5, dist=15.5, fov_px=1500, target=(0, 0, 0), center_px=(540, 470))
    fr = M.ModelFrame(meshes, cam)
    _paste3d(frame, fr, ctx)
    for i, lab in enumerate(labels):
        ap = _to_abs(tuple(cam.project([(2.0, ys[i], 0)])[0][:2]))
        G.callout(frame, lab, ap, (840, ap[1] + 10), 1.4 + i * 0.5, t, color=_NODE_COLORS[i % 5], size=36)
    return fr


def render_stat(frame, scene: Scene, t: float, ctx: Ctx):
    vals = scene.visual.values[:5] or [1.0, 2.0]
    labels = [_node_text(x) for x in scene.visual.labels][: len(vals)]
    labels += [""] * (len(vals) - len(labels))
    mx = max(vals) or 1.0
    meshes = []
    n = len(vals)
    for i, v in enumerate(vals):
        h = 4.6 * (v / mx) * ease_out(seg(t, 0.5 + i * 0.35, 1.8 + i * 0.35))
        if h < 0.02:
            continue
        x = (i - (n - 1) / 2) * 2.0
        meshes.append(T.box(1.3, h, 1.3, color=tuple(int(c * 0.9) for c in _NODE_COLORS[i % 5])).tf(None, (x, h / 2 - 2.4, 0)))
    cam = T.Camera(yaw=0.35 + math.sin(t * 0.4) * 0.15, pitch=0.28, dist=15.0, fov_px=1500, target=(0, 0, 0), center_px=(540, 470))
    fr = M.ModelFrame(meshes, cam)
    base = T.box(2.0 * n + 1.0, 0.2, 2.0, color=(60, 76, 112)).tf(None, (0, -2.5, 0))
    fr.meshes.insert(0, base)
    _paste3d(frame, fr, ctx)
    d = ImageDraw.Draw(frame, "RGBA")
    for i, v in enumerate(vals):
        p = ease_out(seg(t, 0.9 + i * 0.35, 1.8 + i * 0.35))
        if p <= 0.02:
            continue
        x = (i - (n - 1) / 2) * 2.0
        h = 4.6 * (v / mx) * ease_out(seg(t, 0.5 + i * 0.35, 1.8 + i * 0.35))
        sx, sy = tuple(cam.project([(x, h - 2.4, 0)])[0][:2])
        txt = (f"{v:g}" + (f" {scene.visual.unit}" if scene.visual.unit else ""))
        d.text((sx, sy + VIZ_TOP - 50), txt, font=font("bold", 48), fill=(*TEXT, int(255 * p)), anchor="mm", stroke_width=4, stroke_fill=(8, 14, 34, 255))
        bx, by = tuple(cam.project([(x, -2.5, 0.9)])[0][:2])
        d.text((bx, by + VIZ_TOP + 56), labels[i], font=font("bold", 32), fill=(*MUTED, int(255 * p)), anchor="mm")
    return fr


def render_hook(frame, scene: Scene, t: float, ctx: Ctx):
    model = scene.visual.model
    zoom = 1.0 + 0.18 * (1 - ease_out(seg(t, 0, 1.4)))
    if model == "turbofan":
        fr = M.build_turbofan(t * 7.0, -0.7 + t * 0.25, "overview")
    elif model == "piston_engine":
        fr = M.build_piston_engine((t * 140) % 720, False, 0.3 + t * 0.3)
    else:
        fr = M.ModelFrame([_icon("gear", AMBER, 1.6).tf(T.rot_y(t * 0.9) @ T.rot_x(0.4)),
                           _icon("gear", CYAN, 1.0).tf(T.rot_y(-t * 1.5) @ T.rot_x(0.4), (1.9, 1.3, 0))],
                          T.Camera(yaw=0.2, pitch=0.2, dist=12.0, fov_px=1500, center_px=(540, 480)))
    fr.cam.fov_px *= zoom * 0.88
    fr.cam.center_px = (540, 420)
    _paste3d(frame, fr, ctx)
    # big question text, word by word
    title = scene.visual.title or scene.narration
    words = title.split()
    d = ImageDraw.Draw(frame, "RGBA")
    fnt = font("bold", 84)
    lines, cur = [], []
    for w_ in words:
        trial = " ".join(cur + [w_])
        if G.text_size(trial, fnt)[0] > W - 160 and cur:
            lines.append(cur)
            cur = [w_]
        else:
            cur.append(w_)
    if cur:
        lines.append(cur)
    idx = 0
    total_words = len(words)
    y = 1070 if len(lines) <= 2 else 1040
    for line in lines:
        text = " ".join(line)
        tw, _ = G.text_size(text, fnt)
        x = (W - tw) / 2
        for w_ in line:
            p = ease_out_back(seg(t, 0.25 + idx * 0.22, 0.6 + idx * 0.22))
            ww, _ = G.text_size(w_ + " ", fnt)
            if p > 0.01:
                col = AMBER if idx == total_words - 1 or "?" in w_ else TEXT
                d.text((x, y + (1 - p) * 40), w_, font=fnt, fill=(*col, int(255 * clamp(p))), anchor="lm",
                       stroke_width=5, stroke_fill=(8, 14, 34, int(255 * clamp(p))))
            x += ww
            idx += 1
        y += 104
    return fr


def render_cta(frame, scene: Scene, t: float, ctx: Ctx):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer, "RGBA")
    cx, cy = W // 2, 760
    p = ease_out_back(seg(t, 0.1, 0.9))
    R = 250 * p
    for k, (rx, ry, ang, col) in enumerate([(1.0, 0.36, 0.5, CYAN), (1.0, 0.36, -0.5, AMBER), (1.0, 0.36, 1.57, MINT)]):
        pts = []
        for i in range(120):
            a = 2 * math.pi * i / 120
            x, y = R * rx * math.cos(a), R * ry * math.sin(a)
            x, y = x * math.cos(ang + t * 0.5 * (1 if k else -1)) - y * math.sin(ang + t * 0.5 * (1 if k else -1)), \
                x * math.sin(ang + t * 0.5 * (1 if k else -1)) + y * math.cos(ang + t * 0.5 * (1 if k else -1))
            pts.append((cx + x, cy + y))
        d.line(pts + [pts[0]], fill=(*col, 255), width=9, joint="curve")
        a = t * 1.8 + k * 2.1
        x, y = R * rx * math.cos(a), R * ry * math.sin(a)
        ang_t = ang + t * 0.5 * (1 if k else -1)
        x, y = x * math.cos(ang_t) - y * math.sin(ang_t), x * math.sin(ang_t) + y * math.cos(ang_t)
        d.ellipse([cx + x - 17, cy + y - 17, cx + x + 17, cy + y + 17], fill=(*TEXT, 255))
    d.ellipse([cx - 62 * p, cy - 62 * p, cx + 62 * p, cy + 62 * p], fill=(8, 14, 34, 255), outline=(*TEXT, 255), width=4)
    d.text((cx, cy), "360", font=font("bold", int(64 * max(p, 0.1))), fill=(*TEXT, 255), anchor="mm")
    frame.paste(layer, (0, 0), layer)
    d = ImageDraw.Draw(frame, "RGBA")
    pp = ease_out(seg(t, 0.5, 1.1))
    d.text((cx, 1060), "EXPLORA CIENCIA 360", font=font("bold", 70), fill=(*TEXT, int(255 * pp)), anchor="mm", stroke_width=4, stroke_fill=(8, 14, 34, int(255 * pp)))
    bp = ease_out_back(seg(t, 0.9, 1.5))
    pulse = 1 + 0.04 * math.sin(t * 5)
    bw, bh = 420 * bp * pulse, 92 * bp * pulse
    d.rounded_rectangle([cx - bw / 2, 1150 - bh / 2, cx + bw / 2, 1150 + bh / 2], radius=46, fill=(*AMBER, 255))
    if bp > 0.5:
        d.text((cx, 1150), "SÍGUENOS", font=font("bold", 48), fill=(8, 14, 34, 255), anchor="mm")
    return None


RENDERERS = {
    "hook": render_hook,
    "flow": render_flow,
    "cycle": render_cycle,
    "layers": render_layers,
    "stat": render_stat,
    "cta": render_cta,
}


def render_visual(frame: Image.Image, scene: Scene, t: float, ctx: Ctx):
    kind = scene.visual.kind
    if kind == "mechanism":
        if scene.visual.model == "piston_engine":
            return render_engine(frame, scene, t, ctx)
        if scene.visual.model == "turbofan":
            return render_turbofan(frame, scene, t, ctx)
        return render_flow(frame, scene, t, ctx)
    return RENDERERS[kind](frame, scene, t, ctx)


# ---------------------------------------------------------------------------
# Transitions / full frame
# ---------------------------------------------------------------------------
_TRANSITIONS = ["wipe_right", "iris", "wipe_up", "blinds"]


def apply_transition(frame: Image.Image, t: float, index: int, length: float = 0.42):
    if index <= 1 or t >= length:
        return frame
    p = ease_in_out(t / length)
    kind = _TRANSITIONS[(index - 2) % len(_TRANSITIONS)]
    mask = Image.new("L", (W, H), 0)
    md = ImageDraw.Draw(mask)
    edge = None
    if kind == "wipe_right":
        x = int(W * p)
        md.rectangle([0, 0, x, H], fill=255)
        edge = [(x, 0, x + 10, H)]
    elif kind == "wipe_up":
        y = int(H * (1 - p))
        md.rectangle([0, y, W, H], fill=255)
        edge = [(0, y - 10, W, y)]
    elif kind == "iris":
        r = int(math.hypot(W, H) / 2 * p)
        md.ellipse([W / 2 - r, H / 2 - r, W / 2 + r, H / 2 + r], fill=255)
    else:
        n = 8
        for i in range(n):
            y0 = i * H / n
            md.rectangle([0, y0, W, y0 + H / n * p], fill=255)
    cover = Image.new("RGB", (W, H), G.BG_TOP)
    out = Image.composite(frame, cover, mask)
    if edge:
        d = ImageDraw.Draw(out)
        for e in edge:
            d.rectangle(e, fill=G.CYAN)
    return out


def render_scene_frame(scene: Scene, t: float, ctx: Ctx) -> Image.Image:
    frame = G.new_frame(t, seed=ctx.index)
    render_visual(frame, scene, t, ctx)
    accent = ACCENT_BY_ROLE.get(scene.role, CYAN)
    if scene.role not in ("hook", "cta"):
        G.step_header(frame, ctx.index - 1, scene.visual.title, t, accent)
    G.brand_tag(frame, t)
    return apply_transition(frame, t, ctx.index)
