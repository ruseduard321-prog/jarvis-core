"""Pure, filesystem-reading validators run against a completed workflow export
folder before the export is allowed to be marked SUCCESS."""

from __future__ import annotations

import hashlib
import json
import re
import struct
from pathlib import Path

from pydantic import BaseModel, ValidationError

from backend.schemas.assets import AssetManifest

REQUIRED_FILES: tuple[str, ...] = (
    "workflow.json",
    "manifest.json",
    "asset_manifest.json",
    "voice.mp3",
    "thumbnail.png",
    "subtitles.srt",
    "scene_plan.json",
)

_SRT_TIMESTAMP = re.compile(r"^\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}$")


def validate_export(output_folder: Path) -> list[str]:
    """Task 5: required files exist, JSON files parse, markdown files are non-empty."""
    errors: list[str] = []

    for filename in REQUIRED_FILES:
        if not (output_folder / filename).exists():
            errors.append(f"missing required file: {filename}")

    for path in output_folder.glob("*.json"):
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            errors.append(f"invalid JSON in {path.name}: {exc}")

    for path in output_folder.glob("*.md"):
        try:
            content = path.read_text(encoding="utf-8")
        except OSError as exc:
            errors.append(f"unreadable markdown file {path.name}: {exc}")
            continue
        if not content.strip():
            errors.append(f"empty markdown file: {path.name}")

    return errors


def validate_voice(path: Path, duration: float) -> str | None:
    if not path.exists():
        return f"voice file missing: {path.name}"
    if path.stat().st_size == 0:
        return f"voice file is empty: {path.name}"
    if duration <= 0:
        return f"voice duration must be > 0, got {duration}"
    return None


def validate_thumbnail(path: Path) -> str | None:
    if not path.exists():
        return f"thumbnail file missing: {path.name}"
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        return f"thumbnail is not a valid PNG: {path.name}"
    if len(data) < 24:
        return f"thumbnail PNG too small to contain an IHDR chunk: {path.name}"
    width, height = struct.unpack(">II", data[16:24])
    if width <= 0 or height <= 0:
        return f"thumbnail has invalid dimensions {width}x{height}: {path.name}"
    return None


def validate_subtitles(path: Path) -> str | None:
    if not path.exists():
        return f"subtitles file missing: {path.name}"
    content = path.read_text(encoding="utf-8", errors="replace").strip()
    if not content:
        return f"subtitles file is empty: {path.name}"

    blocks = re.split(r"\n\s*\n", content)
    expected_index = 1
    for block in blocks:
        lines = [line for line in block.splitlines() if line.strip()]
        if len(lines) < 2:
            return f"malformed SRT cue block near index {expected_index}: {path.name}"
        try:
            cue_index = int(lines[0].strip())
        except ValueError:
            return f"expected numeric cue index at block {expected_index}, got {lines[0]!r}: {path.name}"
        if cue_index != expected_index:
            return f"non-sequential SRT cue index: expected {expected_index}, got {cue_index}: {path.name}"
        if not _SRT_TIMESTAMP.match(lines[1].strip()):
            return f"malformed SRT timestamp line in cue {cue_index}: {path.name}"
        expected_index += 1
    return None


def validate_json_schema(path: Path, model: type[BaseModel]) -> str | None:
    if not path.exists():
        return f"JSON file missing: {path.name}"
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        model.model_validate(raw)
    except (json.JSONDecodeError, ValidationError) as exc:
        return f"{path.name} does not match expected schema: {exc}"
    return None


def validate_manifest_consistency(manifest: AssetManifest, output_folder: Path) -> list[str]:
    errors: list[str] = []
    for entry in manifest.entries:
        asset_path = output_folder / entry.path
        if not asset_path.exists():
            errors.append(f"manifest entry {entry.asset_type!r} references missing file: {entry.path}")
            continue
        if entry.hash:
            actual_hash = hashlib.sha256(asset_path.read_bytes()).hexdigest()
            if actual_hash != entry.hash:
                errors.append(f"manifest hash mismatch for {entry.path}: recorded {entry.hash}, actual {actual_hash}")
    return errors
