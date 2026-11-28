"""Pruebas del modo ANIMATED STORYTELLING (sin red, sin claves)."""

import json

import numpy as np
import pytest

from app.services.storytelling import audio as A
from app.services.storytelling import planner, qc
from app.services.storytelling.models import CharacterSpec, StoryPlan
from app.services.storytelling.render import SceneJob, SceneRenderer
from app.services.storytelling.rig import Pose, draw_character
from app.services.storytelling.samples import supermarket_scam_plan
from app.services.storytelling.subtitles import build_captions, captions_to_srt


def test_plan_roundtrip_and_fingerprints_are_stable():
    plan = supermarket_scam_plan()
    again = StoryPlan.from_json(plan.to_json())
    assert [c.fingerprint() for c in plan.characters] == [c.fingerprint() for c in again.characters]
    assert len({c.fingerprint() for c in plan.characters}) == len(plan.characters)
    assert "Mateo" in plan.characters[0].visual_description()


def test_same_character_renders_identically_in_every_scene():
    spec = supermarket_scam_plan().characters[0]
    a, _ = draw_character(spec, Pose(), origin=(150, 580), scale=0.5, facing=1, canvas_box=(0, 0, 300, 600), ss=1)
    b, _ = draw_character(spec, Pose(), origin=(150, 580), scale=0.5, facing=1, canvas_box=(0, 0, 300, 600), ss=1)
    assert a.tobytes() == b.tobytes()
    other, _ = draw_character(supermarket_scam_plan().characters[1], Pose(), origin=(150, 580), scale=0.5, facing=1,
                              canvas_box=(0, 0, 300, 600), ss=1)
    assert other.tobytes() != a.tobytes()


def test_sample_plan_passes_structure_and_correspondence_checks():
    plan = supermarket_scam_plan()
    assert all(c["status"] == "pass" for c in qc.check_story_structure(plan))
    assert all(c["status"] == "pass" for c in qc.check_scene_correspondence(plan))
    assert all(c["status"] == "pass" for c in qc.check_character_consistency(plan))


def test_correspondence_detects_missing_character_and_wrong_location():
    plan = supermarket_scam_plan()
    plan.scenes[4].characters = [c for c in plan.scenes[4].characters if c.id != "mateo"]
    assert qc.check_scene_correspondence(plan)[0]["status"] == "fail"
    plan = supermarket_scam_plan()
    plan.scenes[4].location = "house"
    plan.scenes[4].props = []
    assert qc.check_scene_correspondence(plan)[0]["status"] == "fail"


def test_captions_cover_every_word_in_order_and_highlight():
    text = "Cada noche faltaban unos pocos dólares. Siempre en el mismo turno."
    caps = build_captions(text, 0.12, 4.0, ["faltaban"])
    assert " ".join(w for c in caps for w, _ in c.words) == text
    assert all(b.start >= a.start for a, b in zip(caps, caps[1:]))
    assert caps[-1].end <= 4.0 + 0.3
    assert any(hl for c in caps for _, hl in c.words)
    assert all(len(c.words) <= 4 for c in caps)
    assert "-->" in captions_to_srt([(0.0, caps)])


def test_sfx_plan_never_on_hook_never_repeats_and_keeps_spacing():
    scenes = [{"start": 0, "sfx": "whoosh", "lead": 0.12}, {"start": 5, "sfx": "alert", "lead": 0.12},
              {"start": 7, "sfx": "beep", "lead": 0.12}, {"start": 12, "sfx": "beep", "lead": 0.12},
              {"start": 18, "sfx": "beep", "lead": 0.12}]
    ev = A.plan_sfx(scenes)
    assert all(e["time"] > 0.5 for e in ev)
    names = [e["name"] for e in ev]
    assert all(a != b for a, b in zip(names, names[1:]))
    assert all(b["time"] - a["time"] >= 4.0 for a, b in zip(ev, ev[1:]))


def test_speech_bounds_and_envelope():
    sr = A.SR
    x = np.zeros(sr * 3, dtype=np.float32)
    x[sr: 2 * sr] = 0.3 * np.sin(np.linspace(0, 2000, sr))
    s0, s1 = A.speech_bounds(x)
    assert 0.9 < s0 < 1.1 and 1.9 < s1 < 2.1
    env = A.envelope(x, s0, s1)
    assert len(env) > 40 and max(env) <= 1.0


def test_renderer_frames_are_vertical_animated_and_different_between_times():
    plan = supermarket_scam_plan()
    for i in (0, 1, 7):
        job = SceneJob(plan=plan.to_dict(), scene_index=i, duration=5, pre_roll=0, fps=24, out_path="", size=(270, 480))
        r = SceneRenderer(plan, plan.scenes[i], job)
        f1, f2 = r.frame(0.5), r.frame(1.3)
        assert f1.size == (270, 480)
        assert np.abs(np.asarray(f1, dtype=int) - np.asarray(f2, dtype=int)).mean() > 0.3


def _fake_llm_json(words_per_scene=14):
    p = supermarket_scam_plan()
    d = p.to_dict()
    return json.dumps(d)


def test_planner_accepts_valid_json_and_retries_invalid():
    calls = []

    def fake(prompt):
        calls.append(prompt)
        return "no es json" if len(calls) == 1 else _fake_llm_json()

    plan = planner.generate_plan("tema", seconds=52, mode="ficticia", llm_fn=fake)
    assert len(calls) == 2 and "CORRIGE" in calls[1]
    assert plan.veracity == "ficticia" and plan.disclaimer
    assert plan.scenes[0].transition_in == "cut" and plan.scenes[0].sfx == ""


def test_planner_rejects_unverified_numbers_in_real_stories(monkeypatch):
    monkeypatch.setattr(planner, "research_topic", lambda topic: ("El museo abrió en 1901 en Lima.", [{"title": "x", "url": "u"}]))
    d = json.loads(_fake_llm_json())
    d["scenes"][0]["narration"] = "En 1950 ocurrió algo increíble en un museo, y casi nadie lo notó, ni siquiera sus guardias nocturnos."
    with pytest.raises(RuntimeError, match="cifras no presentes"):
        planner.generate_plan("museo", seconds=52, mode="real", llm_fn=lambda p: json.dumps(d), max_attempts=2)


def test_real_mode_without_sources_is_refused_instead_of_inventing(monkeypatch):
    monkeypatch.setattr(planner, "research_topic", lambda topic: ("", []))
    with pytest.raises(RuntimeError, match="fuentes verificables"):
        planner.generate_plan("tema", mode="real", llm_fn=lambda p: "{}")


def test_auto_mode_without_sources_becomes_labeled_fiction(monkeypatch):
    monkeypatch.setattr(planner, "research_topic", lambda topic: ("", []))
    plan = planner.generate_plan("tema", mode="auto", llm_fn=lambda p: _fake_llm_json())
    assert plan.veracity == "ficticia" and "ficticia" in plan.disclaimer.lower()


def test_elevenlabs_voice_is_the_configured_one():
    from app.services.storytelling import pipeline as P

    assert P.DEFAULT_VOICE_NAME.split(":")[1] == "851ejYcv2BoNPjrkw93G"
