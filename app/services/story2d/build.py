"""Orquestador: narración → línea de tiempo → render 2D → mezcla → QA.

Uso:
  python -m app.services.story2d.build --out storage/story2d/cajero.mp4
"""
from __future__ import annotations

import argparse
import math
import os
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import skia

from . import script as S
from . import narration, audio
from .cues import build_cues
from .gfx import C, P, rect, text, text_w, clamp, lerp, smooth, ease_io, ease_out, prog, rnd, FONT_BOLD, camera
from . import scenes as SC
from .scenes import SCENES, TRANSITIONS

W, H, FPS = S.W, S.H, S.FPS
TRANS_DUR = 0.5
SURF_CT = skia.kBGRA_8888_ColorType
PIX_FMT = "bgra"


# ------------------------------------------------------------------ línea de tiempo
class Timeline:
    def __init__(self, narr):
        self.narr = narr
        self.beats = {}
        t = S.LEAD_IN
        for bid, _txt, gap in S.BEATS:
            d = narr[bid]["dur"]
            self.beats[bid] = (t, t + d)
            t += d + gap
        last = S.BEATS[-1][0]
        self.total = self.beats[last][1] + S.TAIL_OUT
        self.transitions = TRANSITIONS
        self.scene_times = {}
        order = [(sid, a, b) for sid, a, b, _ in SCENES]
        for i, (sid, a, b) in enumerate(order):
            st = 0.0 if i == 0 else (self.beats[order[i - 1][2]][1] + self.beats[a][0]) / 2
            en = self.total if i == len(order) - 1 else (self.beats[b][1] + self.beats[order[i + 1][1]][0]) / 2
            self.scene_times[sid] = (st, en)

    def start(self, bid):
        return self.beats[bid][0]

    def word(self, bid, prefix, nth=0):
        """Tiempo absoluto en que se pronuncia la palabra que empieza por `prefix`."""
        b0 = self.beats[bid][0]
        hits = [b0 + s for w, s, e in self.narr[bid]["words"]
                if w.lower().strip("¿¡,.:…?!").startswith(prefix.lower())]
        if not hits:
            raise KeyError(f"{bid}:{prefix}")
        return hits[min(nth, len(hits) - 1)]

    def end(self, bid):
        return self.beats[bid][1]


# ------------------------------------------------------------------ subtítulos
def make_cues(T, narr):
    cues = []
    font = skia.Font(SC.__dict__.get("typeface", None) or __import__("app.services.story2d.gfx", fromlist=["typeface"]).typeface(FONT_BOLD), 60)
    for bid, _t, _g in S.BEATS:
        b0 = T.start(bid)
        raw = narr[bid]["words"]
        toks = dict((b, t) for b, t, _ in S.BEATS)[bid].split()
        if len(toks) == len(raw):   # recupera la puntuación original
            raw = [(tk, s_, e_) for tk, (_w, s_, e_) in zip(toks, raw)]
        words = [(w, b0 + s, b0 + e) for w, s, e in raw]
        chunks, cur = [], []
        for w in words:
            cur.append(w)
            txt = " ".join(x[0] for x in cur)
            ends = w[0].rstrip().endswith((",", ":", ".", "…", "?", "!"))
            if (len(txt) >= 30 and ends) or len(txt) >= 40 or (ends and len(txt) >= 18) :
                chunks.append(cur); cur = []
        if cur:
            if chunks and len(" ".join(x[0] for x in cur)) < 9:
                chunks[-1] += cur
            else:
                chunks.append(cur)
        for i, ch in enumerate(chunks):
            st = ch[0][1] - 0.04
            en = ch[-1][2] + 0.18
            if i + 1 < len(chunks):
                en = min(en, chunks[i + 1][0][1] - 0.02)
            else:
                en = max(en, T.end(bid))
            cues.append(dict(start=st, end=en, words=ch))
    return cues


def wrap_words(words, maxw, size):
    lines, cur, curw = [[]], [], 0
    sp = text_w(" ", size)
    for w in words:
        ww = text_w(w[0], size)
        if lines[-1] and curw + sp + ww > maxw:
            lines.append([])
            curw = 0
        lines[-1].append(w)
        curw += (sp if len(lines[-1]) > 1 else 0) + ww
    return lines


def draw_subtitle(cv, cues, t):
    cue = None
    for c in cues:
        if c["start"] <= t < c["end"]:
            cue = c
            break
    if cue is None:
        return
    size = 62
    lines = wrap_words(cue["words"], 900, size)
    a = smooth(prog(t, cue["start"], cue["start"] + 0.1))
    lh = size * 1.28
    bh = lh * len(lines) + 34
    cy = 1530
    sp = text_w(" ", size)
    widths = [sum(text_w(w[0], size) for w in ln) + sp * (len(ln) - 1) for ln in lines]
    bw = max(widths) + 70
    y0 = cy - bh / 2 + 6 * (1 - a)
    rect(cv, 540 - bw / 2, y0, bw, bh, "#05080F", 0.62 * a, r=30)
    for li, ln in enumerate(lines):
        x = 540 - widths[li] / 2
        y = y0 + 17 + lh * li + size * 0.95
        for w in ln:
            active = w[1] - 0.02 <= t < w[2] + 0.04
            col = "#FFD166" if active else "#FFFFFF"
            text(cv, w[0], x, y, size, col, "left", outline="#000000", outline_w=9, a=a)
            x += text_w(w[0], size) + sp


def write_srt(cues, path):
    def ts(x):
        h, m, s = int(x // 3600), int(x // 60 % 60), x % 60
        return f"{h:02d}:{m:02d}:{int(s):02d},{int((s % 1) * 1000):03d}"
    out = []
    for i, c in enumerate(cues, 1):
        out.append(f"{i}\n{ts(c['start'])} --> {ts(c['end'])}\n{' '.join(w[0] for w in c['words'])}\n")
    Path(path).write_text("\n".join(out), encoding="utf-8")


# ------------------------------------------------------------------ render
class Renderer:
    def __init__(self, T, cues):
        self.T, self.cues = T, cues
        self.surf_main = skia.Surface(W, H)
        self.surf_a = skia.Surface(W, H)
        self.surf_b = skia.Surface(W, H)
        self.order = [(sid, fn) for sid, _a, _b, fn in SCENES]

    def scene_at(self, t):
        for i, (sid, fn) in enumerate(self.order):
            a, b = self.T.scene_times[sid]
            if t < b or i == len(self.order) - 1:
                return i
        return len(self.order) - 1

    def draw_scene(self, surf, i, t):
        sid, fn = self.order[i]
        a, b = self.T.scene_times[sid]
        cv = surf.getCanvas()
        cv.save()
        cv.clear(C("#101820"))
        fn(cv, max(0.0, t - a), dict(dur=b - a, T=self.T, t_abs=t, sid=sid, a=a))
        cv.restore()

    def frame(self, n):
        t = n / FPS
        T = self.T
        i = self.scene_at(t)
        cv = self.surf_main.getCanvas()
        cv.resetMatrix()
        # ¿estamos dentro de una transición hacia la escena i+1 o desde i-1?
        trans = None
        if i + 1 < len(self.order):
            nb = self.T.scene_times[self.order[i][0]][1]
            if nb - t < TRANS_DUR / 2:
                trans = (i, i + 1, 1 - (nb - t) / (TRANS_DUR / 2) * 0.5 - 0.0)
                trans = (i, i + 1, 0.5 - (nb - t) / TRANS_DUR)  # 0..0.5
        if trans is None and i > 0:
            sb = self.T.scene_times[self.order[i][0]][0]
            if t - sb < TRANS_DUR / 2:
                trans = (i - 1, i, 0.5 + (t - sb) / TRANS_DUR)
        if trans is None:
            self.draw_scene(self.surf_main, i, t)
        else:
            ia, ib, p = trans
            self.draw_scene(self.surf_a, ia, t)
            self.draw_scene(self.surf_b, ib, t)
            self.composite(cv, self.surf_a.makeImageSnapshot(), self.surf_b.makeImageSnapshot(),
                           clamp(p), TRANSITIONS.get(self.order[ib][0], "fade"), t)
        # acabado: viñeta + grano suave
        cv.resetMatrix()
        cv.drawRect(skia.Rect.MakeXYWH(0, 0, W, H),
                    skia.Paint(Shader=skia.GradientShader.MakeRadial((W / 2, H / 2), 1250, [C("#000000", 0.0), C("#000000", 0.38)])))
        draw_subtitle(cv, self.cues, t)
        # fundido inicial / final
        fa = 1 - smooth(prog(t, 0, 0.35)) if t < 0.5 else 0
        fz = smooth(prog(t, T.total - 0.6, T.total))
        if fa > 0 or fz > 0:
            rect(cv, 0, 0, W, H, "#000000", max(fa, fz))
        img = self.surf_main.makeImageSnapshot()
        return img.tobytes() if hasattr(img, "tobytes") else bytes(img.toarray())

    def composite(self, cv, A, B, p, kind, t):
        full = skia.Rect.MakeXYWH(0, 0, W, H)
        e = ease_io(p)
        if kind == "whip":
            blur = skia.Paint()
            sig = 60 * math.sin(math.pi * p)
            blur.setImageFilter(skia.ImageFilters.Blur(sig + 0.01, 0.01))
            cv.save(); cv.translate(-W * e, 0); cv.drawImage(A, 0, 0, skia.SamplingOptions(), blur); cv.restore()
            cv.save(); cv.translate(W * (1 - e), 0); cv.drawImage(B, 0, 0, skia.SamplingOptions(), blur); cv.restore()
        elif kind == "iris":
            cv.drawImage(A, 0, 0)
            cv.save()
            path = skia.Path(); path.addCircle(W / 2, H / 2, 1500 * e + 1)
            cv.clipPath(path, skia.ClipOp.kIntersect, True)
            cv.drawImage(B, 0, 0)
            cv.restore()
            cv.drawCircle(W / 2, H / 2, 1500 * e + 1, P("#FFFFFF", 0.7 * math.sin(math.pi * p), "stroke", 14))
        elif kind == "flash":
            cv.drawImage(A if p < 0.5 else B, 0, 0)
            rect(cv, 0, 0, W, H, "#FFFFFF", math.sin(math.pi * p) ** 1.5)
        elif kind == "glitch":
            cv.drawImage(A, 0, 0)
            r_ = rnd(int(t * 60))
            n_s = 24
            for s in range(n_s):
                y0 = s * H / n_s
                if r_.random() < p * 1.4:
                    off = (r_.random() - 0.5) * 140 * math.sin(math.pi * p)
                    cv.save(); cv.clipRect(skia.Rect.MakeXYWH(0, y0, W, H / n_s + 1))
                    cv.drawImage(B, off, 0); cv.restore()
            for _ in range(60):
                rect(cv, r_.random() * W, r_.random() * H, r_.random() * 160 + 20, 3, "#FFFFFF", 0.35 * math.sin(math.pi * p))
        else:  # fade
            cv.drawImage(A, 0, 0)
            pa = skia.Paint(); pa.setAlphaf(e)
            cv.drawImage(B, 0, 0, skia.SamplingOptions(), pa)


# ------------------------------------------------------------------ workers
_R = None


def _init(T, cues):
    global _R
    _R = Renderer(T, cues)


def _render_chunk(args):
    start, end, out_path = args
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", PIX_FMT, "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "17",
           "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out_path)]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for n in range(start, end):
        pr.stdin.write(_R.frame(n))
    pr.stdin.close()
    if pr.wait() != 0:
        raise RuntimeError("ffmpeg falló en el chunk")
    return out_path


def render_video(T, cues, out_video, workers=4, frames=None, workdir=None):
    total = int(math.ceil(T.total * FPS))
    if frames is not None:
        a, b = frames
    else:
        a, b = 0, total
    n = b - a
    chunk = max(1, math.ceil(n / workers))
    jobs, files = [], []
    for k in range(workers):
        s, e = a + k * chunk, min(b, a + (k + 1) * chunk)
        if s >= e:
            continue
        f = Path(workdir) / f"chunk_{k}.mp4"
        jobs.append((s, e, f)); files.append(f)
    with ProcessPoolExecutor(max_workers=workers, initializer=_init, initargs=(T, cues)) as ex:
        list(ex.map(_render_chunk, jobs))
    lst = Path(workdir) / "chunks.txt"
    lst.write_text("".join(f"file '{f}'\n" for f in files))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(out_video)], check=True)
    return total


# ------------------------------------------------------------------ principal
def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="storage/story2d/cajero_robo_imposible.mp4")
    ap.add_argument("--rate", default="+12%")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--work", default=None)
    ap.add_argument("--audio-only", action="store_true")
    ap.add_argument("--frames", default=None, help="a:b (sólo para pruebas)")
    ap.add_argument("--still", default=None, help="tiempos en s separados por coma → PNG")
    a = ap.parse_args(argv)

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    work = Path(a.work) if a.work else out.parent / "work"
    work.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    print("1/5 narración (edge-tts)…")
    narr = narration.synth_beats(S.BEATS, S.VOICE, a.rate, work / "tts", proxy=proxy)
    T = Timeline(narr)
    print(f"    duración total: {T.total:.1f}s")
    for sid, (s, e) in T.scene_times.items():
        print(f"    {sid:4s} {s:6.2f} → {e:6.2f}")
    cues = make_cues(T, narr)
    write_srt(cues, out.with_suffix(".srt"))

    print("2/5 audio (voz + música + efectos)…")
    voice_events = [(T.start(bid), narr[bid]["audio"]) for bid, *_ in S.BEATS]
    music = audio.make_music(T.total + 1)
    sfx_events = build_cues(T)
    parts = audio.mix_track(T.total, voice_events, sfx_events, music)
    beats_tl = [(bid, *T.beats[bid]) for bid, *_ in S.BEATS]
    issues, info = audio.qa_report(parts, beats_tl, narr)
    print("    QA audio:", info)
    for i in issues:
        print("    ⚠", i)
    wav = work / "mix.wav"
    audio.write_wav(wav, parts["mix"])
    audio.write_wav(work / "voice.wav", np.stack([parts["voice"]] * 2, 1))
    if a.audio_only:
        return 0

    if a.still:
        _init(T, cues)
        for s in a.still.split(","):
            n = int(float(s) * FPS)
            data = _R.frame(n)
            skia.Image.MakeRasterData(skia.ImageInfo.Make(W, H, SURF_CT, skia.kPremul_AlphaType), skia.Data.MakeWithCopy(data), W * 4).save(str(work / f"still_{float(s):05.2f}.png"))
        return 0

    print(f"3/5 render 2D {W}x{H}@{FPS} con {a.workers} procesos…")
    fr = tuple(int(x) for x in a.frames.split(":")) if a.frames else None
    video = work / "video.mp4"
    nfr = render_video(T, cues, video, a.workers, fr, work)
    print(f"    {nfr} cuadros en {time.time() - t0:.0f}s")

    print("4/5 mux audio + vídeo…")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-i", str(wav), "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-shortest", "-movflags", "+faststart", str(out)], check=True)
    print("5/5 listo:", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
