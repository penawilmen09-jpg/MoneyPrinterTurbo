"""Audio del modo storytelling: análisis de voz, efectos sintéticos y mezcla."""

from __future__ import annotations

import glob
import os
import random
import subprocess

import numpy as np

SR = 44100
ENV_HZ = 50


def decode_mono(path: str, sr: int = SR) -> np.ndarray:
    """Decodifica cualquier audio a float32 mono."""
    out = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
        check=True, capture_output=True,
    ).stdout
    return np.frombuffer(out, dtype=np.float32).copy()


def write_wav(path: str, data: np.ndarray, sr: int = SR) -> None:
    import wave

    pcm = (np.clip(data, -1, 1) * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def speech_bounds(x: np.ndarray, sr: int = SR, thresh_db: float = -42.0) -> tuple[float, float]:
    """(inicio, fin) en segundos de la voz, recortando silencios."""
    if len(x) == 0:
        return 0.0, 0.0
    hop = int(sr * 0.01)
    n = len(x) // hop
    rms = np.sqrt((x[: n * hop].reshape(n, hop) ** 2).mean(axis=1) + 1e-12)
    db = 20 * np.log10(rms + 1e-9)
    ref = max(db.max(), -20.0)
    active = np.where(db > min(thresh_db, ref - 30))[0]
    if len(active) == 0:
        return 0.0, len(x) / sr
    return max(0.0, active[0] * 0.01 - 0.03), min(len(x) / sr, (active[-1] + 1) * 0.01 + 0.05)


def envelope(x: np.ndarray, start: float, end: float, sr: int = SR, hz: int = ENV_HZ) -> list[float]:
    """Energía de voz normalizada 0..1 muestreada a ``hz`` entre start y end."""
    seg = x[int(start * sr): int(end * sr)]
    hop = sr // hz
    n = len(seg) // hop
    if n <= 0:
        return []
    rms = np.sqrt((seg[: n * hop].reshape(n, hop) ** 2).mean(axis=1))
    peak = np.percentile(rms, 95) + 1e-6
    env = np.clip(rms / peak, 0, 1) ** 0.7
    # suavizado corto
    k = np.array([0.25, 0.5, 0.25])
    env = np.convolve(env, k, mode="same")
    return [round(float(v), 3) for v in env]


# ------------------------------------------------------------------ SFX sintéticos
def _fade(x, a=0.005, b=0.03, sr=SR):
    n1, n2 = int(a * sr), int(b * sr)
    x = x.copy()
    if n1:
        x[:n1] *= np.linspace(0, 1, n1)
    if n2:
        x[-n2:] *= np.linspace(1, 0, n2)
    return x


def synth_sfx(name: str, sr: int = SR) -> np.ndarray:
    rng = np.random.default_rng(7)
    t = lambda d: np.linspace(0, d, int(d * sr), endpoint=False)
    if name == "whoosh":
        d = 0.55
        tt = t(d)
        noise = rng.standard_normal(len(tt))
        # filtro paso-banda simple barriendo (suma de medias móviles)
        env = np.sin(np.pi * tt / d) ** 2
        w = np.convolve(noise, np.ones(40) / 40, mode="same") - np.convolve(noise, np.ones(400) / 400, mode="same")
        return _fade(w * env * 0.9, 0.02, 0.2)
    if name in ("ding", "beep"):
        f = 1318.5 if name == "ding" else 880.0
        d = 0.5 if name == "ding" else 0.28
        tt = t(d)
        y = np.sin(2 * np.pi * f * tt) + 0.4 * np.sin(2 * np.pi * f * 2 * tt)
        return _fade(y * np.exp(-tt * (7 if name == "ding" else 12)) * 0.6, 0.003, 0.05)
    if name == "alert":
        tt = t(0.6)
        y = np.sin(2 * np.pi * (600 + 200 * (np.sin(2 * np.pi * 4 * tt) > 0)) * tt) * 0.35
        return _fade(y * np.exp(-tt * 3), 0.01, 0.1)
    if name == "pop":
        tt = t(0.12)
        return _fade(np.sin(2 * np.pi * (500 + 1500 * np.exp(-tt * 40)) * tt) * np.exp(-tt * 25), 0.001, 0.02)
    if name == "cash":
        tt = t(0.7)
        y = np.zeros_like(tt)
        for k, f in enumerate((2093, 2637, 3136)):
            m = tt > k * 0.07
            y[m] += np.sin(2 * np.pi * f * (tt[m] - k * 0.07)) * np.exp(-(tt[m] - k * 0.07) * 9)
        return _fade(y * 0.35, 0.002, 0.1)
    if name == "suspense":
        tt = t(1.4)
        y = np.sin(2 * np.pi * 55 * tt) * 0.5 + np.sin(2 * np.pi * 58.5 * tt) * 0.4
        return _fade(y * (np.sin(np.pi * tt / 1.4) ** 2) * 0.6, 0.1, 0.4)
    if name in ("typing", "click"):
        n = 5 if name == "typing" else 1
        out = np.zeros(int(0.7 * sr))
        for k in range(n):
            s = int(k * 0.11 * sr)
            tt = t(0.02)
            out[s: s + len(tt)] += rng.standard_normal(len(tt)) * np.exp(-tt * 300) * 0.5
        return out
    return np.zeros(int(0.1 * sr))


# Prioridad y nivel (dB respecto a la voz) de cada efecto; nunca compiten con la narración
SFX_GAIN_DB = {"whoosh": -20, "ding": -19, "beep": -20, "alert": -22, "pop": -20, "cash": -20,
               "suspense": -24, "typing": -24, "click": -22}


def plan_sfx(scenes: list[dict], max_total: int = 6, min_gap: float = 4.0) -> list[dict]:
    """Elige efectos con reglas anti-saturación.

    ``scenes``: [{"start": s, "lead": s, "sfx": nombre, "label": str}]
    Reglas: máximo ``max_total`` efectos, separación mínima ``min_gap`` s, nunca el
    mismo efecto dos veces seguidas, y siempre en el hueco previo a la frase (no durante).
    """
    events, last_t, last_name = [], -99.0, ""
    for sc in scenes:
        name = sc.get("sfx") or ""
        if not name or len(events) >= max_total or sc["start"] <= 0:
            continue  # el gancho inicial se oye limpio: sin efectos en la primera escena
        # el efecto cae en la transición (antes de que empiece a hablar el narrador)
        t = max(0.0, sc["start"] + max(0.0, sc.get("lead", 0.12)) - 0.35)
        if t - last_t < min_gap or name == last_name:
            continue
        events.append({"name": name, "time": round(t, 2), "gain_db": SFX_GAIN_DB.get(name, -22)})
        last_t, last_name = t, name
    return events


def build_sfx_track(events: list[dict], total: float, sr: int = SR) -> np.ndarray:
    track = np.zeros(int((total + 1) * sr), dtype=np.float32)
    for ev in events:
        s = synth_sfx(ev["name"])
        s = s / (np.abs(s).max() + 1e-9) * (10 ** (ev["gain_db"] / 20.0 + 0.5))
        i = int(ev["time"] * sr)
        track[i: i + len(s)] += s[: len(track) - i]
    return track


def pick_music(songs_dir: str, seed: int = 0) -> str | None:
    files = sorted(glob.glob(os.path.join(songs_dir, "*.mp3")))
    if not files:
        return None
    return files[random.Random(seed).randrange(len(files))]


def mix_audio(narration_wav: str, sfx_wav: str, music: str | None, total: float, out_path: str,
              music_db: float = -23.0) -> None:
    """Mezcla: voz normalizada + música con ducking + SFX con ducking + loudnorm final."""
    inputs = ["-i", narration_wav, "-i", sfx_wav]
    if music:
        inputs += ["-stream_loop", "-1", "-i", music]
    voice = "[0:a]loudnorm=I=-16:TP=-2:LRA=7,asplit=3[v1][v2][v3]" if music else "[0:a]loudnorm=I=-16:TP=-2:LRA=7,asplit=2[v1][v2]"
    sfx = f"[1:a]volume=0.8[s0];[s0][v2]sidechaincompress=threshold=0.02:ratio=12:attack=5:release=250[s]"
    parts = [voice, sfx]
    mix_in = "[v1][s]"
    n = 2
    if music:
        parts.append(
            f"[2:a]atrim=0:{total + 1:.2f},asetpts=PTS-STARTPTS,volume={music_db}dB,afade=t=in:d=1.5,"
            f"afade=t=out:st={max(0.0, total - 2.0):.2f}:d=2.0[m0];"
            "[m0][v3]sidechaincompress=threshold=0.015:ratio=14:attack=15:release=450:makeup=1[m]"
        )
        mix_in += "[m]"
        n = 3
    parts.append(f"{mix_in}amix=inputs={n}:normalize=0:duration=first,alimiter=limit=0.89,"
                 f"loudnorm=I=-14:TP=-1.5:LRA=9,atrim=0:{total:.3f}[out]")
    cmd = ["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", ";".join(parts), "-map", "[out]",
           "-ar", "48000", "-ac", "2", out_path]
    subprocess.run(cmd, check=True)
