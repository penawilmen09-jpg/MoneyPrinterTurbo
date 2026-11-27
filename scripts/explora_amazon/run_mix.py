import sys
import audio_amz   # fija TOT y ajusta módulos
import remix_audio as R
R.TOT = audio_amz.TOT
R.main(*sys.argv[1:4])
