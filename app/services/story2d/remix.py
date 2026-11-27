"""Re-mezcla de audio de un video ya renderizado (sin re-renderizar ni re-narrar).

Uso: python -m app.services.story2d.remix --work storage/story2d/work --out video.mp4
La narración se toma de la caché de ElevenLabs (no hay llamadas a la API).
"""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

import numpy as np
from scipy.signal import resample_poly

from . import audio, narration, script as S
from .build import Timeline, write_srt, make_cues
from .cues import build_cues_documental
from . import mixdown as mx

SR = audio.SR


def stoi_score(clean, noisy):
    from pystoi import stoi
    c = resample_poly(clean, 16000, SR)
    n = resample_poly(noisy, 16000, SR)
    return float(stoi(c, n, 16000, extended=False))


def margins(parts, final_mono_gain):
    v, m, s = parts["voice"], parts["music"].mean(axis=1), parts["sfx"].mean(axis=1)
    fr = int(0.1 * SR)
    nn = len(v) // fr * fr
    R = lambda x: np.sqrt(np.mean(x[:nn].reshape(-1, fr) ** 2, axis=1))
    vr, mr, sr_ = R(v), R(m), R(s)
    on = vr > 0.5 * parts["v_rms"]                                  # habla sostenida
    dm = 20 * np.log10(vr[on] / np.maximum(mr[on], 1e-7))
    ds = 20 * np.log10(vr[on] / np.maximum(sr_[on], 1e-7))
    return dm, ds


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", default="storage/story2d/work")
    ap.add_argument("--out", default="storage/story2d/cajero_robo_imposible.mp4")
    a = ap.parse_args(argv)
    work = Path(a.work).resolve()
    out = Path(a.out).resolve()
    stems = work / "stems_v2"
    stems.mkdir(parents=True, exist_ok=True)

    narr = narration.synth_beats(S.BEATS, work / "tts_eleven")      # solo caché
    T = Timeline(narr)
    voice_events = [(T.start(b), narr[b]["audio"]) for b, *_ in S.BEATS]
    music = audio.make_music(T.total + 1)
    parts = mx.mix_documental(T.total, voice_events, build_cues_documental(T), music)

    print("Efectos conservados (solo los que aportan a la historia):")
    for p in parts["placed"]:
        print(f"  {p['t']:6.2f}s {p['name']:7s} {p['rel_db']} dB bajo la voz  "
              f"(movido {p['shift']:+.2f}s, sobre habla: {p['over_speech']})")

    audio.write_wav(stems / "voz.wav", np.stack([parts["voice"]] * 2, 1))
    audio.write_wav(stems / "musica.wav", parts["music"])
    audio.write_wav(stems / "efectos.wav", parts["sfx"])
    pre = stems / "mezcla_pre.wav"
    audio.write_wav(pre, parts["mix"])
    final_wav = stems / "mezcla_final.wav"
    st = mx.normalize_file(pre, final_wav)
    I, TP = float(st["input_i"]), float(st["input_tp"])
    if abs(I + 14) > 0.7 or TP > -1.3:   # loudnorm dinámico no llegó: ganancia + limitador
        g = -14 - I
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(final_wav), "-af",
                        f"volume={g:.2f}dB,alimiter=limit=0.891:attack=2:release=60:level=disabled",
                        "-c:a", "pcm_s16le", str(stems / "mezcla_final2.wav")], check=True)
        final_wav = stems / "mezcla_final2.wav"
        st = mx._loudnorm_stats(final_wav)
        I, TP = float(st["input_i"]), float(st["input_tp"])
    print(f"Loudness final: {I:.1f} LUFS · pico real {TP:.1f} dBTP · LRA {st['input_lra']}")

    # ---- mux: se usa el video YA renderizado, sin tocar las animaciones
    video = work / "video.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-i", str(final_wav), "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-shortest", "-movflags", "+faststart",
                    str(out)], check=True)

    # ---- QA de inteligibilidad sobre el audio FINAL ya codificado
    dec = narration.load_wav(out)
    dm, ds = margins(parts, 0)
    print(f"Música bajo la voz en habla: media {dm.mean():.1f} dB · mínimo {dm.min():.1f} dB")
    print(f"Efectos bajo la voz en habla: mínimo {ds.min():.1f} dB (tramas con efecto: {(ds < 40).sum()})")
    n = min(len(dec), len(parts["voice"]))
    s_mix = stoi_score(parts["voice"][:n], dec[:n])
    s_music_only = stoi_score(parts["voice"][:n], (parts["voice"] + parts["music"].mean(axis=1))[:n])
    print(f"Inteligibilidad STOI (voz limpia vs mezcla final): {s_mix:.3f}  (≥0.95 = excelente)")
    # frase por frase
    worst = 1.0
    for b, *_ in S.BEATS:
        i0, i1 = int(T.start(b) * SR), int(T.end(b) * SR)
        sc = stoi_score(parts["voice"][i0:i1], dec[i0:i1])
        worst = min(worst, sc)
        print(f"  {b}: STOI {sc:.3f}")
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(out), "-af", "ebur128=peak=true",
                        "-f", "null", "-"], capture_output=True, text=True).stderr
    import re as _re
    print("Medición ebur128 del MP4 final:",
          _re.findall(r"\n\s+I:\s+(-?[\d.]+) LUFS", r)[-1], "LUFS ·",
          _re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r)[-1], "dBTP")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
