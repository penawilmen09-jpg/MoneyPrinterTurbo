"""Modelo de guion: JSON/dict -> escenas, y parser de texto plano."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
import re
from typing import Any

SETTINGS = (
    "dealership_desk",   # escritorio del concesionario, showroom al fondo
    "manager_office",    # oficina del jefe
    "waiting_area",      # sala de espera + persianas hacia la oficina
    "blinds_peek",       # vista tras las persianas
    "strategy",          # infografía de estrategia psicológica
    "modern_office",     # oficina moderna (lección final)
    "showroom",          # showroom abierto
)
POSES = ("stand", "sit", "walk", "point", "present", "arms_crossed", "wipe", "loosen_tie")
EXPRESSIONS = (
    "neutral", "happy", "nervous", "worried", "surprised", "suspicious",
    "grateful", "impatient", "serious", "smug", "tired", "laugh",
)
TRANSITIONS = ("fade", "slideleft", "slideright", "wipeleft", "circleopen",
               "dissolve", "slideup", "zoomin", "fadeblack", "none")
EVENT_TYPES = ("expression", "pose", "move", "emote", "look", "label", "shake", "sfx", "speaker")
EMOTES = ("sweat", "question", "exclaim", "idea", "anger", "heart", "clock", "dots")


class ScriptError(ValueError):
    pass


@dataclass
class Placement:
    id: str
    x: float = 0.5          # 0..1 sobre el ancho
    y: float = 0.78         # 0..1 sobre el alto (pies / asiento)
    pose: str = "stand"
    expression: str = "neutral"
    scale: float = 1.0
    flip: bool = False
    visible: bool = True


@dataclass
class Scene:
    index: int
    setting: str
    narration: str
    placements: list[Placement] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)
    camera: list[dict[str, Any]] = field(default_factory=list)
    sfx: list[dict[str, Any]] = field(default_factory=list)
    transition: str = "fade"
    min_duration: float = 3.0
    title: str = ""
    items: list[dict[str, Any]] = field(default_factory=list)
    speaker: str = ""        # personaje que mueve la boca con la narración


@dataclass
class ExplainerScript:
    title: str
    language: str = "es"
    voice: str = "es-MX-JorgeNeural"
    rate: str = "+0%"
    pitch: str = "+0Hz"
    music: str = "builtin:upbeat"
    characters: dict[str, dict[str, Any]] = field(default_factory=dict)
    scenes: list[Scene] = field(default_factory=list)


def _num(v: Any, name: str, lo: float, hi: float, default: float) -> float:
    if v is None:
        return default
    try:
        f = float(v)
    except (TypeError, ValueError):
        raise ScriptError(f"{name} debe ser numérico, recibí {v!r}")
    if not lo <= f <= hi:
        raise ScriptError(f"{name} fuera de rango [{lo}, {hi}]: {f}")
    return f


def _choice(v: Any, name: str, allowed: tuple, default: Any) -> Any:
    v = default if v is None else v
    if v not in allowed:
        raise ScriptError(f"{name} inválido: {v!r}. Opciones: {', '.join(allowed)}")
    return v


def _placement(d: dict, known: set, where: str) -> Placement:
    cid = d.get("id")
    if cid not in known:
        raise ScriptError(f"{where}: personaje desconocido {cid!r}")
    return Placement(
        id=cid,
        x=_num(d.get("x"), f"{where}.x", -0.5, 1.5, 0.5),
        y=_num(d.get("y"), f"{where}.y", 0.0, 1.5, 0.78),
        pose=_choice(d.get("pose"), f"{where}.pose", POSES, "stand"),
        expression=_choice(d.get("expression"), f"{where}.expression", EXPRESSIONS, "neutral"),
        scale=_num(d.get("scale"), f"{where}.scale", 0.2, 3.0, 1.0),
        flip=bool(d.get("flip", False)),
        visible=bool(d.get("visible", True)),
    )


def from_dict(data: dict) -> ExplainerScript:
    if not isinstance(data, dict):
        raise ScriptError("El guion debe ser un objeto JSON")
    chars = data.get("characters") or {}
    if not isinstance(chars, dict):
        raise ScriptError("'characters' debe ser un objeto {id: definición}")
    known = set(chars)
    scenes_raw = data.get("scenes")
    if not isinstance(scenes_raw, list) or not scenes_raw:
        raise ScriptError("El guion necesita al menos una escena en 'scenes'")
    script = ExplainerScript(
        title=str(data.get("title", "Video explicativo")),
        language=str(data.get("language", "es")),
        voice=str(data.get("voice", "es-MX-JorgeNeural")),
        rate=str(data.get("rate", "+0%")),
        pitch=str(data.get("pitch", "+0Hz")),
        music=str(data.get("music", "builtin:upbeat")),
        characters={k: dict(v or {}) for k, v in chars.items()},
    )
    for i, sd in enumerate(scenes_raw, 1):
        where = f"scenes[{i}]"
        narration = str(sd.get("narration", "")).strip()
        if not narration:
            raise ScriptError(f"{where}: falta 'narration'")
        events = []
        for j, ev in enumerate(sd.get("events") or [], 1):
            ew = f"{where}.events[{j}]"
            if not ev.get("type"):
                raise ScriptError(f"{ew}: falta 'type'")
            et = _choice(ev["type"], f"{ew}.type", EVENT_TYPES, None)
            ev = dict(ev)
            ev["at"] = _num(ev.get("at"), f"{ew}.at", 0.0, 1.0, 0.0)
            if et not in ("label", "sfx", "shake") and ev.get("who") not in known:
                raise ScriptError(f"{ew}: 'who' desconocido {ev.get('who')!r}")
            if et == "expression":
                _choice(ev.get("value"), f"{ew}.value", EXPRESSIONS, None)
            if et == "pose":
                _choice(ev.get("value"), f"{ew}.value", POSES, None)
            if et == "emote":
                _choice(ev.get("value"), f"{ew}.value", EMOTES, None)
            events.append(ev)
        scene = Scene(
            index=i,
            setting=_choice(sd.get("setting"), f"{where}.setting", SETTINGS, "showroom"),
            narration=narration,
            placements=[_placement(p, known, f"{where}.characters")
                        for p in (sd.get("characters") or [])],
            events=events,
            camera=[dict(k) for k in (sd.get("camera") or [])],
            sfx=[dict(s) for s in (sd.get("sfx") or [])],
            transition=_choice(sd.get("transition"), f"{where}.transition", TRANSITIONS, "fade"),
            min_duration=_num(sd.get("min_duration"), f"{where}.min_duration", 1.0, 60.0, 3.0),
            title=str(sd.get("title", "")),
            items=[dict(x) for x in (sd.get("items") or [])],
            speaker=str(sd.get("speaker") or ""),
        )
        if scene.speaker and scene.speaker not in known:
            raise ScriptError(f"{where}.speaker desconocido: {scene.speaker!r}")
        for k in scene.camera:
            k["at"] = _num(k.get("at"), f"{where}.camera.at", 0.0, 1.0, 0.0)
            k["zoom"] = _num(k.get("zoom"), f"{where}.camera.zoom", 0.5, 3.0, 1.0)
            k["cx"] = _num(k.get("cx"), f"{where}.camera.cx", 0.0, 1.0, 0.5)
            k["cy"] = _num(k.get("cy"), f"{where}.camera.cy", 0.0, 1.0, 0.5)
            k["roll"] = _num(k.get("roll"), f"{where}.camera.roll", -15.0, 15.0, 0.0)
        for s in scene.sfx:
            s["at"] = _num(s.get("at"), f"{where}.sfx.at", 0.0, 1.0, 0.0)
            if not s.get("name"):
                raise ScriptError(f"{where}.sfx: falta 'name'")
        script.scenes.append(scene)
    return script


def load_script(path) -> ExplainerScript:
    p = Path(path)
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ScriptError(f"JSON inválido en {p}: {e}") from e
    return from_dict(data)


_KEYWORDS = [
    ("strategy", r"estrategia|t[eé]cnica|truco|principio|autoridad|psicol[oó]g"),
    ("manager_office", r"jefe|oficina del|gerente|consultar"),
    ("waiting_area", r"espera|reloj|impacient|persianas"),
    ("modern_office", r"lecci[oó]n|negocio|ganancias|lista de precios|consejo"),
    ("dealership_desk", r"cliente|vendedor|concesionario|descuento|coche|auto"),
]
_HEADER = re.compile(r"^\s*\[(.+?)\]\s*$")


def parse_plain_text(text: str, *, title: str = "Video explicativo") -> ExplainerScript:
    """Convierte texto plano en un guion con valores por defecto sensatos.

    Cada párrafo (separado por línea en blanco) es una escena. Una primera línea
    opcional ``[setting=strategy expr=nervous transition=slideleft]`` la ajusta.
    """
    chars = {n: {"preset": n} for n in ("cliente", "vendedor", "jefe", "presentador")}
    scenes = []
    blocks = [b.strip() for b in re.split(r"\n\s*\n", text.strip()) if b.strip()]
    if not blocks:
        raise ScriptError("El texto del guion está vacío")
    for i, block in enumerate(blocks, 1):
        lines = block.splitlines()
        opts: dict = {}
        m = _HEADER.match(lines[0])
        if m:
            for tok in m.group(1).split():
                if "=" in tok:
                    k, v = tok.split("=", 1)
                    opts[k.strip()] = v.strip()
            lines = lines[1:]
        narration = " ".join(l.strip() for l in lines).strip()
        if not narration:
            raise ScriptError(f"Escena {i}: sin narración")
        setting = opts.get("setting")
        if not setting:
            low = narration.lower()
            setting = next((s for s, rx in _KEYWORDS if re.search(rx, low)), "showroom")
        if setting == "modern_office":
            cast = ["presentador"]
        elif setting in ("manager_office", "blinds_peek"):
            cast = ["vendedor", "jefe"]
        elif setting == "strategy":
            cast = ["vendedor"]
        else:
            cast = ["cliente", "vendedor"]
        pl = []
        for n, cid in enumerate(cast):
            xs = [0.5] if len(cast) == 1 else [0.28, 0.72]
            pl.append({"id": cid, "x": xs[n],
                       "pose": "sit" if setting == "dealership_desk" else "stand",
                       "expression": opts.get("expr", "neutral"), "flip": n == 1})
        scenes.append({
            "setting": setting, "narration": narration, "characters": pl,
            "transition": opts.get("transition", "fade"),
            "camera": [{"at": 0, "zoom": 1.0}, {"at": 1, "zoom": 1.12}],
        })
    return from_dict({"title": title, "characters": chars, "scenes": scenes})
