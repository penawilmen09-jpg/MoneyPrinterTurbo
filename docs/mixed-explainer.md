# MIXED EXPLAINER (Explora Ciencia 360)

Nuevo modo de producción integrado en MoneyPrinterTurbo: el usuario escribe **solo un tema** y se genera un vídeo
vertical 1080×1920 de 45–60 s con animación **2D + 3D**, narración ElevenLabs, subtítulos sincronizados y mezcla de audio
normalizada. Los modos existentes no se modifican (la WebUI añade un selector «Clásico / MIXED EXPLAINER»).

## Uso
- **WebUI**: `Modo → MIXED EXPLAINER` → tema, duración (45/60), generación *Automática* o *Revisar guion* → **Generar vídeo**.
- **API**: `POST /api/v1/explainers` `{ "topic": "...", "duration": 45, "review_script": false }` → `task_id`; estado con
  `GET /api/v1/tasks/{id}`. Revisión: `GET /explainers/{id}/plan`, luego `POST /explainers/{id}/produce` (cuerpo opcional con el plan editado).
  `GET /explainers/{id}/qc` devuelve el informe de calidad.
- **CLI**: `python -m app.services.explainer "¿Cómo funciona…?" [--duration 60] [--review] [--plan plan.json]`.

Salida en `storage/tasks/<id>/`: `final-1.mp4`, `subtitles.srt`, `plan.json`, `qc.json`, `scenes/`, `narration/`, `audio/` (stems).

## Pipeline
1. **Investigación + guion** (`script.py`): extractos de Wikipedia en español como fuentes → LLM configurado redacta un plan JSON de escenas
   usando solo hechos respaldados → segunda pasada LLM que audita cada afirmación → validación determinista (palabras, gancho ≤10 palabras,
   cierre con «Explora Ciencia 360», anclas/etapas válidas, máx. 3 efectos). Si no hay sugerencias válidas tras 3 intentos falla con mensaje claro
   (usa *Revisar guion*). Hay un plan verificado incluido para «freno de motor» que funciona sin LLM. *No hay búsqueda web general:* la investigación
   depende de Wikipedia + el LLM; revisa el guion en temas delicados.
2. **Narración** (`narration.py`): ElevenLabs, voz `851ejYcv2BoNPjrkw93G`, una petición por escena al endpoint `/with-timestamps` (tiempos reales por
   carácter → subtítulos exactos). Resultados en caché por texto/voz (no se repite gasto). Si ElevenLabs falla se detiene con error claro; **nunca cambia de voz**.
3. **Animación** (`scenes.py`, `three.py`, `models3d.py`, `gfx.py`): motor 3D por software (numpy + Pillow, sin dependencias nuevas): mallas, cámara
   en órbita, cortes transversales, partículas de gas, manómetros, flechas y callouts animados. Modelos 3D paramétricos: motor de pistón
   (admisión/compresión/combustión/escape y freno de compresión) y turbofán; escenas genéricas con iconos 3D: flujo, ciclo, capas, barras 3D, gancho, CTA.
   Escenas renderizadas en paralelo por trozos con FFmpeg, cacheadas por escena.
4. **Audio** (`audio.py`): música ambiental sintetizada localmente (−14 dB bajo la voz, −20 dB extra al hablar con *ducking* por tiempos de palabra),
   efectos sintetizados solo si se declaran con motivo (máx. ~1 cada 8,5 s, no repetidos, nunca sobre palabras clave, nunca más fuertes que la voz),
   voz con filtro de presencia/compresor, normalización EBU R128 en dos pasos a **−16 LUFS** con techo **−1 dBTP**.
5. **Control de calidad** (`qc.py`): duración, 1080×1920, fotogramas completos, pantallas negras, escenas congeladas, coherencia de luminosidad,
   narración completa, sincronía voz/subtítulos, silencios, ducking en banda de teléfono (≥16 dB), efectos, LUFS/TP. Las escenas que fallan se
   re-renderizan solas (hasta 2 rondas; la última con una escena simplificada) sin repetir narración ni el resto.

## Limitaciones conocidas
- Solo hay dos modelos 3D detallados (motor de pistón, turbofán). Otros temas usan flujo/ciclo/capas/barras con iconos 3D genéricos; para añadir un modelo,
  crea `build_<modelo>` en `models3d.py`, su renderer en `scenes.py` y regístralo en `script.ANCHORS/STAGES`.
- La música y los efectos son sintéticos (discretos a propósito).
- ElevenLabs es el único proveedor admitido en este modo.

## Dependencias
Ninguna nueva: Pillow, numpy, FFmpeg, requests, pydantic y el cliente/LLM ya existentes. Config: reutiliza `[elevenlabs] api_key/model_id` o `ELEVENLABS_API_KEY`.

## Archivos
Nuevos: `app/services/explainer/*`, `app/controllers/v1/explainer.py`, `webui/explainer_mode.py`, `test/services/test_explainer.py`, `test/services/explainer_fakes.py`, `docs/mixed-explainer.md`.
Modificados: `app/router.py` (registro de rutas), `webui/Main.py` (selector de modo), `config.example.toml` (nota).
