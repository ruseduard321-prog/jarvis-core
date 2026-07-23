from __future__ import annotations

from pydantic import BaseModel, Field

from backend.schemas.assets import Scene
from backend.schemas.composition import (
    CameraIntent,
    ColorLanguage,
    CompositionStyle,
    ContinuityMotif,
    SceneRelationship,
    ScenePurpose,
    SceneRetention,
    VisualBeat,
)
from backend.schemas.timeline import ScenePacing


class AIDirectorRequest(BaseModel):
    """Everything the AI Director needs to reason over the whole production in one
    pass. Deliberately reuses data the pipeline already produces — no new upstream
    collection step is introduced for F28."""

    topic: str
    genre: str = Field(default="documentary", description="Production genre/style")
    narration_script: str = Field(description="The complete, revised narration script")
    scenes: list[Scene] = Field(description="Full per-scene breakdown; scene_number/count are authoritative and must be preserved")
    total_duration_seconds: float = Field(description="Real measured narration duration to allocate across scenes")
    target_audience: str = Field(default="", description="From StrategyPackage, when available")
    positioning: str = Field(default="", description="From StrategyPackage, when available")
    pacing_guidance: str = Field(default="", description="From StrategyPackage, when available")
    emotional_arc: list[str] = Field(default_factory=list, description="From StrategyPackage, when available")
    # F28B Production Budget Awareness — configured limits the AI Director must
    # reason within when deciding how many visual beats (images) a scene deserves.
    # These are never invented by the model; they always come from Settings,
    # computed once per production by CompositionPlanningService.
    maximum_production_budget_usd: float = Field(default=0.0, description="Hard ceiling for the whole production")
    target_production_budget_usd: float = Field(default=0.0, description="Comfortable target for the whole production")
    estimated_cost_so_far_usd: float = Field(default=0.0, description="Estimated spend already committed by earlier steps")
    remaining_budget_usd: float = Field(default=0.0, description="Budget left over for scene image generation")
    estimated_image_cost_usd: float = Field(default=0.0, description="Estimated USD cost of one generated image, from the provider")
    minimum_visual_beats_per_scene: int = Field(default=1, description="Configured floor; guidance only, never force-padded")
    target_visual_beats_per_scene: int = Field(default=1, description="Configured comfortable average per scene")
    maximum_visual_beats_per_scene: int = Field(default=1, description="Configured hard ceiling per scene, enforced after planning")


class AIDirectorSceneDirection(BaseModel):
    """One scene's complete AI Director output — enough to construct both a
    SceneTiming (TimelinePlan) and a SceneComposition (CompositionPlan) with no
    heuristic reconstruction, just direct field mapping plus normalization
    (see ai_director_plan_builder.py)."""

    scene_number: int
    duration_seconds: float = Field(description="Intended relative screen time; rescaled to the exact measured total")
    pacing: ScenePacing
    purpose: ScenePurpose
    composition_style: CompositionStyle
    camera_intent: CameraIntent
    color_language: ColorLanguage = ColorLanguage.NEUTRAL
    continuity_tags: list[str] = Field(default_factory=list)
    relationships: list[SceneRelationship] = Field(default_factory=list)
    emphasis_note: str = Field(default="", description="Short directorial rationale for this scene")
    visual_beats: list[VisualBeat] = Field(
        default_factory=list,
        description=(
            "One or more meaningful visual events within this scene, each producing its "
            "own image (F28B). Empty is valid and means a single image for the scene, "
            "identical to pre-F28B behavior."
        ),
    )
    retention: SceneRetention | None = Field(
        default=None,
        description=(
            "F29 Viewer Retention Engine guidance for this scene. Optional — omitting it "
            "is valid and means no retention optimization for this scene."
        ),
    )


class AIDirectorPlan(BaseModel):
    """Raw structured output from the AI Director for one production: the single
    creative reasoning pass over the entire script, covering every scene plus any
    recurring visual motifs. Adapted into TimelinePlan/CompositionPlan by
    ai_director_plan_builder.py, which validates and normalizes but never
    reinterprets the AI's creative decisions."""

    scenes: list[AIDirectorSceneDirection]
    motifs: list[ContinuityMotif] = Field(default_factory=list)
