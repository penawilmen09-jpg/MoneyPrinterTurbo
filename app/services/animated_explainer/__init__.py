"""Sistema local y gratuito de videos explicativos 2D verticales (9:16).

Todo el render es local (Pillow + numpy + FFmpeg). No usa Higgsfield, Seedance
ni ninguna API de generación de video de pago.

Uso rápido::

    python -m app.services.animated_explainer examples/autoridad_limitada.json salida.mp4
"""

__all__ = ["render_video", "load_script", "parse_plain_text", "ExplainerScript"]


def __getattr__(name):  # importación perezosa: no carga Pillow/numpy hasta que hace falta
    if name == "render_video":
        from .pipeline import render_video
        return render_video
    if name in ("load_script", "parse_plain_text", "ExplainerScript"):
        from . import script
        return getattr(script, name)
    raise AttributeError(name)
