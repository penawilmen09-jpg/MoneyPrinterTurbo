"""Guion aprobado — documental Elon Musk (Explora Ciencia 360)."""
VOICE_ID = "851ejYcv2BoNPjrkw93G"
# (escena, texto mostrado/subtitulado)
SCENES_TEXT = [
    ("gancho", "¿Cómo puede un hombre acumular una fortuna de cientos de miles de millones de dólares? Esta es la historia de Elon Musk, el hombre más rico del mundo."),
    ("comienzos", "Nació en Sudáfrica y desde muy joven mostró un enorme interés por la tecnología. Cuando era adolescente, incluso creó y vendió su propio videojuego."),
    ("zip2", "En 1995 fundó Zip2 junto a su hermano. Cuatro años después, la empresa fue vendida a Compaq por cientos de millones de dólares. Pero Elon no se detuvo."),
    ("paypal", "Después apostó por los pagos digitales con X.com, que terminó convirtiéndose en parte de PayPal. En 2002, eBay compró PayPal por mil quinientos millones de dólares."),
    ("espacio", "Con parte de su fortuna impulsó SpaceX, fundada en 2002, y se convirtió en una figura clave de Tesla. Apostó por los cohetes reutilizables y los automóviles eléctricos."),
    ("imperio", "Su fortuna creció enormemente gracias al valor de sus participaciones empresariales. En noviembre de 2026, Forbes estimaba su patrimonio en unos ochocientos veintitrés mil quinientos millones de dólares."),
    ("cierre", "Pero su historia demuestra algo: una idea puede cambiar una industria entera. ¿Qué te gustaría descubrir en nuestro próximo video? Síguenos en Explora Ciencia 360."),
]
# Sólo para la síntesis: ayuda de pronunciación (no cambia lo que se ve en pantalla).
TTS_SUBS = {"Zip2": "Zip Dos"}
def tts_text():
    out = []
    for _, t in SCENES_TEXT:
        for a, b in TTS_SUBS.items(): t = t.replace(a, b)
        out.append(t)
    return "\n\n".join(out)

# ---- v2: nuevo gancho (texto EXACTO del usuario; sin punto final)
HOOK = "Imagina tener tanto dinero que podrías gastar un millón de dólares todos los días durante más de 2.000 años... y todavía no habrías gastado toda tu fortuna. Esta es la historia del hombre más rico del mundo"
HOOK_TTS_SUBS = {"2.000": "dos mil"}   # sólo ayuda de pronunciación; en pantalla se muestra "2.000"
def hook_tts():
    t = HOOK
    for a, b in HOOK_TTS_SUBS.items(): t = t.replace(a, b)
    return t
