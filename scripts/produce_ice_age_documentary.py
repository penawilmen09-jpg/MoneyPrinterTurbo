#!/usr/bin/env python3
"""Genera «autoridad_hielo.mp4» (documental animado 2D, 60 s, 1080x1920).

Uso:  python scripts/produce_ice_age_documentary.py [--out deliverables/autoridad_hielo] [--tts kokoro]
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.documentary import pipeline  # noqa: E402

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "deliverables" / "autoridad_hielo"))
    ap.add_argument("--tts", choices=["edge", "kokoro"], default=None, help="forzar motor (por defecto: Edge-TTS y, si falla, Kokoro)")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--speed", type=float, default=0.9)
    ap.add_argument("--audio-only", action="store_true")
    a = ap.parse_args()
    print(pipeline.run(Path(a.out), prefer_tts=a.tts, workers=a.workers, speed=a.speed, only_audio=a.audio_only))
