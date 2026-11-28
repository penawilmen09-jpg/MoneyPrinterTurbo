"""Escenarios 2D procedurales.

Cada escenario pinta un fondo estático grande (se cachea por escena) más
elementos dinámicos (monitores, coches, reloj, burbujas...) que se dibujan
cada fotograma con la cámara aplicada.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from PIL import Image

from .gfx import Canvas, mix, products_row, shade

W, H = 1080, 1920
SLOTS = {
    "far_left": 150, "left": 280, "center_left": 410, "center": 540,
    "center_right": 670, "right": 800, "far_right": 930,
}


@dataclass
class SetInfo:
    name: str
    floor_y: float = 1330  # pies de personajes en primer plano
    behind_floor_y: float = 1230  # pies de personajes "detrás" del mostrador
    extras_y: float = 1090  # pies de figurantes de fondo
    extras_scale: float = 0.34
    char_scale: float = 0.78
    has_fg: bool = False
    counter_top: float = 0  # y de la superficie del mostrador (anclaje 'counter')
    wall_y: float = 1000


class DynCanvas:
    """Dibuja en pantalla con coordenadas de mundo (transformadas por la cámara)."""

    def __init__(self, draw, cam):
        self.d, self.cam = draw, cam

    def _p(self, x, y):
        return self.cam.w2s(x, y)

    def rect(self, x0, y0, x1, y1, fill=None, outline=None, width=1):
        a, b = self._p(x0, y0), self._p(x1, y1)
        self.d.rectangle([a[0], a[1], b[0], b[1]], fill=fill, outline=outline, width=max(1, int(width * self.cam.z)))

    def ellipse(self, cx, cy, rx, ry, fill=None, outline=None, width=1):
        a, b = self._p(cx - rx, cy - ry), self._p(cx + rx, cy + ry)
        self.d.ellipse([a[0], a[1], b[0], b[1]], fill=fill, outline=outline, width=max(1, int(width * self.cam.z)))

    def poly(self, pts, fill=None, outline=None):
        self.d.polygon([self._p(x, y) for x, y in pts], fill=fill, outline=outline)

    def line(self, pts, fill, width=2):
        self.d.line([self._p(x, y) for x, y in pts], fill=fill, width=max(1, int(width * self.cam.z)))

    def text(self, x, y, s, size, fill, anchor="mm"):
        from .gfx import font
        self.d.text(self._p(x, y), s, font=font(size * self.cam.z), fill=fill, anchor=anchor)


# ===========================================================================
class BaseSet:
    info = SetInfo("base")

    def paint(self, c: Canvas, variant: int = 0, tod: str = "day"):  # pragma: no cover
        raise NotImplementedError

    def paint_fg(self, c: Canvas, variant: int = 0) -> None:
        return None

    def dynamic(self, dc: DynCanvas, t: float) -> None:
        return None

    # ------- utilidades comunes ------------------------------------------------
    @staticmethod
    def ceiling_lights(c: Canvas, y=70, n=3, w=300, h=36, glow=True):
        for i in range(n):
            cx = W * (i + 0.5) / n
            if glow:
                c.glow(cx, y + 40, w * 0.9, (255, 250, 220), 70)
            c.rrect(cx - w / 2, y, cx + w / 2, y + h, 8, fill=(252, 252, 245), outline=(200, 200, 205), width=2)

    @staticmethod
    def floor_tiles(c: Canvas, y0, base=(224, 226, 232), alt=(205, 208, 216), vp=(540, 640)):
        c.gradient_v(0, y0, W, H, base, shade(base, 0.82))
        n = 14
        for i in range(-n, n + 1):
            xb = 540 + i * 160
            c.line([(vp[0] + (xb - vp[0]) * 0.18, y0), (xb, H)], fill=alt + (200,), width=2)
        y = y0
        step = 18
        while y < H:
            c.line([(0, y), (W, y)], fill=alt + (170,), width=2)
            step *= 1.28
            y += step


# ===========================================================================
class SupermarketAisle(BaseSet):
    info = SetInfo("supermarket_aisle", floor_y=1340, extras_y=1070, extras_scale=0.3)

    def paint(self, c, variant=0, tod="day"):
        c.rect(0, 0, W, H, fill=(240, 236, 226))
        # techo
        c.gradient_v(0, 0, W, 330, (250, 250, 248), (226, 230, 236))
        self.ceiling_lights(c, y=64, n=3, w=300)
        # pared del fondo
        c.rect(0, 330, W, 1010, fill=(246, 238, 222))
        # estanterías del fondo (3 módulos)
        for i, (x0, x1) in enumerate(((190, 500), (580, 890))):
            c.rect(x0, 420, x1, 1010, fill=(205, 210, 220), outline=(150, 156, 170), width=3)
            for r in range(4):
                yb = 520 + r * 140
                products_row(c, x0 + 6, x1 - 6, yb, 110, seed=variant * 31 + i * 7 + r)
                c.rect(x0, yb, x1, yb + 12, fill=(240, 90, 60) if r % 2 else (250, 190, 70))
        # puerta del almacén al fondo
        c.rect(500, 560, 580, 1010, fill=(170, 150, 120), outline=(110, 92, 70), width=3)
        # góndolas laterales con perspectiva
        vp = (540, 640)
        for sgn in (-1, 1):
            xo = 0 if sgn < 0 else W
            xi = 230 if sgn < 0 else W - 230
            c.poly([(xo, 140), (xi, 330), (xi, 1010), (xo, 1480)], fill=(215, 220, 232), outline=(140, 146, 164), width=4)
            for r in range(6):
                f0 = r / 6.0
                ya_o = 190 + f0 * 1250
                ya_i = 360 + f0 * 640
                col = (250, 190, 70) if r % 2 else (240, 90, 60)
                c.poly([(xo, ya_o), (xi, ya_i), (xi, ya_i + 14), (xo, ya_o + 38)], fill=col)
                # productos sobre el estante (aprox. en perspectiva)
                rng = random.Random(variant * 17 + r + (0 if sgn < 0 else 9))
                nprod = 7
                for k in range(nprod):
                    t0, t1 = k / nprod, (k + 0.78) / nprod
                    xa = xo + (xi - xo) * t0
                    xb = xo + (xi - xo) * t1
                    ya = ya_o + (ya_i - ya_o) * t0
                    yb = ya_o + (ya_i - ya_o) * t1
                    hh0 = (120 - 70 * t0)
                    hh1 = (120 - 70 * t1)
                    col = rng.choice([(232, 72, 60), (245, 160, 50), (250, 214, 72), (96, 184, 96), (64, 168, 200), (150, 90, 190)])
                    c.poly([(xa, ya), (xb, yb), (xb, yb - hh1), (xa, ya - hh0)], fill=col, outline=shade(col, 0.6), width=1.5)
        # carteles colgantes
        for x, txt, col in ((300, "LÁCTEOS", (60, 140, 220)), (780, "OFERTAS", (232, 72, 60))):
            c.line([(x - 90, 330), (x - 90, 250)], fill=(90, 90, 100), width=3)
            c.line([(x + 90, 330), (x + 90, 250)], fill=(90, 90, 100), width=3)
            c.rrect(x - 130, 330, x + 130, 410, 14, fill=col, outline=shade(col, 0.6), width=4)
            c.text(x, 372, txt, 46, (255, 255, 255))
        self.floor_tiles(c, 1010, base=(232, 232, 236), alt=(196, 200, 210), vp=vp)
        # reflejo de luz en el suelo
        c.glow(540, 1200, 460, (255, 255, 255), 55)


class Checkout(BaseSet):
    info = SetInfo("checkout", floor_y=1480, behind_floor_y=1250, extras_y=1030, extras_scale=0.3,
                   has_fg=True, counter_top=1105, char_scale=0.78)

    def paint(self, c, variant=0, tod="day"):
        c.rect(0, 0, W, H, fill=(240, 236, 226))
        c.gradient_v(0, 0, W, 320, (250, 250, 248), (228, 232, 238))
        self.ceiling_lights(c, y=60, n=3, w=300)
        c.rect(0, 320, W, 1010, fill=(240, 232, 216))
        # estanterías del fondo (desenfocadas/oscuras)
        for i, (x0, x1) in enumerate(((20, 330), (380, 700), (750, 1060))):
            c.rect(x0, 430, x1, 1010, fill=(198, 204, 216), outline=(150, 156, 170), width=3)
            for r in range(4):
                yb = 530 + r * 138
                products_row(c, x0 + 6, x1 - 6, yb, 105, seed=variant * 13 + i * 5 + r, density=0.9)
                c.rect(x0, yb, x1, yb + 10, fill=(240, 90, 60) if r % 2 else (250, 190, 70))
        # cartel de caja
        for x in (250, 830):
            c.line([(x, 320), (x, 250)], fill=(90, 90, 100), width=3)
        c.rrect(150, 330, 350, 420, 14, fill=(64, 168, 100), outline=(30, 100, 60), width=4)
        c.text(250, 375, "CAJA 3", 52, (255, 255, 255))
        c.rrect(730, 330, 930, 420, 14, fill=(232, 72, 60), outline=(130, 30, 30), width=4)
        c.text(830, 375, "OFERTAS", 46, (255, 255, 255))
        self.floor_tiles(c, 1010, base=(225, 226, 232), alt=(190, 194, 204), vp=(540, 660))
        c.glow(540, 1250, 520, (255, 255, 255), 50)

    def paint_fg(self, c, variant=0):
        top = self.info.counter_top
        # superficie del mostrador
        c.poly([(-40, top + 6), (W + 40, top + 6), (W + 40, top - 26), (-40, top - 26)], fill=(98, 100, 116), outline=(50, 52, 66), width=4)
        # cinta transportadora (izquierda)
        c.rrect(30, top - 26, 520, top - 4, 8, fill=(46, 48, 58), outline=(20, 20, 28), width=3)
        for x in range(50, 510, 34):
            c.line([(x, top - 24), (x - 10, top - 6)], fill=(72, 74, 88), width=3)
        # frente del mostrador
        c.rect(-40, top + 6, W + 40, 1420, fill=(240, 128, 70), outline=(120, 56, 24), width=4)
        c.rect(-40, top + 6, W + 40, top + 46, fill=(252, 160, 100))
        for x in range(0, W + 40, 120):
            c.rect(x + 8, top + 70, x + 104, 1390, fill=(226, 112, 58), outline=(140, 66, 30), width=2)
        c.rect(-40, 1420, W + 40, 1456, fill=(60, 62, 76))
        c.text(540, top + 24, "AUTOSERVICIO · CAJA RÁPIDA", 24, (120, 56, 24))

    def dynamic(self, dc, t):
        # barra de luz del lector (parpadeo)
        on = int(t * 2) % 2 == 0
        dc.rect(120, 1074, 400, 1080, fill=(255, 60, 60, 220 if on else 90))


class SecurityRoom(BaseSet):
    info = SetInfo("security_room", floor_y=1380, behind_floor_y=1330, extras_y=1090, has_fg=True, counter_top=1240)

    MON = [(70, 330), (400, 330), (730, 330), (70, 560), (400, 560), (730, 560)]
    MW, MH = 280, 190

    def paint(self, c, variant=0, tod="day"):
        c.gradient_v(0, 0, W, H, (24, 30, 48), (14, 18, 30))
        c.glow(540, 520, 700, (60, 120, 220), 90)
        # pared con paneles
        for x in range(0, W, 180):
            c.line([(x, 0), (x, 1100)], fill=(40, 48, 72), width=3)
        # banco de monitores
        c.rrect(40, 290, 1040, 790, 18, fill=(18, 22, 34), outline=(70, 84, 120), width=5)
        for (x, y) in self.MON:
            c.rrect(x - 8, y - 8, x + self.MW + 8, y + self.MH + 8, 10, fill=(8, 10, 16), outline=(90, 100, 130), width=3)
            c.rect(x, y, x + self.MW, y + self.MH, fill=(16, 38, 40))
        # cámara decorativa y luz roja de grabación
        c.rrect(60, 130, 260, 200, 12, fill=(60, 66, 84))
        # suelo
        self.floor_tiles(c, 1120, base=(46, 52, 72), alt=(32, 38, 56), vp=(540, 700))
        # escritorio
        c.rect(0, 1090, W, 1130, fill=(88, 96, 120), outline=(40, 46, 64), width=3)

    def paint_fg(self, c, variant=0):
        c.rect(-40, 1240, W + 40, 1500, fill=(70, 78, 102), outline=(30, 36, 52), width=4)
        c.rect(-40, 1240, W + 40, 1272, fill=(104, 114, 142))
        c.rrect(240, 1196, 840, 1240, 8, fill=(30, 32, 44), outline=(10, 10, 16), width=3)  # teclado
        for r in range(2):
            for k in range(20):
                c.rect(256 + k * 28, 1204 + r * 17, 276 + k * 28, 1216 + r * 17, fill=(64, 68, 86))

    def dynamic(self, dc, t):
        for i, (x, y) in enumerate(self.MON):
            rng = random.Random(i)
            tint = [(24, 60, 56), (20, 44, 70), (50, 40, 30), (30, 56, 44), (28, 40, 64), (56, 34, 44)][i]
            dc.rect(x, y, x + self.MW, y + self.MH, fill=tint)
            # suelo y puerta del "plano" de la cámara
            dc.rect(x, y + self.MH * 0.62, x + self.MW, y + self.MH, fill=shade(tint, 1.4))
            # persona moviéndose (silueta)
            px = x + 30 + ((t * (22 + i * 6) + rng.random() * 200) % (self.MW - 60))
            dc.ellipse(px, y + self.MH * 0.42, 9, 9, fill=(220, 220, 230))
            dc.rect(px - 10, y + self.MH * 0.5, px + 10, y + self.MH * 0.82, fill=(200, 205, 220))
            # línea de barrido
            sy = y + ((t * 60 + i * 30) % self.MH)
            dc.rect(x, sy, x + self.MW, sy + 3, fill=(255, 255, 255, 40))
            # REC parpadeante y hora
            if int(t * 1.6 + i) % 2 == 0:
                dc.ellipse(x + 16, y + 16, 6, 6, fill=(255, 50, 50))
            dc.text(x + 36, y + 17, "REC", 14, (255, 255, 255, 230), anchor="lm")
            dc.text(x + self.MW - 10, y + self.MH - 14, f"CAM 0{i + 1}  {int(t) % 60:02d}", 13, (210, 230, 255, 230), anchor="rm")
        # luz roja de la cámara de pared
        if int(t * 2) % 2 == 0:
            dc.ellipse(80, 165, 8, 8, fill=(255, 40, 40))


class Office(BaseSet):
    info = SetInfo("office", floor_y=1340, extras_y=1090, has_fg=True, counter_top=1200)

    def paint(self, c, variant=0, tod="day"):
        c.rect(0, 0, W, H, fill=(228, 222, 210))
        c.gradient_v(0, 0, W, 1010, (240, 232, 216), (226, 216, 196))
        # ventana con ciudad
        c.rrect(230, 190, 850, 720, 14, fill=(130, 190, 240), outline=(250, 250, 250), width=14)
        c.gradient_v(244, 204, 836, 706, (150, 205, 245) if tod != "night" else (20, 28, 60), (230, 242, 252) if tod != "night" else (40, 50, 90))
        rng = random.Random(5 + variant)
        for i in range(10):
            bx = 244 + i * 60
            bh = rng.randint(120, 380)
            col = (110, 130, 170) if tod != "night" else (30, 38, 70)
            c.rect(bx, 706 - bh, bx + 54, 706, fill=col, outline=shade(col, 0.8), width=2)
            for wy in range(int(706 - bh + 14), 700, 28):
                lit = rng.random() > 0.4 if tod == "night" else False
                c.rect(bx + 8, wy, bx + 20, wy + 12, fill=(255, 226, 120) if lit else shade(col, 1.2))
                c.rect(bx + 30, wy, bx + 42, wy + 12, fill=(255, 226, 120) if lit and rng.random() > 0.5 else shade(col, 1.2))
        c.line([(540, 190), (540, 720)], fill=(250, 250, 250), width=10)
        # estantería con libros
        c.rect(40, 330, 200, 960, fill=(120, 86, 60), outline=(70, 48, 32), width=4)
        for r in range(4):
            yb = 450 + r * 150
            x = 52
            rr = random.Random(r + variant)
            while x < 188:
                bw = rr.randint(14, 26)
                col = rr.choice([(200, 70, 60), (70, 120, 190), (230, 190, 70), (90, 160, 100), (140, 90, 170)])
                bh = rr.randint(70, 118)
                c.rect(x, yb - bh, x + bw, yb, fill=col, outline=shade(col, 0.6), width=1.5)
                x += bw + 1
            c.rect(40, yb, 200, yb + 12, fill=(90, 62, 42))
        # cuadro / diploma
        c.rect(890, 300, 1030, 430, fill=(250, 246, 232), outline=(120, 84, 50), width=8)
        c.line([(910, 340), (1010, 340)], fill=(150, 130, 90), width=4)
        c.line([(910, 370), (1010, 370)], fill=(150, 130, 90), width=4)
        c.line([(910, 395), (980, 395)], fill=(150, 130, 90), width=4)
        # reloj (las agujas son dinámicas)
        c.ellipse(940, 200, 50, 50, fill=(252, 252, 250), outline=(60, 60, 70), width=6)
        # planta
        c.rect(900, 880, 990, 990, fill=(190, 110, 70), outline=(110, 60, 36), width=4)
        for ang in range(-60, 61, 30):
            r = math.radians(ang)
            c.poly([(945, 880), (945 + math.sin(r) * 120 - 18, 880 - math.cos(r) * 170), (945 + math.sin(r) * 120 + 18, 880 - math.cos(r) * 170)], fill=(70, 160, 88), outline=(40, 110, 60), width=2)
        # luz de techo
        self.ceiling_lights(c, y=56, n=2, w=330)
        # suelo de madera
        c.gradient_v(0, 1010, W, H, (176, 130, 92), (140, 98, 66))
        for y in range(1010, H, 60):
            c.line([(0, y), (W, y)], fill=(120, 84, 56, 180), width=2)
        c.poly([(120, 1450), (960, 1450), (1040, 1800), (40, 1800)], fill=(150, 62, 70, 160))  # alfombra

    def paint_fg(self, c, variant=0):
        top = 1200
        c.rect(40, top, 1040, top + 40, fill=(122, 86, 56), outline=(70, 46, 30), width=4)
        c.rect(70, top + 40, 1010, 1460, fill=(150, 108, 74), outline=(70, 46, 30), width=4)
        c.rect(90, top + 70, 480, 1430, fill=(138, 98, 66), outline=(70, 46, 30), width=3)
        c.rect(600, top + 70, 990, 1430, fill=(138, 98, 66), outline=(70, 46, 30), width=3)
        for x in (480, 960):
            c.ellipse(x - 70, top + 250, 14, 14, fill=(230, 200, 100), outline=(130, 100, 40), width=2)

    def dynamic(self, dc, t):
        # agujas del reloj
        cx, cy = 940, 200
        a_s = t / 60 * math.tau - math.pi / 2
        a_m = t / 3600 * math.tau * 6 - math.pi / 2 + 1.1
        dc.line([(cx, cy), (cx + math.cos(a_m) * 30, cy + math.sin(a_m) * 30)], fill=(30, 30, 40), width=6)
        dc.line([(cx, cy), (cx + math.cos(a_s) * 38, cy + math.sin(a_s) * 38)], fill=(210, 50, 50), width=3)


class Street(BaseSet):
    info = SetInfo("street", floor_y=1380, extras_y=1130, extras_scale=0.36, wall_y=1090)

    def paint(self, c, variant=0, tod="day"):
        sky = {"day": ((120, 190, 245), (230, 242, 252)),
               "evening": ((250, 150, 90), (254, 214, 150)),
               "night": ((16, 22, 56), (46, 56, 110))}[tod]
        c.gradient_v(0, 0, W, 1090, sky[0], sky[1])
        if tod == "night":
            rng = random.Random(3)
            for _ in range(60):
                c.ellipse(rng.randint(0, W), rng.randint(0, 600), 2.2, 2.2, fill=(255, 255, 240, 220))
            c.ellipse(840, 260, 70, 70, fill=(250, 246, 214))
            c.ellipse(868, 246, 62, 62, fill=sky[0])
        else:
            c.ellipse(860, 250, 80, 80, fill=(255, 238, 150))
            c.glow(860, 250, 260, (255, 240, 170), 90)
        # edificios lejanos
        rng = random.Random(8 + variant)
        x = -20
        while x < W:
            bw, bh = rng.randint(110, 190), rng.randint(280, 640)
            col = mix((150, 165, 205), sky[0], 0.25) if tod != "night" else (30, 38, 76)
            c.rect(x, 1000 - bh, x + bw, 1000, fill=col, outline=shade(col, 0.85), width=2)
            for wy in range(int(1000 - bh + 20), 980, 38):
                for wx in range(int(x + 14), int(x + bw - 20), 34):
                    lit = tod == "night" and rng.random() > 0.45
                    c.rect(wx, wy, wx + 16, wy + 20, fill=(255, 226, 120) if lit else shade(col, 1.18))
            x += bw + rng.randint(4, 18)
        # supermercado (fachada)
        sx0, sx1 = 130, 950
        c.rect(sx0, 560, sx1, 1090, fill=(250, 244, 230), outline=(120, 110, 96), width=5)
        c.rect(sx0 - 14, 520, sx1 + 14, 600, fill=(232, 72, 60), outline=(130, 30, 30), width=5)
        c.text(540, 562, "SUPERMERCADO LA ESQUINA", 46, (255, 255, 255))
        # toldo
        for i in range(10):
            x0 = sx0 + i * (sx1 - sx0) / 10
            col = (255, 255, 255) if i % 2 else (232, 72, 60)
            c.poly([(x0, 600), (x0 + (sx1 - sx0) / 10, 600), (x0 + (sx1 - sx0) / 10 + 8, 690), (x0 - 8, 690)], fill=col, outline=(130, 30, 30), width=2)
        # vidrieras y puerta
        c.rect(sx0 + 40, 720, 440, 1060, fill=(150, 214, 240), outline=(90, 110, 120), width=6)
        c.rect(640, 720, sx1 - 40, 1060, fill=(150, 214, 240), outline=(90, 110, 120), width=6)
        c.rect(470, 720, 610, 1090, fill=(176, 230, 248), outline=(90, 110, 120), width=6)
        c.line([(540, 720), (540, 1090)], fill=(90, 110, 120), width=5)
        for xx in (sx0 + 60, 660):
            for k in range(3):
                products_row(c, xx, xx + 260, 800 + k * 110, 70, seed=k * 3 + xx)
        c.glow(540, 900, 380, (255, 244, 200), 60 if tod != "day" else 25)
        # acera y calle
        c.gradient_v(0, 1090, W, 1500, (196, 196, 204), (176, 176, 186))
        for x in range(-100, W + 200, 220):
            c.line([(x, 1090), (x - 70, 1500)], fill=(150, 150, 160), width=3)
        c.rect(0, 1500, W, 1560, fill=(130, 130, 140))
        c.gradient_v(0, 1560, W, H, (74, 76, 88), (54, 56, 66))
        for x in range(-40, W, 240):
            c.rect(x, 1730, x + 130, 1752, fill=(240, 232, 170))
        # farola
        c.rect(36, 520, 52, 1380, fill=(60, 64, 78))
        c.ellipse(44, 510, 28, 18, fill=(250, 240, 180) if tod != "day" else (210, 210, 190))
        if tod != "day":
            c.glow(44, 520, 320, (255, 230, 150), 110)
        # arbustos
        for x in (110, 990):
            c.ellipse(x, 1110, 70, 60, fill=(70, 150, 84), outline=(40, 100, 56), width=3)
        # luz ambiente general
        if tod == "night":
            pass

    def dynamic(self, dc, t):
        # nubes que derivan (sólo de día/atardecer) y coche que cruza
        for i in range(3):
            x = (i * 420 + t * (14 + i * 6)) % (W + 400) - 200
            y = 150 + i * 90
            dc.ellipse(x, y, 90, 34, fill=(255, 255, 255, 200))
            dc.ellipse(x + 50, y - 14, 60, 30, fill=(255, 255, 255, 200))
        cx = ((t * 120) % (W + 600)) - 300
        y = 1660
        dc.rect(cx, y - 70, cx + 250, y + 14, fill=(64, 130, 210), outline=(20, 40, 80))
        dc.rect(cx + 50, y - 120, cx + 190, y - 70, fill=(90, 160, 230), outline=(20, 40, 80))
        dc.rect(cx + 64, y - 112, cx + 120, y - 76, fill=(190, 230, 250))
        dc.rect(cx + 128, y - 112, cx + 180, y - 76, fill=(190, 230, 250))
        dc.ellipse(cx + 60, y + 14, 28, 28, fill=(30, 30, 40))
        dc.ellipse(cx + 190, y + 14, 28, 28, fill=(30, 30, 40))
        dc.ellipse(cx + 60, y + 14, 12, 12, fill=(180, 180, 190))
        dc.ellipse(cx + 190, y + 14, 12, 12, fill=(180, 180, 190))


class House(BaseSet):
    info = SetInfo("house", floor_y=1350, extras_y=1090)

    def paint(self, c, variant=0, tod="day"):
        c.rect(0, 0, W, H, fill=(246, 226, 200))
        c.gradient_v(0, 0, W, 1010, (250, 232, 205), (240, 214, 184))
        for x in range(0, W, 90):
            c.rect(x, 0, x + 45, 1010, fill=(255, 255, 255, 40))
        # ventana
        c.rrect(60, 250, 360, 720, 12, fill=(150, 200, 240) if tod != "night" else (24, 32, 70), outline=(255, 255, 255), width=14)
        c.line([(210, 250), (210, 720)], fill=(255, 255, 255), width=10)
        c.line([(60, 485), (360, 485)], fill=(255, 255, 255), width=10)
        # cortinas
        c.poly([(40, 230), (120, 230), (110, 740), (40, 740)], fill=(210, 90, 90))
        c.poly([(300, 230), (380, 230), (380, 740), (310, 740)], fill=(210, 90, 90))
        # cuadros
        for x, y, w_, h_, col in ((470, 300, 160, 120, (120, 180, 220)), (660, 330, 120, 160, (230, 180, 90)), (820, 290, 180, 130, (130, 190, 140))):
            c.rect(x, y, x + w_, y + h_, fill=col, outline=(110, 76, 50), width=8)
        # sofá
        c.rrect(420, 760, 1040, 1010, 40, fill=(86, 120, 170), outline=(40, 60, 100), width=5)
        c.rrect(400, 880, 520, 1060, 28, fill=(100, 136, 190), outline=(40, 60, 100), width=5)
        c.rrect(940, 880, 1060, 1060, 28, fill=(100, 136, 190), outline=(40, 60, 100), width=5)
        c.rrect(480, 940, 980, 1050, 22, fill=(98, 132, 184), outline=(40, 60, 100), width=4)
        # lámpara
        c.rect(1010, 560, 1018, 1010, fill=(90, 80, 70))
        c.poly([(960, 560), (1068, 560), (1040, 480), (990, 480)], fill=(255, 226, 150), outline=(180, 140, 60), width=3)
        c.glow(1014, 540, 260, (255, 226, 150), 90)
        # suelo
        c.gradient_v(0, 1010, W, H, (190, 140, 100), (150, 106, 74))
        for y in range(1010, H, 70):
            c.line([(0, y), (W, y)], fill=(120, 84, 56, 150), width=2)
        c.ellipse(540, 1620, 420, 120, fill=(228, 110, 100, 190))
        c.ellipse(540, 1620, 300, 80, fill=(250, 190, 120, 170))

    def dynamic(self, dc, t):
        pass


class Factory(BaseSet):
    info = SetInfo("factory", floor_y=1360, extras_y=1090)

    def paint(self, c, variant=0, tod="day"):
        c.rect(0, 0, W, H, fill=(190, 196, 206))
        c.gradient_v(0, 0, W, 1010, (170, 178, 192), (206, 210, 218))
        # ventanas altas
        for i in range(5):
            x = 40 + i * 205
            c.rect(x, 130, x + 170, 330, fill=(190, 226, 246), outline=(90, 100, 116), width=6)
            c.line([(x + 85, 130), (x + 85, 330)], fill=(90, 100, 116), width=5)
        # tuberías
        c.rect(0, 380, W, 420, fill=(130, 138, 152), outline=(70, 78, 92), width=3)
        c.rect(0, 440, W, 470, fill=(200, 100, 70), outline=(110, 50, 36), width=3)
        for x in range(60, W, 260):
            c.rect(x, 370, x + 24, 480, fill=(100, 108, 122), outline=(60, 66, 80), width=2)
        # máquinas
        c.rrect(60, 560, 400, 1010, 14, fill=(240, 180, 60), outline=(130, 90, 20), width=5)
        c.rect(100, 600, 300, 720, fill=(40, 60, 70), outline=(20, 30, 36), width=4)
        c.rrect(640, 520, 1030, 1010, 14, fill=(80, 150, 190), outline=(30, 80, 110), width=5)
        c.ellipse(840, 700, 110, 110, fill=(220, 230, 238), outline=(40, 70, 90), width=6)
        # rayas de seguridad
        for x in range(0, W, 70):
            c.poly([(x, 1010), (x + 35, 1010), (x + 5, 1040), (x - 30, 1040)], fill=(250, 214, 50))
        self.floor_tiles(c, 1040, base=(150, 152, 160), alt=(120, 122, 132), vp=(540, 700))
        # cinta transportadora
        c.rect(0, 1150, W, 1200, fill=(60, 62, 72), outline=(30, 30, 40), width=3)
        c.rect(0, 1200, W, 1250, fill=(96, 100, 112))
        for x in range(20, W, 140):
            c.ellipse(x, 1226, 18, 18, fill=(70, 74, 86), outline=(30, 30, 40), width=2)
        self.ceiling_lights(c, y=40, n=3, w=240, glow=False)

    def dynamic(self, dc, t):
        for i in range(6):
            x = (i * 190 + t * 90) % (W + 200) - 100
            dc.rect(x, 1090, x + 80, 1150, fill=(220, 170, 110), outline=(120, 80, 40), width=2)
            dc.line([(x + 40, 1090), (x + 40, 1150)], fill=(150, 100, 60), width=3)
        a = t * 1.8
        for k in range(8):
            r = a + k * math.tau / 8
            dc.line([(840, 700), (840 + math.cos(r) * 96, 700 + math.sin(r) * 96)], fill=(70, 100, 120), width=3)


class Lab(BaseSet):
    info = SetInfo("lab", floor_y=1350, extras_y=1090, has_fg=True, counter_top=1190)

    def paint(self, c, variant=0, tod="day"):
        c.rect(0, 0, W, H, fill=(222, 236, 244))
        c.gradient_v(0, 0, W, 1010, (232, 244, 250), (206, 224, 236))
        # pizarra / pantalla con gráfica
        c.rrect(240, 220, 840, 660, 16, fill=(20, 34, 56), outline=(120, 130, 150), width=10)
        c.line([(290, 600), (290, 280)], fill=(120, 170, 230), width=4)
        c.line([(290, 600), (790, 600)], fill=(120, 170, 230), width=4)
        pts = [(300, 560), (390, 520), (470, 540), (560, 420), (650, 440), (730, 320)]
        c.line(pts, fill=(250, 214, 72), width=6)
        for p in pts:
            c.ellipse(p[0], p[1], 8, 8, fill=(250, 214, 72))
        # estanterías con frascos
        c.rect(40, 300, 210, 940, fill=(190, 200, 214), outline=(120, 130, 150), width=4)
        for r in range(4):
            yb = 440 + r * 150
            c.rect(40, yb, 210, yb + 10, fill=(130, 140, 160))
            for k in range(4):
                col = [(232, 72, 60), (96, 184, 96), (64, 168, 200), (250, 214, 72), (150, 90, 190)][(k + r) % 5]
                c.rrect(54 + k * 40, yb - 70, 84 + k * 40, yb, 6, fill=col + (230,), outline=shade(col, 0.6), width=2)
        # póster tabla periódica
        c.rect(880, 280, 1040, 480, fill=(250, 246, 232), outline=(120, 100, 80), width=6)
        for r in range(5):
            for k in range(6):
                col = [(232, 120, 100), (120, 190, 230), (150, 210, 130), (250, 214, 100)][(r + k) % 4]
                c.rect(894 + k * 24, 296 + r * 34, 914 + k * 24, 322 + r * 34, fill=col)
        self.ceiling_lights(c, y=50, n=3, w=280)
        c.gradient_v(0, 1010, W, H, (206, 214, 224), (170, 180, 194))
        for y in range(1010, H, 70):
            c.line([(0, y), (W, y)], fill=(150, 160, 176, 160), width=2)

    def paint_fg(self, c, variant=0):
        top = self.info.counter_top
        c.rect(-40, top, W + 40, top + 30, fill=(60, 66, 80), outline=(30, 34, 44), width=3)
        c.rect(-40, top + 30, W + 40, 1450, fill=(230, 232, 238), outline=(150, 156, 170), width=4)
        for x in range(0, W, 270):
            c.rect(x + 10, top + 60, x + 250, 1420, fill=(214, 218, 228), outline=(150, 156, 170), width=3)

    def dynamic(self, dc, t):
        # burbujas en un matraz
        dc.ellipse(850, 1150, 46, 36, fill=(120, 220, 160, 220))
        for i in range(4):
            y = 1150 - ((t * 40 + i * 25) % 90)
            dc.ellipse(850 + (i - 1.5) * 14, y, 5, 5, fill=(255, 255, 255, 200))


class Warehouse(BaseSet):
    info = SetInfo("warehouse", floor_y=1360, extras_y=1090)

    def paint(self, c, variant=0, tod="day"):
        c.gradient_v(0, 0, W, 1010, (150, 156, 168), (190, 194, 204))
        self.ceiling_lights(c, y=46, n=3, w=260, glow=False)
        for i, (x0, x1) in enumerate(((20, 340), (380, 700), (740, 1060))):
            c.rect(x0, 340, x1, 1010, fill=(70, 100, 160), outline=(30, 50, 90), width=4)
            for r in range(4):
                yb = 480 + r * 140
                c.rect(x0, yb, x1, yb + 12, fill=(240, 130, 50))
                rng = random.Random(i * 10 + r)
                x = x0 + 8
                while x < x1 - 60:
                    bw = rng.randint(50, 90)
                    bh = rng.randint(60, 110)
                    c.rect(x, yb - bh, x + bw, yb, fill=(206, 156, 100), outline=(120, 84, 44), width=3)
                    c.line([(x + bw / 2, yb - bh), (x + bw / 2, yb)], fill=(150, 108, 64), width=3)
                    x += bw + 6
        for x in range(0, W, 70):
            c.poly([(x, 1010), (x + 35, 1010), (x + 5, 1040), (x - 30, 1040)], fill=(250, 214, 50))
        self.floor_tiles(c, 1040, base=(156, 158, 166), alt=(126, 128, 138), vp=(540, 700))


SETS: dict[str, BaseSet] = {
    "street": Street(),
    "supermarket_aisle": SupermarketAisle(),
    "checkout": Checkout(),
    "security_room": SecurityRoom(),
    "office": Office(),
    "house": House(),
    "factory": Factory(),
    "lab": Lab(),
    "warehouse": Warehouse(),
}


def get_set(name: str) -> BaseSet:
    return SETS.get(name) or SETS["street"]


BG_SCALE = 1.5  # el fondo se cachea a 1.5x para poder acercar la cámara sin pixelar


def render_background(name: str, variant: int = 0, tod: str = "day") -> tuple[Image.Image, Image.Image | None]:
    """Devuelve (fondo RGB 1.5x, primer plano RGBA 1.5x o None)."""
    st = get_set(name)
    paint_k = 2.0
    c = Canvas(W, H, paint_k)
    st.paint(c, variant, tod)
    bg = c.finish(int(W * BG_SCALE), int(H * BG_SCALE))
    fg = None
    if st.info.has_fg:
        c2 = Canvas(W, H, paint_k, mode="RGBA", bg=(0, 0, 0, 0))
        st.paint_fg(c2, variant)
        fg = c2.finish(int(W * BG_SCALE), int(H * BG_SCALE))
    return bg, fg
