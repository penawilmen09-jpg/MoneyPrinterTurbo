"""Subtítulos por palabras: fragmentación, sincronía y render con resaltado."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

from PIL import Image, ImageDraw

from .gfx import ease_out_back, font

HIGHLIGHT = (255, 214, 60)
WHITE = (255, 255, 255)
MAX_CHARS_LINE = 20
MAX_WORDS_CHUNK = 4
# Zona segura vertical (centro de la caja de subtítulos) en un lienzo de 1920 px:
# por encima de la interfaz inferior de TikTok/Shorts y por debajo de los rostros.
SUBTITLE_CENTER_Y = 0.755


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(ch for ch in s if unicodedata.category(ch) != "Mn")


def _word_weight(word: str) -> float:
    w = len(re.sub(r"\W", "", word)) + 1.5
    if word.endswith((",", ";", ":")):
        w += 3
    if word.endswith((".", "?", "!", "…")):
        w += 6
    return w


@dataclass
class Caption:
    start: float
    end: float
    words: list[tuple[str, bool]] = field(default_factory=list)

    @property
    def text(self) -> str:
        return " ".join(w for w, _ in self.words)


def _is_emphasis(word: str) -> bool:
    bare = re.sub(r"[^\wÁÉÍÓÚÑáéíóúñ$%]", "", word)
    if not bare:
        return False
    if re.search(r"\d", bare) or "$" in bare or "%" in bare:
        return True
    return len(bare) > 2 and bare.isupper()


def build_captions(narration: str, speech_start: float, speech_end: float,
                   keywords: list[str] | None = None) -> list[Caption]:
    """Reparte el texto en subtítulos de 2–4 palabras con tiempos proporcionales."""
    words = narration.split()
    if not words:
        return []
    speech_end = max(speech_end, speech_start + 0.4)
    weights = [_word_weight(w) for w in words]
    total = sum(weights)
    span = speech_end - speech_start
    t = speech_start
    timed: list[tuple[str, float, float]] = []
    for w, wt in zip(words, weights):
        dt = span * wt / total
        timed.append((w, t, t + dt))
        t += dt

    kw = {_norm(re.sub(r"[^\w]", "", k)) for k in (keywords or []) for k in k.split()}
    kw.discard("")

    chunks: list[list[tuple[str, float, float]]] = []
    cur: list[tuple[str, float, float]] = []
    chars = 0
    for item in timed:
        w = item[0]
        if cur and (len(cur) >= MAX_WORDS_CHUNK or chars + len(w) + 1 > MAX_CHARS_LINE * 2 - 6):
            chunks.append(cur)
            cur, chars = [], 0
        cur.append(item)
        chars += len(w) + 1
        if w.endswith((".", "?", "!", "…", ",", ";", ":")) and len(cur) >= 2:
            chunks.append(cur)
            cur, chars = [], 0
    if cur:
        chunks.append(cur)
    # evita chunks de una sola palabra corta pegándolos al anterior
    merged: list[list[tuple[str, float, float]]] = []
    for ch in chunks:
        if merged and len(ch) == 1 and len(ch[0][0]) <= 4 and len(merged[-1]) < MAX_WORDS_CHUNK:
            merged[-1].extend(ch)
        else:
            merged.append(ch)

    captions: list[Caption] = []
    for i, ch in enumerate(merged):
        start = ch[0][1]
        end = merged[i + 1][0][1] if i + 1 < len(merged) else ch[-1][2]
        flags = []
        for w, _, _ in ch:
            bare = _norm(re.sub(r"[^\w]", "", w))
            flags.append(bare in kw or _is_emphasis(w))
        if not any(flags):
            longest = max(range(len(ch)), key=lambda j: len(re.sub(r"\W", "", ch[j][0])))
            if len(re.sub(r"\W", "", ch[longest][0])) >= 6:
                flags[longest] = True
        captions.append(Caption(start, max(end, start + 0.25), [(w, fl) for (w, _, _), fl in zip(ch, flags)]))
    return captions


class CaptionRenderer:
    """Renderiza un subtítulo (con caché) como capa RGBA lista para pegar."""

    def __init__(self, frame_w: int, frame_h: int):
        self.fw, self.fh = frame_w, frame_h
        self.px = frame_w / 1080
        self._cache: dict[tuple, Image.Image] = {}

    def _lines(self, words, fnt, probe, max_w):
        lines, cur, cur_w = [], [], 0.0
        space = probe.textlength(" ", font=fnt)
        for w, hl in words:
            ww = probe.textlength(w, font=fnt)
            if cur and cur_w + space + ww > max_w:
                lines.append(cur)
                cur, cur_w = [], 0.0
            cur.append((w, hl, ww))
            cur_w += (space if len(cur) > 1 else 0) + ww
        if cur:
            lines.append(cur)
        return lines

    def image(self, cap: Caption) -> Image.Image:
        key = (cap.start, tuple(cap.words))
        if key in self._cache:
            return self._cache[key]
        ss = 2
        fs = int(76 * self.px)
        fnt = font(fs * ss)
        probe = ImageDraw.Draw(Image.new("L", (4, 4)))
        max_w = int(900 * self.px) * ss
        lines = self._lines(cap.words, fnt, probe, max_w)
        lh = int(fs * 1.28) * ss
        pad_x, pad_y = int(34 * self.px) * ss, int(22 * self.px) * ss
        box_w = int(max(sum(l[2] for l in ln) + probe.textlength(" ", font=fnt) * (len(ln) - 1) for ln in lines)) + pad_x * 2
        box_h = lh * len(lines) + pad_y * 2
        layer = Image.new("RGBA", (box_w, box_h), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        d.rounded_rectangle([0, 0, box_w - 1, box_h - 1], radius=int(34 * self.px) * ss, fill=(10, 12, 22, 165))
        space = probe.textlength(" ", font=fnt)
        for li, ln in enumerate(lines):
            line_w = sum(w for _, _, w in ln) + space * (len(ln) - 1)
            x = (box_w - line_w) / 2
            y = pad_y + li * lh + lh / 2
            for w, hl, ww in ln:
                d.text((x, y), w, font=fnt, fill=HIGHLIGHT if hl else WHITE, anchor="lm",
                       stroke_width=int(5 * self.px) * ss, stroke_fill=(15, 15, 25))
                x += ww + space
        layer = layer.resize((box_w // ss, box_h // ss), Image.LANCZOS)
        self._cache[key] = layer
        return layer

    def paste(self, frame: Image.Image, cap: Caption, t: float) -> None:
        img = self.image(cap)
        k = ease_out_back((t - cap.start) / 0.14)
        k = 0.9 + 0.1 * min(1.15, max(0.0, k))
        if abs(k - 1.0) > 0.005:
            img = img.resize((max(2, int(img.width * k)), max(2, int(img.height * k))), Image.BILINEAR)
        cx, cy = self.fw / 2, self.fh * SUBTITLE_CENTER_Y
        frame.paste(img, (int(cx - img.width / 2), int(cy - img.height / 2)), img)

    @property
    def safe_box(self) -> tuple[float, float, float, float]:
        """Caja máxima aproximada (para comprobar que no tapa rostros)."""
        cy = self.fh * SUBTITLE_CENTER_Y
        return (self.fw * 0.04, cy - 150 * self.px, self.fw * 0.96, cy + 150 * self.px)


def active_caption(captions: list[Caption], t: float) -> Caption | None:
    for c in captions:
        if c.start <= t < c.end:
            return c
    return None


def captions_to_srt(scenes_captions: list[tuple[float, list[Caption]]]) -> str:
    """``scenes_captions`` = [(offset_escena, [Caption...])]."""

    def ts(x: float) -> str:
        ms = int(round(x * 1000))
        h, ms = divmod(ms, 3600000)
        m, ms = divmod(ms, 60000)
        s, ms = divmod(ms, 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    out, n = [], 1
    for offset, caps in scenes_captions:
        for c in caps:
            out.append(f"{n}\n{ts(offset + c.start)} --> {ts(offset + c.end)}\n{c.text}\n")
            n += 1
    return "\n".join(out)
