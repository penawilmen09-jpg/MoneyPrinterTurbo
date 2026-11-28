#!/usr/bin/env python3
"""Chinese -> Latin-American Spanish dubbing helper (single ElevenLabs voice).

Stages (run in order, all files live in --work):
  separate    MDX-Net (onnxruntime) vocal split: vocals.wav + accomp.wav (= original - vocals)
  transcribe  faster-whisper (zh) -> zh.json   [--whisper-dir: local faster-whisper model dir]
  (translate) write es.txt by hand/LLM: one line per sentence group  "a-b|texto"  (segment index range)
  synth       ElevenLabs TTS through app.services.voice, ALWAYS the one voice below
  mix         timeline fit (tempo <= 1.2), dub track, Spanish SRT, ducked mix with the accompaniment
  mux         (optional) put the mixed audio on a video, keeping its resolution/orientation

The API key is read by the existing integration (config.toml or ELEVENLABS_API_KEY); never pass it here.
No Edge TTS, no other voices.
"""
import argparse, json, os, re, subprocess, sys, textwrap
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VOICE = "elevenlabs:dlGxemPxFMTY7iXagmOj:Voz 2"  # the only voice used for every character
SR = 44100


def sh(*a, **k):
    return subprocess.run(a, check=True, **k)


def stage_prepare(w, src):
    sh("ffmpeg", "-v", "error", "-y", "-i", src, "-vn", "-ar", str(SR), "-ac", "2", f"{w}/orig.wav")


def stage_separate(w, model, nfft, comp):
    import onnxruntime as ort
    HOP, DIM_F, DIM_T = 1024, 3072, 256
    raw = sh("ffmpeg", "-v", "error", "-i", f"{w}/orig.wav", "-f", "f32le", "-ac", "2", "-ar", str(SR), "-", capture_output=True).stdout
    mix = np.frombuffer(raw, np.float32).reshape(-1, 2).T.copy()
    n = mix.shape[1]
    win = np.hanning(nfft + 1)[:-1].astype(np.float32)

    def stft(x):
        p = nfft // 2
        xp = np.pad(x, (p, p), mode="reflect")
        nf = 1 + (len(xp) - nfft) // HOP
        idx = np.arange(nfft)[None, :] + HOP * np.arange(nf)[:, None]
        return np.fft.rfft(xp[idx] * win, axis=1).T

    def istft(X, length):
        fr = np.fft.irfft(X.T, n=nfft, axis=1) * win
        out = np.zeros(HOP * (X.shape[1] - 1) + nfft, np.float32); ws = np.zeros_like(out)
        for i in range(X.shape[1]):
            out[i*HOP:i*HOP+nfft] += fr[i]; ws[i*HOP:i*HOP+nfft] += win ** 2
        return (out / np.maximum(ws, 1e-8))[nfft // 2: nfft // 2 + length]

    chunk = HOP * (DIM_T - 1); trim = nfft // 2; gen = chunk - 2 * trim
    pad = gen - n % gen
    mp = np.concatenate([np.zeros((2, trim), np.float32), mix, np.zeros((2, pad + trim), np.float32)], axis=1)
    sess = ort.InferenceSession(model, providers=["CPUExecutionProvider"])
    outs = []
    for c in range((n + pad) // gen):
        seg = mp[:, c*gen:c*gen + chunk]
        specs = [stft(seg[ch]) for ch in range(2)]
        inp = np.zeros((1, 4, DIM_F, DIM_T), np.float32)
        for ch in range(2):
            inp[0, 2*ch] = specs[ch].real[:DIM_F, :DIM_T]; inp[0, 2*ch+1] = specs[ch].imag[:DIM_F, :DIM_T]
        o = sess.run(None, {"input": inp})[0][0] * comp
        res = []
        for ch in range(2):
            X = np.zeros((specs[0].shape[0], DIM_T), np.complex64)
            X[:DIM_F] = o[2*ch] + 1j * o[2*ch+1]
            res.append(istft(X, chunk)[trim:chunk-trim])
        outs.append(np.stack(res))
    voc = np.concatenate(outs, axis=1)[:, :n].astype(np.float32)
    for name, a in (("vocals", voc), ("accomp", mix - voc)):
        sh("ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", f"{w}/{name}.wav", input=a.T.astype(np.float32).tobytes())


def stage_transcribe(w, whisper_dir):
    from faster_whisper import WhisperModel
    m = WhisperModel(whisper_dir, device="cpu", compute_type="int8")
    segs, _ = m.transcribe(f"{w}/orig.wav", language="zh", vad_filter=True, beam_size=5)
    out = [{"start": round(s.start, 2), "end": round(s.end, 2), "zh": s.text.strip()} for s in segs]
    json.dump(out, open(f"{w}/zh.json", "w"), ensure_ascii=False, indent=1)


def load_groups(w):
    zh = json.load(open(f"{w}/zh.json")); groups, seen = [], []
    for l in open(f"{w}/es.txt", encoding="utf-8").read().splitlines():
        if not l.strip():
            continue
        r, t = l.split("|", 1)
        a, b = (map(int, r.split("-")) if "-" in r else (int(r),) * 2)
        seen += list(range(a, b + 1))
        groups.append({"a": a, "b": b, "start": zh[a]["start"], "end": zh[b]["end"], "es": t})
    assert seen == list(range(len(zh))), "es.txt must cover every transcribed segment exactly once, in order"
    return groups


def stage_synth(w):
    from concurrent.futures import ThreadPoolExecutor
    from app.services import voice
    os.makedirs(f"{w}/clips", exist_ok=True)
    groups = load_groups(w)
    json.dump(groups, open(f"{w}/groups.json", "w"), ensure_ascii=False, indent=1)

    def run(i):
        f = f"{w}/clips/{i:03d}.mp3"
        if os.path.exists(f) and os.path.getsize(f) > 1000:  # cached: no repeated credits
            return True
        return any(voice.tts(groups[i]["es"], VOICE, 1.0, f) is not None for _ in range(2))
    with ThreadPoolExecutor(3) as ex:
        ok = list(ex.map(run, range(len(groups))))
    print("synthesized", sum(ok), "of", len(ok))
    if not all(ok):
        sys.exit("some clips failed: " + str([i for i, k in enumerate(ok) if not k]))


def _decode(f, af):
    raw = sh("ffmpeg", "-v", "error", "-i", f, "-af", af, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-", capture_output=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def _ts(t):
    t = max(t, 0); ms = int(round(t * 1000))
    return f"{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}"


def stage_mix(w, max_tempo=1.2):
    g = json.load(open(f"{w}/groups.json"))
    trim = ("silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.03,areverse,"
            "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.03,areverse")
    cur, place = 0.0, []
    for i, x in enumerate(g):
        d = len(_decode(f"{w}/clips/{i:03d}.mp3", trim)) / SR
        start = max(x["start"], cur + 0.12) if i else x["start"]
        nxt = g[i+1]["start"] if i + 1 < len(g) else x["end"] + 3
        tempo = min(max(d / max(nxt - 0.08 - start, 0.3), 1.0), max_tempo)
        cur = start + d / tempo
        place.append({"start": start, "end": cur, "tempo": tempo})
    dur = float(sh("ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f"{w}/orig.wav", capture_output=True).stdout)
    buf = np.zeros(int(max(cur + 1, dur) * SR) + SR, np.float32)
    for i, p in enumerate(place):
        y = _decode(f"{w}/clips/{i:03d}.mp3", trim + (f",atempo={p['tempo']:.4f}" if p["tempo"] > 1.001 else ""))
        f = min(int(0.01 * SR), len(y)); y[:f] *= np.linspace(0, 1, f); y[-f:] *= np.linspace(1, 0, f)
        a = int(p["start"] * SR); buf[a:a+len(y)] += y; p["end"] = (a + len(y)) / SR
    sh("ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", f"{w}/dub_raw.wav", input=buf.tobytes())
    delays = [p["start"] - x["start"] for p, x in zip(place, g)]
    print(f"max delay vs original start {max(delays):.2f}s; clips at tempo cap: {sum(p['tempo'] >= max_tempo - 1e-3 for p in place)}")
    # Spanish-only SRT, <=2 lines of <=42 chars
    cues = []
    for x, p in zip(g, place):
        parts = [x["es"]] if len(x["es"]) <= 84 else [s for s in re.split(r"(?<=[.!?:;])\s+", x["es"]) if s]
        tot, t0 = sum(map(len, parts)), p["start"]
        for s in parts:
            dd = (p["end"] - p["start"]) * len(s) / tot; cues.append([t0, t0 + dd, s]); t0 += dd
    blocks = []
    for k, (s, e, t) in enumerate(cues, 1):
        if k < len(cues):
            e = min(e + 0.15, cues[k][0] - 0.02)
        lines = textwrap.wrap(t, 42)
        if len(lines) > 2:
            lines = textwrap.wrap(t, len(t) // 2 + 8)
        blocks.append(f"{k}\n{_ts(s)} --> {_ts(e)}\n" + "\n".join(lines) + "\n")
    open(f"{w}/dub_es.srt", "w", encoding="utf-8").write("\n".join(blocks))
    fc = ("[1:a]loudnorm=I=-16:TP=-1.5:LRA=7,pan=stereo|c0=c0|c1=c0,asplit=2[d][sc];"
          "[0:a][sc]sidechaincompress=threshold=0.02:ratio=5:attack=15:release=350[duck];"
          f"[duck][d]amix=inputs=2:normalize=0:duration=longest,loudnorm=I=-16:TP=-1.5:LRA=9,atrim=0:{dur:.3f}")
    sh("ffmpeg", "-v", "error", "-y", "-i", f"{w}/accomp.wav", "-i", f"{w}/dub_raw.wav", "-filter_complex", fc,
       "-ar", str(SR), "-c:a", "aac", "-b:a", "192k", f"{w}/dub_mix.m4a")


def stage_mux(w, video, out, burn):
    """Original video stream is copied unless subtitles are burned in (re-encode, same resolution)."""
    if burn:
        sh("ffmpeg", "-v", "error", "-y", "-i", video, "-i", f"{w}/dub_mix.m4a", "-map", "0:v:0", "-map", "1:a:0",
           "-vf", f"subtitles={w}/dub_es.srt:force_style='FontSize=20,Outline=2,MarginV=40'",
           "-c:v", "libx264", "-crf", "18", "-c:a", "copy", "-shortest", out)
    else:
        sh("ffmpeg", "-v", "error", "-y", "-i", video, "-i", f"{w}/dub_mix.m4a", "-i", f"{w}/dub_es.srt",
           "-map", "0:v:0", "-map", "1:a:0", "-map", "2:0", "-c:v", "copy", "-c:a", "copy", "-c:s", "mov_text",
           "-metadata:s:s:0", "language=spa", "-shortest", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stage", choices=["prepare", "separate", "transcribe", "synth", "mix", "mux"])
    ap.add_argument("--work", required=True)
    ap.add_argument("--input", help="source audio/video (prepare)")
    ap.add_argument("--mdx-model", help="Kim_Vocal_2.onnx path"); ap.add_argument("--nfft", type=int, default=7680); ap.add_argument("--comp", type=float, default=1.009)
    ap.add_argument("--whisper-dir"); ap.add_argument("--video"); ap.add_argument("--out"); ap.add_argument("--burn", action="store_true")
    a = ap.parse_args(); os.makedirs(a.work, exist_ok=True)
    {"prepare": lambda: stage_prepare(a.work, a.input), "separate": lambda: stage_separate(a.work, a.mdx_model, a.nfft, a.comp),
     "transcribe": lambda: stage_transcribe(a.work, a.whisper_dir), "synth": lambda: stage_synth(a.work),
     "mix": lambda: stage_mix(a.work), "mux": lambda: stage_mux(a.work, a.video, a.out, a.burn)}[a.stage]()
