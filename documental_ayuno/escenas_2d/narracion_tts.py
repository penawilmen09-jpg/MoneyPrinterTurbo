import re,sys,soundfile as sf,numpy as np
from kokoro_onnx import Kokoro
k=Kokoro("kokoro-v1.0.onnx","voices-v1.0.bin")
G=open('/home/user/MoneyPrinterTurbo/documental_ayuno/guion_completo.txt').read()
sc=re.findall(r"ESCENA (\d+) \[(\d+)-(\d+)s\] (.+)\n(.+)",G)
voice=sys.argv[1]; sp=float(sys.argv[2])
for i,a,b,t,x in sc:
    y,sr=k.create(x,voice=voice,speed=sp,lang="es")
    sf.write(f"{voice}_{int(i):02d}.wav",y,sr); print(i,f"{len(y)/sr:.2f}s of {int(b)-int(a)}s",sr)
