"""Word-synchronised captions drawn inside the vertical safe zone."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from PIL import Image, ImageDraw

from . import gfx as G
from .models import SceneTiming, Word

MAX_WORDS = 4
MAX_CHARS = 30
_BREAK = re.compile(r"[,.;:?!…»)]$")


def norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "", text)


@dataclass
class Cue:
    words: list[Word]
    start: float
    end: float

    @property
    def text(self) -> str:
        return " ".join(w.text for w in self.words)


def build_cues(words: list[Word]) -> list[Cue]:
    cues: list[Cue] = []
    cur: list[Word] = []
    for w in words:
        cur.append(w)
        chars = sum(len(x.text) + 1 for x in cur)
        if len(cur) >= MAX_WORDS or chars >= MAX_CHARS or _BREAK.search(w.text):
            cues.append(Cue(cur, cur[0].start, cur[-1].end))
            cur = []
    if cur:
        if cues and len(cur) == 1 and len(cues[-1].words) < MAX_WORDS:
            cues[-1].words += cur  # avoid orphan one-word cue
            cues[-1].end = cur[-1].end
        else:
            cues.append(Cue(cur, cur[0].start, cur[-1].end))
    return cues


def keyword_flags(words: list[Word], keywords: list[str]) -> list[bool]:
    flags = [False] * len(words)
    nw = [norm(w.text) for w in words]
    for kw in keywords:
        toks = [norm(x) for x in kw.split() if norm(x)]
        if not toks:
            continue
        for i in range(len(nw) - len(toks) + 1):
            if nw[i:i + len(toks)] == toks:
                for j in range(len(toks)):
                    flags[i + j] = True
    return flags


def active_cue(cues: list[Cue], t: float) -> tuple[Cue | None, int]:
    for k, c in enumerate(cues):
        nxt = cues[k + 1].start if k + 1 < len(cues) else c.end + 0.35
        if c.start - 0.04 <= t < min(nxt, c.end + 0.35):
            return c, k
    return None, -1


def _layout(cue: Cue, fnt, max_w: int) -> list[list[tuple[int, Word]]]:
    lines, cur, w_acc = [], [], 0
    space = G.text_size(" ", fnt)[0] or 16
    for i, w in enumerate(cue.words):
        ww = G.text_size(w.text, fnt)[0]
        if cur and w_acc + space + ww > max_w:
            lines.append(cur)
            cur, w_acc = [], 0
        cur.append((i, w))
        w_acc += (space if len(cur) > 1 else 0) + ww
    if cur:
        lines.append(cur)
    return lines


def draw_caption(frame: Image.Image, cues: list[Cue], flags_by_word: dict[int, bool], t: float,
                 words: list[Word], accent=G.AMBER):
    cue, _ = active_cue(cues, t)
    if cue is None:
        return
    d = ImageDraw.Draw(frame, "RGBA")
    fnt = G.font("bold", 66)
    space = G.text_size(" ", fnt)[0] or 16
    lines = _layout(cue, fnt, 880)
    line_h = 92
    total_h = line_h * len(lines)
    y = (G.CAPTION_TOP + G.CAPTION_BOTTOM) / 2 - total_h / 2 + line_h / 2 + 10
    fade = G.clamp((t - (cue.start - 0.04)) / 0.12)
    for line in lines:
        widths = [G.text_size(w.text, fnt)[0] for _, w in line]
        total_w = sum(widths) + space * (len(line) - 1)
        x = (G.W - total_w) / 2
        d.rounded_rectangle([x - 26, y - 46, x + total_w + 26, y + 46], radius=34, fill=(6, 10, 24, int(150 * fade)))
        for (i, w), ww in zip(line, widths):
            speaking = w.start - 0.02 <= t <= w.end + 0.02
            key = flags_by_word.get(id(w), False)
            col = accent if (speaking or key) else G.TEXT
            if speaking and key:
                col = (255, 214, 120)
            sc = 1.0
            d.text((x, y), w.text, font=fnt, fill=(*col, int(255 * fade)), anchor="lm",
                   stroke_width=6, stroke_fill=(5, 8, 20, int(255 * fade)))
            if speaking:
                d.rounded_rectangle([x, y + 38, x + ww, y + 44], radius=3, fill=(*G.CYAN, int(255 * fade)))
            x += ww + space


def srt_time(s: float) -> str:
    ms = int(round(s * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    sec, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"


def write_srt(path: str, timings: list[SceneTiming]) -> int:
    n = 0
    out = []
    for tm in timings:
        for cue in build_cues(tm.words):
            n += 1
            out.append(f"{n}\n{srt_time(tm.start + cue.start)} --> {srt_time(tm.start + cue.end)}\n{cue.text}\n")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out))
    return n
