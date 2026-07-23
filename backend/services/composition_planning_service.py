from __future__ import annotations

import logging

from backend.core.config import Settings
from backend.core.cost_tracker import CostTracker
from backend.schemas.ai_director import AIDirectorRequest
from backend.schemas.assets import ScenePlan, ScenePromptSet, VoiceAsset
from backend.schemas.composition import CompositionPlan
from backend.schemas.research import ReviewedScript
from backend.schemas.strategy import StrategyPackage
from backend.schemas.timeline import TimelinePlan
from backend.schemas.visual_identity import VisualIdentityContext
from backend.services.ai_director_plan_builder import (
    build_composition_plan,
    build_timeline_plan,
    clamp_visual_beats_per_scene,
    enforce_visual_beat_budget,
)
from backend.services.ai_director_provider import AIDirectorError, AIDirectorProvider
from backend.services.composition_planner import CompositionPlanner, DeterministicCompositionPlanner
from backend.services.composition_prompt_enricher import CompositionPromptEnricher
from backend.services.timeline_planner import DeterministicTimelinePlanner, TimelinePlanner

logger = logging.getLogger(__name__)

# Mirrors VideoAssemblyService's own fallback default (_DEFAULT_SCENE_SECONDS):
# used only when no real narration duration has been measured yet, so a
# TimelinePlan can still be produced (and later reconciled/overridden once the
# real duration is known) instead of skipping composition planning entirely.
_DEFAULT_SCENE_SECONDS = 3.0


class CompositionPlanningResult:
    """Bundle of every artifact this step produces from one pass — mirrors
    ScenePlanningResult/AudioEngineService's own bundling style."""

    def __init__(self, timeline_plan: TimelinePlan, composition_plan: CompositionPlan, scene_prompts: ScenePromptSet) -> None:
        self.timeline_plan = timeline_plan
        self.composition_plan = composition_plan
        self.scene_prompts = scene_prompts


class CompositionPlanningService:
    """Composes F27's Smart Scene Composition layer with F28's AI Director: tries
    the AI Director first (the single creative authority for TimelinePlan and
    CompositionPlan, reasoning over the whole script in one pass), and falls back
    to the original deterministic TimelinePlanner/CompositionPlanner — unchanged
    from F27 — whenever the AI Director is unavailable, disabled, or its output
    fails validation. Either way, uses the resulting CompositionPlan to enrich the
    Scene Planning step's image prompts. Mirrors AudioEngineService's
    composing-service shape and its automatic-fallback discipline."""

    def __init__(
        self,
        settings: Settings,
        timeline_planner: TimelinePlanner | None = None,
        composition_planner: CompositionPlanner | None = None,
        prompt_enricher: CompositionPromptEnricher | None = None,
        ai_director_provider: AIDirectorProvider | None = None,
        cost_tracker: CostTracker | None = None,
    ) -> None:
        self._settings = settings
        self._timeline_planner = timeline_planner or DeterministicTimelinePlanner(settings)
        self._composition_planner = composition_planner or DeterministicCompositionPlanner()
        self._prompt_enricher = prompt_enricher or CompositionPromptEnricher()
        self._ai_director_provider = ai_director_provider
        self._cost_tracker = cost_tracker or CostTracker()

    async def execute(
        self,
        *,
        scene_plan: ScenePlan,
        scene_prompts: ScenePromptSet,
        voice_asset: VoiceAsset,
        reviewed_script: ReviewedScript | None = None,
        strategy_package: StrategyPackage | None = None,
        estimated_cost_so_far_usd: float = 0.0,
        visual_identity_context: VisualIdentityContext | None = None,
        user_id: str | None = None,
    ) -> CompositionPlanningResult:
        scene_count = max(len(scene_plan.scenes), 1)
        total_duration = (
            voice_asset.duration
            if voice_asset.status == "SUCCESS" and voice_asset.duration > 0
            else _DEFAULT_SCENE_SECONDS * scene_count
        )

        timeline_plan, composition_plan = await self._plan_with_ai_director(
            scene_plan=scene_plan,
            total_duration=total_duration,
            reviewed_script=reviewed_script,
            strategy_package=strategy_package,
            estimated_cost_so_far_usd=estimated_cost_so_far_usd,
            user_id=user_id,
        )
        if timeline_plan is None or composition_plan is None:
            timeline_plan = self._timeline_planner.plan(scene_plan=scene_plan, total_duration_seconds=total_duration)
            composition_plan = self._composition_planner.plan(scene_plan=scene_plan, timeline_plan=timeline_plan)

        historical_context = visual_identity_context.historical_context if visual_identity_context is not None else None
        characters = visual_identity_context.characters if visual_identity_context is not None else None
        enriched_prompts = self._prompt_enricher.enrich(
            scene_prompts=scene_prompts,
            composition_plan=composition_plan,
            scene_plan=scene_plan,
            historical_context=historical_context,
            characters=characters,
        )

        return CompositionPlanningResult(
            timeline_plan=timeline_plan,
            composition_plan=composition_plan,
            scene_prompts=enriched_prompts,
        )

    async def _plan_with_ai_director(
        self,
        *,
        scene_plan: ScenePlan,
        total_duration: float,
        reviewed_script: ReviewedScript | None,
        strategy_package: StrategyPackage | None,
        estimated_cost_so_far_usd: float,
        user_id: str | None,
    ) -> tuple[TimelinePlan | None, CompositionPlan | None]:
        if self._ai_director_provider is None or not self._settings.ai_director_enabled or not scene_plan.scenes:
            return None, None

        # F28B Production Budget Awareness: the AI Director reasons over the same
        # dollar figures the pipeline itself will later enforce, so its own beat
        # count is already budget-aware rather than needing heavy trimming after
        # the fact. "Remaining for images" is the tighter of the whole-video
        # ceiling (minus what's already been spent) and the dedicated image budget.
        estimated_image_cost = self._cost_tracker.estimate_image_cost(
            provider="openai-image-generation",
            model=self._settings.openai_image_model,
            size=self._settings.openai_image_size,
            quality=self._settings.openai_image_quality,
        ).estimated_cost_usd
        remaining_for_images = max(
            0.0,
            min(
                self._settings.maximum_video_budget_usd - estimated_cost_so_far_usd,
                self._settings.maximum_image_budget_usd,
            ),
        )

        request = AIDirectorRequest(
            topic=scene_plan.topic,
            genre=self._settings.ai_director_genre,
            narration_script=reviewed_script.revised_script if reviewed_script is not None else "",
            scenes=scene_plan.scenes,
            total_duration_seconds=total_duration,
            target_audience=strategy_package.target_audience if strategy_package is not None else "",
            positioning=strategy_package.positioning if strategy_package is not None else "",
            pacing_guidance=strategy_package.pacing if strategy_package is not None else "",
            emotional_arc=strategy_package.emotional_arc if strategy_package is not None else [],
            maximum_production_budget_usd=self._settings.maximum_video_budget_usd,
            target_production_budget_usd=self._settings.target_video_budget_usd,
            estimated_cost_so_far_usd=estimated_cost_so_far_usd,
            remaining_budget_usd=remaining_for_images,
            estimated_image_cost_usd=estimated_image_cost,
            minimum_visual_beats_per_scene=self._settings.minimum_visual_beats_per_scene,
            target_visual_beats_per_scene=self._settings.target_visual_beats_per_scene,
            maximum_visual_beats_per_scene=self._settings.maximum_visual_beats_per_scene,
        )

        try:
            ai_plan = await self._ai_director_provider.direct(request=request, user_id=user_id)
            timeline_plan = build_timeline_plan(ai_plan, scene_plan=scene_plan, total_duration_seconds=total_duration)
            composition_plan = build_composition_plan(ai_plan, timeline_plan=timeline_plan, topic=scene_plan.topic)
        except AIDirectorError as exc:
            logger.warning("ai_director_fallback_to_deterministic_planning", extra={"reason": str(exc)})
            return None, None

        # Cost Validation (F28B): clamp per-scene beat count to the configured
        # ceiling first (a hard safety rule, independent of budget), then trim
        # further if the resulting plan still projects over the remaining image
        # budget — "optimize the plan before image generation starts", never
        # exceeding configured production limits.
        composition_plan = clamp_visual_beats_per_scene(
            composition_plan, maximum_per_scene=self._settings.maximum_visual_beats_per_scene
        )
        if estimated_image_cost > 0:
            max_total_images = max(len(composition_plan.scenes), int(remaining_for_images // estimated_image_cost))
            composition_plan = enforce_visual_beat_budget(composition_plan, max_total_images=max_total_images)

        return timeline_plan, composition_plan
