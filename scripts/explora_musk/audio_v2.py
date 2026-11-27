"""Música + efectos v2: la música/efectos originales se desplazan +OFF y se añaden los efectos de la nueva intro."""
import sys, numpy as np
import audio_m as A
from audio_m import *

OFF = 5.22
TOT = 76.3
A.TOTAL = TOT; A.N = int((TOT + 1.0) * A.SR)
N = A.N


def intro_sfx():
    s = np.zeros((N, 2))
    place(s, hit(2.0, 46), 0.0, .75)                                   # golpe grave de apertura
    place(s, chirp(2400, 120, .5, 5), 0.0, .25)
    for tt in (0.55, 0.95, 1.3): place(s, tick(260, .25) * 2.5, tt, .45)  # pasos metálicos en la bóveda
    place(s, shimmer(1.6, 1500), 1.3, .30)                              # destello del oro
    for k in range(26): place(s, bell(midi([88, 91, 95, 100][k % 4]), .5), .6 + k * .07, .10, pan=rng.uniform(-.8, .8))   # monedas
    # un millón por día: "pop" por día
    t = 2.2
    while t < 4.0:
        place(s, tick(1400, .06), t, .30); place(s, chirp(900, 2600, .15, 3), t + .06, .18, pan=rng.uniform(-.6, .6))
        t += .30
    place(s, whoosh(.5, True, 300, 4500), 2.0, .35)
    # calendario: clics cada vez más rápidos
    t = 4.0; rate = 12
    while t < 5.55:
        place(s, tick(1800 + 800 * (t - 4.0), .035), t, .28); rate = 12 + 34 * (t - 4.0) / 1.55; t += 1 / rate
    place(s, whoosh(1.4, True, 200, 6000), 4.0, .30)
    place(s, bell(midi(81), 1.8), 5.42, .22); place(s, hit(.9, 70), 5.42, .24)
    # "todavía no..." retorno a la bóveda: destello suave
    place(s, shimmer(1.8, 900), 7.9, .16)
    # historia del hombre más rico: golpe + ascenso de cohete
    place(s, hit(1.6, 52), 8.4, .55)
    ig = rumble(2.6, 30, 900); ig *= np.linspace(.1, 1, len(ig)) ** 1.4
    place(s, ig * .40, 11.2, 1.0)
    place(s, whoosh(1.4, True, 150, 5000), 11.5, .35)
    for (cb) in (2.2, 4.0, 5.7, 8.3): place(s, whoosh(.4, True, 400, 3000), cb - .25, .30)
    return s


if __name__ == "__main__":
    out = sys.argv[1]
    m = music(); m = reverb(m, 2.6, .35); m = m / np.abs(m).max() * .9
    write_wav(out + "/music.wav", m)
    A.HOOK_SFX = False
    old = A.sfx()                      # efectos originales (sin los del gancho antiguo)
    s = np.zeros((N, 2)); sh = int(OFF * A.SR)
    s[sh:] += old[:N - sh]
    s += intro_sfx()
    s = reverb(s, 1.6, .25); s = s / (np.abs(s).max() + 1e-9) * .9
    write_wav(out + "/sfx.wav", s)
    print("ok", m.shape, s.shape)
