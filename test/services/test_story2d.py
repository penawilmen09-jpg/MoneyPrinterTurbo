import numpy as np

from app.services.story2d import audio, script


def test_beats_are_verbatim_and_complete():
    ids = [b[0] for b in script.BEATS]
    assert len(ids) == len(set(ids)) == 12
    assert script.BEATS[0][1].startswith("Un supermercado perdió miles de dólares")
    assert script.BEATS[-1][1].endswith("que nadie se molesta en revisar.")


def test_every_sfx_is_finite_and_normalised():
    for name in audio.SFX:
        x = audio.get_sfx(name)
        assert np.isfinite(x).all() and 0.5 < np.max(np.abs(x)) <= 1.0001


def test_voice_priority_keeps_bus_under_voice():
    sr = audio.SR
    voice = (0.2 * np.sin(np.arange(sr) * 0.05)).astype(np.float32)
    bus = np.stack([voice * 3, voice * 3], 1)
    out = audio.voice_priority(bus, voice, 8.0)
    ratio = audio.rms(voice) / audio.rms(out.mean(axis=1)[sr // 4:])
    assert ratio > 10 ** (6 / 20)
