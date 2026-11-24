"""Escenario: cielo, colinas, ciudad, poste, cables y electricidad."""
import math
import random
from functools import lru_cache
from ..core import W, H, n

RIG = dict(xl=130, xr=1230, ys=[640, 800, 960], sag=110)


def wire_y(i, x, rig=RIG):
    cx = (rig["xl"] + rig["xr"]) / 2
    hw = (rig["xr"] - rig["xl"]) / 2
    return rig["ys"][i] + rig["sag"] * (1 - ((x - cx) / hw) ** 2)


def sky(kind="skyDay", t=0, sun=True, sun_xy=(820, 330), clouds=True, stars=False):
    out = f'<rect x="-300" y="-300" width="{W+600}" height="{H+600}" fill="url(#{kind})"/>'
    if stars:
        rnd = random.Random(7)
        for _ in range(40):
            out += f'<circle cx="{rnd.randint(0,W)}" cy="{rnd.randint(0,700)}" r="{rnd.choice([1.5,2,2.5])}" fill="#fff" opacity="{.4+.5*abs(math.sin(t*2+_))*0.8:.2f}"/>'
    if sun:
        out += f'<circle cx="{sun_xy[0]}" cy="{sun_xy[1]}" r="260" fill="url(#sun)"/>'
        out += f'<circle cx="{sun_xy[0]}" cy="{sun_xy[1]}" r="62" fill="#FFF3B0"/>'
    if clouds:
        for k, (cx0, cy, sc, sp) in enumerate([(100, 260, 1.3, 14), (650, 430, 1.0, 9), (950, 150, .8, 18), (300, 520, .7, 11)]):
            x = (cx0 + sp * t) % (W + 700) - 350
            out += (f'<g transform="translate({x:.1f},{cy}) scale({sc})" fill="#fff" opacity=".88">'
                    '<ellipse cx="0" cy="0" rx="120" ry="38"/><circle cx="-40" cy="-28" r="42"/>'
                    '<circle cx="22" cy="-40" r="52"/><circle cx="72" cy="-14" r="36"/></g>')
    return out


@lru_cache(maxsize=None)
def hills(c1="#6DBE7B", c2="#4FA36A", base=1180):
    return (f'<path d="M-300,{base} Q100,{base-200} 450,{base-60} T1000,{base-160} T1400,{base-40} L1400,{H+300} L-300,{H+300} Z" fill="{c1}"/>'
            f'<path d="M-300,{base+80} Q200,{base-60} 600,{base+40} T1400,{base-20} L1400,{H+300} L-300,{H+300} Z" fill="{c2}"/>')


@lru_cache(maxsize=None)
def city(seed=3, base=1130, col="#5C6BA8", win="#FFE9A0", lit=.35):
    rnd = random.Random(seed)
    out, x = "", -200
    while x < W + 200:
        w = rnd.randint(70, 150)
        h = rnd.randint(120, 400)
        out += f'<rect x="{x}" y="{base-h}" width="{w}" height="{h+400}" fill="{col}"/>'
        for wy in range(base - h + 18, base - 10, 34):
            for wx in range(x + 12, x + w - 16, 28):
                if rnd.random() < lit:
                    out += f'<rect x="{wx}" y="{wy}" width="12" height="16" fill="{win}" opacity=".85"/>'
        x += w + rnd.randint(0, 14)
    return out


def pole(xp=130, y_top=540, n_arms=3, rig=RIG, transformer=False):
    out = f'<rect x="{xp-26}" y="{y_top}" width="52" height="{H+300-y_top}" fill="url(#wood)"/>'
    for i in range(n_arms):
        ya = rig["ys"][i]
        out += (f'<rect x="{xp-105}" y="{ya+14}" width="210" height="22" rx="5" fill="#7A4F28"/>'
                f'<rect x="{xp-9}" y="{ya-2}" width="18" height="18" rx="3" fill="#2F3A56"/>'
                f'<rect x="{xp-6}" y="{ya+6}" width="12" height="10" fill="#5B6B93"/>')
        for dx in (-85, 85):
            out += f'<rect x="{xp+dx-6}" y="{ya+4}" width="12" height="14" rx="3" fill="#5B6B93"/>'
    if transformer:
        ty = rig["ys"][-1] + 130
        out += (f'<rect x="{xp+26}" y="{ty}" width="120" height="170" rx="22" fill="#7C8AA6"/>'
                f'<rect x="{xp+26}" y="{ty+20}" width="120" height="14" fill="#5C6A86"/>'
                f'<rect x="{xp+26}" y="{ty+60}" width="120" height="14" fill="#5C6A86"/>'
                f'<rect x="{xp+66}" y="{ty-22}" width="14" height="26" fill="#2F3A56"/>'
                f'<rect x="{xp+104}" y="{ty-22}" width="14" height="26" fill="#2F3A56"/>')
    return out


def wire(i, t=0.0, energy=True, speed=300, rig=RIG, glow="glowY", x0=None, x1=None, spacing=190, hot=1.0):
    xs = list(range(int(x0 if x0 is not None else rig["xl"]),
                    int(x1 if x1 is not None else min(rig["xr"], W + 60)) + 1, 30))
    pts = " ".join(f"{x},{wire_y(i, x, rig):.1f}" for x in xs)
    out = (f'<polyline points="{pts}" fill="none" stroke="#1F2330" stroke-width="10" stroke-linejoin="round"/>'
           f'<polyline points="{pts}" fill="none" stroke="#6C7792" stroke-width="3" transform="translate(0,-2)"/>')
    if energy:
        pulse = 0.18 + 0.10 * math.sin(t * 9)
        out += f'<polyline points="{pts}" fill="none" stroke="#FFE066" stroke-width="7" opacity="{pulse*hot:.2f}"/>'
        span = xs[-1] - xs[0]
        k = 0
        while k * spacing < span + spacing:
            px = xs[0] + (k * spacing + speed * t) % (span + spacing)
            if px <= xs[-1]:
                py = wire_y(i, px, rig)
                out += (f'<circle cx="{px:.1f}" cy="{py:.1f}" r="26" fill="url(#{glow})" opacity="{min(1,hot):.2f}"/>'
                        f'<circle cx="{px:.1f}" cy="{py:.1f}" r="6.5" fill="#FFFBD1"/>')
            k += 1
    return out


def bolt(x, y, s=1.0, rot=0, fill="#FFE14D", t=0):
    flick = 0.6 + 0.4 * (math.sin(t * 40) > 0)
    return (f'<g transform="translate({x},{y}) rotate({rot}) scale({s})" opacity="{flick:.2f}">'
            '<path d="M18,-70 L-26,6 L-2,6 L-14,70 L30,-8 L6,-8 Z" fill="#FFF3A8" stroke="#E0A800" stroke-width="5" stroke-linejoin="round"/></g>')


def starburst(x, y, r, t, fill="#FFE14D", points=12, spin=40):
    pts = []
    for k in range(points * 2):
        rr = r if k % 2 == 0 else r * 0.55
        a = math.radians(k * 180 / points + t * spin)
        pts.append(f"{x+rr*math.cos(a):.1f},{y+rr*math.sin(a):.1f}")
    return (f'<circle cx="{x}" cy="{y}" r="{r*1.5:.0f}" fill="url(#glowR)"/>'
            f'<polygon points="{" ".join(pts)}" fill="{fill}" stroke="#FF6B2C" stroke-width="5"/>')


def arc(x1, y1, x2, y2, t, color="#BDF3FF", seed=0, segs=9, amp=22, w=6):
    rnd = random.Random(int(t * 24) * 131 + seed)
    pts = []
    for k in range(segs + 1):
        f = k / segs
        off = 0 if k in (0, segs) else rnd.uniform(-amp, amp)
        pts.append(f"{x1+(x2-x1)*f+off:.1f},{y1+(y2-y1)*f+rnd.uniform(-amp,amp)*(k not in (0,segs)):.1f}")
    p = " ".join(pts)
    return (f'<polyline points="{p}" fill="none" stroke="#4DD8FF" stroke-width="{w*2.4}" opacity=".35" stroke-linejoin="round"/>'
            f'<polyline points="{p}" fill="none" stroke="{color}" stroke-width="{w}" stroke-linejoin="round"/>')
