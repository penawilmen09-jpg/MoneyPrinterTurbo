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
