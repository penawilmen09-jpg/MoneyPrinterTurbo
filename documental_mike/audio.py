"""Música original (sintetizada), ambiente y efectos + mezcla con la voz. Todo generado localmente: sin derechos de autor."""
import json, wave, sys, subprocess, math
import numpy as np
SR=44100
TL=json.load(open('/tmp/claude-0/work/build/timeline.json')); it=TL['items']; TOTAL=TL['total']
def bound(i): return (it[i-1]['end']+it[i]['start'])/2
B=[0,bound(2),bound(4),bound(7),bound(8),bound(10),bound(11),bound(12),bound(13),bound(14),bound(15),TOTAL]
rng=np.random.default_rng(7); N=int(TOTAL*SR)+SR
def ffilt(x,lo=None,hi=None):
    X=np.fft.rfft(x); f=np.fft.rfftfreq(len(x),1/SR); m=np.ones_like(f)
    if lo: m*=1/(1+(lo/np.maximum(f,1))**4)
    if hi: m*=1/(1+(f/hi)**4)
    return np.fft.irfft(X*m,len(x))
def sm(t,a,b): return np.clip((t-a)/(b-a),0,1)
def tt(n): return np.arange(n)/SR
def env_region(n,t0,t1,fi=1.5,fo=1.5):
    t=tt(n); return sm(t,t0,t0+fi)*(1-sm(t,t1-fo,t1))
def noise(n): return rng.normal(0,1,n)
mus=np.zeros(N); sfx=np.zeros(N)
def add(buf,sig,t0,g=1.0):
    s=int(t0*SR)
    if s<0: sig=sig[-s:]; s=0
    e=min(len(buf),s+len(sig))
    if e>s: buf[s:e]+=sig[:e-s]*g
def midi(m): return 440*2**((m-69)/12)
def piano(f,d=2.2,v=1.0):
    n=int(d*SR); t=np.arange(n)/SR; y=np.zeros(n)
    for h,a in ((1,1),(2,.5),(3,.3),(4,.18),(5,.1),(6,.05)): y+=a*np.sin(2*np.pi*f*h*t+h*.3)*np.exp(-t*(2.2+h*1.1)/ (1+f/800))
    y*=np.minimum(1,t/.004); return y*v
def pad(f,d,v=1.0,det=.004):
    n=int(d*SR); t=np.arange(n)/SR; y=np.zeros(n)
    for dd in (-det,0,det):
        for h,a in ((1,1),(2,.4),(3,.25),(4,.12),(5,.07)): y+=a*np.sin(2*np.pi*f*(1+dd)*h*t+rng.uniform(0,6))/ (1+0)
    e=np.minimum(1,t/(d*.35))*np.minimum(1,(d-t)/(d*.35)); return y*e*v/6
def bassnote(f,d,v=1.0):
    n=int(d*SR); t=np.arange(n)/SR; y=(np.sin(2*np.pi*f*t)+.4*np.sin(4*np.pi*f*t))*np.exp(-t*3.2)*np.minimum(1,t/.01); return y*v
def pulse(t0,g=1):  # latido grave
    for dt,gg in ((0,1),(.32,.65)): add(mus,bassnote(48,.5,1)*gg*g,t0+dt)
def drum(kind,t0,g=1):
    if kind=='k':
        n=int(.25*SR); t=np.arange(n)/SR; add(mus,np.sin(2*np.pi*(110*np.exp(-t*18)+45)*t)*np.exp(-t*14)*g,t0)
    elif kind=='s':
        n=int(.2*SR); t=np.arange(n)/SR; y=ffilt(noise(n),1500,9000)*np.exp(-t*24)+.3*np.sin(2*np.pi*190*t)*np.exp(-t*30); add(mus,y*.6*g,t0)
    else:
        n=int(.06*SR); t=np.arange(n)/SR; add(mus,ffilt(noise(n),6000,None)*np.exp(-t*70)*.25*g,t0)
# ================= MÚSICA
A=lambda x:x
# 1) Suspenso suave S1–S4: 0 – B[5]
chords=[(45,52,57,60),(41,48,53,57),(43,50,55,59),(40,47,52,56)]  # Am, F, G, Em graves
t=0.0; i=0; end1=B[5]
while t<end1:
    ch=chords[i%4]; d=8.0
    for m in ch: add(mus,pad(midi(m),d+1.5,.55),t,1.0)
    t+=d; i+=1
# latido de tensión creciente (S2: del evento) y calma en S3b
k=B[1]+3.0
while k<B[2]-1:
    pulse(k,.8*sm(k,B[1]+3,B[1]+10)); k+=1.25
# campanilla sparse
for t_ in np.arange(2.0,end1-2,2.7):
    m=[81,84,88,76,79][int(t_*1.7)%5]
    if not (B[3]<t_<B[3]+0.5): add(mus,piano(midi(m),3.0,.35*(0.5+0.5*math.sin(t_))),t_)
# subida de tensión en el evento (final S2)
ev=it[3]['start']-0.6; n=int(3.0*SR); tn=np.arange(n)/SR
riser=ffilt(noise(n),300,4000)*(tn/3)**2; add(mus,riser*.5,ev-1.0)
for m,tm in ((57,ev+2.2),(64,ev+2.5)): pass
# 2) Fama intensa S5: B[5] – B[8]
bpm=116; beat=60/bpm; t=B[5]; bar=0
prog=[(48,55,64),(53,57,65),(55,59,67),(48,55,64)]
mel=[72,74,76,79,76,74,72,67,69,71,72,76,74,72,71,67]
while t<B[8]-beat:
    ch=prog[bar%4]
    for b in range(4):
        tb=t+b*beat
        add(mus,bassnote(midi(ch[0]-12 if b%2==0 else ch[1]-12),beat*.9,.8),tb)
        if b%2==1:
            for m in ch: add(mus,piano(midi(m+12),.5,.18),tb)
        drum('k' if b%2==0 else 's',tb,.7 if b%2==0 else .5)
        drum('h',tb+beat/2,.5)
        add(mus,piano(midi(mel[(bar*4+b)%16]+0),.9,.34),tb)
    t+=4*beat; bar+=1
# 3) S6 sombrío: B[8] – B[10]
chords2=[(38,45,50,53),(34,41,46,50),(36,43,48,52),(33,40,45,49)]
t=B[8]-1; i=0
while t<B[10]:
    for m in chords2[i%4]: add(mus,pad(midi(m),8.5,.5),t)
    t+=7; i+=1
for tm,m in zip(np.arange(B[8]+1.5,B[10]-1,2.9),[62,65,69,64,62,60,57,62]*3): add(mus,piano(midi(m),3.2,.3),tm)
# 4) Final emotivo S7: B[10] – fin
chords3=[(41,53,57,60,65),(36,52,55,60,64),(38,50,57,62,65),(34,50,53,58,62),(41,53,57,60,65)]
t=B[10]-1.0; i=0
while t<TOTAL:
    for m in chords3[min(i,4)]: add(mus,pad(midi(m),7.5,.75,.006),t)
    t+=6; i+=1
arp=[65,69,72,77,72,69,67,70,74,79,74,70]
for j,tm in enumerate(np.arange(B[10]+.5,TOTAL-2,1.0)): add(mus,piano(midi(arp[j%12]+0),2.8,.42),tm)
# melodía final lenta
for tm,m in zip((B[10]+3,B[10]+7,B[10]+10.5,B[10]+14,TOTAL-9,TOTAL-6),(77,76,72,74,77,81)): add(mus,piano(midi(m),4.5,.5),tm)
# envolvente de intensidad por sección (la fama más fuerte; el final emotivo cálido)
t=tt(N); lev=np.zeros(N)
lev+=0.55*env_region(N,0,B[5],2.5,1.2)+1.0*env_region(N,B[5]-.3,B[8],.8,1.0)+0.6*env_region(N,B[8]-1,B[10],2.0,1.5)+0.85*env_region(N,B[10]-1,TOTAL+3,3.0,3.5)
mus*=lev
# ================= AMBIENTE Y EFECTOS
def ambient(kind,t0,t1,g=1.0,fi=2.0,fo=2.0):
    n=N
    if kind=='wind':
        x=ffilt(noise(n),120,900)*(0.6+0.4*np.sin(2*np.pi*t*.11+1)); x=x*(0.7+0.3*np.sin(2*np.pi*t*.23))
    elif kind=='crickets':
        x=np.zeros(n); 
        for f0,ph in ((4200,0),(4650,1.1)):
            gate=(np.sin(2*np.pi*t*(31+ph*2))>.2)*(np.sin(2*np.pi*t*(2.1+ph*.3)+ph)>-.2)
            x+=np.sin(2*np.pi*f0*t)*gate*.5
        x=x*.5
    elif kind=='crowd':
        x=ffilt(noise(n),250,2600)*(0.6+0.4*np.abs(np.sin(2*np.pi*t*3.7))+0.3*np.sin(2*np.pi*t*.8)**2)
    elif kind=='engine':
        f=48+4*np.sin(2*np.pi*t*.7); x=(np.sin(2*np.pi*np.cumsum(f)/SR)+.5*np.sin(4*np.pi*np.cumsum(f)/SR)+.25*np.sin(6*np.pi*np.cumsum(f)/SR))*(0.8+0.2*np.sin(2*np.pi*t*7))+.3*ffilt(noise(n),60,500)
        x*=.5
    elif kind=='buzz':
        x=np.sin(2*np.pi*120*t)*.4+np.sin(2*np.pi*240*t)*.2+.05*noise(n)
    elif kind=='room':
        x=ffilt(noise(n),40,300)*.5
    sfx[:]+=x*env_region(n,t0,t1,fi,fo)*g
ambient('wind',0,B[3]+1,.12,1.5,2); ambient('wind',B[3]-1,B[4]+1,.07,2,2); ambient('wind',B[10]-1,TOTAL+2,.10,2,3)
ambient('crickets',B[1]-1,B[2]+1,.028,2,2); ambient('crickets',B[4]-1,B[5]+1,.02,2,2); ambient('crickets',B[9]-1,B[10]+1,.03,1.5,2); ambient('crickets',B[10],TOTAL,.015,3,3)
ambient('crowd',B[6]-1,B[7]+1,.18,1.2,1.2); ambient('engine',B[7]-.5,B[8]+.5,.16,.5,.8); ambient('engine',B[8]-.5,B[8]+(B[9]-B[8])*.62,.14,.8,1.5)
ambient('buzz',B[8]+(B[9]-B[8])*.5,B[10],.025,2,1.5); ambient('room',B[9]-1,B[10],.1,1,2)
def chirp(t0,f0=3200,g=1):
    n=int(.14*SR); tn=np.arange(n)/SR; ph=2*np.pi*np.cumsum(f0+900*np.sin(2*np.pi*22*tn)*np.exp(-tn*8))/SR
    add(sfx,np.sin(ph)*np.exp(-((tn-.06)/.04)**2)*.16*g,t0)
def cluck(t0,g=1,f0=520):
    for k in range(rng.integers(2,5)):
        n=int(.11*SR); tn=np.arange(n)/SR; f=f0*np.exp(-tn*5)*(1+.2*np.sin(2*np.pi*30*tn)); y=np.sin(2*np.pi*np.cumsum(f)/SR)+.5*np.sin(4*np.pi*np.cumsum(f)/SR)
        y=ffilt(y*(1+.3*noise(n)),400,3200)*np.exp(-tn*22)*np.minimum(1,tn/.005); add(sfx,y*.35*g,t0+k*.16)
def click(t0,g=1):
    n=int(.05*SR); tn=np.arange(n)/SR; add(sfx,ffilt(noise(n),1200,8000)*np.exp(-tn*160)*.5*g,t0)
def whoosh(t0,d=.5,g=1):
    n=int(d*SR); tn=np.arange(n)/SR; y=ffilt(noise(n),300,4000)*np.sin(np.pi*tn/d)**2; add(sfx,y*.35*g,t0)
def flash(t0,g=1): click(t0,g); add(sfx,ffilt(noise(int(.25*SR)),3000,None)*np.exp(-tt(int(.25*SR))*18)*.25*g,t0+.02)
def plink(t0,g=1):
    n=int(.18*SR); tn=np.arange(n)/SR; add(sfx,np.sin(2*np.pi*(900*np.exp(-tn*8)+500)*tn)*np.exp(-tn*28)*.35*g,t0)
# aves S1 y amanecer
for t_ in np.sort(rng.uniform(1,B[1]-1,16)): chirp(t_,rng.uniform(2800,4200),.8)
for t_ in np.sort(rng.uniform(B[2]+.5,B[3]-.3,7)): chirp(t_,rng.uniform(3000,4400),.9)
for t_ in np.sort(rng.uniform(B[10]+.5,TOTAL-3,8)): chirp(t_,rng.uniform(2800,4000),.5)
# gallinas
for t_ in np.sort(rng.uniform(3,B[1]-1,9)): cluck(t_,.8,rng.uniform(450,620))
for t_ in np.sort(rng.uniform(B[1]+.5,B[1]+(B[2]-B[1])*.45,5)): cluck(t_,.7,rng.uniform(450,620))
for t_ in np.sort(rng.uniform(B[2]+.2,B[3],3)): cluck(t_,.6)
cluck(B[1]+(B[2]-B[1])*.76,.9)
# pasos suaves de Mike? (S2) y papeles/flash
for i in range(4): whoosh(B[5]+.35+i*.62-.05,.4,1.0); flash(B[5]+.35+i*.62+.45,.7)
for i in range(3): flash(B[7]+.45+i*1.25,1.0); whoosh(B[7]+.45+i*1.25-.15,.35,.7)
# gotas del gotero (S4)
for k in range(0,40):
    tm=B[4]+(k+.55)/.9
    if tm<B[5]-.5 and tm<it[9]['words'][[w for w,_,_ in it[9]['words']].index('jeringa')][1]-.4: plink(tm,.9)
tj=[a for w,a,b in it[9]['words'] if w.startswith('jeringa')][0]
for k in range(3): whoosh(tj+k*1.1,.5,.5)
# reloj (S4 y S6b)
for tm in np.arange(B[4],B[5],1.0): click(tm,.35)
for tm in np.arange(B[9],B[10],1.0): click(tm,.25)
# campana final suave (S6b cierre): una nota grave
add(mus,piano(midi(45),6.0,.5),B[10]-3.5)
# ================= VOZ + MEZCLA
w=wave.open('/tmp/claude-0/work/build/voz.wav'); v=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(np.float32)/32768
v=np.interp(np.arange(int(len(v)*SR/22050))/SR*22050,np.arange(len(v)),v)
voice=np.zeros(N); voice[:len(v)]=v[:N]
# ducking: la música baja cuando hay voz
e=np.abs(voice); k=int(.05*SR); e=np.convolve(e,np.ones(k)/k,'same'); e=np.convolve((e>.02).astype(float),np.ones(int(.35*SR))/int(.35*SR),'same')
duck=1-.62*np.clip(e,0,1)
mus*=duck*.30; sfx*=(1-.25*np.clip(e,0,1))
# reverb suave del estudio sobre la música
def stereo(x,w=.2):
    d=int(.012*SR); L=x.copy(); R=np.roll(x,d); return np.stack([L,R],1)
M=stereo(mus); S=stereo(sfx*1.0); V=np.stack([voice,voice],1)
np.save('/tmp/claude-0/work/build/_m.npy',M.astype(np.float32)); np.save('/tmp/claude-0/work/build/_s.npy',S.astype(np.float32)); np.save('/tmp/claude-0/work/build/_v.npy',V.astype(np.float32))
def wr(name,x):
    x=np.clip(x[:int(TOTAL*SR)],-1,1); 
    with wave.open(name,'wb') as f: f.setnchannels(2); f.setsampwidth(2); f.setframerate(SR); f.writeframes((x*32767).astype(np.int16).tobytes())
wr('/tmp/claude-0/work/build/voz44.wav',V); wr('/tmp/claude-0/work/build/musica.wav',M); wr('/tmp/claude-0/work/build/efectos.wav',S)
print('listo',TOTAL)
