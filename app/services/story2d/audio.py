"""Música de suspenso, efectos de sonido y mezcla, todo sintetizado en local."""
from __future__ import annotations

import math
import subprocess
import wave

import numpy as np

SR = 44100
SFX_REF = 0.23   # RMS lineal por unidad de ganancia (g=0.3 ≈ -23 dBFS)
_rng = np.random.default_rng(7)


def _t(d):
    return np.arange(int(d * SR)) / SR


def _env(n, a, r, curve=2.0):
    e = np.ones(n)
    na, nr = max(1, int(a * SR)), max(1, int(r * SR))
    e[:na] = np.linspace(0, 1, na) ** curve if na < n else e[:na]
    e[-nr:] *= np.linspace(1, 0, nr) ** curve
    return e


def _lp(x, fc):
    """Filtro paso-bajo de un polo (rápido, vectorizado por bloques con FFT)."""
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    return np.fft.irfft(X / (1 + (f / fc) ** 2), len(x))


def _hp(x, fc):
    return x - _lp(x, fc)


def _bp(x, lo, hi):
    return _lp(_hp(x, lo), hi)


# ======================================================================
# EFECTOS DE SONIDO (mono, normalizados a pico 1.0; la ganancia se da al mezclar)
# ======================================================================
def _norm(x):
    return x / (np.max(np.abs(x)) + 1e-9)


def sfx_bell(freqs=(1568, 2349, 3136), d=1.0, decays=(3.5, 5, 7)):
    t = _t(d)
    x = sum(np.sin(2 * np.pi * f * t) * np.exp(-t * dc) * (0.6 ** i)
            for i, (f, dc) in enumerate(zip(freqs, decays)))
    return _norm(x)


def sfx_cash():
    n = _t(0.5)
    click = _bp(_rng.standard_normal(len(n)), 800, 5000) * np.exp(-n * 60)
    ring = np.zeros(int(1.2 * SR))
    b1 = sfx_bell((2093, 4186, 6270), 1.0, (5, 8, 11))
    ring[:len(b1)] += b1
    b2 = sfx_bell((2637, 5274), 1.0, (5, 9)) * 0.9
    o = int(0.09 * SR)
    ring[o:o + len(b2)] += b2
    out = np.zeros(len(ring))
    out[:len(click)] += click * 0.9
    out += ring * 0.8
    thunk = np.sin(2 * np.pi * 110 * _t(0.2)) * np.exp(-_t(0.2) * 25)
    out[:len(thunk)] += thunk * 0.6
    return _norm(out)


def sfx_drawer():
    t = _t(0.45)
    slide = _bp(_rng.standard_normal(len(t)), 300, 2500) * np.exp(-t * 7) * 0.7
    thud = np.sin(2 * np.pi * 90 * t) * np.exp(-t * 18)
    return _norm(slide + thud)


def sfx_beep(f=1760, d=0.09, n=1):
    t = _t(d)
    one = np.sin(2 * np.pi * f * t) * _env(len(t), 0.004, 0.01, 1)
    gap = np.zeros(int(0.05 * SR))
    return _norm(np.concatenate([np.concatenate([one, gap]) for _ in range(n)]))


def sfx_error():
    t = _t(0.18)
    one = (np.sign(np.sin(2 * np.pi * 150 * t)) * 0.5 + np.sin(2 * np.pi * 300 * t) * 0.5)
    one = _lp(one, 1800) * _env(len(t), 0.005, 0.03, 1)
    return _norm(np.concatenate([one, np.zeros(int(0.07 * SR)), one]))


def sfx_whoosh(d=0.55, up=True):
    t = _t(d)
    nz = _rng.standard_normal(len(t))
    out = np.zeros(len(t))
    n_b = 12
    for i in range(n_b):
        fc = 300 * (1.45 ** i)
        band = _bp(nz, fc * 0.7, fc * 1.4)
        peak = (i / n_b) if up else 1 - i / n_b
        w = np.exp(-((t / d - (0.25 + 0.5 * peak)) ** 2) / 0.04)
        out += band * w
    return _norm(out * np.sin(np.pi * np.clip(t / d, 0, 1)) ** 0.7)


def sfx_paper():
    t = _t(0.28)
    x = _bp(_rng.standard_normal(len(t)), 1500, 7000)
    x *= (np.abs(_rng.standard_normal(len(t))) > 0.8) * 1.0 + 0.25
    return _norm(x * np.exp(-t * 9))


def sfx_stamp():
    t = _t(0.35)
    th = np.sin(2 * np.pi * 70 * t * (1 + 0.5 * np.exp(-t * 30))) * np.exp(-t * 16)
    sl = _bp(_rng.standard_normal(len(t)), 400, 4000) * np.exp(-t * 55) * 0.6
    return _norm(th + sl)


def sfx_coin(f=1900):
    t = _t(0.7)
    x = sum(np.sin(2 * np.pi * f * m * t) * np.exp(-t * d) * a
            for m, d, a in ((1, 6, 1), (2.76, 10, 0.5), (5.4, 18, 0.25)))
    tick = _bp(_rng.standard_normal(len(t)), 2000, 9000) * np.exp(-t * 120) * 0.4
    return _norm(x + tick)


def sfx_click():
    t = _t(0.06)
    return _norm(_bp(_rng.standard_normal(len(t)), 1200, 6000) * np.exp(-t * 110))


def sfx_pop():
    t = _t(0.16)
    f = 380 + 700 * np.exp(-t * 30)
    return _norm(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 22))


def sfx_ding(f=988):
    return sfx_bell((f, f * 2.0, f * 3.0), 0.9, (4, 6, 9))


def sfx_chime_door():
    a, b = sfx_ding(784), sfx_ding(988)
    out = np.zeros(int(1.3 * SR))
    out[:len(a)] += a
    o = int(0.28 * SR)
    out[o:o + len(b)] += b
    return _norm(out)


def sfx_rewind():
    d = 1.1
    t = _t(d)
    f = 3200 - 2400 * (t / d) ** 0.7
    tone = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.25
    ticks = np.sin(2 * np.pi * 36 * t) > 0.9
    nz = _bp(_rng.standard_normal(len(t)), 1500, 6000) * 0.6 * (1 + ticks)
    return _norm(_lp(tone + nz, 6000) * _env(len(t), 0.05, 0.12, 1))


def sfx_static(d=0.5):
    t = _t(d)
    x = _bp(_rng.standard_normal(len(t)), 400, 9000)
    x *= (1 + 0.8 * np.sign(np.sin(2 * np.pi * 55 * t)))
    return _norm(x * _env(len(t), 0.01, 0.12, 1))


def sfx_boom(d=1.6):
    t = _t(d)
    f = 65 * (1 + 1.2 * np.exp(-t * 7))
    th = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.6)
    air = _lp(_rng.standard_normal(len(t)), 900) * np.exp(-t * 5) * 0.5
    return _norm(th + air)


def sfx_reveal():
    """Golpe dramático + brillo ascendente."""
    boom = sfx_boom(1.8)
    t = _t(1.8)
    sh = sum(np.sin(2 * np.pi * f * t) * np.exp(-t * d) for f, d in
             ((880, 1.8), (1318, 2.2), (1760, 2.8)))
    sh = sh * np.clip(t / 0.25, 0, 1) * 0.25
    return _norm(boom * 0.9 + sh)


def sfx_sting():
    """Acorde disonante corto (sorpresa)."""
    t = _t(1.2)
    x = sum(np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t)
            for f in (233, 247, 349, 370)) * np.exp(-t * 3.5)
    return _norm(_lp(x, 2500) * _env(len(t), 0.01, 0.4, 1))


def sfx_lock():
    t = _t(0.4)
    a = _bp(_rng.standard_normal(len(t)), 1500, 6000) * np.exp(-t * 90)
    b = np.zeros(len(t))
    o = int(0.12 * SR)
    b[o:] = (np.sin(2 * np.pi * 220 * t[:-o]) * np.exp(-t[:-o] * 35)
             + _bp(_rng.standard_normal(len(t) - o), 600, 4000) * np.exp(-t[:-o] * 60))
    return _norm(a + b)


def sfx_tick(f=1200):
    t = _t(0.05)
    return _norm(np.sin(2 * np.pi * f * t) * np.exp(-t * 90) + _bp(_rng.standard_normal(len(t)), 2000, 8000) * np.exp(-t * 200) * 0.3)


def sfx_scan():
    t = _t(0.5)
    f = 400 + 2200 * (t / 0.5)
    return _norm(np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(len(t), 0.03, 0.1, 1) * 0.6)


def sfx_footstep():
    t = _t(0.12)
    return _norm(_lp(_rng.standard_normal(len(t)), 700) * np.exp(-t * 40) + np.sin(2 * np.pi * 70 * t) * np.exp(-t * 35))


def sfx_riser(d=2.0):
    t = _t(d)
    nz = _bp(_rng.standard_normal(len(t)), 400, 6000)
    f = 120 + 1500 * (t / d) ** 2
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR)
    return _norm((nz * 0.5 + tone * 0.5) * (t / d) ** 1.8 * _env(len(t), 0.2, 0.03, 1))


def sfx_tada():
    """Cierre positivo y suave (controles nuevos)."""
    n1, n2, n3 = sfx_ding(659), sfx_ding(784), sfx_ding(1047)
    out = np.zeros(int(1.6 * SR))
    for i, n in enumerate((n1, n2, n3)):
        o = int(i * 0.13 * SR)
        out[o:o + len(n)] += n
    return _norm(out)


SFX = {
    "cash": sfx_cash, "drawer": sfx_drawer, "beep": sfx_beep, "beep2": lambda: sfx_beep(2100, 0.07, 2),
    "error": sfx_error, "whoosh": sfx_whoosh, "whoosh_dn": lambda: sfx_whoosh(0.5, False),
    "paper": sfx_paper, "stamp": sfx_stamp, "coin": sfx_coin, "coin2": lambda: sfx_coin(2400),
    "click": sfx_click, "pop": sfx_pop, "ding": sfx_ding, "door": sfx_chime_door,
    "rewind": sfx_rewind, "static": sfx_static, "boom": sfx_boom, "reveal": sfx_reveal,
    "sting": sfx_sting, "lock": sfx_lock, "tick": sfx_tick, "scan": sfx_scan,
    "step": sfx_footstep, "riser": sfx_riser, "tada": sfx_tada,
}
_cache: dict = {}


def get_sfx(name):
    if name not in _cache:
        _cache[name] = SFX[name]().astype(np.float32)
    return _cache[name]


# ======================================================================
# MÚSICA DE SUSPENSO (original, sintetizada)
# ======================================================================
def _note(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def _pad(freq, d, bright=1.0):
    t = _t(d)
    x = np.zeros(len(t))
    for det in (-0.004, 0.0, 0.004):
        for k in range(1, 7):
            x += np.sin(2 * np.pi * freq * (1 + det) * k * t + k) / (k ** (1.6 / bright))
    return x / 4.0


def _reverb(x, wet=0.28, rt=2.2):
    n = int(rt * SR)
    ir = _rng.standard_normal(n) * np.exp(-np.arange(n) / SR * 3.2)
    ir = _lp(ir, 3500)
    ir /= np.sqrt(np.sum(ir ** 2))
    N = len(x) + n
    y = np.fft.irfft(np.fft.rfft(x, N) * np.fft.rfft(ir, N), N)[:len(x)]
    return x * (1 - wet) + y * wet


def make_music(total):
    """Pista estéreo ~total s.  Estructura emocional:
       0-10 gancho (drone + latido) · 10-27 investigación (arpegio suave) ·
       27-46 tensión creciente · 46-fin resolución cálida."""
    n = int(total * SR)
    L = np.zeros(n)
    R = np.zeros(n)

    def add(sig, t0, gain=1.0, pan=0.0):
        i0 = int(t0 * SR)
        if i0 >= n:
            return
        seg = sig[: n - i0]
        L[i0:i0 + len(seg)] += seg * gain * (1 - max(0, pan))
        R[i0:i0 + len(seg)] += seg * gain * (1 + min(0, pan))

    # secciones de acordes (midi): (inicio, fin, notas, brillo)
    A, F, D, E, Cc, G = (45, 57, 64), (41, 57, 60), (50, 57, 65), (40, 56, 59), (48, 55, 64), (43, 59, 62)
    prog = [
        (0, 10, A, 0.8), (10, 18, F, 1.0), (18, 27, A, 1.0), (27, 34, D, 1.2),
        (34, 40, E, 1.3), (40, 46, D, 1.3), (46, 52, Cc, 1.0), (52, 58, G, 0.9),
        (58, 200, Cc, 0.8),
    ]
    for a, b, notes, br in prog:
        if a >= total:
            continue
        d = min(b, total) - a + 1.6
        for m in notes:
            p = _pad(_note(m), d, br) * _env(int(d * SR), 1.6, 1.8, 1.5)
            add(p, a - 0.8 if a > 0 else 0, 0.55 / len(notes) * 1.6, pan=0.15 * ((m % 3) - 1))
        # sub-bajo
        sub = np.sin(2 * np.pi * _note(notes[0] - 12) * _t(d)) * _env(int(d * SR), 1.2, 1.5, 1.5)
        add(sub, a - 0.6 if a > 0 else 0, 0.35)

    # latido (lub-dub) suave, más presente en el gancho y la tensión
    def heart():
        t = _t(0.4)
        lub = np.sin(2 * np.pi * 52 * t * (1 + 0.6 * np.exp(-t * 25))) * np.exp(-t * 18)
        out = np.zeros(len(t))
        out += lub
        o = int(0.2 * SR)
        out[o:] += 0.6 * lub[:-o]
        return out

    h = heart()
    tt = 0.5
    while tt < total - 4:
        gain = 0.55 if (tt < 10 or 27 <= tt < 46) else 0.0
        if gain:
            period = 1.6 if tt < 27 else 1.6 - 0.7 * min(1, (tt - 27) / 17)
            add(h, tt, gain)
            tt += max(0.9, period)
        else:
            tt += 0.5

    # arpegio de pizzicato (investigación)
    arp = {10: [57, 60, 64, 60], 18: [57, 60, 64, 67]}
    tt = 11.0
    pat = [57, 64, 60, 67, 64, 60, 57, 55]
    k = 0
    while tt < 27:
        t_ = _t(0.9)
        f = _note(pat[k % len(pat)] + 12)
        pl = (np.sin(2 * np.pi * f * t_) + 0.4 * np.sin(2 * np.pi * 2 * f * t_)) * np.exp(-t_ * 6)
        add(pl, tt, 0.16, pan=((k % 4) - 1.5) * 0.25)
        tt += 0.833
        k += 1

    # reloj / tictac en la parte de tensión
    tt = 28.0
    while tt < 45:
        add(sfx_tick(1500 if int((tt - 28) / 0.5) % 2 else 1100).astype(float), tt, 0.1)
        tt += 0.5

    # riser antes del descubrimiento
    r = sfx_riser(5.0).astype(float)
    add(r, 33.0 if total > 40 else 0, 0.08)

    # resolución: melodía simple y cálida
    mel = [(47.0, 76), (48.6, 72), (50.2, 74), (52.0, 79), (54.4, 76), (56.5, 72), (58.5, 69)]
    for t0, m in mel:
        if t0 >= total:
            continue
        d = 2.0
        t_ = _t(d)
        f = _note(m)
        bell = (np.sin(2 * np.pi * f * t_) + 0.3 * np.sin(2 * np.pi * 2 * f * t_)) * np.exp(-t_ * 1.6) * _env(len(t_), 0.02, 0.5, 1)
        add(bell, t0, 0.17, pan=0.1)

    st = np.stack([L, R], 1)
    st[:, 0] = _reverb(st[:, 0])
    st[:, 1] = _reverb(st[:, 1])
    st *= _env(n, 1.0, 2.5, 1.5)[:, None]
    return (st / (np.max(np.abs(st)) + 1e-9)).astype(np.float32)


# ======================================================================
# MEZCLA
# ======================================================================
def db(x):
    return 20 * math.log10(max(x, 1e-9))


def rms(x):
    return float(np.sqrt(np.mean(np.square(x)) + 1e-12))


def voice_activity(voice, win=0.03):
    """Envolvente suavizada (0..1) de actividad de voz para el ducking."""
    n = int(win * SR)
    pad = len(voice) // n * n
    e = np.sqrt(np.mean(voice[:pad].reshape(-1, n) ** 2, axis=1))
    act = (e > 0.012).astype(float)
    k = np.ones(int(0.25 / win)) / int(0.25 / win)
    act = np.maximum(np.convolve(act, k, "same"), act)
    env = np.repeat(act, n)
    env = np.pad(env, (0, len(voice) - len(env)), mode="edge")
    # suavizado ataque/liberación
    a = np.exp(-1 / (0.06 * SR))
    r = np.exp(-1 / (0.45 * SR))
    out = np.empty_like(env)
    s = 0.0
    step = 64
    for i in range(0, len(env), step):
        v = env[i]
        s = (a if v > s else r) * s + (1 - (a if v > s else r)) * v
        out[i:i + step] = s
    return out


def voice_priority(bus, voice, margin_db, frame=0.02, floor=0.04):
    """Limita `bus` (n,2) para que, mientras hay habla sostenida, quede al menos
    `margin_db` por debajo de la voz. En las pausas no actúa (nivel intacto)."""
    fr = int(frame * SR)
    nn = len(voice) // fr * fr
    k = np.ones(5) / 5
    vr = np.convolve(np.sqrt(np.mean(voice[:nn].reshape(-1, fr) ** 2, axis=1)), k, "same")
    br = np.convolve(np.sqrt(np.mean(bus[:nn].mean(axis=1).reshape(-1, fr) ** 2, axis=1)), k, "same")
    lim = vr * 10 ** (-margin_db / 20)
    g = np.where((vr > floor) & (br > lim), lim / np.maximum(br, 1e-9), 1.0)
    # suavizado: ataque rápido, liberación lenta
    out = np.empty_like(g)
    cur = 1.0
    for i, v in enumerate(g):
        cur = v if v < cur else cur + (v - cur) * 0.25
        out[i] = cur
    gain = np.repeat(out, fr)
    gain = np.pad(gain, (0, len(voice) - len(gain)), constant_values=1.0)
    return (bus * gain[:, None]).astype(np.float32)


def mix_track(total, voice_events, sfx_events, music, music_gain=0.20, duck=0.42,
              voice_gain_db=0.0):
    """Devuelve dict con voz, música, sfx y mezcla final (estéreo float32).

    voice_events: [(t, np.ndarray mono)]; sfx_events: [(t, nombre, ganancia_lineal, pan)].
    La música baja (ducking) mientras habla la voz; los SFX NO se reducen.
    """
    n = int(total * SR)
    voice = np.zeros(n, dtype=np.float32)
    for t0, a in voice_events:
        i = int(round(t0 * SR))
        voice[i:i + len(a)] += a[: n - i]
    # normalización de la voz: pico -2 dBFS
    pk = np.max(np.abs(voice))
    voice *= (10 ** (-2 / 20)) / pk * 10 ** (voice_gain_db / 20)

    act = voice_activity(voice)
    mus = music[:n].copy() if len(music) >= n else np.pad(music, ((0, n - len(music)), (0, 0)))
    gain_env = (1.0 - (1.0 - duck) * act).astype(np.float32)
    mus = mus * gain_env[:, None] * music_gain

    sfx = np.zeros((n, 2), dtype=np.float32)
    placed = []
    # energía de voz por trama de 20 ms para colocar cada efecto en un hueco
    fr = int(0.02 * SR)
    ve = np.sqrt(np.mean(voice[: n // fr * fr].reshape(-1, fr) ** 2, axis=1))

    def overlap(ts, dur):
        i0, i1 = int(ts / 0.02), int((ts + dur) / 0.02)
        return float(np.sum(ve[max(0, i0):i1] ** 2)) if i1 > 0 else 0.0

    adjusted = []
    for t0, name, g, pan in sfx_events:
        dur = min(len(get_sfx(name)) / SR, 0.5)
        best, best_c = t0, overlap(t0, dur)
        if best_c > 0.02:
            for off in np.arange(-0.35, 0.351, 0.05):
                c = overlap(t0 + off, dur) + 0.003 * abs(off) / 0.35
                if c < best_c - 1e-9:
                    best, best_c = t0 + off, c
        adjusted.append((max(0.0, best), name, g, pan))
    sfx_events = adjusted
    for t0, name, g, pan in sfx_events:
        a = get_sfx(name)
        i = int(round(t0 * SR))
        if i >= n:
            continue
        seg = a[: n - i]
        # nivelación por RMS real del efecto (primeros 0.5 s); g=0.3 ≈ -23 dBFS RMS
        ref = a[: int(min(len(a), 0.5 * SR))]
        scale = (g * SFX_REF) / max(rms(ref), 1e-6)
        # prioridad a la voz: si el efecto cae sobre palabras, queda ≥ 7 dB por debajo
        vwin = voice[i:i + len(ref)]
        vr = rms(vwin) if len(vwin) else 0.0
        if vr > 0.02:
            scale = min(scale, vr * 10 ** (-7 / 20) / max(rms(ref), 1e-6))
        seg = seg * scale
        lg, rg = (1 - max(0, pan)), (1 + min(0, pan))
        sfx[i:i + len(seg), 0] += seg * lg
        sfx[i:i + len(seg), 1] += seg * rg
        placed.append((t0, name, g, len(seg) / SR, db(rms(ref * scale)), db(vr) if vr > 0.02 else None))

    # prioridad a la voz: música ≥ 15 dB y efectos ≥ 8,5 dB por debajo cuando hay habla
    mus = voice_priority(mus, voice, 15.0)
    sfx = voice_priority(sfx, voice, 8.5)
    v2 = np.stack([voice, voice], 1)
    mix = v2 + mus + sfx
    # limitador suave (nunca recorta)
    pk = np.max(np.abs(mix))
    if pk > 0.89:
        mix = np.tanh(mix / 0.89 * 0.9) * 0.89 / np.tanh(0.9) * (1 if pk < 1.6 else 0.9)
        mix = mix / max(1.0, np.max(np.abs(mix)) / 0.89)
    return dict(voice=voice, music=mus, sfx=sfx, mix=mix.astype(np.float32),
                placed=placed, activity=act)


def write_wav(path, stereo):
    pcm = (np.clip(stereo, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def qa_report(parts, beats_timeline, narr):
    """Comprobaciones: frases completas, música/SFX vs voz, recorte."""
    issues, info = [], {}
    voice, mus, sfx, mix = parts["voice"], parts["music"], parts["sfx"], parts["mix"]
    # 1) cada frase completa: palabra final dentro del audio + cola silenciosa
    for bid, st, en in beats_timeline:
        d = narr[bid]
        if d["last_word_end"] + 0.12 > d["dur"]:
            issues.append(f"{bid}: cola <120 ms tras la última palabra (posible corte)")
        tail = d["audio"][-int(0.02 * SR):]
        if rms(tail) > 0.01:
            issues.append(f"{bid}: el audio termina con energía alta ({db(rms(tail)):.1f} dB)")
    # 2) música y SFX frente a la voz, en ventanas con voz
    act = parts["activity"] > 0.5
    v_rms = rms(voice[act])
    m_rms = rms(mus[act].mean(axis=1))
    info["voz_rms_db"] = round(db(v_rms), 1)
    info["musica_bajo_voz_db"] = round(db(v_rms) - db(m_rms), 1)
    if db(v_rms) - db(m_rms) < 14:
        issues.append("la música queda a menos de 14 dB de la voz")
    worst = None
    for t0, name, g, d, s_db, v_db in parts["placed"]:
        if v_db is None:
            continue  # cae en un hueco: no se solapa con palabras
        margin = v_db - s_db
        if worst is None or margin < worst[0]:
            worst = (margin, name, t0)
        if margin < 5.5:
            issues.append(f"SFX '{name}' en {t0:.1f}s a solo {margin:.1f} dB bajo la voz")
    info["sfx_margen_min_db"] = None if worst is None else (round(worst[0], 1), worst[1], round(worst[2], 1))
    # bus completo de SFX/música frente a la voz, tramas de 100 ms con habla sostenida
    fr = int(0.1 * SR)
    nn = len(voice) // fr * fr
    vr_ = np.sqrt(np.mean(voice[:nn].reshape(-1, fr) ** 2, axis=1))
    sr_ = np.sqrt(np.mean(sfx[:nn].mean(axis=1).reshape(-1, fr) ** 2, axis=1))
    mr_ = np.sqrt(np.mean(mus[:nn].mean(axis=1).reshape(-1, fr) ** 2, axis=1))
    on = vr_ > 0.06
    with np.errstate(divide="ignore"):
        d_sfx = 20 * np.log10(vr_[on] / np.maximum(sr_[on], 1e-6))
        d_mus = 20 * np.log10(vr_[on] / np.maximum(mr_[on], 1e-6))
    info["bus_sfx_bajo_voz_db_min"] = round(float(d_sfx.min()), 1)
    info["tramas_sfx_<5dB"] = int(np.sum(d_sfx < 5))
    info["bus_musica_bajo_voz_db_min"] = round(float(d_mus.min()), 1)
    if np.sum(d_sfx < 4) > 0:
        issues.append(f"el bus de SFX supera -4 dB bajo la voz en {int(np.sum(d_sfx < 4))} tramas de 100 ms")
    if d_mus.min() < 13:
        issues.append("la música se acerca a menos de 13 dB de la voz en alguna trama de 100 ms")
    info["pico_mezcla_db"] = round(db(float(np.max(np.abs(mix)))), 1)
    if np.max(np.abs(mix)) > 0.98:
        issues.append("la mezcla recorta")
    return issues, info
