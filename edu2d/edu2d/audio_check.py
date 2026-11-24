"""Verificación de audio: existe, tiene contenido, se decodifica y no es silencio."""
import json
import re
import subprocess
from pathlib import Path


class AudioError(RuntimeError):
    pass


def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise AudioError(f"ffprobe no puede leer {path}: {r.stderr.strip()}")
    return json.loads(r.stdout)


def check_audio(path, min_duration=0.5, min_mean_db=-45.0):
    p = Path(path)
    if not p.exists():
        raise AudioError(f"no existe: {p}")
    if p.stat().st_size < 2000:
        raise AudioError(f"archivo demasiado pequeño ({p.stat().st_size} bytes): {p}")
    info = probe(p)
    streams = [s for s in info.get("streams", []) if s.get("codec_type") == "audio"]
    if not streams:
        raise AudioError(f"sin pista de audio: {p}")
    dur = float(info["format"].get("duration", 0))
    if dur < min_duration:
        raise AudioError(f"duración {dur:.2f}s < {min_duration}s: {p}")
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-v", "info", "-i", str(p), "-af", "volumedetect", "-vn", "-f", "null", "-"],
                       capture_output=True, text=True)
    if r.returncode != 0 or re.search(r"error while decoding|invalid data|corrupt", r.stderr, re.I):
        raise AudioError(f"el audio no se decodifica bien: {r.stderr.strip()[:300]}")
    m = re.search(r"mean_volume:\s*(-?[\d.]+|-inf) dB", r.stderr)
    mx = re.search(r"max_volume:\s*(-?[\d.]+|-inf) dB", r.stderr)
    if not m or m.group(1) == "-inf":
        raise AudioError(f"audio en silencio: {p}")
    mean = float(m.group(1))
    if mean < min_mean_db:
        raise AudioError(f"volumen medio {mean} dB demasiado bajo (silencio): {p}")
    return {"duration": dur, "mean_db": mean, "max_db": float(mx.group(1)) if mx else None,
            "codec": streams[0].get("codec_name")}
