"""Narración masculina en español latino con comprobación previa del motor TTS.

Orden de motores (nunca se continúa en silencio; si ninguno funciona se lanza
``TTSUnavailableError``):

1. Edge-TTS (``es-MX-JorgeNeural``), el motor nativo de MoneyPrinterTurbo.
2. Kokoro-ONNX (Apache-2.0, gratis, 100 % local, voz masculina ``em_alex``).
"""
from __future__ import annotations

import asyncio
import json
import os
import subprocess
import urllib.request
import wave
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

SR = 44100
EDGE_VOICE = "es-MX-JorgeNeural"
KOKORO_VOICE = "em_alex"
KOKORO_BASE = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0"
KOKORO_FILES = ("kokoro-v1.0.onnx", "voices-v1.0.bin")


class TTSUnavailableError(RuntimeError):
    pass


# --------------------------------------------------------------------------
# Preflight
# --------------------------------------------------------------------------
def check_edge_tts(timeout: float = 15.0) -> tuple[bool, str]:
    try:
        import edge_tts
    except Exception as exc:  # módulo no instalado
        return False, f"edge_tts no importable: {exc}"

    async def probe() -> int:
        com = edge_tts.Communicate("Prueba de voz.", EDGE_VOICE)
        n = 0
        async for chunk in com.stream():
            if chunk["type"] == "audio":
                n += len(chunk["data"])
        return n

    try:
        n = asyncio.run(asyncio.wait_for(probe(), timeout))
        return (n > 1000), f"edge-tts devolvió {n} bytes"
    except Exception as exc:
        return False, f"{type(exc).__name__}: {str(exc)[:160]}"


def ensure_kokoro_models(model_dir: Path) -> tuple[Path, Path]:
    model_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for name in KOKORO_FILES:
        dest = model_dir / name
        if not dest.exists() or dest.stat().st_size < 1_000_000:
            tmp = dest.with_suffix(dest.suffix + ".part")
            with urllib.request.urlopen(f"{KOKORO_BASE}/{name}", timeout=120) as r, open(tmp, "wb") as f:
                while chunk := r.read(1 << 20):
                    f.write(chunk)
            tmp.replace(dest)
        paths.append(dest)
    return paths[0], paths[1]


def check_kokoro(model_dir: Path) -> tuple[bool, str]:
    try:
        import kokoro_onnx  # noqa: F401
        import soundfile  # noqa: F401
        ensure_kokoro_models(model_dir)
        return True, "kokoro-onnx + modelos disponibles"
    except Exception as exc:
        return False, f"{type(exc).__name__}: {str(exc)[:160]}"


def select_engine(model_dir: Path, log=print, prefer: str | None = None) -> str:
    """Devuelve 'edge' o 'kokoro'. Lanza TTSUnavailableError si no hay ninguno."""
    report = {}
    if prefer != "kokoro":
        ok, msg = check_edge_tts()
        report["edge"] = msg
        log(f"[TTS] Edge-TTS: {'OK' if ok else 'NO DISPONIBLE'} ({msg})")
        if ok:
            return "edge"
    ok, msg = check_kokoro(model_dir)
    report["kokoro"] = msg
    log(f"[TTS] Kokoro (alternativa gratuita local): {'OK' if ok else 'NO DISPONIBLE'} ({msg})")
    if ok:
        return "kokoro"
    raise TTSUnavailableError(f"Ningún motor TTS disponible: {json.dumps(report, ensure_ascii=False)}")


# --------------------------------------------------------------------------
# Síntesis por cláusula
# --------------------------------------------------------------------------
def _ffmpeg_to_pcm(data: bytes, ffmpeg: str = "ffmpeg") -> np.ndarray:
    p = subprocess.run(
        [ffmpeg, "-v", "error", "-i", "pipe:0", "-f", "f32le", "-ac", "1", "-ar", str(SR), "pipe:1"],
        input=data, stdout=subprocess.PIPE, check=True,
    )
    return np.frombuffer(p.stdout, dtype=np.float32).copy()


class Synth:
    def __init__(self, engine: str, model_dir: Path, speed: float = 0.9):
        self.engine, self.speed = engine, speed
        self._k = None
        if engine == "kokoro":
            from kokoro_onnx import Kokoro
            m, v = ensure_kokoro_models(model_dir)
            self._k = Kokoro(str(m), str(v))

    def say(self, text: str) -> np.ndarray:
        if self.engine == "edge":
            import edge_tts

            async def run() -> bytes:
                rate = f"{int((self.speed - 1) * 100):+d}%"
                com = edge_tts.Communicate(text, EDGE_VOICE, rate=rate, pitch="-12Hz")
                buf = b""
                async for ch in com.stream():
                    if ch["type"] == "audio":
                        buf += ch["data"]
                return buf

            return _ffmpeg_to_pcm(asyncio.run(run()))
        samples, sr = self._k.create(text, voice=KOKORO_VOICE, speed=self.speed, lang="es")
        samples = np.asarray(samples, dtype=np.float32)
        return _resample(samples, sr, SR)


def _resample(x: np.ndarray, sr_in: int, sr_out: int) -> np.ndarray:
    if sr_in == sr_out:
        return x
    n_out = int(round(len(x) * sr_out / sr_in))
    return np.interp(np.linspace(0, len(x) - 1, n_out), np.arange(len(x)), x).astype(np.float32)


def _trim(x: np.ndarray, thr: float = 0.01, keep: float = 0.03) -> np.ndarray:
    idx = np.where(np.abs(x) > thr)[0]
    if len(idx) == 0:
        return x
    a = max(0, idx[0] - int(keep * SR))
    b = min(len(x), idx[-1] + int(keep * SR))
    return x[a:b]


def _fade(x: np.ndarray, ms: float = 12.0) -> np.ndarray:
    n = int(SR * ms / 1000)
    x = x.copy()
    x[:n] *= np.linspace(0, 1, n)
    x[-n:] *= np.linspace(1, 0, n)
    return x


@dataclass
class Clause:
    scene: int
    text: str
    start: float = 0.0
    end: float = 0.0


@dataclass
class Narration:
    voice: np.ndarray                      # mono SR
    clauses: list[Clause]
    scene_starts: list[float]
    scene_ends: list[float]
    engine: str
    total: float = 0.0


def build_narration(scenes: list[dict], engine: str, model_dir: Path, *, lead: float = 0.55,
                    tail: float = 0.75, speed: float = 0.9, min_scene: float = 10.0, log=print) -> Narration:
    synth = Synth(engine, model_dir, speed=speed)
    chunks: list[np.ndarray] = []
    clauses: list[Clause] = []
    scene_starts, scene_ends = [], []
    t = 0.0

    def push(x: np.ndarray):
        nonlocal t
        chunks.append(x)
        t += len(x) / SR

    for si, sc in enumerate(scenes):
        scene_starts.append(t)
        push(np.zeros(int(lead * SR), np.float32))
        for text, pause in sc["clauses"]:
            wav = _fade(_trim(synth.say(text)))
            c = Clause(si, text, start=t, end=t + len(wav) / SR)
            push(wav)
            clauses.append(c)
            log(f"[TTS] escena {si+1}: {c.start:6.2f}-{c.end:6.2f}  {text}")
            if pause:
                push(np.zeros(int(pause * SR), np.float32))
        push(np.zeros(int(tail * SR), np.float32))
        if t - scene_starts[-1] < min_scene:
            push(np.zeros(int((min_scene - (t - scene_starts[-1])) * SR), np.float32))
        scene_ends.append(t)
    voice = np.concatenate(chunks)
    return Narration(voice, clauses, scene_starts, scene_ends, engine, total=len(voice) / SR)


def shape_voice(x: np.ndarray, ffmpeg: str = "ffmpeg", deepen: float = 0.95) -> np.ndarray:
    """Hace la voz más grave/documental (tono -5 %, graves y compresión suaves)."""
    flt = (f"asetrate={SR*deepen:.0f},aresample={SR},atempo={1/deepen:.5f},"
           "equalizer=f=140:t=q:w=1.0:g=3,equalizer=f=3200:t=q:w=1.2:g=1.5,"
           "acompressor=threshold=-20dB:ratio=2.5:attack=8:release=120:makeup=2,"
           "alimiter=limit=0.89")
    p = subprocess.run(
        [ffmpeg, "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "pipe:0",
         "-af", flt, "-f", "f32le", "-ac", "1", "-ar", str(SR), "pipe:1"],
        input=x.astype(np.float32).tobytes(), stdout=subprocess.PIPE, check=True)
    return np.frombuffer(p.stdout, dtype=np.float32).copy()


def write_wav(path: Path, x: np.ndarray, sr: int = SR, channels: int = 1) -> None:
    pcm = (np.clip(x, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


# --------------------------------------------------------------------------
# Subtítulos: una sola línea por cue
# --------------------------------------------------------------------------
def _fmt(t: float) -> str:
    ms = int(round(t * 1000))
    h, r = divmod(ms, 3_600_000)
    m, r = divmod(r, 60_000)
    s, ms = divmod(r, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def split_lines(text: str, max_chars: int = 26) -> list[str]:
    """Menor número de líneas de <= max_chars, lo más equilibradas posible."""
    from itertools import combinations
    words = text.split()
    for n in range(1, len(words) + 1):
        best = None
        for cuts in combinations(range(1, len(words)), n - 1):
            idx = (0, *cuts, len(words))
            lines = [" ".join(words[idx[i]:idx[i + 1]]) for i in range(n)]
            m = max(len(l) for l in lines)
            if m <= max_chars and (best is None or m < best[0]):
                best = (m, lines)
        if best:
            return best[1]
    return [text]


def build_srt(clauses: list[Clause], voice_shift: float = 0.0) -> list[tuple[float, float, str]]:
    cues = []
    for c in clauses:
        lines = split_lines(c.text)
        weights = np.array([len(l) for l in lines], dtype=float)
        bounds = np.concatenate([[0], np.cumsum(weights) / weights.sum()])
        dur = c.end - c.start
        for i, line in enumerate(lines):
            s = c.start + dur * bounds[i]
            e = c.start + dur * bounds[i + 1]
            cues.append((s, e, line))
    # sin solapes; los cues contiguos se separan 40 ms
    out = []
    for i, (s, e, l) in enumerate(cues):
        if i + 1 < len(cues):
            e = min(e, cues[i + 1][0] - 0.04) if cues[i + 1][0] - e < 0.04 else e
        out.append((s, max(e, s + 0.3), l))
    return out


def write_srt(path: Path, cues: list[tuple[float, float, str]]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for i, (s, e, l) in enumerate(cues, 1):
            f.write(f"{i}\n{_fmt(s)} --> {_fmt(e)}\n{l}\n\n")


def read_srt(path: Path) -> list[tuple[float, float, list[str]]]:
    import re
    txt = Path(path).read_text(encoding="utf-8").replace("\r", "")
    cues = []
    for block in re.split(r"\n\s*\n", txt.strip()):
        lines = block.split("\n")
        m = re.match(r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)", lines[1])
        a = [int(g) for g in m.groups()]
        s = a[0] * 3600 + a[1] * 60 + a[2] + a[3] / 1000
        e = a[4] * 3600 + a[5] * 60 + a[6] + a[7] / 1000
        cues.append((s, e, lines[2:]))
    return cues
