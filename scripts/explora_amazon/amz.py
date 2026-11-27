"""Entorno común: reutiliza el motor 2D existente (explora_musk: people/stage/kit/props)."""
import os, sys
_M = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "explora_musk"))
for p in (_M, os.path.dirname(__file__)):
    if p not in sys.path: sys.path.insert(0, p)
from kit import *
from stage import _font
from props import *
from props_a import *
from m1 import skyline, car_icon
from m7 import logo
from stage import clouds
from people import blend as blend_pose


def rect_np(base, x0, y0, x1, y1, color, alpha=1.0):
    """Rectángulo sólido directamente sobre la base (sin resplandor)."""
    x0, y0, x1, y1 = int(max(x0, 0)), int(max(y0, 0)), int(min(x1, W)), int(min(y1, H))
    if x1 > x0 and y1 > y0:
        base[y0:y1, x0:x1] = base[y0:y1, x0:x1] * (1 - alpha) + np.array(color, np.float32) * alpha
