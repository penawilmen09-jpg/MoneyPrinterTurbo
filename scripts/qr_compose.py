"""Compose the final QR explainer: animated video + ElevenLabs narration +
Whisper subtitles (burned in) + soft synthesized ambient music (auto-ducked)."""
import math
import re
import subprocess
import sys

import numpy as np

SR = 44100


def make_music(path, dur):
    n = int(SR * (dur + 1))
    t = np.arange(n) / SR
    chords = [  # soft major/minor-7 pads (Hz)
        [130.81, 196.00, 246.94, 329.63],   # Cmaj7
        [110.00, 164.81, 220.00, 261.63],   # Am
        [87.31, 130.81, 174.61, 261.63],    # F
        [98.00, 146.83, 196.00, 246.94],    # G
    ]
    seg = 6.9
    out = np.zeros(n)
    for i in range(int(dur / seg) + 2):
        ch = chords[i % 4]
        s0 = i * seg
        env = np.clip((t - s0) / 2.2, 0, 1) * np.clip((s0 + seg + 2.0 - t) / 2.2, 0, 1)
        env = np.where((t >= s0) & (t < s0 + seg + 2.2), env, 0)
        for f in ch:
            for det in (-0.4, 0.4):
                out += env * np.sin(2 * math.pi * (f + det) * t) * 0.07
    # gentle plucks (pentatonic), sparse
    rng = np.random.default_rng(3)
    scale = [523.25, 587.33, 659.25, 783.99, 880.0]
    for k in range(int(dur / 1.725)):
        t0 = k * 1.725 + 0.35
        f = scale[int(rng.integers(0, 5))]
        m = t >= t0
        e = np.exp(-(t - t0) * 2.6) * m
        out += e * np.sin(2 * math.pi * f * t) * 0.035
    out *= np.clip(t / 1.5, 0, 1) * np.clip((dur - t) / 3.0, 0, 1)
    # simple stereo + lowpass-ish smoothing
    k = np.ones(8) / 8
    out = np.convolve(out, k, mode="same")
    peak = np.max(np.abs(out)) or 1
    out = out / peak * 0.5
    st = np.stack([out, np.roll(out, 220)], axis=1)
    pcm = (st * 32767).astype("<i2")
    import wave
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def srt_to_ass(srt, ass, maxc=28):
    def ts(s):
        h = int(s // 3600); m = int(s % 3600 // 60); sec = s % 60
        return f"{h}:{m:02d}:{sec:05.2f}"

    def parse(x):
        h, m, rest = x.split(":")
        sec, ms = rest.replace(",", ".").split(".")
        return int(h) * 3600 + int(m) * 60 + float(sec + "." + ms)

    blocks = re.split(r"\n\s*\n", open(srt, encoding="utf-8").read().strip())
    events = []
    for b in blocks:
        ls = b.strip().splitlines()
        a, z = [parse(x.strip()) for x in ls[1].split("-->")]
        words = " ".join(ls[2:]).split()
        chunks, cur = [], ""
        for w in words:
            if cur and len(cur) + 1 + len(w) > maxc:
                chunks.append(cur); cur = w
            else:
                cur = (cur + " " + w).strip()
        if cur:
            chunks.append(cur)
        tot = sum(len(c) for c in chunks) or 1
        t0 = a
        for c in chunks:
            d = (z - a) * len(c) / tot
            events.append((t0, t0 + d, c))
            t0 += d
    hdr = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Default,Inter,62,&H00FFFFFF,&H000000FF,&H00301808,&H80000000,-1,0,0,0,100,100,0,0,1,6,2,2,70,70,330,1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""
    with open(ass, "w", encoding="utf-8") as f:
        f.write(hdr)
        for a, z, c in events:
            f.write(f"Dialogue: 0,{ts(a)},{ts(z - 0.02)},Default,,0,0,0,,{c}\n")


if __name__ == "__main__":
    video, voice, srt, out, work = sys.argv[1:6]
    music = f"{work}/music.wav"
    ass = f"{work}/subs.ass"
    make_music(music, 55.0)
    srt_to_ass(srt, ass)
    fc = (
        "[1:a]volume=1.4,asplit=2[vo][sc];"
        "[2:a]volume=0.55[m0];"
        "[m0][sc]sidechaincompress=threshold=0.015:ratio=10:attack=15:release=500[md];"
        "[vo][md]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[a];"
        f"[0:v]subtitles={ass}:fontsdir=/usr/share/fonts/opentype/inter[v]"
    )
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-i", video, "-i", voice, "-i", music,
        "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-t", "55", "-movflags", "+faststart", out,
    ], check=True)
