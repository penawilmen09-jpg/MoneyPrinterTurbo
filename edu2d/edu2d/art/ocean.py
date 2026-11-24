"""Mar, barco de carga (exterior y corte transversal), capitán, grúa, bloque de hierro."""
import math
import random
from ..core import W, H, n

CONT = ["#E4572E", "#F3A712", "#29A9A0", "#4C6EF5", "#8E5CF7", "#ECECEC", "#2FBF71", "#FF6B9D"]
COL_X = [-205 + i * 52 for i in range(9)]
BASE_H = [3, 4, 3, 4, 4, 3, 4, 3, 2]
CH = 38  # alto contenedor
HULL = "M-430,-150 L470,-150 Q470,-135 450,-90 Q390,60 300,105 Q280,112 250,112 L-340,112 Q-420,112 -430,40 Z"


def wave_y(x, t, y0, A=14):
    return y0 + A * math.sin(x / 90 + t * 1.6) + A * .5 * math.sin(x / 47 - t * 2.3) + A * .3 * math.sin(x / 31 + t * 3.1)


def _poly(t, y0, A, ph, bottom, x0=-60, x1=W + 60, step=18):
    pts = [f"{x},{wave_y(x + ph, t, y0, A):.1f}" for x in range(x0, x1 + 1, step)]
    return " ".join(pts) + f" {x1},{bottom} {x0},{bottom}"


def sea_back(t, y0, A=14, bottom=H + 200):
    return (f'<polygon points="{_poly(t, y0, A, 0, bottom)}" fill="url(#seaDeep)"/>'
            f'<polygon points="{_poly(t, y0 + 70, A * .8, 160, bottom)}" fill="#0F5BA0" opacity=".35"/>')


def sea_front(t, y0, A=14, bottom=H + 200, alpha=.5):
    pts = " ".join(f"{x},{wave_y(x, t, y0, A):.1f}" for x in range(-60, W + 61, 18))
    return (f'<polygon points="{_poly(t, y0, A, 0, bottom)}" fill="#3AA8EA" opacity="{alpha}"/>'
            f'<polyline points="{pts}" fill="none" stroke="#fff" stroke-width="5" opacity=".75" stroke-linejoin="round"/>')


def gull(x, y, t, s=1.0, k=0):
    f = math.sin(t * 7 + k) * .6
    return (f'<g transform="translate({x:.0f},{y:.0f}) scale({s})"><path d="M-22,0 Q-11,{-14*(1+f):.1f} 0,0 Q11,{-14*(1+f):.1f} 22,0" '
            'fill="none" stroke="#fff" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/></g>')


def containers(extras=()):
    out = ""
    rnd = random.Random(11)
    for c, x in enumerate(COL_X):
        for k in range(BASE_H[c]):
            out += _box(x, -150 - (k + 1) * CH, 50, CH, CONT[(c * 3 + k * 5 + rnd.randint(0, 2)) % len(CONT)])
    for (c, k, col) in extras:
        out += _box(COL_X[c], -150 - (k + 1) * CH, 50, CH, col)
    return out


def _box(x, y, w, h, col):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{col}" stroke="#1B1B2F" stroke-width="2.5"/>'
            f'<line x1="{x+w*.25}" y1="{y+3}" x2="{x+w*.25}" y2="{y+h-3}" stroke="#000" stroke-opacity=".25" stroke-width="2"/>'
            f'<line x1="{x+w*.5}" y1="{y+3}" x2="{x+w*.5}" y2="{y+h-3}" stroke="#000" stroke-opacity=".25" stroke-width="2"/>'
            f'<line x1="{x+w*.75}" y1="{y+3}" x2="{x+w*.75}" y2="{y+h-3}" stroke="#000" stroke-opacity=".25" stroke-width="2"/>')


def bridge():
    out = ('<rect x="-420" y="-225" width="130" height="75" fill="#F4F6FA" stroke="#1B1B2F" stroke-width="3"/>'
           '<rect x="-405" y="-290" width="105" height="65" fill="#E6EAF2" stroke="#1B1B2F" stroke-width="3"/>'
           '<rect x="-375" y="-350" width="34" height="60" fill="#E4572E" stroke="#1B1B2F" stroke-width="3"/>'
           '<rect x="-375" y="-350" width="34" height="14" fill="#1B1B2F"/>'
           '<line x1="-352" y1="-350" x2="-352" y2="-410" stroke="#1B1B2F" stroke-width="4"/>')
    for i in range(4):
        out += f'<rect x="{-395+i*24}" y="-275" width="16" height="20" fill="#2B3A55"/>'
        out += f'<rect x="{-410+i*30}" y="-205" width="18" height="16" fill="#2B3A55"/>'
    return out


def ship_exterior(extras=()):
    """Barco visto desde el costado; origen = línea de flotación al centro."""
    return (f'<defs><clipPath id="hc"><path d="{HULL}"/></clipPath></defs>'
            '<g clip-path="url(#hc)"><rect x="-440" y="-160" width="920" height="320" fill="#24406A"/>'
            '<rect x="-440" y="22" width="920" height="140" fill="#B7352D"/>'
            '<rect x="-440" y="-150" width="920" height="14" fill="#F4F6FA"/></g>'
            f'<path d="{HULL}" fill="none" stroke="#14213A" stroke-width="7" stroke-linejoin="round"/>'
            + containers(extras) + bridge())


def ship_section(t, reveal_x):
    """Corte transversal animado: el 'casco exterior' se retira con un barrido en x=reveal_x."""
    out = (f'<defs><clipPath id="hc"><path d="{HULL}"/></clipPath>'
           f'<clipPath id="rv"><rect x="{reveal_x:.0f}" y="-200" width="1000" height="400"/></clipPath></defs>')
    inner = '<rect x="-440" y="-160" width="920" height="300" fill="url(#airG)"/>'
    # cubiertas y mamparos de acero (finos) -> casi todo es aire
    for y in (-30,):
        inner += f'<rect x="-250" y="{y}" width="700" height="8" fill="#5A6C8F"/>'
    inner += '<rect x="-440" y="70" width="920" height="8" fill="#5A6C8F"/>'
    for x in (-250, -85, 80, 245, 420):
        inner += f'<rect x="{x-4}" y="-150" width="8" height="222" fill="#5A6C8F"/>'
    # tanques de lastre (parcialmente con agua)
    inner += '<rect x="-430" y="78" width="900" height="36" fill="#6FB6E8" opacity=".75"/>'
    # carga: unas pocas cajas, casi todo vacío
    for (x, y, c) in ((-240, -68, 0), (-188, -68, 2), (-240, -106, 4), (-80, -68, 3), (90, -68, 1), (90, -106, 5), (255, -68, 6)):
        inner += _box(x if x > -90 or x < -200 else x, y - 0, 50, 38, CONT[c])
    # sala de máquinas
    ph = math.sin(t * 8)
    inner += ('<rect x="-420" y="-60" width="160" height="120" fill="#C9D1DC" stroke="#5A6C8F" stroke-width="4"/>'
              '<rect x="-400" y="-40" width="40" height="80" fill="#E4572E"/><rect x="-350" y="-40" width="40" height="80" fill="#E4572E"/>'
              f'<rect x="-392" y="{-40+16*ph:.1f}" width="24" height="26" fill="#F3A712"/>'
              f'<rect x="-342" y="{-40-16*ph:.1f}" width="24" height="26" fill="#F3A712"/>')
    # burbujas de aire flotando
    for i in range(34):
        bx = -400 + (i * 131) % 840
        by = 60 - ((t * 38 + i * 53) % 210)
        inner += f'<circle cx="{bx + 8*math.sin(t*2+i):.0f}" cy="{by:.0f}" r="{4+i%3*2}" fill="#fff" opacity=".85" stroke="#8ED0F0" stroke-width="1.5"/>'
    out += f'<g clip-path="url(#hc)">{inner}'
    out += (f'<g clip-path="url(#rv)"><rect x="-440" y="-160" width="920" height="320" fill="#24406A"/>'
            '<rect x="-440" y="22" width="920" height="140" fill="#B7352D"/><rect x="-440" y="-150" width="920" height="14" fill="#F4F6FA"/></g></g>')
    out += f'<path d="{HULL}" fill="none" stroke="#14213A" stroke-width="9" stroke-linejoin="round"/>'
    return out + containers() + bridge()


def ship_g(x, y, s=1.0, rot=0.0, body=""):
    return f'<g transform="translate({x:.1f},{y:.1f}) rotate({rot:.2f}) scale({s})">{body}</g>'


def iron_block(x, y, size=150, rot=0.0):
    h = size / 2
    out = (f'<g transform="translate({x:.1f},{y:.1f}) rotate({rot:.1f})">'
           f'<rect x="{-h}" y="{-h}" width="{size}" height="{size}" rx="10" fill="url(#iron)" stroke="#2F3746" stroke-width="6"/>'
           f'<rect x="{-h+14}" y="{-h+14}" width="{size-28}" height="{size-28}" rx="6" fill="none" stroke="#fff" stroke-opacity=".35" stroke-width="3"/>')
    for sx in (-1, 1):
        for sy in (-1, 1):
            out += f'<circle cx="{sx*(h-22)}" cy="{sy*(h-22)}" r="7" fill="#4A5262"/>'
    out += (f'<text x="0" y="12" text-anchor="middle" font-family="DejaVu Sans" font-weight="bold" font-size="30" fill="#2F3746">HIERRO</text></g>')
    return out


def captain(x, y, s=1.0, t=0.0, expr="neutral", arm="idle", flip=False):
    blink = (t % 3.1) < .12
    ang = {"idle": -8, "wave": -140 + 18 * math.sin(t * 9), "point": -82, "think": -150 + 6 * math.sin(t * 5)}[arm]
    eyes = ('<line x1="-18" y1="-228" x2="-8" y2="-228" stroke="#222" stroke-width="4"/><line x1="8" y1="-228" x2="18" y2="-228" stroke="#222" stroke-width="4"/>'
            if blink else '<circle cx="-14" cy="-228" r="5" fill="#222"/><circle cx="14" cy="-228" r="5" fill="#222"/>')
    if expr == "surprised":
        eyes = '<circle cx="-14" cy="-228" r="8" fill="#fff" stroke="#222" stroke-width="3"/><circle cx="14" cy="-228" r="8" fill="#fff" stroke="#222" stroke-width="3"/><circle cx="-14" cy="-228" r="3" fill="#222"/><circle cx="14" cy="-228" r="3" fill="#222"/>'
        mouth = '<ellipse cx="0" cy="-196" rx="9" ry="12" fill="#6B2A2A"/>'
    elif expr == "happy":
        mouth = '<path d="M-14,-200 Q0,-184 14,-200" fill="#6B2A2A" stroke="#6B2A2A" stroke-width="3"/>'
    else:
        mouth = '<path d="M-10,-198 Q0,-192 10,-198" fill="none" stroke="#6B2A2A" stroke-width="4" stroke-linecap="round"/>'
    brow = ('<path d="M-24,-246 L-6,-240 M24,-246 L6,-240" stroke="#ddd" stroke-width="5" stroke-linecap="round"/>' if expr == "surprised" else
            '<path d="M-24,-240 L-6,-243 M24,-240 L6,-243" stroke="#ddd" stroke-width="5" stroke-linecap="round"/>')
    g = (f'<g transform="translate({x:.1f},{y:.1f}) scale({-s if flip else s},{s})">'
         '<rect x="-22" y="-82" width="18" height="70" fill="#27374D"/><rect x="4" y="-82" width="18" height="70" fill="#27374D"/>'
         '<ellipse cx="-14" cy="-8" rx="22" ry="10" fill="#111"/><ellipse cx="14" cy="-8" rx="22" ry="10" fill="#111"/>'
         '<rect x="-40" y="-192" width="80" height="116" rx="22" fill="#1F3A66"/><rect x="-40" y="-118" width="80" height="12" fill="#F4F6FA"/>'
         '<circle cx="0" cy="-170" r="5" fill="#F3C623"/><circle cx="0" cy="-148" r="5" fill="#F3C623"/>'
         '<rect x="-56" y="-182" width="18" height="80" rx="9" fill="#1F3A66" transform="rotate(8 -47 -182)"/><circle cx="-56" cy="-102" r="11" fill="#F2C29B"/>'
         f'<g transform="translate(40,-178) rotate({ang:.1f})"><rect x="-9" y="0" width="18" height="78" rx="9" fill="#1F3A66"/><circle cx="0" cy="84" r="12" fill="#F2C29B"/></g>'
         '<circle cx="0" cy="-226" r="42" fill="#F2C29B"/>'
         '<path d="M-40,-222 Q-36,-170 0,-166 Q36,-170 40,-222 Q22,-200 0,-203 Q-22,-200 -40,-222 Z" fill="#EDEDED"/>'
         '<circle cx="0" cy="-212" r="9" fill="#E3A87C"/>' + eyes + brow + mouth +
         '<path d="M-44,-244 Q0,-300 44,-244 Z" fill="#F4F6FA" stroke="#1B1B2F" stroke-width="3"/>'
         '<rect x="-50" y="-248" width="100" height="14" rx="6" fill="#1B2A49"/><circle cx="0" cy="-262" r="8" fill="#F3C623"/></g>')
    return g
