from __future__ import annotations

import logging
from datetime import datetime, timezone

from backend.core.config import Settings
from backend.core.cost_tracker import BudgetTracker, CostTracker
from backend.schemas.assets import ScenePrompt, ScenePromptSet, SceneImageAsset, SceneImageSet
from backend.schemas.visual_identity import CharacterVisualIdentity
from backend.services.image_generation_pipeline import (
    ImageBudgetExceededError,
    ImageGenerationFailedError,
    ImageGenerationPipeline,
)
from backend.services.image_generation_provider import ImageGenerationProvider
from backend.services.image_validation_service import ImageValidationService

logger = logging.getLogger(__name__)


class WorkflowSafetyError(Exception):
    """Raised when a workflow step would exceed a hard, non-negotiable production
    cost ceiling.

    This is deliberately NOT one of the provider exceptions above: those model a
    single call failing and are designed to be caught and turned into a FAILED
    asset so the pipeline continues. This models the opposite situation — the
    request itself is unsafe to make at all (a prompt/workflow bug asking for far
    more paid calls than any real video needs) — so it must propagate and stop
    the run before the first request goes out, not be swallowed into a per-item
    failure record.
    """


class SceneImageGenerationService:
    """Generates one real image per scene (or, when a scene carries F28B visual
    beats, one image per beat) from the Composition Planning step's per-scene
    prompts, reusing the same image provider (and its built-in retry/cost/metrics
    behavior) as the Thumbnail step. Never raises for individual failures —
    provider failures are captured as a FAILED SceneImageAsset per prompt so the
    workflow continues — but DOES raise WorkflowSafetyError if the incoming
    request count itself is unsafe (see execute() below).

    F31.5: generation, validation, and any regeneration all run through the
    shared ImageGenerationPipeline (see image_generation_pipeline.py), which is
    budget-aware — once the production's remaining budget is exhausted, further
    images are gracefully SKIPPED (not FAILED, not silently over-spent) rather
    than generated regardless."""

    def __init__(
        self,
        image_generation_provider: ImageGenerationProvider,
        settings: Settings,
        image_validation_service: ImageValidationService | None = None,
    ) -> None:
        self._settings = settings
        self._cost_tracker = CostTracker()
        self._pipeline = ImageGenerationPipeline(
            provider=image_generation_provider, validation_service=image_validation_service, cost_tracker=self._cost_tracker
        )

    async def execute(
        self,
        scene_prompts: ScenePromptSet,
        *,
        characters: list[CharacterVisualIdentity] | None = None,
        reference_images: dict[str, bytes] | None = None,
        estimated_cost_so_far_usd: float = 0.0,
    ) -> tuple[SceneImageSet, dict[str, bytes]]:
        if not scene_prompts.prompts:
            return (
                SceneImageSet(
                    topic=scene_prompts.topic,
                    images=[],
                    metadata={"status": "skipped", "reason": "No scene prompts were produced by the Scene Planning step"},
                ),
                {},
            )

        # Two-tier cost-protection safety net. Final layer, independent of
        # upstream planning: this loop must never trust an upstream count,
        # whether that count comes from ScenePlanningService, the F28B AI
        # Director's visual-beat expansion, or a bug in either — because each
        # iteration below is one billed gpt-image-1 call, and image generation is
        # the largest API expense in this pipeline. LLM output is never trusted
        # to self-limit; the app decides how many images get made, not the model.
        # The ceilings are scaled by maximum_visual_beats_per_scene so a
        # beat-expanded plan (still bounded by its own budget-aware validation in
        # ai_director_plan_builder.enforce_visual_beat_budget) isn't silently
        # truncated back to one image per scene.
        #
        #   count <= max_images                  -> used as-is, no action
        #   max_images < count <= hard_limit      -> ordinary LLM overshoot:
        #                                            trim to max_images and log a
        #                                            warning
        #   count > hard_limit                    -> not ordinary overshoot, almost
        #                                            certainly a prompt/workflow
        #                                            bug: abort with
        #                                            WorkflowSafetyError before the
        #                                            first paid request, rather
        #                                            than trimming and spending
        #                                            money on a broken run
        #
        # F3/F31.5: this count-based ceiling is unchanged and still enforced
        # first — it protects against a runaway *count*. The BudgetTracker below
        # additionally protects against a runaway *dollar total* even when the
        # count itself is reasonable (e.g. every image landing on the expensive
        # end of a variable-cost provider).
        prompts = scene_prompts.prompts
        requested = len(prompts)
        beats_per_scene = max(1, self._settings.maximum_visual_beats_per_scene)
        max_images = self._settings.max_scenes_per_video * beats_per_scene
        hard_limit = self._settings.max_scene_hard_limit * beats_per_scene

        if requested > hard_limit:
            raise WorkflowSafetyError(
                "Image generation aborted.\n\n"
                f"Requested:\n{requested} images\n\n"
                f"Maximum allowed:\n{hard_limit}\n\n"
                "Possible prompt or workflow bug."
            )

        if requested > max_images:
            logger.warning(
                "Composition Planning requested %d images. Maximum allowed: %d. Using first %d.",
                requested,
                max_images,
                max_images,
                extra={
                    "topic": scene_prompts.topic,
                    "scene_prompt_count": requested,
                    "max_images": max_images,
                    "hard_limit": hard_limit,
                },
            )
            prompts = prompts[:max_images]

        budget = self._cost_tracker.build_budget_tracker(
            maximum_budget_usd=self._settings.maximum_video_budget_usd,
            estimated_cost_so_far_usd=estimated_cost_so_far_usd,
        )

        images: list[SceneImageAsset] = []
        image_bytes_by_filename: dict[str, bytes] = {}
        for scene_prompt in prompts:
            asset, image_bytes = await self._generate_one(
                scene_prompt, characters=characters or [], reference_images=reference_images or {}, budget=budget
            )
            images.append(asset)
            if image_bytes is not None:
                image_bytes_by_filename[asset.filename] = image_bytes

        failures = [image for image in images if image.status != "SUCCESS"]
        if not failures:
            status = "success"
        elif len(failures) == len(images):
            status = "failed"
        else:
            status = "partial"
        return (
            SceneImageSet(topic=scene_prompts.topic, images=images, metadata={"status": status}),
            image_bytes_by_filename,
        )

    async def _generate_one(
        self,
        scene_prompt: ScenePrompt,
        *,
        characters: list[CharacterVisualIdentity],
        reference_images: dict[str, bytes],
        budget: BudgetTracker,
    ) -> tuple[SceneImageAsset, bytes | None]:
        prompt = scene_prompt.prompt.strip()
        if not prompt:
            return self._skipped(scene_prompt, "No visual prompt was produced for this scene"), None

        character = self._match_character(characters, prompt)
        reference_image = (
            reference_images.get(character.reference_image_filename)
            if character is not None and character.reference_image_filename
            else None
        )

        try:
            result = await self._pipeline.run(
                prompt=prompt,
                size=self._settings.openai_image_size,
                quality=self._settings.openai_image_quality,
                model=self._settings.openai_image_model,
                reference_image=reference_image,
                budget=budget,
                max_retries=self._settings.image_validation_max_retries,
                validation_context=prompt,
            )
        except ImageBudgetExceededError as exc:
            logger.warning(
                "scene_image_generation_skipped_budget_exhausted",
                extra={"scene_number": scene_prompt.scene_number, "beat_number": scene_prompt.beat_number, "reason": str(exc)},
            )
            return self._skipped(scene_prompt, f"Skipped: production budget exhausted ({exc})"), None
        except ImageGenerationFailedError as exc:
            logger.warning(
                "scene_image_generation_failed",
                extra={"scene_number": scene_prompt.scene_number, "beat_number": scene_prompt.beat_number, "reason": str(exc)},
            )
            return self._failed(scene_prompt, str(exc)), None

        media_asset = result.media_asset
        resolution = f"{media_asset.width}x{media_asset.height}" if media_asset.width and media_asset.height else ""
        asset = SceneImageAsset(
            scene_number=scene_prompt.scene_number,
            beat_number=scene_prompt.beat_number,
            provider=media_asset.provider,
            model=str(media_asset.metadata.get("model", "")),
            resolution=resolution,
            prompt=prompt,
            generation_time=datetime.now(timezone.utc).isoformat(),
            filename=self._filename_for(scene_prompt),
            status="SUCCESS",
            generation_duration_ms=float(media_asset.metadata.get("generation_duration_ms", 0.0)),
            retry_count=int(media_asset.metadata.get("retry_count", 0)),
            estimated_cost_usd=result.total_cost_usd,
            validation_status="valid" if result.validation.valid else "invalid",
            validation_issues=result.validation.issues,
            character_name=character.name if character is not None else "",
        )
        return asset, result.image_bytes

    def _match_character(
        self, characters: list[CharacterVisualIdentity], text: str
    ) -> CharacterVisualIdentity | None:
        for character in characters:
            if character.matches(text):
                return character
        return None

    def _filename_for(self, scene_prompt: ScenePrompt) -> str:
        # Beat suffix only when beats are actually in play — an unbeated scene
        # keeps the exact pre-F28B filename, and duplicate beat_number=0 entries
        # for the same scene_number cannot occur (each scene contributes at most
        # one such entry).
        if scene_prompt.beat_number:
            return f"scene_{scene_prompt.scene_number:02d}_beat_{scene_prompt.beat_number:02d}.png"
        return f"scene_{scene_prompt.scene_number:02d}.png"

    def _skipped(self, scene_prompt: ScenePrompt, reason: str) -> SceneImageAsset:
        return SceneImageAsset(
            scene_number=scene_prompt.scene_number,
            beat_number=scene_prompt.beat_number,
            provider="none",
            generation_time=datetime.now(timezone.utc).isoformat(),
            status="SKIPPED",
            error=reason,
        )

    def _failed(self, scene_prompt: ScenePrompt, reason: str) -> SceneImageAsset:
        return SceneImageAsset(
            scene_number=scene_prompt.scene_number,
            beat_number=scene_prompt.beat_number,
            provider="none",
            generation_time=datetime.now(timezone.utc).isoformat(),
            status="FAILED",
            error=reason,
        )
