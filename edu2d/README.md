# edu2d — generador de videos educativos 2D (9:16)

Guion JSON → voz masculina es-MX (Edge TTS `es-MX-JorgeNeural`, gratis, con marcas de tiempo por palabra)
→ escenas SVG animadas por código (cairosvg) → subtítulos ASS palabra a palabra → MP4 1080×1920 (FFmpeg).
Todo el arte es vectorial y original, generado por código; no usa imágenes ni videos de terceros.

## Uso
```bash
pip install -r requirements.txt        # + ffmpeg y fuente DejaVu (apt install ffmpeg fonts-dejavu-core)
python -m edu2d check-env              # revisa dependencias
python -m edu2d make projects/palomas/script.json --out output/palomas   # genera + verifica (~2 min, 4 CPU)
python -m edu2d verify output/palomas/palomas_cables.mp4
python -m edu2d stills projects/palomas/script.json   # contact sheet de escenas, sin red ni audio
python -m pytest tests
```
Requiere salida a `speech.platform.bing.com` (Edge TTS). La narración se cachea en `output/<x>/work/tts`.

## Arquitectura
| Módulo | Función |
|---|---|
| `tts.py` | Edge TTS, misma voz fija, caché, reintentos, marcas de palabra |
| `audio_check.py` | Verifica que el audio exista, decodifique, dure y no sea silencio |
| `pipeline.py` | Duración de cada escena = duración real de la voz; mezcla audio+SFX; render paralelo de frames → FFmpeg |
| `subtitles.py` | ASS: palabra activa en menta, claves en amarillo, zona segura (base a ~400 px del borde inferior) |
| `scenes_<pack>.py` | Escenas `f(t, duración) -> SVG` + SFX. Pack incluido: `pigeon` |
| `art/` | Paloma rigged (parpadeo, cabeceo, alas, expresiones), cables/electricidad, diagramas, tanques |
| `sfx.py` | Efectos de sonido sintetizados con numpy |
| `verify.py` | Comprueba MP4: 1080×1920 h264+aac, audio con contenido, sin frames negros/estáticos, subtítulos visibles |
| `planner.py` | **Experimental, sin probar con un LLM**: tema → guion JSON (endpoint compatible OpenAI, p. ej. Ollama) |

## Limitaciones conocidas
- Las ilustraciones de un tema nuevo requieren un `scenes_<pack>.py` nuevo; hoy solo existe el pack de la paloma.
  El `planner` solo puede ordenar escenas ya existentes. Siguiente paso: escenas genéricas parametrizables.
- La investigación factual automática depende de un LLM; no se ha probado aquí.
- La sincronía de subtítulos usa los tiempos por palabra de Edge TTS (no se contrastó con un reconocedor de voz).
