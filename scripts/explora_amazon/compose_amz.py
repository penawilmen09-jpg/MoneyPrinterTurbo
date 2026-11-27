"""Composición del documental de Amazon: transiciones, cámara viva, subtítulos y render paralelo."""
import json, math, os, subprocess, sys
import numpy as np
from PIL import Image
import amz, stage
from stage import *
from stage import _font
import compose_m as cm
import words as _w
import a0, a1, a2, a3, a4, a5, a6

HERE = os.path.dirname(__file__)
ALIGN = os.path.join(HERE, "..", "..", "storage", "explora_amazon", "audio", "alignment.json")
SCENES = [("gancho", a0.scene, 0.0, 14.85), ("idea", a1.scene, 14.85, 27.55), ("nacimiento", a2.scene, 27.55, 37.50), ("catalogo", a3.scene, 37.50, 45.80),
          ("imperio", a4.scene, 45.80, 57.13), ("gigante", a5.scene, 57.13, 65.25), ("cierre", a6.scene, 65.25, 77.50)]
TOTAL = 77.5
TRANS = .5
KINDS = ["zoom", "whip", "flash", "whip", "zoom", "dissolve"]
cm.KEYWORDS.update({"jeff", "bezos", "amazon", "libros", "1994", "1995", "prime", "services", "internet", "logística", "garaje", "locura", "imperios", "nube", "catálogo", "web"})
_orig_trans = cm.transition


def whip(A, B, p):
    e = ease_io(p); sh = int(W * e); out = np.empty_like(A)
    out[:, :W - sh] = A[:, sh:]; out[:, W - sh:] = B[:, :sh]
    spread = 220 * math.sin(math.pi * p)
    if spread >= 2:
        acc = np.zeros_like(out)
        for j in range(9): acc += np.roll(out, int(spread * (j / 8 - .5)), axis=1)
        out = acc / 9
    return out + 40 * math.sin(math.pi * p)


def transition(A, B, p, kind):
    return whip(A, B, p) if kind == "whip" else _orig_trans(A, B, p, kind)


def drift(arr, tl, dur, i):
    u = ease_io(prog(tl, 0, dur)); z = 1.0 + (.05 if i % 2 else .04) * u
    if z < 1.003: return arr
    im = Image.fromarray(to_uint8(arr)); w, h = int(W * z), int(H * z); im = im.resize((w, h), Image.BILINEAR)
    dx = max(0, min(w - W, int((w - W) * (.5 + (.35 if i % 2 else -.35) * (u - .5))))); dy = max(0, min(h - H, int((h - H) * (.5 - .2 * (u - .5)))))
    return np.asarray(im.crop((dx, dy, dx + W, dy + H)), np.float32)


# ------------------------------------------------------------ subtítulos (palabras de ElevenLabs)
SCENE_STARTS = {49, 84, 109, 135, 170, 198}      # primera palabra de cada escena: nunca se mezcla con la anterior
_B = None
def blocks():
    global _B
    if _B: return _B
    ws = _w.load(ALIGN); fo = _font(cm.SUB_FONT); bl, cur = [], []
    for i, w in enumerate(ws):
        cur.append(w); txt = " ".join(x[0] for x in cur); nxt = ws[i + 1][0] if i + 1 < len(ws) else None
        end_p = w[0][-1] in ".!?…:" or (w[0][-1] == "," and len(txt) >= 18) or (i + 1) in SCENE_STARTS
        if end_p or (nxt and fo.getlength(txt + " " + nxt) > cm.MAX_W * 1.7) or len(cur) >= 7:
            bl.append(cur); cur = []
    if cur: bl.append(cur)
    out = [dict(words=b, start=b[0][1], end=b[-1][2]) for b in bl]
    for i in range(len(out) - 1):
        gap = out[i + 1]["start"] - out[i]["end"]; out[i]["end"] += min(gap, .35) if gap < .8 else .25
    out[-1]["end"] += .8
    _B = out; return out


cm.blocks = blocks


def scene_out(i, t):
    n, fn, s, e = SCENES[i]
    out = fn(t - s)
    if 1 <= i <= 5: out = drift(out, t - s, e - s, i)
    return out


def frame_at(t):
    stage.CLOCK[0] = t
    idx = 0
    for i, (_, _, s, e) in enumerate(SCENES):
        if t >= s: idx = i
    out = None
    for i in range(len(SCENES) - 1):
        b = SCENES[i][3]
        if abs(t - b) < TRANS / 2:
            p = (t - (b - TRANS / 2)) / TRANS; out = transition(scene_out(i, t), scene_out(i + 1, t), p, KINDS[i]); break
    if out is None: out = scene_out(idx, t)
    out = np.clip(grain(out, t, 2.2), 0, 255)
    out = cm.draw_subs(out, t)
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
