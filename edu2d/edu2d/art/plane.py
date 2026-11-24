"""Avión comercial, motor en corte, moléculas, cristales de hielo y estelas."""
import math
import random
from ..core import n


def airliner(t, bob=True, engine_glow=True):
    """Vista lateral, mira a la derecha, origen = centro del fuselaje (longitud ≈ 560)."""
    out = ""
    # cola: estabilizador horizontal (detrás), deriva vertical grande y cono de cola
    out += ('<polygon points="-232,-4 -186,-4 -292,40 -352,40" fill="#CFD8E6" stroke="#5B6578" stroke-width="3"/>'
            '<polygon points="-196,-40 -292,-176 -338,-176 -322,-22" fill="#1F7AE0" stroke="#10305F" stroke-width="4"/>'
            '<polygon points="-262,-126 -296,-174 -331,-174 -318,-132" fill="#FFD43B" opacity=".95"/>'
            '<circle cx="-300" cy="-150" r="9" fill="#fff" opacity=".9"/>')
    # ala (en perspectiva) y motor
    out += ('<polygon points="-20,20 50,20 -105,112 -170,112" fill="#E9EEF6" stroke="#5B6578" stroke-width="4"/>'
            '<polygon points="-170,112 -105,112 -112,124 -182,124" fill="#B8C2D4" stroke="#5B6578" stroke-width="3"/>')
    out += ('<rect x="-26" y="80" width="12" height="26" fill="#9AA6BA"/>'
            '<path d="M-84,106 L22,106 Q36,106 36,124 Q36,142 22,142 L-84,142 Q-96,142 -96,124 Q-96,106 -84,106 Z" fill="#F5F7FB" stroke="#5B6578" stroke-width="4"/>'
            '<ellipse cx="34" cy="124" rx="7" ry="17" fill="#1B2438"/>'
            f'<ellipse cx="-92" cy="124" rx="6" ry="14" fill="#7C8AA6"/>')
    # fuselaje con cono de cola ascendente
    out += ('<path d="M-346,-26 Q-352,-12 -330,-2 L-210,36 L180,38 Q268,30 288,-4 Q268,-40 180,-46 L-200,-46 Q-330,-44 -346,-26 Z" fill="#fff" stroke="#5B6578" stroke-width="4"/>'
            '<path d="M-330,-8 L-230,24 L268,18 L262,4 L-230,10 Z" fill="#1F7AE0" opacity=".95"/>'
            '<rect x="-352" y="-24" width="14" height="10" rx="4" fill="#9AA6BA" stroke="#5B6578" stroke-width="2"/>'
            '<path d="M196,-40 Q250,-38 272,-6 L212,-6 Z" fill="#2B3A55" stroke="#5B6578" stroke-width="2"/>')
    for i in range(18):
        out += f'<rect x="{-220 + i*17}" y="-22" width="8" height="11" rx="3" fill="#2B3A55"/>'
    out += '<ellipse cx="-90" cy="-4" rx="2" ry="2" fill="#fff"/>'
    return out


def engine_cutaway(t, hot=1.0):
    """Motor en corte (origen centro, longitud 460, mira a la derecha)."""
    out = ('<path d="M-230,-70 Q-246,0 -230,70 L110,56 L228,36 L228,-36 L110,-56 Z" fill="#E4E9F2" stroke="#5B6578" stroke-width="6"/>'
           '<path d="M-214,-56 L100,-44 L100,44 L-214,56 Z" fill="#2B3447"/>')
    # fan: barras que "giran" visto de lado
    for i in range(7):
        y = -52 + ((i * 17 + t * 520) % 104)
        out += f'<rect x="-200" y="{y:.0f}" width="16" height="9" rx="3" fill="#C9D3E6"/>'
    # compresor / cámara de combustión / turbina
    out += '<polygon points="-170,-48 -60,-30 -60,30 -170,48" fill="#5B6B8C" opacity=".75"/>'
    fl = .75 + .25 * math.sin(t * 22)
    out += (f'<rect x="-60" y="-30" width="90" height="60" rx="14" fill="#FF7A1A" opacity="{.85*hot:.2f}"/>'
            f'<ellipse cx="-15" cy="0" rx="{44*fl:.0f}" ry="{22*fl:.0f}" fill="#FFD43B" opacity="{.9*hot:.2f}"/>')
    for i in range(4):
        out += f'<rect x="{40 + i*14}" y="-26" width="6" height="52" fill="#9AA6BA"/>'
    return out


def molecule(x, y, s=1.0, rot=0.0, hot=True):
    """H2O: oxígeno rojo + 2 hidrógenos blancos."""
    c = "#FF5C5C" if hot else "#7CD3FF"
    return (f'<g transform="translate({x:.1f},{y:.1f}) rotate({rot:.0f}) scale({s})">'
            '<circle cx="-13" cy="-11" r="7" fill="#fff" stroke="#8892A8" stroke-width="1.5"/><circle cx="13" cy="-11" r="7" fill="#fff" stroke="#8892A8" stroke-width="1.5"/>'
            f'<circle cx="0" cy="0" r="13" fill="{c}" stroke="#7A1A12" stroke-width="2"/></g>')


def crystal(x, y, r, rot=0.0, op=1.0):
    """Cristal de hielo hexagonal con rayos."""
    pts = " ".join(f"{x + r*math.cos(math.radians(rot + 60*k)):.1f},{y + r*math.sin(math.radians(rot + 60*k)):.1f}" for k in range(6))
    out = f'<polygon points="{pts}" fill="#E8FAFF" stroke="#7CD3FF" stroke-width="{max(2, r*.12):.1f}" opacity="{op:.2f}"/>'
    for k in range(3):
        a = math.radians(rot + 60 * k)
        out += (f'<line x1="{x - r*.85*math.cos(a):.1f}" y1="{y - r*.85*math.sin(a):.1f}" x2="{x + r*.85*math.cos(a):.1f}" y2="{y + r*.85*math.sin(a):.1f}" '
                f'stroke="#9FE3FF" stroke-width="{max(1.5, r*.07):.1f}" opacity="{op:.2f}"/>')
    return out


def sparkle(x, y, r, t, k=0):
    a = .5 + .5 * math.sin(t * 6 + k)
    return (f'<g opacity="{a:.2f}"><line x1="{x-r}" y1="{y}" x2="{x+r}" y2="{y}" stroke="#fff" stroke-width="3" stroke-linecap="round"/>'
            f'<line x1="{x}" y1="{y-r}" x2="{x}" y2="{y+r}" stroke="#fff" stroke-width="3" stroke-linecap="round"/></g>')


def trail(x_plane, y, t, speed, mode="persist", x_left=-80, seed=1, grow=1.0):
    """Estela como nube de bolitas detrás del avión. mode: 'persist' (se extiende) | 'dry' (desaparece) | 'young' (recién formada)."""
    rnd = random.Random(seed)
    out = ""
    x = x_plane - 30
    i = 0
    while x > x_left:
        age = (x_plane - x) / speed
        j = rnd.uniform(-1, 1); j2 = rnd.uniform(-1, 1)
        if mode == "dry":
            op = max(0.0, 1 - age / 1.6)
            w = 7 + 5 * age
        elif mode == "young":
            op = min(1.0, age * 3) * .95
            w = 6 + 6 * age
        else:
            op = min(1.0, age * 2.5) * (.92 if age < 6 else .85)
            w = (7 + 20 * age ** .8) * grow
        if op > .02:
            yy = y + j * w * .7 + 6 * math.sin(i * .5 + t)
            out += f'<circle cx="{x:.0f}" cy="{yy:.1f}" r="{w*(.9+.25*j2):.1f}" fill="#fff" opacity="{op*.8:.2f}"/>'
        x -= 11
        i += 1
    return out
