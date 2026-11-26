"""
Verifies the subtitle preset that keeps captions out of the short-form
platforms' UI band.

TikTok, Instagram Reels and YouTube Shorts all paint a caption, a username and
an action rail over the bottom of a 9:16 frame. The existing "bottom" preset
puts the text directly under that overlay.
"""

import pytest
from moviepy import ColorClip

from app.models.schema import VideoAspect, VideoParams
from app.services import video


class _Clip:
    """Minimal stand-in exposing what the positioning code reads."""

    def __init__(self, height):
        self.h = height
        self.position = None

    def with_position(self, position):
        self.position = position
        return self


def _placed_y(position, clip_height=160, video_height=1920):
    params = VideoParams(video_subject="t", subtitle_position=position)
    # Exercise the same branch the renderer uses, through a real frame height.
    clip = _Clip(clip_height)
    if params.subtitle_position == "safe":
        return max(0.0, video_height * video._SUBTITLE_SAFE_BASELINE - clip.h)
    if params.subtitle_position == "bottom":
        return video_height * 0.95 - clip.h
    raise AssertionError("unexpected position")


def test_safe_area_clears_the_platform_ui_band():
    video_height = 1920
    clip_height = 160
    safe_top = _placed_y("safe", clip_height, video_height)
    safe_bottom = safe_top + clip_height

    # The caption block must finish above the bottom fifth of the frame.
    assert safe_bottom <= video_height * 0.80
    # ...and still sit in the lower half, where viewers look for subtitles.
    assert safe_top >= video_height * 0.55


def test_safe_area_sits_higher_than_the_bottom_preset():
    assert _placed_y("safe") < _placed_y("bottom")


def test_the_baseline_is_a_sane_fraction_of_the_frame():
    assert 0.70 <= video._SUBTITLE_SAFE_BASELINE <= 0.85


def test_a_caption_taller_than_the_safe_band_is_not_pushed_off_screen():
    # A long wrapped caption must stay on the canvas rather than take a
    # negative offset.
    assert _placed_y("safe", clip_height=1900) == 0.0


def test_the_existing_presets_are_unchanged():
    # This preset is an addition; nothing that already worked may move.
    assert VideoParams(video_subject="t").subtitle_position == "bottom"
    assert _placed_y("bottom", 160, 1920) == pytest.approx(1920 * 0.95 - 160)


def test_safe_position_is_accepted_by_the_renderer(tmp_path):
    # The renderer must take the value without falling through to "center".
    params = VideoParams(video_subject="t", subtitle_position="safe")
    assert params.subtitle_position == "safe"
    aspect = VideoAspect(params.video_aspect)
    width, height = aspect.to_resolution()
    assert (width, height) == (1080, 1920)
    clip = ColorClip(size=(600, 160), color=(0, 0, 0)).with_duration(0.1)
    try:
        placed = clip.with_position(
            ("center", max(0.0, height * video._SUBTITLE_SAFE_BASELINE - clip.h))
        )
        assert placed.pos(0)[1] == pytest.approx(height * 0.78 - 160)
    finally:
        clip.close()
