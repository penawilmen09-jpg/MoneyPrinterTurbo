"""Audio: narración TTS gratuita/local, efectos sintetizados, música procedural y mezcla."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
import logging
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import wave

import numpy as np

log = logging.getLogger("animated_explainer.audio")
SR = 44100


def ffmpeg_bin() -> str:
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:  # imageio-ffmpeg es dependencia del proyecto
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as e:  # pragma: no cover
        raise RuntimeError("FFmpeg no encontrado: instálalo o `pip install imageio-ffmpeg`") from e


def decode_audio(path: str | Path, sr: int = SR) -> np.ndarray:
    """Decodifica cualquier audio a mono float32 usando FFmpeg."""
    cmd = [ffmpeg_bin(), "-v", "error", "-i", str(path), "-f", "f32le", "-ac", "1",
           "-ar", str(sr), "-"]
    res = subprocess.run(cmd, capture_output=True)
    if res.returncode != 0:
        raise RuntimeError(f"FFmpeg no pudo decodificar {path}: {res.stderr.decode(errors='ignore')[:300]}")
    return np.frombuffer(res.stdout, dtype=np.float32).copy()


def write_wav(path: str | Path, data: np.ndarray, sr: int = SR) -> None:
    x = np.clip(data, -1.0, 1.0)
    pcm = (x * 32767).astype("<i2")
    ch = 1 if pcm.ndim == 1 else pcm.shape[1]
    with wave.open(str(path), "wb") as w:
        w.setnchannels(ch)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


# ================================================================== narración
@dataclass
class Speech:
    pcm: np.ndarray                      # mono float32 @SR
    words: list[tuple[str, float, float]]  # (palabra, inicio, fin) en segundos
    provider: str
    duration: float = 0.0

    def __post_init__(self):
        self.duration = len(self.pcm) / SR


def _trim(pcm: np.ndarray, keep: float = 0.06, thr: float = 0.012) -> tuple[np.ndarray, float]:
    """Recorta silencio inicial/final. Devuelve (pcm, segundos recortados al inicio)."""
    if len(pcm) == 0:
        return pcm, 0.0
    env = np.abs(pcm)
    k = int(SR * 0.01)
    env = np.convolve(env, np.ones(k) / k, mode="same")
    idx = np.where(env > thr)[0]
    if len(idx) == 0:
        return pcm, 0.0
    a = max(0, idx[0] - int(keep * SR))
    b = min(len(pcm), idx[-1] + int(keep * SR))
    return pcm[a:b], a / SR


def estimate_words(text: str, duration: float) -> list[tuple[str, float, float]]:
    """Reparte la duración entre palabras según su longitud y la puntuación."""
    toks = text.split()
    if not toks:
        return []
    weights = []
    for t in toks:
        w = len(re.sub(r"\W", "", t)) + 2.0
        if t.endswith((",", ";", ":")):
            w += 2.5
        elif t.endswith((".", "!", "?", "…")):
            w += 5.0
        weights.append(w)
    total = sum(weights)
    out, cur = [], 0.0
    for t, w in zip(toks, weights):
        d = duration * w / total
        out.append((t, cur, cur + d))
        cur += d
    return out


async def _edge_stream(text, voice, rate, pitch):
    import edge_tts
    comm = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch,
                                boundary="WordBoundary", connect_timeout=10, receive_timeout=45)
    audio, words = bytearray(), []
    async for chunk in comm.stream():
        if chunk["type"] == "audio":
            audio.extend(chunk["data"])
        elif chunk["type"] == "WordBoundary":
            st = chunk["offset"] / 1e7
            words.append((chunk["text"], st, st + chunk["duration"] / 1e7))
    return bytes(audio), words


def _tts_edge(text, voice, rate, pitch) -> Speech:
    last = None
    for attempt in range(3):
        try:
            data, words = asyncio.run(_edge_stream(text, voice, rate, pitch))
            if not data:
                raise RuntimeError("Edge-TTS devolvió audio vacío")
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                f.write(data)
                name = f.name
            try:
                pcm = decode_audio(name)
            finally:
                os.unlink(name)
            pcm, off = _trim(pcm)
            words = [(w, max(0.0, a - off), max(0.0, b - off)) for w, a, b in words]
            if not words:
                words = estimate_words(text, len(pcm) / SR)
            return Speech(pcm, words, "edge-tts")
        except Exception as e:  # red caída, DNS bloqueado, etc.
            last = e
            log.warning("Edge-TTS intento %d falló: %s", attempt + 1, e)
    raise RuntimeError(f"Edge-TTS no disponible: {last}")


def _tts_piper(text, rate) -> Speech:
    model = os.environ.get("PIPER_MODEL")
    exe = shutil.which("piper")
    if not (model and exe and Path(model).exists()):
        raise RuntimeError("Piper no configurado (define PIPER_MODEL=ruta/es_MX-*.onnx y ten `piper` en PATH)")
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "o.wav"
        subprocess.run([exe, "--model", model, "--output_file", str(out)],
                       input=text.encode(), check=True, capture_output=True, timeout=120)
        pcm = decode_audio(out)
    pcm, _ = _trim(pcm)
    return Speech(pcm, estimate_words(text, len(pcm) / SR), "piper")


def _tts_espeak(text, voice="es-419") -> Speech:
    exe = shutil.which("espeak-ng") or shutil.which("espeak")
    if not exe:
        raise RuntimeError("espeak-ng no instalado")
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "o.wav"
        subprocess.run([exe, "-v", "es-419+m3", "-s", "150", "-w", str(out), text],
                       check=True, capture_output=True, timeout=60)
        pcm = decode_audio(out)
    pcm, _ = _trim(pcm)
    return Speech(pcm, estimate_words(text, len(pcm) / SR), "espeak-ng")


def _tts_silent(text, wpm: float = 165.0) -> Speech:
    """Último recurso: pista muda con la duración estimada (los subtítulos siguen funcionando)."""
    n = max(1, len(text.split()))
    dur = n / wpm * 60 + 0.4
    return Speech(np.zeros(int(dur * SR), np.float32), estimate_words(text, dur), "silent")


def synthesize(text: str, *, voice: str = "es-MX-JorgeNeural", rate: str = "+0%",
               pitch: str = "+0Hz", provider: str = "auto") -> Speech:
    """Genera la narración. ``provider``: auto | edge | piper | espeak | silent."""
    order = {"auto": ["edge", "piper", "espeak", "silent"], "edge": ["edge"],
             "piper": ["piper"], "espeak": ["espeak"], "silent": ["silent"]}.get(provider)
    if order is None:
        raise ValueError(f"Proveedor TTS desconocido: {provider}")
    errors = []
    for p in order:
        try:
            if p == "edge":
                sp = _tts_edge(text, voice, rate, pitch)
            elif p == "piper":
                sp = _tts_piper(text, rate)
            elif p == "espeak":
                sp = _tts_espeak(text)
            else:
                sp = _tts_silent(text)
            if p == "silent" and provider == "auto":
                log.warning("Sin TTS disponible (%s). El video llevará narración MUDA; "
                            "instala/permite Edge-TTS, Piper o espeak-ng.", "; ".join(errors))
            peak = float(np.max(np.abs(sp.pcm))) if len(sp.pcm) else 0.0
            if peak > 0:
                sp.pcm = sp.pcm * (0.7 / peak)
            return sp
        except Exception as e:
            errors.append(f"{p}: {e}")
            log.info("TTS %s no disponible: %s", p, e)
    raise RuntimeError("Ningún motor TTS funcionó: " + " | ".join(errors))


def envelope(pcm: np.ndarray, fps: float) -> np.ndarray:
    """Energía por fotograma normalizada 0..1 (para sincronizar la boca)."""
    hop = SR / fps
    n = int(len(pcm) / hop) + 1
    if len(pcm) == 0:
        return np.zeros(n, np.float32)
    pad = np.pad(pcm, (0, int(hop * n) + 1 - len(pcm)))
    rms = np.array([np.sqrt(np.mean(pad[int(i * hop): int((i + 1) * hop)] ** 2)) for i in range(n)])
    ref = np.percentile(rms, 95) + 1e-6
    env = np.clip(rms / ref, 0, 1) ** 0.7
    # suavizado
    k = np.array([0.25, 0.5, 0.25])
    return np.convolve(env, k, mode="same").astype(np.float32)


# ================================================================== efectos
def _t(d: float) -> np.ndarray:
    return np.arange(int(d * SR), dtype=np.float32) / SR


def _env_ad(n: int, a: float = 0.005, decay: float = 5.0) -> np.ndarray:
    t = np.arange(n, dtype=np.float32) / SR
    return np.minimum(1.0, t / max(a, 1e-4)) * np.exp(-decay * t)


def _lowpass(x: np.ndarray, cutoff: float) -> np.ndarray:
    a = math.exp(-2 * math.pi * cutoff / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):  # n pequeño (<1 s)
        acc = (1 - a) * x[i] + a * acc
        y[i] = acc
    return y


_RNG = np.random.RandomState(7)


def sfx_whoosh(dur=0.55):
    t = _t(dur)
    noise = _RNG.randn(len(t)).astype(np.float32)
    sweep = np.sin(np.pi * t / dur) ** 2
    x = _lowpass(noise, 1800) * sweep
    return (x / (np.max(np.abs(x)) + 1e-6) * 0.6).astype(np.float32)


def sfx_ding(dur=1.1):
    t = _t(dur)
    x = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-d * t)
            for f, a, d in ((1318.5, 1.0, 4.0), (2637, 0.4, 6.0), (3951, 0.2, 9.0)))
    return (x * 0.35).astype(np.float32)


def sfx_pop(dur=0.18):
    t = _t(dur)
    f = 500 + 900 * np.exp(-t * 35)
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 28) * 0.6).astype(np.float32)


def sfx_thud(dur=0.35):
    t = _t(dur)
    f = 110 * np.exp(-t * 6) + 45
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 11)
    return (x * 0.9).astype(np.float32)


def sfx_door(dur=0.9):
    t = _t(dur)
    creak = np.sin(2 * np.pi * np.cumsum(300 + 120 * np.sin(2 * np.pi * 5 * t) + 100 * t) / SR)
    creak *= np.sin(np.pi * np.clip(t / 0.6, 0, 1)) * 0.25
    click = np.zeros_like(t)
    c0 = int(0.62 * SR)
    seg = _RNG.randn(int(0.05 * SR)).astype(np.float32) * np.exp(-np.arange(int(0.05 * SR)) / (0.01 * SR))
    click[c0:c0 + len(seg)] += seg * 0.7
    return (creak + click + np.pad(sfx_thud(0.3)[: len(t) - c0], (c0, 0))[: len(t)] * 0.3).astype(np.float32)


def sfx_steps(dur=1.6, bpm=210):
    out = np.zeros(int(dur * SR), np.float32)
    step = int(60 / bpm * SR)
    th = sfx_thud(0.12) * 0.55
    for i, s in enumerate(range(0, len(out) - len(th), step)):
        out[s:s + len(th)] += th * (1.0 if i % 2 == 0 else 0.8)
    return out


def sfx_tick(dur=1.8):
    out = np.zeros(int(dur * SR), np.float32)
    n = int(0.03 * SR)
    for i, s in enumerate(range(0, len(out) - n, int(0.5 * SR))):
        tt = np.arange(n) / SR
        out[s:s + n] += np.sin(2 * np.pi * (1900 if i % 2 == 0 else 1500) * tt) * np.exp(-tt * 140) * 0.5
    return out


def sfx_sting(dur=1.4):
    t = _t(dur)
    x = sum(np.sin(2 * np.pi * f * t) * np.exp(-2.4 * t) * a
            for f, a in ((220, 0.6), (311.1, 0.5), (466.2, 0.4), (110, 0.7)))
    return (x * 0.35).astype(np.float32)


def sfx_cash(dur=0.9):
    t = _t(dur)
    a = np.sin(2 * np.pi * 1760 * t) * np.exp(-7 * t)
    b = np.where(t > 0.09, np.sin(2 * np.pi * 2349 * np.clip(t - 0.09, 0, None)) *
                 np.exp(-6 * np.clip(t - 0.09, 0, None)), 0)
    return ((a + b) * 0.35).astype(np.float32)


def sfx_sparkle(dur=0.9):
    t = _t(dur)
    x = np.zeros_like(t)
    for i, f in enumerate((2093, 2637, 3136, 4186)):
        s = int(i * 0.07 * SR)
        seg = np.sin(2 * np.pi * f * t[: len(t) - s]) * np.exp(-9 * t[: len(t) - s])
        x[s:] += seg * 0.18
    return x.astype(np.float32)


def sfx_swipe(dur=0.3):
    return sfx_whoosh(dur) * 0.7


def sfx_drip(dur=0.3):
    t = _t(dur)
    f = 1400 - 900 * t / dur
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 22) * 0.5).astype(np.float32)


def sfx_click(dur=0.08):
    t = _t(dur)
    return (_RNG.randn(len(t)).astype(np.float32) * np.exp(-t * 90) * 0.5)


def sfx_tension(dur=2.0):
    t = _t(dur)
    f = 90 + 40 * t / dur
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * (t / dur) * np.exp(-0.2 * t) * 0.45
    return x.astype(np.float32)


SFX = {
    "whoosh": sfx_whoosh, "ding": sfx_ding, "pop": sfx_pop, "thud": sfx_thud, "door": sfx_door,
    "steps": sfx_steps, "tick": sfx_tick, "sting": sfx_sting, "cash": sfx_cash,
    "sparkle": sfx_sparkle, "swipe": sfx_swipe, "drip": sfx_drip, "click": sfx_click,
    "tension": sfx_tension,
}
_SFX_CACHE: dict[str, np.ndarray] = {}


def get_sfx(name: str) -> np.ndarray:
    if name not in SFX:
        raise KeyError(f"Efecto desconocido {name!r}. Disponibles: {', '.join(sorted(SFX))}")
    if name not in _SFX_CACHE:
        x = SFX[name]()
        peak = float(np.max(np.abs(x))) + 1e-6
        _SFX_CACHE[name] = (x * (0.9 / peak) if peak > 0.9 else x).astype(np.float32)
    return _SFX_CACHE[name]


# ================================================================== música
MOODS = {
    "upbeat": dict(bpm=112, prog=[(57, "m"), (53, "M"), (48, "M"), (55, "M")], hat=True, level=1.0),
    "tense": dict(bpm=92, prog=[(57, "m"), (52, "m"), (53, "M"), (52, "M")], hat=False, level=0.9),
    "calm": dict(bpm=84, prog=[(48, "M"), (55, "M"), (57, "m"), (53, "M")], hat=False, level=0.85),
}


def _mtof(m: float) -> float:
    return 440.0 * 2 ** ((m - 69) / 12)


def _add(buf, start, sig, gain=1.0):
    s = int(start * SR)
    if s >= len(buf):
        return
    e = min(len(buf), s + len(sig))
    buf[s:e] += sig[: e - s] * gain


def _note(freq, dur, kind="pluck"):
    t = _t(dur)
    if kind == "pad":
        x = sum(np.sin(2 * np.pi * freq * (1 + d) * t) for d in (-0.003, 0.0, 0.003))
        env = np.minimum(1, t / 0.25) * np.minimum(1, (dur - t) / 0.35)
        return (x / 3 * env).astype(np.float32)
    if kind == "bass":
        x = np.sin(2 * np.pi * freq * t) + 0.3 * np.sin(2 * np.pi * 2 * freq * t)
        return (x * _env_ad(len(t), 0.01, 3.5)).astype(np.float32)
    x = np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(2 * np.pi * 2 * freq * t) \
        + 0.12 * np.sin(2 * np.pi * 3 * freq * t)
    return (x * _env_ad(len(t), 0.004, 7.0)).astype(np.float32)


def make_music(duration: float, mood: str = "upbeat", seed: int = 3) -> np.ndarray:
    """Pista instrumental discreta (pad + bajo + arpegio + hi-hat suave). Mono float32."""
    cfg = MOODS.get(mood, MOODS["upbeat"])
    rng = np.random.RandomState(seed)
    beat = 60.0 / cfg["bpm"]
    bar = beat * 4
    buf = np.zeros(int((duration + 2.5) * SR), np.float32)
    nbars = int(duration / bar) + 2
    for b in range(nbars):
        root, q = cfg["prog"][b % len(cfg["prog"])]
        third = 3 if q == "m" else 4
        chord = [root + 12, root + 12 + third, root + 19]
        t0 = b * bar
        for n in chord:
            _add(buf, t0, _note(_mtof(n), bar + 0.15, "pad"), 0.10)
        _add(buf, t0, _note(_mtof(root - 12), beat * 1.9, "bass"), 0.35)
        _add(buf, t0 + beat * 2, _note(_mtof(root - 12), beat * 1.9, "bass"), 0.28)
        arp = [chord[0] + 12, chord[1] + 12, chord[2] + 12, chord[1] + 12,
               chord[0] + 24, chord[2] + 12, chord[1] + 12, chord[0] + 12]
        for i, n in enumerate(arp):
            if cfg["hat"] or i % 2 == 0:
                _add(buf, t0 + i * beat / 2, _note(_mtof(n), 0.5), 0.10 * (1.0 if i % 2 == 0 else 0.7))
        # bombo suave y hi-hat
        kick = np.sin(2 * np.pi * np.cumsum(120 * np.exp(-_t(0.2) * 18) + 45) / SR) * np.exp(-_t(0.2) * 16)
        for i in (0, 2):
            _add(buf, t0 + i * beat, kick.astype(np.float32), 0.30)
        if cfg["hat"]:
            for i in range(8):
                hat = rng.randn(int(0.04 * SR)).astype(np.float32) * np.exp(-np.arange(int(0.04 * SR)) / (0.008 * SR))
                _add(buf, t0 + i * beat / 2 + beat / 4, hat, 0.05)
    buf = buf[: int(duration * SR)]
    fade_in, fade_out = int(1.2 * SR), int(2.0 * SR)
    buf[:fade_in] *= np.linspace(0, 1, fade_in)
    buf[-fade_out:] *= np.linspace(1, 0, fade_out)
    peak = np.max(np.abs(buf)) + 1e-6
    return (buf / peak * 0.8 * cfg["level"]).astype(np.float32)


def load_music(spec: str, duration: float) -> np.ndarray:
    """``builtin:<mood>`` | ruta a un archivo | ``none``."""
    if not spec or spec == "none":
        return np.zeros(int(duration * SR), np.float32)
    if spec.startswith("builtin:"):
        return make_music(duration, spec.split(":", 1)[1])
    p = Path(spec)
    if not p.exists():
        raise FileNotFoundError(f"Música no encontrada: {spec}")
    pcm = decode_audio(p)
    if len(pcm) < duration * SR:
        pcm = np.tile(pcm, int(duration * SR / max(len(pcm), 1)) + 1)
    pcm = pcm[: int(duration * SR)].copy()
    f = int(1.5 * SR)
    pcm[:f] *= np.linspace(0, 1, f)
    pcm[-f:] *= np.linspace(1, 0, f)
    return pcm * (0.8 / (np.max(np.abs(pcm)) + 1e-6))


# ================================================================== mezcla
def mix(total: float, speech: list[tuple[float, np.ndarray]],
        sfx: list[tuple[float, np.ndarray, float, float]], music: np.ndarray,
        music_gain: float = 0.22, duck: float = 0.65) -> np.ndarray:
    """Mezcla estéreo (N,2). sfx: (inicio, pcm, ganancia, pan -1..1). Música con *ducking*."""
    n = int(total * SR)
    voice = np.zeros(n, np.float32)
    for st, pcm in speech:
        _add(voice, st, pcm, 1.0)
    # envolvente de la voz para el ducking (ventanas de 20 ms, suavizada)
    win = int(0.02 * SR)
    m = len(voice) // win
    e = np.abs(voice[: m * win]).reshape(m, win).mean(axis=1)
    e = np.clip(e / 0.12, 0, 1)
    k = np.ones(15) / 15
    e = np.convolve(np.pad(e, (7, 7), mode="edge"), k, mode="valid")
    gain_curve = np.interp(np.arange(n), (np.arange(len(e)) + 0.5) * win, 1.0 - duck * e)
    mus = np.zeros(n, np.float32)
    mus[: min(n, len(music))] = music[:n]
    mus = mus * gain_curve * music_gain
    left = voice * 0.95 + mus
    right = voice * 0.95 + mus
    d = int(0.012 * SR)  # ensanche estéreo de la música
    right[d:] += mus[:-d] * 0.25
    left[:-d] += mus[d:] * 0.25
    for st, pcm, g, pan in sfx:
        pl, pr = math.cos((pan + 1) * math.pi / 4), math.sin((pan + 1) * math.pi / 4)
        s = int(st * SR)
        if s >= n:
            continue
        e_ = min(n, s + len(pcm))
        left[s:e_] += pcm[: e_ - s] * g * pl * 1.2
        right[s:e_] += pcm[: e_ - s] * g * pr * 1.2
    out = np.stack([left, right], axis=1)
    peak = np.max(np.abs(out)) + 1e-6
    if peak > 0.95:
        out = out * (0.95 / peak)
    return out
