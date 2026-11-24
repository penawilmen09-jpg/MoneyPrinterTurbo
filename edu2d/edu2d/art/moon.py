"""Luna procedural (textura + sombreado esférico con numpy), personaje y fauna nocturna."""
import base64
import io
import math
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


@lru_cache(maxsize=16)
def moon_uri(size=480, lx=-.45, ly=.35):
    rng = np.random.default_rng(7)
    S = size
    base = np.asarray(Image.fromarray((rng.random((18, 18)) * 255).astype(np.uint8)).resize((S, S), Image.BICUBIC), dtype=np.float32) / 255
    fine = np.asarray(Image.fromarray((rng.random((90, 90)) * 255).astype(np.uint8)).resize((S, S), Image.BICUBIC), dtype=np.float32) / 255
    alb = 188 + 22 * base + 12 * fine
    mar = Image.new("L", (S, S), 0); d = ImageDraw.Draw(mar)
    for (cx, cy, rx, ry) in [(.38, .34, .20, .15), (.60, .30, .12, .10), (.62, .52, .15, .13), (.45, .58, .10, .08), (.30, .55, .08, .10), (.70, .68, .09, .07)]:
        d.ellipse([(cx - rx) * S, (cy - ry) * S, (cx + rx) * S, (cy + ry) * S], fill=255)
    mar = np.asarray(mar.filter(ImageFilter.GaussianBlur(S * .025)), dtype=np.float32)[..., None] / 255
    col = np.repeat(alb[..., None], 3, -1) * np.array([1, 1, 1.02])
    col = col * (1 - mar * .42) + mar * .42 * np.array([96, 100, 112])
    # cráteres con borde iluminado
    yy, xx = np.mgrid[0:S, 0:S]
    for _ in range(46):
        cx, cy = rng.uniform(.12, .88, 2) * S
        r = rng.uniform(.012, .055) * S
        dist = np.hypot(xx - cx, yy - cy)
        inside = dist < r
        rim = (np.abs(dist - r) < max(1.5, r * .12))
        col[inside] *= .86
        col[rim] += 22 * (1 if rng.random() > .5 else .5)
    # esfera
    r = S / 2
    x = (xx + .5 - r) / r; y = -(yy + .5 - r) / r
    rr = x * x + y * y; z = np.sqrt(np.clip(1 - rr, 0, 1))
    L = np.array([lx, ly, .8]); L /= np.linalg.norm(L)
    lam = np.clip(x * L[0] + y * L[1] + z * L[2], 0, 1)
    shade = .28 + .72 * lam ** .8
    out = np.clip(col * shade[..., None], 0, 255)
    rgba = np.zeros((S, S, 4), np.uint8)
    rgba[..., :3] = out.astype(np.uint8)
    rgba[..., 3] = (np.clip((1 - np.sqrt(rr)) * r * .9, 0, 1) * 255).astype(np.uint8)
    buf = io.BytesIO(); Image.fromarray(rgba, "RGBA").save(buf, "PNG", compress_level=1)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def moon(cx, cy, R, glow=1.0, op=1.0):
    uri = moon_uri(int(min(max(2 * R, 120), 640)))
    g = f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{R*2.1:.0f}" fill="url(#moonGlow)" opacity="{glow*op:.2f}"/>' if glow > 0 else ""
    return g + f'<image href="{uri}" x="{cx-R:.1f}" y="{cy-R:.1f}" width="{2*R:.1f}" height="{2*R:.1f}" opacity="{op:.2f}"/>'


def person(x, y, s=1.0, t=0.0, expr="neutral", arms="down", head_tilt=0.0, shirt="#E4572E"):
    """Persona de perfil mirando a la derecha; origen = pies."""
    arm = {"down": (-6, 8), "up": (-150, -168), "point": (-128, 8), "cheeks": (-160, -150)}[arms]
    blink = (t % 3.4) < .12
    if expr == "surprised":
        eye = '<circle cx="14" cy="-206" r="9" fill="#fff" stroke="#222" stroke-width="2.5"/><circle cx="16" cy="-206" r="3.5" fill="#222"/>'
        mouth = '<ellipse cx="22" cy="-184" rx="6" ry="9" fill="#6B2A2A"/>'
        brow = '<path d="M4,-222 Q14,-232 26,-222" stroke="#2B1B12" stroke-width="4" fill="none" stroke-linecap="round"/>'
    else:
        eye = ('<line x1="8" y1="-205" x2="20" y2="-205" stroke="#222" stroke-width="3"/>' if blink else '<circle cx="15" cy="-206" r="4.5" fill="#222"/>')
        mouth = '<path d="M14,-186 Q22,-181 28,-187" stroke="#6B2A2A" stroke-width="3.5" fill="none" stroke-linecap="round"/>'
        brow = '<path d="M6,-218 L24,-216" stroke="#2B1B12" stroke-width="4" stroke-linecap="round"/>'
    return (f'<g transform="translate({x:.1f},{y:.1f}) scale({s})">'
            '<rect x="-22" y="-90" width="19" height="86" rx="8" fill="#27374D"/><rect x="2" y="-90" width="19" height="86" rx="8" fill="#1F2E42"/>'
            '<ellipse cx="-8" cy="-2" rx="22" ry="9" fill="#111"/><ellipse cx="16" cy="-2" rx="22" ry="9" fill="#111"/>'
            f'<rect x="-30" y="-170" width="60" height="96" rx="20" fill="{shirt}"/>'
            f'<g transform="translate(0,-156) rotate({arm[0]:.0f})"><rect x="-8" y="0" width="16" height="76" rx="8" fill="#C74422"/><circle cx="0" cy="82" r="11" fill="#E8B48A"/></g>'
            f'<g transform="translate(4,-156) rotate({arm[1]:.0f})"><rect x="-8" y="0" width="16" height="76" rx="8" fill="{shirt}"/><circle cx="0" cy="82" r="11" fill="#F2C29B"/></g>'
            f'<g transform="translate(0,-172) rotate({head_tilt:.0f})"><rect x="-8" y="-14" width="16" height="22" fill="#E8B48A"/>'
            '<circle cx="6" cy="-32" r="31" fill="#F2C29B"/><circle cx="34" cy="-26" r="8" fill="#F2C29B"/>'
            '<path d="M-26,-30 Q-26,-72 8,-70 Q34,-68 36,-44 Q20,-58 0,-52 Q-14,-46 -20,-24 Z" fill="#3A2412"/>'
            f'<g transform="translate(0,172)">{eye}{brow}{mouth}</g></g></g>')


def fox(x, y, s, t, flip=False):
    w = math.sin(t * 6)
    return (f'<g transform="translate({x:.1f},{y:.1f}) scale({-s if flip else s},{s})">'
            f'<path d="M-70,-40 Q-130,{-70+22*w:.0f} -150,{-20+10*w:.0f} Q-100,{-20+8*w:.0f} -66,-20 Z" fill="#F08A24"/><path d="M-150,{-20+10*w:.0f} Q-140,{-26+10*w:.0f} -126,{-24+10*w:.0f} L-136,{-8+10*w:.0f} Z" fill="#fff"/>'
            '<ellipse cx="0" cy="-44" rx="76" ry="34" fill="#F08A24"/><ellipse cx="14" cy="-30" rx="50" ry="16" fill="#FFE2BF"/>'
            f'<rect x="-48" y="-30" width="12" height="{34+6*w:.0f}" rx="5" fill="#7A3B0E"/><rect x="-22" y="-30" width="12" height="{34-6*w:.0f}" rx="5" fill="#7A3B0E"/>'
            f'<rect x="26" y="-30" width="12" height="{34-6*w:.0f}" rx="5" fill="#7A3B0E"/><rect x="50" y="-30" width="12" height="{34+6*w:.0f}" rx="5" fill="#7A3B0E"/>'
            '<ellipse cx="82" cy="-66" rx="34" ry="28" fill="#F08A24"/><polygon points="62,-86 70,-120 86,-90" fill="#F08A24"/><polygon points="88,-90 104,-118 108,-84" fill="#F08A24"/>'
            '<ellipse cx="108" cy="-58" rx="20" ry="14" fill="#fff"/><circle cx="124" cy="-62" r="5" fill="#111"/><circle cx="88" cy="-72" r="4.5" fill="#111"/></g>')


def owl(x, y, s, t, look=0.0):
    blink = (t % 4.0) < .15
    ex = 6 * look
    eye = lambda cx: (f'<circle cx="{cx}" cy="-96" r="18" fill="#FFE14D" stroke="#7A5A00" stroke-width="3"/>'
                      + ('' if blink else f'<circle cx="{cx+ex}" cy="-96" r="8" fill="#111"/><circle cx="{cx+ex-2}" cy="-99" r="2.5" fill="#fff"/>')
                      + (f'<rect x="{cx-19}" y="-116" width="38" height="20" fill="#7A4A25"/>' if blink else ''))
    return (f'<g transform="translate({x:.1f},{y:.1f}) scale({s})">'
            '<ellipse cx="0" cy="-50" rx="46" ry="58" fill="#8A5A30"/><ellipse cx="0" cy="-38" rx="28" ry="38" fill="#D9B98A"/>'
            '<polygon points="-34,-130 -22,-104 -44,-100" fill="#7A4A25"/><polygon points="34,-130 22,-104 44,-100" fill="#7A4A25"/>'
            '<circle cx="0" cy="-96" r="44" fill="#9A6A3A"/>' + eye(-18) + eye(18) +
            '<polygon points="-6,-84 6,-84 0,-70" fill="#F3A712"/><rect x="-60" y="2" width="120" height="12" rx="6" fill="#4A2F1B"/>'
            '<path d="M-40,-60 Q-58,-30 -34,-8 Z M40,-60 Q58,-30 34,-8 Z" fill="#6F4624"/></g>')
