"""Subtítulos sincronizados: ASS con resaltado palabra por palabra + SRT."""

from __future__ import annotations

import re

Word = tuple[str, float, float]  # (texto, inicio, fin) en segundos absolutos

HIGHLIGHT = "00D7FF"   # BGR en ASS -> amarillo/dorado (#FFD700)
WHITE = "FFFFFF"


def _ts_ass(t: float) -> str:
    t = max(0.0, t)
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def _ts_srt(t: float) -> str:
    t = max(0.0, t)
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def chunk_words(words: list[Word], max_words: int = 4, max_chars: int = 24) -> list[list[Word]]:
    """Agrupa palabras en líneas cortas, cortando en puntuación fuerte."""
    chunks, cur = [], []
    for w in words:
        cur.append(w)
        n_chars = sum(len(x[0]) + 1 for x in cur)
        strong = re.search(r"[.!?…:;]$", w[0]) is not None
        soft = re.search(r"[,]$", w[0]) is not None and len(cur) >= 2
        if len(cur) >= max_words or n_chars >= max_chars or strong or soft:
            chunks.append(cur)
            cur = []
    if cur:
        # evita una línea final de una sola palabra suelta
        if chunks and len(cur) == 1 and len(chunks[-1]) < max_words:
            chunks[-1].extend(cur)
        else:
            chunks.append(cur)
    return chunks


def _esc(text: str) -> str:
    return text.replace("\\", "").replace("{", "(").replace("}", ")")


def build_ass(words: list[Word], *, width: int = 1080, height: int = 1920, font: str = "Be Vietnam Pro",
              size: int = 78, margin_v: int = 380, uppercase: bool = True) -> str:
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Main,{font},{size},&H00FFFFFF,&H00FFFFFF,&H00201028,&H96000000,-1,0,0,0,100,100,0,0,1,8,3,2,60,60,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = []
    chunks = chunk_words(words)
    for ci, chunk in enumerate(chunks):
        # la última palabra de una línea nunca debe pisar la primera de la siguiente
        # (libass apilaría ambas líneas y se leerían en orden inverso)
        limit = chunks[ci + 1][0][1] if ci + 1 < len(chunks) else float("inf")
        for i, (w, s, e) in enumerate(chunk):
            nxt = chunk[i + 1][1] if i + 1 < len(chunk) else min(e + 0.12, limit)
            end = max(nxt, s + 0.08)
            if i + 1 == len(chunk):
                end = min(end, limit) if limit > s + 0.05 else end
            parts = []
            for j, (txt, _, _) in enumerate(chunk):
                t = _esc(txt.upper() if uppercase else txt)
                if j == i:
                    parts.append(f"{{\\c&H{HIGHLIGHT}&\\fscx112\\fscy112}}{t}{{\\r}}")
                else:
                    parts.append(t)
            lines.append(f"Dialogue: 0,{_ts_ass(s)},{_ts_ass(end)},Main,,0,0,0,,{' '.join(parts)}")
    return head + "\n".join(lines) + "\n"


def build_srt(words: list[Word]) -> str:
    out = []
    chunks = chunk_words(words)
    for n, chunk in enumerate(chunks, 1):
        s, e = chunk[0][1], chunk[-1][2] + 0.12
        if n < len(chunks):
            e = min(e, max(chunks[n][0][1], s + 0.1))
        out.append(f"{n}\n{_ts_srt(s)} --> {_ts_srt(e)}\n{' '.join(w[0] for w in chunk)}\n")
    return "\n".join(out)
