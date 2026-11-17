"""Renderiza los 1800 fotogramas (60 s @ 30 fps, 1080x1920) en paralelo -> video_silent.mp4"""
import os, sys, subprocess, time
from multiprocessing import Pool
from PIL import Image
from gfx import W, H, post, sm
import scenes_a, scenes_b

FPS, DUR = 30, 60
STARTS = [0, 7, 14, 21, 28, 36, 44, 52, 60]
SCENES = [scenes_a.s1, scenes_a.s2, scenes_a.s3, scenes_a.s4, scenes_b.s5, scenes_b.s6, scenes_b.s7, scenes_b.s8]
DISS = 0.3
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")


def frame(n):
    t = n / FPS
    i = max(k for k in range(8) if STARTS[k] <= t)
    img = SCENES[i](t - STARTS[i])
    if i < 7 and t > STARTS[i + 1] - DISS:
        nxt = SCENES[i + 1](max(0.0, t - STARTS[i + 1]))
        img = Image.blend(img, nxt, sm((t - (STARTS[i + 1] - DISS)) / (2 * DISS)))
    elif i > 0 and t < STARTS[i] + DISS:
        prev = SCENES[i - 1](t - STARTS[i - 1])
        img = Image.blend(prev, img, sm((t - (STARTS[i] - DISS)) / (2 * DISS)))
    fade = min(1.0, t / 0.8, max(0.0, (DUR - t) / 1.0))
    return post(img, n, fade=fade)


def chunk(args):
    k, f0, f1 = args
    path = f"{OUT}/seg_{k}.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "16",
                          "-pix_fmt", "yuv420p", "-g", "30", path], stdin=subprocess.PIPE)
    for n in range(f0, f1):
        p.stdin.write(frame(n).tobytes())
    p.stdin.close()
    p.wait()
    return path


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    total = FPS * DUR
    nchunks = 24
    per = total // nchunks
    jobs = [(k, k * per, (k + 1) * per) for k in range(nchunks)]
    t0 = time.time()
    with Pool(4) as pool:
        for r in pool.imap(chunk, jobs):
            print("listo", r, round(time.time() - t0), "s", flush=True)
    with open(f"{OUT}/list.txt", "w") as f:
        for k in range(nchunks):
            f.write(f"file 'seg_{k}.mp4'\n")
    subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", f"{OUT}/list.txt", "-c", "copy", f"{OUT}/video_silent.mp4"])
    print("VIDEO OK", round(time.time() - t0), "s")
