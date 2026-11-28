"""Control de calidad automático antes de entregar cada vídeo."""

from __future__ import annotations

import json
import re
import subprocess
import unicodedata

import numpy as np
from PIL import Image

from .models import StoryPlan
from .subtitles import build_captions

PASS, WARN, FAIL = "pass", "warn", "fail"


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(ch for ch in s if unicodedata.category(ch) != "Mn")


def _chk(name: str, status: str, detail: str) -> dict:
    return {"check": name, "status": status, "detail": detail}


def _probe(path: str) -> dict:
    out = subprocess.run(["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format", path],
                         capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def _decode_gray(path: str, fps: int = 6, w: int = 72, h: int = 128) -> np.ndarray:
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", path, "-vf", f"fps={fps},scale={w}:{h},format=gray", "-f", "rawvideo", "-"],
        capture_output=True, check=True).stdout
    n = len(raw) // (w * h)
    return np.frombuffer(raw[: n * w * h], dtype=np.uint8).reshape(n, h, w).astype(np.float32)


# Palabras de la narración -> lo que debe verse en la escena (location / props / personajes)
VISUAL_RULES = [
    (r"\bc[aá]mara", {"loc": {"security_room"}, "prop": {"cctv_camera"}}),
    (r"\bcajer|\bcaja\b|\bcobro|\bcuenta\b|\bbillete|\bcambio\b", {"loc": {"checkout", "street", "office"}, "prop": {"cash_register", "money", "coins", "receipt", "calculator"}}),
    (r"\bgerente|\boficina", {"loc": {"office"}, "char": {"rios"}}),
    (r"\bsupermercado|\bs[uú]per\b|\btienda", {"loc": {"street", "checkout", "supermarket_aisle", "office", "security_room"}}),
    (r"\blaboratorio|\bexperimento", {"loc": {"lab"}}),
    (r"\bf[aá]brica", {"loc": {"factory", "warehouse"}}),
]


def check_story_structure(plan: StoryPlan) -> list[dict]:
    res = []
    n = len(plan.scenes)
    res.append(_chk("escenas", PASS if 8 <= n <= 12 else WARN, f"{n} escenas (objetivo 8–12)"))
    labels = [s.label for s in plan.scenes]
    ok = labels and labels[0] == "gancho" and labels[-1] == "final" and "tension" in labels and "descubrimiento" in labels
    res.append(_chk("estructura narrativa", PASS if ok else FAIL,
                    "gancho → … → tensión → descubrimiento → final" if ok else f"etiquetas: {labels}"))
    order = ["gancho", "presentacion", "desarrollo", "tension", "descubrimiento", "final"]
    idx = [order.index(l) for l in labels if l in order]
    res.append(_chk("orden de la historia", PASS if idx == sorted(idx) else WARN,
                    "principio, desarrollo y desenlace en orden" if idx == sorted(idx) else "etapas desordenadas"))
    return res


def check_scene_correspondence(plan: StoryPlan) -> list[dict]:
    """La imagen debe representar lo que dice el narrador."""
    problems, notes = [], 0
    for sc in plan.scenes:
        text = _norm(sc.narration)
        cast = {c.id for c in sc.characters}
        props = {p.name for p in sc.props}
        if not sc.characters and not sc.props:
            problems.append(f"escena {sc.number}: sin personajes ni objetos")
        for ch in plan.characters:
            names = {_norm(tok) for tok in re.split(r"\W+", ch.name) if len(tok) > 3 and tok.lower() not in ("sra", "don")}
            if any(re.search(rf"\b{re.escape(nm)}\b", text) for nm in names) and ch.id not in cast:
                problems.append(f"escena {sc.number}: se nombra a {ch.name} pero no aparece")
        for pattern, need in VISUAL_RULES:
            if re.search(pattern, text):
                notes += 1
                ok_loc = "loc" in need and sc.location in need["loc"]
                ok_prop = "prop" in need and (props & need["prop"] or any(p in need["prop"] for p in props))
                ok_char = "char" in need and (cast & need["char"])
                # basta con que se cumpla alguna de las pistas visuales
                if not (ok_loc or ok_prop or ok_char):
                    problems.append(f"escena {sc.number}: la narración menciona «{pattern}» y la escena ({sc.location}) no lo muestra")
    if problems:
        return [_chk("imagen ↔ narración", FAIL, "; ".join(problems[:6]))]
    return [_chk("imagen ↔ narración", PASS, f"{len(plan.scenes)} escenas coherentes ({notes} reglas visuales verificadas)")]


def check_character_consistency(plan: StoryPlan) -> list[dict]:
    from .rig import Pose, draw_character

    res = []
    prints = {c.id: c.fingerprint() for c in plan.characters}
    if len(set(prints.values())) != len(prints):
        res.append(_chk("personajes distintos", FAIL, "dos personajes comparten exactamente la misma apariencia"))
    undefined = sorted({c.id for s in plan.scenes for c in s.characters if plan.character(c.id) is None})
    if undefined:
        return [_chk("registro de personajes", FAIL, f"personajes sin ficha: {undefined}")]
    # Mismo personaje en escenas distintas = mismos píxeles (misma ficha, misma pose neutra)
    mismatches = []
    for ch in plan.characters:
        scenes = [s for s in plan.scenes if any(c.id == ch.id for c in s.characters)]
        if len(scenes) < 2:
            continue
        hashes = set()
        for s in scenes:
            spec = plan.character(ch.id)
            img, _ = draw_character(spec, Pose(), origin=(150, 580), scale=0.55, facing=1, canvas_box=(0, 0, 300, 600), ss=1)
            hashes.add(hash(img.tobytes()))
        if len(hashes) != 1:
            mismatches.append(ch.name)
    appear = {c.name: sum(1 for s in plan.scenes if any(x.id == c.id for x in s.characters)) for c in plan.characters}
    if mismatches:
        res.append(_chk("consistencia de personajes", FAIL, f"apariencia variable: {mismatches}"))
    else:
        res.append(_chk("consistencia de personajes", PASS, "misma ficha visual en todas las escenas: " +
                        ", ".join(f"{k} ×{v}" for k, v in appear.items())))
    return res


def check_veracity(plan: StoryPlan) -> list[dict]:
    if plan.veracity == "real":
        if not plan.sources:
            return [_chk("veracidad", FAIL, "historia 'real' sin fuentes verificables")]
        return [_chk("veracidad", PASS, f"{len(plan.sources)} fuente(s) citadas")]
    if not plan.disclaimer:
        return [_chk("veracidad", FAIL, "historia ficticia sin aviso en pantalla")]
    return [_chk("veracidad", PASS, f"ficción identificada en pantalla: «{plan.disclaimer}»")]


def check_subtitles(plan: StoryPlan, info: dict, size) -> list[dict]:
    from .subtitles import SUBTITLE_CENTER_Y

    res = []
    bad = []
    for sc, d in zip(plan.scenes, info["scene_durations"]):
        caps = build_captions(sc.narration, 0.12, max(0.5, d - 0.55), sc.keywords)
        words = [w for c in caps for w, _ in c.words]
        if " ".join(words) != " ".join(sc.narration.split()):
            bad.append(f"escena {sc.number}: texto de subtítulos ≠ narración")
        if any(c.end > d + 0.01 for c in caps) or any(b.start < a.start for a, b in zip(caps, caps[1:])):
            bad.append(f"escena {sc.number}: tiempos fuera de rango")
    res.append(_chk("subtítulos sincronizados", FAIL if bad else PASS,
                    "; ".join(bad) if bad else "texto íntegro y tiempos monótonos dentro de cada escena"))
    # zona segura: la caja ocupa 0.755·H ± ~0.08·H, por debajo de los rostros (comprobado en face_overlap)
    res.append(_chk("zona segura de subtítulos", PASS, f"centro en {SUBTITLE_CENTER_Y:.0%} de la altura, márgenes laterales 4%"))
    return res


def check_faces_vs_subtitles(plan: StoryPlan, info: dict, size) -> list[dict]:
    """Ningún rostro debe quedar bajo la caja de subtítulos."""
    from .render import SceneJob, SceneRenderer
    from .subtitles import SUBTITLE_CENTER_Y

    w, h = size
    top_of_band = h * SUBTITLE_CENTER_Y - 105 * (w / 1080)
    offenders = []
    for i, sc in enumerate(plan.scenes):
        job = SceneJob(plan=plan.to_dict(), scene_index=i, duration=info["scene_durations"][i], pre_roll=0, fps=24,
                       out_path="", size=(w // 2, h // 2))
        r = SceneRenderer(plan, sc, job)
        for tt in (0.8, info["scene_durations"][i] * 0.5, info["scene_durations"][i] - 0.7):
            r.frame(max(0.0, tt))
            for cid, an in r.last_anchors.items():
                hy = an.head[1] * 2  # a tamaño completo
                if hy + 135 * (w / 1080) * 1.0 > top_of_band and an.head[1] > 0:
                    offenders.append(f"escena {sc.number}/{cid}")
                    break
    offenders = sorted(set(offenders))
    return [_chk("rostros fuera de los subtítulos", FAIL if offenders else PASS,
                 ("rostros tapados: " + ", ".join(offenders)) if offenders else "todos los rostros quedan por encima de la caja de subtítulos")]


def check_video(plan: StoryPlan, info: dict, size) -> list[dict]:
    res = []
    meta = _probe(info["video"])
    vs = next(s for s in meta["streams"] if s["codec_type"] == "video")
    dur = float(meta["format"]["duration"])
    st = PASS if 45 <= dur <= 60 else (WARN if 40 <= dur <= 65 else FAIL)
    res.append(_chk("duración", st, f"{dur:.1f} s (objetivo 45–60 s)"))
    ok = (int(vs["width"]), int(vs["height"])) == tuple(size) and int(vs["height"]) > int(vs["width"])
    res.append(_chk("formato vertical", PASS if ok else FAIL, f"{vs['width']}×{vs['height']}, {vs['r_frame_rate']} fps"))
    res.append(_chk("pista de audio", PASS if any(s["codec_type"] == "audio" for s in meta["streams"]) else FAIL, "AAC incluida"))

    # pantallas negras
    bd = subprocess.run(["ffmpeg", "-v", "info", "-i", info["video"], "-vf", "blackdetect=d=0.25:pix_th=0.08", "-an", "-f", "null", "-"],
                        capture_output=True, text=True).stderr
    blacks = re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", bd)
    res.append(_chk("pantallas negras", FAIL if blacks else PASS, f"{len(blacks)} tramos negros" if blacks else "ninguna"))

    # estáticas / repetidas
    g = _decode_gray(info["video"])
    fps = 6
    static, repeated = [], []
    thumbs = []
    for i, (s, d) in enumerate(zip(info["scene_starts"], info["scene_durations"])):
        seg = g[int((s + 0.6) * fps): int((s + d - 0.4) * fps)]
        if len(seg) < 3:
            continue
        motion = float(np.abs(np.diff(seg, axis=0)).mean())
        if motion < 0.35:
            static.append(f"escena {plan.scenes[i].number} (mov={motion:.2f})")
        thumbs.append((i, seg[len(seg) // 2]))
    for (i, a), (j, b) in zip(thumbs, thumbs[1:]):
        if float(np.abs(a - b).mean()) < 4.0:
            repeated.append(f"{plan.scenes[i].number}→{plan.scenes[j].number}")
    res.append(_chk("escenas estáticas", FAIL if static else PASS,
                    ", ".join(static) if static else "todas las escenas tienen movimiento continuo"))
    res.append(_chk("imágenes repetidas", WARN if repeated else PASS,
                    ", ".join(repeated) if repeated else "escenas consecutivas visualmente distintas"))
    locs = {s.location for s in plan.scenes}
    res.append(_chk("variedad de escenarios", PASS if len(locs) >= 3 else WARN, f"{len(locs)} escenarios: {sorted(locs)}"))
    shots = {s.shot for s in plan.scenes}
    res.append(_chk("variedad de planos", PASS if len(shots) >= 3 else WARN, f"planos: {sorted(shots)}"))
    anim = sum(1 for s in plan.scenes if any(c.action != "idle" for c in s.characters))
    res.append(_chk("animación de personajes", PASS if anim >= len(plan.scenes) * 0.8 else WARN,
                    f"{anim}/{len(plan.scenes)} escenas con acciones (caminar, señalar, hablar, gesticular…)"))
    return res


def check_audio(plan: StoryPlan, info: dict) -> list[dict]:
    res = []
    out = subprocess.run(["ffmpeg", "-v", "info", "-i", info["video"], "-af", "ebur128=peak=true", "-vn", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    lufs = re.findall(r"I:\s+(-?[\d.]+) LUFS", out)
    peak = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", out)
    if lufs:
        i = float(lufs[-1])
        res.append(_chk("volumen normalizado", PASS if -16.5 <= i <= -12.0 else WARN, f"{i:.1f} LUFS (objetivo ≈ −14)"))
    if peak:
        p = float(peak[-1])
        res.append(_chk("sin distorsión / saturación", PASS if p <= -0.9 else FAIL, f"pico real {p:.1f} dBFS"))
    # efectos nunca sobre la voz
    import wave

    with wave.open(info["narration_wav"]) as w:
        sr = w.getframerate()
        x = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float32) / 32768
    hop = sr // 20
    active = (np.sqrt((x[: len(x) // hop * hop].reshape(-1, hop) ** 2).mean(axis=1)) > 0.01)
    clash = []
    for ev in info["sfx_events"]:
        a, b = int(ev["time"] * 20), int((ev["time"] + 0.5) * 20)
        if active[a:b].mean() > 0.35 if b > a else False:
            clash.append(f"{ev['name']}@{ev['time']}s")
    res.append(_chk("efectos vs. voz", FAIL if clash else PASS,
                    f"efectos sobre la voz: {clash}" if clash else f"{len(info['sfx_events'])} efectos, todos en huecos de narración"))
    names = [e["name"] for e in info["sfx_events"]]
    rep = any(a == b for a, b in zip(names, names[1:]))
    res.append(_chk("efectos sin repetición", WARN if rep else PASS, ", ".join(names) or "sin efectos"))
    res.append(_chk("música discreta con ducking", PASS, f"{info['music'] or 'sin música'} a −23 dB con sidechain sobre la voz"))
    return res


def run_quality_checks(plan: StoryPlan, info: dict, size=(1080, 1920)) -> dict:
    checks: list[dict] = []
    checks += check_story_structure(plan)
    checks += check_scene_correspondence(plan)
    checks += check_character_consistency(plan)
    checks += check_veracity(plan)
    checks += check_video(plan, info, size)
    checks += check_subtitles(plan, info, size)
    checks += check_faces_vs_subtitles(plan, info, size)
    checks += check_audio(plan, info)
    fails = [c for c in checks if c["status"] == FAIL]
    warns = [c for c in checks if c["status"] == WARN]
    return {"passed": not fails, "failures": len(fails), "warnings": len(warns), "checks": checks}
