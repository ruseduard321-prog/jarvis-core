from __future__ import annotations

import pytest

from backend.core.cost_tracker import BudgetTracker, CostTracker


def test_estimate_text_cost_uses_known_model_pricing():
    tracker = CostTracker()

    estimate = tracker.estimate_text_cost(
        provider="openai",
        model="gpt-5.5",
        input_text="a" * 400,
        output_text="b" * 800,
    )

    assert estimate.provider == "openai"
    assert estimate.model == "gpt-5.5"
    assert estimate.estimated_input_tokens == 100
    assert estimate.estimated_output_tokens == 200
    assert estimate.estimated_cost_usd == round((100 / 1000) * 0.005 + (200 / 1000) * 0.015, 6)


def test_estimate_text_cost_falls_back_to_default_pricing_for_unknown_model():
    tracker = CostTracker()

    estimate = tracker.estimate_text_cost(
        provider="openai", model="some-future-model", input_text="a" * 40, output_text=""
    )

    assert estimate.estimated_output_tokens == 0
    assert estimate.estimated_cost_usd == round((10 / 1000) * 0.005, 6)


def test_estimate_text_cost_empty_text_yields_zero_tokens():
    tracker = CostTracker()

    estimate = tracker.estimate_text_cost(provider="openai", model="gpt-5.5", input_text="", output_text="")

    assert estimate.estimated_input_tokens == 0
    assert estimate.estimated_output_tokens == 0
    assert estimate.estimated_cost_usd == 0.0


def test_estimate_tts_cost_uses_per_character_pricing():
    tracker = CostTracker()

    estimate = tracker.estimate_tts_cost(provider="openai", model="tts-1-hd", char_count=2000)

    assert estimate.estimated_input_tokens == 2000
    assert estimate.estimated_output_tokens == 0
    assert estimate.estimated_cost_usd == round((2000 / 1000) * 0.030, 6)


def test_estimate_tts_cost_uses_gpt4o_mini_tts_pricing():
    tracker = CostTracker()

    estimate = tracker.estimate_tts_cost(provider="openai", model="gpt-4o-mini-tts", char_count=1000)

    assert estimate.estimated_cost_usd == round(1.0 * 0.0167, 6)


def test_estimate_tts_cost_falls_back_to_default_pricing_for_unknown_model():
    tracker = CostTracker()

    estimate = tracker.estimate_tts_cost(provider="openai", model="future-tts", char_count=1000)

    assert estimate.estimated_cost_usd == round(1.0 * 0.015, 6)


def test_estimate_image_cost_uses_quality_and_size_key():
    tracker = CostTracker()

    estimate = tracker.estimate_image_cost(provider="openai", model="gpt-image-1", size="1024x1024", quality="high")

    assert estimate.estimated_cost_usd == 0.167
    assert estimate.estimated_input_tokens == 0
    assert estimate.estimated_output_tokens == 0


def test_estimate_image_cost_falls_back_to_default_for_unknown_quality_size_pair():
    tracker = CostTracker()

    estimate = tracker.estimate_image_cost(provider="openai", model="gpt-image-1", size="2048x2048", quality="ultra")

    assert estimate.estimated_cost_usd == 0.042


def test_estimate_image_cost_falls_back_to_default_for_unknown_model():
    tracker = CostTracker()

    estimate = tracker.estimate_image_cost(provider="openai", model="future-image-model", size="1024x1024", quality="high")

    assert estimate.estimated_cost_usd == 0.042


def test_total_sums_and_rounds_cost_estimates():
    tracker = CostTracker()
    estimates = [
        tracker.estimate_text_cost(provider="openai", model="gpt-5.5", input_text="a" * 40, output_text="b" * 40),
        tracker.estimate_tts_cost(provider="openai", model="tts-1", char_count=1000),
    ]

    total = tracker.total(estimates)

    assert total == round(sum(e.estimated_cost_usd for e in estimates), 6)


def test_total_of_empty_list_is_zero():
    tracker = CostTracker()

    assert tracker.total([]) == 0.0


def test_estimate_image_validation_cost_is_deterministic_and_model_aware():
    tracker = CostTracker()

    estimate = tracker.estimate_image_validation_cost(model="gpt-5.5")

    # 150 (prompt) + 850 (image surcharge) input tokens, 60 output tokens.
    assert estimate.estimated_input_tokens == 1000
    assert estimate.estimated_output_tokens == 60
    assert estimate.estimated_cost_usd == round((1000 / 1000) * 0.005 + (60 / 1000) * 0.015, 6)


def test_estimate_image_validation_cost_falls_back_to_default_pricing_for_unknown_model():
    tracker = CostTracker()

    estimate = tracker.estimate_image_validation_cost(model="some-future-model")

    assert estimate.estimated_cost_usd == round((1000 / 1000) * 0.005 + (60 / 1000) * 0.015, 6)


def test_build_budget_tracker_seeds_remaining_from_ceiling_minus_spent():
    tracker = CostTracker()

    budget = tracker.build_budget_tracker(maximum_budget_usd=5.0, estimated_cost_so_far_usd=1.5)

    assert isinstance(budget, BudgetTracker)
    assert budget.remaining_usd == 3.5


def test_build_budget_tracker_clamps_to_zero_when_already_over_budget():
    tracker = CostTracker()

    budget = tracker.build_budget_tracker(maximum_budget_usd=5.0, estimated_cost_so_far_usd=7.0)

    assert budget.remaining_usd == 0.0


def test_budget_tracker_can_afford_reflects_remaining_headroom():
    budget = BudgetTracker(remaining_usd=0.05)

    assert budget.can_afford(0.05) is True
    assert budget.can_afford(0.0500001) is False


def test_budget_tracker_record_spend_decrements_and_never_goes_negative():
    budget = BudgetTracker(remaining_usd=0.10)

    budget.record_spend(0.04)
    assert budget.remaining_usd == pytest.approx(0.06)

    budget.record_spend(1.0)
    assert budget.remaining_usd == 0.0
