import math, numpy as np
from PIL import Image, ImageChops, ImageFilter
from art import Cv, lerp, smooth, clamp
from env import WW,WH,OW,OH

class Frame:
    def __init__(s,cam):
        s.cx,s.cy,s.z=cam; s.cw=WW/s.z; s.ch=s.cw*OH/OW; s.x0=s.cx-s.cw/2; s.y0=s.cy-s.ch/2; s.k=OW/s.cw
        s.im=Image.new('RGBA',(OW,OH),(0,0,0,255))
    def layer(s,img,depth=1.0,off=(0,0)):
        z=1+(s.z-1)*depth; cw=WW/z; ch=cw*OH/OW; iw=img.size[0]
        cx=iw/2+(s.cx-WW/2)*depth+off[0]; cy=WH/2+(s.cy-WH/2)*depth+off[1]
        cx=min(max(cx,cw/2),iw-cw/2); cy=min(max(cy,ch/2),WH-ch/2)
        box=(cx-cw/2,cy-ch/2,cx+cw/2,cy+ch/2)
        r=img.resize((OW,OH),Image.BILINEAR,box=box)
        if r.mode=='RGBA': s.im.alpha_composite(r)
        else: s.im.paste(r.convert('RGBA'))
    def to_screen(s,wx,wy): return ((wx-s.x0)*s.k,(wy-s.y0)*s.k)
    def sprite(s,fn,wx,wy,l=300,u=700,r=300,d=60,tint=None,ss=2,alpha=1.0):
        sx,sy=s.to_screen(wx,wy); k=s.k
        x0=sx-l*k; y0=sy-u*k; w=int((l+r)*k); h=int((u+d)*k)
        if x0>OW or y0>OH or x0+w<0 or y0+h<0 or w<2 or h<2: return
        cv=Cv(w,h,ss); fn(cv,l*k,u*k,k); im=cv.out()
        if tint:
            rch,g,b,a=im.split(); rch=rch.point(lambda v:int(v*tint[0])); g=g.point(lambda v:int(v*tint[1])); b=b.point(lambda v:int(v*tint[2]))
            im=Image.merge('RGBA',(rch,g,b,a))
        if alpha<1: a=im.split()[3].point(lambda v:int(v*alpha)); im.putalpha(a)
        s.im.alpha_composite(im,(int(round(x0)),int(round(y0))),) if (x0>=0 and y0>=0) else _paste_neg(s.im,im,int(round(x0)),int(round(y0)))
    def screen_cv(s,ss=2):
        return Cv(OW,OH,ss)
    def put(s,im,x=0,y=0,alpha=1.0):
        if alpha<1: a=im.split()[3].point(lambda v:int(v*alpha)); im=im.copy(); im.putalpha(a)
        _paste_neg(s.im,im,int(x),int(y))
    def rgb(s): return s.im.convert('RGB')

def _paste_neg(dst,im,x,y):
    W,H=dst.size; w,h=im.size
    sx0=max(0,-x); sy0=max(0,-y); sx1=min(w,W-x); sy1=min(h,H-y)
    if sx1<=sx0 or sy1<=sy0: return
    c=im.crop((sx0,sy0,sx1,sy1)); dst.alpha_composite(c,(x+sx0,y+sy0))

def cam_lerp(a,b,t):
    e=smooth(t); return tuple(lerp(a[i],b[i],e) for i in range(3))

class Look:
    def __init__(s,seed=1):
        from env import vignette_arr
        s.vig=vignette_arr(); rnd=np.random.default_rng(seed)
        s.grain=[(rnd.normal(0,1,(OH,OW,1))*6.0).astype(np.float32) for _ in range(8)]
    def apply(s,img,n,grade=(1,1,1),bright=1.0,vig=1.0,grain=1.0,fade=1.0,sat=1.0):
        a=np.asarray(img,dtype=np.float32)
        if sat!=1.0:
            l=a.mean(2,keepdims=True); a=l+(a-l)*sat
        a=a*np.array(grade,dtype=np.float32)*bright
        a=a*(1-(1-s.vig)*vig)
        a=a+s.grain[n%8]*grain
        a=a*fade
        return Image.fromarray(np.clip(a,0,255).astype(np.uint8))
