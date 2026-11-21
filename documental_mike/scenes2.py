import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from art import *
from env import *
from engine import *
from scenes1 import chick, FR_TINT, smoke, birds

TL=None
def set_timeline(tl):
    global TL; TL=tl

class YardWorld:
    """patio de granja en primer plano (atardecer / amanecer)."""
    def __init__(s,tod):
        s.tod=tod
        s.sky=sky_layer(tod['sky'],sun=tod['sun'])
        s.clouds=cloud_layer(3600,tod.get('cseed',4),7,500,1500,tod['cloud'],tod['cloud2'],1.6,225)
        f=Cv(WW,WH,1)
        hill_poly(f,WW,2080,60,tod.get('hseed',3),tod['hill1'],tod['hill1b'],2500,freqs=(1.0,2.2,4.4))
        hill_poly(f,WW,2200,36,tod.get('hseed',3)+4,tod['hill2'],tod['hill2b'],2500,freqs=(1.5,3.3))
        s.far=f.im
        m=Cv(WW,WH,1)
        grad_fill(m.im,[(0,2260),(WW,2260),(WW,WH),(0,WH)],tod['grass_top'],tod['grass_bot']); m.d=ImageDraw.Draw(m.im)
        for tx,ty,ts,sd in ((1900,2420,1.9,2),(1620,2380,1.1,6),(2060,2400,1.2,5)): tree(m,tx,ty,ts,sd,leaf=tod['leaf'],leaf2=tod['leaf2'])
        silo(m,1180,2430,2.0,col=tod['silo'])
        barn(m,520,2480,2.6,body=tod['barn'],loft_light=tod.get('loft',False))
        fence(m,880,2160,2540,1.7,col=tod['fence'],shade=tod['fenceshade'])
        m.blob([(0,2760),(500,2620),(1500,2640),(2160,2760),(2160,3300),(1500,3420),(500,3380),(0,3300)],tod['dirt'],None,0,10)
        grass_tufts(m,0,WW,2560,2700,60,tod['tuft'],tod['tuft2'],sc=1.6)
        grass_tufts(m,0,WW,3300,3800,60,tod['tuft'],tod['tuft2'],sc=2.4)
        for x in (1900,2020): haybale(m,x,2560,1.3)
        s.main=m.im
        s.tint=tod['tint']
    def base(s,fr,t):
        fr.layer(s.sky,.2); fr.layer(s.clouds,.3,off=((t*12)%700-350,0)); fr.layer(s.far,1.0); fr.layer(s.main,1.0)
    def finish(s,fr):
        im=fr.rgb().convert('RGBA'); r,g,b,a=s.tint; im=Image.alpha_composite(im,Image.new('RGBA',(OW,OH),(r,g,b,a))); return im.convert('RGB')

DUSK=dict(sky=[(0,(52,48,102)),(0.22,(120,86,128)),(0.38,(236,128,92)),(0.5,(252,176,98)),(1,(255,196,120))],sun=(520,1980,130,(255,196,120)),
 cloud=(255,196,168),cloud2=(180,110,120),hill1=(96,78,116),hill1b=(130,92,110),hill2=(70,86,80),hill2b=(96,100,70),
 grass_top=(118,126,66),grass_bot=(90,104,52),leaf=(62,86,54),leaf2=(86,104,60),silo=(176,176,184),barn=(158,50,44),fence=(236,214,190),fenceshade=(140,110,96),
 dirt=(168,124,86,255),tuft=(150,130,60,255),tuft2=(100,110,50,255),tint=(255,140,60,38),loft=False)
DAWN=dict(sky=[(0,(86,112,170)),(0.2,(150,160,200)),(0.36,(246,186,170)),(0.5,(255,214,160)),(1,(255,226,180))],sun=(1500,2040,110,(255,226,170)),
 cloud=(255,226,214),cloud2=(206,170,190),hill1=(138,138,180),hill1b=(178,160,184),hill2=(110,140,130),hill2b=(150,160,118),
 grass_top=(132,156,86),grass_bot=(104,130,66),leaf=(80,116,66),leaf2=(106,142,76),silo=(200,204,210),barn=(172,54,46),fence=(246,236,216),fenceshade=(150,130,108),
 dirt=(184,148,104,255),tuft=(160,158,80,255),tuft2=(112,134,62,255),tint=(255,196,170,30),loft=False,cseed=9,hseed=8)

def walkphase(x): return x/38.0

class Scene2:
    """10 de septiembre: el granjero lleva a Mike; después Mike camina ya sin cabeza (sin imágenes gráficas)."""
    def __init__(s):
        s.w=YardWorld(DUSK)
    def cam(s,t,D):
        p=t/D
        if p<.50: return cam_lerp((820,2760,1.25),(1500,2740,1.2),p/.5)
        if p<.66: return cam_lerp((1500,2740,1.2),(1150,2500,1.05),(p-.5)/.16)
        return cam_lerp((1150,2500,1.05),(1010,2900,1.55),(p-.66)/.34)
    def render(s,t,D):
        p=t/D; fr=Frame(s.cam(t,D)); FR_TINT[0]=(1.0,.82,.74)
        s.w.base(fr,t); birds(fr,t,3,1500,5)
        # gallinas de fondo (quietas, picoteando)
        for i,(x0,y0,sc,pi) in enumerate([(300,3020,1.2,1),(640,3180,1.3,2),(1760,3040,1.25,3),(1980,3200,1.3,0)]):
            peck=max(0,math.sin(t*2.3+i*1.9)); chick(fr,x0+20*math.sin(t*.5+i),y0,sc,HENS[pi],head=True,neck=.1+1.0*peck,flip=(-1 if i%2 else 1),phase=t*3,walk=.0)
        # --- granjero
        fx0=700; fx1=2500; pa=.12; pb=.50
        if p<pb:
            u=clamp((p-pa)/(pb-pa)); fx=lerp(fx0,fx1,u*u*(3-2*u)*0.9+u*0.1) if p>pa else fx0
            walking=(pa<p<pb)
            ph=t*6.5
            mike_c=lambda cv,T: chicken(cv,*T(110,-300),sc=1.25*s._k,pal=MIKE,head=True,flip=1,neck=-.15,phase=0,walk=0,shadow=False,tail_up=.6)
            def draw(cv,ax,ay,k,fx=fx):
                s._k=k*1.0
                farmer(cv,ax,ay,sc=2.35*k*.5*2/2/1.0 if False else 1.0*k,flip=1,walk=.6 if walking else .0,phase=ph,bob=-4*abs(math.sin(ph)) if walking else 0,
                       arm_f=(.9,1.5) if p>pa else (.2,.4),arm_b=(-.3,.1),mid=(lambda cv_,T: chicken(cv_,*T(60,-250),sc=.62*k,pal=MIKE,head=True,flip=1,neck=-.1,shadow=False,tail_up=.5)) if p>pa+.02 else None)
            # el pollo con cabeza en el suelo hasta que el granjero lo toma
            if p<=pa+.02: chick(fr,fx+330,3060,1.5,MIKE,head=True,phase=t*5,walk=.0,neck=.15+.6*max(0,math.sin(t*2)),flip=-1)
            fr.sprite(lambda cv,ax,ay,k,fx=fx: farmer(cv,ax,ay,sc=k*1.55,flip=1,walk=.6 if walking else .0,phase=ph,bob=-5*abs(math.sin(ph)) if walking else 0,
                       arm_f=(.35,1.35) if p>pa+.02 else (.15,.5),arm_b=(-.25,.1),
                       mid=(lambda cv_,T: chicken(cv_,*T(46,-262),sc=k*.78,pal=MIKE,head=True,flip=1,neck=-.2,shadow=False,tail_up=.5)) if p>pa+.02 else None),
                     fx,3110,l=300,u=1050,r=300,d=60,tint=FR_TINT[0])
        # --- Mike sin cabeza regresa caminando
        if p>.68:
            u=clamp((p-.68)/.30); mx=lerp(1760,1060,smooth(u)); wk=1-smooth(clamp((u-.8)/.2))
            fl=-1
            chick(fr,mx,3080,1.5,MIKE,head=False,phase=t*6,walk=.55*wk,neck=.12+.03*math.sin(t*3),flip=fl,bob=-4*abs(math.sin(t*6))*wk,wob=.05*math.sin(t*2.3))
        im=s.w.finish(fr)
        return im

class Scene3b:
    """Al día siguiente: amanecer, el granjero descubre que Mike sigue vivo."""
    def __init__(s): s.w=YardWorld(DAWN)
    def cam(s,t,D): return cam_lerp((1000,2900,1.15),(1180,2820,1.5),t/D)
    def render(s,t,D):
        p=t/D; fr=Frame(s.cam(t,D)); FR_TINT[0]=(1.0,.92,.86)
        s.w.base(fr,t); birds(fr,t,4,1400,9)
        for i,(x0,y0,sc,pi) in enumerate([(300,3020,1.2,1),(1900,3060,1.25,3),(2020,3200,1.3,0)]):
            peck=max(0,math.sin(t*2.1+i*2.2)); chick(fr,x0,y0,sc,HENS[pi],head=True,neck=.1+1.0*peck,flip=(-1 if i%2 else 1),phase=t,walk=0)
        mx=1480+30*math.sin(t*.8); 
        chick(fr,mx,3100,1.55,MIKE,head=False,phase=t*4,walk=.0 if abs(math.cos(t*.8))<.25 else .5,neck=.12,flip=-1 if math.cos(t*.8)<0 else 1,wob=.05*math.sin(t*2.4),bob=-3*abs(math.sin(t*5)))
        # granjero entra, se detiene y se lleva la mano al sombrero
        u=smooth(clamp(p/.55)); fx=lerp(-150,820,u); walking=p<.55
        ph=t*6
        reach=(100,-120) if p>.62 else None
        fr.sprite(lambda cv,ax,ay,k: farmer(cv,ax,ay,sc=k*1.55,flip=1,walk=.6 if walking else 0,phase=ph,bob=-5*abs(math.sin(ph)) if walking else 0,
                  arm_f=(.35,.45) if p<.6 else (2.3,2.7),arm_b=(-.25,.1),look=0.0,mouth=1 if p>.6 else 0),fx,3110,l=300,u=1050,r=300,d=60,tint=FR_TINT[0])
        return s.w.finish(fr)
