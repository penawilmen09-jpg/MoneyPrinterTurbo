"""Verificación del MP4 final: formato, audio, subtítulos y movimiento real."""
import json
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image

from .audio_check import AudioError, check_audio, probe


def _frame(mp4, t, w=270, h=480):
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", str(mp4), "-frames:v", "1",
                        "-vf", f"scale={w}:{h}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True)
    if len(r.stdout) != w * h * 3:
        raise AudioError(f"no se pudo extraer el frame en t={t:.2f}s")
    return np.frombuffer(r.stdout, np.uint8).reshape(h, w, 3).astype(np.int16)


def verify_mp4(mp4, timeline=None, expect=(1080, 1920), log=print):
    problems, p = [], Path(mp4)
    if not p.exists() or p.stat().st_size < 100_000:
        raise AudioError(f"MP4 inexistente o demasiado pequeño: {p}")
    info = probe(p)
    v = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    dur = float(info["format"]["duration"])
    if not v or not a:
        problems.append("falta pista de video o audio")
        raise AudioError("; ".join(problems))
    if (v["width"], v["height"]) != expect:
        problems.append(f"resolución {v['width']}x{v['height']} != {expect}")
    if v["codec_name"] != "h264":
        problems.append(f"codec {v['codec_name']}")
    au = check_audio(p)
    log(f"  video {v['width']}x{v['height']} {v['codec_name']} {v['r_frame_rate']} fps | audio {a['codec_name']} "
        f"{au['mean_db']} dB media | duración {dur:.2f}s | {p.stat().st_size/1e6:.1f} MB")
    if abs(float(a.get("duration", dur)) - float(v.get("duration", dur))) > 0.3:
        problems.append("duración de audio y video no coinciden")

    # movimiento: cada ~2 s comparar frames separados 0.4 s; también que no sean negros
    static, sub_missing, samples = 0, 0, 0
    ts = [x * 2.0 + 1.0 for x in range(int((dur - 2) // 2))]
    for t in ts:
        f1, f2 = _frame(p, t), _frame(p, t + .4)
        samples += 1
        if f1.mean() < 8:
            problems.append(f"frame negro en t={t:.1f}s")
        if np.abs(f1 - f2).mean() < 0.15:
            static += 1
            problems.append(f"imagen estática en t={t:.1f}s")
        band = f1[int(480 * .68):int(480 * .8)]            # franja de subtítulos
        txt = (band[..., 1] > 215).mean()        # blanco, amarillo o menta: todos tienen G alto
        speaking = (not timeline) or any(w["start"] - .05 <= t <= w["end"] + .15
                                         for sc in timeline for w in sc["words"])
        if txt < 0.0025 and speaking:
            sub_missing += 1
            problems.append(f"sin subtítulos visibles en t={t:.1f}s")
    log(f"  {samples} muestras: {static} estáticas, {sub_missing} sin subtítulos")
    if timeline:
        end_words = timeline[-1]["words"][-1]["end"]
        if dur < end_words:
            problems.append("el video termina antes que la narración")
    return problems


def check_sync(timeline, min_db=-42.0):
    """Contrasta los tiempos de palabra de los subtítulos con la forma de onda REAL de la voz.
    Devuelve (fracción de palabras con voz audible en su ventana, desfase medio de inicio de escena en s)."""
    import subprocess
    SR = 22050
    ok, tot, onsets = 0, 0, []
    for sc in timeline:
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", sc["audio"], "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"],
                             capture_output=True).stdout
        a = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
        base = sc["start"] + sc["lead"]
        for w in sc["words"]:
            s0, s1 = int((w["start"] - base) * SR), int((w["end"] - base) * SR)
            seg = a[max(s0, 0):max(s1, s0 + 1)]
            tot += 1
            rms = 20 * np.log10(np.sqrt(np.mean(seg ** 2)) + 1e-9) if len(seg) else -99
            ok += rms > min_db
        env = np.abs(a)
        k = int(.01 * SR)
        smooth_ = np.convolve(env, np.ones(k) / k, mode="same")
        idx = np.argmax(smooth_ > 0.02)
        onsets.append(abs(idx / SR - (sc["words"][0]["start"] - base)))
    return ok / tot, float(np.mean(onsets))


def check_loudness(mp4, max_true_peak=-0.5):
    """Revisión del audio completo del MP4: sonoridad integrada, pico real y ausencia de recortes."""
    import re, subprocess
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(mp4), "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True)
    I = re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr)
    P = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r.stderr)
    if not I or not P:
        raise AudioError("no se pudo medir la sonoridad del MP4")
    lufs, peak = float(I[-1]), float(P[-1])
    if peak > max_true_peak:
        raise AudioError(f"audio con pico {peak} dBFS (> {max_true_peak}): riesgo de recorte")
    return lufs, peak


def check_gaps(timeline, max_gap=1.5):
    """Silencios de narración inesperados: pausas largas entre palabras consecutivas (la cola final es intencional)."""
    words = [w for s in timeline for w in s["words"]]
    gaps = [(b["start"] - a["end"], a["text"], b["text"]) for a, b in zip(words, words[1:])]
    worst = max(gaps, key=lambda g: g[0])
    lead = words[0]["start"]
    return worst, lead, [g for g in gaps if g[0] > max_gap]
