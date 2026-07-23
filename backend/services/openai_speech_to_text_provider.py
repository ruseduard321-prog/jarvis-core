from __future__ import annotations

import io
import logging
from datetime import datetime, timezone
from typing import Any

from backend.core.config import Settings
from backend.core.openai_error_classification import classify_openai_error
from backend.core.openai_llm_provider import OpenAIProvider
from backend.core.retry import retry_with_backoff
from backend.schemas.assets import TranscriptAsset
from backend.services.speech_to_text_provider import SpeechToTextProvider

logger = logging.getLogger(__name__)


class OpenAISpeechToTextProvider(SpeechToTextProvider):
    """Real OpenAI Audio Transcriptions API-backed provider. Reuses the shared
    AsyncOpenAI client from `OpenAIProvider` — never creates a second client.
    Prepared as a platform capability; not called by the YouTube production
    workflow today (see `SpeechToTextProvider`)."""

    def __init__(self, openai_llm_provider: OpenAIProvider, settings: Settings) -> None:
        self._openai_llm_provider = openai_llm_provider
        self._settings = settings

    async def transcribe(
        self,
        *,
        audio_bytes: bytes,
        filename: str = "audio.mp3",
        language: str | None = None,
    ) -> tuple[TranscriptAsset, str]:
        client = await self._openai_llm_provider.get_client()
        resolved_model = self._settings.openai_stt_model

        async def _call() -> Any:
            try:
                file_obj = io.BytesIO(audio_bytes)
                file_obj.name = filename
                kwargs: dict[str, Any] = {"model": resolved_model, "file": file_obj}
                if language:
                    kwargs["language"] = language
                return await client.audio.transcriptions.create(**kwargs)
            except Exception as exc:
                raise classify_openai_error(exc) from exc

        response = await retry_with_backoff(_call)
        text = getattr(response, "text", "") or ""
        detected_language = getattr(response, "language", None) or language or ""

        asset = TranscriptAsset(
            provider="openai-stt",
            model=resolved_model,
            language=detected_language,
            text=text,
            generation_time=datetime.now(timezone.utc).isoformat(),
            status="SUCCESS",
        )
        return asset, text
