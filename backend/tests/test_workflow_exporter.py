from __future__ import annotations

import hashlib
import json
import struct
from datetime import datetime
from types import SimpleNamespace

from backend.core.workflow_engine_models import WorkflowArtifact
from backend.services.workflow_exporter import FUTURE_ASSETS, WorkflowExporter


def _make_exporter(tmp_path) -> WorkflowExporter:
    fake_settings = SimpleNamespace(workflow_output_root=str(tmp_path))
    return WorkflowExporter(settings=fake_settings)


def _valid_png_bytes() -> bytes:
    return b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR" + struct.pack(">II", 100, 100) + b"\x00" * 17


def _valid_srt_text() -> str:
    return (
        "1\n00:00:00,000 --> 00:00:01,000\nHello\n\n"
        "2\n00:00:01,000 --> 00:00:02,000\nWorld\n"
    )


def test_export_writes_artifacts_and_metadata_files(tmp_path):
    exporter = _make_exporter(tmp_path)
    started_at = datetime(2026, 7, 19, 10, 0, 0)
    completed_at = datetime(2026, 7, 19, 10, 15, 30)

    result = exporter.export(
        execution_id="exec-123",
        workflow_id="youtube_production_v1",
        workflow_name="YouTube Production Workflow v1",
        topic="Dyatlov Pass Incident!",
        artifacts=[
            WorkflowArtifact("research.md", "# Research\n"),
            WorkflowArtifact("script.md", "# Script\n"),
        ],
        step_statuses={"Research": "success", "Writer": "success"},
        started_at=started_at,
        completed_at=completed_at,
    )

    output_folder = tmp_path / "2026-07-19_10-15-30_dyatlov-pass-incident"
    assert result.output_folder == str(output_folder)
    assert output_folder.is_dir()

    assert (output_folder / "research.md").read_text(encoding="utf-8") == "# Research\n"
    assert (output_folder / "script.md").read_text(encoding="utf-8") == "# Script\n"

    workflow_json = json.loads((output_folder / "workflow.json").read_text(encoding="utf-8"))
    assert workflow_json["workflow_id"] == "youtube_production_v1"
    assert workflow_json["execution_id"] == "exec-123"
    assert workflow_json["topic"] == "Dyatlov Pass Incident!"
    assert workflow_json["step_status"] == {"Research": "success", "Writer": "success"}
    assert workflow_json["started_at"] == started_at.isoformat()
    assert workflow_json["completed_at"] == completed_at.isoformat()

    manifest = json.loads((output_folder / "manifest.json").read_text(encoding="utf-8"))
    manifest_names = [entry["name"] for entry in manifest["files"]]
    assert manifest_names == ["research.md", "script.md", "workflow.json"]
    assert all(entry["bytes"] > 0 for entry in manifest["files"])
    assert manifest["future_assets"] == FUTURE_ASSETS

    assert result.files_written == ["research.md", "script.md", "workflow.json", "manifest.json", "summary.json"]

    assert workflow_json["status"] == "FAILED"
    assert workflow_json["validation_errors"]
    assert "Export" in workflow_json["step_metrics"]
    assert workflow_json["cost"] == {"per_step": {}, "total_usd": 0.0}

    summary = json.loads((output_folder / "summary.json").read_text(encoding="utf-8"))
    assert summary["workflow_id"] == "youtube_production_v1"
    assert summary["execution_id"] == "exec-123"
    assert summary["status"] == "FAILED"
    assert summary["duration_seconds"] == (completed_at - started_at).total_seconds()
    assert result.status == "FAILED"
    assert result.validation_errors


def test_export_patches_asset_manifest_with_hash_and_stats(tmp_path):
    exporter = _make_exporter(tmp_path)
    timestamp = datetime(2026, 7, 19, 12, 0, 0)

    manifest_content = json.dumps(
        {
            "execution_id": "exec-789",
            "entries": [
                {
                    "asset_type": "document",
                    "provider": "workflow",
                    "status": "SUCCESS",
                    "path": "research.md",
                    "timestamp": "2026-07-19T12:00:00Z",
                    "hash": "",
                }
            ],
        }
    )

    result = exporter.export(
        execution_id="exec-789",
        workflow_id="wf",
        workflow_name="Workflow",
        topic="Hash Patch Test",
        artifacts=[
            WorkflowArtifact("research.md", "# Research content\n"),
            WorkflowArtifact("asset_manifest.json", manifest_content),
        ],
        step_statuses={"Research": "success"},
        started_at=timestamp,
        completed_at=timestamp,
    )

    output_folder = tmp_path / f"{timestamp.strftime('%Y-%m-%d_%H-%M-%S')}_hash-patch-test"
    patched = json.loads((output_folder / "asset_manifest.json").read_text(encoding="utf-8"))
    entry = patched["entries"][0]

    expected_hash = hashlib.sha256("# Research content\n".encode("utf-8")).hexdigest()
    assert entry["hash"] == expected_hash
    assert entry["size_bytes"] == len("# Research content\n".encode("utf-8"))
    assert entry["created_at"] is not None
    assert entry["last_modified_at"] is not None


def test_export_aggregates_step_metrics_and_cost_from_meta_artifacts(tmp_path):
    exporter = _make_exporter(tmp_path)
    timestamp = datetime(2026, 7, 19, 13, 0, 0)

    research_meta = json.dumps(
        {
            "step": "Research",
            "started_at": "2026-07-19T13:00:00+00:00",
            "finished_at": "2026-07-19T13:00:01+00:00",
            "duration_ms": 1000.0,
            "provider_metrics": {"provider": "openai", "model": "gpt-5.5", "call_count": 1},
            "cost_estimate": {"estimated_cost_usd": 0.05},
        }
    )
    writer_meta = json.dumps(
        {
            "step": "Writer",
            "started_at": "2026-07-19T13:00:01+00:00",
            "finished_at": "2026-07-19T13:00:03+00:00",
            "duration_ms": 2000.0,
            "provider_metrics": {"provider": "openai", "model": "gpt-5.5", "call_count": 1},
            "cost_estimate": {"estimated_cost_usd": 0.10},
        }
    )

    result = exporter.export(
        execution_id="exec-meta",
        workflow_id="wf",
        workflow_name="Workflow",
        topic="Meta Aggregation",
        artifacts=[
            WorkflowArtifact("research.md", "# Research\n"),
            WorkflowArtifact("__meta__/Research.json", research_meta),
            WorkflowArtifact("__meta__/Writer.json", writer_meta),
        ],
        step_statuses={"Research": "success", "Writer": "success"},
        started_at=timestamp,
        completed_at=timestamp,
    )

    assert "__meta__/Research.json" not in result.files_written
    assert "__meta__/Writer.json" not in result.files_written

    output_folder = tmp_path / f"{timestamp.strftime('%Y-%m-%d_%H-%M-%S')}_meta-aggregation"
    assert not (output_folder / "__meta__").exists()

    workflow_json = json.loads((output_folder / "workflow.json").read_text(encoding="utf-8"))
    assert workflow_json["step_metrics"]["Research"]["duration_ms"] == 1000.0
    assert workflow_json["step_metrics"]["Writer"]["duration_ms"] == 2000.0
    assert "Export" in workflow_json["step_metrics"]

    assert workflow_json["cost"]["per_step"]["Research"]["estimated_cost_usd"] == 0.05
    assert workflow_json["cost"]["per_step"]["Writer"]["estimated_cost_usd"] == 0.10
    assert workflow_json["cost"]["total_usd"] == 0.15

    summary = json.loads((output_folder / "summary.json").read_text(encoding="utf-8"))
    assert summary["estimated_cost_usd"] == 0.15
    assert summary["provider_usage"] == [{"provider": "openai", "model": "gpt-5.5", "call_count": 2}]


def test_export_status_success_when_all_required_assets_valid(tmp_path):
    exporter = _make_exporter(tmp_path)
    timestamp = datetime(2026, 7, 19, 14, 0, 0)

    voice_bytes = b"fake-mp3-bytes-not-empty"
    png_bytes = _valid_png_bytes()
    srt_text = _valid_srt_text()
    scene_plan = json.dumps({"topic": "T", "scenes": [], "metadata": {}})
    asset_manifest = json.dumps(
        {
            "execution_id": "exec-full",
            "entries": [
                {
                    "asset_type": "voice",
                    "provider": "openai-tts",
                    "status": "SUCCESS",
                    "duration": 12.5,
                    "path": "voice.mp3",
                    "timestamp": "2026-07-19T14:00:00Z",
                    "hash": "",
                    "model": "tts-1",
                }
            ],
        }
    )

    result = exporter.export(
        execution_id="exec-full",
        workflow_id="wf",
        workflow_name="Workflow",
        topic="Full Export",
        artifacts=[
            WorkflowArtifact("research.md", "# Research\n"),
            WorkflowArtifact("script.md", "# Script\n"),
            WorkflowArtifact("voice.mp3", "", content_bytes=voice_bytes),
            WorkflowArtifact("thumbnail.png", "", content_bytes=png_bytes),
            WorkflowArtifact("subtitles.srt", srt_text),
            WorkflowArtifact("scene_plan.json", scene_plan),
            WorkflowArtifact("asset_manifest.json", asset_manifest),
        ],
        step_statuses={"Research": "success"},
        started_at=timestamp,
        completed_at=timestamp,
    )

    assert result.status == "SUCCESS"
    assert result.validation_errors == []

    output_folder = tmp_path / f"{timestamp.strftime('%Y-%m-%d_%H-%M-%S')}_full-export"
    summary = json.loads((output_folder / "summary.json").read_text(encoding="utf-8"))
    assert summary["status"] == "SUCCESS"
    assert summary["asset_count"] == 1
    assert summary["success_count"] == 1
    assert summary["failure_count"] == 0


def test_folder_name_falls_back_to_untitled_for_empty_topic(tmp_path):
    exporter = _make_exporter(tmp_path)
    timestamp = datetime(2026, 1, 1, 0, 0, 0)

    result = exporter.export(
        execution_id="exec-456",
        workflow_id="wf",
        workflow_name="Workflow",
        topic="   ",
        artifacts=[],
        step_statuses={},
        started_at=timestamp,
        completed_at=timestamp,
    )

    assert result.output_folder == str(tmp_path / "2026-01-01_00-00-00_untitled")
