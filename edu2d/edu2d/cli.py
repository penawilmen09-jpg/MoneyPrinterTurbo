"""CLI: python -m edu2d {check-env|make|verify|stills}"""
import argparse
import json
import shutil
import sys
from pathlib import Path


def cmd_check_env(_):
    import importlib
    ok = True
    for tool in ("ffmpeg", "ffprobe"):
        p = shutil.which(tool); ok &= bool(p); print(f"{tool:8s}", p or "FALTA")
    for mod in ("edge_tts", "cairosvg", "numpy", "PIL"):
        try:
            importlib.import_module(mod); print(f"{mod:9s}OK")
        except Exception:
            ok = False; print(f"{mod:9s}FALTA  (pip install -r requirements.txt)")
    fonts = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
    print("fuente DejaVu Sans Bold:", "OK" if fonts.exists() else "FALTA (apt install fonts-dejavu-core)")
    return 0 if ok and fonts.exists() else 1


def cmd_make(a):
    from .pipeline import make
    from .verify import verify_mp4
    out = a.out or f"output/{Path(a.script).parent.name}"
    mp4, tl, total = make(a.script, out, a.workers)
    print("Verificando MP4…")
    problems = verify_mp4(mp4, tl)
    from .verify import check_loudness
    lufs, peak = check_loudness(mp4)
    print(f"  audio final: {lufs} LUFS integrados, pico real {peak} dBFS (sin recortes)")
    if problems:
        print("PROBLEMAS:"); [print(" -", x) for x in problems]; return 2
    print(f"OK -> {mp4}")
    return 0


def cmd_verify(a):
    from .verify import verify_mp4
    tlp = Path(a.mp4).parent / "work" / "timeline.json"
    problems = verify_mp4(a.mp4, json.loads(tlp.read_text()) if tlp.exists() else None)
    [print(" -", x) for x in problems]
    print("OK" if not problems else "CON PROBLEMAS")
    return 1 if problems else 0


def cmd_stills(a):
    """Contact sheet de las escenas (sin audio ni red) para revisar el diseño."""
    import importlib
    import cairosvg
    from PIL import Image
    from .svgkit import frame_svg
    data = json.loads(Path(a.script).read_text(encoding="utf-8"))
    pack = importlib.import_module(f"edu2d.scenes_{data['pack']}")
    ims = []
    for sc in data["scenes"]:
        cairosvg.svg2png(bytestring=frame_svg(pack.SCENES[sc["scene"]](a.d * .6, a.d)).encode(), write_to="/tmp/_s.png", output_width=270)
        ims.append(Image.open("/tmp/_s.png").copy())
    w, h = ims[0].size
    sheet = Image.new("RGB", (w * len(ims), h))
    for i, im in enumerate(ims): sheet.paste(im, (i * w, 0))
    sheet.save(a.out); print(a.out)
    return 0


def cmd_plan(a):
    from .planner import plan
    data = plan(a.topic, a.pack)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(a.out); return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="edu2d")
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("check-env").set_defaults(fn=cmd_check_env)
    m = sp.add_parser("make"); m.add_argument("script"); m.add_argument("--out"); m.add_argument("--workers", type=int)
    m.set_defaults(fn=cmd_make)
    v = sp.add_parser("verify"); v.add_argument("mp4"); v.set_defaults(fn=cmd_verify)
    s = sp.add_parser("stills"); s.add_argument("script"); s.add_argument("--out", default="stills.png"); s.add_argument("--d", type=float, default=8.0)
    s.set_defaults(fn=cmd_stills)
    pl = sp.add_parser("plan", help="(experimental) tema -> script.json con un LLM"); pl.add_argument("topic")
    pl.add_argument("--pack", default="pigeon"); pl.add_argument("--out", default="projects/nuevo/script.json"); pl.set_defaults(fn=cmd_plan)
    a = ap.parse_args(argv)
    sys.exit(a.fn(a))
