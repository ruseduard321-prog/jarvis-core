from __future__ import annotations

from backend.schemas.visual_identity import CharacterVisualIdentity, HistoricalVisualContext, VisualIdentityContext


def test_historical_context_as_prompt_fragment_joins_populated_fields():
    context = HistoricalVisualContext(time_period="79 AD", geography="Bay of Naples", weather_and_atmosphere="ash and smoke")

    fragment = context.as_prompt_fragment()

    assert "set in 79 AD" in fragment
    assert "in Bay of Naples" in fragment
    assert "atmosphere: ash and smoke" in fragment


def test_historical_context_is_empty_when_all_fields_blank():
    assert HistoricalVisualContext().is_empty() is True
    assert HistoricalVisualContext(time_period="79 AD").is_empty() is False


def test_character_matches_name_case_insensitively():
    character = CharacterVisualIdentity(name="Mansa Musa")

    assert character.matches("Mansa Musa rides across the desert") is True
    assert character.matches("mansa musa arrives at Timbuktu") is True
    assert character.matches("A caravan crosses the Sahara") is False


def test_character_matches_alias():
    character = CharacterVisualIdentity(name="Mansa Musa", aliases=["the king", "Musa I"])

    assert character.matches("The king surveys his empire") is True
    assert character.matches("Musa I holds court") is True


def test_character_matches_requires_whole_word():
    character = CharacterVisualIdentity(name="Musa")

    assert character.matches("Musa arrives") is True
    assert character.matches("Musashi arrives") is False


def test_character_as_prompt_fragment_includes_populated_fields():
    character = CharacterVisualIdentity(
        name="Mansa Musa",
        age_appearance="middle-aged",
        hair="short black hair, trimmed beard",
        clothing="cream robes trimmed in gold",
    )

    fragment = character.as_prompt_fragment()

    assert "Mansa Musa" in fragment
    assert "a middle-aged" in fragment
    assert "hair: short black hair" in fragment
    assert "wearing cream robes trimmed in gold" in fragment


def test_reference_portrait_prompt_is_a_neutral_single_subject_prompt():
    character = CharacterVisualIdentity(name="Mansa Musa", clothing="cream robes")

    prompt = character.reference_portrait_prompt()

    assert "Studio reference portrait of Mansa Musa" in prompt
    assert "neutral plain background" in prompt
    assert "photorealistic documentary character reference sheet" in prompt


def test_visual_identity_context_character_for_returns_first_match():
    characters = [
        CharacterVisualIdentity(name="Mansa Musa"),
        CharacterVisualIdentity(name="Ibn Battuta"),
    ]
    context = VisualIdentityContext(topic="Test", characters=characters)

    assert context.character_for("Mansa Musa rides west").name == "Mansa Musa"
    assert context.character_for("Ibn Battuta records his travels").name == "Ibn Battuta"
    assert context.character_for("An empty desert horizon") is None
