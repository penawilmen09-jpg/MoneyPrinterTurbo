"""Constantes y funciones de easing."""
import math

W, H, FPS = 1080, 1920, 30
VOICE = "es-MX-JorgeNeural"   # voz masculina, español latino (fija para todos los videos)
VOICE_RATE = "-3%"


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def lerp(a, b, k):
    return a + (b - a) * k


def prog(t, a, b):
    """Progreso 0..1 de t entre a y b."""
    return clamp((t - a) / (b - a)) if b != a else 1.0


def smooth(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ease_in_out(x):
    x = clamp(x)
    return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2


def ease_out(x):
    return 1 - (1 - clamp(x)) ** 3


def ease_out_back(x, s=1.70158):
    x = clamp(x)
    return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2


def n(v):
    return f"{v:.2f}"
