# ANIMATED STORYTELLING (Explora Ciencia 360)

Modo independiente que convierte un tema en un vídeo vertical 1080×1920 de 45–60 s con historia animada 2D.

- UI: `streamlit run webui/Main.py` → selector «ANIMATED STORYTELLING».
- CLI: `python -m app.services.storytelling --topic "..." [--seconds 45|60] [--review]`
  (`--sample` usa la historia de prueba; `--dev-voice` usa una voz local robótica **solo para pruebas**).
- Voz: ElevenLabs `851ejYcv2BoNPjrkw93G` (o la voz ElevenLabs ya configurada en la UI). Requiere clave en
  `[elevenlabs] api_key` o `ELEVENLABS_API_KEY`. Nunca se sustituye automáticamente.
- Motor: Pillow + numpy + FFmpeg (local y gratuito). Código en `app/services/storytelling/`
  (`planner` guion/escenas, `rig`+`motion` personajes, `sets` escenarios, `render` cámara/animación,
  `audio` mezcla con ducking, `subtitles`, `qc` control de calidad, `pipeline` orquestación).
- Cada historia guarda `plan.json`, `characters.json` (registro visual), `subtitles.srt`, `qc_report.json`.
- Veracidad: investiga en Wikipedia (gratis); cifras no respaldadas se rechazan; sin fuentes → ficción rotulada.
