from __future__ import annotations

import json
import time
from typing import Any

from backend.core.agent_runtime import AgentRuntime
from backend.core.config import Settings
from backend.core.conversation_engine import ConversationEngine
from backend.core.cost_tracker import CostTracker
from backend.schemas.research import ReviewedScript, ScriptDraft
from backend.services.agent_service import AgentService


class ReviewWorkflowService:
    """Runs a quality review pass over a script draft, extracted from the original
    ContentFinalizationWorkflowService so Review is its own pipeline stage."""

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

    async def execute(self, script_draft: ScriptDraft, user_id: str | None) -> ReviewedScript:
        self._call_durations_ms: list[float] = []
        self._call_texts: list[tuple[str, str]] = []

        if not self._is_usable(script_draft):
            return self._build_failed_review(script_draft, "Script draft is unusable")

        review_agent_id = await self._resolve_agent_id(("review_agent", "review"), {"review"})
        if not review_agent_id:
            return self._build_failed_review(script_draft, "No active review agent is available")

        conversation = await self._conversation_engine.create_conversation(
            title=f"Review: {script_draft.topic[:80]}",
            metadata={"workflow": "review"},
        )

        review_prompt = (
            "Review ONLY the supplied script draft and produce strict JSON with keys: "
            "revised_script (string), change_summary (array of strings), factual_notes (array of strings), "
            "quality_score (number), readability_score (number), engagement_score (number), status (string). "
            "Goals: improve readability, pacing, storytelling, retention, consistency, unsupported-claim detection, "
            "while preserving original meaning. Do not browse, do not read URLs, do not use external facts. "
            "Return JSON only."
        )

        result = await self._timed_execute(
            conversation_id=conversation.context.conversation_id,
            agent_id=review_agent_id,
            message=review_prompt,
            user_id=user_id,
            metadata={
                "workflow": "review",
                "script_draft": script_draft.model_dump(),
                "artifacts": [script_draft.model_dump()],
                "capability_requests": [],
            },
        )

        parsed = self._extract_json_object(result.get("content", ""))
        if not parsed:
            return ReviewedScript(
                topic=script_draft.topic,
                revised_script=script_draft.narration_script,
                change_summary=["Fallback review output used due to invalid agent JSON"],
                factual_notes=[],
                quality_score=70.0,
                readability_score=70.0,
                engagement_score=70.0,
                status="partial",
                metadata={
                    "status": "partial",
                    "reason": "Review output parse failure",
                    **self._build_provider_metrics(success=False, failure_reason="Review output parse failure"),
                },
            )

        revised_script = str(parsed.get("revised_script", "")).strip() or script_draft.narration_script
        return ReviewedScript(
            topic=script_draft.topic,
            revised_script=revised_script,
            change_summary=[str(item).strip() for item in parsed.get("change_summary", []) if str(item).strip()],
            factual_notes=[str(item).strip() for item in parsed.get("factual_notes", []) if str(item).strip()],
            quality_score=self._to_score(parsed.get("quality_score"), 75.0),
            readability_score=self._to_score(parsed.get("readability_score"), 75.0),
            engagement_score=self._to_score(parsed.get("engagement_score"), 75.0),
            status=str(parsed.get("status", "success")).strip() or "success",
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

    def _is_usable(self, script_draft: ScriptDraft) -> bool:
        if script_draft.topic.strip():
            return True
        if script_draft.narration_script.strip():
            return True
        if script_draft.sections:
            return True
        return False

    def _build_failed_review(self, script_draft: ScriptDraft, reason: str) -> ReviewedScript:
        return ReviewedScript(
            topic=script_draft.topic,
            revised_script=script_draft.narration_script,
            change_summary=[],
            factual_notes=[reason],
            quality_score=0.0,
            readability_score=0.0,
            engagement_score=0.0,
            status="failed",
            metadata={
                "status": "failed",
                "reason": reason,
                **self._build_provider_metrics(success=False, failure_reason=reason),
            },
        )

    def _to_score(self, value: Any, default: float) -> float:
        try:
            score = float(value)
        except (TypeError, ValueError):
            return default
        return max(0.0, min(100.0, score))

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
