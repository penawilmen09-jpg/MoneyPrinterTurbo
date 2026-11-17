#!/usr/bin/env bash
# Pipeline completo: fotogramas 2D (Canvas/Chromium) -> audio sintetizado -> MP4 H.264/AAC 1080x1920 30fps
set -e; cd "$(dirname "$0")"
[ "$SKIP_RENDER" = 1 ] || node render.js
python3 audio.py
ffmpeg -y -loglevel error -framerate 30 -i tmp/frames/%05d.jpg -i tmp/audio.wav \
  -c:v libx264 -preset medium -crf 21 -maxrate 14M -bufsize 28M -pix_fmt yuv420p -profile:v high -level 4.2 -r 30 -g 60 \
  -c:a aac -b:a 192k -ar 44100 -ac 2 -movflags +faststart -t 60 output/chapo_fuga_60s.mp4
