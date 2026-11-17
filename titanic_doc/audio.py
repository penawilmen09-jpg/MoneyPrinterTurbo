# -*- coding: utf-8 -*-
"""Banda sonora 100% sintetizada (numpy): música instrumental de suspenso + efectos. SIN voces ni letras."""
import numpy as np, wave, os

SR = 44100
DUR = 60.0
N = int(SR * DUR)
rng = np.random.RandomState(12)


def tt(n=N):
    return np.arange(n) / SR


def env_at(t0, t1, a=0.05, r=0.2, n=N):
    t = tt(n)
    e = np.clip((t - t0) / max(a, 1e-3), 0, 1) * np.clip((t1 - t) / max(r, 1e-3), 0, 1)
    e[(t < t0) | (t > t1)] = 0
    return e


def smooth_env(points, n=N):
    t = tt(n)
    return np.interp(t, [p[0] for p in points], [p[1] for p in points])


def lowpass(x, fc, order=2):
    # filtro de un polo repetido (rápido, vectorizado por FFT)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    H = 1 / (1 + (f / fc) ** (2 * order))
    return np.fft.irfft(X * H, len(x))


def highpass(x, fc, order=2):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    H = 1 - 1 / (1 + (f / fc) ** (2 * order))
    return np.fft.irfft(X * H, len(x))


def bandpass(x, lo, hi):
    return highpass(lowpass(x, hi), lo)


def noise(n=N):
    return rng.randn(n)


def sine(f, n=N, ph=0.0):
    if np.isscalar(f):
        return np.sin(2 * np.pi * f * tt(n) + ph)
    return np.sin(2 * np.pi * np.cumsum(f) / SR + ph)


def place_sound(buf, snd, t0):
    i = int(t0 * SR)
    if i >= len(buf):
        return
    j = min(len(buf), i + len(snd))
    buf[i:j] += snd[:j - i]


def norm(x, peak=1.0):
    m = np.max(np.abs(x)) + 1e-9
    return x / m * peak


# ---------------------------------------------------------------- AMBIENTE
def ocean():
    n = noise()
    low = lowpass(n, 380)
    mid = bandpass(n, 400, 1800)
    t = tt()
    swell = 0.55 + 0.45 * np.sin(2 * np.pi * t / 7.3 - 1) * np.sin(2 * np.pi * t / 4.1 + 2) ** 2
    lv = smooth_env([(0, 0.8), (5, 0.9), (12, 0.55), (19, 0.5), (27, 0.5), (35, 0.55), (43, 0.5), (50, 0.3), (51, 0.5), (60, 0.35)])
    return (norm(low) * 0.9 + norm(mid) * 0.35 * swell) * swell * lv


def wind():
    n = noise()
    t = tt()
    fc = 600 + 450 * np.sin(2 * np.pi * t / 9.0) * np.sin(2 * np.pi * t / 5.3 + 1)
    # banda variable aproximada mezclando dos filtros
    a = bandpass(n, 250, 700)
    b = bandpass(n, 700, 1600)
    m = 0.5 + 0.5 * np.sin(2 * np.pi * t / 8.0 + 0.5)
    w = a * (1 - m) + b * m
    lv = smooth_env([(0, 0.35), (12, 0.5), (19, 0.6), (35, 0.5), (45, 0.45), (51, 0.35), (60, 0.2)])
    return norm(w) * lv * (0.7 + 0.3 * np.sin(2 * np.pi * t / 6.1))


def hull_waves():
    # olas golpeando el casco: pulsos graves de ruido filtrado
    out = np.zeros(N)
    t0 = 0.5
    while t0 < 60:
        L = int(1.4 * SR)
        n = lowpass(noise(L), 500)
        e = np.exp(-np.arange(L) / SR * 2.4) * (1 - np.exp(-np.arange(L) / SR * 30))
        amp = 0.5 + 0.5 * rng.rand()
        lv = 1.0 if t0 < 51 else 0.5
        place_sound(out, n * e * amp * lv, t0)
        t0 += 2.2 + rng.rand() * 1.6
    return norm(out) * 0.5


def engine():
    t = tt()
    base = 46 + 0.7 * np.sin(2 * np.pi * t * 0.2)
    x = sine(base) * 0.6 + sine(base * 2) * 0.25 + sine(base * 3.01) * 0.12
    pulse = 0.75 + 0.25 * np.sin(2 * np.pi * t * 3.1)
    rumble = lowpass(noise(), 140) * 0.8
    lv = smooth_env([(0, 0.6), (3, 0.9), (5, 0.9), (12, 0.8), (19.5, 0.8), (27, 0.35), (36, 0.2), (43, 0.1), (51, 0.0), (60, 0.0)])
    # la maquinaria cesa progresivamente (tras el impacto se ordena detenerla)
    return (x * pulse + rumble) * lv * 0.5


def horn(t0, dur=2.6, f=118):
    L = int(dur * SR)
    t = np.arange(L) / SR
    x = sum(np.sin(2 * np.pi * f * k * t) / k ** 0.8 for k in range(1, 8))
    x += 0.4 * sum(np.sin(2 * np.pi * f * 1.5 * k * t) / k for k in range(1, 4))
    e = np.clip(t / 0.25, 0, 1) * np.clip((dur - t) / 0.7, 0, 1)
    x = lowpass(x, 1500) * e
    # eco
    out = np.zeros(L + SR)
    out[:L] += x
    out[int(0.35 * SR):int(0.35 * SR) + L] += x * 0.25
    out = norm(out, 0.9)
    buf = np.zeros(N)
    place_sound(buf, out, t0)
    return buf


def bell_buoy(t0):
    L = int(2.5 * SR)
    t = np.arange(L) / SR
    x = np.sin(2 * np.pi * 880 * t) * np.exp(-t * 2.6) + 0.5 * np.sin(2 * np.pi * 1320 * t) * np.exp(-t * 3.5)
    buf = np.zeros(N)
    place_sound(buf, x * 0.5, t0)
    return buf


def seagulls(t0, n=6):
    buf = np.zeros(N)
    for k in range(n):
        L = int(0.55 * SR)
        t = np.arange(L) / SR
        f = 1500 + 700 * np.sin(np.pi * t / 0.55) + 80 * np.sin(2 * np.pi * 14 * t)
        x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / 0.55) ** 0.7
        place_sound(buf, x * 0.18 * (0.5 + rng.rand()), t0 + k * 0.9 + rng.rand() * 0.4)
    return buf


def impact(t0):
    buf = np.zeros(N)
    L = int(3.5 * SR)
    t = np.arange(L) / SR
    thud = np.sin(2 * np.pi * (52 - 18 * t) * t) * np.exp(-t * 3.2) * 1.2
    scr = bandpass(noise(L), 300, 3500) * np.exp(-np.maximum(t - 0.1, 0) * 0.6) * np.clip(t / 0.2, 0, 1)
    scr *= (0.6 + 0.4 * np.sin(2 * np.pi * 9 * t) * np.sin(2 * np.pi * 3.3 * t))
    scr *= np.clip((3.2 - t) / 1.2, 0, 1)
    crack = highpass(noise(L), 1500) * np.exp(-t * 40) * 1.5
    metal = np.sin(2 * np.pi * 330 * t) * np.exp(-t * 3) * 0.2 + np.sin(2 * np.pi * 477 * t) * np.exp(-t * 4) * 0.15
    x = thud + scr * 0.8 + crack * 0.5 + metal
    place_sound(buf, norm(x, 1.0), t0)
    return buf


def water_rush(t0, t1):
    n = noise()
    x = bandpass(n, 200, 2500) * 0.6 + lowpass(n, 200) * 0.8
    t = tt()
    gur = 0.7 + 0.3 * np.sin(2 * np.pi * t * 5.5) * np.sin(2 * np.pi * t * 1.7)
    e = env_at(t0, t1, 1.0, 1.5)
    lv = e * (0.4 + 0.6 * np.clip((t - t0) / (t1 - t0), 0, 1))
    return norm(x) * gur * lv


def creaks(t0, t1, density=0.9, gain=1.0):
    buf = np.zeros(N)
    t = t0
    while t < t1:
        L = int((0.5 + rng.rand() * 1.1) * SR)
        tt_ = np.arange(L) / SR
        f0 = 90 + rng.rand() * 220
        f = f0 * (1 + 0.25 * np.sin(2 * np.pi * (2 + 4 * rng.rand()) * tt_) + 0.3 * tt_)
        x = sum(np.sin(2 * np.pi * np.cumsum(f * k) / SR) / k for k in range(1, 6))
        x *= (1 + 0.6 * np.sin(2 * np.pi * (11 + 25 * rng.rand()) * tt_))
        x = bandpass(x, 120, 1800)
        e = np.sin(np.pi * tt_ / (L / SR)) ** 1.5
        place_sound(buf, norm(x) * e * (0.3 + 0.7 * rng.rand()) * gain, t)
        t += (0.5 + rng.rand() * 1.4) / density
    return buf


def pulleys(t0, t1):
    buf = np.zeros(N)
    t = t0
    while t < t1:
        L = int(0.12 * SR)
        x = bandpass(noise(L), 600, 2400) * np.hanning(L)
        place_sound(buf, x * 0.35, t)
        t += 0.17 + rng.rand() * 0.05
    return buf


def splash(t0, gain=1.0):
    buf = np.zeros(N)
    L = int(1.4 * SR)
    t = np.arange(L) / SR
    x = bandpass(noise(L), 250, 4000) * np.exp(-t * 3.5) * np.clip(t / 0.03, 0, 1)
    x += lowpass(noise(L), 150) * np.exp(-t * 5) * 0.8
    place_sound(buf, norm(x) * gain, t0)
    return buf


def rocket(t0):
    buf = np.zeros(N)
    L = int(1.1 * SR)
    t = np.arange(L) / SR
    f = 500 + 1800 * (t / 1.1) ** 2
    x = bandpass(noise(L), 800, 4000) * np.clip(t / 0.2, 0, 1) * (1 - t / 1.1) * 0.5
    x += np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.08 * (1 - t / 1.1)
    place_sound(buf, x, t0)
    # estallido
    L2 = int(1.5 * SR)
    t2 = np.arange(L2) / SR
    b = (lowpass(noise(L2), 700) * np.exp(-t2 * 5) * 1.1 + highpass(noise(L2), 2500) * np.exp(-t2 * 18) * 0.6)
    place_sound(buf, b, t0 + 1.0)
    return buf


def breakup(t0):
    """Ruptura estructural: gemido metálico grave + estruendo."""
    buf = np.zeros(N)
    L = int(3.2 * SR)
    t = np.arange(L) / SR
    f = 70 * (1 + 0.5 * np.sin(2 * np.pi * 0.7 * t)) + 30 * t
    g = sum(np.sin(2 * np.pi * np.cumsum(f * k) / SR) / k for k in range(1, 7))
    g *= (1 + 0.5 * np.sin(2 * np.pi * 17 * t))
    g = bandpass(g, 60, 1500) * np.clip(t / 0.4, 0, 1) * np.clip((3.2 - t) / 1.0, 0, 1)
    boom = lowpass(noise(L), 300) * np.exp(-np.maximum(t - 0.6, 0) * 1.4) * np.clip((t - 0.5) / 0.05, 0, 1) * 1.4
    snap = highpass(noise(L), 800) * np.exp(-np.abs(t - 0.6) * 25) * 0.8
    place_sound(buf, norm(g, 0.8) + boom * 0.8 + snap * 0.4, t0)
    return buf


def sinking_gurgle(t0, t1):
    t = tt()
    n = noise()
    x = lowpass(n, 450) * (0.6 + 0.4 * np.sin(2 * np.pi * t * 2.3)) + bandpass(n, 500, 2500) * 0.4 * np.abs(np.sin(2 * np.pi * t * 4.1))
    e = env_at(t0, t1, 0.4, 1.8)
    return norm(x) * e * 0.9


def bubbles(t0, t1):
    buf = np.zeros(N)
    t = t0
    while t < t1:
        L = int(0.12 * SR)
        tt_ = np.arange(L) / SR
        f0 = 300 + rng.rand() * 900
        x = np.sin(2 * np.pi * (f0 * (1 + 4 * tt_)) * tt_) * np.exp(-tt_ * 35)
        place_sound(buf, x * 0.25 * rng.rand(), t)
        t += 0.02 + rng.rand() * 0.1
    return buf


def oars_and_rescue(t0, t1):
    """Ambiente de rescate: remos, madera y agua suave."""
    buf = np.zeros(N)
    t = t0
    while t < t1:
        L = int(0.35 * SR)
        tt_ = np.arange(L) / SR
        x = bandpass(noise(L), 200, 1500) * np.exp(-tt_ * 9) * np.clip(tt_ / 0.02, 0, 1)
        x += np.sin(2 * np.pi * 150 * tt_) * np.exp(-tt_ * 30) * 0.4
        place_sound(buf, x * 0.25 * (0.5 + rng.rand()), t)
        t += 1.1 + rng.rand() * 0.6
    return buf


# ---------------------------------------------------------------- MÚSICA (cuerdas/pads sintéticos, sin voz)
MID = lambda m: 440.0 * 2 ** ((m - 69) / 12)


def pad(notes, t0, t1, gain=1.0, bright=1.0, vib=0.0):
    t = tt()
    out = np.zeros(N)
    e = env_at(t0, t1, 1.6, 2.2)
    for m in notes:
        f = MID(m)
        for det in (-0.07, 0.0, 0.08):
            ff = f * (1 + det * 0.01 + vib * 0.004 * np.sin(2 * np.pi * 5.2 * t))
            x = np.zeros(N)
            for k, a in ((1, 1.0), (2, 0.5 * bright), (3, 0.3 * bright), (4, 0.18 * bright), (5, 0.1 * bright)):
                x += a * np.sin(2 * np.pi * np.cumsum(ff * k * np.ones(N)) / SR + rng.rand() * 6)
            out += x * e
    return out * gain / (len(notes) * 3)


def music():
    m = np.zeros(N)
    # armonía menor lenta: Dm - Bb - Gm - A (tensión) ... y cierre solemne
    prog = [
        (0, 5, [38, 50, 57, 62]),            # D menor (grave)
        (5, 12, [38, 50, 57, 65]),           # viaje: Dm6 ligeramente abierto
        (12, 19, [34, 46, 53, 62, 65]),      # Bb: advertencia
        (19, 23, [43, 55, 62, 70]),          # Gm: tensión
        (23, 27, [33, 45, 52, 61, 64]),      # A7: choque
        (27, 35, [38, 50, 56, 62, 65]),      # Dº: inundación
        (35, 43, [31, 43, 50, 58, 62, 67]),  # Gm: evacuación
        (43, 49.0, [29, 41, 48, 56, 60]),    # F mayor/menor: hundimiento
        (49.0, 55, [38, 50, 57, 62, 69]),    # Dm: elegía
        (55, 60, [38, 45, 50, 57, 62, 66]),  # D (apertura esperanzadora, final)
    ]
    for a, b, notes in prog:
        m += pad(notes, a, b + 1.0, gain=0.9, bright=1.0 if a < 43 else 0.7, vib=1.0)
    t = tt()
    # pulso de tensión (tipo latido grave) creciente hasta el hundimiento
    pulse = np.zeros(N)
    tp = 5.0
    while tp < 50:
        rate = 1.6 - 0.6 * np.clip((tp - 12) / 36, 0, 1)
        L = int(0.4 * SR)
        k = np.arange(L) / SR
        beat = np.sin(2 * np.pi * (60 - 20 * k) * k) * np.exp(-k * 9)
        amp = 0.25 + 0.55 * np.clip((tp - 12) / 36, 0, 1)
        place_sound(pulse, beat * amp, tp)
        tp += rate
    # melodía simple de cuerdas (frase de 3 notas, legato) – instrumental
    mel = np.zeros(N)
    melody = [(1.0, 4.5, 74), (6.0, 11.5, 77), (12.5, 18.0, 76), (19.5, 23.0, 74), (23.5, 26.5, 73), (28.0, 34.0, 70),
              (35.5, 42.0, 74), (43.5, 49.5, 69), (50.0, 54.5, 74), (55.0, 59.5, 78)]
    for a, b, n in melody:
        f = MID(n)
        e = env_at(a, b, 0.9, 1.6)
        v = 1 + 0.006 * np.sin(2 * np.pi * 5.4 * t)
        x = sum(np.sin(2 * np.pi * np.cumsum(f * k * v) / SR) * (1 / k) for k in range(1, 7))
        mel += x * e * 0.35
    # contrabajo sostenido
    sw = smooth_env([(0, 0.5), (12, 0.7), (35, 1.0), (48, 0.8), (55, 0.5), (60, 0.2)])
    bass = np.zeros(N)
    for a, b, notes in prog:
        e = env_at(a, b + 0.8, 1.2, 1.5)
        bass += sine(MID(notes[0] - 12)) * e * 0.9
    rise = 0.0
    out = lowpass(m, 3500) * 0.9 + mel * 0.55 + pulse * 0.6 + bass * 0.55 * sw
    # silencio dramático breve al hundirse (47.8-48.6 baja) y envolvente global
    glob = smooth_env([(0, 0.0), (1.5, 0.75), (46.8, 0.95), (48.6, 0.45), (50, 0.7), (58, 0.85), (60, 0.0)])
    return out * glob


def riser(t0, t1, gain=1.0):
    """Subida de tensión: ruido con barrido ascendente + tono que sube."""
    n = noise()
    t = tt()
    e = np.clip((t - t0) / (t1 - t0), 0, 1) ** 2.2
    e[(t < t0) | (t > t1 + 0.15)] = 0
    lo = bandpass(n, 300, 1400)
    hi = highpass(n, 2500)
    m = np.clip((t - t0) / (t1 - t0), 0, 1)
    x = lo * (1 - m) + hi * m * 0.6
    f = 180 + 900 * m ** 2
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.15
    return (norm(x) * 0.8 + tone) * e * gain


def timpani(t0, gain=1.0):
    buf = np.zeros(N)
    L = int(1.8 * SR)
    t = np.arange(L) / SR
    x = np.sin(2 * np.pi * (46 + 26 * np.exp(-t * 9)) * t) * np.exp(-t * 2.4)
    x += lowpass(noise(L), 200) * np.exp(-t * 14) * 0.6
    place_sound(buf, x * gain, t0)
    return buf


def elec_hum(t0, dur=1.1):
    buf = np.zeros(N)
    L = int(dur * SR)
    t = np.arange(L) / SR
    x = (np.sin(2 * np.pi * 60 * t) + 0.5 * np.sin(2 * np.pi * 120 * t) + 0.3 * np.sin(2 * np.pi * 180 * t))
    x *= (1 - t / dur) ** 1.5 * (0.6 + 0.4 * np.sign(np.sin(2 * np.pi * 14 * t)))
    place_sound(buf, x * 0.4, t0)
    return buf


def build():
    mus = norm(music(), 1.0) * 0.55
    amb = norm(ocean() + wind() * 0.7 + hull_waves() * 0.6 + engine() * 0.9, 1.0) * 0.55
    fx = np.zeros(N)
    # ESCENA 2: silbato de partida y gaviotas
    fx += horn(5.3, 2.8, 112) * 0.9
    fx += seagulls(6.0, 5) * 0.8
    fx += horn(9.0, 1.2, 140) * 0.35
    # ESCENA 3: campana lejana y crujidos suaves
    fx += bell_buoy(15.2) * 0.25
    fx += creaks(12.5, 19, 0.35, 0.18)
    # ESCENA 4: impacto
    fx += impact(22.4) * 1.0
    fx += water_rush(24.0, 27.0) * 0.35
    # ESCENA 5: inundación
    fx += water_rush(27.0, 36.0) * 0.8
    fx += bubbles(28, 35) * 0.8
    fx += creaks(27, 36, 0.7, 0.25)
    # ESCENA 6: evacuación
    fx += pulleys(36.4, 40.2) * 0.8 + pulleys(37.8, 41.6) * 0.7
    fx += splash(40.2) * 0.8 + splash(41.6) * 0.7
    fx += rocket(36.0) * 0.55 + rocket(38.6) * 0.5 + rocket(40.6) * 0.45
    fx += creaks(35, 44, 1.2, 0.4)
    fx += horn(35.6, 2.4, 100) * 0.35
    # ESCENA 7: hundimiento
    fx += creaks(43, 45.0, 1.6, 0.55)
    fx += elec_hum(44.3)
    fx += breakup(45.0) * 1.0
    fx += creaks(45.9, 48.4, 1.6, 0.5)
    fx += sinking_gurgle(45.2, 50.5) * 0.9
    fx += splash(45.4, 0.9) + splash(47.5, 0.9) + splash(48.6, 1.3)
    fx += timpani(45.0, 0.9) + timpani(22.4, 1.0)
    fx += riser(13.0, 19.0, 0.35) + riser(19.2, 22.4, 0.7) + riser(36.5, 44.6, 0.55)
    # ESCENA 8: rescate
    fx += oars_and_rescue(51.2, 56.0) * 0.8
    fx += horn(52.2, 3.0, 96) * 0.5
    fx += seagulls(55.5, 0) * 0
    fx = norm(fx, 1.0) * 0.8
    mix = mus + amb + fx
    # fundido de entrada/salida y limitador suave
    t = tt()
    mix *= np.clip(t / 0.6, 0, 1) * np.clip((DUR - t) / 1.5, 0, 1)
    mix = np.tanh(mix * 1.05)
    mix = norm(mix, 0.89)
    # estéreo con leve ancho (retardo Haas + reverb simple)
    L = mix.copy()
    R = np.roll(mix, int(0.011 * SR)) * 0.96
    rev = np.zeros(N)
    for d, g in ((0.083, 0.28), (0.127, 0.2), (0.191, 0.14), (0.263, 0.1)):
        rev += np.roll(mix, int(d * SR)) * g
    L += rev * 0.5
    R += np.roll(rev, 311) * 0.5
    st = np.stack([L, R], 1)
    st = norm(st, 0.89)
    return st


if __name__ == '__main__':
    here = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(os.path.join(here, 'build'), exist_ok=True)
    st = build()
    pcm = (np.clip(st, -1, 1) * 32767).astype('<i2')
    with wave.open(os.path.join(here, 'build', 'audio.wav'), 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print('audio ok', pcm.shape)
