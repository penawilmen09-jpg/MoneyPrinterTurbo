import wave, numpy as np, sys
import words as W
d, al = sys.argv[1:3]
def rd(p):
    w = wave.open(p); x = np.frombuffer(w.readframes(w.getnframes()), '<i2').astype(float).reshape(-1, 2) / 32768; return x.mean(1)
sr = 44100
def env(x, win=.25):
    n = int(win * sr); k = len(x) // n; return 20 * np.log10(np.sqrt((x[:k * n].reshape(k, n) ** 2).mean(1)) + 1e-9)
v, m, s = rd(d + '/stem_voice.wav'), rd(d + '/stem_music.wav'), rd(d + '/stem_sfx.wav')
em = env(m)[:int(76 / .25)]; dd = np.abs(np.diff(em))
print('MÚSICA: nivel mín %.1f | máx %.1f | mediana %.1f dBFS | salto máx %.1f dB (250 ms) | saltos >6 dB: %d | ventanas < -50 dBFS: %d' % (em.min(), em.max(), np.median(em), dd.max(), (dd > 6).sum(), (em < -50).sum()))
print('MÚSICA primer segundo: %.1f dBFS (suena desde el inicio)' % env(m, 1.0)[0])
ws = W.load(al); rows = []
for w, a0, e0 in ws:
    a, b = int(a0 * sr), int(e0 * sr); r = lambda x: np.sqrt((x[a:b] ** 2).mean()) + 1e-9
    rows.append((20 * np.log10(r(v) / r(m)), 20 * np.log10(r(v) / r(s)), w, round(a0, 2)))
print('VOZ/MÚSICA media %.1f dB | VOZ/SFX media %.1f dB | palabras con voz<música: %d de %d | voz<sfx: %d' % (np.mean([r[0] for r in rows]), np.mean([r[1] for r in rows]), sum(r[0] < 0 for r in rows), len(rows), sum(r[1] < 0 for r in rows)))
print('peores vs música:', [(round(x[0], 1), x[2], x[3]) for x in sorted(rows)[:4]], '| peores vs sfx:', [(round(x[1], 1), x[2], x[3]) for x in sorted(rows, key=lambda x: x[1])[:3]])
print('Cambios de escena (música, dB vs entorno):', end=' ')
for b in (14.85, 27.55, 37.5, 45.8, 57.13, 65.25):
    r = lambda a, c: 20 * np.log10(np.sqrt((m[int(a * sr):int(c * sr)] ** 2).mean()) + 1e-9)
    print('%.1f→%+.1f' % (b, r(b - .25, b + .25) - np.median([r(b + o, b + o + .25) for o in np.arange(-2, 2, .25)])), end='  ')
print()
