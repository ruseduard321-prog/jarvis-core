from __future__ import annotations

from backend.schemas.assets import VoiceAsset
from backend.schemas.research import ReviewedScript
from backend.services.subtitle_generation_service import SubtitleGenerationService


def _reviewed_script(text: str) -> ReviewedScript:
    return ReviewedScript(
        topic="Test Topic",
        revised_script=text,
        quality_score=90.0,
        readability_score=90.0,
        engagement_score=90.0,
        status="success",
        metadata={"status": "success"},
    )


def _voice_asset(duration: float = 0.0, status: str = "SUCCESS") -> VoiceAsset:
    return VoiceAsset(
        provider="fake-tts",
        duration=duration,
        generation_time="2026-01-01T00:00:00Z",
        status=status,
    )


def test_execute_skips_when_script_is_empty():
    service = SubtitleGenerationService()

    asset, srt = service.execute(_reviewed_script(""), _voice_asset(duration=10.0))

    assert asset.status == "SKIPPED"
    assert srt == ""


def test_execute_produces_one_cue_per_sentence_with_increasing_timestamps():
    service = SubtitleGenerationService()
    text = "This is the first sentence. This is the second sentence! Is this the third?"

    asset, srt = service.execute(_reviewed_script(text), _voice_asset(duration=0.0, status="SKIPPED"))

    assert asset.status == "SUCCESS"
    assert asset.cue_count == 3
    assert srt.count("-->") == 3
    assert "1\n00:00:00,000 -->" in srt

    cue_starts = [line for line in srt.splitlines() if "-->" in line]
    assert len(cue_starts) == 3


def test_execute_never_produces_duplicate_or_backwards_timestamps():
    service = SubtitleGenerationService()
    text = " ".join(f"Sentence number {i}." for i in range(1, 6))

    _, srt = service.execute(_reviewed_script(text), _voice_asset(duration=0.0, status="SKIPPED"))

    timestamps = [line.split(" --> ") for line in srt.splitlines() if "-->" in line]
    starts = [start for start, _ in timestamps]
    assert starts == sorted(starts)
    assert len(set(starts)) == len(starts)


def _timestamp_to_seconds(timestamp: str) -> float:
    hms, millis = timestamp.split(",")
    hours, minutes, seconds = (int(part) for part in hms.split(":"))
    return hours * 3600 + minutes * 60 + seconds + int(millis) / 1000.0


def test_execute_scales_cues_to_sum_to_real_voice_asset_duration():
    service = SubtitleGenerationService()
    text = " ".join(f"This is sentence number {i} in the narration." for i in range(1, 8))
    voice_asset = _voice_asset(duration=42.0, status="SUCCESS")

    asset, srt = service.execute(_reviewed_script(text), voice_asset)

    assert asset.status == "SUCCESS"
    last_cue_end = [line for line in srt.splitlines() if "-->" in line][-1].split(" --> ")[1]
    assert _timestamp_to_seconds(last_cue_end) == 42.0


def test_execute_falls_back_to_fixed_rate_when_voice_generation_failed():
    service = SubtitleGenerationService()
    text = "One sentence. Another sentence."

    asset, srt = service.execute(_reviewed_script(text), _voice_asset(duration=0.0, status="FAILED"))

    assert asset.status == "SUCCESS"
    last_cue_end = [line for line in srt.splitlines() if "-->" in line][-1].split(" --> ")[1]
    # Falls back to the fixed reading-rate estimate: two 1-word-count-floored
    # cues of at least 1 second each, well below any real narration duration.
    assert _timestamp_to_seconds(last_cue_end) < 10.0
