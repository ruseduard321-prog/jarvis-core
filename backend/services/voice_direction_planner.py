from __future__ import annotations

from abc import ABC, abstractmethod

from backend.schemas.audio import VoiceDirection
from backend.services.voice_profiles import get_voice_profile


class VoiceDirectionPlanner(ABC):
    """Resolves how narration should be delivered — the single seam between planning
    ('how should this be voiced') and generation ('call the TTS provider'). F28 (AI
    Director) is expected to add an LLM-driven implementation of this interface later;
    VoiceGenerationService only ever consumes a VoiceDirection, so it needs no changes
    when that happens — mirrors ShotPlanner's relationship to RendererPipeline."""

    @abstractmethod
    def plan(self, *, profile_key: str) -> VoiceDirection:
        """Returns the VoiceDirection to use for one narration generation call."""


class DeterministicVoiceDirectionPlanner(VoiceDirectionPlanner):
    """F26 implementation: a direct profile lookup, no LLM call, zero added cost.
    Adding richer per-scene direction later is a new implementation of this
    interface, not a change to this one."""

    def plan(self, *, profile_key: str) -> VoiceDirection:
        profile = get_voice_profile(profile_key)
        return VoiceDirection(
            profile=profile.key,
            model=profile.model,
            voice=profile.voice,
            pace=profile.pace,
            instructions=profile.instructions,
        )
