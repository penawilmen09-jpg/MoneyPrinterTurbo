"""v2 del MISMO documental: nueva intro (gancho) + escenas originales desplazadas + mejoras globales."""
import json, math, os, subprocess, sys
import numpy as np
from PIL import Image
import stage
from stage import *
import compose_m as cm
import words as _w
import m0

OFF = 5.22            # desplazamiento de las escenas originales (la voz original se corta en 7.38 s y se recoloca en 12.60 s)
CUT_OLD = 7.38
TOTAL = 76.3
HOOK_DELAY = .05
AUDIO_DIR = cm.AUDIO_DIR
HOOK_ALIGN = os.path.join(AUDIO_DIR, "gancho_alignment.json")

SCENES = [("intro", m0.scene, 0.0, 12.62)] + [(n, fn, s + OFF, e + OFF) for (n, fn, s, e) in cm.SCENES[1:]]
SCENES[-1] = (SCENES[-1][0], SCENES[-1][1], SCENES[-1][2], TOTAL)
KINDS = ["zoomblur", "whip", "zoom", "whip", "flash", "dissolve"]
TRANS = .5
_orig_blocks = cm.blocks
cm.KEYWORDS.update({"millón", "dinero", "2.000", "fortuna"})


# ------------------------------------------------------------ subtítulos
def hook_words():
    ws = _w.load(HOOK_ALIGN); out = []; i = 0
    while i < len(ws):
        w, a, b = ws[i]
        if w == "dos" and i + 1 < len(ws) and ws[i + 1][0] == "mil":
            out.append(("2.000", a + HOOK_DELAY, ws[i + 1][2] + HOOK_DELAY)); i += 2; continue
        out.append((w, a + HOOK_DELAY, b + HOOK_DELAY)); i += 1
    return out


def make_blocks(ws):
    fo = cm._font(cm.SUB_FONT); bl, cur = [], []
    for i, w in enumerate(ws):
        cur.append(w); txt = " ".join(x[0] for x in cur); nxt = ws[i + 1][0] if i + 1 < len(ws) else None
        end_p = w[0][-1] in ".!?…:" or (w[0][-1] == "," and len(txt) >= 18)
        if end_p or (nxt and fo.getlength(txt + " " + nxt) > cm.MAX_W * 1.7) or len(cur) >= 7:
            bl.append(cur); cur = []
    if cur: bl.append(cur)
    return [dict(words=b, start=b[0][1], end=b[-1][2]) for b in bl]


_B = None
def blocks():
    global _B
    if _B: return _B
    hb = make_blocks(hook_words())
    for i in range(len(hb) - 1):
        gap = hb[i + 1]["start"] - hb[i]["end"]; hb[i]["end"] += min(gap, .35) if gap < .8 else .25
    hb[-1]["end"] += .6
    old = []
    for b in _orig_blocks():
        if b["start"] >= CUT_OLD:
            words = [(w, a + OFF, e + OFF) for (w, a, e) in b["words"]]
            old.append(dict(words=words, start=b["start"] + OFF, end=b["end"] + OFF))
    _B = hb + old
    return _B


cm.blocks = blocks          # draw_subs / write_srt de compose_m usan este generador


# ------------------------------------------------------------ transiciones y cámara
def hblur(arr, n, spread):
    if spread < 2: return arr
    acc = np.zeros_like(arr)
    for j in range(n): acc += np.roll(arr, int(spread * (j / (n - 1) - .5)), axis=1)
    return acc / n


def transition(A, B, p, kind):
    e = ease_io(p)
    if kind == "whip":
        out = slide_blend_np(A, B, p)
        return hblur(out, 9, 220 * math.sin(math.pi * p)) + 40 * math.sin(math.pi * p)
    if kind == "zoomblur":
        a = np.zeros_like(A); b = np.zeros_like(B)
        for j in range(5):
            a += cm._zoom(A, 1 + (.22 * e) * (j / 4 + .2)); b += cm._zoom(B, 1.22 - .22 * e * (1 - (j / 4 + .2) * .6))
        a /= 5; b /= 5
        return a * (1 - e) + b * e + 110 * math.sin(math.pi * p) ** 2 * np.array((.8, .9, 1.0), np.float32)
    return cm.transition(A, B, p, kind)


def slide_blend_np(A, B, p):
    e = ease_io(p); sh = int(W * e); out = np.empty_like(A)
    out[:, :W - sh] = A[:, sh:]; out[:, W - sh:] = B[:, :sh]
    return out


def drift(arr, tl, dur, i):
    """Cámara viva: empuje lento + paneo leve (escenas originales)."""
    u = ease_io(prog(tl, 0, dur))
    z = 1.0 + (.05 if i % 2 else .04) * u
    if z < 1.003: return arr
    im = Image.fromarray(to_uint8(arr)); w, h = int(W * z), int(H * z)
    im = im.resize((w, h), Image.BILINEAR)
    dx = int((w - W) * (.5 + (.35 if i % 2 else -.35) * (u - .5) * 2 * .5)); dy = int((h - H) * (.5 - .2 * (u - .5)))
    dx = max(0, min(w - W, dx)); dy = max(0, min(h - H, dy))
    return np.asarray(im.crop((dx, dy, dx + W, dy + H)), np.float32)


def scene_out(i, t):
    n, fn, s, e = SCENES[i]
    out = fn(t - s)
    if i >= 1 and i < len(SCENES) - 1: out = drift(out, t - s, e - s, i)
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
            p = (t - (b - TRANS / 2)) / TRANS
            out = transition(scene_out(i, t), scene_out(i + 1, t), p, KINDS[i]); break
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
