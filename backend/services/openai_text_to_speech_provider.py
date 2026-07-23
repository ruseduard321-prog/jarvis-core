from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any

from backend.core.config import Settings
from backend.core.cost_tracker import CostTracker
from backend.core.openai_error_classification import classify_openai_error
from backend.core.openai_llm_provider import OpenAIProvider
from backend.core.provider_exceptions import PermanentProviderError
from backend.core.retry import retry_with_backoff
from backend.schemas.assets import VoiceAsset
from backend.services.text_to_speech_provider import TextToSpeechProvider

logger = logging.getLogger(__name__)

_WORDS_PER_MINUTE = 150.0
_MAX_INPUT_CHARS = 4000  # OpenAI's Audio Speech API rejects `input` over 4096 characters


class OpenAITextToSpeechProvider(TextToSpeechProvider):
    """Real OpenAI Audio Speech API-backed provider. Reuses the shared AsyncOpenAI
    client from `OpenAIProvider` — never creates a second client."""

    def __init__(
        self,
        openai_llm_provider: OpenAIProvider,
        settings: Settings,
        cost_tracker: CostTracker | None = None,
    ) -> None:
        self._openai_llm_provider = openai_llm_provider
        self._settings = settings
        self._cost_tracker = cost_tracker or CostTracker()

    async def generate_speech(
        self,
        *,
        text: str,
        model: str | None = None,
        voice: str | None = None,
        speed: float | None = None,
        language: str | None = None,
        instructions: str | None = None,
    ) -> tuple[VoiceAsset, bytes]:
        client = await self._openai_llm_provider.get_client()
        resolved_model = model or self._settings.openai_tts_model
        resolved_voice = voice or self._settings.openai_tts_voice
        resolved_speed = speed if speed is not None else self._settings.openai_tts_speed

        audio_chunks: list[bytes] = []
        retry_count = 0
        started_at = time.perf_counter()
        for chunk in self._chunk_text(text):

            def _record_attempt(attempt: int) -> None:
                nonlocal retry_count
                if attempt > 1:
                    retry_count += 1

            async def _call(chunk: str = chunk) -> Any:
                # `instructions` (delivery direction) is only sent when provided —
                # older models (tts-1/tts-1-hd) don't accept it, so callers that
                # don't pass one see byte-for-byte the same request as before.
                extra_kwargs: dict[str, Any] = {"instructions": instructions} if instructions else {}
                try:
                    return await client.audio.speech.create(
                        model=resolved_model,
                        voice=resolved_voice,
                        input=chunk,
                        speed=resolved_speed,
                        **extra_kwargs,
                    )
                except Exception as exc:
                    raise classify_openai_error(exc) from exc

            response = await retry_with_backoff(_call, on_attempt=_record_attempt)
            audio_chunks.append(await self._read_audio_bytes(response))

        duration_ms = (time.perf_counter() - started_at) * 1000
        audio_bytes = b"".join(audio_chunks)
        cost_estimate = self._cost_tracker.estimate_tts_cost(
            provider="openai-tts", model=resolved_model, char_count=len(text)
        )

        asset = VoiceAsset(
            provider="openai-tts",
            model=resolved_model,
            voice=resolved_voice,
            language=language or "en",
            duration=self._estimate_duration(text, resolved_speed),
            generation_time=datetime.now(timezone.utc).isoformat(),
            status="SUCCESS",
            generation_duration_ms=round(duration_ms, 2),
            retry_count=retry_count,
            estimated_input_tokens=cost_estimate.estimated_input_tokens,
            estimated_output_tokens=cost_estimate.estimated_output_tokens,
            estimated_cost_usd=cost_estimate.estimated_cost_usd,
        )
        return asset, audio_bytes

    def _chunk_text(self, text: str, max_chars: int = _MAX_INPUT_CHARS) -> list[str]:
        """Split narration text into API-sized chunks, breaking on sentence boundaries
        where possible so each TTS call still gets natural-sounding input."""
        text = text.strip()
        if len(text) <= max_chars:
            return [text]

        chunks: list[str] = []
        remaining = text
        while len(remaining) > max_chars:
            window = remaining[:max_chars]
            split_at = max(window.rfind(". "), window.rfind("\n"))
            if split_at <= 0:
                split_at = max_chars
            else:
                split_at += 1
            chunks.append(remaining[:split_at].strip())
            remaining = remaining[split_at:].strip()
        if remaining:
            chunks.append(remaining)
        return chunks

    async def _read_audio_bytes(self, response: Any) -> bytes:
        content = getattr(response, "content", None)
        if content is not None:
            return content
        aread = getattr(response, "aread", None)
        if aread is not None:
            return await aread()
        raise PermanentProviderError("OpenAI TTS response did not expose audio bytes")

    def _estimate_duration(self, text: str, speed: float) -> float:
        """OpenAI's TTS API does not return audio duration. Estimate from word count
        and a baseline reading rate rather than adding an audio-decoding dependency."""
        word_count = len(text.split())
        effective_speed = speed if speed and speed > 0 else 1.0
        minutes = word_count / (_WORDS_PER_MINUTE * effective_speed)
        return round(minutes * 60, 2)
