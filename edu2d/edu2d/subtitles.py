"""Subtítulos ASS sincronizados palabra a palabra, con palabras clave resaltadas."""
import re
import unicodedata

ESCAPE_END = ".,;:?!¿¡"
WHITE, KEY, ACTIVE = "FFFFFF", "FFE14D", "7CF0B3"      # RGB


def norm(w):
    w = unicodedata.normalize("NFD", w.lower())
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in w if unicodedata.category(c) != "Mn"))


def _bgr(rgb):
    return f"&H00{rgb[4:6]}{rgb[2:4]}{rgb[0:2]}&"


def _ts(sec):
    sec = max(0.0, sec)
    h, m = int(sec // 3600), int(sec % 3600 // 60)
    return f"{h}:{m:02d}:{sec % 60:05.2f}"


def chunk_words(words, max_words=5, max_chars=26):
    chunks, cur = [], []
    for w in words:
        cur.append(w)
        chars = sum(len(x["text"]) + 1 for x in cur)
        if len(cur) >= max_words or chars >= max_chars or w["text"][-1] in ESCAPE_END:
            chunks.append(cur)
            cur = []
    if cur:
        if chunks and len(cur) == 1 and len(chunks[-1]) < max_words:
            chunks[-1].extend(cur)          # evita chunks de una sola palabra huérfana
        else:
            chunks.append(cur)
    return chunks


def build_ass(words, keywords, path, w=1080, h=1920, margin_v=400, size=78):
    """words: [{text,start,end}] en tiempo absoluto.  keywords: set de palabras normalizadas."""
    key = {norm(w) for k in keywords for w in k.split()}
    head = (f"[Script Info]\nScriptType: v4.00+\nPlayResX: {w}\nPlayResY: {h}\nWrapStyle: 2\nScaledBorderAndShadow: yes\n\n"
            "[V4+ Styles]\nFormat: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,"
            "Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding\n"
            f"Style: Main,DejaVu Sans,{size},&H00FFFFFF,&H00FFFFFF,&H00231B1B,&H80000000,-1,0,0,0,100,100,0,0,1,8,3,2,90,90,{margin_v},1\n\n"
            "[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n")
    ev = []
    chunks = chunk_words(words)
    prev_end = 0.0
    for ci, ch in enumerate(chunks):
        c_end = ch[-1]["end"] + 0.25
        if ci + 1 < len(chunks):
            c_end = min(c_end, max(chunks[ci + 1][0]["start"] - 0.05, ch[-1]["end"]))
        # salto de línea al medio si el chunk es largo
        total = sum(len(x["text"]) for x in ch)
        brk, acc = None, 0
        if total > 14 and len(ch) > 1:
            best = 1e9
            for i in range(1, len(ch)):
                acc = sum(len(x["text"]) for x in ch[:i])
                if abs(acc - total / 2) < best:
                    best, brk = abs(acc - total / 2), i
        for wi, cur in enumerate(ch):
            start = cur["start"] if wi else max(cur["start"] - 0.05, 0, prev_end)   # sin solapar con el bloque anterior
            end = ch[wi + 1]["start"] if wi + 1 < len(ch) else c_end
            parts = []
            for j, x in enumerate(ch):
                is_key = norm(x["text"]) in key
                if j == wi:
                    col = KEY if is_key else ACTIVE
                    tag = f"{{\\c{_bgr(col)}\\fscx114\\fscy114}}"
                else:
                    col = KEY if is_key else WHITE
                    tag = f"{{\\c{_bgr(col)}\\fscx100\\fscy100}}"
                sep = "\\N" if brk == j and j else (" " if j else "")
                parts.append(sep + tag + x["text"])
            pop = "{\\fscx88\\fscy88\\t(0,110,\\fscx100\\fscy100)}" if wi == 0 else ""
            prev_end = end if wi == len(ch) - 1 else prev_end
            ev.append(f"Dialogue: 0,{_ts(start)},{_ts(end)},Main,,0,0,0,,{pop}{''.join(parts)}")
    with open(path, "w", encoding="utf-8") as f:
        f.write(head + "\n".join(ev) + "\n")
    return len(ev)
