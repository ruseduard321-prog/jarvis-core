from __future__ import annotations

import logging
from datetime import datetime, timezone

from backend.core.config import Settings
from backend.core.workflow_engine_models import (
    WorkflowArtifact,
    WorkflowDefinition,
    WorkflowRunContext,
    WorkflowStep,
    WorkflowStepResult,
)
from backend.services.asset_packaging_service import AssetPackagingService
from backend.services.audio_engine_service import AudioEngineService
from backend.services.character_reference_image_service import CharacterReferenceImageService
from backend.services.composition_planning_service import CompositionPlanningService
from backend.services.media_workflow_service import MediaWorkflowService
from backend.services.publishing_package_workflow_service import PublishingPackageWorkflowService
from backend.services.research_workflow_service import ResearchWorkflowService
from backend.services.review_workflow_service import ReviewWorkflowService
from backend.services.run_artifact_storage_service import RunArtifactStorageService
from backend.services.scene_image_generation_service import SceneImageGenerationService
from backend.services.scene_planning_service import ScenePlanningService
from backend.services.strategy_workflow_service import StrategyWorkflowService
from backend.services.subtitle_generation_service import SubtitleGenerationService
from backend.services.thumbnail_generation_service import ThumbnailGenerationService
from backend.services.video_assembly_service import VideoAssemblyService
from backend.services.visual_identity_service import VisualIdentityService
from backend.services.voice_generation_service import VoiceGenerationService
from backend.services.workflow_artifacts import (
    build_step_metrics_artifact,
    render_asset_manifest_json,
    render_broll_plan_json,
    render_description_md,
    render_hashtags_md,
    render_composition_plan_json,
    render_media_prompts_md,
    render_music_md,
    render_research_md,
    render_review_md,
    render_scene_plan_json,
    render_scene_prompts_json,
    render_script_md,
    render_strategy_md,
    render_thumbnail_prompt_txt,
    render_timeline_plan_json,
    render_title_md,
    render_visual_identity_json,
)
from backend.services.writer_workflow_service import WriterWorkflowService

logger = logging.getLogger(__name__)

WORKFLOW_ID = "youtube_production_v1"
WORKFLOW_NAME = "YouTube Production Workflow v1"


def _map_metadata_status(status: object) -> str:
    normalized = str(status or "").lower()
    if normalized == "failed":
        return "FAILED"
    if normalized == "skipped":
        return "SKIPPED"
    return "SUCCESS"


def _log_step_started(step_name: str, context: WorkflowRunContext) -> None:
    logger.info(
        "step_started",
        extra={"step": step_name, "execution_id": context.execution_id, "workflow_id": WORKFLOW_ID},
    )


def _log_step_finished(step_name: str, context: WorkflowRunContext, duration_ms: float) -> None:
    logger.info(
        "step_finished",
        extra={
            "step": step_name,
            "execution_id": context.execution_id,
            "workflow_id": WORKFLOW_ID,
            "duration_ms": round(duration_ms, 2),
        },
    )


def _log_step_failed(step_name: str, context: WorkflowRunContext, reason: str) -> None:
    logger.warning(
        "step_failed",
        extra={"step": step_name, "execution_id": context.execution_id, "workflow_id": WORKFLOW_ID, "reason": reason},
    )


class ResearchStep(WorkflowStep):
    def __init__(self, research_workflow_service: ResearchWorkflowService) -> None:
        self._service = research_workflow_service

    @property
    def name(self) -> str:
        return "Research"

    async def run(self, context: WorkflowRunContext) -> WorkflowStepResult:
        started_at = datetime.now(timezone.utc)
        _log_step_started(self.name, context)
        package = await self._service.execute(topic=context.topic, constraints=None, user_id=context.user_id)
        if package.metadata.get("status") == "failed":
            reason = "; ".join(package.open_questions) or "unknown reason"
            _log_step_failed(self.name, context, reason)
            return WorkflowStepResult(step_name=self.name, status="failed", error=reason)
        finished_at = datetime.now(timezone.utc)
        _log_step_finished(self.name, context, (finished_at - started_at).total_seconds() * 1000)
        metrics_artifact = build_step_metrics_artifact(
            self.name,
            started_at,
            finished_at,
            provider_metrics=package.metadata.get("provider_metrics"),
            cost_estimate=package.metadata.get("cost_estimate"),
        )
        return WorkflowStepResult(
            step_name=self.name,
            status="success",
            data={"research_package": package},
            artifacts=[WorkflowArtifact("research.md", render_research_md(package)), metrics_artifact],
        )


class StrategyStep(WorkflowStep):
    def __init__(self, strategy_workflow_service: StrategyWorkflowService) -> None:
        self._service = strategy_workflow_service

    @property
    def name(self) -> str:
        return "Strategy"

    async def run(self, context: WorkflowRunContext) -> WorkflowStepResult:
        started_at = datetime.now(timezone.utc)
        _log_step_started(self.name, context)
        research_package = context.inputs["Research"]["research_package"]
        package = await self._service.execute(research_package=research_package, user_id=context.user_id)
        if package.metadata.get("status") == "failed":
            reason = str(package.metadata.get("reason", "unknown reason"))
            _log_step_failed(self.name, context, reason)
            return WorkflowStepResult(step_name=self.name, status="failed", error=reason)
        finished_at = datetime.now(timezone.utc)
        _log_step_finished(self.name, context, (finished_at - started_at).total_seconds() * 1000)
        metrics_artifact = build_step_metrics_artifact(
            self.name,
            started_at,
            finished_at,
            provider_metrics=package.metadata.get("provider_metrics"),
            cost_estimate=package.metadata.get("cost_estimate"),
        )
        return WorkflowStepResult(
            step_name=self.name,
            status="success",
            data={"strategy_package": package},
            artifacts=[WorkflowArtifact("strategy.md", render_strategy_md(package)), metrics_artifact],
        )


class WriterStep(WorkflowStep):
    def __init__(self, writer_workflow_service: WriterWorkflowService) -> None:
        self._service = writer_workflow_service

    @property
    def name(self) -> str:
        return "Writer"

    async def run(self, context: WorkflowRunContext) -> WorkflowStepResult:
        started_at = datetime.now(timezone.utc)
        _log_step_started(self.name, context)
        research_package = context.inputs["Research"]["research_package"]
        strategy_package = context.inputs["Strategy"]["strategy_package"]
        draft = await self._service.execute(
            research_package=research_package,
            duration_profile="standard",
            user_id=context.user_id,
            strategy_package=strategy_package,
        )
        if draft.metadata.get("status") == "failed":
            reason = str(draft.metadata.get("reason", "unknown reason"))
            _log_step_failed(self.name, context, reason)
            return WorkflowStepResult(step_name=self.name, status="failed", error=reason)
        finished_at = datetime.now(timezone.utc)
        _log_step_finished(self.name, context, (finished_at - started_at).total_seconds() * 1000)
        metrics_artifact = build_step_metrics_artifact(
            self.name,
            started_at,
            finished_at,
            provider_metrics=draft.metadata.get("provider_metrics"),
            cost_estimate=draft.metadata.get("cost_estimate"),
        )
        return WorkflowStepResult(
            step_name=self.name,
            status="success",
            data={"script_draft": draft},
            artifacts=[WorkflowArtifact("script.md", render_script_md(draft)), metrics_artifact],
        )


class ReviewStep(WorkflowStep):
    def __init__(self, review_workflow_service: ReviewWorkflowService) -> None:
        self._service = review_workflow_service

    @property
    def name(self) -> str:
        return "Review"

    async def run(self, context: WorkflowRunContext) -> WorkflowStepResult:
        started_at = datetime.now(timezone.utc)
        _log_step_started(self.name, context)
        script_draft = context.inputs["Writer"]["script_draft"]
        reviewed = await self._service.execute(script_draft=script_draft, user_id=context.user_id)
        if reviewed.metadata.get("status") == "failed":
            reason = str(reviewed.metadata.get("reason", "unknown reason"))
            _log_step_failed(self.name, context, reason)
            return WorkflowStepResult(step_name=self.name, status="failed", error=reason)
        finished_at = datetime.now(timezone.utc)
        _log_step_finished(self.name, context, (finished_at - started_at).total_seconds() * 1000)
        metrics_artifact = build_step_metrics_artifact(
            self.name,
            started_at,
            finished_at,
            provider_metrics=reviewed.metadata.get("provider_metrics"),
            cost_estimate=reviewed.metadata.get("cost_estimate"),
        )
        return WorkflowStepResult(
            step_name=self.name,
            status="success",
            data={"reviewed_script": reviewed},
            artifacts=[WorkflowArtifact("review.md", render_review_md(reviewed)), metrics_artifact],
        )


class VisualIdentityStep(WorkflowStep):
    """F31 Photorealistic Visual Engine: builds the production's shared
    HistoricalVisualContext plus one canonical CharacterVisualIdentity per
    recurring named figure (VisualIdentityService), then generates each
    character's reference portrait (CharacterReferenceImageService). Always
    reports success at the engine level — VisualIdentityService's own failure mode
    is an empty (no-op) context, never a workflow failure, the same fallback
    discipline AI Director already established for Composition Planning."""

    def __init__(
        self,
        visual_identity_service: VisualIdentityService,
        character_reference_image_service: CharacterReferenceImageService,
    ) -> None:
        self._service = visual_identity_service
        self._reference_service = character_reference_image_service

    @property
    def name(self) -> str:
        return "Visual Identity"

    async def run(self, context: WorkflowRunContext) -> WorkflowStepResult:
        started_at = datetime.now(timezone.utc)
        _log_step_started(self.name, context)
        research_package = context.inputs["Research"]["research_package"]
        reviewed_script = context.inputs["Review"]["reviewed_script"]
        visual_identity_context = await self._service.execute(
            research_package=research_package, reviewed_script=reviewed_script, user_id=context.user_id
        )

        # F3: seed the character-reference budget with everything spent by every
        # prior step (Research through Review), not just Visual Identity's own LLM
        # call — mirrors CompositionPlanningStep's existing estimated_cost_so_far
        # pattern exactly.
        estimated_cost_so_far = sum(context.cost_ledger.values())
        characters, character_image_bytes, character_reference_cost_usd = await self._reference_service.execute(
            characters=visual_identity_context.characters,
            historical_context=visual_identity_context.historical_context,
            estimated_cost_so_far_usd=estimated_cost_so_far,
        )
        visual_identity_context = visual_identity_context.model_copy(update={"characters": characters})

        finished_at = datetime.now(timezone.utc)
        _log_step_finished(self.name, context, (finished_at - started_at).total_seconds() * 1000)

        # F3: this step's true cost is VisualIdentityService's own LLM call PLUS
        # every character reference portrait (generation + validation + any
        # regeneration) — combining both into one cost_estimate here is what makes
        # context.cost_ledger["Visual Identity"] (populated generically by
        # WorkflowEngine._record_step_cost from this artifact) reflect real total
        # spend instead of only half of it.
        cost_estimate = dict(visual_identity_context.metadata.get("cost_estimate") or {})
        cost_estimate["estimated_cost_usd"] = round(
            float(cost_estimate.get("estimated_cost_usd", 0.0)) + character_reference_cost_usd, 6
        )
        metrics_artifact = build_step_metrics_artifact(
            self.name,
            started_at,
            finished_at,
            provider_metrics=visual_identity_context.metadata.get("provider_metrics"),
            cost_estimate=cost_estimate,
        )
        artifacts = [
            WorkflowArtifact(filename, content_bytes=image_bytes)
            for filename, image_bytes in character_image_bytes.items()
        ]
        artifacts.append(
            WorkflowArtifact("visual_context.json", render_visual_identity_json(visual_identity_context))
        )
        artifacts.append(metrics_artifact)
        return WorkflowStepResult(
            step_name=self.name,
            status="success",
            data={"visual_identity_context": visual_identity_context},
            artifacts=artifacts,
        )


class MediaStep(WorkflowStep):
    def __init__(self, media_workflow_service: MediaWorkflowService) -> None:
        self._service = media_workflow_service

    @property
    def name(self) -> str:
        return "Media"

    async def run(self, context: WorkflowRunContext) -> WorkflowStepResult:
        started_at = datetime.now(timezone.utc)
        _log_step_started(self.name, context)
        reviewed_script = context.inputs["Review"]["reviewed_script"]
        media_package = await self._service.execute(reviewed_script=reviewed_script, user_id=context.user_id)
        if media_package.metadata.get("status") == "failed":
            reason = str(media_package.metadata.get("reason", "unknown reason"))
            _log_step_failed(self.name, context, reason)
            return WorkflowStepResult(step_name=self.name, status="failed", error=reason)
        finished_at = datetime.now(timezone.utc)
        _log_step_finished(self.name, context, (finished_at - started_at).total_seconds() * 1000)
        metrics_artifact = build_step_metrics_artifact(
            self.name,
            started_at,
            finished_at,
            provider_metrics=media_package.metadata.get("provider_metrics"),
            cost_estimate=media_package.metadata.get("cost_estimate"),
        )
        return WorkflowStepResult(
            step_name=self.name,
            status="success",
            data={"media_package": media_package},
            artifacts=[
                WorkflowArtifact("media_prompts.md", render_media_prompts_md(media_package)),
                WorkflowArtifact("thumbnail_prompt.txt", render_thumbnail_prompt_txt(media_package)),
                metrics_artifact,
            ],
        )


class PublishingPackageStep(WorkflowStep):
    def __init__(self, publishing_package_workflow_service: PublishingPackageWorkflowService) -> None:
        self._service = publishing_package_workflow_service

    @property
    def name(self) -> str:
        return "Publishing Package"

    async def run(self, context: WorkflowRunContext) -> WorkflowStepResult:
        started_at = datetime.now(timezone.utc)
        _log_step_started(self.name, context)
        reviewed_script = context.inputs["Review"]["reviewed_script"]
        media_package = context.inputs["Media"]["media_package"]
        package = await self._service.execute(
            reviewed_script=reviewed_script, media_package=media_package, user_id=context.user_id
        )
        if package.metadata.get("status") == "failed":
            reason = str(package.metadata.get("reason", "unknown reason"))
            _log_step_failed(self.name, context, reason)
            return WorkflowStepResult(step_name=self.name, status="failed", error=reason)
        finished_at = datetime.now(timezone.utc)
        _log_step_finished(self.name, context, (finished_at - started_at).total_seconds() * 1000)
        metrics_artifact = build_step_metrics_artifact(
            self.name,
            started_at,
            finished_at,
            provider_metrics=package.metadata.get("provider_metrics"),
            cost_estimate=package.metadata.get("cost_estimate"),
        )
        return WorkflowStepResult(
            step_name=self.name,
            status="success",
            data={"publishing_package": package},
            artifacts=[
                WorkflowArtifact("title.md", render_title_md(package)),
                WorkflowArtifact("description.md", render_description_md(package)),
                WorkflowArtifact("hashtags.md", render_hashtags_md(package)),
                metrics_artifact,
            ],
        )


class VoiceStep(WorkflowStep):
    """Generates the narration voice-over. Always reports success at the engine
    level — the real outcome lives in VoiceAsset.status so a provider failure
    never aborts the rest of the pipeline."""

    def __init__(self, voice_generation_service: VoiceGenerationService) -> None:
        self._service = voice_generation_service

    @property
    def name(self) -> str:
        return "Voice"

    async def run(self, context: WorkflowRunContext) -> WorkflowStepResult:
        started_at = datetime.now(timezone.utc)
        _log_step_started(self.name, context)
        reviewed_script = context.inputs["Review"]["reviewed_script"]
        asset, audio_bytes = await self._service.execute(reviewed_script)
        finished_at = datetime.now(timezone.utc)
        if asset.status != "SUCCESS":
            _log_step_failed(self.name, context, asset.error or "voice generation failed")
        else:
            _log_step_finished(self.name, context, (finished_at - started_at).total_seconds() * 1000)
        provider_metrics = {
            "provider": asset.provider,
            "model": asset.model,
            "call_count": 1 if asset.provider != "none" else 0,
            "duration_ms": asset.generation_duration_ms,
            "success": asset.status == "SUCCESS",
            "failure_reason": asset.error,
        }
        cost_estimate = {
            "provider": asset.provider,
            "model": asset.model,
            "estimated_input_tokens": asset.estimated_input_tokens,
            "estimated_output_tokens": asset.estimated_output_tokens,
            "estimated_cost_usd": asset.estimated_cost_usd,
        }
        metrics_artifact = build_step_metrics_artifact(
            self.name, started_at, finished_at, provider_metrics=provider_metrics, cost_estimate=cost_estimate
        )
        artifacts = [WorkflowArtifact(asset.filename, content_bytes=audio_bytes)] if audio_bytes else []
        artifacts.append(metrics_artifact)
        return WorkflowStepResult(
            step_name=self.name,
            status="success",
            data={"voice_asset": asset},
            artifacts=artifacts,
        )


class ThumbnailStep(WorkflowStep):
    """Generates the production thumbnail image. Always reports success at the
    engine level — the real outcome lives in ImageAsset.status."""

    def __init__(self, thumbnail_generation_service: ThumbnailGenerationService) -> None:
        self._service = thumbnail_generation_service

    @property
    def name(self) -> str:
        return "Thumbnail"

    async def run(self, context: WorkflowRunContext) -> WorkflowStepResult:
        started_at = datetime.now(timezone.utc)
        _log_step_started(self.name, context)
        media_package = context.inputs["Media"]["media_package"]
        visual_identity_context = context.inputs.get("Visual Identity", {}).get("visual_identity_context")
        reference_images = {
            artifact.filename: artifact.content_bytes
            for artifact in context.artifacts
            if artifact.content_bytes is not None and artifact.filename.startswith("character_")
        }
        # F3: budget-aware — see SceneImageStep below for the identical pattern.
        estimated_cost_so_far = sum(context.cost_ledger.values())
        asset, image_bytes = await self._service.execute(
            media_package.thumbnail_prompt,
            visual_identity_context=visual_identity_context,
            reference_images=reference_images,
            estimated_cost_so_far_usd=estimated_cost_so_far,
        )
        finished_at = datetime.now(timezone.utc)
        if asset.status != "SUCCESS":
            _log_step_failed(self.name, context, asset.error or "thumbnail generation failed")
        else:
            _log_step_finished(self.name, context, (finished_at - started_at).total_seconds() * 1000)
        provider_metrics = {
            "provider": asset.provider,
            "model": asset.model,
            "call_count": 1 if asset.provider != "none" else 0,
            "duration_ms": asset.generation_duration_ms,
            "success": asset.status == "SUCCESS",
            "failure_reason": asset.error,
        }
        cost_estimate = {
            "provider": asset.provider,
            "model": asset.model,
            "estimated_input_tokens": asset.estimated_input_tokens,
            "estimated_output_tokens": asset.estimated_output_tokens,
            "estimated_cost_usd": asset.estimated_cost_usd,
        }
        metrics_artifact = build_step_metrics_artifact(
            self.name, started_at, finished_at, provider_metrics=provider_metrics, cost_estimate=cost_estimate
        )
        artifacts = [WorkflowArtifact(asset.filename, content_bytes=image_bytes)] if image_bytes else []
        artifacts.append(metrics_artifact)
        return WorkflowStepResult(
            step_name=self.name,
            status="success",
            data={"image_asset": asset},
            artifacts=artifacts,
        )


class ScenePlanningStep(WorkflowStep):
    """Produces the scene breakdown, per-scene image prompts, B-roll plan, and
    music direction. Always reports success at the engine level — real outcome
    lives in each package's metadata['status']."""

    def __init__(self, scene_planning_service: ScenePlanningService) -> None:
        self._service = scene_planning_service

    @property
    def name(self) -> str:
        return "Scene Planning"

    async def run(self, context: WorkflowRunContext) -> WorkflowStepResult:
        started_at = datetime.now(timezone.utc)
        _log_step_started(self.name, context)
        reviewed_script = context.inputs["Review"]["reviewed_script"]
        media_package = context.inputs["Media"]["media_package"]
        result = await self._service.execute(reviewed_script, media_package, context.user_id)
        finished_at = datetime.now(timezone.utc)
        if result.scene_plan.metadata.get("status") == "failed":
            _log_step_failed(self.name, context, str(result.scene_plan.metadata.get("reason", "unknown reason")))
        else:
            _log_step_finished(self.name, context, (finished_at - started_at).total_seconds() * 1000)
        metrics_artifact = build_step_metrics_artifact(
            self.name,
            started_at,
            finished_at,
            provider_metrics=result.scene_plan.metadata.get("provider_metrics"),
            cost_estimate=result.scene_plan.metadata.get("cost_estimate"),
        )
        return WorkflowStepResult(
            step_name=self.name,
            status="success",
            data={
                "scene_plan": result.scene_plan,
                "scene_prompts": result.scene_prompts,
                "broll_plan": result.broll_plan,
                "music_plan": result.music_plan,
            },
            artifacts=[
                WorkflowArtifact("scene_plan.json", render_scene_plan_json(result.scene_plan)),
                WorkflowArtifact("scene_prompts.json", render_scene_prompts_json(result.scene_prompts)),
                WorkflowArtifact("broll_plan.json", render_broll_plan_json(result.broll_plan)),
                WorkflowArtifact("music.md", render_music_md(result.music_plan)),
                metrics_artifact,
            ],
        )


class CompositionPlanningStep(WorkflowStep):
    """Builds the F27/F28 Smart Scene Composition + AI Director layer: the
    authoritative TimelinePlan (single source of truth for scene timing), the
    CompositionPlan derived from it (purpose, framing, continuity — never
    timing), and the composition-enriched scene prompts SceneImage should use
    instead of the Scene Planning step's raw prompts. Both plans are produced by
    the AI Director (the single creative authority) when available, falling back
    automatically to F27's deterministic planners otherwise — see
    CompositionPlanningService. Always reports success at the engine level: the
    AI Director's own failure mode is an automatic fallback, never a workflow
    failure."""

    def __init__(self, composition_planning_service: CompositionPlanningService) -> None:
        self._service = composition_planning_service

    @property
    def name(self) -> str:
        return "Composition Planning"

    async def run(self, context: WorkflowRunContext) -> WorkflowStepResult:
        started_at = datetime.now(timezone.utc)
        _log_step_started(self.name, context)
        scene_plan = context.inputs["Scene Planning"]["scene_plan"]
        scene_prompts = context.inputs["Scene Planning"]["scene_prompts"]
        voice_asset = context.inputs["Voice"]["voice_asset"]
        reviewed_script = context.inputs["Review"]["reviewed_script"]
        strategy_package = context.inputs.get("Strategy", {}).get("strategy_package")
        visual_identity_context = context.inputs.get("Visual Identity", {}).get("visual_identity_context")
        # F28B Production Budget Awareness: every prior step's own estimated cost,
        # recorded by the engine from each step's metrics artifact (see
        # WorkflowEngine._record_step_cost) — the AI Director reasons against this
        # total, never against its own guess.
        estimated_cost_so_far = sum(context.cost_ledger.values())

        result = await self._service.execute(
            scene_plan=scene_plan,
            scene_prompts=scene_prompts,
            voice_asset=voice_asset,
            reviewed_script=reviewed_script,
            strategy_package=strategy_package,
            estimated_cost_so_far_usd=estimated_cost_so_far,
            visual_identity_context=visual_identity_context,
            user_id=context.user_id,
        )
        finished_at = datetime.now(timezone.utc)
        _log_step_finished(self.name, context, (finished_at - started_at).total_seconds() * 1000)

        metrics_artifact = build_step_metrics_artifact(self.name, started_at, finished_at)
        return WorkflowStepResult(
            step_name=self.name,
            status="success",
            data={
                "timeline_plan": result.timeline_plan,
                "composition_plan": result.composition_plan,
                "scene_prompts": result.scene_prompts,
            },
            artifacts=[
                WorkflowArtifact("timeline_plan.json", render_timeline_plan_json(result.timeline_plan)),
                WorkflowArtifact("composition_plan.json", render_composition_plan_json(result.composition_plan)),
                WorkflowArtifact("composition_scene_prompts.json", render_scene_prompts_json(result.scene_prompts)),
                metrics_artifact,
            ],
        )


class SceneImageStep(WorkflowStep):
    """Generates one real image per scene from the Composition Planning step's
    composition-enriched per-scene prompts. Always reports success at the engine
    level — real per-scene outcomes live in each SceneImageAsset.status within
    the SceneImageSet."""

    def __init__(self, scene_image_generation_service: SceneImageGenerationService) -> None:
        self._service = scene_image_generation_service

    @property
    def name(self) -> str:
        return "Scene Image"

    async def run(self, context: WorkflowRunContext) -> WorkflowStepResult:
        started_at = datetime.now(timezone.utc)
        _log_step_started(self.name, context)
        scene_prompts = context.inputs["Composition Planning"]["scene_prompts"]
        visual_identity_context = context.inputs.get("Visual Identity", {}).get("visual_identity_context")
        characters = visual_identity_context.characters if visual_identity_context is not None else None
        reference_images = {
            artifact.filename: artifact.content_bytes
            for artifact in context.artifacts
            if artifact.content_bytes is not None and artifact.filename.startswith("character_")
        }
        # F3: budget-aware — everything spent by every prior step (including
        # Visual Identity's character portraits and Thumbnail's own validation/
        # regeneration cost) is already reflected in context.cost_ledger by now.
        estimated_cost_so_far = sum(context.cost_ledger.values())
        scene_image_set, image_bytes_by_filename = await self._service.execute(
            scene_prompts,
            characters=characters,
            reference_images=reference_images,
            estimated_cost_so_far_usd=estimated_cost_so_far,
        )
        finished_at = datetime.now(timezone.utc)
        failures = [image for image in scene_image_set.images if image.status != "SUCCESS"]
        if scene_image_set.images and len(failures) == len(scene_image_set.images):
            _log_step_failed(self.name, context, "all scene image generations failed")
        else:
            _log_step_finished(self.name, context, (finished_at - started_at).total_seconds() * 1000)

        provider_metrics = {
            "provider": "openai-image-generation" if scene_image_set.images else "none",
            "call_count": len(scene_image_set.images),
            "duration_ms": round(sum(image.generation_duration_ms for image in scene_image_set.images), 2),
            "retry_count": sum(image.retry_count for image in scene_image_set.images),
            "success": bool(scene_image_set.images) and not failures,
            "failure_count": len(failures),
        }
        cost_estimate = {
            "provider": "openai-image-generation" if scene_image_set.images else "none",
            "estimated_cost_usd": round(sum(image.estimated_cost_usd for image in scene_image_set.images), 6),
        }
        metrics_artifact = build_step_metrics_artifact(
            self.name, started_at, finished_at, provider_metrics=provider_metrics, cost_estimate=cost_estimate
        )
        artifacts = [
            WorkflowArtifact(image.filename, content_bytes=image_bytes_by_filename[image.filename])
            for image in scene_image_set.images
            if image.filename in image_bytes_by_filename
        ]
        artifacts.append(metrics_artifact)
        return WorkflowStepResult(
            step_name=self.name,
            status="success",
            data={"scene_image_set": scene_image_set},
            artifacts=artifacts,
        )


class SubtitleStep(WorkflowStep):
    """Derives an SRT subtitle track from the reviewed script. Always reports
    success at the engine level — real outcome lives in SubtitleAsset.status."""

    def __init__(self, subtitle_generation_service: SubtitleGenerationService) -> None:
        self._service = subtitle_generation_service

    @property
    def name(self) -> str:
        return "Subtitle"

    async def run(self, context: WorkflowRunContext) -> WorkflowStepResult:
        started_at = datetime.now(timezone.utc)
        _log_step_started(self.name, context)
        reviewed_script = context.inputs["Review"]["reviewed_script"]
        voice_asset = context.inputs["Voice"]["voice_asset"]
        asset, srt_content = self._service.execute(reviewed_script, voice_asset)
        finished_at = datetime.now(timezone.utc)
        if asset.status != "SUCCESS":
            _log_step_failed(self.name, context, asset.error or "subtitle generation failed")
        else:
            _log_step_finished(self.name, context, (finished_at - started_at).total_seconds() * 1000)
        metrics_artifact = build_step_metrics_artifact(self.name, started_at, finished_at)
        artifacts = [WorkflowArtifact(asset.filename, srt_content)] if srt_content else []
        artifacts.append(metrics_artifact)
        return WorkflowStepResult(
            step_name=self.name,
            status="success",
            data={"subtitle_asset": asset},
            artifacts=artifacts,
        )


class AudioEngineStep(WorkflowStep):
    """Builds the final mixed/mastered audio track from the processed narration plus
    optional background music and sound effects (see AudioEngineService/AudioTimeline,
    docs/F26_ARCHITECTURE_PROPOSAL.md). Always reports success at the engine level —
    the real outcome lives in AudioAsset.status; a SKIPPED/FAILED outcome here simply
    means Video Assembly falls back to the raw narration track, exactly like
    cinematic rendering falls back to the legacy slideshow renderer."""

    def __init__(self, audio_engine_service: AudioEngineService) -> None:
        self._service = audio_engine_service

    @property
    def name(self) -> str:
        return "Audio Mix"

    async def run(self, context: WorkflowRunContext) -> WorkflowStepResult:
        started_at = datetime.now(timezone.utc)
        _log_step_started(self.name, context)
        voice_asset = context.inputs["Voice"]["voice_asset"]
        music_plan = context.inputs["Scene Planning"]["music_plan"]
        scene_plan = context.inputs["Scene Planning"]["scene_plan"]
        timeline_plan = context.inputs["Composition Planning"]["timeline_plan"]

        bytes_by_filename = {
            artifact.filename: artifact.content_bytes
            for artifact in context.artifacts
            if artifact.content_bytes is not None
        }
        narration_bytes = bytes_by_filename.get(voice_asset.filename)

        asset, mixed_bytes = await self._service.execute(
            voice_asset=voice_asset,
            narration_bytes=narration_bytes,
            music_plan=music_plan,
            scene_plan=scene_plan,
            timeline_plan=timeline_plan,
        )
        finished_at = datetime.now(timezone.utc)
        if asset.status != "SUCCESS":
            _log_step_failed(self.name, context, asset.error or "audio mixing skipped or failed")
        else:
            _log_step_finished(self.name, context, (finished_at - started_at).total_seconds() * 1000)

        provider_metrics = {
            "provider": asset.provider,
            "call_count": 1 if asset.status == "SUCCESS" else 0,
            "duration_ms": asset.generation_duration_ms,
            "success": asset.status == "SUCCESS",
            "failure_reason": asset.error,
        }
        cost_estimate = {"provider": asset.provider, "estimated_cost_usd": asset.estimated_cost_usd}
        metrics_artifact = build_step_metrics_artifact(
            self.name, started_at, finished_at, provider_metrics=provider_metrics, cost_estimate=cost_estimate
        )
        artifacts = [WorkflowArtifact(asset.filename, content_bytes=mixed_bytes)] if mixed_bytes else []
        artifacts.append(metrics_artifact)
        return WorkflowStepResult(
            step_name=self.name,
            status="success",
            data={"audio_asset": asset},
            artifacts=artifacts,
        )


class VideoAssemblyStep(WorkflowStep):
    """Composes the narration audio, per-scene images, and subtitles produced by earlier
    steps into a single .mp4 via VideoAssemblyService. Always reports success at the
    engine level — real outcome lives in VideoAsset.status."""

    def __init__(
        self,
        video_assembly_service: VideoAssemblyService,
        run_artifact_storage_service: RunArtifactStorageService,
    ) -> None:
        self._service = video_assembly_service
        self._storage_service = run_artifact_storage_service

    @property
    def name(self) -> str:
        return "Video Assembly"

    async def run(self, context: WorkflowRunContext) -> WorkflowStepResult:
        started_at = datetime.now(timezone.utc)
        _log_step_started(self.name, context)
        scene_image_set = context.inputs["Scene Image"]["scene_image_set"]
        voice_asset = context.inputs["Voice"]["voice_asset"]
        subtitle_asset = context.inputs["Subtitle"]["subtitle_asset"]
        scene_plan = context.inputs["Scene Planning"]["scene_plan"]
        composition_plan = context.inputs["Composition Planning"]["composition_plan"]

        bytes_by_filename = {
            artifact.filename: artifact.content_bytes
            for artifact in context.artifacts
            if artifact.content_bytes is not None
        }
        text_by_filename = {artifact.filename: artifact.content for artifact in context.artifacts if artifact.content}
        # Prefer the Audio Mix step's mastered track; fall back to the raw (already
        # normalized) narration track untouched if mixing was skipped/disabled/failed —
        # same fallback discipline as cinematic rendering falling back to the slideshow.
        audio_bytes = bytes_by_filename.get(voice_asset.filename)
        audio_asset = context.inputs.get("Audio Mix", {}).get("audio_asset")
        if audio_asset is not None and audio_asset.status == "SUCCESS":
            mixed_bytes = bytes_by_filename.get(audio_asset.filename)
            if mixed_bytes:
                audio_bytes = mixed_bytes
        subtitle_content = text_by_filename.get(subtitle_asset.filename, "")

        asset, video_bytes = await self._service.execute(
            scene_image_set=scene_image_set,
            image_bytes_by_filename=bytes_by_filename,
            voice_asset=voice_asset,
            audio_bytes=audio_bytes,
            subtitle_asset=subtitle_asset,
            subtitle_content=subtitle_content,
            run_id=context.execution_id,
            scene_plan=scene_plan,
            composition_plan=composition_plan,
        )
        finished_at = datetime.now(timezone.utc)
        if asset.status != "SUCCESS":
            _log_step_failed(self.name, context, asset.error or "video assembly failed")
        else:
            _log_step_finished(self.name, context, (finished_at - started_at).total_seconds() * 1000)
            self._storage_service.persist(context.execution_id, context.artifacts)

        provider_metrics = {
            "provider": asset.provider,
            "call_count": 1 if asset.provider != "none" else 0,
            "duration_ms": asset.generation_duration_ms,
            "success": asset.status == "SUCCESS",
            "failure_reason": asset.error,
        }
        cost_estimate = {"provider": asset.provider, "estimated_cost_usd": asset.estimated_cost_usd}
        metrics_artifact = build_step_metrics_artifact(
            self.name, started_at, finished_at, provider_metrics=provider_metrics, cost_estimate=cost_estimate
        )
        artifacts = [WorkflowArtifact(asset.filename, content_bytes=video_bytes)] if video_bytes else []
        artifacts.append(metrics_artifact)
        return WorkflowStepResult(
            step_name=self.name,
            status="success",
            data={"video_asset": asset, "video_file_path": asset.file_path or asset.filename},
            artifacts=artifacts,
        )


class AssetPackagingStep(WorkflowStep):
    """Aggregates the status of every asset produced by prior steps into a final
    asset_manifest.json. Always reports success — packaging itself never fails
    the workflow; individual asset failures are already captured per-entry.

    F3: also computes and records the run's true total cost — the sum of every
    prior step's own reported spend (context.cost_ledger, which by this point
    includes image generation, image validation, and any regeneration) against
    Settings.maximum_video_budget_usd — so the budget ceiling's real outcome is
    visible in the one artifact every run always produces, not just reasoned
    about in a prompt."""

    def __init__(self, asset_packaging_service: AssetPackagingService, settings: Settings) -> None:
        self._service = asset_packaging_service
        self._settings = settings

    @property
    def name(self) -> str:
        return "Asset Packaging"

    async def run(self, context: WorkflowRunContext) -> WorkflowStepResult:
        started_at = datetime.now(timezone.utc)
        _log_step_started(self.name, context)
        entries = []
        now = datetime.now(timezone.utc).isoformat()

        voice_asset = context.inputs.get("Voice", {}).get("voice_asset")
        if voice_asset is not None:
            entries.append(
                self._service.build_entry(
                    asset_type="voice",
                    provider=voice_asset.provider,
                    status=voice_asset.status,
                    path=voice_asset.filename,
                    timestamp=voice_asset.generation_time,
                    duration=voice_asset.duration or None,
                    error=voice_asset.error,
                    model=voice_asset.model,
                    generation_duration_ms=voice_asset.generation_duration_ms,
                    retry_count=voice_asset.retry_count,
                )
            )

        image_asset = context.inputs.get("Thumbnail", {}).get("image_asset")
        if image_asset is not None:
            entries.append(
                self._service.build_entry(
                    asset_type="thumbnail",
                    provider=image_asset.provider,
                    status=image_asset.status,
                    path=image_asset.filename,
                    timestamp=image_asset.generation_time,
                    error=image_asset.error,
                    model=image_asset.model,
                    generation_duration_ms=image_asset.generation_duration_ms,
                    retry_count=image_asset.retry_count,
                )
            )

        subtitle_asset = context.inputs.get("Subtitle", {}).get("subtitle_asset")
        if subtitle_asset is not None:
            entries.append(
                self._service.build_entry(
                    asset_type="subtitle",
                    provider=subtitle_asset.provider,
                    status=subtitle_asset.status,
                    path=subtitle_asset.filename,
                    timestamp=subtitle_asset.generation_time,
                    error=subtitle_asset.error,
                )
            )

        audio_asset = context.inputs.get("Audio Mix", {}).get("audio_asset")
        if audio_asset is not None:
            entries.append(
                self._service.build_entry(
                    asset_type="audio_mix",
                    provider=audio_asset.provider,
                    status=audio_asset.status,
                    path=audio_asset.filename,
                    timestamp=audio_asset.generation_time,
                    duration=audio_asset.duration or None,
                    error=audio_asset.error,
                    generation_duration_ms=audio_asset.generation_duration_ms,
                )
            )

        video_asset = context.inputs.get("Video Assembly", {}).get("video_asset")
        if video_asset is not None:
            entries.append(
                self._service.build_entry(
                    asset_type="video",
                    provider=video_asset.provider,
                    status=video_asset.status,
                    path=video_asset.filename,
                    timestamp=video_asset.generation_time,
                    duration=video_asset.duration or None,
                    error=video_asset.error,
                    generation_duration_ms=video_asset.generation_duration_ms,
                )
            )

        scene_inputs = context.inputs.get("Scene Planning", {})
        scene_plan = scene_inputs.get("scene_plan")
        if scene_plan is not None:
            entries.append(
                self._service.build_entry(
                    asset_type="scene_plan",
                    provider="workflow",
                    status=_map_metadata_status(scene_plan.metadata.get("status")),
                    path="scene_plan.json",
                    timestamp=now,
                    error=str(scene_plan.metadata["reason"]) if scene_plan.metadata.get("status") == "failed" else None,
                )
            )

        scene_prompts = scene_inputs.get("scene_prompts")
        if scene_prompts is not None:
            entries.append(
                self._service.build_entry(
                    asset_type="scene_prompts",
                    provider="workflow",
                    status=_map_metadata_status(scene_prompts.metadata.get("status")),
                    path="scene_prompts.json",
                    timestamp=now,
                    error=str(scene_prompts.metadata["reason"])
                    if scene_prompts.metadata.get("status") == "failed"
                    else None,
                )
            )

        broll_plan = scene_inputs.get("broll_plan")
        if broll_plan is not None:
            entries.append(
                self._service.build_entry(
                    asset_type="broll_plan",
                    provider="workflow",
                    status=_map_metadata_status(broll_plan.metadata.get("status")),
                    path="broll_plan.json",
                    timestamp=now,
                )
            )

        music_plan = scene_inputs.get("music_plan")
        if music_plan is not None:
            entries.append(
                self._service.build_entry(
                    asset_type="music_plan",
                    provider="workflow",
                    status=_map_metadata_status(music_plan.metadata.get("status")),
                    path="music.md",
                    timestamp=now,
                )
            )

        visual_identity_context = context.inputs.get("Visual Identity", {}).get("visual_identity_context")
        if visual_identity_context is not None:
            entries.append(
                self._service.build_entry(
                    asset_type="visual_identity",
                    provider="workflow",
                    status=_map_metadata_status(visual_identity_context.metadata.get("status")),
                    path="visual_context.json",
                    timestamp=now,
                )
            )

        composition_inputs = context.inputs.get("Composition Planning", {})
        timeline_plan = composition_inputs.get("timeline_plan")
        if timeline_plan is not None:
            entries.append(
                self._service.build_entry(
                    asset_type="timeline_plan",
                    provider="workflow",
                    status=_map_metadata_status(timeline_plan.metadata.get("status")),
                    path="timeline_plan.json",
                    timestamp=now,
                    duration=timeline_plan.total_duration_seconds or None,
                )
            )

        composition_plan = composition_inputs.get("composition_plan")
        if composition_plan is not None:
            entries.append(
                self._service.build_entry(
                    asset_type="composition_plan",
                    provider="workflow",
                    status=_map_metadata_status(composition_plan.metadata.get("status")),
                    path="composition_plan.json",
                    timestamp=now,
                )
            )

        total_estimated_cost_usd = sum(context.cost_ledger.values())
        manifest = self._service.build_manifest(
            context.execution_id,
            entries,
            total_estimated_cost_usd=total_estimated_cost_usd,
            maximum_video_budget_usd=self._settings.maximum_video_budget_usd,
        )
        finished_at = datetime.now(timezone.utc)
        _log_step_finished(self.name, context, (finished_at - started_at).total_seconds() * 1000)
        if manifest.budget_status == "exceeded":
            logger.warning(
                "production_budget_exceeded",
                extra={
                    "execution_id": context.execution_id,
                    "total_estimated_cost_usd": manifest.total_estimated_cost_usd,
                    "maximum_video_budget_usd": manifest.maximum_video_budget_usd,
                },
            )
        metrics_artifact = build_step_metrics_artifact(self.name, started_at, finished_at)
        return WorkflowStepResult(
            step_name=self.name,
            status="success",
            data={"asset_manifest": manifest},
            artifacts=[WorkflowArtifact("asset_manifest.json", render_asset_manifest_json(manifest)), metrics_artifact],
        )


def build_youtube_production_workflow(
    *,
    research_workflow_service: ResearchWorkflowService,
    strategy_workflow_service: StrategyWorkflowService,
    writer_workflow_service: WriterWorkflowService,
    review_workflow_service: ReviewWorkflowService,
    visual_identity_service: VisualIdentityService,
    character_reference_image_service: CharacterReferenceImageService,
    media_workflow_service: MediaWorkflowService,
    publishing_package_workflow_service: PublishingPackageWorkflowService,
    voice_generation_service: VoiceGenerationService,
    thumbnail_generation_service: ThumbnailGenerationService,
    scene_planning_service: ScenePlanningService,
    composition_planning_service: CompositionPlanningService,
    scene_image_generation_service: SceneImageGenerationService,
    subtitle_generation_service: SubtitleGenerationService,
    audio_engine_service: AudioEngineService,
    video_assembly_service: VideoAssemblyService,
    asset_packaging_service: AssetPackagingService,
    run_artifact_storage_service: RunArtifactStorageService,
    settings: Settings,
) -> WorkflowDefinition:
    return WorkflowDefinition(
        id=WORKFLOW_ID,
        name=WORKFLOW_NAME,
        steps=[
            ResearchStep(research_workflow_service),
            StrategyStep(strategy_workflow_service),
            WriterStep(writer_workflow_service),
            ReviewStep(review_workflow_service),
            VisualIdentityStep(visual_identity_service, character_reference_image_service),
            MediaStep(media_workflow_service),
            PublishingPackageStep(publishing_package_workflow_service),
            VoiceStep(voice_generation_service),
            ThumbnailStep(thumbnail_generation_service),
            ScenePlanningStep(scene_planning_service),
            CompositionPlanningStep(composition_planning_service),
            SceneImageStep(scene_image_generation_service),
            SubtitleStep(subtitle_generation_service),
            AudioEngineStep(audio_engine_service),
            VideoAssemblyStep(video_assembly_service, run_artifact_storage_service),
            AssetPackagingStep(asset_packaging_service, settings),
        ],
    )
