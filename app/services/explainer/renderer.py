"""Chunked, parallel scene rendering -> one H.264 clip per scene (cached)."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from concurrent.futures import ProcessPoolExecutor
import multiprocessing as mp

from loguru import logger

from app.utils import utils

from . import gfx as G
from . import scenes as S
from . import subtitles as SUB
from .models import Scene, SceneTiming, Word

STYLE_VERSION = "1"
CHUNK_FRAMES = 60


def n_frames(duration: float, fps: int) -> int:
    return max(1, int(round(duration * fps)))


def scene_hash(scene: Scene, timing: SceneTiming, fps: int, fast: bool, index: int, total: int) -> str:
    blob = json.dumps([scene.model_dump(), timing.model_dump(exclude={"audio_path", "start"}), fps, fast, index, total, STYLE_VERSION],
                      sort_keys=True, default=str)
    return hashlib.sha1(blob.encode()).hexdigest()[:12]


def _encoder_cmd(fps: int, out: str) -> list[str]:
    return [utils.get_ffmpeg_binary(), "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{G.W}x{G.H}", "-r", str(fps), "-i", "-", "-an", "-c:v", "libx264", "-preset", "veryfast",
            "-crf", "17", "-pix_fmt", "yuv420p", "-profile:v", "high", "-g", str(fps * 2),
            "-sc_threshold", "0", "-movflags", "+faststart", out]


def render_chunk(job: dict) -> dict:
    """Worker: render frames [f0, f1) of one scene into ``job['out']``."""
    try:
        scene = Scene.model_validate(job["scene"])
        words = [Word(**w) for w in job["words"]]
        ctx = S.Ctx(index=job["index"], total=job["total"], duration=job["duration"], fast=job["fast"])
        cues = SUB.build_cues(words)
        flags = SUB.keyword_flags(words, scene.keywords)
        fmap = {id(w): f for w, f in zip(words, flags)}
        fps = job["fps"]
        proc = subprocess.Popen(_encoder_cmd(fps, job["out"]), stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            for f in range(job["f0"], job["f1"]):
                t = f / fps
                frame = S.render_scene_frame(scene, t, ctx)
                if scene.role != "cta" or True:
                    SUB.draw_caption(frame, cues, fmap, t, words)
                proc.stdin.write(frame.tobytes())
            proc.stdin.close()
            err = proc.stderr.read().decode(errors="ignore")
            if proc.wait() != 0:
                raise RuntimeError("ffmpeg encode failed: " + err[-300:])
        finally:
            if proc.poll() is None:
                proc.kill()
        return {"scene": scene.id, "part": job["part"], "error": None}
    except Exception as exc:  # noqa: BLE001
        return {"scene": job["scene"]["id"], "part": job["part"], "error": f"{type(exc).__name__}: {exc}"}


def make_pool(workers: int | None = None) -> ProcessPoolExecutor:
    workers = workers or max(1, min(os.cpu_count() or 2, 8))
    return ProcessPoolExecutor(max_workers=workers, mp_context=mp.get_context("spawn"))


def _concat(parts: list[str], out: str):
    lst = out + ".txt"
    with open(lst, "w") as fh:
        for p in parts:
            fh.write(f"file '{os.path.abspath(p)}'\n")
    subprocess.run([utils.get_ffmpeg_binary(), "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out], check=True)
    os.remove(lst)


def render_scenes(scenes: list[Scene], timings: list[SceneTiming], fps: int, out_dir: str, pool: ProcessPoolExecutor,
                  only: set[str] | None = None, fast: bool = False, progress=None) -> dict[str, dict]:
    """Render (or reuse cached) clips. Returns {scene_id: {path, error}}."""
    os.makedirs(out_dir, exist_ok=True)
    total = len(scenes)
    results: dict[str, dict] = {}
    jobs, plans = [], {}
    for i, (sc, tm) in enumerate(zip(scenes, timings), start=1):
        h = scene_hash(sc, tm, fps, fast, i, total)
        clip = os.path.join(out_dir, f"{sc.id}_{h}.mp4")
        results[sc.id] = {"path": clip, "error": None}
        if os.path.exists(clip):
            if only is not None and sc.id in only:
                os.remove(clip)          # forced re-render of a scene that failed QC
            else:
                continue
        nf = n_frames(tm.duration, fps)
        parts = []
        for k, f0 in enumerate(range(0, nf, CHUNK_FRAMES)):
            part = os.path.join(out_dir, f"{sc.id}_{h}.part{k:02d}.mp4")
            parts.append(part)
            jobs.append({"scene": sc.model_dump(), "words": [w.model_dump() for w in tm.words], "index": i, "total": total,
                         "duration": nf / fps, "fast": fast, "fps": fps, "f0": f0, "f1": min(nf, f0 + CHUNK_FRAMES),
                         "out": part, "part": k})
        plans[sc.id] = (clip, parts)
    if not jobs:
        return results
    logger.info(f"rendering {len(jobs)} chunks for {len(plans)} scene(s)")
    done = 0
    for res in pool.map(render_chunk, jobs):
        done += 1
        if res["error"]:
            results[res["scene"]]["error"] = res["error"]
        if progress:
            progress(done / len(jobs))
    for sid, (clip, parts) in plans.items():
        if results[sid]["error"]:
            continue
        try:
            _concat(parts, clip)
        except Exception as exc:  # noqa: BLE001
            results[sid]["error"] = f"concat failed: {exc}"
        for p in parts:
            if os.path.exists(p):
                os.remove(p)
    return results
