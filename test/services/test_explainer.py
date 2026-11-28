import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(__file__))

from explainer_fakes import fake_narrator  # noqa: E402

from app.services.explainer import audio as A  # noqa: E402
from app.services.explainer import pipeline, script as SC, subtitles as SUB  # noqa: E402
from app.services.explainer.models import DEFAULT_VOICE_NAME, ExplainerParams, SceneTiming, Word  # noqa: E402
from app.services.explainer.narration import (  # noqa: E402
    ElevenLabsNarrator, NarrationError, parse_voice, spoken_text, words_from_alignment)

TOPIC = "¿Cómo funciona el freno de motor de un camión?"


def _timings(plan):
    narr = {s.id: fake_narrator(s, "", "", "/tmp/mpt_explainer_test") for s in plan.scenes}
    return pipeline.build_timings(plan, narr, 30)


def test_reference_plan_is_valid_and_structured():
    plan = SC.generate_plan(TOPIC, 45)
    assert SC.validate_plan(plan, 45) == []
    assert plan.scenes[0].role == "hook" and len(plan.scenes[0].narration.split()) <= SC.MAX_HOOK_WORDS
    assert "Explora Ciencia 360" in plan.scenes[-1].narration
    assert sum(len(s.sfx) for s in plan.scenes) <= 3


def test_validate_rejects_bad_plan():
    plan = SC.generate_plan(TOPIC, 45)
    plan.scenes[2].visual.labels = ["nope|x"]
    assert any("ancla" in i for i in SC.validate_plan(plan, 45))


def test_llm_plan_without_audit_ok_is_rejected():
    def llm(prompt):
        return '{"ok": false, "problems": [{"scene":"s1","claim":"x","why":"inventado"}]}' if "Audita" in prompt else "no json"
    with pytest.raises(SC.ScriptError):
        SC.generate_plan("tema sin pack", 45, llm=llm, research=False)


def test_timings_are_frame_aligned_and_cover_voice():
    plan = SC.generate_plan(TOPIC, 45)
    for t in _timings(plan):
        assert abs(t.duration * 30 - round(t.duration * 30)) < 1e-6
        assert t.words[-1].end <= t.duration
        assert t.words[0].start >= t.lead


def test_sfx_never_overlap_key_words_and_are_sparse():
    plan = SC.generate_plan(TOPIC, 45)
    timings = _timings(plan)
    total = sum(t.duration for t in timings)
    events, _ = A.plan_sfx(plan, timings, total)
    assert len(events) <= round(total * A.MAX_SFX_RATE)
    for e in events:
        sc = next(s for s in plan.scenes if s.id == e.scene)
        tm = next(t for t in timings if t.id == e.scene)
        flags = SUB.keyword_flags(tm.words, sc.keywords)
        for w, key in zip(tm.words, flags):
            if key:
                assert not (e.t < tm.start + w.end and e.t + 0.8 > tm.start + w.start)


def test_mix_loudness_and_ducking(tmp_path):
    plan = SC.generate_plan(TOPIC, 45)
    timings = _timings(plan)
    total = sum(t.duration for t in timings)
    mix = A.build_mix(plan, timings, total, str(tmp_path))
    A.loudnorm_encode(mix["premix"], str(tmp_path / "f.m4a"))
    loud = A.measure_loudness(str(tmp_path / "f.m4a"))
    assert abs(loud["integrated_lufs"] - (-16)) <= 1.0
    assert loud["true_peak_dbtp"] <= -1.0 + 0.05
    voice, music = A.read_wav(mix["voice"]), A.read_wav(mix["music"])
    t0 = timings[1]
    w = t0.words[3]
    a, b = int((t0.start + w.start) * A.SR), int((t0.start + w.end) * A.SR)
    gap = int((timings[0].start + 0.05) * A.SR)
    assert A.rms_db(music[a:b]) < A.rms_db(voice[a:b]) - 12


def test_subtitle_cues_and_srt(tmp_path):
    words = [Word(text=w, start=i * 0.3, end=i * 0.3 + 0.25) for i, w in enumerate("Hola, esto es una prueba de subtítulos sincronizados.".split())]
    cues = SUB.build_cues(words)
    assert all(len(c.words) <= SUB.MAX_WORDS for c in cues)
    assert SUB.keyword_flags(words, ["prueba de subtítulos"]) .count(True) == 3
    tm = SceneTiming(id="a", start=10.0, duration=5, lead=0.2, audio_duration=3, words=words)
    SUB.write_srt(str(tmp_path / "x.srt"), [tm])
    assert "00:00:10,000" in (tmp_path / "x.srt").read_text()


def test_voice_never_falls_back():
    with pytest.raises(NarrationError):
        parse_voice("edge:es-MX-JorgeNeural")
    assert parse_voice(DEFAULT_VOICE_NAME)[0] == "851ejYcv2BoNPjrkw93G"
    assert spoken_text("el freno Jacobs") == "el freno Yéicobs"  # 1 word -> 1 word keeps alignment


def test_missing_key_gives_clear_error(monkeypatch, tmp_path):
    from app.services import voice
    monkeypatch.setattr(voice, "get_elevenlabs_api_key", lambda: "")
    n = ElevenLabsNarrator(DEFAULT_VOICE_NAME)
    sc = SC.generate_plan(TOPIC, 45).scenes[0]
    with pytest.raises(NarrationError, match="No se cambió la voz|no se cambió"):
        n(sc, "", "", str(tmp_path))


def test_alignment_maps_back_to_caption_words():
    al = {"characters": list("Hola mundo"), "character_start_times_seconds": [i * .1 for i in range(10)],
          "character_end_times_seconds": [i * .1 + .1 for i in range(10)]}
    ws = words_from_alignment(["Hola", "mundo"], al)
    assert ws[0].start == 0 and abs(ws[1].start - 0.5) < 1e-9
    with pytest.raises(NarrationError):
        words_from_alignment(["a", "b", "c"], al)


def test_api_routes_registered():
    from app.router import root_api_router
    paths = {r.path for r in root_api_router.routes}
    assert {"/api/v1/explainers", "/api/v1/explainers/{task_id}/produce"} <= paths


def test_review_mode_stops_after_script(tmp_path):
    out = pipeline.run(None, ExplainerParams(topic=TOPIC, review_script=True), narrator=None, workdir=str(tmp_path))
    assert out["awaiting_review"] and (tmp_path / "plan.json").exists()


@pytest.mark.skipif(not os.getenv("MPT_RUN_EXPLAINER_E2E"), reason="~1 min render; set MPT_RUN_EXPLAINER_E2E=1")
def test_end_to_end_fast_render(tmp_path):
    out = pipeline.run(None, ExplainerParams(topic=TOPIC), narrator=fake_narrator, fast=True, workdir=str(tmp_path))
    assert out["qc_passed"], [c for c in out["qc"]["checks"] if not c["ok"]]
