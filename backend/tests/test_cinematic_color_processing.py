from __future__ import annotations

from backend.services.cinematic_color_processing import ColorProcessing


def test_none_profile_returns_default_documentary_grade():
    filter_fragment = ColorProcessing.for_profile(None).build_filter()
    assert "eq=" in filter_fragment
    assert "contrast" in filter_fragment


def test_documentary_profile_matches_default():
    assert ColorProcessing.for_profile("documentary").build_filter() == ColorProcessing.for_profile(None).build_filter()


def test_unknown_profile_falls_back_to_documentary():
    assert ColorProcessing.for_profile("nonexistent").build_filter() == ColorProcessing.for_profile(None).build_filter()
