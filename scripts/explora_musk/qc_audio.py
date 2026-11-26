import wave, numpy as np, sys
import words as W
d=sys.argv[1]; al=sys.argv[2]
def rd(p):
    w=wave.open(p); x=np.frombuffer(w.readframes(w.getnframes()),'<i2').astype(float).reshape(-1,2)/32768; return x.mean(1)
v=rd(d+'/stem_voice.wav'); m=rd(d+'/stem_music_ducked.wav'); s=rd(d+'/stem_sfx_ducked.wav')
ws=W.load(al); sr=44100; rows=[]
for w,a0,e0 in ws:
    a,b=int(a0*sr),int(e0*sr); r=lambda x: np.sqrt((x[a:b]**2).mean())+1e-9
    rows.append((20*np.log10(r(v)/r(m)),20*np.log10(r(v)/r(s)),w,round(a0,2)))
print('voz/música media: %.1f dB ; voz/sfx media: %.1f dB'%(np.mean([r[0] for r in rows]),np.mean([r[1] for r in rows])))
print('peores vs música:',[(round(x[0],1),x[2],x[3]) for x in sorted(rows)[:5]])
print('peores vs sfx:',[(round(x[1],1),x[2],x[3]) for x in sorted(rows,key=lambda x:x[1])[:5]])
print('palabras con voz < música:',sum(1 for r in rows if r[0]<0),'/',len(rows),' ; voz < sfx:',sum(1 for r in rows if r[1]<0))
