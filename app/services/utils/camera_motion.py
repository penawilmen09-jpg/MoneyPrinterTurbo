"""
Virtual camera moves for still illustrations.

Why this module exists
----------------------
The original image-to-clip renderer had exactly one move: a centred zoom-in
of 3% per second, applied identically to every image in a video
(``video._smooth_zoom_clip``). Every scene therefore started and ended on the
same composition, grew at the same rate and moved in the same direction, so a
finished video reads as a slideshow with a slow zoom rather than as a
documentary with a camera.

This module replaces that single move with a catalogue of real camera moves --
push in, pull out, pan while pushing, tilt, diagonal drift, tight-to-wide
reveal -- chosen so that consecutive scenes never share a move, eased so they
accelerate and settle like a camera on a rig instead of sliding linearly, and
computed per frame with subpixel accuracy so slow moves do not judder.

Geometry
--------
A move is a crop window travelling across the source image. For output pixel
``(x, y)`` the source is sampled at::

    source_x = center_x + (x - width / 2) / scale
    source_y = center_y + (y - height / 2) / scale

which is a PIL affine transform. ``scale`` is always at least 1.0, and the
crop centre is constrained to the margin that the current scale leaves
available, so the window can never sample past the edge of the image. That is
what keeps black slivers out of a pan.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from typing import Sequence

import numpy as np
from PIL import Image

# A move must keep some magnification in hand at all times, otherwise there is
# no margin to pan into: at scale 1.0 the crop already fills the image.
_MIN_SCALE = 1.0
# Headroom cap. Beyond roughly 1.5x a 1080-wide illustration starts to show
# interpolation softness on a phone screen.
_MAX_SCALE = 1.55


def smoothstep(progress: float) -> float:
    """
    Ease-in-out curve.

    A camera operator accelerates into a move and settles out of it. A linear
    ramp is the single clearest tell that a move was done by software, so
    every move here is shaped by this curve.
    """
    clamped = min(1.0, max(0.0, progress))
    return clamped * clamped * (3.0 - 2.0 * clamped)


@dataclass(frozen=True)
class CameraMove:
    """
    One camera move over the full duration of a scene.

    ``pan`` values are fractions (-1.0 to 1.0) of the margin the scale leaves
    available, not pixels, so the same move works on any image size and can
    never push the crop window outside the frame.
    """

    name: str
    start_scale: float
    end_scale: float
    start_pan_x: float = 0.0
    start_pan_y: float = 0.0
    end_pan_x: float = 0.0
    end_pan_y: float = 0.0

    def scaled(self, intensity: float) -> "CameraMove":
        """
        Return the same move with its travel scaled by ``intensity``.

        1.0 is the designed amount. Lower values make a calmer video without
        changing which move plays where, so the look can be dialled back
        without losing the variety between scenes.
        """
        factor = max(0.0, min(2.0, float(intensity)))
        midpoint = (self.start_scale + self.end_scale) / 2.0

        def toward_mid(value: float) -> float:
            return midpoint + (value - midpoint) * factor

        return CameraMove(
            name=self.name,
            start_scale=_clamp_scale(toward_mid(self.start_scale)),
            end_scale=_clamp_scale(toward_mid(self.end_scale)),
            start_pan_x=self.start_pan_x * factor,
            start_pan_y=self.start_pan_y * factor,
            end_pan_x=self.end_pan_x * factor,
            end_pan_y=self.end_pan_y * factor,
        )

    def at(self, progress: float) -> tuple[float, float, float]:
        """The scale and pan fractions at ``progress`` (0.0 to 1.0), eased."""
        eased = smoothstep(progress)
        scale = self.start_scale + (self.end_scale - self.start_scale) * eased
        pan_x = self.start_pan_x + (self.end_pan_x - self.start_pan_x) * eased
        pan_y = self.start_pan_y + (self.end_pan_y - self.start_pan_y) * eased
        return _clamp_scale(scale), pan_x, pan_y


def _clamp_scale(scale: float) -> float:
    if not math.isfinite(scale):
        return _MIN_SCALE
    return max(_MIN_SCALE, min(_MAX_SCALE, scale))


# The catalogue. Each entry is a move a documentary editor would actually
# reach for. They are ordered so that neighbours differ in both direction and
# whether the camera is opening up or closing in, because the point of the
# catalogue is that two scenes in a row never feel the same.
CAMERA_MOVES: tuple[CameraMove, ...] = (
    # Slow push into the centre of the frame: the default documentary move.
    CameraMove("push_in", 1.02, 1.20),
    # Opening up from a tight framing. Good after a push, as the release.
    CameraMove("pull_out", 1.26, 1.04),
    # Push while travelling right, as if following the subject.
    CameraMove("pan_right_push", 1.10, 1.26, -0.75, 0.0, 0.70, 0.0),
    # Lift from the lower part of the frame while opening up: a reveal.
    CameraMove("reveal_up", 1.30, 1.08, 0.0, 0.85, 0.0, -0.20),
    # Push while travelling left.
    CameraMove("pan_left_push", 1.10, 1.26, 0.75, 0.0, -0.70, 0.0),
    # Settle downward onto a detail.
    CameraMove("tilt_down_push", 1.06, 1.24, 0.0, -0.70, 0.0, 0.55),
    # Diagonal drift: the quietest move, for a scene carrying dense narration.
    CameraMove("drift_diagonal", 1.16, 1.26, -0.55, -0.50, 0.45, 0.40),
    # Open up while travelling right: for an establishing scene.
    CameraMove("pan_right_pull", 1.28, 1.08, -0.60, 0.0, 0.50, 0.0),
    # Tilt up onto something above the subject.
    CameraMove("tilt_up_push", 1.06, 1.24, 0.0, 0.70, 0.0, -0.55),
    # Near-static hold with the slightest breath of movement, so a scene that
    # needs the viewer to read a diagram is not fighting a moving camera.
    CameraMove("slow_breath", 1.04, 1.10),
)


def plan_move(
    scene_index: int,
    *,
    seed: str = "",
    intensity: float = 1.0,
    moves: Sequence[CameraMove] = CAMERA_MOVES,
) -> CameraMove:
    """
    Choose the camera move for one scene.

    Selection walks the catalogue by scene index, so scene 0, 1 and 2 always
    get three different moves and a run of scenes cycles through the whole
    catalogue before repeating. ``seed`` (normally the image path or the video
    topic) rotates the starting point, so two videos built from the same
    number of scenes do not open with the same move, while the same inputs
    always produce the same result -- rendering has to be reproducible for
    caching and for tests.
    """
    if not moves:
        raise ValueError("no camera moves available")
    offset = 0
    if seed:
        digest = hashlib.sha256(seed.encode("utf-8", errors="replace")).digest()
        offset = digest[0]
    index = (int(scene_index) + offset) % len(moves)
    return moves[index].scaled(intensity)


def affine_coefficients(
    move: CameraMove, progress: float, width: int, height: int
) -> tuple[float, float, float, float, float, float]:
    """
    The PIL affine coefficients that sample the crop window at ``progress``.

    PIL's ``Image.AFFINE`` maps an output coordinate to a source coordinate,
    so these are the inverse of the crop: output ``(x, y)`` reads source
    ``(a*x + b*y + c, d*x + e*y + f)``.
    """
    scale, pan_x, pan_y = move.at(progress)
    half_width = width / 2.0
    half_height = height / 2.0
    # The distance the crop centre may travel at this scale before the window
    # would reach the edge of the image.
    margin_x = half_width * (1.0 - 1.0 / scale)
    margin_y = half_height * (1.0 - 1.0 / scale)
    center_x = half_width + max(-1.0, min(1.0, pan_x)) * margin_x
    center_y = half_height + max(-1.0, min(1.0, pan_y)) * margin_y
    return (
        1.0 / scale,
        0.0,
        center_x - half_width / scale,
        0.0,
        1.0 / scale,
        center_y - half_height / scale,
    )


def warp_frame(
    image: Image.Image,
    move: CameraMove,
    progress: float,
    *,
    resample: int = Image.BICUBIC,
) -> Image.Image:
    """Render one frame of the move at full canvas size with subpixel accuracy."""
    width, height = image.size
    return image.transform(
        (width, height),
        Image.AFFINE,
        affine_coefficients(move, progress, width, height),
        resample=resample,
    )


def describe_move(move: CameraMove, duration: float) -> str:
    """A one-line summary for the task log, so a render can be audited."""
    start_scale, start_x, start_y = move.at(0.0)
    end_scale, end_x, end_y = move.at(1.0)
    travel = math.hypot(end_x - start_x, end_y - start_y)
    return (
        f"camera '{move.name}' over {duration:.2f}s: "
        f"scale {start_scale:.3f}->{end_scale:.3f}, "
        f"pan travel {travel:.2f} of available margin"
    )


def frame_difference(first: np.ndarray, second: np.ndarray) -> float:
    """
    Mean absolute difference between two frames, 0-255.

    Used by the tests to prove a rendered clip actually moves: a still image
    held on screen scores 0, and anything the eye reads as motion scores well
    above it.
    """
    left = np.asarray(first, dtype=np.float64)
    right = np.asarray(second, dtype=np.float64)
    if left.shape != right.shape:
        raise ValueError("frames must have the same shape")
    return float(np.mean(np.abs(left - right)))
