from __future__ import annotations

import pytest

from backend.schemas.shots import TransitionType
from backend.services.cinematic_transition import build_transition_chain, xfade_name


def test_xfade_name_mapping():
    assert xfade_name(TransitionType.DISSOLVE) == "dissolve"
    assert xfade_name(TransitionType.FADEBLACK) == "fadeblack"


def test_build_transition_chain_computes_cumulative_offsets():
    filter_complex, out_label = build_transition_chain(
        clip_durations=[3.0, 3.0, 3.0],
        transitions=[TransitionType.DISSOLVE, TransitionType.DISSOLVE, TransitionType.FADEBLACK],
        duration_seconds=0.6,
    )
    assert out_label == "vout"
    parts = filter_complex.split(";")
    assert len(parts) == 2
    assert "[0:v][1:v]xfade=transition=dissolve:duration=0.6:offset=2.400[vxf1]" == parts[0]
    assert "[vxf1][2:v]xfade=transition=fadeblack:duration=0.6:offset=4.800[vout]" == parts[1]


def test_build_transition_chain_requires_at_least_two_clips():
    with pytest.raises(ValueError):
        build_transition_chain(clip_durations=[3.0], transitions=[TransitionType.DISSOLVE], duration_seconds=0.6)


def test_build_transition_chain_requires_matching_lengths():
    with pytest.raises(ValueError):
        build_transition_chain(
            clip_durations=[3.0, 3.0],
            transitions=[TransitionType.DISSOLVE],
            duration_seconds=0.6,
        )
