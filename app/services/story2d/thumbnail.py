"""Miniatura con gancho para «El cajero que descubrió un robo imposible» (1080x1920)."""
from __future__ import annotations

import math
import sys

import skia

from .characters import draw_character
from .gfx import (C, P, rect, rectp, circ, poly, line, text, grad, radial, camera, text_w, FONT_BOLD)
from . import props as pr


def render(path):
    W, H = 1080, 1920
    s = skia.Surface(W, H)
    cv = s.getCanvas()
    # fondo: súper oscuro con foco dramático
    cv.save()
    pr.bg_store(cv, 540, 0.0, dim=0.55)
    cv.restore()
    cv.drawRect(skia.Rect.MakeXYWH(0, 0, W, H), radial(540, 1000, 1100, "#FF3B3B", "#000000", 0.45, 0.85))
    # rayos del foco
    for i in range(14):
        a0 = -math.pi / 2 + (i - 7) * 0.11
        poly(cv, [(540, 1100), (540 + math.cos(a0) * 1500, 1100 + math.sin(a0) * 1500),
                  (540 + math.cos(a0 + 0.05) * 1500, 1100 + math.sin(a0 + 0.05) * 1500)], "#FFD166", 0.07)

    # caja registradora con billetes que se esfuman
    pr.register(cv, 540, 1620, 1.5, 0.0, drawer=1.0, screen="-$ 7,430", screen_color="#FF6B6B", alert=1.0)
    for i in range(11):
        x = 360 + i * 36 + (i % 3) * 12
        y = 1180 - i * 62 - (i % 2) * 28
        a = max(0.25, 1 - i * 0.07)
        pr.bill(cv, x, y, rot=-35 + i * 14, s=1.2 - i * 0.04, a=a)
        if i > 4:
            pr.sparkle(cv, x + 50, y - 30, 22, a=0.9)

    # Mateo (protagonista) en primer plano, sorprendido, con lupa
    draw_character(cv, "mateo", 270, 1850, 2.25, pose={"armR": (-150, -168), "armL": (30, 20)}, mood="shock", look=(1, -0.3))
    pr.magnifier(cv, 470, 1020, 130, rot=-30)
    # Darío sospechoso al fondo, sonriendo con billete en el bolsillo
    draw_character(cv, "dario", 860, 1790, 1.8, pose={"armR": (-30, -55)}, mood="smirk", look=(-1, 0.2))
    pr.bill(cv, 800, 1500, rot=25, s=0.8)

    pr.vignette(cv, 0.35)
    # TEXTO GANCHO
    cv.drawRect(skia.Rect.MakeXYWH(0, 0, W, 760), grad(0, 0, 0, 760, "#000000", "#000000", 0.85, 0.0))
    text(cv, "NADIE ENTRABA", 540, 215, 112, "#FFFFFF", outline="#000000", outline_w=22)
    text(cv, "A ROBAR…", 540, 335, 128, "#FFD166", outline="#000000", outline_w=24)
    rect(cv, 150, 395, 780, 150, "#E02B2B", r=30)
    rect(cv, 150, 395, 780, 150, "#FFFFFF", style="stroke", sw=8, r=30)
    text(cv, "¡PERO EL DINERO", 540, 462, 66, "#FFFFFF")
    text(cv, "DESAPARECÍA!", 540, 528, 66, "#FFE98A")
    # etiqueta inferior
    rect(cv, 90, 1720, 900, 130, "#000000", 0.78, r=36)
    text(cv, "EL ROBO IMPOSIBLE", 540, 1812, 84, "#FFD166", outline="#000000", outline_w=10)
    s.makeImageSnapshot().save(path)


if __name__ == "__main__":
    render(sys.argv[1] if len(sys.argv) > 1 else "storage/story2d/miniatura.png")
