"""Utilidades SVG: defs globales, cámara con paralaje, texto."""
from .core import W, H, n, clamp

FONT = "DejaVu Sans"

DEFS = """<defs>
<linearGradient id="skyDay" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#4FA8F0"/><stop offset=".6" stop-color="#A8DCFF"/><stop offset="1" stop-color="#FFEFC2"/></linearGradient>
<linearGradient id="skySunset" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2E2A72"/><stop offset=".45" stop-color="#D9507F"/><stop offset=".8" stop-color="#FF9E5E"/><stop offset="1" stop-color="#FFD58A"/></linearGradient>
<linearGradient id="skyDusk" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3B5BDB"/><stop offset=".55" stop-color="#8E7CC3"/><stop offset="1" stop-color="#FFC48C"/></linearGradient>
<linearGradient id="blueprint" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0A1F44"/><stop offset="1" stop-color="#17407A"/></linearGradient>
<linearGradient id="skyDark" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1A1446"/><stop offset=".6" stop-color="#4B2A7B"/><stop offset="1" stop-color="#C2477A"/></linearGradient>
<linearGradient id="wood" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#6B4423"/><stop offset=".5" stop-color="#9A6A3A"/><stop offset="1" stop-color="#5A3A1E"/></linearGradient>
<linearGradient id="body" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#A9B5CB"/><stop offset="1" stop-color="#7686A3"/></linearGradient>
<linearGradient id="neck" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#34C79A"/><stop offset=".5" stop-color="#5E7CE0"/><stop offset="1" stop-color="#A24FD6"/></linearGradient>
<linearGradient id="water" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#5CC8FF"/><stop offset="1" stop-color="#1E7FD6"/></linearGradient>
<linearGradient id="metal" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#E8EDF5"/><stop offset=".5" stop-color="#9FB0C8"/><stop offset="1" stop-color="#6B7A92"/></linearGradient>
<radialGradient id="glowY"><stop offset="0" stop-color="#FFF6A8" stop-opacity="1"/><stop offset=".35" stop-color="#FFD43B" stop-opacity=".65"/><stop offset="1" stop-color="#FFB300" stop-opacity="0"/></radialGradient>
<radialGradient id="glowR"><stop offset="0" stop-color="#FFFFFF" stop-opacity="1"/><stop offset=".3" stop-color="#FF8A5C" stop-opacity=".8"/><stop offset="1" stop-color="#FF2D55" stop-opacity="0"/></radialGradient>
<radialGradient id="glowC"><stop offset="0" stop-color="#E5FBFF" stop-opacity="1"/><stop offset=".35" stop-color="#4DD8FF" stop-opacity=".6"/><stop offset="1" stop-color="#4DD8FF" stop-opacity="0"/></radialGradient>
<radialGradient id="sun"><stop offset="0" stop-color="#FFFBE0" stop-opacity="1"/><stop offset=".25" stop-color="#FFE48A" stop-opacity=".9"/><stop offset="1" stop-color="#FFC857" stop-opacity="0"/></radialGradient>
<linearGradient id="seaDeep" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#34AEEB"/><stop offset=".5" stop-color="#1B6FB5"/><stop offset="1" stop-color="#0A3470"/></linearGradient>
<linearGradient id="iron" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#C9D1DC"/><stop offset=".5" stop-color="#8C97A8"/><stop offset="1" stop-color="#5D6778"/></linearGradient>
<linearGradient id="airG" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#E9F9FF"/><stop offset="1" stop-color="#BFE8FA"/></linearGradient>
<linearGradient id="sand" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#E8D08A"/><stop offset="1" stop-color="#B8945A"/></linearGradient>
<linearGradient id="heliRed" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#F0604A"/><stop offset="1" stop-color="#C32F22"/></linearGradient>
<linearGradient id="glass" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#D8F2FF"/><stop offset=".6" stop-color="#7EC4F0"/><stop offset="1" stop-color="#4C93CC"/></linearGradient>
<linearGradient id="skyHi" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1F5FC9"/><stop offset=".55" stop-color="#5BB0F5"/><stop offset="1" stop-color="#CFEBFF"/></linearGradient>
<radialGradient id="atmo"><stop offset=".78" stop-color="#5CB8FF" stop-opacity=".55"/><stop offset=".86" stop-color="#5CB8FF" stop-opacity=".2"/><stop offset="1" stop-color="#5CB8FF" stop-opacity="0"/></radialGradient>
<linearGradient id="space" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#05060F"/><stop offset=".6" stop-color="#0B1030"/><stop offset="1" stop-color="#1A1050"/></linearGradient>
</defs>"""


def cam_at(z, fx, fy):
    """Cámara: zoom z, foco (fx,fy) acotado para no mostrar bordes."""
    z = max(1.0, z)
    fx = clamp(fx, W / (2 * z), W - W / (2 * z))
    fy = clamp(fy, H / (2 * z), H - H / (2 * z))
    return (z, fx, fy)


def layer(content, cam, depth=1.0):
    """Capa con paralaje: depth 1 = plano principal, <1 = fondo lejano."""
    z, fx, fy = cam
    ez = 1 + (z - 1) * depth
    cx = W / 2 + (fx - W / 2) * depth
    cy = H / 2 + (fy - H / 2) * depth
    return (f'<g transform="translate({W/2},{H/2}) scale({ez:.4f}) '
            f'translate({-cx:.2f},{-cy:.2f})">{content}</g>')


def text(x, y, s, size=60, fill="#fff", anchor="middle", stroke="#1b1b2f",
         sw=0, opacity=1.0, rot=0, scale=1.0):
    s = s.replace("&", "&amp;").replace("<", "&lt;")
    tr = f'translate({n(x)},{n(y)}) rotate({n(rot)}) scale({n(scale)})'
    base = (f'font-family="{FONT}" font-weight="bold" font-size="{size}" '
            f'text-anchor="{anchor}"')
    out = f'<g transform="{tr}" opacity="{n(opacity)}">'
    if sw:
        out += (f'<text x="0" y="0" {base} fill="none" stroke="{stroke}" '
                f'stroke-width="{sw}" stroke-linejoin="round">{s}</text>')
    out += f'<text x="0" y="0" {base} fill="{fill}">{s}</text></g>'
    return out


def frame_svg(content):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
            f'viewBox="0 0 {W} {H}">{DEFS}{content}</svg>')
