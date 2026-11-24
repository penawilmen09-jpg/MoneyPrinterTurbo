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
