"""Orquestación: TTS (con preflight) → SRT → mezcla → render 2D → MP4 H.264/AAC."""
from __future__ import annotations

import json
import multiprocessing as mp
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

from . import narration as nar
from . import soundscape
from .script_es import END_CARD, SCENES, TITLE

ROOT = Path(__file__).resolve().parents[3]
FONT = ROOT / "resource" / "fonts" / "BeVietnamPro-Bold.ttf"
FPS = 30


def _ffmpeg() -> str:
    return shutil.which("ffmpeg") or __import__("imageio_ffmpeg").get_ffmpeg_exe()


# ---- render paralelo -------------------------------------------------------
_R = None


def _init(args):
    global _R
    from .scenes import Renderer
    starts, ends, cues = args
    _R = Renderer(starts, ends, cues, TITLE, END_CARD, FONT)


def _render_chunk(job):
    idx, f0, f1, out = job
    cmd = [_ffmpeg(), "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", "1080x1920", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.1",
           "-g", str(FPS), "-keyint_min", str(FPS), "-sc_threshold", "0", "-an", str(out)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(f0, f1):
        p.stdin.write(_R.frame(f / FPS).tobytes())
    p.stdin.close()
    if p.wait() != 0:
        raise RuntimeError(f"ffmpeg falló en chunk {idx}")
    return idx


def render_video(starts, ends, cues, work: Path, total: float, workers: int = 4, log=print) -> Path:
    n = int(round(total * FPS))
    per = -(-n // (workers * 3))
    per = -(-per // FPS) * FPS    # trozos múltiplos de 1 s => GOP alineado
    jobs, f = [], 0
    while f < n:
        jobs.append((len(jobs), f, min(n, f + per), work / f"chunk_{len(jobs):03d}.mp4"))
        f += per
    t0 = time.time()
    with mp.get_context("fork").Pool(workers, initializer=_init, initargs=((starts, ends, cues),)) as pool:
        for i in pool.imap_unordered(_render_chunk, jobs):
            log(f"[RENDER] trozo {i+1}/{len(jobs)} listo ({time.time()-t0:.0f}s)")
    lst = work / "chunks.txt"
    lst.write_text("".join(f"file '{j[3].name}'\n" for j in jobs))
    silent = work / "video_silent.mp4"
    subprocess.run([_ffmpeg(), "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(silent)], check=True)
    return silent


def run(out_dir: Path, *, prefer_tts: str | None = None, workers: int = 4, speed: float = 0.9, log=print, only_audio=False) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    work = out_dir / "work"
    work.mkdir(exist_ok=True)
    model_dir = ROOT / "storage" / "models" / "kokoro"
    # 1) PREFLIGHT TTS — nunca se continúa sin voz
    engine = nar.select_engine(model_dir, log=log, prefer=prefer_tts)
    # 2) narración
    N = nar.build_narration(SCENES, engine, model_dir, speed=speed, log=log)
    voice = nar.shape_voice(N.voice, _ffmpeg())
    if _peak_check(voice) < 0.05:
        raise nar.TTSUnavailableError("La narración generada está vacía/silenciosa; abortando.")
    cues = nar.build_srt(N.clauses)
    nar.write_srt(out_dir / "autoridad_hielo.srt", cues)
    nar.write_wav(out_dir / "narracion.wav", voice / max(1e-6, np.abs(voice).max()) * 0.9)
    starts, ends, total = N.scene_starts, N.scene_ends, N.total
    log(f"[INFO] motor={engine} duración total={total:.2f}s escenas={[round(e-s,2) for s,e in zip(starts,ends)]}")
    # 3) mezcla de audio
    stereo, _ = soundscape.mix(voice, starts, ends, total)
    mix_raw = work / "mix_raw.wav"
    _write_stereo(mix_raw, stereo)
    mix_wav = out_dir / "mezcla_final.wav"
    subprocess.run([_ffmpeg(), "-y", "-v", "error", "-i", str(mix_raw), "-af", f"loudnorm=I=-17:TP=-2.5:LRA=9,alimiter=limit=0.8:level=false,atrim=0:{total:.3f}", "-ar", "48000", str(mix_wav)], check=True)
    subprocess.run([_ffmpeg(), "-y", "-v", "error", "-i", str(out_dir / "narracion.wav"), "-b:a", "192k", str(out_dir / "narracion.mp3")], check=True)
    json.dump({"engine": engine, "scene_starts": starts, "scene_ends": ends, "total": total,
               "clauses": [c.__dict__ for c in N.clauses], "cues": [[s, e, l] for s, e, l in cues]},
              open(out_dir / "timeline.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if only_audio:
        return {"engine": engine, "total": total}
    # 4) vídeo: los subtítulos se leen del SRT guardado
    srt_cues = nar.read_srt(out_dir / "autoridad_hielo.srt")
    silent = render_video(starts, ends, srt_cues, work, total, workers, log)
    final = out_dir / "autoridad_hielo.mp4"
    subprocess.run([_ffmpeg(), "-y", "-v", "error", "-i", str(silent), "-i", str(mix_wav), "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-movflags", "+faststart",
                    "-t", f"{total:.3f}", str(final)], check=True)
    return {"engine": engine, "total": total, "mp4": str(final)}


def _peak_check(x): return float(np.abs(x).max())


def _write_stereo(path: Path, st: np.ndarray):
    import wave
    pcm = (np.clip(st, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(soundscape.SR); w.writeframes(pcm.tobytes())
