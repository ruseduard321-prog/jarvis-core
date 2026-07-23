# PROJECT_STATE.md

**SINGLE SOURCE OF TRUTH** — Project progress and architecture state.

Use this document to understand the project status, completed work, and upcoming roadmap.

---

## Current Status

**Project:** Jarvis — AI-native Company Operating System

**Vision:** Jarvis automates business operations end-to-end. The first real business powered by Jarvis is an English YouTube automation business.

**Date**: 2026-07-22  
**Version**: 0.2.0  
**Status**: ✅ Alpha — **First real end-to-end YouTube production run completed successfully.** The full 10-stage pipeline (research → strategy → script → review → scene planning → scene images → thumbnail → narration → subtitles → final MP4) is functionally validated against live providers, at an approximate cost of $0.85/video. Phase 2 — Production Quality is underway: F30 (Production Quality Validation) audited the real F25–F29 output and F31 (Photorealistic Visual Engine) has now closed its highest-priority visual findings.

- ✅ F17E completed
- ✅ F17F completed
- ✅ F24 completed — Workflow Artifact Manifest + first real production run validated end-to-end
- ✅ F25 completed — Cinematic Video Engine (modular Shot-based renderer, ffmpeg-only, zero added API cost)
- ✅ F26 completed — Audio Engine (VoiceDirection/AudioTimeline contracts, gpt-4o-mini-tts, narration processing, optional music/SFX, ffmpeg mixing/mastering)
- ✅ F27 completed — Smart Scene Composition (TimelinePlan single source of truth for timing, CompositionPlan for purpose/framing/continuity, zero added API cost)
- ✅ F28 completed — AI Director (single creative authority producing TimelinePlan + CompositionPlan from one reasoning pass over the whole script, with automatic deterministic fallback)
- ✅ F28A completed — Render Profiles (RenderProfile as the single source of truth for every technical rendering/export parameter; default "YouTube Long" profile; zero planning/AI/rendering-behavior changes)
- ✅ F28B completed — Adaptive Visual Storytelling Engine (Scene → Visual Beats → one generated image per beat, AI Director budget-aware beat planning, zero new planner abstractions, fully backward compatible)
- ✅ F29 completed — Viewer Retention Engine (optional `SceneRetention` metadata + importance-weighted visual-beat duration, extending TimelinePlan/CompositionPlan with zero redesign; fully backward compatible)
- ✅ F30 completed — Production Quality Validation (real-evidence audit of the F25–F29 pipeline; see `docs/F30_PRODUCTION_QUALITY_REPORT.md`)
- ✅ F31 completed — Photorealistic Visual Engine (structured documentary-photography prompt engine, native landscape image generation, Historical/Character Visual Consistency, image validation with automatic regeneration, thumbnail consistency)
- ✅ F31.5 completed — Production Hardening Sprint (async production execution, real runtime budget enforcement, character reference portrait validation, opt-in live OpenAI smoke test — closes the four Critical findings from the F29–F31 architecture review)
- ✅ Supabase infrastructure operational
- ✅ Authentication operational
- ✅ AgentRuntime validated
- ✅ AgentOrchestrator validated
- ✅ General Assistant validated
- ✅ OpenAI stack modernized (GPT-5.5 + Responses API)
- ✅ Brave Search replaced DuckDuckGo as the search provider
- ✅ OpenAI quota issue resolved

### Next Objective

The full F25–F29 quality-first roadmap is implemented, F30 delivered a real-evidence
Production Quality Report, F31 (Photorealistic Visual Engine) shipped against that
report's findings, and F31.5 (Production Hardening Sprint) closed the four Critical
findings a follow-up architecture review raised before continuing. Jarvis continues
**Phase 2 — Production Quality** with: Cinematic Camera Language (F32) → Premium Audio
Experience (F33) → Production Polish (F34), with Automated Publishing (F35) deferred
until production quality reaches the desired bar. See `docs/planning/ROADMAP.md` for the
full Phase 2 roadmap.

### Development Workflow

- **Architect:** ChatGPT acts as Software Architect and feature approver
- **Implementer:** Claude Code implements approved features
- **Approval Gate:** Every feature requires architecture approval before implementation begins
- **Validation:** Every implementation must pass:
  - ✅ ESLint (0 errors/warnings for feature code)
  - ✅ TypeScript (strict mode)
  - ✅ Production Build (`npm run build`)

---

## Completed Features

### ✅ F06 Dashboard
- Overview page with system statistics
- Navigation hub for all features
- Status: Approved and implemented

### ✅ F07 Knowledge Base
- Document storage and retrieval
- Integration with RAG pipeline
- Status: Approved and implemented

### ✅ F08 AI Memory
- Conversation memory management
- Context persistence across sessions
- Status: Approved and implemented

### ✅ F09 Conversations
- Chat interface
- Message streaming (SSE)
- Real-time message handling
- Status: Approved and implemented

### ✅ F10 Prompts Library
- Prompt management and organization
- Reusable prompt templates
- Prompt versioning
- Status: Approved and implemented (15 files)

### ✅ F11 AI Playground
- Interactive parameter tuning (temperature, max_tokens)
- Custom system prompt experimentation
- Real-time streaming responses
- Message regeneration with current settings
- Status: Approved and implemented (6 files: 2 backend, 4 frontend)
- Validation: ESLint ✓, TypeScript ✓, Production Build ✓
- Latest: [F11_IMPLEMENTATION_SUMMARY.md](F11_IMPLEMENTATION_SUMMARY.md)

### ✅ F12 AI Agents
- Persistent agent management (create, list, get, update)
- Runtime-first orchestration path for agent-aware chat execution
- Conversation API extended with optional `agent_id` (no parallel chat API)
- Existing conversation endpoints reused for both standard and agent execution flows
- Frontend agent selection integrated into agents route with reusable chat flow
- Status: Approved and implemented (backend + frontend + SQL migration)
- Validation: ESLint ✓, TypeScript ✓, Production Build ✓, Python compile ✓
- Latest: [F12_IMPLEMENTATION_SUMMARY.md](F12_IMPLEMENTATION_SUMMARY.md)

### ✅ F13–F15 Tools, Workflows & Tasks Foundations
- Tools framework, workflow services (Research/Writer/Content-Finalization), and task
  support completed in prior sessions (F13.1–F13.3, F14, F15, F15.1–F15.3)
- Status: Completed prior to this documentation sync; implementation detail not re-audited here

### ✅ F16 Agent Runtime Default Chat Engine
- Normal `/chat` now executes through `AgentRuntime` → `AgentOrchestrator` by default —
  the frontend never sends `agent_id`; the backend resolves the seeded `general` (General
  Assistant) agent automatically via `AgentService.get_default_agent()`
- `/agents` page behavior unchanged (explicit `agent_id` still bypasses resolution)
- Single execution path: legacy direct-LLM/RAG branch retained in code but unreachable
  from normal requests; missing default agent returns a clean HTTP 503, never a silent
  fallback
- `AgentOrchestrator`'s system prompt now includes a roster of agents the acting agent may
  delegate to, so it can accurately describe the multi-agent system instead of presenting
  itself as a single assistant
- Structured per-execution logging added to `AgentRuntime.execute()` (conversation id,
  selected agent, delegated agents, tools used, execution time, final status)
- Status: Implemented and validated live (F16), then fully verified end-to-end (F17E) once
  Supabase was configured

### ✅ F16.1 Automatic Agent Delegation
- The General Assistant (and any agent reached via chat) now auto-detects whether a
  request needs a specialist agent or a tool capability, via two scoped LLM classification
  calls in `AgentOrchestrator` — no manual agent selection or dedicated workflow endpoint
  required
- Multi-step requests (e.g. "research X and write a script") are planned once as an
  ordered sequence and executed sequentially, threading each step's real output into the
  next step's objective
- Fixed two pre-existing, never-before-triggered bugs surfaced while wiring this up:
  delegation-target slug/id mismatch, and tool output never reaching the LLM's own answer
  (tools now run before the response is drafted)
- Fully backward compatible: F13–F15 workflow-service calls are gated off from
  auto-planning and behave exactly as before
- Status: Implemented; validated live against the real OpenAI API for all spec'd scenarios
  (single-domain delegation ×4, direct-answer, two-hop chain)

### ✅ F17A–F17E Stability Audit & Fixes
- **F17A** — Read-only architecture-aware audit distinguishing real bugs from intentional
  design/roadmap gaps across backend, frontend, auth, tools, and persistence
- **F17B** — Fixed 8 Critical / 4 High / 2 Medium approved findings: production sign-in DI
  bypass, auth-persistence race on refresh, dual token source of truth (frontend now
  single-sources tokens via Zustand), 6 broken Knowledge/Documents/Memory API endpoints,
  `temperature`/`max_tokens` restored through the agent execution path, dev-credential
  debug gating, Stop Generation not closing its `EventSource`, HTML-cleaning regex bug,
  `DatabaseUnavailableError` masked as generic 500s
- **F17C** — Fixed `RetrievalEngineService` method-name mismatch (`.execute()` → `.retrieve()`)
  surfaced during F17B validation
- **F17D** — Fixed Embeddings API `Usage` field mismatch (`completion_tokens` doesn't exist
  for embeddings; verified against the actually-installed `openai` SDK)
- **F17E** — Diagnosed and resolved the final infrastructure gap: this environment had no
  `SUPABASE_URL`/`SUPABASE_KEY` configured, so the `agents` table was never created and the
  default-agent lookup always failed with a 503. **Root cause was missing infrastructure,
  not a code defect** — the resolution logic in `AgentService.get_default_agent()` was
  already correct. Resolved by configuring real Supabase credentials, running the three
  existing migrations (`backend/migrations/20260719_f12_agents.sql`,
  `_f12_2_core_business_agents.sql`, `_f12_3_agent_slug.sql`), and confirming all 8 core
  agents are seeded and active, with General Assistant (`slug=general`) resolvable and
  chat executing end-to-end through `AgentRuntime` against the real database
- Status: All approved findings fixed and live-validated; remaining F17A findings not in
  scope for F17B are still open (see docs/DECISIONS.md and Known Issues below)

### ✅ F17F OpenAI AI Layer Modernization — COMPLETED
- Migrated `OpenAIProvider` (`backend/core/openai_llm_provider.py`) from the legacy Chat
  Completions API to the OpenAI **Responses API** (`client.responses.create(...)`) for both
  `generate()` and `stream()`, with zero changes to the provider's public interface —
  `AgentOrchestrator`, `WorkflowOrchestrator`, `ConversationEngine`, research/writer/review
  services, and General Assistant all call it unchanged
- Default model updated: `default_llm_model` in `backend/core/config.py` changed from
  `"gpt-3.5-turbo"` → **`"gpt-5.5"`**
- Verified facts (live, this environment):
  - Effective default LLM model is `gpt-5.5` (no `.env` override; confirmed by importing
    `backend.core.config.settings`)
  - The OpenAI **Responses API** is in active use — `responses.create()` appears at
    `backend/core/openai_llm_provider.py:143` (`generate()`) and `:192` (`stream()`)
  - `chat.completions.create()` has been fully removed from production code — zero
    occurrences anywhere under `backend/`; remaining repo-wide matches are documentation
    (`docs/DECISIONS.md`, `OPENAI_VERIFICATION.md`, `OPENAI_REFACTORING.md`) only
  - General Assistant verified end-to-end through the call chain:
    `AgentOrchestrator` → `OpenAIProvider` → `responses.create(model="gpt-5.5")`
  - Only one LLM provider is registered (`llm_registry.py`: `"openai" → OpenAIProvider`) —
    no execution path bypasses `OpenAIProvider`
  - No production execution path still targets `gpt-3.5-turbo`; the only remaining literal
    references are a test fixture value (`test_openai_provider.py`, unexecuted stream
    assertion) and an unwired diagnostic script (`verify_config_fix.py`)
- Status: Implemented and runtime-verified; streaming, structured JSON output (via
  `text.format` translation of the existing `response_format` option), logging, and error
  handling all preserved unchanged from the caller's perspective

### ✅ F24 Workflow Artifact Manifest — COMPLETED

- Repositioned/extended `AssetPackagingStep` into a `WorkflowArtifactManifest` step run as
  the last step of `youtube_production_workflow.py`, aggregating `video_file_path`,
  publishing package (title/description/hashtags), thumbnail/subtitle paths, scene/broll/
  music plans, per-step cost totals, and step statuses into one canonical `manifest.json`
- **First real, complete production run validated end-to-end** using this manifest as the
  pipeline's final output — the full 10-stage flow (research → strategy → script → review →
  scene planning → scene images → thumbnail → narration → subtitles → final MP4) executed
  successfully against live providers
- Brave Search replaced the previous DuckDuckGo search provider ahead of this run
- The pre-existing OpenAI quota issue blocking real runs was resolved
- Total measured production cost for the run: **≈ $0.85 per video**
- Status: Implemented and live-validated; **the production pipeline is now considered
  functionally validated** — this closes out the "first end-to-end production workflow"
  objective carried since F17F

### ✅ F25 Cinematic Video Engine — COMPLETED

- Replaced the static slideshow renderer with a locally-rendered cinematic look — camera
  movement, cinematic transitions, and optional atmosphere overlays — entirely via ffmpeg,
  with OpenAI usage unchanged (no added API cost)
- Introduced a `Shot` data contract (`backend/schemas/shots.py`) plus a modular
  `RendererPipeline` (`CameraMovement`, `Transition`, `AtmosphereOverlay`, `ColorProcessing`)
  that **executes Shots** rather than choosing effects itself — `Shot`s are resolved today
  by a deterministic `ShotPlanner`, keyword-matching each scene's existing `camera`/
  `animation` text with a round-robin fallback; **F28 (AI Director)** is expected to supply
  `Shot`s directly from the LLM later with no renderer changes required
- The legacy slideshow renderer remains in place as an **automatic fallback** — if
  cinematic rendering fails for any reason (unsupported filter, timeout, non-zero exit),
  `VideoAssemblyService` falls back to it transparently so the pipeline never regresses to
  a failed run
- `VideoAsset` extended with optional `render_mode`/`camera_movements`/`transition`/
  `atmosphere_overlay` fields for observability, all backward-compatible defaults
- Status: Implemented and fully validated — **152 backend tests passing**, clean
  `py_compile`/`compileall` across the touched files, dependency injection verified live
  (`get_video_assembly_service()` resolves the new `ShotPlanner`/`RendererPipeline`
  correctly). **Real production visual validation (an actual rendered run) is intentionally
  deferred until after F26/F27**, to avoid unnecessary generation costs before the audio and
  scene-composition upgrades land too

### ✅ F26 Audio Engine — COMPLETED

- Full architecture proposal (`docs/F26_ARCHITECTURE_PROPOSAL.md`) approved with one
  revision: an explicit `AudioTimeline` contract — the audio equivalent of F25's
  `Shot` — was introduced so `AudioMixerService` only ever executes a plan it's given
  and never makes a creative decision itself
- Provider decision: **stayed on OpenAI**, upgraded narration from `tts-1`/`alloy` to
  **`gpt-4o-mini-tts`/`onyx`** — same provider/client, but its `instructions` parameter
  is the first delivery-style control (pace, tone, dramatic pauses) this pipeline has
  ever had. ElevenLabs was researched and rejected for now (materially higher and
  differently-shaped cost, non-trivial new-provider integration surface) —
  `TextToSpeechProvider` stays a real abstraction so it can be added later with zero
  caller changes
- New pipeline, mirroring F25's contract/planner/executor split throughout:
  `VoiceDirection` (`VoiceDirectionPlanner`/`DeterministicVoiceDirectionPlanner`) →
  `VoiceGenerationService` (extended: direction-aware + runs Narration Processing) →
  `NarrationProcessingService` (ffmpeg `loudnorm`) → optional Background Music /
  Sound Effects (`MusicGenerationProvider`/`SoundEffectProvider`, first concrete
  implementation `LocalMusicLibraryProvider`/`LocalSoundEffectLibraryProvider` — local,
  keyword-matched, zero API cost, off by default since no asset library ships) →
  `AudioTimeline` (`AudioTimelinePlanner`/`DeterministicAudioTimelinePlanner`) →
  `AudioMixerService` (pure ffmpeg executor: ducking via `sidechaincompress`, fades,
  `loudnorm` mastering to YouTube's -14 LUFS target)
- Seven reusable `VoiceProfile`s shipped (Documentary Male/Female, Storytelling,
  Historical, Mystery, News, Educational) — adding a profile is a registry entry, no
  code path changes
- New `AudioEngineService` composes music/SFX resolution + timeline planning + mixing;
  new `AudioEngineStep` runs after Scene Planning (first point `MusicPlan`/`ScenePlan`
  are both available) and before Video Assembly. `VideoAssemblyStep` now prefers the
  mixed track and **automatically falls back to the raw (normalized) narration track**
  on any mixing failure or disabled configuration — same fallback discipline as
  cinematic rendering falling back to the legacy slideshow
- `AudioTimeline`/`Shot` are sibling contracts keyed by the same `scene_number`,
  positioning F28 (AI Director) to eventually emit both from one LLM call with no
  renderer/mixer redesign
- Status: Implemented and validated — **188 backend tests passing** (36 new across 8
  new test files), clean `py_compile`/`compileall`, dependency injection verified live
  (`get_audio_engine_service()`/`get_voice_generation_service()`/
  `get_youtube_production_workflow_definition()` all resolve correctly, workflow step
  order confirmed to include "Audio Mix"). Music/SFX ship real and tested but **off by
  default** (`background_music_enabled`/`sound_effects_enabled = False`) since no asset
  library ships with this repository; narration direction/processing and the mixing/
  mastering chain are **on by default**. Real production audio validation (an actual
  generated run) is deferred alongside F25's, to bundle with F27's improvements

### ✅ F27 Smart Scene Composition — COMPLETED

- Full architecture proposal (`docs/F27_ARCHITECTURE_PROPOSAL.md`) approved with one
  revision requested at approval time: a new `TimelinePlan` contract was introduced as
  the single source of truth for scene ordering/duration/start/end/pacing, inserted
  between Scene Planning and Composition Planning — `CompositionPlan` and
  `AudioTimeline` now consume it instead of each independently computing their own
  (previously uniform) scene timing
- New pipeline stage, mirroring F25/F26's contract/planner/executor split:
  `TimelinePlanner`/`DeterministicTimelinePlanner` (`backend/schemas/timeline.py`,
  `backend/services/timeline_planner.py`) assigns each scene a `ScenePacing` from its
  position alone (fast setup → steady development → slow build → dramatic pause →
  climax → breathing resolution), converts pacing to a duration multiplier, and
  rescales so per-scene durations sum to the exact measured narration duration — the
  concrete fix for "every scene held the screen for the same number of seconds"
- `CompositionPlanner`/`DeterministicCompositionPlanner`
  (`backend/schemas/composition.py`, `backend/services/composition_planner.py`)
  consumes `TimelinePlan` (never recalculates timing) to assign `ScenePurpose`
  (introduction/context/discovery/conflict/escalation/reveal/resolution),
  `CompositionStyle`, `CameraIntent` (the "WHY" behind F25's camera movement),
  `ColorLanguage`, and detects recurring `ContinuityMotif`s (colors/objects/
  locations/atmosphere) via deterministic keyword repetition across scenes, adding
  `SceneRelationship`s (continuation/contrast/callback/escalation) — all genre-agnostic,
  no mystery-specific logic, zero LLM calls
- `CompositionPlanningService` composes all three planners into one new workflow step,
  "Composition Planning", inserted between Scene Planning and Scene Image
- `CompositionPromptEnricher` deterministically appends composition/continuity phrases
  (framing language, "cinematic 16:9 composition, safe margins, no on-image text",
  recurring-motif callouts) onto each scene's existing image prompt —
  `ImageGenerationProvider`/`SceneImageGenerationService` are completely unchanged,
  satisfying the "improve the information provided to it, don't redesign it" constraint
- `CompositionAwareShotPlanner` (new `ShotPlanner` implementation, now the default in
  `VideoAssemblyService`) derives each `Shot` from `CompositionPlan` — variable
  per-scene duration, purpose-driven shot type/camera movement, contrast-driven
  transitions, motif-driven atmosphere — falling back automatically to the original
  `DeterministicShotPlanner` behavior whenever `CompositionPlan` is absent or its scene
  count doesn't match the images actually rendered (e.g. a scene image failed after
  planning), so video/audio timing can never disagree with the real narration length.
  `RendererPipeline` is completely unchanged
- `AudioTimelinePlanner`/`DeterministicAudioTimelinePlanner` gained an additive
  `timeline_plan` parameter: when given and covering every scene, `scene_transitions`/
  SFX placement read `start_seconds` directly from `TimelinePlan` instead of
  recomputing an independent proportional split; falls back to the original F26
  behavior when absent or mismatched. `AudioMixerService` is completely unchanged
- `VideoAssemblyService`'s total-duration formula fixed to sum each shot's own
  duration instead of assuming a uniform `scene_seconds` — required once per-scene
  duration became variable, verified live to keep video and audio scene boundaries
  identical (see Latest Validation below)
- Status: Implemented and validated — **226 backend tests passing** (38 new across 5
  new test files plus additions to 4 existing ones), clean `py_compile`/`compileall`,
  dependency injection verified live (`get_composition_planning_service()` resolves
  correctly, `get_video_assembly_service()` now resolves `CompositionAwareShotPlanner`
  as its default shot planner, workflow step order confirmed to include "Composition
  Planning" between "Scene Planning" and "Scene Image"). Zero added API cost — every
  new mechanism is deterministic Python over data already produced upstream. Real
  production visual/audio validation (an actual rendered run) remains deferred
  alongside F25/F26's, to bundle with F28's improvements

### ✅ F28 AI Director — COMPLETED

- Preserves the exact F27 pipeline shape end to end (Research → Script → ScenePlan
  → TimelinePlan → CompositionPlan → Shot → AudioTimeline → Renderer → Audio Mixer →
  Final Video) with no redesign — the AI Director becomes the single creative
  authority feeding `TimelinePlan`/`CompositionPlan`; every downstream component
  (`Shot`, `AudioTimeline`, `RendererPipeline`, `AudioMixerService`,
  `ImageGenerationProvider`, `VideoAssemblyService`) is unchanged and still purely
  executes what it's given
- New dedicated provider abstraction: `AIDirectorProvider` (ABC,
  `backend/services/ai_director_provider.py`) hides the concrete implementation
  behind an interface, so a future provider swap requires no caller changes.
  `AgentRuntimeAIDirectorProvider` is the first concrete implementation, reusing
  this codebase's existing agent execution path (`ConversationEngine` +
  `AgentRuntime` + `AgentService`) — the same plumbing `ScenePlanningService`
  already uses, resolved against the existing "Creation Agent" (`creation`/`media`
  slug fallback) — no new agent/migration introduced
- The AI Director reasons over the **entire** script in **one** structured-output
  call per production (never per scene) — full narration, per-scene breakdown,
  genre, and `StrategyPackage` context (target audience/positioning/pacing/
  emotional arc, when available) — producing `AIDirectorPlan`
  (`backend/schemas/ai_director.py`): per-scene duration/pacing/purpose/
  composition-style/camera-intent/color-language/continuity-tags/relationships
  plus production-wide continuity motifs, reusing the exact same enums/schemas
  `TimelinePlan`/`CompositionPlan` already define — no duplicate type system, no
  heuristic reconstruction from free text
- `ai_director_plan_builder.py` validates and normalizes `AIDirectorPlan` into the
  real `TimelinePlan`/`CompositionPlan`: rejects (raises, triggering fallback) on
  scene-coverage mismatches, non-positive durations, or an unmeasurable total
  duration; rescales the AI's relative per-scene durations to sum to the exact
  measured narration duration (preserving its relative pacing decisions exactly,
  never overriding them) — the same duration-exactness invariant F27 established;
  drops (never hard-fails on) any individual relationship/motif referencing a
  scene number outside the production. This is `CompositionPlanner`'s new role
  when the AI Director is active — validation/normalization, not creative
  decision-making — while `DeterministicTimelinePlanner`/
  `DeterministicCompositionPlanner` remain completely unchanged as the fallback
- `CompositionPlanningService.execute()` (now `async`) tries the AI Director
  exactly once per production; on `AIDirectorError` (unavailable agent, failed
  call, invalid JSON, failed validation) or when disabled
  (`settings.ai_director_enabled`) or when no provider was injected, it falls back
  wholesale to F27's deterministic planners — never a partial mix of AI timing
  with deterministic composition or vice versa. Verified live in this environment
  (no configured agent database): the AI Director call fails to resolve an agent,
  logs `ai_director_fallback_to_deterministic_planning`, and the pipeline still
  produces a complete, valid `TimelinePlan`/`CompositionPlan`
- `Settings.ai_director_enabled: bool = True` (default on — this is meant to
  become the production default now that the architecture is considered complete)
  and `Settings.ai_director_genre: str = "documentary"`, mirroring
  `cinematic_rendering_enabled`/`audio_engine_enabled`'s existing manual-override
  role; the real safety net remains the automatic fallback above, not this flag
- Status: Implemented and validated — **249 backend tests passing** (23 new across
  3 new test files: AI Director provider, AI Director plan builder, plus AI
  Director integration tests added to `test_composition_planning_service.py`),
  clean `py_compile`/`compileall`, dependency injection verified live
  (`get_ai_director_provider()` resolves `AgentRuntimeAIDirectorProvider`,
  `get_composition_planning_service()` resolves it as a dependency, workflow step
  order unchanged from F27). Live end-to-end check confirmed `TimelinePlan`
  remains the single source of truth even when the AI Director produces
  dramatically uneven relative durations (e.g. a 22s reveal vs. a 5.5s
  establishing beat on a 50s narration) — video (`Shot`) and audio
  (`AudioTimeline`) still derive identical scene boundaries and the total still
  sums exactly to the real narration duration. Zero added architectural layers —
  no new planner ABCs, `RendererPipeline`/`AudioMixerService`/
  `ImageGenerationProvider` all untouched. Real production visual/audio validation
  (an actual rendered run, with a real seeded director agent) remains deferred, to
  bundle with F29's improvements

### ✅ F28A Render Profiles — COMPLETED

- Pure technical/export-layer feature — no planning, AI, or image-generation logic
  touched. Preserves the F27/F28 production pipeline exactly (Research → Script →
  ScenePlan → TimelinePlan → CompositionPlan → Shot → AudioTimeline → Renderer →
  Audio Mixer → Final Video); `RenderProfile` only ever answers "how is the
  finished production encoded," never a creative question
- New strongly typed `RenderProfile` (`backend/schemas/render_profile.py`,
  Pydantic with `validate_assignment=True`): resolution, aspect ratio, frame rate,
  video/audio codec, audio sample rate, bitrate strategy (CRF/CBR/VBR), container
  format, color space, pixel format, encoder preset, target platform. A
  `model_validator` rejects invalid combinations at construction (and on any later
  mutation) — mismatched aspect ratio vs. resolution, an unsupported sample rate,
  a bitrate strategy missing its required value — so "validate before rendering
  starts" is true by construction, not a separate step a caller could skip
- One production-ready default profile ships: **YouTube Long** (1920×1080, 16:9,
  30fps, H.264/AAC, 48kHz, MP4, CRF 18 + "medium" preset — high-quality,
  YouTube-appropriate defaults). `RenderProfileRegistry`
  (`backend/services/render_profile_registry.py`) is the single place future
  profiles (YouTube Shorts, TikTok, Instagram Reels, HEVC, AV1, HDR, ...) get
  added — registering one `RenderProfile` value, never a Renderer/exporter change
- `render_profile_encoders.py` is the only place RenderProfile's portable codec
  enums translate into actual ffmpeg encoder names (`h264`→`libx264`,
  `opus`→`libopus`, etc.) and into concrete bitrate-strategy ffmpeg args — reused
  identically by `RendererPipeline`, `VideoAssemblyService`'s legacy slideshow
  fallback, and `AudioMixerService`, so all three exported outputs share one
  technical-parameter source of truth rather than three copies of the same
  hardcoded values (which is what existed before this feature: `libx264`,
  `yuv420p`, `aac`, and a bare `_FPS = 24` constant were hardcoded independently
  in `cinematic_renderer_pipeline.py` and `video_assembly_service.py`)
- Minimal integration exactly as scoped: `RendererPipeline`, `VideoAssemblyService`,
  and `AudioMixerService` each gained one additive, optional `render_profile`
  constructor parameter (defaulting via the registry to "YouTube Long" when
  omitted) — no method signature redesign, no change to `AI Director`,
  `TimelinePlan`, `CompositionPlan`, `Shot`, `AudioTimeline`, or
  `ImageGenerationProvider`. `Settings.cinematic_output_resolution` (now fully
  superseded by `RenderProfile.width`/`height`) was removed as dead/conflicting
  configuration; `Settings.render_profile_name: str = "youtube_long"` is the new,
  single selector, resolved once via a `RenderProfileRegistry` DI singleton
- Status: Implemented and validated — **280 backend tests passing** (31 new
  across 3 new test files — RenderProfile validation, encoder mapping, registry —
  plus profile-driven-args coverage added to the existing renderer/video-assembly/
  audio-mixer test files, including full custom-profile tests proving no
  hardcoded technical value remains anywhere in the render/export path), clean
  `py_compile`/`compileall`, dependency injection verified live
  (`get_render_profile_registry()` resolves correctly; `VideoAssemblyService` and
  `AudioMixerService` both resolve to the same shared "youtube_long"
  `RenderProfile` instance). Live end-to-end check: an unmodified
  `VideoAssemblyService.execute()` call (no `render_profile` argument, exactly
  how every existing caller already invokes it) automatically produced the
  correct ffmpeg args for the default profile — `libx264`, `-preset medium`,
  `-crf 18`, `yuv420p`, `bt709`, `30fps`, `aac`/`48000`Hz, `mp4` — confirming
  backward compatibility live, not just in unit tests. Zero added API cost (pure
  local ffmpeg configuration, no LLM/provider calls of any kind)

### ✅ F28B Adaptive Visual Storytelling Engine — COMPLETED

- Evolves the pipeline from Scene → One Generated Image to Scene → Visual Beats →
  One Generated Image per Visual Beat, without introducing any new planner
  abstraction — `AI Director` remains the only creative authority, `TimelinePlan`
  remains the only timing authority, `CompositionPlan` remains the owner of visual
  intent, and `RendererPipeline`/`AudioMixerService`/`ImageGenerationProvider` are
  completely unchanged
- New `VisualBeat` model (`backend/schemas/composition.py`) added as a field on
  `SceneComposition` (`visual_beats: list[VisualBeat]`, default empty) — purely a
  visual-storytelling record (`beat_number`, `description`, `emphasis_note`),
  never a timing object; an empty list means the scene renders as the one image
  it always did, so every pre-F28B production continues to behave identically
- `AIDirectorSceneDirection` gained the same `visual_beats` field, and
  `AIDirectorRequest` gained Production Budget Awareness fields (maximum/target
  production budget, estimated cost already consumed, remaining budget, estimated
  per-image cost, configured minimum/target/maximum visual beats per scene) — the
  AI Director now reasons about storytelling value against a real dollar budget
  instead of a fixed per-scene rule, per the brief's explicit instruction that the
  beat count "must emerge from the AI Director's reasoning... never determined by
  fixed rules"
- New configurable settings in `backend/core/config.py`:
  `maximum_video_budget_usd` (5.0), `target_video_budget_usd` (4.0),
  `maximum_image_budget_usd` (3.0), `target_image_budget_usd` (2.0),
  `minimum_visual_beats_per_scene` (1), `target_visual_beats_per_scene` (2),
  `maximum_visual_beats_per_scene` (4) — never hardcoded in planning/validation
  code, matching `max_scenes_per_video`'s existing guardrail convention
- **Cost Validation**, implemented in `ai_director_plan_builder.py` (extended,
  not a new planner): `clamp_visual_beats_per_scene()` enforces the hard
  per-scene ceiling regardless of what the AI returns; `enforce_visual_beat_budget()`
  trims beats — always from whichever scene currently has the most, never below
  1 image per scene — until the plan's total projected image count fits the
  configured/remaining dollar budget. Both are pure validate-and-normalize
  functions, called from `CompositionPlanningService` after the AI Director
  responds, exactly mirroring this module's existing "validate, never
  creatively re-plan" role
- **Production Budget Awareness plumbing**: `WorkflowRunContext` gained a
  `cost_ledger: dict[str, float]`, populated generically by `WorkflowEngine`
  from each step's own existing `__meta__/<name>.json` metrics artifact
  (`build_step_metrics_artifact`'s established convention) — no changes needed
  to any of the 9+ steps that already report cost this way.
  `CompositionPlanningStep` sums `context.cost_ledger.values()` and passes it
  into `CompositionPlanningService.execute(estimated_cost_so_far_usd=...)`,
  which computes `estimated_image_cost_usd` via the existing `CostTracker` and
  the tighter of the whole-video/image-specific budget ceilings before building
  the `AIDirectorRequest`
- `CompositionPromptEnricher` now expands one incoming `ScenePrompt` into one
  outgoing `ScenePrompt` per visual beat (each describing that beat's own visual
  event), or exactly the one enriched prompt it always produced when a scene has
  no beats — fully backward compatible. `ScenePrompt`/`SceneImageAsset` both
  gained an additive `beat_number: int = 0` field (0 = no beat)
- `SceneImageGenerationService` needed no change to its core one-request-per-prompt
  loop (a beat is just another prompt in the list) — only its filename generation
  (unique per beat: `scene_XX_beat_YY.png`, unchanged `scene_XX.png` when
  beat_number is 0) and its existing two-tier safety-net ceiling, now scaled by
  `maximum_visual_beats_per_scene` so a beat-expanded plan isn't silently
  truncated back to one image per scene. Its return type changed from
  `dict[int, bytes]` keyed by scene_number (no longer unique once beats exist) to
  `dict[str, bytes]` keyed by the now-unique filename — the same change threaded
  through `VideoAssemblyService.execute()`'s `image_bytes_by_filename` parameter
  and both workflow steps
- `CompositionAwareShotPlanner` extended (not redesigned): its fallback-trigger
  condition changed from `len(composition_plan.scenes) != image_count` to an
  expected-image-count sum that accounts for each scene's beat count, and its
  loop now iterates `composition_plan.scenes` directly, emitting one `Shot` per
  beat (or one, when no beats) with the scene's fixed `TimelinePlan`-sourced
  duration split evenly across its beats — scene duration is never changed, only
  how many images it's divided across. Verified via `cinematic_renderer_pipeline.py`
  that `RendererPipeline.render()` zips `images`/`shots` purely by list position
  (never by `scene_number` lookup), so multiple beats safely sharing one
  `scene_number` on their `Shot`s cannot cause any mismatch
- Status: Implemented and validated — **302 backend tests passing** (22 new,
  covering visual-beat normalization/clamping/budget-enforcement, per-beat prompt
  expansion, per-beat shot duration splitting, unique multi-beat filenames, the
  scaled safety-net ceiling, cost-ledger accumulation in `WorkflowEngine`, and
  budget-field wiring into `AIDirectorRequest`), clean `py_compile`/`compileall`
  across the whole backend. Zero changes to `RendererPipeline`,
  `AudioMixerService`, `ImageGenerationProvider`, `RenderProfile`, or the
  deterministic F27 fallback planners (which never populate `visual_beats`, so
  the whole feature is inert whenever the AI Director is unavailable/disabled —
  Scene → One Image, exactly as before)

### ✅ F29 Viewer Retention Engine — COMPLETED

- Pure extension of F28's AI Director output — no redesign. `TimelinePlan` is
  still the only timing authority, `CompositionPlan` is still the only owner of
  visual intent, and `RendererPipeline`/`AudioMixerService`/
  `ImageGenerationProvider` are completely untouched. The engine gives the AI
  Director additional reasoning axes (attention, pacing, curiosity, emotional
  rhythm) and one small mechanical change to how an existing quantity (beat
  screen time) is distributed — it never invents a different story
- New optional `SceneRetention` model (`backend/schemas/composition.py`):
  `retention_priority`, `curiosity_level`, `emotional_intensity`,
  `information_density`, `visual_change_frequency`, `reveal_strength`,
  `transition_energy` — added as `SceneComposition.retention: SceneRetention |
  None = None` and `AIDirectorSceneDirection.retention`. `None` means "no
  retention guidance" and is the exact deterministic-fallback/pre-F29 state.
  `ImportanceLevel` (low/normal/high/critical) is one shared enum reused for
  both a scene's `retention_priority` and a beat's `beat_importance` — a single
  taxonomy instead of two near-identical ones, per the "prefer the simpler
  solution" architecture rule
- `VisualBeat` gained `beat_importance: ImportanceLevel = NORMAL` (additive).
  **Beat Duration Optimization**: `CompositionAwareShotPlanner` (F27/F28B)
  replaces its equal split of a scene's fixed duration across beats with an
  importance-weighted split (`_BEAT_IMPORTANCE_WEIGHT`, weights 3/4/6/7 for
  low/normal/high/critical — reproduces the architecture spec's own worked
  example: a 40s scene at low/normal/critical/high splits 6/8/14/12s). Every
  weight is strictly positive, so a beat can never receive zero duration, and
  the split always sums back to the scene's exact `TimelinePlan` duration. A
  scene where every beat is `NORMAL` (including every pre-F29 plan, since the
  field defaults to `NORMAL`) still splits perfectly evenly — zero behavior
  change for existing plans
- **Transition Intelligence**: `SceneRetention.transition_energy`
  (seamless/energetic/suspense/calm/dramatic/emotional) is planning-only
  guidance mapped onto the renderer's existing two `TransitionType` values
  (`dissolve`/`fadeblack`) by `CompositionAwareShotPlanner._transition_for`,
  taking priority over the older contrast-relationship heuristic when present
  and falling back to it otherwise — `RendererPipeline` never sees the new enum
- The AI Director's prompt (`ai_director_provider.py`) was extended (not
  restructured) to additionally reason about and return, per scene, a
  `retention` object plus each visual beat's `beat_importance` — covering
  curiosity-loop classification (question/mystery/discovery/explanation/
  reveal/resolution pacing), a whole-production emotional curve (avoiding a
  flat progression), information-density-driven visual support, anti-repetition,
  and stronger openings/endings — entirely through richer LLM reasoning, not
  new deterministic Python rules, since introducing hardcoded retention
  heuristics would create a second creative authority alongside the AI Director
- `ai_director_plan_builder.py`'s `build_composition_plan` copies
  `direction.retention` straight onto `SceneComposition` — no new normalization
  function needed: out-of-range numeric fields are already rejected by
  `SceneRetention`'s own Pydantic `Field(ge=0.0, le=1.0)` constraints, which
  raises the same `AIDirectorValidationError` → automatic deterministic
  fallback every other malformed AI Director field already triggers
- `DeterministicCompositionPlanner` (F27) needed zero changes — it never
  constructs a `SceneRetention`, so `retention` stays `None` and
  `CompositionAwareShotPlanner` falls through to pre-F29 equal-split/
  contrast-heuristic behavior automatically whenever the AI Director is
  unavailable or disabled, satisfying the mandatory deterministic-fallback
  requirement with no explicit "ignore retention" branch needed
- No new settings, no new planner ABCs, no new orchestration layer — F29 is
  entirely additive optional fields plus one weighting formula change inside
  the existing `CompositionAwareShotPlanner`
- Status: Implemented and validated — **308 backend tests passing** (6 new:
  importance-weighted duration matching the spec's worked example, zero-duration
  impossibility, retention-driven transition selection overriding/deferring to
  the contrast heuristic, retention pass-through and default-`None` in the plan
  builder), clean `py_compile`/`compileall` across the whole backend. Zero
  added API cost (no new LLM calls — same one AI Director pass per production
  now returns more fields). Real production visual validation of the full
  F25–F29 stack (an actual rendered run, with a real seeded director agent)
  remains deferred until explicitly requested, to avoid unplanned generation
  cost.

### ✅ F30 Production Quality Validation — COMPLETED

- Audited the real F25–F29 pipeline against actual production evidence — 6 real
  `storage/runs/*` productions, `ffprobe` analysis of every video/audio stream, direct
  visual inspection of generated images/thumbnails, a full real execution log, and the
  actual `backend/services/` implementations — never documentation claims alone
- Deliverable: `docs/F30_PRODUCTION_QUALITY_REPORT.md` — scores, root-cause
  classification (Bug / Missing Feature / Prompt Engineering / AI Model Limitation /
  Rendering Limitation / Architecture Limitation), and a prioritized backlog assigned
  across F30–F35
- Headline findings that directly shaped F31's scope: no character/reference
  consistency across image generations (worst finding in the audit); every image
  generated at square 1024×1024 regardless of the 16:9 render target; no historical/
  visual continuity anchor shared across scenes; no automated detection of broken
  generations (multi-panel collages, garbled text); thumbnail visually disconnected
  from the documentary's own body images
- Status: report delivered; no code changed as part of F30 itself (validation-only,
  per its own charter). F31 (below) implements the F31-assigned findings from this
  report.

### ✅ F31 Photorealistic Visual Engine — COMPLETED

- Goal: turn the F30-validated "good AI illustration pipeline" into a documentary-grade
  visual generation system, without redesigning the pipeline or touching rendering/
  camera/audio (explicitly out of scope — reserved for F32/F33)
- **Photorealistic Prompt Engine** — `backend/services/photorealistic_prompt_builder.py`
  (`PhotorealisticPromptBuilder`), a new stateless prompt template assembler covering
  subject/action, environment, historical context, character identity, camera angle/
  framing/focal length/lens, depth of field, lighting, atmosphere, color palette, and an
  explicit documentary-photography realism directive ("not an illustration, not a
  painting, not concept art, not fantasy art"). `CompositionPromptEnricher`
  (`backend/services/composition_prompt_enricher.py`) now delegates to it instead of the
  old single generic style phrase — same seam, same call signature shape, fully
  additive (new params default to `None`/no-op)
- **Widescreen Native Image Generation** — `Settings.openai_image_size` default changed
  from `"1024x1024"` to `"1536x1024"` (gpt-image-1's closest native landscape option),
  applied uniformly to scene images and thumbnails. `CostTracker.PRICING_TABLE` gained
  accurate per-image pricing for the new landscape sizes. No renderer change — F32
  remains untouched; the image itself now arrives already oriented for cinematic
  framing
- **Historical Visual Consistency** — new `HistoricalVisualContext` schema
  (`backend/schemas/visual_identity.py`): time period, geography, architecture,
  materials, clothing, weapons/tools, symbols/landmarks, vegetation, weather/
  atmosphere, culture notes, color palette. Built once per production by the new
  `VisualIdentityService` (one LLM call over the finalized research/script) and reused
  by every scene/beat/thumbnail prompt
- **Character Consistency (centerpiece)** — new `CharacterVisualIdentity` schema: one
  canonical text description (face, hair, skin tone, clothing, accessories, build, age,
  distinguishing features) per recurring named figure, detected and generated once by
  `VisualIdentityService` and reused verbatim in every prompt that depicts them
  (deterministic whole-word name/alias matching, mirroring `CompositionPlanner`'s
  existing motif-detection discipline). This is the provider-agnostic baseline
  mechanism. A stronger, optional mechanism also ships: `CharacterReferenceImageService`
  generates one canonical reference portrait per character, and
  `ImageGenerationProvider.generate_image()` gained an optional `reference_image: bytes
  | None` parameter — `OpenAIImageGenerationProvider` uses it via the real
  `images.edit` (image-conditioned) endpoint when available, falling back to ordinary
  text-to-image generation on any failure, so consistency degrades gracefully rather
  than breaking the run
- **Image Validation** — new `ImageValidationService`: one vision-model classification
  call per generated image (multi-panel/split-screen composition, garbled/unreadable
  text, broken anatomy, obvious artifacts), wired into `SceneImageGenerationService` and
  `ThumbnailGenerationService` with up to one automatic regeneration attempt on failure.
  Fails open (treats a validator outage as "valid") — the same fallback discipline every
  other optional stage in this pipeline (AI Director, Audio Engine, cinematic
  rendering) already follows
- **Thumbnail Consistency** — `ThumbnailGenerationService` now builds its prompt through
  the same `PhotorealisticPromptBuilder` and consumes the same `VisualIdentityContext`
  (historical context + matched character, including that character's reference
  portrait when available) as the scene images, so the thumbnail depicts the same
  person, setting, and photographic style the video actually delivers
- New workflow step: `VisualIdentityStep`, inserted between Review and Media (runs
  once per production, before Thumbnail/Scene Planning/Composition Planning/Scene
  Image all need its output). Always reports success at the engine level — a failed or
  disabled Visual Identity pass returns an empty context, which every consumer already
  treats as "no additional guidance," identical to pre-F31 behavior. Persists
  `visual_context.json` and each character's reference portrait
  (`character_NN_name.png`) as real run artifacts — closing part of F30's own
  observability-gap finding (intermediate plan artifacts previously vanished; F31's new
  artifacts are allow-listed in `RunArtifactStorageService` from day one)
- New settings: `visual_identity_enabled`, `character_reference_images_enabled`,
  `max_characters_per_video` (default 3), `image_validation_enabled`,
  `image_validation_model`, `image_validation_max_retries` — all operator overrides with
  safe fallback defaults, mirroring `ai_director_enabled`/`audio_engine_enabled`'s
  existing pattern
- Backward compatible throughout: every new service/parameter defaults to `None`/off-
  equivalent behavior, so a call site that doesn't thread the new context through still
  behaves exactly as it did before F31
- Explicitly NOT touched, per F31's own charter: camera movement, transitions, zoom
  effects, rendering, voice, music, sound effects, audio mixing, publishing — reserved
  for F32/F33/F34/F35
- Status: implemented and validated — **349 backend tests passing** (36 new: prompt
  builder template coverage, visual identity schema matching/fragment-building,
  `VisualIdentityService` LLM-parsing and fallback paths, `CharacterReferenceImageService`
  portrait generation and failure handling, `ImageValidationService` pass/fail/fail-open
  paths, `OpenAIImageGenerationProvider`'s new `images.edit` conditioning + fallback,
  and updated `CompositionPromptEnricher`/`CompositionPlanningService`/
  `SceneImageGenerationService`/`ThumbnailGenerationService`/end-to-end workflow
  coverage). DI container verified to wire and resolve every new service with zero
  import errors. Real production cost impact stays within the existing $5/video ceiling
  (landscape scene images ≈$0.063/ea at medium quality vs. $0.042 square; a handful of
  character reference portraits stay square/cheap; one added Visual Identity LLM call
  per production).

### ✅ F31.5 Production Hardening Sprint — COMPLETED

- Purpose: a follow-up architecture review (F29–F31 audited as a "guilty until proven
  innocent" CTO-style critique) identified four Critical-severity gaps that had to close
  before F32 — this sprint closed all four in one coordinated pass, no architecture
  redesign, no new features.
- **F1 — Async production execution.** `POST /production/runs` previously awaited the
  entire pipeline inline (up to ~8 minutes per F30's real evidence), blocking past every
  realistic HTTP timeout with zero concurrency control. Now dispatches through the
  already-existing `BackgroundTaskManager`/`TaskBackend` infrastructure
  (`backend/api/v1/production.py`): the endpoint submits a background task, returns
  `execution_id` with status `"pending"` immediately (`202 Accepted`), and the pipeline
  runs via `asyncio.create_task` (tracked in a module-level set to avoid the well-known
  GC-of-untracked-tasks gotcha). New `GET /production/runs/{execution_id}` retrieves
  progress/status/results at any point in the run's lifecycle, reading from the existing
  `WorkflowHistoryStore` (rich step-by-step detail) with a `BackgroundTaskManager`
  fallback for the brief pre-start window. `WorkflowEngine.stream_execute()` gained one
  optional `execution_id` parameter (default `None` preserves the exact prior
  auto-generated-uuid4 behavior) so the caller can pre-generate the id and return it
  before the run finishes.
- **F3 — Real runtime budget enforcement.** `maximum_video_budget_usd` was previously
  advisory text fed into the AI Director's prompt only — nothing ever aggregated actual
  spend or stopped a call once the ceiling was crossed. New `BudgetTracker`
  (`backend/core/cost_tracker.py`): a small stateful tracker seeded from
  `context.cost_ledger` (everything spent by every prior step) via
  `CostTracker.build_budget_tracker()`, exposing `can_afford()`/`record_spend()`. Every
  paid image call (scene generation, thumbnail generation, character reference
  portraits, image validation, and any regeneration) now checks affordability BEFORE
  spending and gracefully SKIPS (never FAILS, never silently over-spends) once the
  budget is exhausted — implemented once in the new shared `ImageGenerationPipeline`
  (see F9 below) rather than duplicated per service. `ImageValidationService` gained its
  own pre-flight cost estimate (`CostTracker.estimate_image_validation_cost`, a
  fixed-token-surcharge approximation for one embedded image) and budget-gating — the
  cost source F31 introduced but never tracked is now fully accounted for. Each step
  that spends money (`VisualIdentityStep`, `ThumbnailStep`, `SceneImageStep`) computes
  `estimated_cost_so_far = sum(context.cost_ledger.values())` and passes it through
  (mirroring `CompositionPlanningStep`'s pre-existing pattern exactly); `VisualIdentityStep`
  additionally merges `VisualIdentityService`'s LLM cost with
  `CharacterReferenceImageService`'s image costs into one true step total, closing a gap
  where only half the step's real spend was ever reported. `AssetPackagingStep` now
  computes the run's true total cost against the ceiling and records
  `total_estimated_cost_usd`/`maximum_video_budget_usd`/`budget_status` on the final
  `AssetManifest` — the budget outcome is visible in the one artifact every run always
  produces, not just reasoned about in a prompt. Deliberately does NOT hard-abort the
  whole workflow on overage: per-call graceful degradation is the primary mechanism
  (see rationale in the trade-offs section below).
- **F9 — Character reference portrait validation.** `CharacterReferenceImageService`
  previously accepted whatever `images.generate` returned as a character's canonical
  identity anchor with zero quality check — the single highest-leverage image in the
  whole Character Consistency feature was also its only unguarded point of failure.
  Portraits now run through the same generate → validate → regenerate-once flow as
  every other image (see `ImageGenerationPipeline` below); critically, unlike scene/
  thumbnail images (which ship their best-effort result even if still invalid after a
  retry, since a scene frame has to be *something*), a reference portrait that is STILL
  invalid after retrying is REJECTED outright — `reference_image_filename` is left
  empty, and that character falls back to text-only consistency (an already-supported,
  fully backward-compatible path) rather than ever propagating a broken identity anchor
  into every subsequent scene.
- **New shared component — `ImageGenerationPipeline`**
  (`backend/services/image_generation_pipeline.py`): F31 had independently reimplemented
  an equivalent "generate → validate → maybe regenerate" loop in both
  `SceneImageGenerationService` and `ThumbnailGenerationService` (a duplication flagged
  by the architecture review); F9 needed the identical loop a third time. This class is
  now the single implementation all three (plus `CharacterReferenceImageService`) use —
  deliberately policy-free about what to do with a still-invalid final result (callers
  decide: ship anyway vs. reject outright), but the only place that decides how many
  attempts to make and whether each is affordable. Raises `ImageBudgetExceededError`
  (graceful skip, nothing attempted) or `ImageGenerationFailedError` (provider error/
  undecodable response, unchanged FAILED-asset handling) only on a first-attempt
  failure; once a first image exists, always returns a `GeneratedImage` carrying the
  TRUE total cost across every attempt (generation + validation + regeneration) — this
  is what makes `context.cost_ledger` reflect real spend instead of only the winning
  attempt's cost.
- **F11 — Opt-in live OpenAI smoke test.**
  `backend/tests/live/test_f31_live_openai_smoke.py`: makes real, billed calls against a
  live OpenAI account to verify the two F31 assumptions no fake-based unit test could
  ever catch — that `gpt-5.5` accepts multimodal `image_url` input (via the real
  `ImageValidationService`, not a hand-rolled call) and that `images.edit` reference
  conditioning is actually honored (asserting `used_reference_image is True`, not just
  that a response came back). Gated by a module-level `RUN_LIVE_SMOKE_TESTS=1`
  environment-variable check using `pytest.skip(..., allow_module_level=True)` — skipped
  cleanly (not run, not collected as a failure) under the normal `pytest backend/tests`
  invocation with zero API cost; the file's own docstring documents exactly how to run
  it manually. Verified: `pytest backend/tests` still shows a clean skip with no live
  calls made.
- Status: implemented and validated — **385 backend tests passing** (36 new: `BudgetTracker`
  and image-validation-cost estimation, the full `ImageGenerationPipeline` generate/
  validate/regenerate/budget matrix, F9's portrait-rejection paths, budget-exhaustion
  skip behavior for scene/thumbnail/character-reference generation, the async
  production-trigger background-task lifecycle, and `WorkflowEngine`'s new
  `execution_id` passthrough), plus 1 cleanly-skipped live smoke test module. DI
  container and full FastAPI app verified to import and wire with zero errors. Fully
  backward compatible: every new parameter defaults to preserve pre-F31.5 behavior for
  any caller that doesn't thread the new context through.
- Trade-off, stated explicitly: budget enforcement is per-paid-call (graceful
  degradation), not an engine-level hard abort of the whole workflow. Image generation
  is by far the dominant, variable cost driver (per F30's own finding) and is fully
  gated; the small number of non-image steps (research/strategy/writer/review/voice/
  subtitle/audio-mix) are relatively fixed-cost and are not individually budget-gated —
  aborting a nearly-complete run over a marginal, non-image overage was judged a worse
  outcome than shipping a complete video with `budget_status: "exceeded"` visible in the
  manifest for follow-up.

---

## Current Architecture State

### Core Infrastructure

**Deployed Stack:**
- **Frontend:** Next.js 16.2.10, React 19.2.4, TypeScript (strict mode), Tailwind CSS 4, Lucide React
- **Backend:** FastAPI 0.139.2, Python 3.14, Pydantic v2.13.4
- **Data Layer:** Service/Repository pattern, strict separation of concerns
- **Authentication:** JWT-based auth with role management
- **Streaming:** Server-Sent Events (SSE) for real-time responses
- **State Management:** React Query 5 (server state), Zustand (UI state, minimal usage)
- **Deployment:** Vercel (frontend), Railway (backend)

**Services Implemented:**
- `AuthService` — User authentication and session management
- `ConversationEngine` — CRUD operations for conversations
- `ConversationService` — Message streaming with parameters (temperature, max_tokens, system_prompt)
- `LLMProvider` — AI model integration with parameter support
- `RAGService` — Knowledge base retrieval
- `EventBusService` — Conversation lifecycle events
- `MemoryService` — Persistent context management
- `AgentService` / `AgentRepository` — Persistent agent entities (Supabase-backed, live)
- `AgentRuntime` / `AgentOrchestrator` — Default chat execution path; default-agent
  resolution, automatic delegation planning, tool-use detection
- `ToolManager` / `ToolRegistry` — Tool execution façade and registry (7 tools registered:
  memory, web search, URL/PDF/markdown/text readers, vision, image generation)

### Architecture Principles

**Established Rules:**
1. **Reuse existing infrastructure** whenever possible — No parallel systems
2. **No duplicate services** — Consolidate logic into single, reusable modules
3. **No unnecessary wrappers** — Keep component hierarchy flat
4. **No unnecessary abstraction** — Prefer explicit code over magic
5. **Local state preferred** — Global store only when required across routes
6. **Extend, don't duplicate** — Add to existing modules rather than creating parallel versions
7. **Lean implementation** — Avoid over-engineering; prioritize shipping working features

**Applied Patterns:**
- Backend: Service → Repository → Database
- Frontend: Route page owns state → child components receive props
- Streaming: EventSource (SSE) with event types (start, token, end, error)
- Parameters: Extracted at endpoint level, passed downstream to LLMRequest

### Key Recent Decisions

**F11 (AI Playground) Architecture:**
- No Redux/Zustand for playground state — Ephemeral, route-isolated state kept in route page
- Reuse `conversationService.streamMessage()` — No duplicate streaming logic
- "Clear" as new conversation — Creates new conversation instead of deleting; preserves history
- No sidebar wrapper — Playground standalone route; conversation selection via header dropdown
- Parameter extraction in endpoint — Each endpoint handles POST body vs. GET query params

**F16/F16.1 (Agent Runtime Default + Automatic Delegation) Architecture:**
- Default-agent resolution lives in the API layer (`conversations.py`), not in
  `AgentRuntime`/`AgentOrchestrator` themselves — keeps those reusable for workflow
  services that already resolve their own agent
- Auto-delegation is two separate, narrowly-scoped LLM classification calls (delegate
  planning, then tool-use), not one compound decision — a compound version proved
  unreliable in testing (agents tried to re-delegate their own assigned work)
- RAG augmentation is intentionally not wired into `AgentOrchestrator` — matches
  pre-existing `/agents` page behavior; revisit only if a real workflow needs it
- See `docs/DECISIONS.md` ADR-009–ADR-011 for full rationale

---

## Product Roadmap

### Upcoming Features — First Complete Production Flow (Idea → Workflow → Assets → Video → Upload → Monitoring)

> Supersedes the previous F18–F23 list (Automations/Integrations/Team/Billing/Analytics/
> Production Readiness), which no longer reflected the actual state of the codebase. The
> 12-step `youtube_production_workflow.py` pipeline (Research → Strategy → Writer → Review →
> Media → Publishing Package → Voice → Thumbnail → Scene Planning → Scene Image → Subtitle →
> Asset Packaging) is real and largely complete. F20 (production run trigger) and F21
> (per-scene images) are done; the tasks below close the remaining gaps (video assembly,
> a canonical run manifest, and wiring the already-built YouTube upload service to it)
> needed for one real end-to-end run.

**F20 — Production Run Trigger API — ✅ COMPLETED**
- Scop: replace the fake in-memory stub in `execution.py` with a real entry point into the pipeline.
- Ce se implementează: `POST /api/v1/production/runs {topic}` invoking `WorkflowEngine`/`build_youtube_production_workflow` via existing DI; returns `execution_id`.
- Criterii de acceptare: request with a topic starts the real pipeline (not the fake dict); auth-gated like other endpoints.
- Dependențe: none.
- Status: implemented and test-verified.

**F21 — Scene Image Generation — ✅ COMPLETED**
- Scop: `scene_prompts` are text-only today; no real per-scene images exist, blocking any video assembly.
- Ce se implementează: reuse `OpenAIImageGenerationProvider` (already used for the thumbnail) against each `ScenePromptSet` prompt; new `SceneImageStep` in the pipeline.
- Criterii de acceptare: each scene produces a real image file on disk, with the same retry/cost metrics as Thumbnail.
- Dependențe: none.
- Status: implemented and test-verified; `AssetPackagingStep`/`asset_manifest.json` intentionally left untouched (belongs to F24).

**F22 — Video Assembly Service — ✅ COMPLETED**
- Scop: nothing composes audio + images + subtitles into an actual video — the largest gap in the flow.
- Ce se implementează: `backend/services/video_assembly_service.py` using `ffmpeg` (subprocess) to render a slideshow from scene images timed to the narration audio; new `VideoAssemblyStep` writes `video_file_path`.
- Criterii de acceptare: a full run produces a real, playable `.mp4` on disk.
- Dependențe: F21.
- Status: implemented and test-verified; static slideshow only (no Ken Burns zoom/pan); `workflow_export_validators.py`/`FUTURE_ASSETS` intentionally left untouched (belongs to F24).

**F23 — Subtitle/Audio Duration Sync — ✅ COMPLETED**
- Scop: SRT cues are timed off a fixed 150wpm estimate, not the real generated narration duration.
- Ce se implementează: `SubtitleGenerationService.execute()` now takes the `VoiceAsset` produced by the
  `Voice` step; per-sentence cue weights are still computed from word count, but when the voice
  generation succeeded with a real `duration > 0`, cue durations are scaled so their sum equals
  `VoiceAsset.duration` exactly. Falls back to the previous fixed-rate estimate only when voice
  generation was skipped/failed (no real duration to sync against). `SubtitleStep` in
  `youtube_production_workflow.py` now reads `context.inputs["Voice"]["voice_asset"]` (the `Voice`
  step already runs earlier in the pipeline) and passes it through.
- Criterii de acceptare: cue timestamps sum to ≈ `VoiceAsset.duration`; tests updated.
- Dependențe: none.
- Status: implemented and test-verified.

**F24 — Workflow Artifact Manifest — ✅ COMPLETED**
- Scop: run output today is scattered across per-step data and a partial `asset_manifest.json` — no single canonical object publishing, monitoring, debugging, and future UI can all consume.
- Ce se implementează: repositions/extends the existing `AssetPackagingStep` into a `WorkflowArtifactManifest` step run immediately after `VideoAssemblyStep` (last step of the pipeline), aggregating `video_file_path`, publishing package (title/description/hashtags), thumbnail/subtitle paths, scene/broll/music plans, per-step cost totals, and step statuses into one canonical `manifest.json`.
- Criterii de acceptare: after a full run, `manifest.json` contains every field publishing and monitoring need, validated against a dedicated schema/dataclass.
- Dependențe: F21, F22, F23.
- Status: implemented and live-validated against the first real, complete production run
  (see the F24 entry under Completed Features above). **The pipeline is now considered
  functionally validated.**

---

### Upcoming Features — Quality First (Post-F24 Priority Shift)

> **Priority change (2026-07-21):** After reviewing the first generated video, publishing
> automation is **no longer the next priority**. The goal now is to maximize the quality of
> generated videos before automating publishing. This supersedes the previous F25–F28 list
> (Publishing Consumes the Manifest, Workflow Run Status & History API, Cost Visibility in
> Monitoring, End-to-End MVP Integration Test) — that work is not discarded, it is deferred
> and folded into **F35 — Automated Publishing** below, to be resumed once video quality
> reaches the desired bar. See `docs/planning/ROADMAP.md` for the same list at
> milestone-roadmap level. All architectural principles below are unchanged.
>
> **Update (2026-07-22):** F25–F29 are now complete. Real-world testing of that pipeline
> has shown the next development phase should focus on maximizing production quality before
> publishing automation. The single F30 placeholder below is replaced by **Phase 2 —
> Production Quality** (F30–F35); see `docs/planning/ROADMAP.md` for the same structure at
> milestone-roadmap level.

**F25 — Cinematic Rendering Engine — ✅ COMPLETED**
- Goal: transform static slideshow scenes into cinematic scenes using local rendering
  (camera movement, pan, push-in, parallax, depth effects, particles, fog, light rays,
  subtle transitions).
- Important: prioritize local rendering (FFmpeg, Remotion, OpenCV, or similar) instead of
  generating AI video, to keep API costs nearly unchanged.
- Dependențe: F22 (Video Assembly Service).
- Status: implemented as the Cinematic Video Engine — see F25 under Completed Features
  above for full detail. Fully validated (152 tests passing, clean compile, DI verified);
  real production visual validation deferred until after F26/F27 to avoid unnecessary
  generation costs.

**F26 — Audio & Voice Engine — ✅ COMPLETED**
- Goal: greatly improve narration quality — deeper male voice, more natural pacing,
  dramatic pauses, adaptive background music, automatic sound effects, automatic audio
  mixing.
- Dependențe: none.
- Status: implemented as the Jarvis Audio Engine — `VoiceDirection`/`AudioTimeline`
  contracts mirroring F25's `Shot` philosophy, `gpt-4o-mini-tts` narration with
  profile-driven delivery instructions, ffmpeg-only narration processing/mixing/
  mastering, optional local-library music/SFX. See F26 under Completed Features above
  for full detail. 188 backend tests passing; real production audio validation
  deferred alongside F25's, to bundle with F27.

**F27 — Smart Scene Composition — ✅ COMPLETED**
- Goal: make every scene feel intentionally directed — narrative purpose, framing,
  visual continuity, and rhythm, instead of independently-generated images.
- Dependențe: F21 (Scene Image Generation).
- Status: implemented as `TimelinePlan` (single source of truth for scene timing) →
  `CompositionPlan` (purpose/framing/continuity, consumes but never calculates
  timing) → `CompositionAwareShotPlanner`/`CompositionPromptEnricher`. See F27 under
  Completed Features above for full detail. 226 backend tests passing; zero added
  API cost; real production validation deferred alongside F25/F26's, to bundle with
  F28.

**F28 — AI Director — ✅ COMPLETED**
- Goal: the LLM generates cinematic direction for every scene, not only image prompts
  (camera movement, scene duration, atmosphere, transition, lighting, particles, emotional
  intensity); the renderer executes these directions automatically.
- Dependențe: F25 (Cinematic Rendering Engine). F27 (Smart Scene Composition) prepared
  the seam: an LLM-driven `TimelinePlanner`/`CompositionPlanner` can replace today's
  deterministic ones with no change to `ShotPlanner`/`AudioTimelinePlanner`/
  `RendererPipeline`/`AudioMixerService`.
- Status: implemented exactly on that seam — a new `AIDirectorProvider` abstraction
  (`AgentRuntimeAIDirectorProvider` reusing the existing agent execution path) produces
  one `AIDirectorPlan` per production from a single reasoning pass over the whole
  script, validated/normalized by `ai_director_plan_builder.py` into the real
  `TimelinePlan`/`CompositionPlan` — with automatic wholesale fallback to F27's
  deterministic planners on any unavailability or validation failure. No new planner
  ABCs, no changes to `RendererPipeline`/`AudioMixerService`/`ImageGenerationProvider`.
  See F28 under Completed Features above for full detail. 249 backend tests passing;
  zero architectural redesign; real production validation deferred to bundle with F29.

**F28A — Render Profiles — ✅ COMPLETED**
- Goal: standardize how finished videos are rendered and exported — a strongly typed
  `RenderProfile` becomes the single source of truth for every technical
  rendering/export parameter, with no renderer/exporter/encoder hardcoding a technical
  value. Not an AI, planning, or image-generation feature.
- Dependențe: F25 (Cinematic Rendering Engine).
- Status: implemented exactly as scoped — `RenderProfile`
  (`backend/schemas/render_profile.py`) plus `RenderProfileRegistry` shipping one
  production-ready "YouTube Long" profile (1920×1080, 16:9, 30fps, H.264/AAC, 48kHz,
  MP4, CRF 18). `RendererPipeline`, `VideoAssemblyService`'s legacy slideshow
  fallback, and `AudioMixerService` all consume it via one additive constructor
  parameter (defaulting to "YouTube Long" automatically when omitted) instead of
  each hardcoding `libx264`/`yuv420p`/`aac`/`_FPS = 24` independently as before.
  Adding a future platform (Shorts, TikTok, HEVC, AV1, HDR, ...) is registering one
  new `RenderProfile` — no Renderer redesign. See F28A under Completed Features
  above for full detail. 280 backend tests passing; zero added API cost; zero
  changes to AI Director, TimelinePlan, CompositionPlan, Shot, or AudioTimeline.

**F28B — Adaptive Visual Storytelling Engine — ✅ COMPLETED**
- Goal: evolve Scene → One Generated Image into Scene → Visual Beats → One
  Generated Image per Visual Beat, eliminating long static scenes, without
  redesigning the renderer/timeline/audio/AI Director architecture.
- Dependențe: F28 (AI Director), F27 (Smart Scene Composition).
- Status: implemented exactly on the existing seam — `VisualBeat` added to
  `SceneComposition`/`AIDirectorSceneDirection` (no new planner type), AI Director
  made Production-Budget-Aware via new configurable settings, Cost Validation
  (clamp + budget-based trimming) added to `ai_director_plan_builder.py`,
  `CompositionPromptEnricher`/`SceneImageGenerationService`/
  `CompositionAwareShotPlanner` extended to handle one-image-per-beat while
  `TimelinePlan`/`RendererPipeline`/`AudioMixerService`/`ImageGenerationProvider`
  remain completely untouched. See F28B under Completed Features above for full
  detail. 302 backend tests passing; fully backward compatible (deterministic
  fallback never produces visual_beats, so Scene → One Image is preserved exactly
  whenever the AI Director is unavailable/disabled).

**F29 — Viewer Retention Engine — ✅ COMPLETED**
- Goal: optimize every video for YouTube retention — stronger hooks, cliffhangers, pacing
  optimization, curiosity loops, emotional progression, stronger endings.
- Dependențe: none.
- Status: implemented as an optional `SceneRetention` extension to
  `CompositionPlan`/`AIDirectorSceneDirection` plus an importance-weighted
  replacement for F28B's equal beat-duration split. See F29 under Completed
  Features above for full detail. 308 backend tests passing; zero added API
  cost; zero changes to TimelinePlan, RendererPipeline, AudioMixerService, or
  ImageGenerationProvider; deterministic fallback verified to reproduce
  pre-F29 behavior exactly.

### Phase 2 — Production Quality

The objective of this phase is no longer proving that the pipeline works. The objective
is producing documentaries that are visually and audibly competitive with successful
YouTube documentary channels while keeping production costs below approximately
$5/video.

**F30 — Production Quality Validation — ✅ COMPLETED**
- Purpose: audit the complete F25–F29 pipeline using real productions; compare expected
  architecture vs actual generated output; remove remaining quality bottlenecks; validate
  every subsystem using real production runs.
- Deliverable: Production Quality Report — see `docs/F30_PRODUCTION_QUALITY_REPORT.md`.
- Dependențe: F25, F26, F27, F28, F28A, F28B, F29.
- Status: report delivered against real production evidence (6 real runs, ffprobe
  analysis, direct image/log inspection). See F30 under Completed Features above.

**F31 — Photorealistic Visual Engine — ✅ COMPLETED**
- Goal: improve image realism without redesigning the architecture.
- Focus: cinematic prompting, photorealism, historical consistency, visual consistency,
  better scene composition, higher perceived production value.
- Dependențe: F30.
- Status: implemented — Photorealistic Prompt Engine, native landscape image generation,
  Historical Visual Consistency, Character Consistency (text-anchored + optional
  image-conditioned reference portraits), Image Validation with automatic
  regeneration, and Thumbnail Consistency all shipped. See F31 under Completed
  Features above for full detail.

**F32 — Cinematic Camera Language**
- Goal: improve how static images become cinematic scenes.
- Includes: scene-aware camera movement, more natural motion, less repetitive zooming,
  improved transitions, stronger visual storytelling.
- Dependențe: F30.

**F33 — Premium Audio Experience**
- Goal: improve immersion.
- Includes: expressive narration, better voice direction, background music, ambient
  sound, cinematic sound effects, adaptive audio mixing.
- Dependențe: F30.

**F34 — Production Polish**
- Goal: final production refinements.
- Includes: color grading, pacing refinements, transition improvements, continuity
  improvements, final quality polish.
- Dependențe: F30.

**F35 — Automated Publishing**
- Goal: all YouTube upload automation — upload, scheduling, playlists, visibility, thumbnail
  upload, monitoring. Absorbs the previously-planned F25–F28 work (publishing reading from
  the manifest, run status/history API, cost visibility, end-to-end integration test).
- Intentionally postponed until production quality reaches the desired level.
- Dependențe: F24.

Explicitly deferred (would be scope creep before the quality bar is met): automated
idea/trend generation, durable (non-in-memory) run history.

---

## Quality-First Development Principle

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

## Product Progress

| Component | Status | Notes |
|-----------|--------|-------|
| **Foundation** | 100% | Auth, Dashboard, Navigation, Base infrastructure |
| **Core AI** | ~55% | Conversations, Memory, Prompts, Playground, Agent runtime as default chat path |
| **Agents & Tools** | ~70% | F12–F17E complete: agents live against real Supabase, default resolution, automatic delegation, tool execution verified end-to-end |
| **Advanced Features** | ~10% | Tools/Workflows/Tasks foundations complete (F13–F15); Documents (RAG), Projects, Automations still pending |
| **Production Pipeline** | ✅ 100% (F20–F24) | Full 10-stage pipeline (research → strategy → script → review → scene planning → scene images → thumbnail → narration → subtitles → final MP4) implemented and **functionally validated end-to-end** in a real production run (~$0.85/video) |
| **Video Quality (F25–F29)** | ✅ 100% (F25–F29 done) | ✅ Cinematic Rendering, ✅ Audio Engine, ✅ Smart Scene Composition, ✅ AI Director, ✅ Render Profiles, ✅ Adaptive Visual Storytelling, ✅ Viewer Retention Engine — the full quality-first roadmap is implemented; a real bundled production run is the remaining validation step |
| **Production Quality — Phase 2 (F30–F34)** | 40% (F30, F31 done) | ✅ Production Quality Validation (real-evidence audit + report), ✅ Photorealistic Visual Engine (prompt engine, landscape generation, historical/character consistency, image validation, thumbnail consistency); Cinematic Camera Language, Premium Audio Experience, Production Polish remain |
| **Publishing Automation (F35)** | 0% | Intentionally postponed until Phase 2 validates the video quality bar |
| **Overall Product** | ~54% | Multi-agent chat pipeline live end-to-end; first real production run validated; roadmap now spans 35 total features |

### Post-F24 Projection

- **First complete production workflow validated** — the pipeline reliably produces a full,
  real YouTube video end-to-end at ~$0.85/video
- **All of F25–F29 (video quality architecture) are now implemented**; F30 validated that
  architecture against real production evidence, and F31 has closed its highest-priority
  visual-quality findings
- Time to commercial launch: **TBD** — next gate is F32 (Cinematic Camera Language)
  against the F30 report's remaining camera/rendering findings, not publishing
  automation (deferred to F35)

---

## Business Strategy

### Core Principle

**Jarvis is NOT being built as a demo.** Jarvis is being built to run real businesses.

### Business #1: English YouTube Automation

**Goal:** Jarvis should automate the complete YouTube video production pipeline:

- Research (via Knowledge Base + RAG)
- Scripting (via AI + Prompts + Playground)
- Prompt Management (via Prompts Library)
- Memory (via AI Memory)
- Knowledge Retrieval (via Documents + RAG)
- Agent Execution (via AI Agents)
- Workflow Orchestration (via Workflows)
- Automation (via Automations)
- Publishing Pipeline (via Integrations)

### Launch Strategy

**IMPORTANT:** Do NOT wait until F23 before launching.

**Launch Target:** Public YouTube videos after **F12 (AI Agents)** and **F13 (Tools)** are complete.

**Rationale:** At that point, Jarvis has:
- ✅ Conversations (chat interface)
- ✅ Memory (persistent context)
- ✅ Prompts (reusable templates)
- ✅ Playground (parameter tuning)
- ✅ Agents (autonomous execution)
- ✅ Tools (external integrations)

**This is sufficient for an end-to-end automated production workflow.**

**Strategy:**
1. Launch YouTube videos **after F12–F13**
2. Continue building platform **in parallel**
3. Validate Jarvis in real world **before platform completion**
4. Use video metrics and user feedback to **prioritize remaining features**

---

## Development Rules

### Always Apply

- ✅ **Prefer simplicity** — Avoid clever or over-engineered solutions
- ✅ **Avoid over-engineering** — Don't build for hypothetical future needs
- ✅ **Reuse existing components** — Check service/repository/component library before creating new
- ✅ **Avoid duplicate logic** — Consolidate similar code into single source
- ✅ **Keep architecture modular** — Services are independently testable
- ✅ **Keep implementation incremental** — Ship working features in small, reviewable chunks

### Feature Completion Checklist

Every feature must end with:

- ✅ **Implementation Summary** — Document architecture, decisions, integration points
- ✅ **Validation Results** — ESLint, TypeScript, Production Build
- ✅ **ESLint PASS** — 0 feature-specific errors/warnings
- ✅ **TypeScript PASS** — Strict mode type checking
- ✅ **Production Build PASS** — Full production build succeeds

### Feature Approval Gate

1. **Propose feature** (user or team)
2. **Architect reviews** — ChatGPT provides architecture analysis
3. **User approves/refines** — Two-way feedback loop
4. **Implementation begins** — Claude Code implements approved architecture
5. **Validation** — Feature must pass all checklist items
6. **Merge & deploy** — Approved features integrated to main branch
7. **Next feature** — Proceed only after current feature complete and approved

---

## System Design

```
User Browser
    ↓
Next.js Frontend (React 19, TypeScript)
    ↓
Axios HTTP Client (Auth interceptors)
    ↓
FastAPI Backend (Python 3.14)
├─ Authentication (Supabase Auth)
├─ Conversation Engine (Real-time SSE streaming)
├─ LLM Orchestrator (OpenAI async client)
├─ RAG Service (Vector retrieval)
├─ Document Ingestion (Multi-format support)
├─ Task Management (Async operations)
└─ Agent System (Tool execution)
    ↓
Supabase PostgreSQL + Auth
```

### Tech Stack

**Frontend:**
- Next.js 16.2.10 with App Router
- React 19.2.4 with strict TypeScript
- Tailwind CSS 4 (CSS variables, dark mode)
- Zustand 5 (state management)
- React Query 5 (server state)
- Radix UI (accessible components)
- Framer Motion (animations)

**Backend:**
- FastAPI 0.139.2 (async Python)
- Pydantic 2.13.4 (validation & settings)
- AsyncOpenAI 1.109.1 (LLM)
- Supabase Client 2.31.0 (auth & database)
- Python 3.14

**Infrastructure:**
- Middleware stack (auth, security, rate limiting, compression, metrics)
- Service registry with lazy initialization
- Dependency injection (FastAPI Depends)
- Exception handling (domain + HTTP)
- Request context tracking

---

## Backend Completion Status

### ✅ Core APIs (100% Complete)

| Endpoint | Status | Details |
|----------|--------|---------|
| **Authentication** | ✅ Complete | Sign in, refresh token, user profile, logout |
| **Conversations** | ✅ Complete | CRUD, message history, streaming chat |
| **Knowledge/Memory** | ✅ Complete | Document storage, vector retrieval, memory records (endpoint bugs found in F17A fixed in F17B–D) |
| **Tools & Execution** | ✅ Complete | Tool registry, execution, result tracking |
| **Agents** | ✅ Complete | Live against real Supabase (F17E); default resolution + automatic delegation (F16/F16.1) |
| **Documents** | ✅ Complete | Multi-format upload, parsing, chunking |
| **Health & Metrics** | ✅ Complete | Status checks, metrics collection |
| **Projects & Users** | ✅ Complete | User management, project isolation |

### ✅ Infrastructure (95% Complete)

| Component | Status | Notes |
|-----------|--------|-------|
| Configuration | ✅ Fixed | Pydantic v2, env loading verified |
| LLM Provider | ✅ Working | OpenAI async, comprehensive logging |
| Embedding Provider | ✅ Working | OpenAI embeddings for RAG |
| Vector Store | ✅ Implemented | In-memory + Supabase integration |
| RAG Service | ✅ Implemented | Query, retrieve, re-rank |
| Event Bus | ✅ Implemented | In-memory pubsub for events |
| Task Manager | ✅ Implemented | Async task tracking |
| Conversation Engine | ✅ Implemented | History, streaming, context mgmt (in-memory store, ADR-003) |
| Document Ingestion | ✅ Implemented | Parser registry, chunking strategies |
| Agent Runtime | ✅ Implemented | Default chat execution path, automatic delegation, tool-use detection |
| Database (Supabase) | ✅ Live | Configured 2026-07-19 (F17E) — Agents/Projects/Users persisted for real; Conversations/Memory/Vector/Prompts remain in-memory per ADR-003 (unchanged) |
| Startup Validator | ✅ Implemented | Health checks on startup |

### ⚠️ Gaps (5% - Non-blocking)

- Workflow orchestration (n8n integration stubbed, not fully connected)
- Background job processing (task manager exists, workers not deployed)
- Vector database (in-memory fallback works, real VectorDB not integrated)
- Advanced prompt engineering (templates exist, advanced features not used)
- RAG augmentation not wired into `AgentOrchestrator` (default chat path doesn't apply
  `use_rag` — matches pre-existing `/agents` page behavior; see DECISIONS.md ADR-010)

---

## Session History

### Recent Session (2026-07-19)

**Completed:**
- ✅ F11 (AI Playground) full implementation
  - Backend: Extended chat request schema with runtime parameters
  - Frontend: Route page + focused playground components
  - Validation: ESLint ✓, TypeScript ✓, Production Build ✓
  - Generated: F11_IMPLEMENTATION_SUMMARY.md
- ✅ F12 (AI Agents) full implementation
  - Backend: Persistent agents domain (model/schema/repository/service/API) + runtime-first orchestration
  - API: Existing conversation chat/stream endpoints extended with optional `agent_id`
  - Frontend: Agent service/hooks/selector + agents page integrated with chat flow
  - Database: SQL migration added for agents table and initial seed
  - Validation: ESLint ✓, TypeScript ✓, Production Build ✓, Python compile ✓
  - Generated: F12_IMPLEMENTATION_SUMMARY.md

**Key Metrics:**
- Files created: F11 + F12 implementation files (backend, frontend, migration, summaries)
- Frontend validation: build and strict TypeScript pass
- Lint status: feature code passes without new errors
- Backend validation: Python compile pass

**System State:**
- All 7 completed features passing validation
- Architecture stable and modular
- Ready for F13 (Tools) architecture review

### Recent Session (2026-07-19, continued) — F16 through F17E

**Completed:**
- ✅ F16 Agent Runtime Default Chat Engine — normal chat now always executes through
  `AgentRuntime`/`AgentOrchestrator`, defaulting to General Assistant
- ✅ F16.1 Automatic Agent Delegation — free-form chat now auto-detects and executes
  delegation/tool use without manual agent selection
- ✅ F17A Architecture-Aware Audit (read-only) — 8 Critical / 4 High / 11 Medium / 4 Low
  findings, classified against intentional design vs. real bugs
- ✅ F17B Critical Stability Fixes — all approved Critical/High/Medium findings fixed and
  live-validated
- ✅ F17C Retrieval API Final Fix — `RetrievalEngineService.retrieve()` method-name bug
- ✅ F17D Embedding Usage Compatibility Fix — Embeddings API `Usage` field mismatch
- ✅ F17E Restore Default General Assistant — Supabase configured, 3 migrations applied,
  8 core agents seeded, default-agent resolution and end-to-end chat verified live

**Key Metrics:**
- Backend files modified across F16–F17E: `agent_orchestrator.py`, `agent_runtime.py`,
  `agent_service.py`, `conversations.py`, `auth.py`, `knowledge.py`, `documents.py`,
  `agent_repository.py`, `project_repository.py`, `tool_content_processing_service.py`,
  `openai_embedding_provider.py`
- Frontend files modified: `store/index.ts`, `api-client.ts`, `protected-app-layout.tsx`,
  `conversation-service.ts`, `chat-page.tsx`, `agents/page.tsx`
- Validation: `py_compile` + real imports clean throughout; `tsc --noEmit` and `eslint`
  clean on all touched frontend files; live smoke tests against a running backend for
  every fix (auth, knowledge/memory/documents, retrieval, embeddings, chat resolution)
- Infrastructure: Supabase project `saqldhjlmdtatmacdmha` now configured and live for the
  Agents/Projects/Users domain

**System State:**
- Multi-agent chat pipeline fully live end-to-end against a real Supabase database
- Both entry points (`/chat` default-agent, `/agents` explicit-agent) verified working
- Ready for the first real end-to-end production workflow validation

### Recent Session (2026-07-21) — F24 & First Real Production Run

**Completed:**
- ✅ F24 Workflow Artifact Manifest — canonical `manifest.json` produced as the pipeline's
  final step
- ✅ **First real, complete end-to-end YouTube production run** — research, strategy,
  script, review, scene planning, scene images, thumbnail, narration, subtitles, and final
  MP4 all generated successfully in one run
- ✅ Brave Search replaced DuckDuckGo as the search provider
- ✅ OpenAI quota issue resolved
- Total measured production cost: **≈ $0.85/video**

**Decision:** After reviewing the generated video, publishing automation was deprioritized
in favor of maximizing video quality first. Roadmap reordered: F25 Cinematic Rendering
Engine, F26 Audio & Voice Engine, F27 Smart Scene Composition, F28 AI Director, F29 Viewer
Retention Engine, F30 Automated Publishing (postponed). See `docs/planning/ROADMAP.md`.

**System State:**
- Production pipeline functionally validated end-to-end against live providers
- Next work is quality-focused (F25–F29); no publishing-automation code will be touched
  until that bar is met

### Recent Session (2026-07-21, continued) — F25 Cinematic Video Engine

**Completed:**
- ✅ F25 Cinematic Video Engine — `Shot` data contract + modular `RendererPipeline`
  (`CameraMovement`, `Transition`, `AtmosphereOverlay`, `ColorProcessing`) executing Shots
  produced by a deterministic `ShotPlanner`; legacy slideshow renderer kept as an automatic
  fallback on any cinematic-rendering failure
- Entirely local/ffmpeg-based — OpenAI usage and per-video cost unchanged

**Key Metrics:**
- 152 backend tests passing (including 6 new test files for the cinematic modules plus
  updated `video_assembly_service`/`youtube_production_workflow` tests)
- Clean `py_compile`/`compileall` across all touched backend files
- Dependency injection verified live (`get_video_assembly_service()` resolves the new
  `ShotPlanner`/`RendererPipeline` correctly)

**System State:**
- F25 fully implemented and validated at the code/test level
- Real production visual validation (an actual rendered run) intentionally deferred until
  after F26/F27, to avoid unnecessary generation costs
- F26 (Audio & Voice Engine) is now the current active feature

### Recent Session (2026-07-21, continued) — F26 Jarvis Audio Engine

**Completed:**
- ✅ Architecture proposal (`docs/F26_ARCHITECTURE_PROPOSAL.md`) researched, written,
  and approved with one revision: an explicit `AudioTimeline` contract (Shot's audio
  counterpart) was introduced so `AudioMixerService` stays a pure executor
- ✅ F26 Jarvis Audio Engine implemented per the revised architecture: `VoiceDirection`/
  `VoiceProfile` (7 profiles), upgraded `gpt-4o-mini-tts`/`onyx` narration with
  delivery `instructions`, `NarrationProcessingService` (ffmpeg `loudnorm`), optional
  `LocalMusicLibraryProvider`/`LocalSoundEffectLibraryProvider` (off by default —
  no asset library ships with this repo), `AudioTimelinePlanner` →
  `AudioMixerService` (ffmpeg `sidechaincompress` ducking + `afade` + `loudnorm`
  mastering), new `AudioEngineService`/`AudioEngineStep` wired into
  `youtube_production_workflow.py` between Subtitle and Video Assembly, with automatic
  fallback to raw normalized narration on any mixing failure or disabled config
- Provider decision executed as approved: stayed on OpenAI, ElevenLabs deferred (not
  foreclosed — `TextToSpeechProvider` remains swappable)

**Key Metrics:**
- 12 new backend files (`schemas/audio.py` + 11 services) and 8 new test files; 4
  existing files extended (`voice_generation_service.py`, `text_to_speech_provider.py`
  + its OpenAI/Default implementations, `youtube_production_workflow.py`), plus
  `config.py`/`cost_tracker.py`/`dependencies.py` wiring
- 188 backend tests passing (36 new), clean `py_compile`/`compileall`, DI verified live

**System State:**
- F26 fully implemented and validated at the code/test level
- Real production audio validation intentionally deferred until after F27, bundled
  with F25's deferred visual validation
- F27 (Smart Scene Composition) is now the current active feature

### Recent Session (2026-07-21, continued) — F27 Smart Scene Composition

**Completed:**
- ✅ Architecture proposal (`docs/F27_ARCHITECTURE_PROPOSAL.md`) researched, written,
  and approved with one revision requested at approval time: a new `TimelinePlan`
  contract (the single source of truth for scene ordering/duration/start/end/pacing),
  inserted between Scene Planning and Composition Planning, so `CompositionPlan` and
  `AudioTimeline` consume timing instead of each independently calculating it — closing
  a drift risk the original proposal had explicitly flagged but deferred
- ✅ F27 Smart Scene Composition implemented per the revised architecture:
  `TimelinePlan`/`TimelinePlanner` (position-based `ScenePacing` arc, normalized to the
  real narration duration), `CompositionPlan`/`CompositionPlanner` (purpose/framing/
  camera-intent/color-language/continuity-motifs/relationships, consuming but never
  calculating timing), `CompositionPlanningService` (new "Composition Planning"
  workflow step between Scene Planning and Scene Image), `CompositionPromptEnricher`
  (deterministic prompt templating — `ImageGenerationProvider` untouched),
  `CompositionAwareShotPlanner` (new default `ShotPlanner`, with automatic fallback to
  the original deterministic behavior on any scene-count mismatch)
- `AudioTimelinePlanner` extended with an additive `timeline_plan` parameter (falls
  back to its original proportional split when absent/mismatched); `VideoAssemblyService`'s
  total-duration formula fixed to sum each shot's own duration instead of assuming a
  uniform `scene_seconds` — verified live to keep video and audio scene boundaries
  identical even with fully variable per-scene pacing
- All entirely deterministic — zero added LLM calls, zero added API cost

**Key Metrics:**
- 7 new backend files (`schemas/timeline.py`, `schemas/composition.py`, and 5 new
  services) and 5 new test files; 6 existing files extended
  (`cinematic_shot_planner.py`, `audio_timeline_planner.py`, `video_assembly_service.py`,
  `audio_engine_service.py`, `workflow_artifacts.py`, `youtube_production_workflow.py`),
  plus `dependencies.py` wiring
- 226 backend tests passing (38 new), clean `py_compile`/`compileall`, DI verified live
  (`get_composition_planning_service()` resolves correctly; `get_video_assembly_service()`
  now resolves `CompositionAwareShotPlanner` as its default shot planner; workflow step
  order confirmed to include "Composition Planning" between "Scene Planning" and "Scene
  Image")
- Live end-to-end sanity check: an 8-scene `TimelinePlan` built from a 64-second
  narration produces genuinely variable per-scene durations (7.8s–10.15s, not a uniform
  8.0s), and both `CompositionAwareShotPlanner`'s `Shot`s and
  `DeterministicAudioTimelinePlanner`'s `scene_transitions` derive identical scene
  boundaries from that one `TimelinePlan` — confirming it is the actual single source
  of truth for timing, not just a schema that exists unused

**System State:**
- F27 fully implemented and validated at the code/test level
- Real production visual+audio validation (an actual rendered run) intentionally
  deferred until after F28, bundled with F25/F26's deferred validation
- F28 (AI Director) is now the current active feature

### Recent Session (2026-07-21, continued) — F28 AI Director

**Completed:**
- ✅ F28 AI Director implemented while explicitly preserving F27's pipeline shape
  (Research → Script → ScenePlan → TimelinePlan → CompositionPlan → Shot →
  AudioTimeline → Renderer → Audio Mixer → Final Video) with no redesign — the AI
  Director becomes the single creative authority for `TimelinePlan`/`CompositionPlan`;
  every executor (`RendererPipeline`, `AudioMixerService`, `ImageGenerationProvider`,
  `VideoAssemblyService`) is unchanged
- New dedicated `AIDirectorProvider` abstraction (ABC) with `AgentRuntimeAIDirectorProvider`
  as its first concrete implementation, reusing the existing agent execution path
  (`ConversationEngine`/`AgentRuntime`/`AgentService` — the same plumbing
  `ScenePlanningService` already uses) resolved against the existing "Creation Agent"
  (no new agent/migration added)
- The AI Director reasons over the complete narration script plus per-scene breakdown
  and `StrategyPackage` context in **one** structured-output call per production
  (never per scene, never twice), producing `AIDirectorPlan` — reusing
  `TimelinePlan`'s/`CompositionPlan`'s own enums/schemas directly, no duplicate type
  system and no heuristic reconstruction from free text
- `ai_director_plan_builder.py` validates/normalizes the AI's output into the real
  `TimelinePlan`/`CompositionPlan`: rejects on scene-coverage mismatches or
  non-positive durations (triggering fallback), rescales relative durations to the
  exact measured narration total (preserving the AI's pacing decisions, never
  overriding them), and drops (rather than hard-failing on) any single
  relationship/motif referencing an invalid scene number — this is
  `CompositionPlanner`'s new role when the AI Director is active: validation and
  normalization, not creative decision-making. `DeterministicTimelinePlanner`/
  `DeterministicCompositionPlanner` remain completely unchanged as the automatic
  fallback whenever the AI Director is unavailable, disabled, or fails validation
- `CompositionPlanningService.execute()` is now `async` and tries the AI Director
  exactly once, falling back wholesale (never a partial AI/deterministic mix) on any
  `AIDirectorError`

**Key Metrics:**
- 3 new backend files (`schemas/ai_director.py`, `services/ai_director_provider.py`,
  `services/ai_director_plan_builder.py`) and 3 new test files; 3 existing files
  extended (`composition_planning_service.py` made async + AI-Director-aware,
  `youtube_production_workflow.py`, `dependencies.py`), plus two new `Settings` fields
  (`ai_director_enabled: bool = True`, `ai_director_genre: str = "documentary"`)
- 249 backend tests passing (23 new), clean `py_compile`/`compileall` across the whole
  backend, dependency injection verified live (`get_ai_director_provider()` resolves
  `AgentRuntimeAIDirectorProvider`; `get_composition_planning_service()` resolves it as
  a dependency; workflow step order unchanged from F27)
- Live end-to-end verification in this environment (no configured agent database): the
  AI Director call correctly fails to resolve an agent, logs
  `ai_director_fallback_to_deterministic_planning`, and the pipeline still produces a
  complete, valid `TimelinePlan`/`CompositionPlan` — confirming the "the production
  pipeline must always remain operational" requirement live, not just in unit tests
- A second live check simulated an AI Director response with dramatically uneven
  relative scene durations (a 22s reveal vs. a 5.5s establishing beat on a 50s
  narration) and confirmed `TimelinePlan` still ends up the single source of truth:
  `CompositionAwareShotPlanner`'s `Shot`s and `DeterministicAudioTimelinePlanner`'s
  `scene_transitions` derive identical scene boundaries from it, with the video total
  summing exactly to the real narration duration

**System State:**
- F28 fully implemented and validated at the code/test level; the production
  architecture (TimelinePlan → CompositionPlan → Shot/AudioTimeline → Renderer/Audio
  Mixer) is now considered complete, per this feature's own charter
- Real production visual+audio validation (an actual rendered run, with a real seeded
  director agent) remains deferred, to bundle with F29's improvements
- F28A (Render Profiles) is now the current active feature

### Recent Session (2026-07-21, continued) — F28A Render Profiles

**Completed:**
- ✅ F28A implemented as a pure technical/export-layer feature — no planning, AI,
  or image-generation logic touched, per its own charter. Preserves the F27/F28
  pipeline exactly
- New strongly typed `RenderProfile` (Pydantic, `validate_assignment=True`):
  resolution, aspect ratio, frame rate, video/audio codec, audio sample rate,
  bitrate strategy (CRF/CBR/VBR), container, color space, pixel format, encoder
  preset, target platform — with a `model_validator` rejecting invalid
  combinations (mismatched aspect ratio/resolution, unsupported sample rate,
  missing crf/bitrate for the chosen strategy) at construction and on any later
  mutation
- One production-ready default profile ships: **YouTube Long** (1920×1080, 16:9,
  30fps, H.264/AAC, 48kHz, MP4, CRF 18 + "medium" preset). `RenderProfileRegistry`
  is the single place future platforms get added — one new `RenderProfile`
  registration, never a Renderer change
- Found and eliminated the actual duplication this feature targets:
  `cinematic_renderer_pipeline.py` and `video_assembly_service.py`'s legacy
  slideshow fallback each independently hardcoded `libx264`/`yuv420p`/`aac` and a
  bare `_FPS = 24` constant; `audio_mixer_service.py` independently hardcoded
  `aac` for the mixed track. All three now consume the same `RenderProfile`
  instance through one shared `render_profile_encoders.py` codec-mapping module
- Minimal integration exactly as scoped: `RendererPipeline`, `VideoAssemblyService`,
  and `AudioMixerService` each gained one additive, optional `render_profile`
  constructor parameter, defaulting via `RenderProfileRegistry` to "YouTube Long"
  when omitted — zero changes to AI Director, TimelinePlan, CompositionPlan,
  Shot, AudioTimeline, or ImageGenerationProvider
- Removed `Settings.cinematic_output_resolution` (now fully superseded and,
  if left in place, would have become a second, conflicting source of truth for
  resolution — exactly what the brief says must not exist); added
  `Settings.render_profile_name: str = "youtube_long"` as the single selector

**Key Metrics:**
- 3 new backend files (`schemas/render_profile.py`,
  `services/render_profile_encoders.py`, `services/render_profile_registry.py`)
  and 3 new test files; 5 existing files extended
  (`cinematic_renderer_pipeline.py`, `video_assembly_service.py`,
  `audio_mixer_service.py`, `config.py`, `dependencies.py`)
- 280 backend tests passing (31 new), clean `py_compile`/`compileall` across the
  whole backend, dependency injection verified live
  (`get_render_profile_registry()` resolves correctly; `VideoAssemblyService` and
  `AudioMixerService` both resolve to the same shared "youtube_long"
  `RenderProfile` instance)
- Live end-to-end verification: an unmodified `VideoAssemblyService.execute()`
  call — no `render_profile` argument, exactly how every existing caller already
  invokes it — automatically produced the correct default-profile ffmpeg args
  (`libx264`, `-preset medium`, `-crf 18`, `yuv420p`, `bt709`, `30fps`,
  `aac`/`48000`Hz, `mp4`), confirming backward compatibility live, not just in
  unit tests. A second live check with a completely different custom profile
  (HEVC, 4K, 60fps, CBR bitrate, `bt2020`/10-bit color, `.mov` container)
  confirmed every value propagated through with nothing hardcoded

**System State:**
- F28A fully implemented and validated at the code/test level
- F29 (Viewer Retention Engine) is now the current active feature

### Recent Session (2026-07-21, continued) — F28B Adaptive Visual Storytelling Engine

**Completed:**
- ✅ F28B implemented on the existing F27/F28 seam — no new planner abstraction:
  `VisualBeat` (`backend/schemas/composition.py`) added as an additive field on
  `SceneComposition`/`AIDirectorSceneDirection`, describing one meaningful visual
  event inside a scene. Empty (the default) means exactly the one image every
  scene has always produced — pre-F28B productions are unaffected
- AI Director made **Production Budget Aware**: `AIDirectorRequest` gained
  maximum/target production budget, estimated cost already consumed, remaining
  budget, and estimated per-image cost, plus configured minimum/target/maximum
  visual-beat-per-scene guidance — all sourced from new `Settings` fields
  (`maximum_video_budget_usd`, `target_video_budget_usd`,
  `maximum_image_budget_usd`, `target_image_budget_usd`,
  `minimum_visual_beats_per_scene`, `target_visual_beats_per_scene`,
  `maximum_visual_beats_per_scene`), never invented by the model
- **Cost so far** flows from a new generic `WorkflowRunContext.cost_ledger`,
  populated by `WorkflowEngine` directly from each step's existing
  `__meta__/<name>.json` metrics artifact — zero changes needed to any of the
  9+ steps that already report cost that way
- **Cost Validation** added to `ai_director_plan_builder.py` (extended, not a
  new file's worth of new architecture): `clamp_visual_beats_per_scene()` (hard
  per-scene ceiling) and `enforce_visual_beat_budget()` (trims from the
  largest scene first, never below one image per scene) run after the AI
  Director responds, inside `CompositionPlanningService`
- `CompositionPromptEnricher` expands one `ScenePrompt` into one per visual
  beat; `SceneImageGenerationService` needed no core loop change (a beat is
  just another prompt) — only unique per-beat filenames and a safety-net
  ceiling scaled by `maximum_visual_beats_per_scene`. Return type changed from
  `dict[int, bytes]` (scene_number, no longer unique once beats exist) to
  `dict[str, bytes]` (filename, always unique) — threaded through
  `VideoAssemblyService` and both workflow steps
- `CompositionAwareShotPlanner` now emits one `Shot` per beat, splitting the
  scene's `TimelinePlan`-fixed duration evenly across its beats — verified via
  `cinematic_renderer_pipeline.py` that shots/images are matched purely by list
  position (`zip`), never by `scene_number` lookup, so beats safely sharing one
  `scene_number` cannot cause a mismatch

**Key Metrics:**
- 2 new fields added to 2 existing schema files (`composition.py`,
  `ai_director.py`), 1 new field on `WorkflowRunContext`; 8 existing service
  files extended (`ai_director_provider.py`, `ai_director_plan_builder.py`,
  `composition_planning_service.py`, `composition_prompt_enricher.py`,
  `scene_image_generation_service.py`, `video_assembly_service.py`,
  `composition_aware_shot_planner.py`, `youtube_production_workflow.py`), plus
  `config.py` and `workflow_engine.py`/`workflow_engine_models.py`
- 302 backend tests passing (22 new), clean `py_compile`/`compileall` across
  the whole backend
- No DI/dependencies.py changes required — `CompositionPlanningService`'s new
  `CostTracker` dependency defaults exactly like `AgentRuntimeAIDirectorProvider`'s
  own optional pattern

**System State:**
- F28B fully implemented and validated at the code/test level; fully backward
  compatible — the deterministic F27 fallback planners never populate
  `visual_beats`, so Scene → One Image holds exactly as before whenever the AI
  Director is unavailable or disabled
- Real production validation (an actual rendered run with multiple visual
  beats per scene) remains deferred, consistent with F25–F28A's own deferred
  live-rendering validation
- F29 (Viewer Retention Engine) remains the current active feature

---

## Latest Validation

**Date:** 2026-07-21 — Post-F28A Render Profiles

- ✅ 280 backend tests passing (full suite, including 3 new F28A test files:
  RenderProfile schema validation, codec/bitrate encoder mapping, profile
  registry, plus profile-driven-args coverage added to the existing
  renderer/video-assembly/audio-mixer test files)
- ✅ Clean `py_compile`/`compileall` across all new/modified backend files
- ✅ Dependency injection validated live — `get_render_profile_registry()`
  resolves a shared `RenderProfileRegistry`; `get_video_assembly_service()` and
  `get_audio_engine_service()`'s mixer both resolve to the same "youtube_long"
  `RenderProfile` instance; workflow step order and every planning/AI component
  completely unchanged from F28
- ✅ Default profile selection confirmed live: constructing
  `VideoAssemblyService`/`RendererPipeline`/`AudioMixerService` with no
  `render_profile` argument at all automatically resolves "YouTube Long"
  (1920×1080/16:9/30fps/H.264/AAC/48kHz/MP4/CRF 18) — the concrete mechanism
  behind "if no RenderProfile is specified, automatically select the default"
- ✅ Renderer output configuration confirmed live: a full (faked-subprocess)
  `VideoAssemblyService.execute()` run produced the exact expected ffmpeg
  compose args for the default profile, and a second run with a custom
  HEVC/4K/60fps/CBR/`bt2020`/`.mov` profile produced entirely different,
  correctly-propagated args — proving no technical value is hardcoded anywhere
  in the render/export path
- ✅ Backward compatibility confirmed: every existing caller of
  `RendererPipeline`/`VideoAssemblyService`/`AudioMixerService` (none of which
  pass `render_profile`) continues to work completely unchanged; the full
  280-test suite, including the untouched F25–F28 test files, passes with zero
  modifications required beyond the new profile-driven-args assertions added

**Date:** 2026-07-21 — Post-F28 AI Director

- ✅ 249 backend tests passing (full suite, including 3 new F28 test files: AI
  Director provider, AI Director plan builder, plus AI-Director-integration tests
  added to the composition planning service tests)
- ✅ Clean `py_compile`/`compileall` across all new/modified backend files
- ✅ Dependency injection validated live — `get_ai_director_provider()` resolves
  `AgentRuntimeAIDirectorProvider`; `get_composition_planning_service()` resolves it
  as an injected dependency; workflow step order unchanged from F27 (`Composition
  Planning` still sits between `Scene Planning` and `Scene Image`)
- ✅ AI Director integration confirmed live: with no agent database configured in
  this environment, the AI Director call fails to resolve an agent and
  `CompositionPlanningService` falls back to F27's deterministic planners
  automatically — the pipeline still produces a complete, valid plan, no exception
  propagates, confirming backward compatibility holds even with the AI Director
  fully wired in
- ✅ `TimelinePlan` confirmed to remain the single source of truth even when the AI
  Director is the producer: a live script fed a deliberately uneven AI-authored
  `AIDirectorPlan` (22s reveal vs. 5.5s establishing beat on a 50s narration) through
  `ai_director_plan_builder.py`, then through `CompositionAwareShotPlanner` and
  `DeterministicAudioTimelinePlanner` independently — both derived identical scene
  boundaries, and the video duration total matched the narration exactly (50.0s)
- ⏸️ Real production visual/audio validation (an actual rendered run, with a real
  seeded director agent) intentionally deferred until after F29, bundled with
  F25/F26's deferred validation, to avoid a separate round of generation costs

**Date:** 2026-07-21 — Post-F27 Smart Scene Composition

- ✅ 226 backend tests passing (full suite, including 5 new F27 test files: timeline
  planner, composition planner, composition prompt enricher, composition-aware shot
  planner, composition planning service, plus updated shot planner/audio timeline
  planner/video assembly/audio engine/workflow tests)
- ✅ Clean `py_compile`/`compileall` across all new/modified backend files
- ✅ Dependency injection validated live — `get_composition_planning_service()`
  resolves correctly from the existing `Settings`; `get_video_assembly_service()`'s
  `_shot_planner` resolves to `CompositionAwareShotPlanner`; `get_audio_engine_service()`
  unchanged; `get_youtube_production_workflow_definition()` confirms "Composition
  Planning" is present between "Scene Planning" and "Scene Image"
- ✅ `TimelinePlan` confirmed live as the single source of truth for timing: a live
  script constructed an 8-scene `TimelinePlan` from a 64s narration, fed it through
  `CompositionAwareShotPlanner` and `DeterministicAudioTimelinePlanner` independently,
  and confirmed both produced identical scene boundaries and a video-duration total
  matching the narration exactly (64.0s) — variable pacing (7.8s–10.15s per scene) with
  zero video/audio drift
- ⏸️ Real production visual/audio validation (an actual rendered run through the live
  pipeline) intentionally deferred until after F28, bundled with F25/F26's deferred
  validation, to avoid a separate round of generation costs

**Date:** 2026-07-21 — Post-F26 Audio Engine

- ✅ 188 backend tests passing (full suite, including 8 new F26 test files: voice
  profiles, voice direction planner, narration processing, local audio library
  provider, audio timeline planner, audio mixer, audio engine service, plus updated
  voice generation/TTS provider/workflow tests)
- ✅ Clean `py_compile`/`compileall` across all new/modified backend files
- ✅ Dependency injection validated live — `get_audio_engine_service()`,
  `get_voice_generation_service()`, and `get_youtube_production_workflow_definition()`
  all resolve correctly from the existing `Settings`; workflow step order confirmed to
  include the new "Audio Mix" step between "Subtitle" and "Video Assembly"
- ⏸️ Real production audio validation (an actual generated run through the live
  pipeline) intentionally deferred until after F27, bundled with F25's deferred visual
  validation, to avoid a separate round of generation costs

**Date:** 2026-07-21 — Post-F25 Cinematic Video Engine

- ✅ 152 backend tests passing (full suite, including 6 new cinematic-module test files)
- ✅ Clean `py_compile`/`compileall` across all new/modified backend files
- ✅ Dependency injection validated live — `get_video_assembly_service()` resolves
  `DeterministicShotPlanner`/`RendererPipeline` correctly from the existing `Settings`
- ⏸️ Real production visual validation (an actual rendered run through the live pipeline)
  intentionally deferred until after F26/F27, to avoid unnecessary generation costs

**Date:** 2026-07-21 — Post-F24 first real production run

- ✅ Full 10-stage pipeline executed end-to-end against live providers (research → strategy
  → script → review → scene planning → scene images → thumbnail → narration → subtitles →
  final MP4)
- ✅ Canonical `manifest.json` produced by the `WorkflowArtifactManifest` step
- ✅ Brave Search confirmed working as the search provider (replaces DuckDuckGo)
- ✅ OpenAI quota issue confirmed resolved for a real run
- ✅ Total production cost measured at ≈ $0.85/video
- **Pipeline is now considered functionally validated.**

**Date:** 2026-07-19 — Post-F17F runtime verification

- ✅ Backend starts successfully
- ✅ Frontend works
- ✅ General Assistant responds successfully
- ✅ Responses API confirmed operational (`responses.create()` live at
  `backend/core/openai_llm_provider.py:143,192`; no `chat.completions.create()` remaining
  in production code)
- ✅ No production path exists to `gpt-3.5-turbo` (effective default model verified live as
  `gpt-5.5`, sourced from `backend/core/config.py`, no `.env` override)

---

## Next Steps

### Immediate (Next Session)

1. **F30 — Production Quality Validation**: audit the entire F25–F29 stack in one bundled
   real-production run — F25's cinematic renderer, F26's audio engine, F27's scene
   composition, F28's AI Director (with a real seeded director agent), F28A's default
   render profile, and F29's Viewer Retention Engine (importance-weighted beat durations,
   retention-aware transitions) — comparing expected architecture vs actual generated
   output, removing remaining quality bottlenecks, and producing the Production Quality
   Report that gates the rest of Phase 2 (F31–F34)
2. **Address remaining F17A findings not in F17B's approved scope** if they block the
   above (see docs/DECISIONS.md and PROJECT_RULES.md workflow for re-approval)
3. **Populate a real music/SFX asset library** (or wire a generative provider) and flip
   `background_music_enabled`/`sound_effects_enabled` on, once F26's local-library
   interfaces have a real library to point at
4. **Register additional RenderProfiles as real platform needs arise** (YouTube Shorts,
   TikTok, Instagram Reels, YouTube 4K, ...) — each is a `RenderProfileRegistry.register()`
   call, no Renderer change, per F28A's design

### Strategic

1. **F25–F29 (video quality architecture) are fully implemented** — Cinematic Rendering
   (✅ F25) → Audio Engine (✅ F26) → Smart Scene Composition (✅ F27) → AI Director
   (✅ F28) → Render Profiles (✅ F28A) → Adaptive Visual Storytelling (✅ F28B) →
   Viewer Retention Engine (✅ F29)
2. **Phase 2 — Production Quality now governs all upcoming work**: F30 (Production
   Quality Validation) → F31 (Photorealistic Visual Engine) → F32 (Cinematic Camera
   Language) → F33 (Premium Audio Experience) → F34 (Production Polish)
3. **F35 — Automated Publishing** — deliberately deferred; picked up only once Phase 2
   confirms the videos are visually and audibly competitive with successful YouTube
   documentary channels, at approximately $5/video or less
4. **Continue platform maturation** in parallel where it doesn't compete with quality work
5. **Iterate based on feedback** — review each generated video against the previous one to
   guide which Phase 2 feature to prioritize next

---

## File Locations & Key References

### Backend Core
- `backend/main.py` — FastAPI entrypoint
- `backend/services/` — Business logic layer
- `backend/repositories/` — Data access layer
- `backend/schemas/` — Pydantic request/response models
- `backend/api/v1/` — REST API endpoints

### Frontend Core
- `app/` — Next.js app directory with routes
- `src/components/` — Reusable UI components
- `src/hooks/` — Custom React hooks (data fetching, state)
- `src/services/` — API client services
- `src/store/` — Zustand global state (minimal usage)

### Documentation
- `AGENTS.md` — AI agent customization rules
- `CLAUDE.md` — Claude Code role and guidelines
- `docs/architecture/ARCHITECTURE.md` — Detailed architecture decisions
- `docs/standards/DEV_STANDARDS.md` — Coding standards
- `docs/standards/AI_RULES.md` — AI-specific development rules
- `F11_IMPLEMENTATION_SUMMARY.md` — Latest feature implementation details
- `PROJECT_STATE.md` — **THIS FILE** — Single source of truth

---

## Contact & Escalation

For questions on:
- **Architecture decisions** → Refer to AGENTS.md, docs/architecture/
- **Feature status** → Check individual F##_IMPLEMENTATION_SUMMARY.md files
- **Development standards** → See docs/standards/
- **Project direction** → This file (PROJECT_STATE.md) is the source of truth

---

**Last Updated:** 2026-07-22  
**Last Feature:** F31.5 (Production Hardening Sprint — async production execution via the
existing `BackgroundTaskManager`, real runtime budget enforcement aggregating every cost
source including image validation and regeneration, character reference portrait
validation with rejection of still-invalid portraits, and an opt-in live OpenAI smoke
test covering the two F31 assumptions no fake-based test could verify; closes all four
Critical findings from the F29–F31 architecture review; no architecture redesign, fully
backward compatible) — COMPLETE. **F30, F31, and F31.5 of the Phase 2 — Production
Quality roadmap are now implemented.**  
**Next Feature:** **F32 — Cinematic Camera Language** (scene-aware camera movement, more
natural motion, less repetitive zooming, improved transitions, stronger visual
storytelling — the F30 report's remaining camera/rendering findings), followed by F33
(Premium Audio Experience) and F34 (Production Polish), then F35 — Automated Publishing
(deferred until Phase 2 confirms the production-quality bar is met) — NOT STARTED
