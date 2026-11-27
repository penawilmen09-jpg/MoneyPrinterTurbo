#!/bin/bash
# masterización: limitador + loudnorm en dos pasadas (ganancia lineal, sin bombeo)
P=$1; OUT=$2
M=$(ffmpeg -hide_banner -nostats -i $P -af "alimiter=limit=0.89:attack=5:release=60,loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json" -f null - 2>&1 | python3 -c "
import sys,json
t=sys.stdin.read(); j=json.loads(t[t.rindex('{'):t.rindex('}')+1]); print(j['input_i'],j['input_tp'],j['input_lra'],j['input_thresh'],j['target_offset'])")
set -- $M
ffmpeg -y -loglevel error -i $P -af "alimiter=limit=0.89:attack=5:release=60,loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=$1:measured_TP=$2:measured_LRA=$3:measured_thresh=$4:offset=$5:linear=true" -ar 44100 -ac 2 -c:a pcm_s16le $OUT
