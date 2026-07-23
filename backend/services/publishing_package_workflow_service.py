from __future__ import annotations

import json
import time
from typing import Any

from backend.core.agent_runtime import AgentRuntime
from backend.core.config import Settings
from backend.core.conversation_engine import ConversationEngine
from backend.core.cost_tracker import CostTracker
from backend.schemas.media import MediaPackage
from backend.schemas.research import PublishingPackage, ReviewedScript
from backend.services.agent_service import AgentService


class PublishingPackageWorkflowService:
    """Produces the final title/description/hashtags publishing metadata from a reviewed
    script and its media package, and assembles the complete `PublishingPackage`."""

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

    async def execute(
        self,
        reviewed_script: ReviewedScript,
        media_package: MediaPackage,
        user_id: str | None,
    ) -> PublishingPackage:
        self._call_durations_ms: list[float] = []
        self._call_texts: list[tuple[str, str]] = []

        if not reviewed_script.revised_script.strip():
            return self._build_failed_package(reviewed_script, "Reviewed script is unusable")

        publishing_agent_id = await self._resolve_agent_id(("publishing_agent", "publishing"), {"publishing"})
        if not publishing_agent_id:
            return self._build_failed_package(reviewed_script, "No active publishing agent is available")

        conversation = await self._conversation_engine.create_conversation(
            title=f"Publishing Package: {reviewed_script.topic[:80]}",
            metadata={"workflow": "publishing_package"},
        )

        publishing_prompt = (
            "Using ONLY the reviewed script, produce strict JSON with keys: "
            "youtube_title (string), youtube_description (string), youtube_tags (array of strings), "
            "youtube_chapters (array of strings), seo_keywords (array of strings), status (string). "
            "Rules: no clickbait, curiosity-driven SEO title, natural description, include source "
            "acknowledgement when appropriate. Return JSON only."
        )

        result = await self._timed_execute(
            conversation_id=conversation.context.conversation_id,
            agent_id=publishing_agent_id,
            message=publishing_prompt,
            user_id=user_id,
            metadata={
                "workflow": "publishing_package",
                "reviewed_script": reviewed_script.model_dump(),
                "artifacts": [reviewed_script.model_dump()],
                "capability_requests": [],
            },
        )

        parsed = self._extract_json_object(result.get("content", ""))
        if not parsed:
            return PublishingPackage(
                reviewed_script=reviewed_script,
                youtube_title="",
                youtube_description="",
                youtube_tags=[],
                youtube_chapters=[],
                seo_keywords=[],
                thumbnail_prompt=media_package.thumbnail_prompt,
                image_prompts=media_package.image_prompts,
                b_roll_suggestions=media_package.b_roll_prompts,
                metadata={
                    "status": "partial",
                    "reason": "Publishing output was not valid JSON",
                    "conversation_id": conversation.context.conversation_id,
                    **self._build_provider_metrics(
                        success=False, failure_reason="Publishing output was not valid JSON"
                    ),
                },
            )

        return PublishingPackage(
            reviewed_script=reviewed_script,
            youtube_title=str(parsed.get("youtube_title", "")).strip(),
            youtube_description=str(parsed.get("youtube_description", "")).strip(),
            youtube_tags=[str(tag).strip() for tag in parsed.get("youtube_tags", []) if str(tag).strip()],
            youtube_chapters=[
                str(chapter).strip() for chapter in parsed.get("youtube_chapters", []) if str(chapter).strip()
            ],
            seo_keywords=[str(keyword).strip() for keyword in parsed.get("seo_keywords", []) if str(keyword).strip()],
            thumbnail_prompt=media_package.thumbnail_prompt,
            image_prompts=media_package.image_prompts,
            b_roll_suggestions=media_package.b_roll_prompts,
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

    def _build_failed_package(self, reviewed_script: ReviewedScript, reason: str) -> PublishingPackage:
        return PublishingPackage(
            reviewed_script=reviewed_script,
            youtube_title="",
            youtube_description="",
            youtube_tags=[],
            youtube_chapters=[],
            seo_keywords=[],
            thumbnail_prompt="",
            image_prompts=[],
            b_roll_suggestions=[],
            metadata={
                "status": "failed",
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
