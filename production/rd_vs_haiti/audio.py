"""Música instrumental original + ambientes y efectos sincronizados (síntesis pura, sin voces)."""
import numpy as np, math, wave
SR = 44100; DUR = 60.0; N = int(SR * DUR); BPM = 96.0; BEAT = 60 / BPM
rng = np.random.default_rng(42)
L = np.zeros(N, np.float32); R = np.zeros(N, np.float32)       # bus de efectos
ML = np.zeros(N, np.float32); MR = np.zeros(N, np.float32)     # bus de música

def tt(n): return np.arange(n) / SR
def noise(n): return rng.standard_normal(n).astype(np.float32)
def fbp(x, lo, hi):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); m = np.ones_like(f)
    if lo: m *= 1 / (1 + (lo / np.maximum(f, 1e-3)) ** 4)
    if hi: m *= 1 / (1 + (f / hi) ** 4)
    return np.fft.irfft(X * m, len(x)).astype(np.float32)
def env(n, a, d=None, curve=3.0):
    t = tt(n); e = np.minimum(1, t / max(a, 1e-4)); dd = (n / SR) if d is None else d
    return (e * np.exp(-curve * t / dd)).astype(np.float32)
def add(bus, sig, t0, pan=0.0, g=1.0):
    i = int(t0 * SR); 
    if i >= N or i + len(sig) <= 0: return
    s = sig[max(0, -i):]; i = max(0, i); s = s[:N - i]; gl = g * math.cos((pan + 1) * math.pi / 4); gr = g * math.sin((pan + 1) * math.pi / 4)
    (bus[0] if isinstance(bus, tuple) else bus)[i:i + len(s)] += s * gl
    if isinstance(bus, tuple): bus[1][i:i + len(s)] += s * gr
FX = (L, R); MU = (ML, MR)
def hz(m): return 440 * 2 ** ((m - 69) / 12)
def lfo(n, f, ph=0): return np.sin(TAU * f * tt(n) + ph)
TAU = 2 * math.pi
def seg(bus_sig, a, b, fi=.3, fo=.3):
    """Ventana temporal con fundido para una cama continua."""
    w = np.zeros(N, np.float32); i0, i1 = int(a * SR), int(b * SR); w[i0:i1] = 1
    k = int(max(fi, fo) * SR) | 1; w = np.convolve(w, np.hanning(int(fi * SR) | 1) / np.hanning(int(fi * SR) | 1).sum(), 'same') if fi else w
    return bus_sig * w

def bed(sig, a, b, g=1.0, pan=0.0, fi=.4):
    w = np.zeros(N, np.float32); i0, i1 = int(a * SR), int(b * SR); w[i0:i1] = 1
    kk = int(fi * SR); ker = np.ones(kk) / kk; w = np.convolve(w, ker, 'same').astype(np.float32)
    s = sig * w * g; add(FX, s[:N], 0, pan, 1.0)

# ------------------------------------------------------------- MÚSICA
CH = {'Am': [45, 52, 57, 60, 64], 'F': [41, 48, 53, 57, 60], 'C': [48, 55, 60, 64, 67], 'G': [43, 50, 55, 59, 62]}
PROG = (['Am', 'F', 'C', 'G'] * 6)[:23] + ['C']
BAR = 4 * BEAT
def gain_at(t):  # dinámica global
    pts = [(0, .35), (3, .55), (7, .75), (14, .8), (28, 1.0), (35, .85), (43, .85), (52, 1.05), (57, .8), (60, .0)]
    return np.interp(t, [p[0] for p in pts], [p[1] for p in pts])
for b, ch in enumerate(PROG):
    t0 = b * BAR; n = int((BAR + 1.6) * SR); 
    for k, m in enumerate(CH[ch]):
        f = hz(m + 12 * (1 if k > 2 else 0) * 0); tt_ = tt(n); sig = np.zeros(n, np.float32)
        for dt in (-.06, .06):
            ff = f * 2 ** (dt / 12)
            for h in range(1, 7): sig += (np.sin(TAU * ff * h * tt_ + k) / h ** 1.3).astype(np.float32)
        e = np.minimum(1, tt_ / .9) * np.minimum(1, (n / SR - tt_) / 1.2); sig *= e * (.05 if k < 2 else .035) * gain_at(t0)
        add(MU, sig, t0, pan=-.4 + k * .2)
    # cuerdas agudas (swell) cada 2 compases
    if b % 2 == 0 and b < 22:
        n2 = int((BAR * 2) * SR); t_ = tt(n2); s = np.zeros(n2, np.float32)
        for m in CH[ch][2:]:
            for h in range(1, 5): s += np.sin(TAU * hz(m + 12) * h * t_ + 3 * np.sin(5 * t_) * .002) / h ** 1.6
        s *= np.sin(np.pi * t_ / (n2 / SR)) ** 2 * .035 * gain_at(t0); add(MU, s, t0, 0)
# bajo
for b, ch in enumerate(PROG):
    t0 = b * BAR
    if t0 < 6.9: continue
    root = CH[ch][0]
    for (pos, m, ln) in ((0, root, .55), (1.5, root, .3), (2.5, root + 7, .3), (3.25, root + 12, .25)) if b < 22 else ((0, root, 3.5),):
        n = int(ln * SR * 1.6); t_ = tt(n); f = hz(m); s = (np.sin(TAU * f * t_) + .4 * np.sin(TAU * 2 * f * t_) + .15 * np.sin(TAU * 3 * f * t_)) * env(n, .008, ln * .9, 4) * .3 * gain_at(t0)
        add(MU, s, t0 + pos * BEAT, -.1)
# marimba / arpegio
for b, ch in enumerate(PROG):
    t0 = b * BAR
    if t0 < 6.9 or b >= 23: continue
    notes = CH[ch][2:] + [CH[ch][2] + 12, CH[ch][3] + 12]; pat = [0, 2, 1, 3, 2, 4, 3, 1] if t0 < 28 or t0 >= 35 else [0, 1, 2, 3, 4, 3, 2, 1]
    for i in range(8):
        if (t0 < 14 and i % 2) : continue
        m = notes[pat[i] % len(notes)] + 12; n = int(.5 * SR); t_ = tt(n); f = hz(m)
        s = (np.sin(TAU * f * t_) + .35 * np.sin(TAU * 4 * f * t_) * np.exp(-30 * t_)) * env(n, .003, .16, 4) * .22 * gain_at(t0)
        add(MU, s, t0 + i * BEAT / 2, pan=-.5 + (i % 4) * .33)
# percusión caribeña
def conga(t0, f=190, g=.3, pan=.3):
    n = int(.35 * SR); t_ = tt(n); s = np.sin(TAU * (f + 60 * np.exp(-40 * t_)) * t_) * env(n, .001, .09, 4); s += fbp(noise(n), 800, 4000) * env(n, .0005, .012, 5) * .5; add(MU, s * g, t0, pan)
def guira(t0, g=.12, pan=-.3, ln=.07):
    n = int(ln * SR); s = fbp(noise(n), 4500, 12000) * env(n, .003, ln * .7, 3); add(MU, s * g, t0, pan)
def tambora(t0, g=.35, hi=False):
    n = int(.3 * SR); t_ = tt(n); f = 170 if not hi else 260; s = np.sin(TAU * (f + 40 * np.exp(-50 * t_)) * t_) * env(n, .001, .1, 4) + fbp(noise(n), 1500, 6000) * env(n, .0005, .02, 5) * .6; add(MU, s * g, t0, .1)
def kick(t0, g=.7, f0=110, f1=38, ln=.9):
    n = int(ln * SR); t_ = tt(n); ph = TAU * (f1 * t_ + (f0 - f1) * (1 - np.exp(-12 * t_)) / 12); s = np.sin(ph) * env(n, .002, ln * .5, 3) + fbp(noise(n), 0, 300) * env(n, .001, .3, 4) * .4; add(MU, s * g, t0, 0)
tot = int(DUR / BEAT)
for i in range(tot * 4):
    t = i * BEAT / 4
    if t < 6.9 or t >= 58: continue
    g = gain_at(t); bar_pos = (i % 16)
    if bar_pos in (2, 6, 7, 10, 14): conga(t, 190 + (bar_pos % 3) * 20, .22 * g, .35)            # tumbao
    if i % 4 == 0 and t > 13.9: kick(t, .25 * g, 90, 50, .3)
    if i % 4 in (1, 3) and t > 13.9 or (28 <= t < 35 and i % 2 == 0): guira(t, .14 * g * (1.4 if 28 <= t < 35 else 1), -.3)
    if 28 <= t < 35: 
        if i % 4 in (0, 2): tambora(t, .3 * g, i % 8 == 2)
        if i % 8 == 3: conga(t, 280, .2 * g, -.4)
    if t >= 43 and t < 52 and i % 2 == 0: guira(t, .1 * g, .3)
# impactos y risers en cambios de escena
for ts in (7, 14, 21, 28, 35, 43, 52): kick(ts - .02, .9 if ts in (7, 28, 52) else .55)
def riser(a, b, g=.25):
    n = int((b - a) * SR); x = noise(n); t_ = tt(n); x = fbp(x, 400, 9000) * (t_ / (b - a)) ** 2.2 * g; add(MU, x, a, 0)
for a, b in ((5.3, 7), (26.2, 28), (41.3, 43), (50.2, 52)): riser(a, b)
def whoosh(t0, ln=.9, g=.4, pan=0):
    n = int(ln * SR); t_ = tt(n); x = noise(n); fc = 300 * 2 ** (t_ / ln * 4); y = fbp(x, 300, 6000) * np.sin(np.pi * t_ / ln) ** 2; add(FX, y * g, t0, pan)
for ts, p in ((6.7, 0), (13.75, -.3), (20.75, .3), (23.7, .3), (27.7, -.3), (42.7, .3)): whoosh(ts - .15, .9, .35, p)

# ---------- final: acorde largo de resolución (C add9) con campanas ----------
for m, d in ((60, 0), (64, .25), (67, .5), (71, .75), (74, 1.0), (79, 1.4)):
    n = int(6 * SR); t_ = tt(n); f = hz(m); s = (np.sin(TAU * f * t_) + .3 * np.sin(TAU * 2.76 * f * t_) * np.exp(-3 * t_)) * env(n, .005, 2.4, 3) * .14; add(MU, s, 53.5 + d, (m % 5 - 2) / 3)

# ------------------------------------------------------------- AMBIENTES / SFX
def waves(a, b, g, per=6.3, pan=0, lp=1100):
    n = N; t_ = tt(n); sw = (.5 + .5 * np.sin(TAU * t_ / per - 1)) ** 2.2
    x = fbp(noise(n), 60, lp) * (.25 + .9 * sw) + fbp(noise(n), 2500, 9000) * sw * .12; bed(x, a, b, g, pan)
def wind(a, b, g, pan=0):
    n = N; t_ = tt(n); m = .55 + .45 * np.sin(TAU * t_ / 9.0) * np.sin(TAU * t_ / 5.3 + 1); x = fbp(noise(n), 200, 900) * m; bed(x, a, b, g, pan)
def rumble(a, b, g, lo=30, hi=220): bed(fbp(noise(N), lo, hi), a, b, g)
def chirp(t0, f0=3200, f1=4800, ln=.12, g=.15, pan=0, n_=1):
    for k in range(n_):
        n = int(ln * SR); t_ = tt(n); f = f0 + (f1 - f0) * (t_ / ln) ** .7 + 300 * np.sin(TAU * 38 * t_); s = np.sin(TAU * np.cumsum(f) / SR) * np.sin(np.pi * t_ / ln) ** 1.5; add(FX, s * g, t0 + k * (ln + .05), pan)
def gull(t0, pan=0, g=.18):
    n = int(.7 * SR); t_ = tt(n); f = 900 + 500 * np.sin(np.pi * t_ / .7) ** 1 + 60 * np.sin(TAU * 12 * t_); s = (np.sin(TAU * np.cumsum(f) / SR) + .5 * np.sin(TAU * np.cumsum(2 * f) / SR)) * np.sin(np.pi * t_ / .7) ** 1.2; add(FX, s * g * .5, t0, pan)
def car_pass(t0, direction=1, g=.3, ln=2.2):
    n = int(ln * SR); t_ = tt(n); sw = np.sin(np.pi * t_ / ln) ** 2; x = fbp(noise(n), 80, 1400) * sw * g + np.sin(TAU * (55 + 20 * sw) * t_) * sw * g * .3; 
    add(FX, x, t0, -.9 * direction * 0 + 0, 1.0); 
    # paneo
    i = int(t0 * SR); pan = np.linspace(-direction, direction, n); gl = np.cos((pan + 1) * np.pi / 4); gr = np.sin((pan + 1) * np.pi / 4)
    L[i:i + n] -= (x * 0)[:N - i] if False else 0
def horn(t0, f=420, ln=.22, g=.12, pan=0):
    n = int(ln * SR); t_ = tt(n); s = (np.sin(TAU * f * t_) + .5 * np.sin(TAU * f * 1.26 * t_) + .3 * np.sin(TAU * f * 2 * t_)) * np.minimum(1, t_ / .01) * np.minimum(1, (ln - t_) / .02); add(FX, s * g, t0, pan)
def clink(t0, g=.08, pan=0):
    n = int(.3 * SR); t_ = tt(n); f = 2800 + 1800 * rng.random(); s = (np.sin(TAU * f * t_) + .5 * np.sin(TAU * f * 2.4 * t_)) * env(n, .0005, .06, 5); add(FX, s * g, t0, pan)
def step(t0, g=.12, pan=0):
    n = int(.12 * SR); s = fbp(noise(n), 60, 700) * env(n, .002, .03, 4); add(FX, s * g, t0, pan)
def hammer(t0, g=.25, pan=0):
    n = int(.4 * SR); t_ = tt(n); s = fbp(noise(n), 1500, 7000) * env(n, .0005, .02, 6) + np.sin(TAU * 820 * t_) * env(n, .0005, .12, 5) * .5; add(FX, s * g, t0, pan)
def beep(t0, f=1000, ln=.09, g=.06, pan=0):
    n = int(ln * SR); t_ = tt(n); add(FX, np.sin(TAU * f * t_) * np.minimum(1, (ln - t_) / .01) * g, t0, pan)
def moto(a, b, g=.12, pan=0):
    n = int((b - a) * SR); t_ = tt(n); f = 70 + 25 * np.sin(TAU * .6 * t_); ph = np.cumsum(f) / SR; s = (np.sign(np.sin(TAU * ph)) * .5 + np.sin(TAU * 2 * ph) * .3) * (.6 + .4 * np.sin(TAU * 11 * t_)); s = fbp(s.astype(np.float32), 60, 1400) * np.sin(np.pi * t_ / (b - a)) ** 1.5; add(FX, s * g, a, pan)
def firework(t0, pan=0, g=.5):
    n = int(2.2 * SR); t_ = tt(n); s = fbp(noise(n), 30, 160) * env(n, .001, .35, 4) * 1.4 + np.sin(TAU * 60 * t_) * env(n, .001, .25, 4)
    cr = noise(n) * (rng.random(n) > .985) * env(n, .05, 1.2, 3); cr = fbp(cr.astype(np.float32), 1500, 9000) * 1.5; add(FX, (s + cr) * g, t0, pan)
def whistle(t0, ln=.5, pan=0): 
    n = int(ln * SR); t_ = tt(n); f = 800 + 2200 * (t_ / ln) ** 1.5; add(FX, np.sin(TAU * np.cumsum(f) / SR) * .05 * (t_ / ln), t0, pan)
def ship_horn(t0, ln=2.0, g=.22):
    n = int(ln * SR); t_ = tt(n); s = sum(np.sin(TAU * f * t_) / (i + 1) for i, f in enumerate((98, 196, 294, 392, 490))) * np.minimum(1, t_ / .12) * np.minimum(1, (ln - t_) / .6); add(FX, s * g * .5, t0, .3)
def crickets(a, b, g=.05):
    n = N; t_ = tt(n); m = (np.sin(TAU * 22 * t_) > .3) * (np.sin(TAU * 1.7 * t_) > -.2); x = np.sin(TAU * 4600 * t_) * m * (1 + .3 * np.sin(TAU * 3 * t_)); bed(x.astype(np.float32), a, b, g, .0, 1.0)
def stream(a, b, g=.2): bed(fbp(noise(N), 800, 6000) * (.7 + .3 * lfo(N, .7)), a, b, g)

# S1 0-7 olas lejanas + viento fuerte de altura
wind(0, 7.6, .75, 0); waves(0, 7.8, .22, 7.0, 0, 700)
for tx, p in ((1.6, -.6), (3.4, .5)): gull(tx, p, .05)
# S2 7-14
waves(6.6, 9.9, .55, 6.3, 0); chirp(7.6, n_=3, g=.1, pan=-.5); gull(8.0, .4); gull(8.9, -.4); [step(7.4 + k * .46, .06, .2) for k in range(5)]
rumble(9.1, 12.3, .32); [car_pass(t0, d, .35) for t0, d in ((9.5, 1), (10.3, -1), (10.9, 1), (11.5, -1))]
for tx, pn in ((9.9, -.3), (11.0, .4), (11.9, 0)): horn(tx, 430, .18, .1, pn); horn(tx + .22, 540, .3, .1, pn)
moto(10.5, 11.8, .1, .5); chirp(12.0, 2800, 4200, n_=4, g=.08, pan=.4); chirp(12.8, 3600, 5200, n_=3, g=.07, pan=-.5); wind(11.6, 14.3, .4); stream(12.3, 14.2, .06)
waves(11.8, 14.2, .2, 6.3, 0)
# S3 14-21
wind(13.6, 16.8, .5); chirp(14.8, 3000, 4600, n_=3, g=.1, pan=-.4); chirp(15.6, 2600, 4000, n_=3, g=.09, pan=.5); [step(14.5 + k * .5, .08, .3) for k in range(6)]
rumble(16.2, 18.9, .22, 40, 300); [clink(16.5 + k * .37 + (k % 3) * .08, .07, ((k * 7) % 11 - 5) / 6) for k in range(9)]
moto(16.8, 18.3, .18, -.4); horn(17.4, 380, .25, .14, .5); horn(17.7, 480, .35, .14, .5); [step(16.4 + k * .4, .06, (k % 5 - 2) / 4) for k in range(7)]
waves(18.6, 21.4, .6, 6.3, 0); gull(19.2, .4); gull(20.2, -.5); wind(18.6, 21.4, .3)
# S4 21-28
wind(20.7, 24.7, .45); stream(21.2, 24.8, .12); chirp(22.0, 3200, 4800, n_=2, g=.07, pan=.4); moto(23.0, 24.6, .12, .3)
rumble(24.0, 28.3, .28, 40, 260); [step(24.5 + k * .42, .09, ((k * 5) % 9 - 4) / 5) for k in range(8)]; [clink(24.8 + k * .5, .06, ((k * 3) % 7 - 3) / 4) for k in range(7)]
moto(25.2, 26.8, .15, -.4); horn(26.3, 400, .3, .11, -.4); [step(26.0 + k * .45, .1, ((k * 5) % 9 - 4) / 5) for k in range(8)]
# S5 28-35 festivo: ambiente liviano + aplausos de palmas (sin voces)
def claps(t0, g=.05):
    n = int(.1 * SR); s = fbp(noise(n), 800, 5000) * env(n, .001, .02, 5); add(FX, s * g, t0, ((t0 * 7) % 2) - 1)
for k in range(24): claps(28.4 + k * .27 + (k % 3) * .03, .05)
for k in range(14): claps(30.6 + k * .31, .05)
for k in range(3): firework(33.0 + (0.3, .7, 1.2)[k] * .0 + (.3, .7, 1.2)[k] - .0, [-.5, .5, 0][k], .5)
for tx, pn in ((33.4, -.6), (34.1, -.2), (34.8, .5)): firework(tx + .0 - 0.0, pn, .55); whistle(tx - .45, .45, pn)
# S6 35-43
rumble(34.8, 43.2, .28, 30, 250); moto(36.0, 37.5, .14, -.3); [car_pass(36.0 + k * .8, 1 if k % 2 else -1, .3) for k in range(4)]
ship_horn(38.2, 1.9, .2); [beep(37.0 + k * .5, 1000, .09, .05, .5) for k in range(8)]; waves(35, 39.4, .25, 6.3, 0)
[hammer(39.3 + k * .52, .22, (k % 3 - 1) / 3) for k in range(7)]; rumble(40.0, 43.2, .4, 35, 120)
for k in range(10): clink(39.6 + k * .33, .06, ((k * 5) % 9 - 4) / 5)
moto(39.4, 40.8, .15, .4); moto(40.9, 42.2, .15, -.4); [step(41.0 + k * .45, .09, ((k * 3) % 5 - 2) / 3) for k in range(8)]
[beep(41.5 + k * .5, 800, .12, .05, -.4) for k in range(4)]
# S7 43-52
for a, b in ((42.6, 46.2), ):
    wind(a, b, .55); chirp(43.4, 3000, 4600, n_=3, g=.1, pan=-.5); chirp(44.6, 2600, 4000, n_=3, g=.09, pan=.5)
waves(45.8, 49.4, .5, 6.3, .2); stream(46.0, 49.2, .35, ) if False else None; stream(46.0, 49.2, .28); gull(46.5, .5); gull(47.8, -.3)
chirp(47.2, 3400, 5200, n_=4, g=.08, pan=-.6)
rumble(48.8, 52.3, .25); [car_pass(49.4 + k * .8, 1 if k % 2 else -1, .28) for k in range(3)]; horn(50.3, 430, .2, .1, .3); horn(50.55, 540, .3, .1, .3); moto(50.5, 51.8, .1, -.4)
[clink(49.5 + k * .45, .05, ((k * 5) % 9 - 4) / 5) for k in range(6)]
# S8 52-60
waves(51.8, 60, .75, 7.0, 0); wind(52, 60, .5); crickets(56.0, 60.0, .06); gull(56.5, -.4); gull(58.2, .5)

# ------------------------------------------------------------- MEZCLA
def reverb(x, wet=.22, sec=2.2):
    n = int(sec * SR); ir = rng.standard_normal(n) * np.exp(-3.2 * np.arange(n) / n); ir = fbp(ir.astype(np.float32), 200, 6000); ir /= np.abs(ir).sum() * .12
    X = np.fft.rfft(x, len(x) + n); Y = np.fft.irfft(X * np.fft.rfft(ir, len(x) + n))[:len(x)]
    return (x * (1 - wet * .5) + Y.astype(np.float32) * wet)
ML2 = reverb(ML, .30); MR2 = reverb(MR, .30)
mus = np.stack([ML2, MR2]); fx = np.stack([L, R])
mus = mus / (np.abs(mus).max() + 1e-6) * .60; fx = fx / (np.abs(fx).max() + 1e-6) * .58
out = mus + fx
fade = np.minimum(1, tt(N) / .6) * np.minimum(1, (DUR - tt(N)) / 1.2)
out = out * fade; out = np.tanh(out * 1.25) / np.tanh(1.25) 
out = out / np.abs(out).max() * .89
pcm = (out.T * 32767).astype(np.int16)
with wave.open('audio/mix.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print('ok', N / SR, 's')
