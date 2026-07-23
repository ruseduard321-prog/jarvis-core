from __future__ import annotations

import json
import time
from typing import Any

from backend.core.agent_runtime import AgentRuntime
from backend.core.config import Settings
from backend.core.conversation_engine import ConversationEngine
from backend.core.cost_tracker import CostTracker
from backend.schemas.media import MediaPackage
from backend.schemas.research import ReviewedScript
from backend.services.agent_service import AgentService


class MediaWorkflowService:
    """Produces media production prompts from a reviewed script, extracted/expanded from
    the original ContentFinalizationWorkflowService so Media is its own pipeline stage."""

    def __init__(
        self,
        conversation_engine: ConversationEngine,
        agent_runtime: AgentRuntime,
        agent_service: AgentService,
        settings: Settings | None = None,
        cost_tracker: CostTracker | None = None,
    ) -> None:
        self._conversation_engine = conversation_engine
        self._agent_runtime = agent_runtime
        self._agent_service = agent_service
        self._settings = settings or Settings()
        self._cost_tracker = cost_tracker or CostTracker()

    async def execute(self, reviewed_script: ReviewedScript, user_id: str | None) -> MediaPackage:
        self._call_durations_ms: list[float] = []
        self._call_texts: list[tuple[str, str]] = []

        if not reviewed_script.revised_script.strip():
            return self._build_failed_package("Reviewed script is unusable")

        media_agent_id = await self._resolve_agent_id(("media_agent", "media"), {"media"})
        if not media_agent_id:
            return self._build_failed_package("No active media agent is available")

        conversation = await self._conversation_engine.create_conversation(
            title=f"Media Prompts: {reviewed_script.topic[:80]}",
            metadata={"workflow": "media"},
        )

        media_prompt = (
            "Using ONLY the reviewed script, produce strict JSON with keys: "
            "thumbnail_prompt (string), scene_prompts (array of strings), b_roll_prompts (array of strings), "
            "image_prompts (array of strings), animation_prompts (array of strings), "
            "voice_over_notes (array of strings), music_direction (string), status (string). "
            "Rules: cinematic high-contrast emotional thumbnail prompt, one scene prompt per major section, "
            "no clickbait, do not generate images. Return JSON only."
        )

        result = await self._timed_execute(
            conversation_id=conversation.context.conversation_id,
            agent_id=media_agent_id,
            message=media_prompt,
            user_id=user_id,
            metadata={
                "workflow": "media",
                "reviewed_script": reviewed_script.model_dump(),
                "artifacts": [reviewed_script.model_dump()],
                "capability_requests": [],
            },
        )

        parsed = self._extract_json_object(result.get("content", ""))
        if not parsed:
            return self._build_partial_package("Media output was not valid JSON")

        return MediaPackage(
            thumbnail_prompt=str(parsed.get("thumbnail_prompt", "")).strip(),
            scene_prompts=[str(item).strip() for item in parsed.get("scene_prompts", []) if str(item).strip()],
            b_roll_prompts=[str(item).strip() for item in parsed.get("b_roll_prompts", []) if str(item).strip()],
            image_prompts=[str(item).strip() for item in parsed.get("image_prompts", []) if str(item).strip()],
            animation_prompts=[
                str(item).strip() for item in parsed.get("animation_prompts", []) if str(item).strip()
            ],
            voice_over_notes=[
                str(item).strip() for item in parsed.get("voice_over_notes", []) if str(item).strip()
            ],
            music_direction=str(parsed.get("music_direction", "")).strip(),
            metadata={
                "status": "success",
                "conversation_id": conversation.context.conversation_id,
                **self._build_provider_metrics(success=True),
            },
        )

    async def _timed_execute(self, **kwargs: Any) -> dict[str, Any]:
        started_at = time.perf_counter()
        result = await self._agent_runtime.execute(**kwargs)
        self._call_durations_ms.append((time.perf_counter() - started_at) * 1000)
        self._call_texts.append((str(kwargs.get("message", "")), str(result.get("content", ""))))
        return result

    def _build_provider_metrics(self, success: bool, failure_reason: str | None = None) -> dict[str, Any]:
        model = self._settings.default_llm_model
        total_duration_ms = round(sum(self._call_durations_ms), 2)
        cost_estimate = self._cost_tracker.estimate_text_cost(
            provider="openai",
            model=model,
            input_text="\n".join(text for text, _ in self._call_texts),
            output_text="\n".join(text for _, text in self._call_texts),
        )
        provider_metrics = {
            "provider": "openai",
            "model": model,
            "call_count": len(self._call_durations_ms),
            "duration_ms": total_duration_ms,
            "success": success,
            "failure_reason": failure_reason,
        }
        return {"provider_metrics": provider_metrics, "cost_estimate": cost_estimate.__dict__}

    async def _resolve_agent_id(self, candidates: tuple[str, ...], fallback_slugs: set[str]) -> str | None:
        for candidate in candidates:
            try:
                candidate_agent = await self._agent_service.get_agent(candidate)
                if candidate_agent.is_active:
                    return candidate_agent.id
            except Exception:
                continue

        try:
            agents = await self._agent_service.list_agents(active_only=True)
        except Exception:
            return None

        for agent in agents:
            if agent.slug in fallback_slugs:
                return agent.id
        return None

    def _build_failed_package(self, reason: str) -> MediaPackage:
        return MediaPackage(
            thumbnail_prompt="",
            scene_prompts=[],
            b_roll_prompts=[],
            image_prompts=[],
            animation_prompts=[],
            voice_over_notes=[],
            music_direction="",
            metadata={
                "status": "failed",
                "reason": reason,
                **self._build_provider_metrics(success=False, failure_reason=reason),
            },
        )

    def _build_partial_package(self, reason: str) -> MediaPackage:
        return MediaPackage(
            thumbnail_prompt="",
            scene_prompts=[],
            b_roll_prompts=[],
            image_prompts=[],
            animation_prompts=[],
            voice_over_notes=[],
            music_direction="",
            metadata={
                "status": "partial",
                "reason": reason,
                **self._build_provider_metrics(success=False, failure_reason=reason),
            },
        )

    def _extract_json_object(self, content: str) -> dict[str, Any] | None:
        text = (content or "").strip()
        if not text:
            return None

        try:
            loaded = json.loads(text)
            return loaded if isinstance(loaded, dict) else None
        except json.JSONDecodeError:
            pass

        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None

        snippet = text[start : end + 1]
        try:
            loaded = json.loads(snippet)
            return loaded if isinstance(loaded, dict) else None
        except json.JSONDecodeError:
            return None
