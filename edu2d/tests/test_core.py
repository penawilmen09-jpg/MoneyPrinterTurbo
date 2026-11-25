import subprocess, wave, struct, math, json
from pathlib import Path
import pytest
from edu2d.audio_check import AudioError, check_audio
from edu2d.subtitles import chunk_words, build_ass, norm
from edu2d.planner import validate_script
from edu2d.pipeline import load_script
from edu2d.scenes_pigeon import SCENES
from edu2d.svgkit import frame_svg

ROOT = Path(__file__).resolve().parents[1]


def _wav(path, freq, secs=1.0, amp=0.5):
    with wave.open(str(path), "wb") as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(22050)
        f.writeframes(b"".join(struct.pack("<h", int(amp * 32767 * math.sin(2 * math.pi * freq * i / 22050)))
                               for i in range(int(22050 * secs))))


def test_audio_ok(tmp_path):
    _wav(tmp_path / "a.wav", 440)
    assert check_audio(tmp_path / "a.wav")["duration"] > .9


def test_audio_silent_rejected(tmp_path):
    _wav(tmp_path / "s.wav", 440, amp=0.0)
    with pytest.raises(AudioError):
        check_audio(tmp_path / "s.wav")


def test_audio_missing_and_corrupt(tmp_path):
    with pytest.raises(AudioError):
        check_audio(tmp_path / "no.mp3")
    (tmp_path / "bad.mp3").write_bytes(b"x" * 5000)
    with pytest.raises(AudioError):
        check_audio(tmp_path / "bad.mp3")


def test_chunks_and_ass(tmp_path):
    words = [{"text": t, "start": i * .3, "end": i * .3 + .25} for i, t in enumerate("Hola mundo. Esto es una prueba larga de subtítulos".split())]
    assert chunk_words(words)[0][-1]["text"] == "mundo."
    n = build_ass(words, {"prueba"}, tmp_path / "s.ass")
    assert n == len(words) and "Dialogue" in (tmp_path / "s.ass").read_text()
    assert norm("Sígueme!") == "sigueme"


def test_script_valid():
    d = load_script(ROOT / "projects/palomas/script.json")
    assert validate_script(d) == []
    assert validate_script({"pack": "pigeon", "scenes": [{"scene": "nope", "text": "x"}]})


@pytest.mark.parametrize("name", sorted(SCENES))
def test_scene_renders_and_moves(name):
    import cairosvg
    a = cairosvg.svg2png(bytestring=frame_svg(SCENES[name](2.0, 8)).encode(), output_width=108)
    b = cairosvg.svg2png(bytestring=frame_svg(SCENES[name](2.4, 8)).encode(), output_width=108)
    assert a != b            # hay animación real entre frames


def test_voice_profile_is_locked():
    import json
    from edu2d.core import VOICE, VOICE_RATE, VOICE_PITCH
    prof = json.loads((ROOT / "voice_profile.json").read_text())
    assert (VOICE, VOICE_RATE, VOICE_PITCH) == ("es-MX-JorgeNeural", "+6%", "+0Hz")
    for proj in ("palomas", "barco", "helicoptero", "tierra", "estelas", "luna", "gira", "agujero"):
        d = json.loads((ROOT / f"projects/{proj}/script.json").read_text())
        assert (d["voice"], d["rate"]) == (prof["voice"], prof["rate"])


def test_rotor_speed_no_aliasing():
    from edu2d.art.heli import rotor_ang
    from edu2d.core import FPS
    step = rotor_ang(1 / FPS) - rotor_ang(0)
    assert 8 < step < 40, step          # gira visiblemente y sin efecto rueda de carreta (4 aspas = 90°)


def test_mixer_keeps_voice_clear():
    import numpy as np
    from edu2d import mixer
    sr = mixer.SR
    n_ = sr * 6
    rng = np.random.default_rng(1)
    voice = np.zeros(n_, np.float32)
    t = np.arange(sr * 2) / sr
    voice[sr:sr * 3] = (np.sin(2 * np.pi * 180 * t) * (1 + np.sin(2 * np.pi * 4 * t)) * .3).astype(np.float32)
    boom = (rng.standard_normal(sr) * 1.0).astype(np.float32)             # efecto fuerte justo bajo la voz
    wind = rng.standard_normal(sr * 6).astype(np.float32)
    music = np.sin(2 * np.pi * 220 * np.arange(n_) / sr).astype(np.float32)
    out, v, bed = mixer.mix(voice, [(int(sr * 1.5), boom, "boom"), (int(sr * 2.2), boom, "pop")], [(0, wind, "wind")], music)
    words = [{"text": "palabra", "start": 1.0, "end": 3.0}]
    worst = mixer.check_margins(mixer.speech_margins(v, bed, words))
    assert worst[1] >= mixer.MIN_MARGIN_DB
    assert np.abs(out).max() <= .93
    # el viento continuo se recorta a una ráfaga corta
    _, _, bed2 = mixer.mix(voice, [], [(0, wind, "wind")], None)
    assert np.abs(bed2[int(sr * 4):]).max() < 1e-6          # el viento no dura toda la escena
    assert np.abs(bed2).max() <= mixer.LEVEL["wind"] * mixer.VOICE_PEAK + 1e-6
    assert abs(np.abs(bed[int(sr * 5):]).max() - mixer.LEVEL["music"] * mixer.VOICE_PEAK) < 5e-3   # música ≈ 10 % de la voz


def test_mixer_rejects_loud_bed():
    import numpy as np, pytest
    from edu2d import mixer
    with pytest.raises(mixer.MixError):
        mixer.check_margins([("hola", 12.0)])


def test_align_words_keeps_script_text():
    from edu2d.pipeline import align_words
    edge = [{"text": "Te", "start": 0, "end": .2}, {"text": "atreverías", "start": .2, "end": .8}, {"text": "negro", "start": .8, "end": 1.1},
            {"text": "Explora", "start": 1.2, "end": 1.6}, {"text": "360 para", "start": 1.6, "end": 2.4}]
    out = align_words("¿Te atreverías negro? Explora 360 para", edge)
    assert [w["text"] for w in out] == ["¿Te", "atreverías", "negro?", "Explora", "360", "para"]
    assert all(a["end"] <= b["start"] + 1e-6 for a, b in zip(out, out[1:]))
