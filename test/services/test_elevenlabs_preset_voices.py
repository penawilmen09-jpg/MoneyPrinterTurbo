from app.services import voice


def test_presets_are_first_and_in_order():
    presets = voice.get_elevenlabs_preset_voices()
    assert presets == [
        "elevenlabs:851ejYcv2BoNPjrkw93G:Voz 1",
        "elevenlabs:dlGxemPxFMTY7iXagmOj:Voz 2",
    ]


def test_merge_dedupes_catalog_and_keeps_other_voices():
    catalog = [
        "elevenlabs:851ejYcv2BoNPjrkw93G:Old Name",
        "elevenlabs:other:Other",
    ]
    merged = voice.merge_elevenlabs_preset_voices(catalog)
    assert merged[:2] == voice.get_elevenlabs_preset_voices()
    assert merged[2:] == ["elevenlabs:other:Other"]


def test_saved_voice_with_old_label_maps_to_preset():
    assert (
        voice.normalize_elevenlabs_voice_name("elevenlabs:851ejYcv2BoNPjrkw93G:Old")
        == "elevenlabs:851ejYcv2BoNPjrkw93G:Voz 1"
    )
    assert voice.normalize_elevenlabs_voice_name("elevenlabs:x:Y") == "elevenlabs:x:Y"
    assert voice.normalize_elevenlabs_voice_name("en-US-X") == "en-US-X"
