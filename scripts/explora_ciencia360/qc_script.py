"""Comprueba que la narración alineada coincide literalmente con el guion aprobado."""
import json, sys, re
from script_text import PARAGRAPHS, VOICE_ID
d = json.load(open(sys.argv[1]))
assert d["voice_id"] == VOICE_ID, "Voice ID distinto"
want = "\n\n".join(PARAGRAPHS)
print("texto enviado == guion:", d["text"] == want)
print("caracteres alineados == longitud del texto:", len(d["alignment"]["characters"]) == len(want))
print("alineación reconstruye el guion:", "".join(d["alignment"]["characters"]) == want)
