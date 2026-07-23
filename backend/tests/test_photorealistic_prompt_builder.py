from __future__ import annotations

from backend.schemas.composition import CameraIntent, ColorLanguage, CompositionStyle
from backend.schemas.visual_identity import CharacterVisualIdentity, HistoricalVisualContext
from backend.services.photorealistic_prompt_builder import PhotorealisticPromptBuilder


def _builder() -> PhotorealisticPromptBuilder:
    return PhotorealisticPromptBuilder()


def test_build_includes_subject_framing_and_realism_directive():
    prompt = _builder().build(
        subject_and_action="A ship departs the harbor",
        composition_style=CompositionStyle.ESTABLISHING_SHOT,
        camera_intent=CameraIntent.NEUTRAL_OBSERVATION,
    )

    assert prompt.startswith("A ship departs the harbor")
    assert "24mm wide-angle lens" in prompt
    assert "cinematic 16:9 composition" in prompt
    assert "no on-image text" in prompt
    assert "photojournalistic documentary photography" in prompt
    assert "Not an illustration, not a painting, not concept art, not fantasy art" in prompt


def test_build_reflects_composition_style_and_camera_intent():
    close_up = _builder().build(
        subject_and_action="A face in shadow",
        composition_style=CompositionStyle.CLOSE_UP,
        camera_intent=CameraIntent.SUSPENSE,
    )
    wide = _builder().build(
        subject_and_action="A face in shadow",
        composition_style=CompositionStyle.WIDE_SHOT,
        camera_intent=CameraIntent.SUSPENSE,
    )

    assert "85mm portrait telephoto lens" in close_up
    assert "shallow depth of field" in close_up
    assert "35mm lens" in wide
    assert close_up != wide


def test_build_includes_historical_context_when_provided():
    context = HistoricalVisualContext(
        time_period="14th century",
        architecture="mudbrick minarets and flat-roofed compounds",
        clothing="flowing robes and turbans",
    )

    prompt = _builder().build(
        subject_and_action="Merchants gather in the market",
        composition_style=CompositionStyle.WIDE_SHOT,
        camera_intent=CameraIntent.INVESTIGATION,
        historical_context=context,
    )

    assert "14th century" in prompt
    assert "mudbrick minarets" in prompt
    assert "flowing robes" in prompt


def test_build_omits_historical_context_when_empty():
    prompt = _builder().build(
        subject_and_action="Merchants gather in the market",
        composition_style=CompositionStyle.WIDE_SHOT,
        camera_intent=CameraIntent.INVESTIGATION,
        historical_context=HistoricalVisualContext(),
    )

    # An entirely empty context must not inject an empty/near-empty clause.
    assert ",  ," not in prompt


def test_build_locks_character_appearance_when_matched():
    character = CharacterVisualIdentity(
        name="Mansa Musa",
        clothing="cream robes trimmed in gold",
        accessories="a simple gold crown",
    )

    prompt = _builder().build(
        subject_and_action="The king rides across the desert",
        composition_style=CompositionStyle.WIDE_SHOT,
        camera_intent=CameraIntent.NEUTRAL_OBSERVATION,
        character=character,
    )

    assert "Mansa Musa" in prompt
    assert "cream robes trimmed in gold" in prompt
    assert "maintain this exact appearance" in prompt


def test_build_applies_color_language_and_lighting():
    prompt = _builder().build(
        subject_and_action="A tense standoff",
        composition_style=CompositionStyle.REACTION_SHOT,
        camera_intent=CameraIntent.EMOTIONAL_FOCUS,
        color_language=ColorLanguage.TENSION,
        lighting="single hard sidelight",
    )

    assert "single hard sidelight" in prompt
    assert "high-contrast tense color grade" in prompt


def test_build_includes_continuity_tags_and_mood():
    prompt = _builder().build(
        subject_and_action="The old lighthouse at dusk",
        composition_style=CompositionStyle.WIDE_SHOT,
        camera_intent=CameraIntent.NEUTRAL_OBSERVATION,
        mood="melancholy",
        continuity_tags=["lighthouse", "fog"],
    )

    assert "mood: melancholy" in prompt
    assert "maintain visual continuity with recurring lighthouse, fog" in prompt
