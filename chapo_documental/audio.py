#!/usr/bin/env python3
"""Banda sonora 100 % sintetizada (sin voces): música instrumental de suspenso + efectos sincronizados.
Todo se genera con numpy/scipy (sin muestras externas, sin licencias). Salida: tmp/audio.wav (44.1 kHz estéreo, 60 s)."""
import json, math, os, sys
import numpy as np
from scipy import signal
from scipy.io import wavfile

SR = 44100; DUR = 60.0; N = int(SR * DUR)
HERE = os.path.dirname(os.path.abspath(__file__))
TL = json.load(open(os.path.join(HERE, 'web/timeline.json'), encoding='utf-8'))
rs = np.random.RandomState(7)
L = np.zeros(N); R = np.zeros(N)           # bus seco
RL = np.zeros(N); RR = np.zeros(N)         # bus de reverberación (send)

def t_(d): return np.arange(int(d * SR)) / SR
def noise(d): return rs.randn(int(d * SR))
def sos(x, kind, f, order=4):
    f = np.array(f, dtype=float) / (SR / 2); f = np.clip(f, 1e-4, .999)
    return signal.sosfilt(signal.butter(order, f, btype=kind, output='sos'), x)
def env_ad(n, a, d):  # ataque/decaimiento exponencial
    t = np.arange(n) / SR; e = np.exp(-t / max(d, 1e-4)); k = int(a * SR)
    if k > 0: e[:k] *= np.linspace(0, 1, k)
    return e
def fade(x, a=.01, b=.01):
    x = x.copy(); ka, kb = int(a * SR), int(b * SR)
    if ka: x[:ka] *= np.linspace(0, 1, ka)
    if kb: x[-kb:] *= np.linspace(1, 0, kb)
    return x
def put(sig, t0, gain=1.0, pan=0.0, send=0.0):
    i = int(t0 * SR)
    if i >= N or i + len(sig) <= 0: return
    a = max(0, -i); s = sig[a:]; i = max(0, i); n = min(len(s), N - i); s = s[:n]
    gl = gain * math.cos((pan + 1) * math.pi / 4); gr = gain * math.sin((pan + 1) * math.pi / 4)
    L[i:i + n] += s * gl; R[i:i + n] += s * gr
    if send: RL[i:i + n] += s * gl * send; RR[i:i + n] += s * gr * send

# ---------- síntesis de efectos ----------
def step(kind='concrete', w=1.0):
    d = .22 if kind != 'gravel' else .3; n = int(d * SR)
    if kind == 'gravel':
        x = sos(noise(d), 'bandpass', [1500, 7000], 2) * env_ad(n, .003, .07)
        x += sos(noise(d), 'bandpass', [900, 3000], 2) * env_ad(n, .06, .08) * .6
        x += np.sin(2 * np.pi * 70 * t_(d)) * env_ad(n, .002, .04) * .5
    else:
        x = sos(noise(d), 'lowpass', 1400 * w, 2) * env_ad(n, .001, .035) * 1.2
        x += np.sin(2 * np.pi * (85 + rs.rand() * 20) * t_(d)) * env_ad(n, .001, .06) * .9
        x += sos(noise(d), 'bandpass', [2500, 5000], 2) * env_ad(n, .001, .012) * .25
    return x * (.85 + .3 * rs.rand())
def metal_hit(d=1.2, base=420, ring=1.0):
    t = t_(d); x = np.zeros_like(t)
    for r, g, dec in [(1, 1, .5), (1.59, .8, .35), (2.13, .6, .28), (2.92, .5, .2), (3.61, .35, .15), (5.2, .2, .1)]:
        x += g * np.sin(2 * np.pi * base * r * t + rs.rand() * 6) * np.exp(-t / (dec * ring))
    x += sos(noise(d), 'bandpass', [1000, 6000], 2) * np.exp(-t / .01) * 1.5
    return x / np.max(np.abs(x))
def clunk(d=.5):
    t = t_(d); x = np.sin(2 * np.pi * 70 * t) * np.exp(-t / .12) + sos(noise(d), 'lowpass', 900, 2) * np.exp(-t / .03) * 1.4
    x += metal_hit(d, 240, .25) * .5
    return x / np.max(np.abs(x))
def keys(d=.9):
    x = np.zeros(int(d * SR))
    for _ in range(14):
        t0 = rs.rand() * (d - .15); f = 2800 + rs.rand() * 4200; dd = .08 + rs.rand() * .1
        tt = t_(dd); p = np.sin(2 * np.pi * f * tt) * np.exp(-tt / (dd / 3)) * (.4 + .6 * rs.rand())
        i = int(t0 * SR); x[i:i + len(p)] += p
    return x * (.6 + .4 * np.abs(np.sin(np.arange(len(x)) / SR * 9)))
def door_open(d=1.4):
    t = t_(d); sq = (sos(noise(d), 'bandpass', [400, 900], 2) * (np.sin(2 * np.pi * 5 * t) > 0) * np.minimum(1, t * 8) * np.exp(-t / .8)) * .5
    f = 180 + 120 * np.minimum(1, t / .9); sq += .25 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / .9) * np.minimum(1, t * 6)
    thud = np.zeros_like(t); k = int(.05 * SR); tt = t_(1.0); thud[:len(tt)] = 0
    return sq
def siren_wail(d, f0=620, f1=1450, per=3.2, tri=True):
    t = t_(d); ph = (t / per) % 1; m = 1 - np.abs(2 * ph - 1) if tri else ph
    f = f0 + (f1 - f0) * m; p = np.cumsum(f) / SR
    x = np.zeros_like(t)
    for k, g in [(1, 1), (2, .4), (3, .25), (5, .1)]: x += g * np.sin(2 * np.pi * k * p)
    return sos(x, 'bandpass', [400, 4800], 2) * .5
def klaxon(d, a=880, b=660, per=.55):
    t = t_(d); f = np.where((t / per) % 1 < .5, a, b); p = np.cumsum(f) / SR
    x = np.sign(np.sin(2 * np.pi * p)) * .5 + np.sin(2 * np.pi * p) * .5
    return sos(x, 'lowpass', 3200, 2) * .55
def engine(d, rate_fn, bright=1.0, noise_g=.15):
    t = t_(d); r = rate_fn(t); ph = np.cumsum(r) / SR; x = np.zeros_like(t)
    for k in range(1, 14): x += (1.0 / k ** 1.1) * np.sin(2 * np.pi * k * ph + k * .6)
    x *= (.6 + .4 * np.sin(2 * np.pi * ph) ** 2)
    x += noise_g * sos(noise(d), 'bandpass', [120, 1200], 2) * (.5 + .5 * np.sin(2 * np.pi * ph) ** 2)
    return sos(x, 'lowpass', 900 + 1500 * bright, 2)
def clicks(times_rate, d):  # traqueteo de rieles
    x = np.zeros(int(d * SR)); t = 0.0
    while t < d:
        r = times_rate(t); k = int(t * SR); n = int(.06 * SR)
        tt = np.arange(n) / SR; p = sos(noise(.06), 'bandpass', [700, 3500], 2) * np.exp(-tt / .008) + np.sin(2 * np.pi * 210 * tt) * np.exp(-tt / .03) * .6
        if k + n < len(x): x[k:k + n] += p * (.6 + .4 * rs.rand())
        t += 1.0 / max(r, 1)
    return x
def bark(d=.28, f=420):
    t = t_(d); ff = f * (1 - .35 * t / d); p = np.cumsum(ff) / SR
    x = (np.sin(2 * np.pi * p) + .6 * np.sin(4 * np.pi * p) + .4 * np.sin(6 * np.pi * p)) * np.exp(-t / .09) * np.minimum(1, t * 120)
    x += sos(noise(d), 'bandpass', [500, 2500], 2) * np.exp(-t / .06) * .5
    return sos(x, 'bandpass', [250, 3000], 2) * 1.2
def squelch(d=.12):
    x = sos(noise(d), 'bandpass', [900, 3800], 2) * env_ad(int(d * SR), .002, .05)
    return x * 1.4
def chirp(d=.18, f0=3000, f1=4600):
    t = t_(d); f = f0 + (f1 - f0) * (t / d); return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / d) ** 2
def boom(d=2.4, f=48):
    t = t_(d); ff = f * (1 + 1.4 * np.exp(-t / .12)); x = np.sin(2 * np.pi * np.cumsum(ff) / SR) * np.exp(-t / .7)
    x += sos(noise(d), 'lowpass', 220, 2) * np.exp(-t / .25) * .7
    return x * 1.4
def riser(d, f0=200, f1=5500):
    t = t_(d); x = noise(d); k = (t / d) ** 2; y = np.zeros_like(x)
    blocks = 24; bl = len(x) // blocks
    for b in range(blocks):
        fc = f0 + (f1 - f0) * (b / blocks) ** 2; seg = x[b * bl:(b + 1) * bl]
        y[b * bl:(b + 1) * bl] = sos(seg, 'bandpass', [fc * .8, fc * 1.3], 2)
    return y * k * 3.5

# ---------- ambientes y música ----------
def ambience(t0, t1, kind, g=1.0):
    d = t1 - t0; t = t_(d)
    if kind == 'night':
        w = sos(noise(d), 'bandpass', [200, 700], 2) * (.5 + .5 * np.sin(2 * np.pi * .13 * t + 1) ** 2)
        c = np.zeros_like(t); ph = (t * 5.2) % 1; c = sos(noise(d), 'bandpass', [4200, 5200], 2) * (ph < .35) * .4
        put(fade(w, .5, .5), t0, .5 * g, 0, .3); put(fade(c, .5, .5), t0, .05 * g, .4)
    elif kind == 'cell':
        v = sos(noise(d), 'bandpass', [90, 500], 2) * .6 + np.sin(2 * np.pi * 120 * t) * .12 + np.sin(2 * np.pi * 240 * t) * .05
        buzz = np.sin(2 * np.pi * 100 * t) * .05 * (1 + .6 * (np.sin(2 * np.pi * 11 * t) > .95))
        put(fade(v + buzz, .6, .6), t0, .35 * g, 0, .25)
    elif kind == 'tunnel':
        v = sos(noise(d), 'bandpass', [150, 900], 2) * .7 + np.sin(2 * np.pi * 95 * t) * .1
        put(fade(v, .6, .6), t0, .32 * g, 0, .6)
    elif kind == 'road':
        v = sos(noise(d), 'lowpass', 500, 2) * .8
        put(fade(v, .5, .5), t0, .28 * g, 0, .3)
ambience(0, 7.6, 'night', 1.0); ambience(6.8, 14.4, 'cell', 1.0); ambience(13.6, 22.4, 'cell', .9)
ambience(21.6, 30.4, 'cell', .5); ambience(29.6, 40.4, 'tunnel', 1.1); ambience(39.6, 48.4, 'night', 1.2)
ambience(47.6, 55.4, 'road', 1.0); ambience(54.6, 59.6, 'night', .7)

def pad(t0, d, notes, g=.12, cutoff=700, send=.7):
    t = t_(d); x = np.zeros_like(t)
    for f in notes:
        for det in (-.004, 0, .004):
            ph = np.cumsum(np.full_like(t, f * (1 + det))) / SR
            x += 2 * ((ph % 1) - .5) * .33
    lfo = .5 + .5 * np.sin(2 * np.pi * .09 * t + rs.rand() * 6)
    x = sos(x, 'lowpass', cutoff, 2) * (.7 + .3 * lfo)
    e = np.minimum(1, t / (d * .35)) * np.minimum(1, (d - t) / (d * .35))
    put(x * e, t0, g, 0, send)
hz = lambda m: 440 * 2 ** ((m - 69) / 12)
# progresión Am – F – Dm – E – Am – F – Dm – Esus – Am (7.5 s cada acorde)
chords = [[45, 52, 57, 60], [41, 48, 57, 60], [38, 50, 57, 62], [40, 52, 56, 59], [45, 52, 57, 60], [41, 48, 56, 60], [38, 50, 57, 62], [40, 52, 56, 62], [45, 52, 57, 60]]
vol = lambda tt: .07 + .12 * np.clip((tt - 14) / 20, 0, 1) + .08 * np.clip((tt - 40) / 12, 0, 1)
for i, c in enumerate(chords):
    t0 = i * 7.5 - 1.0; d = 9.0; cut = 500 + 90 * i
    pad(max(0, t0), d if t0 >= 0 else d + t0, [hz(m) for m in c], g=float(vol(t0 + 4.5)), cutoff=cut)
# subgrave continuo
t = t_(DUR); sub = np.sin(2 * np.pi * 55 * t) * (.5 + .5 * np.sin(2 * np.pi * .05 * t)) * (.16 + .1 * np.clip((t - 20) / 20, 0, 1)); put(fade(sub, 1, 2.2), 0, 1.0)
# ostinato pulsado (A menor) desde la escena 3, más presente en 5–7
seq = [45, 52, 57, 52, 48, 52, 55, 52]; beat = 60 / 96 / 2; k = 0; tt = 15.0
while tt < 58.2:
    m = seq[k % 8] + (0 if tt < 40 else 0)
    n = int(.5 * SR); tz = np.arange(n) / SR; f = hz(m)
    pl = sos(2 * ((np.cumsum(np.full(n, f)) / SR % 1) - .5) + np.sin(2 * np.pi * f * tz), 'lowpass', 1100 + 1800 * min(1, max(0, (tt - 22) / 20)), 2) * np.exp(-tz / .17)
    g = .05 + .09 * min(1, max(0, (tt - 22) / 14)) + .05 * (tt > 48)
    put(pl, tt, g, -.2 + .4 * ((k % 3) / 2), .55); tt += beat; k += 1
# latido grave en tensión (escenas 3–4 y 7)
for a, b in [(17.0, 22.0), (50.5, 55.0)]:
    x = a
    while x < b:
        for off, gg in ((0, 1.0), (.2, .7)): put(boom(.5, 52) * .5, x + off, .22 * gg, 0)
        x += .78 - .15 * (x - a) / (b - a)
# golpes de transición y subidas
for tb, gg in [(7, .5), (14, .5), (22.0, 1.0), (30, .6), (40, .55), (48, .55), (55, .7)]: put(boom(2.6), tb - .02, .5 * gg, 0, .6)
put(riser(3.0), 19.0, .12, 0, .5); put(riser(2.6), 45.4, .1, 0, .5); put(riser(4.2, 300, 6500), 51.0, .11, 0, .5)
put(boom(4.5, 44), 58.85, .9, 0, .7)

# ---------- escena por escena: efectos sincronizados con las acciones dibujadas ----------
walks = {w['id']: w for w in TL['walks']}
def steps(wid, kind='concrete', g=.5, w=1.0, pan=0.0, skip_start=False):
    wk = walks[wid]; per = 2 * (wk['t1'] - wk['t0']) / wk['N']
    for i in range(wk['N']):
        tt = wk['t0'] + i * per / 2 + .02; xp = (wk['x0'] + (wk['x1'] - wk['x0']) * i / wk['N'])
        put(step(kind, w) * 1.0, tt, g, pan, .25)
# E1: panorámica
put(metal_hit(1.5, 330, .8) * .5, 3.1, .09, .5, .8); put(clunk() * .6, 4.6, .12, -.4, .6)
for tt in (5.4, 6.2): put(squelch() * .6, tt, .09, .3);
put(squelch(.25) * .5, 6.5, .08, .3)
for k in range(4): put(klaxon(.0001) if False else np.sin(2 * np.pi * 120 * t_(.5)) * env_ad(int(.5 * SR), .05, .3), 0.5 + k * 1.7, .015, 0)   # zumbido lejano de reflectores
# E2: celda
steps('chapo_a', 'concrete', .55, 1.0, .1); steps('chapo_b', 'concrete', .55, 1.0, .1)
for tt in (10.35, 12.05): put(sos(noise(.1), 'bandpass', [1800, 3500], 2) * env_ad(int(.1 * SR), .001, .02) * 1.2, tt, .12, .6, .8)
put(clunk() * .8, 12.9, .16, -.8, .7); put(metal_hit(1.0, 300, .5) * .5, 12.9, .1, -.8, .8)
# E3: cámara y último registro
put(sos(noise(.5), 'bandpass', [500, 1800], 2) * env_ad(int(.5 * SR), .1, .15) * .7, 14.1, .14, .3)
for tt in (14.75, 15.0): put(np.sin(2 * np.pi * 2200 * t_(.09)) * env_ad(int(.09 * SR), .002, .03) * .8, tt, .1, 0)
steps('chapo_c', 'concrete', .5, .9, .2)
put(sos(noise(.3), 'bandpass', [800, 5000], 2) * env_ad(int(.3 * SR), .003, .08), 20.3, .22, 0)
for tt in (14.4, 15.4, 16.4, 17.4, 18.4, 19.4, 20.4, 21.4): put(np.sin(2 * np.pi * 2200 * t_(.05)) * env_ad(int(.05 * SR), .002, .02) * .5, tt, .035, 0, .1) if tt in (16.4, 18.4, 20.4) else None
# E4: llaves, cerradura, puerta, botas, linterna, alarma
put(keys(), 21.8, .22, -.6, .4); put(clunk(.5) * .8, 22.55, .3, -.5, .7); put(metal_hit(.5, 600, .2) * .5, 22.58, .1, -.5)
put(door_open(), 22.65, .25, -.55, .5); put(boom(1.2, 90) * .4, 23.25, .4, -.55, .5); put(metal_hit(1.6, 260, 1.2) * .6, 23.25, .15, -.55, .8)
steps('g1_a', 'concrete', .75, .7, -.3); steps('g2_a', 'concrete', .7, .7, -.2)
put(np.sin(2 * np.pi * 3000 * t_(.03)) * env_ad(int(.03 * SR), .001, .01) + sos(noise(.03), 'bandpass', [1500, 4000], 2) * .3, 24.4, .2, .2)
al = klaxon(5.0) * np.minimum(1, t_(5.0) / .2); put(al, 25.2, .13, 0, .5)
put(sos(noise(.3), 'bandpass', [800, 3800], 2) * env_ad(int(.3 * SR), .004, .1), 28.15, .14, .3); put(np.sin(2 * np.pi * 1700 * t_(.07)) * env_ad(int(.07 * SR), .002, .03), 28.9, .08, .3)
# E5: túnel
for tt in (30.45, 30.95, 31.4): put(metal_hit(.8, 520, .35), tt, .1, -.3, .9)
put(sos(noise(.7), 'bandpass', [1000, 4000], 2) * env_ad(int(.7 * SR), .15, .3), 30.6, .08, 0, .5)
fan = sos(noise(10), 'bandpass', [180, 1600], 2) * (.5 + .5 * np.sin(2 * np.pi * 38 * t_(10)) ** 2) + np.sin(2 * np.pi * 140 * t_(10)) * .15
put(fade(fan * np.exp(-t_(10) / 6), .5, 1.0), 30, .18, -.3, .5)
# moto: arranque 31.6, recorrido 32.7–37.0 (acelera), ralentí hasta 38.6
d_m = 38.6 - 31.6
def rate(t):
    r = np.full_like(t, 11.0); mv = (t > 1.1) & (t < 5.4); r = np.where(mv, 11 + 22 * np.clip((t - 1.1) / 1.8, 0, 1), r)
    r = np.where(t >= 5.4, 33 - 22 * np.clip((t - 5.4) / .9, 0, 1), r); r += 1.2 * np.sin(2 * np.pi * 3 * t); return r
eng = engine(d_m, rate, 1.0, .22) * np.minimum(1, t_(d_m) / .4) * np.minimum(1, (d_m - t_(d_m)) / .8)
put(eng, 31.6, .34, 0, .45)
put(sos(noise(.5), 'bandpass', [300, 2200], 2) * env_ad(int(.5 * SR), .02, .15) * 1.4, 31.5, .1, 0)   # encendido/arranque
rail = clicks(lambda t: 6 + 18 * np.clip((t - 1.1) / 1.8, 0, 1) if t < 5.4 else 3, d_m)
put(sos(rail, 'bandpass', [400, 4000], 2) * np.minimum(1, t_(d_m) / .6), 31.6, .22, 0, .5)
for tt in np.arange(32.3, 37.3, .24): put(sos(noise(.04), 'bandpass', [2500, 6000], 2) * env_ad(int(.04 * SR), .001, .01), tt, .04, 0, .3)
for tt in (33.1, 34.4, 35.5, 36.6): put(clunk(.3) * .3, tt, .06, -.2 + (tt - 33) / 8, .8)
put(boom(1.0, 60) * .3, 38.7, .15, 0)
# E6: salida (exterior nocturno)
for i in range(7): put(metal_hit(.5, 480 + (i % 2) * 60, .3), 41.4 + i * (2.9 / 7) + .08, .10 + .01 * i, .1, .7)
put(sos(noise(.5), 'bandpass', [150, 900], 2) * env_ad(int(.5 * SR), .1, .2), 44.0, .15, .1, .4)
steps('chapo_d', 'gravel', .55, 1.0, .25)
put(bark(.28, 430), 45.3, .1, .7, .8); put(bark(.25, 380), 45.75, .09, .7, .8); put(bark(.3, 400), 46.9, .08, .7, .8)
# E7: búsqueda
sir = siren_wail(8.0, 650, 1350, 2.6) * np.minimum(1, t_(8.0) / .5) * np.minimum(1, (8.0 - t_(8.0)) / .8); put(sir, 47.8, .17, -.3, .45)
sir2 = siren_wail(8.0, 560, 1200, 3.4) * np.minimum(1, t_(8.0) / 1.0) * np.minimum(1, (8.0 - t_(8.0)) / .8); put(sir2, 48.2, .12, .4, .45)
d7 = 7.0
def r7(t): return 16 + 12 * np.clip(t / 2.5, 0, 1) - 22 * np.clip((t - 5.7) / 1.1, 0, 1) * (1.0)
e7 = engine(d7, lambda t: np.maximum(8, r7(t)), 1.2, .3) * np.minimum(1, t_(d7) / .3) * np.minimum(1, (d7 - t_(d7)) / .5)
put(e7, 48, .26, -.2, .35); put(sos(noise(d7), 'bandpass', [600, 3000], 2) * .5 * (1 - np.clip((t_(d7) - 5.5) / 1.2, 0, 1)), 48, .14, 0, .2)
put(sos(noise(1.0), 'bandpass', [1800, 5000], 2) * env_ad(int(1.0 * SR), .5, .3) * .8, 53.7, .12, 0, .3)  # frenado
put(clunk(.4) * .6, 54.55, .2, .4, .3); put(squelch(.2) * .8, 51.2, .1, .5); put(squelch(.18) * .8, 52.9, .1, -.5)
# E8: calle al amanecer y cierre
for tt, f0, f1 in [(55.6, 3200, 4600), (55.9, 3600, 4200), (56.4, 2900, 4100), (57.1, 3300, 4700), (57.6, 3500, 4300)]: put(chirp(.16, f0, f1), tt, .06, .5 + (tt % 2) * -.5, .5)
steps('m1_a', 'concrete', .55, 1.0, -.25); steps('m2_a', 'concrete', .55, 1.0, .1); steps('chapoB_a', 'concrete', .4, 1.0, -.05)
idle = engine(5.0, lambda t: np.full_like(t, 12.0) + .5 * np.sin(2 * np.pi * 2 * t), .6, .3); put(fade(idle, .3, .6), 55.0, .2, .5, .3)
put(clunk(.5) * .8, 58.3, .2, .5, .5); put(metal_hit(1.2, 280, .9), 58.3, .08, .5, .6)
put(metal_hit(2.6, 190, 1.8) * 1.0, 58.95, .55, 0, .8); put(boom(2.4, 40) * .9, 58.95, .6, 0, .5)
put(sos(noise(.9), 'bandpass', [500, 3000], 2) * env_ad(int(.9 * SR), .3, .25) * .6, 58.1, .1, 0, .3)

# ---------- reverberación y mezcla final ----------
def make_ir(d=2.6, rt=1.6):
    n = int(d * SR); t = np.arange(n) / SR; l = rs.randn(n) * np.exp(-3.0 * t / rt); r = rs.randn(n) * np.exp(-3.0 * t / rt)
    l = sos(l, 'lowpass', 5000, 2); r = sos(r, 'lowpass', 5000, 2); l[:int(.012 * SR)] *= .0; r[:int(.018 * SR)] *= .0
    return l / np.sqrt(np.sum(l ** 2)) * .6, r / np.sqrt(np.sum(r ** 2)) * .6
irl, irr = make_ir()
wl = signal.fftconvolve(RL, irl)[:N]; wr = signal.fftconvolve(RR, irr)[:N]
OL_ = L + wl * 1.0; OR_ = R + wr * 1.0
# compresión suave y normalización (-3 dBFS pico), fundido de entrada/salida
def softclip(x): return np.tanh(x * 1.15) / np.tanh(1.15)
OL_, OR_ = softclip(OL_), softclip(OR_)
pk = max(np.max(np.abs(OL_)), np.max(np.abs(OR_))); g = 10 ** (-3 / 20) / pk
OL_ *= g; OR_ *= g
fi = np.minimum(1, np.arange(N) / (SR * .6)); fo = np.minimum(1, (N - np.arange(N)) / (SR * 1.4))
OL_ *= fi * fo; OR_ *= fi * fo
out = np.stack([OL_, OR_], 1)
os.makedirs(os.path.join(HERE, 'tmp'), exist_ok=True)
wavfile.write(os.path.join(HERE, 'tmp/audio.wav'), SR, (out * 32767).astype(np.int16))
print('audio.wav listo: %.2f s, pico %.2f dBFS' % (N / SR, 20 * np.log10(np.max(np.abs(out)))))
