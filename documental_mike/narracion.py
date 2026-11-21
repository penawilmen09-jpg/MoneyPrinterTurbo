"""Genera la narración en español latino (Piper es_MX-claude, offline) y los tiempos por palabra."""
import json, wave, sys, numpy as np
from piper import PiperVoice, SynthesisConfig
D="/tmp/claude-0/work/voice/vits-piper-es_MX-claude-high/"
OUT="/tmp/claude-0/work/build/"
SPEED=float(sys.argv[1]) if len(sys.argv)>1 else 0.93   # length_scale (<1 = más rápido)
# (escena, texto de subtítulo, [(palabra_subtitulo, lectura_TTS)...] sobreescrituras)
RESP={"1945":"mil novecientos cuarenta y cinco","1947":"mil novecientos cuarenta y siete","10":"diez","18":"dieciocho",
      "Mike":"Maik","Lloyd":"Loid","Olsen":"Ólsen","Phoenix,":"Fínix,"}
SENT=[
(1,"En 1945 ocurrió algo que parecía imposible en una pequeña granja de Colorado, Estados Unidos."),
(1,"Un pollo llamado Mike estaba a punto de convertirse en la cena de una familia."),
(2,"El 10 de septiembre, su dueño, el granjero Lloyd Olsen, intentó cortarle la cabeza."),
(2,"Pero ocurrió algo extraordinario: Mike no murió."),
(3,"La explicación era increíble."),
(3,"El corte había dejado intacta una parte importante del tronco encefálico, que controla funciones esenciales del organismo."),
(3,"Además, un coágulo ayudó a evitar que se desangrara."),
(3,"Al día siguiente, el granjero descubrió que Mike seguía vivo."),
(4,"Desde entonces, comenzó a cuidarlo."),
(4,"Le administraba agua y alimento líquido utilizando un gotero y le limpiaba la garganta con una jeringa para evitar obstrucciones."),
(5,"La noticia se extendió por todo Estados Unidos."),
(5,"Mike se convirtió en una auténtica celebridad y miles de personas pagaban para verlo."),
(5,"Viajó por diferentes ciudades y llegó a aparecer en importantes publicaciones."),
(6,"Pero su increíble historia terminó en marzo de 1947, cuando se encontraba en un motel de Phoenix, Arizona."),
(6,"Mike comenzó a ahogarse durante la noche y no pudieron despejarle la garganta a tiempo."),
(7,"Así terminó la vida del pollo que sobrevivió aproximadamente 18 meses sin cabeza."),
(7,"Su historia sigue sorprendiendo al mundo hasta nuestros días."),
]
v=PiperVoice.load(D+"es_MX-claude-high.onnx",config_path=D+"es_MX-claude-high.onnx.json")
cfg=SynthesisConfig(length_scale=SPEED,noise_scale=0.55,noise_w_scale=0.7)
SR=22050; T0=1.8; cur=T0; audio=[]; items=[]
def trim(x,th=0.006):
    idx=np.where(np.abs(x)>th)[0]
    return x[max(idx[0]-int(.03*SR),0):idx[-1]+int(.08*SR)]
for i,(sc,txt) in enumerate(SENT):
    words=txt.split(); tts=[]; groups=[]
    for w in words:
        r=RESP.get(w, RESP.get(w.rstrip(",.:"),w)+("" if w[-1] not in ",.:" else w[-1]) if w.rstrip(",.:") in RESP else w)
        groups.append(len(r.split())); tts.append(r)
    chunks=list(v.synthesize(" ".join(tts).replace(" Estados Unidos.", " Estados Unidos."),cfg))
    x=np.concatenate([c.audio_float_array for c in chunks])
    ph=[p for c in chunks for p in c.phonemes]
    # fonemas por palabra TTS (separadas por ' '), puntuación pesa como pausa
    wp=[];n=0;cur_w=[]
    for p in ph:
        if p==' ':
            wp.append(cur_w);cur_w=[]
        else: cur_w.append(p)
    wp.append(cur_w)
    wt=[sum(1 for p in g if p not in ',.:;')+ (6 if any(p in ',:;' for p in g) else 0)+(8 if '.' in g else 0) for g in wp]
    if len(wt)!=sum(groups): wt=[1]*sum(groups)
    k=0;ww=[]
    for g in groups: ww.append(sum(wt[k:k+g]));k+=g
    full=x; x=trim(x); lead=(len(full)-len(full))  # trim inicio
    idx=np.where(np.abs(full)>0.006)[0]; lead=max(idx[0]-int(.03*SR),0)/SR
    dur=len(x)/SR; tot=sum(ww); acc=0; wl=[]
    for w,wgt in zip(words,ww):
        a=cur+dur*acc/tot; acc+=wgt; b=cur+dur*acc/tot; wl.append((w,round(a,3),round(b,3)))
    items.append(dict(scene=sc,text=txt,start=round(cur,3),end=round(cur+dur,3),words=wl))
    audio.append((cur,x))
    gap=0.9 if (i+1<len(SENT) and SENT[i+1][0]!=sc) else 0.5
    if i==len(SENT)-1: gap=0
    cur+=dur+gap
total=cur+4.2   # cola emotiva final
buf=np.zeros(int(total*SR)+SR,dtype=np.float32)
for t,x in audio: s=int(t*SR); buf[s:s+len(x)]+=x
buf/=max(np.abs(buf).max(),1e-6)/0.9
with wave.open(OUT+"voz.wav","wb") as w:
    w.setnchannels(1);w.setsampwidth(2);w.setframerate(SR);w.writeframes((buf[:int(total*SR)]*32767).astype(np.int16).tobytes())
json.dump(dict(total=round(total,3),items=items),open(OUT+"timeline.json","w"),ensure_ascii=False,indent=1)
print("total",round(total,2),"voz hasta",round(cur,2))
for it in items: print(it['scene'],it['start'],it['end'])
