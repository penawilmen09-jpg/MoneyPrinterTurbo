"""MIXED EXPLAINER orchestration: topic -> research -> script -> narration ->
2D+3D render -> audio mix -> QC (with per-scene repair) -> final-1.mp4."""

from __future__ import annotations

import json
import math
import os
import subprocess
import time
from typing import Callable

from loguru import logger

from app.models import const
from app.services import state as sm
from app.utils import utils

from . import audio as A
from . import qc as QC
from . import renderer as R
from . import script as SC
from . import subtitles as SUB
from .models import ExplainerParams, Plan, Scene, SceneTiming, Visual
from .narration import ElevenLabsNarrator, NarrationError, NarrationResult, Narrator

LEAD, TAIL, TAIL_LAST = 0.25, 0.40, 0.90
MIN_SCENE = 2.5
MAX_REPAIR_ROUNDS = 2


class ExplainerError(RuntimeError):
    def __init__(self, stage: str, message: str):
        super().__init__(message)
        self.stage = stage


def _update(task_id: str | None, **kw):
    if not task_id:
        return
    try:
        sm.state.update_task(task_id, **kw)
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"state update failed: {exc}")


def build_timings(plan: Plan, narr: dict[str, NarrationResult], fps: int) -> list[SceneTiming]:
    timings, cursor = [], 0.0
    for i, sc in enumerate(plan.scenes):
        n = narr[sc.id]
        lead = LEAD
        tail = TAIL_LAST if i == len(plan.scenes) - 1 else TAIL
        dur = max(MIN_SCENE, lead + n.duration + tail)
        dur = math.ceil(dur * fps) / fps          # whole frames: audio/video stay locked
        words = [w.model_copy(update={"start": w.start + lead, "end": w.end + lead}) for w in n.words]
        timings.append(SceneTiming(id=sc.id, start=cursor, duration=dur, lead=lead, audio_duration=n.duration,
                                   words=words, audio_path=n.audio_path))
        cursor += dur
    return timings


def _fallback_scene(sc: Scene) -> Scene:
    labels = (sc.keywords or [w for w in sc.narration.split()[:3]])[:3]
    return sc.model_copy(update={"visual": Visual(kind="flow", title=sc.visual.title or "Idea clave", labels=labels)})


def _mux(clips: list[str], audio_m4a: str, out: str, workdir: str):
    lst = os.path.join(workdir, "clips.txt")
    with open(lst, "w") as fh:
        for c in clips:
            fh.write(f"file '{os.path.abspath(c)}'\n")
    video = os.path.join(workdir, "video_only.mp4")
    subprocess.run([utils.get_ffmpeg_binary(), "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", video], check=True)
    subprocess.run([utils.get_ffmpeg_binary(), "-y", "-v", "error", "-i", video, "-i", audio_m4a, "-map", "0:v:0", "-map", "1:a:0",
                    "-c", "copy", "-movflags", "+faststart", out], check=True)


def make_plan(params: ExplainerParams, llm=None) -> Plan:
    if params.plan is not None:
        issues = SC.validate_plan(params.plan, params.duration)
        hard = [i for i in issues if "palabras" not in i]
        if hard:
            raise ExplainerError("script", "El guion editado no es válido: " + "; ".join(hard))
        return params.plan
    try:
        return SC.generate_plan(params.topic, params.duration, llm=llm)
    except SC.ScriptError as exc:
        raise ExplainerError("script", str(exc)) from exc
    except Exception as exc:  # noqa: BLE001 - e.g. no LLM configured
        raise ExplainerError("script", f"No se pudo generar el guion: {exc}. Configura un proveedor LLM o usa un guion propio.") from exc


def run(task_id: str | None, params: ExplainerParams, narrator: Narrator | None = None, llm=None, pool=None,
        fast: bool = False, workdir: str | None = None, progress: Callable[[str, float], None] | None = None) -> dict:
    """Execute the whole production. Raises ExplainerError with a clear message."""
    t_start = time.time()
    workdir = workdir or utils.task_dir(task_id or "explainer-adhoc")
    os.makedirs(workdir, exist_ok=True)

    def step(stage: str, pct: int, frac: float = 0.0, nxt: int | None = None):
        p = pct + int((nxt - pct) * frac) if nxt else pct
        _update(task_id, state=const.TASK_STATE_PROCESSING, progress=p, stage=stage)
        if progress:
            progress(stage, p)

    step("research", 5)
    plan = make_plan(params, llm=llm)
    with open(os.path.join(workdir, "plan.json"), "w", encoding="utf-8") as fh:
        fh.write(plan.model_dump_json(indent=2))
    with open(os.path.join(workdir, "script.json"), "w", encoding="utf-8") as fh:   # same shape other modes persist
        json.dump({"script": plan.narration_text(), "search_terms": [], "params": params.model_dump(exclude={"plan"})}, fh, ensure_ascii=False)
    if params.review_script and params.plan is None:
        _update(task_id, state=const.TASK_STATE_COMPLETE, progress=100, stage="awaiting_review", awaiting_review=True,
                script=plan.narration_text(), videos=[])
        return {"awaiting_review": True, "plan": plan}

    # ---------------------------------------------------------------- narration
    step("narration", 18)
    narrator = narrator or ElevenLabsNarrator(params.voice_name)
    narr: dict[str, NarrationResult] = {}
    ndir = os.path.join(workdir, "narration")
    for i, sc in enumerate(plan.scenes):
        prev = plan.scenes[i - 1].narration if i else ""
        nxt = plan.scenes[i + 1].narration if i + 1 < len(plan.scenes) else ""
        try:
            narr[sc.id] = narrator(sc, prev, nxt, ndir)
        except NarrationError as exc:
            raise ExplainerError("narration", f"Escena {sc.id}: {exc}") from exc
        step("narration", 18, (i + 1) / len(plan.scenes), 34)
    timings = build_timings(plan, narr, params.fps)
    total = sum(t.duration for t in timings)
    logger.info(f"explainer timeline: {total:.1f}s over {len(timings)} scenes, words={plan.word_count()}")
    lo, hi = QC.DURATION_WINDOW[params.duration]
    if not (45.0 <= total <= 60.0):
        raise ExplainerError("script", f"La narración real dura {total:.1f}s (fuera de 45-60s). Ajusta el guion en el modo 'revisar guion' "
                                       f"({plan.word_count()} palabras; ~{SC.WORDS_PER_SECOND} palabras/s).")

    # ------------------------------------------------------------------- render
    own_pool = pool is None
    pool = pool or R.make_pool()
    scenes = list(plan.scenes)
    sdir = os.path.join(workdir, "scenes")
    try:
        step("render", 35)
        res = R.render_scenes(scenes, timings, params.fps, sdir, pool, fast=fast,
                              progress=lambda f: step("render", 35, f, 78))
        # ----------------------------------------------------------- audio mix
        step("audio", 80)
        mix = A.build_mix(plan, timings, total, os.path.join(workdir, "audio"), music=params.music)
        a_final = os.path.join(workdir, "audio", "final.m4a")
        A.loudnorm_encode(mix["premix"], a_final)
        SUB.write_srt(os.path.join(workdir, "subtitles.srt"), timings)

        final = os.path.join(workdir, "final-1.mp4")
        report = None
        for rnd in range(MAX_REPAIR_ROUNDS + 1):
            broken = {sid for sid, r in res.items() if r["error"]}
            if broken:
                logger.warning(f"scene render errors: { {k: res[k]['error'] for k in broken} }")
                if rnd >= MAX_REPAIR_ROUNDS - 1:        # last resort: simpler visual for that scene only
                    scenes = [_fallback_scene(s) if s.id in broken else s for s in scenes]
                res = {**res, **R.render_scenes(scenes, timings, params.fps, sdir, pool, only=broken, fast=fast)}
                broken = {sid for sid, r in res.items() if r["error"]}
                if broken:
                    raise ExplainerError("render", f"Falló el render de {sorted(broken)}: {[res[b]['error'] for b in broken]}")
            step("assemble", 90)
            _mux([res[s.id]["path"] for s in scenes], a_final, final, workdir)
            step("qc", 94)
            report = QC.run_qc(final, plan, timings, mix, params.duration, params.fps, workdir)
            if report["passed"] or not report["failing_scenes"]:
                break
            logger.warning(f"QC failed scenes {report['failing_scenes']}; re-rendering only those (round {rnd + 1})")
            res = {**res, **R.render_scenes(scenes, timings, params.fps, sdir, pool, only=set(report["failing_scenes"]), fast=fast)}
            if rnd >= MAX_REPAIR_ROUNDS - 1:
                scenes = [_fallback_scene(s) if s.id in report["failing_scenes"] else s for s in scenes]
    finally:
        if own_pool:
            pool.shutdown(wait=True)

    summary = {"video": final, "duration": report["duration"], "qc_passed": report["passed"], "qc": report,
               "subtitles": os.path.join(workdir, "subtitles.srt"), "plan": plan,
               "elevenlabs_requests": getattr(narrator, "calls", None), "elapsed_s": round(time.time() - t_start, 1)}
    _update(task_id, state=const.TASK_STATE_COMPLETE, progress=100, stage="done", videos=[final],
            subtitle_path=summary["subtitles"], qc_passed=report["passed"],
            qc_failed=[c["name"] for c in report["checks"] if not c["ok"]], script=plan.narration_text())
    return summary


def start(task_id: str, params: ExplainerParams, **kw) -> dict | None:
    """Task-manager entry point: any failure becomes a queryable failed state."""
    try:
        return run(task_id, params, **kw)
    except ExplainerError as exc:
        logger.error(f"explainer task {task_id} failed at {exc.stage}: {exc}")
        _update(task_id, state=const.TASK_STATE_FAILED, progress=0, failed_stage=exc.stage, error=str(exc))
    except Exception as exc:  # noqa: BLE001
        logger.exception(f"explainer task {task_id} crashed")
        _update(task_id, state=const.TASK_STATE_FAILED, progress=0, failed_stage="pipeline", error=f"{type(exc).__name__}: {exc}")
    return None
