from __future__ import annotations

import logging
import traceback
from typing import Any

from backend.core.config import Settings
from backend.core.llm_exceptions import LLMGenerationError, LLMHealthError, LLMInitializationError
from backend.core.llm_models import LLMRequest, LLMResponse, LLMUsage
from backend.core.llm_provider import LLMProvider

logger = logging.getLogger(__name__)


class OpenAIProvider(LLMProvider):
    """OpenAI-compatible LLM provider implementation using SDK v1.x."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._client: Any = None
        self._initialized = False

    @property
    def name(self) -> str:
        return "openai"

    async def initialize(self) -> None:
        try:
            logger.info("🔵 OPENAI PROVIDER INITIALIZATION STARTING")
            
            # Log configuration state
            logger.info(f"🔵 Settings check:")
            logger.info(f"   - openai_api_key set: {self.settings.openai_api_key is not None}")
            logger.info(f"   - openai_api_key empty: {self.settings.openai_api_key == ''}")
            logger.info(f"   - openai_api_key value: {'***' if self.settings.openai_api_key else 'NONE'}")
            logger.info(f"   - openai_api_base: {self.settings.openai_api_base}")
            logger.info(f"   - default_llm_model: {getattr(self.settings, 'default_llm_model', 'NOT SET')}")
            
            # Step 1: Check API key
            if self.settings.openai_api_key is None:
                logger.error("🔴 OPENAI_API_KEY is None in settings")
                raise LLMInitializationError("OPENAI_API_KEY is not configured")
            
            if self.settings.openai_api_key == "":
                logger.error("🔴 OPENAI_API_KEY is empty string in settings")
                raise LLMInitializationError("OPENAI_API_KEY is empty")
            
            logger.info(f"🟢 API key verified (length: {len(self.settings.openai_api_key)} chars)")
            
            # Step 2: Import AsyncOpenAI
            logger.info("🔵 Attempting to import AsyncOpenAI...")
            try:
                from openai import AsyncOpenAI
                logger.info("🟢 AsyncOpenAI imported successfully")
            except ImportError as import_err:
                logger.error(f"🔴 Failed to import AsyncOpenAI: {import_err}")
                logger.error(f"🔴 Exception type: {type(import_err).__name__}")
                logger.error(f"🔴 Full traceback:\n{traceback.format_exc()}")
                raise LLMInitializationError("OpenAI SDK is not installed") from import_err
            
            # Step 3: Create AsyncOpenAI client
            logger.info("🔵 Creating AsyncOpenAI client...")
            logger.info(f"   - API key: {'***' if self.settings.openai_api_key else 'NONE'}")
            logger.info(f"   - Base URL: {self.settings.openai_api_base if self.settings.openai_api_base else 'default (api.openai.com)'}")
            
            try:
                self._client = AsyncOpenAI(
                    api_key=self.settings.openai_api_key,
                    base_url=self.settings.openai_api_base if self.settings.openai_api_base else None,
                )
                logger.info(f"🟢 AsyncOpenAI client created: {type(self._client).__name__}")
            except Exception as client_err:
                logger.error(f"🔴 Failed to create AsyncOpenAI client: {client_err}")
                logger.error(f"🔴 Exception type: {type(client_err).__name__}")
                logger.error(f"🔴 Full traceback:\n{traceback.format_exc()}")
                raise LLMInitializationError(f"Failed to create OpenAI client: {client_err}") from client_err
            
            self._initialized = True
            logger.info("🟢 OPENAI PROVIDER INITIALIZATION COMPLETE")
            
        except ImportError as exc:
            logger.error(f"🔴 IMPORTERROR during initialization: {exc}")
            logger.error(f"🔴 Full traceback:\n{traceback.format_exc()}")
            raise LLMInitializationError("OpenAI SDK is not installed") from exc
        except LLMInitializationError as exc:
            # Re-raise LLMInitializationError as-is (don't double-wrap)
            logger.error(f"🔴 LLM INITIALIZATION ERROR: {exc}")
            logger.error(f"🔴 Full traceback:\n{traceback.format_exc()}")
            raise
        except Exception as exc:
            logger.error(f"🔴 UNEXPECTED EXCEPTION during initialization: {type(exc).__name__}: {exc}")
            logger.error(f"🔴 Full traceback:\n{traceback.format_exc()}")
            raise LLMInitializationError(f"Failed to initialize OpenAI provider: {type(exc).__name__}: {exc}") from exc

    async def health(self) -> bool:
        if not self._initialized:
            await self.initialize()

        try:
            logger.info("🔵 Performing health check...")
            # Simple health check by listing models
            models = await self._client.models.list()
            model_list = list(models)
            logger.info(f"🟢 Health check successful: {len(model_list)} models available")
            return len(model_list) > 0
        except Exception as exc:
            logger.error(f"🔴 HEALTH CHECK FAILED: {type(exc).__name__}: {exc}")
            logger.error(f"🔴 Full traceback:\n{traceback.format_exc()}")
            raise LLMHealthError(f"OpenAI health check failed: {type(exc).__name__}: {exc}") from exc

    def _build_input(self, request: LLMRequest) -> list[dict[str, Any]]:
        """Convert standardized messages into Responses API `input` items."""
        return [
            {"role": message.role, "content": message.content, **({"name": message.name} if message.name else {})}
            for message in request.messages
        ]

    def _temperature_kwargs(self, request: LLMRequest) -> dict[str, Any]:
        """Reasoning-family models (gpt-5*, o1/o3/o4*) reject the `temperature`
        parameter outright, so it's only forwarded for models that accept it."""
        reasoning_prefixes = ("gpt-5", "o1", "o3", "o4")
        if request.model.startswith(reasoning_prefixes):
            return {}
        return {"temperature": request.temperature}

    def _translate_options(self, options: dict[str, Any] | None) -> dict[str, Any]:
        """Translate Chat-Completions-style options (e.g. response_format) into their
        Responses API equivalents, passing through anything else unchanged."""
        translated = dict(options or {})
        response_format = translated.pop("response_format", None)
        if response_format is not None:
            translated["text"] = {"format": response_format}
        return translated

    async def generate(self, request: LLMRequest) -> LLMResponse:
        if not self._initialized:
            logger.info("🔵 Provider not initialized, initializing now...")
            await self.initialize()

        try:
            logger.info(f"🔵 Generating completion:")
            logger.info(f"   - Model: {request.model}")
            logger.info(f"   - Messages: {len(request.messages)}")
            logger.info(f"   - Temperature: {request.temperature}")
            logger.info(f"   - Max tokens: {request.max_tokens}")

            input_items = self._build_input(request)

            logger.info(f"🔵 Calling OpenAI API...")
            # Call OpenAI Responses API asynchronously
            response = await self._client.responses.create(
                model=request.model,
                input=input_items,
                max_output_tokens=request.max_tokens,
                **self._temperature_kwargs(request),
                **self._translate_options(request.options),
            )

            logger.info(f"🟢 OpenAI API call successful")

            content = response.output_text or ""
            logger.info(f"   - Response length: {len(content)} chars")

            usage = None
            if response.usage is not None:
                usage = LLMUsage(
                    prompt_tokens=response.usage.input_tokens,
                    completion_tokens=response.usage.output_tokens,
                    total_tokens=response.usage.total_tokens,
                )
                logger.info(f"   - Tokens: {usage.total_tokens} ({usage.prompt_tokens} prompt, {usage.completion_tokens} completion)")

            return LLMResponse(
                id=response.id,
                model=response.model,
                output=content,
                usage=usage,
                raw_response=response,
            )
        except Exception as exc:
            logger.error(f"🔴 GENERATION FAILED: {type(exc).__name__}: {exc}")
            logger.error(f"🔴 Full traceback:\n{traceback.format_exc()}")
            raise LLMGenerationError(f"OpenAI generation failed: {type(exc).__name__}: {exc}") from exc

    async def stream(self, request: LLMRequest) -> Any:
        """Stream completions from OpenAI API.

        Forwards each incremental text delta as its own `LLMResponse` the moment it
        arrives, then yields one terminal `LLMResponse` (`is_final=True`, empty `output`)
        carrying the completion's id/model/usage once the Responses API signals the
        stream is done (completed, incomplete, or failed).
        """
        if not self._initialized:
            logger.info("🔵 Provider not initialized, initializing now...")
            await self.initialize()

        try:
            logger.info(f"🔵 Starting streaming completion:")
            logger.info(f"   - Model: {request.model}")
            logger.info(f"   - Messages: {len(request.messages)}")

            input_items = self._build_input(request)

            logger.info(f"🔵 Creating streaming request...")
            # Create streaming Responses API request
            stream = await self._client.responses.create(
                model=request.model,
                input=input_items,
                max_output_tokens=request.max_tokens,
                stream=True,
                **self._temperature_kwargs(request),
                **self._translate_options(request.options),
            )

            logger.info(f"🔵 Streaming tokens...")
            token_count = 0
            total_chars = 0
            async for event in stream:
                if event.type == "response.output_text.delta":
                    delta = event.delta
                    token_count += 1
                    total_chars += len(delta)
                    if token_count % 10 == 0:
                        logger.info(f"   - Forwarded {token_count} chunks, {total_chars} chars so far")
                    yield LLMResponse(
                        id="",
                        model=request.model,
                        output=delta,
                        usage=None,
                        raw_response=None,
                        is_final=False,
                    )
                elif event.type in ("response.completed", "response.incomplete", "response.failed"):
                    completed_response = event.response
                    usage = None
                    if getattr(completed_response, "usage", None) is not None:
                        usage = LLMUsage(
                            prompt_tokens=completed_response.usage.input_tokens,
                            completion_tokens=completed_response.usage.output_tokens,
                            total_tokens=completed_response.usage.total_tokens,
                        )
                    logger.info(
                        f"🟢 Streaming complete ({event.type}): {token_count} chunks, {total_chars} chars total"
                    )
                    yield LLMResponse(
                        id=completed_response.id,
                        model=completed_response.model,
                        output="",
                        usage=usage,
                        raw_response=completed_response,
                        is_final=True,
                    )
        except Exception as exc:
            logger.error(f"🔴 STREAMING FAILED: {type(exc).__name__}: {exc}")
            logger.error(f"🔴 Full traceback:\n{traceback.format_exc()}")
            raise LLMGenerationError(f"OpenAI streaming failed: {type(exc).__name__}: {exc}") from exc

    async def get_client(self) -> Any:
        """Expose the shared AsyncOpenAI client for other OpenAI-backed providers
        (image/TTS/STT) so they never create a second client."""
        if not self._initialized:
            await self.initialize()
        return self._client

    async def shutdown(self) -> None:
        try:
            if self._client is not None:
                logger.info("🔵 Closing OpenAI client...")
                await self._client.close()
                logger.info("🟢 OpenAI client closed")
        except Exception as exc:
            logger.error(f"🔴 Error during shutdown: {type(exc).__name__}: {exc}")
            logger.error(f"🔴 Full traceback:\n{traceback.format_exc()}")
        finally:
            self._initialized = False
