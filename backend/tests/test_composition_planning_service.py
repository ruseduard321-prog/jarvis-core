from __future__ import annotations

import pytest

from backend.core.config import Settings
from backend.schemas.ai_director import AIDirectorPlan, AIDirectorSceneDirection
from backend.schemas.assets import Scene, ScenePlan, ScenePrompt, ScenePromptSet, VoiceAsset
from backend.schemas.composition import CameraIntent, CompositionStyle, ScenePurpose, VisualBeat
from backend.schemas.research import ReviewedScript
from backend.schemas.strategy import StrategyPackage
from backend.schemas.timeline import ScenePacing
from backend.schemas.visual_identity import CharacterVisualIdentity, HistoricalVisualContext, VisualIdentityContext
from backend.services.ai_director_provider import AIDirectorUnavailableError
from backend.services.composition_planning_service import CompositionPlanningService


def _voice_asset(status: str = "SUCCESS", duration: float = 24.0) -> VoiceAsset:
    return VoiceAsset(provider="fake-tts", generation_time="2026-01-01T00:00:00Z", status=status, duration=duration)


def _scene_plan(count: int) -> ScenePlan:
    return ScenePlan(topic="Test", scenes=[Scene(scene_number=i) for i in range(1, count + 1)])


def _scene_prompts(count: int) -> ScenePromptSet:
    return ScenePromptSet(
        topic="Test", prompts=[ScenePrompt(scene_number=i, prompt=f"prompt {i}") for i in range(1, count + 1)]
    )


def _ai_plan(count: int) -> AIDirectorPlan:
    return AIDirectorPlan(
        scenes=[
            AIDirectorSceneDirection(
                scene_number=i,
                duration_seconds=1.0,
                pacing=ScenePacing.STANDARD,
                purpose=ScenePurpose.INTRODUCTION if i == 1 else ScenePurpose.DISCOVERY,
                composition_style=CompositionStyle.WIDE_SHOT,
                camera_intent=CameraIntent.NEUTRAL_OBSERVATION,
            )
            for i in range(1, count + 1)
        ]
    )


class FakeAIDirectorProvider:
    def __init__(self, plan: AIDirectorPlan | None = None, raises: Exception | None = None):
        self._plan = plan
        self._raises = raises
        self.called_with: dict | None = None

    async def direct(self, *, request, user_id):
        self.called_with = {"request": request, "user_id": user_id}
        if self._raises:
            raise self._raises
        return self._plan


@pytest.mark.asyncio
async def test_execute_produces_timeline_plan_composition_plan_and_enriched_prompts():
    service = CompositionPlanningService(Settings())
    scene_plan = _scene_plan(4)
    scene_prompts = _scene_prompts(4)

    result = await service.execute(
        scene_plan=scene_plan, scene_prompts=scene_prompts, voice_asset=_voice_asset(duration=40.0)
    )

    assert result.timeline_plan.total_duration_seconds == 40.0
    assert len(result.timeline_plan.scenes) == 4
    assert len(result.composition_plan.scenes) == 4
    assert all(prompt.prompt != f"prompt {i}" for i, prompt in enumerate(result.scene_prompts.prompts, start=1))


@pytest.mark.asyncio
async def test_execute_falls_back_to_default_scene_seconds_when_voice_failed():
    service = CompositionPlanningService(Settings())
    scene_plan = _scene_plan(3)
    scene_prompts = _scene_prompts(3)

    result = await service.execute(
        scene_plan=scene_plan, scene_prompts=scene_prompts, voice_asset=_voice_asset(status="FAILED", duration=0.0)
    )

    assert result.timeline_plan.total_duration_seconds == 9.0  # 3.0 default * 3 scenes
    assert len(result.timeline_plan.scenes) == 3


@pytest.mark.asyncio
async def test_execute_handles_empty_scene_plan_without_raising():
    service = CompositionPlanningService(Settings())
    scene_plan = ScenePlan(topic="Test", scenes=[])
    scene_prompts = ScenePromptSet(topic="Test", prompts=[])

    result = await service.execute(scene_plan=scene_plan, scene_prompts=scene_prompts, voice_asset=_voice_asset())

    assert result.timeline_plan.scenes == []
    assert result.composition_plan.scenes == []
    assert result.scene_prompts.prompts == []


@pytest.mark.asyncio
async def test_execute_uses_ai_director_plan_when_available_and_enabled():
    provider = FakeAIDirectorProvider(plan=_ai_plan(3))
    service = CompositionPlanningService(Settings(ai_director_enabled=True), ai_director_provider=provider)
    scene_plan = _scene_plan(3)
    scene_prompts = _scene_prompts(3)
    reviewed_script = ReviewedScript(
        topic="Test", revised_script="Full narration.", quality_score=90.0, readability_score=90.0,
        engagement_score=90.0, status="success",
    )
    strategy_package = StrategyPackage(
        topic="Test", target_audience="general", positioning="unique", hook="hook", pacing="steady"
    )

    result = await service.execute(
        scene_plan=scene_plan,
        scene_prompts=scene_prompts,
        voice_asset=_voice_asset(duration=30.0),
        reviewed_script=reviewed_script,
        strategy_package=strategy_package,
        user_id="user-1",
    )

    assert provider.called_with is not None
    assert provider.called_with["request"].narration_script == "Full narration."
    assert provider.called_with["request"].target_audience == "general"
    assert provider.called_with["user_id"] == "user-1"
    assert result.timeline_plan.metadata.get("source") == "ai_director"
    assert result.composition_plan.metadata.get("source") == "ai_director"
    assert result.composition_plan.scenes[0].purpose == ScenePurpose.INTRODUCTION
    assert result.timeline_plan.total_duration_seconds == 30.0


@pytest.mark.asyncio
async def test_execute_falls_back_to_deterministic_planning_when_ai_director_unavailable():
    provider = FakeAIDirectorProvider(raises=AIDirectorUnavailableError("no agent"))
    service = CompositionPlanningService(Settings(ai_director_enabled=True), ai_director_provider=provider)
    scene_plan = _scene_plan(3)
    scene_prompts = _scene_prompts(3)

    result = await service.execute(
        scene_plan=scene_plan, scene_prompts=scene_prompts, voice_asset=_voice_asset(duration=30.0)
    )

    assert provider.called_with is not None
    assert result.timeline_plan.metadata.get("source") != "ai_director"
    assert result.composition_plan.metadata.get("source") != "ai_director"
    assert result.timeline_plan.total_duration_seconds == 30.0
    assert len(result.composition_plan.scenes) == 3


@pytest.mark.asyncio
async def test_execute_falls_back_to_deterministic_planning_when_ai_director_output_invalid():
    # Only 2 of 3 scenes covered — a structural validation failure the plan
    # builder must reject, triggering the same fallback as an unavailable provider.
    bad_plan = _ai_plan(2)
    provider = FakeAIDirectorProvider(plan=bad_plan)
    service = CompositionPlanningService(Settings(ai_director_enabled=True), ai_director_provider=provider)
    scene_plan = _scene_plan(3)
    scene_prompts = _scene_prompts(3)

    result = await service.execute(
        scene_plan=scene_plan, scene_prompts=scene_prompts, voice_asset=_voice_asset(duration=30.0)
    )

    assert result.timeline_plan.metadata.get("source") != "ai_director"
    assert len(result.composition_plan.scenes) == 3


@pytest.mark.asyncio
async def test_execute_skips_ai_director_entirely_when_disabled_by_settings():
    provider = FakeAIDirectorProvider(plan=_ai_plan(3))
    service = CompositionPlanningService(Settings(ai_director_enabled=False), ai_director_provider=provider)
    scene_plan = _scene_plan(3)
    scene_prompts = _scene_prompts(3)

    result = await service.execute(
        scene_plan=scene_plan, scene_prompts=scene_prompts, voice_asset=_voice_asset(duration=30.0)
    )

    assert provider.called_with is None
    assert result.timeline_plan.metadata.get("source") != "ai_director"


@pytest.mark.asyncio
async def test_execute_skips_ai_director_when_no_provider_injected():
    # Default construction (no ai_director_provider) must behave exactly like F27
    # — pure deterministic planning, no AttributeError from a missing provider.
    service = CompositionPlanningService(Settings(ai_director_enabled=True))
    scene_plan = _scene_plan(2)
    scene_prompts = _scene_prompts(2)

    result = await service.execute(
        scene_plan=scene_plan, scene_prompts=scene_prompts, voice_asset=_voice_asset(duration=20.0)
    )

    assert result.timeline_plan.metadata.get("source") != "ai_director"
    assert len(result.timeline_plan.scenes) == 2


@pytest.mark.asyncio
async def test_execute_computes_budget_fields_for_ai_director_request():
    provider = FakeAIDirectorProvider(plan=_ai_plan(2))
    settings = Settings(
        ai_director_enabled=True,
        maximum_video_budget_usd=5.0,
        target_video_budget_usd=4.0,
        maximum_image_budget_usd=3.0,
        target_image_budget_usd=2.0,
        minimum_visual_beats_per_scene=1,
        target_visual_beats_per_scene=2,
        maximum_visual_beats_per_scene=4,
        # Pinned to the pre-F31 square size so this test's budget arithmetic stays
        # independent of F31's native-landscape default (see CostTracker.PRICING_TABLE).
        openai_image_size="1024x1024",
    )
    service = CompositionPlanningService(settings, ai_director_provider=provider)
    scene_plan = _scene_plan(2)
    scene_prompts = _scene_prompts(2)

    await service.execute(
        scene_plan=scene_plan,
        scene_prompts=scene_prompts,
        voice_asset=_voice_asset(duration=20.0),
        estimated_cost_so_far_usd=0.93,
    )

    request = provider.called_with["request"]
    assert request.maximum_production_budget_usd == 5.0
    assert request.target_production_budget_usd == 4.0
    assert request.estimated_cost_so_far_usd == 0.93
    assert request.remaining_budget_usd == pytest.approx(min(5.0 - 0.93, 3.0))
    assert request.estimated_image_cost_usd == pytest.approx(0.042)
    assert request.minimum_visual_beats_per_scene == 1
    assert request.target_visual_beats_per_scene == 2
    assert request.maximum_visual_beats_per_scene == 4


@pytest.mark.asyncio
async def test_execute_clamps_visual_beats_to_configured_maximum():
    beats = [VisualBeat(beat_number=i, description=f"beat {i}") for i in range(1, 6)]
    ai_plan = AIDirectorPlan(
        scenes=[
            AIDirectorSceneDirection(
                scene_number=1,
                duration_seconds=1.0,
                pacing=ScenePacing.STANDARD,
                purpose=ScenePurpose.INTRODUCTION,
                composition_style=CompositionStyle.WIDE_SHOT,
                camera_intent=CameraIntent.NEUTRAL_OBSERVATION,
                visual_beats=beats,
            )
        ]
    )
    provider = FakeAIDirectorProvider(plan=ai_plan)
    settings = Settings(
        ai_director_enabled=True,
        maximum_visual_beats_per_scene=2,
        maximum_image_budget_usd=1000.0,
        maximum_video_budget_usd=1000.0,
    )
    service = CompositionPlanningService(settings, ai_director_provider=provider)
    scene_plan = _scene_plan(1)
    scene_prompts = _scene_prompts(1)

    result = await service.execute(
        scene_plan=scene_plan, scene_prompts=scene_prompts, voice_asset=_voice_asset(duration=10.0)
    )

    assert len(result.composition_plan.scenes[0].visual_beats) == 2


@pytest.mark.asyncio
async def test_execute_trims_visual_beats_when_projected_cost_exceeds_remaining_budget():
    beats = [VisualBeat(beat_number=i, description=f"beat {i}") for i in range(1, 5)]
    ai_plan = AIDirectorPlan(
        scenes=[
            AIDirectorSceneDirection(
                scene_number=1,
                duration_seconds=1.0,
                pacing=ScenePacing.STANDARD,
                purpose=ScenePurpose.INTRODUCTION,
                composition_style=CompositionStyle.WIDE_SHOT,
                camera_intent=CameraIntent.NEUTRAL_OBSERVATION,
                visual_beats=beats,
            )
        ]
    )
    provider = FakeAIDirectorProvider(plan=ai_plan)
    # gpt-image-1/medium/1024x1024 costs $0.042/image (CostTracker.PRICING_TABLE); pinned
    # explicitly since F31 changed the application default to a landscape size/cost.
    settings = Settings(
        ai_director_enabled=True,
        maximum_visual_beats_per_scene=10,
        maximum_video_budget_usd=5.0,
        maximum_image_budget_usd=3.0,
        openai_image_size="1024x1024",
    )
    service = CompositionPlanningService(settings, ai_director_provider=provider)
    scene_plan = _scene_plan(1)
    scene_prompts = _scene_prompts(1)

    result = await service.execute(
        scene_plan=scene_plan,
        scene_prompts=scene_prompts,
        voice_asset=_voice_asset(duration=10.0),
        # remaining = min(5.0 - 4.9, 3.0) = 0.1 -> floor(0.1 / 0.042) = 2 images allowed
        estimated_cost_so_far_usd=4.9,
    )

    assert len(result.composition_plan.scenes[0].visual_beats) == 2


@pytest.mark.asyncio
async def test_execute_threads_visual_identity_context_into_enriched_prompts():
    service = CompositionPlanningService(Settings())
    scene_plan = _scene_plan(1)
    scene_prompts = ScenePromptSet(
        topic="Test", prompts=[ScenePrompt(scene_number=1, prompt="Mansa Musa crosses the desert")]
    )
    visual_identity_context = VisualIdentityContext(
        topic="Test",
        historical_context=HistoricalVisualContext(time_period="14th century"),
        characters=[CharacterVisualIdentity(name="Mansa Musa", clothing="cream robes trimmed in gold")],
    )

    result = await service.execute(
        scene_plan=scene_plan,
        scene_prompts=scene_prompts,
        voice_asset=_voice_asset(duration=10.0),
        visual_identity_context=visual_identity_context,
    )

    prompt = result.scene_prompts.prompts[0].prompt
    assert "14th century" in prompt
    assert "cream robes trimmed in gold" in prompt
