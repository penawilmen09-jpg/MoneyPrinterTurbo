"""Automatic quality control of the finished video. Failing scenes are identified
so only those need re-rendering."""

from __future__ import annotations

import json
import math
import shutil
import subprocess
import os

import numpy as np

from app.utils import utils

from . import audio as A
from . import gfx as G
from .models import Plan, SceneTiming

DURATION_WINDOW = {45: (45.0, 54.0), 60: (55.0, 60.0)}


def _ffprobe() -> str:
    ff = utils.get_ffmpeg_binary()
    cand = os.path.join(os.path.dirname(ff), "ffprobe")
    if os.path.exists(cand):
        return cand
    return shutil.which("ffprobe") or "ffprobe"


def probe(path: str) -> dict:
    out = subprocess.run([_ffprobe(), "-v", "error", "-print_format", "json", "-show_streams", "-show_format", path],
                         capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def _gray_frames(path: str, rate: int = 5) -> np.ndarray:
    cmd = [utils.get_ffmpeg_binary(), "-v", "error", "-i", path, "-vf", f"fps={rate},scale=108:192,format=gray",
           "-f", "rawvideo", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.uint8).reshape(-1, 192, 108)


def _scene_at(timings: list[SceneTiming], t: float) -> str:
    for tm in timings:
        if tm.start <= t < tm.start + tm.duration:
            return tm.id
    return timings[-1].id


def run_qc(video: str, plan: Plan, timings: list[SceneTiming], mix: dict, duration_target: int, fps: int,
           workdir: str) -> dict:
    checks: list[dict] = []
    failing: set[str] = set()

    def add(name, ok, detail, scenes=()):
        checks.append({"name": name, "ok": bool(ok), "detail": detail, "scenes": sorted(set(scenes))})
        if not ok:
            failing.update(scenes)

    info = probe(video)
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    has_audio = any(s["codec_type"] == "audio" for s in info["streams"])
    dur = float(info["format"]["duration"])
    lo, hi = DURATION_WINDOW[duration_target]
    add("duración", 45.0 <= dur <= 60.0 and lo <= dur <= hi, f"{dur:.2f}s (objetivo {duration_target}s: {lo}-{hi}s; absoluto 45-60s)")
    add("formato vertical 1080x1920",
        v["width"] == G.W and v["height"] == G.H and v.get("sample_aspect_ratio", "1:1") in ("1:1", "0:1", None),
        f"{v['width']}x{v['height']} SAR {v.get('sample_aspect_ratio')} (sin imágenes estiradas)")
    add("audio presente", has_audio, "pista de audio AAC" if has_audio else "sin audio")
    total_frames = int(v.get("nb_frames", 0) or 0)
    expected = sum(round(t.duration * fps) for t in timings)
    add("fotogramas completos", abs(total_frames - expected) <= 2, f"{total_frames} fotogramas (esperados {expected}; sin errores de render)")

    # --- visual: black / freeze / motion per scene (5 fps gray sampling)
    frames = _gray_frames(video)
    rate = 5
    means = frames.reshape(len(frames), -1).mean(axis=1)
    bad_black = [i for i, m in enumerate(means) if m < 10]
    add("sin pantallas negras", not bad_black, f"{len(bad_black)} muestras negras", [_scene_at(timings, i / rate) for i in bad_black])
    diffs = np.abs(frames[1:].astype(np.int16) - frames[:-1].astype(np.int16)).reshape(len(frames) - 1, -1).mean(axis=1)
    static_scenes, motion_report = [], {}
    for tm in timings:
        a, b = int(tm.start * rate) + 2, int((tm.start + tm.duration) * rate) - 1
        seg = diffs[a:b]
        if len(seg) == 0:
            continue
        motion_report[tm.id] = round(float(seg.mean()), 3)
        # longest run of (nearly) identical consecutive samples
        run = best = 0
        for d in seg:
            run = run + 1 if d < 0.02 else 0
            best = max(best, run)
        if seg.mean() < 0.15 or best / rate > 1.2:
            static_scenes.append(tm.id)
    add("movimiento continuo (sin escenas congeladas)", not static_scenes, f"movimiento medio por escena: {motion_report}", static_scenes)
    lum = {tm.id: float(means[int(tm.start * rate):max(int(tm.start * rate) + 1, int((tm.start + tm.duration) * rate))].mean()) for tm in timings}
    ref = float(np.median(list(lum.values())))
    incoh = [k for k, m in lum.items() if abs(m - ref) > 45]
    add("coherencia visual (luminosidad entre escenas)", not incoh, f"luminosidad media {ref:.0f}±45: " + ", ".join(f"{k}={v:.0f}" for k, v in lum.items()), incoh)

    # --- narration completeness + sync against the real voice stem
    voice = A.read_wav(mix["voice"])
    n_words = sum(len(t.words) for t in timings)
    expected_words = len(plan.narration_text().split())
    add("narración completa", n_words == expected_words and all(t.audio_path for t in timings),
        f"{n_words}/{expected_words} palabras con audio real")
    sr = A.SR
    dead, shifted = [], []
    for tm in timings:
        bad = 0
        for w in tm.words:
            a, b = int((tm.start + w.start) * sr), int((tm.start + w.end) * sr)
            if A.rms_db(voice[a:b]) < -48:
                bad += 1
        if tm.words and bad / len(tm.words) > 0.1:
            dead.append(tm.id)
        # onset check: first audible energy vs first word start
        a0 = int((tm.start + tm.lead - 0.4) * sr)
        a0 = max(0, a0)
        win = voice[a0:int((tm.start + tm.words[0].start + 1.2) * sr)]
        if len(win):
            env = np.convolve(np.abs(win), np.ones(int(0.01 * sr)) / (0.01 * sr), mode="same")
            idx = np.nonzero(env > 0.02)[0]
            if len(idx):
                onset = a0 / sr + idx[0] / sr
                if abs(onset - (tm.start + tm.words[0].start)) > 0.30:
                    shifted.append(tm.id)
    add("subtítulos sincronizados con la voz", not dead and not shifted,
        f"palabras sin voz en escenas {dead or 'ninguna'}; inicio desfasado >0.3s en {shifted or 'ninguna'}")
    gaps = []
    for a, b in zip(timings, timings[1:]):
        gap = (a.duration - a.words[-1].end) + b.words[0].start
        gaps.append(gap)
    inner = max((w2.start - w1.end for t in timings for w1, w2 in zip(t.words, t.words[1:])), default=0)
    add("sin silencios inesperados", max(gaps, default=0) <= 1.3 and inner <= 0.9,
        f"pausa máxima entre escenas {max(gaps, default=0):.2f}s; dentro de escena {inner:.2f}s")

    # --- mix: ducking / effects / loudness
    music = A.read_wav(mix["music"])
    sfx = A.read_wav(mix["sfx"])
    mask = np.zeros(len(voice), dtype=bool)
    for tm in timings:
        for w in tm.words:
            mask[int((tm.start + w.start) * sr):int((tm.start + w.end) * sr)] = True
    vb, mb, sb = (A.fft_band(x[:len(voice)], 400, 6000) for x in (voice, music, sfx))  # phone-speaker band
    voice_rms = A.rms_db(vb[mask])
    music_rms = A.rms_db(mb[mask])
    margin = voice_rms - music_rms
    add("música sin tapar la voz (ducking)", margin >= 16, f"voz {margin:.1f} dB por encima de la música durante el habla (mín. 16 dB, banda de teléfono)")
    events = mix["sfx_events"]
    over = [e for e in events if e["over_speech"]]
    sfx_peak = A.peak_db(sfx)
    voice_peak = A.peak_db(voice)
    add("efectos sin excesos", len(events) <= max(1, round(dur / 8.5)) and sfx_peak <= voice_peak - 3.0,
        f"{len(events)} efectos ({len(over)} sobre habla no clave), pico {sfx_peak:.1f} dBFS vs voz {voice_peak:.1f} dBFS; omitidos: {mix['sfx_notes']}")
    loud = A.measure_loudness(video)
    ok_l = loud["integrated_lufs"] is not None and abs(loud["integrated_lufs"] - A.TARGET_LUFS) <= 1.0
    ok_tp = loud["true_peak_dbtp"] is not None and loud["true_peak_dbtp"] <= A.TARGET_TP + 0.05
    add("volumen -16 LUFS / pico ≤ -1 dBTP", ok_l and ok_tp, f"{loud['integrated_lufs']} LUFS, {loud['true_peak_dbtp']} dBTP, LRA {loud['lra']}")

    report = {"passed": all(c["ok"] for c in checks), "checks": checks, "failing_scenes": sorted(failing),
              "duration": dur, "loudness": loud, "voice_margin_db": margin}
    with open(os.path.join(workdir, "qc.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    return report
