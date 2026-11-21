# Mike, el pollo sin cabeza – documental animado
- `mike_documental.mp4`: 1080×1920 (9:16), 24 fps, ~97 s, H.264 + AAC.
- Voz: Piper TTS, voz masculina `es_MX-claude-high` (español de México, Apache-2.0), 100 % offline. `narracion_es_mx.mp3` es la pista de voz sola.
- Música, ambiente y efectos: sintetizados desde cero con numpy (`audio.py`), sin derechos de autor.
- Imágenes: ilustración 2D procedural en Python/PIL (no son fotografías). Subtítulos: `subtitulos_es.srt` (también quemados en el video).
- Regenerar: `narracion.py 0.85` → `render.py <i> 4` (i=0..3) → `audio.py` → ensamblar con ffmpeg. Las rutas de trabajo apuntan a /tmp/claude-0/work.
