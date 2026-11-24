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
