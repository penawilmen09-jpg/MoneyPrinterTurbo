"""
Loudness-managed audio mastering for the final video soundtrack.

Why this module exists
----------------------
The original pipeline handed the raw TTS file and the background music
straight to MoviePy and mixed them with ``CompositeAudioClip``:

    audio_clip = voice * voice_volume
    bgm_clip   = music * bgm_volume          # bgm_volume defaults to 0.2
    audio_clip = CompositeAudioClip([audio_clip, bgm_clip])

That mix has three defects that are audible on a phone speaker:

1. No loudness management. Whatever the TTS provider returns is what ships.
   ElevenLabs returns roughly -20 LUFS, and after the music sums in and the
   encoder runs, finished videos measured around -24.6 LUFS integrated --
   about 8 LU below what TikTok, Reels and Shorts normalize to, so the
   narration sounds distant and thin.
2. A constant music level. ``bgm_volume`` is a single multiplier, so the bed
   sits at the same level whether the narrator is speaking or not and masks
   consonants, which is what makes narration "unclear".
3. No peak control, so a loud music transient can clip the summed track.

Everything here runs through FFmpeg, which the project already requires. No
new Python dependency is introduced.

Signal flow
-----------
    narration -> highpass -> low-mid cut -> presence lift -> de-esser
              -> gentle compressor -> measured gain  ------------------+
                                                                        |
    music -> loop/trim to length -> measured gain to a fixed bed level  |
          -> fades -> sidechain ducking (narration drives the sidechain) |
                                                                        |
                                 -> amix (no auto level scaling) -------+
                                 -> exact corrective gain
                                 -> lookahead limiter -> target true peak

Gains are never guessed: every stage is measured with FFmpeg's EBU R128
scanner (``ebur128``) and the required gain is computed from the real
measurement, then the result is measured again and reported back to the
caller so a task can log what actually shipped.
"""

from __future__ import annotations

import json
import math
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass
from typing import Sequence

from loguru import logger

from app.config import config
from app.utils import utils

# FFmpeg's EBU R128 scanner needs this much signal before it reports a
# meaningful integrated loudness. Shorter clips still get mastered, but the
# measurement is taken as approximate and the limiter does the safety work.
_MIN_MEASURABLE_SECONDS = 0.4

# ebur128 reports "I: -16.0 LUFS" and "Peak: -1.0 dBFS" in its summary block.
_INTEGRATED_PATTERN = re.compile(r"^\s*I:\s+(-?\d+(?:\.\d+)?) LUFS", re.MULTILINE)
_PEAK_PATTERN = re.compile(r"^\s*Peak:\s+(-?\d+(?:\.\d+)?) dBFS", re.MULTILINE)
_LRA_PATTERN = re.compile(r"^\s*LRA:\s+(-?\d+(?:\.\d+)?) LU", re.MULTILINE)

# A silent or near-silent track measures at -inf / -120 LUFS. Boosting it to
# the target would be a division by nothing, so such tracks are left alone.
_SILENCE_FLOOR_LUFS = -70.0

# Mastering never moves a track by more than this. It keeps a broken
# measurement, a corrupt file or a near-silent narration from being amplified
# into noise, and it keeps an already-loud track from being crushed.
_MAX_ABSOLUTE_GAIN_DB = 24.0

_MEASURE_TIMEOUT_SECONDS = 600
_RENDER_TIMEOUT_SECONDS = 1800


class AudioMasterError(RuntimeError):
    """Raised when a mastering stage cannot produce a usable audio file."""


@dataclass(frozen=True)
class LoudnessReport:
    """An EBU R128 measurement of one audio file."""

    integrated_lufs: float
    true_peak_dbtp: float
    loudness_range_lu: float
    duration_seconds: float

    @property
    def is_measurable(self) -> bool:
        """Whether the scanner saw enough non-silent audio to be trusted."""
        return (
            self.duration_seconds >= _MIN_MEASURABLE_SECONDS
            and math.isfinite(self.integrated_lufs)
            and self.integrated_lufs > _SILENCE_FLOOR_LUFS
        )

    def describe(self) -> str:
        return (
            f"{self.integrated_lufs:.1f} LUFS integrated, "
            f"{self.true_peak_dbtp:.1f} dBTP peak, "
            f"{self.loudness_range_lu:.1f} LU range"
        )


@dataclass(frozen=True)
class MasteringSettings:
    """
    Every number the mastering chain uses, so the whole chain is one value
    that a caller can log, diff or override in tests.

    The defaults target the short-form platforms: TikTok, Instagram Reels and
    YouTube Shorts all normalize playback to about -14 LUFS, and delivering
    -16 LUFS with 1 dB of true-peak headroom stays clear of their limiters
    while leaving the narration loud enough to carry a phone speaker.
    """

    # Delivery targets for the finished mix.
    target_lufs: float = -16.0
    target_true_peak_dbtp: float = -1.0

    # Where the narration sits before the music is summed in. Keeping this at
    # the delivery target means the music bed is the only thing that can push
    # the mix, and it only adds a few tenths of a LU.
    narration_target_lufs: float = -16.0

    # The music bed's own integrated loudness before ducking. 14 LU below the
    # narration is audible as a bed but cannot mask speech.
    music_bed_lufs: float = -30.0

    # Narration tone shaping.
    highpass_hz: float = 80.0
    low_mid_cut_hz: float = 220.0
    low_mid_cut_db: float = -1.5
    presence_hz: float = 3000.0
    presence_gain_db: float = 2.5
    presence_width: float = 1.2
    deesser_intensity: float = 0.3

    # Narration dynamics. A shallow ratio with a slow release evens out the
    # loud/quiet swing between sentences without the pumping that makes a
    # voice sound processed.
    compressor_threshold_db: float = -20.0
    compressor_ratio: float = 2.5
    compressor_attack_ms: float = 8.0
    compressor_release_ms: float = 180.0
    compressor_knee: float = 4.0

    # Sidechain ducking. The narration drives the sidechain, so the music
    # drops while the narrator speaks and recovers in the pauses. Measured on
    # the bundled tracks, these values duck by about 13-15 dB.
    duck_threshold: float = 0.03
    duck_ratio: float = 6.0
    duck_attack_ms: float = 15.0
    duck_release_ms: float = 350.0

    # Music envelope across the whole timeline.
    music_fade_in_seconds: float = 1.5
    music_fade_out_seconds: float = 3.0

    # Output format for the mastered track handed back to the video writer.
    sample_rate: int = 48000
    channels: int = 2

    # How far off target the measured mix may land before a corrective gain
    # pass runs. 0.3 LU is below the threshold of audibility.
    correction_tolerance_lu: float = 0.3

    @classmethod
    def from_config(cls) -> "MasteringSettings":
        """
        Read overrides from the ``[audio_master]`` config section.

        Unknown keys are ignored and a non-numeric value falls back to the
        default, so a hand-edited config can never stop a render.
        """
        section = {}
        try:
            section = dict(getattr(config, "audio_master", {}) or {})
        except Exception:  # pragma: no cover - defensive config access
            section = {}

        overrides = {}
        for field_name, default_value in cls().__dict__.items():
            if field_name not in section:
                continue
            raw_value = section[field_name]
            try:
                if isinstance(default_value, int) and not isinstance(
                    default_value, bool
                ):
                    overrides[field_name] = int(raw_value)
                else:
                    value = float(raw_value)
                    if not math.isfinite(value):
                        raise ValueError(field_name)
                    overrides[field_name] = value
            except (TypeError, ValueError):
                logger.warning(
                    f"ignoring invalid audio_master.{field_name}: {raw_value!r}"
                )
        return cls(**overrides)


def is_enabled() -> bool:
    """
    Whether the mastering chain runs. Enabled by default; setting
    ``audio_master.enabled = false`` restores the original MoviePy mix.
    """
    try:
        section = dict(getattr(config, "audio_master", {}) or {})
    except Exception:  # pragma: no cover - defensive config access
        return True
    value = section.get("enabled", True)
    if isinstance(value, str):
        return value.strip().lower() not in {"false", "0", "no", "off"}
    return bool(value)


def _ffmpeg_binary() -> str:
    return utils.get_ffmpeg_binary()


def _run_ffmpeg(arguments: Sequence[str], *, timeout: int) -> str:
    """
    Run FFmpeg and return its stderr, which is where it writes both filter
    reports and error messages.
    """
    command = [_ffmpeg_binary(), "-hide_banner", "-nostdin", "-nostats", *arguments]
    try:
        completed = subprocess.run(
            command,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        raise AudioMasterError(f"ffmpeg is not available: {exc}") from exc
    except subprocess.TimeoutExpired as exc:
        raise AudioMasterError(
            f"ffmpeg timed out after {timeout}s during audio mastering"
        ) from exc
    if completed.returncode != 0:
        # Keep only the tail: FFmpeg prints the real reason last, and the
        # banner/stream dump above it is noise in a task log.
        tail = (completed.stderr or "").strip().splitlines()[-6:]
        raise AudioMasterError(
            "ffmpeg failed during audio mastering: " + " | ".join(tail)
        )
    return completed.stderr or ""


def probe_duration(file_path: str) -> float:
    """Return a file's duration in seconds, or 0.0 when it cannot be read."""
    # ffprobe ships next to ffmpeg in every layout utils.get_ffmpeg_binary()
    # resolves: an explicit IMAGEIO_FFMPEG_EXE, a PATH install, or the
    # imageio-ffmpeg wheel. Fall back to the bare name so subprocess reports
    # a precise error instead of this helper guessing.
    candidate = _ffmpeg_binary()
    binary = os.path.join(
        os.path.dirname(candidate),
        "ffprobe" + (".exe" if candidate.lower().endswith(".exe") else ""),
    )
    if not os.path.exists(binary):
        binary = "ffprobe"
    try:
        completed = subprocess.run(
            [
                binary,
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=nokey=1:noprint_wrappers=1",
                file_path,
            ],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=120,
        )
        duration = float((completed.stdout or "").strip())
    except (OSError, ValueError, subprocess.SubprocessError):
        return 0.0
    return duration if math.isfinite(duration) and duration > 0 else 0.0


def measure_loudness(file_path: str) -> LoudnessReport:
    """
    Measure a file with FFmpeg's EBU R128 scanner.

    ``ebur128`` is used rather than ``loudnorm``'s JSON report because the
    scanner reports the real integrated loudness and true peak of the file as
    it stands, which is exactly what has to be verified before and after
    mastering.
    """
    if not file_path or not os.path.exists(file_path):
        raise AudioMasterError(f"cannot measure a missing audio file: {file_path}")

    stderr = _run_ffmpeg(
        ["-i", file_path, "-af", "ebur128=peak=true", "-f", "null", "-"],
        timeout=_MEASURE_TIMEOUT_SECONDS,
    )

    def last_match(pattern: re.Pattern[str], fallback: float) -> float:
        matches = pattern.findall(stderr)
        if not matches:
            return fallback
        try:
            value = float(matches[-1])
        except ValueError:
            return fallback
        return value if math.isfinite(value) else fallback

    return LoudnessReport(
        integrated_lufs=last_match(_INTEGRATED_PATTERN, -120.0),
        true_peak_dbtp=last_match(_PEAK_PATTERN, -120.0),
        loudness_range_lu=last_match(_LRA_PATTERN, 0.0),
        duration_seconds=probe_duration(file_path),
    )


def _clamp_gain(gain_db: float) -> float:
    if not math.isfinite(gain_db):
        return 0.0
    return max(-_MAX_ABSOLUTE_GAIN_DB, min(_MAX_ABSOLUTE_GAIN_DB, gain_db))


def _gain_to_reach(
    report: LoudnessReport, target_lufs: float, *, label: str
) -> float:
    """
    The gain that moves a measured track to ``target_lufs``.

    A track the scanner could not measure -- silence, or a clip too short for
    R128 -- is left at unity rather than amplified by a guess.
    """
    if not report.is_measurable:
        logger.warning(
            f"{label} loudness is not measurable "
            f"({report.integrated_lufs:.1f} LUFS over "
            f"{report.duration_seconds:.2f}s); leaving its level untouched"
        )
        return 0.0
    gain_db = target_lufs - report.integrated_lufs
    clamped = _clamp_gain(gain_db)
    if abs(clamped - gain_db) > 0.01:
        logger.warning(
            f"{label} needs {gain_db:+.1f} dB to reach {target_lufs:.1f} LUFS, "
            f"clamped to {clamped:+.1f} dB"
        )
    return clamped


def _true_peak_to_limit(target_true_peak_dbtp: float) -> float:
    """Convert a dBTP ceiling into the linear ``alimiter`` limit."""
    ceiling = min(-0.1, float(target_true_peak_dbtp))
    return 10.0 ** (ceiling / 20.0)


def narration_filter_chain(settings: MasteringSettings) -> str:
    """
    The tone and dynamics chain applied to the narration, without any gain.

    Keeping gain out of this chain is deliberate: the chain changes the
    loudness, so the level has to be measured after it, not before.
    """
    return ",".join(
        [
            # Rumble, plosive thumps and any DC offset below the voice.
            f"highpass=f={settings.highpass_hz:g}",
            # A narrow dip where recorded and synthetic voices get boxy.
            f"equalizer=f={settings.low_mid_cut_hz:g}:t=q:w=1.0"
            f":g={settings.low_mid_cut_db:g}",
            # Consonant presence. This is the band a phone speaker can
            # actually reproduce, so it is what makes speech intelligible
            # without raising the overall level.
            f"equalizer=f={settings.presence_hz:g}:t=q"
            f":w={settings.presence_width:g}:g={settings.presence_gain_db:g}",
            # Tame the sibilance the presence lift just emphasised.
            f"deesser=i={settings.deesser_intensity:g}",
            f"acompressor=threshold={settings.compressor_threshold_db:g}dB"
            f":ratio={settings.compressor_ratio:g}"
            f":attack={settings.compressor_attack_ms:g}"
            f":release={settings.compressor_release_ms:g}"
            f":knee={settings.compressor_knee:g}:makeup=1",
        ]
    )


def _render(
    inputs: Sequence[Sequence[str]],
    filter_complex: str,
    output_label: str,
    output_file: str,
    settings: MasteringSettings,
) -> None:
    arguments: list[str] = ["-y"]
    for input_arguments in inputs:
        arguments.extend(input_arguments)
    arguments.extend(
        [
            "-filter_complex",
            filter_complex,
            "-map",
            output_label,
            "-ar",
            str(settings.sample_rate),
            "-ac",
            str(settings.channels),
            "-c:a",
            "pcm_s16le",
            output_file,
        ]
    )
    _run_ffmpeg(arguments, timeout=_RENDER_TIMEOUT_SECONDS)


def _apply_corrective_gain(
    source_file: str,
    destination_file: str,
    gain_db: float,
    settings: MasteringSettings,
) -> None:
    limit = _true_peak_to_limit(settings.target_true_peak_dbtp)
    _render(
        [["-i", source_file]],
        f"[0:a]volume={gain_db:.3f}dB,"
        f"alimiter=limit={limit:.6f}:attack=5:release=50:level=disabled[out]",
        "[out]",
        destination_file,
        settings,
    )


def _verify_and_correct(
    mixed_file: str,
    settings: MasteringSettings,
    work_dir: str,
    *,
    label: str,
) -> tuple[str, LoudnessReport]:
    """
    Measure the rendered mix and, when it missed the target by more than the
    tolerance, apply one exact corrective gain pass and measure again.

    Returns the file that should ship and its final measurement.
    """
    report = measure_loudness(mixed_file)
    if not report.is_measurable:
        return mixed_file, report

    delta = settings.target_lufs - report.integrated_lufs
    if abs(delta) <= settings.correction_tolerance_lu:
        logger.info(f"{label} measured {report.describe()}")
        return mixed_file, report

    logger.info(
        f"{label} measured {report.describe()}; applying {delta:+.2f} dB to "
        f"reach {settings.target_lufs:.1f} LUFS"
    )
    corrected_file = os.path.join(work_dir, "mastered-corrected.wav")
    _apply_corrective_gain(mixed_file, corrected_file, _clamp_gain(delta), settings)
    corrected_report = measure_loudness(corrected_file)
    logger.info(f"{label} after correction: {corrected_report.describe()}")
    return corrected_file, corrected_report


def master_soundtrack(
    narration_file: str,
    output_file: str,
    *,
    music_file: str = "",
    timeline_duration: float = 0.0,
    narration_gain_db: float = 0.0,
    music_gain_db: float = 0.0,
    settings: MasteringSettings | None = None,
) -> LoudnessReport:
    """
    Produce the finished soundtrack for a video and return its measurement.

    Args:
        narration_file: the TTS or custom narration track.
        output_file: where the mastered soundtrack is written (WAV, so the
            video writer's encoder is the only lossy stage).
        music_file: optional background music. Looped or trimmed to the
            timeline, levelled to a fixed bed loudness, faded and ducked
            under the narration.
        timeline_duration: the finished video's duration. The music is cut to
            it; 0 falls back to the narration's own duration.
        narration_gain_db: the user's voice-volume control, applied as a trim
            on top of the measured level rather than as the level itself, so
            a user preference can no longer leave the mix 8 LU quiet.
        music_gain_db: the user's music-volume control, same idea.
        settings: mastering values; read from config when omitted.

    Raises:
        AudioMasterError: when FFmpeg cannot produce the soundtrack. Callers
            are expected to fall back to their previous mixing path.
    """
    settings = settings or MasteringSettings.from_config()

    if not narration_file or not os.path.exists(narration_file):
        raise AudioMasterError(f"narration file is missing: {narration_file}")

    narration_duration = probe_duration(narration_file)
    duration = float(timeline_duration or 0.0)
    if not math.isfinite(duration) or duration <= 0:
        duration = narration_duration
    if duration <= 0:
        raise AudioMasterError("cannot master a soundtrack with no duration")

    output_directory = os.path.dirname(os.path.abspath(output_file)) or "."
    os.makedirs(output_directory, exist_ok=True)

    with tempfile.TemporaryDirectory(
        prefix=".audio-master-", dir=output_directory
    ) as work_dir:
        # Stage 1: tone and dynamics, then measure what that chain produced.
        shaped_file = os.path.join(work_dir, "narration-shaped.wav")
        _render(
            [["-i", narration_file]],
            f"[0:a]{narration_filter_chain(settings)}[out]",
            "[out]",
            shaped_file,
            settings,
        )
        shaped_report = measure_loudness(shaped_file)
        narration_level_gain = _gain_to_reach(
            shaped_report, settings.narration_target_lufs, label="narration"
        )
        total_narration_gain = _clamp_gain(
            narration_level_gain + float(narration_gain_db or 0.0)
        )
        logger.info(
            f"narration shaped to {shaped_report.describe()}; applying "
            f"{total_narration_gain:+.2f} dB "
            f"(level {narration_level_gain:+.2f} dB, "
            f"user trim {float(narration_gain_db or 0.0):+.2f} dB)"
        )

        limit = _true_peak_to_limit(settings.target_true_peak_dbtp)
        mixed_file = os.path.join(work_dir, "mastered-mix.wav")

        if not music_file or not os.path.exists(music_file):
            # Narration only: level it, hold the peak ceiling, done.
            _render(
                [["-i", shaped_file]],
                f"[0:a]volume={total_narration_gain:.3f}dB,"
                f"alimiter=limit={limit:.6f}:attack=5:release=50:level=disabled"
                f"[out]",
                "[out]",
                mixed_file,
                settings,
            )
            shipped_file, report = _verify_and_correct(
                mixed_file, settings, work_dir, label="narration-only soundtrack"
            )
            os.replace(shipped_file, output_file)
            return report

        # Stage 2: level the music against its own measurement so every
        # track -- bundled, uploaded or provider-generated -- lands on the
        # same bed level before ducking.
        music_report = measure_loudness(music_file)
        music_level_gain = _gain_to_reach(
            music_report, settings.music_bed_lufs, label="music"
        )
        total_music_gain = _clamp_gain(
            music_level_gain + float(music_gain_db or 0.0)
        )
        logger.info(
            f"music measured {music_report.describe()}; applying "
            f"{total_music_gain:+.2f} dB "
            f"(bed {music_level_gain:+.2f} dB, "
            f"user trim {float(music_gain_db or 0.0):+.2f} dB)"
        )

        fade_out_start = max(0.0, duration - settings.music_fade_out_seconds)
        fade_in = min(settings.music_fade_in_seconds, max(0.1, duration / 4.0))
        fade_out = min(settings.music_fade_out_seconds, max(0.1, duration / 4.0))

        # ``-stream_loop -1`` repeats a music file shorter than the video; the
        # trim then cuts the loop to the timeline. A longer file is simply
        # trimmed, so both cases take the same path.
        music_input = ["-stream_loop", "-1", "-i", music_file]

        # The narration feeds both the mix and the ducking sidechain, so it is
        # split. Every branch of a filter graph must be consumed or FFmpeg
        # refuses to build the graph.
        filter_complex = (
            # The narration is padded to the timeline so the music bed and
            # its fade-out run to the end of the video instead of stopping
            # where the narration stops. The trim keeps the mix exactly as
            # long as the video, whichever track is longer.
            f"[0:a]aformat=sample_rates={settings.sample_rate}"
            f":channel_layouts=stereo,"
            f"volume={total_narration_gain:.3f}dB,"
            f"apad=whole_dur={duration:.3f},atrim=0:{duration:.3f},"
            f"asetpts=N/SR/TB,asplit=2[voice][sidechain];"
            f"[1:a]aformat=sample_rates={settings.sample_rate}"
            f":channel_layouts=stereo,"
            f"atrim=0:{duration:.3f},asetpts=N/SR/TB,"
            f"volume={total_music_gain:.3f}dB,"
            f"afade=t=in:st=0:d={fade_in:.3f},"
            f"afade=t=out:st={fade_out_start:.3f}:d={fade_out:.3f}[bed];"
            f"[bed][sidechain]sidechaincompress="
            f"threshold={settings.duck_threshold:g}"
            f":ratio={settings.duck_ratio:g}"
            f":attack={settings.duck_attack_ms:g}"
            f":release={settings.duck_release_ms:g}[ducked];"
            f"[voice][ducked]amix=inputs=2:duration=first:normalize=0,"
            f"alimiter=limit={limit:.6f}:attack=5:release=50:level=disabled[out]"
        )
        _render(
            [["-i", shaped_file], music_input],
            filter_complex,
            "[out]",
            mixed_file,
            settings,
        )
        shipped_file, report = _verify_and_correct(
            mixed_file, settings, work_dir, label="ducked soundtrack"
        )
        os.replace(shipped_file, output_file)
        return report


def volume_multiplier_to_db(multiplier: float | None) -> float:
    """
    Translate the project's linear volume controls into a dB trim.

    The WebUI, CLI and API all express ``voice_volume`` and ``bgm_volume`` as
    linear multipliers where 1.0 means "unchanged". Mastering works in dB, and
    the multiplier now trims the *measured* level instead of defining it, so
    1.0 maps to no trim and the stored defaults keep their meaning.
    """
    try:
        value = float(multiplier if multiplier is not None else 1.0)
    except (TypeError, ValueError):
        return 0.0
    if not math.isfinite(value) or value <= 0:
        # 0 or a negative multiplier means "off" to the callers that check it
        # before mastering; reaching here means "leave the level alone".
        return 0.0
    return _clamp_gain(20.0 * math.log10(value))


def music_multiplier_to_db(multiplier: float | None) -> float:
    """
    Translate ``bgm_volume`` into a trim on the measured music bed.

    ``bgm_volume`` historically doubled as the only thing standing between a
    full-scale music file and the narration, so its default of 0.2 (-14 dB)
    was compensating for the missing bed level. Now that the bed is measured
    and ducked, treating 0.2 as another -14 dB would make the music inaudible.
    The default and anything above it therefore means "use the bed level",
    and only a value below the default is honoured as a deliberate cut.
    """
    try:
        value = float(multiplier if multiplier is not None else 0.2)
    except (TypeError, ValueError):
        return 0.0
    if not math.isfinite(value) or value <= 0:
        return 0.0
    # Scaling from the default in both directions keeps the slider's
    # direction intact: above 0.2 the bed comes up, below it the bed goes
    # down, and exactly 0.2 means "use the measured bed level".
    return _clamp_gain(20.0 * math.log10(value / 0.2))


def report_as_json(report: LoudnessReport) -> str:
    """Serialize a measurement for task logs and artifacts."""
    return json.dumps(
        {
            "integrated_lufs": round(report.integrated_lufs, 2),
            "true_peak_dbtp": round(report.true_peak_dbtp, 2),
            "loudness_range_lu": round(report.loudness_range_lu, 2),
            "duration_seconds": round(report.duration_seconds, 3),
        },
        ensure_ascii=False,
    )
