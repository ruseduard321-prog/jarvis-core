from __future__ import annotations

from backend.core.config import Settings
from backend.core.workflow_engine_models import WorkflowArtifact
from backend.services.run_artifact_storage_service import RunArtifactStorageService


def _service(tmp_path) -> RunArtifactStorageService:
    return RunArtifactStorageService(settings=Settings(run_storage_root=str(tmp_path)))


def test_persist_creates_run_directory(tmp_path):
    service = _service(tmp_path)

    run_dir = service.persist("run-1", [])

    assert run_dir == tmp_path / "run-1"
    assert run_dir.is_dir()


def test_persist_writes_only_known_top_level_artifacts_that_exist(tmp_path):
    service = _service(tmp_path)
    artifacts = [
        WorkflowArtifact("voice.mp3", content_bytes=b"audio-bytes"),
        WorkflowArtifact("subtitles.srt", content="1\n00:00:00,000 --> 00:00:01,000\nHi\n"),
        WorkflowArtifact("thumbnail.png", content_bytes=b"thumb-bytes"),
        WorkflowArtifact("script.md", content="# Script\n"),
        WorkflowArtifact("research.md", content="# Research\n"),
        WorkflowArtifact("__meta__/Voice.json", content="{}"),
    ]

    run_dir = service.persist("run-2", artifacts)

    assert (run_dir / "voice.mp3").read_bytes() == b"audio-bytes"
    assert (run_dir / "subtitles.srt").read_text(encoding="utf-8").startswith("1\n")
    assert (run_dir / "thumbnail.png").read_bytes() == b"thumb-bytes"
    assert (run_dir / "script.md").read_text(encoding="utf-8") == "# Script\n"
    assert not (run_dir / "research.md").exists()
    assert not (run_dir / "__meta__").exists()


def test_persist_writes_scene_images_under_images_subdirectory(tmp_path):
    service = _service(tmp_path)
    artifacts = [
        WorkflowArtifact("scene_01.png", content_bytes=b"scene-1-bytes"),
        WorkflowArtifact("scene_02.png", content_bytes=b"scene-2-bytes"),
    ]

    run_dir = service.persist("run-3", artifacts)

    assert (run_dir / "images" / "scene_01.png").read_bytes() == b"scene-1-bytes"
    assert (run_dir / "images" / "scene_02.png").read_bytes() == b"scene-2-bytes"


def test_persist_writes_nothing_when_no_relevant_artifacts_exist(tmp_path):
    service = _service(tmp_path)
    artifacts = [WorkflowArtifact("research.md", content="# Research\n")]

    run_dir = service.persist("run-4", artifacts)

    assert list(run_dir.iterdir()) == []
