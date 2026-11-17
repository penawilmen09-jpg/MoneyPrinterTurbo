"""Banda sonora original (suspenso instrumental) + efectos ambientales sincronizados. Sin voces."""
import math, wave
import numpy as np

SR = 44100
DUR = 60.0
N = int(SR * DUR)
rng = np.random.RandomState(2024)
L = np.zeros(N, np.float32)
R = np.zeros(N, np.float32)
MUS_L = np.zeros(N, np.float32)
MUS_R = np.zeros(N, np.float32)
T = np.arange(N) / SR
HIT = 58.3


def sm(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def curve(pts):
    xs, ys = zip(*pts)
    return np.interp(T, xs, ys).astype(np.float32)


def bp(x, lo, hi):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    m = np.ones_like(f)
    if lo:
        m *= 1 / (1 + (lo / np.maximum(f, 1e-3)) ** 4)
    if hi:
        m *= 1 / (1 + (f / hi) ** 4)
    return np.fft.irfft(X * m, len(x)).astype(np.float32)


def noise(n):
    return rng.randn(n).astype(np.float32)


def place(snd, t, gain=1.0, pan=0.0, bus=None):
    i = int(t * SR)
    if i < 0 or i >= N:
        return
    snd = snd[: N - i]
    gl = gain * math.cos((pan + 1) * math.pi / 4)
    gr = gain * math.sin((pan + 1) * math.pi / 4)
    (bus[0] if bus else L)[i:i + len(snd)] += snd * gl
    (bus[1] if bus else R)[i:i + len(snd)] += snd * gr


def tt(d):
    return np.arange(int(d * SR)) / SR


def step(weight=1.0, bright=0.5):
    d = 0.22
    t = tt(d)
    n = bp(noise(len(t)), 120, 500 + 2500 * bright) * np.exp(-t * 38)
    th = np.sin(2 * math.pi * (70 + 40 * np.exp(-t * 30)) * t) * np.exp(-t * 30)
    return (n * 0.9 + th * 0.9 * weight).astype(np.float32)


def clang(f=330, d=1.6, hard=1.0):
    t = tt(d)
    out = np.zeros(len(t), np.float32)
    for k, (r, a) in enumerate(((1, 1), (2.76, .6), (5.4, .4), (8.93, .25), (13.3, .12))):
        out += a * np.sin(2 * math.pi * f * r * t + k) * np.exp(-t * (3 + 2.2 * k))
    out += bp(noise(len(t)), 2000, 9000) * np.exp(-t * 90) * hard
    return out * 0.5


def tap(f=900, d=0.18):
    t = tt(d)
    return (np.sin(2 * math.pi * f * t) * np.exp(-t * 40) + bp(noise(len(t)), 1500, 7000) * np.exp(-t * 120) * 0.5).astype(np.float32)


def creak(d=1.2, f0=180, f1=260, vib=14, seed=0):
    t = tt(d)
    r = np.random.RandomState(seed)
    jit = np.cumsum(r.randn(len(t))) * 0.0006
    f = np.linspace(f0, f1, len(t)) * (1 + 0.08 * np.sin(2 * math.pi * vib * t) + jit)
    ph = 2 * math.pi * np.cumsum(f) / SR
    s = sum(np.sin(ph * h) / h for h in range(1, 12))
    s = bp(s.astype(np.float32), 500, 2600)
    return (s * np.sin(math.pi * t / d) ** 1.5 * 0.6).astype(np.float32)


def scrape(d=0.45):
    t = tt(d)
    n = bp(noise(len(t)), 1800, 7500)
    chop = (0.55 + 0.45 * np.sin(2 * math.pi * 38 * t + np.cumsum(rng.randn(len(t))) * 0.01)) ** 2
    return (n * chop * np.sin(math.pi * t / d) ** 0.7 * 0.7).astype(np.float32)


def splash(d=0.5, c=1.0):
    t = tt(d)
    return (bp(noise(len(t)), 500, 5500) * (1 - np.exp(-t * 90)) * np.exp(-t * 7) * c).astype(np.float32)


def cloth(d=0.5, c=1.0):
    t = tt(d)
    return (bp(noise(len(t)), 250, 2600) * np.sin(math.pi * t / d) ** 2 * 0.5 * c).astype(np.float32)


def hissn(d, lo=3000, hi=9500):
    t = tt(d)
    return (bp(noise(len(t)), lo, hi) * np.sin(math.pi * t / d) ** 1.2 * 0.4).astype(np.float32)


def crash(d=2.2, c=1.0):
    t = tt(d)
    n = bp(noise(len(t)), 60, 2200)
    env = (1 - np.exp(-t * 7)) * np.exp(-t * 2.0)
    return (n * env * 1.4 * c + bp(noise(len(t)), 2500, 8000) * env * 0.25).astype(np.float32)


def boom(d=3.2):
    t = tt(d)
    s = np.sin(2 * math.pi * (30 + 60 * np.exp(-t * 3)) * np.cumsum(np.ones(len(t))) / SR * 0 + 2 * math.pi * 0)
    ph = 2 * math.pi * np.cumsum(28 + 90 * np.exp(-t * 4)) / SR
    s = np.sin(ph) * np.exp(-t * 1.3)
    n = bp(noise(len(t)), 40, 3000) * np.exp(-t * 4.5)
    metal = sum(np.sin(2 * math.pi * 118 * r * t) * np.exp(-t * (2 + k)) for k, r in enumerate((1, 1.51, 2.37, 3.9))) * 0.25
    return (s * 1.2 + n * 0.9 + metal).astype(np.float32)


def bell(d=0.8, f=760):
    t = tt(d)
    s = sum(a * np.sin(2 * math.pi * f * r * t) * np.exp(-t * (2.0 + k * 1.5)) for k, (r, a) in enumerate(((1, 1), (2.32, .7), (3.1, .5), (4.5, .3))))
    return (s * 0.5).astype(np.float32)


# ============================================================ AMBIENTES CONTINUOS
def ambience():
    w1, w2 = bp(noise(N), 130, 1100), bp(noise(N), 130, 1100)
    lfo = 0.55 + 0.45 * np.sin(2 * math.pi * T / 9.0 + 1) * np.sin(2 * math.pi * T / 4.3)
    whistle = bp(noise(N), 500, 900) * (0.4 + 0.6 * np.sin(2 * math.pi * T / 6.0) ** 2)
    g = curve([(0, .95), (5, 1.0), (7.0, .25), (14, .06), (28, .10), (35, .35), (36, 1.0), (44, 1.15), (52, 1.0), (54, .22),
               (56.4, .22), (56.9, .9), (58.2, 1.0), (58.3, 0), (60, 0)])
    return (w1 * lfo * g * 0.55 + whistle * g * 0.2), (w2 * lfo * g * 0.55 + whistle * g * 0.2)


def sea_bed():
    s1, s2 = bp(noise(N), 50, 1600), bp(noise(N), 50, 1600)
    sw = (0.5 + 0.5 * np.sin(2 * math.pi * T / 6.6)) ** 2.0 * 0.8 + 0.2
    g = curve([(0, .8), (7, .7), (8, 0.03), (35, 0.03), (36, .9), (44, .95), (48, 0.7), (52, .55), (54, .35), (56.5, .8), (58.2, .85), (58.3, 0), (60, 0)])
    return s1 * sw * g * 0.5, s2 * sw * g * 0.5


def room_tone():
    h = np.sin(2 * math.pi * 55 * T) * 0.4 + np.sin(2 * math.pi * 110 * T) * 0.2 + bp(noise(N), 80, 400) * 0.6
    g = curve([(6, 0), (8, .16), (27.5, .16), (28.5, 0.05), (35, .12), (36, 0), (60, 0)])
    return (h * g).astype(np.float32)


# ============================================================ MÚSICA
def midi(n):
    return 440 * 2 ** ((n - 69) / 12)


def pad(notes, t0, d, gain, bright=7):
    t = tt(d + 2.5)
    out = np.zeros(len(t), np.float32)
    env = sm(t / 2.2) * np.where(t < d, 1, sm(1 - (t - d) / 2.5))
    for n in notes:
        f = midi(n)
        for det in (-0.12, 0.0, 0.1):
            ph = 2 * math.pi * f * (1 + det * 0.006) * t + det * 5
            out += sum(np.sin(ph * h) / h ** 1.15 for h in range(1, bright)) * (1 + 0.15 * np.sin(t * (0.6 + det)))
    out *= env * gain / 3
    place(out.astype(np.float32), t0, 1.0, 0, (MUS_L, MUS_R))
    place(out.astype(np.float32)[::-1] * 0 + out.astype(np.float32), t0, 0, 0, (MUS_L, MUS_R))


def tremolo(f, t0, d, gain, rate=13.0):
    t = tt(d + 1.0)
    env = sm(t / 1.4) * np.where(t < d, 1, sm(1 - (t - d) / 1.0))
    ph = 2 * math.pi * f * t
    s = (np.sin(ph) + 0.5 * np.sin(2 * ph) + 0.3 * np.sin(3 * ph) + 0.15 * np.sin(4 * ph)) * (0.55 + 0.45 * np.sin(2 * math.pi * rate * t))
    place((s * env * gain).astype(np.float32), t0, 1.0, -0.3, (MUS_L, MUS_R))
    place((s * env * gain * 0.7).astype(np.float32), t0 + 0.012, 1.0, 0.4, (MUS_L, MUS_R))


def thud(t0, gain):
    t = tt(0.6)
    ph = 2 * math.pi * np.cumsum(46 + 70 * np.exp(-t * 18)) / SR
    s = np.sin(ph) * np.exp(-t * 7) + bp(noise(len(t)), 60, 500) * np.exp(-t * 28) * 0.4
    place((s * gain).astype(np.float32), t0, 1.0, 0, (MUS_L, MUS_R))


def music():
    # drone D1/A1 creciente
    drone = (np.sin(2 * math.pi * 36.71 * T) + 0.5 * np.sin(2 * math.pi * 73.42 * T + 1) + 0.35 * np.sin(2 * math.pi * 55.0 * T))
    drone *= curve([(0, 0.0), (3, 0.45), (30, 0.55), (52, 0.8), (58.3, 0.9), (58.35, 0), (60, 0)]) * (0.8 + 0.2 * np.sin(2 * math.pi * T / 5.0))
    MUS_L[:] += drone * 0.5
    MUS_R[:] += drone * 0.5
    # acordes (Dm, Bb, Gm, A) cada 4 s, volumen creciente
    prog = [(50, 53, 57), (46, 50, 53), (43, 46, 50), (45, 49, 52)]
    t0, k = 1.0, 0
    while t0 < 58.3:
        notes = prog[k % 4]
        g = 0.07 + 0.22 * sm((t0 - 4) / 44)
        pad([n for n in notes] + [notes[0] + 12], t0, 4.2, g, bright=6 if t0 < 30 else 9)
        t0 += 4.0
        k += 1
    # latido / pulso creciente
    t = 14.0
    while t < 58.0:
        bpm = 46 + 90 * sm((t - 14) / 40)
        g = 0.18 + 0.5 * sm((t - 14) / 36)
        thud(t, g)
        if t > 36:
            thud(t + 60 / bpm * 0.5, g * 0.55)
        t += 60 / bpm
    # cuerdas con trémolo (agudos) desde la escena 5
    for i, (tf, f, d, g) in enumerate([(28, midi(69), 5, .08), (32, midi(72), 5, .09), (36, midi(74), 4.5, .11), (40, midi(77), 4.5, .12),
                                      (44, midi(81), 4.2, .16), (47, midi(84), 4.2, .17), (50, midi(86), 3.5, .19), (52.5, midi(87.2), 2.5, .2),
                                      (54.5, midi(89), 2.6, .22), (56.5, midi(93), 1.9, .24)]):
        tremolo(f, tf, d, g, 10 + i)
        tremolo(f / 2, tf, d, g * 0.7, 10 + i)
    # riser (ruido filtrado ascendente 40-52 y 52-58)
    for (a, b) in ((38, 52), (52, 58.3)):
        t = tt(b - a)
        n = noise(len(t))
        fc = np.linspace(400, 5000, len(t))
        sm_n = bp(n, 300, 4500)
        MUS_L[int(a * SR):int(a * SR) + len(t)] += sm_n * (np.linspace(0, 1, len(t)) ** 2.5) * 0.18
        MUS_R[int(a * SR):int(a * SR) + len(t)] += bp(noise(len(t)), 300, 4500) * (np.linspace(0, 1, len(t)) ** 2.5) * 0.18
    # golpe dramático final
    b = boom(3.4)
    place(b, HIT, 1.5, 0, (MUS_L, MUS_R))
    place(clang(92, 3.0, 0.4), HIT, 0.5, 0, (MUS_L, MUS_R))


def reverb(x, rt=2.4, seed=1):
    r = np.random.RandomState(seed)
    n = int(rt * SR)
    ir = r.randn(n) * np.exp(-np.arange(n) / SR * 3.0 / rt * 2.3)
    ir[:int(0.012 * SR)] *= 0.1
    size = 1 << int(math.ceil(math.log2(len(x) + n)))
    y = np.fft.irfft(np.fft.rfft(x, size) * np.fft.rfft(ir, size), size)[:len(x)]
    return y.astype(np.float32) * 0.06


# ============================================================ EVENTOS
def steps_at(times, gain=0.5, pan=0.0, weight=1.0, bright=0.5):
    for tm in times:
        place(step(weight, bright), tm, gain, pan)


def walk_strikes(t_from, t_to, f_phase, offset=0.0):
    """Instantes de apoyo del pie para ciclo phase=f(t)+offset (apoyo en pi/2 + k pi)."""
    ts = np.arange(t_from, t_to, 0.001)
    ph = np.array([f_phase(x) for x in ts]) + offset
    k = np.floor((ph - math.pi / 2) / math.pi)
    idx = np.where(np.diff(k) > 0)[0]
    return [float(ts[i]) for i in idx]


def seg_(x, a, b):
    y = min(1, max(0, (x - a) / (b - a)))
    return y * y * (3 - 2 * y)


def events():
    # ---------- Escena 1 (0-7)
    for ti in (0.9, 2.7, 4.3, 5.9):
        place(crash(2.4, 1.0), ti - 0.15, 0.55, -0.2)
        place(splash(0.9, 0.7), ti + 0.05, 0.5, 0.3)
    place(creak(2.2, 70, 55, 3, 1), 2.4, 0.3, 0.0)           # bocina / metal lejano
    place(clang(220, 2.5, 0.2), 4.9, 0.14, 0.6)
    # ---------- Escena 2 (7-14)
    steps_at([7 + 0.5 + 1.1 * i for i in range(5)], 0.12, -0.6, 0.6, 0.3)       # pasos lejanos
    place(creak(1.0, 210, 150, 9, 2), 7 + 2.2, 0.4, -0.3)       # metal crujiendo al agacharse
    place(cloth(0.8), 7 + 2.4, 0.4, -0.2)
    for i in range(4):
        place(tap(700 + 60 * i), 7 + 3.9 + i * 0.57, 0.5, -0.5)  # golpecitos en la rejilla
    place(creak(1.3, 160, 240, 11, 3), 7 + 4.8, 0.45, -0.5)
    gs = walk_strikes(4.4, 6.9, lambda x: x * 6.2)
    steps_at([7 + x for x in gs], 0.42, 0.55, 1.0, 0.5)
    for i in range(10):
        place(cloth(0.9, 0.4), 7 + 0.3 + i * 0.7, 0.07, 0.0)     # respiración / ambiente
    # ---------- Escena 3 (14-21)
    for c, pan in enumerate((-0.6, 0.0, 0.6)):
        i = 0
        while True:
            tm = 14 + 0.45 + c * 0.17 * 3 + i * 0.5
            if tm > 20.8:
                break
            place(scrape(0.38), tm, 0.28, pan)
            place(tap(1100 + 200 * c, 0.1), tm + 0.4, 0.1, pan)
            i += 1
        for i in range(8):
            t0 = 0.3 + i * 0.83 + c * 0.27
            for tl in (t0 + 0.62, t0 + 0.84):
                if 0 < tl < 7:
                    place(tap(2300 + 400 * ((i + c) % 3), 0.08), 14 + tl, 0.12, pan)
    for i in range(6):
        place(hissn(1.0, 2000, 7000), 14 + 0.8 + i * 1.1, 0.06, 0.0)    # polvo cayendo
    place(step(0.5, 0.2), 14 + 4.6, 0.25, 0.7)
    # ---------- Escena 4 (21-28)
    for i in range(3):
        place(cloth(0.8, 0.8), 21 + 0.2 + i * 1.14, 0.35, -0.3)     # pincel
    for i in range(5):
        place(tap(260, 0.1), 21 + 0.9 + i * 0.6, 0.18, 0.2)         # palmaditas de pegado
    place(cloth(0.7, 1.0), 21 + 3.5, 0.5, -0.3)                      # cabeza colocada
    place(tap(180, 0.25), 21 + 4.35, 0.5, -0.4)
    place(cloth(0.9, 1.3), 21 + 4.5, 0.6, -0.2)                      # manta
    place(cloth(0.6, 1.0), 21 + 5.0, 0.35, 0.1)
    place(tap(2000, 0.08), 21 + 5.2, 0.4, 0.6)                        # linterna click
    steps_at([21 + 5.0 + 0.55 * i for i in range(4)], 0.35, 0.6, 0.9, 0.4)
    # ---------- Escena 5 (28-36)
    ph = lambda x, off: 560 * seg_(x, 0, 5.0) * 0.036
    for off, pan in ((0.0, -0.4), (1.6, 0.0), (3.1, 0.4)):
        st = walk_strikes(0.05, 5.1, lambda x: ph(x, 0), off)
        steps_at([28 + x for x in st], 0.2, pan, 0.8, 0.3)
    place(clang(180, 2.0, 0.6), 28 + 1.2, 0.55, 0.5)
    place(clang(250, 1.8, 0.6), 28 + 3.1, 0.45, -0.5)
    place(creak(1.5, 130, 90, 5, 5), 28 + 2.2, 0.4, 0.4)
    place(hissn(3.0), 28 + 1.0, 0.25, 0.3)
    place(hissn(3.5), 28 + 4.0, 0.2, 0.3)
    for i in range(6):
        place(clang(540 + 40 * (i % 2), 0.9, 1.0), 28 + 5.2 + i * 0.52 * (1 if True else 1), 0.32, 0.1)   # peldaños
    place(creak(2.0, 150, 300, 8, 6), 28 + 7.0, 0.55, 0.0)            # escotilla
    for tm in (3.0, 4.2, 5.1):
        place(tap(2400, 0.1), 28 + tm, 0.1, 0.5)                       # goteo
    # ---------- Escena 6 (36-44)
    st = walk_strikes(0.0, 2.3, lambda x: x * 5.2, 0.0)
    steps_at([36 + x for x in st], 0.22, 0.0, 0.9, 0.2)
    for i in range(14):
        tm = 2.6 + i * 0.9
        if tm > 6.3:
            break
        place(hissn(0.5, 800, 6000), 36 + tm, 0.35, -0.4)            # bombeo
        place(creak(0.4, 200, 260, 20, 10 + i), 36 + tm + 0.3, 0.25, 0.1)
        place(cloth(0.5, 0.8), 36 + tm + 0.1, 0.25, 0.4)
    for tm in (1.6, 3.8, 5.6, 7.0):
        place(splash(0.8, 0.5), 36 + tm, 0.35, 0.2)
    place(tap(150, 0.4), 36 + 6.4, 0.3, 0.0)
    # ---------- Escena 7 (44-52)
    for i in range(0, 4):
        tm = 0.7 + i * 1.21
        place(splash(0.6, 0.9), 44 + tm, 0.5, -0.5)
        place(splash(0.6, 0.9), 44 + tm + 0.6, 0.5, 0.5)
    place(crash(2.5, 0.7), 44 + 1.5, 0.35, 0.0)
    place(crash(2.5, 0.7), 44 + 3.0, 0.3, 0.0)
    for tm in (4.8, 5.6, 6.4, 7.2):
        place(hissn(1.0, 600, 4000), 44 + tm, 0.12, 0.0)
    # ---------- Escena 8 (52-60)
    t = 52.0
    while t < HIT - 0.05:
        place(bell(0.5, 760), t, 0.25 + 0.12 * (1 if t > 54.4 else 0), 0.0)
        place(bell(0.5, 1015), t + 0.07, 0.15, 0.1)
        t += 0.11
    place(cloth(0.5, 1.2), 52 + 2.25, 0.35, -0.5)
    steps_at([52 + 2.1 + 0.5 * i for i in range(2)], 0.3, 0.7, 1.0, 0.5)
    place(cloth(0.25, 1.8), 52 + 3.22, 0.9, -0.2)                   # tirón de la manta
    place(tap(120, 0.4), 52 + 3.45, 0.9, -0.5)                       # golpe de la cabeza al suelo
    place(tap(180, 0.3), 52 + 3.75, 0.55, -0.6)
    place(tap(200, 0.25), 52 + 3.95, 0.3, -0.6)
    rs = walk_strikes(3.7, 4.7, lambda x: x * 11)
    steps_at([52 + x for x in rs], 0.6, 0.0, 1.1, 0.7)
    place(clang(160, 2.0, 1.0), 52 + 2.9, 0.4, 0.5)
    for i, tm in enumerate((4.7, 5.2, 5.7)):
        place(splash(0.9, 0.3), 52 + tm, 0.2, 0.0)


def build():
    events()
    mus_l, mus_r = MUS_L.copy(), MUS_R.copy()
    music()
    ml, mr = MUS_L.copy(), MUS_R.copy()
    al, ar = ambience()
    sl, sr_ = sea_bed()
    rt = room_tone()
    wet_l, wet_r = reverb(ml, 2.6, 1), reverb(mr, 2.6, 2)
    # ambiente/música balanceados
    gm = curve([(0, 0), (1, .5), (60, .9)])
    outl = L * 0.9 + al * 0.55 + sl * 0.5 + rt * 0.5 + (ml + wet_l * 2.0) * 0.55
    outr = R * 0.9 + ar * 0.55 + sr_ * 0.5 + rt * 0.5 + (mr + wet_r * 2.0) * 0.55
    # silencio breve tras el golpe: todo muere
    i0 = int((HIT + 0.9) * SR)
    cut = np.ones(N, np.float32)
    cut[i0:int((HIT + 1.1) * SR)] = np.linspace(1, 0, int((HIT + 1.1) * SR) - i0)
    cut[int((HIT + 1.1) * SR):] = 0
    fade_in = np.clip(T / 0.6, 0, 1)
    outl, outr = outl * cut * fade_in, outr * cut * fade_in
    pk = max(np.abs(outl).max(), np.abs(outr).max())
    g = 0.89 / pk
    outl, outr = np.tanh(outl * g * 1.15) / np.tanh(1.15) * 0.97, np.tanh(outr * g * 1.15) / np.tanh(1.15) * 0.97
    st = np.stack([outl, outr], 1)
    pcm = (np.clip(st, -1, 1) * 32767).astype(np.int16)
    with wave.open("output/audio.wav", "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print("audio ok  pico:", round(float(np.abs(pcm).max()) / 32767, 3), " RMS dB:", round(20 * math.log10(np.sqrt((st ** 2).mean()) + 1e-9), 1))


if __name__ == "__main__":
    build()
