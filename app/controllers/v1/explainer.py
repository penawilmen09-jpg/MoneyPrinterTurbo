"""REST API for the MIXED EXPLAINER mode (status is read with the existing GET /tasks/{id})."""

import json
import os
from typing import Optional

from fastapi import Depends, Path, Request
from loguru import logger

from app.controllers import base
from app.controllers.manager.base_manager import TaskQueueFullError
from app.controllers.v1.base import new_router
from app.controllers.v1.video import task_manager
from app.models.exception import HttpException
from app.services import state as sm
from app.services.explainer import pipeline
from app.services.explainer.models import ExplainerParams, Plan
from app.utils import utils

router = new_router(dependencies=[Depends(base.verify_token)])


def _submit(request: Request, task_id: str, params: ExplainerParams):
    request_id = base.get_task_id(request)
    try:
        sm.state.update_task(task_id, explainer_params=params.model_dump(exclude={"plan"}), stage="queued")
        try:
            task_manager.add_task(pipeline.start, task_id=task_id, params=params)
        except Exception:
            sm.state.delete_task(task_id)
            raise
    except TaskQueueFullError as exc:
        raise HttpException(task_id=task_id, status_code=429, message=f"{request_id}: {exc}")
    return utils.get_response(200, {"task_id": task_id, "request_id": request_id, "params": params.model_dump(exclude={"plan"})})


@router.post("/explainers", summary="MIXED EXPLAINER: topic -> finished 2D+3D explainer video")
def create_explainer(request: Request, body: ExplainerParams):
    return _submit(request, utils.get_uuid(), body)


@router.get("/explainers/{task_id}/plan", summary="Read the researched script/scene plan (for review)")
def get_plan(task_id: str = Path(...)):
    path = os.path.join(utils.task_dir(task_id), "plan.json")
    if not os.path.exists(path):
        raise HttpException(task_id=task_id, status_code=404, message="plan not found")
    return utils.get_response(200, json.load(open(path, encoding="utf-8")))


@router.post("/explainers/{task_id}/produce", summary="Approve (optionally edited) plan and produce the video")
def produce_explainer(request: Request, task_id: str = Path(...), plan: Optional[Plan] = None):
    task = sm.state.get_task(task_id)
    if not task or not task.get("explainer_params"):
        raise HttpException(task_id=task_id, status_code=404, message="explainer task not found")
    path = os.path.join(utils.task_dir(task_id), "plan.json")
    if plan is None:
        if not os.path.exists(path):
            raise HttpException(task_id=task_id, status_code=409, message="no plan to produce yet")
        plan = Plan.model_validate_json(open(path, encoding="utf-8").read())
    params = ExplainerParams(**{**task["explainer_params"], "review_script": False, "plan": plan})
    return _submit(request, task_id, params)


@router.get("/explainers/{task_id}/qc", summary="Quality-control report of the finished video")
def get_qc(task_id: str = Path(...)):
    path = os.path.join(utils.task_dir(task_id), "qc.json")
    if not os.path.exists(path):
        raise HttpException(task_id=task_id, status_code=404, message="qc report not found")
    return utils.get_response(200, json.load(open(path, encoding="utf-8")))
