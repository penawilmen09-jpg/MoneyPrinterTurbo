"""
Verifies the scene-planning prompt that image-generating sources receive.

An image generator handed a 1-3 word stock-library query has to invent the
setting, the composition and the explanatory graphics, which is how a video
ends up with scenes that illustrate nothing the narrator said. These tests
pin the contract of the prompt that replaces it, without calling a provider.
"""

import pytest

from app.models.schema import VideoParams
from app.services import llm, task


SCRIPT = (
    "Marte tiene el cielo rojo de día y atardeceres azules. "
    "La respuesta está en el polvo."
)


def test_scene_mode_asks_for_described_scenes_in_narration_order():
    prompt = llm.build_terms_prompt(
        "atardeceres azules en Marte", SCRIPT, amount=6, visual_scenes=True
    )
    assert "Documentary Scene Designer" in prompt
    assert "Design 6 consecutive scenes" in prompt
    assert "json-array of 6 strings" in prompt
    # The rules that answer the specific complaints about the old output.
    assert "scene N must illustrate the Nth part of the narration" in prompt
    assert "never an empty background" in prompt
    assert "must differ from the one before it" in prompt
    assert "9:16" in prompt
    assert "subtitles" in prompt
    assert "no lettering" in prompt
    assert "never contradict" in prompt
    assert SCRIPT in prompt


def test_scene_descriptions_are_bounded_so_they_stay_specific_and_usable():
    prompt = llm.build_terms_prompt("x", SCRIPT, amount=4, visual_scenes=True)
    assert f"{llm.MIN_VISUAL_SCENE_WORDS}-{llm.MAX_VISUAL_SCENE_WORDS} words" in prompt
    assert llm.MIN_VISUAL_SCENE_WORDS >= 10
    assert llm.MAX_VISUAL_SCENE_WORDS <= 80


def test_stock_search_terms_are_unchanged_for_library_sources():
    prompt = llm.build_terms_prompt("mars", SCRIPT, amount=5)
    assert "Video Search Terms Generator" in prompt
    assert "1-3 words" in prompt
    assert "Documentary Scene Designer" not in prompt

    ordered = llm.build_terms_prompt("mars", SCRIPT, amount=3, match_script_order=True)
    assert "chronological stock-video search terms" in ordered
    assert "same order as the script narration" in ordered


@pytest.mark.parametrize(
    "video_source,expects_scenes",
    [
        ("openai_image", True),
        ("codex_image", True),
        ("useapi_image", True),
        ("pexels", False),
        ("pixabay", False),
        ("local", False),
    ],
)
def test_only_image_generating_sources_get_scene_briefs(
    video_source, expects_scenes, monkeypatch
):
    captured = {}

    def fake_generate_terms(**kwargs):
        captured.update(kwargs)
        return ["a term"]

    monkeypatch.setattr(llm, "generate_terms", fake_generate_terms)
    params = VideoParams(video_subject="marte", video_source=video_source)
    params.video_terms = ""

    task.generate_terms("task-id", params, SCRIPT)

    assert captured["visual_scenes"] is expects_scenes
