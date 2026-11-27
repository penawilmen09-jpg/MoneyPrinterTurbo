#!/bin/bash
# uso: mix.sh narracion.mp3 music.wav sfx.wav salida_dir
# Mezcla: voz (principal) + música con ducking bajo la voz + efectos con ducking ligero.
set -e
V=$1; M=$2; S=$3; O=$4; D=76.3
CHAIN="
[0:a]aformat=channel_layouts=stereo,aresample=44100,volume=1.5,apad=whole_dur=$D,atrim=0:$D,asplit=3[vo][vk][vs];
[1:a]volume=0.50,atrim=0:$D[m0];
[m0][vk]sidechaincompress=threshold=0.006:ratio=16:attack=8:release=350:makeup=1[md];
[2:a]volume=0.34,atrim=0:$D[s0];
[s0][vs]sidechaincompress=threshold=0.006:ratio=8:attack=5:release=250:makeup=1[sf]"
ffmpeg -y -loglevel error -i "$V" -i "$M" -i "$S" -filter_complex "$CHAIN;
[vo][md][sf]amix=inputs=3:normalize=0:duration=longest,afade=t=out:st=74.9:d=1.4,loudnorm=I=-14:TP=-1.5:LRA=9[mix]" -map "[mix]" -ar 44100 -ac 2 -c:a pcm_s16le "$O/mix.wav"
# stems (para control de calidad)
ffmpeg -y -loglevel error -i "$V" -i "$M" -i "$S" -filter_complex "$CHAIN" \
  -map "[vo]" -c:a pcm_s16le "$O/stem_voice.wav" -map "[md]" -c:a pcm_s16le "$O/stem_music_ducked.wav" -map "[sf]" -c:a pcm_s16le "$O/stem_sfx_ducked.wav"
