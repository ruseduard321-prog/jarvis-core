from __future__ import annotations

import hashlib

from backend.services.asset_packaging_service import AssetPackagingService


def test_build_entry_hashes_bytes_content():
    service = AssetPackagingService()
    content = b"fake-audio-bytes"

    entry = service.build_entry(
        asset_type="voice",
        provider="openai-tts",
        status="SUCCESS",
        path="voice.mp3",
        timestamp="2026-01-01T00:00:00Z",
        content=content,
    )

    assert entry.hash == hashlib.sha256(content).hexdigest()


def test_build_entry_hashes_text_content():
    service = AssetPackagingService()
    content = "some text content"

    entry = service.build_entry(
        asset_type="scene_plan",
        provider="workflow",
        status="SUCCESS",
        path="scene_plan.json",
        timestamp="2026-01-01T00:00:00Z",
        content=content,
    )

    assert entry.hash == hashlib.sha256(content.encode("utf-8")).hexdigest()


def test_build_entry_empty_hash_when_no_content():
    service = AssetPackagingService()

    entry = service.build_entry(
        asset_type="thumbnail",
        provider="none",
        status="SKIPPED",
        path="thumbnail.png",
        timestamp="2026-01-01T00:00:00Z",
        error="No thumbnail prompt was produced",
    )

    assert entry.hash == ""
    assert entry.error == "No thumbnail prompt was produced"


def test_build_entry_passes_through_provider_metric_fields():
    service = AssetPackagingService()

    entry = service.build_entry(
        asset_type="voice",
        provider="openai-tts",
        status="SUCCESS",
        path="voice.mp3",
        timestamp="2026-01-01T00:00:00Z",
        model="tts-1-hd",
        generation_duration_ms=842.5,
        retry_count=2,
    )

    assert entry.model == "tts-1-hd"
    assert entry.generation_duration_ms == 842.5
    assert entry.retry_count == 2


def test_build_entry_defaults_provider_metric_fields_when_omitted():
    service = AssetPackagingService()

    entry = service.build_entry(
        asset_type="thumbnail",
        provider="openai-image",
        status="SUCCESS",
        path="thumbnail.png",
        timestamp="2026-01-01T00:00:00Z",
    )

    assert entry.model == ""
    assert entry.generation_duration_ms == 0.0
    assert entry.retry_count == 0


def test_build_manifest_aggregates_entries():
    service = AssetPackagingService()
    entries = [
        service.build_entry(
            asset_type="voice", provider="openai-tts", status="SUCCESS", path="voice.mp3", timestamp="t1"
        ),
        service.build_entry(
            asset_type="thumbnail", provider="none", status="SKIPPED", path="thumbnail.png", timestamp="t2"
        ),
    ]

    manifest = service.build_manifest("exec-123", entries)

    assert manifest.execution_id == "exec-123"
    assert manifest.entries == entries
    assert [e.status for e in manifest.entries] == ["SUCCESS", "SKIPPED"]
