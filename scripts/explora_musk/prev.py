import sys, importlib, time
sys.path.insert(0,'.')
from stage import *
SCR='/tmp/claude-0/-home-user-MoneyPrinterTurbo/9e76ab43-2e93-5f90-8b5a-0f7608749ee4/scratchpad/'
mod,fn,name=sys.argv[1:4]; times=[float(x) for x in sys.argv[4].split(',')]
f=getattr(importlib.import_module(mod),fn); ims=[]
for t in times:
    t0=time.time(); a=f(t); print(name,t,round(time.time()-t0,2))
    ims.append(Image.fromarray(to_uint8(a)).resize((int(W*.3),int(H*.3)),Image.LANCZOS))
cols=min(len(ims),6); rows=(len(ims)+cols-1)//cols
sh=Image.new('RGB',(cols*ims[0].width,rows*ims[0].height))
for i,im in enumerate(ims): sh.paste(im,((i%cols)*im.width,(i//cols)*im.height))
sh.save(SCR+name+'.png')
