import sys, os, subprocess
from multiprocessing import Pool
from compose import render_chunk
d = sys.argv[1]; starts = [int(x) for x in sys.argv[2].split(',')]
jobs = [(s, s + 90, os.path.join(d, f"seg_{s:05d}.mp4")) for s in starts]
with Pool(4) as p: print(p.map(render_chunk, jobs))
subprocess.check_call(["ffmpeg","-y","-loglevel","error","-f","concat","-safe","0","-i",os.path.join(d,"list.txt"),"-c","copy",os.path.join(d,"video_noaudio.mp4")])
print("done")
