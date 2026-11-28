"""CLI: python -m app.services.explainer "¿Cómo funciona ...?" [--duration 45] [--review]"""

import argparse
import json
import sys

from .models import DEFAULT_VOICE_NAME, ExplainerParams, Plan
from . import pipeline


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m app.services.explainer")
    ap.add_argument("topic")
    ap.add_argument("--duration", type=int, choices=(45, 60), default=45)
    ap.add_argument("--review", action="store_true", help="stop after the script for approval")
    ap.add_argument("--plan", help="path to an approved/edited plan.json")
    ap.add_argument("--voice", default=DEFAULT_VOICE_NAME)
    ap.add_argument("--task-id", default=None)
    a = ap.parse_args(argv)
    plan = Plan.model_validate_json(open(a.plan, encoding="utf-8").read()) if a.plan else None
    params = ExplainerParams(topic=a.topic, duration=a.duration, review_script=a.review, voice_name=a.voice, plan=plan)
    out = pipeline.run(a.task_id or "explainer-cli", params)
    if out.get("awaiting_review"):
        print(out["plan"].model_dump_json(indent=2))
        return 0
    print(json.dumps({k: v for k, v in out.items() if k not in ("plan", "qc")}, ensure_ascii=False, indent=2))
    for c in out["qc"]["checks"]:
        print(("OK  " if c["ok"] else "FAIL"), c["name"], "-", c["detail"])
    return 0 if out["qc_passed"] else 2


if __name__ == "__main__":
    sys.exit(main())
