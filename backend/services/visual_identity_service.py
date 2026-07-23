from __future__ import annotations

import json
import time
from typing import Any

from backend.core.agent_runtime import AgentRuntime
from backend.core.config import Settings
from backend.core.conversation_engine import ConversationEngine
from backend.core.cost_tracker import CostTracker
from backend.schemas.research import ReviewedScript
from backend.schemas.research import ResearchPackage
from backend.schemas.visual_identity import CharacterVisualIdentity, HistoricalVisualContext, VisualIdentityContext
from backend.services.agent_service import AgentService


class VisualIdentityService:
    """F31 Historical Visual Consistency + Character Consistency: one LLM call over
    the finalized research/script that produces the single HistoricalVisualContext
    (architecture, materials, clothing, geography, etc.) and the canonical
    CharacterVisualIdentity for every recurring named figure worth keeping visually
    consistent — reused by every later prompt in the production instead of each
    scene/beat reinventing the setting and its people from scratch. Runs once per
    production, mirroring MediaWorkflowService/ScenePlanningService's shape. Never
    raises — any failure (disabled, no agent, bad JSON) returns an empty context,
    which every downstream consumer (CompositionPromptEnricher,
    ThumbnailGenerationService) already treats as 'no visual identity guidance',
    identical to pre-F31 behavior."""

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
        *,
        research_package: ResearchPackage,
        reviewed_script: ReviewedScript,
        user_id: str | None,
    ) -> VisualIdentityContext:
        self._call_durations_ms: list[float] = []
        self._call_texts: list[tuple[str, str]] = []

        if not self._settings.visual_identity_enabled:
            return self._empty(research_package.topic, "Visual Identity is disabled by settings")

        if not reviewed_script.revised_script.strip():
            return self._empty(research_package.topic, "Reviewed script is unusable")

        agent_id = await self._resolve_agent_id(("media_agent", "media"), {"media"})
        if not agent_id:
            return self._empty(research_package.topic, "No active visual identity agent is available")

        conversation = await self._conversation_engine.create_conversation(
            title=f"Visual Identity: {research_package.topic[:80]}",
            metadata={"workflow": "visual_identity"},
        )

        max_characters = max(0, self._settings.max_characters_per_video)
        prompt = (
            "You are a documentary art director building a visual continuity bible for one "
            "production, from the finalized research and narration script below. Produce strict "
            "JSON with two top-level keys.\n\n"
            "1) 'historical_context': ONE object describing the shared visual setting every scene "
            "must stay consistent with, keys: time_period, geography, architecture, materials, "
            "clothing, weapons_and_tools, symbols_and_landmarks, vegetation, weather_and_atmosphere, "
            "culture_notes, color_palette (all strings; leave a key as an empty string if the "
            "research gives no basis for it — never invent unsupported specifics).\n\n"
            "2) 'characters': an array of AT MOST "
            f"{max_characters} objects, one per recurring NAMED human figure that appears more than "
            "once in the narration and would benefit from staying visually recognizable across "
            "scenes (skip minor or single-mention figures). Each object: name, aliases (array of "
            "other names/titles this figure is called in the script), role, face_description, hair, "
            "skin_tone, clothing, accessories, body_build, age_appearance, distinguishing_features "
            "(all strings, grounded only in what the research/script supports or what is a "
            "reasonable period-accurate inference — never fabricate ethnicity/appearance details "
            "the source material contradicts).\n\n"
            "Also include a top-level 'status' key. Return JSON only, no prose, no markdown fences.\n\n"
            f"Research key facts:\n{chr(10).join(f'- {fact}' for fact in research_package.key_facts) or '(none)'}\n\n"
            f"Narration script:\n{reviewed_script.revised_script}"
        )

        result = await self._timed_execute(
            conversation_id=conversation.context.conversation_id,
            agent_id=agent_id,
            message=prompt,
            user_id=user_id,
            metadata={
                "workflow": "visual_identity",
                "reviewed_script": reviewed_script.model_dump(),
                "artifacts": [reviewed_script.model_dump()],
                "capability_requests": [],
            },
        )

        parsed = self._extract_json_object(result.get("content", ""))
        if not parsed:
            return self._empty(research_package.topic, "Visual Identity output was not valid JSON")

        historical_context = self._parse_historical_context(parsed.get("historical_context"))
        characters = self._parse_characters(parsed.get("characters"))[:max_characters]

        return VisualIdentityContext(
            topic=research_package.topic,
            historical_context=historical_context,
            characters=characters,
            metadata={
                "status": "success",
                "conversation_id": conversation.context.conversation_id,
                "character_count": len(characters),
                **self._build_provider_metrics(success=True),
            },
        )

    def _parse_historical_context(self, raw: Any) -> HistoricalVisualContext:
        if not isinstance(raw, dict):
            return HistoricalVisualContext()
        fields = HistoricalVisualContext.model_fields.keys()
        return HistoricalVisualContext(**{key: str(raw.get(key, "")).strip() for key in fields})

    def _parse_characters(self, raw: Any) -> list[CharacterVisualIdentity]:
        if not isinstance(raw, list):
            return []
        characters: list[CharacterVisualIdentity] = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", "")).strip()
            if not name:
                continue
            aliases = [str(alias).strip() for alias in item.get("aliases", []) if str(alias).strip()]
            characters.append(
                CharacterVisualIdentity(
                    name=name,
                    aliases=aliases,
                    role=str(item.get("role", "")).strip(),
                    face_description=str(item.get("face_description", "")).strip(),
                    hair=str(item.get("hair", "")).strip(),
                    skin_tone=str(item.get("skin_tone", "")).strip(),
                    clothing=str(item.get("clothing", "")).strip(),
                    accessories=str(item.get("accessories", "")).strip(),
                    body_build=str(item.get("body_build", "")).strip(),
                    age_appearance=str(item.get("age_appearance", "")).strip(),
                    distinguishing_features=str(item.get("distinguishing_features", "")).strip(),
                )
            )
        return characters

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

    def _empty(self, topic: str, reason: str) -> VisualIdentityContext:
        return VisualIdentityContext(
            topic=topic,
            historical_context=HistoricalVisualContext(),
            characters=[],
            metadata={
                "status": "skipped",
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
