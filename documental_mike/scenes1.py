import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from art import *
from env import *
from engine import *

def chick(fr,x,y,sc,pal=MIKE,**kw):
    fr.sprite(lambda cv,ax,ay,k: chicken(cv,ax,ay,sc*k,pal,**kw),x,y,l=300*sc,u=400*sc,r=300*sc,d=30*sc,tint=kw.pop('tint',None) if False else FR_TINT[0])
FR_TINT=[None]

def wander(t,x0,amp,w,ph):
    x=x0+amp*math.sin(w*t+ph); v=amp*w*math.cos(w*t+ph)
    return x,(1 if v>=0 else -1),abs(v)

def smoke(fr,t,x,y,s,col=(235,235,235)):
    for i in range(7):
        u=((t*0.35+i/7.0)%1.0); px=x+u*90*s+math.sin(u*6+i)*14*s; py=y-u*200*s; r=(14+u*40)*s; a=int(150*(1-u))
        fr.sprite(lambda cv,ax,ay,k,r=r,a=a: cv.ell(ax,ay,r*k,r*k,col+(a,)),px,py,l=r+2,u=r+2,r=r+2,d=r+2,ss=1)

def birds(fr,t,n=5,y0=1200,seed=3):
    rnd=random.Random(seed)
    for i in range(n):
        x=(rnd.uniform(0,WW)+t*(60+i*8))%(WW+400)-200; y=y0+rnd.uniform(-200,200)+math.sin(t*1.2+i)*12; fl=math.sin(t*9+i*1.7)
        def f(cv,ax,ay,k,fl=fl): cv.line([(ax-16*k,ay+(-8*fl)*k),(ax,ay+2*k),(ax+16*k,ay+(-8*fl)*k)],3.2*k,(40,36,40,255))
        fr.sprite(f,x,y,l=30,u=30,r=30,d=30,ss=1)

class Scene1:
    name='granja'
    def __init__(s):
        # --- cielo
        sky=sky_layer([(0,(66,104,166)),(0.22,(120,152,194)),(0.36,(238,200,158)),(0.455,(255,218,152)),(1,(255,222,170))],sun=(640,1650,120,(255,236,176)))
        # rayos de sol
        L=Image.new('RGBA',(WW,WH),(0,0,0,0)); d=ImageDraw.Draw(L)
        for i in range(9):
            a0=math.radians(-60+i*14); a1=a0+math.radians(5)
            d.polygon([(640,1650),(640+math.cos(a0)*2600,1650+math.sin(a0)*2600),(640+math.cos(a1)*2600,1650+math.sin(a1)*2600)],fill=(255,230,170,34))
        L=L.filter(ImageFilter.GaussianBlur(14)); sky.alpha_composite(L); s.sky=sky
        s.clouds=cloud_layer(3600,11,9,520,1500,(255,246,230),(246,218,196),1.5,225)
        # --- lejos
        far=Cv(WW,WH,1)
        hill_poly(far,WW,1690,70,5,(150,150,190),(190,176,196),2100,freqs=(1.0,2.3,4.7))
        hill_poly(far,WW,1760,36,9,(128,150,150),(170,170,140),2100,freqs=(1.4,3.1))
        s.far=far.im
        # --- principal
        m=Cv(WW,WH,1)
        m.d.rectangle((0,1780,WW,WH),fill=(120,150,72,255))
        grad_fill(m.im,[(0,1780),(WW,1780),(WW,WH),(0,WH)],(176,170,96),(106,136,62)); m.d=ImageDraw.Draw(m.im)
        vp=(1080,1770); cols=[(222,184,98),(118,150,70),(206,166,84),(96,128,60),(232,196,110),(130,160,76)]
        N=26
        for i in range(N):
            xa=-4200+i*(8400/N); xb=xa+8400/N
            c=cols[i%len(cols)]; c2=tuple(int(v*0.86) for v in c)
            pts=[vp,(xa,WH+40),(xb,WH+40)]
            grad_fill(m.im,[(int(x),int(y)) for x,y in pts],mix(c,(250,214,160),.5),c2,1770,WH)
        m.d=ImageDraw.Draw(m.im)
        # surcos finos
        for i in range(120):
            xa=-4200+i*(8400/120); m.d.line([(vp[0]+(xa-vp[0])*.3,vp[1]+(WH+40-vp[1])*.3),(xa,WH+40)],fill=(80,70,40,30),width=2)
        # setos / líneas de árboles
        for yy,ss_,n,seed in ((1822,.20,26,2),(1900,.30,18,5),(2060,.44,14,8)):
            rnd=random.Random(seed)
            for j in range(n):
                x=rnd.uniform(-50,WW+50)
                if abs(x-1080)<(380 if yy>2000 else 200): continue
                tree(m,x,yy+rnd.uniform(-12,12),ss_,seed+j,leaf=(74,112,60),leaf2=(104,142,74))
        # montículo de la granja
        m.d=ImageDraw.Draw(m.im)
        grad_fill(m.im,[(int(x),int(y)) for x,y in spline([(180,2540),(520,2430),(1080,2410),(1700,2430),(2000,2560),(1700,2680),(1080,2700),(480,2690)],True,10)],(138,168,82),(112,146,68))
        m.d=ImageDraw.Draw(m.im)
        # patio de tierra y camino
        m.blob([(520,2560),(900,2490),(1500,2500),(1800,2580),(1700,2820),(1080,2890),(520,2820)],(180,146,100,255),None,0,10)
        m.blob([(930,2840),(1250,2840),(1700,3840),(520,3840)],(190,156,108,255),None,0,6)
        m.blob([(1000,2860),(1160,2860),(1260,3840),(900,3840)],(200,168,120,255),None,0,6)
        grass_tufts(m,160,2000,2560,2760,50,(96,130,60,255),(130,160,78,255),sc=.8)
        grass_tufts(m,0,WW,3100,3820,70,(180,160,70,255),(120,140,60,255),sc=1.4)
        # edificios
        windmill_tower(m,300,2520,1.0); 
        for tx,ty,ts,sd in ((470,2470,.55,1),(1930,2480,.6,2),(640,2440,.45,3),(1780,2450,.5,4)): tree(m,tx,ty,ts,sd)
        silo(m,1290,2460,1.0); barn(m,980,2470,1.45)
        house(m,1650,2490,1.1); 
        for x in (1180,1300): haybale(m,x,2610,.6)
        fence(m,560,1800,2780,1.0)
        s.main=m.im
        # tinte dorado
        warm=Image.new('RGBA',(WW,WH),(255,196,120,40)); s.warm=warm
        s.look=None
    def cam(s,t):
        if t<10.6: return cam_lerp((1080,1930,1.0),(1070,2300,1.72),t/10.6)
        return cam_lerp((1070,2300,1.72),(1030,2560,2.25),(t-10.6)/7)
    def render(s,t,D):
        fr=Frame(s.cam(t)); FR_TINT[0]=(1.0,.96,.9)
        fr.layer(s.sky,0.15); fr.layer(s.clouds,0.3,off=((t*14)%700-350,0)); fr.layer(s.far,1.0)
        birds(fr,t,5,1250)
        fr.layer(s.main,1.0)
        # molino y humo
        fr.sprite(lambda cv,ax,ay,k: windmill_blades(cv,ax,ay,150*k,t*1.4),300+60,2520-430,l=170,u=170,r=170,d=170,tint=(1,.93,.84))
        smoke(fr,t,1650+0.5*1.1*170+30,2490-150-120,1.2,(240,232,220))
        # gallinas y Mike (con cabeza)
        hens=[(760,2690,.62,1,0.0),(1420,2680,.66,2,1.3),(1250,2740,.6,3,2.1),(840,2760,.58,0,3.0),(1560,2760,.6,1,4.0),(700,2790,.55,2,5.0)]
        for x0,y0,sc,pi,ph in hens:
            x,fl,v=wander(t,x0,60,.55,ph); peck=0.5+0.5*math.sin(t*2.2+ph*3)
            chick(fr,x,y0,sc,HENS[pi],head=True,phase=t*7+ph,walk=clamp(v/40)*.6,neck=0.12+0.9*max(0,peck-0.55)*2.2,flip=fl)
        x,fl,v=wander(t,1030,90,.40,0.4)
        chick(fr,x,2770,0.98,MIKE,head=True,phase=t*8,walk=clamp(v/40)*.9,neck=0.12,flip=fl,bob=-3*abs(math.sin(t*8)))
        # motas de luz
        rnd=random.Random(4)
        for i in range(26):
            px=(rnd.uniform(0,WW)+t*12*(0.5+i%3*.3))%WW; py=(rnd.uniform(1500,3400)-t*10)%1900+1500
            fr.sprite(lambda cv,ax,ay,k: cv.ell(ax,ay,5*k,5*k,(255,240,190,120)),px,py,l=10,u=10,r=10,d=10,ss=1)
        im=fr.rgb()
        warm=s.warm.resize((OW,OH)); im=Image.alpha_composite(im.convert('RGBA'),warm.crop((0,0,OW,OH))).convert('RGB')
        return im
