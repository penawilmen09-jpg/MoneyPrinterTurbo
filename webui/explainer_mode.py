"""WebUI panel for the MIXED EXPLAINER mode (rendered next to the classic mode)."""

import json
import os
import threading

import streamlit as st

from app.models import const
from app.services import state as sm
from app.services import voice as voice_service
from app.services.explainer import pipeline
from app.services.explainer.models import DEFAULT_VOICE_ID, DEFAULT_VOICE_NAME, ExplainerParams, Plan
from app.utils import utils

STAGE_LABELS = {
    "queued": "En cola", "research": "Investigando y escribiendo el guion", "narration": "Generando la narración (ElevenLabs)",
    "render": "Animando escenas 2D + 3D", "audio": "Mezclando audio (-16 LUFS)", "assemble": "Ensamblando vídeo",
    "qc": "Control de calidad", "done": "Terminado", "awaiting_review": "Guion listo para revisar",
}


def _launch(task_id: str, params: ExplainerParams):
    sm.state.update_task(task_id, explainer_params=params.model_dump(exclude={"plan"}), stage="queued")
    threading.Thread(target=pipeline.start, kwargs={"task_id": task_id, "params": params}, daemon=True).start()


@st.fragment(run_every=3)
def _status():
    task_id = st.session_state.get("mx_task_id")
    if not task_id:
        return
    task = sm.state.get_task(task_id)
    if not task:
        st.warning("Tarea no encontrada.")
        return
    state, stage = task.get("state"), task.get("stage", "")
    if state == const.TASK_STATE_FAILED:
        st.error(f"Falló en «{task.get('failed_stage')}»: {task.get('error')}")
        return
    if task.get("awaiting_review"):
        _review(task_id, task)
        return
    if state == const.TASK_STATE_COMPLETE and task.get("videos"):
        st.success("Vídeo listo" + ("" if task.get("qc_passed") else " (con avisos de calidad)"))
        st.video(task["videos"][0])
        qc_path = os.path.join(utils.task_dir(task_id), "qc.json")
        if os.path.exists(qc_path):
            with st.expander("Control de calidad"):
                for c in json.load(open(qc_path, encoding="utf-8"))["checks"]:
                    st.write(("✅ " if c["ok"] else "❌ ") + f"**{c['name']}** — {c['detail']}")
        return
    st.progress(min(int(task.get("progress", 0)), 100) / 100, text=STAGE_LABELS.get(stage, stage or "Procesando"))


def _review(task_id: str, task: dict):
    plan_path = os.path.join(utils.task_dir(task_id), "plan.json")
    plan = Plan.model_validate_json(open(plan_path, encoding="utf-8").read())
    st.info("Revisa y edita el guion; después aprueba para producir.")
    edited = []
    for sc in plan.scenes:
        sc = sc.model_copy(update={"narration": st.text_area(f"Escena {sc.id} · {sc.role}", sc.narration, key=f"mx_{task_id}_{sc.id}")})
        edited.append(sc)
    new_plan = plan.model_copy(update={"scenes": edited, "source": "user_edited"})
    with st.expander("Datos verificados / fuentes"):
        st.write(plan.research_note)
        for f in plan.facts:
            st.write(f"- {f.claim}")
    if st.button("Aprobar y producir", type="primary", key=f"mx_ok_{task_id}"):
        p = ExplainerParams(**{**task["explainer_params"], "review_script": False, "plan": new_plan})
        sm.state.update_task(task_id, awaiting_review=False)
        _launch(task_id, p)
        st.rerun()


def render():
    st.subheader("MIXED EXPLAINER · Explora Ciencia 360")
    st.caption("Introduce solo un tema: el sistema investiga, escribe, anima en 2D + 3D, narra, mezcla y revisa el vídeo.")
    topic = st.text_input("Tema del vídeo", placeholder="¿Cómo funciona el freno de motor de un camión?", key="mx_topic")
    c1, c2, c3 = st.columns(3)
    duration = c1.radio("Duración", [45, 60], horizontal=True, format_func=lambda v: f"{v} s", key="mx_duration")
    c2.selectbox("Estilo visual", ["Mixto 2D + 3D"], key="mx_style", disabled=True)
    mode = c3.radio("Generación", ["Automática", "Revisar guion"], horizontal=True, key="mx_mode")
    has_key = bool(voice_service.get_elevenlabs_api_key())
    st.caption(f"Voz: ElevenLabs · {DEFAULT_VOICE_ID} (masculina, español latino) — "
               + ("clave configurada ✅" if has_key else "⚠️ falta la clave de ElevenLabs (config.toml o ELEVENLABS_API_KEY)"))
    if st.button("Generar vídeo", type="primary", key="mx_go", disabled=len(topic.strip()) < 3):
        task_id = utils.get_uuid()
        params = ExplainerParams(topic=topic, duration=duration, voice_name=DEFAULT_VOICE_NAME, review_script=(mode == "Revisar guion"))
        st.session_state["mx_task_id"] = task_id
        _launch(task_id, params)
    _status()
