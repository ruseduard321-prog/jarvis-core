# Vision

Jarvis is the executive operating system for an AI-native company. It is designed to coordinate strategy, automate operations, and support multiple businesses through a shared platform that keeps humans in control of vision and AI in control of execution.

# Milestone 1 — Foundation

- Establish project structure and repository organization.
- Define backend architecture and service layer.
- Define frontend architecture and component organization.
- Implement authentication and user identity foundations.
- Provision database infrastructure and data model guidance.
- Document architecture, standards, and development rules.
- Establish mandatory development and AI assistant standards.

# Milestone 2 — Core Platform

- Implement user management and role handling.
- Support organizations and business contexts.
- Build a dashboard for operational visibility.
- Add projects and task management capabilities.
- Implement settings and configuration management.
- Expose basic APIs for frontend and integration.

# Milestone 3 — AI Platform

- Integrate Claude as the first AI provider. _(not started — OpenAI is currently the sole
  configured provider; see `default_llm_provider` in `backend/core/config.py`)_
- Build AI agent orchestration and execution workflows. _(✅ delivered — AgentRuntime /
  AgentOrchestrator, default chat execution path with automatic delegation; see root
  `PROJECT_STATE.md` F16/F16.1)_
- Support conversations between users and AI agents. _(✅ delivered — live end-to-end
  against a real Supabase project as of F17E)_
- Introduce memory capabilities for persistent context. _(✅ delivered — `MemoryService`,
  in-memory store per ADR-003)_
- Create knowledge management and reuse patterns. _(🟡 partial — Knowledge/Documents API
  implemented; not yet wired into the default agent chat path, see PROJECT_STATE.md
  "Gaps")_
- Establish prompt management and versioning. _(✅ delivered — F10 Prompts Library)_

# Milestone 4 — Automation

- Integrate n8n for workflow automation.
- Model and execute structured workflows.
- Add background job processing for asynchronous work.
- Support scheduling for recurrent operations.
- Introduce notifications for important events and exceptions.

# Milestone 5 — Business Platform

- Add product management capabilities.
- Support multiple products within the same platform.
- Provide analytics for operational performance.
- Build reporting capabilities for business insight.
- Manage documents and content assets.

# Milestone 6 — Scale

- Add support for multiple AI providers.
- Enable multi-business and multi-tenant support.
- Improve monitoring and observability.
- Optimize performance across the platform.
- Strengthen security and compliance.
- Expose a public API for external integration.

# Next Feature Priorities (Post-F24)

> **Priority change (2026-07-21):** The first complete, real end-to-end YouTube production
> run (F24, see root `PROJECT_STATE.md`) succeeded — research, strategy, script, review,
> scene planning, scene images, thumbnail, narration, subtitles, and a final MP4 were all
> generated in one real run at an approximate cost of $0.85/video. After reviewing that
> output, **publishing automation is no longer the next priority.** The platform now
> prioritizes maximizing generated-video quality before any further publishing automation
> work. This supersedes the previous F25–F28 list in `PROJECT_STATE.md` (Publishing Consumes
> Manifest, Workflow Run Status & History API, Cost Visibility, End-to-End MVP Integration
> Test) — that work is not discarded, it is deferred and folded into **F35 — Automated
> Publishing** below, to be picked up once video quality reaches the desired bar.

> **Update (2026-07-22):** F25, F26, F27, F28, F28A, F28B, and F29 are now complete. The
> full quality-first roadmap (F25–F29) is implemented, and real-world testing of that
> pipeline has shown that the next development phase should focus on maximizing production
> quality before publishing automation. See **Phase 2 — Production Quality** below for the
> revised upcoming roadmap (F30–F35), which replaces the previous single F30 placeholder.

### F25 — Cinematic Rendering Engine — ✅ COMPLETED

**Goal:** Transform static slideshow scenes into cinematic scenes using local rendering.

**Examples:** camera movement, pan, push-in, parallax, depth effects, particles, fog, light
rays, subtle transitions.

**Important:** This feature should prioritize local rendering (FFmpeg, Remotion, OpenCV, or
similar) instead of generating AI video, in order to keep API costs nearly unchanged.

**Status:** Implemented as the Cinematic Video Engine — a modular `RendererPipeline`
(camera movement, transitions, atmosphere overlays, color processing) that executes `Shot`
objects produced by a deterministic `ShotPlanner`, with the legacy slideshow renderer kept
as an automatic fallback. Fully local (ffmpeg-only), no added API cost. See F25 under
`PROJECT_STATE.md` Completed Features for full detail. Production visual validation (a real
rendered run) is intentionally deferred until after F26/F27 to avoid unnecessary generation
costs.

### F26 — Audio & Voice Engine — ✅ COMPLETED

**Goal:** Greatly improve narration quality.

**Includes:** deeper male voice, more natural pacing, dramatic pauses, adaptive background
music, automatic sound effects, automatic audio mixing.

**Status:** Implemented as the Jarvis Audio Engine, mirroring F25's `Shot`
contract/planner/executor philosophy: `VoiceDirection` (profile-driven delivery
instructions for the upgraded `gpt-4o-mini-tts`/`onyx` narration), `NarrationProcessingService`
(ffmpeg loudness normalization), optional local-library background music/sound effects
(off by default pending a real asset library), and an `AudioTimeline` — the audio
equivalent of `Shot` — executed by a pure `AudioMixerService` (ducking, fades, loudness
mastering), all via ffmpeg only, no added API cost beyond the narration model swap. See
F26 under `PROJECT_STATE.md` Completed Features for full detail. Real production audio
validation is deferred until after F27, bundled with F25's deferred visual validation.

### F27 — Smart Scene Composition — ✅ COMPLETED

**Goal:** Make every scene feel intentionally directed — narrative purpose, framing,
visual continuity, and rhythm — instead of independently-generated images.

**Includes:** no text inside generated images, safe margins, cleaner compositions, fewer
visual elements, better framing, reduced cropped content.

**Status:** Implemented with one approval-time architectural revision: a new
`TimelinePlan` contract (`backend/schemas/timeline.py`) was introduced as the single
source of truth for scene ordering/duration/start/end/pacing, sitting between Scene
Planning and Composition Planning — `CompositionPlan` (`backend/schemas/composition.py`)
and `AudioTimeline` both consume it and never calculate timing themselves. Purpose
(introduction/context/discovery/conflict/escalation/reveal/resolution), composition
style, camera intent, color language, and recurring continuity motifs are all resolved
deterministically (`DeterministicTimelinePlanner`/`DeterministicCompositionPlanner`) from
data the pipeline already produces — zero added LLM calls. `CompositionAwareShotPlanner`
(new default `ShotPlanner`) and `CompositionPromptEnricher` are the only new
consumers/producers; `RendererPipeline`, `AudioMixerService`, and
`ImageGenerationProvider` are all unchanged, with automatic fallback to F25/F26's
original deterministic behavior whenever composition data is absent or mismatched. See
`docs/F27_ARCHITECTURE_PROPOSAL.md` and `PROJECT_STATE.md`'s F27 entry for full detail.
226 backend tests passing; real production validation deferred alongside F25/F26's, to
bundle with F28.

### F28 — AI Director — ✅ COMPLETED

**Goal:** The LLM should generate cinematic direction for every scene, not only image
prompts.

**Example outputs:** camera movement, scene duration, atmosphere, transition, lighting,
particles, emotional intensity.

The renderer executes these directions automatically.

F27 prepared this seam explicitly: an LLM-driven `TimelinePlanner`/`CompositionPlanner`
can replace today's deterministic implementations directly, with no change required to
`ShotPlanner`, `AudioTimelinePlanner`, `RendererPipeline`, or `AudioMixerService`.

**Status:** Implemented exactly on that seam, preserving the F27 pipeline shape with no
redesign. A new dedicated `AIDirectorProvider` abstraction (ABC) hides the concrete
implementation; `AgentRuntimeAIDirectorProvider` is the first, reusing the existing agent
execution path (`ConversationEngine`/`AgentRuntime`/`AgentService`). The AI Director
reasons over the entire script in one structured-output call per production, producing an
`AIDirectorPlan` that reuses `TimelinePlan`'s/`CompositionPlan`'s own schemas directly —
no duplicate types, no heuristic reconstruction. `ai_director_plan_builder.py` validates
and normalizes that output into the real `TimelinePlan`/`CompositionPlan` (rescaling
relative durations to the exact measured narration total, dropping any invalid
relationship/motif reference, rejecting structurally broken output outright) —
`CompositionPlanner`'s new role once the AI Director is active. `CompositionPlanningService`
falls back wholesale to F27's unchanged deterministic planners on any AI Director
unavailability or validation failure — verified live in an environment with no configured
agent database. `RendererPipeline`, `AudioMixerService`, and `ImageGenerationProvider`
remain completely untouched; no new planner ABCs were introduced. See
`PROJECT_STATE.md`'s F28 entry for full detail. 249 backend tests passing; zero
architectural redesign; real production validation deferred, to bundle with F29.

### F28A — Render Profiles — ✅ COMPLETED

**Goal:** Standardize how finished videos are rendered and exported. Not an AI,
planning, or image-generation feature — its only responsibility is making a
strongly typed `RenderProfile` the single source of truth for every technical
rendering/export parameter (resolution, aspect ratio, frame rate, video/audio
codec, audio sample rate, bitrate strategy, container, color space, pixel format,
encoder preset, target platform), so no renderer, exporter, or encoder hardcodes a
technical value.

**Default profile:** YouTube Long — 1920×1080, 16:9, 30fps, H.264, AAC, 48kHz, MP4,
high-quality encoder defaults (CRF 18, "medium" preset).

**Future profiles** (YouTube Shorts, TikTok, Instagram Reels, Facebook, LinkedIn,
YouTube 4K, HDR, HEVC, AV1) become a configuration problem — registering one new
`RenderProfile` — never an architectural one.

**Status:** Implemented exactly on that scope. `RendererPipeline`,
`VideoAssemblyService`'s legacy slideshow fallback, and `AudioMixerService` each
gained one additive, optional `render_profile` constructor parameter (defaulting to
the "YouTube Long" profile via `RenderProfileRegistry` when omitted), replacing
independently-hardcoded `libx264`/`yuv420p`/`aac`/`_FPS = 24` values with one shared
source of truth. `RenderProfile` itself validates invalid combinations at
construction (mismatched aspect ratio/resolution, unsupported sample rate, a
bitrate strategy missing its required value) via a Pydantic `model_validator` with
`validate_assignment=True`. Zero changes to AI Director, TimelinePlan,
CompositionPlan, Shot, AudioTimeline, or ImageGenerationProvider — verified live: an
unmodified `VideoAssemblyService.execute()` call with no `render_profile` argument
automatically produces the correct default-profile ffmpeg args, and a custom
HEVC/4K/60fps/CBR/`.mov` profile propagates just as cleanly. See
`PROJECT_STATE.md`'s F28A entry for full detail. 280 backend tests passing; zero
added API cost.

### F28B — Adaptive Visual Storytelling Engine — ✅ COMPLETED

**Goal:** Evolve Scene → One Generated Image into Scene → Visual Beats → One Generated
Image per Visual Beat, eliminating long static scenes, without redesigning the
renderer/timeline/audio/AI Director architecture.

**Status:** Implemented on the existing seam — `VisualBeat` added to
`SceneComposition`/`AIDirectorSceneDirection` (no new planner type), AI Director made
Production-Budget-Aware via configurable settings, Cost Validation (clamp + budget-based
trimming) added to `ai_director_plan_builder.py`. `TimelinePlan`/`RendererPipeline`/
`AudioMixerService`/`ImageGenerationProvider` remain completely untouched. See
`PROJECT_STATE.md`'s F28B entry for full detail. 302 backend tests passing; fully
backward compatible.

### F29 — Viewer Retention Engine — ✅ COMPLETED

**Goal:** Optimize every video for YouTube retention.

**Includes:** stronger hooks, cliffhangers, pacing optimization, curiosity loops, emotional
progression, stronger endings.

**Status:** Implemented as a pure extension of F28's AI Director output — an optional
`SceneRetention` model (retention_priority, curiosity_level, emotional_intensity,
information_density, visual_change_frequency, reveal_strength, transition_energy) added
to `CompositionPlan`/`AIDirectorSceneDirection`, plus an importance-weighted replacement
(`beat_importance`: low/normal/high/critical) for F28B's equal beat-duration split in
`CompositionAwareShotPlanner`. Retention-aware transition selection maps
`transition_energy` onto the renderer's existing two `TransitionType` values.
`TimelinePlan`, `RendererPipeline`, `AudioMixerService`, and `ImageGenerationProvider`
are completely untouched; the deterministic fallback never populates retention data, so
pre-F29 behavior is reproduced exactly whenever the AI Director is unavailable. See
`PROJECT_STATE.md`'s F29 entry for full detail. 308 backend tests passing; zero added
API cost.

# Phase 2 — Production Quality

The objective of this phase is no longer proving that the pipeline works.

The objective is producing documentaries that are visually and audibly competitive with
successful YouTube documentary channels while keeping production costs below approximately
$5/video.

### F30 — Production Quality Validation — ✅ COMPLETED

**Purpose:**

- Audit the complete F25–F29 pipeline using real productions.
- Compare expected architecture vs actual generated output.
- Remove remaining quality bottlenecks.
- Validate every subsystem using real production runs.

**Deliverable:** Production Quality Report — see `docs/F30_PRODUCTION_QUALITY_REPORT.md`.

**Status:** Delivered against real production evidence — 6 real `storage/runs/*`
productions, `ffprobe` analysis of every video/audio stream, direct visual inspection of
generated images/thumbnails, a full real execution log, and the actual
`backend/services/` implementations. Findings were classified by root cause (Bug /
Missing Feature / Prompt Engineering / AI Model Limitation / Rendering Limitation /
Architecture Limitation) and assigned across F30–F35. Validation-only, per its own
charter — no code changed as part of F30 itself; F31 below implements the
F31-assigned findings.

### F31 — Photorealistic Visual Engine — ✅ COMPLETED

**Goal:** Improve image realism without redesigning the architecture.

**Focus:**

- cinematic prompting
- photorealism
- historical consistency
- visual consistency
- better scene composition
- higher perceived production value

**Status:** Implemented. `PhotorealisticPromptBuilder`
(`backend/services/photorealistic_prompt_builder.py`) replaces the old single generic
style phrase with a structured documentary-photography template (subject/action,
environment, historical context, character identity, camera angle/framing/focal length/
lens, depth of field, lighting, atmosphere, color palette, and an explicit realism
directive), wired through the existing `CompositionPromptEnricher` seam. Native
landscape image generation ships as a config default change
(`openai_image_size` → `"1536x1024"`, gpt-image-1's closest option to 16:9), with no
renderer change — F32 is untouched. Historical Visual Consistency and Character
Consistency are new: `VisualIdentityService` (one LLM call per production) produces a
shared `HistoricalVisualContext` plus a canonical `CharacterVisualIdentity` per
recurring named figure, reused verbatim across every scene/beat/thumbnail prompt
(provider-agnostic text anchor); `CharacterReferenceImageService` additionally
generates one reference portrait per character, and
`ImageGenerationProvider.generate_image()` gained an optional `reference_image`
parameter that `OpenAIImageGenerationProvider` honors via the real `images.edit`
endpoint when available, falling back to ordinary generation on any failure. A new
`ImageValidationService` runs one vision-model classification per generated image
(multi-panel/split-screen, garbled text, broken anatomy, obvious artifacts) with up to
one automatic regeneration attempt, fail-open on any validator outage. Thumbnail
generation now shares the same prompt engine and visual identity context as scene
images, so the thumbnail depicts the same person/setting/style the video delivers. New
`VisualIdentityStep` runs once per production between Review and Media; every new
service/parameter defaults to a no-op, so pre-F31 call sites are unaffected. See
`PROJECT_STATE.md`'s F31 entry for full detail. 349 backend tests passing (36 new); DI
container verified end-to-end; camera movement, transitions, rendering, voice, music,
SFX, audio mixing, and publishing were explicitly left untouched, per F31's charter.

### F31.5 — Production Hardening Sprint — ✅ COMPLETED

**Purpose:** a follow-up architecture review of F29–F31 identified four Critical-severity
gaps that had to close before F32 (async production execution, real budget enforcement,
character reference portrait validation, and untested live-API assumptions). This sprint
closed all four in one coordinated pass — production hardening, not new features, no
architecture redesign.

**Status:** implemented. `POST /production/runs` now returns immediately via the existing
`BackgroundTaskManager`/`TaskBackend` infrastructure instead of blocking for the full
pipeline run; a new `GET /production/runs/{execution_id}` retrieves progress/status/
results at any point. `maximum_video_budget_usd` is now enforced at runtime by a new
`BudgetTracker` (`backend/core/cost_tracker.py`), checked before every paid image call
(generation, validation, regeneration, character reference portraits) via a new shared
`ImageGenerationPipeline` (which also retired the validate-and-regenerate duplication F31
had introduced across two services) — the run's true total cost and budget status are
recorded on the final `AssetManifest`. Character reference portraits are now validated
before acceptance, and a still-invalid portrait after one retry is rejected outright
rather than ever becoming a character's identity anchor. A new opt-in live smoke test
(`backend/tests/live/test_f31_live_openai_smoke.py`, gated by `RUN_LIVE_SMOKE_TESTS=1`,
never runs in CI) verifies the two live-API assumptions F31 shipped untested. See
`PROJECT_STATE.md`'s F31.5 entry for full detail. 385 backend tests passing (36 new); DI
container and full FastAPI app verified to import and wire with zero errors.

### F32 — Cinematic Camera Language

**Goal:** Improve how static images become cinematic scenes.

**Includes:**

- scene-aware camera movement
- more natural motion
- less repetitive zooming
- improved transitions
- stronger visual storytelling

### F33 — Premium Audio Experience

**Goal:** Improve immersion.

**Includes:**

- expressive narration
- better voice direction
- background music
- ambient sound
- cinematic sound effects
- adaptive audio mixing

### F34 — Production Polish

**Goal:** Final production refinements.

**Includes:**

- color grading
- pacing refinements
- transition improvements
- continuity improvements
- final quality polish

### F35 — Automated Publishing

Move the existing Publishing roadmap here.

**Includes:** upload, scheduling, playlists, visibility, thumbnail upload, monitoring.

Publishing remains intentionally postponed until production quality reaches the desired
level.

---

# Quality-First Development Principle

After the successful validation of the first real end-to-end production workflow (F24),
Jarvis enters a new development phase.

The primary objective is no longer proving that the production pipeline works.

The primary objective is producing videos that are competitive with successful AI-powered
YouTube channels while preserving low production costs.

From this point forward, every proposed feature should satisfy at least one of the
following goals:

- Improve viewer experience.
- Improve viewer retention.
- Improve cinematic quality.
- Improve production quality.
- Reduce production cost.
- Reduce production time.
- Preserve or simplify the architecture.

Features that do not clearly contribute to one or more of these goals should be postponed
until after the first commercially successful YouTube product.

The philosophy is:

"Quality before automation."

Automation is valuable only after the generated product reaches the desired quality level.

For this reason, publishing automation (F35) intentionally remains the last milestone in
the current roadmap, following the Phase 2 production-quality milestones (F30–F34).

The roadmap should prioritize improving the generated product before improving operational
automation.

---

# Development Philosophy

- Build small.
- Ship often.
- Refactor continuously.
- Never sacrifice architecture for speed.
- Automation first.
- AI-assisted development.
- Long-term maintainability over short-term convenience.

The roadmap is a living document and should evolve together with the platform.
