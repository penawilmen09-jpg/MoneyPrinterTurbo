import sys, importlib
from PIL import Image
def sheet(fn, times, out, cols=None, scale=.28):
    ims = [fn(t).resize((int(1080*scale), int(1920*scale))) for t in times]
    cols = cols or len(ims); rows = (len(ims)+cols-1)//cols; w,h = ims[0].size
    S = Image.new('RGB',(w*cols,h*rows),(0,0,0))
    for i,im in enumerate(ims): S.paste(im,((i%cols)*w,(i//cols)*h))
    S.save(out)
