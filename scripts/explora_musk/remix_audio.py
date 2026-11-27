"""Corrección de audio: pista musical continua + ducking suave + efectos independientes.
No toca la voz, la narración, las animaciones ni los subtítulos (el vídeo se copia sin recodificar)."""
import sys, wave, subprocess, numpy as np
import audio_m as A

SR = 44100
TOT = 76.3
PRE = 6.0                      # pre-roll: la música ya está sonando en el segundo 0 (sin fundido de entrada)
V_GAIN_DB = -2.5               # margen de cabeza (la normalización final sube el conjunto; sin recortes intermedios)
DUCK_DB = 6.0                  # ducking suave (antes: 27 dB de media, 37 dB máx.)
VOICE_VS_MUSIC_DB = 17.0       # la música queda ~17 dB bajo la voz mientras habla
HOLD, ATTACK, RELEASE = .70, .20, 1.00


def rd(path):
    w = wave.open(path); x = np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(np.float64) / 32768
    return x.reshape(-1, w.getnchannels()).T


def wr(path, x):
    x = np.clip(x.T, -1, 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(x.shape[1]); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x * 32767).astype("<i2").tobytes())


def db(x): return 20 * np.log10(np.maximum(x, 1e-9))
def undb(x): return 10 ** (np.asarray(x) / 20)


def smooth_gain(target_db, attack, release):
    """Seguidor de un polo sobre la ganancia en dB (ataque = bajar, release = subir). Evita saltos bruscos."""
    out = np.empty_like(target_db); y = target_db[0]
    a = np.exp(-1 / (attack * SR)); r = np.exp(-1 / (release * SR))
    for i, v in enumerate(target_db):
        c = a if v < y else r
        y = c * y + (1 - c) * v; out[i] = y
    return out


def loop_to_length(x, n, xf=2.0):
    """Si la pista es más corta que el vídeo: bucle con crossfade de potencia constante (sin cortes)."""
    if x.shape[1] >= n: return x[:, :n]
    k = int(xf * SR); out = x.copy()
    while out.shape[1] < n:
        t = np.linspace(0, np.pi / 2, k)
        tail, head = out[:, -k:], x[:, :k]
        mix = tail * np.cos(t) + head * np.sin(t)
        out = np.concatenate([out[:, :-k], mix, x[:, k:]], axis=1)
    return out[:, :n]


def music_track(n):
    A.TOTAL = TOT + PRE; A.N = int((TOT + PRE + 1.0) * SR)
    m = A.music(); m = A.reverb(m, 2.6, .35)
    m = m[int(PRE * SR):].T                       # (2, N) ya "en marcha" desde el primer segundo
    m = loop_to_length(m, n)
    return m / np.abs(m).max()


def decimate_env(x, win=.05):
    n = int(win * SR); k = len(x) // n
    return np.sqrt((x[:k * n].reshape(k, n) ** 2).mean(1))


def main(narr_wav, sfx_wav, out_dir):
    n = int(TOT * SR)
    v = rd(narr_wav)[0]; v = np.pad(v, (0, max(0, n - len(v))))[:n] * undb(V_GAIN_DB)
    s = rd(sfx_wav); s = np.pad(s, ((0, 0), (0, max(0, n - s.shape[1]))))[:, :n]
    m = music_track(n)
    # ---------- actividad de voz con "hold" (puentea pausas cortas entre palabras: sin bombeo)
    ev = decimate_env(v, .05); act = (db(ev) > -42).astype(float)
    k_hold = int(HOLD / .05); k_pre = int(.15 / .05)
    hold = np.zeros_like(act)
    for i in np.where(act > 0)[0]:
        hold[max(0, i - k_pre): i + k_hold + 1] = 1
    act_fine = np.repeat(hold, int(.05 * SR))[:n]; act_fine = np.pad(act_fine, (0, n - len(act_fine)))
    duck_db = smooth_gain(-DUCK_DB * act_fine, ATTACK, RELEASE)          # 0 dB en pausas, -9 dB hablando (suave)
    # ---------- nivelado lento de la música (volumen uniforme)
    mono = m.mean(0); e = db(np.sqrt(np.convolve(mono ** 2, np.ones(int(4 * SR)) / (4 * SR), "same")) + 1e-9)
    lvl_db = smooth_gain(np.clip(np.median(e) - e, -3, 3), 1.5, 1.5)
    # ---------- niveles absolutos: música ~19 dB bajo la voz al hablar
    v_speech_rms = np.sqrt((v[act_fine > .5] ** 2).mean())
    m_rms = np.sqrt((m ** 2).mean()) / 1.0
    music_base = db(v_speech_rms) - VOICE_VS_MUSIC_DB + DUCK_DB - db(np.sqrt((mono ** 2).mean()))   # nivel en pausas
    mg = undb(music_base + lvl_db + duck_db)
    music = m * mg
    # ---------- efectos: independientes (suman, nunca recortan la música), con ducking ligero propio
    sfx_duck = smooth_gain(-6.0 * act_fine, .08, .5)
    sfx_gain = db(np.abs(v).max()) - 13.0 - db(np.abs(s).max())          # pico de efectos ~13 dB bajo el pico de la voz
    sfx = s * undb(sfx_gain + sfx_duck)
    # ---------- mezcla + fundido final
    fo = np.clip((TOT - np.arange(n) / SR) / 1.4, 0, 1)
    voice = np.stack([v, v]) * fo; music = music * fo; sfx = sfx * fo
    wr(out_dir + "/stem_voice.wav", voice); wr(out_dir + "/stem_music.wav", music); wr(out_dir + "/stem_sfx.wav", sfx)
    mix = voice + music + sfx
    wr(out_dir + "/premix.wav", mix)
    print("pico premix %.2f | voz activa %.1f dBFS | música base %.1f dBFS" % (np.abs(mix).max(), db(v_speech_rms), music_base))


if __name__ == "__main__":
    main(*sys.argv[1:4])
