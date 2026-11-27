import sys; sys.path.insert(0,'.')
import amz, stage, a4, a5, a6, compose_amz as c
bad = 0
for name, mod, dur in (("a4", a4, 11.33), ("a5", a5, 8.12), ("a6", a6, 12.25)):
    t = 0.0
    while t < dur + .3:
        stage.CLOCK[0] = t
        try: mod.scene(t)
        except Exception as e: bad += 1; print("FALLO", name, round(t, 2), repr(e)[:120], flush=True)
        t += .07
    print("barrido", name, "ok", flush=True)
# transiciones entre escenas (zonas con dos escenas a la vez)
for b in (14.85, 27.55, 37.5, 45.8, 57.13, 65.25):
    for dt in (-.24, -.12, 0, .12, .24):
        try: c.frame_at(b + dt)
        except Exception as e: bad += 1; print("FALLO transición", b + dt, repr(e)[:120], flush=True)
print("TOTAL fallos:", bad, flush=True)
