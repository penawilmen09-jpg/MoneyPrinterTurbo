"""
Verifies that scene changes dissolve, and that a dissolve that would not fit
degrades to the hard cuts this project shipped before.
"""

import subprocess

import pytest
from moviepy import VideoFileClip

from app.config import config
from app.services import video
from app.utils import utils


def _solid_clip(path, colour, seconds, size="320x180"):
    subprocess.run(
        [utils.get_ffmpeg_binary(), "-hide_banner", "-nostdin", "-nostats", "-y",
         "-f", "lavfi", "-i", f"color=c={colour}:s={size}:r=30",
         "-t", str(seconds), "-c:v", "libx264", "-pix_fmt", "yuv420p", str(path)],
        stdin=subprocess.DEVNULL, capture_output=True, check=True, timeout=300,
    )
    return str(path)


def test_offsets_overlap_each_pair_of_clips():
    filter_complex, label, total = video.build_crossfade_filter(
        [4.0, 4.0, 4.0], 0.5, ["fade"]
    )
    assert label == "[vout]"
    # Three 4s clips joined by two 0.5s dissolves play for 11s, not 12.
    assert total == pytest.approx(11.0)
    # The first dissolve starts 0.5s before the first clip ends; the second
    # 0.5s before the chain built so far ends.
    assert "offset=3.500" in filter_complex
    assert "offset=7.000" in filter_complex
    assert filter_complex.count("xfade=") == 2


def test_transitions_rotate_through_the_configured_list():
    filter_complex, _, _ = video.build_crossfade_filter(
        [3.0, 3.0, 3.0, 3.0], 0.4, ["fade", "smoothleft"]
    )
    assert "transition=fade" in filter_complex
    assert "transition=smoothleft" in filter_complex


def test_a_dissolve_longer_than_a_clip_is_refused():
    with pytest.raises(ValueError, match="not longer than"):
        video.build_crossfade_filter([3.0, 0.4], 0.5, ["fade"])
    with pytest.raises(ValueError):
        video.build_crossfade_filter([3.0], 0.5, ["fade"])
    with pytest.raises(ValueError):
        video.build_crossfade_filter([3.0, 3.0], 0.0, ["fade"])


def test_configured_transitions_are_validated_before_reaching_ffmpeg(monkeypatch):
    monkeypatch.setitem(config.app, "video_crossfade_transitions", "fade, smoothleft")
    assert video.get_crossfade_transitions() == ["fade", "smoothleft"]
    # An unsupported name would fail the whole concat, so it is dropped here.
    monkeypatch.setitem(config.app, "video_crossfade_transitions", "explode, fade")
    assert video.get_crossfade_transitions() == ["fade"]
    monkeypatch.setitem(config.app, "video_crossfade_transitions", "explode")
    assert video.get_crossfade_transitions() == ["fade"]
    monkeypatch.setitem(config.app, "video_crossfade_transitions", "")
    assert video.get_crossfade_transitions() == ["fade"]


def test_crossfade_duration_is_bounded_and_switchable(monkeypatch):
    monkeypatch.setitem(config.app, "video_crossfade_seconds", 0.0)
    assert video.get_crossfade_seconds() == 0.0
    monkeypatch.setitem(config.app, "video_crossfade_seconds", 99)
    assert video.get_crossfade_seconds() == 1.5
    monkeypatch.setitem(config.app, "video_crossfade_seconds", "nonsense")
    assert video.get_crossfade_seconds() == 0.5


def test_scenes_blend_into_each_other_instead_of_cutting(tmp_path):
    red = _solid_clip(tmp_path / "a.mp4", "red", 2.0)
    blue = _solid_clip(tmp_path / "b.mp4", "blue", 2.0)
    output = tmp_path / "joined.mp4"

    video.concat_video_clips_with_ffmpeg(
        clip_files=[red, blue],
        output_file=str(output),
        threads=2,
        output_dir=str(tmp_path),
        max_duration=3.0,
        crossfade_duration=0.6,
    )

    with VideoFileClip(str(output), audio=False) as clip:
        assert clip.duration == pytest.approx(3.0, abs=0.15)
        # Mid-dissolve the frame must be neither source colour but a blend.
        blended = clip.get_frame(1.7).reshape(-1, 3).mean(axis=0)
    assert blended[0] > 30 and blended[2] > 30, f"frame is not a blend: {blended}"


def test_hard_cuts_are_used_when_the_dissolve_is_switched_off(tmp_path):
    red = _solid_clip(tmp_path / "a.mp4", "red", 1.5)
    blue = _solid_clip(tmp_path / "b.mp4", "blue", 1.5)
    output = tmp_path / "joined.mp4"

    video.concat_video_clips_with_ffmpeg(
        clip_files=[red, blue],
        output_file=str(output),
        threads=2,
        output_dir=str(tmp_path),
        crossfade_duration=0.0,
    )

    with VideoFileClip(str(output), audio=False) as clip:
        # Nothing is consumed by a dissolve, so the full length survives.
        assert clip.duration == pytest.approx(3.0, abs=0.15)
        frame = clip.get_frame(1.5).reshape(-1, 3).mean(axis=0)
    # A hard cut leaves one pure colour on either side of the join.
    assert min(frame[0], frame[2]) < 20


def test_a_dissolve_that_would_shorten_the_video_falls_back_to_hard_cuts(tmp_path):
    red = _solid_clip(tmp_path / "a.mp4", "red", 1.5)
    blue = _solid_clip(tmp_path / "b.mp4", "blue", 1.5)
    output = tmp_path / "joined.mp4"

    # The narration needs all 3 seconds, so there is no room to overlap the
    # scenes: a silent tail is worse than a missing dissolve.
    video.concat_video_clips_with_ffmpeg(
        clip_files=[red, blue],
        output_file=str(output),
        threads=2,
        output_dir=str(tmp_path),
        max_duration=3.0,
        crossfade_duration=0.6,
    )

    with VideoFileClip(str(output), audio=False) as clip:
        assert clip.duration == pytest.approx(3.0, abs=0.15)


def test_an_unreadable_clip_falls_back_instead_of_failing_the_render(tmp_path, monkeypatch):
    red = _solid_clip(tmp_path / "a.mp4", "red", 1.5)
    blue = _solid_clip(tmp_path / "b.mp4", "blue", 1.5)
    output = tmp_path / "joined.mp4"
    monkeypatch.setattr(video, "probe_clip_duration", lambda _path: 0.0)

    video.concat_video_clips_with_ffmpeg(
        clip_files=[red, blue],
        output_file=str(output),
        threads=2,
        output_dir=str(tmp_path),
        crossfade_duration=0.6,
    )

    assert output.exists()
    with VideoFileClip(str(output), audio=False) as clip:
        assert clip.duration == pytest.approx(3.0, abs=0.15)


def test_probe_reports_zero_for_a_file_that_is_not_a_video(tmp_path):
    broken = tmp_path / "broken.mp4"
    broken.write_bytes(b"not a video")
    assert video.probe_clip_duration(str(broken)) == 0.0
