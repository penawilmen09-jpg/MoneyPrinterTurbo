"""Genera la narración con ElevenLabs (voz fija) + alineación por carácter."""
import base64, json, os, sys, requests
VOICE_ID = "851ejYcv2BoNPjrkw93G"
OUT = sys.argv[1]
TEXT = ("Una noche, un hombre recibió una llamada telefónica de su propio número… "
 "pero lo que escuchó al contestar lo dejó completamente aterrorizado. "
 "Al principio pensó que era una broma. Miró la pantalla y comprobó que el número era exactamente el suyo. "
 "Decidió contestar. "
 "Del otro lado escuchó su propia voz, susurrando desesperadamente: “No salgas de casa esta noche”. "
 "Confundido, preguntó quién estaba hablando. "
 "Pero la llamada se cortó. "
 "Unos segundos después, recibió un mensaje desde ese mismo número: “Mira por la ventana”. "
 "Cuando se acercó, vio un automóvil estacionado frente a su casa… y alguien dentro estaba observándolo. "
 "Asustado, llamó a la policía. Cuando llegaron, el automóvil había desaparecido. "
 "Nunca descubrió quién hizo aquella llamada. "
 "Pero desde esa noche, cada vez que su teléfono suena desde un número desconocido, primero mira por la ventana.")
r = requests.post(f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}/with-timestamps?output_format=mp3_44100_128",
    headers={"xi-api-key": os.environ["ELEVENLABS_API_KEY"], "Content-Type": "application/json"},
    json={"text": TEXT, "model_id": "eleven_multilingual_v2",
          "voice_settings": {"stability": 0.5, "similarity_boost": 0.8, "style": 0.25, "use_speaker_boost": True}}, timeout=180)
print(r.status_code)
r.raise_for_status()
d = r.json()
open(f"{OUT}/narration.mp3", "wb").write(base64.b64decode(d["audio_base64"]))
json.dump({"text": TEXT, "alignment": d["alignment"]}, open(f"{OUT}/align.json", "w"), ensure_ascii=False)
