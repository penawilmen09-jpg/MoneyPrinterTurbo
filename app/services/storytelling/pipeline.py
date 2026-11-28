"""Orquestación completa: plan -> voz -> render -> mezcla -> QC -> MP4 final."""

from __future__ import annotations

import json
import multiprocessing as mp
import os
import shutil
import subprocess
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
from typing import Callable

import numpy as np

from . import audio as A
from .models import StoryPlan
from .render import SceneJob, render_scene_clip
from .subtitles import build_captions, captions_to_srt

# Voz del narrador (la misma configurada actualmente; no se sustituye automáticamente).
ELEVENLABS_VOICE_ID = "851ejYcv2BoNPjrkw93G"
DEFAULT_VOICE_NAME = f"elevenlabs:{ELEVENLABS_VOICE_ID}:Narrador"

LEAD = 0.12  # silencio antes de que hable el narrador en cada escena
TAIL = 0.55  # hueco posterior (aquí ocurre la transición y caen los efectos)
FINAL_TAIL = 1.0
XFADE = {"cut": ("fade", 0.06), "fade": ("fade", 0.35), "dissolve": ("dissolve", 0.4),
         "slide_left": ("slideleft", 0.35), "slide_right": ("slideright", 0.35),
         "circle": ("circleopen", 0.4), "wipe": ("wipeleft", 0.35), "zoom": ("zoomin", 0.4)}

ProgressFn = Callable[[float, str], None]


def default_voice_name() -> str:
    """Voz configurada: si la UI ya usa una voz ElevenLabs se respeta; si no, la del encargo."""
    try:
        from app.config import config

        name = str(config.ui.get("voice_name", "") or "")
        if name.startswith("elevenlabs:"):
            return name
    except Exception:
        pass
    return DEFAULT_VOICE_NAME


def elevenlabs_tts(text: str, voice_name: str, path: str) -> bool:
    """TTS con la integración ElevenLabs existente de MoneyPrinterTurbo."""
    from app.services import voice

    sub = voice.tts(text=text, voice_name=voice_name, voice_rate=1.0, voice_file=path)
    return sub is not None and os.path.exists(path) and os.path.getsize(path) > 0


def espeak_dev_tts(text: str, voice_name: str, path: str) -> bool:
    """SOLO para pruebas sin clave de ElevenLabs (voz robótica local, no es la voz final)."""
    wav = path + ".wav"
    subprocess.run(["espeak-ng", "-v", "es-419", "-s", "158", "-p", "38", "-w", wav, text], check=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", wav, path], check=True)
    os.remove(wav)
    return True


def _probe_duration(path: str) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                         capture_output=True, text=True, check=True).stdout.strip()
    return float(out)


def generate_story_video(
    plan: StoryPlan,
    out_dir: str,
    *,
    tts_fn: Callable[[str, str, str], bool] | None = None,
    voice_name: str | None = None,
    size: tuple[int, int] = (1080, 1920),
    fps: int = 24,
    music: bool = True,
    songs_dir: str | None = None,
    workers: int | None = None,
    progress: ProgressFn | None = None,
    max_scene_frames: int = 0,
    run_qc: bool = True,
) -> dict:
    """Genera el vídeo completo. Devuelve un dict con rutas, duración e informe de calidad."""
    t_start = time.time()
    os.makedirs(out_dir, exist_ok=True)
    clips_dir = os.path.join(out_dir, "clips")
    audio_dir = os.path.join(out_dir, "audio")
    for d in (clips_dir, audio_dir):
        os.makedirs(d, exist_ok=True)
    tts_fn = tts_fn or elevenlabs_tts
    voice_name = voice_name or default_voice_name()

    def prog(frac: float, msg: str):
        if progress:
            progress(frac, msg)

    with open(os.path.join(out_dir, "plan.json"), "w", encoding="utf-8") as f:
        f.write(plan.to_json())
    with open(os.path.join(out_dir, "characters.json"), "w", encoding="utf-8") as f:
        json.dump([{**c.normalized().__dict__, "visual_description": c.visual_description(),
                    "fingerprint": c.fingerprint()} for c in plan.characters], f, ensure_ascii=False, indent=2, default=list)

    # ---------------- 1) narración por escena (una llamada TTS por escena) ----------------
    n = len(plan.scenes)
    speech = []
    for i, sc in enumerate(plan.scenes):
        prog(0.02 + 0.18 * i / n, f"Narración escena {i + 1}/{n}")
        mp3 = os.path.join(audio_dir, f"scene_{sc.number:02d}.mp3")
        if not (os.path.exists(mp3) and os.path.getsize(mp3) > 0):
            if not tts_fn(sc.narration, voice_name, mp3):
                raise RuntimeError(
                    f"No se pudo sintetizar la narración de la escena {sc.number}. "
                    "Comprueba la clave de ElevenLabs (config.toml [elevenlabs] api_key o ELEVENLABS_API_KEY)."
                )
        x = A.decode_mono(mp3)
        s0, s1 = A.speech_bounds(x)
        speech.append({"x": x, "s0": s0, "s1": s1, "len": max(0.3, s1 - s0)})

    # ---------------- 2) tiempos de escena ----------------
    starts, durations, pre_rolls = [], [], []
    cursor = 0.0
    for i, sc in enumerate(plan.scenes):
        tail = FINAL_TAIL if i == n - 1 else TAIL
        d = LEAD + speech[i]["len"] + tail
        starts.append(cursor)
        durations.append(d)
        sc.duration = round(d, 3)
        pre_rolls.append(0.0 if i == 0 else XFADE.get(sc.transition_in, XFADE["fade"])[1])
        cursor += d
    total = cursor

    # pista de narración completa
    narr = np.zeros(int((total + 1) * A.SR), dtype=np.float32)
    for i in range(n):
        seg = speech[i]["x"][int(speech[i]["s0"] * A.SR): int(speech[i]["s1"] * A.SR)]
        off = int((starts[i] + LEAD) * A.SR)
        narr[off: off + len(seg)] += seg
    narr_wav = os.path.join(out_dir, "narration.wav")
    A.write_wav(narr_wav, narr)

    # ---------------- 3) subtítulos ----------------
    all_caps = []
    scene_caps = []
    for i, sc in enumerate(plan.scenes):
        caps = build_captions(sc.narration, LEAD, LEAD + speech[i]["len"], sc.keywords)
        scene_caps.append(caps)
        all_caps.append((starts[i], caps))
    with open(os.path.join(out_dir, "subtitles.srt"), "w", encoding="utf-8") as f:
        f.write(captions_to_srt(all_caps))

    # ---------------- 4) render de escenas en paralelo ----------------
    plan_dict = plan.to_dict()
    jobs = []
    for i, sc in enumerate(plan.scenes):
        env = A.envelope(speech[i]["x"], speech[i]["s0"], speech[i]["s1"])
        disc_windows = []
        if plan.veracity != "real" and plan.disclaimer:
            if i == 0:
                disc_windows = [(0.3, min(durations[i], 3.8))]
            if i == n - 1:
                disc_windows = [(max(0.0, durations[i] - 3.4), durations[i] - 0.2)]
        jobs.append(SceneJob(
            plan=plan_dict, scene_index=i, duration=durations[i], pre_roll=pre_rolls[i], fps=fps,
            out_path=os.path.join(clips_dir, f"scene_{sc.number:02d}.mp4"), size=size,
            speech_start=LEAD, speech_end=LEAD + speech[i]["len"], env=env,
            captions=[(c.start, c.end, [list(w) for w in c.words]) for c in scene_caps[i]],
            disclaimer_text=plan.disclaimer if disc_windows else "", disclaimer_windows=disc_windows,
            max_frames=max_scene_frames,
        ))
    workers = workers or max(1, min(len(jobs), (os.cpu_count() or 2)))
    done = 0
    ctx = mp.get_context("spawn")
    with ProcessPoolExecutor(max_workers=workers, mp_context=ctx) as ex:
        for res in ex.map(render_scene_clip, jobs):
            done += 1
            prog(0.20 + 0.55 * done / len(jobs), f"Animación escena {res['scene']} lista ({done}/{len(jobs)})")

    # ---------------- 5) unión con transiciones ----------------
    prog(0.77, "Uniendo escenas con transiciones")
    silent = os.path.join(out_dir, "video_silent.mp4")
    _concat_with_xfade([j.out_path for j in jobs], plan.scenes, durations, pre_rolls, size, fps, silent)

    # ---------------- 6) audio ----------------
    prog(0.86, "Mezclando audio")
    events = A.plan_sfx([{"start": starts[i], "lead": LEAD, "sfx": plan.scenes[i].sfx, "label": plan.scenes[i].label}
                         for i in range(n)])
    sfx_wav = os.path.join(out_dir, "sfx.wav")
    A.write_wav(sfx_wav, A.build_sfx_track(events, total))
    songs_dir = songs_dir or os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))), "resource", "songs")
    music_path = A.pick_music(songs_dir, seed=len(plan.title)) if music else None
    mix_path = os.path.join(out_dir, "mix.m4a")
    A.mix_audio(narr_wav, sfx_wav, music_path, total, mix_path)

    final = os.path.join(out_dir, "final.mp4")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", silent, "-i", mix_path, "-c:v", "copy", "-c:a", "aac",
                    "-b:a", "192k", "-shortest", "-movflags", "+faststart", final], check=True)

    result = {
        "video": final, "srt": os.path.join(out_dir, "subtitles.srt"), "plan": os.path.join(out_dir, "plan.json"),
        "duration": _probe_duration(final), "scene_starts": starts, "scene_durations": durations,
        "sfx_events": events, "music": os.path.basename(music_path) if music_path else None, "voice": voice_name,
        "narration_wav": narr_wav, "music_path": music_path, "sfx_wav": sfx_wav,
        "render_seconds": round(time.time() - t_start, 1),
    }
    if run_qc:
        prog(0.93, "Control de calidad")
        from .qc import run_quality_checks

        result["qc"] = run_quality_checks(plan, result, size=size)
        with open(os.path.join(out_dir, "qc_report.json"), "w", encoding="utf-8") as f:
            json.dump(result["qc"], f, ensure_ascii=False, indent=2)
    prog(1.0, "Vídeo listo")
    with open(os.path.join(out_dir, "result.json"), "w", encoding="utf-8") as f:
        json.dump({k: v for k, v in result.items() if k != "qc"}, f, ensure_ascii=False, indent=2)
    return result


def _concat_with_xfade(clips: list[str], scenes, durations, pre_rolls, size, fps, out_path: str) -> None:
    if len(clips) == 1:
        shutil.copy(clips[0], out_path)
        return
    cmd = ["ffmpeg", "-y", "-v", "error"]
    for c in clips:
        cmd += ["-i", c]
    filt, label, run = [], "[0:v]", durations[0]
    for i in range(1, len(clips)):
        name, tx = XFADE.get(scenes[i].transition_in, XFADE["fade"])
        out = f"[x{i}]"
        filt.append(f"{label}[{i}:v]xfade=transition={name}:duration={tx:.3f}:offset={run - tx:.3f}{out}")
        label, run = out, run + durations[i]
    cmd += ["-filter_complex", ";".join(filt), "-map", label, "-r", str(fps), "-c:v", "libx264", "-preset", "medium",
            "-crf", "16", "-pix_fmt", "yuv420p", out_path]
    subprocess.run(cmd, check=True)
