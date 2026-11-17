"""Banda sonora procedural (sin muestras externas ni derechos de autor):
música ambiental, viento, fuego, pasos en la nieve y efectos puntuales."""
from __future__ import annotations

import numpy as np
from scipy import signal

SR = 44100


def _rng(seed): return np.random.default_rng(seed)


def _noise(n, seed): return _rng(seed).standard_normal(n).astype(np.float32)


def _band(x, lo, hi, order=2):
    sos = signal.butter(order, [lo, hi], btype="band", fs=SR, output="sos")
    return signal.sosfilt(sos, x).astype(np.float32)


def _lp(x, fc, order=2):
    sos = signal.butter(order, fc, btype="low", fs=SR, output="sos")
    return signal.sosfilt(sos, x).astype(np.float32)


def _hp(x, fc, order=2):
    sos = signal.butter(order, fc, btype="high", fs=SR, output="sos")
    return signal.sosfilt(sos, x).astype(np.float32)


def _slow_noise(n, rate_hz, seed):
    k = max(2, int(n / SR * rate_hz) + 2)
    pts = _rng(seed).random(k)
    return np.interp(np.linspace(0, k - 1, n), np.arange(k), pts).astype(np.float32)


def _env_from_scenes(n, starts, ends, levels, ramp=1.2):
    """Nivel por escena con transiciones suaves."""
    t = np.arange(n) / SR
    pts_t, pts_v = [], []
    for s, e, v in zip(starts, ends, levels):
        pts_t += [s + ramp * 0.5, e - ramp * 0.5]
        pts_v += [v, v]
    return np.interp(t, pts_t, pts_v).astype(np.float32)


def _rms(x): return float(np.sqrt(np.mean(x ** 2) + 1e-12))


def wind(n, starts, ends):
    levels = [0.55, 0.3, 0.35, 1.0, 0.12, 0.28]
    base = _band(_noise(n, 1), 120, 1100, 2)
    gust = 0.35 + 0.65 * _slow_noise(n, 0.35, 2) ** 1.5
    whistle = _band(_noise(n, 3), 700, 1500, 3) * (_slow_noise(n, 0.22, 4) ** 3)
    out = (base * gust + 0.5 * whistle) * _env_from_scenes(n, starts, ends, levels)
    return out / _rms(out)


def fire(n, starts, ends):
    t = np.arange(n) / SR
    s3, s4, s5 = starts[2], starts[3], starts[4]
    env = np.zeros(n, np.float32)
    env += np.interp(t, [s3 + 1.6, s3 + 4.8, ends[2] - 0.4, ends[2] + 0.4], [0, 1, 1, 0]).astype(np.float32) * 0.9
    env += np.interp(t, [s4 + 4.5, s4 + 7.5, ends[3] - 0.3, ends[3] + 0.5], [0, 0.35, 0.35, 0]).astype(np.float32)
    env += np.interp(t, [s5 - 0.5, s5 + 0.8, ends[4] - 0.4, ends[4] + 0.5], [0, 1, 1, 0]).astype(np.float32)
    rumble = _lp(_noise(n, 5), 260) * (0.6 + 0.4 * _slow_noise(n, 3, 6))
    crack = np.zeros(n, np.float32)
    r = _rng(7)
    count = int(n / SR * 14)
    pos = r.integers(0, n - 4000, count)
    for p in pos:
        L = int(r.uniform(200, 2600))
        burst = _noise(L, int(p)) * np.exp(-np.linspace(0, r.uniform(5, 12), L)) * r.uniform(0.2, 1.0)
        crack[p:p + L] += burst
    crack = _hp(crack, 900)
    hiss = _band(_noise(n, 8), 2500, 7000) * 0.07
    out = (rumble * 0.9 + crack * 1.8 + hiss) * env
    return out, env


def crunch(n, times, level=1.0, seed=20):
    out = np.zeros(n, np.float32)
    r = _rng(seed)
    for t in times:
        p = int(t * SR)
        L = int(0.14 * SR)
        if p + L >= n:
            continue
        b = _band(_noise(L, int(p)), 600, 4200) * np.exp(-np.linspace(0, 7, L)) * r.uniform(0.6, 1.0)
        out[p:p + L] += b * level
    return out


def whoosh(n, t0, dur=0.55, level=1.0):
    out = np.zeros(n, np.float32)
    p, L = int(t0 * SR), int(dur * SR)
    x = _band(_noise(L, 31), 500, 3500, 2)
    env = np.sin(np.linspace(0, np.pi, L)) ** 2
    out[p:p + L] += x * env * level
    return out


def horn(n, t0, dur=1.6, level=1.0):
    out = np.zeros(n, np.float32)
    p, L = int(t0 * SR), int(dur * SR)
    tt = np.arange(L) / SR
    f = 150 + 120 * np.sin(np.pi * tt / dur) ** 1.5
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) + 0.5 * np.sin(2 * ph) + 0.3 * np.sin(3 * ph) + 0.25 * _noise(L, 41)
    x = _lp(x.astype(np.float32), 1100) * np.sin(np.linspace(0, np.pi, L)) ** 1.5
    out[p:p + L] += x * level
    return out


def flint(n, t0, t1, level=1.0):
    out = np.zeros(n, np.float32)
    for t in np.arange(t0, t1, 0.14):
        p, L = int(t * SR), int(0.05 * SR)
        out[p:p + L] += _hp(_noise(L, int(t * 1000)), 2500) * np.exp(-np.linspace(0, 9, L)) * level
    return out


def music(n, starts, ends):
    t = np.arange(n) / SR
    D, F, A, Bb, G, C, E_, Fs = 146.83, 174.61, 220.0, 233.08, 196.0, 261.63, 164.81, 185.0
    chords = [[D / 2, D, A, F * 2, C * 2], [Bb / 2, Bb, F * 2, D * 2, A * 2], [G / 2, G, D * 2, Bb * 2, F * 2],
              [A / 2, E_ * 2, A, C * 2, E_ * 4], [D / 2, F, A, C * 2, E_ * 2], [D / 2, D, A, Fs * 2, E_ * 2]]
    chord_env = []
    for s, e in zip(starts, ends):
        chord_env.append(np.interp(t, [s - 1.6, s + 1.6, e - 1.6, e + 1.6], [0, 1, 1, 0]).astype(np.float32))
    pad = np.zeros(n, np.float32)
    for ch, ce in zip(chords, chord_env):
        for k, f in enumerate(ch):
            lfo = 1 + 0.15 * np.sin(2 * np.pi * (0.07 + 0.03 * k) * t + k)
            for det in (-0.6, 0.6):
                pad += (np.sin(2 * np.pi * (f + det) * t) * ce * lfo / (1 + 0.3 * k)).astype(np.float32)
    pad = _lp(pad, 1800)
    # campanillas dispersas (pentatónica de Re)
    bells = np.zeros(n, np.float32)
    r = _rng(50)
    notes = [587.33, 698.46, 880.0, 1046.5, 783.99, 1174.7]
    tb = 2.2
    while tb < n / SR - 3:
        f = r.choice(notes)
        L = int(3.2 * SR)
        tt = np.arange(L) / SR
        b = (np.sin(2 * np.pi * f * tt) + 0.35 * np.sin(2 * np.pi * f * 2.76 * tt)) * np.exp(-tt * 1.5)
        p = int(tb * SR)
        m = min(L, n - p)
        bells[p:p + m] += b[:m].astype(np.float32) * r.uniform(0.25, 0.55)
        tb += r.uniform(3.2, 6.0)
    # reverb sintética
    ir_n = int(2.6 * SR)
    ir = _noise(ir_n, 60) * np.exp(-np.linspace(0, 7, ir_n))
    ir = _lp(ir, 3500)
    wet_pad = signal.fftconvolve(pad + bells * 1.5, ir, mode="full")[:n].astype(np.float32)
    wet_pad /= (_rms(wet_pad) + 1e-9)
    dry = (pad / (_rms(pad) + 1e-9)) * 0.8 + (bells / (_rms(bells) + 1e-9)) * 0.25
    out = 0.65 * dry + 0.55 * wet_pad
    return out / _rms(out)


def voice_envelope(voice, win=0.08):
    k = int(win * SR)
    e = np.sqrt(np.convolve(voice ** 2, np.ones(k) / k, mode="same"))
    e = np.clip(e / (e.max() + 1e-9) * 6, 0, 1)
    g = np.exp(-np.arange(int(0.5 * SR)) / (0.18 * SR))   # release suave
    e = np.maximum.accumulate(e) * 0 + signal.fftconvolve(e, g / g.sum(), mode="same")
    return np.clip(e * 1.6, 0, 1).astype(np.float32)


def mix(voice: np.ndarray, starts, ends, total: float):
    n = int(total * SR) + SR // 2
    v = np.zeros(n, np.float32)
    v[:min(n, len(voice))] = voice[:n]
    v = v / _rms(v[np.abs(v) > 0.01]) * 0.12
    m = music(n, starts, ends)
    w = wind(n, starts, ends)
    f, fenv = fire(n, starts, ends)
    s1, s2, s4 = starts[0], starts[1], starts[3]
    steps = list(np.arange(s1 + 0.8, ends[0] - 0.5, 0.77)) + list(np.arange(s2 + 0.4, s2 + 2.0, 0.9)) + list(np.arange(s4 + 0.6, s4 + 6.4, 0.62))
    sfx = crunch(n, steps) * 0.7
    sfx += whoosh(n, s2 + 3.5, level=1.6) + horn(n, s2 + 4.4, level=1.0) * 0.55
    sfx += flint(n, starts[2] + 1.0, starts[2] + 2.4, level=1.2)
    sfx += whoosh(n, starts[2] + 2.4, 1.2, 0.6) * 0.4
    duck = 1 - 0.55 * voice_envelope(v)
    L = (m * 0.020 * duck + w * 0.012 + f * 0.022 + sfx * 0.010)
    R = (m * 0.020 * duck + _hp(w, 40)[::-1][::-1] * 0.012 * 0.9 + f * 0.022 + sfx * 0.010)
    # estéreo: viento y música ligeramente descorrelacionados
    R = np.roll(R, 37)
    st = np.stack([L + v * 0.99, R + v * 0.99], axis=1)
    return np.clip(st, -1.5, 1.5), v
