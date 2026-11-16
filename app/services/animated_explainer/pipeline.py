"""Orquestación: guion -> TTS -> escenas animadas -> mezcla -> FFmpeg -> MP4 1080x1920."""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field
import logging
import math
import multiprocessing as mp
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Callable

import numpy as np

from . import audio, subtitles
from .script import ExplainerScript, Scene

log = logging.getLogger("animated_explainer")

W, H = 1080, 1920
TRANSITION_SECONDS = 0.5
FONTS_DIR = Path(__file__).resolve().parents[3] / "resource" / "fonts"


@dataclass
class SceneTiming:
    index: int
    start: float          # inicio de la escena en el video final
    duration: float
    lead: float           # silencio antes de la narración
    transition_out: float


@dataclass
class RenderResult:
    path: str
    duration: float
    srt_path: str | None
    tts_providers: list[str]
    scenes: list[SceneTiming] = field(default_factory=list)


def plan_timing(scenes: list[Scene], speech_durations: list[float]) -> list[SceneTiming]:
    """Calcula inicio/duración de cada escena para que las transiciones no pisen la voz."""
    n = len(scenes)
    t_out = [0.0 if (i == n - 1 or scenes[i].transition == "none") else TRANSITION_SECONDS
             for i in range(n)]
    out, cursor = [], 0.0
    for i, sc in enumerate(scenes):
        t_in = t_out[i - 1] if i > 0 else 0.0
        lead = max(0.3, t_in + 0.15)
        tail = max(0.6, t_out[i] + 0.25)
        dur = max(sc.min_duration, lead + speech_durations[i] + tail)
        dur = math.ceil(dur * 30) / 30  # múltiplo de fotograma a 30 fps
        out.append(SceneTiming(sc.index, cursor, dur, lead, t_out[i]))
        cursor += dur - t_out[i]
    return out


# ------------------------------------------------------------------ render de escenas (multiproceso)
def _render_chunk(args) -> str:
    (scene, characters, duration, env, speech_start, words, fps, start, end, out_file,
     draft) = args
    from .animator import SceneRenderer
    r = SceneRenderer(scene, characters, duration, env, speech_start, words, fps)
    vf = "scale=540:960:flags=lanczos" if draft else "null"
    cmd = [audio.ffmpeg_bin(), "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(fps), "-i", "-", "-vf", vf, "-c:v", "libx264",
           "-preset", "veryfast", "-crf", "12" if not draft else "20", "-pix_fmt", "yuv420p",
           "-g", str(fps * 2), "-an", out_file]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    try:
        for i in range(start, end):
            p.stdin.write(r.frame(i).tobytes())
        p.stdin.close()
        if p.wait() != 0:
            raise RuntimeError(f"FFmpeg falló al codificar {out_file}")
    finally:
        if p.poll() is None:
            p.kill()
    return out_file


def _render_scene_video(scene, characters, timing: SceneTiming, speech: audio.Speech, fps: int,
                        work: Path, workers: int, draft: bool) -> Path:
    n = int(round(timing.duration * fps))
    env = audio.envelope(speech.pcm, fps)
    nchunks = max(1, min(workers, n // 12))
    bounds = np.linspace(0, n, nchunks + 1, dtype=int)
    jobs, files = [], []
    for k in range(nchunks):
        f = str(work / f"s{scene.index:02d}_{k:02d}.mp4")
        files.append(f)
        jobs.append((scene, characters, timing.duration, env, timing.lead, speech.words, fps,
                     int(bounds[k]), int(bounds[k + 1]), f, draft))
    if nchunks == 1:
        _render_chunk(jobs[0])
    else:
        ctx = mp.get_context("fork") if "fork" in mp.get_all_start_methods() else mp.get_context()
        with ProcessPoolExecutor(max_workers=nchunks, mp_context=ctx) as ex:
            list(ex.map(_render_chunk, jobs))
    final = work / f"scene_{scene.index:02d}.mp4"
    if nchunks == 1:
        os.replace(files[0], final)
    else:
        lst = work / f"s{scene.index:02d}.txt"
        lst.write_text("".join(f"file '{Path(f).name}'\n" for f in files))
        subprocess.run([audio.ffmpeg_bin(), "-y", "-v", "error", "-f", "concat", "-safe", "0",
                        "-i", str(lst), "-c", "copy", str(final)], check=True, cwd=work)
    return final


# ------------------------------------------------------------------ sfx automáticos
_AUTO_EMOTE_SFX = {"exclaim": "pop", "question": "pop", "idea": "ding", "sweat": "drip",
                   "anger": "thud", "heart": "sparkle", "dots": "click", "clock": "tick"}
_TRANS_SFX = {"fade": None, "dissolve": None, "none": None, "fadeblack": "sting"}


def collect_sfx(scene: Scene, timing: SceneTiming, next_transition: str | None):
    """Lista (tiempo_abs, pcm, ganancia, pan) a partir de eventos, sfx explícitos y automáticos."""
    out = []
    D, S = timing.duration, timing.start
    for s in scene.sfx:
        pcm = audio.get_sfx(s["name"])
        out.append((S + s["at"] * D, pcm, float(s.get("gain", 0.8)), float(s.get("pan", 0.0))))
    for ev in scene.events:
        t = S + ev["at"] * D
        et = ev["type"]
        if et == "sfx":
            out.append((t, audio.get_sfx(ev["name"]), float(ev.get("gain", 0.8)), float(ev.get("pan", 0.0))))
        elif et == "emote" and _AUTO_EMOTE_SFX.get(ev["value"]):
            out.append((t, audio.get_sfx(_AUTO_EMOTE_SFX[ev["value"]]), 0.6, 0.0))
        elif et == "label":
            out.append((t, audio.get_sfx("pop"), 0.5, 0.0))
        elif et == "shake":
            out.append((t, audio.get_sfx("thud"), 0.8, 0.0))
        elif et == "move" and ev.get("walk", True):
            dur = max(0.4, float(ev.get("dur", 0.25)) * D)
            out.append((t, audio.sfx_steps(dur), 0.45, 0.0))
    if next_transition and next_transition != "none":
        name = _TRANS_SFX.get(next_transition, "whoosh")
        if next_transition in ("fade", "dissolve"):
            name = "swipe"
        if name:
            out.append((S + D - TRANSITION_SECONDS - 0.05, audio.get_sfx(name), 0.45, 0.0))
    return out


# ------------------------------------------------------------------ ensamblado FFmpeg
def _assemble(scene_files, scenes, timings, wav, ass_file, out_path, fps, draft, srt_burn: bool,
              work: Path, crf: int):
    exe = audio.ffmpeg_bin()
    inputs = []
    for f in scene_files:
        inputs += ["-i", str(f)]
    inputs += ["-i", str(wav)]
    n = len(scene_files)
    parts, last = [], "[v0]"
    for i in range(n):
        parts.append(f"[{i}:v]setsar=1,fps={fps},format=yuv420p[p{i}]")
    cur = "[p0]"
    for k in range(1, n):
        tr = scenes[k - 1].transition
        if tr == "none":
            tr, d = "fade", 0.04
        else:
            d = TRANSITION_SECONDS
        # timings[k-1].transition_out puede ser 0.04 en 'none'; usamos el offset real
        offset = timings[k].start if scenes[k - 1].transition != "none" else \
            timings[k - 1].start + timings[k - 1].duration - 0.04
        parts.append(f"{cur}[p{k}]xfade=transition={tr}:duration={d}:offset={offset:.3f}[x{k}]")
        cur = f"[x{k}]"
    vlabel = cur
    if ass_file is not None:
        fd = "fonts"
        parts.append(f"{vlabel}ass=subs.ass:fontsdir={fd}[vs]")
        vlabel = "[vs]"
    if draft:
        pass
    filt = ";".join(parts)
    total = timings[-1].start + timings[-1].duration
    cmd = [exe, "-y", "-v", "error", *inputs, "-filter_complex", filt, "-map", vlabel,
           "-map", f"{n}:a", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11,aresample=44100",
           "-c:v", "libx264", "-preset", "medium", "-crf", str(crf), "-pix_fmt", "yuv420p",
           "-profile:v", "high", "-r", str(fps), "-c:a", "aac", "-b:a", "192k",
           "-t", f"{total:.3f}", "-movflags", "+faststart", str(Path(out_path).resolve())]
    subprocess.run(cmd, check=True, cwd=work)


def render_video(script: ExplainerScript, out_path: str, *, tts: str = "auto",
                 voice: str | None = None, music: str | None = None, fps: int = 30,
                 workers: int | None = None, draft: bool = False, subtitles_on: bool = True,
                 work_dir: str | None = None, keep_work: bool = False, crf: int = 18,
                 progress: Callable[[str, float], None] | None = None) -> RenderResult:
    """Renderiza el guion completo a MP4 vertical (1080x1920; 540x960 con ``draft``)."""
    prog = progress or (lambda stage, frac: None)
    if draft:
        fps = min(fps, 15)
    workers = workers or max(1, (os.cpu_count() or 2))
    out_path = str(out_path)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    work_ctx = tempfile.TemporaryDirectory(prefix="explainer_") if not work_dir else None
    work = Path(work_dir) if work_dir else Path(work_ctx.name)
    work.mkdir(parents=True, exist_ok=True)
    try:
        # 1) narración
        speeches = []
        for i, sc in enumerate(script.scenes):
            prog("tts", i / len(script.scenes))
            speeches.append(audio.synthesize(sc.narration, voice=voice or script.voice,
                                             rate=script.rate, pitch=script.pitch, provider=tts))
        timings = plan_timing(script.scenes, [s.duration for s in speeches])
        total = timings[-1].start + timings[-1].duration
        log.info("Duración total: %.1fs (%d escenas)", total, len(timings))

        # 2) animación por escena
        files = []
        for i, (sc, tm, sp) in enumerate(zip(script.scenes, timings, speeches)):
            prog("scenes", i / len(script.scenes))
            log.info("Renderizando escena %d/%d (%s, %.1fs)", i + 1, len(script.scenes), sc.setting, tm.duration)
            files.append(_render_scene_video(sc, script.characters, tm, sp, fps, work, workers, draft))

        # 3) audio
        prog("audio", 0.0)
        speech_tracks = [(tm.start + tm.lead, sp.pcm) for tm, sp in zip(timings, speeches)]
        sfx = []
        for i, (sc, tm) in enumerate(zip(script.scenes, timings)):
            nxt = sc.transition if i < len(script.scenes) - 1 else None
            sfx += collect_sfx(sc, tm, nxt)
        music_spec = music if music is not None else script.music
        mus = audio.load_music(music_spec, total + 1.0)
        mixed = audio.mix(total, speech_tracks, sfx, mus)
        wav = work / "mix.wav"
        audio.write_wav(wav, mixed)

        # 4) subtítulos
        words = []
        for tm, sp in zip(timings, speeches):
            words += [(w, tm.start + tm.lead + a, tm.start + tm.lead + b) for w, a, b in sp.words]
        srt_path = None
        ass_file = None
        if subtitles_on and words:
            ass = subtitles.build_ass(words, width=W, height=H if not draft else H)
            (work / "subs.ass").write_text(ass, encoding="utf-8")
            fonts = work / "fonts"
            fonts.mkdir(exist_ok=True)
            for ttf in FONTS_DIR.glob("BeVietnamPro-*.ttf"):
                shutil.copy(ttf, fonts / ttf.name)
            ass_file = work / "subs.ass"
            srt_path = str(Path(out_path).with_suffix(".srt"))
            Path(srt_path).write_text(subtitles.build_srt(words), encoding="utf-8")

        # 5) unión + exportación
        prog("export", 0.0)
        if draft and ass_file is not None:  # ASS está en 1080x1920: libass escala por PlayRes
            pass
        _assemble(files, script.scenes, timings, wav, ass_file, out_path, fps, draft,
                  subtitles_on, work, crf)
        prog("done", 1.0)
        return RenderResult(out_path, total, srt_path, [s.provider for s in speeches], timings)
    finally:
        if work_ctx and not keep_work:
            work_ctx.cleanup()
