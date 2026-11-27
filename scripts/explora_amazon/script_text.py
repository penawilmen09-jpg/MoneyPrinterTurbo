"""Guion — documental Amazon / Jeff Bezos (Explora Ciencia 360). Texto EXACTO del usuario."""
VOICE_ID = "851ejYcv2BoNPjrkw93G"
SCENES_TEXT = [
    ("gancho", "Hoy puedes comprar prácticamente cualquier cosa con unos pocos clics. Pero hubo un tiempo en que esta empresa solo vendía libros desde un pequeño garaje. Su fundador apostó su futuro por una idea que muchos consideraban una locura… y terminó construyendo uno de los imperios más grandes del planeta"),
    ("idea", "Su nombre era Jeff Bezos. En 1994 dejó su trabajo en el mundo financiero y decidió apostar por el enorme potencial de Internet. Eligió comenzar vendiendo libros, porque podían almacenarse y enviarse con relativa facilidad."),
    ("nacimiento", "En 1995 nació Amazon como una librería por Internet. Al principio, un pequeño equipo preparaba los pedidos manualmente. Cada paquete representaba una oportunidad para crecer."),
    ("catalogo", "Pero Bezos tenía una visión mucho más grande. Amazon comenzó a ampliar su catálogo, incorporando nuevas categorías de productos y convirtiéndose en un enorme mercado digital."),
    ("imperio", "Con el tiempo, Amazon dejó de ser solamente una tienda. Construyó una gigantesca red logística, lanzó Amazon Prime y desarrolló Amazon Web Services, una plataforma de computación en la nube utilizada por millones de clientes."),
    ("gigante", "Lo que comenzó con libros terminó convirtiéndose en una de las empresas más importantes del mundo. Una apuesta por Internet que transformó para siempre nuestra manera de comprar."),
    ("cierre", "Y todo comenzó con una idea que parecía demasiado arriesgada. ¿Qué otra historia extraordinaria quieres conocer? Síguenos en Explora Ciencia 360"),
]
def tts_text(): return "\n\n".join(t for _, t in SCENES_TEXT)
