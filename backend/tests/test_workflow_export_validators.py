from __future__ import annotations

import hashlib
import json
import struct

from backend.schemas.assets import AssetManifest, AssetManifestEntry, ScenePlan
from backend.services.workflow_export_validators import (
    REQUIRED_FILES,
    validate_export,
    validate_json_schema,
    validate_manifest_consistency,
    validate_subtitles,
    validate_thumbnail,
    validate_voice,
)


def _write_all_required_files(folder) -> None:
    for filename in REQUIRED_FILES:
        if filename.endswith(".json"):
            (folder / filename).write_text("{}", encoding="utf-8")
        else:
            (folder / filename).write_bytes(b"x")


def _valid_png_bytes() -> bytes:
    return b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR" + struct.pack(">II", 64, 32) + b"\x00" * 17


def _valid_srt_text() -> str:
    return "1\n00:00:00,000 --> 00:00:01,000\nHello\n\n2\n00:00:01,000 --> 00:00:02,000\nWorld\n"


# ---- validate_export -------------------------------------------------------


def test_validate_export_reports_missing_required_files(tmp_path):
    errors = validate_export(tmp_path)

    assert len(errors) == len(REQUIRED_FILES)
    assert all("missing required file" in error for error in errors)


def test_validate_export_passes_when_all_required_files_present_and_valid(tmp_path):
    _write_all_required_files(tmp_path)

    errors = validate_export(tmp_path)

    assert errors == []


def test_validate_export_reports_invalid_json(tmp_path):
    _write_all_required_files(tmp_path)
    (tmp_path / "workflow.json").write_text("{not valid json", encoding="utf-8")

    errors = validate_export(tmp_path)

    assert any("invalid JSON in workflow.json" in error for error in errors)


def test_validate_export_reports_empty_markdown_file(tmp_path):
    _write_all_required_files(tmp_path)
    (tmp_path / "notes.md").write_text("   \n  ", encoding="utf-8")

    errors = validate_export(tmp_path)

    assert any("empty markdown file: notes.md" in error for error in errors)


# ---- validate_voice ---------------------------------------------------------


def test_validate_voice_missing_file(tmp_path):
    error = validate_voice(tmp_path / "voice.mp3", 10.0)

    assert error is not None
    assert "missing" in error


def test_validate_voice_empty_file(tmp_path):
    path = tmp_path / "voice.mp3"
    path.write_bytes(b"")

    error = validate_voice(path, 10.0)

    assert error is not None
    assert "empty" in error


def test_validate_voice_zero_duration(tmp_path):
    path = tmp_path / "voice.mp3"
    path.write_bytes(b"data")

    error = validate_voice(path, 0.0)

    assert error is not None
    assert "duration" in error


def test_validate_voice_valid(tmp_path):
    path = tmp_path / "voice.mp3"
    path.write_bytes(b"data")

    assert validate_voice(path, 12.5) is None


# ---- validate_thumbnail ------------------------------------------------------


def test_validate_thumbnail_missing_file(tmp_path):
    error = validate_thumbnail(tmp_path / "thumbnail.png")

    assert error is not None
    assert "missing" in error


def test_validate_thumbnail_not_a_png(tmp_path):
    path = tmp_path / "thumbnail.png"
    path.write_bytes(b"not-a-png" * 5)

    error = validate_thumbnail(path)

    assert error is not None
    assert "not a valid PNG" in error


def test_validate_thumbnail_invalid_dimensions(tmp_path):
    path = tmp_path / "thumbnail.png"
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR" + struct.pack(">II", 0, 0) + b"\x00" * 17)

    error = validate_thumbnail(path)

    assert error is not None
    assert "invalid dimensions" in error


def test_validate_thumbnail_valid(tmp_path):
    path = tmp_path / "thumbnail.png"
    path.write_bytes(_valid_png_bytes())

    assert validate_thumbnail(path) is None


# ---- validate_subtitles -------------------------------------------------------


def test_validate_subtitles_missing_file(tmp_path):
    error = validate_subtitles(tmp_path / "subtitles.srt")

    assert error is not None
    assert "missing" in error


def test_validate_subtitles_empty_file(tmp_path):
    path = tmp_path / "subtitles.srt"
    path.write_text("   ", encoding="utf-8")

    error = validate_subtitles(path)

    assert error is not None
    assert "empty" in error


def test_validate_subtitles_non_sequential_cue_index(tmp_path):
    path = tmp_path / "subtitles.srt"
    path.write_text("1\n00:00:00,000 --> 00:00:01,000\nHello\n\n3\n00:00:01,000 --> 00:00:02,000\nWorld\n", encoding="utf-8")

    error = validate_subtitles(path)

    assert error is not None
    assert "non-sequential" in error


def test_validate_subtitles_malformed_timestamp(tmp_path):
    path = tmp_path / "subtitles.srt"
    path.write_text("1\nnot-a-timestamp\nHello\n", encoding="utf-8")

    error = validate_subtitles(path)

    assert error is not None
    assert "malformed SRT timestamp" in error


def test_validate_subtitles_valid(tmp_path):
    path = tmp_path / "subtitles.srt"
    path.write_text(_valid_srt_text(), encoding="utf-8")

    assert validate_subtitles(path) is None


# ---- validate_json_schema -----------------------------------------------------


def test_validate_json_schema_missing_file(tmp_path):
    error = validate_json_schema(tmp_path / "scene_plan.json", ScenePlan)

    assert error is not None
    assert "missing" in error


def test_validate_json_schema_invalid_shape(tmp_path):
    path = tmp_path / "scene_plan.json"
    path.write_text(json.dumps({"scenes": "not-a-list"}), encoding="utf-8")

    error = validate_json_schema(path, ScenePlan)

    assert error is not None
    assert "does not match expected schema" in error


def test_validate_json_schema_valid(tmp_path):
    path = tmp_path / "scene_plan.json"
    path.write_text(json.dumps({"topic": "T", "scenes": [], "metadata": {}}), encoding="utf-8")

    assert validate_json_schema(path, ScenePlan) is None


# ---- validate_manifest_consistency ---------------------------------------------


def test_validate_manifest_consistency_missing_asset_file(tmp_path):
    manifest = AssetManifest(
        execution_id="exec-1",
        entries=[
            AssetManifestEntry(
                asset_type="voice", status="SUCCESS", path="voice.mp3", timestamp="t", hash="deadbeef"
            )
        ],
    )

    errors = validate_manifest_consistency(manifest, tmp_path)

    assert any("missing file" in error for error in errors)


def test_validate_manifest_consistency_hash_mismatch(tmp_path):
    (tmp_path / "voice.mp3").write_bytes(b"real-bytes")
    manifest = AssetManifest(
        execution_id="exec-1",
        entries=[
            AssetManifestEntry(
                asset_type="voice", status="SUCCESS", path="voice.mp3", timestamp="t", hash="wronghash"
            )
        ],
    )

    errors = validate_manifest_consistency(manifest, tmp_path)

    assert any("hash mismatch" in error for error in errors)


def test_validate_manifest_consistency_passes_with_matching_hash(tmp_path):
    content = b"real-bytes"
    (tmp_path / "voice.mp3").write_bytes(content)
    manifest = AssetManifest(
        execution_id="exec-1",
        entries=[
            AssetManifestEntry(
                asset_type="voice",
                status="SUCCESS",
                path="voice.mp3",
                timestamp="t",
                hash=hashlib.sha256(content).hexdigest(),
            )
        ],
    )

    assert validate_manifest_consistency(manifest, tmp_path) == []


def test_validate_manifest_consistency_skips_empty_hash(tmp_path):
    (tmp_path / "voice.mp3").write_bytes(b"real-bytes")
    manifest = AssetManifest(
        execution_id="exec-1",
        entries=[AssetManifestEntry(asset_type="voice", status="SUCCESS", path="voice.mp3", timestamp="t", hash="")],
    )

    assert validate_manifest_consistency(manifest, tmp_path) == []
