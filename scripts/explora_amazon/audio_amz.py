"""Música continua + efectos del documental de Amazon, y mezcla con ducking suave (mismo método que el vídeo de Elon corregido)."""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "explora_musk")))
import numpy as np
import audio_m as A
from audio_m import *
import remix_audio as R

TOT = 77.5
A.TOTAL = TOT; A.N = int((TOT + 1.0) * A.SR); N = A.N
R.TOT = TOT
BOUNDS = [14.85, 27.55, 37.5, 45.8, 57.13, 65.25]


def clicks_(s, t0, t1, rate, gain=.14, f=2200):
    t = t0
    while t < t1:
        place(s, tick(f * rng.uniform(.8, 1.3), .03), t, gain * rng.uniform(.5, 1.0), pan=rng.uniform(-.5, .5)); t += rng.exponential(1 / rate)


def sfx():
    s = np.zeros((N, 2))
    for i, tb in enumerate(BOUNDS):
        place(s, whoosh(.9, up=(i % 2 == 0)), tb - .6, .45); place(s, hit(1.2, 44 + 3 * i), tb - .25, .22)
    # gancho
    place(s, hit(1.6, 50), 0.0, .5)
    for i in range(10):                                   # compras: cada producto sale del móvil
        tt = .25 + i * .30
        place(s, tick(1500, .05), tt, .28); place(s, bell(midi([84, 88, 91, 96][i % 4]), .45), tt + .08, .10, pan=rng.uniform(-.7, .7))
    place(s, whoosh(.7, False, 200, 6000), 2.85, .45)    # rebobinado al pasado
    for k in range(8): place(s, tick(900 - 40 * k, .04), 3.0 + k * .06, .25)
    clicks_(s, 3.7, 7.0, 8, .13)
    for n in range(7): place(s, bell(midi(91 + [0, 4, 7][n % 3]), .6), 7.0 + 1.2 / 1.7 + n * .6, .13, pan=rng.uniform(-.6, .6))   # pedidos
    place(s, chirp(300, 160, .5, 4), 9.3, .18); place(s, chirp(300, 160, .5, 4), 9.9, .15)                              # escépticos
    place(s, hit(1.4, 48), 11.2, .45); place(s, whoosh(1.6, True, 150, 5000), 11.6, .35)
    # 2 idea
    o = 14.85
    clicks_(s, o + .2, o + 2.2, 9, .13); place(s, hit(.5, 80), o + 3.7, .28)
    for k in range(6): place(s, hit(.22, 85), o + 3.6 + k * .28, .07)                    # pasos al irse
    place(s, rumble(2.4, 40, 300) * .10, o + 5.15, 1.0)                                  # motor del coche
    for k in range(10): place(s, bell(midi(88 + [0, 3, 7, 10][k % 4]), .5), o + 6.4 + k * .12, .10, pan=-.6 + k * .13)
    clicks_(s, o + 7.9, o + 12.4, 8, .12)
    for k in range(4): place(s, hit(.3, 90), o + 9.5 + k * .45, .12)
    place(s, whoosh(1.0, True, 200, 3000), o + 10.8, .3)
    # 3 nacimiento
    o = 27.55
    place(s, shimmer(1.4, 1500), o + 1.7, .25)
    for k in range(5): place(s, bell(midi(88 + k * 2), .8), o + 1.7 + k * .08, .16)
    for k in range(6): place(s, tick(260, .25) * 2, o + 2.2 + k * .5, .0)
    for k in range(4): place(s, chirp(1200, 400, .3, 5), o + 4.4 + k * 1.5, .07); place(s, hit(.18, 100), o + 4.7 + k * 1.5, .12)   # cinta y cajas
    # 4 catálogo
    o = 37.5
    for k in range(9): place(s, tick(1800 + 100 * k, .05), o + 1.4 + k * .21, .2)
    place(s, shimmer(1.8, 1100), o + 1.4, .22)
    clicks_(s, o + 4.4, o + 8.0, 7, .12)
    for k in range(5): place(s, bell(midi(91), .5), o + 5.2 + k * .6, .08)
    # 5 imperio
    o = 45.8
    place(s, rumble(4.4, 40, 500) * .12, o, 1.0)
    for k in range(10): place(s, chirp(900, 1500, .1, 4), o + .5 + k * .4, .07, pan=rng.uniform(-.8, .8))
    place(s, whoosh(.8, True, 200, 5000), o + 4.3, .4); place(s, bell(midi(96), 1.4), o + 5.7, .16)           # Prime / llegada
    clicks_(s, o + 6.7, o + 11.2, 12, .09, 3000)
    for k in range(12): place(s, bell(midi(96 + [0, 3, 7][k % 3]), .4), o + 7.0 + k * .3, .07, pan=rng.uniform(-.8, .8))
    # 6 gigante
    o = 57.13
    place(s, whoosh(2.4, True, 150, 5000), o + .2, .35); place(s, shimmer(1.6, 900), o + 2.2, .2)
    for k in range(6): place(s, bell(midi(88 + 2 * k), .8), o + 3.1 + k * .25, .12, pan=-.7 + k * .25)
    # 7 cierre
    o = 65.25
    place(s, rumble(3.4, 40, 400) * .12, o + 1.2, 1.0); place(s, whoosh(2.0, True, 200, 4000), o + 3.0, .25)
    place(s, shimmer(2.0, 700), o + 5.6, .25)
    for q, nt in enumerate((81, 85, 88, 93)): place(s, bell(midi(nt), 2.4), o + 7.0 + q * .09, .28, pan=-.4 + q * .27)
    return s


if __name__ == "__main__":
    out = sys.argv[1]
    s = sfx(); s = reverb(s, 1.6, .25); s = s / (np.abs(s).max() + 1e-9) * .9
    write_wav(out + "/sfx.wav", s); print("sfx ok", s.shape)
