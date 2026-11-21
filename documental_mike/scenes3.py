import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from art import *
from env import *
from engine import *
import scenes2
from scenes1 import chick, FR_TINT

FB='/usr/share/fonts/opentype/inter/Inter-Bold.otf'; FM='/usr/share/fonts/opentype/inter/Inter-Medium.otf'
SERIF='/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf'; SERIFR='/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf'
_fc={}
def font(p,sz):
    k=(p,sz)
    if k not in _fc: _fc[k]=ImageFont.truetype(p,sz)
    return _fc[k]
def text_img(txt,path,sz,fill,stroke=0,sf=(0,0,0),track=0):
    f=font(path,sz)
    if track:
        w=sum(f.getlength(c)+track for c in txt); h=int(sz*1.5); im=Image.new('RGBA',(int(w)+20,h),(0,0,0,0)); d=ImageDraw.Draw(im); x=10
        for c in txt: d.text((x,sz*.1),c,font=f,fill=fill,stroke_width=stroke,stroke_fill=sf); x+=f.getlength(c)+track
        return im
    b=f.getbbox(txt,stroke_width=stroke); im=Image.new('RGBA',(b[2]-b[0]+20,b[3]-b[1]+int(sz*.5)),(0,0,0,0)); d=ImageDraw.Draw(im)
    d.text((10-b[0],int(sz*.1)-b[1]+int(sz*.1)),txt,font=f,fill=fill,stroke_width=stroke,stroke_fill=sf); return im

def word_t(idx,prefix,default=0):
    for w,a,b in scenes2.TL['items'][idx]['words']:
        if w.lower().startswith(prefix.lower()): return a
    return default

def radial(r,col,a,pw=2.0):
    n=int(r*2); y,x=np.mgrid[0:n,0:n].astype(np.float32); d=np.sqrt((x-r)**2+(y-r)**2)/r
    al=np.clip(1-d,0,1)**pw*a*255; arr=np.zeros((n,n,4),np.uint8); arr[...,0]=col[0];arr[...,1]=col[1];arr[...,2]=col[2];arr[...,3]=al.astype(np.uint8)
    return Image.fromarray(arr,'RGBA')

def screen_glow(fr,wx,wy,r,col,a,pw=2.0):
    sx,sy=fr.to_screen(wx,wy); rr=r*fr.k
    if rr<4: return
    g=radial(int(rr),col,a,pw); fr.put(g,sx-rr,sy-rr)

class Scene4:
    """Cocina de noche: el granjero alimenta a Mike con un gotero y le limpia la garganta con una jeringa."""
    def __init__(s):
        m=Cv(WW,WH,1)
        grad_fill(m.im,[(0,0),(WW,0),(WW,3000),(0,3000)],(98,66,50),(150,106,72)); m.d=ImageDraw.Draw(m.im)
        for x in range(0,WW,90): m.d.line([(x,0),(x,2900)],fill=(80,52,40,50),width=3)   # papel pintado rayado
        for x in range(45,WW,180):
            for y in range(120,2800,210): m.ell(x,y,10,16,(190,150,100,60))
        m.rect(0,2300,WW,2460,(110,72,50,255)); m.rect(0,2290,WW,2312,(190,150,108,255))   # zócalo
        for x in range(0,WW,240): m.line([(x,2312),(x,2460)],4,(80,52,38,255),False)
        m.rect(0,3000,WW,WH,(86,58,40,255))
        for y in range(3000,WH,120): m.line([(0,y),(WW,y)],4,(60,40,28,255),False)
        # ventana de noche
        m.rect(130,620,700,1560,(236,220,186,255)); 
        g=vgrad(500,860,[(0,(14,20,46)),(1,(34,44,86))]).convert('RGBA'); m.paste(g,165,655)
        rnd=random.Random(6)
        for _ in range(40): x=rnd.randint(180,640);y=rnd.randint(670,1400); m.ell(x,y,2.5,2.5,(250,246,220,200))
        m.ell(500,860,52,52,(250,240,200,255)); m.ell(520,848,44,44,(14,22,50,0))
        m.line([(415,655),(415,1515)],14,(236,220,186,255),False); m.line([(165,1085),(665,1085)],14,(236,220,186,255),False)
        m.poly([(110,600),(260,620),(220,1560),(110,1580)],(150,60,56,255),(100,36,34,255),3); m.poly([(720,600),(570,620),(610,1560),(720,1580)],(150,60,56,255),(100,36,34,255),3)
        # estante
        m.rect(1500,900,2060,930,(100,66,46,255)); 
        for i,x in enumerate((1560,1700,1840,1960)): m.rect(x-40,780,x+40,900,[(200,170,120,255),(150,170,130,255),(210,150,100,255),(180,190,200,255)][i],(70,50,36,255),3)
        # reloj
        m.ell(1780,520,110,110,(240,230,200,255),0,(70,50,36,255),8); m.line([(1780,520),(1780,440)],7,(40,30,24,255)); m.line([(1780,520),(1840,550)],7,(40,30,24,255))
        # mesa
        m.rect(260,2700,1980,2780,(150,60,50,255)); 
        for i in range(0,1720,86):
            for j in range(0,80,40): 
                if ((i//86)+(j//40))%2==0: m.rect(260+i,2700+j,260+i+86,2700+j+40,(240,226,206,255))
        m.rect(260,2780,1980,3260,(160,66,56,255))
        for i in range(0,1720,86):
            for j in range(0,480,86):
                if ((i//86)+(j//86))%2==0: m.rect(260+i,2780+j,min(260+i+86,1980),min(2780+j+86,3260),(238,222,200,255))
        m.rect(260,2700,1980,2712,(110,40,34,255)); m.rect(300,3260,350,3800,(82,54,38,255)); m.rect(1890,3260,1940,3800,(82,54,38,255))
        m.poly([(300,2640),(1940,2640),(1980,2700),(260,2700)],(196,84,70,255)); 
        for i in range(0,1720,86):
            if (i//86)%2==0: m.poly([(300+i*0.975,2640),(300+(i+86)*0.975,2640),(260+(i+86),2700),(260+i,2700)],(240,226,206,255))
        # lámpara de queroseno
        m.ell(470,2690,110,18,(0,0,0,60)); m.poly([(400,2690),(540,2690),(512,2540),(428,2540)],(200,170,110,255),(100,76,44,255),3)
        m.rect(436,2470,504,2545,(180,150,96,255)); m.blob([(424,2470),(516,2470),(540,2260),(470,2150),(400,2260)],(255,246,214,150),(255,236,180,220),5); m.ell(470,2400,24,50,(255,214,110,255))
        # cuenco y vaso
        m.poly([(640,2700),(780,2700),(760,2640),(660,2640)],(240,236,226,255),(150,140,128,255),3); m.ell(710,2640,52,10,(240,230,200,255))
        m.poly([(830,2700),(900,2700),(912,2590),(820,2590)],(190,220,240,170),(150,180,200,255),3); m.poly([(826,2650),(906,2650),(900,2700),(830,2700)],(160,200,230,200))
        # toalla doblada
        m.blob([(820,2700),(1180,2700),(1190,2660),(820,2660)],(226,214,190,255),(170,150,120,255),3,6); m.line([(840,2680),(1170,2680)],5,(170,80,70,255),False)
        s.main=m.im
        f=Cv(WW,WH,1); f.im=m.im.copy(); f.d=ImageDraw.Draw(f.im)
        s.front=Image.new('RGBA',(WW,WH),(0,0,0,0)); s.front.paste(m.im.crop((260,2700,1980,3800)),(260,2700))
        s.t_got=word_t(9,'gotero'); s.t_jer=word_t(9,'jeringa'); s.t0=0
    def cam(s,t,D): return cam_lerp((1100,2150,1.0),(1230,2380,1.42),t/D)
    def render(s,t,D):
        fr=Frame(s.cam(t,D)); fr.layer(s.main,1.0)
        fl=0.85+0.15*math.sin(t*17)+0.07*math.sin(t*5.3)
        screen_glow(fr,470,2400,1100,(255,170,80),.6*fl,1.5)
        # Mike sobre la toalla
        mx,my=1000,2672; sc=2.0
        chick_t=(1.0,.9,.78)
        breath=1.2*math.sin(t*2.2)
        farm_x,farm_y=1520,3560; k_f=2.9
        use_syr=t>=s.t_jer-getattr(s,"t0",0)-0.5
        # objetivo (muñón) para brazo
        tip_w=(mx+72*sc, my-340*sc)
        # reacción: hombro del granjero (flip -1)
        sh_w=(farm_x-0*k_f, farm_y-445*k_f)
        hand_w=(tip_w[0]+(150 if use_syr else 110), tip_w[1]-(120 if use_syr else 170))
        reach=((sh_w[0]-hand_w[0])/k_f, (hand_w[1]-sh_w[1])/k_f)
        drop=((t*0.9)%1.0)
        def draw_f(cv,ax,ay,k):
            e,h=farmer(cv,ax,ay,sc=k*k_f,flip=-1,walk=0,arm_f=(0,0),arm_b=(.15,.2),reach_f=reach,look=0.5,mouth=0.0)
            # herramienta
            tx,ty=ax+(tip_w[0]-farm_x)*k,ay+(tip_w[1]-farm_y)*k
            if not use_syr:
                nx,ny=tx+6*k,ty-46*k
                dx,dy=nx-h[0],ny-h[1]; L=math.hypot(dx,dy); ux,uy=dx/L,dy/L
                cv.line([(h[0]-ux*50*k,h[1]-uy*50*k),(h[0]+ux*10*k,h[1]+uy*10*k)],42*k,(176,40,40,255))      # pera de goma
                cv.line([(h[0],h[1]),(nx,ny)],18*k,(214,234,244,235)); cv.line([(h[0]+ux*60*k,h[1]+uy*60*k),(nx,ny)],10*k,(120,170,220,200))
                cv.line([(nx,ny),(nx+ux*14*k,ny+uy*14*k)],7*k,(214,234,244,255))
                if drop>.12: cv.ell(nx+ux*14*k,ny+uy*14*k+drop*40*k,6*k,9*k,(150,200,245,255))
            else:
                nx,ny=tx+10*k,ty-36*k
                dx,dy=nx-h[0],ny-h[1]; L=math.hypot(dx,dy); ux,uy=dx/L,dy/L; px,py=-uy,ux
                bl=L*.78; p0=(h[0]-ux*30*k,h[1]-uy*30*k)
                cv.poly([(p0[0]+px*20*k,p0[1]+py*20*k),(p0[0]+ux*bl+px*20*k,p0[1]+uy*bl+py*20*k),(p0[0]+ux*bl-px*20*k,p0[1]+uy*bl-py*20*k),(p0[0]-px*20*k,p0[1]-py*20*k)],(224,240,248,230),(90,110,120,255),3)
                pl=lerp(.15,.6,.5+.5*math.sin(t*3.0))
                pp=(p0[0]+ux*bl*pl,p0[1]+uy*bl*pl)
                cv.poly([(p0[0]+px*16*k,p0[1]+py*16*k),(pp[0]+px*16*k,pp[1]+py*16*k),(pp[0]-px*16*k,pp[1]-py*16*k),(p0[0]-px*16*k,p0[1]-py*16*k)],(190,225,245,200))
                cv.line([(pp[0],pp[1]),(p0[0]-ux*60*k,p0[1]-uy*60*k)],9*k,(120,130,138,255)); cv.line([(p0[0]-ux*60*k-px*32*k,p0[1]-uy*60*k-py*32*k),(p0[0]-ux*60*k+px*32*k,p0[1]-uy*60*k+py*32*k)],9*k,(120,130,138,255))
                cv.line([(p0[0]+ux*bl,p0[1]+uy*bl),(nx,ny)],9*k,(214,234,244,255))
        fr.sprite(draw_f,farm_x,farm_y,l=700,u=2000,r=500,d=60,tint=chick_t)
        # mesa por delante del granjero ya está en el fondo → redibujar mesa frontal como capa superior
        fr.layer(s.front,1.0)
        chick(fr,mx,my,sc,MIKE,head=False,neck=.1,flip=1,bob=breath,wob=.015*math.sin(t*2.2),walk=0,tail_up=.9)
        # luz cálida y viñeta de lámpara
        screen_glow(fr,470,2400,800,(255,190,110),.30*fl,2.0)
        im=fr.rgb().convert('RGBA'); im=Image.alpha_composite(im,Image.new('RGBA',(OW,OH),(30,18,40,34))); return im.convert('RGB')
