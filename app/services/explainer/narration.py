"""Narration with the user-approved ElevenLabs voice (no silent voice fallback).

One request per scene keeps scene-level retries cheap, and the
``/with-timestamps`` endpoint returns character-level alignment, so captions are
synchronised with the *real* audio instead of being estimated.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import subprocess
import time
from dataclasses import dataclass
from typing import Callable, Protocol

import requests
from loguru import logger

from app.config import config
from app.services import voice as voice_service
from app.utils import utils

from .models import DEFAULT_VOICE_ID, Scene, Word

# Applied to the *spoken* text only (1 word -> 1 word, so caption alignment survives).
PRONUNCIATIONS = {
    "Jacobs": "Yéicobs",
    "Jake": "Yeik",
}


class NarrationError(RuntimeError):
    """Clear, user-facing narration failure. The configured voice is never changed."""


@dataclass
class NarrationResult:
    audio_path: str
    duration: float
    words: list[Word]
    cached: bool = False


class Narrator(Protocol):
    def __call__(self, scene: Scene, previous_text: str, next_text: str, out_dir: str) -> NarrationResult: ...


def parse_voice(voice_name: str) -> tuple[str, str]:
    """``elevenlabs:{voice_id}:{name}`` -> (voice_id, display name)."""
    if not voice_name or not voice_name.startswith("elevenlabs:"):
        raise NarrationError(
            "MIXED EXPLAINER usa ElevenLabs como proveedor de voz. Configura una voz con el formato "
            f"'elevenlabs:<voice_id>:<nombre>' (por defecto elevenlabs:{DEFAULT_VOICE_ID}). "
            "No se cambia de voz automáticamente."
        )
    parts = voice_name.split(":", 2)
    voice_id = parts[1].strip()
    if not re.fullmatch(r"[A-Za-z0-9]{10,40}", voice_id):
        raise NarrationError(f"voice_id de ElevenLabs inválido: {voice_id!r}")
    return voice_id, (parts[2] if len(parts) > 2 else "")


def spoken_text(text: str) -> str:
    out = []
    for w in text.split():
        core = re.sub(r"^\W+|\W+$", "", w)
        if core in PRONUNCIATIONS:
            w = w.replace(core, PRONUNCIATIONS[core])
        out.append(w)
    return " ".join(out)


def audio_duration(path: str) -> float:
    try:
        return float(voice_service.get_audio_duration(path))
    except Exception:  # noqa: BLE001 - duration probing must never crash the pipeline
        return 0.0


def words_from_alignment(original_words: list[str], alignment: dict) -> list[Word]:
    """Group ElevenLabs character timings into the *original* (caption) words."""
    chars = alignment.get("characters") or []
    starts = alignment.get("character_start_times_seconds") or []
    ends = alignment.get("character_end_times_seconds") or []
    spoken: list[tuple[str, float, float]] = []
    cur, cs, ce = "", None, None
    for ch, a, b in zip(chars, starts, ends):
        if ch.isspace():
            if cur:
                spoken.append((cur, cs, ce))
                cur, cs, ce = "", None, None
            continue
        if cs is None:
            cs = a
        cur += ch
        ce = b
    if cur:
        spoken.append((cur, cs, ce))
    if len(spoken) != len(original_words):
        raise NarrationError(
            f"La alineación de ElevenLabs devolvió {len(spoken)} palabras y el guion tiene {len(original_words)}."
        )
    return [Word(text=o, start=float(s), end=float(e)) for o, (_, s, e) in zip(original_words, spoken)]


class ElevenLabsNarrator:
    def __init__(self, voice_name: str, model_id: str | None = None, timeout: int = 90):
        self.voice_id, self.voice_label = parse_voice(voice_name)
        self.model_id = model_id or config.elevenlabs.get("model_id", "eleven_multilingual_v2")
        self.timeout = timeout
        self.settings = {"stability": 0.55, "similarity_boost": 0.8, "style": 0.1, "use_speaker_boost": True}
        self.seed = 360
        self.calls = 0

    def _api_key(self) -> str:
        key = voice_service.get_elevenlabs_api_key()
        if not key:
            raise NarrationError(
                "Falta la clave de ElevenLabs (config.toml [elevenlabs].api_key o variable ELEVENLABS_API_KEY). "
                "No se cambió la voz ni se usó otro proveedor."
            )
        return key

    def _cache_key(self, scene: Scene, previous_text: str, next_text: str) -> str:
        blob = json.dumps([scene.narration, spoken_text(scene.narration), self.voice_id, self.model_id,
                           self.settings, self.seed, previous_text, next_text], sort_keys=True)
        return hashlib.sha1(blob.encode()).hexdigest()[:16]

    def __call__(self, scene: Scene, previous_text: str, next_text: str, out_dir: str) -> NarrationResult:
        os.makedirs(out_dir, exist_ok=True)
        key = self._cache_key(scene, previous_text, next_text)
        mp3 = os.path.join(out_dir, f"{scene.id}_{key}.mp3")
        meta = os.path.join(out_dir, f"{scene.id}_{key}.json")
        original = scene.narration.split()
        if os.path.exists(mp3) and os.path.exists(meta):
            data = json.load(open(meta, encoding="utf-8"))
            return NarrationResult(mp3, data["duration"], [Word(**w) for w in data["words"]], cached=True)

        api_key = self._api_key()
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}/with-timestamps"
        payload = {
            "text": spoken_text(scene.narration), "model_id": self.model_id,
            "voice_settings": self.settings, "seed": self.seed,
        }
        if previous_text:
            payload["previous_text"] = spoken_text(previous_text)[-400:]
        if next_text:
            payload["next_text"] = spoken_text(next_text)[:400]
        headers = {"xi-api-key": api_key, "Content-Type": "application/json"}
        last_err = ""
        dropped_context = False
        for attempt in range(3):
            try:
                self.calls += 1
                r = requests.post(url, params={"output_format": "mp3_44100_128"}, headers=headers, json=payload,
                                  timeout=self.timeout)
            except requests.RequestException as exc:
                last_err = f"error de red ({type(exc).__name__})"
                logger.warning(f"elevenlabs narration network error, retry {attempt + 1}: {exc}")
                time.sleep(1.5 * (attempt + 1))
                continue
            if r.status_code == 200:
                break
            body = r.text[:300]
            if r.status_code in (401, 403):
                raise NarrationError(f"ElevenLabs rechazó la solicitud (HTTP {r.status_code}): clave inválida o sin acceso a la voz "
                                     f"{self.voice_id}. No se cambió la voz. Detalle: {body}")
            if r.status_code == 422 and not dropped_context and ("previous_text" in payload or "next_text" in payload):
                # Context hints are optional; the same voice is kept.
                payload.pop("previous_text", None)
                payload.pop("next_text", None)
                dropped_context = True
                continue
            if r.status_code in (422, 400, 404):
                raise NarrationError(f"ElevenLabs devolvió HTTP {r.status_code}. No se cambió la voz. Detalle: {body}")
            last_err = f"HTTP {r.status_code}: {body}"
            if r.status_code == 429 or r.status_code >= 500:
                time.sleep(2.0 * (attempt + 1))
                continue
            raise NarrationError(f"ElevenLabs falló ({last_err}). No se cambió la voz.")
        else:
            raise NarrationError(f"ElevenLabs no respondió correctamente tras 3 intentos ({last_err}). "
                                 "La voz configurada se conserva; reintenta más tarde.")
        data = r.json()
        audio = base64.b64decode(data["audio_base64"])
        if not audio:
            raise NarrationError("ElevenLabs devolvió audio vacío.")
        tmp = mp3 + ".part"
        with open(tmp, "wb") as fh:
            fh.write(audio)
        os.replace(tmp, mp3)
        dur = audio_duration(mp3)
        if dur <= 0:
            raise NarrationError("El audio de ElevenLabs no es válido (duración 0).")
        words = words_from_alignment(original, data.get("alignment") or data.get("normalized_alignment") or {})
        with open(meta, "w", encoding="utf-8") as fh:
            json.dump({"duration": dur, "words": [w.model_dump() for w in words]}, fh, ensure_ascii=False)
        return NarrationResult(mp3, dur, words)
