"""CLI: ``python -m app.services.storytelling --topic "..."``  (o ``--sample`` para la historia de prueba)."""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="storytelling", description="ANIMATED STORYTELLING · Explora Ciencia 360")
    ap.add_argument("--topic", help="tema de la historia (el sistema hace el resto)")
    ap.add_argument("--sample", action="store_true", help="usar la historia de prueba del supermercado")
    ap.add_argument("--plan", help="usar un plan.json ya revisado")
    ap.add_argument("--category", default="Historias curiosas")
    ap.add_argument("--seconds", type=int, choices=(45, 60), default=52)
    ap.add_argument("--mode", choices=("auto", "real", "ficticia"), default="auto")
    ap.add_argument("--out", help="carpeta de salida (por defecto storage/tasks/<id>)")
    ap.add_argument("--review", action="store_true", help="solo generar y guardar plan.json para revisarlo")
    ap.add_argument("--dev-voice", action="store_true", help="voz local de PRUEBA (espeak-ng) si no hay ElevenLabs")
    ap.add_argument("--no-music", action="store_true")
    ap.add_argument("--size", default="1080x1920")
    a = ap.parse_args(argv)

    from . import pipeline as P
    from .models import StoryPlan
    from .planner import generate_plan

    if a.plan:
        plan = StoryPlan.from_json(open(a.plan, encoding="utf-8").read())
    elif a.sample:
        from .samples import supermarket_scam_plan

        plan = supermarket_scam_plan()
    elif a.topic:
        plan = generate_plan(a.topic, category=a.category, seconds=a.seconds, mode=a.mode)
    else:
        ap.error("indica --topic, --sample o --plan")
    out = a.out
    if not out:
        from app.utils import utils

        out = utils.task_dir(str(uuid.uuid4()))
    os.makedirs(out, exist_ok=True)
    if a.review:
        path = os.path.join(out, "plan.json")
        open(path, "w", encoding="utf-8").write(plan.to_json())
        print(path)
        return 0
    w, h = (int(v) for v in a.size.split("x"))
    res = P.generate_story_video(plan, out, size=(w, h), music=not a.no_music,
                                 tts_fn=P.espeak_dev_tts if a.dev_voice else None,
                                 progress=lambda f, m: print(f"[{f:4.0%}] {m}", flush=True))
    print(json.dumps({k: res[k] for k in ("video", "duration", "render_seconds")}, ensure_ascii=False))
    print("QC:", "OK" if res["qc"]["passed"] else "FALLOS", f"({res['qc']['warnings']} avisos)")
    return 0 if res["qc"]["passed"] else 2


if __name__ == "__main__":
    sys.exit(main())
