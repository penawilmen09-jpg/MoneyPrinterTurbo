"""Línea de tiempo, subtítulos y renderizado del video.

Uso:
  render.py still <segundos> <salida.png>
  render.py sheet <salida.png>            (hoja de contacto)
  render.py video <salida_sin_audio.mp4>
"""
import json
import os
import subprocess
import sys
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(__file__))
from lib import *
import scenes as sc

WORK = os.environ.get("STORY_WORK", "/home/user/MoneyPrinterTurbo/output_story/work")
LEAD = 1.2
TAIL = 8.5
AL = json.load(open(f"{WORK}/align.json"))
TEXT = AL["text"]
ST = AL["alignment"]["character_start_times_seconds"]
EN = AL["alignment"]["character_end_times_seconds"]


def A(s):
    i = TEXT.find(s)
    assert i >= 0, s
    return ST[i] + LEAD


a_pens, a_dec, a_del = A("Al principio"), A("Decidió"), A("Del otro")
a_conf, a_corto, a_msg = A("Confundido"), A("Pero la llamada"), A("Unos segundos")
a_acerco, a_vio, a_alg = A("Cuando se acercó"), A("vio un automóvil"), A("alguien dentro")
a_asust, a_lleg, a_nunca, a_desde = A("Asustado"), A("Cuando llegaron"), A("Nunca descubrió"), A("Pero desde")
a_end = EN[-1] + LEAD
TOTAL = a_end + TAIL
END_CARD = 1.9

SHOTS = [
    (0.0, 2.7, sc.s_hook_wide),
    (2.7, 5.6, sc.s_hook_bust),
    (5.6, a_pens, sc.s_hook_phone),
    (a_pens, a_pens + 2.6, sc.s_skeptic),
    (a_pens + 2.6, a_dec, sc.s_number),
    (a_dec, a_del, sc.s_decide),
    (a_del, a_conf, sc.s_listen),
    (a_conf, a_corto, sc.s_speak),
    (a_corto, a_msg, sc.s_ended),
    (a_msg, a_msg + 2.1, sc.s_read),
    (a_msg + 2.1, a_acerco - 1.07, sc.s_msg),
    (a_acerco - 1.07, a_vio, sc.s_walk),
    (a_vio, a_alg, sc.s_street),
    (a_alg, a_asust, sc.s_silhouette),
    (a_asust, a_lleg, sc.s_call_police),
    (a_lleg, a_nunca, sc.s_patrol),
    (a_nunca, a_desde, sc.s_watch),
    (a_desde, a_desde + 3.0, sc.s_unknown),
    (a_desde + 3.0, a_end, sc.s_glance),
    (a_end, a_end + 2.4, sc.s_final_phone),
    (a_end + 2.4, TOTAL, sc.s_final_bust),
]
XF = 0.16


def shot_at(t):
    for i, (a, b, f) in enumerate(SHOTS):
        if a <= t < b:
            return i
    return len(SHOTS) - 1


def frame_scene(t):
    i = shot_at(t)
    a, b, f = SHOTS[i]
    img = f(t - a, b - a)
    if i > 0 and t - a < XF:
        pa, pb, pf = SHOTS[i - 1]
        prev = pf(pb - pa - 0.04, pb - pa)
        img = Image.blend(prev, img, ease((t - a) / XF))
    return img


# --- subtítulos ------------------------------------------------------------------
def build_words():
    words, cur = [], None
    for i, ch in enumerate(TEXT):
        if ch in " \n":
            if cur:
                words.append(cur)
                cur = None
            continue
        if cur is None:
            cur = [ch, ST[i] + LEAD, EN[i] + LEAD]
        else:
            cur[0] += ch
            cur[2] = EN[i] + LEAD
    if cur:
        words.append(cur)
    return words


def build_chunks():
    words = build_words()
    chunks, cur = [], []
    for w in words:
        cur.append(w)
        L = sum(len(x[0]) + 1 for x in cur)
        end = w[0][-1] in ".,:;?…”»!"
        if end or L >= 22 or len(cur) >= 4:
            if end or L >= 15:
                chunks.append(cur)
                cur = []
    if cur:
        chunks.append(cur)
    return chunks


CHUNKS = build_chunks()


def draw_subs(img, t):
    # trozo activo
    act = None
    for i, ch in enumerate(CHUNKS):
        s0 = ch[0][1] - 0.04
        s1 = CHUNKS[i + 1][0][1] - 0.04 if i + 1 < len(CHUNKS) else ch[-1][2] + 0.5
        s1 = min(s1, ch[-1][2] + 0.7)
        if s0 <= t < s1:
            act = ch
            break
    if not act:
        return
    f = font(66, True)
    d = ImageDraw.Draw(img, "RGBA")
    words = [w[0] for w in act]
    # dos líneas si hace falta
    lines, cur = [], []
    for w in words:
        test = " ".join(cur + [w])
        if d.textlength(test, font=f) > 900 and cur:
            lines.append(cur)
            cur = [w]
        else:
            cur.append(w)
    lines.append(cur)
    y = 1585 - (len(lines) - 1) * 40
    idx = 0
    for ln in lines:
        txt = " ".join(ln)
        tw = d.textlength(txt, font=f)
        x = (W - tw) / 2
        for j, w in enumerate(ln):
            cw = act[idx]
            on = cw[1] - 0.02 <= t < cw[2] + 0.12
            col = (255, 222, 96) if on else (255, 255, 255)
            d.text((x, y), w, font=f, fill=col, anchor="lm", stroke_width=9, stroke_fill=(8, 8, 18))
            x += d.textlength(w + " ", font=f)
            idx += 1
        y += 84


def draw_overlays(img, t):
    d = ImageDraw.Draw(img, "RGBA")
    if t < 4.2:
        a = int(210 * min(1, (4.2 - t) / 0.6, t / 0.4 + 0.01))
        f = font(30, True)
        txt = "HISTORIA DE FICCIÓN · SUSPENSO"
        tw = d.textlength(txt, font=f)
        d.rounded_rectangle([W / 2 - tw / 2 - 28, 108, W / 2 + tw / 2 + 28, 164], radius=28, fill=(10, 10, 24, int(a * 0.7)))
        d.text((W / 2, 137), txt, font=f, fill=(235, 238, 255, a), anchor="mm")
    # tarjeta final
    u = clamp((t - (TOTAL - END_CARD)) / 0.7)
    if u > 0:
        d.rectangle([0, 0, W, H], fill=(4, 4, 10, int(255 * ease(u))))
        if u > 0.5:
            v = ease((u - 0.5) / 0.5)
            d.text((W / 2, 880), "EXPLORA CIENCIA 360", font=font(70, True), fill=(235, 240, 255, int(255 * v)), anchor="mm")
            d.line([(W / 2 - 220, 940), (W / 2 + 220, 940)], fill=(120, 150, 255, int(255 * v)), width=4)
            d.text((W / 2, 1000), "Historia de ficción · Suspenso", font=font(36, False), fill=(190, 200, 235, int(255 * v)), anchor="mm")


def render_frame(fi):
    t = fi / FPS
    img = frame_scene(t)
    img = postfx(img, fi)
    if t < TOTAL - END_CARD * 0.6:
        draw_subs(img, t)
    draw_overlays(img, t)
    return img


def _rf(fi):
    return render_frame(fi).tobytes()


def main():
    cmd = sys.argv[1]
    if cmd == "still":
        t = float(sys.argv[2])
        render_frame(int(t * FPS)).save(sys.argv[3])
    elif cmd == "sheet":
        ts = [float(x) for x in sys.argv[3].split(",")]
        tw, th = 270, 480
        sheet = Image.new("RGB", (tw * 6, th * ((len(ts) + 5) // 6)))
        for i, t in enumerate(ts):
            sheet.paste(render_frame(int(t * FPS)).resize((tw, th), Image.LANCZOS), ((i % 6) * tw, (i // 6) * th))
        sheet.save(sys.argv[2])
    elif cmd == "video":
        out = sys.argv[2]
        n = int(TOTAL * FPS)
        ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                               "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "17",
                               "-pix_fmt", "yuv420p", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
        with Pool(4) as p:
            for i, b in enumerate(p.imap(_rf, range(n), chunksize=2)):
                ff.stdin.write(b)
                if i % 100 == 0:
                    print("frame", i, "/", n, flush=True)
        ff.stdin.close()
        ff.wait()
        print("listo", out, "duración", TOTAL)
    elif cmd == "info":
        print("TOTAL", TOTAL)
        for a, b, f in SHOTS:
            print(f"{a:6.2f}-{b:6.2f} {f.__name__}")
        for ch in CHUNKS:
            print(f"{ch[0][1]:6.2f} " + " ".join(w[0] for w in ch))


if __name__ == "__main__":
    main()
