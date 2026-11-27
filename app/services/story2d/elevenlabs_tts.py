"""Narración con ElevenLabs Text to Speech (API oficial) + tiempos por palabra.

Es la ÚNICA fuente de voz del generador 2D: no hay voz alternativa. Si falta la
clave o la API falla, se lanza un error claro y no se sintetiza con otro motor.

La clave se lee exclusivamente de la variable de entorno ELEVENLABS_API_KEY.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import time
from pathlib import Path

import requests

# Voz fija para todos los videos del generador 2D (masculina, español latino).
VOICE_ID = "851ejYcv2BoNPjrkw93G"
MODEL_ID = "eleven_multilingual_v2"
SPEED = 1.1                       # voice_settings.speed (0.7–1.2)
OUTPUT_FORMAT = "mp3_44100_128"
BASE_URL = "https://api.elevenlabs.io"
ENV_KEY = "ELEVENLABS_API_KEY"


class ElevenLabsError(RuntimeError):
    pass


class MissingApiKey(ElevenLabsError):
    pass


def api_key() -> str:
    key = os.environ.get(ENV_KEY, "").strip()
    if not key:
        raise MissingApiKey(
            f"Falta la variable de entorno {ENV_KEY}. Configúrala con tu API Key de "
            "ElevenLabs (permiso text_to_speech). No se usará ninguna otra voz."
        )
    return key


def _words_from_alignment(text: str, al: dict) -> list[tuple[str, float, float]]:
    chars = al["characters"]
    st = al["character_start_times_seconds"]
    en = al["character_end_times_seconds"]
    if "".join(chars) != text:
        # ElevenLabs puede normalizar espacios; se alinea por posición no vacía
        text = "".join(chars)
    words, cur, s0, e0 = [], "", None, None
    for ch, a, b in zip(chars, st, en):
        if ch.isspace():
            if cur:
                words.append((cur, s0, e0))
            cur, s0, e0 = "", None, None
        else:
            if s0 is None:
                s0 = a
            cur += ch
            e0 = b
    if cur:
        words.append((cur, s0, e0))
    return words


def synthesize(text: str, out_mp3: Path, previous_text: str = "", next_text: str = "",
               voice_id: str = VOICE_ID, model_id: str = MODEL_ID, speed: float = SPEED):
    """Devuelve [(palabra, inicio, fin)] y deja el audio en out_mp3.

    Usa caché por contenido: re-renderizar no vuelve a gastar créditos.
    """
    if voice_id != VOICE_ID:
        raise ElevenLabsError("Solo se permite la voz configurada para este generador.")
    key = hashlib.sha256(json.dumps([text, previous_text, next_text, voice_id, model_id, speed],
                                    ensure_ascii=False).encode()).hexdigest()[:16]
    meta = out_mp3.with_name(f"{out_mp3.stem}_{key}.json")
    audio = out_mp3.with_name(f"{out_mp3.stem}_{key}.mp3")
    if meta.exists() and audio.exists():
        words = json.loads(meta.read_text())
        out_mp3.write_bytes(audio.read_bytes())
        return [tuple(w) for w in words]

    headers = {"xi-api-key": api_key(), "Content-Type": "application/json"}
    body = {"text": text, "model_id": model_id,
            "voice_settings": {"speed": speed}}
    if previous_text:
        body["previous_text"] = previous_text
    if next_text:
        body["next_text"] = next_text
    url = f"{BASE_URL}/v1/text-to-speech/{voice_id}/with-timestamps"
    last = None
    for attempt in range(3):   # solo ante fallos de red / 5xx (no se cobran)
        try:
            r = requests.post(url, headers=headers, params={"output_format": OUTPUT_FORMAT},
                              json=body, timeout=(10, 90), allow_redirects=False)
        except requests.RequestException as exc:
            last = f"red: {exc.__class__.__name__}"
            time.sleep(1.5 * (attempt + 1))
            continue
        if r.status_code >= 500:
            last = f"HTTP {r.status_code}"
            time.sleep(1.5 * (attempt + 1))
            continue
        if r.status_code in (401, 403):
            try:
                d = r.json().get("detail", {})
                msg = d.get("message", "") if isinstance(d, dict) else str(d)
            except ValueError:
                msg = ""
            raise ElevenLabsError(f"ElevenLabs rechazó la clave ({r.status_code}): {msg[:200]}")
        if not r.ok:
            raise ElevenLabsError(f"ElevenLabs devolvió HTTP {r.status_code}: {r.text[:200]}")
        j = r.json()
        raw = base64.b64decode(j["audio_base64"])
        al = j.get("alignment") or j.get("normalized_alignment")
        if not raw or not al:
            raise ElevenLabsError("Respuesta de ElevenLabs sin audio o sin alineación")
        words = _words_from_alignment(text, al)
        audio.write_bytes(raw)
        meta.write_text(json.dumps(words))
        out_mp3.write_bytes(raw)
        return words
    raise ElevenLabsError(f"ElevenLabs no respondió tras 3 intentos ({last})")
