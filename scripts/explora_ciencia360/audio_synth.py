"""Música cinematográfica de suspenso científico y efectos — síntesis propia (sin derechos de autor)."""
import sys, wave, numpy as np
from common import TOTAL, SCENES

SR = 44100
N = int((TOTAL + 1.0) * SR)
rng = np.random.RandomState(2024)


def tvec(n): return np.arange(n) / SR


def env_ad(n, a, d):
    t = tvec(n); e = np.minimum(t / max(a, 1e-4), 1.0) * np.exp(-t / d)
    return e


def place(buf, x, at, gain=1.0, pan=0.0):
    i = int(at * SR)
    if i >= len(buf) or i < 0: return
    seg = x[: len(buf) - i]
    l = gain * (1 - max(pan, 0)); r = gain * (1 + min(pan, 0))
    buf[i:i + len(seg), 0] += seg * l; buf[i:i + len(seg), 1] += seg * r


def lowpass(x, fc):
    a = np.exp(-2 * np.pi * fc / SR); y = np.empty_like(x); s = 0.0
    # IIR vectorizado por bloques (rápido): usar FFT
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    return np.fft.irfft(X / (1 + (f / fc) ** 2), len(x))


def bandpass_noise(n, f0, f1):
    x = rng.randn(n); X = np.fft.rfft(x); f = np.fft.rfftfreq(n, 1 / SR)
    m = ((f > f0) & (f < f1)).astype(float)
    return np.fft.irfft(X * m, n)


def midi(m): return 440.0 * 2 ** ((m - 69) / 12)


def saw_pad(freq, dur, detune=(0.996, 1.0, 1.004), harm=14):
    n = int(dur * SR); t = tvec(n); out = np.zeros(n)
    for d in detune:
        for h in range(1, harm + 1):
            out += np.sin(2 * np.pi * freq * d * h * t + h) / h ** 1.6
    return out / len(detune)


def bell(freq, dur=1.6):
    n = int(dur * SR); t = tvec(n)
    x = np.sin(2 * np.pi * freq * t) + .4 * np.sin(2 * np.pi * freq * 2.01 * t) * np.exp(-t * 4) + .2 * np.sin(2 * np.pi * freq * 3.99 * t) * np.exp(-t * 7)
    return x * env_ad(n, .004, dur / 4)


def reverb(x, secs=2.4, mix=0.3):
    n = int(secs * SR); t = tvec(n)
    ir = (rng.randn(n, 2)) * np.exp(-t / (secs / 4))[:, None]
    ir[:int(.02 * SR)] *= np.linspace(0, 1, int(.02 * SR))[:, None]
    L = int(2 ** np.ceil(np.log2(len(x) + n)))
    out = np.zeros_like(x)
    for c in range(2):
        y = np.fft.irfft(np.fft.rfft(x[:, c], L) * np.fft.rfft(ir[:, c], L), L)[:len(x)]
        out[:, c] = y
    out *= 0.04
    return x * (1 - mix * .5) + out * mix * 2.2


def music():
    m = np.zeros((N, 2))
    t = tvec(N)
    bpm = 72; beat = 60 / bpm
    # drone grave
    drone = (np.sin(2 * np.pi * 55 * t) + .5 * np.sin(2 * np.pi * 82.4 * t + .5 * np.sin(t * .3)) + .25 * np.sin(2 * np.pi * 110 * t)) * (0.55 + .25 * np.sin(2 * np.pi * t / 7.3))
    drone *= np.minimum(t / 3.0, 1) * np.clip((TOTAL + .6 - t) / 2.0, 0, 1)
    m[:, 0] += drone * .5; m[:, 1] += drone * .5
    # acordes (Am - F - Dm - E sus) cada 8 pulsos
    chords = [(57, 60, 64), (53, 57, 60), (50, 53, 57), (52, 56, 59)]
    seg = beat * 8
    k = 0; at = 0.0
    while at < TOTAL + .5:
        ch = chords[k % 4]
        if at >= TOTAL - 4.3:       # resolución luminosa en la marca
            ch = (57, 61, 64, 71)
        dur = seg + 2.5
        n = int(dur * SR)
        pad = np.zeros(n)
        for nt in ch:
            pad += saw_pad(midi(nt), dur, harm=9)
        e = np.minimum(tvec(n) / 2.2, 1) * np.clip((dur - tvec(n)) / 2.5, 0, 1)
        pad = lowpass(pad, 900) * e * .16
        place(m, pad, at, 1.0, pan=0.0)
        place(m, np.roll(pad, int(.012 * SR)), at, .6, pan=.5)
        at += seg; k += 1
    # pulso grave (corazón) — desde el inicio, suave
    kick_n = int(.5 * SR); tk = tvec(kick_n)
    kick = np.sin(2 * np.pi * (46 + 70 * np.exp(-tk * 22)) * tk) * np.exp(-tk * 7)
    b = 0.0; i = 0
    while b < TOTAL:
        g = .5 if i % 2 == 0 else .28
        place(m, kick, b, g * (0.6 + .4 * min(b / 10, 1)))
        b += beat; i += 1
    # arpegio campanas con eco, desde 3.3 s
    arp = [57, 64, 69, 72, 69, 64, 60, 67]
    chord_roots = [0, -4, -7, -5]
    a = 3.3; q = 0
    while a < TOTAL - 0.8:
        bar = int((a / seg)) % 4
        note = arp[q % 8] + chord_roots[bar]
        pan = .5 * np.sin(q * .9)
        x = bell(midi(note + 12 * (q % 3 == 0)), 1.8)
        lvl = .17 * (0.6 + .4 * min((a - 3.3) / 8, 1))
        if a > TOTAL - 4.3: lvl *= 1.15
        place(m, x, a, lvl, pan)
        place(m, x, a + beat * .75, lvl * .45, -pan)
        place(m, x, a + beat * 1.5, lvl * .2, pan)
        a += beat / 2; q += 1
    # riser hacia marca y hacia final
    return m


SFX_T = {
    "whoosh": [s[2] for s in SCENES[:-1]],
}


def whoosh(dur=.9, up=True, f0=300, f1=5000):
    n = int(dur * SR); t = tvec(n)
    x = rng.randn(n); X = np.fft.rfft(x); f = np.fft.rfftfreq(n, 1 / SR)
    # barrido: filtrar en tiempo por segmentos
    out = np.zeros(n); segs = 24; L = n // segs
    for s in range(segs):
        k = s / segs; k2 = k if up else 1 - k
        fc = f0 * (f1 / f0) ** k2
        xs = rng.randn(L); Xs = np.fft.rfft(xs); fs = np.fft.rfftfreq(L, 1 / SR)
        h = np.exp(-((np.log(fs + 1) - np.log(fc)) ** 2) / .5)
        out[s * L:(s + 1) * L] = np.fft.irfft(Xs * h, L)
    out = out / (np.abs(out).max() + 1e-9)
    e = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 2
    return out[:n] * e


def hit(dur=1.6, f=48):
    n = int(dur * SR); t = tvec(n)
    x = np.sin(2 * np.pi * (f + 90 * np.exp(-t * 18)) * t) * np.exp(-t * 2.6)
    x += lowpass(rng.randn(n), 1800) * np.exp(-t * 14) * .6
    return x


def tick(f=2400, dur=.05):
    n = int(dur * SR); t = tvec(n)
    return (np.sin(2 * np.pi * f * t) + .5 * rng.randn(n) * .3) * np.exp(-t * 90)


def chirp(f0, f1, dur, shape=6):
    n = int(dur * SR); t = tvec(n); k = t / dur
    ph = 2 * np.pi * (f0 * t + (f1 - f0) * (dur * (k ** 2) / 2))
    return np.sin(ph) * np.exp(-k * shape) * np.minimum(t / .004, 1)


def shimmer(dur, f=1200):
    n = int(dur * SR); t = tvec(n); x = np.zeros(n)
    for j in range(9):
        fj = f * (1 + j * .5) * (1 + .003 * j)
        x += np.sin(2 * np.pi * fj * t + j) * (.5 + .5 * np.sin(2 * np.pi * (3 + j) * t)) / (1 + j * .4)
    return x * np.sin(np.pi * t / dur) ** 2


def sfx():
    s = np.zeros((N, 2))
    A = 0.0
    # transiciones
    for i, tb in enumerate(SFX_T["whoosh"]):
        place(s, whoosh(.9, up=(i % 2 == 0)), tb - .6, .5)
        place(s, hit(1.4, 44 + 3 * i), tb - .25, .28)
    # gancho
    place(s, hit(1.8, 52), 0.0, .9)
    place(s, chirp(2600, 90, .5, 5), 0.0, .35)
    place(s, hit(1.2, 60), 0.9, .55)
    place(s, whoosh(1.5, True, 200, 7000), 1.7, .6)
    for tt in np.arange(3.5, 10.4, .43):
        nt = [69, 72, 76, 79, 81][int(rng.randint(5))] + 12
        place(s, bell(midi(nt), .9), tt, .10, pan=rng.uniform(-.7, .7))
    for k in range(18):   # relleno de información (cuadrados)
        place(s, bell(midi([76, 79, 83, 88][k % 4]), .6), 7.1 + k * .17, .13, pan=rng.uniform(-.8, .8))
    # escena 2 (abs = 10.95 + local)
    o = 10.95
    place(s, tick(1800, .09) * 1.2, o + 2.95, .8)        # obturador
    place(s, tick(900, .12), o + 2.99, .6)
    place(s, chirp(1800, 120, .35, 5), o + 3.95, .4)     # zap del "no"
    place(s, shimmer(.9, 700), o + 4.85, .25)             # se desintegra
    for q in range(10):
        place(s, bell(midi(76 + [0, 3, 7, 10][q % 4]), .5), o + 6.6 + q * .24, .09, pan=-.5 + q * .1)
    place(s, whoosh(1.4, True, 150, 3000), o + 6.4, .35)
    place(s, shimmer(1.8, 600), o + 7.6, .35)
    place(s, hit(1.5, 50), o + 7.6, .5)
    # escena 3
    o = 20.0
    for q in range(3):
        place(s, bell(midi(69 + q * 4), 1.2), o + .6 + q * .18, .22)
    place(s, shimmer(1.1, 1500), o + 1.45, .3)
    # escena 4
    o = 24.7
    place(s, bell(midi(81), 1.0), o + 1.75, .28, -.5); place(s, bell(midi(84), 1.0), o + 2.2, .28, .5)
    place(s, chirp(300, 2400, .35, 3), o + 3.95, .3)
    place(s, chirp(1400, 90, .3, 7), o + 4.95, .5)       # el punto desaparece
    place(s, tick(150, .25) * 2, o + 5.15, .4)
    place(s, chirp(900, 200, .25, 4), o + 5.4, .3)
    place(s, whoosh(2.5, True, 200, 6000), o + 7.7, .35)
    place(s, shimmer(1.6, 1000), o + 10.15, .4)
    # escena 5 (flicker)
    o = 35.85
    t0 = 5.0
    while t0 < 9.2:
        for b in (0.5, 1.18):
            if t0 + b < 9.2:
                place(s, tick(3000, .04), o + t0 + b, .35); place(s, tick(1500, .04), o + t0 + b + .18, .25)
        t0 += 1.36
    place(s, whoosh(.8, True, 400, 6000), o + 9.2, .45)
    place(s, bell(midi(88), 1.4), o + 9.75, .3)
    place(s, bell(midi(93), 1.6), o + 10.2, .35)
    place(s, shimmer(.9, 1800), o + 10.2, .3)
    # escena 6
    o = 47.0
    for q in range(5):
        place(s, bell(midi(81), 1.4) * .6, o + 4.55 + q * .6, .12, pan=(-1) ** q * .5)
    place(s, whoosh(2.0, True, 150, 5000), o + 5.5, .5)
    place(s, hit(2.4, 46), o + 7.0, .9)
    place(s, shimmer(2.0, 900), o + 7.05, .5)
    # marca
    o = 55.25
    place(s, chirp(200, 3000, .6, 2), o + .1, .25)
    for q, nt in enumerate((81, 85, 88, 93)):
        place(s, bell(midi(nt), 2.4), o + .5 + q * .09, .32, pan=-.4 + q * .27)
    for q in range(7):
        place(s, tick(4000 + q * 500, .03), o + .5 + q * .07, .12)
    return s


def write_wav(path, x):
    x = np.clip(x, -1, 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype("<i2").tobytes())


if __name__ == "__main__":
    out = sys.argv[1]
    m = music(); m = reverb(m, 2.6, .35)
    m = m / np.abs(m).max() * .9
    write_wav(out + "/music.wav", m)
    s = sfx(); s = reverb(s, 1.6, .25); s = s / (np.abs(s).max() + 1e-9) * .9
    write_wav(out + "/sfx.wav", s)
    print("ok", m.shape)
