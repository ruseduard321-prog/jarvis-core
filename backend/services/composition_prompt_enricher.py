from __future__ import annotations

from backend.schemas.assets import ScenePlan, ScenePromptSet
from backend.schemas.composition import CompositionPlan, SceneComposition
from backend.schemas.visual_identity import CharacterVisualIdentity, HistoricalVisualContext
from backend.services.photorealistic_prompt_builder import PhotorealisticPromptBuilder


class CompositionPromptEnricher:
    """The single seam where composition/continuity phrases — and, as of F31, the
    Photorealistic Prompt Engine's structured documentary-photography language plus
    Visual Identity's historical/character consistency anchors — are woven onto each
    ScenePrompt.prompt before SceneImageGenerationService ever sees it.
    ImageGenerationProvider and SceneImageGenerationService's own contract are
    unchanged — this only changes the prompt text they receive.

    F28B: when a scene carries visual_beats, its single incoming ScenePrompt is
    expanded into one outgoing ScenePrompt per beat (each describing that beat's own
    visual event), so Scene Image still generates exactly one image per ScenePrompt
    with no change to that service. A scene with no visual_beats produces exactly
    the one enriched prompt it always did — fully backward compatible.

    F31: `scene_plan`, `historical_context`, and `characters` are all optional
    (default None) — omitting them reproduces the exact pre-F31 enrichment shape
    (composition/continuity only), so every existing caller keeps working
    unchanged."""

    def __init__(self, prompt_builder: PhotorealisticPromptBuilder | None = None) -> None:
        self._prompt_builder = prompt_builder or PhotorealisticPromptBuilder()

    def enrich(
        self,
        *,
        scene_prompts: ScenePromptSet,
        composition_plan: CompositionPlan,
        scene_plan: ScenePlan | None = None,
        historical_context: HistoricalVisualContext | None = None,
        characters: list[CharacterVisualIdentity] | None = None,
    ) -> ScenePromptSet:
        by_scene = {composition.scene_number: composition for composition in composition_plan.scenes}
        scenes_by_number = {scene.scene_number: scene for scene in (scene_plan.scenes if scene_plan else [])}
        character_list = characters or []

        enriched_prompts: list = []
        for scene_prompt in scene_prompts.prompts:
            composition = by_scene.get(scene_prompt.scene_number)
            if composition is None:
                enriched_prompts.append(scene_prompt)
                continue

            scene = scenes_by_number.get(scene_prompt.scene_number)
            environment = scene.environment.strip() if scene else ""
            lighting = scene.lighting.strip() if scene else ""
            base = scene_prompt.prompt.strip()

            if not composition.visual_beats:
                new_prompt = self._build_prompt(
                    subject_and_action=base,
                    scene_prompt_mood=scene_prompt.mood,
                    composition=composition,
                    environment=environment,
                    lighting=lighting,
                    historical_context=historical_context,
                    characters=character_list,
                )
                enriched_prompts.append(scene_prompt.model_copy(update={"prompt": new_prompt}))
                continue

            for beat in composition.visual_beats:
                beat_description = beat.description.strip()
                beat_subject = f"{base}. {beat_description}" if base else beat_description
                new_prompt = self._build_prompt(
                    subject_and_action=beat_subject,
                    scene_prompt_mood=scene_prompt.mood,
                    composition=composition,
                    environment=environment,
                    lighting=lighting,
                    historical_context=historical_context,
                    characters=character_list,
                )
                enriched_prompts.append(
                    scene_prompt.model_copy(update={"prompt": new_prompt, "beat_number": beat.beat_number})
                )

        return scene_prompts.model_copy(update={"prompts": enriched_prompts})

    def _build_prompt(
        self,
        *,
        subject_and_action: str,
        scene_prompt_mood: str,
        composition: SceneComposition,
        environment: str,
        lighting: str,
        historical_context: HistoricalVisualContext | None,
        characters: list[CharacterVisualIdentity],
    ) -> str:
        character = self._match_character(characters, f"{subject_and_action} {environment}")
        return self._prompt_builder.build(
            subject_and_action=subject_and_action,
            composition_style=composition.composition_style,
            camera_intent=composition.camera_intent,
            color_language=composition.color_language,
            environment=environment,
            lighting=lighting,
            mood=scene_prompt_mood,
            continuity_tags=composition.continuity_tags,
            historical_context=historical_context,
            character=character,
        )

    def _match_character(
        self, characters: list[CharacterVisualIdentity], text: str
    ) -> CharacterVisualIdentity | None:
        for character in characters:
            if character.matches(text):
                return character
        return None
