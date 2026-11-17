# ¿Cómo sobrevivían los humanos a la Edad de Hielo? — documental animado 2D

Entregables: `autoridad_hielo.mp4` (1080x1920, 30 fps, H.264 High@4.1 yuv420p, AAC 48 kHz estéreo, ~60,6 s, faststart),
`autoridad_hielo.srt`, `narracion.wav` / `narracion.mp3`, `mezcla_final.wav`, `timeline.json`, `qa_report.json`.

Regenerar: `python scripts/produce_ice_age_documentary.py` (código en `app/services/documentary/`; no modifica el resto de MoneyPrinterTurbo).
Dependencias extra: `pip install edge-tts kokoro-onnx soundfile skia-python scipy` (+ `apt install libegl1 libgl1`).

- Animación: ilustración vectorial 2D plana (Skia), rigs 2D articulados, paralaje, nieve, fuego, aurora; sin 3D.
- Voz: Edge-TTS (`es-MX-JorgeNeural`) se comprueba primero; si falla (aquí el host está bloqueado), se usa Kokoro-ONNX (`em_alex`, Apache-2.0, local). Si ninguno funciona el proceso aborta.
- Música/viento/fuego/pasos: sintetizados proceduralmente (sin derechos de autor). Fuente de subtítulos: Be Vietnam Pro Bold (OFL).
