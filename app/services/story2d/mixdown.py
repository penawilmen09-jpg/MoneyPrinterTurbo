"""Mezcla «documental»: la voz manda sobre todo lo demás.

- Voz: compresión suave (sin tocar palabras ni tiempos), cuerpo constante.
- Música: ~22 dB bajo la voz durante el habla (sube algo solo en pausas/intro/cierre).
- Efectos: ~12-18 dB bajo la voz y colocados en huecos; se atenúan si pisan habla.
- Ducking automático de música y efectos con la actividad de la voz.
- Normalización final a -14 LUFS / -1 dBTP (ffmpeg loudnorm, 2 pasadas).
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import numpy as np

from . import audio
from .audio import SR, rms, db, voice_activity, voice_priority, get_sfx


def compress_voice(x, thresh_db=-26.0, ratio=2.2, attack=0.008, release=0.12, makeup_db=None):
    """Compresor suave feed-forward con envolvente RMS. No cambia el tiempo."""
    fr = int(0.005 * SR)
    n = len(x) // fr * fr
    e = np.sqrt(np.mean(x[:n].reshape(-1, fr) ** 2, axis=1)) + 1e-9
    lev = 20 * np.log10(e)
    over = np.maximum(lev - thresh_db, 0)
    gr = -over * (1 - 1 / ratio)                    # reducción en dB
    a, r = np.exp(-fr / SR / attack), np.exp(-fr / SR / release)
    s = np.empty_like(gr)
    cur = 0.0
    for i, g in enumerate(gr):
        k = a if g < cur else r
        cur = k * cur + (1 - k) * g
        s[i] = cur
    gain = np.repeat(10 ** (s / 20), fr)
    gain = np.pad(gain, (0, len(x) - len(gain)), constant_values=gain[-1])
    y = x * gain
    if makeup_db is None:                           # recupera el nivel de pico original
        makeup_db = db(np.max(np.abs(x))) - db(np.max(np.abs(y)))
    return (y * 10 ** (makeup_db / 20)).astype(np.float32)


def mix_documental(total, voice_events, sfx_events, music, music_db=23.0, music_gap_boost_db=6.0,
                   sfx_margin_db=16.0, music_margin_db=22.0):
    n = int(total * SR)
    voice = np.zeros(n, dtype=np.float32)
    for t0, a in voice_events:
        i = int(round(t0 * SR))
        voice[i:i + len(a)] += a[: n - i]
    voice = compress_voice(voice)
    voice *= (10 ** (-3 / 20)) / np.max(np.abs(voice))          # pico -3 dBFS
    act = voice_activity(voice)
    speech = act > 0.5
    v_rms = rms(voice[speech])                                   # nivel de la voz en habla

    # ---- música: música_db bajo la voz en habla; +boost en pausas (ducking automático)
    mus = music[:n].copy() if len(music) >= n else np.pad(music, ((0, n - len(music)), (0, 0)))
    duck = 10 ** (-music_gap_boost_db / 20)
    env = (1.0 - (1.0 - duck) * act).astype(np.float32)
    m0 = mus * env[:, None]
    ref = rms(m0[speech].mean(axis=1))
    mus = m0 * (v_rms * 10 ** (-music_db / 20) / ref)

    # ---- efectos: dB bajo la voz, en huecos entre palabras
    fr = int(0.02 * SR)
    ve = np.sqrt(np.mean(voice[: n // fr * fr].reshape(-1, fr) ** 2, axis=1))

    def overlap(ts, dur):
        i0, i1 = int(ts / 0.02), int((ts + dur) / 0.02)
        return float(np.sum(ve[max(0, i0):i1] ** 2)) if i1 > 0 else 0.0

    sfx = np.zeros((n, 2), dtype=np.float32)
    placed = []
    for t0, name, rel_db, pan in sfx_events:
        a = get_sfx(name)
        dur = min(len(a) / SR, 0.8)
        best, best_c = t0, overlap(t0, dur)
        for off in np.arange(-0.6, 0.601, 0.05):               # busca el hueco más cercano
            c = overlap(t0 + off, dur) + 0.002 * abs(off)
            if c < best_c - 1e-9:
                best, best_c = t0 + off, c
        t_ = max(0.0, best)
        i = int(round(t_ * SR))
        seg = a[: n - i]
        refw = a[: int(min(len(a), 0.5 * SR))]
        scale = v_rms * 10 ** (-rel_db / 20) / max(rms(refw), 1e-6)
        sfx[i:i + len(seg), 0] += seg * scale * (1 - max(0, pan))
        sfx[i:i + len(seg), 1] += seg * scale * (1 + min(0, pan))
        vw = voice[i:i + int(min(len(a), 0.8 * SR))]
        placed.append(dict(t=t_, name=name, shift=t_ - t0, rel_db=rel_db,
                           over_speech=bool(rms(vw) > 0.03)))
    # prioridad a la voz (ducking por actividad + red de seguridad)
    mus = voice_priority(mus, voice, music_margin_db)
    sfx = voice_priority(sfx, voice, sfx_margin_db)
    mix = np.stack([voice, voice], 1) + mus + sfx
    return dict(voice=voice, music=mus, sfx=sfx, mix=mix.astype(np.float32),
                placed=placed, activity=act, v_rms=v_rms)


# ---------------------------------------------------------------- loudness
def _loudnorm_stats(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af",
                        "loudnorm=I=-14:TP=-1.6:LRA=9:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr, re.S)
    return json.loads(m.group(0))


def normalize_file(src, dst):
    """loudnorm en dos pasadas (lineal) → -14 LUFS, pico real ≤ -1 dBTP."""
    st = _loudnorm_stats(src)
    f = (f"loudnorm=I=-14:TP=-1.6:LRA=9:measured_I={st['input_i']}:measured_TP={st['input_tp']}:"
         f"measured_LRA={st['input_lra']}:measured_thresh={st['input_thresh']}:"
         f"offset={st['target_offset']}:linear=true:print_format=summary")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-af", f,
                    "-ar", str(SR), "-c:a", "pcm_s16le", str(dst)], check=True)
    return _loudnorm_stats(dst)
