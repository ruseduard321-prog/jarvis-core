from __future__ import annotations

from backend.schemas.audio import VoiceProfile

_GPT4O_MINI_TTS = "gpt-4o-mini-tts"

# Adding a profile is adding one entry here — no code path changes required.
# Voice ids are OpenAI's stock gpt-4o-mini-tts voices; `onyx` is the safe deep-male
# default researched for F26, `cedar`/`marin` are OpenAI's own quality-focused
# recommendations and are worth an ear-test before being promoted to default.
VOICE_PROFILES: dict[str, VoiceProfile] = {
    "documentary_male": VoiceProfile(
        key="documentary_male",
        display_name="Documentary Male",
        model=_GPT4O_MINI_TTS,
        voice="onyx",
        instructions=(
            "Speak like a confident, deep-voiced documentary narrator: deliberate pacing, "
            "quiet authority, and dramatic pauses at commas and sentence breaks."
        ),
        pace=1.0,
    ),
    "documentary_female": VoiceProfile(
        key="documentary_female",
        display_name="Documentary Female",
        model=_GPT4O_MINI_TTS,
        voice="nova",
        instructions="Speak with warm, measured authority and even, deliberate pacing, like a prestige documentary narrator.",
        pace=1.0,
    ),
    "storytelling": VoiceProfile(
        key="storytelling",
        display_name="Storytelling",
        model=_GPT4O_MINI_TTS,
        voice="fable",
        instructions="Speak intimately and curiously, with varied pace that leans in on interesting details.",
        pace=1.0,
    ),
    "historical": VoiceProfile(
        key="historical",
        display_name="Historical",
        model=_GPT4O_MINI_TTS,
        voice="echo",
        instructions="Speak gravely and formally, at a slow, weighted pace befitting historical narration.",
        pace=0.95,
    ),
    "mystery": VoiceProfile(
        key="mystery",
        display_name="Mystery",
        model=_GPT4O_MINI_TTS,
        voice="onyx",
        instructions="Speak quietly and tensely, with deliberate pauses that build suspense.",
        pace=0.95,
    ),
    "news": VoiceProfile(
        key="news",
        display_name="News",
        model=_GPT4O_MINI_TTS,
        voice="alloy",
        instructions="Speak briskly and neutrally, with clipped, efficient delivery like a news broadcast.",
        pace=1.05,
    ),
    "educational": VoiceProfile(
        key="educational",
        display_name="Educational",
        model=_GPT4O_MINI_TTS,
        voice="nova",
        instructions="Speak clearly and warmly, at an even pace suited to teaching a new concept.",
        pace=1.0,
    ),
}

DEFAULT_VOICE_PROFILE_KEY = "documentary_male"


def get_voice_profile(key: str) -> VoiceProfile:
    """Returns the named profile, falling back to the default profile for an
    unknown/blank key rather than raising — a bad config value should never crash
    voice generation."""
    return VOICE_PROFILES.get(key) or VOICE_PROFILES[DEFAULT_VOICE_PROFILE_KEY]
