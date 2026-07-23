from __future__ import annotations

import json
import time
from typing import Any, Literal

from backend.core.agent_runtime import AgentRuntime
from backend.core.config import Settings
from backend.core.conversation_engine import ConversationEngine
from backend.core.cost_tracker import CostTracker
from backend.schemas.research import ResearchPackage, ScriptDraft
from backend.schemas.strategy import StrategyPackage
from backend.services.agent_service import AgentService


_DURATION_LABELS: dict[str, str] = {
    "short": "3-5 min",
    "standard": "6-10 min",
    "long": "10-20 min",
}


class WriterWorkflowService:
    """Transforms a research package into a YouTube-ready script draft."""

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
        research_package: ResearchPackage,
        duration_profile: Literal["short", "standard", "long"],
        user_id: str | None,
        strategy_package: StrategyPackage | None = None,
    ) -> ScriptDraft:
        self._call_durations_ms: list[float] = []
        self._call_texts: list[tuple[str, str]] = []

        if not self._is_usable(research_package):
            return self._build_failed_draft(research_package, "Research package is unusable")

        writer_agent_id = await self._resolve_writer_agent_id()
        if not writer_agent_id:
            return self._build_failed_draft(research_package, "No active writer-capable agent is available")

        conversation = await self._conversation_engine.create_conversation(
            title=f"Script Draft: {research_package.topic[:80]}",
            metadata={"workflow": "script_draft"},
        )

        duration_label = _DURATION_LABELS[duration_profile]
        strategy_guidance = ""
        if strategy_package is not None:
            strategy_guidance = (
                "\n\nFollow this content strategy: "
                f"target audience: {strategy_package.target_audience}; "
                f"positioning: {strategy_package.positioning}; "
                f"suggested hook direction: {strategy_package.hook}; "
                f"retention tactics: {', '.join(strategy_package.retention_strategy)}; "
                f"emotional arc: {', '.join(strategy_package.emotional_arc)}; "
                f"pacing: {strategy_package.pacing}."
            )
        synthesis_prompt = (
            "Using ONLY the supplied research package, write a YouTube script as strict JSON with keys: "
            "hook (string), intro (string), sections (array of strings), outro (string), "
            "call_to_action (string), narration_script (string), scene_markers (array of strings). "
            "Rules: no web search, no URL reading, no external facts, no unsupported claims, "
            "avoid filler/repetition, smooth transitions, conversational English, voice-over ready. "
            "Structure: Hook -> Introduction -> Main Story -> Interesting Facts -> Conclusion -> Call To Action. "
            f"Duration target: {duration_label}. Return JSON only.{strategy_guidance}"
        )

        metadata: dict[str, Any] = {
            "workflow": "script_draft",
            "research_package": research_package.model_dump(),
            "documents": self._to_documents(research_package),
            "artifacts": [research_package.model_dump()],
            "capability_requests": [],
        }
        if strategy_package is not None:
            metadata["strategy_package"] = strategy_package.model_dump()
            metadata["artifacts"].append(strategy_package.model_dump())

        runtime_result = await self._timed_execute(
            conversation_id=conversation.context.conversation_id,
            agent_id=writer_agent_id,
            message=synthesis_prompt,
            user_id=user_id,
            metadata=metadata,
        )

        parsed = self._extract_json_object(runtime_result.get("content", ""))
        if not parsed:
            return self._build_partial_draft(
                research_package=research_package,
                duration_profile=duration_profile,
                reason="Writer output was not valid JSON",
            )

        draft = ScriptDraft(
            topic=research_package.topic,
            hook=str(parsed.get("hook", "")).strip(),
            intro=str(parsed.get("intro", "")).strip(),
            sections=[str(section).strip() for section in parsed.get("sections", []) if str(section).strip()],
            outro=str(parsed.get("outro", "")).strip(),
            call_to_action=str(parsed.get("call_to_action", "")).strip(),
            estimated_duration=duration_label,
            narration_script=str(parsed.get("narration_script", "")).strip(),
            scene_markers=[
                str(marker).strip() for marker in parsed.get("scene_markers", []) if str(marker).strip()
            ],
            references=research_package.sources,
            metadata={
                "status": "success",
                "duration_profile": duration_profile,
                "conversation_id": conversation.context.conversation_id,
                **self._build_provider_metrics(success=True),
            },
        )

        if self._is_incomplete_input(research_package) or not self._is_complete_output(draft):
            draft.metadata["status"] = "partial"
            draft.metadata["reason"] = "Input package was incomplete or output required fallback"

        if not draft.narration_script:
            draft.narration_script = self._build_narration_script(draft)
        if not draft.scene_markers:
            draft.scene_markers = self._build_scene_markers(duration_profile)

        return draft

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

    async def _resolve_writer_agent_id(self) -> str | None:
        for candidate in ("writer_agent", "writer", "creation"):
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
            if agent.slug in {"writer", "creation"}:
                return agent.id
            if agent.name.lower() in {"writer agent", "creation agent"}:
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

    def _is_incomplete_input(self, research_package: ResearchPackage) -> bool:
        if not research_package.findings:
            return True
        if not research_package.key_facts:
            return True
        if not research_package.executive_summary.strip():
            return True
        return False

    def _is_complete_output(self, draft: ScriptDraft) -> bool:
        return bool(
            draft.hook.strip()
            and draft.intro.strip()
            and draft.sections
            and draft.outro.strip()
            and draft.call_to_action.strip()
        )

    def _build_failed_draft(self, research_package: ResearchPackage, reason: str) -> ScriptDraft:
        return ScriptDraft(
            topic=research_package.topic,
            hook="",
            intro="",
            sections=[],
            outro="",
            call_to_action="",
            estimated_duration=_DURATION_LABELS["standard"],
            narration_script="",
            scene_markers=[],
            references=research_package.sources,
            metadata={
                "status": "failed",
                "reason": reason,
                **self._build_provider_metrics(success=False, failure_reason=reason),
            },
        )

    def _build_partial_draft(
        self,
        research_package: ResearchPackage,
        duration_profile: Literal["short", "standard", "long"],
        reason: str,
    ) -> ScriptDraft:
        fallback_sections = [finding.details for finding in research_package.findings if finding.details.strip()][:4]
        if not fallback_sections:
            fallback_sections = [fact for fact in research_package.key_facts if fact.strip()][:4]

        draft = ScriptDraft(
            topic=research_package.topic,
            hook=f"What if everything you thought about {research_package.topic} was only half the story?",
            intro=research_package.executive_summary or f"Today we break down {research_package.topic}.",
            sections=fallback_sections,
            outro="That is the core story, and now you have the context to evaluate what comes next.",
            call_to_action="If you found this useful, like this video and subscribe for deeper breakdowns.",
            estimated_duration=_DURATION_LABELS[duration_profile],
            narration_script="",
            scene_markers=self._build_scene_markers(duration_profile),
            references=research_package.sources,
            metadata={
                "status": "partial",
                "reason": reason,
                **self._build_provider_metrics(success=False, failure_reason=reason),
            },
        )
        draft.narration_script = self._build_narration_script(draft)
        return draft

    def _to_documents(self, research_package: ResearchPackage) -> list[dict[str, Any]]:
        docs: list[dict[str, Any]] = []
        for source in research_package.sources:
            docs.append(
                {
                    "title": source.title or source.url,
                    "content": source.snippet or "",
                    "url": source.url,
                }
            )
        return docs

    def _build_narration_script(self, draft: ScriptDraft) -> str:
        parts = [draft.hook, draft.intro, *draft.sections, draft.outro, draft.call_to_action]
        return "\n\n".join(part for part in parts if part.strip())

    def _build_scene_markers(self, duration_profile: Literal["short", "standard", "long"]) -> list[str]:
        if duration_profile == "short":
            return ["00:00 Hook", "00:25 Background", "01:40 Main Story", "03:30 Conclusion"]
        if duration_profile == "long":
            return [
                "00:00 Hook",
                "00:40 Background",
                "03:00 Main Story",
                "08:30 Interesting Facts",
                "13:30 Conclusion",
            ]
        return [
            "00:00 Hook",
            "00:30 Background",
            "02:20 Main Story",
            "05:30 Interesting Facts",
            "08:20 Conclusion",
        ]

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
