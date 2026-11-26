"""
Verifies that scenes actually move, and that they move differently.

The defect being fixed is a video that looks like a slideshow: every image got
the same centred 3%-per-second zoom, so no scene travelled anywhere and no two
scenes were framed differently. These tests measure rendered pixels and the
crop geometry, not the configuration.
"""

import numpy as np
import pytest
from moviepy import VideoFileClip
from PIL import Image, ImageDraw

from app.models.schema import ImageMotion
from app.services import video
from app.services.utils import camera_motion


def _detailed_image(path, width=540, height=960):
    """An image with detail everywhere, so motion in any direction registers."""
    image = Image.new("RGB", (width, height), (12, 16, 28))
    draw = ImageDraw.Draw(image)
    for y in range(0, height, 16):
        draw.line([(0, y), (width, y)], fill=(40 + (y // 16 * 5) % 160, 30, 70), width=2)
    for x in range(0, width, 16):
        draw.line([(x, 0), (x, height)], fill=(30, 50 + (x // 16 * 5) % 160, 90), width=2)
    draw.ellipse([width * 0.2, height * 0.3, width * 0.8, height * 0.7],
                 fill=(190, 90, 50), outline=(255, 220, 180), width=6)
    image.save(path)
    return str(path)


def test_consecutive_scenes_never_repeat_a_move():
    names = [camera_motion.plan_move(index, seed="video").name for index in range(10)]
    assert len(set(names)) == len(camera_motion.CAMERA_MOVES)
    for earlier, later in zip(names, names[1:]):
        assert earlier != later


def test_move_selection_is_reproducible_but_differs_between_videos():
    # The same inputs must render the same clip, or caching would serve the
    # wrong pixels.
    assert camera_motion.plan_move(3, seed="a").name == camera_motion.plan_move(3, seed="a").name
    starts = {camera_motion.plan_move(0, seed=seed).name for seed in ("a", "b", "c", "d", "e")}
    assert len(starts) > 1


@pytest.mark.parametrize("move", camera_motion.CAMERA_MOVES)
def test_the_crop_window_never_leaves_the_image(move):
    width, height = 1080, 1920
    for step in range(0, 21):
        progress = step / 20
        a, _, c, _, e, f = camera_motion.affine_coefficients(move, progress, width, height)
        # The affine maps output corners to source coordinates; both corners
        # have to land inside the image or the frame would show an edge.
        assert c >= -1e-6
        assert f >= -1e-6
        assert c + a * width <= width + 1e-6
        assert f + e * height <= height + 1e-6


@pytest.mark.parametrize("move", camera_motion.CAMERA_MOVES)
def test_every_move_stays_within_the_magnification_budget(move):
    for step in range(0, 11):
        scale, _, _ = move.at(step / 10)
        assert 1.0 <= scale <= 1.55


def test_moves_are_eased_rather_than_linear():
    # A linear ramp is the clearest sign a move was done by software. Halfway
    # through, an eased move sits at the midpoint but its rate does not.
    assert camera_motion.smoothstep(0.0) == 0.0
    assert camera_motion.smoothstep(1.0) == 1.0
    assert camera_motion.smoothstep(0.5) == pytest.approx(0.5)
    early = camera_motion.smoothstep(0.1) - camera_motion.smoothstep(0.0)
    middle = camera_motion.smoothstep(0.55) - camera_motion.smoothstep(0.45)
    assert middle > early * 2
    # Out-of-range progress is clamped, not extrapolated.
    assert camera_motion.smoothstep(-5.0) == 0.0
    assert camera_motion.smoothstep(5.0) == 1.0


def test_intensity_scales_travel_without_changing_which_move_plays():
    full = camera_motion.plan_move(2, seed="s", intensity=1.0)
    calm = camera_motion.plan_move(2, seed="s", intensity=0.25)
    assert full.name == calm.name
    assert abs(calm.end_pan_x) <= abs(full.end_pan_x)
    assert abs(calm.end_scale - calm.start_scale) < abs(full.end_scale - full.start_scale)


def test_most_moves_travel_across_the_image_unlike_the_legacy_zoom():
    width, height = 1080, 1920

    def centre_travel(move):
        start_scale, _, _ = move.at(0.0)
        end_scale, _, _ = move.at(1.0)
        start = camera_motion.affine_coefficients(move, 0.0, width, height)
        end = camera_motion.affine_coefficients(move, 1.0, width, height)
        start_centre = (start[2] + (width / 2) / start_scale,
                        start[5] + (height / 2) / start_scale)
        end_centre = (end[2] + (width / 2) / end_scale,
                      end[5] + (height / 2) / end_scale)
        return ((end_centre[0] - start_centre[0]) ** 2
                + (end_centre[1] - start_centre[1]) ** 2) ** 0.5

    # The behaviour being replaced: a centred zoom, which never reframes.
    legacy = camera_motion.CameraMove("legacy", 1.0, 1.12)
    assert centre_travel(legacy) == pytest.approx(0.0, abs=0.001)

    travelling = [move for move in camera_motion.CAMERA_MOVES if centre_travel(move) > 50]
    assert len(travelling) >= 6


def test_rendered_cinematic_clip_actually_moves(tmp_path):
    source = _detailed_image(tmp_path / "scene.png")

    rendered = {}
    for motion in (ImageMotion.static, ImageMotion.zoom, ImageMotion.cinematic):
        output = video.render_image_zoom_video(source, 3, image_motion=motion, scene_index=2)
        with VideoFileClip(output, audio=False) as clip:
            frames = [clip.get_frame(t) for t in (0.0, 0.75, 1.5, 2.25, 2.9)]
        rendered[motion] = frames

    def mean_step(frames):
        return sum(
            camera_motion.frame_difference(frames[i], frames[i + 1])
            for i in range(len(frames) - 1)
        ) / (len(frames) - 1)

    # A held still image is the failure mode being fixed.
    assert mean_step(rendered[ImageMotion.static]) < 1.0
    assert mean_step(rendered[ImageMotion.cinematic]) > 5.0
    # And the overall reframing is larger than the legacy centred zoom's.
    legacy_reframe = camera_motion.frame_difference(
        rendered[ImageMotion.zoom][0], rendered[ImageMotion.zoom][-1]
    )
    cinematic_reframe = camera_motion.frame_difference(
        rendered[ImageMotion.cinematic][0], rendered[ImageMotion.cinematic][-1]
    )
    assert cinematic_reframe > legacy_reframe


def test_neighbouring_scenes_render_different_motion(tmp_path):
    source = _detailed_image(tmp_path / "scene.png")
    first = video.render_image_zoom_video(
        source, 2, image_motion=ImageMotion.cinematic, scene_index=0
    )
    second = video.render_image_zoom_video(
        source, 2, image_motion=ImageMotion.cinematic, scene_index=1
    )
    # Different scenes of the same image must not share a cached clip, or the
    # variety would be lost to the cache.
    assert first != second
    with VideoFileClip(first, audio=False) as clip_a, VideoFileClip(second, audio=False) as clip_b:
        assert camera_motion.frame_difference(clip_a.get_frame(1.9), clip_b.get_frame(1.9)) > 2.0


def test_preprocess_gives_each_material_its_own_scene_position(tmp_path, monkeypatch):
    from app.models.schema import MaterialInfo
    from app.utils import utils

    directory = tmp_path / "local_videos"
    directory.mkdir()
    monkeypatch.setattr(utils, "storage_dir", lambda *a, **k: str(directory))
    for index in range(3):
        _detailed_image(directory / f"scene{index}.png")

    seen = []

    def record(image_path, clip_duration, image_motion=None, scene_index=0):
        seen.append(scene_index)
        return str(directory / "out.mp4")

    monkeypatch.setattr(video, "render_image_zoom_video", record)
    video.preprocess_video(
        materials=[MaterialInfo(url=f"scene{index}.png") for index in range(3)],
        clip_duration=3,
        image_motion=ImageMotion.cinematic,
    )
    assert seen == [0, 1, 2]


def test_frame_difference_rejects_mismatched_frames():
    with pytest.raises(ValueError):
        camera_motion.frame_difference(np.zeros((4, 4, 3)), np.zeros((5, 4, 3)))


def test_an_empty_catalogue_is_an_error_not_a_silent_still():
    with pytest.raises(ValueError):
        camera_motion.plan_move(0, moves=())
