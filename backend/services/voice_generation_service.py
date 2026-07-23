from __future__ import annotations

import logging
from datetime import datetime, timezone

from backend.core.config import Settings
from backend.core.provider_exceptions import PermanentProviderError, ProviderError, TransientProviderError
from backend.schemas.assets import VoiceAsset
from backend.schemas.research import ReviewedScript
from backend.services.narration_processing_service import NarrationProcessingService
from backend.services.text_to_speech_provider import TextToSpeechProvider
from backend.services.voice_direction_planner import DeterministicVoiceDirectionPlanner, VoiceDirectionPlanner

logger = logging.getLogger(__name__)


class VoiceGenerationService:
    """Generates the narration voice-over track from a reviewed script: resolves a
    VoiceDirection (VoiceDirectionPlanner), calls the TTS provider with it, then runs
    Narration Processing (loudness normalization) on the result. Never raises —
    provider failures are captured as a FAILED VoiceAsset so the workflow continues."""

    def __init__(
        self,
        text_to_speech_provider: TextToSpeechProvider,
        settings: Settings,
        voice_direction_planner: VoiceDirectionPlanner | None = None,
        narration_processing_service: NarrationProcessingService | None = None,
    ) -> None:
        self._provider = text_to_speech_provider
        self._settings = settings
        self._voice_direction_planner = voice_direction_planner or DeterministicVoiceDirectionPlanner()
        self._narration_processing_service = narration_processing_service or NarrationProcessingService(settings)

    async def execute(self, reviewed_script: ReviewedScript) -> tuple[VoiceAsset, bytes | None]:
        text = reviewed_script.revised_script.strip()
        if not text:
            return self._skipped("Reviewed script has no narration text"), None

        direction = self._voice_direction_planner.plan(profile_key=self._settings.voice_profile)

        try:
            asset, audio_bytes = await self._provider.generate_speech(
                text=text,
                model=direction.model,
                voice=direction.voice,
                speed=direction.pace,
                instructions=direction.instructions,
            )
            if asset.status != "SUCCESS":
                return asset, None
            asset = asset.model_copy(update={"voice_profile": direction.profile})
            processed_bytes = self._narration_processing_service.process(audio_bytes) if audio_bytes else audio_bytes
            return asset, processed_bytes
        except (PermanentProviderError, TransientProviderError, ProviderError) as exc:
            logger.warning("voice_generation_failed", extra={"reason": str(exc)})
            return self._failed(str(exc)), None
        except Exception as exc:  # pragma: no cover - defensive path
            logger.exception("voice_generation_unexpected_failure")
            return self._failed(f"Unexpected voice generation failure: {exc}"), None

    def _skipped(self, reason: str) -> VoiceAsset:
        return VoiceAsset(
            provider="none",
            generation_time=datetime.now(timezone.utc).isoformat(),
            status="SKIPPED",
            error=reason,
        )

    def _failed(self, reason: str) -> VoiceAsset:
        return VoiceAsset(
            provider="none",
            generation_time=datetime.now(timezone.utc).isoformat(),
            status="FAILED",
            error=reason,
        )
