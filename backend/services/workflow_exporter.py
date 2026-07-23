from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.core.config import Settings
from backend.core.cost_tracker import CostTracker
from backend.core.workflow_engine_models import WorkflowArtifact
from backend.schemas.assets import AssetManifest, ScenePlan
from backend.services.workflow_export_validators import (
    validate_export,
    validate_json_schema,
    validate_manifest_consistency,
    validate_subtitles,
    validate_thumbnail,
    validate_voice,
)

FUTURE_ASSETS = ["video.mp4"]

_META_PREFIX = "__meta__/"


@dataclass
class ExportResult:
    """Where a workflow's artifacts landed on disk, and what was written there."""

    output_folder: str
    files_written: list[str]
    status: str = "SUCCESS"
    validation_errors: list[str] = field(default_factory=list)


class WorkflowExporter:
    """Writes every step's real artifacts to disk, then patches integrity metadata
    (hash/size/timestamps) into asset_manifest.json, aggregates per-step timing and
    cost carried on `__meta__/` artifacts into workflow.json, validates the export,
    and writes summary.json. `__meta__/` artifacts are a side-channel used only by
    this exporter — they are never written to disk or listed in manifest.json."""

    def __init__(self, settings: Settings, cost_tracker: CostTracker | None = None) -> None:
        self._settings = settings
        self._cost_tracker = cost_tracker or CostTracker()

    def export(
        self,
        *,
        execution_id: str,
        workflow_id: str,
        workflow_name: str,
        topic: str,
        artifacts: list[WorkflowArtifact],
        step_statuses: dict[str, str],
        started_at: datetime,
        completed_at: datetime,
    ) -> ExportResult:
        export_started_at = datetime.now(timezone.utc)
        real_artifacts, meta_by_step = self._split_artifacts(artifacts)

        folder_name = self._build_folder_name(topic, completed_at)
        output_root = Path(self._settings.workflow_output_root)
        output_folder = output_root / folder_name
        output_folder.mkdir(parents=True, exist_ok=True)

        files_written: list[str] = []
        file_stats: dict[str, dict[str, Any]] = {}
        for artifact in real_artifacts:
            path = output_folder / artifact.filename
            data = artifact.content_bytes if artifact.content_bytes is not None else artifact.content.encode("utf-8")
            path.write_bytes(data)
            files_written.append(artifact.filename)
            stat = path.stat()
            file_stats[artifact.filename] = {
                "hash": hashlib.sha256(data).hexdigest(),
                "size_bytes": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc).isoformat(),
                "last_modified_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
            }

        self._patch_asset_manifest(output_folder, file_stats)

        step_metrics = {
            step: {
                "started_at": payload.get("started_at"),
                "finished_at": payload.get("finished_at"),
                "duration_ms": payload.get("duration_ms"),
            }
            for step, payload in meta_by_step.items()
        }
        cost = self._aggregate_cost(meta_by_step)

        # workflow.json and manifest.json are themselves among validate_export's
        # REQUIRED_FILES, so they must exist on disk before validation runs. Write a
        # provisional workflow.json now (status/validation_errors filled in below, once
        # known) purely so the export-completeness check can see it.
        workflow_json = {
            "workflow_id": workflow_id,
            "workflow_name": workflow_name,
            "execution_id": execution_id,
            "topic": topic,
            "started_at": started_at.isoformat(),
            "completed_at": completed_at.isoformat(),
            "step_status": step_statuses,
            "step_metrics": step_metrics,
            "cost": cost,
            "status": "PENDING",
            "validation_errors": [],
        }
        (output_folder / "workflow.json").write_text(json.dumps(workflow_json, indent=2), encoding="utf-8")
        files_written.append("workflow.json")

        manifest = {
            "files": [{"name": name, "bytes": (output_folder / name).stat().st_size} for name in files_written],
            "future_assets": FUTURE_ASSETS,
        }
        (output_folder / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        files_written.append("manifest.json")

        validation_errors = self._run_validation(output_folder)
        status = "SUCCESS" if not validation_errors else "FAILED"

        export_finished_at = datetime.now(timezone.utc)
        step_metrics["Export"] = {
            "started_at": export_started_at.isoformat(),
            "finished_at": export_finished_at.isoformat(),
            "duration_ms": round((export_finished_at - export_started_at).total_seconds() * 1000, 2),
        }
        workflow_json["step_metrics"] = step_metrics
        workflow_json["status"] = status
        workflow_json["validation_errors"] = validation_errors
        (output_folder / "workflow.json").write_text(json.dumps(workflow_json, indent=2), encoding="utf-8")

        asset_count, success_count, failure_count = self._asset_counts(output_folder)
        summary = {
            "workflow_id": workflow_id,
            "execution_id": execution_id,
            "topic": topic,
            "status": status,
            "duration_seconds": round((completed_at - started_at).total_seconds(), 3),
            "provider_usage": self._aggregate_provider_usage(meta_by_step),
            "asset_count": asset_count,
            "success_count": success_count,
            "failure_count": failure_count,
            "estimated_cost_usd": cost["total_usd"],
        }
        (output_folder / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        files_written.append("summary.json")

        return ExportResult(
            output_folder=str(output_folder),
            files_written=files_written,
            status=status,
            validation_errors=validation_errors,
        )

    def _split_artifacts(
        self, artifacts: list[WorkflowArtifact]
    ) -> tuple[list[WorkflowArtifact], dict[str, dict[str, Any]]]:
        real_artifacts: list[WorkflowArtifact] = []
        meta_by_step: dict[str, dict[str, Any]] = {}
        for artifact in artifacts:
            if not artifact.filename.startswith(_META_PREFIX):
                real_artifacts.append(artifact)
                continue
            try:
                payload = json.loads(artifact.content)
            except (json.JSONDecodeError, TypeError):
                continue
            step_name = payload.get("step") or artifact.filename[len(_META_PREFIX) : -len(".json")]
            meta_by_step[step_name] = payload
        return real_artifacts, meta_by_step

    def _patch_asset_manifest(self, output_folder: Path, file_stats: dict[str, dict[str, Any]]) -> None:
        manifest_path = output_folder / "asset_manifest.json"
        if not manifest_path.exists():
            return
        try:
            manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return
        for entry in manifest_data.get("entries", []):
            stats = file_stats.get(entry.get("path"))
            if not stats:
                continue
            entry["hash"] = stats["hash"]
            entry["size_bytes"] = stats["size_bytes"]
            entry["created_at"] = stats["created_at"]
            entry["last_modified_at"] = stats["last_modified_at"]
        manifest_path.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")

    def _aggregate_cost(self, meta_by_step: dict[str, dict[str, Any]]) -> dict[str, Any]:
        per_step: dict[str, Any] = {}
        total = 0.0
        for step, payload in meta_by_step.items():
            cost_estimate = payload.get("cost_estimate")
            if not cost_estimate:
                continue
            per_step[step] = cost_estimate
            total += float(cost_estimate.get("estimated_cost_usd", 0.0))
        return {"per_step": per_step, "total_usd": round(total, 6)}

    def _aggregate_provider_usage(self, meta_by_step: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
        usage: dict[tuple[str, str], int] = {}
        for payload in meta_by_step.values():
            provider_metrics = payload.get("provider_metrics")
            if not provider_metrics:
                continue
            call_count = provider_metrics.get("call_count") or 0
            if not call_count:
                continue
            key = (provider_metrics.get("provider", ""), provider_metrics.get("model", ""))
            usage[key] = usage.get(key, 0) + call_count
        return [
            {"provider": provider, "model": model, "call_count": count} for (provider, model), count in usage.items()
        ]

    def _asset_counts(self, output_folder: Path) -> tuple[int, int, int]:
        manifest_path = output_folder / "asset_manifest.json"
        if not manifest_path.exists():
            return 0, 0, 0
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return 0, 0, 0
        entries = data.get("entries", [])
        success_count = sum(1 for entry in entries if entry.get("status") == "SUCCESS")
        failure_count = sum(1 for entry in entries if entry.get("status") == "FAILED")
        return len(entries), success_count, failure_count

    def _find_asset_entry(self, output_folder: Path, asset_type: str) -> dict[str, Any] | None:
        manifest_path = output_folder / "asset_manifest.json"
        if not manifest_path.exists():
            return None
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
        for entry in data.get("entries", []):
            if entry.get("asset_type") == asset_type:
                return entry
        return None

    def _run_validation(self, output_folder: Path) -> list[str]:
        errors = list(validate_export(output_folder))

        voice_path = output_folder / "voice.mp3"
        if voice_path.exists():
            voice_entry = self._find_asset_entry(output_folder, "voice")
            voice_duration = float(voice_entry.get("duration") or 0.0) if voice_entry else 0.0
            voice_error = validate_voice(voice_path, voice_duration)
            if voice_error:
                errors.append(voice_error)

        thumbnail_path = output_folder / "thumbnail.png"
        if thumbnail_path.exists():
            thumbnail_error = validate_thumbnail(thumbnail_path)
            if thumbnail_error:
                errors.append(thumbnail_error)

        subtitles_path = output_folder / "subtitles.srt"
        if subtitles_path.exists():
            subtitles_error = validate_subtitles(subtitles_path)
            if subtitles_error:
                errors.append(subtitles_error)

        scene_plan_path = output_folder / "scene_plan.json"
        if scene_plan_path.exists():
            schema_error = validate_json_schema(scene_plan_path, ScenePlan)
            if schema_error:
                errors.append(schema_error)

        asset_manifest_path = output_folder / "asset_manifest.json"
        if asset_manifest_path.exists():
            schema_error = validate_json_schema(asset_manifest_path, AssetManifest)
            if schema_error:
                errors.append(schema_error)
            else:
                manifest = AssetManifest.model_validate(json.loads(asset_manifest_path.read_text(encoding="utf-8")))
                errors.extend(validate_manifest_consistency(manifest, output_folder))

        return errors

    def _build_folder_name(self, topic: str, timestamp: datetime) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", topic.strip().lower()).strip("-") or "untitled"
        return f"{timestamp.strftime('%Y-%m-%d_%H-%M-%S')}_{slug}"
