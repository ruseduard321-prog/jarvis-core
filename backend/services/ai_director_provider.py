from __future__ import annotations

import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Any

from pydantic import ValidationError

from backend.core.agent_runtime import AgentRuntime
from backend.core.config import Settings
from backend.core.conversation_engine import ConversationEngine
from backend.core.cost_tracker import CostTracker
from backend.schemas.ai_director import AIDirectorPlan, AIDirectorRequest
from backend.services.agent_service import AgentService

logger = logging.getLogger(__name__)


class AIDirectorError(Exception):
    """Base error for any AI Director failure. Callers (CompositionPlanningService)
    catch this broadly and fall back to deterministic planning — the pipeline must
    always remain able to produce a complete video."""


class AIDirectorUnavailableError(AIDirectorError):
    """No director agent could be resolved, or the underlying LLM call failed."""


class AIDirectorValidationError(AIDirectorError):
    """The AI Director responded, but its output was not valid/usable structured
    data (bad JSON, wrong shape, invalid enum values, or a structural problem
    caught by ai_director_plan_builder.py)."""


class AIDirectorProvider(ABC):
    """Dedicated abstraction hiding the AI Director's provider-specific
    implementation. The rest of the pipeline depends only on this interface and on
    AIDirectorPlan — a future provider (a different model, a different agent, a
    non-agent-based call) is a new implementation of this ABC, with zero changes
    to CompositionPlanningService or anything downstream."""

    @abstractmethod
    async def direct(self, *, request: AIDirectorRequest, user_id: str | None) -> AIDirectorPlan:
        """Reasons over the entire production in one pass and returns the raw,
        structured AIDirectorPlan. Raises AIDirectorError (never returns partial/
        best-effort data) on any failure — callers must fall back wholesale."""


class AgentRuntimeAIDirectorProvider(AIDirectorProvider):
    """Concrete implementation reusing this codebase's existing agent execution
    path (ConversationEngine + AgentRuntime + AgentService) — the same plumbing
    ScenePlanningService already uses for structured-JSON planning calls. This is
    a genuine reuse of existing architecture, not a new LLM-calling mechanism."""

    _AGENT_CANDIDATES = ("creation_agent", "creation")
    _AGENT_FALLBACK_SLUGS = {"creation", "media"}

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

    async def direct(self, *, request: AIDirectorRequest, user_id: str | None) -> AIDirectorPlan:
        agent_id = await self._resolve_agent_id()
        if not agent_id:
            raise AIDirectorUnavailableError("No active AI Director agent is available")

        conversation = await self._conversation_engine.create_conversation(
            title=f"AI Director: {request.topic[:80]}",
            metadata={"workflow": "ai_director"},
        )

        prompt = self._build_prompt(request)
        started_at = time.perf_counter()
        try:
            result = await self._agent_runtime.execute(
                conversation_id=conversation.context.conversation_id,
                agent_id=agent_id,
                message=prompt,
                user_id=user_id,
                metadata={"workflow": "ai_director", "capability_requests": []},
            )
        except Exception as exc:
            raise AIDirectorUnavailableError(f"AI Director agent execution failed: {exc}") from exc
        duration_ms = (time.perf_counter() - started_at) * 1000

        content = str(result.get("content", ""))
        self._cost_tracker.estimate_text_cost(
            provider="openai", model=self._settings.default_llm_model, input_text=prompt, output_text=content
        )
        logger.info(
            "ai_director_call_completed",
            extra={"topic": request.topic, "duration_ms": round(duration_ms, 2)},
        )

        parsed = self._extract_json_object(content)
        if parsed is None:
            raise AIDirectorValidationError("AI Director output was not valid JSON")

        try:
            return AIDirectorPlan.model_validate(parsed)
        except ValidationError as exc:
            raise AIDirectorValidationError(f"AI Director output did not match the expected schema: {exc}") from exc

    def _build_prompt(self, request: AIDirectorRequest) -> str:
        scenes_json = json.dumps(
            [
                {
                    "scene_number": scene.scene_number,
                    "narration": scene.narration,
                    "camera": scene.camera,
                    "lighting": scene.lighting,
                    "environment": scene.environment,
                    "composition": scene.composition,
                }
                for scene in request.scenes
            ]
        )
        return (
            "You are the sole creative director for this video production. Read the "
            "complete narration script and the per-scene breakdown below, then produce "
            "ONE cohesive creative plan for the ENTIRE production. Reason about "
            "introduction, setup, escalation, climax, resolution, and emotional "
            "progression across all scenes together — never plan a scene in isolation.\n\n"
            f"Genre: {request.genre}\n"
            f"Topic: {request.topic}\n"
            f"Target audience: {request.target_audience or 'general'}\n"
            f"Positioning: {request.positioning or 'n/a'}\n"
            f"Pacing guidance: {request.pacing_guidance or 'n/a'}\n"
            f"Emotional arc beats: {', '.join(request.emotional_arc) or 'n/a'}\n\n"
            f"Full narration script:\n{request.narration_script}\n\n"
            "Per-scene breakdown (you MUST preserve this exact scene count and every "
            f"scene_number, unchanged):\n{scenes_json}\n\n"
            f"Total measured narration duration in seconds: {request.total_duration_seconds}\n\n"
            "PRODUCTION BUDGET (you must reason about this — do not exceed it):\n"
            f"Maximum production budget: ${request.maximum_production_budget_usd:.2f}\n"
            f"Target production budget: ${request.target_production_budget_usd:.2f}\n"
            f"Estimated cost already committed: ${request.estimated_cost_so_far_usd:.2f}\n"
            f"Remaining budget available for scene images: ${request.remaining_budget_usd:.2f}\n"
            f"Estimated cost per generated image: ${request.estimated_image_cost_usd:.4f}\n\n"
            "VISUAL STORYTELLING — VISUAL BEATS:\n"
            "Beyond the scene-level direction above, decide the internal visual structure "
            "of every scene: its 'visual_beats'. A visual beat is ONE meaningful visual "
            "event within a scene (a different action, subject, location, emotion, "
            "perspective, reveal, or cinematic framing) and generates exactly one image. "
            "Visual beats describe visual storytelling only — they never change scene "
            "duration, narration duration, or pacing; a scene's fixed screen time is "
            "simply divided evenly across however many beats you give it. Decide the "
            "number of beats per scene from narrative importance, emotional progression, "
            "visual complexity, and dramatic impact — NOT from a fixed rule. A short, "
            "important reveal may deserve several beats; a long, simple explanation may "
            "need only one. Every beat's description must represent a real visual change "
            "from the others in the same scene — never near-duplicate prompts. Prioritize "
            "quality over quantity, and stay within the remaining budget above: "
            f"configured guidance is a minimum of {request.minimum_visual_beats_per_scene} "
            f"(floor, not forced), a comfortable target of "
            f"{request.target_visual_beats_per_scene}, and a hard maximum of "
            f"{request.maximum_visual_beats_per_scene} beats per scene. If in doubt, use "
            "fewer, higher-impact beats rather than more. Give every beat a "
            "beat_importance (low/normal/high/critical) — its narrative weight, NOT its "
            "duration: the scene's fixed screen time is then divided across its beats in "
            "proportion to this importance (a critical beat is held longer than a low one), "
            "so a scene where every beat is 'normal' still splits evenly.\n\n"
            "VIEWER RETENTION ENGINE (F29):\n"
            "You are also optimizing HOW this same story is delivered for attention, "
            "pacing, curiosity, and emotional rhythm — never inventing a different story. "
            "For every scene, additionally return a 'retention' object reasoning about: "
            "retention_priority (low/normal/high/critical — this scene's importance for "
            "holding the viewer), curiosity_level (0.0-1.0 — how much open curiosity/"
            "unanswered question this scene creates; classify each scene's role in the "
            "curiosity loop — question, mystery, discovery, explanation, reveal, or "
            "resolution — and pace it accordingly: build curiosity fast, reveal it slowly), "
            "emotional_intensity (0.0-1.0 — this scene's position on the whole production's "
            "emotional curve; avoid a flat progression, build small peaks, medium peaks, one "
            "major reveal, then resolution), information_density (low/medium/high — dense "
            "scenes should get more visual support and shorter visual persistence via more/"
            "higher-importance beats, without changing the narration), visual_change_frequency "
            "(0.0-1.0 — how often visuals should change here; raise it for long explanatory "
            "scenes to avoid a static period, keep it lower for scenes that need to breathe), "
            "reveal_strength (0.0-1.0 — how much this scene pays off an earlier curiosity loop; "
            "0 for scenes that only build tension), and transition_energy (seamless/energetic/"
            "suspense/calm/dramatic/emotional — the feel of the cut INTO this scene). Also "
            "actively avoid repetitive imagery: vary framing, subject, and composition across "
            "consecutive beats/scenes rather than repeating the same visual idea. Stronger "
            "openings and stronger endings matter — the first and last scenes deserve your "
            "highest retention_priority and most deliberate transition_energy choices.\n\n"
            "Return strict JSON with a top-level 'scenes' key: an array with EXACTLY one "
            f"entry per scene_number from 1 to {len(request.scenes)} (every scene_number "
            "must appear exactly once), each with keys: scene_number (int), "
            "duration_seconds (float — your intended RELATIVE screen time; it will be "
            "rescaled to the exact measured total, so express relative emphasis, not an "
            "absolute budget), pacing (one of: fast, standard, slow, dramatic_pause, "
            "climax, breathing), purpose (one of: introduction, context, discovery, "
            "conflict, escalation, reveal, resolution), composition_style (one of: "
            "establishing_shot, wide_shot, close_up, detail_shot, reveal_shot, "
            "comparison_shot, reaction_shot, transition_shot), camera_intent (one of: "
            "slow_reveal, dramatic_zoom, investigation, suspense, emotional_focus, "
            "neutral_observation), color_language (one of: neutral, warm_progression, "
            "cold_progression, tension), continuity_tags (array of short strings naming "
            "recurring visual elements active in this scene), relationships (array of "
            "objects: relation_type [continuation|contrast|callback|escalation|"
            "repetition], reference_scene_number [int, an EARLIER scene_number], note "
            "[short string]), emphasis_note (short string explaining your directorial "
            "rationale for this scene), visual_beats (array of objects: beat_number "
            "[1-based int], description [vivid, concrete visual description driving this "
            "beat's own image prompt], emphasis_note [short string, optional], "
            "beat_importance [one of: low, normal, high, critical — optional, defaults to "
            "normal]), retention (optional object: retention_priority [low|normal|high|"
            "critical], curiosity_level [0.0-1.0], emotional_intensity [0.0-1.0], "
            "information_density [low|medium|high], visual_change_frequency [0.0-1.0], "
            "reveal_strength [0.0-1.0], transition_energy [seamless|energetic|suspense|calm|"
            "dramatic|emotional]). Also include a top-level 'motifs' key: an array of objects (motif_type "
            "[object|location|atmosphere], description, established_scene_number, "
            "recurring_scene_numbers [array of ints]) for any recurring visual thread you "
            "intend to carry across scenes. Return JSON only, no prose, no markdown "
            "fences."
        )

    async def _resolve_agent_id(self) -> str | None:
        for candidate in self._AGENT_CANDIDATES:
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
            if agent.slug in self._AGENT_FALLBACK_SLUGS:
                return agent.id
        return None

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
