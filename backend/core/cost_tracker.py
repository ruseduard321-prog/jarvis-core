"""Estimated cost tracking for AI provider calls.

Pricing is approximate and intentionally isolated in `PRICING_TABLE` so it can be
updated without touching estimation logic. Token counts are estimated with a
`len(text) / 4` heuristic (no tokenizer dependency) since exact usage is not
always available from every provider response.
"""

from __future__ import annotations

from dataclasses import dataclass

_CHARS_PER_TOKEN = 4.0

# USD per 1K units. Text models: per 1K tokens (input/output). TTS: per 1K
# characters. Image models: flat per-image rate keyed by "quality:size".
PRICING_TABLE: dict[str, dict[str, object]] = {
    "gpt-5.5": {"input_per_1k": 0.005, "output_per_1k": 0.015},
    "tts-1": {"per_1k_chars": 0.015},
    "tts-1-hd": {"per_1k_chars": 0.030},
    # gpt-4o-mini-tts is billed per audio-minute (~$0.015/min) rather than per
    # character. Converted to this table's per-1k-chars shape at ~150 words/min
    # (~900 chars/min of English narration) so CostTracker's existing per-call
    # estimation logic needs no redesign: $0.015 / 900 chars * 1000 ≈ $0.0167/1k chars.
    "gpt-4o-mini-tts": {"per_1k_chars": 0.0167},
    "gpt-image-1": {
        "per_image": {
            "low:1024x1024": 0.011,
            "medium:1024x1024": 0.042,
            "high:1024x1024": 0.167,
            # F31: landscape (1536x1024/1024x1536) options cost more than square at
            # the same quality tier — larger canvas, more pixels billed.
            "low:1536x1024": 0.016,
            "medium:1536x1024": 0.063,
            "high:1536x1024": 0.25,
            "low:1024x1536": 0.016,
            "medium:1024x1536": 0.063,
            "high:1024x1536": 0.25,
        }
    },
}

_DEFAULT_TEXT_PRICING = {"input_per_1k": 0.005, "output_per_1k": 0.015}
_DEFAULT_TTS_PRICING = {"per_1k_chars": 0.015}
_DEFAULT_IMAGE_COST = 0.042

# F31.5 Image Validation cost estimate: a short text prompt plus one embedded image.
# Vision tokens aren't linear in the base64 payload's character length, so this uses
# a fixed per-image token surcharge (~850 tokens, OpenAI's commonly-cited approximate
# cost for one standard-detail image) on top of a short, roughly constant prompt/
# response size — kept in the same `len/4`-heuristic family as every other estimate
# in this module rather than inventing a second pricing model.
_VALIDATION_PROMPT_TOKEN_ESTIMATE = 150
_VALIDATION_IMAGE_TOKEN_ESTIMATE = 850
_VALIDATION_OUTPUT_TOKEN_ESTIMATE = 60


@dataclass
class CostEstimate:
    provider: str
    model: str
    estimated_input_tokens: int
    estimated_output_tokens: int
    estimated_cost_usd: float


@dataclass
class BudgetTracker:
    """F31.5 runtime budget enforcement. Tracks real remaining USD headroom within
    one production run, seeded from cost already committed by earlier workflow
    steps (`context.cost_ledger`, see `WorkflowRunContext`). Every paid call in the
    image pipeline (generation, validation, regeneration, character reference
    portraits) must check `can_afford()` before spending and call `record_spend()`
    after — this is what turns `Settings.maximum_video_budget_usd` from prompt-only
    guidance (see `AIDirectorRequest`) into an actual enforced runtime ceiling."""

    remaining_usd: float

    def can_afford(self, estimated_cost_usd: float) -> bool:
        return estimated_cost_usd <= self.remaining_usd

    def record_spend(self, actual_cost_usd: float) -> None:
        self.remaining_usd = max(0.0, self.remaining_usd - actual_cost_usd)


class CostTracker:
    """Stateless USD cost estimation for text, TTS, and image provider calls."""

    def estimate_text_cost(self, *, provider: str, model: str, input_text: str, output_text: str) -> CostEstimate:
        pricing = PRICING_TABLE.get(model, _DEFAULT_TEXT_PRICING)
        input_tokens = self._estimate_tokens(input_text)
        output_tokens = self._estimate_tokens(output_text)
        cost = (input_tokens / 1000.0) * float(pricing["input_per_1k"]) + (output_tokens / 1000.0) * float(
            pricing["output_per_1k"]
        )
        return CostEstimate(
            provider=provider,
            model=model,
            estimated_input_tokens=input_tokens,
            estimated_output_tokens=output_tokens,
            estimated_cost_usd=round(cost, 6),
        )

    def estimate_tts_cost(self, *, provider: str, model: str, char_count: int) -> CostEstimate:
        pricing = PRICING_TABLE.get(model, _DEFAULT_TTS_PRICING)
        cost = (char_count / 1000.0) * float(pricing.get("per_1k_chars", _DEFAULT_TTS_PRICING["per_1k_chars"]))
        return CostEstimate(
            provider=provider,
            model=model,
            estimated_input_tokens=char_count,
            estimated_output_tokens=0,
            estimated_cost_usd=round(cost, 6),
        )

    def estimate_image_cost(self, *, provider: str, model: str, size: str, quality: str) -> CostEstimate:
        pricing = PRICING_TABLE.get(model, {})
        per_image: dict[str, float] = pricing.get("per_image", {})  # type: ignore[assignment]
        cost = per_image.get(f"{quality}:{size}", _DEFAULT_IMAGE_COST)
        return CostEstimate(
            provider=provider,
            model=model,
            estimated_input_tokens=0,
            estimated_output_tokens=0,
            estimated_cost_usd=round(float(cost), 6),
        )

    def estimate_image_validation_cost(self, *, provider: str = "openai", model: str) -> CostEstimate:
        """F31.5: approximates one ImageValidationService call (see
        _VALIDATION_*_TOKEN_ESTIMATE above). Deterministic and independent of the
        actual prompt/image content, exactly like estimate_image_cost's flat
        per-(quality,size) lookup — this is what lets callers pre-check
        affordability before making the call, not just report cost after the fact."""
        pricing = PRICING_TABLE.get(model, _DEFAULT_TEXT_PRICING)
        input_tokens = _VALIDATION_PROMPT_TOKEN_ESTIMATE + _VALIDATION_IMAGE_TOKEN_ESTIMATE
        output_tokens = _VALIDATION_OUTPUT_TOKEN_ESTIMATE
        cost = (input_tokens / 1000.0) * float(pricing["input_per_1k"]) + (output_tokens / 1000.0) * float(
            pricing["output_per_1k"]
        )
        return CostEstimate(
            provider=provider,
            model=model,
            estimated_input_tokens=input_tokens,
            estimated_output_tokens=output_tokens,
            estimated_cost_usd=round(cost, 6),
        )

    def build_budget_tracker(self, *, maximum_budget_usd: float, estimated_cost_so_far_usd: float) -> BudgetTracker:
        """F31.5: the one place `remaining budget` is computed from a hard ceiling
        and whatever has already been spent — every budget-aware service builds its
        BudgetTracker through this method instead of repeating the subtraction/
        clamp inline."""
        return BudgetTracker(remaining_usd=max(0.0, maximum_budget_usd - estimated_cost_so_far_usd))

    def build_image_generation_preview(
        self,
        *,
        scene_count: int,
        thumbnail_count: int,
        model: str,
        size: str,
        quality: str,
    ) -> str:
        """Render a human-readable cost preview for the images a production run is
        about to request.

        Image generation is the single largest API expense in the production
        workflow, so its cost must be visible and predictable *before* any request
        is sent — not reconstructed afterward from a bill. `scene_count` is expected
        to be the app's own enforced ceiling (e.g. Settings.max_scenes_per_video),
        not an LLM-reported count, so this preview reflects what the application
        has decided it will spend, independent of anything the model returns.
        """
        total_images = scene_count + thumbnail_count
        per_image_cost = self.estimate_image_cost(
            provider="openai-image-generation", model=model, size=size, quality=quality
        ).estimated_cost_usd
        total_cost = round(per_image_cost * total_images, 6)
        return (
            "Image Generation Preview\n\n"
            f"Image quality: {quality}\n\n"
            f"Scene images: {scene_count}\n"
            f"Thumbnail: {thumbnail_count}\n\n"
            f"Total images: {total_images}\n\n"
            "Estimated image cost:\n"
            f"${total_cost:.2f}"
        )

    def total(self, estimates: list[CostEstimate]) -> float:
        return round(sum(e.estimated_cost_usd for e in estimates), 6)

    def _estimate_tokens(self, text: str) -> int:
        if not text:
            return 0
        return max(1, int(len(text) / _CHARS_PER_TOKEN))
