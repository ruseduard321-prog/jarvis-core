from __future__ import annotations

from backend.services.voice_profiles import DEFAULT_VOICE_PROFILE_KEY, VOICE_PROFILES, get_voice_profile


def test_default_profile_is_documentary_male():
    assert DEFAULT_VOICE_PROFILE_KEY == "documentary_male"
    assert DEFAULT_VOICE_PROFILE_KEY in VOICE_PROFILES


def test_get_voice_profile_returns_matching_profile():
    profile = get_voice_profile("news")
    assert profile.key == "news"
    assert profile.voice == "alloy"


def test_get_voice_profile_falls_back_to_default_for_unknown_key():
    profile = get_voice_profile("nonexistent")
    assert profile.key == DEFAULT_VOICE_PROFILE_KEY


def test_get_voice_profile_falls_back_to_default_for_blank_key():
    profile = get_voice_profile("")
    assert profile.key == DEFAULT_VOICE_PROFILE_KEY


def test_every_profile_has_non_empty_instructions_and_a_model():
    for profile in VOICE_PROFILES.values():
        assert profile.instructions.strip()
        assert profile.model
        assert profile.voice
