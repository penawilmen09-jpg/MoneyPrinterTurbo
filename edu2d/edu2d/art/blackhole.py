"""Agujero negro con lente gravitacional, astronauta, nave y estrellas distorsionadas."""
import math
import random
from ..core import n


def nebula(t, shift=(0, 0)):
    sx, sy = shift
    return (f'<ellipse cx="{300+sx*.2:.0f}" cy="{520+sy*.2:.0f}" rx="620" ry="420" fill="url(#nebP)" transform="rotate(-20 300 520)"/>'
            f'<ellipse cx="{800+sx*.3:.0f}" cy="{1100+sy*.3:.0f}" rx="700" ry="460" fill="url(#nebB)" transform="rotate(25 800 1100)"/>'
            f'<ellipse cx="{560+sx*.15:.0f}" cy="{300+sy*.15:.0f}" rx="520" ry="260" fill="url(#nebT)" transform="rotate(10 560 300)"/>'
            f'<rect x="-200" y="{880+sy*.1:.0f}" width="1500" height="140" fill="#fff" opacity=".035" transform="rotate(-22 540 950)"/>')


def space_bg(t, shift=(0, 0), nstars=70):
    out = '<rect x="-300" y="-300" width="1700" height="2600" fill="#03030E"/>' + nebula(t, shift)
    rnd = random.Random(21)
    for i in range(nstars):
        x, y = rnd.uniform(-100, 1180), rnd.uniform(-100, 2000)
        r = rnd.choice([1.2, 1.7, 2.3, 3.0])
        op = .35 + .65 * abs(math.sin(t * rnd.uniform(.5, 1.6) + i))
        out += f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r}" fill="#fff" opacity="{op:.2f}"/>'
    return out


def lensed_stars(t, cx, cy, R, zoom=1.0, nstars=150, seed=5, flow=0.0, thetaE=1.25, fade_inner=True):
    """Estrellas con lente gravitacional (masa puntual): imagen principal desplazada hacia fuera y alargada en arco."""
    rnd = random.Random(seed)
    out = ""
    for i in range(nstars):
        ang = rnd.uniform(0, 2 * math.pi)
        r0 = rnd.uniform(.9, 9.5) * R
        r0 = r0 * zoom
        if flow:
            r0 = (r0 + flow * R * 2) % (9.5 * R * zoom + R) + .6 * R
        beta = r0
        te = thetaE * R
        th1 = (beta + math.sqrt(beta ** 2 + 4 * te ** 2)) / 2
        th2 = (beta - math.sqrt(beta ** 2 + 4 * te ** 2)) / 2
        size = rnd.choice([1.4, 2.0, 2.8, 3.6])
        tw = .5 + .5 * abs(math.sin(t * rnd.uniform(.6, 1.8) + i))
        arc = min(.5, (te ** 2 / (th1 ** 2 + 1)) * .3 + (.02 if flow else 0))
        for (rad, op) in ((th1, tw), (-th2, tw * .45)):
            if rad < R * 1.04:
                continue
            a = ang if rad == th1 else ang + math.pi
            x1, y1 = cx + rad * math.cos(a - arc / 2), cy + rad * math.sin(a - arc / 2)
            x2, y2 = cx + rad * math.cos(a + arc / 2), cy + rad * math.sin(a + arc / 2)
            out += f'<path d="M{x1:.1f},{y1:.1f} A{rad:.1f} {rad:.1f} 0 0 1 {x2:.1f},{y2:.1f}" fill="none" stroke="#fff" stroke-width="{size}" stroke-linecap="round" opacity="{op:.2f}"/>'
    return out


def black_hole(cx, cy, R, t, tilt=.28, rot=-12, uid="a", glow=1.0):
    """Disco de acreción con efecto Doppler (lado izquierdo más brillante), arco lenteado y fotosfera."""
    out = f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{R*5:.0f}" fill="url(#bhGlow)" opacity="{glow:.2f}"/>'
    rings = ""
    for k in range(7):
        rx = R * (1.55 + .34 * k)
        ry = rx * tilt
        w = R * (.24 - .012 * k)
        rings += (f'<ellipse cx="{cx}" cy="{cy}" rx="{rx:.0f}" ry="{ry:.0f}" fill="none" stroke="url(#diskG)" stroke-width="{w:.1f}" opacity="{.95-.1*k:.2f}"/>')
        spd = 260 / (1 + .35 * k)
        rings += (f'<ellipse cx="{cx}" cy="{cy}" rx="{rx:.0f}" ry="{ry:.0f}" fill="none" stroke="url(#diskH)" stroke-width="{w*.45:.1f}" '
                  f'stroke-dasharray="{R*.5:.0f} {R*1.4:.0f}" stroke-dashoffset="{-(t*spd) % (R*1.9):.0f}" opacity=".85"/>')
    g = f'<g transform="rotate({rot} {cx} {cy})">'
    out += g + rings + '</g>'
    # arco lenteado (parte trasera del disco doblada sobre y bajo la sombra)
    out += (f'<path d="M{cx-R*1.55:.0f},{cy} A{R*1.55:.0f} {R*1.45:.0f} 0 0 1 {cx+R*1.55:.0f},{cy}" fill="none" stroke="url(#diskH)" stroke-width="{R*.42:.0f}" opacity=".95" stroke-linecap="round"/>'
            f'<path d="M{cx-R*1.3:.0f},{cy} A{R*1.3:.0f} {R*1.2:.0f} 0 0 0 {cx+R*1.3:.0f},{cy}" fill="none" stroke="url(#diskG)" stroke-width="{R*.16:.0f}" opacity=".8" stroke-linecap="round"/>')
    out += f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="#000"/>'
    out += f'<circle cx="{cx}" cy="{cy}" r="{R*1.015:.1f}" fill="none" stroke="#FFE2A8" stroke-width="{max(2, R*.04):.1f}" opacity=".9"/>'
    # mitad frontal del disco, por delante de la sombra
    out += (f'<defs><clipPath id="front{uid}"><rect x="{cx-R*8:.0f}" y="{cy}" width="{R*16:.0f}" height="{R*8:.0f}"/></clipPath></defs>'
            f'<g clip-path="url(#front{uid})">{g}{rings}</g></g>')
    return out


def astronaut(x, y, s=1.0, t=0.0, rot=0.0, stretch=1.0, squeeze=1.0, expr="scared", flip=False, drift=True):
    """Astronauta (mismo diseño en todo el video). Origen = centro del torso, cabeza hacia -y."""
    sw = 10 * math.sin(t * 1.4) if drift else 0
    a1, a2 = -35 + sw, 30 - sw
    l1, l2 = 12 + 6 * math.sin(t * 1.1), -10 - 6 * math.sin(t * 1.3)
    blink = (t % 3.6) < .12
    eyes = (('<line x1="-10" y1="-124" x2="-2" y2="-124" stroke="#222" stroke-width="3"/><line x1="8" y1="-124" x2="16" y2="-124" stroke="#222" stroke-width="3"/>') if blink else
            '<circle cx="-6" cy="-124" r="6" fill="#fff"/><circle cx="12" cy="-124" r="6" fill="#fff"/><circle cx="-4" cy="-124" r="2.6" fill="#111"/><circle cx="14" cy="-124" r="2.6" fill="#111"/>')
    mouth = ('<ellipse cx="4" cy="-104" rx="6" ry="8" fill="#5A1F1F"/>' if expr == "scared" else '<path d="M-4,-106 Q4,-100 12,-106" fill="none" stroke="#5A1F1F" stroke-width="3"/>')
    brow = '<path d="M-14,-131 L-1,-137 M17,-131 L5,-137" stroke="#3A2412" stroke-width="3" stroke-linecap="round"/>' if expr == "scared" else ''
    body = (
        # mochila
        '<rect x="-52" y="-78" width="34" height="96" rx="12" fill="#AEB8CC" stroke="#6B7690" stroke-width="3"/>'
        # piernas
        f'<g transform="translate(-14,50) rotate({l1:.0f})"><rect x="-13" y="0" width="26" height="78" rx="12" fill="url(#suit)" stroke="#6B7690" stroke-width="3"/><rect x="-16" y="64" width="32" height="26" rx="10" fill="#E4572E" stroke="#7A2A12" stroke-width="3"/></g>'
        f'<g transform="translate(14,50) rotate({l2:.0f})"><rect x="-13" y="0" width="26" height="78" rx="12" fill="url(#suit)" stroke="#6B7690" stroke-width="3"/><rect x="-16" y="64" width="32" height="26" rx="10" fill="#E4572E" stroke="#7A2A12" stroke-width="3"/></g>'
        # torso
        '<rect x="-34" y="-84" width="68" height="146" rx="26" fill="url(#suit)" stroke="#6B7690" stroke-width="3"/>'
        '<rect x="-16" y="-58" width="32" height="30" rx="8" fill="#E4572E"/><circle cx="-6" cy="-43" r="4" fill="#FFE14D"/><circle cx="7" cy="-43" r="4" fill="#7CF0B3"/>'
        '<rect x="-34" y="30" width="68" height="10" fill="#E4572E" opacity=".9"/>'
        # brazos
        f'<g transform="translate(-26,-62) rotate({a1:.0f})"><rect x="-11" y="0" width="22" height="72" rx="11" fill="url(#suit)" stroke="#6B7690" stroke-width="3"/><circle cx="0" cy="78" r="13" fill="#E4572E"/></g>'
        f'<g transform="translate(26,-62) rotate({a2:.0f})"><rect x="-11" y="0" width="22" height="72" rx="11" fill="url(#suit)" stroke="#6B7690" stroke-width="3"/><circle cx="0" cy="78" r="13" fill="#E4572E"/></g>'
        # casco
        '<rect x="-10" y="-98" width="20" height="18" fill="#AEB8CC"/>'
        '<circle cx="2" cy="-122" r="50" fill="url(#suit)" stroke="#6B7690" stroke-width="4"/>'
        '<ellipse cx="12" cy="-122" rx="36" ry="38" fill="url(#visor)" stroke="#0B1030" stroke-width="3"/>'
        '<circle cx="4" cy="-120" r="26" fill="#F2C29B" opacity=".92"/>' + eyes + brow + mouth +
        '<path d="M-6,-148 Q16,-158 36,-140" fill="none" stroke="#fff" stroke-width="5" stroke-linecap="round" opacity=".7"/>'
        '<rect x="-4" y="-176" width="8" height="18" rx="4" fill="#AEB8CC"/><circle cx="0" cy="-180" r="6" fill="#FF4D6D"/>')
    sx = -squeeze if flip else squeeze
    return f'<g transform="translate({x:.1f},{y:.1f}) rotate({rot:.1f}) scale({sx*s:.3f},{stretch*s:.3f})">{body}</g>'


def ship(x, y, s=1.0, t=0.0, rot=0.0, thrust=1.0):
    fl = (.7 + .3 * math.sin(t * 30)) * thrust
    return (f'<g transform="translate({x:.0f},{y:.0f}) rotate({rot:.0f}) scale({s})">'
            f'<polygon points="-70,-14 -70,14 {-70-90*fl:.0f},0" fill="#FFB347" opacity=".9"/><polygon points="-70,-8 -70,8 {-70-55*fl:.0f},0" fill="#FFF3C4"/>'
            '<path d="M-70,-30 L40,-30 Q110,-30 120,0 Q110,30 40,30 L-70,30 Z" fill="url(#suit)" stroke="#6B7690" stroke-width="4"/>'
            '<ellipse cx="62" cy="-2" rx="26" ry="16" fill="url(#visor)" stroke="#0B1030" stroke-width="3"/>'
            '<rect x="-48" y="-30" width="30" height="60" fill="#E4572E"/><polygon points="-40,-30 -66,-62 -20,-30" fill="#E4572E"/><polygon points="-40,30 -66,62 -20,30" fill="#E4572E"/></g>')


def clock(x, y, r, angle, col="#7CD3FF"):
    out = f'<circle cx="{x}" cy="{y}" r="{r}" fill="#0B1030" stroke="{col}" stroke-width="6"/>'
    for k in range(12):
        a = math.radians(k * 30)
        out += f'<line x1="{x + (r-10)*math.sin(a):.0f}" y1="{y - (r-10)*math.cos(a):.0f}" x2="{x + (r-2)*math.sin(a):.0f}" y2="{y - (r-2)*math.cos(a):.0f}" stroke="{col}" stroke-width="3"/>'
    a = math.radians(angle)
    return out + f'<line x1="{x}" y1="{y}" x2="{x + (r-18)*math.sin(a):.0f}" y2="{y - (r-18)*math.cos(a):.0f}" stroke="#fff" stroke-width="6" stroke-linecap="round"/><circle cx="{x}" cy="{y}" r="7" fill="#fff"/>'
