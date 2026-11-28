"""Audio system: narration-first mix with ducked music, sparse informative SFX
and broadcast-style loudness normalisation (-16 LUFS, -1 dBTP).

Everything (music + effects) is synthesised locally with numpy, so there is no
licensing risk and no paid service involved.
"""

from __future__ import annotations

import json
import math
import re
import subprocess
from dataclasses import dataclass

import numpy as np

from app.utils import utils

from .models import Plan, SceneTiming

SR = 44100
TARGET_LUFS = -16.0
TARGET_TP = -1.0
# Mix design (dB relative to the narration level)
MUSIC_BASE_DB = -14.0      # music bed level in pauses (RMS vs. narration RMS)
MUSIC_DUCK_DB = -6.0       # extra reduction while the narrator speaks (=> -23 dB under speech)
SFX_GAP_DB = -9.0          # SFX RMS in silence, vs. narration RMS
SFX_OVER_SPEECH_DB = -17.0  # SFX RMS when it must overlap non-key speech
MAX_SFX_RATE = 1 / 8.5     # at most one effect every ~8.5 s on average
MIN_SFX_SPACING = 4.0


def _ff() -> str:
    return utils.get_ffmpeg_binary()


def decode(path: str) -> np.ndarray:
    cmd = [_ff(), "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"]
    out = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(out, dtype=np.float32).astype(np.float64)


def write_wav(path: str, x: np.ndarray, channels: int = 1):
    import wave
    data = np.clip(x, -1, 1)
    pcm = (data * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def read_wav(path: str) -> np.ndarray:
    return decode(path)


def db(x: float) -> float:
    return 10 ** (x / 20.0)


def rms_db(x: np.ndarray) -> float:
    if len(x) == 0:
        return -120.0
    return 20 * math.log10(max(float(np.sqrt(np.mean(x ** 2))), 1e-9))


def peak_db(x: np.ndarray) -> float:
    return 20 * math.log10(max(float(np.max(np.abs(x))) if len(x) else 0.0, 1e-9))


# ---------------------------------------------------------------- DSP helpers
def fft_band(x: np.ndarray, lo: float | None, hi: float | None) -> np.ndarray:
    n = len(x)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / SR)
    m = np.ones_like(f)
    if lo:
        m *= 1 / (1 + (lo / np.maximum(f, 1e-3)) ** 4)
    if hi:
        m *= 1 / (1 + (np.maximum(f, 1e-3) / hi) ** 4)
    return np.fft.irfft(X * m, n)


def fades(x: np.ndarray, fin: float, fout: float) -> np.ndarray:
    n = len(x)
    g = np.ones(n)
    a, b = int(fin * SR), int(fout * SR)
    if a:
        g[:a] = np.linspace(0, 1, a) ** 2
    if b:
        g[-b:] = np.minimum(g[-b:], np.linspace(1, 0, b) ** 2)
    return x * g


# --------------------------------------------------------------------- synth
def synth_ambient(duration: float, seed: int = 7) -> np.ndarray:
    """Slow curious-documentary pad: Am9 / Fmaj7 / Cmaj7 / Gsus, soft and wide."""
    rng = np.random.default_rng(seed)
    n = int(duration * SR)
    t = np.arange(n) / SR
    chords = [
        [110.0, 164.81, 220.0, 261.63, 329.63],       # Am9-ish
        [87.31, 130.81, 220.0, 261.63, 349.23],       # Fmaj7
        [130.81, 196.0, 261.63, 329.63, 493.88],      # Cmaj7
        [98.0, 146.83, 196.0, 293.66, 392.0],         # Gsus
    ]
    seg_len = 8.0
    out = np.zeros(n)
    for k in range(int(duration / seg_len) + 2):
        c = chords[k % len(chords)]
        t0 = k * seg_len
        env = np.clip((t - (t0 - 2.0)) / 3.0, 0, 1) * np.clip(((t0 + seg_len + 2.0) - t) / 3.0, 0, 1)
        if not env.any():
            continue
        for fi, f in enumerate(c):
            for det in (-0.9, 0.9):
                ph = rng.uniform(0, 2 * math.pi)
                lfo = 0.75 + 0.25 * np.sin(2 * math.pi * (0.07 + 0.02 * fi) * t + ph)
                out += env * lfo * (np.sin(2 * math.pi * (f + det) * t + ph) + 0.3 * np.sin(2 * math.pi * 2 * (f + det) * t) * 0.5) / (1 + 0.15 * fi)
    # very soft air
    noise = fft_band(rng.standard_normal(n), 400, 3000) * 0.01
    out = fft_band(out, 60, 2600) + noise
    out = out / (np.sqrt(np.mean(out ** 2)) + 1e-9)
    return out


def _env_ad(n: int, attack: float, decay: float) -> np.ndarray:
    t = np.arange(n) / SR
    a = np.clip(t / max(attack, 1e-3), 0, 1)
    return a * np.exp(-t / max(decay, 1e-3))


def synth_sfx(kind: str, seed: int = 3) -> np.ndarray:
    rng = np.random.default_rng(seed)
    if kind == "whoosh":
        n = int(0.7 * SR)
        noise = rng.standard_normal(n)
        out = np.zeros(n)
        centers = [250, 450, 800, 1400, 2400]
        t = np.arange(n) / SR
        for i, c in enumerate(centers):
            band = fft_band(noise, c * 0.7, c * 1.4)
            peak = 0.18 + i * 0.07
            out += band * np.exp(-((t - peak) / 0.11) ** 2)
        out *= np.sin(np.pi * np.clip(t / 0.7, 0, 1)) ** 1.5
    elif kind == "ping":
        n = int(0.9 * SR)
        t = np.arange(n) / SR
        out = (np.sin(2 * math.pi * 1174.66 * t) + 0.35 * np.sin(2 * math.pi * 2349.3 * t)) * _env_ad(n, 0.006, 0.22)
    elif kind == "rumble":
        n = int(1.3 * SR)
        t = np.arange(n) / SR
        low = fft_band(rng.standard_normal(n), 25, 140)
        out = (low / (np.std(low) + 1e-9) * 0.7 + 0.6 * np.sin(2 * math.pi * 52 * t)) * np.sin(np.pi * np.clip(t / 1.3, 0, 1)) ** 2
    elif kind == "hiss":
        n = int(0.9 * SR)
        hi = fft_band(rng.standard_normal(n), 2500, 9000)
        out = hi * _env_ad(n, 0.03, 0.28)
    elif kind == "thump":
        n = int(0.5 * SR)
        t = np.arange(n) / SR
        f = 90 * np.exp(-t * 9) + 38
        out = np.sin(2 * math.pi * np.cumsum(f) / SR) * _env_ad(n, 0.004, 0.11)
    elif kind == "tick":
        n = int(0.12 * SR)
        click = fft_band(rng.standard_normal(n), 1500, 6000)
        out = click * _env_ad(n, 0.001, 0.018)
    else:
        raise ValueError(kind)
    out = out / (np.max(np.abs(out)) + 1e-9)
    return fades(out, 0.004, 0.02)


@dataclass
class PlacedSfx:
    t: float
    kind: str
    over_speech: bool
    gain_db: float
    scene: str


def _speech_windows(timings: list[SceneTiming], pad: float = 0.0) -> list[tuple[float, float, bool, str]]:
    wins = []
    for tm in timings:
        for w in tm.words:
            wins.append((tm.start + w.start - pad, tm.start + w.end + pad, False, tm.id))
    return wins


def plan_sfx(plan: Plan, timings: list[SceneTiming], total: float) -> tuple[list[PlacedSfx], list[str]]:
    """Choose a *small* set of informative effects and place them safely."""
    from .subtitles import keyword_flags
    notes: list[str] = []
    cands = []
    scene_by_id = {s.id: s for s in plan.scenes}
    for tm in timings:
        sc = scene_by_id[tm.id]
        flags = keyword_flags(tm.words, sc.keywords)
        for cue in sc.sfx:
            if not tm.words:
                continue
            i = min(max(cue.at_word, 0), len(tm.words) - 1)
            cands.append((tm.start + tm.words[i].start, cue, tm, flags))
    cands.sort(key=lambda c: c[0])
    max_n = max(1, int(round(total * MAX_SFX_RATE)))
    placed: list[PlacedSfx] = []
    keyword_windows = []
    other_windows = []
    for tm in timings:
        sc = scene_by_id[tm.id]
        flags = keyword_flags(tm.words, sc.keywords)
        for w, fl in zip(tm.words, flags):
            (keyword_windows if fl else other_windows).append((tm.start + w.start, tm.start + w.end))
    counts: dict[str, int] = {}
    for t0, cue, tm, flags in cands:
        if len(placed) >= max_n:
            notes.append(f"efecto '{cue.type}' omitido: límite de {max_n} efectos")
            continue
        if counts.get(cue.type, 0) >= 2:
            notes.append(f"efecto '{cue.type}' omitido: ya se usó 2 veces")
            continue
        if placed and placed[-1].kind == cue.type:
            notes.append(f"efecto '{cue.type}' omitido: repetiría el anterior")
            continue
        if placed and t0 - placed[-1].t < MIN_SFX_SPACING:
            notes.append(f"efecto '{cue.type}' omitido: demasiado cerca del anterior")
            continue
        dur = len(synth_sfx(cue.type)) / SR
        # find a start (within +-0.9 s) whose window avoids every key word
        best = None
        for shift in [0.0, -0.15, 0.15, -0.3, 0.3, -0.5, 0.5, 0.7, 0.9, 1.1]:
            s = t0 + shift
            if s < 0.05 or s + dur > total - 0.2:
                continue
            e = s + min(dur, 0.8)
            if any(not (e <= a - 0.05 or s >= b + 0.05) for a, b in keyword_windows):
                continue
            over = any(not (e <= a or s >= b) for a, b in other_windows)
            if best is None or (best[1] and not over):
                best = (s, over)
            if not over:
                break
        if best is None:
            notes.append(f"efecto '{cue.type}' omitido: cae sobre palabras clave")
            continue
        s, over = best
        placed.append(PlacedSfx(s, cue.type, over, SFX_OVER_SPEECH_DB if over else SFX_GAP_DB, tm.id))
        counts[cue.type] = counts.get(cue.type, 0) + 1
    return placed, notes


def voice_track(timings: list[SceneTiming], total: float) -> np.ndarray:
    n = int(math.ceil(total * SR)) + SR
    v = np.zeros(n)
    for tm in timings:
        if not tm.audio_path:
            continue
        clip = decode(tm.audio_path)
        a = int(round((tm.start + tm.lead) * SR))
        v[a:a + len(clip)] += clip[: max(0, n - a)]
    return v[: int(round(total * SR))]


def process_voice(in_wav: str, out_wav: str):
    """Clean, tame and add presence so speech survives phone speakers."""
    af = ("highpass=f=75,lowpass=f=14000,"
          "acompressor=threshold=-22dB:ratio=2.4:attack=8:release=140:makeup=3,"
          "equalizer=f=3200:t=q:w=0.9:g=2.5,equalizer=f=220:t=q:w=1:g=-1.5,"
          "alimiter=limit=0.85:level=disabled")
    subprocess.run([_ff(), "-y", "-v", "error", "-i", in_wav, "-af", af, out_wav], check=True)


def duck_gain(total: float, timings: list[SceneTiming]) -> np.ndarray:
    n = int(round(total * SR))
    active = np.zeros(n)
    for tm in timings:
        for w in tm.words:
            a = max(0, int((tm.start + w.start - 0.10) * SR))
            b = min(n, int((tm.start + w.end + 0.18) * SR))
            active[a:b] = 1.0
    # smooth: fast attack (60 ms), slow release (450 ms)
    out = np.zeros(n)
    att = 1 - math.exp(-1 / (0.06 * SR))
    rel = 1 - math.exp(-1 / (0.45 * SR))
    # vectorised via block processing at 441-sample resolution
    blk = 441
    m = int(math.ceil(n / blk))
    a_blk = np.array([active[i * blk:(i + 1) * blk].max() for i in range(m)])
    s = 0.0
    sm = np.zeros(m)
    for i in range(m):
        k = 1 - (1 - att) ** blk if a_blk[i] > s else 1 - (1 - rel) ** blk
        s += (a_blk[i] - s) * k
        sm[i] = s
    out = np.repeat(sm, blk)[:n]
    return db(MUSIC_DUCK_DB * out)


def build_mix(plan: Plan, timings: list[SceneTiming], total: float, workdir: str,
              music: str = "ambient") -> dict:
    """Create voice/music/sfx stems, mix them and return stem paths + stats."""
    import os
    os.makedirs(workdir, exist_ok=True)
    raw_voice = voice_track(timings, total)
    write_wav(f"{workdir}/voice_raw.wav", raw_voice)
    process_voice(f"{workdir}/voice_raw.wav", f"{workdir}/voice.wav")
    voice = read_wav(f"{workdir}/voice.wav")
    n = int(round(total * SR))
    voice = np.pad(voice, (0, max(0, n - len(voice))))[:n]
    speech_rms = rms_db(voice[np.abs(voice) > 1e-4]) if np.any(np.abs(voice) > 1e-4) else -30.0
    # normalise voice so its speech RMS sits at -19 dBFS (peak-safe due to limiter)
    voice = voice * db(-19.0 - speech_rms)
    voice = np.clip(voice, -0.95, 0.95)
    ref = -19.0
    voice_peak = peak_db(voice)
    # music
    if music == "none":
        bed = np.zeros(n)
    else:
        m = synth_ambient(total + 1.0)[:n]
        m = m / (np.sqrt(np.mean(m ** 2)) + 1e-9)
        m = m * db(ref + MUSIC_BASE_DB) * duck_gain(total, timings)
        bed = fades(m, 1.0, 2.2)
    # sfx
    sfx_events, notes = plan_sfx(plan, timings, total)
    sfx = np.zeros(n)
    for ev in sfx_events:
        s = synth_sfx(ev.kind)
        a = int(ev.t * SR)
        active = s[np.abs(s) > 0.05]
        s_rms = rms_db(active) if len(active) else -12.0
        s = s * db(ref + ev.gain_db - s_rms)
        s = s * min(1.0, db(voice_peak - 4.0) / max(np.max(np.abs(s)), 1e-9))  # never louder than speech peaks
        sfx[a:a + len(s)] += s[: max(0, n - a)]
    write_wav(f"{workdir}/music.wav", bed)
    write_wav(f"{workdir}/sfx.wav", sfx)
    mix = voice + bed + sfx
    mix = mix * min(1.0, 0.89 / max(np.max(np.abs(mix)), 1e-9))
    write_wav(f"{workdir}/premix.wav", mix)
    return {
        "voice": f"{workdir}/voice.wav", "music": f"{workdir}/music.wav", "sfx": f"{workdir}/sfx.wav",
        "premix": f"{workdir}/premix.wav", "sfx_events": [ev.__dict__ for ev in sfx_events], "sfx_notes": notes,
        "voice_gain_ref_db": ref,
    }


def _loudnorm_json(stderr: str) -> dict:
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", stderr, re.S)
    return json.loads(m.group(0)) if m else {}


def loudnorm_encode(premix: str, out_audio: str, target: float = TARGET_LUFS, tp: float = -1.5) -> dict:
    """Two-pass EBU R128 normalisation to ``target`` LUFS with a true-peak ceiling."""
    p1 = subprocess.run(
        [_ff(), "-hide_banner", "-nostats", "-i", premix, "-af",
         f"loudnorm=I={target}:TP={tp}:LRA=11:print_format=json", "-f", "null", "-"],
        capture_output=True, text=True)
    meas = _loudnorm_json(p1.stderr)
    if not meas:
        raise RuntimeError("loudnorm analysis failed: " + p1.stderr[-400:])
    af = (f"loudnorm=I={target}:TP={tp}:LRA=11:measured_I={meas['input_i']}:measured_TP={meas['input_tp']}:"
          f"measured_LRA={meas['input_lra']}:measured_thresh={meas['input_thresh']}:offset={meas['target_offset']}:"
          f"linear=true:print_format=summary,alimiter=limit=0.89:level=disabled")
    subprocess.run([_ff(), "-y", "-v", "error", "-i", premix, "-af", af, "-ar", "44100", "-ac", "2",
                    "-c:a", "aac", "-b:a", "192k", out_audio], check=True)
    return meas


def measure_loudness(path: str) -> dict:
    """Integrated loudness / true peak of the final file (audio stream)."""
    p = subprocess.run([_ff(), "-hide_banner", "-nostats", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True)
    txt = p.stderr
    summ = txt[txt.rfind("Summary:"):]
    i = re.search(r"I:\s+(-?[\d.]+)\s+LUFS", summ)
    tp = re.search(r"Peak:\s+(-?[\d.]+)\s+dBFS", summ)
    lra = re.search(r"LRA:\s+(-?[\d.]+)\s+LU", summ)
    return {
        "integrated_lufs": float(i.group(1)) if i else None,
        "true_peak_dbtp": float(tp.group(1)) if tp else None,
        "lra": float(lra.group(1)) if lra else None,
    }
