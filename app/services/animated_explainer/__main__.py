"""CLI: ``python -m app.services.animated_explainer guion.json salida.mp4``."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
import sys


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="animated_explainer",
        description="Videos explicativos 2D verticales 9:16 100% locales (sin APIs de pago).")
    ap.add_argument("script", nargs="?", help="guion .json (o .txt de texto plano)")
    ap.add_argument("output", nargs="?", default="explainer.mp4", help="MP4 de salida")
    ap.add_argument("--tts", default="auto", choices=["auto", "edge", "piper", "espeak", "silent"])
    ap.add_argument("--voice", help="voz Edge-TTS (por defecto es-MX-JorgeNeural)")
    ap.add_argument("--music", help="builtin:upbeat|tense|calm, ruta a un audio o 'none'")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--workers", type=int)
    ap.add_argument("--draft", action="store_true", help="borrador rápido 540x960 a 15 fps")
    ap.add_argument("--no-subtitles", action="store_true")
    ap.add_argument("--work-dir", help="conserva los archivos intermedios aquí")
    ap.add_argument("--check", action="store_true", help="solo valida el guion y lista escenas")
    ap.add_argument("--list-sfx", action="store_true")
    ap.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO if a.verbose else logging.WARNING,
                        format="%(levelname)s %(message)s")

    from . import audio
    if a.list_sfx:
        print("\n".join(sorted(audio.SFX)))
        return 0
    if not a.script:
        ap.error("falta el guion")
    from .script import ScriptError, load_script, parse_plain_text
    try:
        p = Path(a.script)
        script = parse_plain_text(p.read_text(encoding="utf-8"), title=p.stem) \
            if p.suffix.lower() == ".txt" else load_script(p)
    except (ScriptError, OSError) as e:
        print(f"Error en el guion: {e}", file=sys.stderr)
        return 2
    if a.check:
        for s in script.scenes:
            print(f"Escena {s.index}: {s.setting:16s} {len(s.narration.split()):3d} palabras  -> {s.transition}")
        return 0
    from .pipeline import render_video
    res = render_video(
        script, a.output, tts=a.tts, voice=a.voice, music=a.music, fps=a.fps, workers=a.workers,
        draft=a.draft, subtitles_on=not a.no_subtitles, work_dir=a.work_dir, keep_work=bool(a.work_dir),
        progress=lambda st, f: print(f"[{st}] {f:.0%}", file=sys.stderr))
    print(f"OK  {res.path}  ({res.duration:.1f}s, TTS: {', '.join(sorted(set(res.tts_providers)))})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
