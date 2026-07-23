# F27 — Smart Scene Composition: Architecture Proposal

**Status: APPROVED and IMPLEMENTED**, with one architectural revision requested at
approval time: a new `TimelinePlan` abstraction (§9) was inserted as the single
source of truth for scene timing, between Scene Planning and Composition Planning.
The original proposal (§1–§8 below) let `CompositionPlanner` compute its own
per-scene durations; the revision moves all timing computation into `TimelinePlan`/
`TimelinePlanner`, and `CompositionPlan` now only *carries* (never calculates) the
timing values it consumes from `TimelinePlan`. See §9 for the as-built design.

---

## 1. Current Architecture (read from code, not assumed)

```
Reviewed Script (ReviewedScript.revised_script)
        ↓
ScenePlanningService.execute()          backend/services/scene_planning_service.py
   ONE LLM call → strict JSON, exactly `max_scenes_per_video` scenes
        ↓
ScenePlan (list[Scene])  +  ScenePromptSet (list[ScenePrompt])
   Scene: camera, lens, lighting, environment, animation, composition, visual_prompt
   ScenePrompt: prompt, negative_prompt, style, aspect_ratio, camera, mood
        ↓
SceneImageGenerationService.execute()   backend/services/scene_image_generation_service.py
   one gpt-image-1 call per ScenePrompt.prompt, independently, in isolation
        ↓
SceneImageSet (per-scene PNG bytes)
        ↓
VideoAssemblyService._assemble_cinematic()   backend/services/video_assembly_service.py:127-151
   scene_seconds = voice_asset.duration / len(images)          ← ONE uniform value
        ↓
DeterministicShotPlanner.plan()         backend/services/cinematic_shot_planner.py:88-133
   keyword-matches Scene.camera/animation text → CameraMovementType
   keyword-matches Scene.composition text      → ShotType
   no match → fixed round-robin rotation (index % len(rotation))
   duration_seconds = scene_seconds for EVERY scene (uniform, passed in from above)
   transition / atmosphere / color_profile = one Settings value for the WHOLE VIDEO
        ↓
list[Shot]                              backend/schemas/shots.py
        ↓
RendererPipeline.render()               backend/services/cinematic_renderer_pipeline.py
   executes Shots exactly as given — camera movement filter, atmosphere overlay,
   color grade, transition chain (build_transition_chain)
        ↓
AudioEngineStep → AudioTimelinePlanner  backend/services/audio_timeline_planner.py:39-88
   scene_transitions: at_seconds = ((scene_number-1) / scene_count) * total   ← ALSO
   a uniform proportional split, computed independently from Shot.duration_seconds
   but arriving at the same number today only because both divide uniformly
        ↓
AudioMixerService → mixed track
        ↓
VideoAssemblyService mux → Final MP4
```

Key facts, verified in code:

- **One LLM call produces every scene at once, with no cross-scene instruction.**
  The prompt in `ScenePlanningService.execute()` (`scene_planning_service.py:85-99`)
  asks for "EXACTLY `{max_scenes}` scenes" as independent JSON objects. Nothing in
  the prompt asks the model to relate one scene to another, assign a narrative
  role, or track a recurring motif. Each `Scene`/`ScenePrompt` is generated as an
  isolated unit; scene 1 and scene 7 are exchangeable from the LLM's point of view.
- **Every scene gets identical screen time.** `scene_seconds = voice_asset.duration
  / len(images)` (`video_assembly_service.py:63-67`) is a single float, reused
  unchanged for every `Shot.duration_seconds` (`cinematic_shot_planner.py:128`).
  There is no fast/slow/breathing/climax distinction anywhere in the pipeline —
  "pacing" as a concept does not exist yet.
- **Shot selection is either a keyword accident or a fixed rotation, never a
  narrative decision.** `DeterministicShotPlanner` (`cinematic_shot_planner.py:61-74`)
  matches free-text substrings like "zoom out" or "close-up" if the LLM happened to
  write them into `camera`/`animation`/`composition`; otherwise it falls back to
  `index % len(_MOVEMENT_ROTATION)` — literally scene index modulo a fixed list.
  Two videos with different topics but the same scene count get the *exact same*
  camera-movement sequence. There is no concept of "this is the reveal scene, so
  push in slowly" anywhere in this code path.
- **Transition, atmosphere, and color grade are one global choice for the entire
  video**, read once from `Settings` (`cinematic_shot_planner.py:99-104`) and
  applied to every `Shot`. There is no per-scene variation, and therefore no way to
  express contrast, escalation, or a callback through visual language — the single
  existing color preset (`_PROFILES["documentary"]`, `cinematic_color_processing.py:8-9`)
  is also literally the only option, so `Shot.color_profile` is a real seam with
  nothing behind it yet.
- **Image generation has zero continuity mechanism.** `SceneImageGenerationService`
  (`scene_image_generation_service.py:101-114`) calls `OpenAIImageGenerationProvider`
  once per scene with that scene's `prompt` string only. No shared style anchor, no
  reference to a previous scene's palette/location/object, no instruction to keep a
  visual element consistent. Every image is generated as if it were the only image
  in the video.
- **Video and audio scene-timing are only consistent by coincidence.** The video
  side derives `Shot.duration_seconds` from `scene_seconds` (uniform division);
  the audio side derives `SceneTransitionMarker.at_seconds` from the same uniform
  proportional split, but through an *entirely separate calculation*
  (`audio_timeline_planner.py:69-77`) that has no reference to `Shot` at all. They
  agree today purely because both assume "every scene is the same length." The
  moment either side introduces variable per-scene pacing without a shared source
  of truth, video and audio scene boundaries will silently drift apart.
- **`Scene`/`ScenePlan` already carry rich per-scene free text** (`camera`, `lens`,
  `lighting`, `environment`, `animation`, `composition` — `backend/schemas/assets.py:127-140`)
  that is *never read* by anything except `DeterministicShotPlanner`'s keyword
  matcher, and never used to inform continuity, purpose, or pacing. This is
  under-used raw material, not a gap that needs new data collection.
- **The `Shot` / `AudioTimeline` contract-planner-executor pattern (F25/F26) already
  proves out exactly the shape F27 needs.** `ShotPlanner` and `AudioTimelinePlanner`
  are both `ABC`s with one deterministic implementation each, both explicitly
  reserving room for an F28 AI Director implementation with **zero changes** to
  `RendererPipeline`/`AudioMixerService`. F27 should be the same shape one layer up.

### Where scene quality is actually lost (root causes, not symptoms)

1. **No narrative role per scene** → every scene is directed identically regardless
   of whether it should introduce, escalate, or resolve. This is the direct cause of
   "the viewer feels like they're watching unrelated AI images."
2. **No cross-scene memory** → nothing carries a color, object, or location forward,
   so there is no visual thread for the viewer to follow.
3. **No pacing model** → uniform duration for every scene structurally prevents
   rhythm; a reveal and a transition beat currently hold the screen for exactly the
   same number of seconds.
4. **Shot/atmosphere/transition decisions are accidental** (keyword luck) or
   **mechanical** (rotation), never intentional. The "WHY" the brief asks for does
   not exist as a concept anywhere in the current code.
5. **Video and audio have no shared timing authority** — a latent bug waiting for
   the first variable-pacing feature (i.e., this one) to expose it.

None of this is a defect in F25/F26 — both are executors that faithfully render
whatever they're handed. The gap is that **nothing upstream of them has ever made a
directorial decision.** That missing layer is `CompositionPlan`.

---

## 2. Recommended Architecture

```
Research → Script → Reviewer → ScenePlanningService (unchanged)
                                        ↓
                            ScenePlan + ScenePromptSet (unchanged output)
                                        ↓
                            ┌───────────────────────────┐
                            │   CompositionPlanner      │  NEW
                            │  (deterministic today)    │
                            └───────────────────────────┘
                                        ↓
                                 CompositionPlan            ← NEW, the missing layer
                                        ↓
                    ┌───────────────────┼───────────────────┐
                    ↓                   ↓                   ↓
     CompositionPromptEnricher   CompositionAwareShotPlanner   (reserved: pacing/purpose
     (NEW, deterministic,         (NEW ShotPlanner impl,         hook for VoiceDirection/
      string templating only)      replaces DeterministicShotPlanner   AudioTimeline —
                    ↓               as the default wiring)          NOT wired in F27)
        enriched ScenePromptSet            ↓
                    ↓                    list[Shot]              (unchanged type)
     SceneImageGenerationService          ↓
        (UNCHANGED)                RendererPipeline (UNCHANGED)
                    ↓                     ↓
              scene images  ─────────────→│
                                    F26 Audio Engine (UNCHANGED for F27)
                                          ↓
                                    Final Video
```

`CompositionPlan` becomes the audio-equivalent-of-`Shot`'s *visual counterpart one
level up*: it sits between Scene Planning and Shot creation exactly as the brief
specifies, is produced by a planner, and is consumed by two executors that already
exist in spirit (`ShotPlanner`) or are string-templating utilities (the prompt
enricher) — no existing executor (`RendererPipeline`, `AudioMixerService`,
`ImageGenerationProvider`) changes its own decision-making.

### What must remain unchanged

- `ImageGenerationProvider` / `OpenAIImageGenerationProvider` — untouched, per the
  brief. `CompositionPlan` only changes what text is sent to it.
- `RendererPipeline` — untouched. It already only executes `Shot`; `CompositionPlan`
  produces `Shot`s through a new `ShotPlanner` implementation, not a renderer change.
- `AudioMixerService` — untouched in F27. `CompositionPlan` is designed so its
  pacing/purpose fields *can* feed `VoiceDirectionPlanner`/`AudioTimelinePlanner`
  later (same `scene_number` key as `Shot`), but wiring that is explicitly deferred
  to keep F27's scope to its stated goal (scene composition, not audio pacing).
- `Shot` and `AudioTimeline` schemas — untouched. `CompositionPlan` is a new,
  separate contract, not a rewrite of either.
- `ScenePlanningService`'s one LLM call — reused as `CompositionPlanner`'s input,
  not duplicated (see §4 cost discussion — this is the same discipline F26 applied
  to `MusicPlan`/`BrollPlan`).

---

## 3. CompositionPlan Design

### 3.1 Vocabulary (the reusable concepts the brief asks for)

```python
# backend/schemas/composition.py (proposed)

class ScenePurpose(str, Enum):
    """The narrative role a scene plays. Deliberately generic — no mystery-specific
    or genre-specific values. New roles are new enum members; nothing else changes."""
    INTRODUCTION = "introduction"
    CONTEXT = "context"
    DISCOVERY = "discovery"
    CONFLICT = "conflict"
    ESCALATION = "escalation"
    REVEAL = "reveal"
    RESOLUTION = "resolution"


class CompositionStyle(str, Enum):
    """Reusable framing/coverage concept — independent of, but mapped onto, Shot.ShotType."""
    ESTABLISHING_SHOT = "establishing_shot"
    WIDE_SHOT = "wide_shot"
    CLOSE_UP = "close_up"
    DETAIL_SHOT = "detail_shot"
    REVEAL_SHOT = "reveal_shot"
    COMPARISON_SHOT = "comparison_shot"
    REACTION_SHOT = "reaction_shot"
    TRANSITION_SHOT = "transition_shot"


class CameraIntent(str, Enum):
    """WHY the camera moves — F25 already decides HOW (CameraMovementType); this is
    the missing WHY layer the brief calls for. CompositionAwareShotPlanner maps
    CameraIntent → CameraMovementType; RendererPipeline never sees this enum."""
    SLOW_REVEAL = "slow_reveal"
    DRAMATIC_ZOOM = "dramatic_zoom"
    INVESTIGATION = "investigation"
    SUSPENSE = "suspense"
    EMOTIONAL_FOCUS = "emotional_focus"
    NEUTRAL_OBSERVATION = "neutral_observation"


class ScenePacing(str, Enum):
    """Rhythm category. Maps to a duration multiplier applied to the scene's
    proportional share of narration time — see §3.3."""
    FAST = "fast"
    SLOW = "slow"
    BREATHING = "breathing"
    DRAMATIC_PAUSE = "dramatic_pause"
    CLIMAX = "climax"
    STANDARD = "standard"


class SceneRelationType(str, Enum):
    """How a scene relates to an earlier scene it references."""
    CONTINUATION = "continuation"
    CONTRAST = "contrast"
    CALLBACK = "callback"
    ESCALATION = "escalation"
    REPETITION = "repetition"


class ColorLanguage(str, Enum):
    """Reserved emotional/temporal color intent. Resolves to Shot.color_profile;
    only one preset ("documentary") exists today (cinematic_color_processing.py),
    so every value below currently renders identically. The field is real, the
    palette behind it is future work — matches the brief's "do not implement
    advanced color grading today" constraint exactly."""
    NEUTRAL = "neutral"
    WARM_PROGRESSION = "warm_progression"
    COLD_PROGRESSION = "cold_progression"
    TENSION = "tension"
```

### 3.2 Relationships and continuity

```python
class SceneRelationship(BaseModel):
    """One directed link from this scene back to an earlier one."""
    relation_type: SceneRelationType
    reference_scene_number: int
    note: str = ""   # human-readable rationale, e.g. "same location as scene 2"


class ContinuityMotif(BaseModel):
    """One recurring visual thread. `established_scene_number` is where it first
    appears; `recurring_scene_numbers` are every later scene instructed to keep it
    visible. This is the concrete mechanism behind 'recurring colors/objects/
    locations/framing/atmosphere' from the brief."""
    motif_type: Literal["color", "object", "location", "framing", "atmosphere"]
    description: str                       # e.g. "the locked attic door"
    established_scene_number: int
    recurring_scene_numbers: list[int] = Field(default_factory=list)
```

### 3.3 Per-scene composition + the plan itself

```python
class SceneComposition(BaseModel):
    """Everything CompositionPlanner decided for one scene. Keyed by scene_number —
    the same key Shot and AudioTimeline's scene-linked entries already use."""
    scene_number: int
    purpose: ScenePurpose
    composition_style: CompositionStyle
    camera_intent: CameraIntent
    pacing: ScenePacing
    duration_seconds: float = 0.0          # authoritative — see §5.3 sync note
    color_language: ColorLanguage = ColorLanguage.NEUTRAL
    relationships: list[SceneRelationship] = Field(default_factory=list)
    continuity_tags: list[str] = Field(default_factory=list)   # motif descriptions active in this scene
    emphasis_note: str = ""                 # short human-readable directorial rationale


class CompositionPlan(BaseModel):
    """The data contract between scene-level planning ('what is this video's visual
    story') and shot/prompt production ('render/prompt for that'). This is Shot's
    and AudioTimeline's sibling one layer up: CompositionPlanner resolves it
    deterministically today; F28's AI Director is expected to produce
    CompositionPlans directly later — CompositionAwareShotPlanner and the prompt
    enricher execute whatever plan they're given and never invent a directorial
    decision themselves, matching RendererPipeline's and AudioMixerService's
    discipline exactly."""
    topic: str
    scenes: list[SceneComposition] = Field(default_factory=list)
    motifs: list[ContinuityMotif] = Field(default_factory=list)
    metadata: dict[str, object] = Field(default_factory=dict)   # status, provider_metrics, cost_estimate — matches every other *Plan
```

---

## 4. CompositionPlanner

```python
class CompositionPlanner(ABC):
    """Resolves a ScenePlan into a CompositionPlan — the single seam between scene
    planning and shot/prompt production. F28 (AI Director) is expected to add an
    LLM-driven implementation later; downstream consumers only ever read
    CompositionPlan, so they need no changes when that happens."""

    @abstractmethod
    def plan(self, *, scene_plan: ScenePlan, scene_seconds_total: float) -> CompositionPlan: ...
```

### 4.1 `DeterministicCompositionPlanner` (F27 implementation — zero added cost)

Pure position/heuristic logic over data that already exists in `Scene`/`ScenePlan` —
no LLM call, mirroring `DeterministicShotPlanner`'s discipline exactly:

- **Purpose by position**: scene 1 → `INTRODUCTION`; last scene → `RESOLUTION`;
  remaining scenes distributed across `CONTEXT → DISCOVERY → CONFLICT → ESCALATION
  → REVEAL` proportionally by index (a fixed narrative-arc curve, the same
  round-robin-with-intent idea `_MOVEMENT_ROTATION` already uses, just mapped to a
  dramatic arc instead of an arbitrary list).
- **Composition style / camera intent from purpose**: a fixed lookup table (e.g.
  `INTRODUCTION → ESTABLISHING_SHOT / NEUTRAL_OBSERVATION`, `REVEAL →
  REVEAL_SHOT / SLOW_REVEAL`, `CONFLICT → CLOSE_UP / SUSPENSE`) — deterministic,
  same pattern as `_SHOT_TYPE_ROTATION`.
- **Pacing from purpose**: `REVEAL`/`CLIMAX`-adjacent purposes get `SLOW` or
  `DRAMATIC_PAUSE`; `CONTEXT`/transition-ish scenes get `FAST` or `BREATHING`;
  everything else `STANDARD`. Each pacing category maps to a duration multiplier
  (e.g. `SLOW=1.3`, `FAST=0.75`, `STANDARD=1.0`), then **normalized so the sum of
  all scene durations still equals the real measured narration duration** — this
  is the one new piece of real logic, and it is what finally gives the video
  rhythm instead of uniform timing, entirely deterministically.
- **Continuity motifs via keyword repetition**: extract simple repeated noun
  phrases from `Scene.narration`/`Scene.environment` (case-insensitive, stopword
  filtered) across scenes; any phrase appearing in 2+ scenes becomes a
  `ContinuityMotif` with `motif_type="object"` or `"location"` (heuristically, by
  matching against `Scene.environment` vs. narration body); the first occurrence
  is `established_scene_number`, later ones are `recurring_scene_numbers`. Cheap
  string processing, no added cost.
- **Relationships**: a scene whose motif list overlaps a non-adjacent earlier
  scene's motif list gets a `CALLBACK` relationship to it; an escalation-purpose
  scene immediately following a conflict-purpose scene gets an `ESCALATION`
  relationship to it; consecutive same-purpose scenes get `CONTINUATION`. All
  derived from data already computed above — no new inputs required.
- **Color language from purpose**: `CONFLICT`/`ESCALATION` → `TENSION`,
  `RESOLUTION` → `WARM_PROGRESSION`, everything before the midpoint →
  `COLD_PROGRESSION` (or `NEUTRAL` if the brief prefers to ship inert first) — a
  reserved field per §3.1, harmless today since only one color preset exists.

**Cost: $0. Zero LLM calls, zero added latency of consequence** (pure Python over
data already in memory). This is the tier that should ship with F27.

### 4.2 Optional Tier 2 — LLM-assisted composition (explicitly NOT built now)

The brief requires evaluating additional AI reasoning honestly rather than
defaulting to "add a call." The only version worth ever considering is: **extend
the existing single `ScenePlanningService` LLM call's requested JSON schema** to
also ask for `purpose`, `relationship_to_previous_scene`, and `recurring_motif`
per scene, instead of adding a second LLM call.

- **Expected quality improvement**: meaningful — an LLM reading the *whole* script
  at once can identify real thematic callbacks (e.g. "the same clue reappears in
  scene 8") that keyword-repetition heuristics will miss.
- **Expected cost increase**: near-zero. It is the same one call
  `ScenePlanningService` already makes (`_timed_execute`, `scene_planning_service.py:101`);
  only the requested output schema grows, meaning a marginally larger completion
  (a few hundred extra output tokens spread across one call) — sub-cent impact
  against the ~$0.85/video baseline.
- **Justification for NOT building it in F27**: it changes `ScenePlanningService`
  itself (a working, tested component) rather than adding a new layer beside it,
  and it makes `CompositionPlanner` depend on LLM output being well-formed for a
  feature whose entire pitch is "give the video rhythm and continuity
  deterministically, for free." Ship the deterministic tier first, validate it
  visually, and revisit this extension only if real output shows the heuristics
  under-detect motifs/relationships that matter. If adopted later, it is a
  **second `CompositionPlanner` implementation** reading the richer
  `ScenePlanningService` output — `DeterministicCompositionPlanner` remains the
  fallback exactly the way every other planner in this codebase has one.

---

## 5. Integration Points

### 5.1 Image Generation (prompt enrichment, not a redesign)

New, small service: `CompositionPromptEnricher` (deterministic string templating,
no provider call of its own):

```python
class CompositionPromptEnricher:
    def enrich(self, *, scene_prompts: ScenePromptSet, composition_plan: CompositionPlan) -> ScenePromptSet: ...
```

For each `ScenePrompt`, appends short, deterministic phrases derived from its
matching `SceneComposition` to the existing `prompt` string before
`SceneImageGenerationService` ever sees it — e.g. composition-style framing
language ("wide establishing composition, safe margins, no on-image text"), active
`continuity_tags` ("maintain the recurring dim amber lighting introduced
earlier"), and purpose-appropriate mood language. `SceneImageGenerationService`
and `ImageGenerationProvider` do not change at all — they still receive one
`ScenePrompt.prompt` string per scene, exactly as today. This directly satisfies
"do not redesign ImageGenerationService, instead improve the information provided
to it," and is also where F27's literal roadmap goal (no in-image text, safe
margins, cleaner composition, better framing) gets executed — as one motif/style
phrase source among several, not a separate mechanism.

This runs as a new, tiny step between `ScenePlanningStep` and `SceneImageStep` in
`youtube_production_workflow.py` (a `CompositionPlanningStep`) — it does not touch
either of those steps' internals.

### 5.2 F25 Cinematic Renderer

New `ShotPlanner` implementation, `CompositionAwareShotPlanner`, registered as the
default in place of `DeterministicShotPlanner` (both remain available; swapping
one deterministic planner for another is exactly the kind of change F25's ABC was
built to absorb with zero `RendererPipeline` changes):

- `composition_style` + `camera_intent` → `ShotType`/`CameraMovementType` via fixed
  lookup tables (e.g. `SLOW_REVEAL → PUSH_IN` with a longer `duration_seconds`,
  `SUSPENSE → HANDHELD`, `INVESTIGATION → PAN_LEFT`/`PAN_RIGHT` alternating).
- `SceneComposition.duration_seconds` (already normalized to sum to the real
  narration duration, §4.1) replaces the uniform `scene_seconds` value directly —
  this is the concrete fix for the "every scene holds the same amount of time"
  limitation identified in §1.
- `relationships`/`continuity_tags` inform `transition` (e.g. a `CONTRAST`
  relationship prefers `FADEBLACK` over `DISSOLVE`) and `atmosphere`/`color_profile`
  (recurring atmosphere motif → same `AtmosphereOverlayType` reused across its
  recurring scenes).
- `ShotPlanner.plan()`'s signature gains one additive optional parameter,
  `composition_plan: CompositionPlan | None = None` — backward compatible;
  `DeterministicShotPlanner` ignores it. `Shot` itself does not change shape.

**Implementation constraint this proposal surfaces (§1):** once per-scene duration
becomes variable, `VideoAssemblyService._assemble_cinematic`'s total-duration
formula (`scene_seconds * len(shots) - transition_seconds * (len(shots)-1)`,
`video_assembly_service.py:151`) must change to `sum(shot.duration_seconds for
shot in shots) - ...` instead of assuming a uniform `scene_seconds`. This is a
one-line, low-risk fix to flag for the implementation phase, not a redesign.

### 5.3 F26 Audio Engine

Not rewired in F27 — deliberately, to keep this feature's scope to composition.
But the design point that must be respected going forward:
**`SceneComposition.duration_seconds` is the single authoritative per-scene timing
source once F27 ships.** `AudioTimelinePlanner`'s `scene_transitions` calculation
(`audio_timeline_planner.py:69-77`, currently an independent uniform proportional
split) will silently disagree with the video's now-variable per-scene timing
unless a future change makes it consume the same `CompositionPlan`/`Shot` duration
values instead of recomputing its own split. This proposal does not fix that in
F27 (no `AudioTimelinePlanner` change is being made), but flags it explicitly so
it is not rediscovered as a confusing bug later — it is the direct, foreseeable
consequence of introducing variable scene pacing, and the fix is straightforward
once audio pacing is in scope (pass `CompositionPlan` in, key `scene_transitions`
off `SceneComposition.duration_seconds` instead of an even split).

`VoiceDirection`/`AudioTimeline` are still natural future consumers of
`SceneComposition.pacing`/`purpose` (e.g. a `DRAMATIC_PAUSE` scene could lengthen
`instructions`-driven TTS pause behavior, or add a `SceneTransitionMarker`-anchored
ducking dip) — reserved, not built, exactly per the brief.

---

## 6. Preparation for F28 (AI Director)

`CompositionPlan` is designed so F28 has one clean seam per concern, matching the
`Shot`/`AudioTimeline` precedent exactly:

- A future `LLMCompositionPlanner` (second `CompositionPlanner` implementation)
  produces richer `CompositionPlan`s directly from the LLM — same output type,
  `CompositionAwareShotPlanner`/`CompositionPromptEnricher` need no changes.
- `CompositionPlan`, `Shot`, and `AudioTimeline` are three sibling contracts, all
  keyed by `scene_number`. A single future AI Director call could emit all three
  from one script read, or `CompositionPlan` could be produced first and *inform*
  a later `Shot`/`AudioTimeline`-producing call — either sequencing works because
  none of the three schemas depends on another's internal shape, only on the
  shared `scene_number` key.
- `CameraIntent`, `ScenePacing`, `SceneRelationType`, and `ColorLanguage` are the
  exact vocabulary an LLM-driven director would need to emit — F28's job becomes
  "produce these enums well," not "invent a new schema."

---

## 7. Cost Summary

| Item | Today | Proposed (F27) | Delta |
|---|---|---|---|
| Scene Planning LLM call | 1 call (unchanged) | 1 call (unchanged) | $0 |
| CompositionPlanner (Tier 1, shipped) | — | pure Python, in-process | $0 |
| CompositionPromptEnricher | — | string templating, in-process | $0 |
| Scene Image generation | 1 gpt-image-1 call/scene | 1 gpt-image-1 call/scene (richer prompt text only) | $0 (prompt length has negligible effect on gpt-image-1 pricing) |
| Shot planning | keyword-match/rotation | composition-driven lookup, in-process | $0 |
| CompositionPlanner Tier 2 (optional, NOT built) | — | folds into existing Scene Planning call | ~sub-cent/video, deferred |

**Net expected cost increase for F27 as proposed: $0.** Every mechanism above is
deterministic logic over data already produced by an existing, already-paid-for
LLM call — consistent with "prefer deterministic logic whenever it provides
similar quality" and the Quality-First Development Principle's cost constraint.

---

## 8. Constraints Surfaced for the Implementation Phase (not actioned here)

1. `VideoAssemblyService`'s total-duration formula assumes uniform `scene_seconds`
   (§5.2) — must sum real per-shot durations once pacing varies.
2. `AudioTimelinePlanner.scene_transitions` computes its own independent uniform
   split (§5.3) — will drift from video timing the moment pacing varies; not fixed
   in F27, explicitly flagged for whenever audio pacing is tackled.
3. `ShotPlanner.plan()` needs one additive optional parameter
   (`composition_plan: CompositionPlan | None = None`) — non-breaking.
4. `Scene`/`ScenePlan` already contain everything `DeterministicCompositionPlanner`
   needs; no change to `ScenePlanningService`'s LLM prompt is required for Tier 1.

---

## 9. Revision: `TimelinePlan` — Single Source of Truth for Time (as approved and built)

The architecture review flagged §5.3/§8's own finding as unacceptable to ship as a
"known constraint for later": once F27 introduces variable per-scene pacing, video
(`Shot.duration_seconds`) and audio (`AudioTimeline.scene_transitions`) would each
compute their own independent timing split and could silently drift apart. The
approved fix is structural, not a patch: introduce **`TimelinePlan`** as a new
contract that sits between Scene Planning and Composition Planning, and make it the
**only** place scene ordering, duration, start/end time, and pacing are ever
computed. Everything downstream *consumes* time; nothing else calculates it.

```
Scene Planning → TimelinePlan → CompositionPlan → Shot
                       ↓                              ↑ (via CompositionPlan)
                       └──────────────→ AudioTimeline ─┘
```

### 10.1 Responsibility split (as built)

| Contract | Answers | Computes timing? |
|---|---|---|
| `TimelinePlan` | WHEN things happen (order, duration, start/end, pacing) | **Yes — the only one** |
| `CompositionPlan` | HOW the scene should look (purpose, framing, continuity, camera intent, color) | No — carries `TimelinePlan`'s values verbatim |
| `Shot` | HOW the renderer animates the scene | No — reads `CompositionPlan`'s carried timing |
| `AudioTimeline` | HOW audio evolves through time | No — reads `TimelinePlan` directly |

`RendererPipeline` and `AudioMixerService` are unchanged — both already only ever
executed the plan they were given; this revision only changes which planner
produces the timing values that eventually reach them.

### 10.2 `TimelinePlan` (new — `backend/schemas/timeline.py`)

```python
class ScenePacing(str, Enum):
    FAST = "fast"
    STANDARD = "standard"
    SLOW = "slow"
    DRAMATIC_PAUSE = "dramatic_pause"
    CLIMAX = "climax"
    BREATHING = "breathing"


class SceneTiming(BaseModel):
    """One scene's authoritative position on the production timeline."""
    scene_number: int
    order: int                    # 1-based position — TimelinePlan owns ordering, not scene_number
    start_seconds: float
    end_seconds: float
    duration_seconds: float
    pacing: ScenePacing


class TimelinePlan(BaseModel):
    """The single source of truth for WHEN things happen in the production.
    DeterministicTimelinePlanner resolves this from ScenePlan + the real measured
    narration duration; F28's AI Director is expected to produce TimelinePlans
    directly later. No other component in the pipeline computes scene ordering,
    duration, start/end time, or pacing — they all read it from here."""
    total_duration_seconds: float
    scenes: list[SceneTiming] = Field(default_factory=list)
    metadata: dict[str, object] = Field(default_factory=dict)

    def timing_for(self, scene_number: int) -> SceneTiming | None: ...
```

`DeterministicTimelinePlanner` (F27 implementation, $0 cost) assigns each scene a
`ScenePacing` from its **position** in the sequence only (first → `STANDARD`,
second-to-last → `CLIMAX`, last → `BREATHING`, middle scenes on a
FAST→STANDARD→SLOW→DRAMATIC_PAUSE curve by ratio) — deliberately independent of
`CompositionPlan`, since `CompositionPlan` consumes `TimelinePlan` and not the
other way around (no circular dependency). Each pacing category maps to a fixed
duration multiplier; multipliers are applied to each scene's proportional share of
the real measured narration duration and then **rescaled so the sum of all scene
durations equals that real duration exactly** — this is the concrete fix for
§1's "every scene holds the same amount of time" limitation, computed exactly
once, in exactly one place.

### 10.3 `CompositionPlan` revised to carry, not calculate, timing

`SceneComposition` (§3.3) gains one field: `timing: SceneTiming` — copied verbatim
from `TimelinePlan.timing_for(scene_number)` when `DeterministicCompositionPlanner`
builds each entry. `CompositionPlan` never computes a duration, start time, or
pacing value itself; it only reads `timing.pacing`/`timing.order` (already computed
by `TimelinePlan`) as *inputs* to its own, purely visual decisions (e.g. `CLIMAX`
pacing → `REVEAL` purpose). This is why `Shot` production only needs to read
`CompositionPlan` (per the revision's explicit requirement) — the timing it needs
is already attached to each `SceneComposition`.

### 10.4 `AudioTimeline` revised to consume `TimelinePlan` directly

`AudioTimelinePlanner.plan()` gains one additive optional parameter,
`timeline_plan: TimelinePlan | None = None`. When present and its scene set lines
up with the `ScenePlan` being mixed, `scene_transitions`/SFX placement read
`start_seconds`/`duration_seconds` straight from `TimelinePlan.timing_for(...)`
instead of recomputing `((scene_number-1)/scene_count)*total` independently. When
absent (or mismatched), the planner falls back to that exact original proportional
split — the same fallback discipline as every other planner in this codebase, and
why every existing `AudioTimelinePlanner` test keeps passing unchanged.

### 10.5 Sequencing constraint this revision resolves

§8 originally flagged that `TimelinePlan`-driven variable pacing requires knowing
the final scene count *before* Scene Image generation runs (since
`CompositionPromptEnricher` must enrich prompts before images are generated), yet
the authoritative final image count is only known *after* `SceneImageStep` (some
scenes may fail generation). Resolution, consistent with "maintain automatic
fallback behavior wherever appropriate": `TimelinePlan`/`CompositionPlan` are built
once, early, over every planned scene (the optimistic/common case). If the number
of images that actually succeed later differs from `CompositionPlan`'s scene
count, `CompositionAwareShotPlanner` (the new `ShotPlanner` implementation) detects
the mismatch and defers entirely to the legacy uniform-duration `ShotPlanner` path
for that run — exactly the same fallback discipline as cinematic→slideshow and
mixed-audio→raw-narration. Composition-aware variable pacing is used whenever
everything lines up (the normal path); the pipeline never ends up with video and
audio of different lengths.

### 10.6 Preparation for F28 (unchanged conclusion, now more precise)

`TimelinePlan` becomes a third sibling contract alongside `CompositionPlan` and
`Shot`/`AudioTimeline`, all keyed by `scene_number`. F28's AI Director is now
expected to produce `TimelinePlan` and `CompositionPlan`; the existing
deterministic planners for `Shot` and `AudioTimeline` derive from those without any
`RendererPipeline`/`AudioMixerService` redesign — exactly the brief's stated goal
for F28 readiness.

### 10.7 Cost

$0 additional. `DeterministicTimelinePlanner` is pure Python over
`voice_asset.duration` (already measured) and `ScenePlan` (already produced) — no
new LLM call, consistent with §7's cost discipline.

---

## 10. Definition of Done Checklist (this document)

- [x] Current pipeline analyzed with file/line references, not assumed
- [x] Root causes of lost scene quality identified (not symptoms)
- [x] Visual storytelling vocabulary designed (purpose, composition style, camera
      intent, pacing, relationships, continuity motifs, color language) —
      genre-agnostic, no mystery-specific logic
- [x] `CompositionPlan` designed as the `Shot`/`AudioTimeline`-equivalent missing
      layer, produced by a planner, consumed by executors that never invent
      decisions themselves
- [x] Integration with image generation (prompt enrichment only) explained
- [x] Integration with F25 (`CompositionAwareShotPlanner`, additive `ShotPlanner`
      signature, duration-authority fix) explained
- [x] Integration with F26 (why it is NOT wired in F27, and the exact future seam
      when it is) explained
- [x] Preparation for F28 AI Director mapped to concrete seams
- [x] Every proposed mechanism cost-justified; deterministic logic preferred
      throughout; the one possible AI-reasoning addition explicitly evaluated and
      deferred with reasoning
- [x] `TimelinePlan` introduced as the single, authoritative source of truth for
      scene ordering/duration/start/end/pacing (§9, approval-time revision);
      `CompositionPlan` and `AudioTimeline` revised to consume it rather than
      calculate timing independently

**Approved. Implementation follows in this same change.**
