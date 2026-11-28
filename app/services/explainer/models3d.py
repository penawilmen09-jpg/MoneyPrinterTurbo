"""Parametric 3D models used by MIXED EXPLAINER scenes.

Each ``build_*`` function receives animation parameters and returns the meshes
plus screen-space helper data (anchor points, particle paths) so the 2D
overlay layer can annotate exactly what the 3D layer is showing.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from . import three as T
from .gfx import CORAL, CYAN, AMBER, STEEL_D, STEEL_L, STEEL_M, MINT, lerp_color, clamp, seg

# ---------------------------------------------------------------------------
# Four-stroke (diesel) piston engine with optional compression-release brake
# ---------------------------------------------------------------------------
CR_ = 0.55    # crank radius
ROD = 2.1     # connecting rod length
PIN_UP = 0.5  # piston crown above pin
PIN_DN = 0.45
Y_HEAD = (CR_ + ROD) + PIN_UP + 0.14
BORE = 0.98
AIR = (90, 170, 255)
HOT = (255, 196, 80)
FIRE = (255, 112, 44)
EXH = (150, 150, 165)
BRAKE_RED = (255, 70, 92)

ENGINE_STAGES = ("intake", "compression", "power", "exhaust", "full_cycle",
                 "brake_compression", "brake_release", "brake_full")


def piston_pin_y(theta: float) -> float:
    return CR_ * math.cos(theta) + math.sqrt(ROD ** 2 - (CR_ * math.sin(theta)) ** 2)


def _volume(theta: float) -> float:
    return Y_HEAD - (piston_pin_y(theta) + PIN_UP)


_V_MAX = _volume(math.pi)
_V_MIN = _volume(0.0)


def stage_range(stage: str) -> tuple[float, float]:
    """Crank-angle window (degrees, 0..720) shown for a named stage."""
    return {
        "intake": (0, 180), "compression": (180, 360), "power": (360, 540),
        "exhaust": (540, 720), "full_cycle": (0, 720),
        "brake_compression": (180, 372), "brake_release": (300, 420),
        "brake_full": (0, 720),
    }[stage]


def engine_state(theta_deg: float, brake: bool) -> dict:
    """Gas pressure (0..1), colour, valve lifts and flame for a crank angle."""
    d = theta_deg % 720.0
    th = math.radians(d)
    vol = _volume(th)
    comp = (_V_MAX / vol) ** 1.3 / ((_V_MAX / _V_MIN) ** 1.3)  # 0..1 at TDC
    intake_lift = 0.30 * math.sin(math.pi * clamp(d / 190.0)) if d < 190 else 0.0
    exh_lift = 0.30 * math.sin(math.pi * clamp((d - 530.0) / 190.0)) if d > 530 else 0.0
    release = 0.0
    flame = 0.0
    if brake:
        release = 0.20 * math.sin(math.pi * clamp((d - 336.0) / 34.0)) if 336 <= d <= 370 else 0.0
        exh_lift = max(exh_lift, release)
    if d < 180:
        p, col, gas = 0.06, AIR, "air"
    elif d < 360:
        p = comp
        if brake and d >= 346:           # compression-release: pressure dumps
            p = comp * max(0.0, 1 - (d - 346) / 10.0) + 0.03
        col = lerp_color(AIR, BRAKE_RED if brake else HOT, clamp(p * 1.35))
        gas = "compressed"
    elif d < 540:
        if brake:
            p, col, gas = 0.05, lerp_color(HOT, AIR, 0.5), "spent"
        else:
            k = (d - 360) / 180.0
            p = max(0.05, 1.0 * (1 - k) ** 1.4 if k > 0.06 else 1.0)
            flame = clamp(1 - (d - 360) / 55.0)
            col = lerp_color(FIRE, EXH, clamp(k * 1.2))
            gas = "burn"
    else:
        p, col, gas = 0.06, EXH if not brake else lerp_color(HOT, AIR, 0.5), "exhaust"
    return {"theta": d, "p": clamp(p), "color": col, "gas": gas, "flame": flame,
            "intake_lift": intake_lift, "exh_lift": exh_lift, "release": release}


@dataclass
class ModelFrame:
    meshes: list
    cam: T.Camera
    anchors: dict = field(default_factory=dict)       # name -> world point
    paths: dict = field(default_factory=dict)         # name -> (points, color, dir)
    info: dict = field(default_factory=dict)


def build_piston_engine(theta_deg: float, brake: bool, yaw: float, pitch: float = 0.2,
                        highlight_release: bool = False, intro: float = 1.0) -> ModelFrame:
    st = engine_state(theta_deg, brake)
    th = math.radians(theta_deg)
    py = piston_pin_y(th)
    meshes: list[T.Mesh] = []
    steel = STEEL_L
    dark = STEEL_D
    mid = STEEL_M

    # cylinder liner (back half only -> cutaway) + outer block
    meshes.append(T.shell(BORE + 0.30, BORE, Y_HEAD - 1.0, seg=56, axis="y", color=mid,
                          z0=1.0, arc=(0.0, math.pi)))
    # crankcase: back plate + lower tub
    meshes.append(T.cylinder(1.65, 0.12, axis="z", color=dark, z0=-0.95, seg=48))
    meshes.append(T.shell(1.65, 1.5, 1.1, axis="z", color=mid, z0=-0.95, seg=48, arc=(math.pi, 2 * math.pi)))
    # crankshaft: axle, webs, pin and counterweight (rotating)
    meshes.append(T.cylinder(0.2, 1.5, axis="z", color=steel, z0=-0.75))
    pin = np.array([CR_ * math.sin(th), CR_ * math.cos(th), 0.0])
    web = T.cylinder(0.62, 0.16, axis="z", color=steel, z0=-0.34)
    meshes.append(web)
    meshes.append(T.cylinder(0.17, 0.7, axis="z", color=(210, 220, 240), z0=-0.35).tf(t=pin))
    cw_center = th + math.pi  # counterweight opposite the pin
    # counterweight arc is expressed in the XY plane (z axis revolve): angle from +x
    cw_a = math.pi / 2 - cw_center
    meshes.append(T.revolve([(0, -0.34), (1.0, -0.34), (1.0, -0.16), (0, -0.16)], seg=24,
                            arc=(cw_a - 0.75, cw_a + 0.75), axis="z", color=(120, 138, 172)))
    # connecting rod
    pp = np.array([0.0, py, 0.0])
    meshes.append(T.slab_between(pin + [0, 0, 0.02], pp, 0.2, 0.16, color=(185, 198, 224)))
    meshes.append(T.cylinder(0.3, 0.1, axis="z", color=steel, z0=-0.02).tf(t=pin + [0, 0, 0.12]))
    meshes.append(T.cylinder(0.2, 0.1, axis="z", color=steel, z0=-0.05).tf(t=pp + [0, 0, 0.0]))
    # piston: crown + skirt + rings
    top = py + PIN_UP
    meshes.append(T.cylinder(BORE - 0.03, PIN_UP + PIN_DN, axis="y", color=(196, 208, 232), z0=py - PIN_DN))
    for k in range(3):
        meshes.append(T.shell(BORE, BORE - 0.1, 0.05, axis="y", color=(70, 84, 118), z0=top - 0.14 - 0.12 * k, seg=40))
    meshes.append(T.cylinder(0.13, 1.5, axis="z", color=dark, z0=-0.75).tf(t=pp))
    # head plate + ports + valves
    meshes.append(T.box(3.0, 0.18, 2.6, color=dark).tf(t=(0, Y_HEAD + 0.09, 0)))
    for sx in (-1, 1):
        x = 0.55 * sx
        meshes.append(T.shell(0.40, 0.30, 0.9, axis="y", color=mid, z0=Y_HEAD + 0.18, arc=(0, math.pi)).tf(t=(x, 0, 0)))
        z0 = 0.0 if sx > 0 else -1.9
        meshes.append(T.shell(0.40, 0.30, 1.9, axis="x", color=mid, z0=z0, arc=(-math.pi / 2, math.pi / 2))
                      .tf(t=(x, Y_HEAD + 1.08, 0)))
    lifts = {-1: st["intake_lift"], 1: st["exh_lift"]}
    for sx in (-1, 1):
        x = 0.55 * sx
        lift = lifts[sx]
        col = (100, 190, 255) if sx < 0 else ((255, 120, 110) if (st["release"] > 0.02) else (255, 160, 90))
        meshes.append(T.cylinder(0.055, 1.45, axis="y", color=(215, 225, 245), z0=Y_HEAD - lift - 0.02).tf(t=(x, 0, 0)))
        meshes.append(T.cone(0.34, 0.06, 0.1, axis="y", color=col, z0=Y_HEAD - lift - 0.1).tf(t=(x, 0, 0)))
    # injector
    meshes.append(T.cylinder(0.09, 0.9, axis="y", color=(190, 150, 100), z0=Y_HEAD).tf(t=(0, 0.0, 0)))
    # Jacobs-style brake slave piston above the exhaust valve (brake modes only)
    if brake:
        act = st["release"] > 0.02
        c = (255, 80, 100) if act else (170, 70, 90)
        meshes.append(T.cylinder(0.2, 0.42, axis="y", color=c, z0=Y_HEAD + 1.3).tf(t=(0.55, 0, 0)).colored(c, emissive=0.5 if act else 0.0))

    # translucent gas volume in the chamber (drawn last)
    h = Y_HEAD - top
    if h > 0.01:
        g = T.cylinder(BORE - 0.04, h, axis="y", color=st["color"], z0=top, arc=(0, math.pi))
        a = 0.35 + 0.35 * st["p"]
        g = g.colored(st["color"], alpha=a, prio=50.0, outline=False, emissive=0.55)
        meshes.append(g)

    cam = T.Camera(yaw=yaw, pitch=pitch, dist=13.8, fov_px=1500, target=(0.0, 1.95, 0.0), center_px=(540, 480))
    anchors = {
        "piston": (0.0, top - 0.2, 0.0), "valve_in": (-0.55, Y_HEAD + 0.6, 0.0),
        "valve_ex": (0.55, Y_HEAD + 0.6, 0.0), "chamber": (0.0, (Y_HEAD + top) / 2, 0.0),
        "crank": (0.0, 0.0, 0.0), "rod": tuple((pin + pp) / 2), "head_top": (0.0, Y_HEAD + 1.0, 0),
        "slave": (0.55, Y_HEAD + 1.5, 0),
    }
    paths = {
        "intake": ([(-2.6, Y_HEAD + 1.08, 0), (-0.55, Y_HEAD + 1.08, 0), (-0.55, Y_HEAD + 0.1, 0), (-0.45, Y_HEAD - 0.5, 0)], AIR),
        "exhaust": ([(0.55, Y_HEAD - 0.4, 0), (0.55, Y_HEAD + 1.08, 0), (2.6, Y_HEAD + 1.08, 0)], st["color"] if st["gas"] != "air" else EXH),
    }
    return ModelFrame(meshes, cam, anchors, paths, {"state": st, "piston_top": top})


# ---------------------------------------------------------------------------
# Turbofan jet engine (cutaway, axis along X)
# ---------------------------------------------------------------------------
TURBOFAN_STAGES = ("overview", "intake", "compression", "combustion", "exhaust")
_TF = {  # axial x-ranges of each section
    "fan": -3.2, "comp": (-1.9, -0.5), "burner": (0.0, 1.25), "turb": (1.55, 2.25), "nozzle": (2.5, 3.9),
}


def _blade_ring(x, n, r0, r1, phase, chord, thick, color, twist=0.8):
    b = T.blade(r1 - r0, chord, thick, twist=twist, color=color)
    b = b.tf(T.rot_z(math.pi / 2), (0, r0, 0))
    out = []
    for i in range(n):
        out.append(b.tf(T.rot_x(phase + 2 * math.pi * i / n), (x, 0, 0)))
    return out


def build_turbofan(spin: float, yaw: float, stage: str = "overview", pitch: float = 0.22) -> ModelFrame:
    meshes: list[T.Mesh] = []
    steel, mid, dark = STEEL_L, STEEL_M, STEEL_D
    cut = (-math.pi / 2, math.pi / 2)  # keep the back half (z<0) so the interior is visible
    # Nacelle and core cowl (cutaway)
    nac = [(2.05, -4.0), (2.0, 3.2), (1.85, 3.2), (1.9, -4.0), (2.05, -4.0)]
    meshes.append(T.revolve(nac, seg=60, arc=cut, axis="x", color=(120, 140, 178)))
    core = [(1.02, -1.2), (1.02, 3.6), (0.92, 3.6), (0.92, -1.2), (1.02, -1.2)]
    meshes.append(T.revolve(core, seg=48, arc=cut, axis="x", color=(96, 114, 150)))
    # spinner and hub drum
    meshes.append(T.revolve([(0, -4.3), (0.35, -4.05), (0.62, -3.55), (0.62, -3.1)], seg=32, axis="x", color=(205, 215, 238)))
    meshes.append(T.revolve([(0.62, -3.1), (0.5, -1.9), (0.7, 0.0), (0.7, 3.5)], seg=32, axis="x", color=(130, 146, 178)))
    # fan blades
    meshes += _blade_ring(-3.25, 16, 0.55, 1.88, spin, 0.55, 0.06, (210, 222, 245), twist=0.9)
    # compressor stages: blades getting shorter
    for k, x in enumerate([-1.85, -1.4, -0.95, -0.5]):
        r1 = 0.97 - 0.05 * k
        meshes += _blade_ring(x, 20, 0.55 + 0.06 * k, r1, -spin * 1.4 + k * 0.3, 0.2, 0.04, (186, 200, 228), twist=0.6)
    # combustor: glowing annular chamber
    comb_active = stage in ("combustion", "overview")
    cc = (255, 140, 60) if comb_active else (150, 110, 90)
    meshes.append(T.revolve([(0.92, 0.0), (0.92, 1.25), (0.74, 1.25), (0.74, 0.0), (0.92, 0.0)], seg=40, arc=cut, axis="x",
                            color=cc).colored(cc, emissive=0.45 if comb_active else 0.12))
    # turbine stages
    for k, x in enumerate([1.6, 1.95, 2.3]):
        meshes += _blade_ring(x, 22, 0.7, 0.92 + 0.0 * k, spin * 1.6 + k * 0.2, 0.22, 0.04, (170, 150, 150), twist=0.6)
    # exhaust plug
    meshes.append(T.revolve([(0.7, 2.6), (0.5, 3.2), (0.08, 3.9), (0.0, 3.95)], seg=32, axis="x", color=(120, 128, 150)))
    cam = T.Camera(yaw=yaw, pitch=pitch, dist=15.0, fov_px=1500, target=(-0.2, 0, 0), center_px=(540, 470))
    anchors = {
        "fan": (-3.25, 1.5, 0), "compressor": (-1.2, 0.85, 0), "combustor": (0.65, 0.85, 0),
        "turbine": (1.95, 0.85, 0), "nozzle": (3.2, 0.6, 0), "intake": (-4.2, 0.9, 0),
    }
    air = AIR
    paths = {
        "bypass": ([(-5.2, 1.5, 0), (-3.4, 1.45, 0), (-1.0, 1.45, 0), (2.5, 1.45, 0), (4.3, 1.4, 0)], air),
        "core": ([(-5.2, 0.8, 0), (-3.4, 0.8, 0), (-1.9, 0.78, 0), (-0.5, 0.82, 0), (0.0, 0.83, 0), (1.3, 0.83, 0),
                  (2.2, 0.83, 0), (3.2, 0.5, 0), (4.4, 0.3, 0)], air),
    }
    return ModelFrame(meshes, cam, anchors, paths, {"stage": stage})


def core_temp_color(x: float) -> tuple:
    """Gas colour along the core path of the turbofan (x in model units)."""
    if x < -3.0:
        return AIR
    if x < -0.5:
        return lerp_color(AIR, HOT, (x + 3.0) / 2.5 * 0.8)
    if x < 0.0:
        return lerp_color((200, 200, 120), HOT, (x + 0.5) / 0.5)
    if x < 1.3:
        return lerp_color(HOT, FIRE, (x - 0.0) / 1.3)
    return lerp_color(FIRE, EXH, clamp((x - 1.3) / 2.8))
