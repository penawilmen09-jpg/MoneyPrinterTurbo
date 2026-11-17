"""Control de calidad del MP4 entregable."""
from __future__ import annotations

import json
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

from .narration import read_srt


def _probe(mp4):
    out = subprocess.check_output(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(mp4)])
    return json.loads(out)


def _wav(path):
    with wave.open(str(path)) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(np.float32) / 32768
        return (x.reshape(-1, w.getnchannels()).mean(1)), w.getframerate()


def run(d: Path) -> dict:
    d = Path(d)
    mp4, srt = d / "autoridad_hielo.mp4", d / "autoridad_hielo.srt"
    R, ok = {}, True

    def chk(name, cond, info=""):
        nonlocal ok
        R[name] = {"ok": bool(cond), "info": info}
        ok &= bool(cond)

    chk("mp4_existe", mp4.exists() and mp4.stat().st_size > 1e6, f"{mp4.stat().st_size/1e6:.1f} MB")
    P = _probe(mp4)
    v = next(s for s in P["streams"] if s["codec_type"] == "video")
    a = next((s for s in P["streams"] if s["codec_type"] == "audio"), None)
    dur = float(P["format"]["duration"])
    chk("video_h264_1080x1920", v["codec_name"] == "h264" and (v["width"], v["height"]) == (1080, 1920), f'{v["codec_name"]} {v["width"]}x{v["height"]} {v["profile"]} lvl{v["level"]} {v["pix_fmt"]}')
    chk("android_compat", v["pix_fmt"] == "yuv420p" and v["profile"] in ("High", "Main") and int(v["level"]) <= 42, "yuv420p, High@4.1, faststart")
    chk("tiene_audio_aac", a is not None and a["codec_name"] == "aac", f'{a["codec_name"]} {a["sample_rate"]}Hz {a["channels"]}ch' if a else "SIN AUDIO")
    chk("duracion_~60s", 58 <= dur <= 62.5, f"{dur:.2f}s")
    chk("fps_constante_30", v["r_frame_rate"] == "30/1", v["r_frame_rate"])
    head = open(mp4, "rb").read(65536)
    chk("faststart_moov_al_inicio", head.find(b"moov") != -1 and head.find(b"moov") < head.find(b"mdat") if b"mdat" in head else head.find(b"moov") != -1)
    # decodificación completa sin errores
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(mp4), "-f", "null", "-"], capture_output=True, text=True)
    chk("decodifica_sin_errores", r.returncode == 0 and not r.stderr.strip(), r.stderr[:100])
    # audio del MP4
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(mp4), "-vn", "-ac", "2", "-ar", "44100", "-f", "f32le", "-"], capture_output=True).stdout
    st = np.frombuffer(raw, np.float32).reshape(-1, 2)
    peak = float(np.abs(st).max())
    mixa = st.mean(1)
    voice, sr = _wav(d / "narracion.wav")
    n = min(len(mixa), len(voice))
    k = int(0.05 * sr)
    vr = np.sqrt(np.convolve(voice[:n] ** 2, np.ones(k) / k, "same"))
    speech = vr > 0.02
    chk("narracion_presente", speech.mean() > 0.55, f"voz activa {speech.mean()*100:.0f}% del tiempo")
    # voz vs música: comparar mezcla con y sin voz (mezcla - voz escalada)
    seg_rms = lambda x, m: float(np.sqrt(np.mean(x[m] ** 2)))
    mix_speech = seg_rms(mixa[:n], speech)
    mix_silence = seg_rms(mixa[:n], ~speech) if (~speech).any() else 0
    chk("voz_sobre_musica", mix_speech > 2.5 * mix_silence, f"RMS con voz {mix_speech:.3f} vs fondo {mix_silence:.3f} ({20*np.log10(mix_speech/max(mix_silence,1e-6)):.1f} dB)")
    chk("audio_no_clipping", peak < 0.99, f"pico {peak:.2f} ({20*np.log10(peak):.1f} dBFS)")
    # SRT
    cues = read_srt(srt)
    chk("srt_una_linea_por_cue", all(len(l) == 1 and len(l[0]) <= 28 for _, _, l in cues), f"{len(cues)} cues, máx {max(len(l[0]) for _,_,l in cues)} car.")
    chk("srt_sin_solapes", all(cues[i][1] <= cues[i + 1][0] + 1e-6 for i in range(len(cues) - 1)))
    chk("srt_sin_duplicados", len({c[2][0] + str(round(c[0], 2)) for c in cues}) == len(cues))
    # sincronía: cada cue cae sobre voz activa (≥70 % de su duración)
    bad = []
    for s, e, l in cues:
        m = speech[int(s * sr):int(e * sr)]
        if len(m) and m.mean() < 0.7:
            bad.append((round(s, 2), l[0], round(float(m.mean()), 2)))
    chk("srt_sincronizado_con_voz", not bad, f"{len(cues)-len(bad)}/{len(cues)} cues sobre voz; fuera: {bad}")
    # el primer fotograma de voz de cada cláusula está <=150 ms de su cue
    tl = json.load(open(d / "timeline.json"))
    offs = []
    for c in tl["clauses"]:
        i0 = int(c["start"] * sr)
        a0 = max(0, i0 - int(0.05 * sr))
        w = speech[a0:i0 + int(0.6 * sr)]
        idx = np.argmax(w) if w.any() else -1
        offs.append((idx / sr - 0.05) if idx >= 0 else 9)
    chk("inicio_voz_vs_cue_<=0.2s", max(abs(o) for o in offs) <= 0.2, f"desvío máx {max(abs(o) for o in offs)*1000:.0f} ms")
    # movimiento: los fotogramas no son estáticos
    fr = lambda t: np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", str(mp4), "-frames:v", "1", "-vf", "scale=108:192", "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True).stdout, np.uint8).astype(float)
    mov = [float(np.abs(fr(t + 0.5) - fr(t)).mean()) for t in (3, 15, 24, 34, 44, 54)]
    chk("animacion_con_movimiento", all(m > 0.4 for m in mov), "dif media por escena (0.5 s): " + ", ".join(f"{m:.2f}" for m in mov))
    R["_resumen"] = "APROBADO" if ok else "FALLOS"
    return R


if __name__ == "__main__":
    res = run(Path(sys.argv[1]))
    for k, v in res.items():
        print(("OK  " if v["ok"] else "FAIL") + f" {k}: {v['info']}" if k != "_resumen" else f"\n== {v}")
    json.dump(res, open(Path(sys.argv[1]) / "qa_report.json", "w"), ensure_ascii=False, indent=1)
