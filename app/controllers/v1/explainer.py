"""API del generador local de videos explicativos 2D (sin servicios de pago).

POST /api/v1/explainer/videos        -> inicia el render en segundo plano
GET  /api/v1/explainer/videos/{id}   -> estado y progreso
GET  /api/v1/explainer/videos/{id}/download -> MP4 terminado
"""

from __future__ import annotations

import os
import threading
import time
from typing import Any
from uuid import uuid4

from fastapi import Depends, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.controllers import base
from app.controllers.v1.base import new_router
from app.models.exception import HttpException
from app.utils import utils

router = new_router(dependencies=[Depends(base.verify_token)])

_JOBS: dict[str, dict[str, Any]] = {}
_LOCK = threading.Lock()
_MAX_JOBS = 50
_RENDER_SLOT = threading.Semaphore(1)  # un render a la vez: usa todos los núcleos


class ExplainerRequest(BaseModel):
    script: dict | None = Field(default=None, description="Guion en el formato JSON del paquete")
    text: str | None = Field(default=None, description="Guion en texto plano (un párrafo = una escena)")
    title: str = "Video explicativo"
    tts: str = Field(default="auto", pattern="^(auto|edge|piper|espeak|silent)$")
    voice: str | None = None
    music: str | None = Field(default=None, description="builtin:upbeat|tense|calm, ruta o none")
    draft: bool = False
    subtitles: bool = True


def _run(job_id: str, script, req: ExplainerRequest, out: str) -> None:
    from app.services.animated_explainer import render_video

    def progress(stage: str, frac: float) -> None:
        with _LOCK:
            _JOBS[job_id].update(stage=stage, progress=round(frac, 3))

    with _RENDER_SLOT:
        try:
            with _LOCK:
                _JOBS[job_id]["state"] = "running"
            res = render_video(script, out, tts=req.tts, voice=req.voice, music=req.music,
                               draft=req.draft, subtitles_on=req.subtitles, progress=progress)
            with _LOCK:
                _JOBS[job_id].update(state="done", progress=1.0, duration=res.duration,
                                     tts_providers=res.tts_providers)
        except Exception as e:  # el error se informa por el endpoint de estado
            with _LOCK:
                _JOBS[job_id].update(state="failed", error=str(e)[:500])


@router.post("/explainer/videos", summary="Create a local 2D explainer video (free, offline render)")
def create_explainer(request: Request, body: ExplainerRequest):
    from app.services.animated_explainer.script import ScriptError, from_dict, parse_plain_text

    task_id = base.get_task_id(request)
    try:
        if body.script is not None:
            script = from_dict(body.script)
        elif body.text:
            script = parse_plain_text(body.text, title=body.title)
        else:
            raise ScriptError("Envía 'script' (JSON) o 'text' (texto plano)")
    except ScriptError as e:
        raise HttpException(task_id=task_id, status_code=400, message=str(e))
    job_id = str(uuid4())
    out_dir = utils.storage_dir("explainer", create=True)
    out = os.path.join(out_dir, f"{job_id}.mp4")
    with _LOCK:
        if len(_JOBS) >= _MAX_JOBS:  # descarta los más antiguos ya terminados
            for k in [k for k, v in sorted(_JOBS.items(), key=lambda kv: kv[1]["created"])
                      if v["state"] in ("done", "failed")][: len(_JOBS) - _MAX_JOBS + 1]:
                _JOBS.pop(k, None)
        _JOBS[job_id] = dict(state="queued", stage="queued", progress=0.0, created=time.time(),
                             file=out, scenes=len(script.scenes))
    threading.Thread(target=_run, args=(job_id, script, body, out), daemon=True).start()
    return {"status": 200, "message": "success", "data": {"job_id": job_id}}


def _job(task_id: str, job_id: str) -> dict:
    with _LOCK:
        job = _JOBS.get(job_id)
        if job is None:
            raise HttpException(task_id=task_id, status_code=404, message="job not found")
        return dict(job)


@router.get("/explainer/videos/{job_id}", summary="Status of an explainer render")
def explainer_status(request: Request, job_id: str):
    job = _job(base.get_task_id(request), job_id)
    job.pop("file", None)
    return {"status": 200, "message": "success", "data": job}


@router.get("/explainer/videos/{job_id}/download", summary="Download the finished MP4")
def explainer_download(request: Request, job_id: str):
    task_id = base.get_task_id(request)
    job = _job(task_id, job_id)
    if job["state"] != "done" or not os.path.isfile(job["file"]):
        raise HttpException(task_id=task_id, status_code=409, message="video not ready")
    return FileResponse(job["file"], media_type="video/mp4", filename="explainer.mp4")
