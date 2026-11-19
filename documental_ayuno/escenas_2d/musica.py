"""Genera musica_original.wav (90 s, estéreo, 44.1 kHz) con síntesis aditiva en numpy.
Música original sintetizada por código: sin muestras, sin canciones ni librerías de terceros."""
import numpy as np, wave, sys
SR=44100; D=90; N=SR*D; t=np.arange(N)/SR
rng=np.random.default_rng(7)
def hz(n): return 440*2**((n-69)/12)
def ss(x,a,b): x=np.clip((x-a)/(b-a),0,1); return x*x*(3-2*x)
# intensidad global: intriga -> crecimiento -> pico en riesgos (64-72) -> resolución
inten=np.interp(t,[0,8,40,64,72,82,90],[.30,.40,.62,.85,1.0,.55,.35])
# progresión armónica (cada 8 s): Am | F | Dm | E(7) | Am | F | Dm | E | Am | F | Am
chords=[[45,52,57,60,64],[41,48,57,60,65],[38,50,57,62,65],[40,52,56,59,62],[45,52,57,60,64],[41,48,57,60,65],
        [38,50,57,62,65],[40,52,56,59,62],[45,52,57,60,64],[41,48,57,60,65],[45,52,57,60,64,69]]
bounds=[0,8,16,24,32,40,48,56,64,72,82,90]
L=np.zeros(N);R=np.zeros(N)
for ci,ch in enumerate(chords):
    a,b=bounds[ci],bounds[ci+1]; xf=1.8
    env=ss(t,a-xf/2,a+xf/2)*(1-ss(t,b-xf/2,b+xf/2)); 
    if ci==0: env=1-ss(t,b-xf/2,b+xf/2)
    if not env.any(): continue
    i0=max(0,int((a-2)*SR)); i1=min(N,int((b+2)*SR)); tt=t[i0:i1]; e=env[i0:i1]
    bright=0.35+1.9*inten[i0:i1]
    for ni,n in enumerate(ch):
        f=hz(n); pan=(ni%2)*.6+.2
        for det,sgn in ((0.0,1),(0.6,1),(-0.6,-1)):
            ff=f*2**(det/1200*8)
            ph=2*np.pi*ff*tt+ni
            sig=np.zeros_like(tt)
            for h in range(1,9):
                if ff*h>9000: break
                sig+=np.sin(h*ph)/h*np.exp(-h/(bright*2.2))
            amp=.05*(1.3 if n<48 else 1)
            L[i0:i1]+=sig*e*amp*(1-pan*.5); R[i0:i1]+=sig*e*amp*(.5+pan*.5)
    # vibrato lento de intensidad
trem=1+.08*np.sin(2*np.pi*.12*t)*inten
L*=trem;R*=trem
# subgrave en A1 con pulso respiratorio
sub=np.sin(2*np.pi*55*t)*.10*(0.5+0.5*np.sin(2*np.pi*t/8-1.2))*ss(t,2,6)
L+=sub;R+=sub
# latido "lub-dub" desde 8 s hasta 72 s, más rápido y fuerte al acercarse a los riesgos
def thump(t0,amp):
    i=int(t0*SR); n=int(.35*SR)
    if i+n>=N: return
    tt=np.arange(n)/SR; k=np.sin(2*np.pi*(52+30*np.exp(-tt*30))*tt)*np.exp(-tt*11)*amp
    L[i:i+n]+=k;R[i:i+n]+=k
tb=8.0
while tb<74:
    per=np.interp(tb,[8,40,64,72],[1.35,1.1,.85,.7]); a=np.interp(tb,[8,40,64,72,74],[.10,.16,.28,.34,0])
    thump(tb,a); thump(tb+per*.28,a*.65); tb+=per
# destellos agudos (campanitas) al inicio de cada escena
for i,b in enumerate(bounds[:-1]):
    f=hz([81,84,76,79,81,88,76,83,86,81,93][i]); n=int(3.2*SR); tt=np.arange(n)/SR
    s=(np.sin(2*np.pi*f*tt)+.4*np.sin(2*np.pi*f*2.01*tt))*np.exp(-tt*1.6)*.025*(0.6+inten[int(b*SR)])
    j=int((b+.25)*SR); L[j:j+n]+=s[:N-j]; R[j:j+n]+=s[::-1][:N-j]*0+s[:N-j]*.8
# ruido filtrado (whoosh de transición y riser antes de los riesgos)
def lp(x,k): 
    c=np.cumsum(np.insert(x,0,0)); y=(c[k:]-c[:-k])/k; return np.concatenate([np.zeros(k-1),y])
noise=rng.standard_normal(N)
air=lp(noise,40)  # ruido oscuro
for b in bounds[1:-1]:
    g=np.exp(-((t-b)/.35)**2)*.05; L+=air*g;R+=air*g
ris=ss(t,56,64)*(1-ss(t,64,64.4))*.09; L+=air*ris;R+=air*ris
hit=np.exp(-np.clip(t-64,0,None)*3)*(t>=64)*.25; L+=np.sin(2*np.pi*38*t)*hit;R+=np.sin(2*np.pi*38*t)*hit
# aire sutil continuo (ambiente)
amb=lp(noise,200)*.9*(0.4+inten); L+=amb*.05;R+=amb*.05
# fundido inicial/final
fade=ss(t,0,2.0)*(1-ss(t,86,90)); L*=fade;R*=fade
# normalizar: pico -10 dBFS (la voz se agregará encima; bajar más en CapCut si hace falta)
m=max(abs(L).max(),abs(R).max()); g=10**(-10/20)/m; L*=g;R*=g
x=np.stack([L,R],1); pcm=(np.clip(x,-1,1)*32767).astype('<i2')
with wave.open(sys.argv[1],'wb') as w: w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR);w.writeframes(pcm.tobytes())
rms=20*np.log10(np.sqrt((x**2).mean())); print(f"ok {D}s, RMS {rms:.1f} dBFS")
