"""Paloma protagonista (SVG vectorial, animable por parámetros).

Origen local = punto donde las patas tocan el cable. Mira a la derecha.
"""
import math
from ..core import n


def pigeon(x, y, s=1.0, flip=False, t=0.0, expr="neutral", bob=True,
           wing=None, fly=False, tilt=0.0, shake=0.0, alpha=1.0):
    """expr: neutral|surprised|worried|happy|dizzy.  wing: ángulo (+ = punta arriba)
    o None para reposo.  fly: patas recogidas.  shake: amplitud de temblor."""
    hb = 7 * math.sin(t * 2 * math.pi * 1.1) if bob else 0.0       # cabeceo típico
    hv = 2.5 * abs(math.sin(t * 2 * math.pi * 1.1)) if bob else 0.0
    if wing is None:
        wing = 4 + 2 * math.sin(t * 2.2)
    blink = (t % 3.4) < 0.12 and expr not in ("happy", "dizzy")
    hx, hy = 62 + hb, -150 + hv
    jx = shake * math.sin(t * 90) if shake else 0
    jy = shake * math.cos(t * 77) if shake else 0

    # patas
    if fly:
        legs = ('<path d="M-6,-45 L-34,-18" stroke="#D95F7A" stroke-width="6" stroke-linecap="round"/>'
                '<path d="M12,-45 L-18,-14" stroke="#D95F7A" stroke-width="6" stroke-linecap="round"/>')
    else:
        legs = ('<path d="M-8,-48 L-9,-3" stroke="#D95F7A" stroke-width="7" stroke-linecap="round"/>'
                '<path d="M16,-48 L15,-3" stroke="#C9506B" stroke-width="7" stroke-linecap="round"/>'
                '<path d="M-24,-6 Q-9,-16 8,-6" stroke="#D95F7A" stroke-width="6" fill="none" stroke-linecap="round"/>'
                '<path d="M0,-6 Q15,-16 32,-6" stroke="#C9506B" stroke-width="6" fill="none" stroke-linecap="round"/>')

    tail = ('<path d="M-52,-92 L-142,-70 L-136,-104 L-120,-112 L-52,-108 Z" fill="#59668A"/>'
            '<path d="M-60,-98 L-134,-88 M-60,-92 L-130,-76" stroke="#46526F" stroke-width="3"/>')

    body = ('<ellipse cx="0" cy="-88" rx="70" ry="46" fill="url(#body)"/>'
            '<ellipse cx="14" cy="-70" rx="48" ry="26" fill="#C6CFDF" opacity=".75"/>'
            f'<path d="M20,-120 Q{n(hx-6)},-125 {n(hx-8)},{n(hy+22)} L{n(hx+26)},{n(hy+22)} Q58,-96 52,-96 Z" fill="#8795B0"/>'
            '<circle cx="46" cy="-108" r="34" fill="url(#neck)" opacity=".92"/>')

    # ojo según expresión
    ex, ey = hx + 10, hy - 4
    if expr == "happy":
        eye = (f'<path d="M{n(ex-9)},{n(ey+2)} Q{n(ex)},{n(ey-10)} {n(ex+9)},{n(ey+2)}" '
               'stroke="#2B2233" stroke-width="4.5" fill="none" stroke-linecap="round"/>')
    elif expr == "dizzy":
        eye = (f'<path d="M{n(ex-8)},{n(ey-8)} L{n(ex+8)},{n(ey+8)} M{n(ex+8)},{n(ey-8)} L{n(ex-8)},{n(ey+8)}" '
               'stroke="#2B2233" stroke-width="4.5" stroke-linecap="round"/>')
    else:
        r = 11 if expr == "surprised" else 9
        pr = 3.6 if expr == "surprised" else 4.8
        sy = 0.12 if blink else 1.0
        eye = (f'<g transform="translate({n(ex)},{n(ey)}) scale(1,{sy})">'
               f'<circle r="{r}" fill="#F7A531"/><circle r="{r-3.2}" fill="#E8741C"/>'
               f'<circle r="{pr}" fill="#1B1423"/><circle cx="-2" cy="-2.5" r="1.8" fill="#fff"/></g>')
    brow = ""
    if expr == "surprised":
        brow = f'<path d="M{n(ex-10)},{n(ey-17)} Q{n(ex)},{n(ey-25)} {n(ex+10)},{n(ey-17)}" stroke="#4A5575" stroke-width="4" fill="none" stroke-linecap="round"/>'
    elif expr == "worried":
        brow = f'<path d="M{n(ex-10)},{n(ey-13)} L{n(ex+10)},{n(ey-22)}" stroke="#4A5575" stroke-width="4.5" stroke-linecap="round"/>'

    open_ = 7 if expr in ("surprised",) else 0
    beak = (f'<path d="M{n(hx+22)},{n(hy-6)} L{n(hx+52)},{n(hy+2)} L{n(hx+22)},{n(hy+5)} Z" fill="#CBD1DC"/>'
            f'<path d="M{n(hx+22)},{n(hy+5)} L{n(hx+48)},{n(hy+4+open_)} L{n(hx+22)},{n(hy+11+open_)} Z" fill="#B3BAC9"/>'
            f'<ellipse cx="{n(hx+24)}" cy="{n(hy-4)}" rx="7" ry="5" fill="#F4F4F7"/>')
    head = (f'<circle cx="{n(hx)}" cy="{n(hy)}" r="29" fill="#8A97B1"/>'
            f'<circle cx="{n(hx-4)}" cy="{n(hy+10)}" r="19" fill="url(#neck)" opacity=".7"/>'
            + beak + eye + brow)

    wing_svg = (f'<g transform="translate(-4,-100) rotate({n(wing)})">'
                '<path d="M0,0 C-34,-34 -104,-26 -142,22 C-104,36 -44,40 0,20 Z" fill="#5E6C88"/>'
                '<path d="M-20,-4 C-60,-14 -98,-4 -128,18 M-14,8 C-54,6 -92,14 -124,24" stroke="#46526F" stroke-width="3.5" fill="none"/>'
                '<path d="M-6,-4 C-30,-22 -60,-22 -86,-6" stroke="#8D9AB6" stroke-width="3" fill="none"/></g>')

    g = (f'<g transform="translate({n(x+jx)},{n(y+jy)}) rotate({n(tilt)}) '
         f'scale({n(-s if flip else s)},{n(s)})" opacity="{n(alpha)}">'
         + legs + tail + body + wing_svg + head + '</g>')
    return g
