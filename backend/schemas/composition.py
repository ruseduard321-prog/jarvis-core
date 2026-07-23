from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

from backend.schemas.timeline import SceneTiming


class ScenePurpose(str, Enum):
    """The narrative role a scene plays. Deliberately genre-agnostic — no
    mystery-specific or topic-specific values. New roles are new enum members;
    nothing else in the architecture changes."""

    INTRODUCTION = "introduction"
    CONTEXT = "context"
    DISCOVERY = "discovery"
    CONFLICT = "conflict"
    ESCALATION = "escalation"
    REVEAL = "reveal"
    RESOLUTION = "resolution"


class CompositionStyle(str, Enum):
    """Reusable framing/coverage concept, independent of (but mapped onto)
    Shot.ShotType by CompositionAwareShotPlanner."""

    ESTABLISHING_SHOT = "establishing_shot"
    WIDE_SHOT = "wide_shot"
    CLOSE_UP = "close_up"
    DETAIL_SHOT = "detail_shot"
    REVEAL_SHOT = "reveal_shot"
    COMPARISON_SHOT = "comparison_shot"
    REACTION_SHOT = "reaction_shot"
    TRANSITION_SHOT = "transition_shot"


class CameraIntent(str, Enum):
    """WHY the camera moves. F25 already decided HOW (CameraMovementType); this is
    the missing WHY layer. CompositionAwareShotPlanner maps CameraIntent to a
    CameraMovementType; RendererPipeline never sees this enum."""

    SLOW_REVEAL = "slow_reveal"
    DRAMATIC_ZOOM = "dramatic_zoom"
    INVESTIGATION = "investigation"
    SUSPENSE = "suspense"
    EMOTIONAL_FOCUS = "emotional_focus"
    NEUTRAL_OBSERVATION = "neutral_observation"


class SceneRelationType(str, Enum):
    """How a scene relates to an earlier scene it references."""

    CONTINUATION = "continuation"
    CONTRAST = "contrast"
    CALLBACK = "callback"
    ESCALATION = "escalation"
    REPETITION = "repetition"


class ImportanceLevel(str, Enum):
    """Shared narrative-importance scale (F29). Used both as a scene's overall
    retention_priority and as a single beat's beat_importance — one taxonomy
    instead of two near-identical ones, since both answer the same underlying
    question ('how much does this moment matter'), just at different
    granularity."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class InformationDensity(str, Enum):
    """How much new information a scene conveys (F29). Guidance only — the AI
    Director uses it (per the prompt) to justify shorter visual persistence and
    stronger transitions on dense scenes; it never changes narration."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TransitionEnergy(str, Enum):
    """Planning-only transition guidance (F29) — describes the FEEL of the cut
    into a scene. CompositionAwareShotPlanner maps this onto the renderer's
    existing TransitionType (dissolve/fadeblack); RendererPipeline never sees
    this enum, exactly like CameraIntent's relationship to CameraMovementType."""

    SEAMLESS = "seamless"
    ENERGETIC = "energetic"
    SUSPENSE = "suspense"
    CALM = "calm"
    DRAMATIC = "dramatic"
    EMOTIONAL = "emotional"


class ColorLanguage(str, Enum):
    """Reserved emotional/temporal color intent. Resolves to Shot.color_profile;
    only one preset ("documentary") exists today in ColorProcessing, so every value
    below currently renders identically — the field is a real seam, the palette
    behind it is future work (advanced color grading is explicitly out of scope
    for F27)."""

    NEUTRAL = "neutral"
    WARM_PROGRESSION = "warm_progression"
    COLD_PROGRESSION = "cold_progression"
    TENSION = "tension"


class SceneRelationship(BaseModel):
    """One directed link from this scene back to an earlier one."""

    relation_type: SceneRelationType
    reference_scene_number: int = Field(description="The earlier scene this relationship points to")
    note: str = Field(default="", description="Human-readable rationale")


class ContinuityMotif(BaseModel):
    """One recurring visual thread — the concrete mechanism behind 'recurring
    colors/objects/locations/framing/atmosphere'. established_scene_number is
    where it first appears; recurring_scene_numbers are every later scene
    instructed to keep it visible."""

    motif_type: Literal["object", "location", "atmosphere"]
    description: str = Field(description="The recurring word/phrase this motif tracks, e.g. 'attic'")
    established_scene_number: int
    recurring_scene_numbers: list[int] = Field(default_factory=list)


class VisualBeat(BaseModel):
    """One meaningful visual event inside a scene (F28B). Purely a visual-storytelling
    concept: it describes WHAT the image should show, never WHEN — TimelinePlan's
    SceneTiming remains the only timing authority, and a scene's total duration is
    distributed across however many beats it has (F29: importance-weighted, see
    CompositionAwareShotPlanner), never changed. Each beat generates exactly one
    image."""

    beat_number: int = Field(description="1-based order within the scene")
    description: str = Field(description="Visual storytelling description driving this beat's image prompt")
    emphasis_note: str = Field(default="", description="Short directorial rationale for why this beat exists")
    beat_importance: ImportanceLevel = Field(
        default=ImportanceLevel.NORMAL,
        description=(
            "F29: this beat's narrative importance — NOT duration. Drives how much of the "
            "scene's fixed total duration this beat's image is held on screen relative to "
            "its siblings; a scene where every beat is NORMAL splits evenly, identical to "
            "pre-F29 behavior."
        ),
    )


class SceneRetention(BaseModel):
    """Viewer Retention Engine metadata (F29) for one scene. Purely descriptive
    guidance the AI Director attaches alongside its existing creative decisions —
    it never times anything (TimelinePlan.SceneTiming is untouched) and is
    optional: absence (None) means this scene carries no retention guidance,
    which is exactly the deterministic-fallback and pre-F29 state."""

    retention_priority: ImportanceLevel = Field(
        default=ImportanceLevel.NORMAL, description="How much this scene matters for viewer retention"
    )
    curiosity_level: float = Field(default=0.5, ge=0.0, le=1.0, description="How much open curiosity this scene should generate")
    emotional_intensity: float = Field(default=0.5, ge=0.0, le=1.0, description="This scene's position on the production's emotional curve")
    information_density: InformationDensity = Field(
        default=InformationDensity.MEDIUM, description="How much new information this scene conveys"
    )
    visual_change_frequency: float = Field(
        default=0.5, ge=0.0, le=1.0, description="How often the visuals should change to avoid a static period; guidance only"
    )
    reveal_strength: float = Field(default=0.0, ge=0.0, le=1.0, description="How much this scene reveals/pays off a prior curiosity loop")
    transition_energy: TransitionEnergy = Field(
        default=TransitionEnergy.SEAMLESS, description="The FEEL of the cut into this scene; mapped onto TransitionType by the shot planner"
    )


class SceneComposition(BaseModel):
    """Everything CompositionPlanner decided for one scene's look. Keyed by
    scene_number — the same key Shot and AudioTimeline's scene-linked entries use.
    `timing` is copied verbatim from TimelinePlan.timing_for(scene_number) —
    CompositionPlan never computes a duration, start time, or pacing value
    itself."""

    scene_number: int
    timing: SceneTiming = Field(description="Copied verbatim from TimelinePlan — never recalculated here")
    purpose: ScenePurpose
    composition_style: CompositionStyle
    camera_intent: CameraIntent
    color_language: ColorLanguage = ColorLanguage.NEUTRAL
    relationships: list[SceneRelationship] = Field(default_factory=list)
    continuity_tags: list[str] = Field(default_factory=list, description="Motif descriptions active in this scene")
    emphasis_note: str = Field(default="", description="Short human-readable directorial rationale")
    visual_beats: list[VisualBeat] = Field(
        default_factory=list,
        description=(
            "Visual beats within this scene (F28B), each generating its own image. "
            "Empty means the scene renders as a single image — the pre-F28B behavior — "
            "so every consumer must treat an empty list as exactly one implicit beat."
        ),
    )
    retention: SceneRetention | None = Field(
        default=None,
        description=(
            "F29 Viewer Retention Engine guidance. None means no retention metadata is "
            "available (deterministic fallback, or an AI Director response that omitted "
            "it) — every consumer must treat that as 'no optimization beyond F28B'."
        ),
    )


class CompositionPlan(BaseModel):
    """The data contract between scene-level planning ('what is this video's visual
    story') and Shot/prompt production ('render/prompt for that'). This is
    TimelinePlan's and Shot's/AudioTimeline's sibling: CompositionPlanner resolves
    it deterministically today, consuming TimelinePlan for all timing and never
    calculating timing itself; F28's AI Director is expected to produce
    CompositionPlans directly later. CompositionAwareShotPlanner and
    CompositionPromptEnricher execute whatever plan they're given and never invent
    a directorial decision themselves — the same discipline RendererPipeline and
    AudioMixerService already apply to Shot/AudioTimeline."""

    topic: str
    timeline_total_duration_seconds: float = Field(
        default=0.0, description="Copied from TimelinePlan.total_duration_seconds, for observability only"
    )
    scenes: list[SceneComposition] = Field(default_factory=list)
    motifs: list[ContinuityMotif] = Field(default_factory=list)
    metadata: dict[str, object] = Field(default_factory=dict, description="Execution metadata including status")
