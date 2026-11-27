"""Guion de «El cajero que descubrió un robo imposible».

Cada «beat» es una frase de narración (texto literal del encargo). Las
escenas se sincronizan con el momento real en que se pronuncia cada beat.
"""

TITLE = "El cajero que descubrió un robo imposible"
# La voz (ElevenLabs, ID fijo) vive en elevenlabs_tts.VOICE_ID.

# (id, texto, pausa_después_en_segundos)
BEATS = [
    ("h1", "Un supermercado perdió miles de dólares durante semanas…", 0.45),
    ("h2", "y lo más extraño es que nadie entraba a robar.", 0.35),
    ("h3", "El dinero simplemente desaparecía de las cajas registradoras.", 0.55),
    ("d1", "El gerente revisó las cámaras, interrogó a los empleados y comprobó los recibos.", 0.35),
    ("d2", "Todo parecía normal.", 0.5),
    ("d3", "Pero un cajero notó algo extraño: cada vez que un cliente pagaba en efectivo y pedía cambio, aparecía una pequeña diferencia en el registro.", 0.45),
    ("d4", "Decidió observar con más atención.", 0.5),
    ("d5", "Una noche, revisó las grabaciones y descubrió que uno de los empleados utilizaba un truco para registrar devoluciones falsas y quedarse con el dinero.", 0.5),
    ("d6", "Lo había hecho durante semanas, aprovechando que nadie revisaba las operaciones pequeñas.", 0.6),
    ("c1", "Cuando sumaron todas las operaciones, descubrieron que las pequeñas cantidades habían formado una pérdida enorme.", 0.45),
    ("c2", "El empleado fue descubierto y el supermercado cambió sus controles de seguridad.", 0.6),
    ("c3", "Y es que, a veces, un gran robo no comienza con una gran cantidad… sino con pequeñas cantidades que nadie se molesta en revisar.", 0.0),
]

FPS = 30
W, H = 1080, 1920
LEAD_IN = 0.35     # silencio inicial antes de la primera palabra
TAIL_OUT = 2.2     # cola tras la última palabra (escena final + música)
