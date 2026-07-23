from __future__ import annotations

from backend.schemas.shots import CameraMovementType
from backend.services.cinematic_camera_movement import build_camera_movement_filter


def test_build_camera_movement_filter_shape_for_every_movement():
    for movement in CameraMovementType:
        filter_fragment = build_camera_movement_filter(movement, frame_count=72, fps=24, out_w=1920, out_h=1080)
        assert "zoompan=" in filter_fragment
        assert "d=72" in filter_fragment
        assert "s=1920x1080" in filter_fragment
        assert "fps=24" in filter_fragment
        assert filter_fragment.startswith("scale=")


def test_pan_left_and_pan_right_produce_opposite_x_direction():
    left = build_camera_movement_filter(CameraMovementType.PAN_LEFT, frame_count=48, fps=24, out_w=1280, out_h=720)
    right = build_camera_movement_filter(CameraMovementType.PAN_RIGHT, frame_count=48, fps=24, out_w=1280, out_h=720)
    assert left != right
    assert "1-on/" in left
    assert "(on/" in right


def test_tilt_up_and_tilt_down_vary_y_not_x():
    up = build_camera_movement_filter(CameraMovementType.TILT_UP, frame_count=48, fps=24, out_w=1280, out_h=720)
    down = build_camera_movement_filter(CameraMovementType.TILT_DOWN, frame_count=48, fps=24, out_w=1280, out_h=720)
    assert up != down
    assert "x='iw/2-(iw/zoom/2)'" in up
    assert "x='iw/2-(iw/zoom/2)'" in down


def test_push_in_and_pull_out_are_distinct():
    push = build_camera_movement_filter(CameraMovementType.PUSH_IN, frame_count=48, fps=24, out_w=1280, out_h=720)
    pull = build_camera_movement_filter(CameraMovementType.PULL_OUT, frame_count=48, fps=24, out_w=1280, out_h=720)
    assert push != pull


def test_handheld_uses_sinusoidal_jitter():
    filter_fragment = build_camera_movement_filter(
        CameraMovementType.HANDHELD, frame_count=48, fps=24, out_w=1280, out_h=720
    )
    assert "sin(" in filter_fragment
    assert "cos(" in filter_fragment


def test_frame_count_of_one_does_not_crash_pan_expressions():
    filter_fragment = build_camera_movement_filter(CameraMovementType.PAN_LEFT, frame_count=1, fps=24, out_w=640, out_h=360)
    assert "/0" not in filter_fragment
