"""Personajes originales con rig de esqueleto (vista frontal, estilo plano)."""
from __future__ import annotations

import math

from .gfx import (C, P, circ, oval, line, rect, poly, curve, shadow, shade,
                  clamp, lerp, smooth)

import skia

STYLES = {
    # Mateo: el cajero protagonista (polo verde, gafas redondas, pelo oscuro)
    "mateo": dict(skin="#D8A06E", hair="#2A1B14", hair_style="messy",
                  top="#2FA36B", pants="#27344A", shoes="#1B1B22",
                  glasses=True, nametag=True, w=1.0),
    # Sr. Ramírez: gerente (traje gris, corbata roja, bigote, canas)
    "ramirez": dict(skin="#E7B48C", hair="#9A9AA3", hair_style="bald",
                    top="#F1F1F4", vest="#4B5563", pants="#2B2F3A",
                    shoes="#15151A", mustache=True, tie="#C0392B", w=1.18),
    # Darío: empleado del fraude (gorra amarilla, mirada esquiva)
    "dario": dict(skin="#C98F63", hair="#1A1410", hair_style="slick",
                  top="#2FA36B", pants="#3A3A44", shoes="#1B1B22",
                  cap="#F2B632", nametag=True, w=1.0),
    # Clientes y personal de fondo
    "clienta": dict(skin="#F0C19A", hair="#6B3A22", hair_style="long",
                    top="#8E5BC7", pants="#36507A", shoes="#6B2E2E", w=0.95,
                    female=True),
    "cliente": dict(skin="#B77A52", hair="#111111", hair_style="short",
                    top="#3B82C4", pants="#4A4A52", shoes="#222222", w=1.05),
    "lupe": dict(skin="#E2AB80", hair="#4A2A1A", hair_style="ponytail",
                 top="#2FA36B", pants="#27344A", shoes="#1B1B22", w=0.95,
                 female=True, nametag=True),
    "repo": dict(skin="#D9A877", hair="#5C3B22", hair_style="short",
                 top="#2FA36B", pants="#3A3A44", shoes="#1B1B22", w=1.08,
                 nametag=True),
    "guardia": dict(skin="#CF9A70", hair="#1A1A1A", hair_style="short",
                    top="#1F3A5F", pants="#1B2638", shoes="#111111",
                    cap="#1F3A5F", w=1.15, badge=True),
}


def _limb(cv, x0, y0, ang1, l1, ang2, l2, w, color, hand=None, hand_color=None):
    """Brazo/pierna de dos segmentos. ángulos absolutos en grados; 0 = abajo."""
    a1, a2 = math.radians(ang1), math.radians(ang2)
    x1, y1 = x0 + math.sin(a1) * l1, y0 + math.cos(a1) * l1
    x2, y2 = x1 + math.sin(a2) * l2, y1 + math.cos(a2) * l2
    line(cv, x0, y0, x1, y1, color, w)
    line(cv, x1, y1, x2, y2, color, w * 0.92)
    if hand:
        circ(cv, x2, y2, hand, hand_color or color)
    return x1, y1, x2, y2


def _hair_back(cv, st, hx, hy, R):
    h = st["hair"]
    if st.get("hair_style") == "long":
        poly(cv, [(hx - R * 1.02, hy - R * 0.2), (hx + R * 1.02, hy - R * 0.2),
                  (hx + R * 1.1, hy + R * 1.5), (hx - R * 1.1, hy + R * 1.5)], h)
        oval(cv, hx, hy - R * 0.1, R * 1.05, R * 1.1, h)
    elif st.get("hair_style") == "ponytail":
        oval(cv, hx + R * 1.1, hy + R * 0.5, R * 0.34, R * 0.85, h)


def _hair_front(cv, st, hx, hy, R):
    h = st["hair"]
    hs = st.get("hair_style", "short")
    if st.get("cap"):
        cap = st["cap"]
        path = skia.Path()
        path.addArc(skia.Rect.MakeXYWH(hx - R * 1.02, hy - R * 1.12, R * 2.04, R * 1.9), 180, 180)
        path.close()
        cv.drawPath(path, P(cap))
        rect(cv, hx - R * 1.02, hy - R * 0.22, R * 2.04, R * 0.2, shade(cap, -0.18), r=8)
        poly(cv, [(hx - R * 0.2, hy - R * 0.2), (hx + R * 1.5, hy - R * 0.12),
                  (hx + R * 1.5, hy + R * 0.02), (hx - R * 0.2, hy - R * 0.02)], shade(cap, -0.12))
        return
    if hs == "bald":
        oval(cv, hx - R * 1.0, hy + R * 0.05, R * 0.2, R * 0.35, h)
        oval(cv, hx + R * 1.0, hy + R * 0.05, R * 0.2, R * 0.35, h)
        path = skia.Path()
        path.addArc(skia.Rect.MakeXYWH(hx - R * 0.85, hy - R * 1.02, R * 1.7, R * 0.9), 180, 180)
        cv.drawPath(path, P(h, 0.0))
        return
    path = skia.Path()
    path.addArc(skia.Rect.MakeXYWH(hx - R * 1.06, hy - R * 1.12, R * 2.12, R * 1.7), 180, 180)
    path.close()
    cv.drawPath(path, P(h))
    if hs == "messy":
        for dx, dy, r in [(-0.7, -1.0, 0.34), (-0.25, -1.18, 0.36), (0.3, -1.15, 0.38), (0.78, -0.95, 0.32)]:
            circ(cv, hx + dx * R, hy + dy * R, r * R, h)
    elif hs == "slick":
        poly(cv, [(hx - R, hy - R * 0.2), (hx + R * 1.0, hy - R * 0.55),
                  (hx + R * 1.05, hy - R * 0.1), (hx - R * 0.3, hy - R * 0.5)], shade(h, 0.08))
    elif hs in ("long", "ponytail"):
        poly(cv, [(hx - R * 1.02, hy - R * 0.1), (hx + R * 0.1, hy - R * 0.7),
                  (hx + R * 1.02, hy - R * 0.1), (hx + R * 1.02, hy - R * 0.5),
                  (hx, hy - R * 1.1), (hx - R * 1.02, hy - R * 0.5)], h)


def draw_character(cv, name, x, y, s=1.0, pose=None, t=0.0, flip=False, mood="neutral",
                   look=(0, 0), holding=None, talk=0.0, alpha=1.0):
    """Dibuja un personaje con los pies en (x, y).

    pose: dict opcional con claves
      walk(fase rad), armL/armR=(ang_sup, ang_inf), lean, bob, head_tilt,
      crouch, legL/legR=(ang)
    holding: callback(cv, handR_xy, handL_xy, s) para dibujar objetos.
    """
    st = STYLES[name]
    pose = pose or {}
    cv.save()
    if alpha < 1:
        cv.saveLayerAlpha(None, int(255 * alpha))
    cv.translate(x, y)
    cv.scale(-s if flip else s, s)

    wk = pose.get("walk")
    bw = st.get("w", 1.0)
    bob = pose.get("bob", 0.0)
    breathe = math.sin(t * 2.1 + (hash(name) % 7)) * 2.0
    if wk is not None:
        bob += abs(math.sin(wk)) * -9
    crouch = pose.get("crouch", 0.0)
    lean = pose.get("lean", 0.0)

    shadow(cv, 0, 4, 82 * bw, 14, 0.28)

    # ------- piernas
    hip_y = -138 + crouch + bob * 0.4
    leg_w = 30
    if wk is not None:
        la = math.sin(wk) * 30
        ra = -math.sin(wk) * 30
        lf = max(0, math.sin(wk)) * 24
        rf = max(0, -math.sin(wk)) * 24
    else:
        la, ra, lf, rf = pose.get("legL", 3), pose.get("legR", -3), 0, 0
    for sx, ang, lift in ((-1, la, lf), (1, ra, rf)):
        px = sx * 24 * bw
        _limb(cv, px, hip_y, ang * 0.9, 68, ang * 0.45, 66 - lift * 0.4, leg_w, st["pants"])
        fx = px + math.sin(math.radians(ang * 0.9)) * 68 + math.sin(math.radians(ang * 0.45)) * (66 - lift * 0.4)
        fy = hip_y + math.cos(math.radians(ang * 0.9)) * 68 + math.cos(math.radians(ang * 0.45)) * (66 - lift * 0.4)
        fy = min(fy, 0) - lift
        oval(cv, fx + 8, fy - 2, 26, 13, st["shoes"])

    # ------- cuerpo
    tx = lean
    ty = hip_y - 6
    th = 150 + breathe * 0.4
    tw = 118 * bw
    torso_top = ty - th
    cv.save()
    cv.translate(tx, 0)
    # brazos traseros (derecho del personaje se dibuja después)
    shoulder_y = torso_top + 30
    armL = pose.get("armL", (8, 4))
    armR = pose.get("armR", (-8, -4))
    if wk is not None:
        armL = (-math.sin(wk) * 26, -math.sin(wk) * 26 + 10)
        armR = (math.sin(wk) * 26, math.sin(wk) * 26 - 10)
        # lado izquierdo de la pantalla = brazo "izquierdo"
        armL, armR = (-armL[0], -armL[1]), (-armR[0], -armR[1])
    sleeve = st["top"]
    skin = st["skin"]
    hl = _limb(cv, -tw / 2 + 4, shoulder_y, armL[0] - 0, 62, armL[1], 58, 27, sleeve)
    # camisa / torso
    top = st["top"]
    rect(cv, -tw / 2, torso_top, tw, th, top, r=34)
    if st.get("vest"):
        rect(cv, -tw / 2 + 2, torso_top + 20, tw - 4, th - 20, st["vest"], r=26)
        poly(cv, [(0, torso_top + 6), (-24, torso_top + 40), (0, torso_top + 130), (24, torso_top + 40)], st["top"])
    if st.get("tie"):
        poly(cv, [(0, torso_top + 12), (-12, torso_top + 28), (0, torso_top + 38), (12, torso_top + 28)], st["tie"])
        poly(cv, [(0, torso_top + 34), (-11, torso_top + 54), (0, torso_top + 112), (11, torso_top + 54)], st["tie"])
    else:
        # cuello en V para polos
        poly(cv, [(-22, torso_top + 4), (22, torso_top + 4), (0, torso_top + 34)], shade(skin, -0.05))
        poly(cv, [(-26, torso_top + 2), (-8, torso_top + 4), (-18, torso_top + 22)], shade(top, 0.18))
        poly(cv, [(26, torso_top + 2), (8, torso_top + 4), (18, torso_top + 22)], shade(top, 0.18))
    if st.get("nametag"):
        rect(cv, tw / 2 - 52, torso_top + 52, 36, 20, "#FFFFFF", r=4)
        rect(cv, tw / 2 - 48, torso_top + 58, 22, 4, "#9AA0A6")
    if st.get("badge"):
        poly(cv, [(tw / 2 - 40, torso_top + 52), (tw / 2 - 20, torso_top + 52),
                  (tw / 2 - 30, torso_top + 78)], "#E8C547")
    # cinturón
    rect(cv, -tw / 2 + 2, ty - 20, tw - 4, 14, shade(st["pants"], -0.25), r=6)

    hr = _limb(cv, tw / 2 - 4, shoulder_y, armR[0], 62, armR[1], 58, 27, sleeve)
    # manos
    lx, ly = hl[2], hl[3]
    rx, ry = hr[2], hr[3]
    circ(cv, lx, ly, 15, skin)
    circ(cv, rx, ry, 15, skin)
    if holding:
        holding(cv, (rx, ry), (lx, ly), s)

    # ------- cabeza
    hx, hy = 0 + pose.get("head_dx", 0), torso_top - 60 + bob * 0.2
    R = 56
    tilt = pose.get("head_tilt", 0.0)
    cv.save()
    cv.translate(hx, hy + R * 0.75)
    cv.rotate(tilt)
    cv.translate(0, -R * 0.75)
    hx2, hy2 = 0, 0
    rect(cv, -16, R * 0.6, 32, 40, shade(skin, -0.08), r=10)  # cuello
    _hair_back(cv, st, hx2, hy2, R)
    oval(cv, hx2 - R * 1.0, hy2 + 4, 10, 15, shade(skin, -0.04))  # orejas
    oval(cv, hx2 + R * 1.0, hy2 + 4, 10, 15, shade(skin, -0.04))
    oval(cv, hx2, hy2, R * 0.98, R * 1.08, skin)
    _hair_front(cv, st, hx2, hy2, R)
    if mood in ("angry", "shock") or st.get("hair_style") == "bald":
        pass
    # ojos
    blink = 1.0
    ph = (t * 0.37 + (hash(name) % 11) * 0.31) % 1.0
    if ph < 0.025:
        blink = 0.1
    ex = 0.42 * R
    ey = hy2 + 2
    lxo, lyo = look
    narrow = 0.55 if mood in ("focus", "smirk") else 1.0
    wide = 1.25 if mood in ("shock",) else 1.0
    for sx in (-1, 1):
        cx_ = sx * ex
        oval(cv, cx_, ey, 13 * wide, 15 * blink * narrow * wide, "#FFFFFF")
        circ(cv, cx_ + lxo * 5, ey + lyo * 4, 6.5 * (0.8 if mood == "shock" else 1), "#1A1A22")
        if blink < 1:
            line(cv, cx_ - 13, ey, cx_ + 13, ey, "#1A1A22", 3)
    # cejas
    br = {"neutral": (0, 0), "angry": (14, -5), "worry": (-12, 8), "shock": (-6, -10),
          "focus": (10, 2), "smirk": (6, -6), "smile": (-2, -3), "sad": (-14, 6)}.get(mood, (0, 0))
    for sx in (-1, 1):
        cx_ = sx * ex
        y0 = ey - 28 + br[1]
        a = br[0] * sx
        line(cv, cx_ - 13, y0 + a * 0.3, cx_ + 13, y0 - a * 0.3, st["hair"] if st.get("hair_style") != "bald" else "#7D7D86", 5)
    if st.get("glasses"):
        for sx in (-1, 1):
            circ(cv, sx * ex, ey, 21, "#0F1115", style="stroke", w=4)
        line(cv, -ex + 21, ey, ex - 21, ey, "#0F1115", 4)
    # nariz
    oval(cv, lxo * 3, hy2 + 22, 8, 6, shade(skin, -0.12))
    if st.get("mustache"):
        poly(cv, [(-34, hy2 + 38), (-4, hy2 + 31), (0, hy2 + 38), (4, hy2 + 31), (34, hy2 + 38),
                  (20, hy2 + 48), (0, hy2 + 42), (-20, hy2 + 48)], "#8A8A93")
    # boca
    my = hy2 + 52
    op = clamp(talk)
    if mood == "shock":
        oval(cv, 0, my + 4, 14, 18, "#4A1D1D")
    elif mood in ("smile", "smirk"):
        path = skia.Path()
        path.moveTo(-20, my - 2)
        path.quadTo(0, my + (22 if mood == "smile" else 12), 20 if mood == "smile" else 24, my - (2 if mood == "smile" else 8))
        cv.drawPath(path, P("#4A1D1D", 1, "stroke", 5))
    elif mood in ("worry", "sad"):
        path = skia.Path()
        path.moveTo(-18, my + 8)
        path.quadTo(0, my - 8, 18, my + 8)
        cv.drawPath(path, P("#4A1D1D", 1, "stroke", 5))
    elif mood == "angry":
        line(cv, -18, my + 4, 18, my + 4, "#4A1D1D", 6)
    elif op > 0.05:
        oval(cv, 0, my + 3, 13, 5 + 10 * op, "#4A1D1D")
    else:
        line(cv, -14, my + 2, 14, my + 2, "#4A1D1D", 5)
    cv.restore()   # cabeza
    cv.restore()   # cuerpo
    if alpha < 1:
        cv.restore()
    cv.restore()
    return dict(head=(x + hx * (-s if flip else s), y + (hy - 10) * s), hand=(x + rx * (-s if flip else s), y + ry * s))
