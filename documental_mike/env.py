"""Elementos de entorno 2D: cielo, nubes, colinas, granero, silo, casa, árboles, cercas, campos..."""
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
from art import *

WW,WH=2160,3840; OW,OH=1080,1920

def sky_layer(stops,sun=None,stars=False,seed=1):
    im=vgrad(WW,WH,stops).convert('RGBA')
    if sun:
        x,y,r,col=sun; L=Image.new('RGBA',(WW,WH),(0,0,0,0)); d=ImageDraw.Draw(L)
        d.ellipse((x-r*3,y-r*3,x+r*3,y+r*3),fill=col+(90,)); L=L.filter(ImageFilter.GaussianBlur(r*1.2))
        im.alpha_composite(L); L=Image.new('RGBA',(WW,WH),(0,0,0,0)); d=ImageDraw.Draw(L)
        d.ellipse((x-r,y-r,x+r,y+r),fill=col+(255,)); L=L.filter(ImageFilter.GaussianBlur(3)); im.alpha_composite(L)
    if stars:
        rnd=random.Random(seed); d=ImageDraw.Draw(im)
        for _ in range(260):
            x=rnd.randint(0,WW); y=rnd.randint(0,1500); r=rnd.choice((1.5,2,2.5,3)); a=rnd.randint(140,255)
            d.ellipse((x-r,y-r,x+r,y+r),fill=(255,250,230,a))
    return im

def cloud_layer(width,seed,n,ymin,ymax,col,shade,scale=1.0,alpha=235):
    rnd=random.Random(seed); L=Image.new('RGBA',(width,WH),(0,0,0,0))
    for _ in range(n):
        cx=rnd.randint(0,width); cy=rnd.randint(ymin,ymax); sc=rnd.uniform(.7,1.4)*scale
        puffs=[]
        S=Image.new('RGBA',(width,WH),(0,0,0,0)); d=ImageDraw.Draw(S)
        for i in range(rnd.randint(5,8)):
            px=cx+rnd.randint(-int(260*sc),int(260*sc)); py=cy+rnd.randint(-int(30*sc),int(30*sc)); r=rnd.randint(int(60*sc),int(120*sc))
            d.ellipse((px-r*1.3,py-r*.7+14,px+r*1.3,py+r*.7+14),fill=shade+(alpha,))
        for i in range(rnd.randint(5,8)):
            px=cx+rnd.randint(-int(260*sc),int(260*sc)); py=cy+rnd.randint(-int(34*sc),int(20*sc)); r=rnd.randint(int(60*sc),int(120*sc))
            d.ellipse((px-r*1.3,py-r*.7,px+r*1.3,py+r*.7),fill=col+(alpha,))
        S=S.filter(ImageFilter.GaussianBlur(10*sc)); L.alpha_composite(S)
    return L

def grad_fill(im,pts,top,bot,y0=None,y1=None):
    """rellena polígono con gradiente vertical."""
    ys=[p[1] for p in pts]; y0=y0 if y0 is not None else min(ys); y1=y1 if y1 is not None else max(ys)
    m=Image.new('L',im.size,0); ImageDraw.Draw(m).polygon(pts,fill=255)
    box=m.getbbox()
    if not box: return
    g=vgrad(box[2]-box[0],max(1,box[3]-box[1]),[(0,top),(1,bot)]).convert('RGBA')
    im.paste(g,(box[0],box[1]),m.crop(box))

def ridge(w,base,amp,seed,freqs=(1.0,2.3,5.1),step=24,x0=0):
    rnd=random.Random(seed); ph=[rnd.uniform(0,6.28) for _ in freqs]; pts=[]
    for x in range(x0,w+step,step):
        y=base
        for i,f in enumerate(freqs): y+=amp/(i+1)*math.sin(x/w*math.pi*2*f+ph[i])
        pts.append((x,y))
    return pts

def hill_poly(cv,w,base,amp,seed,top,bot,bottom,**k):
    pts=ridge(w,base,amp,seed,**k)+[(w,bottom),(0,bottom)]
    grad_fill(cv.im,[(int(x),int(y)) for x,y in pts],top,bot,min(p[1] for p in pts),bottom); cv.d=ImageDraw.Draw(cv.im)

def tree(cv,x,y,s,seed=0,leaf=(70,110,56),leaf2=(98,140,70),trunk=(84,60,44)):
    rnd=random.Random(seed)
    cv.ell(x,y+4*s,90*s,14*s,(0,0,0,60))
    cv.poly([(x-14*s,y),(x-8*s,y-120*s),(x+8*s,y-120*s),(x+16*s,y)],trunk,(54,38,28,255),2)
    cv.line([(x,y-100*s),(x-46*s,y-170*s)],10*s,trunk); cv.line([(x,y-110*s),(x+50*s,y-180*s)],9*s,trunk)
    for i in range(14):
        px=x+rnd.randint(-100,100)*s; py=y-rnd.randint(150,300)*s; r=rnd.randint(50,90)*s
        cv.ell(px,py,r,r*.82,leaf,0,(50,80,40,255),2)
    for i in range(10):
        px=x+rnd.randint(-90,90)*s; py=y-rnd.randint(190,320)*s; r=rnd.randint(30,60)*s
        cv.ell(px-10*s,py-10*s,r,r*.8,leaf2)

def barn(cv,x,y,s,body=(172,54,46),trim=(240,230,204),roof=(76,66,66),lit=1.0,door_open=0.0,loft_light=False):
    """x centro, y suelo. ancho ≈ 520*s."""
    w=260*s; h=190*s
    cv.ell(x+30*s,y+6*s,w*1.15,16*s,(0,0,0,70))
    # base de piedra
    cv.rect(x-w,y-22*s,x+w,y,(130,124,116,255))
    # muro
    shade=tuple(int(c*0.78) for c in body)
    cv.rect(x-w,y-h,x+w,y-22*s,body,(70,24,22,255),2)
    for i in range(1,26):  # tablones
        xx=x-w+i*(2*w/26); cv.line([(xx,y-h),(xx,y-22*s)],1.4*s,shade+(130,),False)
    # techo gambrel
    top=y-h-170*s; mid=y-h-84*s
    cv.poly([(x-w-26*s,y-h+8*s),(x-w*.62,mid),(x,top),(x+w*.62,mid),(x+w+26*s,y-h+8*s)],roof,(40,34,34,255),3)
    for i in range(1,7):
        yy=lerp(y-h+8*s,top,i/7.0); cv.line([(x-(w+26*s)*(1-i/7.0*.9),yy),(x+(w+26*s)*(1-i/7.0*.9),yy)],1.4*s,(50,44,44,160),False)
    cv.poly([(x-w*.62,mid),(x,top),(x+w*.62,mid),(x,mid+10*s)],(98,86,84,255))
    cv.line([(x-w-26*s,y-h+8*s),(x-w*.62,mid),(x,top),(x+w*.62,mid),(x+w+26*s,y-h+8*s)],6*s,trim)
    # frontón: puerta del pajar
    cv.rect(x-34*s,mid+16*s,x+34*s,y-h-2*s,(46,22,20,255),trim,4*s)
    if loft_light: cv.rect(x-30*s,mid+20*s,x+30*s,y-h-6*s,(255,214,120,255))
    cv.line([(x-34*s,mid+16*s),(x+34*s,y-h-2*s)],4*s,trim,False); cv.line([(x+34*s,mid+16*s),(x-34*s,y-h-2*s)],4*s,trim,False)
    # puertas grandes
    dw=88*s; dh=140*s
    for sx in (-1,1):
        x0=x+sx*(dw*(.02+door_open*.0)); 
    cv.rect(x-dw,y-22*s-dh,x+dw,y-22*s,(150,44,38,255),trim,6*s)
    if door_open>0:
        cv.rect(x-dw*door_open,y-22*s-dh,x+dw*door_open,y-22*s,(40,22,20,255))
    for sx in (-1,1):
        xa=x+sx*dw if sx<0 else x; 
    cv.line([(x,y-22*s-dh),(x,y-22*s)],5*s,trim,False)
    for sx in (-1,1):
        x0=x if sx>0 else x-dw; x1=x+dw if sx>0 else x
        cv.line([(x0,y-22*s-dh),(x1,y-22*s)],5*s,trim,False); cv.line([(x1,y-22*s-dh),(x0,y-22*s)],5*s,trim,False)
    # ventanas
    for wx_ in (-190*s,190*s):
        cv.rect(x+wx_-30*s,y-h+40*s,x+wx_+30*s,y-h+104*s,(60,38,30,255),trim,5*s)
        cv.line([(x+wx_,y-h+40*s),(x+wx_,y-h+104*s)],3*s,trim,False)
    # esquinas
    cv.rect(x-w,y-h,x-w+12*s,y-22*s,trim); cv.rect(x+w-12*s,y-h,x+w,y-22*s,trim)

def silo(cv,x,y,s,col=(196,200,204),dome=(120,128,134)):
    w=62*s; h=420*s
    cv.ell(x+20*s,y+4*s,w*1.4,10*s,(0,0,0,60))
    cv.rect(x-w,y-h,x+w,y,col,(110,114,118,255),2)
    cv.rect(x+w*.35,y-h,x+w,y,tuple(int(c*.82) for c in col)+(255,))
    for i in range(1,9): cv.line([(x-w,y-h*i/9),(x+w,y-h*i/9)],2.5*s,(120,124,128,255),False)
    cv.poly([(x-w,y-h),(x-w*.8,y-h-34*s),(x-w*.4,y-h-60*s),(x,y-h-70*s),(x+w*.4,y-h-60*s),(x+w*.8,y-h-34*s),(x+w,y-h)],dome,(70,76,82,255),2)

def house(cv,x,y,s,wall=(236,228,206),roof=(112,64,56),lit=True,night=False):
    w=170*s; h=150*s
    cv.ell(x+20*s,y+5*s,w*1.2,12*s,(0,0,0,60))
    cv.rect(x-w,y-h,x+w,y,wall,(150,138,116,255),2)
    cv.poly([(x-w-24*s,y-h+4*s),(x,y-h-130*s),(x+w+24*s,y-h+4*s)],roof,(62,34,30,255),3)
    cv.rect(x+w*.45,y-h-120*s,x+w*.72,y-h-20*s,(150,76,60,255),(80,40,34,255),2)
    glass=(255,208,120,255) if lit else (150,176,200,255)
    for wx_ in (-100*s,60*s):
        cv.rect(x+wx_-30*s,y-h+30*s,x+wx_+30*s,y-h+100*s,glass,(250,244,230,255),5*s)
        cv.line([(x+wx_,y-h+30*s),(x+wx_,y-h+100*s)],3*s,(250,244,230,255),False); cv.line([(x+wx_-30*s,y-h+65*s),(x+wx_+30*s,y-h+65*s)],3*s,(250,244,230,255),False)
    cv.rect(x+110*s,y-96*s,x+156*s,y,(120,78,52,255),(250,244,230,255),4*s)
    cv.rect(x-w-8*s,y-14*s,x+w+8*s,y,(160,148,130,255))
    # porche
    cv.rect(x-w*.1,y-100*s,x+w*.04,y,(222,210,184,255)) 

def fence(cv,x0,x1,y,s,col=(236,228,208),shade=(150,132,108)):
    step=int(120*s); xs=list(range(int(x0),int(x1),step))
    for yy in (-62*s,-34*s): cv.line([(x0,y+yy),(x1,y+yy)],7*s,col)
    for xx in xs:
        cv.poly([(xx-8*s,y),(xx-8*s,y-86*s),(xx,y-96*s),(xx+8*s,y-86*s),(xx+8*s,y)],col,shade+(255,),2)
    cv.ell((x0+x1)/2,y+4*s,(x1-x0)/2,5*s,(0,0,0,40))

def grass_tufts(cv,x0,x1,y0,y1,n,col,col2,seed=3,sc=1.0):
    rnd=random.Random(seed)
    for _ in range(n):
        x=rnd.uniform(x0,x1); y=rnd.uniform(y0,y1); k=sc*(0.5+(y-y0)/(y1-y0+1))
        c=col if rnd.random()<.5 else col2
        for dx in (-6,0,7): cv.line([(x+dx*k,y),(x+dx*k*2.2,y-rnd.uniform(14,26)*k)],2.4*k,c,False)

def haybale(cv,x,y,s):
    cv.rect(x-60*s,y-56*s,x+60*s,y,(220,184,92,255),(150,118,50,255),2)
    for i in range(1,5): cv.line([(x-60*s+i*24*s,y-56*s),(x-60*s+i*24*s,y)],1.6*s,(150,118,50,200),False)
    cv.line([(x-60*s,y-38*s),(x+60*s,y-38*s)],3*s,(120,84,40,255),False); cv.line([(x-60*s,y-16*s),(x+60*s,y-16*s)],3*s,(120,84,40,255),False)

def windmill_tower(cv,x,y,s,col=(120,110,100)):
    cv.poly([(x-34*s,y),(x-8*s,y-430*s),(x+8*s,y-430*s),(x+34*s,y)],col,(70,64,58,255),2)
    for i in range(1,6): cv.line([(x-34*s+i*4*s,y-i*72*s),(x+34*s-i*4*s,y-i*72*s)],3*s,(70,64,58,255),False)
    cv.poly([(x+10*s,y-420*s),(x+90*s,y-440*s),(x+90*s,y-400*s),(x+10*s,y-396*s)],(150,140,128,255),(70,64,58,255),2)  # cola
def windmill_blades(cv,cx,cy,r,ang,col=(168,158,146)):
    for i in range(12):
        a=ang+i*math.pi/6; ca,sa=math.cos(a),math.sin(a)
        p0=(cx+ca*r*.12,cy+sa*r*.12); p1=(cx+ca*r,cy+sa*r)
        nx,ny=-sa*r*.12,ca*r*.12
        cv.poly([p0,p1,(p1[0]+nx,p1[1]+ny),(p0[0]+nx*.6,p0[1]+ny*.6)],col,(80,72,66,255),1.5)
    cv.ell(cx,cy,r*.07,r*.07,(70,64,58,255))

def vignette_arr(strength=0.55,power=2.4):
    yy,xx=np.mgrid[0:OH,0:OW].astype(np.float32); cx,cy=OW/2,OH/2
    d=np.sqrt(((xx-cx)/cx)**2+((yy-cy)/cy)**2*0.72); v=1-strength*np.clip((d-.35)/.9,0,1)**power*1.4
    return np.clip(v,0,1)[...,None]
