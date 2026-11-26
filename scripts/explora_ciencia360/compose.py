"""Composición: transiciones, subtítulos, render paralelo a MP4 (sin audio)."""
import math, os, subprocess, sys, json, re
import numpy as np
from PIL import Image, ImageDraw
from common import *
import words as _w
from scenes_a import scene_gancho, scene_cerebro
from scenes_b import scene_completar, scene_punto_ciego
from scenes_c import scene_ceguera, scene_conclusion, scene_marca, ALIGN

SCENE_FN = [scene_gancho, scene_cerebro, scene_completar, scene_punto_ciego, scene_ceguera, scene_conclusion, scene_marca]
TRANS_KIND = ["flash", "zoom", "slide", "zoom", "flash", "flash"]

# ------------------------------------------------------------ subtítulos
KEYWORDS = {"cerebro", "engañarte", "rellenando", "punto", "ciego", "ceguera", "cambio", "interpreta", "completa", "atención"}
LAST_BLOCK_FROM = 157  # el mensaje final se muestra en la escena de marca (sincronizado palabra a palabra)
SUB_FONT = 62
MAX_W = 900


def _clean(w):
    return re.sub(r"[^\wáéíóúüñ]", "", w.lower())


def build_blocks(words):
    fo = font(SUB_FONT)
    blocks, cur = [], []
    def flush():
        nonlocal cur
        if cur: blocks.append(cur); cur = []
    for i, w in enumerate(words):
        cur.append((i, w))
        txt = " ".join(x[1][0] for x in cur)
        nxt = words[i + 1][0] if i + 1 < len(words) else None
        end_p = w[0][-1] in ".!?…:" or (w[0][-1] == "," and len(txt) >= 18)
        too_long = nxt is not None and (fo.getlength(txt + " " + nxt) > MAX_W * 1.7)
        if end_p or too_long or len(cur) >= 7:
            flush()
    flush()
    return blocks


def split_lines(block):
    """Divide un bloque en ≤2 líneas equilibradas."""
    fo = font(SUB_FONT)
    ws = [w for _, w in block]
    full = " ".join(w[0] for w in ws)
    if fo.getlength(full) <= MAX_W:
        return [block]
    best = None
    for k in range(1, len(block)):
        a = " ".join(w[0] for w in ws[:k]); b = " ".join(w[0] for w in ws[k:])
        m = max(fo.getlength(a), fo.getlength(b))
        if best is None or m < best[0]:
            best = (m, k)
    k = best[1]
    return [block[:k], block[k:]]


_WORDS = None
_BLOCKS = None
def get_blocks():
    global _WORDS, _BLOCKS
    if _BLOCKS is None:
        _WORDS = _w.load(ALIGN)
        raw = build_blocks(_WORDS[:LAST_BLOCK_FROM])
        # tiempos: de inicio de la primera palabra a fin de la última (+ retención), sin huecos pequeños
        out = []
        for bi, b in enumerate(raw):
            s = b[0][1][1]; e = b[-1][1][2]
            out.append(dict(words=b, start=s, end=e))
        for bi in range(len(out) - 1):
            gap = out[bi + 1]["start"] - out[bi]["end"]
            out[bi]["end"] = out[bi]["end"] + min(gap, 0.35) if gap < 0.8 else out[bi]["end"] + 0.25
        out[-1]["end"] += 0.25
        _BLOCKS = out
    return _BLOCKS


def srt_time(x):
    ms = int(round(x * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def write_srt(path, include_last=True):
    blocks = get_blocks()
    items = [(b["start"], b["end"], split_lines(b["words"])) for b in blocks]
    if include_last:
        ws = _WORDS[LAST_BLOCK_FROM:]
        items.append((ws[0][1], ws[-1][2] + 0.25, [[(i, w) for i, w in enumerate(ws[:5])], [(i, w) for i, w in enumerate(ws[5:])]]))
    with open(path, "w", encoding="utf-8") as fh:
        for n, (s, e, lines) in enumerate(items, 1):
            txt = "\n".join(" ".join(w[0] for _, w in ln) for ln in lines)
            fh.write(f"{n}\n{srt_time(s)} --> {srt_time(e)}\n{txt}\n\n")


def draw_subs(arr, t):
    blocks = get_blocks()
    cur = None
    for b in blocks:
        if b["start"] - 0.02 <= t <= b["end"]:
            cur = b
    if cur is None:
        return arr
    a_in = ease_out(prog(t, cur["start"] - 0.02, cur["start"] + 0.12))
    a_out = 1 - ease(prog(t, cur["end"] - 0.10, cur["end"]))
    a = a_in * a_out
    if a <= 0.01:
        return arr
    lines = split_lines(cur["words"])
    fo = font(SUB_FONT)
    lh = 84
    H_ = lh * len(lines) + 20
    lay = Image.new("RGBA", (W, H_ + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    y0 = 14 + (1 - a_in) * 14
    for li, ln in enumerate(lines):
        txt = " ".join(w[0] for _, w in ln)
        tw = fo.getlength(txt); x = (W - tw) / 2; y = y0 + li * lh
        for _, w in ln:
            hi = _clean(w[0]) in KEYWORDS
            col = (255, 205, 90, 255) if hi else (255, 255, 255, 255)
            d.text((x, y + 4), w[0], font=fo, fill=(0, 0, 0, 150), stroke_width=7, stroke_fill=(0, 0, 0, 150))
            d.text((x, y), w[0], font=fo, fill=col, stroke_width=6, stroke_fill=(6, 10, 26, 255))
            x += fo.getlength(w[0] + " ")
    al = np.asarray(lay, np.float32)
    ya = 1470
    sub = arr[ya:ya + lay.height]
    aa = al[..., 3:4] / 255.0 * a
    arr[ya:ya + lay.height] = sub * (1 - aa) + al[..., :3] * aa
    return arr


# ------------------------------------------------------------ transiciones
def _zoom(arr, z):
    im = Image.fromarray(to_uint8(arr))
    w, h = int(W * z), int(H * z)
    im = im.resize((w, h), Image.BILINEAR)
    x0, y0 = (w - W) // 2, (h - H) // 2
    return np.asarray(im.crop((x0, y0, x0 + W, y0 + H)), np.float32)


def transition(A, B, p, kind):
    e = ease_io(p)
    if kind == "dissolve":
        return A * (1 - e) + B * e
    if kind == "flash":
        out = A * (1 - e) + B * e
        return out + 150 * math.sin(math.pi * p) ** 2 * np.array((0.7, .9, 1.0), np.float32)
    if kind == "zoom":
        a = _zoom(A, 1 + .22 * e); b = _zoom(B, 1.18 - .18 * e)
        a = blur_np(a, 6 * math.sin(math.pi * p) + 1)
        return a * (1 - e) + b * e + 40 * math.sin(math.pi * p)
    if kind == "slide":
        sh = int(W * .45 * e)
        a = np.roll(A, -sh, axis=1); b = np.roll(B, int(W * .45 * (1 - e)), axis=1)
        a = blur_np(a, 10 * math.sin(math.pi * p) + 1); b = blur_np(b, 10 * math.sin(math.pi * p) + 1)
        return a * (1 - e) + b * e
    return A


def frame_at(t):
    # escena principal
    idx = 0
    for i, (n, s, e) in enumerate(SCENES):
        if t >= s: idx = i
    n, s, e = SCENES[idx]
    # ¿en transición?
    out = None
    for i in range(len(SCENES) - 1):
        b = SCENES[i][2]
        if abs(t - b) < TRANS / 2:
            p = (t - (b - TRANS / 2)) / TRANS
            A = SCENE_FN[i](t - SCENES[i][1]); B = SCENE_FN[i + 1](t - SCENES[i + 1][1])
            out = transition(A, B, p, TRANS_KIND[i])
            break
    if out is None:
        out = SCENE_FN[idx](t - s)
    out = grain(out, t, 2.5)
    out = np.clip(out, 0, 255)
    out = draw_subs(out, t)
    return np.clip(out, 0, 255).astype(np.uint8)


# ------------------------------------------------------------ render
def render_chunk(args):
    start, end, path = args
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.2",
           "-g", "30", "-movflags", "+faststart", path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for fr in range(start, end):
        p.stdin.write(frame_at(fr / FPS).tobytes())
    p.stdin.close(); p.wait()
    return path


if __name__ == "__main__":
    from multiprocessing import Pool
    out_dir = sys.argv[1]; os.makedirs(out_dir, exist_ok=True)
    total = int(math.ceil(TOTAL * FPS))
    step = 90
    jobs = [(s, min(s + step, total), os.path.join(out_dir, f"seg_{s:05d}.mp4")) for s in range(0, total, step)]
    with Pool(4) as pool:
        for i, pth in enumerate(pool.imap(render_chunk, jobs)):
            print("ok", pth, flush=True)
    with open(os.path.join(out_dir, "list.txt"), "w") as fh:
        for _, _, pth in jobs:
            fh.write(f"file '{pth}'\n")
    subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", os.path.join(out_dir, "list.txt"), "-c", "copy", os.path.join(out_dir, "video_noaudio.mp4")])
    print("done", total, "frames")
