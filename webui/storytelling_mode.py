"""Panel del modo ANIMATED STORYTELLING (independiente del flujo clásico)."""

from __future__ import annotations

import os
import threading
import time
import uuid

import streamlit as st

from app.config import config
from app.services.storytelling import pipeline as P
from app.services.storytelling.models import StoryPlan
from app.services.storytelling.planner import generate_plan
from app.utils import utils

_JOBS: dict[str, dict] = {}  # task_id -> estado (compartido entre reruns)

CATEGORIES = ["Estafas y engaños", "Dinero y negocios", "Sucesos reales", "Casos curiosos", "Misterios",
              "Tecnología", "Inventos", "Experimentos", "Historias sorprendentes", "Vida cotidiana"]


def _has_elevenlabs_key() -> bool:
    try:
        from app.services import voice

        return bool(voice.get_elevenlabs_api_key())
    except Exception:
        return False


def _run_job(task_id: str, plan: StoryPlan, dev_voice: bool, music: bool):
    job = _JOBS[task_id]
    try:
        res = P.generate_story_video(
            plan, utils.task_dir(task_id), music=music, tts_fn=P.espeak_dev_tts if dev_voice else None,
            progress=lambda f, m: job.update(progress=f, message=m))
        job.update(done=True, result=res)
    except Exception as e:  # se muestra en la UI
        job.update(done=True, error=str(e))


def render_storytelling_mode():
    st.subheader("🎬 ANIMATED STORYTELLING · Explora Ciencia 360")
    st.caption("Escribe solo el tema: el sistema investiga, escribe la historia, anima los personajes, "
               "narra con la voz configurada, subtitula, mezcla y revisa la calidad.")

    c1, c2 = st.columns([2, 1])
    topic = c1.text_input("Tema de la historia", key="sty_topic",
                          placeholder="El empleado que descubrió una pequeña estafa en un supermercado")
    category = c2.selectbox("Categoría", CATEGORIES, key="sty_category")
    d1, d2, d3, d4 = st.columns(4)
    seconds = d1.radio("Duración", [45, 60], index=0, horizontal=True, key="sty_seconds",
                       format_func=lambda s: f"{s} s")
    d2.selectbox("Estilo visual", ["Cartoon 2D"], key="sty_style")
    use_3d = d3.checkbox("3D complementario (opcional)", value=False, key="sty_3d",
                         help="Acentos 3D sutiles; el estilo principal sigue siendo 2D.")
    mode = d4.selectbox("Veracidad", ["auto", "real", "ficticia"], key="sty_mode",
                        help="auto: investiga y marca como real solo si encuentra fuentes; si no, se identifica como ficción.")
    voice_name = P.default_voice_name()
    st.info(f"🎙️ Narrador configurado: **{voice_name}** (ElevenLabs · masculina · español latino).")
    o1, o2, o3 = st.columns(3)
    auto = o1.checkbox("Modo automático", value=True, key="sty_auto")
    review = o2.checkbox("Revisar guion antes de generar", value=False, key="sty_review")
    music = o3.checkbox("Música ambiental discreta", value=True, key="sty_music")

    dev_voice = False
    if not _has_elevenlabs_key():
        st.warning("No hay clave de ElevenLabs (config.toml [elevenlabs] api_key o ELEVENLABS_API_KEY). "
                   "La voz NO se sustituye automáticamente.")
        dev_voice = st.checkbox("Permitir voz local robótica solo para PRUEBAS", value=False, key="sty_dev_voice")

    if st.button("Preparar historia" if review else "Generar vídeo", type="primary", disabled=not topic.strip(), key="sty_go"):
        with st.spinner("Investigando y escribiendo la historia…"):
            try:
                plan = generate_plan(topic.strip(), category=category, seconds=seconds, mode=mode)
                plan.use_3d_accents = use_3d
                st.session_state["sty_plan"] = plan
                st.session_state["sty_autostart"] = bool(auto and not review)
            except Exception as e:
                st.error(f"No se pudo crear la historia: {e}")

    plan: StoryPlan | None = st.session_state.get("sty_plan")
    if plan is not None and "sty_task" not in st.session_state:
        st.markdown(f"### {plan.title}")
        st.caption(("✅ Historia real con fuentes: " + ", ".join(s["title"] for s in plan.sources))
                   if plan.veracity == "real" else f"🧪 {plan.disclaimer}")
        with st.expander("Personajes (registro visual fijo)", expanded=False):
            for c in plan.characters:
                st.markdown(f"- {c.visual_description()}")
        for sc in plan.scenes:
            sc.narration = st.text_area(f"Escena {sc.number} · {sc.label} · {sc.location}", sc.narration,
                                        key=f"sty_n_{sc.number}", height=70)
        if st.session_state.pop("sty_autostart", False) or st.button("Producir vídeo", type="primary", key="sty_produce"):
            task_id = str(uuid.uuid4())
            _JOBS[task_id] = {"progress": 0.0, "message": "Iniciando…", "done": False}
            threading.Thread(target=_run_job, args=(task_id, plan, dev_voice, music), daemon=True).start()
            st.session_state["sty_task"] = task_id
            st.rerun()

    task_id = st.session_state.get("sty_task")
    if task_id and task_id in _JOBS:
        job = _JOBS[task_id]
        st.progress(min(1.0, job.get("progress", 0.0)), text=job.get("message", ""))
        if not job["done"]:
            time.sleep(2)
            st.rerun()
        elif job.get("error"):
            st.error(job["error"])
            if st.button("Reintentar", key="sty_retry"):
                st.session_state.pop("sty_task")
                st.rerun()
        else:
            res = job["result"]
            st.success(f"Vídeo listo · {res['duration']:.1f} s · carpeta: {utils.task_dir(task_id)}")
            st.video(res["video"])
            with open(res["video"], "rb") as f:
                st.download_button("Descargar MP4", f, file_name="explora_ciencia_360.mp4", mime="video/mp4")
            qc = res.get("qc", {})
            st.markdown(f"#### Control de calidad: {'✅ aprobado' if qc.get('passed') else '❌ con fallos'} "
                        f"({qc.get('warnings', 0)} avisos)")
            icon = {"pass": "✅", "warn": "⚠️", "fail": "❌"}
            for c in qc.get("checks", []):
                st.write(f"{icon[c['status']]} **{c['check']}** — {c['detail']}")
            if st.button("Nueva historia", key="sty_new"):
                for k in ("sty_task", "sty_plan"):
                    st.session_state.pop(k, None)
                st.rerun()
