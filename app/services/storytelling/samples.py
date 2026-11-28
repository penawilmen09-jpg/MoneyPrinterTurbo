"""Historia de ejemplo ORIGINAL (ficticia) para la primera prueba del modo."""

from __future__ import annotations

from .models import (CharacterCue as C, CharacterSpec, PopupCue as Pop, PropCue as Pr, Scene, StoryPlan)

TOPIC = "El empleado que descubrió una pequeña estafa en un supermercado"


def supermarket_scam_plan() -> StoryPlan:
    mateo = CharacterSpec(
        id="mateo", name="Mateo", role="cajero del supermercado", gender="m", age="young", skin="tan",
        hair_style="short", hair_color="#3b2a20", eye_color="#4a3020", outfit="apron",
        top_color="#3a8fd9", accent_color="#e0483a", bottom_color="#2f3a5c", accessories=["badge"], build="average",
    )
    rios = CharacterSpec(
        id="rios", name="Sra. Ríos", role="gerente", gender="f", age="adult", skin="light",
        hair_style="bun", hair_color="#2a2024", eye_color="#3a2a22", outfit="suit",
        top_color="#5b3b8c", accent_color="#e5c64a", bottom_color="#2e2a44", accessories=["glasses"], build="slim",
    )
    beto = CharacterSpec(
        id="beto", name="Don Beto", role="guardia de seguridad", gender="m", age="senior", skin="brown",
        hair_style="cap", hair_color="#555555", eye_color="#3a2a22", outfit="uniform",
        top_color="#22345a", accent_color="#e5c64a", bottom_color="#1c2a48", accessories=["mustache"], build="stocky",
    )
    ramiro = CharacterSpec(
        id="ramiro", name="Ramiro", role="cliente sospechoso", gender="m", age="adult", skin="fair",
        hair_style="curly", hair_color="#5a3320", eye_color="#3a2a22", outfit="hoodie",
        top_color="#d98b2b", accent_color="#f0c060", bottom_color="#3a3a46", accessories=["beard"], build="average",
    )
    S = Scene
    scenes = [
        S(1, "¿Cómo se pierde dinero en un supermercado sin que nadie robe nada?", label="gancho", location="street",
          time_of_day="evening", shot="wide", camera_move="push_in", transition_in="cut", sfx="whoosh",
          characters=[C("mateo", "center_left", "walk_in", "worried", enters_from="left", look_at="")],
          popups=[Pop("popup", "?", 0.9, 2.2, "char:mateo", "info")], background_extras=3,
          keywords=["dinero", "nadie"], action_summary="Mateo camina hacia el supermercado al atardecer, pensativo."),
        S(2, "Mateo era cajero en un súper de barrio. Todo iba bien… hasta que la caja dejó de cuadrar.",
          label="presentacion", location="checkout", shot="medium", camera_move="pull_out", transition_in="slide_left",
          characters=[C("mateo", "center_right", "talk", "happy", depth="behind", look_at="")],
          props=[Pr("cash_register", "counter", "right", 1.0)], background_extras=2,
          keywords=["cajero", "cuadrar"], action_summary="Mateo sonríe tras la caja registradora del supermercado."),
        S(3, "Cada noche faltaban unos pocos dólares. Siempre en el mismo turno.", label="desarrollo",
          location="checkout", shot="close_up", camera_move="push_in", transition_in="fade", time_of_day="night",
          characters=[C("mateo", "center_right", "scan_item", "worried", depth="behind")],
          props=[Pr("money", "counter", "center_right", 0.9), Pr("calculator", "counter", "right", 0.8, "bounce")],
          popups=[Pop("counter", "-$5", 1.2, 2.6, "prop:money", "alert")], sfx="alert",
          keywords=["faltaban", "mismo", "turno"], action_summary="Mateo cuenta el dinero con cara de preocupación; faltan dólares."),
        S(4, "La gerente, la señora Ríos, empezó a sospechar de él.", label="desarrollo", location="office",
          shot="medium", camera_move="pan_right", transition_in="slide_right",
          characters=[C("rios", "right", "point", "angry", look_at="mateo", depth="behind"),
                      C("mateo", "left", "hands_up", "worried", look_at="rios")],
          popups=[Pop("speech", "¡Otra vez faltan cinco dólares!", 0.7, 2.8, "char:rios", "alert")],
          keywords=["sospechar", "gerente"], action_summary="La gerente señala con enfado a Mateo, que levanta las manos."),
        S(5, "Mateo pidió revisar las cámaras de seguridad junto a Don Beto, el guardia.", label="tension",
          location="security_room", shot="medium", camera_move="push_in", transition_in="circle", time_of_day="night",
          characters=[C("beto", "center_right", "type", "neutral", depth="behind", look_at="mateo"),
                      C("mateo", "left", "lean_in", "suspicious", look_at="prop:cctv_camera")],
          props=[Pr("cctv_camera", "wall", "left", 0.9, "blink")], sfx="beep",
          keywords=["cámaras", "seguridad"], action_summary="Mateo y Don Beto revisan los monitores de las cámaras."),
        S(6, "Y apareció un patrón: cada noche, el mismo cliente.", label="tension", location="security_room",
          shot="close_up", camera_move="push_in", transition_in="fade", time_of_day="night",
          characters=[C("mateo", "center", "look_around", "surprised")],
          props=[Pr("magnifier", "floor", "center_right", 1.2, "bounce")],
          popups=[Pop("popup", "¡El mismo!", 0.6, 2.4, "char:mateo", "alert")], sfx="suspense",
          keywords=["patrón", "mismo", "cliente"], action_summary="Mateo se sorprende al ver el mismo cliente en todas las grabaciones."),
        S(7, "Ramiro pagaba una compra mínima con un billete grande.", label="descubrimiento", location="checkout",
          shot="medium", camera_move="pan_left", transition_in="wipe",
          characters=[C("ramiro", "center_left", "hold_item", "smug", look_at="mateo", holding="money"),
                      C("mateo", "center_right", "idle", "neutral", depth="behind", look_at="ramiro")],
          props=[Pr("cash_register", "counter", "right", 1.0)],
          keywords=["billete", "grande"], action_summary="Ramiro entrega un billete grande al cajero para pagar poco."),
        S(8, "A media cuenta cambiaba de opinión, y en la confusión el cambio salía de más.", label="descubrimiento",
          location="checkout", shot="medium", camera_move="shake", transition_in="cut",
          characters=[C("ramiro", "center_left", "point", "smug", look_at="mateo", speaking=False),
                      C("mateo", "center_right", "shrug", "worried", depth="behind", look_at="ramiro")],
          props=[Pr("receipt", "counter", "center", 0.9), Pr("coins", "counter", "right", 0.9, "shake")],
          popups=[Pop("speech", "¡Mejor dame esto otro… no, espera!", 0.4, 2.7, "char:ramiro", "info"),
                  Pop("counter", "+$5", 3.6, 2.2, "prop:coins", "money")], sfx="cash",
          keywords=["cambiaba", "confusión", "cambio", "más"], action_summary="Ramiro cambia el pedido para confundir a Mateo; el cambio sale de más."),
        S(9, "Mateo no había robado nada: era víctima de un truco muy viejo.", label="descubrimiento", location="office",
          shot="medium", camera_move="push_in", transition_in="fade",
          characters=[C("rios", "right", "nod", "happy", look_at="mateo", depth="behind"),
                      C("mateo", "left", "celebrate", "happy", look_at="rios")],
          props=[Pr("check_mark", "wall", "center", 1.3, "grow")], sfx="ding",
          keywords=["víctima", "truco", "viejo"], action_summary="La gerente reconoce la inocencia de Mateo; ambos sonríen."),
        S(10, "Desde entonces, allí cuentan el cambio en voz alta. Y tú, ¿revisas el tuyo? Sigue Explora Ciencia 360.",
          label="final", location="street", time_of_day="evening", shot="wide", camera_move="pull_out", transition_in="zoom",
          characters=[C("mateo", "center_left", "wave", "happy", look_at="camera"),
                      C("rios", "center_right", "idle", "happy", look_at="camera")],
          popups=[Pop("popup", "¡Cuenta tu cambio!", 1.6, 3.2, "char:mateo", "good")], background_extras=3,
          keywords=["cambio", "revisas", "Explora", "Ciencia", "360"], action_summary="Mateo y la gerente saludan frente al supermercado."),
    ]
    return StoryPlan(
        title="El cajero y el cambio de más", topic=TOPIC, category="Estafas y engaños", veracity="ficticia",
        disclaimer="Historia ficticia inspirada en estafas reales de cambio", target_duration=52.0,
        characters=[mateo, rios, beto, ramiro], scenes=scenes,
    )
