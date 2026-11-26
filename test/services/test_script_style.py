"""
Verifies the opt-in documentary script style.

The default prompt asks only for "a script": nothing about the first three
seconds, which is where a short-form viewer decides whether to keep watching,
and nothing about not presenting a hypothesis as settled fact.
"""

from unittest.mock import patch

from app.config import config
from app.services import llm


def test_the_default_prompt_is_unchanged_when_no_style_is_configured():
    prompt = llm.build_script_prompt("mars sunsets")
    assert "Video Script Generator" in prompt
    assert "Documentary Narration Writer" not in prompt


def test_the_documentary_style_encodes_the_retention_structure():
    with patch.dict(config.app, {"script_style": "documentary"}):
        prompt = llm.build_script_prompt("mars sunsets")

    assert "Documentary Narration Writer" in prompt
    # The hook, and that it has to land immediately.
    assert "first three seconds" in prompt
    # The rest of the requested arc.
    assert "question the video answers" in prompt
    assert "step by step" in prompt
    assert "surprising, specific fact" in prompt
    assert "invitation to follow" in prompt


def test_the_documentary_style_bans_filler_openings():
    with patch.dict(config.app, {"script_style": "documentary"}):
        prompt = llm.build_script_prompt("mars sunsets")
    for filler in ("welcome", "in this video", "today we will", "stay tuned"):
        assert filler in prompt, f"{filler} should be named as forbidden"
    assert "no introductions and no filler" in prompt


def test_the_documentary_style_requires_factual_rigour():
    with patch.dict(config.app, {"script_style": "documentary"}):
        prompt = llm.build_script_prompt("mars sunsets")
    assert "never present it" in prompt
    assert "invent no numbers" in prompt
    assert "state a" in prompt and "hypothesis" in prompt


def test_the_documentary_style_writes_for_a_text_to_speech_read():
    with patch.dict(config.app, {"script_style": "documentary"}):
        prompt = llm.build_script_prompt("mars sunsets")
    # Symbols and numerals are what make a TTS read stumble or rush.
    assert "write numbers and units as words" in prompt
    assert "naturally breathe" in prompt
    # Stage directions and speaker labels would be read aloud by the narrator.
    assert "stage directions" in prompt
    assert "speaker labels" in prompt


def test_runtime_context_is_appended_to_whichever_style_is_used():
    with patch.dict(config.app, {"script_style": "documentary"}):
        prompt = llm.build_script_prompt(
            "mars sunsets", language="es-ES", paragraph_number=3,
            video_script_prompt="mention the rovers",
        )
    assert "video subject: mars sunsets" in prompt
    assert "language: es-ES" in prompt
    assert "number of paragraphs: 3" in prompt
    assert "mention the rovers" in prompt


def test_an_unknown_style_falls_back_rather_than_failing_a_generation():
    with patch.dict(config.app, {"script_style": "nonexistent"}):
        prompt = llm.build_script_prompt("mars sunsets")
    assert "Video Script Generator" in prompt


def test_an_explicit_custom_prompt_still_wins():
    with patch.dict(config.app, {"script_style": "documentary"}):
        prompt = llm.build_script_prompt("mars", custom_system_prompt="ONLY MY RULES")
    assert "ONLY MY RULES" in prompt
    assert "Documentary Narration Writer" not in prompt
    # The runtime context is still appended, as it is for every style.
    assert "video subject: mars" in prompt


def test_style_lookup_is_case_insensitive_and_tolerates_whitespace():
    with patch.dict(config.app, {"script_style": "  Documentary  "}):
        assert "Documentary Narration Writer" in llm.get_script_style_prompt()
    with patch.dict(config.app, {"script_style": "default"}):
        assert llm.get_script_style_prompt() == ""
    with patch.dict(config.app, {"script_style": ""}):
        assert llm.get_script_style_prompt() == ""
