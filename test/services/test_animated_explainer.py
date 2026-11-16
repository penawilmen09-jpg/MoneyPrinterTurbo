"""Pruebas del generador local de videos explicativos 2D (sin red, sin APIs de pago)."""

import subprocess

import numpy as np
import pytest
from PIL import Image

from app.services.animated_explainer import audio, subtitles
from app.services.animated_explainer.characters import (EXPRESSIONS, POSE_HANDS, PRESETS,
                                                         render_character)
from app.services.animated_explainer.pipeline import (TRANSITION_SECONDS, plan_timing,
                                                      render_video)
from app.services.animated_explainer.script import (ScriptError, from_dict, load_script,
                                                    parse_plain_text)

EXAMPLE = "examples/autoridad_limitada.json"


def _mini(**scene_over):
    scene = {"setting": "showroom", "narration": "Hola mundo, esto es una prueba.",
             "characters": [{"id": "a", "x": 0.5, "y": 0.8}], "min_duration": 2.0}
    scene.update(scene_over)
    return {"title": "t", "characters": {"a": {"preset": "vendedor"}}, "scenes": [scene]}


def test_example_script_loads_and_has_six_scenes():
    s = load_script(EXAMPLE)
    assert len(s.scenes) == 6
    assert s.voice == "es-MX-JorgeNeural"
    assert "lista de precios diga que no" in s.scenes[-1].narration


@pytest.mark.parametrize("patch,msg", [
    ({"setting": "luna"}, "setting"),
    ({"narration": ""}, "narration"),
    ({"characters": [{"id": "zzz"}]}, "desconocido"),
    ({"events": [{"type": "expression", "who": "a", "value": "enojado", "at": 0.1}]}, "value"),
    ({"events": [{"type": "emote", "who": "a", "value": "sweat", "at": 2}]}, "fuera de rango"),
    ({"transition": "explosion"}, "transition"),
])
def test_invalid_scripts_are_rejected(patch, msg):
    with pytest.raises(ScriptError, match=msg):
        from_dict(_mini(**patch))


def test_plain_text_parser_assigns_settings():
    s = parse_plain_text("El cliente pide un descuento.\n\n[setting=strategy]\nEsta es la técnica.")
    assert [x.setting for x in s.scenes] == ["dealership_desk", "strategy"]


def test_timing_leaves_room_for_transitions_and_voice():
    s = load_script(EXAMPLE)
    speech = [6.0] * len(s.scenes)
    tm = plan_timing(s.scenes, speech)
    for i, t in enumerate(tm):
        assert t.duration >= t.lead + speech[i] + t.transition_out  # la voz no se pisa
        if i:
            assert t.start == pytest.approx(tm[i - 1].start + tm[i - 1].duration - tm[i - 1].transition_out)
    assert tm[0].transition_out == TRANSITION_SECONDS and tm[-1].transition_out == 0.0


def test_subtitles_chunking_and_formats():
    words = [(w, i * 0.4, i * 0.4 + 0.35) for i, w in enumerate(
        "Si quieres proteger tus ganancias, deja que tu lista de precios diga que no.".split())]
    chunks = subtitles.chunk_words(words)
    assert all(len(c) <= 4 for c in chunks) and sum(len(c) for c in chunks) == len(words)
    ass = subtitles.build_ass(words)
    assert "PlayResY: 1920" in ass and "Be Vietnam Pro" in ass and ass.count("Dialogue:") == len(words)
    srt = subtitles.build_srt(words)
    assert "00:00:00,000 -->" in srt


def test_subtitle_lines_never_overlap_in_time():
    import re
    words = [(w, i * 0.30, i * 0.30 + 0.29) for i, w in enumerate(
        "tener poder para decidir, pero es parte de una estrategia: el jefe invisible dice que no.".split())]
    ev = [re.match(r"Dialogue: 0,([\d:.]+),([\d:.]+)", l).groups()
          for l in subtitles.build_ass(words).splitlines() if l.startswith("Dialogue")]
    to_s = lambda x: sum(float(p) * m for p, m in zip(x.split(":"), (3600, 60, 1)))
    for (s1, e1), (s2, e2) in zip(ev, ev[1:]):
        assert to_s(e1) <= to_s(s2) + 0.011  # sin solape entre eventos consecutivos
    srt_t = re.findall(r"(\d\d:\d\d:\d\d,\d+) --> (\d\d:\d\d:\d\d,\d+)", subtitles.build_srt(words))
    assert all(a[1] <= b[0] for a, b in zip(srt_t, srt_t[1:]))


def test_characters_are_consistent_between_renders():
    st = dict(hands=POSE_HANDS["stand"], expr=EXPRESSIONS["neutral"], mouth=0.0, blink=0.0,
              look=(0, 0), tilt=0, bob=0, walk=None, sit=False, tie_loose=0, flip=False)
    a, _, _ = render_character(PRESETS["vendedor"], st, 0.5)
    b, _, _ = render_character(PRESETS["vendedor"], st, 0.5)
    assert a.tobytes() == b.tobytes()
    other, _, _ = render_character(PRESETS["jefe"], st, 0.5)
    assert a.tobytes() != other.tobytes()


def test_sfx_music_and_mix():
    for name in audio.SFX:
        x = audio.get_sfx(name)
        assert len(x) > 0 and np.max(np.abs(x)) <= 0.91
    with pytest.raises(KeyError):
        audio.get_sfx("no_existe")
    music = audio.make_music(6.0, "calm")
    voice = np.sin(np.linspace(0, 400, audio.SR * 2)).astype(np.float32) * 0.5
    out = audio.mix(6.0, [(1.0, voice)], [(0.5, audio.get_sfx("ding"), 0.8, 0.0)], music)
    assert out.shape == (6 * audio.SR, 2) and np.max(np.abs(out)) <= 0.96
    # ducking: con voz la música baja
    quiet = np.abs(out[int(1.5 * audio.SR):int(2.5 * audio.SR)]).mean()
    assert quiet > 0


def test_silent_tts_fallback_estimates_word_timing():
    sp = audio.synthesize("uno dos tres cuatro", provider="silent")
    assert sp.provider == "silent" and len(sp.words) == 4
    assert sp.words[-1][2] == pytest.approx(sp.duration, rel=0.01)


def test_end_to_end_draft_render_is_vertical_mp4(tmp_path):
    out = tmp_path / "v.mp4"
    res = render_video(from_dict(_mini(speaker="a")), str(out), tts="silent", draft=True,
                       workers=1, music="builtin:calm")
    assert out.exists() and res.srt_path
    probe = subprocess.run([audio.ffmpeg_bin(), "-i", str(out)], capture_output=True, text=True).stderr
    assert "Video: h264" in probe and "540x960" in probe and "Audio: aac" in probe


def test_example_frame_renders_at_1080x1920():
    from app.services.animated_explainer.animator import SceneRenderer
    s = load_script(EXAMPLE)
    sc = s.scenes[0]
    sp = audio.synthesize(sc.narration, provider="silent")
    r = SceneRenderer(sc, s.characters, 8.0, audio.envelope(sp.pcm, 30), 0.3, sp.words, 30)
    frame = r.frame(100)
    assert isinstance(frame, Image.Image) and frame.size == (1080, 1920) and frame.mode == "RGB"
