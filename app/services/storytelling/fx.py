"""Elementos gráficos animados: bocadillos, popups, contadores, resaltados."""

from __future__ import annotations

import math
import re

from PIL import Image, ImageDraw

from .gfx import aa_layer, ease, ease_out_back, font, shade

OUT = (34, 28, 44)
STYLES = {
    "alert": ((232, 72, 60), (255, 255, 255)),
    "info": ((64, 140, 220), (255, 255, 255)),
    "money": ((60, 170, 100), (255, 255, 255)),
    "good": ((250, 214, 72), (60, 40, 10)),
}


def _wrap(text: str, fnt, max_w: int) -> list[str]:
    words, lines, cur = text.split(), [], ""
    probe = ImageDraw.Draw(Image.new("L", (4, 4)))
    for w in words:
        trial = (cur + " " + w).strip()
        if probe.textlength(trial, font=fnt) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines or [""]


def speech_bubble(frame: Image.Image, anchor: tuple[float, float], text: str, tl: float,
                  px: float = 1.0, thought: bool = False, side: int = 1) -> None:
    """Bocadillo con cola hacia ``anchor`` (boca). ``tl`` = segundos desde que aparece."""
    k = ease_out_back(tl / 0.28)
    if k <= 0.02:
        return
    fs = int(42 * px)
    fnt = font(fs)
    lines = _wrap(text, fnt, int(440 * px))
    probe = ImageDraw.Draw(Image.new("L", (4, 4)))
    tw = max(probe.textlength(l, font=fnt) for l in lines)
    lh = fs * 1.22
    bw, bh = tw + 56 * px, lh * len(lines) + 40 * px
    ax, ay = anchor
    # la burbuja se sitúa arriba, desplazada hacia el centro de la pantalla
    bx = max(24 * px, min(frame.width - bw - 24 * px, ax - bw * (0.5 - 0.12 * side)))
    by = max(150 * px, ay - 330 * px - bh * 0.1)
    size = (int(bw + 60 * px), int(bh + 120 * px))
    ox, oy = int(bx - 30 * px), int(by - 10 * px)

    def draw(d, ss):
        x0, y0 = 30 * px * ss, 10 * px * ss
        x1, y1 = x0 + bw * ss, y0 + bh * ss
        tail_x = (ax - ox) * ss
        tail_y = (ay - oy - 40 * px) * ss
        mid = min(max(tail_x, x0 + 40 * px * ss), x1 - 40 * px * ss)
        d.polygon([(mid - 26 * px * ss, y1 - 4 * ss), (mid + 26 * px * ss, y1 - 4 * ss), (tail_x, min(tail_y, y1 + 100 * px * ss))],
                  fill=(255, 255, 255), outline=OUT)
        d.rounded_rectangle([x0, y0, x1, y1], radius=26 * px * ss, fill=(255, 255, 255), outline=OUT, width=int(5 * px * ss))
        d.polygon([(mid - 22 * px * ss, y1 - 3 * ss), (mid + 22 * px * ss, y1 - 3 * ss), (tail_x, min(tail_y, y1 + 100 * px * ss) - 3 * ss)],
                  fill=(255, 255, 255))
        for i, line in enumerate(lines):
            d.text(((x0 + x1) / 2, y0 + 20 * px * ss + (i + 0.5) * lh * ss), line, font=font(fs * ss), fill=OUT, anchor="mm")

    layer = aa_layer(size, draw, ss=2)
    if k != 1:
        nw, nh = max(2, int(size[0] * min(k, 1.15))), max(2, int(size[1] * min(k, 1.15)))
        layer = layer.resize((nw, nh), Image.BILINEAR)
        ox += (size[0] - nw) // 2
        oy += size[1] - nh
    frame.paste(layer, (ox, oy), layer)


def _parse_number(text: str):
    m = re.search(r"(\d[\d.,]*)", text)
    if not m:
        return None
    raw = m.group(1).replace(",", "")
    try:
        val = float(raw)
    except ValueError:
        return None
    pre, post = text[: m.start()], text[m.end():]
    return val, pre, post, ("." in m.group(1) and not m.group(1).endswith("."))


def popup(frame: Image.Image, center: tuple[float, float], text: str, style: str, tl: float,
          dur: float, px: float = 1.0, counter: bool = False) -> None:
    """Etiqueta/pop-up con rebote de entrada, vibración y salida."""
    if tl < 0 or tl > dur:
        return
    k_in = ease_out_back(tl / 0.30)
    k_out = 1.0 - ease(max(0.0, (tl - (dur - 0.25)) / 0.25))
    k = max(0.01, k_in * k_out)
    shown = text
    if counter:
        num = _parse_number(text)
        if num:
            val, pre, post, is_float = num
            f = ease(min(1.0, tl / max(0.6, dur * 0.7)))
            cur = val * f
            shown = f"{pre}{cur:,.2f}{post}" if is_float else f"{pre}{int(round(cur)):,}{post}"
    bg, fg = STYLES.get(style, STYLES["alert"])
    fs = int((86 if len(shown) <= 6 else 62) * px)
    fnt = font(fs)
    probe = ImageDraw.Draw(Image.new("L", (4, 4)))
    tw = probe.textlength(shown, font=fnt)
    w, h = int(tw + 90 * px), int(fs * 1.5)
    size = (w + 40, h + 40)

    def draw(d, ss):
        x0, y0, x1, y1 = 20 * ss, 20 * ss, (20 + w) * ss, (20 + h) * ss
        d.rounded_rectangle([x0 + 6 * ss, y0 + 8 * ss, x1 + 6 * ss, y1 + 8 * ss], radius=h * 0.32 * ss, fill=(0, 0, 0, 70))
        d.rounded_rectangle([x0, y0, x1, y1], radius=h * 0.32 * ss, fill=bg, outline=OUT, width=int(6 * ss))
        d.text(((x0 + x1) / 2, (y0 + y1) / 2 - 2 * ss), shown, font=font(fs * ss), fill=fg, anchor="mm",
               stroke_width=int(2 * ss), stroke_fill=shade(bg, 0.6) if fg == (255, 255, 255) else None)

    layer = aa_layer(size, draw, ss=2)
    shake = math.sin(tl * 38) * 3 * px if tl < 0.7 and style == "alert" else 0
    rot = math.sin(tl * 9) * 3
    nw, nh = max(2, int(size[0] * k)), max(2, int(size[1] * k))
    layer = layer.resize((nw, nh), Image.BILINEAR).rotate(rot, expand=True, resample=Image.BILINEAR)
    frame.paste(layer, (int(center[0] - layer.width / 2 + shake), int(center[1] - layer.height / 2)), layer)


def highlight_ring(frame: Image.Image, center: tuple[float, float], radius: float, tl: float, dur: float,
                   style: str = "alert") -> None:
    if tl < 0 or tl > dur:
        return
    col = STYLES.get(style, STYLES["alert"])[0]
    k = ease_out_back(tl / 0.3) * (1 - ease(max(0.0, (tl - (dur - 0.25)) / 0.25)))
    pulse = 1 + 0.06 * math.sin(tl * 9)
    r = max(4.0, radius * k * pulse)
    size = int(r * 2 + 60)

    def draw(d, ss):
        c = size * ss / 2
        d.ellipse([c - r * ss, c - r * ss, c + r * ss, c + r * ss], outline=OUT, width=int(16 * ss))
        d.ellipse([c - r * ss, c - r * ss, c + r * ss, c + r * ss], outline=col, width=int(9 * ss))

    layer = aa_layer((size, size), draw, 2)
    frame.paste(layer, (int(center[0] - size / 2), int(center[1] - size / 2)), layer)


def arrow(frame: Image.Image, tip: tuple[float, float], tl: float, dur: float, style: str = "alert", px: float = 1.0) -> None:
    if tl < 0 or tl > dur:
        return
    col = STYLES.get(style, STYLES["alert"])[0]
    bounce = abs(math.sin(tl * 6)) * 30 * px
    k = ease_out_back(tl / 0.3) * (1 - ease(max(0.0, (tl - (dur - 0.25)) / 0.25)))
    L = int(170 * px)
    size = (int(120 * px), L + int(40 * px))

    def draw(d, ss):
        cx = size[0] * ss / 2
        pts = [(cx, (L + 30 * px) * ss), (cx - 55 * px * ss, (L - 50 * px) * ss), (cx - 22 * px * ss, (L - 50 * px) * ss),
               (cx - 22 * px * ss, 6 * ss), (cx + 22 * px * ss, 6 * ss), (cx + 22 * px * ss, (L - 50 * px) * ss),
               (cx + 55 * px * ss, (L - 50 * px) * ss)]
        d.polygon(pts, fill=col, outline=OUT)
        d.line(pts + [pts[0]], fill=OUT, width=int(6 * ss), joint="curve")

    layer = aa_layer(size, draw, 2)
    nh = max(2, int(layer.height * max(0.01, k)))
    layer = layer.resize((layer.width, nh), Image.BILINEAR)
    frame.paste(layer, (int(tip[0] - layer.width / 2), int(tip[1] - layer.height - bounce + 10 * px)), layer)


def flash(frame: Image.Image, tl: float, dur: float = 0.25, color=(255, 255, 255)) -> Image.Image:
    if tl < 0 or tl > dur:
        return frame
    a = (1 - tl / dur) * 0.75
    return Image.blend(frame, Image.new("RGB", frame.size, color), a)


def hook_title(frame: Image.Image, text: str, tl: float, dur: float, px: float = 1.0) -> None:
    """Tarjeta de gancho de los primeros segundos (arriba, sin tapar rostros)."""
    if tl < 0 or tl > dur:
        return
    k_in = ease_out_back(tl / 0.35)
    k_out = 1.0 - ease(max(0.0, (tl - (dur - 0.3)) / 0.3))
    k = max(0.01, k_in * k_out)
    fs = int(70 * px)
    fnt = font(fs)
    lines = _wrap(text.upper(), fnt, int(900 * px))
    lh = fs * 1.18
    w = int(1000 * px)
    h = int(lh * len(lines) + 56 * px)
    size = (w + 40, h + 40)

    def draw(d, ss):
        x0, y0, x1, y1 = 20 * ss, 20 * ss, (20 + w) * ss, (20 + h) * ss
        d.rounded_rectangle([x0 + 8 * ss, y0 + 10 * ss, x1 + 8 * ss, y1 + 10 * ss], radius=34 * ss, fill=(0, 0, 0, 90))
        d.rounded_rectangle([x0, y0, x1, y1], radius=34 * ss, fill=(250, 214, 72), outline=OUT, width=int(7 * ss))
        for i, line in enumerate(lines):
            d.text(((x0 + x1) / 2, y0 + 28 * px * ss + (i + 0.5) * lh * ss), line, font=font(fs * ss), fill=(40, 28, 20), anchor="mm")

    layer = aa_layer(size, draw, 2)
    nw, nh = max(2, int(size[0] * k)), max(2, int(size[1] * k))
    layer = layer.resize((nw, nh), Image.BILINEAR)
    frame.paste(layer, (int(frame.width / 2 - nw / 2), int(300 * px - nh / 2)), layer)


def brand_tag(frame: Image.Image, px: float = 1.0) -> None:
    fs = int(30 * px)
    fnt = font(fs)
    s = "EXPLORA CIENCIA 360"
    probe = ImageDraw.Draw(Image.new("L", (4, 4)))
    tw = probe.textlength(s, font=fnt)
    w, h = int(tw + 40 * px), int(fs * 1.7)
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=h // 2, fill=(20, 24, 40, 190))
    d.text((w / 2, h / 2 - 1), s, font=fnt, fill=(255, 255, 255), anchor="mm")
    frame.paste(layer, (int(34 * px), int(112 * px)), layer)


def disclaimer(frame: Image.Image, text: str, tl: float, px: float = 1.0) -> None:
    fs = int(28 * px)
    fnt = font(fs, bold=False)
    probe = ImageDraw.Draw(Image.new("L", (4, 4)))
    tw = probe.textlength(text, font=fnt)
    w, h = int(tw + 36 * px), int(fs * 1.8)
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=h // 2, fill=(0, 0, 0, 150))
    d.text((w / 2, h / 2 - 1), text, font=fnt, fill=(255, 255, 255, 235), anchor="mm")
    frame.paste(layer, (int(34 * px), int(172 * px)), layer)
