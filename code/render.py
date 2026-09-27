import subprocess, skia, sys, time
import scenes
from lib import W,H,FPS
a,b=int(sys.argv[1]),int(sys.argv[2])
p=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgba','-s',f'{W}x{H}','-r',str(FPS),'-i','-',
  '-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p',f'part_{a:04d}.mp4'],stdin=subprocess.PIPE)
s=skia.Surface(W,H); c=s.getCanvas(); st=time.time()
for f in range(a,b):
    c.clear(0); scenes.frame(c,f/FPS)
    p.stdin.write(s.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType).tobytes())
p.stdin.close(); p.wait(); print('chunk',a,b,'sec',round(time.time()-st))
