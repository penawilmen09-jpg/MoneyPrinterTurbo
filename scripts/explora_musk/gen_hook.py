import base64, json, os, sys, requests
from script_text import VOICE_ID, hook_tts, HOOK
out_dir = sys.argv[1]; os.makedirs(out_dir, exist_ok=True)
key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
if not key: sys.exit("falta ELEVENLABS_API_KEY")
text = hook_tts()
url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}/with-timestamps?output_format=mp3_44100_128"
payload = {"text": text, "model_id": "eleven_multilingual_v2", "language_code": "es",
           "voice_settings": {"stability": 0.5, "similarity_boost": 0.75, "style": 0.0, "use_speaker_boost": True, "speed": 1.1}}
r = requests.post(url, json=payload, headers={"xi-api-key": key, "Content-Type": "application/json"}, timeout=240)
print("status", r.status_code)
if r.status_code != 200:
    print(r.text[:300].replace(key, "<hidden>")); sys.exit(1)
d = r.json()
open(os.path.join(out_dir, "gancho.mp3"), "wb").write(base64.b64decode(d["audio_base64"]))
json.dump({"text": text, "shown": HOOK, "alignment": d["alignment"], "voice_id": VOICE_ID, "speed": 1.1}, open(os.path.join(out_dir, "gancho_alignment.json"), "w"), ensure_ascii=False)
print("ok")
