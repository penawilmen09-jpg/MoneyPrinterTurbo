"""Narración del video: ElevenLabs (única fuente de voz) con tiempos por palabra."""
from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np

from . import elevenlabs_tts as eleven

SR = 44100


def load_wav(path) -> np.ndarray:
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-f", "f32le", "-ac", "1",
         "-ar", str(SR), "-"],
        check=True, capture_output=True,
    ).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()


def synth_beats(beats, workdir: Path):
    """Devuelve {beat_id: dict(audio, words, dur, file_dur, last_word_end)}.

    Cada audio se recorta con ~60 ms antes de la 1.ª palabra y 280 ms de cola
    tras la última, para no cortar nunca el final de una frase.
    """
    workdir.mkdir(parents=True, exist_ok=True)
    out = {}
    for i, (bid, text, _gap) in enumerate(beats):
        prev_t = beats[i - 1][1] if i else ""
        next_t = beats[i + 1][1] if i + 1 < len(beats) else ""
        mp3 = workdir / f"{bid}.mp3"
        words = eleven.synthesize(text, mp3, prev_t, next_t)
        wav = load_wav(mp3)
        t0 = max(0.0, words[0][1] - 0.06)
        t1 = words[-1][2] + 0.28
        seg = wav[int(t0 * SR): min(len(wav), int(t1 * SR))].copy()
        # ElevenLabs recorta el silencio final: se añade margen y un fundido corto
        # para que la última palabra nunca suene cortada.
        ff = int(0.02 * SR)
        seg[-ff:] *= np.linspace(1, 0, ff)
        seg = np.concatenate([seg, np.zeros(int(0.3 * SR), dtype=np.float32)])
        f = int(0.008 * SR)
        seg[:f] *= np.linspace(0, 1, f)
        out[bid] = dict(
            audio=seg,
            words=[(w, s - t0, e - t0) for w, s, e in words],
            dur=len(seg) / SR,
            file_dur=len(wav) / SR,
            last_word_end=words[-1][2] - t0,
        )
    return out
