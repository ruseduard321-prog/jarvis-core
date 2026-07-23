# F26 — Jarvis Audio Engine: Architecture Proposal

**Status: APPROVED and IMPLEMENTED**, with one architectural revision (see §3.6a).
Provider decision (stay OpenAI, upgrade to `gpt-4o-mini-tts`) was approved and
implemented as proposed. The revision replaced the original "planner feeds AudioMixer
directly" design with an explicit `AudioTimeline` contract, mirroring F25's `Shot`
philosophy exactly — see §3.6a for the as-built architecture. See `PROJECT_STATE.md`'s
F26 entry for the implementation summary and test results.

---

## 1. Current Architecture (read from code, not assumed)

Narration today is a single linear hop with no post-processing stage:

```
ReviewedScript.revised_script (flat string)
        ↓
VoiceGenerationService.execute()          backend/services/voice_generation_service.py
        ↓
TextToSpeechProvider.generate_speech()     backend/services/text_to_speech_provider.py (ABC)
        ↓
OpenAITextToSpeechProvider                 backend/services/openai_text_to_speech_provider.py
   model = "tts-1", voice = "alloy", speed = 1.0   (backend/core/config.py:52-54)
   client.audio.speech.create(...)  — reuses the shared AsyncOpenAI client
        ↓
VoiceAsset + raw mp3 bytes
        ↓
VideoAssemblyService._assemble_cinematic / _assemble_slideshow_fallback
   writes voice.mp3 to disk, ffmpeg `-map 1:a -c:a aac` — muxed in unchanged
        ↓
Final .mp4 (video_assembly_service.py:192-207)
```

Key facts, verified in code:

- **One TTS call per script**, chunked only by character count (`_MAX_INPUT_CHARS = 4000`,
  splitting on `". "`/`\n` — a purely mechanical API-limit workaround, not a narrative
  device). No per-scene or per-sentence structure is preserved.
- **`speed` is the only expressive control**, a single float applied uniformly to the
  entire narration (`openai_tts_speed = 1.0`). There is no pause, emphasis, or tone
  control anywhere in the call path.
- **Duration is estimated, not measured** (`_estimate_duration`: word count ÷ 150 wpm).
  This is sufficient for F23's subtitle-sync-to-estimate, but means the system never
  actually inspects the audio it produces.
- **Audio pipeline stops at raw TTS output.** `VideoAssemblyService` maps the narration
  track directly into the final container. There is no mixing stage, no music bed, no
  sound effects, no ducking, no loudness normalization, no limiter/compressor, no
  mastering step of any kind — silence behind the narration is architectural, not a
  missing asset.
- **`MusicPlan` and `BrollPlan` already exist** (`backend/schemas/assets.py:170-197`) as
  LLM-authored *direction* (genre/mood/tempo/energy, footage/camera notes) but are
  documented as intent-only — nothing renders them.
- **`MusicGenerationProvider` already exists** (`backend/services/music_generation_provider.py`)
  as an unimplemented ABC, explicitly reserved since F19 for a future concrete provider
  "through the same DI pattern without touching callers." No sound-effect equivalent
  exists yet.
- **F25 already established the exact template F26 should reuse**: a data contract
  (`Shot`, `backend/schemas/shots.py`) produced today by a deterministic planner
  (`DeterministicShotPlanner`) and consumed by a dumb executor (`RendererPipeline`) that
  "never chooses effects itself." F28 (AI Director) is expected to produce `Shot`s
  directly later with **zero renderer changes**. This plan applies the same
  planner/executor split to audio.

### Where the "calm, obviously AI-generated" quality actually comes from

1. **`tts-1` + `alloy`** — OpenAI's fastest/cheapest legacy voice model, chosen for
   nothing but low latency; `alloy` is a neutral, non-cinematic stock voice. There is
   no lever in the current call to make it sound confident or documentary-style,
   because the API surface being used (`model`, `voice`, `speed`) doesn't expose one.
2. **No pacing beyond one flat multiplier** — real documentary narration varies pace
   per beat (slows for weight, quickens for transition); a single `speed` float
   structurally cannot do this.
3. **No dramatic pauses/emphasis** — sentence boundaries are used only to avoid
   splitting mid-sentence for the 4000-char API limit, never to insert a beat.
4. **Silence is the background track.** Even a perfect voice read over dead air reads
   as sterile/synthetic on YouTube, where every competitive documentary channel runs a
   music bed, ambient texture, and a mastered loudness target.
5. **No finishing chain.** Raw TTS output has an inconsistent level and no loudness
   target; there's no normalization to YouTube's ~-14 LUFS, no compression to tighten
   dynamics, no limiter — so perceived "production value" is missing independent of
   voice quality.

### What must remain unchanged

- `TextToSpeechProvider` ABC + DI pattern, and `OpenAITextToSpeechProvider` as its
  concrete implementation (same shared `AsyncOpenAI` client — never a second client).
- `VoiceGenerationService`'s never-raise / FAILED-asset resilience pattern.
- `VideoAssemblyService`'s overall shape: cinematic-with-slideshow-fallback. Audio work
  plugs in as *which bytes get muxed*, not a rewrite of that service.
- `CostTracker`'s per-provider pricing table pattern — extended, not replaced.
- The already-defined `MusicPlan` / `BrollPlan` / `MusicGenerationProvider` contracts —
  reused as the seed of the Background Music module, not reinvented.
- ffmpeg-only local execution for anything mechanical (mixing, normalization,
  mastering) — the same reasoning that put F25's renderer on ffmpeg instead of a paid
  AI-video API applies identically to audio finishing.

---

## 2. Voice Provider Research

### OpenAI (current provider)

| Model | Voices | Style control | Price | Notes |
|---|---|---|---|---|
| `tts-1` (current) | alloy, echo, fable, onyx, nova, shimmer, ash, ballad, coral, sage, verse, marin, cedar | None — text in, audio out | $0.015 / 1K chars | Optimized for latency, not quality |
| `tts-1-hd` | same voice list | None | $0.030 / 1K chars | Higher fidelity, same lack of control |
| **`gpt-4o-mini-tts`** | same voice list; OpenAI recommends **marin**/**cedar** for quality-focused use | **`instructions` parameter** — natural-language direction ("speak slowly, with quiet authority and dramatic pauses at commas") steers tone, pacing, and delivery per request | ≈$0.60/M input tokens + $12/M audio tokens ≈ **$0.015/minute of audio** in practice | Same vendor, same client, same auth — this is the model that solves the stated problem |

`gpt-4o-mini-tts`'s `instructions` parameter is the single highest-leverage change
available: it is a direct, first-party implementation target for the `VoiceDirection`
abstraction requested below, at cost parity with what's already being paid.

### ElevenLabs (leading alternative, researched not assumed)

- Quality is genuinely ahead on independent MOS benchmarks — richer emotional
  inflection, larger voice library, purpose-built for narration/audiobook work.
- Cost is materially higher and shaped differently: subscription tiers rather than
  simple per-character billing (e.g. ~$99/mo for 500K chars vs. ~$7.50 for the same
  volume on OpenAI TTS) — a worse fit for `CostTracker`'s flat per-video cost model.
- Integration cost is non-trivial: a new provider class, new credential/secret
  management, a new error-classification/retry mapping (mirroring
  `openai_error_classification.py`), and a new billing relationship to maintain —
  real, ongoing maintenance surface, not a one-time cost.

**Decision: stay on OpenAI, upgrade `tts-1`/`alloy` → `gpt-4o-mini-tts` with a
documentary-appropriate voice (`onyx` as the safe deep-male default; `cedar`/`marin`
should be short-listed and ear-tested before locking in — voice timbre is a subjective
judgment call no amount of research substitutes for a listening pass) and its
`instructions` parameter.**

Justification against the stated trade-off criteria:
- **Quality improvement**: large — this is the difference between "no style control"
  and "natural-language directable delivery," which is architecturally what was
  missing, not just voice timbre.
- **Cost increase**: roughly flat (≈$0.015/min vs. ≈$0.015/1K chars today — a few cents
  per video either way against the existing $0.85/video budget).
- **Complexity**: near zero — same provider, same client, one new optional parameter
  on an existing method signature.
- `TextToSpeechProvider` remains a real abstraction specifically so ElevenLabs (or any
  premium provider) can be added later as a second concrete class with **zero caller
  changes**, if/when quality economics shift. This is not foreclosed, only deferred.

---

## 3. Recommended Architecture

Mirrors F25's contract/planner/executor split exactly — a proven pattern in this
codebase, not a new idiom. **Revised per architecture review (§3.6a): the mixer does
not receive raw narration/music/effects or a "mix plan" directly — it receives one
`AudioTimeline`, the audio equivalent of `Shot`, and only ever executes it.**

```
Script (ReviewedScript)
        ↓
VoiceDirectionPlanner  ─┐  deterministic today (profile lookup);
        ↓               │  F28 AI Director produces VoiceDirection directly later —
   VoiceDirection       ┘  zero downstream change required
        ↓
VoiceGenerationService (extended)
        ↓
   TextToSpeechProvider.generate_speech(..., instructions=...)
        ↓
   VoiceAsset + raw narration bytes
        ↓
NarrationProcessingService        — normalization / cleanup pass on the raw voice track
        ↓
Background Music (selection)      — MusicGenerationProvider resolves a MediaAsset (or none)
        ↓
Sound Effects (selection)         — SoundEffectProvider resolves MediaAssets (or none)
        ↓
AudioTimelinePlanner  ─┐  deterministic today (narration duration + selected
        ↓              │  music/SFX assets + Scene metadata → a timeline);
   AudioTimeline       ┘  F28 AI Director produces AudioTimeline directly later,
                          keyed by the same scene_number as Shot — zero mixer change
        ↓
AudioMixerService  — executes the AudioTimeline exactly as given (places segments/cues,
        ↓            ducks, fades, masters) via ffmpeg filters only. Never decides
        ↓            WHAT should happen — only HOW to render what it's told.
   AudioAsset + mixed bytes
        ↓
VideoAssemblyService  — unchanged shape; muxes the mixed track instead of raw voice
        ↓                bytes (same fallback discipline: mixing failure → fall back
                         to muxing raw narration, exactly like cinematic → slideshow)
Final Video
```

### 3.1 Voice Direction (new abstraction)

```python
# backend/schemas/audio.py (proposed)
class VoiceDirection(BaseModel):
    profile: str                 # e.g. "documentary_male"
    pace: float = 1.0            # maps to gpt-4o-mini-tts speed / instructions phrasing
    intensity: str = "measured"  # calm | measured | dramatic — future emotional range
    instructions: str            # literal text sent to gpt-4o-mini-tts's `instructions`
    pause_markers: list[PauseMarker] = []   # reserved; not applied until F28-era work
```

Today: `VoiceDirectionPlanner` builds this deterministically from a selected
`VoiceProfile` plus simple script heuristics (e.g. sentence length → pace), the same
way `DeterministicShotPlanner` keyword-matches `camera`/`animation` text today. No AI
call, no added cost. Later: F28's AI Director can emit `VoiceDirection` per scene/beat
directly from the LLM, reusing `Shot.scene_number` to align narration direction with
cinematic direction — this is the "AI Director controls both engines" hook the roadmap
asks for.

### 3.2 Voice Profiles (new, reusable registry)

A small, data-only registry — not a redesign surface. Each profile maps to a model,
voice id, and a base `instructions` template:

| Profile | Voice | Base direction |
|---|---|---|
| Documentary Male (default) | `onyx` (or `cedar`, pending audition) | confident, deep, deliberate pacing, dramatic pauses at commas |
| Documentary Female | `nova` / `sage` (pending audition) | warm, authoritative, measured pacing |
| Storytelling | `fable` | intimate, curious, varied pace |
| Historical | `echo` | grave, slow, formal |
| Mystery | `onyx` + tense instructions | quiet, tense, deliberate pauses |
| News | `alloy` | brisk, neutral, clipped |
| Educational | `nova` | clear, friendly, even pace |

Adding a profile is adding one registry entry — no code path changes. F26 only needs to
ship **Documentary Male** for real; the rest is architecture headroom, per the brief.

### 3.3 Narration Processing (new, minimal)

A single ffmpeg pass on the raw TTS output before mixing: loudness normalization
(`loudnorm`) so every narration track starts from a consistent level regardless of
provider/voice. This is the "Narration Processing" stage from the requested pipeline
diagram — deliberately thin today (normalization only), with a clear seam for future
noise reduction/EQ if ever needed.

### 3.4 Background Music (extends existing, unimplemented, contracts)

- Reuses `MusicPlan` (already defined) as the direction input and
  `MusicGenerationProvider` (already defined, zero implementations) as the provider
  seam — no new abstraction needed here, only a first concrete implementation.
- Recommended first implementation: a **local, tagged, royalty-free asset library**
  (folder-per-mood: ambient/mystery/cinematic/emotional/historical/tension), selected
  deterministically by matching `MusicPlan.mood`/`genre` — zero API cost, consistent
  with "reduce production cost" and F25's "prioritize local rendering" precedent.
- True generative music (Stable Audio / ElevenLabs Music / Suno-style APIs) is a
  clearly-labeled future upgrade behind the *same* `MusicGenerationProvider` interface —
  swappable later without touching `AudioMixerService`.
- Music is always optional: selection simply yields no `MediaAsset`, and
  `AudioTimelinePlanner` omits any `MusicCue` when that happens. Its absence never
  blocks narration or video assembly (matches "music must always remain optional").

### 3.5 Sound Effects (new, mirrors 3.4 exactly)

```python
# backend/services/sound_effect_provider.py (proposed ABC, mirrors music_generation_provider.py)
class SoundEffectProvider(ABC):
    async def get_sound_effect(self, *, keywords: str) -> MediaAsset: ...
```

First implementation: a small curated local library (CC0 packs — wind, ocean, rain,
radio static, footsteps, typewriter, whoosh, drone, impact), selected by keyword match
against `Scene` text — the same deterministic-keyword-matching pattern
`DeterministicShotPlanner` already uses for camera movement. Effects are data (asset +
tag), never hardcoded into `AudioMixerService` — new effects are new library entries.
Selecting *which* asset is a provider concern (like `ImageGenerationProvider` choosing
an image); deciding *when/how loud* it plays on the timeline is the planner's job below.

### 3.6a AudioTimeline — the `Shot` of the audio engine (revised)

The original proposal fed a flat "mix plan" of volumes/toggles straight to the mixer.
**That does not mirror F25 closely enough.** F25's actual discipline is a *data
contract* describing what should happen, produced by a planner and consumed by a
renderer that "never chooses effects itself." Revised accordingly:

```python
# backend/schemas/audio.py (proposed)
class NarrationSegment(BaseModel):
    """One placed span of the processed narration track on the timeline."""
    start_seconds: float = 0.0
    duration_seconds: float = 0.0
    scene_number: int | None = None
    volume_db: float = 0.0


class MusicCue(BaseModel):
    """One placed background-music span. Supports future per-cue volume automation
    (a list of (time, db) points) as an additive field — not needed today."""
    start_seconds: float = 0.0
    duration_seconds: float = 0.0
    source_path: str
    volume_db: float = -18.0
    fade_in_seconds: float = 0.0
    fade_out_seconds: float = 0.0
    duck_under_narration: bool = True


class SoundEffectEvent(BaseModel):
    """One sound-effect placement, keyed to the scene it belongs to."""
    at_seconds: float = 0.0
    source_path: str
    scene_number: int | None = None
    volume_db: float = 0.0


class SceneTransitionMarker(BaseModel):
    """Marks a scene handoff point in time — reserved for future per-scene
    ducking/SFX timing keyed to the same scene_number as Shot."""
    scene_number: int
    at_seconds: float


class AudioTimeline(BaseModel):
    """The data contract between audio planning ('what should happen, and when')
    and audio execution ('mix exactly that'). This IS Shot's counterpart for audio:
    AudioTimelinePlanner resolves it deterministically today; F28's AI Director is
    expected to produce AudioTimelines directly later, keyed by the same scene_number
    as Shot. AudioMixerService executes whatever timeline it is given and never
    makes a creative decision itself — same discipline as RendererPipeline."""
    total_duration_seconds: float = 0.0
    narration_segments: list[NarrationSegment] = Field(default_factory=list)
    music_cues: list[MusicCue] = Field(default_factory=list)
    sound_effect_events: list[SoundEffectEvent] = Field(default_factory=list)
    scene_transitions: list[SceneTransitionMarker] = Field(default_factory=list)
    fade_in_seconds: float = 1.0
    fade_out_seconds: float = 2.0
    master_loudness_lufs: float = -14.0   # YouTube's normalization target
```

`AudioTimeline` naturally accommodates every future concept the brief asked for:
narration segments (already multi-segment capable — silence is simply a gap between
segments, no separate type needed), music cues, SFX events, fades, ducking (a bool on
`MusicCue` today; a future automation curve is additive), scene transitions, and
`scene_number` synchronization with `Shot` — without adding a single field that isn't
already load-bearing today.

### 3.6b Audio Mixer (executor only — revised)

```python
# backend/services/audio_mixer_service.py (proposed)
class AudioMixerService:
    """Executes an AudioTimeline against narration/music/SFX source bytes to produce
    one mixed, mastered audio track via ffmpeg filters only — amix/sidechaincompress
    (ducking), afade (fades), loudnorm (mastering to a fixed LUFS target). Mirrors
    RendererPipeline exactly: every value comes from the AudioTimeline it is given;
    it never chooses volumes, timing, or whether to duck — those are planning
    decisions, made upstream, before the mixer is ever called."""

    def mix(self, *, narration_bytes: bytes, timeline: AudioTimeline,
            music_bytes: bytes | None, sound_effect_bytes: dict[str, bytes],
            timeout_seconds: float) -> bytes: ...
```

`AudioTimelinePlanner` (ABC) + `DeterministicAudioTimelinePlanner` (F26's
implementation) fill the planner role — deterministic today (one full-length
narration segment, one optional full-length ducked `MusicCue` when a track was
selected, optional per-scene `SoundEffectEvent`s when SFX are enabled), with F28's AI
Director expected to supply richer, per-scene `AudioTimeline`s later using the exact
same `Shot.duration_seconds` timing data already produced for video — no new data
required, only a new producer of the same contract.

---

## 4. Integration With the Existing Pipeline

```
Research → Writer → Reviewer → Scene Planning → F25 Cinematic Video Engine
                                                        ↑ Shot metadata (reused)
Reviewed Script → VoiceDirectionPlanner → VoiceGenerationService (extended)
                → NarrationProcessingService → Background Music → Sound Effects
                → AudioTimelinePlanner → AudioTimeline → AudioMixerService
                                                        ↓
                                          VideoAssemblyService (unchanged shape)
                                                        ↓
                                                  Final Video
```

Concretely, in `youtube_production_workflow.py`: narration direction/generation/
processing stay inside the existing `VoiceStep` (extending `VoiceGenerationService`,
not adding a step). A new `AudioEngineStep` ("Audio Mix") is inserted after `Scene
Planning` (the first point `MusicPlan`/`ScenePlan` are both available) and before
`Video Assembly`. It resolves optional music/SFX, builds the `AudioTimeline`, executes
it via `AudioMixerService`, and produces an `AudioAsset` (mixed bytes) that
`VideoAssemblyService` receives instead of raw `audio_bytes`; on any mixing failure or
disabled configuration it falls back to muxing the raw narration track untouched,
matching the cinematic→slideshow fallback discipline already in place.
`VideoAssemblyService`'s ffmpeg mux call itself does not change — it already accepts
"one audio track"; only which track is handed to it changes.

---

## 5. Future Compatibility (explicitly designed for, not built now)

- **AI Voice Director (post-F28)**: replaces `VoiceDirectionPlanner`'s heuristic with an
  LLM call producing the same `VoiceDirection` objects — no change to
  `VoiceGenerationService` or `TextToSpeechProvider`.
- **Adaptive pacing/pauses/emphasis**: additive fields on `VoiceDirection` /
  `PauseMarker`, consumed by the same `instructions` string-building step.
- **Multilingual narration**: `VoiceAsset.language` and `VoiceDirection.profile` already
  separate language from style; a non-English profile is a registry entry, not a
  redesign.
- **Premium provider swap (e.g. ElevenLabs)**: a second `TextToSpeechProvider`
  implementation selected by `settings.tts_provider`, exactly like today's
  `DefaultTextToSpeechProvider`/`OpenAITextToSpeechProvider` split.
- **Automatic music/SFX generation**: second concrete implementations of
  `MusicGenerationProvider`/`SoundEffectProvider` — `AudioMixerService` is unaffected
  either way, it only consumes bytes referenced by the `AudioTimeline` it's given.
- **Scene-aware/dynamic audio**: `AudioTimelinePlanner` reading the `Shot` list (F25)
  directly — the data already exists, this is a new consumer, not new data.
- **F28 AI Director controlling both engines**: `Shot` (video) and `AudioTimeline`
  (audio) are sibling contracts keyed by the same `scene_number` — a single AI Director
  call can emit both without either `RendererPipeline` or `AudioMixerService` changing.
  This is the central reason `AudioTimeline` exists as its own contract rather than the
  mixer taking raw inputs directly: it gives F28 one clean seam to target for audio,
  exactly as `Shot` already is for video.

---

## 6. Cost Summary

| Item | Today | Proposed | Delta |
|---|---|---|---|
| Voice model | `tts-1` @ $0.015/1K chars | `gpt-4o-mini-tts` @ ≈$0.015/min audio | ≈flat, a few cents/video |
| Narration processing | none | ffmpeg `loudnorm` (local, free) | $0 |
| Background music | none | local royalty-free library (local, free) | $0 |
| Sound effects | none | local CC0 library (local, free) | $0 |
| Mixing/mastering | none | ffmpeg filters (local, free) | $0 |

**Net expected cost increase: negligible (single-digit cents/video)** against the
current ≈$0.85/video baseline, for what is architecturally the largest lever available
on narration quality plus a full mixing/mastering chain that costs nothing today.

---

## 7. Definition of Done Checklist (this document)

- [x] Current architecture explained, with file/line references
- [x] Weaknesses identified and tied to root cause, not symptom
- [x] What must remain unchanged, called out explicitly
- [x] Voice provider research completed (OpenAI models/voices, style control, ElevenLabs)
- [x] Recommended provider decision, justified on quality/cost/complexity/maintainability
- [x] Module breakdown for Voice Direction, Voice Profiles, Narration Processing,
      Background Music, Sound Effects, AudioTimeline, Audio Mixer
- [x] Integration with existing pipeline (F25 → F26 → Final Video)
- [x] Future extensibility mapped to concrete roadmap items (F27–F30)
- [x] Cost trade-off explained for every recommendation
- [x] `AudioTimeline` introduced as the explicit `Shot`-equivalent contract; `AudioMixer`
      reduced to a pure executor with no creative decisions (architecture review revision)

**Approved. Implementation follows in this same change.**
