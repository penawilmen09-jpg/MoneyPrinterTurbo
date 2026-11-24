"""Efectos de sonido sintetizados (numpy): 100% originales, sin licencias."""
import numpy as np

SR = 44100


def _env(n, a=.005, r=.3):
    t = np.arange(n) / SR
    return np.minimum(t / a, 1) * np.exp(-t / r)


def pop():
    t = np.arange(int(.14 * SR)) / SR
    f = 700 - 3500 * t
    return .5 * np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(len(t), .002, .05)


def click():
    t = np.arange(int(.08 * SR)) / SR
    return .5 * np.sin(2 * np.pi * 1800 * t) * _env(len(t), .001, .015)


def ding():
    t = np.arange(int(.9 * SR)) / SR
    return .35 * (np.sin(2 * np.pi * 1318 * t) + .5 * np.sin(2 * np.pi * 2637 * t)) * _env(len(t), .003, .25)


def zap():
    rng = np.random.default_rng(5)
    n = int(.55 * SR)
    t = np.arange(n) / SR
    noise = rng.standard_normal(n)
    crack = noise * (rng.random(n) > .93)               # chasquidos
    buzz = np.sign(np.sin(2 * np.pi * 120 * t)) * .25
    return .45 * np.clip(.5 * noise * np.exp(-t / .12) + crack * .8 + buzz * np.exp(-t / .3), -1, 1) * np.minimum(t / .003, 1)


def whoosh():
    rng = np.random.default_rng(9)
    n = int(.4 * SR)
    t = np.arange(n) / SR
    x = rng.standard_normal(n)
    k = np.cumsum(x) / SR * 600              # ruido filtrado (pasa-bajos tosco)
    x = x - np.convolve(x, np.ones(40) / 40, mode="same") * (1 - t / .4)
    env = np.sin(np.pi * t / .4) ** 2
    return .22 * x * env / (np.abs(x * env).max() + 1e-9)


BANK = dict(pop=pop, click=click, ding=ding, zap=zap, whoosh=whoosh)


def splash():
    rng = np.random.default_rng(3)
    n = int(.7 * SR); t = np.arange(n) / SR
    x = rng.standard_normal(n)
    x = np.convolve(x, np.ones(6) / 6, mode="same")
    return .6 * x * np.exp(-t / .16) * np.minimum(t / .004, 1)


def clank():
    t = np.arange(int(.6 * SR)) / SR
    return .5 * (np.sin(2 * np.pi * 310 * t) + .6 * np.sin(2 * np.pi * 523 * t) + .4 * np.sin(2 * np.pi * 811 * t)) * _env(len(t), .001, .14)


def horn():
    t = np.arange(int(1.3 * SR)) / SR
    x = np.sin(2 * np.pi * 110 * t) + .7 * np.sin(2 * np.pi * 165 * t) + .3 * np.sin(2 * np.pi * 220 * t)
    return .3 * x * np.minimum(t / .08, 1) * np.minimum((1.3 - t) / .25, 1)


def bubble():
    t = np.arange(int(.12 * SR)) / SR
    return .35 * np.sin(2 * np.pi * np.cumsum(500 + 3000 * t) / SR) * _env(len(t), .002, .04)


BANK.update(splash=splash, clank=clank, horn=horn, bubble=bubble)


def rotor(dur, rate=8.5):
    """Golpeteo grave y continuo de un rotor (estilizado)."""
    rng = np.random.default_rng(21)
    n_ = int(dur * SR); out = np.zeros(n_)
    step = int(SR / rate)
    for o in range(0, n_ - int(.09 * SR), step):
        m = int(.09 * SR); t = np.arange(m) / SR
        thump = np.sin(2 * np.pi * (70 - 200 * t) * t) * np.exp(-t / .03)
        whoosh = np.convolve(rng.standard_normal(m), np.ones(30) / 30, mode="same") * np.exp(-t / .04) * 2
        out[o:o + m] += .55 * thump + .25 * whoosh
    fade = np.minimum(np.arange(n_) / (.25 * SR), 1) * np.minimum((n_ - np.arange(n_)) / (.25 * SR), 1)
    return out * fade


def music(total):
    """Fondo suave original: acordes en pad + arpegio de campanitas (Am-F-C-G)."""
    n_ = int((total + .2) * SR); t = np.arange(n_) / SR
    chords = [(220.0, 261.63, 329.63), (174.61, 220.0, 261.63), (261.63, 329.63, 392.0), (196.0, 246.94, 293.66)]
    bar = 4.0
    out = np.zeros(n_)
    for i in range(int(total // bar) + 2):
        a, b = int(i * bar * SR), min(int((i + 1) * bar * SR + SR), n_)
        if a >= n_: break
        tt = np.arange(b - a) / SR
        env = np.minimum(tt / 1.2, 1) * np.minimum((bar + 1 - tt) / 1.2, 1)
        for f in chords[i % 4]:
            out[a:b] += env * (np.sin(2 * np.pi * f * tt) + .3 * np.sin(2 * np.pi * f * 2 * tt)) * .12
        for k, f in enumerate(chords[i % 4] * 2):                 # arpegio
            o = int((i * bar + k * .5) * SR)
            m = int(.9 * SR)
            if o + m < n_:
                tm = np.arange(m) / SR
                out[o:o + m] += .09 * np.sin(2 * np.pi * f * 2 * tm) * np.exp(-tm / .3) * np.minimum(tm / .005, 1)
    fade = np.minimum(t / 1.5, 1) * np.minimum((t[-1] - t) / 2.5, 1)
    return out * fade
