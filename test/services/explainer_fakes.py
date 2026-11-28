"""Offline stand-ins used by the explainer tests (no network, no paid TTS)."""

import os

import numpy as np

from app.services.explainer import audio as A
from app.services.explainer.models import Word
from app.services.explainer.narration import NarrationResult


def fake_narrator(scene, previous_text, next_text, out_dir):
    """Speech-like signal (voiced pulses) with exact word timings."""
    os.makedirs(out_dir, exist_ok=True)
    rng = np.random.default_rng(len(scene.narration))
    t_cursor, words, chunks = 0.0, [], []
    for w in scene.narration.split():
        dur = 0.10 + 0.036 * len(w)
        n = int(dur * A.SR)
        t = np.arange(n) / A.SR
        f0 = 120 + 20 * rng.random()
        voiced = sum(np.sin(2 * np.pi * f0 * k * t) / k for k in range(1, 12))
        env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 0.6 * (0.6 + 0.4 * np.sin(2 * np.pi * 4.5 * t))
        chunks.append((A.fft_band(voiced, 90, 3800) * env * 0.12, t_cursor))
        words.append(Word(text=w, start=t_cursor, end=t_cursor + dur))
        t_cursor += dur + 0.05 + (0.18 if w[-1] in ",.?" else 0.0)
    total = t_cursor + 0.15
    buf = np.zeros(int(total * A.SR))
    for sig, t0 in chunks:
        a = int(t0 * A.SR)
        buf[a:a + len(sig)] += sig
    path = os.path.join(out_dir, f"{scene.id}.wav")
    A.write_wav(path, buf / max(np.max(np.abs(buf)), 1e-6) * 0.5)
    return NarrationResult(path, total, words)
