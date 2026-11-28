"""Guion y planificación automática de escenas a partir de un tema.

* Investiga (Wikipedia en español, gratis, sin clave) cuando la historia se
  presenta como real y sólo permite usar los datos encontrados.
* Verifica que toda cifra de la narración aparezca en las fuentes.
* Si no hay fuentes, la historia se marca como FICCIÓN y se avisa en pantalla.
"""

from __future__ import annotations

import json
import re
from typing import Callable

from .models import (ACTIONS, CAMERA_MOVES, EXPRESSIONS, LOCATIONS, POPUP_TYPES, POSITIONS, PROP_NAMES,
                     SFX_NAMES, SHOTS, STRUCTURE_LABELS, TRANSITIONS, CharacterCue, CharacterSpec, PopupCue,
                     PropCue, Scene, StoryPlan)
from .sets import get_set

WORDS_PER_SECOND = 2.55
DISCLAIMER_FICTION = "Historia ficticia inspirada en casos reales"

SYSTEM_PROMPT = """Eres guionista de vídeos verticales de historias animadas para el canal "Explora Ciencia 360".
Escribes en español latino natural, ritmo de documental/storytelling, frases cortas y con intriga.
Devuelves EXCLUSIVAMENTE un JSON válido (sin texto extra, sin markdown)."""


def build_prompt(topic: str, category: str, seconds: int, veracity: str, facts: str = "") -> str:
    words = int(seconds * WORDS_PER_SECOND * 0.92)
    facts_block = (
        f"\nDATOS VERIFICADOS (única fuente permitida para hechos, nombres, cifras y fechas):\n{facts}\n"
        "No inventes ningún dato fuera de esta lista. Si algo no está aquí, no lo afirmes."
        if veracity == "real" else
        "\nLa historia es FICCIÓN original: personajes y cifras inventados, pero verosímiles. "
        "No la presentes como un hecho real ni uses nombres de personas o empresas reales."
    )
    return f"""{SYSTEM_PROMPT}

TEMA: {topic}
CATEGORÍA: {category}
DURACIÓN OBJETIVO: {seconds} segundos de narración (~{words} palabras en total).
{facts_block}

ESTRUCTURA OBLIGATORIA (campo "label" de cada escena, en este orden):
gancho (frase que despierte curiosidad en 3 s) -> presentacion -> desarrollo -> tension -> descubrimiento -> final
El final debe dar una conclusión interesante e invitar a seguir "Explora Ciencia 360".
La historia debe entenderse aunque el espectador no conozca el tema. Nada aburrido ni explicaciones largas.

Genera de 8 a 12 escenas. En cada escena la imagen debe representar EXACTAMENTE lo que dice el narrador.
Crea 2 a 4 personajes originales con ficha visual detallada (se reutilizan idénticos en todas las escenas).

VOCABULARIOS PERMITIDOS:
- location: {list(LOCATIONS)}
- action: {list(ACTIONS)}
- expression: {list(EXPRESSIONS)}
- position: {list(POSITIONS)}
- shot: {list(SHOTS)}
- camera_move: {list(CAMERA_MOVES)}
- transition_in: {list(TRANSITIONS)}
- sfx (opcional, pocos): {list(SFX_NAMES)}
- props: {list(PROP_NAMES)} con anchor en [floor, counter, wall, screen]
- popups type: {list(POPUP_TYPES)}, style en [alert, info, money, good]; "speech" = bocadillo de diálogo corto del personaje.
- personaje: gender m|f, age young|adult|senior, skin [light, fair, tan, brown, dark], hair_style [short, parted, bald, bun, long, curly, cap, ponytail],
  outfit [shirt, tshirt, apron, uniform, suit, labcoat, hoodie, dress], build [slim, average, stocky], accessories [glasses, tie, badge, mustache, beard, headset, earrings, scarf],
  colores como "#rrggbb": hair_color, eye_color, top_color, accent_color, bottom_color.
- depth "behind" = personaje detrás del mostrador/escritorio (solo en checkout, office, security_room, lab).

FORMATO JSON:
{{"title": "...", "category": "...", "veracity": "{veracity}", "sources": [{{"title": "...", "url": "..."}}],
 "characters": [{{"id":"mateo","name":"Mateo","role":"...", ...ficha...}}],
 "scenes": [{{"number":1,"label":"gancho","narration":"texto exacto que dirá el narrador",
   "location":"street","time_of_day":"day|evening|night","shot":"wide","camera_move":"push_in","transition_in":"cut",
   "characters":[{{"id":"mateo","position":"center","action":"walk_in","expression":"worried","enters_from":"left","look_at":"","depth":""}}],
   "props":[{{"name":"cash_register","anchor":"counter","position":"right","scale":1.0,"animation":""}}],
   "popups":[{{"type":"speech","text":"¡Alto!","at":0.6,"duration":2.0,"target":"char:mateo","style":"alert"}}],
   "sfx":"","keywords":["palabra","clave"],"background_extras":0,"action_summary":"qué se ve"}}]}}
Reglas: la suma de palabras de todas las "narration" ≈ {words}. Las escenas con 2 personajes usan posiciones distintas.
Los textos en pantalla (popups) son muy cortos."""


# --------------------------------------------------------------------------
def research_topic(topic: str, lang: str = "es", timeout: float = 10.0) -> tuple[str, list[dict]]:
    """Busca datos verificables en Wikipedia (gratis). Devuelve (texto_de_datos, fuentes)."""
    import requests

    base = f"https://{lang}.wikipedia.org/w/api.php"
    try:
        r = requests.get(base, params={"action": "query", "list": "search", "srsearch": topic, "format": "json",
                                       "srlimit": 3}, timeout=timeout, headers={"User-Agent": "ExploraCiencia360-storytelling/1.0"})
        hits = r.json().get("query", {}).get("search", [])
        if not hits:
            return "", []
        facts, sources = [], []
        for h in hits[:2]:
            title = h["title"]
            ex = requests.get(base, params={"action": "query", "prop": "extracts", "exintro": 1, "explaintext": 1,
                                            "titles": title, "format": "json", "redirects": 1}, timeout=timeout,
                              headers={"User-Agent": "ExploraCiencia360-storytelling/1.0"}).json()
            page = next(iter(ex["query"]["pages"].values()))
            text = (page.get("extract") or "").strip()
            if len(text) > 200:
                facts.append(f"[{title}] {text[:1800]}")
                sources.append({"title": title, "url": f"https://{lang}.wikipedia.org/wiki/{title.replace(' ', '_')}"})
        return "\n\n".join(facts), sources
    except Exception:
        return "", []


def unverified_numbers(plan: StoryPlan, facts: str) -> list[str]:
    """Cifras de la narración que NO aparecen en los datos investigados."""
    bad = []
    flat = re.sub(r"[.,\s]", "", facts)
    for sc in plan.scenes:
        for num in re.findall(r"\d[\d.,]*", sc.narration):
            digits = re.sub(r"[.,]", "", num)
            if digits and digits not in flat:
                bad.append(f"escena {sc.number}: «{num}»")
    return bad


# --------------------------------------------------------------------------
def _pick(value, allowed, default):
    return value if value in allowed else default


def normalize_plan(data: dict, topic: str, seconds: int, veracity: str, sources: list[dict]) -> StoryPlan:
    """Convierte la respuesta del LLM en un plan válido (vocabulario cerrado, posiciones, etc.)."""
    chars = []
    for i, c in enumerate(data.get("characters", [])[:5]):
        cid = re.sub(r"\W", "", str(c.get("id") or c.get("name") or f"p{i}").lower()) or f"p{i}"
        fields_ok = {k: v for k, v in c.items() if k in CharacterSpec.__dataclass_fields__}
        fields_ok["id"] = cid
        fields_ok.setdefault("name", cid.title())
        chars.append(CharacterSpec(**fields_ok).normalized())
    ids = {c.id for c in chars}

    scenes = []
    for i, s in enumerate(data.get("scenes", [])[:12], start=1):
        loc = _pick(s.get("location"), LOCATIONS, "street")
        info = get_set(loc).info
        cues, used = [], set()
        for cc in s.get("characters", []):
            cid = re.sub(r"\W", "", str(cc.get("id", "")).lower())
            if cid not in ids:
                continue
            pos = _pick(cc.get("position"), POSITIONS, "center")
            while pos in used:  # posiciones distintas
                pos = POSITIONS[(POSITIONS.index(pos) + 2) % len(POSITIONS)]
            used.add(pos)
            depth = cc.get("depth", "") if info.has_fg else ""
            cues.append(CharacterCue(
                id=cid, position=pos, action=_pick(cc.get("action"), ACTIONS, "talk"),
                expression=_pick(cc.get("expression"), EXPRESSIONS, "neutral"),
                enters_from=_pick(cc.get("enters_from"), ("", "left", "right"), ""),
                look_at=str(cc.get("look_at", "") or ""), speaking=bool(cc.get("speaking", False)),
                holding=_pick(cc.get("holding"), PROP_NAMES, "") if cc.get("holding") else "",
                depth="behind" if depth == "behind" else "",
            ))
        props = [PropCue(name=p["name"], anchor=_pick(p.get("anchor"), ("floor", "counter", "wall", "screen"), "floor"),
                         position=_pick(p.get("position"), POSITIONS, "center"), scale=float(p.get("scale", 1.0) or 1.0),
                         animation=_pick(p.get("animation"), ("", "bounce", "blink", "slide_in", "shake", "grow"), ""))
                 for p in s.get("props", []) if p.get("name") in PROP_NAMES]
        if not info.counter_top:
            for p in props:
                if p.anchor == "counter":
                    p.anchor = "floor"
        popups = [PopupCue(type=_pick(p.get("type"), POPUP_TYPES, "popup"), text=str(p.get("text", ""))[:42],
                           at=float(p.get("at", 0.8)), duration=float(p.get("duration", 2.0)), target=str(p.get("target", "")),
                           style=_pick(p.get("style"), ("alert", "info", "money", "good"), "info"))
                  for p in s.get("popups", [])][:3]
        scenes.append(Scene(
            number=i, narration=str(s.get("narration", "")).strip(), label=_pick(s.get("label"), STRUCTURE_LABELS, "desarrollo"),
            location=loc, time_of_day=_pick(s.get("time_of_day"), ("day", "evening", "night"), "day"),
            characters=cues, props=props, popups=popups, shot=_pick(s.get("shot"), SHOTS, "medium"),
            camera_move=_pick(s.get("camera_move"), CAMERA_MOVES, "push_in"), focus=str(s.get("focus", "") or ""),
            transition_in="cut" if i == 1 else _pick(s.get("transition_in"), TRANSITIONS, "fade"),
            sfx=_pick(s.get("sfx"), SFX_NAMES, "") if i > 1 else "", keywords=[str(k) for k in s.get("keywords", [])][:5],
            background_extras=min(4, int(s.get("background_extras", 0) or 0)), action_summary=str(s.get("action_summary", "")),
        ))
    if scenes:
        scenes[0].label, scenes[-1].label = "gancho", "final"
    plan = StoryPlan(
        title=str(data.get("title") or topic)[:90], topic=topic, category=str(data.get("category") or "Historias curiosas"),
        veracity=veracity, sources=sources, target_duration=float(seconds), characters=chars, scenes=scenes,
        disclaimer="" if veracity == "real" else DISCLAIMER_FICTION,
    )
    return plan


def validate_plan(plan: StoryPlan, seconds: int) -> list[str]:
    """Problemas que impiden usar el plan tal cual (el generador reintenta)."""
    errs = []
    if not 8 <= len(plan.scenes) <= 12:
        errs.append(f"hay {len(plan.scenes)} escenas; deben ser 8–12")
    if not plan.characters:
        errs.append("faltan personajes")
    words = len(plan.narration.split())
    budget = seconds * WORDS_PER_SECOND
    if words > budget * 1.12:
        errs.append(f"narración demasiado larga ({words} palabras; máximo ≈ {int(budget * 1.12)})")
    if words < budget * 0.6:
        errs.append(f"narración demasiado corta ({words} palabras; mínimo ≈ {int(budget * 0.6)})")
    for sc in plan.scenes:
        if not sc.narration:
            errs.append(f"escena {sc.number} sin narración")
        if not sc.characters and not sc.props:
            errs.append(f"escena {sc.number} sin personajes ni objetos")
    return errs


def _parse_json(text: str) -> dict:
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < 0:
        raise ValueError("la respuesta del modelo no contiene JSON")
    return json.loads(text[start: end + 1])


def generate_plan(topic: str, *, category: str = "Historias curiosas", seconds: int = 52, mode: str = "auto",
                  llm_fn: Callable[[str], str] | None = None, research: bool = True, max_attempts: int = 3) -> StoryPlan:
    """Tema -> StoryPlan.  ``mode``: auto | real | ficticia."""
    if llm_fn is None:
        from app.services import llm

        llm_fn = llm._generate_response  # reutiliza el proveedor LLM ya configurado

    facts, sources, veracity = "", [], "ficticia"
    if mode in ("auto", "real") and research:
        facts, sources = research_topic(topic)
        if facts:
            veracity = "real"
        elif mode == "real":
            raise RuntimeError("No se encontraron fuentes verificables para presentar la historia como real. "
                               "Usa modo 'ficticia' o aporta otro tema.")
    last_err = ""
    for attempt in range(max_attempts):
        prompt = build_prompt(topic, category, seconds, veracity, facts)
        if last_err:
            prompt += f"\n\nCORRIGE los problemas de tu intento anterior: {last_err}"
        raw = llm_fn(prompt)
        try:
            plan = normalize_plan(_parse_json(raw), topic, seconds, veracity, sources)
        except Exception as e:  # JSON inválido
            last_err = f"JSON inválido ({e})"
            continue
        errs = validate_plan(plan, seconds)
        if veracity == "real":
            bad = unverified_numbers(plan, facts)
            if bad:
                errs.append("cifras no presentes en los datos verificados: " + ", ".join(bad))
        if not errs:
            return plan
        last_err = "; ".join(errs)
    raise RuntimeError(f"No se pudo generar un plan válido tras {max_attempts} intentos: {last_err}")
