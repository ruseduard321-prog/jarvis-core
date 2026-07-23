from __future__ import annotations

import base64
import json
import logging
from dataclasses import dataclass, field

from backend.core.config import Settings
from backend.core.cost_tracker import BudgetTracker, CostTracker
from backend.core.openai_llm_provider import OpenAIProvider

logger = logging.getLogger(__name__)

_VALIDATION_SYSTEM_PROMPT = (
    "You are an automated quality gate for AI-generated documentary footage stills. Inspect the "
    "image and report ONLY obvious generation failures, never subjective taste. Flag an image as "
    "invalid when it shows: multiple unrelated panels or a split-screen/comic-grid composition "
    "instead of one coherent shot; large blocks of unreadable or garbled on-image text (e.g. a "
    "map or sign with nonsense lettering); broken or anatomically impossible bodies/faces/hands; "
    "or other unmistakably broken rendering artifacts. Do NOT flag ordinary artistic choices, "
    "stylization, difficult lighting, or minor imperfections that a real photograph could also have."
)


@dataclass
class ImageValidationResult:
    valid: bool
    issues: list[str] = field(default_factory=list)
    reason: str = ""
    # F31.5: real (estimated) USD cost of THIS validate() call — 0.0 whenever no
    # provider call actually happened (disabled, budget-skipped, or the fail-open
    # error path), so callers can sum it into a total without double-accounting.
    estimated_cost_usd: float = 0.0


class ImageValidationService:
    """F31 Image Validation: one cheap vision-model classification call per
    generated image, checking for the specific failure modes F30's real-evidence
    audit found in production (multi-panel collages, garbled on-image text, broken
    anatomy). Fails open on any provider/parse error — a validator outage must
    never block image generation, the same discipline every other optional stage in
    this pipeline (AI Director, Audio Engine, cinematic rendering) already
    follows.

    F31.5: budget-aware. When a `BudgetTracker` is supplied, a call whose
    estimated cost the tracker can't afford is skipped entirely (fail-open, same
    as any other validator outage) rather than spending regardless — validation
    is a real, trackable cost source, not free QA."""

    def __init__(self, openai_llm_provider: OpenAIProvider, settings: Settings, cost_tracker: CostTracker | None = None) -> None:
        self._openai_llm_provider = openai_llm_provider
        self._settings = settings
        self._cost_tracker = cost_tracker or CostTracker()

    async def validate(
        self, *, image_bytes: bytes, context: str = "", budget_tracker: BudgetTracker | None = None
    ) -> ImageValidationResult:
        if not self._settings.image_validation_enabled:
            return ImageValidationResult(valid=True, reason="validation_disabled")

        estimated_cost = self._cost_tracker.estimate_image_validation_cost(
            model=self._settings.image_validation_model
        ).estimated_cost_usd
        if budget_tracker is not None and not budget_tracker.can_afford(estimated_cost):
            logger.warning(
                "image_validation_skipped_budget_exhausted",
                extra={"estimated_cost_usd": estimated_cost, "remaining_usd": budget_tracker.remaining_usd},
            )
            return ImageValidationResult(valid=True, reason="validation_skipped_budget_exhausted")

        try:
            client = await self._openai_llm_provider.get_client()
            data_uri = f"data:image/png;base64,{base64.b64encode(image_bytes).decode('ascii')}"
            response = await client.chat.completions.create(
                model=self._settings.image_validation_model,
                messages=[
                    {"role": "system", "content": _VALIDATION_SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    f"Scene context this image is meant to depict: {context or '(none)'}\n\n"
                                    'Return strict JSON: {"valid": bool, "issues": [short strings], '
                                    '"reason": short string}. Return JSON only, no prose, no markdown fences.'
                                ),
                            },
                            {"type": "image_url", "image_url": {"url": data_uri}},
                        ],
                    },
                ],
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
            parsed = json.loads(content)
            result = ImageValidationResult(
                valid=bool(parsed.get("valid", True)),
                issues=[str(issue) for issue in parsed.get("issues", []) if str(issue).strip()],
                reason=str(parsed.get("reason", "")).strip(),
                estimated_cost_usd=estimated_cost,
            )
        except Exception as exc:
            logger.warning("image_validation_unavailable", extra={"reason": str(exc)})
            return ImageValidationResult(valid=True, reason="validation_unavailable")

        if budget_tracker is not None:
            budget_tracker.record_spend(estimated_cost)
        return result
