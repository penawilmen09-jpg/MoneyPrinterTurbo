"""TTS: Edge TTS (voz neuronal gratuita, es-MX-JorgeNeural) con marcas de tiempo por palabra.

Los resultados se guardan en caché, de modo que re-renderizar no vuelve a llamar a la red.
"""
import asyncio
import hashlib
import json
import os
from pathlib import Path

from .core import VOICE, VOICE_RATE


class TTSError(RuntimeError):
    pass


def _proxy():
    return os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy") or None


async def _stream(text, voice, rate, pitch):
    import edge_tts
    comm = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch,
                                boundary="WordBoundary", proxy=_proxy())
    audio, words = bytearray(), []
    async for ev in comm.stream():
        if ev["type"] == "audio":
            audio.extend(ev["data"])
        elif ev["type"] == "WordBoundary":
            st = ev["offset"] / 1e7
            words.append({"text": ev["text"], "start": st, "end": st + ev["duration"] / 1e7})
    return bytes(audio), words


def synthesize(text, cache_dir, voice=VOICE, rate=VOICE_RATE, pitch="+0Hz", retries=3):
    """Devuelve {'path': mp3, 'words': [{text,start,end}]}. Lanza TTSError si falla."""
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha1(f"{voice}|{rate}|{pitch}|{text}".encode()).hexdigest()[:16]
    mp3, meta = cache_dir / f"{key}.mp3", cache_dir / f"{key}.json"
    if mp3.exists() and meta.exists():
        return {"path": str(mp3), "words": json.loads(meta.read_text())}
    last = None
    for attempt in range(retries):
        try:
            audio, words = asyncio.run(_stream(text, voice, rate, pitch))
            if len(audio) < 2000:
                raise TTSError("audio vacío o demasiado corto")
            mp3.write_bytes(audio)
            meta.write_text(json.dumps(words, ensure_ascii=False))
            return {"path": str(mp3), "words": words}
        except Exception as e:           # red, servicio, etc.
            last = e
            if attempt < retries - 1:
                import time
                time.sleep(2 * (attempt + 1))
    raise TTSError(f"Edge TTS falló tras {retries} intentos: {last}")


def fallback_words(text, duration):
    """Si el servicio no devolviera marcas de palabra: reparto proporcional a los caracteres."""
    toks = text.split()
    total = sum(len(t) + 1 for t in toks)
    out, cur = [], 0.0
    for t in toks:
        d = duration * (len(t) + 1) / total
        out.append({"text": t, "start": cur, "end": cur + d})
        cur += d
    return out
