"""
Verifies the mastered soundtrack against real measurements, not settings.

Every assertion here runs FFmpeg over real audio and reads the EBU R128
scanner's answer, because the defect being fixed -- a finished video that
measured -24.6 LUFS with the music masking the narration -- was invisible to
any test that only checked which filter arguments were built.
"""

import subprocess

import pytest

from app.services import audio_master
from app.utils import utils


def _ffmpeg(*arguments):
    subprocess.run(
        [utils.get_ffmpeg_binary(), "-hide_banner", "-nostdin", "-nostats", "-y",
         *arguments],
        stdin=subprocess.DEVNULL, capture_output=True, check=True, timeout=300,
    )


def _tone(path, frequency, seconds, amplitude_db, *, gate=None):
    """
    A test tone, optionally gated on and off so it behaves like speech.

    ``gate`` is a list of (start, end) windows where the tone sounds; outside
    them the file is silent, which is what the ducking test needs in order to
    compare "while the narrator speaks" with "in the pause".
    """
    expression = f"sin(2*PI*{frequency}*t)"
    if gate:
        windows = "+".join(
            f"between(t,{start},{end})" for start, end in gate
        )
        expression = f"({expression})*min(1,{windows})"
    _ffmpeg(
        "-f", "lavfi", "-i",
        f"aevalsrc='{expression}':s=48000:d={seconds}",
        "-af", f"volume={amplitude_db}dB",
        "-ac", "1", "-c:a", "pcm_s16le", str(path),
    )


def _band_rms_db(path, frequency, start, duration):
    """Mean level of one frequency band over one window, in dBFS."""
    completed = subprocess.run(
        [utils.get_ffmpeg_binary(), "-hide_banner", "-nostdin", "-nostats",
         "-ss", str(start), "-t", str(duration), "-i", str(path),
         "-af", f"bandpass=f={frequency}:width_type=h:w={frequency * 0.4},volumedetect",
         "-f", "null", "-"],
        stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=300,
    )
    for line in completed.stderr.splitlines():
        if "mean_volume:" in line:
            return float(line.split("mean_volume:")[1].replace("dB", "").strip())
    raise AssertionError(f"ffmpeg reported no level for {path}")


def test_quiet_narration_is_raised_to_the_delivery_target(tmp_path):
    # -30 dB is roughly where an unmanaged TTS file sits once the old pipeline
    # had finished with it.
    narration = tmp_path / "quiet.wav"
    _tone(narration, 300, 6, -30)
    before = audio_master.measure_loudness(str(narration))
    assert before.integrated_lufs < -24

    output = tmp_path / "mastered.wav"
    report = audio_master.master_soundtrack(str(narration), str(output))

    assert report.integrated_lufs == pytest.approx(-16.0, abs=0.6)
    assert report.true_peak_dbtp <= -0.9
    assert output.exists()


def test_loud_narration_is_brought_down_and_kept_under_the_peak_ceiling(tmp_path):
    narration = tmp_path / "loud.wav"
    _tone(narration, 300, 6, -1)
    output = tmp_path / "mastered.wav"

    report = audio_master.master_soundtrack(str(narration), str(output))

    assert report.integrated_lufs == pytest.approx(-16.0, abs=0.6)
    # A limiter that lets anything through above the ceiling is the one defect
    # that cannot be fixed downstream.
    assert report.true_peak_dbtp <= -0.9


def test_music_ducks_while_the_narrator_speaks_and_returns_in_the_pause(tmp_path):
    # The narration sounds from 1-3s and 5-7s; 3-5s is the pause. The music is
    # a different frequency so it can be isolated in the finished mix.
    narration = tmp_path / "speech.wav"
    _tone(narration, 2500, 8, -14, gate=[(1.0, 3.0), (5.0, 7.0)])
    music = tmp_path / "music.wav"
    _tone(music, 200, 8, -12)
    output = tmp_path / "mixed.wav"

    audio_master.master_soundtrack(
        str(narration), str(output), music_file=str(music), timeline_duration=8.0
    )

    speaking = _band_rms_db(output, 200, 1.6, 1.2)
    pausing = _band_rms_db(output, 200, 3.6, 1.2)
    # The music has to be clearly out of the way of the narration, and clearly
    # back once the narrator stops.
    assert pausing - speaking >= 8.0, (
        f"music only ducked {pausing - speaking:.1f} dB "
        f"(speaking {speaking:.1f} dBFS, pause {pausing:.1f} dBFS)"
    )


def test_music_never_overtakes_the_narration(tmp_path):
    narration = tmp_path / "speech.wav"
    _tone(narration, 2500, 8, -14, gate=[(1.0, 7.0)])
    music = tmp_path / "music.wav"
    # Music far louder than the narration: the bed level is measured, so a hot
    # music file must not be able to bury the voice.
    _tone(music, 200, 8, 0)
    output = tmp_path / "mixed.wav"

    audio_master.master_soundtrack(
        str(narration), str(output), music_file=str(music), timeline_duration=8.0
    )

    voice_level = _band_rms_db(output, 2500, 2.0, 3.0)
    music_level = _band_rms_db(output, 200, 2.0, 3.0)
    assert voice_level - music_level >= 10.0, (
        f"narration is only {voice_level - music_level:.1f} dB above the music"
    )


def test_mixed_soundtrack_hits_the_delivery_target(tmp_path):
    narration = tmp_path / "speech.wav"
    _tone(narration, 2500, 8, -26, gate=[(0.5, 3.0), (4.0, 7.5)])
    music = tmp_path / "music.wav"
    _tone(music, 200, 8, -20)
    output = tmp_path / "mixed.wav"

    report = audio_master.master_soundtrack(
        str(narration), str(output), music_file=str(music), timeline_duration=8.0
    )

    assert report.integrated_lufs == pytest.approx(-16.0, abs=0.8)
    assert report.true_peak_dbtp <= -0.9


def test_soundtrack_runs_to_the_end_of_the_video(tmp_path):
    # The music, and its fade, must cover the tail the narration does not.
    narration = tmp_path / "speech.wav"
    _tone(narration, 2500, 4, -20)
    music = tmp_path / "music.wav"
    _tone(music, 200, 2, -20)
    output = tmp_path / "mixed.wav"

    report = audio_master.master_soundtrack(
        str(narration), str(output), music_file=str(music), timeline_duration=9.0
    )

    # Short music is looped, short narration is padded: either way the
    # soundtrack matches the timeline.
    assert report.duration_seconds == pytest.approx(9.0, abs=0.15)


def test_silence_is_left_alone_rather_than_amplified(tmp_path):
    silence = tmp_path / "silence.wav"
    _ffmpeg("-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono", "-t", "5",
            "-c:a", "pcm_s16le", str(silence))
    output = tmp_path / "mastered.wav"

    report = audio_master.master_soundtrack(str(silence), str(output))

    # Nothing to normalize; amplifying silence by the maximum gain would turn
    # a dropout into a burst of noise.
    assert report.integrated_lufs < -60


def test_a_missing_narration_is_reported_not_silently_skipped(tmp_path):
    with pytest.raises(audio_master.AudioMasterError):
        audio_master.master_soundtrack(
            str(tmp_path / "absent.wav"), str(tmp_path / "out.wav")
        )


def test_missing_music_degrades_to_a_narration_only_soundtrack(tmp_path):
    narration = tmp_path / "speech.wav"
    _tone(narration, 300, 5, -26)
    output = tmp_path / "mastered.wav"

    report = audio_master.master_soundtrack(
        str(narration), str(output), music_file=str(tmp_path / "gone.mp3")
    )

    assert report.integrated_lufs == pytest.approx(-16.0, abs=0.8)


def test_settings_read_overrides_and_ignore_unusable_values(monkeypatch):
    from app.config import config

    monkeypatch.setitem(config.audio_master, "target_lufs", -14.0)
    monkeypatch.setitem(config.audio_master, "duck_ratio", "not a number")
    monkeypatch.setitem(config.audio_master, "music_bed_lufs", float("inf"))

    settings = audio_master.MasteringSettings.from_config()

    assert settings.target_lufs == -14.0
    # A broken value must fall back, not stop a render.
    assert settings.duck_ratio == audio_master.MasteringSettings().duck_ratio
    assert settings.music_bed_lufs == audio_master.MasteringSettings().music_bed_lufs


def test_mastering_can_be_switched_off(monkeypatch):
    from app.config import config

    assert audio_master.is_enabled() is True
    monkeypatch.setitem(config.audio_master, "enabled", False)
    assert audio_master.is_enabled() is False
    monkeypatch.setitem(config.audio_master, "enabled", "off")
    assert audio_master.is_enabled() is False


def test_volume_controls_become_trims_on_the_measured_level():
    # 1.0 has always meant "unchanged", and it still does.
    assert audio_master.volume_multiplier_to_db(1.0) == pytest.approx(0.0)
    assert audio_master.volume_multiplier_to_db(2.0) == pytest.approx(6.02, abs=0.05)
    assert audio_master.volume_multiplier_to_db(0.5) == pytest.approx(-6.02, abs=0.05)
    assert audio_master.volume_multiplier_to_db(None) == pytest.approx(0.0)
    assert audio_master.volume_multiplier_to_db("broken") == 0.0

    # bgm_volume's historical default now means "use the measured bed level",
    # because the bed level is what it used to be standing in for.
    assert audio_master.music_multiplier_to_db(0.2) == pytest.approx(0.0)
    assert audio_master.music_multiplier_to_db(0.4) == pytest.approx(6.02, abs=0.05)
    assert audio_master.music_multiplier_to_db(0.1) == pytest.approx(-6.02, abs=0.05)


def test_measuring_a_missing_file_is_an_error(tmp_path):
    with pytest.raises(audio_master.AudioMasterError):
        audio_master.measure_loudness(str(tmp_path / "nothing.wav"))


def test_narration_chain_shapes_tone_before_any_gain():
    chain = audio_master.narration_filter_chain(audio_master.MasteringSettings())
    # Gain belongs after the measurement, never inside the chain that changes
    # the level being measured.
    assert "volume=" not in chain
    assert "highpass=" in chain
    assert "deesser=" in chain
    assert "acompressor=" in chain


def test_report_serializes_for_task_logs():
    report = audio_master.LoudnessReport(-16.04, -1.02, 7.5, 42.123)
    assert '"integrated_lufs": -16.04' in audio_master.report_as_json(report)
    assert report.is_measurable
    assert "LUFS" in report.describe()
    assert not audio_master.LoudnessReport(-120.0, -120.0, 0.0, 10.0).is_measurable
    assert not audio_master.LoudnessReport(-16.0, -1.0, 7.0, 0.05).is_measurable


def test_a_zero_volume_control_stays_a_mute(tmp_path):
    """
    The volume controls express 0 as "off". Mastering measures and levels the
    narration, so without an explicit mute a muted video would come back with
    the narration raised to the delivery target.
    """
    narration = tmp_path / "speech.wav"
    _tone(narration, 300, 5, -26)
    output = tmp_path / "muted.wav"

    report = audio_master.master_soundtrack(
        str(narration), str(output), mute_narration=True
    )

    assert report.integrated_lufs < -60


def test_a_muted_narration_leaves_the_music_at_the_bed_level(tmp_path):
    narration = tmp_path / "speech.wav"
    _tone(narration, 2500, 6, -20)
    music = tmp_path / "music.wav"
    _tone(music, 200, 6, -20)

    muted = tmp_path / "muted.wav"
    muted_report = audio_master.master_soundtrack(
        str(narration), str(muted), music_file=str(music),
        timeline_duration=6.0, mute_narration=True,
    )
    audible = tmp_path / "audible.wav"
    audible_report = audio_master.master_soundtrack(
        str(narration), str(audible), music_file=str(music), timeline_duration=6.0,
    )

    # The bed must not be pushed up to the delivery target to make up for the
    # missing narration.
    assert audible_report.integrated_lufs == pytest.approx(-16.0, abs=1.0)
    assert muted_report.integrated_lufs < -24
    # The narration's own band is gone from the muted mix but present in the
    # one that was not muted.
    muted_voice = _band_rms_db(muted, 2500, 1.6, 1.0)
    audible_voice = _band_rms_db(audible, 2500, 1.6, 1.0)
    assert audible_voice - muted_voice > 20
