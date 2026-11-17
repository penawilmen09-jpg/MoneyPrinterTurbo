# Documental animado 2D — Así fue como se hundió el Titanic (60 s)
Pipeline 100 % gratuito: Python (Pillow + numpy) dibuja cada fotograma 2D por capas; el audio se sintetiza con numpy; FFmpeg monta el MP4.

    python3 render.py     # 1800 fotogramas -> build/video_mudo.mp4
    python3 audio.py      # música instrumental + efectos -> build/audio.wav
    ffmpeg -i build/video_mudo.mp4 -i build/audio.wav -c:v libx264 -crf 23 -c:a aac -t 60 ASI_FUE_COMO_SE_HUNDIO_EL_TITANIC.mp4

Salida: 1080x1920, 30 fps, H.264 + AAC, 60,000 s. Fuentes: FUENTES_HISTORICAS.txt
