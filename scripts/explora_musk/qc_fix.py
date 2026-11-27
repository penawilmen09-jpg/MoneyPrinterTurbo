import wave, numpy as np, sys
sys.path.insert(0, '.')
import words as W
d, al_h, al_s = sys.argv[1:4]
def rd(p):
    w = wave.open(p); x = np.frombuffer(w.readframes(w.getnframes()), '<i2').astype(float).reshape(-1, 2) / 32768; return x.mean(1)
sr = 44100
def env(x, win=.25):
    n = int(win * sr); k = len(x) // n
    return 20 * np.log10(np.sqrt((x[:k * n].reshape(k, n) ** 2).mean(1)) + 1e-9)
v, m, s = rd(d + '/stem_voice.wav'), rd(d + '/stem_music.wav'), rd(d + '/stem_sfx.wav')
em = env(m)[:int(75 / .25)]
print('MÚSICA: nivel mín %.1f | máx %.1f | mediana %.1f dBFS (0–75 s)' % (em.min(), em.max(), np.median(em)))
dd = np.abs(np.diff(em))
print('MÚSICA: salto máx entre ventanas de 250 ms: %.1f dB | saltos >3 dB: %d | >6 dB: %d (antes: 82 saltos >6 dB)' % (dd.max(), (dd > 3).sum(), (dd > 6).sum()))
print('MÚSICA: primer 1 s: %.1f dBFS (audible desde el segundo 0) | ventanas por debajo de -50 dBFS: %d' % (env(m, 1.0)[0], (em < -50).sum()))
ws = [(w, a + .05, b + .05) for w, a, b in W.load(al_h)] + [(w, a + 5.22, b + 5.22) for w, a, b in W.load(al_s) if a >= 7.38]
rows = []
for w, a0, e0 in ws:
    a, b = int(a0 * sr), int(e0 * sr); r = lambda x: np.sqrt((x[a:b] ** 2).mean()) + 1e-9
    rows.append((20 * np.log10(r(v) / r(m)), 20 * np.log10(r(v) / r(s)), w, round(a0, 2)))
print('VOZ/MÚSICA media %.1f dB | VOZ/SFX media %.1f dB' % (np.mean([r[0] for r in rows]), np.mean([r[1] for r in rows])))
print('peores vs música:', [(round(x[0], 1), x[2], x[3]) for x in sorted(rows)[:4]], '| palabras con voz<música:', sum(1 for r in rows if r[0] < 0), 'de', len(rows))
# profundidad real del ducking: música en pausas largas vs hablando
vact = env(v) > -45
mp = em[~vact[:len(em)]]; ms = em[vact[:len(em)]]
print('DUCKING: música hablando %.1f dB vs en pausas %.1f dB -> diferencia %.1f dB' % (np.median(ms), np.median(mp), np.median(mp) - np.median(ms)))
