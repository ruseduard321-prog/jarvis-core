"""F11 (F31.5 hardening) — live OpenAI smoke test.

F31's Photorealistic Visual Engine rests on two assumptions that NO unit test in
this repository can verify, because every other test in `backend/tests/` runs
against fakes: (1) that `gpt-5.5` actually accepts multimodal `image_url` content
in Chat Completions (ImageValidationService's entire mechanism), and (2) that
`images.edit` accepts the parameter shape this codebase assumes for the pinned
`openai==1.109.1` SDK, and that gpt-image-1 actually honors a reference image
(OpenAIImageGenerationProvider's reference-conditioning path). If either
assumption is wrong, both features fail OPEN today — they log a warning and
silently behave as if disabled, forever, with no test catching it.

This file is that catch. It makes REAL, BILLED OpenAI API calls and must never
run as part of the normal test suite or any CI pipeline.

HOW TO RUN (manually, only when you intend to spend real API credits):

    RUN_LIVE_SMOKE_TESTS=1 .venv/Scripts/python.exe -m pytest backend/tests/live/test_f31_live_openai_smoke.py -v -s

On Windows PowerShell:

    $env:RUN_LIVE_SMOKE_TESTS = "1"
    .venv/Scripts/python.exe -m pytest backend/tests/live/test_f31_live_openai_smoke.py -v -s

Requirements to actually exercise the live calls:
  - `RUN_LIVE_SMOKE_TESTS=1` set in the environment (the opt-in gate below).
  - A real `OPENAI_API_KEY` configured (via `.env` or the environment), loaded
    through the normal `Settings`/DI wiring — this test intentionally uses the
    REAL dependency-injection container (`backend.core.dependencies`), not
    hand-rolled clients, so it validates the exact wiring production uses.

Without RUN_LIVE_SMOKE_TESTS=1, every test in this module is skipped — never
collected as a failure, never run, and never contributes real API cost — so it
is always safe to include this file in the repository and safe for `pytest
backend/tests` (the normal, CI-safe invocation) to walk over it.

Expected cost: two gpt-image-1 generations (one plain, one images.edit
reference-conditioned) plus one gpt-5.5 vision validation call — a few cents,
comparable to what a single real production beat costs.
"""

from __future__ import annotations

import os

import pytest

RUN_LIVE_SMOKE_TESTS = os.environ.get("RUN_LIVE_SMOKE_TESTS") == "1"

if not RUN_LIVE_SMOKE_TESTS:
    pytest.skip(
        "F31.5 live OpenAI smoke test skipped (opt-in only). "
        "Set RUN_LIVE_SMOKE_TESTS=1 to run it manually — see this file's module "
        "docstring for exact instructions. Never enable this in CI.",
        allow_module_level=True,
    )

from backend.core.dependencies import (  # noqa: E402 - imported after the skip guard on purpose
    get_image_generation_provider,
    get_image_validation_service,
    get_settings,
)


def _require_real_api_key() -> None:
    settings = get_settings()
    if not settings.openai_api_key:
        pytest.skip(
            "RUN_LIVE_SMOKE_TESTS=1 was set but no OPENAI_API_KEY is configured — "
            "set it in .env or the environment to actually exercise the live calls."
        )


@pytest.mark.asyncio
async def test_live_image_generation_produces_a_decodable_image():
    """Baseline: confirms the real image-generation call chain (DI-wired
    OpenAIImageGenerationProvider, real gpt-image-1 call) works at all, before
    the more specific assertions below build on its output."""
    _require_real_api_key()
    provider = get_image_generation_provider()

    media_asset = await provider.generate_image(
        prompt="A single weathered stone lighthouse on a rocky coastline at dusk, photorealistic documentary photography.",
        size="1024x1024",
        quality="low",
        model="gpt-image-1",
    )

    from backend.services.openai_image_generation_provider import OpenAIImageGenerationProvider

    image_bytes = OpenAIImageGenerationProvider.decode_image_bytes(media_asset.source)
    assert image_bytes is not None
    assert len(image_bytes) > 1000  # a real PNG, not an empty/placeholder response
    assert media_asset.metadata.get("used_reference_image") is False


@pytest.mark.asyncio
async def test_live_image_validation_service_accepts_multimodal_image_input():
    """F11 requirement 1: gpt-5.5 multimodal image input, exercised through the
    real ImageValidationService (not a hand-rolled chat completion call), the
    same code path SceneImageGenerationService/ThumbnailGenerationService/
    CharacterReferenceImageService use in production.

    The critical assertion is NOT `result.valid` (a real photo could reasonably
    be classified either way) — it's that `reason` is NOT
    "validation_unavailable", which is exactly the fail-open value this service
    silently returns when the live call itself is broken (wrong model
    capability, malformed request, auth failure, etc.). If this test ever
    fails on that specific assertion, F31's image validation has been a
    silent no-op in every real production run."""
    _require_real_api_key()
    provider = get_image_generation_provider()
    validation_service = get_image_validation_service()

    media_asset = await provider.generate_image(
        prompt="A single weathered stone lighthouse on a rocky coastline at dusk, photorealistic documentary photography.",
        size="1024x1024",
        quality="low",
        model="gpt-image-1",
    )
    from backend.services.openai_image_generation_provider import OpenAIImageGenerationProvider

    image_bytes = OpenAIImageGenerationProvider.decode_image_bytes(media_asset.source)
    assert image_bytes is not None

    result = await validation_service.validate(image_bytes=image_bytes, context="a lighthouse on a coastline")

    assert result.reason != "validation_unavailable", (
        "ImageValidationService fell back to fail-open — gpt-5.5 multimodal "
        "image input or the validation call itself is broken in this account/SDK."
    )
    assert result.estimated_cost_usd > 0.0
    assert isinstance(result.valid, bool)


@pytest.mark.asyncio
async def test_live_images_edit_reference_conditioning_is_actually_used():
    """F11 requirements 2 and 3: images.edit and reference conditioning,
    exercised through the real OpenAIImageGenerationProvider.generate_image()
    reference_image parameter — the same path CharacterReferenceImageService's
    portraits condition every subsequent scene/thumbnail generation on.

    The critical assertion is `metadata["used_reference_image"] is True`. If
    the account/SDK/model combination doesn't actually support images.edit the
    way this codebase assumes, the provider silently falls back to an ordinary
    text-to-image call (by design — see OpenAIImageGenerationProvider) and this
    assertion is what catches that silently-degraded state instead of a human
    having to notice degraded character consistency in a finished video."""
    _require_real_api_key()
    provider = get_image_generation_provider()

    reference_asset = await provider.generate_image(
        prompt=(
            "Studio reference portrait of a middle-aged sailor with a weathered face, short grey beard, "
            "wearing a dark wool coat, neutral plain background, centered composition, eye-level angle, "
            "photorealistic documentary character reference sheet."
        ),
        size="1024x1024",
        quality="low",
        model="gpt-image-1",
    )
    from backend.services.openai_image_generation_provider import OpenAIImageGenerationProvider

    reference_bytes = OpenAIImageGenerationProvider.decode_image_bytes(reference_asset.source)
    assert reference_bytes is not None

    conditioned_asset = await provider.generate_image(
        prompt="The same sailor standing on the deck of a ship, looking out at a stormy sea, photorealistic documentary photography.",
        size="1024x1024",
        quality="low",
        model="gpt-image-1",
        reference_image=reference_bytes,
    )

    assert conditioned_asset.metadata.get("used_reference_image") is True, (
        "images.edit reference conditioning silently fell back to a plain "
        "text-to-image call — F31's Character Consistency reference-portrait "
        "mechanism is not actually being honored by this account/SDK/model."
    )
    conditioned_bytes = OpenAIImageGenerationProvider.decode_image_bytes(conditioned_asset.source)
    assert conditioned_bytes is not None
    assert len(conditioned_bytes) > 1000
