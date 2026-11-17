# -*- coding: utf-8 -*-
"""Renderiza los 1800 fotogramas en paralelo y los codifica con FFmpeg (H.264) por tramos."""
import os, sys, subprocess, multiprocessing as mp
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'build')
CH = 60  # fotogramas por tramo


def work(k):
    from scenes import render_frame
    f0, f1 = k * CH, min(1800, (k + 1) * CH)
    path = os.path.join(OUT, 'seg_%02d.mp4' % k)
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '1080x1920', '-r', '30',
                          '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', '-g', '30',
                          '-bf', '2', '-an', path], stdin=subprocess.PIPE)
    for i in range(f0, f1):
        p.stdin.write(render_frame(i).tobytes())
    p.stdin.close(); p.wait()
    return k


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    n = 1800 // CH
    with mp.Pool(4) as pool:
        for k in pool.imap_unordered(work, range(n)):
            print('tramo', k, 'listo', flush=True)
    with open(os.path.join(OUT, 'list.txt'), 'w') as f:
        for k in range(n):
            f.write("file 'seg_%02d.mp4'\n" % k)
    subprocess.check_call(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', os.path.join(OUT, 'list.txt'),
                           '-c', 'copy', os.path.join(OUT, 'video_mudo.mp4')])
    print('video listo')
