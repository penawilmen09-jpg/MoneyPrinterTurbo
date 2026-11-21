import math, random
from art import *
from env import *

SK=[(236,190,150,255),(224,172,128,255),(196,140,104,255),(240,200,168,255)]
def person(cv,x,y,sc,kind=0,phase=0.0,flip=1,walk=1.0):
    k=sc; f=flip
    def T(px,py): return (x+f*px*k,y+py*k)
    suits=[((84,90,102,255),(50,54,64,255),(60,56,60,255)),((176,52,58,255),(176,52,58,255),(70,40,40,255)),((120,92,64,255),(84,64,44,255),(54,40,30,255)),
           ((60,100,148,255),(60,100,148,255),(60,44,40,255)),((196,160,92,255),(98,120,150,255),(70,50,40,255))]
    top,bot,shoe=suits[kind%5]; skin=SK[kind%4]
    h=250+(0 if kind!=4 else -80)
    cv.ell(x,y+2*k,50*k,8*k,(0,0,0,50))
    for sd in (1,0):
        sw=math.sin(phase+sd*math.pi)*walk; lift=max(0,math.cos(phase+sd*math.pi))*walk*8
        hip=T(0,-h*.9+60*(kind==4)*0); foot=T(sw*26,-4-lift)
        if kind in (1,3): cv.line([T(0,-h*.55),foot],16*k,(skin[0]-20,skin[1]-20,skin[2]-20,255))
        else: cv.line([T(0,-h*.55),foot],22*k,bot if sd else tuple(int(c*.82) for c in bot[:3])+(255,))
        cv.ell(foot[0]+f*8*k,foot[1],17*k,8*k,shoe)
    # torso
    if kind in (1,3):
        cv.blob([T(-20,-h*.98),T(24,-h*.98),T(40,-h*.5),T(-38,-h*.5)],top,None,0,6)
    else:
        cv.blob([T(-26,-h*1.02),T(26,-h*1.02),T(30,-h*.5),T(-30,-h*.5)],top,(40,40,48,255),1.5,6)
        cv.poly([T(-6,-h*1.0),T(6,-h*1.0),T(0,-h*.7)],(236,230,214,255))
    sw=math.sin(phase)*walk
    for sd,col in ((1,top),(0,tuple(int(c*.85) for c in top[:3])+(255,))):
        sh=T(0,-h*.96); sgn=1 if sd else -1; hd=T(sw*30*sgn,-h*.52)
        cv.line([sh,hd],14*k,col); cv.ell(hd[0],hd[1],8*k,8*k,skin)
    cv.line([T(0,-h*1.0),T(0,-h*1.06)],14*k,skin)
    hc=T(2,-h*1.14); cv.ell(hc[0],hc[1],20*k,23*k,skin,0,None,0)
    cv.ell(hc[0]+f*8*k,hc[1]-3*k,2.8*k,2.8*k,(30,24,22,255))
    if kind in (0,):  # sombrero fedora
        cv.ell(hc[0],hc[1]-18*k,34*k,8*k,(60,56,60,255)); cv.blob([(hc[0]-20*k,hc[1]-18*k),(hc[0]-16*k,hc[1]-42*k),(hc[0]+16*k,hc[1]-42*k),(hc[0]+20*k,hc[1]-18*k)],(70,66,70,255),None,0,6)
    elif kind==1:
        cv.ell(hc[0],hc[1]-20*k,30*k,9*k,(120,30,40,255)); cv.ell(hc[0],hc[1]-30*k,16*k,12*k,(150,40,50,255))
    elif kind==2:
        cv.ell(hc[0],hc[1]-14*k,24*k,16*k,(100,80,60,255)); cv.poly([(hc[0]+f*4*k,hc[1]-6*k),(hc[0]+f*34*k,hc[1]-4*k),(hc[0]+f*30*k,hc[1])],(80,60,44,255))
    elif kind==3: cv.ell(hc[0]-f*4*k,hc[1]-8*k,24*k,22*k,(80,52,40,255),0,None,0); cv.ell(hc[0]+f*4*k,hc[1]+2*k,18*k,20*k,skin)
    elif kind==4: cv.ell(hc[0],hc[1]-14*k,22*k,13*k,(90,60,40,255))

def car(cv,x,y,sc,col=(66,128,128,255),rot=0.0,crate=False):
    k=sc; 
    def P(pts): return [(x+px*k,y+py*k) for px,py in pts]
    cv.ell(x,y+4*k,250*k,16*k,(0,0,0,70))
    dark=tuple(int(c*.72) for c in col[:3])+(255,)
    if crate:
        cv.rect(x-60*k,y-232*k,x+70*k,y-176*k,(176,130,80,255),(100,70,40,255),3)
        for i in range(1,6): cv.line([(x-60*k+i*22*k,y-232*k),(x-60*k+i*22*k,y-176*k)],2*k,(120,86,50,255),False)
        cv.line([(x-80*k,y-180*k),(x+90*k,y-180*k)],6*k,(60,50,44,255),False)
    # cabina
    cv.blob(P([(-130,-120),(-96,-190),(-30,-212),(70,-208),(124,-170),(150,-120)]),col,dark,3,8)
    cv.blob(P([(-112,-124),(-84,-178),(-34,-198),(0,-198),(0,-124)]),(190,224,230,255),dark,2,6)
    cv.blob(P([(12,-124),(12,-198),(66,-196),(108,-166),(128,-124)]),(190,224,230,255),dark,2,6)
    # carrocería
    cv.blob(P([(-230,-70),(-226,-120),(-170,-130),(-60,-122),(100,-122),(190,-116),(238,-96),(246,-70),(240,-40),(-224,-40)]),col,dark,3,8)
    cv.line(P([(-210,-82),(230,-82)]),4*k,(240,236,220,255),False)
    # parachoques y faro
    cv.rect(x+232*k,y-72*k,x+260*k,y-54*k,(220,220,214,255),(120,120,120,255),2); cv.rect(x-250*k,y-72*k,x-224*k,y-54*k,(220,220,214,255),(120,120,120,255),2)
    cv.ell(x+224*k,y-100*k,14*k,16*k,(255,244,200,255),0,(150,140,110,255),2)
    # ruedas
    for wx_ in (-150,150):
        cx_,cy_=x+wx_*k,y-34*k
        cv.ell(cx_,cy_,52*k,52*k,(30,30,34,255)); cv.ell(cx_,cy_,34*k,34*k,(236,232,220,255)); cv.ell(cx_,cy_,20*k,20*k,(180,176,168,255))
        for i in range(6):
            a=rot+i*math.pi/3; cv.line([(cx_,cy_),(cx_+math.cos(a)*30*k,cy_+math.sin(a)*30*k)],3*k,(120,116,110,255),False)

def saguaro(cv,x,y,s,col=(66,112,72,255),dk=(44,82,52,255)):
    def arm(sx,sy,dx,up,w):
        cv.line([(sx,sy),(sx+dx,sy),(sx+dx,sy-up)],w,col)
    cv.ell(x,y+4*s,60*s,8*s,(0,0,0,50))
    cv.line([(x,y),(x,y-300*s)],46*s,col)
    cv.line([(x-8*s,y-20*s),(x-8*s,y-280*s)],4*s,dk,False)
    arm(x-6*s,y-150*s,-80*s,100*s,30*s); arm(x+6*s,y-200*s,90*s,90*s,30*s)

def mesa(cv,x,y,w,h,col):
    cv.poly([(x-w/2,y),(x-w*.4,y-h),(x-w*.32,y-h-10),(x+w*.3,y-h-10),(x+w*.4,y-h),(x+w/2,y)],col)

def neon(cv,x,y,text_img,glow=(255,60,140),a=140):
    pass
