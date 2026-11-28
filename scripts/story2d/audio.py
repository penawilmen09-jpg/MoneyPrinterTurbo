"""Música sintetizada, 3 efectos importantes y mezcla final (-14 LUFS / -1 dBTP).

Todo se genera localmente con numpy + ffmpeg; la voz es la narración de ElevenLabs.
"""
import json
import os
import re
import subprocess
import sys
import wave

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import render as R

WORK = R.WORK
SR = 44100
LEAD, TOTAL = R.LEAD, R.TOTAL
rng = np.random.default_rng(42)


def wav_write(path, x):
    x = np.clip(x, -1, 1)
    if x.ndim == 1:
        x = np.stack([x, x], 1)
    pcm = (x * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def lp(x, n):
    k = np.ones(n) / n
    return np.convolve(x, k, mode="same")


def tt(n):
    return np.arange(n) / SR


# ------------------------------------------------------------------ música
def music(dur):
    n = int(dur * SR)
    t = tt(n)
    out = np.zeros((n, 2))
    def pad(freqs, amp, lfo_rate, phase):
        s = np.zeros(n)
        for i, f in enumerate(freqs):
            for det in (-0.35, 0.0, 0.4):
                s += np.sin(2 * np.pi * (f + det) * t + i) * 0.5
                s += np.sin(2 * np.pi * (2 * f + det * 2) * t) * 0.12
        lfo = 0.65 + 0.35 * np.sin(2 * np.pi * lfo_rate * t + phase)
        return s * lfo * amp
    base = pad([36.7, 55.0, 73.4], 0.5, 0.06, 0)                       # Re menor, muy grave
    mid = pad([110.0, 174.6], 0.18, 0.045, 1.5)
    # tensión: segunda menor que entra hacia el minuto 0:30
    tens_env = np.clip((t - 28) / 10, 0, 1) * np.clip((t - 52) / -8 + 1, 0, 1)
    tens = pad([77.8, 116.5], 0.22, 0.09, 0.7) * tens_env
    # brillo fantasmal
    shim = (np.sin(2 * np.pi * 1318.5 * t) + np.sin(2 * np.pi * 1397 * t)) * 0.012 * (0.5 + 0.5 * np.sin(2 * np.pi * 0.11 * t))
    wind = lp(rng.normal(0, 1, n), 160) * 0.5
    wind = wind * (0.4 + 0.6 * np.sin(2 * np.pi * 0.05 * t + 2) ** 2)
    # latido lejano (se intensifica en el clímax)
    beat = np.zeros(n)
    bpm_t = 60 / 66
    k = 0
    while k * bpm_t < dur:
        for off, a in ((0.0, 1.0), (0.28, 0.6)):
            i0 = int((k * bpm_t + off) * SR)
            L = int(0.35 * SR)
            if i0 + L < n:
                tau = np.arange(L) / SR
                beat[i0:i0 + L] += np.sin(2 * np.pi * (52 - 18 * tau) * tau) * np.exp(-tau * 11) * a
        k += 1
    beat *= np.clip((t - 30) / 8, 0, 1) * 0.35
    mono = base + mid + tens + shim + wind + beat
    fade = np.clip(t / 2.5, 0, 1) * np.clip((dur - t) / 2.5, 0, 1)
    mono *= fade
    out[:, 0] = mono
    out[:, 1] = np.roll(mono, 55) * 0.96  # leve ensanchamiento
    return out / (np.abs(out).max() + 1e-9) * 0.8


# ------------------------------------------------------------------ efectos
def ring(length):
    n = int(length * SR)
    t = tt(n)
    x = np.zeros(n)
    cyc = 1.5
    notes = [987.8, 1318.5, 987.8, 1318.5, 987.8, 1318.5]
    k = 0
    while k * cyc < length:
        for i, f in enumerate(notes):
            i0 = int((k * cyc + i * 0.11) * SR)
            L = int(0.2 * SR)
            if i0 + L > n:
                continue
            tau = np.arange(L) / SR
            tone = (np.sin(2 * np.pi * f * tau) + 0.35 * np.sin(2 * np.pi * 2 * f * tau)) * np.exp(-tau * 14)
            tone *= np.minimum(1, tau / 0.004)
            x[i0:i0 + L] += tone
        # vibración grave
        v0, v1 = int(k * cyc * SR), min(n, int((k * cyc + 0.75) * SR))
        if v1 > v0:
            tv = np.arange(v1 - v0) / SR
            x[v0:v1] += 0.22 * np.sin(2 * np.pi * 135 * tv) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 22 * tv)))
        k += 1
    x *= np.clip((length - t) / 0.25, 0, 1)
    return x / (np.abs(x).max() + 1e-9) * 0.9


def ding():
    L = int(1.6 * SR)
    tau = np.arange(L) / SR
    x = np.sin(2 * np.pi * 1760 * tau) * np.exp(-tau * 4.2)
    x += 0.6 * np.sin(2 * np.pi * 2349 * tau) * np.exp(-tau * 5.0)
    y = np.zeros(L + int(0.18 * SR))
    y[:L] += x
    y[int(0.18 * SR):int(0.18 * SR) + L] += x * 0.7
    return y[:L] / np.abs(y[:L]).max() * 0.8


def sting():
    """Subida breve + golpe grave en la revelación del conductor."""
    rise_len = int(1.1 * SR)
    tau = np.arange(rise_len) / SR
    noise = lp(rng.normal(0, 1, rise_len), 40) * (tau / tau[-1]) ** 2.5 * 0.5
    tone = np.sin(2 * np.pi * (180 + 160 * tau) * tau) * (tau / tau[-1]) ** 3 * 0.18
    hit_len = int(2.4 * SR)
    h = np.arange(hit_len) / SR
    hit = np.sin(2 * np.pi * (80 - 34 * np.minimum(h, 0.5) / 0.5) * h) * np.exp(-h * 2.1)
    hit += 0.3 * np.sin(2 * np.pi * 311 * h) * np.exp(-h * 3.0) + 0.25 * np.sin(2 * np.pi * 329.6 * h) * np.exp(-h * 3.0)
    out = np.zeros(rise_len + hit_len)
    out[:rise_len] += noise + tone
    out[rise_len:] += hit
    return out / np.abs(out).max() * 0.9, rise_len


def place(buf, clip, t0):
    i0 = int(t0 * SR)
    j = min(len(buf), i0 + len(clip))
    if i0 < len(buf):
        buf[i0:j] += clip[:j - i0]


def sh(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def lufs(path, start=None, dur=None):
    cmd = ["ffmpeg", "-nostats", "-hide_banner"]
    if start is not None:
        cmd += ["-ss", str(start), "-t", str(dur)]
    cmd += ["-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"]
    r = sh(cmd).stderr
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", r)
    p = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r)
    return float(m[-1]), float(p[-1]) if p else None


def main():
    # 1 · voz
    v_raw = f"{WORK}/voice_raw.wav"
    sh(["ffmpeg", "-y", "-i", f"{WORK}/narration.mp3", "-ar", str(SR), "-ac", "2", v_raw])
    sh(["ffmpeg", "-y", "-i", v_raw, "-af",
        f"adelay={int(LEAD*1000)}|{int(LEAD*1000)},highpass=f=80,equalizer=f=3200:t=q:w=1:g=1.5,"
        "acompressor=threshold=-20dB:ratio=2.5:attack=12:release=140:makeup=3,"
        f"apad=whole_dur={TOTAL:.3f},atrim=0:{TOTAL:.3f}", f"{WORK}/voice.wav"])
    V, _ = lufs(f"{WORK}/voice.wav", LEAD, R.a_end - LEAD)
    print("voz (habla) LUFS", V)

    # 2 · música
    m = music(TOTAL + 0.5)[: int(TOTAL * SR)]
    wav_write(f"{WORK}/music.wav", m)
    M, _ = lufs(f"{WORK}/music.wav")

    # 3 · efectos (3 tipos)
    s = np.zeros(int(TOTAL * SR))
    place(s, ring(LEAD + 0.15), 0.0)                              # 1) teléfono, antes de la voz
    place(s, ring(2.4) * 0.8, R.a_desde)                          # 1) mismo teléfono al final
    place(s, ring(R.TOTAL - R.a_end - 1.9), R.a_end)
    place(s, ding(), R.a_msg + 2.1 + 0.2)                         # 2) mensaje entrante
    st, rl = sting()
    place(s, st, R.a_alg - rl / SR + 0.05)                         # 3) revelación del conductor
    wav_write(f"{WORK}/sfx.wav", s)
    SFX, _ = lufs(f"{WORK}/sfx.wav")
    print("LUFS música", M, "sfx", SFX)

    # 4 · niveles objetivo respecto a la voz (antes del ducking)
    g_mus = (V - 14.0) - M      # música ≈ -17 dB (≈ -24 dB al ducking)
    g_sfx = (V - 7.0) - SFX    # efectos ≈ -14.5 dB
    cmp_mus = "sidechaincompress=threshold=0.12:ratio=2.4:attack=30:release=800:makeup=1"
    cmp_sfx = "sidechaincompress=threshold=0.2:ratio=2:attack=6:release=200:makeup=1"
    fg = (f"[0:a]asplit=3[v0][v1][v2];"
          f"[1:a]volume={g_mus}dB,aecho=0.8:0.6:90|170:0.25|0.15[m];"
          f"[2:a]volume={g_sfx}dB,aecho=0.8:0.5:60:0.2[s];"
          f"[m][v1]{cmp_mus}[md];[s][v2]{cmp_sfx}[sd];"
          f"[md]asplit=2[md1][md2];[sd]asplit=2[sd1][sd2];"
          f"[v0][md1][sd1]amix=inputs=3:normalize=0:duration=first[mix]")
    sh(["ffmpeg", "-y", "-i", f"{WORK}/voice.wav", "-i", f"{WORK}/music.wav", "-i", f"{WORK}/sfx.wav",
        "-filter_complex", fg, "-map", "[mix]", f"{WORK}/premix.wav",
        "-map", "[md2]", f"{WORK}/music_ducked.wav", "-map", "[sd2]", f"{WORK}/sfx_ducked.wav"])
    # niveles reales durante el habla
    Md, _ = lufs(f"{WORK}/music_ducked.wav", LEAD, R.a_end - LEAD)
    Sd, _ = lufs(f"{WORK}/sfx_ducked.wav", LEAD, R.a_end - LEAD)
    print(f"durante el habla: música {Md - V:+.1f} dB, efectos {Sd - V:+.1f} dB respecto a la voz")

    # 5 · normalización final (dos pasadas)
    r = sh(["ffmpeg", "-nostats", "-hide_banner", "-i", f"{WORK}/premix.wav", "-af",
            "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"]).stderr
    j = json.loads(r[r.rfind("{"):])
    ln = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:"
          f"measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true,"
          "alimiter=limit=0.89:level=false")
    sh(["ffmpeg", "-y", "-i", f"{WORK}/premix.wav", "-af", ln, "-ar", "48000", f"{WORK}/final_audio.wav"])
    I, P = lufs(f"{WORK}/final_audio.wav")
    print(f"FINAL: {I} LUFS integrado, pico de muestra {P} dBFS")
    json.dump({"voice_lufs": V, "final_lufs": I, "peak": P, "music_vs_voice_db": Md - V, "sfx_vs_voice_db": Sd - V},
              open(f"{WORK}/audio_report.json", "w"))


if __name__ == "__main__":
    main()
