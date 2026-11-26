import sys, time, importlib
sys.path.insert(0,'.')
from common import *
SCR='/tmp/claude-0/-home-user-MoneyPrinterTurbo/9e76ab43-2e93-5f90-8b5a-0f7608749ee4/scratchpad/'
def sheet(fn, times, name, cols=4, scale=0.34):
    ims=[]
    for t in times:
        t0=time.time(); a=fn(t); dt=time.time()-t0
        im=Image.fromarray(to_uint8(a)).resize((int(W*scale),int(H*scale)),Image.LANCZOS); ims.append(im); print(name,t,round(dt,2))
    rows=(len(ims)+cols-1)//cols
    sh=Image.new('RGB',(cols*ims[0].width,rows*ims[0].height))
    for i,im in enumerate(ims): sh.paste(im,((i%cols)*im.width,(i//cols)*im.height))
    sh.save(SCR+name+'.png')
if __name__=='__main__':
    mod,fn,name=sys.argv[1:4]; times=[float(x) for x in sys.argv[4].split(',')]
    sheet(getattr(importlib.import_module(mod),fn),times,name)
