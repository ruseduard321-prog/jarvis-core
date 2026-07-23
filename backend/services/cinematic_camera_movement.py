from __future__ import annotations

from collections.abc import Callable

from backend.schemas.shots import CameraMovementType

# Ken-Burns recipe: scale the source well beyond the output size first so zoompan has
# sub-pixel headroom to pan/zoom within without visible jitter, then zoompan animates
# zoom/x/y over the clip's frame count, then crop/scale to the exact output resolution.
_SCALE_FACTOR = 2.0


def _zoompan(*, zoom_expr: str, x_expr: str, y_expr: str, frame_count: int, fps: int, out_w: int, out_h: int) -> str:
    return (
        f"scale=iw*{_SCALE_FACTOR}:ih*{_SCALE_FACTOR},"
        f"zoompan=z='{zoom_expr}':x='{x_expr}':y='{y_expr}':d={frame_count}:s={out_w}x{out_h}:fps={fps}"
    )


def _push_in(frame_count: int, fps: int, out_w: int, out_h: int) -> str:
    return _zoompan(
        zoom_expr="min(zoom+0.0015,1.5)",
        x_expr="iw/2-(iw/zoom/2)",
        y_expr="ih/2-(ih/zoom/2)",
        frame_count=frame_count,
        fps=fps,
        out_w=out_w,
        out_h=out_h,
    )


def _pull_out(frame_count: int, fps: int, out_w: int, out_h: int) -> str:
    return _zoompan(
        zoom_expr="if(eq(on,0),1.5,max(zoom-0.0015,1.0))",
        x_expr="iw/2-(iw/zoom/2)",
        y_expr="ih/2-(ih/zoom/2)",
        frame_count=frame_count,
        fps=fps,
        out_w=out_w,
        out_h=out_h,
    )


def _pan_left(frame_count: int, fps: int, out_w: int, out_h: int) -> str:
    return _zoompan(
        zoom_expr="1.15",
        x_expr=f"(iw-iw/zoom)*(1-on/{max(frame_count - 1, 1)})",
        y_expr="ih/2-(ih/zoom/2)",
        frame_count=frame_count,
        fps=fps,
        out_w=out_w,
        out_h=out_h,
    )


def _pan_right(frame_count: int, fps: int, out_w: int, out_h: int) -> str:
    return _zoompan(
        zoom_expr="1.15",
        x_expr=f"(iw-iw/zoom)*(on/{max(frame_count - 1, 1)})",
        y_expr="ih/2-(ih/zoom/2)",
        frame_count=frame_count,
        fps=fps,
        out_w=out_w,
        out_h=out_h,
    )


def _tilt_up(frame_count: int, fps: int, out_w: int, out_h: int) -> str:
    return _zoompan(
        zoom_expr="1.15",
        x_expr="iw/2-(iw/zoom/2)",
        y_expr=f"(ih-ih/zoom)*(1-on/{max(frame_count - 1, 1)})",
        frame_count=frame_count,
        fps=fps,
        out_w=out_w,
        out_h=out_h,
    )


def _tilt_down(frame_count: int, fps: int, out_w: int, out_h: int) -> str:
    return _zoompan(
        zoom_expr="1.15",
        x_expr="iw/2-(iw/zoom/2)",
        y_expr=f"(ih-ih/zoom)*(on/{max(frame_count - 1, 1)})",
        frame_count=frame_count,
        fps=fps,
        out_w=out_w,
        out_h=out_h,
    )


def _handheld(frame_count: int, fps: int, out_w: int, out_h: int) -> str:
    # Deterministic, continuous sinusoidal jitter — reads as subtle organic movement
    # without needing actual randomness (reproducible, still testable).
    return _zoompan(
        zoom_expr="1.08+0.01*sin(on/9)",
        x_expr="iw/2-(iw/zoom/2)+4*sin(on/5)",
        y_expr="ih/2-(ih/zoom/2)+3*cos(on/7)",
        frame_count=frame_count,
        fps=fps,
        out_w=out_w,
        out_h=out_h,
    )


def _cinematic_zoom(frame_count: int, fps: int, out_w: int, out_h: int) -> str:
    return _zoompan(
        zoom_expr="min(zoom+0.004,1.8)",
        x_expr="iw/2-(iw/zoom/2)",
        y_expr="ih/2-(ih/zoom/2)",
        frame_count=frame_count,
        fps=fps,
        out_w=out_w,
        out_h=out_h,
    )


_BUILDERS: dict[CameraMovementType, Callable[[int, int, int, int], str]] = {
    CameraMovementType.PUSH_IN: _push_in,
    CameraMovementType.PULL_OUT: _pull_out,
    CameraMovementType.PAN_LEFT: _pan_left,
    CameraMovementType.PAN_RIGHT: _pan_right,
    CameraMovementType.TILT_UP: _tilt_up,
    CameraMovementType.TILT_DOWN: _tilt_down,
    CameraMovementType.HANDHELD: _handheld,
    CameraMovementType.CINEMATIC_ZOOM: _cinematic_zoom,
}


def build_camera_movement_filter(
    movement: CameraMovementType, *, frame_count: int, fps: int, out_w: int, out_h: int
) -> str:
    """Returns an ffmpeg -vf filter fragment (scale+zoompan) implementing `movement` over
    `frame_count` output frames at `fps`, targeting `out_w`x`out_h`. Exact numeric constants
    are a reasonable starting point and may need empirical tuning against a real ffmpeg
    build; the technique (scale-up then zoompan) is standard and stable across builds."""
    builder = _BUILDERS[movement]
    return builder(frame_count, fps, out_w, out_h)
