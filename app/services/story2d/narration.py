"""Síntesis de la narración (edge-tts, gratuito) con tiempos por palabra."""
from __future__ import annotations

import asyncio
import json
import os
import subprocess
from pathlib import Path

import numpy as np

SR = 44100


def _run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


async def _synth_one(text, voice, rate, out_mp3, proxy):
    import edge_tts

    comm = edge_tts.Communicate(
        text, voice, rate=rate, boundary="WordBoundary", proxy=proxy
    )
    words, audio = [], bytearray()
    async for ch in comm.stream():
        if ch["type"] == "audio":
            audio += ch["data"]
        elif ch["type"] == "WordBoundary":
            words.append(
                (ch["text"], ch["offset"] / 1e7, ch["duration"] / 1e7)
            )
    if not audio:
        raise RuntimeError("edge-tts no devolvió audio")
    Path(out_mp3).write_bytes(bytes(audio))
    return words


def load_wav(path) -> np.ndarray:
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-f", "f32le", "-ac", "1",
         "-ar", str(SR), "-"],
        check=True, capture_output=True,
    ).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()


def synth_beats(beats, voice, rate, workdir: Path, proxy=None, force=False):
    """Devuelve {beat_id: dict(audio=np.ndarray, words=[(txt,start,end)])}.

    Cada audio queda recortado con ~60 ms antes de la 1.ª palabra y una cola
    de 280 ms después de la última (nunca se corta el final de la frase).
    """
    workdir.mkdir(parents=True, exist_ok=True)
    out = {}
    for bid, text, _gap in beats:
        mp3 = workdir / f"{bid}_{rate.replace('%','p').replace('+','')}.mp3"
        meta = mp3.with_suffix(".json")
        if force or not mp3.exists() or not meta.exists():
            last = None
            for attempt in range(4):
                try:
                    words = asyncio.run(_synth_one(text, voice, rate, mp3, proxy))
                    break
                except Exception as exc:  # reintento ante fallos de red
                    last = exc
            else:
                raise RuntimeError(f"TTS falló para {bid}: {last}")
            meta.write_text(json.dumps(words))
        words = json.loads(meta.read_text())
        wav = load_wav(mp3)
        t0 = max(0.0, words[0][1] - 0.06)
        t1 = words[-1][1] + words[-1][2] + 0.28
        i0, i1 = int(t0 * SR), min(len(wav), int(t1 * SR))
        seg = wav[i0:i1].copy()
        # fundidos de 8 ms para evitar clics, sin recortar contenido
        f = int(0.008 * SR)
        seg[:f] *= np.linspace(0, 1, f)
        seg[-f:] *= np.linspace(1, 0, f)
        out[bid] = dict(
            audio=seg,
            words=[(w, s - t0, s - t0 + d) for w, s, d in words],
            dur=len(seg) / SR,
            file_dur=len(wav) / SR,
            last_word_end=words[-1][1] + words[-1][2] - t0,
        )
    return out
