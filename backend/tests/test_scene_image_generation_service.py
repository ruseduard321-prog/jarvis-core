from __future__ import annotations

import base64

import pytest

from backend.core.config import Settings
from backend.core.media_asset import MediaAsset
from backend.core.provider_exceptions import TransientProviderError
from backend.schemas.assets import ScenePrompt, ScenePromptSet
from backend.services.scene_image_generation_service import SceneImageGenerationService, WorkflowSafetyError


class FakeImageProvider:
    def __init__(self, *, media_assets: list[MediaAsset] | None = None, raises: Exception | None = None):
        self._media_assets = media_assets or []
        self._raises = raises
        self.calls = 0

    async def generate_image(self, *, prompt, size=None, quality=None, model=None, reference_image=None):
        if self._raises:
            raise self._raises
        asset = self._media_assets[self.calls]
        self.calls += 1
        return asset


def _media_asset(source: str) -> MediaAsset:
    return MediaAsset(
        id="asset-1",
        type="image",
        source=source,
        provider="openai-image-generation",
        mime_type="image/png",
        width=1024,
        height=1024,
        prompt="a scene",
        metadata={"model": "gpt-image-1", "retry_count": 0, "estimated_cost_usd": 0.02},
    )


def _prompt_set(*, scene_count: int) -> ScenePromptSet:
    return ScenePromptSet(
        topic="Test Topic",
        prompts=[ScenePrompt(scene_number=i, prompt=f"scene {i} prompt") for i in range(1, scene_count + 1)],
    )


@pytest.mark.asyncio
async def test_execute_skips_when_no_scene_prompts():
    service = SceneImageGenerationService(image_generation_provider=FakeImageProvider(), settings=Settings())

    scene_image_set, image_bytes_by_filename = await service.execute(ScenePromptSet(topic="Test Topic", prompts=[]))

    assert scene_image_set.metadata["status"] == "skipped"
    assert scene_image_set.images == []
    assert image_bytes_by_filename == {}


@pytest.mark.asyncio
async def test_execute_generates_one_image_per_scene():
    raw_1, raw_2 = b"scene-1-bytes", b"scene-2-bytes"
    data_uri_1 = f"data:image/png;base64,{base64.b64encode(raw_1).decode('ascii')}"
    data_uri_2 = f"data:image/png;base64,{base64.b64encode(raw_2).decode('ascii')}"
    provider = FakeImageProvider(media_assets=[_media_asset(data_uri_1), _media_asset(data_uri_2)])
    service = SceneImageGenerationService(image_generation_provider=provider, settings=Settings())

    scene_image_set, image_bytes_by_filename = await service.execute(_prompt_set(scene_count=2))

    assert scene_image_set.metadata["status"] == "success"
    assert [image.status for image in scene_image_set.images] == ["SUCCESS", "SUCCESS"]
    assert [image.filename for image in scene_image_set.images] == ["scene_01.png", "scene_02.png"]
    assert image_bytes_by_filename == {"scene_01.png": raw_1, "scene_02.png": raw_2}
    assert scene_image_set.images[0].retry_count == 0
    assert scene_image_set.images[0].estimated_cost_usd == 0.02


@pytest.mark.asyncio
async def test_execute_marks_partial_status_on_mixed_outcomes():
    raw = b"scene-1-bytes"
    data_uri = f"data:image/png;base64,{base64.b64encode(raw).decode('ascii')}"
    provider = FakeImageProvider(media_assets=[_media_asset(data_uri), _media_asset("generated")])
    service = SceneImageGenerationService(image_generation_provider=provider, settings=Settings())

    scene_image_set, image_bytes_by_filename = await service.execute(_prompt_set(scene_count=2))

    assert scene_image_set.metadata["status"] == "partial"
    assert [image.status for image in scene_image_set.images] == ["SUCCESS", "FAILED"]
    assert image_bytes_by_filename == {"scene_01.png": raw}


@pytest.mark.asyncio
async def test_execute_never_raises_on_provider_failure():
    provider = FakeImageProvider(raises=TransientProviderError("rate limited"))
    service = SceneImageGenerationService(image_generation_provider=provider, settings=Settings())

    scene_image_set, image_bytes_by_filename = await service.execute(_prompt_set(scene_count=1))

    assert scene_image_set.metadata["status"] == "failed"
    assert scene_image_set.images[0].status == "FAILED"
    assert image_bytes_by_filename == {}


@pytest.mark.asyncio
async def test_execute_generates_unique_filenames_for_multiple_beats_in_one_scene():
    # F28B regression: two beats sharing scene_number=1 must not collide on
    # filename/dict key, or one beat's image would silently overwrite the other's.
    raw_1, raw_2 = b"beat-1-bytes", b"beat-2-bytes"
    data_uri_1 = f"data:image/png;base64,{base64.b64encode(raw_1).decode('ascii')}"
    data_uri_2 = f"data:image/png;base64,{base64.b64encode(raw_2).decode('ascii')}"
    provider = FakeImageProvider(media_assets=[_media_asset(data_uri_1), _media_asset(data_uri_2)])
    service = SceneImageGenerationService(image_generation_provider=provider, settings=Settings())
    prompt_set = ScenePromptSet(
        topic="Test Topic",
        prompts=[
            ScenePrompt(scene_number=1, beat_number=1, prompt="beat one"),
            ScenePrompt(scene_number=1, beat_number=2, prompt="beat two"),
        ],
    )

    scene_image_set, image_bytes_by_filename = await service.execute(prompt_set)

    filenames = [image.filename for image in scene_image_set.images]
    assert filenames == ["scene_01_beat_01.png", "scene_01_beat_02.png"]
    assert len(set(filenames)) == 2
    assert image_bytes_by_filename == {"scene_01_beat_01.png": raw_1, "scene_01_beat_02.png": raw_2}
    assert [image.beat_number for image in scene_image_set.images] == [1, 2]


@pytest.mark.asyncio
async def test_execute_hard_ceiling_scales_with_maximum_visual_beats_per_scene():
    settings = Settings(max_scenes_per_video=2, max_scene_hard_limit=4, maximum_visual_beats_per_scene=3)
    service = SceneImageGenerationService(image_generation_provider=FakeImageProvider(), settings=settings)
    # 2 scenes * 3 beats = 6 requested images, which exceeds hard_limit (4*3=12)? No:
    # hard_limit scales to 4*3=12, so 13 requested should abort; use 13 to hit that.
    prompt_set = ScenePromptSet(
        topic="Test Topic",
        prompts=[ScenePrompt(scene_number=(i // 3) + 1, beat_number=(i % 3) + 1, prompt=f"p{i}") for i in range(13)],
    )

    with pytest.raises(WorkflowSafetyError):
        await service.execute(prompt_set)


@pytest.mark.asyncio
async def test_execute_skips_image_when_budget_already_exhausted():
    # Default settings: gpt-image-1/medium/1536x1024 estimates $0.063/image
    # (CostTracker.PRICING_TABLE). estimated_cost_so_far_usd already equals the
    # full $5.0 default ceiling, so nothing is affordable.
    provider = FakeImageProvider(media_assets=[_media_asset("generated")])
    service = SceneImageGenerationService(image_generation_provider=provider, settings=Settings())

    scene_image_set, image_bytes_by_filename = await service.execute(
        _prompt_set(scene_count=1), estimated_cost_so_far_usd=5.0
    )

    assert scene_image_set.images[0].status == "SKIPPED"
    assert "budget exhausted" in scene_image_set.images[0].error
    assert image_bytes_by_filename == {}
    assert provider.calls == 0


@pytest.mark.asyncio
async def test_execute_stops_affording_further_images_once_budget_runs_out():
    raw_1 = b"scene-1-bytes"
    data_uri_1 = f"data:image/png;base64,{base64.b64encode(raw_1).decode('ascii')}"
    provider = FakeImageProvider(media_assets=[_media_asset(data_uri_1), _media_asset("generated")])
    # Budget affords exactly one $0.063 image (the default medium/1536x1024 rate),
    # not two.
    settings = Settings(maximum_video_budget_usd=0.07)
    service = SceneImageGenerationService(image_generation_provider=provider, settings=settings)

    scene_image_set, image_bytes_by_filename = await service.execute(_prompt_set(scene_count=2))

    assert scene_image_set.images[0].status == "SUCCESS"
    assert scene_image_set.images[1].status == "SKIPPED"
    assert "budget exhausted" in scene_image_set.images[1].error
    assert image_bytes_by_filename == {"scene_01.png": raw_1}
    assert provider.calls == 1


@pytest.mark.asyncio
async def test_execute_trims_to_scaled_max_images_on_ordinary_overshoot():
    settings = Settings(max_scenes_per_video=2, max_scene_hard_limit=50, maximum_visual_beats_per_scene=2)
    # max_images = 2 * 2 = 4; request 5 (within hard_limit) -> trimmed to 4, not aborted.
    media_assets = [_media_asset("generated") for _ in range(5)]
    provider = FakeImageProvider(media_assets=media_assets)
    service = SceneImageGenerationService(image_generation_provider=provider, settings=settings)
    prompt_set = ScenePromptSet(
        topic="Test Topic",
        prompts=[ScenePrompt(scene_number=i + 1, prompt=f"p{i}") for i in range(5)],
    )

    scene_image_set, _ = await service.execute(prompt_set)

    assert len(scene_image_set.images) == 4
