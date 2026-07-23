from __future__ import annotations

from backend.core.config import Settings
from backend.schemas.assets import Scene
from backend.schemas.shots import AtmosphereOverlayType, CameraMovementType, TransitionType
from backend.services.cinematic_shot_planner import DeterministicShotPlanner


def _scene(scene_number: int, *, camera: str = "", animation: str = "") -> Scene:
    return Scene(scene_number=scene_number, camera=camera, animation=animation)


def test_plan_without_scenes_uses_deterministic_rotation():
    planner = DeterministicShotPlanner(Settings())
    shots = planner.plan(scenes=None, image_count=8, scene_seconds=3.0)

    assert [shot.scene_number for shot in shots] == list(range(1, 9))
    assert [shot.camera_movement for shot in shots] == [
        CameraMovementType.PUSH_IN,
        CameraMovementType.PAN_LEFT,
        CameraMovementType.PAN_RIGHT,
        CameraMovementType.TILT_UP,
        CameraMovementType.TILT_DOWN,
        CameraMovementType.PULL_OUT,
        CameraMovementType.HANDHELD,
        CameraMovementType.CINEMATIC_ZOOM,
    ]
    assert all(shot.duration_seconds == 3.0 for shot in shots)


def test_plan_rotation_is_stable_across_calls():
    planner = DeterministicShotPlanner(Settings())
    first = planner.plan(scenes=None, image_count=4, scene_seconds=2.0)
    second = planner.plan(scenes=None, image_count=4, scene_seconds=2.0)
    assert [shot.camera_movement for shot in first] == [shot.camera_movement for shot in second]


def test_plan_keyword_matches_scene_camera_text():
    scenes = [
        _scene(1, camera="Slow push in on the subject's face"),
        _scene(2, camera="Pan left across the skyline"),
        _scene(3, camera="Camera zooms out to reveal the city"),
        _scene(4, animation="Handheld, slightly shaky"),
    ]
    planner = DeterministicShotPlanner(Settings())
    shots = planner.plan(scenes=scenes, image_count=4, scene_seconds=3.0)

    assert shots[0].camera_movement == CameraMovementType.PUSH_IN
    assert shots[1].camera_movement == CameraMovementType.PAN_LEFT
    assert shots[2].camera_movement == CameraMovementType.PULL_OUT
    assert shots[3].camera_movement == CameraMovementType.HANDHELD


def test_plan_falls_back_to_rotation_when_text_has_no_keyword_match():
    scenes = [_scene(1, camera="A quiet moment in the forest")]
    planner = DeterministicShotPlanner(Settings())
    shots = planner.plan(scenes=scenes, image_count=1, scene_seconds=3.0)
    assert shots[0].camera_movement == CameraMovementType.PUSH_IN


def test_plan_reads_transition_and_atmosphere_from_settings():
    settings = Settings(cinematic_transition_style="fadeblack", cinematic_default_atmosphere_overlay="vignette")
    planner = DeterministicShotPlanner(settings)
    shots = planner.plan(scenes=None, image_count=3, scene_seconds=3.0)

    assert all(shot.transition == TransitionType.FADEBLACK for shot in shots)
    assert all(shot.atmosphere == AtmosphereOverlayType.VIGNETTE for shot in shots)


def test_plan_atmosphere_is_none_by_default():
    planner = DeterministicShotPlanner(Settings())
    shots = planner.plan(scenes=None, image_count=2, scene_seconds=3.0)
    assert all(shot.atmosphere is None for shot in shots)


def test_plan_accepts_and_ignores_composition_plan_kwarg():
    # F27 backward-compatibility: DeterministicShotPlanner gained an additive
    # composition_plan parameter but must behave identically whether it is
    # omitted or passed as None.
    planner = DeterministicShotPlanner(Settings())
    with_default = planner.plan(scenes=None, image_count=4, scene_seconds=3.0)
    with_explicit_none = planner.plan(scenes=None, image_count=4, scene_seconds=3.0, composition_plan=None)

    assert with_default == with_explicit_none
