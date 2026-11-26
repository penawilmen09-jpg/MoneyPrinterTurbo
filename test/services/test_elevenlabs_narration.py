"""
Verifies the ElevenLabs narration path: the official voice settings, the audio
format, and -- the point of the change -- subtitle timings taken from the
provider's measured speech instead of estimated from character counts.
"""

import base64
import json
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.config import config
from app.services import voice


def _alignment(characters, starts, ends):
    return {
        "characters": list(characters),
        "character_start_times_seconds": list(starts),
        "character_end_times_seconds": list(ends),
    }


def test_words_are_grouped_on_whitespace_with_measured_edges():
    # "ab cd" -> two words, each spanning its own characters.
    alignment = _alignment("ab cd", [0.0, 0.1, 0.2, 0.3, 0.5], [0.1, 0.2, 0.3, 0.5, 0.7])
    words = voice.words_from_elevenlabs_alignment(alignment)
    assert words == [("ab", 0.0, 0.2), ("cd", 0.3, 0.7)]


def test_punctuation_stays_attached_to_its_word():
    # The subtitle matcher compares text with punctuation stripped from both
    # sides, so keeping it means the words still reproduce the script.
    alignment = _alignment("hi!", [0.0, 0.1, 0.2], [0.1, 0.2, 0.3])
    assert voice.words_from_elevenlabs_alignment(alignment) == [("hi!", 0.0, 0.3)]


def test_a_malformed_alignment_yields_nothing_rather_than_wrong_timings():
    assert voice.words_from_elevenlabs_alignment({}) == []
    assert voice.words_from_elevenlabs_alignment(_alignment("abc", [0, 1], [1, 2])) == []
    assert voice.words_from_elevenlabs_alignment(
        _alignment("ab", ["x", 1], [1, 2])
    ) == []
    assert voice.words_from_elevenlabs_alignment(
        _alignment("ab", [float("nan"), 1], [1, 2])
    ) == []


def test_submaker_receives_real_word_boundaries():
    alignment = _alignment("ab cd", [0.0, 0.1, 0.2, 0.3, 0.5], [0.1, 0.2, 0.3, 0.5, 0.7])
    sub_maker = voice.ensure_legacy_submaker_fields(voice.SubMaker())

    assert voice.populate_submaker_with_elevenlabs_alignment(sub_maker, alignment)

    assert sub_maker.subs == ["ab", "cd"]
    # The project stores offsets in 100ns units.
    assert sub_maker.offset == [(0, 2000000), (3000000, 7000000)]


def test_an_empty_alignment_reports_failure_so_the_caller_can_fall_back():
    sub_maker = voice.ensure_legacy_submaker_fields(voice.SubMaker())
    assert not voice.populate_submaker_with_elevenlabs_alignment(sub_maker, {})


def test_measured_timings_beat_the_character_count_estimate():
    # A script whose first sentence is spoken fast and whose second is spoken
    # slowly: proportioning by character count puts the boundary in the wrong
    # place, which is what made captions drift against the narration.
    script = "Uno dos. Tres cuatro."
    characters = []
    starts = []
    ends = []
    clock = 0.0
    for character in script:
        characters.append(character)
        starts.append(clock)
        # The first sentence runs at 0.02s per character, the second at 0.30s.
        clock += 0.02 if len(characters) <= 9 else 0.30
        ends.append(clock)
    measured = voice.ensure_legacy_submaker_fields(voice.SubMaker())
    voice.populate_submaker_with_elevenlabs_alignment(
        measured, _alignment(characters, starts, ends)
    )
    estimated = voice.populate_legacy_submaker_with_full_text(
        voice.ensure_legacy_submaker_fields(voice.SubMaker()), script, clock
    )

    measured_second_sentence = measured.offset[2][0] / 10000000
    estimated_second_sentence = estimated.offset[1][0] / 10000000
    assert measured_second_sentence == pytest.approx(0.18, abs=0.01)
    # The estimate places the same words more than a second late.
    assert estimated_second_sentence - measured_second_sentence > 1.0


def test_voice_settings_default_to_a_documentary_read():
    settings = voice.get_elevenlabs_voice_settings()
    assert settings["stability"] == 0.5
    assert settings["similarity_boost"] == 0.85
    # Style exaggeration is what introduces rushed pacing and swallowed
    # syllables, so narration keeps it off.
    assert settings["style"] == 0.0
    assert settings["use_speaker_boost"] is True


def test_voice_settings_read_config_and_clamp_out_of_range_values(monkeypatch):
    monkeypatch.setitem(config.elevenlabs, "stability", 0.7)
    monkeypatch.setitem(config.elevenlabs, "similarity_boost", 4.0)
    monkeypatch.setitem(config.elevenlabs, "style", "not a number")
    monkeypatch.setitem(config.elevenlabs, "use_speaker_boost", "off")

    settings = voice.get_elevenlabs_voice_settings()

    assert settings["stability"] == 0.7
    # Out of range would be rejected by the provider, wasting a paid request.
    assert settings["similarity_boost"] == 1.0
    assert settings["style"] == 0.0
    assert settings["use_speaker_boost"] is False


def test_output_format_falls_back_when_unsupported(monkeypatch):
    assert voice.get_elevenlabs_output_format() == "mp3_44100_128"
    monkeypatch.setitem(config.elevenlabs, "output_format", "mp3_44100_192")
    assert voice.get_elevenlabs_output_format() == "mp3_44100_192"
    monkeypatch.setitem(config.elevenlabs, "output_format", "flac_192000")
    assert voice.get_elevenlabs_output_format() == "mp3_44100_128"


def test_timestamps_can_be_switched_off(monkeypatch):
    assert voice.elevenlabs_timestamps_enabled() is True
    monkeypatch.setitem(config.elevenlabs, "use_timestamps", False)
    assert voice.elevenlabs_timestamps_enabled() is False
    monkeypatch.setitem(config.elevenlabs, "use_timestamps", "no")
    assert voice.elevenlabs_timestamps_enabled() is False


def _fake_response(status_code, body: bytes):
    return SimpleNamespace(
        status_code=status_code,
        iter_content=lambda chunk_size=0: iter([body]),
        close=lambda: None,
    )


def _silent_mp3() -> bytes:
    import subprocess

    from app.utils import utils

    completed = subprocess.run(
        [utils.get_ffmpeg_binary(), "-hide_banner", "-nostdin", "-nostats", "-y",
         "-f", "lavfi", "-i", "sine=f=440:r=44100", "-t", "1",
         "-c:a", "libmp3lame", "-f", "mp3", "pipe:1"],
        stdin=subprocess.DEVNULL, capture_output=True, check=True, timeout=120,
    )
    return completed.stdout


def test_the_request_asks_for_the_configured_voice_format_and_timestamps(tmp_path):
    captured = {}
    audio = _silent_mp3()
    document = json.dumps({
        "audio_base64": base64.b64encode(audio).decode(),
        "alignment": _alignment("hola", [0.0, 0.1, 0.2, 0.3], [0.1, 0.2, 0.3, 0.4]),
    }).encode()

    def fake_post(method, func, url, **kwargs):
        captured["url"] = url
        captured["payload"] = kwargs["json"]
        captured["headers"] = kwargs["headers"]
        return _fake_response(200, document)

    with (
        patch.object(voice, "trace_http_call", fake_post),
        patch.object(voice, "get_elevenlabs_api_key", lambda: "test-key"),
    ):
        sub_maker = voice.elevenlabs_tts(
            text="hola", voice_id="851ejYcv2BoNPjrkw93G",
            voice_file=str(tmp_path / "out.mp3"),
        )

    assert "851ejYcv2BoNPjrkw93G/with-timestamps" in captured["url"]
    assert "output_format=mp3_44100_128" in captured["url"]
    assert captured["payload"]["model_id"] == "eleven_multilingual_v2"
    assert captured["payload"]["voice_settings"]["similarity_boost"] == 0.85
    # The key travels in the header and must never reach the URL or the body.
    assert captured["headers"]["xi-api-key"] == "test-key"
    assert "test-key" not in captured["url"]
    assert "test-key" not in json.dumps(captured["payload"])
    # The decoded audio was written, and the measured timings were kept.
    assert (tmp_path / "out.mp3").read_bytes() == audio
    assert sub_maker.subs == ["hola"]


def test_the_plain_endpoint_is_used_when_timestamps_are_off(tmp_path, monkeypatch):
    monkeypatch.setitem(config.elevenlabs, "use_timestamps", False)
    captured = {}
    audio = _silent_mp3()

    def fake_post(method, func, url, **kwargs):
        captured["url"] = url
        return _fake_response(200, audio)

    with (
        patch.object(voice, "trace_http_call", fake_post),
        patch.object(voice, "get_elevenlabs_api_key", lambda: "test-key"),
    ):
        sub_maker = voice.elevenlabs_tts(
            text="hola mundo", voice_id="851ejYcv2BoNPjrkw93G",
            voice_file=str(tmp_path / "out.mp3"),
        )

    assert "/with-timestamps" not in captured["url"]
    assert (tmp_path / "out.mp3").read_bytes() == audio
    # No alignment is available, so the estimate still covers the script.
    assert sub_maker is not None and sub_maker.subs


def test_an_undecodable_timestamped_body_is_not_retried(tmp_path):
    calls = []

    def fake_post(method, func, url, **kwargs):
        calls.append(url)
        return _fake_response(200, b"{not json")

    with (
        patch.object(voice, "trace_http_call", fake_post),
        patch.object(voice, "get_elevenlabs_api_key", lambda: "test-key"),
    ):
        result = voice.elevenlabs_tts(
            text="hola", voice_id="851ejYcv2BoNPjrkw93G",
            voice_file=str(tmp_path / "out.mp3"),
        )

    assert result is None
    # The request already succeeded and may have been charged.
    assert len(calls) == 1
