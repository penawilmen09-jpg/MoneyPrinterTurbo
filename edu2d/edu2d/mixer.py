"""REGLA OFICIAL DE MEZCLA: la narración manda.

- La voz se normaliza a un nivel fijo (igual en todos los videos).
- Música muy suave y con ducking fuerte mientras habla el narrador.
- Efectos puntuales a bajo nivel y con ducking; los sonidos continuos (viento, rotor, rumor) se
  limitan a ráfagas breves y muy bajas (nunca durante toda una escena).
- Se mide, palabra por palabra, cuánto queda el fondo (música + efectos) por debajo de la voz y se
  rechaza la exportación si algún margen es insuficiente.
"""
import numpy as np

SR = 44100
VOICE_PEAK = 0.89
MUSIC_PEAK = 0.045            # ≈ -26 dBFS de pico, muy suave
DUCK_MUSIC = 0.85             # reducción de la música cuando habla la voz
DUCK_SFX = 0.90
AMBIENT = {"rotor", "wind", "rumble", "riser"}
AMBIENT_MAX_SEC = 1.8         # sin sonidos constantes: solo ráfagas cortas
AMBIENT_GAIN = 0.06
SFX_GAIN = {"pop": .22, "click": .22, "tick": .20, "ding": .20, "clank": .18, "zap": .12, "boom": .09,
            "crash": .09, "splash": .10, "horn": .08, "whoosh": .30, "bubble": .15}
DEFAULT_SFX_GAIN = .15
MIN_MARGIN_DB = 20.0          # el fondo debe quedar ≥ 20 dB por debajo de la voz en cada palabra


class MixError(RuntimeError):
    pass


def speech_activity(voice, sr=SR):
    """Envolvente 0..1 de actividad de voz con anticipo (ducking antes de hablar) y cola de recuperación."""
    k = int(.04 * sr)
    env = np.convolve(np.abs(voice), np.ones(k) / k, mode="same")
    on = (env > .012).astype(np.float32)
    lead, tail = int(.12 * sr), int(.30 * sr)
    kern = np.ones(lead + tail, dtype=np.float32)
    wide = (np.convolve(on, kern, mode="full")[tail:tail + len(on)] > 0).astype(np.float32)   # adelanta 'lead'
    sm = int(.06 * sr)
    return np.convolve(wide, np.ones(sm) / sm, mode="same")


def ambient_clip(fx, sr=SR):
    n_ = min(len(fx), int(AMBIENT_MAX_SEC * sr))
    fx = fx[:n_].copy()
    f = np.minimum(np.arange(n_) / (.3 * sr), 1) * np.minimum((n_ - np.arange(n_)) / (.5 * sr), 1)
    return fx * f


def mix(voice, spots, ambients, music_track=None):
    """voice: pista de voz ya colocada en el tiempo. spots/ambients: [(muestra_inicio, array, nombre)].
    Devuelve (mezcla final, fondo ya atenuado)."""
    n_ = len(voice)
    vp = np.abs(voice).max()
    voice = voice * (VOICE_PEAK / vp) if vp > 0 else voice
    act = speech_activity(voice)
    bed = np.zeros(n_, dtype=np.float32)
    sfx = np.zeros(n_, dtype=np.float32)
    for o, fx, name in spots:
        g = SFX_GAIN.get(name, DEFAULT_SFX_GAIN)
        seg = fx[:max(0, n_ - o)]
        sfx[o:o + len(seg)] += seg * g
    for o, fx, name in ambients:
        fx = ambient_clip(fx)
        seg = fx[:max(0, n_ - o)]
        sfx[o:o + len(seg)] += seg * AMBIENT_GAIN
    bed += sfx * (1 - DUCK_SFX * act)
    if music_track is not None:
        m = np.pad(music_track[:n_], (0, max(0, n_ - len(music_track))))
        m = m / (np.abs(m).max() + 1e-9) * MUSIC_PEAK
        bed += m * (1 - DUCK_MUSIC * act)
    out = voice + bed
    peak = np.abs(out).max()
    if peak > .92:
        out *= .92 / peak
        voice, bed = voice * (.92 / peak), bed * (.92 / peak)
    return out.astype(np.float32), voice.astype(np.float32), bed.astype(np.float32)


def speech_margins(voice, bed, words, sr=SR):
    """Margen en dB (voz − fondo) en la ventana de cada palabra. Devuelve lista de (palabra, margen)."""
    out = []
    for w in words:
        a, b = int(w["start"] * sr), max(int(w["end"] * sr), int(w["start"] * sr) + 1)
        v = np.sqrt(np.mean(voice[a:b] ** 2) + 1e-12)
        f = np.sqrt(np.mean(bed[a:b] ** 2) + 1e-12)
        out.append((w["text"], 20 * np.log10(v / f)))
    return out


def check_margins(margins, minimum=MIN_MARGIN_DB):
    worst = min(margins, key=lambda x: x[1])
    if worst[1] < minimum:
        raise MixError(f"mezcla rechazada: en «{worst[0]}» el fondo solo queda {worst[1]:.1f} dB bajo la voz (mínimo {minimum} dB)")
    return worst
