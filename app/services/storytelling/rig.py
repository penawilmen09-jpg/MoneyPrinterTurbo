"""Rig 2D procedural de personajes cartoon (Pillow).

Un personaje se dibuja SIEMPRE a partir de su :class:`CharacterSpec`; las
poses (brazos, piernas, cabeza, boca, ojos) sólo cambian ángulos, nunca la
ficha visual.  Eso garantiza la consistencia entre escenas.

Sistema de coordenadas del rig (unidades): altura del personaje = 1000,
y=0 en la coronilla, y=1000 en los pies, x=0 en el eje central.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from PIL import Image, ImageDraw

from .models import CharacterSpec

OUTLINE = (34, 28, 44)
Color = tuple[int, int, int]


def shade(c: Color, f: float) -> Color:
    return tuple(max(0, min(255, int(v * f))) for v in c)  # type: ignore[return-value]


def mix(a: Color, b: Color, t: float) -> Color:
    return tuple(int(a[i] * (1 - t) + b[i] * t) for i in range(3))  # type: ignore[return-value]


# --------------------------------------------------------------------------
# Pose
# --------------------------------------------------------------------------
@dataclass
class Pose:
    bob: float = 0.0  # desplazamiento vertical del cuerpo (unidades)
    lean: float = 0.0  # inclinación del torso (unidades de desplazamiento en hombros)
    head_tilt: float = 0.0  # grados
    head_turn: float = 0.0  # -1 (izq) .. 1 (der), en coordenadas de pantalla
    arm_l: tuple[float, float] = (-8.0, -8.0)  # rig-space: arm_l = brazo trasero (-x), arm_r = delantero (+x)
    arm_r: tuple[float, float] = (8.0, 8.0)  # ángulos absolutos (hombro, codo), 0=abajo, +=hacia +x
    leg_l: tuple[float, float] = (0.0, 0.0)
    leg_r: tuple[float, float] = (0.0, 0.0)
    # cara
    eye_x: float = 0.0  # mirada -1..1
    eye_y: float = 0.0
    blink: float = 0.0  # 0 abierto .. 1 cerrado
    brow_l: float = 0.0  # + = ceja interior arriba (preocupado), - = enfadado
    brow_r: float = 0.0
    brow_lift: float = 0.0  # + sube ambas cejas
    mouth_open: float = 0.0  # 0..1
    mouth_curve: float = 0.0  # -1 triste .. 1 sonrisa
    mouth_wide: float = 1.0
    eye_open: float = 1.0  # 0.5 = entrecerrados (sospecha)
    sweat: bool = False
    blush: float = 0.0


@dataclass
class Anchors:
    hand_front: tuple[float, float] = (0, 0)
    hand_back: tuple[float, float] = (0, 0)
    head: tuple[float, float] = (0, 0)
    mouth: tuple[float, float] = (0, 0)
    feet: tuple[float, float] = (0, 0)
    top: tuple[float, float] = (0, 0)
    bbox: tuple[float, float, float, float] = (0, 0, 0, 0)
    extra: dict = field(default_factory=dict)


EXPRESSION_PRESETS: dict[str, dict] = {
    "neutral": dict(mouth_curve=0.15, brow_l=0, brow_r=0, brow_lift=0, eye_open=1.0),
    "happy": dict(mouth_curve=1.0, mouth_open=0.35, brow_lift=0.4, eye_open=0.9, blush=0.5),
    "surprised": dict(mouth_curve=0.0, mouth_open=0.8, brow_lift=1.0, eye_open=1.25, mouth_wide=0.55),
    "worried": dict(mouth_curve=-0.5, brow_l=0.9, brow_r=-0.9, brow_lift=0.3, eye_open=1.05, sweat=True),
    "angry": dict(mouth_curve=-0.8, brow_l=-1.0, brow_r=1.0, brow_lift=-0.3, eye_open=0.85),
    "suspicious": dict(mouth_curve=-0.1, brow_l=-0.6, brow_r=0.0, brow_lift=0.1, eye_open=0.55),
    "thinking": dict(mouth_curve=-0.1, brow_l=0.3, brow_r=-0.2, brow_lift=0.5, eye_open=0.95),
    "sad": dict(mouth_curve=-0.9, brow_l=1.0, brow_r=-1.0, brow_lift=0.2, eye_open=0.85),
    "smug": dict(mouth_curve=0.7, brow_l=-0.3, brow_r=0.2, brow_lift=0.2, eye_open=0.65),
}


def apply_expression(pose: Pose, name: str, intensity: float = 1.0) -> Pose:
    preset = EXPRESSION_PRESETS.get(name, EXPRESSION_PRESETS["neutral"])
    for k, v in preset.items():
        if isinstance(v, bool):
            setattr(pose, k, v and intensity > 0.5)
        elif k == "mouth_wide":
            setattr(pose, k, 1.0 + (v - 1.0) * intensity)
        elif k == "eye_open":
            setattr(pose, k, 1.0 + (v - 1.0) * intensity)
        elif k == "mouth_open":
            pose.mouth_open = max(pose.mouth_open, v * intensity)
        else:
            setattr(pose, k, v * intensity)
    return pose


def _fk(shoulder, a1, a2, l1, l2):
    """Cinemática directa 2 segmentos. Ángulo 0 = hacia abajo, + = hacia +x."""
    r1, r2 = math.radians(a1), math.radians(a2)
    elbow = (shoulder[0] + l1 * math.sin(r1), shoulder[1] + l1 * math.cos(r1))
    hand = (elbow[0] + l2 * math.sin(r2), elbow[1] + l2 * math.cos(r2))
    return elbow, hand


def _ellipse_points(cx, cy, rx, ry, a0, a1, n=24):
    pts = []
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        pts.append((cx + rx * math.cos(a), cy + ry * math.sin(a)))
    return pts


class _Ctx:
    """Contexto de dibujo: transforma unidades del rig a píxeles del lienzo."""

    def __init__(self, draw, ox, oy, s, facing, ss):
        self.d = draw
        self.ox, self.oy, self.s, self.f, self.ss = ox, oy, s, facing, ss

    def p(self, x, y):
        return ((self.ox + self.f * x * self.s), (self.oy + y * self.s))

    def pts(self, seq):
        return [self.p(x, y) for x, y in seq]

    def w(self, units):
        return max(1, int(round(units * self.s)))

    def line_w(self):
        return max(2, int(round(7 * self.s)))

    def ellipse(self, cx, cy, rx, ry, fill, outline=True, width=None):
        x, y = self.p(cx, cy)
        rxs, rys = rx * self.s, ry * self.s
        self.d.ellipse(
            [x - rxs, y - rys, x + rxs, y + rys],
            fill=fill,
            outline=OUTLINE if outline else None,
            width=(width or self.line_w()) if outline else 0,
        )

    def poly(self, pts, fill, outline=True):
        P = self.pts(pts)
        self.d.polygon(P, fill=fill)
        if outline:
            self.d.line(P + [P[0]], fill=OUTLINE, width=self.line_w(), joint="curve")

    def limb(self, p0, p1, width, fill, outline=True):
        a, b = self.p(*p0), self.p(*p1)
        wpx = width * self.s
        ow = wpx + self.line_w() * 1.6
        if outline:
            self.d.line([a, b], fill=OUTLINE, width=int(ow))
            for q in (a, b):
                self.d.ellipse([q[0] - ow / 2, q[1] - ow / 2, q[0] + ow / 2, q[1] + ow / 2], fill=OUTLINE)
        self.d.line([a, b], fill=fill, width=int(wpx))
        for q in (a, b):
            self.d.ellipse([q[0] - wpx / 2, q[1] - wpx / 2, q[0] + wpx / 2, q[1] + wpx / 2], fill=fill)

    def arc(self, pts, width, color=OUTLINE):
        P = self.pts(pts)
        self.d.line(P, fill=color, width=max(1, int(width * self.s)), joint="curve")
        r = max(1, int(width * self.s / 2))
        for q in (P[0], P[-1]):
            self.d.ellipse([q[0] - r, q[1] - r, q[0] + r, q[1] + r], fill=color)


_BUILD_W = {"slim": 0.88, "average": 1.0, "stocky": 1.18}


def draw_character(
    spec: CharacterSpec,
    pose: Pose,
    *,
    origin: tuple[float, float],
    scale: float,
    facing: int,
    canvas_box: tuple[int, int, int, int],
    ss: int = 2,
) -> tuple[Image.Image, Anchors]:
    """Dibuja el personaje y devuelve (capa RGBA del tamaño de ``canvas_box``, anclas).

    ``origin`` = posición en pantalla de los pies (x centro, y suelo).
    ``scale``  = píxeles de pantalla por unidad de rig (altura 1000 u).
    ``canvas_box`` = (x0, y0, x1, y1) región de pantalla a producir.
    Las anclas se devuelven en coordenadas de pantalla.
    """
    spec = spec.normalized()
    x0, y0, x1, y1 = canvas_box
    cw, ch = x1 - x0, y1 - y0
    layer = Image.new("RGBA", (cw * ss, ch * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    s = scale * spec.height * ss
    ox = (origin[0] - x0) * ss
    # y=0 del rig es la coronilla: calculamos desde los pies
    oy = (origin[1] - y0) * ss - 1000 * s
    c = _Ctx(d, ox, oy, s, facing, ss)

    bw = _BUILD_W[spec.build]
    skin = spec.skin
    skin_sh = shade(skin, 0.86)
    top = spec.top_color
    top_sh = shade(top, 0.82)
    bottom = spec.bottom_color
    accent = spec.accent_color
    hair = spec.hair_color
    bob = pose.bob
    lean = pose.lean

    hip_y = 632 + bob
    sh_y = 330 + bob + abs(lean) * 0.05
    sh_dx = 92 * bw
    # ---- anclas de hombro ---------------------------------------------------
    sh_l = (-sh_dx + lean, sh_y + 20)  # "l"/"r" = lado izquierdo/derecho de la pantalla (sin flip)
    sh_r = (sh_dx + lean, sh_y + 20)

    # ---- piernas ------------------------------------------------------------
    leg_w = 62 * (0.95 + 0.1 * bw)
    hips = [(-40 * bw, hip_y), (40 * bw, hip_y)]
    foot_pos = []
    legs = []
    for (hx, hy), (a1, a2) in zip(hips, (pose.leg_l, pose.leg_r)):
        knee, foot = _fk((hx, hy), a1, a2, 172, 176)
        # los pies no pueden atravesar el suelo (1000)
        legs.append(((hx, hy), knee, foot))
        foot_pos.append(foot)
    # el cuerpo se ancla al suelo: el pie más bajo toca y=1000
    drop = 1000 - max(f[1] for f in foot_pos) - 14
    # (si el personaje flota por bob, mantenemos la referencia fija; no corregimos)
    for hip, knee, foot in legs:
        # pantalón
        c.limb(hip, knee, leg_w, bottom)
        c.limb(knee, foot, leg_w * 0.92, bottom)
        # zapato
        fx, fy = foot
        c.poly(
            [(fx - 34, fy - 4), (fx + 56, fy - 4), (fx + 64, fy + 20), (fx - 38, fy + 20)],
            spec.shoes_color,
        )
    if spec.outfit == "dress":
        c.poly(
            [(-80 * bw, hip_y - 20), (80 * bw, hip_y - 20), (120 * bw, hip_y + 190), (-120 * bw, hip_y + 190)],
            top,
        )

    # ---- brazo de atrás (se dibuja antes del torso) ------------------------------
    def draw_arm(sh, angles, front: bool):
        a1, a2 = angles
        elbow, hand = _fk(sh, a1, a2, 150, 140)
        sleeve_long = spec.outfit in ("shirt", "suit", "labcoat", "hoodie", "uniform")
        arm_w = 54 * (0.95 + 0.1 * bw)
        if sleeve_long:
            c.limb(sh, elbow, arm_w, top)
            c.limb(elbow, hand, arm_w * 0.9, top if spec.outfit != "uniform" else top)
            # puño
            hx, hy = hand
            c.ellipse(hx, hy, 33, 33, skin)
        else:
            c.limb(sh, elbow, arm_w, top)
            c.limb(elbow, hand, arm_w * 0.82, skin)
            hx, hy = hand
            c.ellipse(hx, hy, 33, 33, skin)
        return hand

    # rig-space: el personaje siempre mira a +x; el flip se aplica en c.p().
    hand_back = draw_arm(sh_l, pose.arm_l, False)

    # pelvis (une el torso con las piernas)
    c.poly([(-84 * bw + lean * .3, hip_y - 30), (84 * bw + lean * .3, hip_y - 30),
            (78 * bw, hip_y + 62), (-78 * bw, hip_y + 62)], bottom)

    # ---- torso --------------------------------------------------------------
    t_top_w = 100 * bw
    t_bot_w = 88 * bw
    torso = [
        (-t_top_w + lean, sh_y + 10), (t_top_w + lean, sh_y + 10),
        (t_bot_w + lean * 0.3, hip_y + 24), (-t_bot_w + lean * 0.3, hip_y + 24),
    ]
    # esquinas redondeadas con puntos extra
    rt = []
    for (px, py), (qx, qy) in zip(torso, torso[1:] + torso[:1]):
        rt.append((px + (qx - px) * 0.12, py + (qy - py) * 0.12))
        rt.append((px + (qx - px) * 0.88, py + (qy - py) * 0.88))
    torso_col = top if spec.outfit != "apron" else mix(top, (250, 250, 250), 0.1)
    c.poly(rt, torso_col)
    # cuello
    c.ellipse(lean * 0.8, sh_y - 18, 32, 38, skin_sh)

    # detalles de ropa
    if spec.outfit in ("shirt", "suit", "uniform", "labcoat"):
        # cuello de camisa / solapas
        v = [(-34 + lean, sh_y + 4), (0 + lean, sh_y + 80), (34 + lean, sh_y + 4)]
        c.poly(v, mix(skin, top, 0.0) if spec.outfit != "labcoat" else (240, 240, 245), outline=True)
        if spec.outfit == "suit":
            c.poly([(-34 + lean, sh_y + 4), (-80 + lean, sh_y + 40), (-14 + lean, sh_y + 150)], shade(top, 0.8))
            c.poly([(34 + lean, sh_y + 4), (80 + lean, sh_y + 40), (14 + lean, sh_y + 150)], shade(top, 0.8))
            c.poly([(-26 + lean, sh_y + 6), (26 + lean, sh_y + 6), (0 + lean, sh_y + 90)], (245, 245, 248))
        if spec.outfit == "labcoat":
            c.poly([(-40 + lean, sh_y + 6), (40 + lean, sh_y + 6), (0 + lean, sh_y + 100)], mix(top, (255, 255, 255), 0.6))
        if "tie" in spec.accessories or spec.outfit == "suit":
            tie = accent if "tie" in spec.accessories else shade(accent, 0.8)
            c.poly([(-14 + lean, sh_y + 16), (14 + lean, sh_y + 16), (10 + lean, sh_y + 44), (-10 + lean, sh_y + 44)], tie)
            c.poly([(-10 + lean, sh_y + 44), (10 + lean, sh_y + 44), (22 + lean, sh_y + 170), (0 + lean, sh_y + 190), (-22 + lean, sh_y + 170)], tie)
        if spec.outfit == "shirt":
            for k in range(3):
                c.ellipse(lean, sh_y + 110 + k * 45, 6, 6, shade(top, 0.7), outline=False)
    if spec.outfit == "apron":
        ap = accent
        c.poly([(-62 * bw + lean, sh_y + 40), (62 * bw + lean, sh_y + 40), (84 * bw + lean * .3, hip_y + 150), (-84 * bw + lean * .3, hip_y + 150)], ap)
        c.arc([(-52 * bw + lean, sh_y + 40), (-20 + lean, sh_y - 8)], 10, OUTLINE)
        c.arc([(52 * bw + lean, sh_y + 40), (20 + lean, sh_y - 8)], 10, OUTLINE)
        c.poly([(-40 + lean, hip_y + 40), (40 + lean, hip_y + 40), (40 + lean, hip_y + 100), (-40 + lean, hip_y + 100)], shade(ap, 0.88))
    if spec.outfit == "hoodie":
        c.arc([(-60 + lean, sh_y + 6), (-30 + lean, sh_y + 60), (30 + lean, sh_y + 60), (60 + lean, sh_y + 6)], 18, shade(top, 0.8))
    if spec.outfit == "uniform":
        c.poly([(-70 + lean, sh_y + 60), (-30 + lean, sh_y + 60), (-30 + lean, sh_y + 92), (-70 + lean, sh_y + 92)], shade(top, 0.78))
        c.ellipse(52 * bw + lean, sh_y + 90, 24, 28, accent)
    if "badge" in spec.accessories and spec.outfit != "uniform":
        c.poly([(40 * bw + lean, sh_y + 70), (82 * bw + lean, sh_y + 70), (82 * bw + lean, sh_y + 98), (40 * bw + lean, sh_y + 98)], (245, 245, 250))
        c.limb((48 * bw + lean, sh_y + 84), (74 * bw + lean, sh_y + 84), 6, accent, outline=False)
    if "scarf" in spec.accessories:
        c.poly([(-50 + lean, sh_y + 2), (50 + lean, sh_y + 2), (46 + lean, sh_y + 40), (-46 + lean, sh_y + 40)], accent)

    # ---- brazo frontal --------------------------------------------------------
    hand_front = draw_arm(sh_r, pose.arm_r, True)

    # ---- cabeza ---------------------------------------------------------------
    hcx = lean * 1.25 + pose.head_turn * 10 * facing * 0 + 0
    hcy = 150 + bob * 0.9
    tilt = math.radians(pose.head_tilt)
    # la inclinación se aproxima desplazando los rasgos y la parte superior
    tdx = math.sin(tilt) * 40
    rx, ry = 128, 138
    turn = pose.head_turn * facing  # en el espacio del rig (flip ya aplicado)
    fx_off = turn * 34  # desplazamiento de rasgos faciales

    hair_back_styles = ("long", "ponytail", "bun")
    # pelo trasero
    if spec.hair_style == "long":
        c.poly(
            [(-rx - 16 + hcx, hcy - 30), (rx + 16 + hcx, hcy - 30), (rx + 30 + hcx, hcy + 230), (-rx - 30 + hcx, hcy + 230)],
            hair,
        )
    if spec.hair_style == "ponytail":
        c.poly([(rx - 20 + hcx, hcy - 40), (rx + 90 + hcx, hcy + 40), (rx + 70 + hcx, hcy + 190), (rx + hcx, hcy + 60)], hair)
    if spec.hair_style == "bun":
        c.ellipse(hcx + tdx, hcy - ry - 28, 54, 50, hair)
    # orejas
    c.ellipse(-rx + 6 + hcx, hcy + 14, 24, 32, skin_sh)
    c.ellipse(rx - 6 + hcx, hcy + 14, 24, 32, skin_sh)
    if "earrings" in spec.accessories:
        c.ellipse(-rx + 6 + hcx, hcy + 56, 8, 8, accent)
        c.ellipse(rx - 6 + hcx, hcy + 56, 8, 8, accent)
    # cara
    c.ellipse(hcx + tdx * 0.5, hcy, rx, ry, skin)
    # mejillas / sombra mandibular
    c.ellipse(hcx + tdx * 0.5, hcy + ry * 0.55, rx * 0.8, ry * 0.22, shade(skin, 0.94), outline=False)

    # --- pelo frontal ---
    _draw_hair_front(c, spec, hcx + tdx * 0.5, hcy, rx, ry, turn)

    # --- ojos ---
    eye_dx = 52
    eye_y = hcy + 6
    eo = max(0.05, pose.eye_open) * (1.0 - pose.blink)
    for sgn, brow in ((-1, pose.brow_l), (1, pose.brow_r)):
        ex = hcx + tdx * 0.5 + sgn * eye_dx + fx_off
        eh = 34 * min(1.3, eo)
        ew = 30
        if eo < 0.12:
            c.arc([(ex - ew, eye_y), (ex, eye_y + 6), (ex + ew, eye_y)], 7)
        else:
            c.ellipse(ex, eye_y, ew, eh, (255, 255, 255), width=c.line_w())
            # párpado superior entrecerrado (sospecha)
            px = ex + pose.eye_x * 12 * facing
            py = eye_y + pose.eye_y * 10
            c.ellipse(px, py, 15, min(17, eh * 0.7), spec.eye_color, outline=False)
            c.ellipse(px, py, 8, min(9, eh * 0.4), (15, 12, 20), outline=False)
            c.ellipse(px + 5, py - 6, 4.5, 4.5, (255, 255, 255), outline=False)
            if eo < 0.8:
                lid_h = (1 - eo / 0.8) * eh * 1.1
                c.poly(
                    [(ex - ew - 3, eye_y - eh - 3), (ex + ew + 3, eye_y - eh - 3),
                     (ex + ew + 3, eye_y - eh + lid_h * 1.6), (ex, eye_y - eh + lid_h * 1.9),
                     (ex - ew - 3, eye_y - eh + lid_h * 1.6)], skin, outline=False,
                )
                c.arc([(ex - ew, eye_y - eh + lid_h * 1.6), (ex, eye_y - eh + lid_h * 1.9), (ex + ew, eye_y - eh + lid_h * 1.6)], 6)
        # cejas: brow>0 -> extremo interior arriba (preocupado); brow<0 -> enfadado
        by = eye_y - 58 - pose.brow_lift * 18
        inner_y = by - brow * 14
        outer_y = by + brow * 6
        c.limb((ex - sgn * 26, inner_y), (ex + sgn * 30, outer_y), 14,
               shade(hair, 0.75) if spec.hair_style != "bald" else shade(skin, 0.6), outline=False)

    # --- gafas ---
    if "glasses" in spec.accessories:
        for sgn in (-1, 1):
            ex = hcx + tdx * 0.5 + sgn * eye_dx + fx_off
            x, y = c.p(ex, eye_y)
            r = 44 * c.s
            d.ellipse([x - r, y - r * 0.95, x + r, y + r * 0.95], outline=OUTLINE, width=max(2, int(7 * c.s)))
        a = c.p(hcx + tdx * 0.5 - eye_dx + 40 + fx_off, eye_y)
        b = c.p(hcx + tdx * 0.5 + eye_dx - 40 + fx_off, eye_y)
        d.line([a, b], fill=OUTLINE, width=max(2, int(7 * c.s)))

    # --- nariz ---
    nx = hcx + tdx * 0.5 + fx_off * 1.25
    c.ellipse(nx, hcy + 56, 17, 13, shade(skin, 0.88))

    # --- mejillas rubor ---
    if pose.blush > 0.1:
        for sgn in (-1, 1):
            c.ellipse(hcx + tdx * 0.5 + sgn * 84 + fx_off, hcy + 72, 20, 12, mix(skin, (255, 120, 120), 0.45 * pose.blush), outline=False)

    # --- bigote ---
    my = hcy + 92
    mx = hcx + tdx * 0.5 + fx_off * 1.1
    if "mustache" in spec.accessories:
        c.poly(_ellipse_points(mx - 30, hcy + 80, 38, 14, 0, 360, 16), shade(hair, 0.8))
        c.poly(_ellipse_points(mx + 30, hcy + 80, 38, 14, 0, 360, 16), shade(hair, 0.8))

    # --- boca ---
    mw = 46 * pose.mouth_wide
    curve = pose.mouth_curve
    openness = pose.mouth_open
    if openness > 0.08:
        mh = 10 + openness * 40
        top_y = my - curve * 6
        pts = [(mx - mw, top_y), (mx + mw, top_y)]
        # cavidad bucal
        c.poly(
            [(mx - mw, top_y)] + _ellipse_points(mx, top_y, mw, mh + max(0, curve) * 14, 0, 180, 14)[::-1][::-1] + [(mx + mw, top_y)],
            (110, 30, 45),
        )
        # dientes superiores
        c.poly([(mx - mw * 0.8, top_y + 2), (mx + mw * 0.8, top_y + 2), (mx + mw * 0.7, top_y + 11), (mx - mw * 0.7, top_y + 11)], (255, 255, 255), outline=False)
        # lengua
        c.ellipse(mx, top_y + mh * 0.8, mw * 0.5, mh * 0.35, (230, 110, 120), outline=False)
        c.arc([(mx - mw, top_y), (mx, top_y - curve * 8), (mx + mw, top_y)], 6)
    else:
        pts = [(mx - mw, my - curve * 10 * -1 * -1 + 0), (mx, my + curve * 16), (mx + mw, my - curve * 10 * -1 * -1 + 0)]
        pts = [(mx - mw, my - curve * 8), (mx, my + curve * 14), (mx + mw, my - curve * 8)]
        # suavizado cuadrático
        smooth = []
        for i in range(13):
            t = i / 12
            smooth.append((
                (1 - t) ** 2 * pts[0][0] + 2 * (1 - t) * t * pts[1][0] + t ** 2 * pts[2][0],
                (1 - t) ** 2 * pts[0][1] + 2 * (1 - t) * t * pts[1][1] + t ** 2 * pts[2][1],
            ))
        c.arc(smooth, 7)

    # --- barba ---
    if "beard" in spec.accessories:
        c.poly(
            _ellipse_points(hcx + tdx * 0.5, hcy + 20, rx * 0.98, ry * 0.98, 20, 160, 20)
            + _ellipse_points(hcx + tdx * 0.5, hcy + 60, rx * 0.7, ry * 0.5, 160, 20, 14)[::-1][::-1],
            shade(hair, 0.9),
        )
        # reabrimos la boca sobre la barba
        c.arc([(mx - mw, my), (mx, my + 10), (mx + mw, my)], 7, OUTLINE)

    # sudor
    if pose.sweat:
        sx, sy = hcx + tdx * 0.5 + 115, hcy - 60
        c.poly([(sx, sy - 34), (sx + 16, sy), (sx, sy + 16), (sx - 16, sy)], (150, 210, 255))

    # headset (sobre la cabeza)
    if "headset" in spec.accessories:
        c.arc(_ellipse_points(hcx + tdx * 0.5, hcy - 8, rx * 1.02, ry * 1.02, 190, 350, 16), 12, (50, 50, 60))
        c.ellipse(-rx + 4 + hcx, hcy + 20, 26, 38, (50, 50, 60))

    # ---- salida -------------------------------------------------------------------
    if ss > 1:
        layer = layer.resize((cw, ch), Image.LANCZOS)

    def to_screen(x, y):
        px, py = c.p(x, y + drop * 0)  # sin corrección de suelo
        return (x0 + px / ss, y0 + py / ss)

    anchors = Anchors(
        hand_front=to_screen(*hand_front),
        hand_back=to_screen(*hand_back),
        head=to_screen(hcx, hcy),
        mouth=to_screen(mx, my),
        feet=(origin[0], origin[1]),
        top=to_screen(0, 0),
    )
    anchors.bbox = (
        origin[0] - 300 * scale * spec.height, origin[1] - 1010 * scale * spec.height,
        origin[0] + 300 * scale * spec.height, origin[1] + 30 * scale * spec.height,
    )
    return layer, anchors


def _draw_hair_front(c: _Ctx, spec: CharacterSpec, hcx, hcy, rx, ry, turn):
    hair = spec.hair_color
    style = spec.hair_style
    if style == "bald":
        # sólo un poco de pelo lateral
        for sgn in (-1, 1):
            c.ellipse(hcx + sgn * (rx - 6), hcy - 10, 16, 38, hair)
        return
    cap_pts = _ellipse_points(hcx, hcy, rx * 1.05, ry * 1.06, 188, 352, 28)
    if style in ("short", "ponytail", "bun", "long"):
        fringe_y = hcy - ry * 0.52
        fr = [(hcx + rx * 1.02, hcy - ry * 0.2)]
        n = 7
        for i in range(n + 1):
            t = i / n
            x = hcx + rx * 1.0 - t * rx * 2.0 + turn * 8
            y = fringe_y + math.sin(t * math.pi * 3) * 14 + (t - 0.5) ** 2 * 40
            fr.append((x, y))
        fr.append((hcx - rx * 1.02, hcy - ry * 0.2))
        c.poly(cap_pts + fr[::1], hair)
    elif style == "parted":
        fringe = [(hcx + rx * 1.02, hcy - ry * 0.15)]
        for i in range(8):
            t = i / 7
            x = hcx + rx - t * rx * 2.0
            y = hcy - ry * 0.70 + t * (ry * 0.42) + math.sin(t * math.pi) * -10
            fringe.append((x, y))
        fringe.append((hcx - rx * 1.02, hcy - ry * 0.15))
        c.poly(cap_pts + fringe, hair)
        c.limb((hcx - rx * 0.1, hcy - ry * 1.02), (hcx - rx * 0.2, hcy - ry * 0.55), 7, shade(hair, 0.7), outline=False)
    elif style == "curly":
        for i in range(9):
            a = math.radians(190 + i * 20)
            c.ellipse(hcx + math.cos(a) * rx * 1.0, hcy + math.sin(a) * ry * 1.0, 34, 34, hair)
        c.poly(cap_pts + [(hcx - rx * 0.9, hcy - ry * 0.5), (hcx + rx * 0.9, hcy - ry * 0.5)], hair, outline=False)
    elif style == "cap":
        capc = spec.accent_color if spec.outfit != "uniform" else shade(spec.top_color, 0.9)
        c.poly(cap_pts + [(hcx + rx * 1.02, hcy - ry * 0.28), (hcx - rx * 1.02, hcy - ry * 0.28)], capc)
        c.poly([(hcx + rx * 0.2, hcy - ry * 0.3), (hcx + rx * 1.55, hcy - ry * 0.26),
                (hcx + rx * 1.55, hcy - ry * 0.14), (hcx + rx * 0.2, hcy - ry * 0.14)], shade(capc, 0.8))
        c.ellipse(hcx, hcy - ry * 0.75, 18, 14, shade(capc, 0.8), outline=False)
        # pelo bajo la gorra
        for sgn in (-1, 1):
            c.ellipse(hcx + sgn * (rx - 4), hcy - 4, 15, 34, hair)
