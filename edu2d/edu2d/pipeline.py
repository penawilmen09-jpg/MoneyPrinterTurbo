"""Pipeline: guion JSON -> TTS -> línea de tiempo -> audio -> subtítulos -> frames SVG -> MP4."""
import importlib
import json
import math
import multiprocessing as mp
import subprocess
import wave
from pathlib import Path

import numpy as np

from .audio_check import check_audio
from .core import FPS, H, W, VOICE, VOICE_RATE
from .sfx import BANK, SR
from .subtitles import build_ass
from .svgkit import frame_svg
from .tts import synthesize

LEAD, LEAD_FIRST, TAIL, TAIL_LAST, TRANS = 0.15, 0.25, 0.35, 1.3, 0.4


def load_script(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    pack = importlib.import_module(f"edu2d.scenes_{data['pack']}")
    for sc in data["scenes"]:
        if sc["scene"] not in pack.SCENES:
            raise ValueError(f"escena desconocida '{sc['scene']}' en el pack '{data['pack']}'. "
                             f"Disponibles: {sorted(pack.SCENES)}")
        if not sc.get("text", "").strip():
            raise ValueError(f"escena '{sc['scene']}' sin texto de narración")
    return data


def build_timeline(data, work):
    """Sintetiza cada escena, valida el audio y calcula tiempos reales."""
    voice, rate = data.get("voice", VOICE), data.get("rate", VOICE_RATE)
    t, tl = 0.0, []
    for i, sc in enumerate(data["scenes"]):
        r = synthesize(sc["text"], Path(work) / "tts", voice, rate)
        info = check_audio(r["path"])
        lead = LEAD_FIRST if i == 0 else LEAD
        tail = TAIL_LAST if i == len(data["scenes"]) - 1 else TAIL
        dur = lead + info["duration"] + tail
        toks = sc["text"].split()
        raw = r["words"]
        if len(toks) == len(raw):          # el servicio omite la puntuación: la recuperamos del guion
            raw = [{**w, "text": tk} for w, tk in zip(raw, toks)]
        words = [{**w, "start": w["start"] + t + lead, "end": w["end"] + t + lead} for w in raw]
        tl.append(dict(scene=sc["scene"], start=t, dur=dur, audio=r["path"], audio_dur=info["duration"],
                       lead=lead, words=words, highlight=sc.get("highlight", []), mean_db=info["mean_db"]))
        t += dur
    return tl, t


def _decode(path):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"],
                       capture_output=True, check=True)
    return np.frombuffer(r.stdout, dtype=np.int16).astype(np.float32) / 32768


def build_audio(tl, total, pack, out_wav):
    buf = np.zeros(int((total + .2) * SR), dtype=np.float32)
    for s in tl:
        a = _decode(s["audio"])
        o = int((s["start"] + s["lead"]) * SR)
        buf[o:o + len(a)] += a
    for i, s in enumerate(tl):                       # efectos
        if i:
            o = int((s["start"] - .05) * SR)
            w = BANK["whoosh"]()
            buf[o:o + len(w)] += w
        for name, fn in getattr(pack, "SFX", {}).get(s["scene"], []):
            fx = BANK[name]() * .6
            o = int((s["start"] + fn(s["dur"])) * SR)
            buf[o:o + len(fx)] += fx[:max(0, len(buf) - o)]
    peak = np.abs(buf).max()
    if peak > .0:
        buf *= .89 / peak
    pcm = (buf * 32767).astype(np.int16)
    with wave.open(str(out_wav), "wb") as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(SR); f.writeframes(pcm.tobytes())
    return len(buf) / SR


# ---------------------------------------------------------------- frames
_G = {}


def _init(pack_name, tl):
    _G["pack"] = importlib.import_module(f"edu2d.scenes_{pack_name}")
    _G["tl"] = tl


def _transition(prev, cur, k, kind):
    k = k * k * (3 - 2 * k)
    if kind == "iris":
        r = k * 1250
        return (f'{prev}<clipPath id="tr"><circle cx="{W/2}" cy="{H/2}" r="{r:.0f}"/></clipPath>'
                f'<g clip-path="url(#tr)">{cur}</g>'
                f'<circle cx="{W/2}" cy="{H/2}" r="{r:.0f}" fill="none" stroke="#fff" stroke-width="10" opacity="{1-k:.2f}"/>')
    x = k * (W + 40) - 20
    return (f'{prev}<clipPath id="tr"><rect x="0" y="0" width="{max(x,0):.0f}" height="{H}"/></clipPath>'
            f'<g clip-path="url(#tr)">{cur}</g><rect x="{x-10:.0f}" y="0" width="20" height="{H}" fill="#FFE14D"/>')


def render_frame(i):
    import cairosvg
    tl, pack = _G["tl"], _G["pack"]
    t = i / FPS
    idx = max(j for j, s in enumerate(tl) if s["start"] <= t + 1e-9)
    s = tl[idx]
    lt = t - s["start"]
    cur = pack.SCENES[s["scene"]](lt, s["dur"])
    if idx and lt < TRANS:
        p = tl[idx - 1]
        prev = pack.SCENES[p["scene"]](p["dur"] + lt, p["dur"])
        cur = _transition(prev, cur, lt / TRANS, "iris" if idx % 2 else "wipe")
    return cairosvg.svg2png(bytestring=frame_svg(cur).encode("utf-8"))


def render_video(data, tl, total, wav, ass, out_mp4, workers=None, log=print):
    nframes = int(math.ceil(total * FPS))
    workers = workers or max(1, mp.cpu_count())
    fonts = "/usr/share/fonts/truetype/dejavu"
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "png", "-i", "-",
           "-i", str(wav), "-vf", f"ass={ass}:fontsdir={fonts},format=yuv420p",
           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-r", str(FPS), "-c:a", "aac", "-b:a", "192k",
           "-movflags", "+faststart", "-t", f"{total:.3f}", str(out_mp4)]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    ctx = mp.get_context("fork")
    with ctx.Pool(workers, initializer=_init, initargs=(data["pack"], tl)) as pool:
        for k, png in enumerate(pool.imap(render_frame, range(nframes), chunksize=4)):
            ff.stdin.write(png)
            if k % 150 == 0:
                log(f"  frame {k}/{nframes}")
    ff.stdin.close()
    if ff.wait() != 0:
        raise RuntimeError("ffmpeg falló al codificar el video")
    return nframes


def make(script_path, out_dir, workers=None, log=print):
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    data = load_script(script_path)
    pack = importlib.import_module(f"edu2d.scenes_{data['pack']}")
    log("1/4 Narración (TTS) y validación de audio…")
    tl, total = build_timeline(data, out_dir / "work")
    for s in tl:
        log(f"   {s['scene']:10s} inicio {s['start']:6.2f}s  dur {s['dur']:5.2f}s  (voz {s['audio_dur']:.2f}s, {s['mean_db']:.1f} dB)")
    log(f"   duración total: {total:.2f}s")
    log("2/4 Mezcla de audio…")
    wav = out_dir / "work" / "audio.wav"
    build_audio(tl, total, pack, wav)
    check_audio(wav)
    log("3/4 Subtítulos…")
    words = [w for s in tl for w in s["words"]]
    keys = {k for s in tl for k in s["highlight"]}
    ass = out_dir / "work" / "subs.ass"
    nev = build_ass(words, keys, ass)
    log(f"   {nev} eventos de subtítulo")
    (out_dir / "work" / "timeline.json").write_text(json.dumps(tl, ensure_ascii=False, indent=1))
    log("4/4 Render de frames SVG y codificación…")
    mp4 = out_dir / f"{data.get('slug','video')}.mp4"
    nf = render_video(data, tl, total, wav, ass, mp4, workers, log)
    log(f"   {nf} frames -> {mp4}")
    return mp4, tl, total
