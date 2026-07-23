from __future__ import annotations

import re
from datetime import datetime, timezone

from backend.schemas.assets import SubtitleAsset, VoiceAsset
from backend.schemas.research import ReviewedScript

_WORDS_PER_MINUTE = 150.0
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


class SubtitleGenerationService:
    """Derives an SRT subtitle track from the reviewed script by splitting it into
    sentences and timing each cue proportionally to its share of the narration.
    When a successful `VoiceAsset` with a real duration is available, cue timing
    is scaled to sum to that duration; otherwise falls back to a fixed reading
    rate. Purely mechanical — makes no provider/LLM call. Never raises."""

    def execute(self, reviewed_script: ReviewedScript, voice_asset: VoiceAsset) -> tuple[SubtitleAsset, str]:
        # Collapse all whitespace runs (including paragraph breaks) to single spaces before
        # splitting into sentences — otherwise a blank line landing between punctuation
        # marks ends up embedded inside a single cue's text, which SRT parsers (and
        # validate_subtitles()) read as a blank-line cue separator, corrupting the file.
        text = re.sub(r"\s+", " ", reviewed_script.revised_script).strip()
        if not text:
            return self._skipped("Reviewed script has no narration text"), ""

        sentences = [s.strip() for s in _SENTENCE_SPLIT_RE.split(text) if s.strip()]
        if not sentences:
            return self._skipped("Reviewed script produced no subtitle cues"), ""

        estimated_durations = [
            max(len(sentence.split()) / (_WORDS_PER_MINUTE / 60.0), 1.0) for sentence in sentences
        ]
        if voice_asset.status == "SUCCESS" and voice_asset.duration > 0:
            scale = voice_asset.duration / sum(estimated_durations)
            cue_durations = [duration * scale for duration in estimated_durations]
        else:
            cue_durations = estimated_durations

        srt_lines: list[str] = []
        cursor = 0.0
        for index, (sentence, duration) in enumerate(zip(sentences, cue_durations), start=1):
            start = cursor
            end = cursor + duration
            cursor = end
            srt_lines.append(
                f"{index}\n{self._format_timestamp(start)} --> {self._format_timestamp(end)}\n{sentence}\n"
            )

        srt_content = "\n".join(srt_lines)
        asset = SubtitleAsset(
            cue_count=len(sentences),
            generation_time=datetime.now(timezone.utc).isoformat(),
            status="SUCCESS",
        )
        return asset, srt_content

    def _format_timestamp(self, total_seconds: float) -> str:
        # Round to a single integer millisecond count first, then derive hours/minutes/
        # seconds/ms from it via chained divmod — rounding seconds and milliseconds
        # independently (as before) let a fractional part like .9996s round to "1000" ms
        # instead of carrying into the next second (e.g. "21,1000" instead of "22,000"),
        # which produced SRT timestamps that fail strict 3-digit-millisecond parsing.
        total_ms = int(round(total_seconds * 1000))
        hours, remainder_ms = divmod(total_ms, 3_600_000)
        minutes, remainder_ms = divmod(remainder_ms, 60_000)
        seconds, milliseconds = divmod(remainder_ms, 1000)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

    def _skipped(self, reason: str) -> SubtitleAsset:
        return SubtitleAsset(
            cue_count=0,
            generation_time=datetime.now(timezone.utc).isoformat(),
            status="SKIPPED",
            error=reason,
        )
