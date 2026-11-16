# Videos explicativos 2D locales (sin APIs de pago)

Sistema alternativo e independiente de creación de videos verticales 9:16 con animación 2D.
Todo se renderiza en tu máquina con **Pillow + numpy + FFmpeg**. No llama a Higgsfield, Seedance
ni a ninguna API de generación de video de pago, y no modifica ninguna función existente de
MoneyPrinterTurbo (es un paquete nuevo: `app/services/animated_explainer/`).

## Uso rápido

```bash
# Guion de ejemplo incluido: "El truco psicológico de los vendedores de coches"
python -m app.services.animated_explainer examples/autoridad_limitada.json salida.mp4

# Borrador rápido (540x960, 15 fps) para revisar el guion
python -m app.services.animated_explainer examples/autoridad_limitada.json borrador.mp4 --draft

# Desde texto plano (un párrafo = una escena)
python -m app.services.animated_explainer mi_guion.txt salida.mp4

python -m app.services.animated_explainer guion.json --check      # valida y lista escenas
python -m app.services.animated_explainer --list-sfx              # efectos disponibles
```

Salida: `salida.mp4` (H.264 + AAC, **1080x1920**, 30 fps, audio normalizado a -16 LUFS) y
`salida.srt` con los subtítulos.

## Qué incluye

| Requisito | Implementación |
|---|---|
| Escenas desde un guion | JSON (`examples/autoridad_limitada.json`) o texto plano; validación con mensajes claros (`script.py`) |
| Personajes consistentes | Rig vectorial con IK de brazos; cada personaje se define **una vez** (preset o colores) y se dibuja igual en todas las escenas (`characters.py`) |
| Expresiones | 12 (`neutral, happy, nervous, worried, surprised, suspicious, grateful, impatient, serious, smug, tired, laugh`), con parpadeo, mirada, rubor, sudor y boca sincronizada con la energía del audio |
| Poses | `stand, sit, walk, point, present, arms_crossed, wipe, loosen_tie` con transiciones suaves |
| Escenarios | 7 decorados por capas (fondo / medio / primer plano) con paralaje: `dealership_desk, manager_office, waiting_area, blinds_peek, strategy, modern_office, showroom` |
| Cámara | Keyframes de zoom/paneo/giro, cámara en mano, sacudidas, viñeta; transiciones FFmpeg `xfade` (`slideleft`, `wipeleft`, `circleopen`, `zoomin`, `slideup`, `fade`…) |
| Narración masculina es-LA | Edge-TTS `es-MX-JorgeNeural` (gratis) → Piper local → espeak-ng → pista muda con tiempos estimados |
| Subtítulos sincronizados | ASS con la palabra activa resaltada (grandes, Be Vietnam Pro Bold, fuera de la zona de UI de TikTok/Reels) + SRT |
| Música y efectos | Música instrumental procedural (`builtin:upbeat\|tense\|calm`, sin derechos) o tu archivo; 14 efectos sintetizados; *ducking* automático bajo la voz; efectos automáticos en emotes/etiquetas/pasos/transiciones |
| Unión y exportación | Cada escena se codifica por trozos en paralelo y FFmpeg une con `xfade`, quema subtítulos y exporta MP4 |

## Formato del guion

```json
{
  "title": "…", "voice": "es-MX-JorgeNeural", "rate": "+4%", "music": "builtin:upbeat",
  "characters": {"vendedor": {"preset": "vendedor", "tie": "#D92B3A"}},
  "scenes": [{
    "setting": "dealership_desk",
    "narration": "Texto que se narra y subtitula.",
    "speaker": "vendedor",
    "characters": [{"id": "vendedor", "x": 0.7, "y": 0.8, "pose": "sit", "expression": "happy", "scale": 1.25}],
    "events": [
      {"type": "expression", "who": "vendedor", "value": "nervous", "at": 0.4},
      {"type": "emote", "who": "vendedor", "value": "sweat", "at": 0.5, "dur": 0.3},
      {"type": "move", "who": "vendedor", "to": [0.4, 0.84], "at": 0.1, "dur": 0.3},
      {"type": "label", "text": "TEXTO EN PANTALLA", "at": 0.6, "dur": 0.3},
      {"type": "sfx", "name": "ding", "at": 0.9}
    ],
    "camera": [{"at": 0, "zoom": 1.0}, {"at": 1, "zoom": 1.25, "cx": 0.3, "cy": 0.5}],
    "transition": "slideleft"
  }]
}
```

* `at` / `dur` son **fracciones de la duración de la escena** (0–1): así los eventos siguen
  sincronizados sea cual sea la duración real de la voz. La duración de cada escena sale de la
  narración (más margen para las transiciones).
* Presets de personaje: `vendedor`, `cliente`, `jefe`, `presentador`. Cualquier campo
  (`skin, hair, hair_style, jacket, shirt, tie, pants, glasses, facial, build…`) se puede sobreescribir.
* Escena de infografía (`"setting": "strategy"`): `title` y `items` de tipo `node`, `link`, `badge`,
  `icon`, `text` que aparecen animados en el instante `at`.

## Voz (TTS gratuito/local)

1. **Edge-TTS** (por defecto, gratis, requiere internet): `es-MX-JorgeNeural` (otras: `es-US-AlonsoNeural`,
   `es-CO-GonzaloNeural`). Da tiempos por palabra reales para los subtítulos.
2. **Piper** (100 % local): instala `piper-tts`, descarga un modelo `es_MX-*.onnx` y
   `export PIPER_MODEL=/ruta/modelo.onnx`.
3. **espeak-ng** (local, voz robótica): `apt install espeak-ng`.
4. Si ninguno está disponible, el video se genera con narración **muda** (los subtítulos y la
   animación siguen funcionando) y se muestra una advertencia. Fuerza uno con `--tts edge|piper|espeak|silent`.

## API HTTP

Con el servidor FastAPI en marcha (misma autenticación `x-api-key` que el resto de la API):

* `POST /api/v1/explainer/videos` con `{"script": {...}}` o `{"text": "..."}` (+ `tts`, `voice`, `music`, `draft`)
* `GET /api/v1/explainer/videos/{job_id}` → estado y progreso
* `GET /api/v1/explainer/videos/{job_id}/download` → MP4

Los videos se guardan en `storage/explainer/`.

## Rendimiento

~1,2 fotogramas/s por núcleo a 1080x1920 (el render se reparte entre todos los núcleos con `--workers`).
Un video de 60 s a 30 fps tarda unos minutos en 4 núcleos; usa `--draft` mientras iteras.

## Pruebas

```bash
python -m pytest test/services/test_animated_explainer.py
```
