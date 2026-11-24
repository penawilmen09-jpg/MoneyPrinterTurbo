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
La voz oficial vive en `voice_profile.json` (Edge TTS, es-MX-JorgeNeural, +6%, +0Hz) y el pipeline rechaza otra distinta.
Requiere salida a `speech.platform.bing.com` (Edge TTS). La narración se cachea en `output/<x>/work/tts`.

## Arquitectura
| Módulo | Función |
|---|---|
| `tts.py` | Edge TTS, misma voz fija, caché, reintentos, marcas de palabra |
| `audio_check.py` | Verifica que el audio exista, decodifique, dure y no sea silencio |
| `pipeline.py` | Duración de cada escena = duración real de la voz; mezcla audio+SFX; render paralelo de frames → FFmpeg |
| `subtitles.py` | ASS: palabra activa en menta, claves en amarillo, zona segura (base a ~400 px del borde inferior) |
| `scenes_<pack>.py` | Escenas `f(t, duración) -> SVG` + SFX. Packs incluidos: `pigeon` (video 1), `ship` (video 2), `heli` (video 3), `earth` (video 4: Tierra 3D simulada con numpy), `contrail` (video 5), `moon` (video 6, Explora Ciencia 360), `motion` (video 7) |
| `art/` | Paloma rigged (parpadeo, cabeceo, alas, expresiones), cables/electricidad, diagramas, tanques |
| `sfx.py` | Efectos de sonido sintetizados con numpy |
| `verify.py` | Comprueba MP4: 1080×1920 h264+aac, audio con contenido, sin frames negros/estáticos, subtítulos visibles |
| `planner.py` | **Experimental, sin probar con un LLM**: tema → guion JSON (endpoint compatible OpenAI, p. ej. Ollama) |

## Limitaciones conocidas
- Las ilustraciones de un tema nuevo requieren un `scenes_<pack>.py` nuevo; hoy solo existe el pack de la paloma.
  El `planner` solo puede ordenar escenas ya existentes. Siguiente paso: escenas genéricas parametrizables.
- La investigación factual automática depende de un LLM; no se ha probado aquí.
- La sincronía de subtítulos usa los tiempos por palabra de Edge TTS (no se contrastó con un reconocedor de voz).

## Regla oficial de mezcla de audio (`edu2d/mixer.py`)
La narración manda. La aplica el generador para todos los videos, sin tocar las escenas:
- Voz a nivel fijo; música al 10 % de la voz con ducking del 95 % cuando habla el narrador.
- Efectos especiales al 7 %, ambientales al 6 %, viento al 4 % y con ducking del 95 %; viento/rotor/rumor limitados a ráfagas de ≤ 1,8 s y muy bajos (sin sonido constante).
- Control automático: en CADA palabra (ventana mínima de 250 ms) el fondo debe quedar ≥ 20 dB por debajo de la voz; si no, la exportación se rechaza.
- Revisión final del MP4: sonoridad integrada, pico real (sin recortes) y decodificación completa.
