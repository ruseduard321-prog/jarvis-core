from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from backend.core.workflow_engine_models import WorkflowArtifact
from backend.schemas.assets import AssetManifest, BrollPlan, MusicPlan, ScenePlan, ScenePromptSet
from backend.schemas.composition import CompositionPlan
from backend.schemas.media import MediaPackage
from backend.schemas.research import PublishingPackage, ResearchPackage, ReviewedScript, ScriptDraft
from backend.schemas.strategy import StrategyPackage
from backend.schemas.timeline import TimelinePlan
from backend.schemas.visual_identity import VisualIdentityContext


def _bulleted(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items) if items else "- (none)"


def build_step_metrics_artifact(
    name: str,
    started_at: datetime,
    finished_at: datetime,
    provider_metrics: dict[str, Any] | None = None,
    cost_estimate: dict[str, Any] | None = None,
) -> WorkflowArtifact:
    """Builds the `__meta__/<StepName>.json` artifact every `WorkflowStep.run()` appends
    on success. `WorkflowExporter` recognizes the `__meta__/` prefix, strips these entries
    out of the real on-disk file list, and folds their contents into `workflow.json` —
    the only channel available to hand step-level timing/provider/cost data to the
    exporter without changing `WorkflowStepResult` or the engine's control flow."""
    duration_ms = round((finished_at - started_at).total_seconds() * 1000, 2)
    payload = {
        "step": name,
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "duration_ms": duration_ms,
        "provider_metrics": provider_metrics,
        "cost_estimate": cost_estimate,
    }
    return WorkflowArtifact(filename=f"__meta__/{name}.json", content=json.dumps(payload, indent=2))


def render_research_md(package: ResearchPackage) -> str:
    findings = "\n\n".join(
        f"### {finding.title}\n{finding.details}\nSources: {', '.join(finding.source_urls) or '(none)'}"
        for finding in package.findings
    ) or "(no findings)"
    sources = "\n".join(f"- [{source.title or source.url}]({source.url})" for source in package.sources) or "- (none)"
    return (
        f"# Research: {package.topic}\n\n"
        f"## Executive Summary\n{package.executive_summary}\n\n"
        f"## Findings\n{findings}\n\n"
        f"## Key Facts\n{_bulleted(package.key_facts)}\n\n"
        f"## Timeline\n{_bulleted(package.timeline)}\n\n"
        f"## Recommended Angle\n{package.recommended_angle}\n\n"
        f"## Open Questions\n{_bulleted(package.open_questions)}\n\n"
        f"## Sources\n{sources}\n"
    )


def render_strategy_md(package: StrategyPackage) -> str:
    return (
        f"# Strategy: {package.topic}\n\n"
        f"## Target Audience\n{package.target_audience}\n\n"
        f"## Positioning\n{package.positioning}\n\n"
        f"## Hook\n{package.hook}\n\n"
        f"## Retention Strategy\n{_bulleted(package.retention_strategy)}\n\n"
        f"## Emotional Arc\n{_bulleted(package.emotional_arc)}\n\n"
        f"## Pacing\n{package.pacing}\n"
    )


def render_script_md(draft: ScriptDraft) -> str:
    sections = "\n\n".join(draft.sections) or "(no sections)"
    return (
        f"# Script: {draft.topic}\n\n"
        f"**Estimated duration:** {draft.estimated_duration}\n\n"
        f"## Hook\n{draft.hook}\n\n"
        f"## Intro\n{draft.intro}\n\n"
        f"## Sections\n{sections}\n\n"
        f"## Outro\n{draft.outro}\n\n"
        f"## Call To Action\n{draft.call_to_action}\n\n"
        f"## Scene Markers\n{_bulleted(draft.scene_markers)}\n\n"
        f"## Narration Script\n{draft.narration_script}\n"
    )


def render_review_md(reviewed: ReviewedScript) -> str:
    return (
        f"# Review: {reviewed.topic}\n\n"
        f"**Status:** {reviewed.status}\n\n"
        f"**Quality score:** {reviewed.quality_score}\n"
        f"**Readability score:** {reviewed.readability_score}\n"
        f"**Engagement score:** {reviewed.engagement_score}\n\n"
        f"## Change Summary\n{_bulleted(reviewed.change_summary)}\n\n"
        f"## Factual Notes\n{_bulleted(reviewed.factual_notes)}\n\n"
        f"## Revised Script\n{reviewed.revised_script}\n"
    )


def render_media_prompts_md(media: MediaPackage) -> str:
    return (
        "# Media Prompts\n\n"
        f"## Scene Prompts\n{_bulleted(media.scene_prompts)}\n\n"
        f"## B-Roll Prompts\n{_bulleted(media.b_roll_prompts)}\n\n"
        f"## Image Prompts\n{_bulleted(media.image_prompts)}\n\n"
        f"## Animation Prompts\n{_bulleted(media.animation_prompts)}\n\n"
        f"## Voice-Over Notes\n{_bulleted(media.voice_over_notes)}\n\n"
        f"## Music Direction\n{media.music_direction}\n"
    )


def render_thumbnail_prompt_txt(media: MediaPackage) -> str:
    return media.thumbnail_prompt


def render_title_md(package: PublishingPackage) -> str:
    return f"# {package.youtube_title}\n"


def render_description_md(package: PublishingPackage) -> str:
    chapters = _bulleted(package.youtube_chapters)
    return f"{package.youtube_description}\n\n## Chapters\n{chapters}\n\n## SEO Keywords\n{_bulleted(package.seo_keywords)}\n"


def render_hashtags_md(package: PublishingPackage) -> str:
    tags = " ".join(f"#{tag.replace(' ', '')}" for tag in package.youtube_tags) or "(no tags)"
    return f"# Hashtags\n\n{tags}\n"


def render_scene_plan_json(scene_plan: ScenePlan) -> str:
    return json.dumps(scene_plan.model_dump(), indent=2)


def render_scene_prompts_json(scene_prompts: ScenePromptSet) -> str:
    return json.dumps(scene_prompts.model_dump(), indent=2)


def render_broll_plan_json(broll_plan: BrollPlan) -> str:
    return json.dumps(broll_plan.model_dump(), indent=2)


def render_timeline_plan_json(timeline_plan: TimelinePlan) -> str:
    return json.dumps(timeline_plan.model_dump(), indent=2)


def render_composition_plan_json(composition_plan: CompositionPlan) -> str:
    return json.dumps(composition_plan.model_dump(), indent=2)


def render_music_md(music_plan: MusicPlan) -> str:
    return (
        "# Music Direction\n\n"
        f"**Genre:** {music_plan.genre or '(unspecified)'}\n\n"
        f"**Mood:** {music_plan.mood or '(unspecified)'}\n\n"
        f"**Tempo:** {music_plan.tempo or '(unspecified)'}\n\n"
        f"**Energy:** {music_plan.energy or '(unspecified)'}\n\n"
        f"## Reference\n{music_plan.reference or '(none)'}\n"
    )


def render_asset_manifest_json(manifest: AssetManifest) -> str:
    return json.dumps(manifest.model_dump(), indent=2)


def render_visual_identity_json(visual_identity_context: VisualIdentityContext) -> str:
    return json.dumps(visual_identity_context.model_dump(), indent=2)
