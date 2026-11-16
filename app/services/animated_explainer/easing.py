"""Funciones de interpolación y utilidades de animación."""

from __future__ import annotations

import math


def clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return lo if v < lo else hi if v > hi else v


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def linear(t: float) -> float:
    return clamp(t)


def ease_in_out(t: float) -> float:
    t = clamp(t)
    return t * t * (3 - 2 * t)


def ease_out(t: float) -> float:
    t = clamp(t)
    return 1 - (1 - t) ** 3


def ease_in(t: float) -> float:
    t = clamp(t)
    return t ** 3


def ease_out_back(t: float) -> float:
    t = clamp(t)
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


def ease_out_elastic(t: float) -> float:
    t = clamp(t)
    if t in (0.0, 1.0):
        return t
    return 2 ** (-10 * t) * math.sin((t * 10 - 0.75) * (2 * math.pi) / 3) + 1


EASINGS = {
    "linear": linear,
    "in_out": ease_in_out,
    "out": ease_out,
    "in": ease_in,
    "back": ease_out_back,
    "elastic": ease_out_elastic,
}


def get_easing(name: str):
    return EASINGS.get(name or "in_out", ease_in_out)


def keyframes(frames: list[dict], t: float, keys: tuple[str, ...], easing: str = "in_out"):
    """Interpola entre keyframes ``[{'at':0..1, k:valor,...}]`` en el tiempo ``t`` (0..1)."""
    frames = sorted(frames, key=lambda f: f.get("at", 0.0))
    if t <= frames[0].get("at", 0.0):
        return {k: frames[0][k] for k in keys if k in frames[0]}
    for a, b in zip(frames, frames[1:]):
        ta, tb = a.get("at", 0.0), b.get("at", 0.0)
        if t <= tb:
            u = get_easing(b.get("ease", easing))((t - ta) / max(tb - ta, 1e-6))
            out = {}
            for k in keys:
                if k in a and k in b:
                    out[k] = lerp(a[k], b[k], u)
                elif k in b:
                    out[k] = b[k]
                elif k in a:
                    out[k] = a[k]
            return out
    return {k: frames[-1][k] for k in keys if k in frames[-1]}
