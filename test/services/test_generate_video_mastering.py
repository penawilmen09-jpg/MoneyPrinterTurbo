"""
Verifies how the final render uses the mastering stage, including the paths
that must keep a render alive when mastering cannot run.
"""

from unittest.mock import patch

import pytest

from app.config import config
from app.models.schema import VideoParams
from app.services import audio_master, video


def _params(**overrides):
    base = dict(video_subject="t", subtitle_enabled=False, bgm_type="random")
    base.update(overrides)
    return VideoParams(**base)


def _report():
    return audio_master.LoudnessReport(-16.0, -1.0, 7.0, 30.0)


def test_the_user_volume_controls_become_trims_on_the_measured_level():
    captured = {}

    def fake_master(narration, output, **kwargs):
        captured.update(kwargs)
        open(output, "wb").write(b"")
        return _report()

    with (
        patch.object(audio_master, "master_soundtrack", fake_master),
        patch.object(audio_master, "is_enabled", lambda: True),
    ):
        path, mixed = video._master_soundtrack_for_render(
            narration_path="narration.mp3",
            music_path="music.mp3",
            timeline_duration=30.0,
            params=_params(voice_volume=2.0, bgm_volume=0.1),
            output_dir=".",
        )

    assert mixed is True
    assert captured["narration_gain_db"] == pytest.approx(6.02, abs=0.05)
    assert captured["music_gain_db"] == pytest.approx(-6.02, abs=0.05)
    assert captured["timeline_duration"] == 30.0
    video.delete_files(path)


def test_disabled_mastering_returns_to_the_direct_mix(monkeypatch):
    monkeypatch.setitem(config.audio_master, "enabled", False)
    path, mixed = video._master_soundtrack_for_render(
        narration_path="narration.mp3",
        music_path="music.mp3",
        timeline_duration=10.0,
        params=_params(),
        output_dir=".",
    )
    assert path == ""
    # Nothing failed, so this must not be reported as a music failure.
    assert mixed is True


def test_broken_music_still_ships_a_mastered_narration(tmp_path):
    attempts = []

    def fake_master(narration, output, **kwargs):
        attempts.append(kwargs.get("music_file"))
        if kwargs.get("music_file"):
            raise audio_master.AudioMasterError("music will not decode")
        open(output, "wb").write(b"")
        return _report()

    with (
        patch.object(audio_master, "master_soundtrack", fake_master),
        patch.object(audio_master, "is_enabled", lambda: True),
    ):
        path, mixed = video._master_soundtrack_for_render(
            narration_path="narration.mp3",
            music_path="broken.mp3",
            timeline_duration=10.0,
            params=_params(),
            output_dir=str(tmp_path),
        )

    # The narration keeps its loudness management; only the bed is lost.
    assert path
    assert mixed is False
    assert attempts == ["broken.mp3", ""]


def test_a_total_mastering_failure_falls_back_without_leaving_a_temp_file(tmp_path):
    def always_fail(narration, output, **kwargs):
        raise audio_master.AudioMasterError("ffmpeg is unavailable")

    with (
        patch.object(audio_master, "master_soundtrack", always_fail),
        patch.object(audio_master, "is_enabled", lambda: True),
    ):
        path, mixed = video._master_soundtrack_for_render(
            narration_path="narration.mp3",
            music_path="music.mp3",
            timeline_duration=10.0,
            params=_params(),
            output_dir=str(tmp_path),
        )

    assert path == ""
    assert mixed is False
    assert not list(tmp_path.glob(".mastered-audio-*"))


def test_no_music_failure_is_reported_when_no_music_was_requested(tmp_path):
    def always_fail(narration, output, **kwargs):
        raise audio_master.AudioMasterError("ffmpeg is unavailable")

    with (
        patch.object(audio_master, "master_soundtrack", always_fail),
        patch.object(audio_master, "is_enabled", lambda: True),
    ):
        path, mixed = video._master_soundtrack_for_render(
            narration_path="narration.mp3",
            music_path="",
            timeline_duration=10.0,
            params=_params(bgm_type=""),
            output_dir=str(tmp_path),
        )

    assert path == ""
    assert mixed is True
