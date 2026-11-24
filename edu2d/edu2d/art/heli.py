"""Helicóptero ilustrado: vistas lateral, frontal y superior + rotor con perspectiva y desenfoque de giro."""
import math
from ..core import n

ROTOR_RPS = 2.0                 # vueltas/s dibujadas (≈24°/frame a 30 fps: sin efecto "rueda de carreta")


def rotor_ang(t, rps=ROTOR_RPS):
    return (t * rps * 360.0)


def blades(cx, cy, R, k, ang, nb=4, blur=3, col="#2B3347", tip="#FFD43B", disc=True, sgn=1):
    """Rotor visto con elipticidad k (ry/rx). El giro es antihorario visto desde arriba."""
    out = ""
    if disc:
        out += f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{R}" ry="{R*k:.1f}" fill="#fff" opacity=".10"/>'
    for j in range(blur, -1, -1):
        a0 = ang - sgn * j * 11
        op = 1.0 if j == 0 else .16 / j + .05
        far, near = "", ""
        for i in range(nb):
            a = math.radians(a0 - i * 360 / nb)
            dx, dy = math.cos(a), k * math.sin(a)
            L = math.hypot(dx, dy) or 1
            px, py = -dy / L, dx / L                  # perpendicular en pantalla
            persp = 1 + .18 * math.sin(a)
            w0, w1 = 11 * persp, 8 * persp
            tx, ty = cx + R * dx, cy + R * dy
            ix, iy = cx + .28 * R * dx, cy + .28 * R * dy
            seg = lambda c, p0, p1, wa, wb: (
                f'<polygon points="{cx+p0*dx*R-px*wa:.1f},{cy+p0*dy*R-py*wa:.1f} {cx+p0*dx*R+px*wa:.1f},{cy+p0*dy*R+py*wa:.1f} '
                f'{cx+p1*dx*R+px*wb:.1f},{cy+p1*dy*R+py*wb:.1f} {cx+p1*dx*R-px*wb:.1f},{cy+p1*dy*R-py*wb:.1f}" fill="{c}" opacity="{op:.2f}"/>')
            s = seg(col, .12, .86, w0, w1) + seg(tip, .86, 1.0, w1, w1 * .9)
            (far if math.sin(a) < 0 else near).__class__  # noqa
            if math.sin(a) < 0:
                far += s
            else:
                near += s
            if j == 0:
                pass
            out_chunk = (far, near)
        out += out_chunk[0] + out_chunk[1]
    out += (f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="17" fill="#1E2433"/><circle cx="{cx-4:.1f}" cy="{cy-4:.1f}" r="6" fill="#6C7690"/>')
    return out


def tail_rotor(cx, cy, r, ang):
    out = f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#fff" opacity=".13"/>'
    for j in (2, 1, 0):
        for i in (0, 180):
            a = math.radians(ang - j * 14 + i)
            op = 1 if j == 0 else .18
            out += (f'<line x1="{cx}" y1="{cy}" x2="{cx + r*math.cos(a):.1f}" y2="{cy + r*math.sin(a):.1f}" stroke="#2B3347" '
                    f'stroke-width="9" stroke-linecap="round" opacity="{op}"/>')
    return out + f'<circle cx="{cx}" cy="{cy}" r="8" fill="#1E2433"/>'


def pilot(x, y, t, s=1.0):
    blink = (t % 3.3) < .12
    eye = ('<line x1="8" y1="-2" x2="22" y2="-2" stroke="#222" stroke-width="3"/>' if blink else '<circle cx="15" cy="-3" r="4" fill="#222"/>')
    nod = 3 * math.sin(t * 2.1)
    return (f'<g transform="translate({x},{y + nod:.1f}) scale({s})"><rect x="-18" y="18" width="46" height="60" rx="14" fill="#1F3A66"/>'
            '<circle cx="2" cy="0" r="30" fill="#F2C29B"/><path d="M-30,-4 Q-28,-38 2,-38 Q32,-38 32,-6 L32,-14 Q2,-24 -30,-4 Z" fill="#F3C623"/>'
            '<path d="M-31,-6 Q-30,-40 2,-40 Q34,-40 33,-6 Z" fill="#F3C623" stroke="#B88A00" stroke-width="3"/>'
            f'<rect x="-6" y="-14" width="40" height="12" rx="6" fill="#2B3347" opacity=".35"/>{eye}'
            '<path d="M6,12 Q16,20 26,10" fill="none" stroke="#7A2E2E" stroke-width="3.5" stroke-linecap="round"/>'
            '<rect x="-34" y="-8" width="10" height="22" rx="5" fill="#2B3347"/></g>')


def heli_side(t, rot_ang=None, tilt_disc=0.0, k=.12, tail_on=True, tail_ang=None):
    """Origen = cubo del rotor principal; mira a la derecha. Devuelve SVG."""
    ang = rotor_ang(t) if rot_ang is None else rot_ang
    tail_ang = (t * 900) if tail_ang is None else tail_ang
    out = ""
    # cola
    out += ('<polygon points="-90,95 -440,58 -440,84 -90,152" fill="#C32F22" stroke="#7A1A12" stroke-width="3"/>'
            '<polygon points="-380,62 -462,-34 -490,-34 -436,86" fill="#E24B3A" stroke="#7A1A12" stroke-width="3"/>'
            '<polygon points="-380,62 -440,60 -462,-10" fill="#F3C623" opacity=".9"/>'
            '<rect x="-350" y="76" width="70" height="9" rx="4" fill="#9B2519"/>')
    out += tail_rotor(-470, 22, 58, tail_ang) if tail_on else ""
    # patines
    out += ('<path d="M-80,214 L-92,266 M118,212 L132,266" stroke="#2B3347" stroke-width="10" stroke-linecap="round"/>'
            '<path d="M-200,270 L200,270 Q232,270 244,246" fill="none" stroke="#2B3347" stroke-width="13" stroke-linecap="round"/>')
    # cabina
    body = "M-135,112 C-125,40 -40,18 42,24 C124,30 196,72 220,140 C232,190 196,220 124,226 L-60,226 C-124,226 -146,170 -135,112 Z"
    out += (f'<defs><clipPath id="hb"><path d="{body}"/></clipPath></defs><path d="{body}" fill="url(#heliRed)" stroke="#7A1A12" stroke-width="5"/>'
            '<g clip-path="url(#hb)"><rect x="-150" y="176" width="400" height="16" fill="#fff"/><rect x="-150" y="196" width="400" height="8" fill="#F3C623"/>'
            '<ellipse cx="-20" cy="60" rx="140" ry="26" fill="#fff" opacity=".13"/></g>')
    out += ('<path d="M72,48 C132,54 186,90 206,142 L98,142 C94,104 84,74 72,48 Z" fill="url(#glass)" stroke="#7A1A12" stroke-width="4"/>'
            '<path d="M88,62 C118,70 150,96 168,128" stroke="#fff" stroke-width="5" fill="none" opacity=".7" stroke-linecap="round"/>')
    out += pilot(138, 100, t, .78)
    out += ('<rect x="-52" y="70" width="104" height="70" rx="14" fill="url(#glass)" stroke="#7A1A12" stroke-width="4"/>'
            '<line x1="-2" y1="70" x2="-2" y2="140" stroke="#7A1A12" stroke-width="3"/>')
    # motor y mástil
    out += ('<ellipse cx="-28" cy="14" rx="92" ry="26" fill="#B8C0CE" stroke="#5B6578" stroke-width="4"/>'
            '<rect x="-9" y="-6" width="18" height="40" fill="#3A4256"/>'
            '<path d="M-116,18 L-150,8" stroke="#6C7690" stroke-width="10" stroke-linecap="round"/>')
    disc = f'<g transform="rotate({tilt_disc:.2f} 0 0)">{blades(0, -4, 330, k, ang)}</g>'
    return out + disc


def heli_front(t, tilt_disc=0.0):
    ang = rotor_ang(t)
    out = ('<path d="M-130,268 L130,268" stroke="#2B3347" stroke-width="13" stroke-linecap="round"/>'
           '<path d="M-70,214 L-78,268 M70,214 L78,268" stroke="#2B3347" stroke-width="10" stroke-linecap="round"/>'
           '<ellipse cx="0" cy="124" rx="118" ry="104" fill="url(#heliRed)" stroke="#7A1A12" stroke-width="5"/>'
           '<ellipse cx="0" cy="106" rx="82" ry="66" fill="url(#glass)" stroke="#7A1A12" stroke-width="4"/>'
           '<path d="M-52,82 Q-20,62 20,66" stroke="#fff" stroke-width="5" fill="none" opacity=".7" stroke-linecap="round"/>'
           '<rect x="-118" y="170" width="236" height="14" fill="#fff" opacity=".9"/>'
           '<ellipse cx="0" cy="14" rx="46" ry="20" fill="#B8C0CE" stroke="#5B6578" stroke-width="4"/>'
           '<rect x="-9" y="-6" width="18" height="40" fill="#3A4256"/>')
    out += pilot(0, 96, t, .62)
    out += f'<g transform="rotate({tilt_disc:.2f} 0 0)">{blades(0, -4, 330, .09, ang, nb=2, blur=3)}</g>'
    return out


def heli_top(t, yaw=0.0, tail_thrust=False):
    """Vista superior, nariz hacia arriba; rotor principal gira antihorario."""
    ang = rotor_ang(t)
    out = (f'<g transform="rotate({yaw:.2f} 0 0)">'
           '<rect x="-12" y="70" width="24" height="270" fill="#C32F22" stroke="#7A1A12" stroke-width="3"/>'
           '<rect x="-34" y="318" width="68" height="14" rx="6" fill="#E24B3A" stroke="#7A1A12" stroke-width="3"/>'
           '<path d="M-62,-110 L-62,100 M62,-110 L62,100" stroke="#2B3347" stroke-width="9" stroke-linecap="round"/>'
           '<ellipse cx="0" cy="-8" rx="56" ry="122" fill="url(#heliRed)" stroke="#7A1A12" stroke-width="5"/>'
           '<ellipse cx="0" cy="-70" rx="38" ry="50" fill="url(#glass)" stroke="#7A1A12" stroke-width="4"/>'
           '<rect x="-8" y="-110" width="16" height="200" fill="#fff" opacity=".35"/>')
    th = 40 + 30 * abs(math.cos(math.radians(t * 900)))
    out += f'<ellipse cx="26" cy="326" rx="9" ry="{th/2:.0f}" fill="#2B3347"/>'
    out += blades(0, -8, 300, 1.0, -ang, nb=4, blur=3, disc=True, sgn=-1)
    return out + '</g>'


def downwash(t, cx, y_top, R, y_ground, n_=22, speed=520, alpha=.7, ground_spread=True):
    """Columnas de partículas/líneas de aire empujadas hacia abajo; se abren al llegar al suelo."""
    out = ""
    L = y_ground - y_top
    for i in range(n_):
        u = -1 + 2 * ((i * 0.618) % 1)
        ph = (t * speed / L + i * .137) % 1
        y = y_top + ph * L
        x = cx + u * R * (1 + .25 * ph)
        if ground_spread and y > y_ground - 70:
            q = (y - (y_ground - 70)) / 70
            x = cx + u * R * (1 + .25 + 1.6 * q)
        op = alpha * math.sin(math.pi * min(ph * 1.05, 1))
        out += f'<line x1="{x:.0f}" y1="{y-22:.0f}" x2="{x:.0f}" y2="{y+22:.0f}" stroke="#E8F7FF" stroke-width="5" stroke-linecap="round" opacity="{op:.2f}"/>'
    return out


def arrow(x1, y1, x2, y2, col, w=16, head=34):
    a = math.atan2(y2 - y1, x2 - x1)
    ex, ey = x2 - head * .7 * math.cos(a), y2 - head * .7 * math.sin(a)
    px, py = -math.sin(a), math.cos(a)
    return (f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{ex:.0f}" y2="{ey:.0f}" stroke="{col}" stroke-width="{w}" stroke-linecap="round"/>'
            f'<polygon points="{x2:.0f},{y2:.0f} {ex+px*head*.55:.0f},{ey+py*head*.55:.0f} {ex-px*head*.55:.0f},{ey-py*head*.55:.0f}" fill="{col}"/>')
