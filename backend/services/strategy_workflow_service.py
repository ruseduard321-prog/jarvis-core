from __future__ import annotations

import json
import time
from typing import Any

from backend.core.agent_runtime import AgentRuntime
from backend.core.config import Settings
from backend.core.conversation_engine import ConversationEngine
from backend.core.cost_tracker import CostTracker
from backend.schemas.research import ResearchPackage
from backend.schemas.strategy import StrategyPackage
from backend.services.agent_service import AgentService


class StrategyWorkflowService:
    """Transforms a research package into a content strategy for the Writer Agent."""

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

    async def execute(self, research_package: ResearchPackage, user_id: str | None) -> StrategyPackage:
        self._call_durations_ms: list[float] = []
        self._call_texts: list[tuple[str, str]] = []

        if not self._is_usable(research_package):
            return self._build_failed_package(research_package, "Research package is unusable")

        strategy_agent_id = await self._resolve_strategy_agent_id()
        if not strategy_agent_id:
            return self._build_failed_package(research_package, "No active strategy agent is available")

        conversation = await self._conversation_engine.create_conversation(
            title=f"Strategy: {research_package.topic[:80]}",
            metadata={"workflow": "strategy_package"},
        )

        synthesis_prompt = (
            "Using ONLY the supplied research package, define a content strategy as strict JSON with keys: "
            "target_audience (string), positioning (string), hook (string), "
            "retention_strategy (array of strings), emotional_arc (array of strings), pacing (string). "
            "Rules: no web search, no external facts, base every recommendation strictly on the research "
            "package's findings and recommended angle. Return JSON only."
        )

        runtime_result = await self._timed_execute(
            conversation_id=conversation.context.conversation_id,
            agent_id=strategy_agent_id,
            message=synthesis_prompt,
            user_id=user_id,
            metadata={
                "workflow": "strategy_package",
                "research_package": research_package.model_dump(),
                "artifacts": [research_package.model_dump()],
                "capability_requests": [],
            },
        )

        parsed = self._extract_json_object(runtime_result.get("content", ""))
        if not parsed:
            return self._build_partial_package(research_package, "Strategy output was not valid JSON")

        return StrategyPackage(
            topic=research_package.topic,
            target_audience=str(parsed.get("target_audience", "")).strip(),
            positioning=str(parsed.get("positioning", "")).strip(),
            hook=str(parsed.get("hook", "")).strip(),
            retention_strategy=[
                str(item).strip() for item in parsed.get("retention_strategy", []) if str(item).strip()
            ],
            emotional_arc=[str(item).strip() for item in parsed.get("emotional_arc", []) if str(item).strip()],
            pacing=str(parsed.get("pacing", "")).strip(),
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

    async def _resolve_strategy_agent_id(self) -> str | None:
        for candidate in ("strategy_agent", "strategy"):
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
            if agent.slug == "strategy" or agent.name.lower() == "strategy agent":
                return agent.id
        return None

    def _is_usable(self, research_package: ResearchPackage) -> bool:
        if research_package.topic.strip():
            return True
        if research_package.findings:
            return True
        if research_package.key_facts:
            return True
        return False

    def _build_failed_package(self, research_package: ResearchPackage, reason: str) -> StrategyPackage:
        return StrategyPackage(
            topic=research_package.topic,
            target_audience="",
            positioning="",
            hook="",
            retention_strategy=[],
            emotional_arc=[],
            pacing="",
            metadata={
                "status": "failed",
                "reason": reason,
                **self._build_provider_metrics(success=False, failure_reason=reason),
            },
        )

    def _build_partial_package(self, research_package: ResearchPackage, reason: str) -> StrategyPackage:
        return StrategyPackage(
            topic=research_package.topic,
            target_audience="General audience interested in the topic",
            positioning=research_package.recommended_angle or "Informative deep-dive",
            hook=f"What if everything you thought about {research_package.topic} was only half the story?",
            retention_strategy=["Open loops", "Escalating stakes", "Payoff before the midpoint"],
            emotional_arc=["Curiosity", "Tension", "Resolution"],
            pacing="Steady build with a mid-point twist",
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
