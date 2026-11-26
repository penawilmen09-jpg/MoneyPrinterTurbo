# Explora Ciencia 360 — «Tu cerebro puede engañarte sin que lo sepas»

Pipeline autónomo (no modifica el código existente de MoneyPrinterTurbo). Motor 2D procedural con
Pillow + numpy (ya dependencias del proyecto) y FFmpeg; sin servicios de vídeo externos.

    export ELEVENLABS_API_KEY=...            # nunca se imprime
    python3 gen_voice.py ../../storage/explora_ciencia360/audio   # voz oficial 851ejYcv2BoNPjrkw93G + alineación
    python3 compose.py  <dir_render>         # escenas 2D + subtítulos -> video_noaudio.mp4 (4 procesos)
    python3 audio_synth.py <dir_audio>       # música + efectos sintetizados (sin copyright)
    ./mix.sh <narracion.mp3> <music.wav> <sfx.wav> <dir_audio>   # mezcla con ducking + loudnorm -14 LUFS
    python3 qc_audio.py <dir_audio> <alignment.json>

* `script_text.py` — guion aprobado (literal) y Voice ID.
* `scenes_a/b/c.py` — las 7 escenas; `compose.py` — transiciones, subtítulos (también escribe el .srt).
