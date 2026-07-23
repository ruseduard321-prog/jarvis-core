from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ResearchPackageRequest(BaseModel):
    """Request payload for generating a research package."""

    topic: str = Field(description="Topic to research")
    constraints: str | None = Field(default=None, description="Optional research constraints")


class ResearchSource(BaseModel):
    """Normalized source descriptor used in research package outputs."""

    title: str | None = Field(default=None, description="Source title")
    url: str = Field(description="Source URL")
    snippet: str | None = Field(default=None, description="Short source snippet")


class ResearchFinding(BaseModel):
    """Structured finding produced by research synthesis."""

    title: str = Field(description="Finding title")
    details: str = Field(description="Finding explanation")
    source_urls: list[str] = Field(default_factory=list, description="Supporting source URLs")


class ResearchPackage(BaseModel):
    """First production workflow output for YouTube topic research."""

    topic: str = Field(description="Original topic")
    executive_summary: str = Field(description="Short synthesis summary")
    findings: list[ResearchFinding] = Field(default_factory=list, description="Structured detailed findings")
    key_facts: list[str] = Field(default_factory=list, description="Key facts as concise bullets")
    timeline: list[str] = Field(default_factory=list, description="Chronological timeline when applicable")
    sources: list[ResearchSource] = Field(default_factory=list, description="List of sources used")
    open_questions: list[str] = Field(default_factory=list, description="Unknowns or conflicting claims")
    recommended_angle: str = Field(description="Suggested direction for Writer Agent")
    metadata: dict[str, object] = Field(default_factory=dict, description="Execution metadata including status")


class ScriptDraftRequest(BaseModel):
    """Request payload for transforming a research package into a YouTube script draft."""

    research_package: ResearchPackage = Field(description="Structured research package input")
    duration_profile: Literal["short", "standard", "long"] = Field(
        default="standard",
        description="Target duration profile: short (3-5 min), standard (6-10 min), or long (10-20 min)",
    )


class ScriptDraft(BaseModel):
    """Production content generation output for YouTube-ready script narration."""

    topic: str = Field(description="Original topic")
    hook: str = Field(description="Attention-grabbing opening")
    intro: str = Field(description="Introduction context")
    sections: list[str] = Field(default_factory=list, description="Main script body sections")
    outro: str = Field(description="Closing narrative")
    call_to_action: str = Field(description="Viewer action request")
    estimated_duration: str = Field(description="Estimated duration range")
    narration_script: str = Field(description="Single continuous voice-over script")
    scene_markers: list[str] = Field(default_factory=list, description="Suggested scene boundaries")
    references: list[ResearchSource] = Field(default_factory=list, description="Carried-forward references")
    metadata: dict[str, object] = Field(default_factory=dict, description="Execution metadata including status")


class ReviewedScript(BaseModel):
    """Content quality review output for script refinement."""

    topic: str = Field(description="Original topic")
    revised_script: str = Field(description="Revised narration script after quality pass")
    change_summary: list[str] = Field(default_factory=list, description="Summary of meaningful edits")
    factual_notes: list[str] = Field(default_factory=list, description="Consistency and unsupported-claim notes")
    quality_score: float = Field(description="Overall quality score")
    readability_score: float = Field(description="Readability quality score")
    engagement_score: float = Field(description="Retention and engagement score")
    status: str = Field(description="Review status")
    metadata: dict[str, object] = Field(default_factory=dict, description="Execution metadata")


class PublishingPackage(BaseModel):
    """Final publication-ready package for YouTube distribution."""

    reviewed_script: ReviewedScript = Field(description="Reviewed and finalized script")
    youtube_title: str = Field(description="SEO-friendly YouTube title")
    youtube_description: str = Field(description="YouTube description with context and acknowledgements")
    youtube_tags: list[str] = Field(default_factory=list, description="YouTube tags")
    youtube_chapters: list[str] = Field(default_factory=list, description="YouTube chapter markers")
    seo_keywords: list[str] = Field(default_factory=list, description="Primary SEO keywords")
    thumbnail_prompt: str = Field(description="AI-image-ready thumbnail prompt")
    image_prompts: list[str] = Field(default_factory=list, description="Image prompts by major section")
    b_roll_suggestions: list[str] = Field(default_factory=list, description="B-roll footage suggestions")
    metadata: dict[str, object] = Field(default_factory=dict, description="Execution metadata including status")


class PublishingPackageRequest(BaseModel):
    """Request payload for transforming a script draft into publishing assets."""

    script_draft: ScriptDraft = Field(description="Script draft input")
