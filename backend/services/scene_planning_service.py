from __future__ import annotations

import json
import logging
import time
from typing import Any

from backend.core.agent_runtime import AgentRuntime
from backend.core.config import Settings
from backend.core.conversation_engine import ConversationEngine
from backend.core.cost_tracker import CostTracker
from backend.schemas.assets import BrollPlan, BrollSegment, MusicPlan, Scene, ScenePlan, ScenePrompt, ScenePromptSet
from backend.schemas.media import MediaPackage
from backend.schemas.research import ReviewedScript
from backend.services.agent_service import AgentService

logger = logging.getLogger(__name__)


class ScenePlanningResult:
    """Bundle of every artifact this service produces from one LLM call plus the
    already-generated media package — avoids duplicate provider calls."""

    def __init__(self, scene_plan: ScenePlan, scene_prompts: ScenePromptSet, broll_plan: BrollPlan, music_plan: MusicPlan) -> None:
        self.scene_plan = scene_plan
        self.scene_prompts = scene_prompts
        self.broll_plan = broll_plan
        self.music_plan = music_plan


class ScenePlanningService:
    """Breaks a reviewed script into a scene-by-scene production plan, per-scene image
    prompts, a B-roll plan, and music direction. Reuses the Media step's output for
    B-roll/music instead of making additional LLM calls."""

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
    ) -> ScenePlanningResult:
        self._call_durations_ms: list[float] = []
        self._call_texts: list[tuple[str, str]] = []

        broll_plan = self._build_broll_plan(reviewed_script.topic, media_package.b_roll_prompts)
        music_plan = self._build_music_plan(media_package.music_direction)

        if not reviewed_script.revised_script.strip():
            failed_plan = self._build_failed_scene_plan(reviewed_script.topic, "Reviewed script is unusable")
            failed_prompts = self._build_failed_scene_prompts(reviewed_script.topic, "Reviewed script is unusable")
            return ScenePlanningResult(failed_plan, failed_prompts, broll_plan, music_plan)

        scene_agent_id = await self._resolve_agent_id(("media_agent", "media"), {"media"})
        if not scene_agent_id:
            failed_plan = self._build_failed_scene_plan(reviewed_script.topic, "No active scene planning agent is available")
            failed_prompts = self._build_failed_scene_prompts(
                reviewed_script.topic, "No active scene planning agent is available"
            )
            return ScenePlanningResult(failed_plan, failed_prompts, broll_plan, music_plan)

        conversation = await self._conversation_engine.create_conversation(
            title=f"Scene Planning: {reviewed_script.topic[:80]}",
            metadata={"workflow": "scene_planning"},
        )

        # The number of scenes the LLM returns maps 1:1 to paid gpt-image-1 calls
        # downstream (one image per scene, see SceneImageGenerationService). The
        # LLM must never be able to set that count itself — the app dictates an
        # exact, fixed scene count so per-video image cost stays predictable.
        max_scenes = self._settings.max_scenes_per_video
        prompt = (
            "Using ONLY the reviewed script, break it into a scene-by-scene production plan. "
            f"Return EXACTLY {max_scenes} scenes — no more, no less. Group the script's "
            f"narrative beats into exactly {max_scenes} scenes regardless of how many beats "
            "it naturally has. "
            f"Produce strict JSON with a top-level 'scenes' key: an array of EXACTLY "
            f"{max_scenes} objects, each with keys: scene_number (int, 1-based, 1 through "
            f"{max_scenes}), start_time (string mm:ss), "
            "end_time (string mm:ss), narration (string, verbatim excerpt from the script), "
            "camera (string), lens (string), lighting (string), environment (string), "
            "animation (string), composition (string), visual_prompt (string, a detailed "
            "image-generation prompt for this scene), negative_prompt (string), style (string), "
            "aspect_ratio (string, e.g. 16:9), mood (string). Include a top-level 'status' key. "
            "Return JSON only."
        )

        result = await self._timed_execute(
            conversation_id=conversation.context.conversation_id,
            agent_id=scene_agent_id,
            message=prompt,
            user_id=user_id,
            metadata={
                "workflow": "scene_planning",
                "reviewed_script": reviewed_script.model_dump(),
                "artifacts": [reviewed_script.model_dump()],
                "capability_requests": [],
            },
        )

        parsed = self._extract_json_object(result.get("content", ""))
        if not parsed or not isinstance(parsed.get("scenes"), list):
            reason = "Scene planning output was not valid JSON"
            failed_plan = self._build_failed_scene_plan(reviewed_script.topic, reason)
            failed_prompts = self._build_failed_scene_prompts(reviewed_script.topic, reason)
            return ScenePlanningResult(failed_plan, failed_prompts, broll_plan, music_plan)

        # Cost protection: the prompt above asks for exactly `max_scenes`, but nothing
        # stops the LLM from ignoring that instruction. Enforce the ceiling here too —
        # every scene that survives this step becomes one paid gpt-image-1 call later,
        # so the app (not the model's output) must have the final say on the count.
        # Fewer than max_scenes is fine and passes through unchanged.
        raw_scenes = parsed["scenes"]
        if len(raw_scenes) > max_scenes:
            logger.warning(
                "LLM returned %d scenes. Maximum allowed: %d. Using first %d scenes.",
                len(raw_scenes),
                max_scenes,
                max_scenes,
                extra={
                    "topic": reviewed_script.topic,
                    "llm_scene_count": len(raw_scenes),
                    "max_scenes_per_video": max_scenes,
                },
            )
            raw_scenes = raw_scenes[:max_scenes]

        scenes: list[Scene] = []
        scene_prompts: list[ScenePrompt] = []
        for index, raw in enumerate(raw_scenes, start=1):
            if not isinstance(raw, dict):
                continue
            scene_number = int(raw.get("scene_number") or index)
            scenes.append(
                Scene(
                    scene_number=scene_number,
                    start_time=str(raw.get("start_time", "")).strip(),
                    end_time=str(raw.get("end_time", "")).strip(),
                    narration=str(raw.get("narration", "")).strip(),
                    camera=str(raw.get("camera", "")).strip(),
                    lens=str(raw.get("lens", "")).strip(),
                    lighting=str(raw.get("lighting", "")).strip(),
                    environment=str(raw.get("environment", "")).strip(),
                    animation=str(raw.get("animation", "")).strip(),
                    composition=str(raw.get("composition", "")).strip(),
                    visual_prompt=str(raw.get("visual_prompt", "")).strip(),
                )
            )
            scene_prompts.append(
                ScenePrompt(
                    scene_number=scene_number,
                    prompt=str(raw.get("visual_prompt", "")).strip(),
                    negative_prompt=str(raw.get("negative_prompt", "")).strip(),
                    style=str(raw.get("style", "")).strip(),
                    aspect_ratio=str(raw.get("aspect_ratio", "")).strip(),
                    camera=str(raw.get("camera", "")).strip(),
                    mood=str(raw.get("mood", "")).strip(),
                )
            )

        status = "success" if scenes else "partial"
        provider_metrics = self._build_provider_metrics(success=bool(scenes))
        scene_plan = ScenePlan(
            topic=reviewed_script.topic,
            scenes=scenes,
            metadata={
                "status": status,
                "conversation_id": conversation.context.conversation_id,
                **provider_metrics,
            },
        )
        scene_prompt_set = ScenePromptSet(
            topic=reviewed_script.topic,
            prompts=scene_prompts,
            metadata={
                "status": status,
                "conversation_id": conversation.context.conversation_id,
                **provider_metrics,
            },
        )
        return ScenePlanningResult(scene_plan, scene_prompt_set, broll_plan, music_plan)

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

    def _build_broll_plan(self, topic: str, b_roll_prompts: list[str]) -> BrollPlan:
        segments = [
            BrollSegment(narration_range=f"segment-{index}", footage_description=footage)
            for index, footage in enumerate(b_roll_prompts, start=1)
        ]
        status = "success" if segments else "skipped"
        return BrollPlan(topic=topic, segments=segments, metadata={"status": status})

    def _build_music_plan(self, music_direction: str) -> MusicPlan:
        direction = music_direction.strip()
        if not direction:
            return MusicPlan(metadata={"status": "skipped", "reason": "No music direction available"})
        return MusicPlan(reference=direction, metadata={"status": "success"})

    def _build_failed_scene_plan(self, topic: str, reason: str) -> ScenePlan:
        return ScenePlan(
            topic=topic,
            scenes=[],
            metadata={
                "status": "failed",
                "reason": reason,
                **self._build_provider_metrics(success=False, failure_reason=reason),
            },
        )

    def _build_failed_scene_prompts(self, topic: str, reason: str) -> ScenePromptSet:
        return ScenePromptSet(
            topic=topic,
            prompts=[],
            metadata={
                "status": "failed",
                "reason": reason,
                **self._build_provider_metrics(success=False, failure_reason=reason),
            },
        )

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
