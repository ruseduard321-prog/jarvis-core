from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ShotType(str, Enum):
    """Framing/composition category for one rendered scene."""

    WIDE = "wide"
    MEDIUM = "medium"
    CLOSE_UP = "close_up"
    ESTABLISHING = "establishing"
    INSERT = "insert"


class CameraMovementType(str, Enum):
    """Local camera movement applied to a static scene image.

    ORBIT is intentionally not a member: a true orbit needs depth/parallax on a flat
    image, which requires a real depth estimator (see backend/services/depth_estimator.py).
    Add it here once that estimator is wired in — no other change is needed.
    """

    PUSH_IN = "push_in"
    PULL_OUT = "pull_out"
    PAN_LEFT = "pan_left"
    PAN_RIGHT = "pan_right"
    TILT_UP = "tilt_up"
    TILT_DOWN = "tilt_down"
    HANDHELD = "handheld"
    CINEMATIC_ZOOM = "cinematic_zoom"


class TransitionType(str, Enum):
    """Cinematic cut used between two consecutive shots.

    Fade/crossfade/dissolve are visually synonymous cinematic cuts and are deliberately
    collapsed into DISSOLVE — ffmpeg's `xfade` filter doesn't meaningfully distinguish them.
    """

    DISSOLVE = "dissolve"
    FADEBLACK = "fadeblack"


class AtmosphereOverlayType(str, Enum):
    """Optional visual atmosphere overlay. Only applied when explicitly set on a Shot.

    Fog/rain/snow are not yet members — they need particle/asset-based compositing, not a
    one-line ffmpeg filter. Add a member + a matching filter branch in
    cinematic_atmosphere_overlay.py later; no other redesign is needed.
    """

    FILM_GRAIN = "film_grain"
    VIGNETTE = "vignette"
    LIGHT_RAYS = "light_rays"
    DUST_PARTICLES = "dust_particles"


class Shot(BaseModel):
    """The data contract between planning ('what should this scene look like') and
    rendering ('how do we render that'). F25's DeterministicShotPlanner resolves these
    locally/for free; F28 (AI Director) is expected to produce Shots directly from the
    LLM later — the renderer executes Shots either way, unchanged."""

    scene_number: int = Field(description="Matching Scene.scene_number")
    shot_type: ShotType = Field(default=ShotType.MEDIUM, description="Framing/composition category")
    camera_movement: CameraMovementType = Field(
        default=CameraMovementType.PUSH_IN, description="Local camera movement to apply"
    )
    transition: TransitionType = Field(
        default=TransitionType.DISSOLVE,
        description="Cut used to transition INTO this shot from the previous one; ignored for the first shot",
    )
    duration_seconds: float = Field(default=0.0, description="How long this shot holds, in seconds")
    atmosphere: AtmosphereOverlayType | None = Field(
        default=None, description="Optional atmosphere overlay; None means no overlay is applied"
    )
    color_profile: str | None = Field(
        default=None, description="Named color grading preset; None means the default documentary grade"
    )
