from __future__ import annotations

import hashlib

from backend.schemas.assets import AssetManifest, AssetManifestEntry, AssetStatus


class AssetPackagingService:
    """Aggregates the status of every asset produced across the workflow into one
    manifest. Purely mechanical bookkeeping — makes no provider/LLM call and never
    raises; a hashing failure simply yields an empty hash."""

    def build_entry(
        self,
        *,
        asset_type: str,
        provider: str,
        status: AssetStatus,
        path: str,
        timestamp: str,
        content: bytes | str | None = None,
        duration: float | None = None,
        error: str | None = None,
        model: str = "",
        generation_duration_ms: float = 0.0,
        retry_count: int = 0,
    ) -> AssetManifestEntry:
        return AssetManifestEntry(
            asset_type=asset_type,
            provider=provider,
            status=status,
            duration=duration,
            path=path,
            timestamp=timestamp,
            hash=self._hash_content(content),
            error=error,
            model=model,
            generation_duration_ms=generation_duration_ms,
            retry_count=retry_count,
        )

    def build_manifest(
        self,
        execution_id: str,
        entries: list[AssetManifestEntry],
        *,
        total_estimated_cost_usd: float = 0.0,
        maximum_video_budget_usd: float = 0.0,
    ) -> AssetManifest:
        # F3: budget_status is derived here, not passed in, so there is exactly one
        # place that decides what "within budget" means for the final manifest —
        # the same discipline every other derived status field in this codebase
        # follows (e.g. SceneImageSet's success/partial/failed rollup).
        budget_status = "exceeded" if total_estimated_cost_usd > maximum_video_budget_usd > 0 else "within_budget"
        return AssetManifest(
            execution_id=execution_id,
            entries=entries,
            total_estimated_cost_usd=round(total_estimated_cost_usd, 6),
            maximum_video_budget_usd=maximum_video_budget_usd,
            budget_status=budget_status,
        )

    def _hash_content(self, content: bytes | str | None) -> str:
        if not content:
            return ""
        data = content if isinstance(content, bytes) else content.encode("utf-8")
        return hashlib.sha256(data).hexdigest()
