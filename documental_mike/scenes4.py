import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from art import *
from art2 import *
from env import *
from engine import *
import scenes2
from scenes1 import chick, FR_TINT, birds
from scenes3 import font, text_img, word_t, screen_glow, radial, FB, FM, SERIF, SERIFR

def paste_sprite(base,fn,x,y,l,u,r,d,ss=2):
    w,h=int(l+r),int(u+d); cv=Cv(w,h,ss); fn(cv,l,u,1.0); base.alpha_composite(cv.out(),(int(x-l),int(y-u)))

# =========================================================== 3A: ilustración científica
class Scene3a:
    def __init__(s):
        W,H=1080,1920
        b=vgrad(W,H,[(0,(238,226,198)),(1,(214,196,158))]).convert('RGBA')
        rnd=np.random.default_rng(5); n=(rnd.normal(0,1,(H,W,1))*5).astype(np.float32)
        arr=np.clip(np.asarray(b.convert('RGB'),dtype=np.float32)+n,0,255).astype(np.uint8); b=Image.fromarray(arr).convert('RGBA')
        cv=Cv(W,H,2); cv.im=b.resize((W*2,H*2)); cv.d=ImageDraw.Draw(cv.im)
        for x in range(0,W,60): cv.line([(x,0),(x,H)],1,(150,130,100,40),False)
        for y in range(0,H,60): cv.line([(0,y),(W,y)],1,(150,130,100,40),False)
        cv.rect(36,36,W-36,H-36,(0,0,0,0),(110,84,56,255),4); cv.rect(52,52,W-52,H-52,(0,0,0,0),(110,84,56,255),2)
        s.static=cv
        # cuadro superior (Mike caminando)
        fr=Cv(W,H,2,(0,0,0,0)); 
        s.frameA=(110,290,970,770)
        # círculo
        s.C=(540,1130); s.R=290
    def build_circle(s):
        C=s.C; R=s.R; cx,cy=C
        cv=Cv(2*R,2*R,2,(0,0,0,0)); 
        g=radial(R,(255,250,232),1.0,0.4).resize((2*R*2,2*R*2)); 
        cv.im=Image.new('RGBA',(2*R*2,2*R*2),(246,238,214,255))
        cv.d=ImageDraw.Draw(cv.im)
        o=(R,R)
        # cuello (corte longitudinal)
        cv.blob([(o[0]-150,o[1]+330),(o[0]-135,o[1]-120),(o[0]-100,o[1]-190),(o[0]+100,o[1]-190),(o[0]+135,o[1]-120),(o[0]+150,o[1]+330)],(250,248,242,255),(120,104,90,255),4,8)
        cv.blob([(o[0]-122,o[1]+330),(o[0]-112,o[1]-112),(o[0]-84,o[1]-166),(o[0]+84,o[1]-166),(o[0]+112,o[1]-112),(o[0]+122,o[1]+330)],(232,168,160,255),(180,110,106,255),3,8)
        # tráquea
        cv.rect(o[0]-100,o[1]-100,o[0]-62,o[1]+330,(236,226,214,255),(150,136,120,255),2)
        for i in range(0,430,26): cv.line([(o[0]-100,o[1]-90+i),(o[0]-62,o[1]-90+i)],2,(170,154,138,255),False)
        # vena (azul) hacia el coágulo
        cv.line([(o[0]-36,o[1]+330),(o[0]-36,o[1]-90)],24,(86,118,178,255),False)
        # vértebras
        for i in range(0,10):
            yy=o[1]-30+i*46; cv.blob([(o[0]+4,yy),(o[0]+90,yy),(o[0]+98,yy+16),(o[0]+90,yy+36),(o[0]+4,yy+36),(o[0]-4,yy+16)],(240,230,206,255),(160,140,108,255),2.5,5)
        cv.line([(o[0]+47,o[1]-40),(o[0]+47,o[1]+400)],22,(204,150,184,255),False)
        # tronco encefálico (rosa violáceo)
        cv.blob([(o[0]+4,o[1]-132),(o[0]+30,o[1]-152),(o[0]+66,o[1]-152),(o[0]+92,o[1]-132),(o[0]+96,o[1]-60),(o[0]+66,o[1]-30),(o[0]+30,o[1]-30),(o[0]+0,o[1]-60)],(196,128,172,255),(120,70,110,255),3,6)
        for i in range(4): cv.line([(o[0]+14,o[1]-120+i*20),(o[0]+82,o[1]-120+i*20)],2.5,(150,90,134,255),False)
        s.circ=cv.out()
        s.brain=(o[0]+47,o[1]-92); s.clot=(o[0]-36,o[1]-96)
    def render(s,t,D):
        W,H=1080,1920
        if not hasattr(s,'circ'):
            s.build_circle()
        t0=getattr(s,'t0',0)
        tmag=word_t(5,'El')-t0-0.2; tt=word_t(5,'tronco')-t0; tc=word_t(6,'coágulo',99)-t0 if True else 0
        tc=word_t(6,'coágulo')-t0
        im=s.static.out().copy()
        d=ImageDraw.Draw(im)
        a=smooth((t-.2)/.8)
        # título
        ti=text_img("ILUSTRACIÓN CIENTÍFICA SIMPLIFICADA",FB,34,(80,58,40,255),track=3); tim=text_img("Esquema ilustrativo · no es una fotografía",FM,28,(110,84,60,255))
        im.alpha_composite(ti,(int(540-ti.size[0]/2),110)); im.alpha_composite(tim,(int(540-tim.size[0]/2),170))
        # marco A
        x0,y0,x1,y1=s.frameA
        sk=vgrad(x1-x0,y1-y0,[(0,(150,196,230)),(0.62,(220,238,246)),(0.62,(130,170,86)),(1,(98,138,66))]).convert('RGBA')
        sk.alpha_composite(Image.new('RGBA',sk.size,(255,220,160,40)))
        # mini fondo: granero lejano
        sc_=Cv(x1-x0,y1-y0,2,(0,0,0,0)); sc_.rect(60,200,200,262,(172,54,46,255)); sc_.poly([(50,200),(130,150),(210,200)],(76,66,66,255)); sc_.ell(560,60,30,30,(255,240,190,255))
        sk.alpha_composite(sc_.out())
        mk=Cv(x1-x0,y1-y0,2,(0,0,0,0))
        chicken(mk,430,y1-y0-50,.95,MIKE,head=False,phase=t*6,walk=.5,neck=.12,flip=1,bob=-4*abs(math.sin(t*6)))
        sk.alpha_composite(mk.out())
        fm=Image.new('L',sk.size,0); ImageDraw.Draw(fm).rounded_rectangle((0,0,sk.size[0]-1,sk.size[1]-1),radius=18,fill=255)
        sk.putalpha(fm)
        pk=Image.new('RGBA',(sk.size[0]+16,sk.size[1]+16),(120,92,64,255)); pk.alpha_composite(sk,(8,8))
        im.alpha_composite(pk,(x0-8,y0-8),) if a>0 else None
        # zoom lines + círculo
        m=smooth((t-tmag)/.7)
        cxm,cym=s.C; R=s.R
        if m>0:
            nk=(x0+470+0,y0+100)
            for sgn in (-1,1):
                d.line([(nk[0],nk[1]),(cxm+sgn*R*math.sin(.6)*m+0*(1-m),cym-R*math.cos(.6)*m)],fill=(110,84,56,int(190*m)),width=3)
            cm=Image.new('L',(2*R,2*R),0); ImageDraw.Draw(cm).ellipse((0,0,2*R-1,2*R-1),fill=255)
            circ=s.circ.copy(); circ.putalpha(cm)
            # pulso del tronco encefálico
            pul=.5+.5*math.sin(t*3.2) if t>tt-.3 else 0
            if pul>0:
                g=radial(130,(255,120,190),.75*pul*smooth((t-tt+.3)/.5)); layer=Image.new('RGBA',circ.size,(0,0,0,0)); layer.alpha_composite(g,(int(s.brain[0]-130),int(s.brain[1]-130)))
                circ.alpha_composite(layer)
            if t>tc-.2:
                pul2=.5+.5*math.sin(t*4.0)
                g=radial(80,(180,20,40),.55*pul2*smooth((t-tc+.2)/.5)); layer=Image.new('RGBA',circ.size,(0,0,0,0)); layer.alpha_composite(g,(int(s.clot[0]-80),int(s.clot[1]-80)))
                circ.alpha_composite(layer)
                cc=Cv(2*R,2*R,2,(0,0,0,0)); cc.blob([(s.clot[0]-26,s.clot[1]-14),(s.clot[0]-6,s.clot[1]-26),(s.clot[0]+14,s.clot[1]-12),(s.clot[0]+10,s.clot[1]+14),(s.clot[0]-12,s.clot[1]+20),(s.clot[0]-28,s.clot[1]+6)],(118,24,40,255),(70,10,24,255),3,6)
                circ.alpha_composite(cc.out())
            # escala de aparición
            sc=max(.05,m); cs=circ.resize((int(2*R*sc),int(2*R*sc)),Image.LANCZOS)
            im.alpha_composite(cs,(int(cxm-R*sc),int(cym-R*sc)))
            ring=Cv(2*R+30,2*R+30,2,(0,0,0,0)); ring.ell(R+15,R+15,R*sc,R*sc,(0,0,0,0),0,(120,90,60,255),8)
            im.alpha_composite(ring.out(),(int(cxm-R-15),int(cym-R-15)))
            # etiquetas
            def label(tx,ty,w,txt,sub,t_on,target,side):
                u=smooth((t-t_on)/.6)
                if u<=0: return
                bx0=tx; 
                card=Cv(w,110 if sub else 74,2,(0,0,0,0)); card.rect(0,0,w,110 if sub else 74,(250,244,228,235),(110,84,56,255),3); 
                ci=card.out(); t1=text_img(txt,FB,38,(70,44,30,255)); ci.alpha_composite(t1,(12,6))
                if sub: t2=text_img(sub,FM,25,(120,84,60,255)); ci.alpha_composite(t2,(12,60))
                ci=ci.copy(); ci.putalpha(ci.split()[3].point(lambda v:int(v*u)))
                im.alpha_composite(ci,(int(tx),int(ty)))
                ex=tx+(w if side<0 else 0); ey=ty+37
                tx2=ex+(target[0]-ex)*u; ty2=ey+(target[1]-ey)*u
                d.line([(ex,ey),(tx2,ty2)],fill=(110,60,50,int(255*u)),width=4); 
                if u>.95: d.ellipse((target[0]-8,target[1]-8,target[0]+8,target[1]+8),fill=(206,60,70,255),outline=(255,255,255,255),width=2)
            bt=(cxm-R+s.brain[0],cym-R+s.brain[1]); ct=(cxm-R+s.clot[0],cym-R+s.clot[1])
            label(640,880,390,"Tronco encefálico","controla funciones esenciales",tt-.2,bt,+1)
            label(46,930,300,"Coágulo","evitó la hemorragia" if False else "",tc-.2,ct,-1)
        return im.convert('RGB')

# =========================================================== 5A: periódicos
def newspaper(head,mast,tilt=0,col=(236,228,204)):
    W,H=640,860; cv=Cv(W,H,2,(0,0,0,0)); cv.rect(0,0,W,H,col,(120,108,88,255),4)
    m=text_img(mast,SERIF,64,(30,26,24,255)); 
    cv.rect(24,22,W-24,26,(30,26,24,255)); im=cv.out(); im.alpha_composite(m,(int(W/2-m.size[0]/2),30)); cv=Cv(W,H,2,(0,0,0,0)); cv.im=im.resize((W*2,H*2)); cv.d=ImageDraw.Draw(cv.im)
    cv.rect(24,112,W-24,116,(30,26,24,255)); cv.rect(24,120,W-24,122,(30,26,24,255))
    im=cv.out(); y=134
    for ln in head.split('\n'):
        hi=text_img(ln,SERIF,58,(20,16,14,255)); im.alpha_composite(hi,(int(W/2-hi.size[0]/2),y)); y+=62
    cv=Cv(W,H,2,(0,0,0,0)); cv.im=im.resize((W*2,H*2)); cv.d=ImageDraw.Draw(cv.im)
    # ilustración sepia
    cv.rect(40,y+14,W-40,y+330,(204,182,140,255),(60,46,34,255),3)
    sub=Cv(W-80,316,2,(204,182,140,255)); sub.ell(130,250,300,60,(170,146,104,120)); 
    chicken(sub,(W-80)/2,290,1.15,dict(body=(238,226,196),shade=(190,170,130),wing=(224,208,172),tail=(220,204,166),tail2=(170,150,110),hack=(240,230,204)),head=False,neck=.1)
    cv.paste(sub.out(),40,y+14)
    yy=y+346
    for r in range(8):
        w=W-80-(24 if r%3==2 else 0); cv.rect(40,yy+r*18,40+w,yy+r*18+7,(90,80,66,255))
    t=text_img("Ilustración recreada",SERIFR,22,(90,70,50,255)); im=cv.out(); im.alpha_composite(t,(int(W-t.size[0]-34),H-46))
    return im

class Scene5a:
    def __init__(s):
        s.cards=[newspaper("¡SOBREVIVE SIN\nCABEZA!","EL HERALDO"),newspaper("EL POLLO QUE SE\nNEGÓ A MORIR","LA GACETA"),newspaper("¡INCREÍBLE!\nMIKE, LA ATRACCIÓN","EL CORREO"),newspaper("NOTICIA QUE\nRECORRE EL PAÍS","EL DIARIO")]
        s.cfg=[(-210,-330,-9),(240,-120,7),(-220,330,5),(200,430,-6)]
    def render(s,t,D):
        W,H=1080,1920
        bg=vgrad(W,H,[(0,(16,24,48)),(1,(40,30,56))]).convert('RGBA')
        L=Image.new('RGBA',(W,H),(0,0,0,0)); dd=ImageDraw.Draw(L)
        for i in range(18):
            a0=t*.18+i*math.pi/9; a1=a0+.07
            dd.polygon([(540,900),(540+math.cos(a0)*2400,900+math.sin(a0)*2400),(540+math.cos(a1)*2400,900+math.sin(a1)*2400)],fill=(255,214,140,26))
        bg.alpha_composite(L.filter(ImageFilter.GaussianBlur(4)))
        for i,(card,(ox,oy,tilt)) in enumerate(zip(s.cards,s.cfg)):
            ts=.35+i*.62; u=clamp((t-ts)/.55)
            if u<=0: continue
            e=1-(1-u)**3; sc=lerp(.15,1.0,e)*(1.0+.02*math.sin(t*1.5+i)); ang=lerp(540,tilt,e)
            c=card.resize((int(card.size[0]*sc*.78),int(card.size[1]*sc*.78)),Image.LANCZOS).rotate(ang,expand=True,resample=Image.BICUBIC)
            # sombra
            shw=Image.new('RGBA',c.size,(0,0,0,0)); shw.putalpha(c.split()[3].point(lambda v:int(v*.5))); shw=shw.filter(ImageFilter.GaussianBlur(12))
            cx=540+ox*e*.62; cy=860+oy*e*.62+math.sin(t*1.1+i*2)*6
            bg.alpha_composite(shw,(int(cx-c.size[0]/2+10),int(cy-c.size[1]/2+16))); bg.alpha_composite(c,(int(cx-c.size[0]/2),int(cy-c.size[1]/2)))
            if u<.25:
                f=Image.new('RGBA',(W,H),(255,255,255,int(150*(1-u/.25)))); bg.alpha_composite(f)
        return bg.convert('RGB')

# =========================================================== 5B: fila de personas
class Scene5b:
    def __init__(s):
        sky=sky_layer([(0,(112,164,214)),(0.3,(180,212,232)),(0.5,(250,232,200)),(1,(250,232,200))]); s.sky=sky
        s.clouds=cloud_layer(3600,21,6,500,1400,(255,255,250),(226,226,226),1.5,235)
        m=Cv(WW,WH,1)
        # edificios de fondo
        rnd=random.Random(12); x=-40
        while x<WW:
            w=rnd.randint(300,460); h=rnd.randint(560,900); col=rnd.choice([(170,96,78),(190,120,90),(154,116,96),(200,160,112)])
            m.rect(x,2780-h,x+w,2780,col,(70,44,36,255),3); m.rect(x-6,2780-h-26,x+w+6,2780-h,tuple(int(c*.8) for c in col)+(255,),(70,44,36,255),3)
            for wx_ in range(int(x)+40,int(x+w)-60,110):
                for wy_ in range(2780-h+60,2700,150):
                    lit=rnd.random()<.3; m.rect(wx_,wy_,wx_+64,wy_+92,(250,226,150,255) if lit else (70,86,110,255),(240,232,214,255),4)
            x+=w+rnd.randint(0,20)
        # acera y calle
        m.rect(0,2780,WW,3040,(190,184,172,255)); m.rect(0,2780,WW,2800,(150,144,134,255))
        for xx in range(0,WW,240): m.line([(xx,2800),(xx-60,3040)],3,(150,144,134,255),False)
        m.rect(0,3040,WW,3080,(120,114,104,255)); m.rect(0,3080,WW,WH,(86,86,92,255))
        for xx in range(0,WW,360): m.rect(xx,3480,xx+190,3506,(236,226,160,255))
        # farolas y banderines
        for lx in (240,900,1560):
            m.rect(lx-9,2250,lx+9,2800,(40,40,44,255)); m.ell(lx,2230,40,40,(250,240,200,255),0,(40,40,44,255),5)
        for i in range(14):
            xa=60+i*150; col=[(200,50,50,255),(240,220,200,255),(40,80,150,255)][i%3]
            m.poly([(xa,2330+10*math.sin(i)),(xa+70,2330+10*math.sin(i)),(xa+35,2410+10*math.sin(i))],col)
        m.line([(0,2326),(WW,2340)],4,(60,50,44,255),False)
        # carpa
        tx,ty=1640,2800
        m.poly([(tx-460,ty),(tx-400,ty-420),(tx,ty-620),(tx+400,ty-420),(tx+460,ty)],(224,224,216,255),(70,50,40,255),4)
        for i in range(-4,4):
            a=tx+i*115; m.poly([(a,ty),(a+60,ty),(a+30,ty-640+abs(i)*0),],(190,40,44,255)) if False else None
        for i in range(8):
            xa=tx-460+i*115; 
            m.poly([(xa,ty),(xa+58,ty),(tx+(xa-tx)*.12+29*0,ty-620),],(188,44,48,255)) if i%2==0 else None
        m.rect(tx-150,ty-330,tx+150,ty,(26,20,22,255),(70,50,40,255),5)
        m.poly([(tx-120,ty-330),(tx+120,ty-330),(tx+150,ty),(tx-150,ty)],(40,26,28,255))
        m.rect(tx-300,ty-520,tx+300,ty-440,(244,222,120,255),(120,40,30,255),6)
        s.sign=text_img("¡VEA A MIKE!",FB,66,(150,30,30,255)); m.im.alpha_composite(s.sign,(tx-s.sign.size[0]//2,ty-532))
        # taquilla
        bx=980; m.rect(bx-150,ty-380,bx+150,ty,(206,160,96,255),(100,66,40,255),5); m.rect(bx-100,ty-300,bx+100,ty-170,(255,226,150,255),(100,66,40,255),5)
        m.poly([(bx-190,ty-380),(bx+190,ty-380),(bx+150,ty-450),(bx-150,ty-450)],(188,44,48,255),(100,30,30,255),4)
        bt=text_img("ENTRADA",FB,34,(80,40,30,255)); m.im.alpha_composite(bt,(bx-bt.size[0]//2,ty-440))
        s.main=m.im
        s.ppl=[]; rnd=random.Random(3)
        for i in range(24): s.ppl.append((rnd.choice([0,1,2,3,3,1,0,4]),rnd.uniform(-.2,.2),rnd.uniform(0,6)))
    def render(s,t,D):
        fr=Frame(cam_lerp((620,2900,1.55),(1250,2880,1.5),t/D))
        fr.layer(s.sky,.2); fr.layer(s.clouds,.3,off=((t*10)%700-350,0)); fr.layer(s.main,1.0)
        FR=(1.0,.97,.93)
        # fila: personas del fondo (más pequeñas) y de primer plano
        adv=(t*18)%190
        for j in range(0,16):
            kind,jit,ph=s.ppl[j]; x=1000-(j*190)+adv-(0)
            xx=x; yy=3000+ (0 if j%2==0 else 22)
            sc=1.1
            fr.sprite(lambda cv,ax,ay,k,kind=kind,ph=ph: person(cv,ax,ay,sc*k*1.0,kind,t*4+ph,1,.45),xx,3170+(j%2)*26,l=140,u=520,r=140,d=40,tint=FR)
        for j in range(0,14):
            kind,jit,ph=s.ppl[j+8]; x=1050-(j*210)+adv*.9+80
            fr.sprite(lambda cv,ax,ay,k,kind=kind,ph=ph: person(cv,ax,ay,1.6*k,kind,t*4+ph,1,.4),x,3330,l=200,u=760,r=200,d=40,tint=(.95,.95,.96))
        # destellos de cámara
        rnd=random.Random(int(t*3))
        im=fr.rgb()
        return im

# =========================================================== 5C: ciudades y revistas
def magazine(title,col,sub):
    W,H=540,720; cv=Cv(W,H,2,(0,0,0,0)); cv.rect(0,0,W,H,col,(30,30,30,255),4)
    im=cv.out(); t=text_img(title,FB,64,(250,244,230,255),track=2); im.alpha_composite(t,(int(W/2-t.size[0]/2),24))
    cv=Cv(W,H,2,(0,0,0,0)); cv.im=im.resize((W*2,H*2)); cv.d=ImageDraw.Draw(cv.im)
    cv.ell(W/2,380,200,200,(246,232,196,255),0,(30,30,30,255),4)
    chicken(cv,W/2+10,500,1.1,MIKE,head=False,neck=.1)
    im=cv.out(); t2=text_img(sub,FM,30,(250,244,230,255)); im.alpha_composite(t2,(int(W/2-t2.size[0]/2),H-100))
    t3=text_img("Ilustración recreada",FM,20,(250,244,230,200)); im.alpha_composite(t3,(int(W/2-t3.size[0]/2),H-50))
    return im
def city_layer(width,seed,col,hmin,hmax,base,lit=.35,wcol=(255,214,130)):
    rnd=random.Random(seed); L=Image.new('RGBA',(width,WH),(0,0,0,0)); d=ImageDraw.Draw(L); x=0
    while x<width:
        w=rnd.randint(110,260); h=rnd.randint(hmin,hmax)
        d.rectangle((x,base-h,x+w,base),fill=col+(255,))
        if rnd.random()<.35: d.polygon([(x+w*.5-8,base-h),(x+w*.5,base-h-rnd.randint(60,200)),(x+w*.5+8,base-h)],fill=col+(255,))
        for wy in range(base-h+30,base-30,46):
            for wx in range(x+16,x+w-26,34):
                if rnd.random()<lit: d.rectangle((wx,wy,wx+14,wy+22),fill=wcol+(255,))
        x+=w+rnd.randint(0,16)
    return L
class Scene5c:
    def __init__(s):
        s.sky=sky_layer([(0,(46,40,96)),(0.25,(110,72,126)),(0.42,(236,120,96)),(0.52,(252,176,104)),(1,(255,196,120))],sun=(1500,2000,110,(255,196,120)))
        s.c1=city_layer(4600,2,(120,84,118),520,1100,2800,.12,(255,206,140)); s.c2=city_layer(4600,7,(54,40,80),380,820,2880,.28)
        m=Cv(WW,WH,1); m.rect(0,2880,WW,WH,(54,52,62,255)); m.rect(0,2880,WW,2910,(120,116,120,255))
        s.road=m.im
        d=Cv(4600,WH,1); 
        for x in range(0,4600,300): d.rect(x,3380,x+170,3406,(236,220,150,255))
        s.dash=d.im
        s.mags=[magazine("PANORAMA",(160,40,44,255),"Edición especial"),magazine("ACTUALIDAD",(30,70,120,255),"El pollo sin cabeza"),magazine("MUNDO HOY",(30,100,70,255),"Una historia increíble")]
        s.pos=[(-190,-120,-8),(200,-420,6),(-110,-640,-4)]
    def render(s,t,D):
        fr=Frame((1080,2420,1.05)); fr.layer(s.sky,.2)
        fr.layer(s.c1,1.0,off=(300-t*90,0)); fr.layer(s.c2,1.0,off=(400-t*170,0)); fr.layer(s.road,1.0); fr.layer(s.dash,1.0,off=(-((t*420)%300)+150,0))
        fr.sprite(lambda cv,ax,ay,k: car(cv,ax,ay,.95*k,(66,128,128,255),rot=t*14,crate=True),700+8*math.sin(t*2),3250+3*math.sin(t*9),l=300,u=300,r=300,d=40,tint=(1,.9,.85))
        im=fr.rgb().convert('RGBA')
        for i,(card,(ox,oy,tilt)) in enumerate(zip(s.mags,s.pos)):
            ts=.45+i*1.25; u=clamp((t-ts)/.45)
            if u<=0: continue
            e=1-(1-u)**3; ov=1+.12*math.sin(u*math.pi); sc=lerp(.2,.62,e)*ov
            c=card.resize((int(card.size[0]*sc*1.15),int(card.size[1]*sc*1.15)),Image.LANCZOS).rotate(tilt*e,expand=True,resample=Image.BICUBIC)
            shw=Image.new('RGBA',c.size,(0,0,0,0)); shw.putalpha(c.split()[3].point(lambda v:int(v*.5))); shw=shw.filter(ImageFilter.GaussianBlur(10))
            cx=540+ox*.9; cy=1290+oy*.62+i*0
            cy=[640,980,1250][i]
            im.alpha_composite(shw,(int(cx-c.size[0]/2+8),int(cy-c.size[1]/2+12))); im.alpha_composite(c,(int(cx-c.size[0]/2),int(cy-c.size[1]/2)))
            if u<.3: im.alpha_composite(Image.new('RGBA',(OW,OH),(255,255,255,int(210*(1-u/.3)))))
        return im.convert('RGB')

# =========================================================== 6A: viaje a Arizona + motel
class Scene6a:
    def __init__(s):
        s.sky=sky_layer([(0,(40,36,92)),(0.2,(104,70,128)),(0.36,(228,110,100)),(0.48,(252,170,100)),(1,(255,196,120))],sun=(700,1980,120,(255,190,110)))
        def far(width,seed,col,base,amp):
            L=Image.new('RGBA',(width,WH),(0,0,0,0)); c=Cv(width,WH,1); c.im=L; c.d=ImageDraw.Draw(L); rnd=random.Random(seed); x=0
            while x<width:
                w=rnd.randint(300,700); h=rnd.randint(int(amp*.4),amp); mesa(c,x+w/2,base,w,h,col+(255,)); x+=w+rnd.randint(40,260)
            return c.im
        s.m1=far(4600,3,(150,84,104),2760,300); s.m2=far(4600,8,(110,60,86),2830,200)
        g=Cv(4600,WH,1); g.rect(0,2830,4600,WH,(150,94,70,255)); rnd=random.Random(2)
        g.rect(0,3000,4600,3300,(70,66,72,255)); g.rect(0,3000,4600,3014,(190,176,160,255)); g.rect(0,3286,4600,3300,(190,176,160,255))
        for x in range(0,4600,340): g.rect(x,3146,x+180,3166,(236,214,140,255))
        for i in range(16): saguaro(g,rnd.randint(40,4560),rnd.choice((2900,2950)),rnd.uniform(.9,1.6))
        s.ground=g.im
        # motel
        m=Cv(WW,WH,1); m.rect(0,2830,WW,WH,(150,94,70,255)); m.rect(0,3000,WW,3300,(70,66,72,255))
        m.rect(560,2560,2100,3000,(232,212,172,255),(100,80,60,255),4); m.rect(540,2530,2120,2575,(168,70,60,255),(90,40,34,255),3)
        for i in range(6):
            dx=640+i*240; m.rect(dx,2740,dx+100,3000,(54,92,120,255),(240,230,210,255),5); m.rect(dx+130,2780,dx+210,2870,(255,214,120,255) if i not in (3,) else (230,200,110,255),(240,230,210,255),4)
            nt=text_img(str(i+1),FB,34,(250,240,220,255)); m.im.alpha_composite(nt,(dx+30,2660))
        m.rect(300,2000,324,3000,(60,52,56,255))
        m.rect(130,1900,500,2200,(30,24,40,255),(250,240,220,255),8)
        s.sign=text_img("MOTEL",FB,76,(255,90,160,255),stroke=0,track=4); s.sign2=text_img("ARIZONA",FM,44,(120,220,255,255),track=8)
        m.im.alpha_composite(s.sign,(int(315-s.sign.size[0]/2),1930)); m.im.alpha_composite(s.sign2,(int(315-s.sign2.size[0]/2),2090))
        for xx,sc in ((2000,1.4),(2100,1.0)): saguaro(m,xx,2880,sc)
        s.motel=m.im
    def render(s,t,D):
        p=t/D; sw=smooth(clamp((p-.40)/.25))
        fr=Frame((1080,2480,1.0+.1*p)); fr.layer(s.sky,.2)
        if p<.70:
            off=-t*260
            fr.layer(s.m1,1.0,off=(off*.25,0)); fr.layer(s.m2,1.0,off=(off*.5,0)); fr.layer(s.ground,1.0,off=(off,0))
        if p>.38:
            im0=fr.rgb().convert('RGBA'); 
            fr2=Frame((1080,2480,1.0+.1*p)); fr2.layer(s.sky,.2); fr2.layer(s.motel,1.0)
            # motel entra desde la derecha
            im1=fr2.rgb().convert('RGBA')
            sh=int((1-sw)*OW); 
            out=im0.copy(); 
            out.alpha_composite(im1.crop((0,0,OW-sh,OH)),(sh,0)) if sh<OW else None
            base=out
        else: base=fr.rgb().convert('RGBA')
        fr3=Frame((1080,2480,1.0+.1*p)); fr3.im=base
        cx=lerp(520,620,sw)-(0 if p<.6 else 0)
        carx=lerp(620,1380,smooth(clamp((p-.62)/.3))) if p>.62 else lerp(620,700,0)
        if p<.62: carx=640+10*math.sin(t*2)
        spd=1.0 if p<.62 else 1-smooth(clamp((p-.62)/.3))
        s_=fr3
        s_.sprite(lambda cv,ax,ay,k: car(cv,ax,ay,.95*k,(66,128,128,255),rot=t*12*spd,crate=True),carx,3250+3*math.sin(t*9)*spd,l=300,u=300,r=300,d=40,tint=(1,.85,.85))
        im=fr3.rgb().convert('RGBA')
        # resplandor de neón
        if p>.5:
            u=smooth((p-.5)/.2)*(.8+.2*math.sin(t*9)); g=radial(380,(255,80,160),.55*u); 
            sx=(315-(0))*(OW/ (WW/(1.0+.1*p))) ; 
            k=OW/(WW/(1.0+.1*p)); x0=1080-WW/(1.0+.1*p)/2; y0=2480-(WW/(1.0+.1*p))*OH/OW/2
            gx=(315-x0)*k; gy=(2050-y0)*k
            im.alpha_composite(g,(int(gx-380),int(gy-380))) if sw>.9 else None
        return im.convert('RGB')

# =========================================================== 6B: habitación de motel
class Scene6b:
    def __init__(s):
        m=Cv(WW,WH,1)
        grad_fill(m.im,[(0,0),(WW,0),(WW,3000),(0,3000)],(62,96,100),(88,126,124)); m.d=ImageDraw.Draw(m.im)
        m.rect(0,2860,WW,WH,(86,62,52,255)); m.rect(0,2840,WW,2870,(40,56,60,255))
        # ventana con persiana
        m.rect(1380,640,2000,1700,(20,26,50,255),(224,214,190,255),14)
        for y in range(660,1690,62): m.rect(1394,y,1986,y+30,(210,204,186,255)); 
        # cama
        m.rect(60,2260,1200,2400,(98,62,48,255)); m.rect(60,1960,1200,2300,(236,226,204,255),(90,70,56,255),5)
        m.rect(40,1700,120,2840,(98,62,48,255)); m.rect(1180,2060,1260,2840,(98,62,48,255))
        m.blob([(100,2300),(1200,2300),(1190,2800),(110,2800)],(178,72,66,255),(100,40,36,255),4,6)
        for x in range(120,1200,140): m.rect(x,2300,x+60,2800,(206,100,88,255))
        # mesa de noche y lámpara
        m.rect(1340,2480,1700,2860,(110,72,52,255),(70,44,32,255),5); m.rect(1340,2480,1700,2510,(150,104,74,255))
        m.poly([(1450,2480),(1590,2480),(1570,2380),(1470,2380)],(180,150,100,255),(90,70,40,255),3)
        m.poly([(1420,2300),(1620,2300),(1580,2160),(1460,2160)],(250,232,180,255),(150,130,90,255),3)
        s.main=m.im
        # caja de viaje en silla
        s.cratexy=(1800,2860)
    def render(s,t,D):
        p=t/D; fr=Frame(cam_lerp((1260,2300,1.0),(1580,2620,1.7),p))
        fr.layer(s.main,1.0)
        lamp=clamp(1.0-smooth((p-.45)/.5))*(1.0 if p<.4 else (0.9+0.1*math.sin(t*20)))
        # luz de neón rosa por la persiana
        screen_glow(fr,1700,1200,900,(255,70,150),.30*(.8+.2*math.sin(t*1.5)),1.4)
        # silla + caja + Mike
        cx,cy=1830,2860
        def chair(cv,ax,ay,k):
            cv.rect(ax-130*k,ay-300*k,ax+130*k,ay-270*k,(120,80,56,255),(70,44,30,255),3)
            for dx in (-120,100): cv.rect(ax+dx*k,ay-270*k,ax+(dx+22)*k,ay,(110,72,50,255))
            cv.rect(ax-10*k,ay-300*k-0,ax+0,ay-300*k,(0,0,0,0))
        fr.sprite(chair,cx,cy,l=200,u=400,r=200,d=20)
        agit=clamp(1-(p-.2)/.35) if .1<p<.55 else 0
        def crate(cv,ax,ay,k):
            cx_=ax; by=ay-300*k
            # Mike dentro de la caja (solo parte superior visible)
            chicken(cv,cx_,by-0*k+40*k,.75*k,MIKE,head=False,neck=.1,flip=1,bob=-4*abs(math.sin(t*10))*agit,wob=.09*math.sin(t*14)*agit,shadow=False,tail_up=.8)
            cv.rect(ax-130*k,by-30*k,ax+130*k,by+110*k,(176,130,82,255),(100,70,40,255),4)
            for i in range(1,5): cv.line([(ax-130*k+i*52*k,by-30*k),(ax-130*k+i*52*k,by+110*k)],3*k,(120,84,50,255),False)
        fr.sprite(crate,cx,cy,l=300,u=700,r=300,d=20,tint=(.8,.78,.85))
        screen_glow(fr,1520,2260,1000,(255,190,110),.55*lamp,1.7)
        im=fr.rgb().convert('RGBA')
        im=Image.alpha_composite(im,Image.new('RGBA',(OW,OH),(10,14,40,int(60+120*(1-lamp)))))
        return im.convert('RGB')

# =========================================================== 7: imagen final de Mike
class Scene7:
    def __init__(s):
        s.sky=sky_layer([(0,(40,44,100)),(0.2,(120,92,140)),(0.34,(244,150,110)),(0.46,(255,206,130)),(1,(255,214,150))],sun=(1080,1900,170,(255,226,160)))
        L=Image.new('RGBA',(WW,WH),(0,0,0,0)); d=ImageDraw.Draw(L)
        for i in range(14):
            a0=math.radians(200+i*10.5); a1=a0+math.radians(4)
            d.polygon([(1080,1900),(1080+math.cos(a0)*3000,1900+math.sin(a0)*3000),(1080+math.cos(a1)*3000,1900+math.sin(a1)*3000)],fill=(255,230,170,38))
        s.sky.alpha_composite(L.filter(ImageFilter.GaussianBlur(10)))
        s.clouds=cloud_layer(3600,31,6,700,1500,(255,214,180),(210,130,130),1.6,215)
        f=Cv(WW,WH,1)
        hill_poly(f,WW,2050,60,4,(70,60,100),(110,80,100),2600,freqs=(1,2.2,4))
        barn(f,420,2230,.8,body=(120,44,48),trim=(210,190,170),roof=(50,44,56)); silo(f,720,2230,.6,col=(130,130,150),dome=(90,90,110)); tree(f,1740,2250,1.0,3,leaf=(52,66,60),leaf2=(70,84,66),trunk=(50,40,40))
        hill_poly(f,WW,2400,50,9,(112,132,70),(86,110,54),WH,freqs=(.8,1.9))
        grass_tufts(f,0,WW,2500,3800,140,(150,170,76,255),(110,140,60,255),sc=2.4)
        for x in range(160,2160,200): f.line([(x,2760),(x,2900)],10,(230,210,190,255),False) if False else None
        s.main=f.im
    def render(s,t,D):
        p=t/D; fr=Frame(cam_lerp((1080,2500,1.0),(1060,2720,1.45),p))
        fr.layer(s.sky,.2); fr.layer(s.clouds,.3,off=((t*8)%700-350,0)); fr.layer(s.main,1.0)
        screen_glow(fr,1080,2520,900,(255,200,120),.45,1.6)
        chick(fr,1080,3080,2.6,MIKE,head=False,neck=.12,flip=1,bob=1.5*math.sin(t*1.9),wob=.012*math.sin(t*1.3),tail_up=.95)
        rnd=random.Random(8)
        for i in range(40):
            px=(rnd.uniform(0,WW)+t*20*(0.4+i%4*.2))%WW; py=(rnd.uniform(1800,3600)-t*16*(0.5+i%3*.3))%1900+1700
            a=int(110+90*math.sin(t*2+i)); fr.sprite(lambda cv,ax,ay,k,a=a: (cv.ell(ax,ay,6*k,6*k,(255,240,170,a))),px,py,l=12,u=12,r=12,d=12,ss=1)
        return fr.rgb()
