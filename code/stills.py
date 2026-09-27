import sys, skia, numpy as np
from PIL import Image
import scenes
from lib import W,H
ts=[float(x) for x in sys.argv[2:]]
s=skia.Surface(W,H); c=s.getCanvas()
ims=[]
for t in ts:
    c.clear(0); scenes.frame(c,t)
    a=s.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType)[...,:3]
    ims.append(Image.fromarray(a).resize((640,360)))
cols=3; rows=(len(ims)+2)//3
sheet=Image.new('RGB',(640*cols,360*rows),'white')
for i,im in enumerate(ims): sheet.paste(im,((i%cols)*640,(i//cols)*360))
sheet.save(sys.argv[1])
