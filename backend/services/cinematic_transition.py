from __future__ import annotations

from backend.schemas.shots import TransitionType

_XFADE_NAMES: dict[TransitionType, str] = {
    TransitionType.DISSOLVE: "dissolve",
    TransitionType.FADEBLACK: "fadeblack",
}


def xfade_name(transition: TransitionType) -> str:
    return _XFADE_NAMES[transition]


def build_transition_chain(
    *,
    clip_durations: list[float],
    transitions: list[TransitionType],
    duration_seconds: float,
    input_label: str = "v",
) -> tuple[str, str]:
    """Builds an ffmpeg filter_complex fragment chaining `[0:v][1:v]...` per-scene clip
    inputs into one continuous video stream via sequential `xfade` transitions.

    `transitions[i]` is the cut used to transition INTO clip `i` from clip `i-1`
    (`transitions[0]` is ignored — there's nothing before the first clip).

    Returns (filter_complex_fragment, output_label). Raises ValueError if fewer than 2
    clips are given (nothing to transition between); callers should map a single clip
    straight through without calling this.
    """
    clip_count = len(clip_durations)
    if clip_count != len(transitions):
        raise ValueError("clip_durations and transitions must be the same length")
    if clip_count < 2:
        raise ValueError("build_transition_chain requires at least 2 clips")

    parts: list[str] = []
    prev_label = f"0:{input_label}"
    cumulative_duration = clip_durations[0]
    for i in range(1, clip_count):
        transition_name = xfade_name(transitions[i])
        offset = max(cumulative_duration - duration_seconds * i, 0.0)
        out_label = f"vxf{i}" if i < clip_count - 1 else "vout"
        parts.append(
            f"[{prev_label}][{i}:{input_label}]xfade=transition={transition_name}:"
            f"duration={duration_seconds}:offset={offset:.3f}[{out_label}]"
        )
        prev_label = out_label
        cumulative_duration += clip_durations[i]

    return ";".join(parts), "vout"
