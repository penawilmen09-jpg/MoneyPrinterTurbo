"""Automatic dubbing of an existing Spanish video with ONE ElevenLabs voice.

Pipeline (the picture stream is never re-encoded unless subtitles are burned in):

1. extract audio with FFmpeg
2. separate vocals / background (audio-separator MDX model; FFmpeg fallback)
3. transcribe the *vocals* with faster-whisper (Spanish, word timestamps)
4. synthesize every line with the SAME ElevenLabs voice (cached per text)
5. place each line on a timeline (time-stretch only when needed, never cut words)
6. mix: background (ducked slightly under the dub) + new voice
7. mux with the untouched video (``-c:v copy``), optionally with SRT / burned subs

Every character, man, woman or child, gets the same Voice ID by design.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import wave
from dataclasses import asdict, dataclass, field
from typing import Callable, Optional

import numpy as np
from loguru import logger

from app.services import voice as voice_service

# Single voice for every character (man / woman / child). Do not vary per speaker.
DEFAULT_VOICE_ID = "851ejYcv2BoNPjrkw93G"
DEFAULT_TTS_MODEL = "eleven_multilingual_v2"
SAMPLE_RATE = 44100
MAX_SPEEDUP = 1.35  # beyond this we prefer shifting later over a rushed voice
GAP = 0.06  # minimum seconds between two dubbed lines
SEPARATOR_MODEL = "UVR-MDX-NET-Voc_FT.onnx"

ProgressFn = Callable[[str, float, str], None]


@dataclass
class Segment:
    index: int
    start: float
    end: float
    text: str
    # filled after synthesis / placement
    tts_duration: float = 0.0
    placed_start: float = 0.0
    placed_end: float = 0.0
    speed: float = 1.0
    voice_id: str = ""
    audio_file: str = ""


@dataclass
class DubResult:
    output_video: str
    srt_path: str
    segments: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    separation: str = ""
    report_path: str = ""


# ---------------------------------------------------------------- helpers
def _run(cmd: list[str]) -> None:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"{cmd[0]} failed: {proc.stderr[-1500:]}")


def probe_duration(path: str) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
        capture_output=True,
        text=True,
    )
    return float(out.stdout.strip())


def _notify(cb: Optional[ProgressFn], stage: str, frac: float, msg: str) -> None:
    logger.info(f"[dub:{stage}] {frac:.0%} {msg}")
    if cb:
        cb(stage, frac, msg)


def fmt_srt_time(t: float) -> str:
    t = max(0.0, t)
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


# ------------------------------------------------------ 1/2. audio + stems
def extract_audio(video: str, out_wav: str) -> None:
    _run(["ffmpeg", "-y", "-v", "error", "-i", video, "-vn", "-ac", "2", "-ar", str(SAMPLE_RATE), out_wav])


def separate_sources(audio_wav: str, workdir: str) -> tuple[str, str, str]:
    """Return (vocals_wav, background_wav, method_description)."""
    vocals = os.path.join(workdir, "vocals.wav")
    background = os.path.join(workdir, "background.wav")
    marker = os.path.join(workdir, "separation.txt")
    if os.path.exists(vocals) and os.path.exists(background) and os.path.exists(marker):
        with open(marker, encoding="utf-8") as fh:
            return vocals, background, fh.read()
    try:
        from audio_separator.separator import Separator

        model_dir = os.path.join(os.path.expanduser("~"), ".cache", "audio-separator-models")
        sep = Separator(output_dir=workdir, output_format="WAV", model_file_dir=model_dir, log_level=40)
        sep.load_model(SEPARATOR_MODEL)
        files = sep.separate(audio_wav)
        voc = next((f for f in files if "(Vocals)" in f), None)
        ins = next((f for f in files if "(Instrumental)" in f), None)
        if not voc or not ins:
            raise RuntimeError(f"unexpected separator outputs: {files}")
        voc = voc if os.path.isabs(voc) else os.path.join(workdir, voc)
        ins = ins if os.path.isabs(ins) else os.path.join(workdir, ins)
        shutil.move(voc, vocals)
        shutil.move(ins, background)
        method = f"AI source separation ({SEPARATOR_MODEL})"
        with open(marker, "w", encoding="utf-8") as fh:
            fh.write(method)
        return vocals, background, method
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"source separation unavailable, using centre-channel fallback: {exc}")
        # Voices are usually panned centre: L-R keeps music/stereo FX, removes centre voice.
        _run(["ffmpeg", "-y", "-v", "error", "-i", audio_wav, "-af", "pan=stereo|c0=c0-c1|c1=c1-c0,volume=1.0", background])
        shutil.copy(audio_wav, vocals)
        return (
            vocals,
            background,
            "FALLBACK: centre-channel cancellation (voices may leak, music may lose body)",
        )


# --------------------------------------------------------- 3. transcription
def _split_long(words, max_len: float = 9.0):
    """Split a long segment at sentence punctuation using word timestamps."""
    chunks, cur = [], []
    for w in words:
        cur.append(w)
        dur = cur[-1].end - cur[0].start
        if dur >= max_len and re.search(r"[.!?…]$", w.word.strip()):
            chunks.append(cur)
            cur = []
    if cur:
        chunks.append(cur)
    return chunks


def transcribe(vocals_wav: str, model_size: str = "small", language: str = "es") -> list[Segment]:
    from faster_whisper import WhisperModel

    model = WhisperModel(model_size, device="cpu", compute_type="int8", cpu_threads=os.cpu_count() or 4)
    raw, _info = model.transcribe(
        vocals_wav,
        language=language,
        beam_size=5,
        word_timestamps=True,
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 350, "speech_pad_ms": 150},
        condition_on_previous_text=False,
    )
    pieces: list[tuple[float, float, str]] = []
    for seg in raw:
        text = seg.text.strip()
        if not text:
            continue
        if seg.no_speech_prob > 0.8 and seg.avg_logprob < -1.0:
            continue  # almost surely noise / music, not dialogue
        words = [w for w in (seg.words or []) if w.word.strip()]
        if words and (words[-1].end - words[0].start) > 10.0:
            for chunk in _split_long(words):
                pieces.append((chunk[0].start, chunk[-1].end, "".join(w.word for w in chunk).strip()))
        elif words:
            pieces.append((words[0].start, words[-1].end, text))
        else:
            pieces.append((seg.start, seg.end, text))
    pieces.sort(key=lambda p: p[0])
    return [Segment(i, s, e, t) for i, (s, e, t) in enumerate(pieces)]


# ------------------------------------------------------------ 4. synthesis
def synthesize(
    segments: list[Segment],
    workdir: str,
    voice_id: str = DEFAULT_VOICE_ID,
    model_id: str = DEFAULT_TTS_MODEL,
    progress: Optional[ProgressFn] = None,
) -> None:
    """One voice id for every segment; results are cached to avoid paying twice."""
    tts_dir = os.path.join(workdir, "tts")
    os.makedirs(tts_dir, exist_ok=True)
    for seg in segments:
        key = hashlib.sha1(f"{voice_id}|{model_id}|{seg.text}".encode()).hexdigest()[:20]
        path = os.path.join(tts_dir, f"{key}.mp3")
        if not (os.path.exists(path) and os.path.getsize(path) > 0):
            ok = voice_service.elevenlabs_tts(seg.text, voice_id, path, 1.0, 1.0, model_id)
            if not ok:
                raise RuntimeError(f"ElevenLabs failed for line {seg.index}: {seg.text[:60]!r}")
        seg.audio_file = path
        seg.voice_id = voice_id
        seg.tts_duration = probe_duration(path)
        _notify(progress, "voices", (seg.index + 1) / len(segments), f"Voz {seg.index + 1}/{len(segments)}")


# ------------------------------------------------------ 5. placement + mix
def _decode(path: str, tempo: float) -> np.ndarray:
    af = []
    if abs(tempo - 1.0) > 0.005:
        af = ["-af", f"atempo={tempo:.4f}"]  # pitch-preserving time stretch
    cmd = ["ffmpeg", "-v", "error", "-i", path, *af, "-ac", "1", "-ar", str(SAMPLE_RATE), "-f", "f32le", "-"]
    proc = subprocess.run(cmd, capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.decode()[-500:])
    return np.frombuffer(proc.stdout, dtype=np.float32).copy()


def schedule(segments: list[Segment], video_duration: float) -> list[str]:
    """Decide start time and speed of each line. Never drops or truncates words."""
    warnings: list[str] = []
    cursor = 0.0
    for i, seg in enumerate(segments):
        nxt_start = segments[i + 1].start if i + 1 < len(segments) else video_duration
        start = max(seg.start, cursor)
        orig_len = max(seg.end - seg.start, 0.3)
        available = max(nxt_start - start - GAP, 0.3)
        d = seg.tts_duration
        speed = 1.0
        if d > max(orig_len, available):
            speed = min(d / available, MAX_SPEEDUP)
        eff = d / speed
        seg.speed = round(speed, 3)
        seg.placed_start = start
        seg.placed_end = start + eff
        cursor = seg.placed_end + GAP
        if start - seg.start > 0.4:
            warnings.append(f"Línea {seg.index}: retrasada {start - seg.start:.2f}s (la locución previa ocupa más tiempo)")
        if seg.placed_end > video_duration + 0.05:
            warnings.append(f"Línea {seg.index}: termina {seg.placed_end - video_duration:.2f}s después del final del video")
    return warnings


def build_dub_track(segments: list[Segment], total_duration: float, out_wav: str) -> None:
    n = int((max(total_duration, segments[-1].placed_end if segments else 0) + 0.5) * SAMPLE_RATE)
    track = np.zeros(n, dtype=np.float32)
    for seg in segments:
        clip = _decode(seg.audio_file, seg.speed)
        # gentle fades avoid clicks at the edges
        f = min(int(0.008 * SAMPLE_RATE), len(clip) // 2)
        if f:
            clip[:f] *= np.linspace(0, 1, f)
            clip[-f:] *= np.linspace(1, 0, f)
        a = int(seg.placed_start * SAMPLE_RATE)
        track[a : a + len(clip)] += clip[: max(0, n - a)]
    # level the narration to a consistent loudness (RMS of active samples) ~ -20 dBFS
    active = track[np.abs(track) > 0.01]
    if active.size:
        rms = float(np.sqrt(np.mean(active**2)))
        track *= 0.1 / max(rms, 1e-6)
    track = np.clip(track, -0.98, 0.98)
    pcm = (track * 32767).astype("<i2")
    with wave.open(out_wav, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(pcm.tobytes())


def write_srt(segments: list[Segment], path: str) -> None:
    lines = []
    for n, s in enumerate(segments, 1):
        lines += [str(n), f"{fmt_srt_time(s.placed_start)} --> {fmt_srt_time(s.placed_end)}", _wrap(s.text), ""]
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


def _wrap(text: str, width: int = 38) -> str:
    words, lines, cur = text.split(), [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > width:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    return "\n".join(lines)


def mux(video: str, background: str, dub: str, out_mp4: str, srt: str | None, burn: bool, duration: float) -> None:
    graph = (
        "[1:a]aformat=sample_rates=44100:channel_layouts=stereo[bg];"
        "[2:a]aformat=sample_rates=44100:channel_layouts=mono,asplit=2[d1][d2];"
        # music dips ~4-6 dB under speech, then returns smoothly (no abrupt cuts)
        "[bg][d1]sidechaincompress=threshold=0.03:ratio=2.5:attack=40:release=600:makeup=1[duck];"
        "[d2]pan=stereo|c0=c0|c1=c0[dubs];"
        "[duck][dubs]amix=inputs=2:normalize=0:duration=longest,loudnorm=I=-16:TP=-1.5:LRA=11,alimiter=limit=0.95[aout]"
    )
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", video, "-i", background, "-i", dub, "-filter_complex"]
    if burn and srt:
        esc = srt.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")
        style = "FontName=DejaVu Sans,FontSize=14,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=2,Shadow=0,Alignment=2,MarginV=40"
        graph = f"[0:v]subtitles='{esc}':force_style='{style}'[vout];" + graph
        cmd += [graph, "-map", "[vout]", "-map", "[aout]", "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p"]
    else:
        cmd += [graph, "-map", "0:v:0", "-map", "[aout]", "-c:v", "copy"]  # picture untouched
    cmd += ["-c:a", "aac", "-b:a", "192k", "-t", f"{duration:.3f}", "-movflags", "+faststart", out_mp4]
    _run(cmd)


# ------------------------------------------------------------------ driver
def dub_video(
    video_path: str,
    output_dir: str,
    voice_id: str = DEFAULT_VOICE_ID,
    model_id: str = DEFAULT_TTS_MODEL,
    whisper_model: str = "small",
    subtitles: bool = False,
    burn_subtitles: bool = False,
    progress: Optional[ProgressFn] = None,
) -> DubResult:
    if not voice_service.get_elevenlabs_api_key():
        raise RuntimeError("ELEVENLABS_API_KEY no está configurada")
    os.makedirs(output_dir, exist_ok=True)
    work = os.path.join(output_dir, "work")
    os.makedirs(work, exist_ok=True)
    base = os.path.splitext(os.path.basename(video_path))[0]
    duration = probe_duration(video_path)

    _notify(progress, "audio", 0.0, "Extrayendo audio original…")
    wav = os.path.join(work, "original.wav")
    extract_audio(video_path, wav)

    _notify(progress, "separation", 0.0, "Separando voces y música…")
    vocals, background, method = separate_sources(wav, work)
    warnings = []
    if method.startswith("FALLBACK"):
        warnings.append(method)
    _notify(progress, "separation", 1.0, method)

    _notify(progress, "transcription", 0.0, "Transcribiendo diálogos…")
    tr_cache = os.path.join(work, f"transcript_{whisper_model}.json")
    if os.path.exists(tr_cache):
        with open(tr_cache, encoding="utf-8") as fh:
            segments = [Segment(**d) for d in json.load(fh)]
    else:
        segments = transcribe(vocals, whisper_model)
        with open(tr_cache, "w", encoding="utf-8") as fh:
            json.dump([asdict(s) for s in segments], fh, ensure_ascii=False, indent=1)
    if not segments:
        raise RuntimeError("No se detectaron diálogos en el video")
    _notify(progress, "transcription", 1.0, f"{len(segments)} intervenciones detectadas")

    synthesize(segments, work, voice_id, model_id, progress)

    _notify(progress, "sync", 0.0, "Sincronizando…")
    warnings += schedule(segments, duration)
    dub_wav = os.path.join(work, "dub_track.wav")
    build_dub_track(segments, duration, dub_wav)

    srt_path = os.path.join(output_dir, f"{base}_es.srt")
    write_srt(segments, srt_path)
    out = os.path.join(output_dir, f"{base}_doblado.mp4")
    mux(video_path, background, dub_wav, out, srt_path, burn_subtitles and subtitles, duration)
    _notify(progress, "sync", 1.0, "Video final listo")

    report = os.path.join(output_dir, f"{base}_report.json")
    with open(report, "w", encoding="utf-8") as fh:
        json.dump(
            {"separation": method, "voice_ids_used": sorted({s.voice_id for s in segments}), "warnings": warnings,
             "segments": [asdict(s) for s in segments]},
            fh, ensure_ascii=False, indent=1,
        )
    return DubResult(out, srt_path, segments, warnings, method, report)
