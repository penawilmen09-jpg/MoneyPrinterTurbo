"""Piezas de diagramas técnicos: rejilla, batería, bombilla, interruptor, tanques."""
import math
from ..core import W, H, n


def grid(t=0):
    out = '<g stroke="#3E73C4" stroke-width="1.5" opacity=".28">'
    for x in range(0, W + 1, 60):
        out += f'<line x1="{x}" y1="0" x2="{x}" y2="{H}"/>'
    for y in range(0, H + 1, 60):
        out += f'<line x1="0" y1="{y}" x2="{W}" y2="{y}"/>'
    return out + '</g>'


def rect_point(s, x0, y0, x1, y1):
    """Punto sobre un rectángulo recorrido en sentido horario desde (x0,y0)."""
    w, h = x1 - x0, y1 - y0
    P = 2 * (w + h)
    s %= P
    if s < w:
        return x0 + s, y0
    s -= w
    if s < h:
        return x1, y0 + s
    s -= h
    if s < w:
        return x1 - s, y1
    s -= w
    return x0, y1 - s


def battery(x, y, t=0):
    return (f'<rect x="{x-70}" y="{y-110}" width="140" height="220" fill="#0A1F44"/>'
            f'<line x1="{x-60}" y1="{y-30}" x2="{x+60}" y2="{y-30}" stroke="#fff" stroke-width="12" stroke-linecap="round"/>'
            f'<line x1="{x-34}" y1="{y+30}" x2="{x+34}" y2="{y+30}" stroke="#fff" stroke-width="12" stroke-linecap="round"/>'
            f'<circle cx="{x+95}" cy="{y-30}" r="26" fill="#FF4D6D"/>'
            f'<text x="{x+95}" y="{y-16}" text-anchor="middle" font-family="DejaVu Sans" font-weight="bold" font-size="42" fill="#fff">+</text>'
            f'<circle cx="{x+95}" cy="{y+30}" r="26" fill="#4DA3FF"/>'
            f'<text x="{x+95}" y="{y+43}" text-anchor="middle" font-family="DejaVu Sans" font-weight="bold" font-size="46" fill="#fff">−</text>')


def bulb(x, y, on, t=0):
    glow = ""
    if on:
        pulse = 1 + 0.06 * math.sin(t * 14)
        glow = f'<circle cx="{x}" cy="{y}" r="{170*pulse:.0f}" fill="url(#glowY)"/>'
    fill = "#FFF3A0" if on else "#9BB3D6"
    return (glow +
            f'<circle cx="{x}" cy="{y-10}" r="62" fill="{fill}" stroke="#E8F0FF" stroke-width="6"/>'
            f'<rect x="{x-30}" y="{y+44}" width="60" height="44" rx="8" fill="#9FB0C8"/>'
            f'<path d="M{x-24},{y+30} L{x-14},{y-20} L{x},{y+10} L{x+14},{y-20} L{x+24},{y+30}" fill="none" stroke="{"#FF8A00" if on else "#5B6B8C"}" stroke-width="6" stroke-linejoin="round"/>')


def tank(x0, x1, ybot, height, level, label=""):
    w = x1 - x0
    out = ""
    if level > 0:
        out += (f'<rect x="{x0+6}" y="{ybot-level:.1f}" width="{w-12}" height="{level:.1f}" fill="url(#water)" opacity=".95"/>'
                f'<rect x="{x0+6}" y="{ybot-level-5:.1f}" width="{w-12}" height="10" fill="#C6EEFF" opacity=".8"/>')
    out += (f'<path d="M{x0},{ybot-height} L{x0},{ybot} L{x1},{ybot} L{x1},{ybot-height}" fill="none" '
            f'stroke="#E8F0FF" stroke-width="10" stroke-linejoin="round" stroke-linecap="round"/>')
    return out
