"""Planificador tema -> guion JSON (EXPERIMENTAL, el paso del LLM NO está probado en este entorno).

Usa cualquier endpoint compatible con la API de chat de OpenAI (p. ej. Ollama local, gratuito):
  EDU2D_LLM_URL=http://localhost:11434/v1/chat/completions  EDU2D_LLM_MODEL=llama3.1
La validación del guion (validate_script) sí está probada por tests.
"""
import importlib
import json
import os
import re

import requests

PROMPT = """Eres guionista de videos educativos verticales de ~60 s en español latino.
Investiga con tu conocimiento y escribe un guion FACTUAL y científicamente correcto sobre: «{topic}».
Estructura: gancho (pregunta intrigante), introducción breve, 4-5 escenas de explicación,
demostración visual, respuesta final y cierre. Total 140-165 palabras.
Responde SOLO un JSON: {{"title":..., "slug":..., "pack":"{pack}", "scenes":[{{"scene":<una de {scenes}>,
"text":<narración de 15-30 palabras>, "highlight":[palabras clave]}}]}}."""


def validate_script(data):
    errs = []
    try:
        pack = importlib.import_module(f"edu2d.scenes_{data['pack']}")
    except Exception:
        return [f"pack desconocido: {data.get('pack')}"]
    if not data.get("scenes"):
        errs.append("sin escenas")
    for i, s in enumerate(data.get("scenes", [])):
        if s.get("scene") not in pack.SCENES:
            errs.append(f"escena {i}: '{s.get('scene')}' no existe en el pack")
        if not s.get("text", "").strip():
            errs.append(f"escena {i}: sin texto")
    words = sum(len(s.get("text", "").split()) for s in data.get("scenes", []))
    if not 100 <= words <= 200:
        errs.append(f"{words} palabras: fuera de 100-200 (≈60 s)")
    return errs


def plan(topic, pack="pigeon"):
    url = os.environ.get("EDU2D_LLM_URL")
    if not url:
        raise RuntimeError("Define EDU2D_LLM_URL (y EDU2D_LLM_MODEL) para usar el planificador.")
    mod = importlib.import_module(f"edu2d.scenes_{pack}")
    body = {"model": os.environ.get("EDU2D_LLM_MODEL", "llama3.1"), "temperature": 0.4,
            "messages": [{"role": "user", "content": PROMPT.format(topic=topic, pack=pack, scenes=sorted(mod.SCENES))}]}
    r = requests.post(url, json=body, timeout=300,
                      headers={"Authorization": f"Bearer {os.environ.get('EDU2D_LLM_KEY', '')}"})
    r.raise_for_status()
    txt = r.json()["choices"][0]["message"]["content"]
    data = json.loads(re.search(r"\{.*\}", txt, re.S).group(0))
    errs = validate_script(data)
    if errs:
        raise ValueError("guion inválido: " + "; ".join(errs))
    return data
