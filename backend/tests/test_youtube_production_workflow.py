from __future__ import annotations

import pytest

from backend.core.config import Settings
from backend.core.workflow_engine_models import WorkflowRunContext
from backend.schemas.assets import BrollPlan, ImageAsset, MusicPlan, Scene, ScenePlan, ScenePrompt, ScenePromptSet, SubtitleAsset, VideoAsset, VoiceAsset
from backend.schemas.audio import AudioAsset
from backend.schemas.media import MediaPackage
from backend.schemas.research import PublishingPackage, ResearchPackage, ReviewedScript, ScriptDraft
from backend.schemas.strategy import StrategyPackage
from backend.schemas.visual_identity import VisualIdentityContext
from backend.services.asset_packaging_service import AssetPackagingService
from backend.services.run_artifact_storage_service import RunArtifactStorageService
from backend.services.scene_planning_service import ScenePlanningResult
from backend.services.youtube_production_workflow import build_youtube_production_workflow


class FakeResearchWorkflowService:
    async def execute(self, *, topic, constraints, user_id):
        self.called_with = {"topic": topic, "constraints": constraints, "user_id": user_id}
        return ResearchPackage(
            topic=topic,
            executive_summary="summary",
            recommended_angle="angle",
            metadata={"status": "success"},
        )


class FakeStrategyWorkflowService:
    async def execute(self, *, research_package, user_id):
        self.called_with = {"research_package": research_package, "user_id": user_id}
        return StrategyPackage(
            topic=research_package.topic,
            target_audience="general",
            positioning="unique",
            hook="hook",
            pacing="steady",
            metadata={"status": "success"},
        )


class FakeWriterWorkflowService:
    async def execute(self, *, research_package, duration_profile, user_id, strategy_package=None):
        self.called_with = {
            "research_package": research_package,
            "duration_profile": duration_profile,
            "user_id": user_id,
            "strategy_package": strategy_package,
        }
        return ScriptDraft(
            topic=research_package.topic,
            hook="hook",
            intro="intro",
            outro="outro",
            call_to_action="cta",
            estimated_duration="8 min",
            narration_script="full narration",
            metadata={"status": "success"},
        )


class FakeReviewWorkflowService:
    async def execute(self, script_draft, user_id):
        self.called_with = {"script_draft": script_draft, "user_id": user_id}
        return ReviewedScript(
            topic=script_draft.topic,
            revised_script="revised narration",
            quality_score=90.0,
            readability_score=90.0,
            engagement_score=90.0,
            status="success",
            metadata={"status": "success"},
        )


class FakeVisualIdentityService:
    async def execute(self, *, research_package, reviewed_script, user_id):
        self.called_with = {"research_package": research_package, "reviewed_script": reviewed_script, "user_id": user_id}
        return VisualIdentityContext(topic=research_package.topic, metadata={"status": "success"})


class FakeCharacterReferenceImageService:
    async def execute(self, *, characters, historical_context=None, estimated_cost_so_far_usd=0.0):
        self.called_with = {
            "characters": characters,
            "historical_context": historical_context,
            "estimated_cost_so_far_usd": estimated_cost_so_far_usd,
        }
        return characters, {}, 0.0


class FakeMediaWorkflowService:
    async def execute(self, *, reviewed_script, user_id):
        self.called_with = {"reviewed_script": reviewed_script, "user_id": user_id}
        return MediaPackage(thumbnail_prompt="thumb prompt", metadata={"status": "success"})


class FakePublishingPackageWorkflowService:
    async def execute(self, *, reviewed_script, media_package, user_id):
        self.called_with = {
            "reviewed_script": reviewed_script,
            "media_package": media_package,
            "user_id": user_id,
        }
        return PublishingPackage(
            reviewed_script=reviewed_script,
            youtube_title="title",
            youtube_description="description",
            thumbnail_prompt=media_package.thumbnail_prompt,
            metadata={"status": "success"},
        )


class FakeVoiceGenerationService:
    async def execute(self, reviewed_script):
        self.called_with = {"reviewed_script": reviewed_script}
        asset = VoiceAsset(provider="fake-tts", generation_time="2026-01-01T00:00:00Z", status="SUCCESS")
        return asset, b"fake-audio-bytes"


class FakeThumbnailGenerationService:
    async def execute(self, thumbnail_prompt, *, visual_identity_context=None, reference_images=None, estimated_cost_so_far_usd=0.0):
        self.called_with = {
            "thumbnail_prompt": thumbnail_prompt,
            "visual_identity_context": visual_identity_context,
            "reference_images": reference_images,
            "estimated_cost_so_far_usd": estimated_cost_so_far_usd,
        }
        asset = ImageAsset(provider="fake-image", generation_time="2026-01-01T00:00:00Z", status="SUCCESS")
        return asset, b"fake-image-bytes"


class FakeScenePlanningService:
    async def execute(self, reviewed_script, media_package, user_id):
        self.called_with = {
            "reviewed_script": reviewed_script,
            "media_package": media_package,
            "user_id": user_id,
        }
        scene_plan = ScenePlan(
            topic=reviewed_script.topic, scenes=[Scene(scene_number=1)], metadata={"status": "success"}
        )
        scene_prompts = ScenePromptSet(
            topic=reviewed_script.topic, prompts=[ScenePrompt(scene_number=1)], metadata={"status": "success"}
        )
        broll_plan = BrollPlan(topic=reviewed_script.topic, metadata={"status": "success"})
        music_plan = MusicPlan(reference="ambient", metadata={"status": "success"})
        return ScenePlanningResult(scene_plan, scene_prompts, broll_plan, music_plan)


class FakeCompositionPlanningService:
    async def execute(
        self,
        *,
        scene_plan,
        scene_prompts,
        voice_asset,
        reviewed_script=None,
        strategy_package=None,
        estimated_cost_so_far_usd=0.0,
        visual_identity_context=None,
        user_id=None,
    ):
        self.called_with = {
            "scene_plan": scene_plan,
            "scene_prompts": scene_prompts,
            "voice_asset": voice_asset,
            "reviewed_script": reviewed_script,
            "strategy_package": strategy_package,
            "visual_identity_context": visual_identity_context,
            "user_id": user_id,
        }
        from backend.services.composition_planning_service import CompositionPlanningResult
        from backend.services.composition_planner import DeterministicCompositionPlanner
        from backend.services.timeline_planner import DeterministicTimelinePlanner
        from backend.core.config import Settings

        timeline_plan = DeterministicTimelinePlanner(Settings()).plan(
            scene_plan=scene_plan, total_duration_seconds=max(voice_asset.duration, 3.0)
        )
        composition_plan = DeterministicCompositionPlanner().plan(scene_plan=scene_plan, timeline_plan=timeline_plan)
        return CompositionPlanningResult(
            timeline_plan=timeline_plan, composition_plan=composition_plan, scene_prompts=scene_prompts
        )


class FakeSceneImageGenerationService:
    async def execute(self, scene_prompts, *, characters=None, reference_images=None, estimated_cost_so_far_usd=0.0):
        self.called_with = {
            "scene_prompts": scene_prompts,
            "characters": characters,
            "reference_images": reference_images,
            "estimated_cost_so_far_usd": estimated_cost_so_far_usd,
        }
        from backend.schemas.assets import SceneImageAsset, SceneImageSet

        images = [
            SceneImageAsset(
                scene_number=prompt.scene_number,
                provider="fake-image",
                generation_time="2026-01-01T00:00:00Z",
                filename=f"scene_{prompt.scene_number:02d}.png",
                status="SUCCESS",
            )
            for prompt in scene_prompts.prompts
        ]
        scene_image_set = SceneImageSet(topic=scene_prompts.topic, images=images, metadata={"status": "success"})
        image_bytes_by_filename = {image.filename: b"fake-scene-image-bytes" for image in images}
        return scene_image_set, image_bytes_by_filename


class FakeSubtitleGenerationService:
    def execute(self, reviewed_script, voice_asset):
        self.called_with = {"reviewed_script": reviewed_script, "voice_asset": voice_asset}
        asset = SubtitleAsset(cue_count=1, generation_time="2026-01-01T00:00:00Z", status="SUCCESS")
        return asset, "1\n00:00:00,000 --> 00:00:02,000\nHello\n"


class FakeAudioEngineService:
    async def execute(self, *, voice_asset, narration_bytes, music_plan, scene_plan, timeline_plan=None):
        self.called_with = {
            "voice_asset": voice_asset,
            "narration_bytes": narration_bytes,
            "music_plan": music_plan,
            "scene_plan": scene_plan,
            "timeline_plan": timeline_plan,
        }
        asset = AudioAsset(generation_time="2026-01-01T00:00:00Z", status="SUCCESS", duration=3.0)
        return asset, b"fake-mixed-audio-bytes"


class FakeVideoAssemblyService:
    async def execute(
        self,
        *,
        scene_image_set,
        image_bytes_by_filename,
        voice_asset,
        audio_bytes,
        subtitle_asset,
        subtitle_content,
        run_id,
        scene_plan=None,
        composition_plan=None,
    ):
        self.called_with = {
            "scene_image_set": scene_image_set,
            "image_bytes_by_filename": image_bytes_by_filename,
            "voice_asset": voice_asset,
            "audio_bytes": audio_bytes,
            "subtitle_asset": subtitle_asset,
            "subtitle_content": subtitle_content,
            "run_id": run_id,
            "scene_plan": scene_plan,
            "composition_plan": composition_plan,
        }
        asset = VideoAsset(
            provider="ffmpeg-local",
            duration=3.0,
            generation_time="2026-01-01T00:00:00Z",
            status="SUCCESS",
            scene_count=len(image_bytes_by_filename),
            file_path=f"/fake/storage/runs/{run_id}/video.mp4",
        )
        return asset, b"fake-video-bytes"


def _build_definition(
    *,
    research_service,
    strategy_service,
    writer_service,
    review_service,
    media_service,
    publishing_service,
    run_storage_root,
    visual_identity_service=None,
    character_reference_image_service=None,
):
    return build_youtube_production_workflow(
        research_workflow_service=research_service,
        strategy_workflow_service=strategy_service,
        writer_workflow_service=writer_service,
        review_workflow_service=review_service,
        visual_identity_service=visual_identity_service or FakeVisualIdentityService(),
        character_reference_image_service=character_reference_image_service or FakeCharacterReferenceImageService(),
        media_workflow_service=media_service,
        publishing_package_workflow_service=publishing_service,
        voice_generation_service=FakeVoiceGenerationService(),
        thumbnail_generation_service=FakeThumbnailGenerationService(),
        scene_planning_service=FakeScenePlanningService(),
        composition_planning_service=FakeCompositionPlanningService(),
        scene_image_generation_service=FakeSceneImageGenerationService(),
        subtitle_generation_service=FakeSubtitleGenerationService(),
        audio_engine_service=FakeAudioEngineService(),
        video_assembly_service=FakeVideoAssemblyService(),
        asset_packaging_service=AssetPackagingService(),
        run_artifact_storage_service=RunArtifactStorageService(
            settings=Settings(run_storage_root=str(run_storage_root))
        ),
        settings=Settings(run_storage_root=str(run_storage_root)),
    )


@pytest.mark.asyncio
async def test_steps_run_in_order_and_produce_documented_filenames(tmp_path):
    research_service = FakeResearchWorkflowService()
    strategy_service = FakeStrategyWorkflowService()
    writer_service = FakeWriterWorkflowService()
    review_service = FakeReviewWorkflowService()
    media_service = FakeMediaWorkflowService()
    publishing_service = FakePublishingPackageWorkflowService()

    definition = _build_definition(
        research_service=research_service,
        strategy_service=strategy_service,
        writer_service=writer_service,
        review_service=review_service,
        media_service=media_service,
        publishing_service=publishing_service,
        run_storage_root=tmp_path,
    )

    assert [step.name for step in definition.steps] == [
        "Research",
        "Strategy",
        "Writer",
        "Review",
        "Visual Identity",
        "Media",
        "Publishing Package",
        "Voice",
        "Thumbnail",
        "Scene Planning",
        "Composition Planning",
        "Scene Image",
        "Subtitle",
        "Audio Mix",
        "Video Assembly",
        "Asset Packaging",
    ]

    context = WorkflowRunContext(
        execution_id="exec-1",
        conversation_id="conv-1",
        user_id=None,
        topic="Dyatlov Pass Incident",
    )

    produced_filenames: list[str] = []
    meta_filenames: list[str] = []
    for step in definition.steps:
        result = await step.run(context)
        assert result.status == "success"
        context.inputs[step.name] = result.data
        context.artifacts.extend(result.artifacts)
        for artifact in result.artifacts:
            if artifact.filename.startswith("__meta__/"):
                meta_filenames.append(artifact.filename)
            else:
                produced_filenames.append(artifact.filename)

    assert meta_filenames == [f"__meta__/{step.name}.json" for step in definition.steps]

    assert produced_filenames == [
        "research.md",
        "strategy.md",
        "script.md",
        "review.md",
        "visual_context.json",
        "media_prompts.md",
        "thumbnail_prompt.txt",
        "title.md",
        "description.md",
        "hashtags.md",
        "voice.mp3",
        "thumbnail.png",
        "scene_plan.json",
        "scene_prompts.json",
        "broll_plan.json",
        "music.md",
        "timeline_plan.json",
        "composition_plan.json",
        "composition_scene_prompts.json",
        "scene_01.png",
        "subtitles.srt",
        "audio_mix.m4a",
        "video.mp4",
        "asset_manifest.json",
    ]

    manifest_result = context.inputs["Asset Packaging"]["asset_manifest"]
    manifest_types = {entry.asset_type for entry in manifest_result.entries}
    assert manifest_types == {
        "voice",
        "thumbnail",
        "subtitle",
        "audio_mix",
        "video",
        "scene_plan",
        "scene_prompts",
        "broll_plan",
        "music_plan",
        "timeline_plan",
        "composition_plan",
        "visual_identity",
    }
    assert all(entry.status == "SUCCESS" for entry in manifest_result.entries)

    # F3: the manifest carries the run's real aggregate cost against the
    # configured ceiling — with fake services reporting no cost, this run is
    # trivially within budget, but the fields themselves must be populated.
    assert manifest_result.maximum_video_budget_usd == 5.0
    assert manifest_result.budget_status == "within_budget"
    assert manifest_result.total_estimated_cost_usd >= 0.0

    # Writer receives both Research and Strategy outputs threaded through context.
    assert writer_service.called_with["research_package"] is context.inputs["Research"]["research_package"]
    assert writer_service.called_with["strategy_package"] is context.inputs["Strategy"]["strategy_package"]

    # Publishing Package receives both Review and Media outputs threaded through context.
    assert (
        publishing_service.called_with["reviewed_script"]
        is context.inputs["Review"]["reviewed_script"]
    )
    assert publishing_service.called_with["media_package"] is context.inputs["Media"]["media_package"]

    # Composition Planning (F28 AI Director integration) receives Review's and
    # Strategy's outputs threaded through context, alongside Scene Planning's.
    composition_planning_service = next(
        step for step in definition.steps if step.name == "Composition Planning"
    )._service
    assert (
        composition_planning_service.called_with["reviewed_script"]
        is context.inputs["Review"]["reviewed_script"]
    )
    assert (
        composition_planning_service.called_with["strategy_package"]
        is context.inputs["Strategy"]["strategy_package"]
    )

    # Video Assembly receives the Audio Mix step's mixed track, not the raw voice bytes,
    # confirming the mixed-audio-preferred-over-raw-narration wiring is actually live.
    video_assembly_service = next(
        step for step in definition.steps if step.name == "Video Assembly"
    )._service
    assert video_assembly_service.called_with["audio_bytes"] == b"fake-mixed-audio-bytes"

    # Video Assembly persists the run's other artifacts to storage/runs/<run_id>/ alongside
    # the video (which VideoAssemblyService itself would persist — not exercised here since
    # FakeVideoAssemblyService never touches disk).
    run_dir = tmp_path / context.execution_id
    assert (run_dir / "voice.mp3").exists()
    assert (run_dir / "subtitles.srt").exists()
    assert (run_dir / "thumbnail.png").exists()
    assert (run_dir / "script.md").exists()
    assert (run_dir / "images" / "scene_01.png").exists()


@pytest.mark.asyncio
async def test_research_step_fails_when_status_failed(tmp_path):
    class FailingResearchService:
        async def execute(self, *, topic, constraints, user_id):
            return ResearchPackage(
                topic=topic,
                executive_summary="",
                recommended_angle="",
                open_questions=["no sources found"],
                metadata={"status": "failed"},
            )

    definition = _build_definition(
        research_service=FailingResearchService(),
        strategy_service=FakeStrategyWorkflowService(),
        writer_service=FakeWriterWorkflowService(),
        review_service=FakeReviewWorkflowService(),
        media_service=FakeMediaWorkflowService(),
        publishing_service=FakePublishingPackageWorkflowService(),
        run_storage_root=tmp_path,
    )
    context = WorkflowRunContext(
        execution_id="exec-2", conversation_id="conv-1", user_id=None, topic="Unresearchable Topic"
    )

    result = await definition.steps[0].run(context)

    assert result.status == "failed"
    assert result.error == "no sources found"
