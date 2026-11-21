import sys, json, os, math, time
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw
import scenes2
TL=json.load(open('/tmp/claude-0/work/build/timeline.json')); scenes2.set_timeline(TL)
from scenes1 import Scene1
from scenes2 import Scene2, Scene3b
from scenes3 import Scene4, text_img, FB, FM, SERIF, font
from scenes4 import Scene3a, Scene5a, Scene5b, Scene5c, Scene6a, Scene6b, Scene7
from engine import Look
FPS=24; TOTAL=TL['total']; N=int(TOTAL*FPS); OUT='/tmp/claude-0/work/frames/'
it=TL['items']
def bound(i): return (it[i-1]['end']+it[i]['start'])/2
B=[0,bound(2),bound(4),bound(7),bound(8),bound(10),bound(11),bound(12),bound(13),bound(14),bound(15),TOTAL]
SC=[('s1',Scene1,dict()),('s2',Scene2,dict(bright=.95)),('s3a',Scene3a,dict(grain=.4,vig=.5)),('s3b',Scene3b,dict()),('s4',Scene4,dict(bright=1.05)),
    ('s5a',Scene5a,dict()),('s5b',Scene5b,dict()),('s5c',Scene5c,dict()),('s6a',Scene6a,dict()),('s6b',Scene6b,dict(grain=1.3)),('s7',Scene7,dict())]
XF=0.8
# ---------------- subtítulos
def cues():
    out=[]
    for i,x in enumerate(it):
        words=x['words']; lines=[];cur=[];
        grp=[];g=[]
        for w in words:
            tentative=' '.join(a for a,_,_ in g+[w])
            if g and len(tentative)>27 and True:
                grp.append(g); g=[w]
            else: g.append(w)
        if g: grp.append(g)
        # agrupa de dos en dos líneas
        k=0
        while k<len(grp):
            seg=grp[k:k+2]
            if len(grp)-k==3: seg=grp[k:k+3] if len(' '.join(a for gg in grp[k:k+3] for a,_,_ in gg))<=60 else grp[k:k+2]
            out.append(dict(lines=[' '.join(a for a,_,_ in gg) for gg in seg],a=seg[0][0][1],b=seg[-1][-1][2]))
            k+=len(seg)
    for j,c in enumerate(out):
        nxt=out[j+1]['a'] if j+1<len(out) else 1e9
        c['b']=min(c['b']+0.25,nxt-0.02,c['b']+0.9)
        c['a']=c['a']-0.05
    return out
CUES=cues()
def sub_img(lines):
    f=font(FB,60); h=84; W=1080; im=Image.new('RGBA',(W,h*len(lines)+20),(0,0,0,0)); d=ImageDraw.Draw(im)
    for i,l in enumerate(lines):
        w=d.textlength(l,font=f); d.text(((W-w)/2,10+i*h),l,font=f,fill=(255,255,255,255),stroke_width=7,stroke_fill=(0,0,0,255))
    return im
SUBS=[sub_img(c['lines']) for c in CUES]
def overlay_sub(im,T):
    for c,s in zip(CUES,SUBS):
        if c['a']<=T<c['b']:
            a=min(1,(T-c['a'])/.12,(c['b']-T)/.12+.001)
            if a<1: s=s.copy(); s.putalpha(s.split()[3].point(lambda v:int(v*max(a,0))))
            h=s.size[1]; y=1745-h
            im.paste(s,(0,y),s); return
def overlay_title(im,T):
    a=min(smooth((T-1.0)/1.0),1-smooth((T-8.0)/1.2)) if T<9.5 else 0
    if a>0:
        t1=text_img("MIKE",SERIF,170,(255,244,220,255),stroke=5,sf=(40,20,10),track=10); t2=text_img("EL POLLO SIN CABEZA",FB,50,(255,244,220,255),stroke=4,sf=(40,20,10),track=6)
        t3=text_img("Documental animado  ·  Ilustraciones recreadas",FM,32,(255,236,200,255),stroke=3,sf=(40,20,10))
        for t_,y in ((t1,190),(t2,420),(t3,500)):
            t_=t_.copy(); t_.putalpha(t_.split()[3].point(lambda v:int(v*a))); im.paste(t_,(int(540-t_.size[0]/2),y),t_)
    e=TOTAL-6.0
    if T>e:
        a=smooth((T-e)/1.2)
        for t_,y in ((text_img("MIKE",SERIF,150,(255,244,220,255),stroke=5,sf=(40,20,10),track=10),170),(text_img("1945 – 1947",FB,52,(255,244,220,255),stroke=4,sf=(40,20,10),track=6),380),
            (text_img("Ilustraciones recreadas, no son fotografías reales",FM,30,(255,236,200,255),stroke=3,sf=(40,20,10)),470)):
            t_=t_.copy(); t_.putalpha(t_.split()[3].point(lambda v:int(v*a))); im.paste(t_,(int(540-t_.size[0]/2),y),t_)
def smooth(t): t=max(0,min(1,t)); return t*t*(3-2*t)
def main(w,nw):
    os.makedirs(OUT,exist_ok=True)
    frames=[n for n in range(N) if n%nw==w]
    look=Look(w+1); cache={}
    def scene(i):
        if i not in cache:
            for k in list(cache): 
                if abs(k-i)>1: del cache[k]
            nm,cls,kw=SC[i]; o=cls(); o.t0=B[i]; cache[i]=(o,kw)
        return cache[i]
    def rend(i,T,n):
        o,kw=scene(i); im=o.render(max(0,T-B[i]),B[i+1]-B[i]); return look.apply(im,n,**kw)
    for n in frames:
        T=n/FPS
        i=max(j for j in range(len(SC)) if B[j]<=T+1e-9)
        im=rend(i,T,n)
        # fundido cruzado hacia la escena siguiente / desde la anterior
        if i+1<len(SC) and T>B[i+1]-XF/2:
            im2=rend(i+1,T,n); a=smooth((T-(B[i+1]-XF/2))/XF); im=Image.blend(im,im2,a)
        elif i>0 and T<B[i]+XF/2:
            im2=rend(i-1,T,n); a=smooth((T-(B[i]-XF/2))/XF); im=Image.blend(im2,im,a)
        overlay_title(im,T); overlay_sub(im,T)
        fade=min(1,T/1.0,(TOTAL-T)/1.2)
        if fade<1: im=Image.eval(im,lambda v:int(v*max(fade,0)))
        im.save(OUT+f'f{n:05d}.png',compress_level=1)
        if w==0 and n%48==0: print(n,N,flush=True)
if __name__=='__main__':
    if len(sys.argv)>2 and sys.argv[1]=='one':
        os.makedirs('/tmp/claude-0/work/probe',exist_ok=True); OUT='/tmp/claude-0/work/probe/'
        for T in map(float,sys.argv[2:]): main_n=int(T*FPS); 
    main(int(sys.argv[1]),int(sys.argv[2])) if sys.argv[1]!='one' else None
