"""Research + script writing for MIXED EXPLAINER.

Pipeline: (1) optional grounding from Spanish Wikipedia extracts, (2) LLM drafts a
structured scene plan from *only* those facts + well-established knowledge,
(3) a second LLM pass audits every claim, (4) deterministic validation.
A small verified reference pack lets common demo topics work with no LLM at all.
"""

from __future__ import annotations

import json
import re
import unicodedata
from typing import Callable

import requests
from loguru import logger

from . import models3d as M
from .models import Fact, Plan, Scene, SfxCue, Visual

WORDS_PER_SECOND = 2.6
WORD_RANGE = {45: (108, 135), 60: (140, 170)}
MAX_HOOK_WORDS = 10
ANCHORS = {
    "piston_engine": {"piston", "valve_in", "valve_ex", "chamber", "crank", "rod", "head_top", "slave"},
    "turbofan": {"fan", "compressor", "combustor", "turbine", "nozzle", "intake"},
}
STAGES = {"piston_engine": set(M.ENGINE_STAGES), "turbofan": set(M.TURBOFAN_STAGES)}


class ScriptError(RuntimeError):
    pass


def _norm(t: str) -> str:
    t = unicodedata.normalize("NFKD", t.lower())
    return "".join(c for c in t if not unicodedata.combining(c))


# ------------------------------------------------------------------ reference
def _engine_brake_plan(topic: str) -> Plan:
    S = lambda **k: Scene(**k)
    V = lambda **k: Visual(**k)
    return Plan(
        topic=topic, title="¿Cómo funciona el freno de motor de un camión?", source="reference_pack",
        research_note=("Plan verificado (freno de compresión tipo Jacobs): con el combustible cortado, las válvulas de escape "
                       "se abren cerca del final de la compresión; el aire comprimido escapa y no devuelve energía al pistón. "
                       "Fuentes: Cummins (Compression Release Engine Brake), Wikipedia (Compression release engine brake), "
                       "Rush Truck Centers."),
        facts=[
            Fact(claim="Con el freno de motor activado se corta el suministro de combustible."),
            Fact(claim="El freno de compresión abre las válvulas de escape cerca del final de la carrera de compresión."),
            Fact(claim="Sin freno, la energía de la compresión se devuelve al pistón en la expansión; con el freno, el aire escapa antes y no la devuelve."),
            Fact(claim="Los frenos de fricción pueden perder fuerza por sobrecalentamiento (fading); el freno de motor reduce su uso."),
            Fact(claim="El ruido es alto porque las válvulas se abren con aire a alta presión; por eso se restringe en algunas zonas urbanas."),
        ],
        scenes=[
            S(id="s1", role="hook", narration="¿Cómo frena un camión sin usar los frenos?",
              keywords=["sin usar los frenos"], visual=V(kind="hook", model="piston_engine", title="¿Frenar sin frenos?")),
            S(id="s2", role="problem",
              narration="Al bajar una pendiente larga, los frenos de las ruedas se calientan tanto que pueden perder fuerza.",
              keywords=["se calientan", "perder fuerza"],
              visual=V(kind="flow", title="El problema", labels=["Bajada larga", "Frenos calientes", "Menos fuerza"], icons=["cone", "box", "sphere"])),
            S(id="s3", role="step",
              narration="La solución está dentro del motor. Cuando el conductor activa el freno de motor, se corta el combustible.",
              keywords=["freno de motor", "se corta el combustible"],
              visual=V(kind="mechanism", model="piston_engine", stage="brake_full", title="Motor sin combustible",
                       labels=["head_top|Sin inyección", "piston|Pistón"])),
            S(id="s4", role="step",
              narration="Entonces el pistón sube y comprime el aire. Comprimirlo exige mucha energía, y esa energía la aporta el camión.",
              keywords=["comprime el aire", "energía"],
              visual=V(kind="mechanism", model="piston_engine", stage="brake_compression", title="Compresión",
                       labels=["chamber|Aire comprimido"])),
            S(id="s5", role="step",
              narration="Justo al final de la compresión, se abre una válvula de escape y el aire sale de golpe.",
              keywords=["válvula de escape", "sale de golpe"],
              visual=V(kind="mechanism", model="piston_engine", stage="brake_release", title="Liberación",
                       labels=["valve_ex|Válvula de escape", "slave|Mecanismo del freno"]),
              sfx=[SfxCue(type="hiss", at_word=16, reason="el aire comprimido escapa de golpe")]),
            S(id="s6", role="step",
              narration="Sin ese aire empujando de vuelta, el pistón no recupera la energía. En un motor normal, sí la devolvía.",
              keywords=["no recupera la energía"],
              visual=V(kind="mechanism", model="piston_engine", stage="brake_full", title="Sin empuje de regreso",
                       labels=["piston|Sin empuje de regreso"])),
            S(id="s7", role="discovery",
              narration="Así, la energía del camión se va con el aire caliente por el escape. Por eso suena ese estruendo característico.",
              keywords=["aire caliente", "estruendo"],
              visual=V(kind="flow", title="¿A dónde va la energía?", labels=["Energía del camión", "Aire comprimido", "Escape caliente"],
                       icons=["cylinder", "sphere", "cone"]),
              sfx=[SfxCue(type="ping", at_word=0, reason="momento de descubrimiento")]),
            S(id="s8", role="cta", narration="Sigue Explora Ciencia 360 y descubre cómo funciona el mundo.",
              keywords=["Explora Ciencia 360"], visual=V(kind="cta")),
        ],
    )


REFERENCE_PACK: list[tuple[re.Pattern, Callable[[str], Plan]]] = [
    (re.compile(r"freno\s+(de\s+)?motor|jake\s*brake|freno\s+jacobs"), _engine_brake_plan),
]


def reference_plan(topic: str) -> Plan | None:
    n = _norm(topic)
    for pat, fn in REFERENCE_PACK:
        if pat.search(n):
            return fn(topic)
    return None


# ------------------------------------------------------------------- research
def web_research(topic: str, limit_chars: int = 2500) -> list[dict]:
    """Best-effort grounding from Spanish Wikipedia (free, no key). Never raises."""
    try:
        s = requests.get("https://es.wikipedia.org/w/api.php", timeout=8, params={
            "action": "opensearch", "search": topic, "limit": 2, "format": "json"})
        titles = s.json()[1]
        out = []
        for ti in titles:
            r = requests.get("https://es.wikipedia.org/w/api.php", timeout=8, params={
                "action": "query", "prop": "extracts", "explaintext": 1, "exintro": 1, "titles": ti, "format": "json"})
            page = next(iter(r.json()["query"]["pages"].values()))
            out.append({"title": ti, "url": "https://es.wikipedia.org/wiki/" + ti.replace(" ", "_"),
                        "text": (page.get("extract") or "")[:limit_chars]})
        return out
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"web research unavailable: {exc}")
        return []


def _extract_json(text: str) -> dict:
    a, b = text.find("{"), text.rfind("}")
    if a < 0 or b <= a:
        raise ScriptError("el modelo no devolvió JSON")
    return json.loads(text[a:b + 1])


PROMPT = """Eres guionista de divulgación científica para "Explora Ciencia 360" (videos verticales de {duration} s en español latino).
TEMA: {topic}

FUENTES DISPONIBLES (usa solo hechos respaldados por ellas o por conocimiento de libro de texto indiscutible):
{sources}

REGLAS ESTRICTAS
- No inventes cifras, fechas, nombres ni afirmaciones. Si no estás seguro, no lo digas. Sin relleno.
- Narración total entre {wmin} y {wmax} palabras, 7 a 9 escenas, explicación progresiva y fácil de entender.
- Estructura: escena 1 role "hook" (pregunta/gancho de MÁXIMO {hook} palabras), escena 2 "problem", escenas "step" que explican paso a paso, una "discovery", última "cta" que diga exactamente "Sigue Explora Ciencia 360".
- Cada escena: narration (frases cortas, pronunciables), keywords (1-3 frases EXACTAS de la narración), visual y sfx.
- visual.kind ∈ hook|mechanism|flow|cycle|layers|stat|cta.
  * mechanism con model "piston_engine" (stage ∈ {pe}; labels "ancla|Texto", anclas {pea}) o "turbofan" (stage ∈ {tf}; anclas {tfa}). Úsalos SOLO si el tema trata de ese mecanismo.
  * flow/cycle: labels = 3-5 nombres cortos de etapas; icons opcionales ∈ gear|box|cylinder|sphere|cone.
  * layers: labels = capas. stat: labels + values numéricos (solo si el dato es real) + unit.
  * hook: model opcional (piston_engine|turbofan) y title corto (≤6 palabras).
- sfx: lista opcional; solo si el sonido APORTA información (type ∈ whoosh|ping|rumble|hiss|thump|tick, at_word = índice de palabra, reason). Máximo 3 en todo el video.
Responde SOLO JSON: {{"title":str,"facts":[{{"claim":str,"confidence":"high"|"medium","note":str}}],"scenes":[{{"id":"s1","role":..,"narration":..,"keywords":[..],"visual":{{..}},"sfx":[..]}}]}}"""

AUDIT = """Audita este guion de divulgación. Compara cada afirmación con las FUENTES y con conocimiento científico establecido.
Devuelve SOLO JSON: {{"ok":bool,"problems":[{{"scene":"s#","claim":str,"why":str}}]}}. ok=false si hay datos inventados, dudosos o incorrectos.
FUENTES:\n{sources}\n\nGUION:\n{script}"""


def validate_plan(plan: Plan, duration: int) -> list[str]:
    issues: list[str] = []
    lo, hi = WORD_RANGE[duration]
    wc = plan.word_count()
    if not (lo * 0.9 <= wc <= hi * 1.1):
        issues.append(f"guion de {wc} palabras; para {duration}s se esperan {lo}-{hi}")
    if not (5 <= len(plan.scenes) <= 10):
        issues.append("debe tener entre 5 y 10 escenas")
    ids = [s.id for s in plan.scenes]
    if len(set(ids)) != len(ids):
        issues.append("ids de escena repetidos")
    first, last = plan.scenes[0], plan.scenes[-1]
    if first.role != "hook" or len(first.narration.split()) > MAX_HOOK_WORDS:
        issues.append(f"la primera escena debe ser un gancho de máximo {MAX_HOOK_WORDS} palabras")
    if last.role != "cta" or "explora ciencia 360" not in _norm(last.narration):
        issues.append("la última escena debe ser la llamada a seguir Explora Ciencia 360")
    nsfx = sum(len(s.sfx) for s in plan.scenes)
    if nsfx > 3:
        issues.append(f"{nsfx} efectos de sonido (máximo 3 en el plan)")
    for s in plan.scenes:
        v = s.visual
        if not s.narration.strip():
            issues.append(f"{s.id}: narración vacía")
        if v.kind == "mechanism" and v.model in STAGES:
            if v.stage and v.stage not in STAGES[v.model]:
                issues.append(f"{s.id}: etapa {v.stage!r} inválida para {v.model}")
            for lab in v.labels:
                if "|" in lab and lab.split("|", 1)[0] not in ANCHORS[v.model]:
                    issues.append(f"{s.id}: ancla {lab.split('|')[0]!r} inválida para {v.model}")
        if v.kind == "stat" and (not v.values or len(v.values) != len(v.labels)):
            issues.append(f"{s.id}: 'stat' requiere un valor por etiqueta")
        low = _norm(s.narration)
        s.keywords = [k for k in s.keywords if _norm(k) in low]
        for c in s.sfx:
            if not (0 <= c.at_word < max(1, len(s.narration.split()))):
                c.at_word = 0
    return issues


LLMFn = Callable[[str], str]


def generate_plan(topic: str, duration: int = 45, llm: LLMFn | None = None, research: bool = True) -> Plan:
    ref = reference_plan(topic)
    if ref is not None:
        issues = validate_plan(ref, duration)
        hard = [i for i in issues if "palabras" not in i]
        if hard:
            raise ScriptError("; ".join(hard))
        return ref
    if llm is None:
        from app.services import llm as llm_service
        llm = llm_service._generate_response
    sources = web_research(topic) if research else []
    src_text = "\n\n".join(f"[{s['title']}] ({s['url']})\n{s['text']}" for s in sources) or "(sin fuentes web disponibles; usa solo conocimiento indiscutible)"
    lo, hi = WORD_RANGE[duration]
    prompt = PROMPT.format(duration=duration, topic=topic, sources=src_text, wmin=lo, wmax=hi, hook=MAX_HOOK_WORDS,
                           pe="|".join(sorted(STAGES["piston_engine"])), pea=",".join(sorted(ANCHORS["piston_engine"])),
                           tf="|".join(sorted(STAGES["turbofan"])), tfa=",".join(sorted(ANCHORS["turbofan"])))
    feedback = ""
    last_issues: list[str] = []
    for attempt in range(3):
        raw = llm(prompt + feedback)
        try:
            data = _extract_json(raw)
            plan = Plan(topic=topic, title=data.get("title", topic), facts=data.get("facts", []), scenes=data["scenes"],
                        research_note="Fuentes: " + (", ".join(s["url"] for s in sources) or "ninguna (conocimiento del modelo)"))
        except Exception as exc:  # noqa: BLE001
            feedback = f"\n\nTu respuesta anterior no fue válida ({exc}). Devuelve solo el JSON correcto."
            last_issues = [str(exc)]
            continue
        issues = validate_plan(plan, duration)
        if not issues:
            audit = _extract_json(llm(AUDIT.format(sources=src_text, script=json.dumps(
                [{"scene": s.id, "narration": s.narration} for s in plan.scenes], ensure_ascii=False))))
            if audit.get("ok", False):
                return plan
            issues = [f"{p.get('scene')}: {p.get('claim')} ({p.get('why')})" for p in audit.get("problems", [])] or ["auditoría fallida"]
        last_issues = issues
        feedback = "\n\nCorrige estos problemas y devuelve el JSON completo:\n- " + "\n- ".join(issues)
    raise ScriptError("No se obtuvo un guion válido y verificado: " + "; ".join(last_issues) +
                      ". Usa el modo 'revisar guion' para editarlo manualmente.")
