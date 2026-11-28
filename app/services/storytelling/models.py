"""Modelos de datos del modo ANIMATED STORYTELLING.

Todo el modo se describe con un :class:`StoryPlan` serializable a JSON:
registro de personajes + lista de escenas.  El plan es la única fuente de
verdad: el renderizador, el audio, los subtítulos y el control de calidad
leen el mismo objeto, de modo que lo que se dice, lo que se ve y lo que se
comprueba no puede desincronizarse.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field, fields
from typing import Any

# --------------------------------------------------------------------------
# Vocabularios cerrados (el LLM sólo puede elegir de aquí)
# --------------------------------------------------------------------------
ACTIONS = (
    "idle", "talk", "walk_in", "walk_out", "walk", "point", "look_around",
    "shrug", "panic", "think", "wave", "type", "hold_item", "scan_item",
    "lean_in", "nod", "celebrate", "cross_arms", "hands_up",
)
EXPRESSIONS = (
    "neutral", "happy", "surprised", "worried", "angry",
    "suspicious", "thinking", "sad", "smug",
)
POSITIONS = ("far_left", "left", "center_left", "center", "center_right", "right", "far_right")
SHOTS = ("wide", "medium", "close_up", "extreme_close")
CAMERA_MOVES = ("static", "push_in", "pull_out", "pan_left", "pan_right", "shake")
TRANSITIONS = ("cut", "fade", "slide_left", "slide_right", "circle", "wipe", "zoom", "dissolve")
LOCATIONS = (
    "street", "supermarket_aisle", "checkout", "security_room", "office",
    "house", "factory", "lab", "warehouse",
)
STRUCTURE_LABELS = ("gancho", "presentacion", "desarrollo", "tension", "descubrimiento", "final")
SFX_NAMES = ("whoosh", "ding", "beep", "alert", "pop", "cash", "suspense", "typing", "click")
PROP_NAMES = (
    "cash_register", "receipt", "money", "coins", "magnifier", "clipboard",
    "tablet", "phone", "cctv_camera", "box", "cart", "basket", "calculator",
    "laptop", "scanner", "can", "monitor_wall", "alarm", "question_mark",
    "exclamation", "check_mark", "price_tag", "lightbulb", "document",
)
POPUP_TYPES = ("popup", "counter", "highlight", "arrow", "speech")

SKIN_TONES = {
    "light": (255, 224, 196), "fair": (247, 208, 172), "tan": (224, 172, 125),
    "brown": (176, 120, 80), "dark": (120, 78, 52),
}
HAIR_STYLES = ("short", "parted", "bald", "bun", "long", "curly", "cap", "ponytail")
OUTFITS = ("shirt", "tshirt", "apron", "uniform", "suit", "labcoat", "hoodie", "dress")
BUILDS = ("slim", "average", "stocky")
ACCESSORIES = ("glasses", "tie", "badge", "mustache", "beard", "headset", "earrings", "scarf")


def _named_color(value: Any, default: tuple[int, int, int]) -> tuple[int, int, int]:
    """Acepta (r,g,b) o '#rrggbb'."""
    if isinstance(value, (list, tuple)) and len(value) >= 3:
        return tuple(max(0, min(255, int(c))) for c in value[:3])  # type: ignore[return-value]
    if isinstance(value, str):
        v = value.strip().lstrip("#")
        if len(v) == 6:
            try:
                return (int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16))
            except ValueError:
                pass
    return default


@dataclass
class CharacterSpec:
    """Ficha visual inmutable de un personaje.

    Se define UNA vez por historia y se reutiliza en todas las escenas:
    el renderizador sólo recibe esta ficha, nunca valores sueltos, por lo que
    el rostro, peinado, ropa y colores no pueden cambiar entre escenas.
    """

    id: str
    name: str
    role: str = ""
    gender: str = "m"  # m | f
    age: str = "adult"  # young | adult | senior
    skin: Any = "fair"
    hair_style: str = "short"
    hair_color: Any = (60, 40, 30)
    eye_color: Any = (60, 40, 30)
    outfit: str = "shirt"
    top_color: Any = (70, 130, 200)
    accent_color: Any = (230, 200, 60)  # corbata, delantal, insignia
    bottom_color: Any = (50, 60, 90)
    shoes_color: Any = (40, 35, 35)
    build: str = "average"
    height: float = 1.0
    accessories: list[str] = field(default_factory=list)

    def normalized(self) -> "CharacterSpec":
        """Devuelve una copia con valores válidos (colores como tuplas, etc.)."""
        s = CharacterSpec(**{f.name: getattr(self, f.name) for f in fields(self)})
        skin = SKIN_TONES.get(str(s.skin), None) if isinstance(s.skin, str) and s.skin in SKIN_TONES else None
        s.skin = skin or _named_color(s.skin, SKIN_TONES["fair"])
        s.hair_color = _named_color(s.hair_color, (60, 40, 30))
        s.eye_color = _named_color(s.eye_color, (60, 40, 30))
        s.top_color = _named_color(s.top_color, (70, 130, 200))
        s.accent_color = _named_color(s.accent_color, (230, 200, 60))
        s.bottom_color = _named_color(s.bottom_color, (50, 60, 90))
        s.shoes_color = _named_color(s.shoes_color, (40, 35, 35))
        if s.hair_style not in HAIR_STYLES:
            s.hair_style = "short"
        if s.outfit not in OUTFITS:
            s.outfit = "shirt"
        if s.build not in BUILDS:
            s.build = "average"
        s.gender = "f" if str(s.gender).lower().startswith("f") else "m"
        s.height = max(0.85, min(1.12, float(s.height or 1.0)))
        s.accessories = [a for a in (s.accessories or []) if a in ACCESSORIES]
        return s

    def visual_description(self) -> str:
        """Descripción textual estable, reutilizable como prompt de imagen."""
        s = self.normalized()
        hair = f"cabello {s.hair_style} {_color_name(s.hair_color)}" if s.hair_style != "bald" else "calvo"
        acc = (", " + ", ".join(s.accessories)) if s.accessories else ""
        return (
            f"{s.name} ({s.role}): {'mujer' if s.gender == 'f' else 'hombre'} {s.age}, "
            f"piel {_color_name(s.skin)}, {hair}, ojos {_color_name(s.eye_color)}, "
            f"complexión {s.build}, viste {s.outfit} {_color_name(s.top_color)} con "
            f"detalles {_color_name(s.accent_color)} y pantalón {_color_name(s.bottom_color)}{acc}. "
            "Estilo cartoon 2D, cabeza grande, ojos expresivos, contorno oscuro."
        )

    def fingerprint(self) -> str:
        """Huella estable de la apariencia (para verificar consistencia)."""
        s = self.normalized()
        payload = json.dumps(
            {k: v for k, v in asdict(s).items() if k not in ("name", "role")},
            sort_keys=True, default=list,
        )
        return hashlib.sha1(payload.encode()).hexdigest()[:12]


def _color_name(rgb: tuple[int, int, int]) -> str:
    r, g, b = rgb
    palette = {
        "negro": (25, 25, 30), "gris oscuro": (80, 80, 90), "gris": (150, 150, 155),
        "blanco": (240, 240, 240), "rojo": (200, 50, 50), "naranja": (235, 140, 45),
        "amarillo": (240, 205, 60), "verde": (70, 160, 85), "turquesa": (60, 170, 170),
        "azul": (60, 110, 200), "azul marino": (30, 45, 100), "morado": (130, 80, 170),
        "rosa": (230, 120, 170), "café": (110, 70, 45), "castaño": (80, 55, 40),
        "rubio": (225, 190, 110), "pelirrojo": (180, 80, 40), "beige": (235, 205, 170),
        "canela": (200, 150, 110), "moreno": (150, 100, 70),
    }
    return min(palette, key=lambda k: sum((a - b2) ** 2 for a, b2 in zip(palette[k], (r, g, b))))


@dataclass
class CharacterCue:
    """Qué hace un personaje en una escena concreta."""

    id: str
    position: str = "center"
    action: str = "idle"
    expression: str = "neutral"
    enters_from: str = ""  # "", "left", "right" -> camina hacia su posición
    look_at: str = ""  # id de otro personaje, "camera", "prop:<nombre>" o ""
    speaking: bool = False  # el personaje habla (boca sincronizada con el audio)
    holding: str = ""  # nombre de prop sostenido en la mano
    depth: str = ""  # "behind" = detrás del mostrador/escritorio del primer plano


@dataclass
class PropCue:
    name: str
    anchor: str = "floor"  # floor | counter | wall | screen | hand:<id>
    position: str = "center"
    scale: float = 1.0
    animation: str = ""  # "", "bounce", "blink", "slide_in", "shake", "grow"


@dataclass
class PopupCue:
    type: str = "popup"  # popup | counter | highlight | arrow
    text: str = ""
    at: float = 0.0  # segundos desde el inicio de la escena
    duration: float = 1.6
    target: str = ""  # "char:<id>" | "prop:<name>" | ""
    style: str = "alert"  # alert | info | money | good


@dataclass
class Scene:
    number: int
    narration: str
    duration: float = 0.0  # se recalcula con la duración real del audio
    label: str = "desarrollo"
    location: str = "street"
    time_of_day: str = "day"  # day | night | evening
    characters: list[CharacterCue] = field(default_factory=list)
    props: list[PropCue] = field(default_factory=list)
    popups: list[PopupCue] = field(default_factory=list)
    shot: str = "medium"
    camera_move: str = "push_in"
    focus: str = ""  # "char:<id>" | "prop:<name>" | ""
    transition_in: str = "fade"
    sfx: str = ""
    keywords: list[str] = field(default_factory=list)
    background_extras: int = 0  # figurantes caminando al fondo
    action_summary: str = ""  # descripción textual de lo que se ve (para QC / prompts)


@dataclass
class StoryPlan:
    title: str
    topic: str
    category: str = "Historias curiosas"
    veracity: str = "ficticia"  # real | ficticia
    disclaimer: str = ""
    sources: list[dict] = field(default_factory=list)
    target_duration: float = 52.0
    language: str = "es-419"
    characters: list[CharacterSpec] = field(default_factory=list)
    scenes: list[Scene] = field(default_factory=list)
    use_3d_accents: bool = False

    # ----- acceso ----------------------------------------------------------
    def character(self, char_id: str) -> CharacterSpec | None:
        for c in self.characters:
            if c.id == char_id:
                return c
        return None

    @property
    def narration(self) -> str:
        return " ".join(s.narration.strip() for s in self.scenes)

    @property
    def total_duration(self) -> float:
        return sum(s.duration for s in self.scenes)

    # ----- (de)serialización ------------------------------------------------
    def to_dict(self) -> dict:
        d = asdict(self)
        for c in d["characters"]:
            for k in ("skin", "hair_color", "eye_color", "top_color",
                      "accent_color", "bottom_color", "shoes_color"):
                if isinstance(c[k], tuple):
                    c[k] = list(c[k])
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, data: dict) -> "StoryPlan":
        def pick(klass, raw: dict):
            names = {f.name for f in fields(klass)}
            return {k: v for k, v in raw.items() if k in names}

        chars = [CharacterSpec(**pick(CharacterSpec, c)) for c in data.get("characters", [])]
        scenes = []
        for i, s in enumerate(data.get("scenes", []), start=1):
            s = dict(s)
            s["characters"] = [CharacterCue(**pick(CharacterCue, c)) for c in s.get("characters", [])]
            s["props"] = [PropCue(**pick(PropCue, p)) for p in s.get("props", [])]
            s["popups"] = [PopupCue(**pick(PopupCue, p)) for p in s.get("popups", [])]
            s.setdefault("number", i)
            scenes.append(Scene(**pick(Scene, s)))
        plan_kwargs = pick(StoryPlan, {k: v for k, v in data.items() if k not in ("characters", "scenes")})
        plan_kwargs.setdefault("title", data.get("title") or data.get("topic") or "Historia")
        plan_kwargs.setdefault("topic", data.get("topic") or plan_kwargs["title"])
        return cls(characters=chars, scenes=scenes, **plan_kwargs)

    @classmethod
    def from_json(cls, text: str) -> "StoryPlan":
        return cls.from_dict(json.loads(text))
