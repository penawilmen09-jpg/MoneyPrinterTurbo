import numpy as np, soundfile as sf, sys
from kokoro_onnx import Kokoro
K = Kokoro('/tmp/kokoro/kokoro-v1.0.onnx', '/tmp/kokoro/voices-v1.0.bin')
LINES = ["Una isla del Caribe. Dos países y dos historias muy diferentes.",
"Esta es La Española, compartida por República Dominicana y Haití.",
"Al este se encuentra República Dominicana, conocida por sus playas y su turismo.",
"Al oeste está Haití, una nación de montañas y una cultura llena de historia.",
"Ambos países comparten territorio, pero tienen idiomas y tradiciones diferentes.",
"En República Dominicana destacan el merengue y la bachata.",
"En Haití destacan sus tambores, carnavales y tradiciones culturales.",
"Sus economías también son diferentes. República Dominicana tiene un importante sector turístico.",
"Haití enfrenta grandes desafíos económicos y sociales.",
"Haití declaró su independencia en 1804. República Dominicana en 1844.",
"Dos países, una isla y dos historias. ¿Cuál de estas diferencias te sorprendió más?"]
voice = sys.argv[1] if len(sys.argv) > 1 else 'em_alex'
for i, t in enumerate(LINES):
    s, sr = K.create(t, voice=voice, speed=0.97, lang='es')
    sf.write(f'narracion/_l{i:02d}.wav', s, sr); print(i, round(len(s) / sr, 2), sr)
