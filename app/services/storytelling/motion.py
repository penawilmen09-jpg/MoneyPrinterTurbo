"""Biblioteca de acciones: pose del personaje en función del tiempo.

Cada acción es una función pura de ``(t, ctx)`` (sin estado), de modo que el
renderizado es determinista y se puede paralelizar por escenas.

Convención (espacio del rig): el personaje SIEMPRE mira hacia +x.  El volteo
horizontal lo aplica el dibujante.  ``arm_r``/``leg_r`` son los miembros
delanteros (+x) y ``arm_l``/``leg_l`` los traseros (-x).  Ángulos: 0 = hacia
abajo, + = hacia +x, ±180 = hacia arriba.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

from .rig import Pose, apply_expression

TAU = math.pi * 2


@dataclass
class MotionCtx:
    action: str
    expression: str
    speaking: bool
    facing: int  # +1 mira a la derecha de la pantalla
    look_dir: float  # -1 izquierda .. 1 derecha de la pantalla (hacia dónde mirar)
    speech_level: float  # 0..1 energía de la voz en este instante
    seed: int
    walk_phase: float = 0.0  # fase de caminata acumulada (ciclos)
    moving: bool = False
    point_dir: float = 1.0  # +1 señala a la derecha de la pantalla


def _blink(t: float, seed: int) -> float:
    rng = random.Random(seed)
    period = 3.1 + rng.random() * 1.4
    phase = (t + rng.random() * period) % period
    if phase < 0.14:
        return math.sin(phase / 0.14 * math.pi)
    return 0.0


def compute_pose(t: float, ctx: MotionCtx) -> Pose:
    """Pose completa (cuerpo + cara) en el instante ``t`` (segundos)."""
    p = Pose()
    f = ctx.facing
    a = ctx.action
    phase = t * 0.9 + ctx.seed * 0.37
    breathe = math.sin(phase * TAU * 0.5)
    p.bob = breathe * 4
    p.head_tilt = math.sin(phase * TAU * 0.28) * 2.0

    # --- base: de pie, relajado ------------------------------------------------
    p.arm_l = (-9 - breathe * 2, -6)
    p.arm_r = (9 + breathe * 2, 6)
    sh = math.sin(phase * TAU * 0.5) * 1.5
    p.leg_l = (-4 - sh, -3)
    p.leg_r = (4 + sh, 3)

    walking = ctx.moving or a in ("walk", "walk_in", "walk_out")
    if walking:
        ph = ctx.walk_phase * TAU
        swing = 24
        p.leg_r = (math.sin(ph) * swing, math.sin(ph) * swing - max(0.0, -math.sin(ph)) * 26)
        p.leg_l = (-math.sin(ph) * swing, -math.sin(ph) * swing - max(0.0, math.sin(ph)) * 26)
        p.bob = -abs(math.sin(ph)) * 14
        p.arm_l = (math.sin(ph) * 30 - 6, math.sin(ph) * 30 - 6)
        p.arm_r = (-math.sin(ph) * 30 + 6, -math.sin(ph) * 30 + 6)
        p.lean = 8

    # --- acciones ------------------------------------------------------------
    if a == "talk" or ctx.speaking:
        g = math.sin(t * 5.2 + ctx.seed) * 0.5 + 0.5
        energy = 0.35 + ctx.speech_level * 0.65
        if a in ("talk", "idle", "nod", "lean_in") or ctx.speaking:
            p.arm_r = (28 + g * 26 * energy, 78 + g * 34 * energy)
        p.head_tilt += math.sin(t * 3.1 + ctx.seed) * 3 * energy
        p.bob += math.sin(t * 6.0) * 2 * energy

    if a == "point":
        rel = ctx.point_dir * f  # >0: el objetivo está delante del personaje
        pump = math.sin(t * 4) * 4
        if rel >= 0:
            p.arm_r = (84 + pump, 86 + pump * 0.5)
            p.arm_l = (-9, -6)
        else:
            p.arm_l = (-84 - pump, -86 - pump * 0.5)
            p.arm_r = (9, 6)
        p.lean = 10 * rel
    elif a == "look_around":
        p.head_turn = math.sin(t * 1.6) * 0.85
        p.eye_x = math.sin(t * 1.6) * 0.9
        p.lean = math.sin(t * 1.6) * 5
    elif a == "shrug":
        k = math.sin(t * 2.4) * 0.5 + 0.5
        p.arm_l = (-40 - k * 18, -95 - k * 25)
        p.arm_r = (40 + k * 18, 95 + k * 25)
        p.bob -= k * 6
        p.head_tilt += 5
    elif a == "panic":
        k = math.sin(t * 14) * 4
        p.arm_l = (-150 + k, 165 + k)  # manos a las mejillas
        p.arm_r = (150 - k, -165 - k)
        p.bob += math.sin(t * 16) * 3
        p.head_tilt += math.sin(t * 11) * 4
    elif a == "hands_up":
        p.arm_l = (-150, -176)
        p.arm_r = (150, 176)
    elif a == "think":
        p.arm_r = (-25, -165)  # mano al mentón
        p.arm_l = (-9, -6)
        p.head_tilt += 5
        p.eye_y = -0.5
    elif a == "wave":
        w = math.sin(t * 9) * 16
        p.arm_r = (140 + w * 0.3, 172 + w)
    elif a == "type":
        k = math.sin(t * 12) * 6
        p.arm_l = (-48 - k, -98 + k)
        p.arm_r = (48 + k, 98 - k)
        p.lean = 14
        p.head_tilt += 3
        p.eye_y = 0.5
    elif a == "scan_item":
        k = math.sin(t * 3.0) * 0.5 + 0.5
        p.arm_r = (55 + k * 25, 78 + k * 35)
        p.arm_l = (-40 - k * 5, -100 + k * 20)
        p.lean = 8
        p.eye_y = 0.5
    elif a == "hold_item":
        p.arm_r = (52, 95)
    elif a == "lean_in":
        p.lean = 24
        p.head_tilt += 4
        p.eye_y = 0.2
    elif a == "nod":
        p.head_tilt += math.sin(t * 6) * 6
        p.bob += math.sin(t * 6) * 3
    elif a == "celebrate":
        k = math.sin(t * 7)
        p.arm_l = (-150 + k * 10, -172 + k * 10)
        p.arm_r = (150 - k * 10, 172 - k * 10)
        p.bob = -abs(math.sin(t * 7)) * 26
    elif a == "cross_arms":
        p.arm_l = (15, 100)
        p.arm_r = (-15, -100)
        p.head_tilt -= 3

    # --- mirada / giro de cabeza (espacio de pantalla) -------------------------
    if a != "look_around" and abs(ctx.look_dir) > 0.01:
        p.head_turn = max(-1.0, min(1.0, ctx.look_dir * 0.75))
        p.eye_x = ctx.look_dir * 0.9

    apply_expression(p, ctx.expression)
    p.blink = _blink(t, ctx.seed)
    if ctx.speaking:
        osc = (math.sin(t * 17.0 + ctx.seed) * 0.5 + 0.5) * 0.6 + (math.sin(t * 9.3) * 0.5 + 0.5) * 0.4
        p.mouth_open = max(p.mouth_open * 0.5, min(1.0, ctx.speech_level * (0.35 + 0.75 * osc)))
        p.mouth_curve = max(p.mouth_curve, 0.1)
    return p
