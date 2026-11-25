"""Cápsula tipo Orion (diseño genérico, sin logotipos), plasma de reentrada, paracaídas y cohete."""
import math
import random
from ..core import n


def capsule_body(glow=0.0, t=0.0):
    """Origen = centro; el escudo térmico queda en +y (hacia donde viaja en la reentrada)."""
    edge = f'<path d="M-98,66 L98,66 Q108,76 96,90 Q40,118 0,118 Q-40,118 -96,90 Q-108,76 -98,66 Z" fill="none" stroke="#FF8A3D" stroke-width="7" opacity="{glow:.2f}"/>' if glow > 0 else ""
    return ('<path d="M-34,-118 Q-34,-124 -26,-126 L26,-126 Q34,-124 34,-118 L98,56 Q102,70 88,74 L-88,74 Q-102,70 -98,56 Z" fill="url(#suit)" stroke="#6B7690" stroke-width="4"/>'
            '<rect x="-24" y="-140" width="48" height="16" rx="5" fill="#AEB8CC" stroke="#6B7690" stroke-width="3"/>'
            '<path d="M-26,-60 L26,-60 M-48,-6 L48,-6" stroke="#9AA6BA" stroke-width="3"/>'
            '<rect x="-30" y="-92" width="60" height="22" rx="11" fill="url(#visor)" stroke="#0B1030" stroke-width="3"/>'
            '<circle cx="-60" cy="30" r="6" fill="#E4572E"/><circle cx="60" cy="30" r="6" fill="#E4572E"/>'
            '<path d="M-98,66 L98,66 Q108,76 96,90 Q40,118 0,118 Q-40,118 -96,90 Q-108,76 -98,66 Z" fill="url(#avcoat)" stroke="#1E140F" stroke-width="4"/>'
            '<path d="M-60,72 Q0,96 60,72 M-80,82 Q0,108 80,82 M0,70 L0,112" fill="none" stroke="#1E140F" stroke-width="2.5" opacity=".6"/>' + edge)


def plasma_back(t, power=1.0):
    """Resplandor y estela de plasma (se dibuja detrás de la cápsula)."""
    rnd = random.Random(4)
    out = f'<circle cx="0" cy="120" r="{300*power:.0f}" fill="url(#plasma)" opacity="{.9*power:.2f}"/>'
    for j in range(18):
        x = -120 + j * 14 + rnd.uniform(-5, 5)
        L = (360 + 260 * abs(math.sin(t * 8 + j * 1.3))) * power
        w = rnd.choice([10, 14, 18])
        col = "#FFB347" if j % 3 else "#FFE9A8"
        out += f'<line x1="{x:.0f}" y1="-20" x2="{x*1.5:.0f}" y2="{-20-L:.0f}" stroke="{col}" stroke-width="{w}" stroke-linecap="round" opacity="{.28*power:.2f}"/>'
    for j in range(7):
        x = -70 + j * 24
        L = (240 + 160 * abs(math.sin(t * 11 + j))) * power
        out += f'<line x1="{x}" y1="0" x2="{x*1.2:.0f}" y2="{-L:.0f}" stroke="#fff" stroke-width="8" stroke-linecap="round" opacity="{.35*power:.2f}"/>'
    return out


def plasma_front(t, power=1.0):
    """Capa de choque brillante delante del escudo."""
    k = .85 + .15 * math.sin(t * 20)
    return (f'<path d="M-170,52 Q0,{250*power:.0f} 170,52" fill="none" stroke="#FFD27A" stroke-width="{22*k:.0f}" stroke-linecap="round" opacity="{.8*power:.2f}"/>'
            f'<path d="M-150,56 Q0,{220*power:.0f} 150,56" fill="none" stroke="#fff" stroke-width="{9*k:.0f}" stroke-linecap="round" opacity="{.9*power:.2f}"/>')


def capsule(x, y, s, phi_deg, t, plasma=1.0, glow=None):
    """Cápsula viajando hacia la dirección phi (grados, 0 = derecha, 90 = abajo), escudo por delante."""
    rot = phi_deg - 90
    g = plasma if glow is None else glow
    body = (plasma_back(t, plasma) if plasma > 0 else "") + capsule_body(g, t) + (plasma_front(t, plasma) if plasma > 0 else "")
    return f'<g transform="translate({x:.1f},{y:.1f}) rotate({rot:.1f}) scale({s})">{body}</g>'


def parachute(x, y, w, h, t, col="#FF7A1A", deployed=1.0, sway=0.0):
    """Paracaídas (cúpula) con cuerdas hacia (x, y+h+len)."""
    ww = w * deployed; hh = h * deployed
    sw = sway * math.sin(t * 2)
    out = (f'<path d="M{x-ww:.0f},{y:.0f} Q{x+sw:.0f},{y-hh*1.9:.0f} {x+ww:.0f},{y:.0f} Q{x+ww*.5:.0f},{y+hh*.18:.0f} {x:.0f},{y+hh*.1:.0f} Q{x-ww*.5:.0f},{y+hh*.18:.0f} {x-ww:.0f},{y:.0f} Z" fill="{col}" stroke="#7A2A12" stroke-width="3"/>'
           f'<path d="M{x-ww*.5:.0f},{y-hh*.2:.0f} Q{x:.0f},{y-hh*1.5:.0f} {x+ww*.5:.0f},{y-hh*.2:.0f}" fill="none" stroke="#fff" stroke-width="5" opacity=".8"/>')
    return out


def rocket(x, y, s, t, flame=1.0, stage1=True, stage2=True, rot=0.0):
    """Cohete genérico de dos etapas con cápsula en la punta (origen = base de la etapa 1, apunta hacia -y)."""
    out = ""
    if stage1:
        fl = (.8 + .2 * math.sin(t * 30)) * flame
        out += (f'<polygon points="-26,0 26,0 0,{230*fl:.0f}" fill="#FFB347" opacity=".9"/><polygon points="-14,0 14,0 0,{150*fl:.0f}" fill="#FFF3C4"/>'
                '<rect x="-34" y="-260" width="68" height="260" rx="6" fill="url(#suit)" stroke="#6B7690" stroke-width="3"/><rect x="-34" y="-100" width="68" height="14" fill="#E4572E"/>'
                '<polygon points="-34,-8 -62,24 -34,-50" fill="#AEB8CC"/><polygon points="34,-8 62,24 34,-50" fill="#AEB8CC"/>')
    if stage2:
        out += ('<rect x="-30" y="-440" width="60" height="180" rx="6" fill="url(#suit)" stroke="#6B7690" stroke-width="3"/>'
                '<path d="M-30,-440 L-12,-500 L12,-500 L30,-440 Z" fill="#AEB8CC" stroke="#6B7690" stroke-width="3"/><rect x="-8" y="-518" width="16" height="20" fill="#E4572E"/>')
    return f'<g transform="translate({x:.0f},{y:.0f}) rotate({rot:.1f}) scale({s})">{out}</g>'


def booster(x, y, s, t, legs=0.0, flame=1.0, rot=0.0):
    """Propulsor aterrizando (origen = base, apunta hacia -y; las patas se despliegan con legs 0..1)."""
    fl = (.8 + .2 * math.sin(t * 34)) * flame
    out = ''
    if flame > 0:
        out += f'<polygon points="-22,0 22,0 0,{200*fl:.0f}" fill="#FFB347" opacity=".9"/><polygon points="-12,0 12,0 0,{130*fl:.0f}" fill="#FFF3C4"/>'
    for sx in (-1, 1):
        out += f'<line x1="{sx*30}" y1="-10" x2="{sx*(30+70*legs):.0f}" y2="{40*legs:.0f}" stroke="#6B7690" stroke-width="9" stroke-linecap="round"/><line x1="{sx*(30+70*legs):.0f}" y1="{40*legs:.0f}" x2="{sx*(30+90*legs):.0f}" y2="{40*legs:.0f}" stroke="#6B7690" stroke-width="10" stroke-linecap="round"/>'
    out += ('<rect x="-30" y="-290" width="60" height="290" rx="6" fill="url(#suit)" stroke="#6B7690" stroke-width="3"/><rect x="-30" y="-120" width="60" height="12" fill="#E4572E"/>'
            '<rect x="-30" y="-290" width="60" height="22" rx="6" fill="#3A4256"/>')
    return f'<g transform="translate({x:.0f},{y:.0f}) rotate({rot:.1f}) scale({s})">{out}</g>'
