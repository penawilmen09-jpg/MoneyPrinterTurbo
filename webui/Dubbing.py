"""Streamlit UI: dub any Spanish MP4 with one ElevenLabs voice.

Run:  streamlit run webui/Dubbing.py
"""

import os
import sys
import tempfile
import time

root_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, root_dir)

import streamlit as st  # noqa: E402

from app.services import dubbing  # noqa: E402

st.set_page_config(page_title="Doblaje automático", page_icon="🎙️", layout="wide")
st.title("🎙️ Doblaje automático con una sola voz")
st.caption(f"Todas las voces (hombres, mujeres y niños) usan la misma voz masculina · Voice ID {dubbing.DEFAULT_VOICE_ID}")

with st.sidebar:
    st.header("Opciones")
    whisper_model = st.selectbox("Modelo de transcripción", ["small", "medium", "base"], index=0,
                                 help="'medium' es más preciso pero más lento en CPU")
    tts_model = st.selectbox("Modelo ElevenLabs", ["eleven_multilingual_v2", "eleven_flash_v2_5"], index=0)
    want_subs = st.checkbox("Generar subtítulos (SRT)", value=True)
    burn = st.checkbox("Incrustar subtítulos en el video", value=False,
                       help="Re-codifica el video; si no, la imagen se copia sin tocar")

upload = st.file_uploader("Selecciona el video (MP4)", type=["mp4"])
left, right = st.columns(2)

if upload:
    left.subheader("Original")
    left.video(upload.getvalue())

if upload and st.button("Iniciar doblaje", type="primary"):
    workdir = tempfile.mkdtemp(prefix="dub_")
    src = os.path.join(workdir, "input.mp4")
    with open(src, "wb") as fh:
        fh.write(upload.getbuffer())

    bar = st.progress(0.0)
    status = st.empty()
    order = ["audio", "separation", "transcription", "voices", "sync"]
    labels = {"audio": "Audio", "separation": "Separación de música/voz", "transcription": "Transcripción",
              "voices": "Generación de voces", "sync": "Sincronización y montaje"}

    def on_progress(stage: str, frac: float, msg: str) -> None:
        overall = (order.index(stage) + frac) / len(order)
        bar.progress(min(overall, 1.0))
        status.info(f"**{labels[stage]}** — {msg}")

    try:
        res = dubbing.dub_video(src, os.path.join(workdir, "out"), whisper_model=whisper_model, model_id=tts_model,
                                subtitles=want_subs, burn_subtitles=burn and want_subs, progress=on_progress)
    except Exception as exc:  # noqa: BLE001
        st.error(f"Error: {exc}")
        st.stop()

    bar.progress(1.0)
    status.success("Doblaje completado")
    right.subheader("Resultado")
    with open(res.output_video, "rb") as fh:
        data = fh.read()
    right.video(data)
    right.download_button("Descargar video doblado", data, file_name=os.path.basename(res.output_video), mime="video/mp4")
    if want_subs:
        with open(res.srt_path, "rb") as fh:
            right.download_button("Descargar subtítulos (SRT)", fh.read(), file_name=os.path.basename(res.srt_path))
    st.write(f"**Separación de audio:** {res.separation}")
    for w in res.warnings:
        st.warning(w)
    st.dataframe([{"#": s.index, "inicio": round(s.placed_start, 2), "fin": round(s.placed_end, 2),
                   "velocidad": s.speed, "voz": s.voice_id, "texto": s.text} for s in res.segments])
