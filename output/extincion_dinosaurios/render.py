#!/usr/bin/env python3
"""LA EXTINCIÓN DE LOS DINOSAURIOS - documental 2D de 60 s (1080x1920, 30 fps), sin voz.

Uso:
  python render.py --preview 2.5 12.5 ...   # PNG de cuadros sueltos (segundos)
  python render.py                           # renderiza el MP4 completo + SRT
"""
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import H, W, clamp, prog, sm  # noqa: E402
from scenes import scene_cam  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
FPS, DUR = 30, 60
NF = FPS * DUR
TITLE = "LA EXTINCIÓN DE LOS DINOSAURIOS"
SUBS = [
    "Hace 66 millones de años, los dinosaurios dominaban la Tierra.",
    "Enormes criaturas caminaban por bosques y llanuras.",
    "Algunos eran gigantescos depredadores, como el Tiranosaurio Rex.",
    "Pero algo terrible estaba a punto de suceder.",
    "Un enorme asteroide viajaba directamente hacia nuestro planeta.",
    "Su impacto ocurrió cerca de la actual península de Yucatán.",
    "Una explosión gigantesca sacudió la Tierra.",
    "El fuego y los terremotos devastaron enormes regiones.",
    "El polvo y los gases bloquearon gran parte de la luz solar.",
    "Las temperaturas descendieron y muchas plantas desaparecieron.",
    "Los ecosistemas colapsaron y desapareció cerca del 75 % de las especies.",
    "Así terminó la era de los dinosaurios no avianos y comenzó una nueva etapa de la vida.",
]
FONT_PATH = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
SUB_SIZE, SUB_STROKE, SUB_MAXW, SUB_BOTTOM = 66, 9, 960, 1690


def srt_time(s):
    ms = int(round(s * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def wrap(text, font, maxw):
    words, lines, cur = text.split(" "), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if font.getlength(trial) <= maxw or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    # evita una ultima linea con una sola palabra
    if len(lines) > 1 and " " not in lines[-1] and len(lines) > 1:
        prev = lines[-2].split(" ")
        if len(prev) > 2:
            lines[-1] = prev[-1] + " " + lines[-1]
            lines[-2] = " ".join(prev[:-1])
    return lines


_cache = {}


def text_block(text, size=SUB_SIZE, stroke=SUB_STROKE, maxw=SUB_MAXW):
    key = (text, size)
    if key in _cache:
        return _cache[key]
    font = ImageFont.truetype(FONT_PATH, size)
    lines = wrap(text, font, maxw)
    lh = int(size * 1.22)
    h = lh * len(lines) + stroke * 2 + 10
    im = Image.new("RGBA", (W, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i, ln in enumerate(lines):
        w = font.getlength(ln)
        d.text(((W - w) / 2, stroke + i * lh), ln, font=font, fill=(255, 255, 255, 255), stroke_width=stroke,
               stroke_fill=(0, 0, 0, 255))
    _cache[key] = im
    return im


_post = {}


def post_arrays():
    if "vig" not in _post:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        dist = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
        vig = 1 - .38 * np.clip((dist - .55) / .9, 0, 1) ** 1.6
        bot = np.clip((yy - 1280) / 520, 0, 1)
        vig = vig * (1 - .5 * bot ** 1.3)
        _post["vig"] = vig[..., None].astype(np.float32)
        rnd = np.random.RandomState(1)
        _post["noise"] = [rnd.normal(0, 3.2, (H, W, 1)).astype(np.float32) for _ in range(4)]
    return _post


def finish(img, i, T):
    P = post_arrays()
    arr = np.asarray(img, dtype=np.float32)
    arr = arr * P["vig"] + P["noise"][i % 4]
    # pequeno realce de contraste cinematografico
    arr = (arr - 128) * 1.05 + 128
    out = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")
    # fundido inicial desde negro
    if T < .6:
        out = Image.blend(Image.new("RGB", out.size, (0, 0, 0)), out, sm(T / .6))
    return out


def overlay_text(out, T):
    k = min(int(T // 5), 11)
    t = T - 5 * k
    blk = text_block(SUBS[k])
    a = clamp(min(t, 5 - t) / .12) if k > 0 or t > 0 else 1
    a = 1.0 if (k == 0 and t < .6) else a
    if a < 1:
        blk = blk.copy()
        blk.putalpha(blk.getchannel("A").point(lambda v: int(v * a)))
    out.paste(blk, (0, SUB_BOTTOM - blk.height), blk)
    if T < 3.9:
        tb = text_block(TITLE, 74, 8, 940)
        ta = sm(prog(T, .5, 1.1)) * (1 - sm(prog(T, 3.2, 3.9)))
        if ta > 0:
            tb = tb.copy()
            tb.putalpha(tb.getchannel("A").point(lambda v: int(v * ta)))
            out.paste(tb, (0, 250), tb)


def frame(i):
    T = i / FPS
    k = min(int(T // 5), 11)
    t = T - 5 * k
    half = .25
    img = scene_cam(k, t)
    if t < half and k > 0:
        other = scene_cam(k - 1, t + 5)
        a = sm((t + half) / (2 * half))
        img = Image.blend(other, img, a)
    elif t > 5 - half and k < 11:
        other = scene_cam(k + 1, t - 5)
        a = sm((t - (5 - half)) / (2 * half))
        img = Image.blend(img, other, a)
    out = finish(img, i, T)
    overlay_text(out, T)
    return out


def raw(i):
    return frame(i).tobytes()


def write_srt():
    p = os.path.join(HERE, "subtitulos.srt")
    with open(p, "w", encoding="utf-8") as f:
        for n, s in enumerate(SUBS):
            f.write(f"{n + 1}\n{srt_time(n * 5)} --> {srt_time(n * 5 + 5)}\n{s}\n\n")
    return p


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--preview":
        out = os.environ.get("PREVIEW_DIR", HERE)
        for a in sys.argv[2:]:
            T = float(a)
            frame(int(round(T * FPS))).save(os.path.join(out, f"prev_{T:06.2f}.png"))
        return
    write_srt()
    dst = os.path.join(HERE, "LA_EXTINCION_DE_LOS_DINOSAURIOS.mp4")
    ff = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
          "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", str(DUR),
          "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", "-profile:v", "high",
          "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", "-metadata", "title=La extincion de los dinosaurios", dst]
    p = subprocess.Popen(ff, stdin=subprocess.PIPE)
    with Pool(4) as pool:
        for n, b in enumerate(pool.imap(raw, range(NF), chunksize=15)):
            p.stdin.write(b)
            if n % 150 == 0:
                print(f"{n}/{NF}", flush=True)
    p.stdin.close()
    p.wait()
    print("OK", dst)


if __name__ == "__main__":
    main()
