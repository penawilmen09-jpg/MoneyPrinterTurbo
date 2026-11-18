import sys, os, subprocess, time
import numpy as np
from multiprocessing import Pool
FPS = 24; N = 1440
def work(i):
    import timeline
    return i, timeline.frame_at(i / FPS).tobytes()

if __name__ == '__main__':
    a = int(sys.argv[1]) if len(sys.argv) > 1 else 0; b = int(sys.argv[2]) if len(sys.argv) > 2 else N
    out = sys.argv[3] if len(sys.argv) > 3 else 'build/video_silent.mp4'
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '1080x1920', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '13', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', '-an', out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE); t0 = time.time()
    with Pool(4) as pool:
        for k, (i, buf) in enumerate(pool.imap(work, range(a, b), chunksize=2)):
            p.stdin.write(buf)
            if k % 48 == 0: print(f'{k}/{b-a} {time.time()-t0:.0f}s', flush=True)
    p.stdin.close(); p.wait(); print('done', time.time() - t0)
