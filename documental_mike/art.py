"""Utilidades de dibujo 2D (PIL) y personajes: Mike, gallinas y el granjero."""
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

def lerp(a,b,t): return a+(b-a)*t
def clamp(x,a=0,b=1): return max(a,min(b,x))
def smooth(t): t=clamp(t); return t*t*(3-2*t)
def ease(t): return smooth(t)
def rgb(h): h=h.lstrip('#'); return tuple(int(h[i:i+2],16) for i in (0,2,4))
def mix(c1,c2,t): return tuple(int(lerp(a,b,t)) for a,b in zip(c1,c2))

def vgrad(w,h,stops):
    ys=np.linspace(0,1,h); out=np.zeros((h,3),np.float32)
    ps=[s[0] for s in stops]
    for c in range(3): out[:,c]=np.interp(ys,ps,[s[1][c] for s in stops])
    return Image.fromarray(np.repeat(out[:,None,:],w,1).astype(np.uint8),'RGB')

def spline(pts,closed=True,n=10):
    P=list(pts); out=[]
    m=len(P)
    for i in range(m if closed else m-1):
        p0=P[(i-1)%m] if (closed or i>0) else P[0]
        p1=P[i]; p2=P[(i+1)%m]; p3=P[(i+2)%m] if (closed or i+2<m) else P[-1]
        for k in range(n):
            t=k/n; t2=t*t; t3=t2*t
            out.append(tuple(0.5*((2*p1[j])+(-p0[j]+p2[j])*t+(2*p0[j]-5*p1[j]+4*p2[j]-p3[j])*t2+(-p0[j]+3*p1[j]-3*p2[j]+p3[j])*t3) for j in (0,1)))
    return out

class Cv:
    """Lienzo RGBA con supersampling; coordenadas lógicas (sin escalar)."""
    def __init__(self,w,h,ss=1,bg=(0,0,0,0)):
        self.w,self.h,self.ss=w,h,ss
        self.im=Image.new('RGBA',(int(w*ss),int(h*ss)),bg); self.d=ImageDraw.Draw(self.im)
    def S(self,pts): return [(x*self.ss,y*self.ss) for x,y in pts]
    def poly(self,pts,fill,outline=None,ow=0):
        if fill is not None and len(fill)==4 and fill[3]<255:
            P=self.S(pts); xs=[p[0] for p in P]; ys=[p[1] for p in P]
            x0,y0=max(int(min(xs))-2,0),max(int(min(ys))-2,0); x1,y1=min(int(max(xs))+3,self.im.size[0]),min(int(max(ys))+3,self.im.size[1])
            if x1<=x0 or y1<=y0: return
            L=Image.new('RGBA',(x1-x0,y1-y0),(0,0,0,0)); ImageDraw.Draw(L).polygon([(x-x0,y-y0) for x,y in P],fill=fill)
            reg=self.im.crop((x0,y0,x1,y1)); reg.alpha_composite(L); self.im.paste(reg,(x0,y0)); return
        self.d.polygon(self.S(pts),fill=fill)
        if outline and ow: self.d.line(self.S(list(pts)+[pts[0]]),fill=outline,width=max(1,int(ow*self.ss)),joint='curve')
    def blob(self,pts,fill,outline=None,ow=0,n=10): self.poly(spline(pts,True,n),fill,outline,ow)
    def ell(self,cx,cy,rx,ry,fill,rot=0,outline=None,ow=0):
        pts=[]; c,s=math.cos(rot),math.sin(rot)
        for i in range(40):
            a=i/40*2*math.pi; x=rx*math.cos(a); y=ry*math.sin(a)
            pts.append((cx+x*c-y*s,cy+x*s+y*c))
        self.poly(pts,fill,outline,ow)
    def line(self,pts,w,fill,round_=True):
        P=self.S(pts); self.d.line(P,fill=fill,width=max(1,int(w*self.ss)),joint='curve')
        if round_:
            r=w*self.ss/2
            for x,y in (P[0],P[-1]): self.d.ellipse((x-r,y-r,x+r,y+r),fill=fill)
    def rect(self,x0,y0,x1,y1,fill,outline=None,ow=0):
        x0,x1=min(x0,x1),max(x0,x1); y0,y1=min(y0,y1),max(y0,y1)
        if fill is not None and (len(fill)<4 or fill[3]>0): self.d.rectangle(self.S([(x0,y0),(x1,y1)]),fill=fill)
        if outline and ow: self.d.rectangle(self.S([(x0,y0),(x1,y1)]),outline=outline,width=int(ow*self.ss))
    def glow(self,cx,cy,r,col,alpha=180,blur=None):
        L=Image.new('RGBA',self.im.size,(0,0,0,0)); d=ImageDraw.Draw(L); s=self.ss
        d.ellipse(((cx-r)*s,(cy-r)*s,(cx+r)*s,(cy+r)*s),fill=col+(alpha,))
        L=L.filter(ImageFilter.GaussianBlur((blur or r*.6)*s)); self.im=Image.alpha_composite(self.im,L); self.d=ImageDraw.Draw(self.im)
    def paste(self,other,x,y):
        im=other.im if isinstance(other,Cv) else other
        self.im.alpha_composite(im,(int(x*self.ss),int(y*self.ss)))
    def out(self):
        return self.im.resize((self.w,self.h),Image.LANCZOS) if self.ss!=1 else self.im

# ---------------------------------------------------------------- gallinas / Mike
INK=(96,78,66,255)
MIKE=dict(body=(247,245,238),shade=(222,216,202),wing=(236,231,217),tail=(240,236,224),tail2=(214,206,190),hack=(250,248,242))
HENS=[dict(body=(181,104,58),shade=(140,76,40),wing=(160,88,46),tail=(110,60,34),tail2=(80,44,28),hack=(196,124,70)),
      dict(body=(226,222,212),shade=(190,184,170),wing=(206,200,188),tail=(150,146,138),tail2=(110,106,100),hack=(236,232,224)),
      dict(body=(120,92,72),shade=(86,64,50),wing=(98,74,58),tail=(52,40,36),tail2=(36,28,26),hack=(150,118,92)),
      dict(body=(214,168,96),shade=(176,132,70),wing=(196,150,80),tail=(130,92,50),tail2=(96,66,38),hack=(228,186,112))]
YEL=(232,178,52,255); YEL2=(196,140,34,255); STUMP=(226,168,160,255); STUMP2=(196,128,128,255)
RED=(206,46,42,255)

def feather(cv,x,y,ang,L,wd,col,edge):
    c,s=math.cos(ang),math.sin(ang); pts=[]
    for t,w in ((0,.25),(.25,.8),(.6,1),(.85,.7),(1,0),(.85,-.7),(.6,-1),(.25,-.8),(0,-.25)):
        px,py=t*L,w*wd*.5; pts.append((x+px*c-py*s,y+px*s+py*c))
    cv.blob(pts,col,edge,1.6,6)

def chicken(cv,x,y,sc=1.0,pal=MIKE,head=True,phase=0.0,walk=0.0,neck=0.12,flip=1,bob=0.0,tail_up=1.0,wob=0.0,shadow=True):
    """x,y = suelo bajo el cuerpo. flip=-1 mira a la izquierda. Cuerpo ~230 de largo."""
    k=sc
    def T(px,py): return (x+flip*px*k, y+(py+bob)*k)
    def TT(pts): return [T(*p) for p in pts]
    if shadow: cv.ell(x,y+2*k,96*k,12*k,(0,0,0,64))
    for side,ph in ((0,0),(1,math.pi)):
        sw=math.sin(phase+ph)*walk; lift=max(0,math.cos(phase+ph))*walk*16
        hip=T(-6+side*12,-128); foot=T(-6+side*12+sw*28,-5-lift); knee=T(-6+side*12+sw*14+8,-66-lift*.5)
        col=YEL if side else YEL2
        cv.line([hip,knee,foot],7*k,col)
        for tx,ty in ((20,2),(12,6),(-12,1)): cv.line([foot,(foot[0]+flip*tx*k,foot[1]+ty*k*.4)],4.4*k,col)
    # cola (plumas largas curvadas hacia arriba-atrás)
    bx,by=T(-108,-222)
    for i,a in enumerate((-100,-118,-134,-150,-166,-85)):
        ang=math.radians(a)*tail_up+math.radians(-150)*(1-tail_up)
        if flip<0: ang=math.pi-ang
        feather(cv,bx,by,ang,(150-i*8)*k,38*k,pal['tail'] if i%2==0 else pal['tail2'],INK)
    body=TT([(84,-208),(76,-166),(40,-130),(-30,-120),(-92,-146),(-124,-196),(-110,-246),(-56,-272),(12,-272),(54,-254),(82,-236)])
    cv.blob(body,pal['body'],INK,2.4,10)
    cv.blob(TT([(66,-170),(34,-134),(-30,-126),(-84,-148),(-30,-142),(30,-146)]),pal['shade']+(170,),None,0,8)
    # cuello curvo y cónico
    th=neck+wob; nl=92*k; base=T(56,-250)
    pts=[]; ang=-math.pi/2+th*flip; cx_,cy_=base; cl=[(cx_,cy_)]
    for i in range(1,7):
        ang+= (0.10*flip)*(1 if th<0.5 else -1)  # leve curvatura en S
        cx_+=math.cos(ang)*nl/6; cy_+=math.sin(ang)*nl/6; cl.append((cx_,cy_))
    L=[];R=[]
    for i,(px,py) in enumerate(cl):
        if i<len(cl)-1: dx,dy=cl[i+1][0]-px,cl[i+1][1]-py
        else: dx,dy=px-cl[i-1][0],py-cl[i-1][1]
        n=math.hypot(dx,dy) or 1; nx,ny=-dy/n,dx/n; w=lerp(40,26,i/6)*k/2
        L.append((px+nx*w,py+ny*w)); R.append((px-nx*w,py-ny*w))
    cv.blob(L+R[::-1],pal['hack'],INK,2.2,6)
    for i in range(1,6):   # escamas de plumas del cuello
        px,py=cl[i]; cv.line([(px-flip*10*k,py+4*k),(px,py+10*k),(px+flip*10*k,py+4*k)],1.6*k,INK[:3]+(120,),False)
    tip=cl[-1]; ta=ang; ux,uy=math.cos(ta),math.sin(ta)
    if head:
        hc=(tip[0]+ux*10*k,tip[1]+uy*10*k)
        cv.ell(hc[0],hc[1],23*k,20*k,pal['hack'],0,INK,2)
        bxx=hc[0]+flip*21*k; cv.poly([(bxx-flip*2*k,hc[1]-7*k),(bxx+flip*24*k,hc[1]+4*k),(bxx-flip*2*k,hc[1]+10*k)],(236,150,40,255),INK,1.6)
        for i in range(3): cv.ell(hc[0]-flip*(4-i*8)*k,hc[1]-22*k-(i==1)*5*k,8*k,10*k,RED,0,(140,30,30,255),1.2)
        cv.ell(hc[0]+flip*10*k,hc[1]+21*k,5.4*k,10*k,RED,0,(140,30,30,255),1.2)
        cv.ell(hc[0]+flip*5*k,hc[1]-3*k,3.6*k,3.6*k,(20,16,16,255)); cv.ell(hc[0]+flip*6*k,hc[1]-4.2*k,1.2*k,1.2*k,(255,255,255,255))
    else:
        ang2=math.atan2(uy,ux)+math.pi/2
        cv.ell(tip[0],tip[1],15*k,11*k,STUMP,ang2,STUMP2,1.8)
        cv.ell(tip[0]+ux*1*k,tip[1]+uy*1*k,7*k,4.5*k,(240,200,192,255),ang2)
    # plumas de collar (hackle) sobre la base del cuello
    for i in range(5):
        feather(cv,base[0]-flip*8*k,base[1]+6*k,math.pi/2+(i-2)*.42*flip+.5*flip*(1),44*k,24*k,pal['hack'],INK)
    wing=TT([(42,-212),(12,-244),(-48,-246),(-104,-214),(-76,-172),(-12,-152),(30,-176)])
    cv.blob(wing,pal['wing'],INK,2,9)
    for i in range(5): cv.line(TT([(26-i*20,-206+i*4),(-34-i*14,-176+i*3)]),1.8*k,INK[:3]+(140,),False)
    cv.ell(*T(-8,-142),25*k,19*k,pal['body'],0.2*flip,INK,2)

# ---------------------------------------------------------------- granjero (personaje ficticio estilizado)
SKIN=(224,170,128,255); SKIN2=(196,140,102,255); DEN=(58,84,128,255); DEN2=(42,62,100,255)
SHIRT=(222,206,170,255); SHIRT2=(196,176,138,255); BOOT=(88,58,40,255); HAT=(226,196,116,255); HAT2=(170,138,70,255)

def limb(cv,p0,a1,l1,a2,l2,w,col,hand=None,sleeve=None):
    e=(p0[0]+math.sin(a1)*l1,p0[1]+math.cos(a1)*l1)
    h=(e[0]+math.sin(a2)*l2,e[1]+math.cos(a2)*l2)
    cv.line([p0,e],w,sleeve or col); cv.line([e,h],w*.92,col)
    if hand: cv.ell(h[0],h[1],w*.62,w*.62,hand,0,(150,100,70,255),1.5)
    return e,h

def farmer(cv,x,y,sc=1.0,flip=1,walk=0.0,phase=0.0,arm_f=(0.35,0.45),arm_b=(-0.2,0.1),bob=0.0,look=0.0,mid=None,hat=True,mouth=0.0,reach_f=None,reach_b=None,ss_note=None):
    """x,y: pies. Altura ~ 640*sc. mid(cv,T): se llama entre brazo trasero y delantero para dibujar objetos (p.ej. un pollo)."""
    k=sc
    def T(px,py): return (x+flip*px*k, y+(py+bob)*k)
    cv.ell(x,y+3*k,120*k,16*k,(0,0,0,70))
    # piernas
    for side in (1,0):
        sw=math.sin(phase+side*math.pi)*walk
        hip=T(-4,-300); foot=T(sw*50,-14-max(0,math.cos(phase+side*math.pi))*walk*18)
        col=DEN if side else DEN2
        cv.line([hip,T(sw*22,-160),foot],46*k,col)
        cv.poly([(foot[0]-flip*18*k,foot[1]-16*k),(foot[0]+flip*10*k,foot[1]-16*k),(foot[0]+flip*54*k,foot[1]+10*k),(foot[0]+flip*54*k,foot[1]+18*k),(foot[0]-flip*18*k,foot[1]+18*k)],BOOT,(50,34,24,255),2)
    sh=T(0,-445)
    def ik(tg,l1=120,l2=110,bend=1):
        tx,ty=tg[0],tg[1]; d=min(math.hypot(tx,ty),l1+l2-1); phi=math.atan2(tx,ty)
        dl=math.acos(max(-1,min(1,(l1*l1+d*d-l2*l2)/(2*l1*d)))); a1=phi-bend*dl
        ex,ey=l1*math.sin(a1),l1*math.cos(a1); return (a1,math.atan2(tx-ex,ty-ey))
    if reach_f: arm_f=ik(reach_f)
    if reach_b: arm_b=ik(reach_b)
    # brazo trasero
    limb(cv,(sh[0]-flip*4*k,sh[1]),flip*arm_b[0],120*k,flip*arm_b[1],110*k,34*k,SKIN2,SKIN2,SHIRT2)
    # torso (camisa) + peto
    cv.blob([T(-46,-440),T(40,-446),T(56,-300),T(-50,-290)],SHIRT,(120,100,70,255),2.5,8)
    cv.blob([T(-40,-420),T(34,-420),T(50,-300),T(-46,-296)],DEN,(36,52,86,255),2.5,6)
    cv.line([T(-24,-445),T(-14,-360)],12*k,DEN); cv.line([T(24,-445),T(18,-360)],12*k,DEN)
    cv.rect(*T(-22,-362),*T(18,-326),DEN2); cv.ell(*T(-24,-440),6*k,6*k,(210,180,80,255)); cv.ell(*T(26,-440),6*k,6*k,(210,180,80,255))
    # cuello + cabeza
    cv.line([T(0,-452),T(2,-478)],34*k,SKIN2)
    hd=T(6+look*6,-535)
    cv.ell(hd[0],hd[1],44*k,52*k,SKIN,0,(150,100,70,255),2.4)
    cv.ell(hd[0]-flip*40*k,hd[1]+4*k,10*k,15*k,SKIN2,0,(150,100,70,255),1.8)   # oreja
    ex=hd[0]+flip*(18+look*3)*k; ey=hd[1]-8*k
    cv.ell(ex,ey,5.5*k,6.5*k,(250,246,240,255)); cv.ell(ex+flip*1.5*k,ey,3.2*k,3.6*k,(40,28,22,255))
    cv.line([(ex-flip*10*k,ey-14*k),(ex+flip*13*k,ey-13*k-mouth*0)],4*k,(110,78,52,255))   # ceja
    cv.line([(hd[0]+flip*30*k,hd[1]),(hd[0]+flip*38*k,hd[1]+14*k),(hd[0]+flip*26*k,hd[1]+17*k)],4*k,SKIN2,False)  # nariz
    cv.line([(hd[0]+flip*10*k,hd[1]+30*k),(hd[0]+flip*26*k,hd[1]+30*k-mouth*5*k)],3.4*k,(140,70,60,255))
    cv.blob([(hd[0]+flip*6*k,hd[1]+18*k),(hd[0]+flip*30*k,hd[1]+20*k),(hd[0]+flip*28*k,hd[1]+26*k),(hd[0]+flip*8*k,hd[1]+26*k)],(120,90,66,255),None,0,6) # bigote
    if hat:
        cv.ell(hd[0],hd[1]-38*k,86*k,15*k,HAT,0,HAT2,3)
        cv.blob([(hd[0]-flip*44*k,hd[1]-40*k),(hd[0]-flip*38*k,hd[1]-86*k),(hd[0]+flip*8*k,hd[1]-98*k),(hd[0]+flip*42*k,hd[1]-80*k),(hd[0]+flip*46*k,hd[1]-40*k)],HAT,HAT2,3,8)
        cv.rect(hd[0]-44*k,hd[1]-52*k,hd[0]+46*k,hd[1]-42*k,(110,70,40,255))
    if mid: mid(cv,T)
    # brazo delantero
    return limb(cv,(sh[0]+flip*6*k,sh[1]),flip*arm_f[0],120*k,flip*arm_f[1],110*k,36*k,SKIN,SKIN,SHIRT)
