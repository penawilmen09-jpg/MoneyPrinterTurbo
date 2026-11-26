"""Composición del documental: transiciones, subtítulos y render paralelo."""
import math, os, re, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw
from stage import *
from stage import _font
import words as _w
import m1, m2, m3, m4, m5, m6, m7

AUDIO_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "storage", "explora_musk", "audio")
ALIGN = os.path.join(AUDIO_DIR, "alignment.json")
SCENES = [("gancho", m1.scene, 0.0, 7.40), ("comienzos", m2.scene, 7.40, 16.00), ("zip2", m3.scene, 16.00, 25.80), ("paypal", m4.scene, 25.80, 36.30),
          ("espacio", m5.scene, 36.30, 45.80), ("imperio", m6.scene, 45.80, 57.80), ("cierre", m7.scene, 57.80, 70.00)]
TOTAL = 70.0
TRANS = .5
KINDS = ["flash", "zoom", "dissolve", "zoom", "flash", "dissolve"]

KEYWORDS = {"elon", "musk", "fortuna", "millones", "sudáfrica", "videojuego", "zip2", "compaq", "paypal", "x.com", "ebay", "spacex", "tesla", "forbes", "cohetes", "eléctricos", "patrimonio", "idea"}
SUB_FONT = 62; MAX_W = 900

def clean(w): return re.sub(r"[^\w.áéíóúüñ]", "", w.lower()).strip(".")


def load_words():
    ws = _w.load(ALIGN)
    out = []; i = 0
    while i < len(ws):
        w, a, b = ws[i]
        if w == "Zip" and i + 1 < len(ws) and ws[i + 1][0].startswith("Dos"):
            tail = ws[i + 1][0][3:]
            out.append(("Zip2" + tail, a, ws[i + 1][2])); i += 2; continue
        out.append((w, a, b)); i += 1
    return out


_B = None
def blocks():
    global _B
    if _B: return _B
    ws = load_words(); fo = _font(SUB_FONT)
    bl, cur = [], []
    for i, w in enumerate(ws):
        cur.append(w)
        txt = " ".join(x[0] for x in cur); nxt = ws[i + 1][0] if i + 1 < len(ws) else None
        end_p = w[0][-1] in ".!?…:" or (w[0][-1] == "," and len(txt) >= 18)
        if end_p or (nxt and fo.getlength(txt + " " + nxt) > MAX_W * 1.7) or len(cur) >= 7:
            bl.append(cur); cur = []
    if cur: bl.append(cur)
    out = [dict(words=b, start=b[0][1], end=b[-1][2]) for b in bl]
    for i in range(len(out) - 1):
        gap = out[i + 1]["start"] - out[i]["end"]
        out[i]["end"] += min(gap, .35) if gap < .8 else .25
    out[-1]["end"] += .6
    _B = out; return out


def lines_of(words):
    fo = _font(SUB_FONT)
    full = " ".join(w[0] for w in words)
    if fo.getlength(full) <= MAX_W: return [words]
    best = None
    for k in range(1, len(words)):
        a = " ".join(w[0] for w in words[:k]); b = " ".join(w[0] for w in words[k:])
        m = max(fo.getlength(a), fo.getlength(b))
        if best is None or m < best[0]: best = (m, k)
    return [words[:best[1]], words[best[1]:]]


def stime(x):
    ms = int(round(x * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def write_srt(path):
    with open(path, "w", encoding="utf-8") as fh:
        for n, b in enumerate(blocks(), 1):
            fh.write(f"{n}\n{stime(b['start'])} --> {stime(b['end'])}\n" + "\n".join(" ".join(w[0] for w in ln) for ln in lines_of(b["words"])) + "\n\n")


def draw_subs(arr, t):
    cur = None
    for b in blocks():
        if b["start"] - .02 <= t <= b["end"]: cur = b
    if cur is None: return arr
    a_in = ease_out(prog(t, cur["start"] - .02, cur["start"] + .12)); a_out = 1 - ease(prog(t, cur["end"] - .1, cur["end"]))
    a = a_in * a_out
    if a <= .01: return arr
    lines = lines_of(cur["words"]); fo = _font(SUB_FONT); lh = 84
    lay = Image.new("RGBA", (W, lh * len(lines) + 60), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    y0 = 14 + (1 - a_in) * 14
    for li, ln in enumerate(lines):
        tw = fo.getlength(" ".join(w[0] for w in ln)); x = (W - tw) / 2; y = y0 + li * lh
        for w in ln:
            col = (255, 205, 90, 255) if clean(w[0]) in KEYWORDS else (255, 255, 255, 255)
            d.text((x, y + 4), w[0], font=fo, fill=(0, 0, 0, 150), stroke_width=7, stroke_fill=(0, 0, 0, 150))
            d.text((x, y), w[0], font=fo, fill=col, stroke_width=6, stroke_fill=(6, 10, 26, 255))
            x += fo.getlength(w[0] + " ")
    al = np.asarray(lay, np.float32); ya = 1470
    sub = arr[ya:ya + lay.height]; aa = al[..., 3:4] / 255.0 * a
    arr[ya:ya + lay.height] = sub * (1 - aa) + al[..., :3] * aa
    return arr


def _zoom(arr, z):
    im = Image.fromarray(to_uint8(arr)); w, h = int(W * z), int(H * z)
    im = im.resize((w, h), Image.BILINEAR); x0, y0 = (w - W) // 2, (h - H) // 2
    return np.asarray(im.crop((x0, y0, x0 + W, y0 + H)), np.float32)


def transition(A, B, p, kind):
    e = ease_io(p)
    if kind == "dissolve": return A * (1 - e) + B * e
    if kind == "flash": return A * (1 - e) + B * e + 130 * math.sin(math.pi * p) ** 2 * np.array((.8, .9, 1.0), np.float32)
    a = blur_np(_zoom(A, 1 + .2 * e), 5 * math.sin(math.pi * p) + 1); b = _zoom(B, 1.16 - .16 * e)
    return a * (1 - e) + b * e + 30 * math.sin(math.pi * p)


def frame_at(t):
    idx = 0
    for i, (_, _, s, e) in enumerate(SCENES):
        if t >= s: idx = i
    out = None
    for i in range(len(SCENES) - 1):
        b = SCENES[i][3]
        if abs(t - b) < TRANS / 2:
            p = (t - (b - TRANS / 2)) / TRANS
            A = SCENES[i][1](t - SCENES[i][2]); B = SCENES[i + 1][1](t - SCENES[i + 1][2])
            out = transition(A, B, p, KINDS[i]); break
    if out is None: out = SCENES[idx][1](t - SCENES[idx][2])
    out = np.clip(grain(out, t, 2.2), 0, 255)
    out = draw_subs(out, t)
    return out.astype(np.uint8)


def render_chunk(args):
    start, end, path = args
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", "-profile:v", "high", "-g", "30", path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for fr in range(start, end): p.stdin.write(frame_at(fr / FPS).tobytes())
    p.stdin.close(); p.wait(); return path


if __name__ == "__main__":
    from multiprocessing import Pool
    d = sys.argv[1]; os.makedirs(d, exist_ok=True)
    total = int(math.ceil(TOTAL * FPS)); step = 60
    only = [int(x) for x in sys.argv[2].split(",")] if len(sys.argv) > 2 else None
    jobs = [(s, min(s + step, total), os.path.join(d, f"seg_{s:05d}.mp4")) for s in range(0, total, step)]
    run = [j for j in jobs if only is None or j[0] in only]
    with Pool(4) as pool:
        for pth in pool.imap_unordered(render_chunk, run): print("ok", pth, flush=True)
    with open(os.path.join(d, "list.txt"), "w") as fh:
        for _, _, pth in jobs: fh.write(f"file '{pth}'\n")
    subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", os.path.join(d, "list.txt"), "-c", "copy", os.path.join(d, "video_noaudio.mp4")])
    print("done", total, "frames")
