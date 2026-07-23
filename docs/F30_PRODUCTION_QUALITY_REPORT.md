# F30 — Production Quality Validation Report

**Status:** Validation complete. No code was modified to produce this report.
**Scope:** Audit of the real, already-implemented F25–F29 pipeline (Cinematic Rendering, Audio Engine, Smart Scene Composition, AI Director, Render Profiles, Adaptive Visual Storytelling, Viewer Retention) against actual production output.

## Evidence base

This report is built from **real production runs**, not documentation claims. Every finding below is anchored to one or more of:

- **6 real `storage/runs/*` productions**, of which two are full current-architecture runs used as primary evidence:
  - `2898c8d4-21f8-45e6-b107-440215d01629` — *"Destruction of Pompeii"* (most recent, 2026-07-22 21:29)
  - `eeeb8edd-c14c-4a35-a086-7f43c8aaf6c9` — *"Mansa Musa — The Man So Rich He Changed an Economy"* (2026-07-22 00:35, has a full 461KB structured execution log: `mansa_musa_run.log`)
  - 4 older runs (`524bb8af`, `7a99e839`, `8b6e1667`, `fb037b67`) used as a "before" comparison baseline
- `ffprobe`/`ffmpeg` analysis of every `video.mp4` and `voice.mp3` (resolution, codec, bitrate, channel layout, GOP structure, `volumedetect`/`silencedetect` loudness analysis)
- Direct visual inspection of generated images, thumbnails, and script/subtitle text
- Direct reading of the actual service implementations in `backend/services/` and `backend/core/`, not just their docstrings or `PROJECT_STATE.md` claims
- `mansa_musa_run.log` — real step timings, real LLM call durations, real errors/tracebacks

Throughout, findings distinguish **intended architecture** (what `PROJECT_STATE.md`/architecture docs describe), **implemented architecture** (what the code actually does), and **observed production behaviour** (what real runs actually produced).

---

## 1. Production Quality Report

### Score summary (1–10, observed production quality)

| # | Category | Score | Primary finding |
|---|---|---|---|
| 1 | Script Quality | 8 | Strong prose/factual hedging; formulaic hook/CTA phrasing |
| 2 | Story Pacing | 5 | Scene count decoupled from Writer's own scene markers |
| 3 | Viewer Retention | 5 | Plumbing exists but unverifiable — no plan persisted |
| 4 | AI Director Decisions | 8 | Genuinely executes real reasoning in production |
| 5 | Timeline Planning | 7 | Sound logic, invisible as a telemetry stage |
| 6 | Composition Planning | 6 | Beat counts cluster at the hard ceiling, not the target |
| 7 | Visual Beats | 7 | Duration-weighting math is real and correct |
| 8 | Image Quality | 7 | Strong baseline; occasional multi-panel collage failures |
| 9 | Historical Consistency | 5 | Landmark geometry drifts; garbled on-image map text |
| 10 | Character Consistency | 3 | No seed/reference conditioning — worst finding in the audit |
| 11 | Thumbnail Quality | 7 (standalone) | Strong alone; mismatches the body's character design |
| 12 | Camera Movement | 6 | Real Ken Burns motion, but not AI-Director-driven |
| 13 | Scene Transitions | 5 | Only 2 of 6 planned transition energies are actually renderable |
| 14 | Image Generation → Render Aspect | 3 | Square 1024×1024 stretched (not cropped) to 16:9, every frame |
| 15 | Render Quality (encoder/profile) | 8 (when reached) | CRF18/AAC48k/GOP is genuinely solid — the profile is good |
| 16 | Resolution / 1080p delivery | 3 | 4 of 6 real runs shipped at 1024×1024, not 1080p |
| 17 | Voice Quality | 6 | Mono/64kbps CBR — a hard OpenAI TTS API ceiling |
| 18 | Voice Expressiveness | 6 | Static per-script instructions; never wired to AI Director |
| 19 | Background Music | 1 | Off by default; asset library doesn't exist on disk |
| 20 | Sound Effects | 1 | Off by default; asset library doesn't exist on disk |
| 21 | Audio Mixing | 7 (code) / unvalidated (production) | Well-built ducking/mastering chain that has never executed against real multi-track input |
| — | Overall Cinematic Feeling | **~3–4** | Composite of #10, #14, #16, #19, #20 |
| — | Cost telemetry vs $5/doc target | n/a | No aggregate per-run cost is ever logged; the one cost estimate that exists is stale (see §1.12) |

### 1.1 Script Quality — 8/10

**Implementation:** `writer_workflow_service.py:74-82` — one LLM call (`gpt-5.5`), fixed structure (Hook → Intro → Main Story → Interesting Facts → Conclusion → CTA), strict JSON, single free-text duration label as the only pacing control.

**Observed:** Both real scripts (Pompeii, 92 lines; Mansa Musa, 107 lines) and all 4 older runs read cleanly, hedge appropriately on disputed facts ("the total number of deaths is still debated in the supplied sources"), and have strong hooks. But the CTA — *"...like the video, subscribe... tell us in the comments what/which..."* — is near-verbatim identical across every single run regardless of topic.

**Architecture vs reality:** Matches intended design (single synthesis pass); the repetition is an emergent property of an unconstrained prompt, not a broken feature.

**Root cause:** **C) Prompt Engineering** — no variation directive for hook/CTA phrasing.
**Effort:** Small. **Improvement if fixed:** 8→9.
**Evidence:** `storage/runs/2898c8d4.../script.md:22`, `storage/runs/eeeb8edd.../script.md:32`, and matching lines in the 4 older runs; `writer_workflow_service.py:74-82`.

### 1.2 Story Pacing — 5/10

**Implementation:** Scene Planning (`scene_planning_service.py:59-99`) runs a **second, independent** LLM call over only the flat narration text and is instructed to *"Return EXACTLY {max_scenes} scenes... regardless of how many beats it naturally has"* (`max_scenes_per_video = 8`, `backend/core/config.py:108`), with hard truncation if the model overshoots (lines 126-139).

**Observed:** The Pompeii script lists 16 `## Scene Markers`; Mansa Musa lists 10. Neither maps to the 8 scenes actually produced. **`## Scene Markers` is dead output — never read by any downstream service.** It exists for human readability only, which makes `script.md` misleading as a record of the video's real structure. Scene boundaries are placed with no narrative-weight signal, so a dense climax and a slow setup receive comparable screen time purely by even text-length division.

**Architecture vs reality:** `PROJECT_STATE.md` framing implies Writer→Scene Planning is a refinement pipeline; in reality they're two disconnected LLM calls with incompatible scene counts.

**Root cause:** **F) Architecture Limitation** — the fixed-8-scenes ceiling is a defensible cost guardrail (`scene_planning_service.py:80-83`, comment: *"must never be able to set that count itself"* — this protects the paid `gpt-image-1` call budget), but there is no compensating per-scene duration-weighting step.
**Effort:** Medium. **Improvement if fixed:** 5→7 (same 8 scenes, better-placed boundaries, no added generation cost).
**Evidence:** `scene_planning_service.py:59-99,126-139`; `config.py:108`; marker counts in both real `script.md` files.

### 1.3 Viewer Retention (F29) — 5/10

**Implementation:** `SceneRetention` (`backend/schemas/composition.py:154-175`) is fully optional and populated only if the AI Director's JSON includes it; the prompt explicitly solicits retention fields (`ai_director_provider.py:175-227`).

**Observed:** The wiring is real and doesn't error — `CompositionAwareShotPlanner` correctly reads `composition.retention.transition_energy` when present (`composition_aware_shot_planner.py:152-154`). **But the raw `AIDirectorPlan`/`CompositionPlan` JSON is never persisted anywhere in `storage/runs/`** — only final rendered artifacts exist. This audit cannot directly confirm from real evidence whether `retention` was populated for any scene in either full run; only indirect proxies (beat-count spread, transition choice) are observable.

**Root cause:** **B) Missing Feature** — no persistence/logging of the intermediate AI Director plan. This is the single biggest validation gap in the whole pipeline: it blocks confirming whether F29 delivers what it claims.
**Effort:** Small (`composition_plan.model_dump_json()` → `storage/runs/{id}/composition_plan.json`, no new pipeline step).
**Improvement if fixed:** Not directly a quality fix, but unblocks measuring the +2–3 points F29 should be delivering.
**Evidence:** `backend/schemas/composition.py:154-209`; absence confirmed by directory listing of both real run folders.

### 1.4 AI Director Decisions (F28) — 8/10

**Implementation:** `ai_director_provider.py:74-228` — one LLM call (`gpt-5.5`) reasoning over the whole script at once, strict JSON → `AIDirectorPlan`.

**Observed (positive finding):** In `mansa_musa_run.log`, the AI Director call genuinely executed — 88,071ms of real LLM time producing 21,717 characters of plan output, with **no `ai_director_fallback_to_deterministic_planning` warning anywhere in the log**. This substantiates the "F28 completed" claim with real evidence, not just documentation. Scene Planning similarly ran a real 88,340ms call.

**Gap:** `_resolve_agent_id()` (`ai_director_provider.py:230-247`) always probes `agent_id="creation_agent"`/`"creation"` as literal UUID lookups first, both guaranteed to fail against Supabase (`invalid input syntax for type uuid`), producing 2 stack-trace ERROR logs every run before falling back to slug matching. Harmless but noisy (repeats for Writer, Review, Scene Planning agents too — 4+ tracebacks per run).

**Root cause:** **A) Bug** (agent-resolution anti-pattern).
**Effort:** Small. **Improvement if fixed:** +1–2 (observability only).
**Evidence:** `mansa_musa_run.log:1826-1840`; `ai_director_provider.py:57-58,230-247`.

### 1.5 Timeline Planning (F27) — 7/10

**Implementation:** There is **no standalone "Timeline Planning" workflow step** — `ai_director_plan_builder.build_timeline_plan()` (`ai_director_plan_builder.py:16-61`) runs inside the "Composition Planning" step, rescaling the AI's relative per-scene durations to match the real measured narration length exactly, with defensive validation.

**Observed:** Ran cleanly in both real runs, no `AIDirectorValidationError`. But grepping the full 3,478-line `mansa_musa_run.log` for a `'step': 'Timeline Planning'` marker returns **zero matches** — its cost/time is invisibly folded into Composition Planning's 88s, so an operator has no way to see how much time/cost timeline reasoning specifically consumes.

**Root cause:** **F) Architecture Limitation** — merging Timeline Planning into the AI Director's single pass was a correct design choice, but step-instrumentation was never updated to reflect it.
**Effort:** Small. **Improvement if fixed:** +1 (observability).
**Evidence:** Full-log grep (zero hits); `ai_director_plan_builder.py:16-61`; `composition_planning_service.py:87-97`.

### 1.6 Composition Planning (F27) — 6/10

**Implementation:** `CompositionPlanningService.execute()` (`composition_planning_service.py:69-105`) tries AI Director first, then clamps beats/scene to a configured ceiling (`maximum_visual_beats_per_scene`, default **4**) and a cost-budget trim.

**Observed:** Real beat counts per scene — Mansa Musa: `3,4,4,4,3,3,3,4`; Pompeii: `3,4,4,3,3,4,3,3`. **Every scene landed in {3,4} — never at the configured floor (1) or the stated "comfortable target" (2)**, in both independently-generated runs. The prompt states target=2, min=1, max=4 "if in doubt, use fewer" (`ai_director_provider.py:166-169`) — the model consistently anchors to the ceiling instead.

**Root cause:** **C) Prompt Engineering** — the safety ceiling functions as the de facto decision, not the stated target.
**Effort:** Medium (prompt rework + retesting across topics). **Improvement if fixed:** +2–3 (more cost-efficient, more differentiated allocation).
**Evidence:** Image directory listings for both real runs; `config.py:153-155`; `ai_director_plan_builder.py:129-142`.

### 1.7 Visual Beats (F28B) — 7/10

**Implementation:** `CompositionAwareShotPlanner._beat_durations()` (`composition_aware_shot_planner.py:137-150`) does real importance-weighted duration splitting (LOW=3, NORMAL=4, HIGH=6, CRITICAL=7), matching the architecture spec exactly.

**Observed (positive):** Every scene in both real runs rendered its full planned beat count with zero fallback triggers — the duration-weighting half of F29/F28B genuinely works.

**Gap:** `_TRANSITION_BY_ENERGY` maps 6 `TransitionEnergy` values down to only 2 actual renderable `TransitionType`s (dissolve/fadeblack), because `RendererPipeline` only supports two (code's own comment, lines 30-33). Retention reasoning that picks `suspense` vs `dramatic` vs `energetic` all render identically.

**Root cause:** **E) Rendering Limitation** (planning logic is correct; the renderer's `TransitionType` enum is the bottleneck).
**Effort:** Large. **Improvement if fixed:** +2.
**Evidence:** `composition_aware_shot_planner.py:23-41,137-150`.

### 1.8 Image Quality — 7/10

**Implementation:** `scene_image_generation_service.py:131-136` → `openai_image_generation_provider.py:59-65`, model `gpt-image-1`, `size="1024x1024"`, `quality="medium"` (`config.py:44-51`). No output validation, no re-roll on bad output.

**Observed:** Baseline is genuinely strong — correct anatomy, coherent lighting, real dramatic staging (e.g. `scene_04_beat_02.png`, Pompeii; `scene_15.png`, Roanoke). But `scene_06_beat_02.png` (Pompeii) is a **3-panel collage** — the model composited three unrelated sub-shots into one canvas with visible black gutter lines, defeating the one-beat-one-shot design with zero detection.

**Root cause:** **B) Missing Feature** — no output validator/re-roll step exists.
**Effort:** Small. **Improvement if fixed:** +1–2.
**Evidence:** `scene_06_beat_02.png`, `scene_04_beat_02.png`; `scene_image_generation_service.py:125-168`.

### 1.9 Historical Consistency — 5/10

**Implementation:** No fact-grounding or reference-image step exists between Research/Script and image prompting; `composition_prompt_enricher.py` only appends style/continuity *text* phrases, never geographic/factual reference data.

**Observed:** Mount Vesuvius's silhouette is inconsistent across the same run — a twin-crater aerial cone (`scene_03_beat_01.png`), a rounded single peak (`scene_08_beat_03.png`), a steep cone with visible lava (`scene_06_beat_02.png`) — three different mountains for one landmark. The Mansa Musa map card renders "Gao" as **"GAG"** and truncates "Timbuktu" to **"TIMF"**.

**Root cause:** **D) AI Model Limitation** (diffusion text rendering is unreliable) compounding **F) Architecture Limitation** (no cross-call reference to anchor recurring real-world landmarks).
**Effort:** Medium. **Improvement if fixed:** +2–3.
**Evidence:** `scene_03_beat_01.png`, `scene_08_beat_03.png`, `scene_06_beat_02.png`, `scene_06_beat_01.png`.

### 1.10 Character Consistency — 3/10 — **worst finding in the audit**

**Implementation:** Confirmed by grep across `backend/services`/`backend/schemas`: **no `seed`, `reference_image`, or `character_sheet` parameter exists anywhere in the image-generation call chain** (`image_generation_provider.py:12-19`, `openai_image_generation_provider.py:37-65` accept only `prompt, size, quality, model`). Continuity is text-only motif tags (`composition_planner.py:204-238`), never visual.

**Observed:** Mansa Musa appears **four distinct ways** in one run: a small generic silhouette (`scene_01_beat_01.png`); a camel-mounted king in cream robes with a simple gold crown (`scene_04_beat_01.png`); a flat graphic-illustration bust with a "starburst" crown in a completely different art style (`scene_08_beat_01.png`); and a hyper-detailed close portrait with an ornate red-gemmed crown (`thumbnail.png`). Crown, robe, skin rendering, and even art style differ across all four — a viewer cannot recognize this as one recurring person.

**Root cause:** **F) Architecture Limitation** — every `generate_image` call is a fully independent, stateless request with no mechanism to lock a recurring figure's appearance.
**Effort:** Large (real feature: reference-image conditioning / img2img / character-sheet-first pipeline). **Improvement if fixed:** +4–5 — **highest-ROI single fix identified in this entire audit.**
**Evidence:** `scene_01_beat_01.png`, `scene_04_beat_01.png`, `scene_08_beat_01.png`, `thumbnail.png` (all `eeeb8edd`); `composition_prompt_enricher.py:37-69`; `image_generation_provider.py:12-19`.

### 1.11 Thumbnail Quality — 7/10 standalone

**Implementation:** `thumbnail_generation_service.py:49-54` reuses identical size/quality/model settings as body images.

**Observed:** Both sampled thumbnails are strong in isolation — good contrast, legible bold text, clear focal subject, competitive with real YouTube history-channel thumbnails. But the Mansa Musa thumbnail's character design matches **none** of the body images (see §1.10) — packaging oversells a character the video never delivers.

**Root cause:** Shares root cause with §1.10 (**F) Architecture Limitation** — no shared canonical character reference).
**Effort:** Small once §1.10 is fixed. **Improvement if fixed:** +1 standalone, +3 bundled with §1.10.
**Evidence:** `thumbnail_generation_service.py:49-54`; thumbnail vs. body images, `eeeb8edd` run.

### 1.12 Cost telemetry vs. $5/documentary target

**Implementation:** `cost_tracker.py` exists and is referenced across 13 service files. A pre-generation image-cost preview is logged.

**Observed:** `mansa_musa_run.log` shows exactly one cost line: *"Estimated image cost: $0.38"* for "Scene images: 8, Thumbnail: 1, Total images: 9" — **this estimate is stale**. It assumes the pre-F28B model of one image per scene; the real F28B/F29 run actually generated ~27–31 beat-level images (3–4 per scene × 8 scenes), so the true image spend is roughly **3–4× the logged estimate**. Beyond that one stale preview line, **no aggregate per-run cost total (LLM + images + TTS combined) is ever logged or persisted anywhere** — there is no artifact in `storage/runs/` or the logs that states "this documentary cost $X," making it impossible to verify the $5/documentary target from real evidence.

**Root cause:** **A) Bug** (stale cost formula, predates F28B) + **B) Missing Feature** (no aggregate cost logging/persistence).
**Effort:** Small–Medium. **Improvement if fixed:** Not a quality fix, but a hard prerequisite for validating the stated $5/documentary constraint at all.
**Evidence:** `mansa_musa_run.log:1820-1821`; `cost_tracker.py:46-125`; real beat-image counts (27–31) vs. the "9 images" the estimate assumes.

### 1.13 Camera Movement (F25) — 6/10

**Implementation:** `cinematic_camera_movement.py` implements real per-frame Ken Burns motion via ffmpeg `zoompan` — 8 distinct movement types, not a static shot. Selection (`cinematic_shot_planner.py:15-51`) is keyword-match-then-round-robin, deterministic, **not** LLM/AI-Director-driven — the code's own comment (lines 79-82) notes this seam is "expected to add" AI-Director involvement later, which never happened despite F28 being marked complete.

**Observed:** `camera_movements` genuinely varies across scenes in real output (`video_assembly_service.py:188`) — the technique is real, not a stub.

**Root cause:** **B) Missing Feature** (F28's creative authority was never wired into shot/movement selection).
**Effort:** Medium. **Improvement if fixed:** +1–2.
**Evidence:** `cinematic_shot_planner.py:15-82`; `video_assembly_service.py:188`.

### 1.14 Aspect-ratio distortion (Image Generation → Render seam) — 3/10

This is the deepest and most consequential rendering defect found. Two contributing root causes, verified empirically, not assumed:

**(a) Source images are always square.** `config.py:45` hardcodes one global `openai_image_size = "1024x1024"` for every image regardless of shot/composition style — even though `gpt-image-1` natively supports `1536x1024` (near-16:9), which the code never requests. **Root cause: B) Missing Feature.**

**(b) The renderer stretches, not crops, square source into 16:9.** `cinematic_camera_movement.py:13-17`, `_zoompan()`: `scale=iw*2:ih*2, zoompan=z=...:x=...:y=...:d=...:s={out_w}x{out_h}`. Because `z` scales width/height by the same scalar, the extracted crop window is always **square**, then force-resized to `s=1920x1080` (16:9) with no aspect-preserving crop/pad step anywhere. Verified by reproducing the exact `_push_in` filter against a real source frame (`scene_01_beat_01.png`, confirmed 1024×1024 via ffprobe): the *entire* square composition is visible in the 16:9 output (nothing cropped), and circular objects render visibly flattened — this is **anamorphic stretch**, present in **both real 1080p runs**, on every frame, at every zoom level. `depth_estimator.py`'s own docstring confirms `NullDepthEstimator` is "not called by anything yet" — no saliency-aware crop exists anywhere in the pipeline. **Root cause: A) Bug.**

**Effort:** Medium for (a) (wire composition style → image size request); Medium for (b) (add crop-to-fill before/inside the zoompan chain). **Improvement if fixed:** 3→8 — this is a defect on 100% of frames of the only 2 runs that reach 1080p at all.
**Evidence:** `cinematic_camera_movement.py:13-17`; `cinematic_renderer_pipeline.py:85-86`; `depth_estimator.py:1-23`; `config.py:45`; empirical filter reproduction against `scene_01_beat_01.png`.

### 1.15 Render Quality (encoder/profile) — 8/10 when reached

**Implementation:** `render_profile_registry.py:19-35` — CRF18, `medium` preset, `yuv420p`, `bt709`, AAC 48kHz — genuinely good "visually-lossless master" defaults. `cinematic_transition.py` implements real `xfade` crossfades, not hard cuts.

**Observed:** GOP check on `2898c8d4` (first 150 frames) shows healthy standard IBP structure, no encoder pathology. Both 1080p runs hit 5.4–5.8 Mbps, consistent with CRF18. **This part of the pipeline is genuinely solid and needs no rework** — its low real-world impact is entirely a symptom of §1.16, not a defect of its own.
**Root cause:** None — validates positively. **Priority:** none (do not touch).

### 1.16 Resolution / 1080p delivery — 3/10

**Implementation:** `render_profile_registry.py` defines a single `youtube_long` profile (1920×1080/30/CRF18), which `RendererPipeline._render_scene_clip` forces deterministically whenever that code path executes.

**Observed:** Only **2 of 6** real runs (`eeeb8edd`, `2898c8d4`, both post 2026-07-21 ~22:51) are true 1920×1080/30fps. The other 4 — **including `7a99e839`, generated 2026-07-22 19:42, nineteen hours after the 1080p rewrite existed on disk** — are 1024×1024/24fps at 221–546 kbps, far below any usable YouTube quality bar.

**Root cause investigation:** `backend/services/cinematic_renderer_pipeline.py`, `render_profile_registry.py`, `video_assembly_service.py`, `render_profile_encoders.py`, `youtube_production_workflow.py` and their tests are **all untracked in git** (`git status` → `??`), with filesystem mtimes clustered at 2026-07-21 21:11–22:51. Only one production entry point exists (`backend/api/v1/production.py`); there is no legacy second workflow. The most consistent explanation: a long-lived `uvicorn` worker process was never restarted after this rewrite landed, so it kept serving requests (like `7a99e839`) from its stale in-memory import of the pre-rewrite module graph, which defaulted to native 1024×1024/24fps with no forced resolution. (No `backend.log` entries exist for 2026-07-22 to trace `7a99e839`'s request directly — this is a well-supported inference from process lifecycle and mtime evidence, not a 100%-confirmed trace.)

**Root cause:** **A) Bug** — process-lifecycle/deployment staleness, compounded by the entire rendering rewrite never having been committed to version control.
**Effort:** Small (restart discipline / commit the code / add a module-load-time health check) to Medium (guarantee-restart deploy step). **Improvement if fixed:** 3→9 — would make the already-good 1080p profile (§1.15) universal for near-zero engineering cost.
**Evidence:** ffprobe table (all 6 runs); `git status --short` (untracked rendering files); filesystem mtimes.

### 1.17 Voice Quality — 6/10

**Implementation:** `openai_text_to_speech_provider.py:68-74` calls `client.audio.speech.create(model=, voice=, input=, speed=, instructions=)`. No `response_format` or channel/sample-rate param exists on this OpenAI API at all. Model: `gpt-4o-mini-tts`, voice: `onyx`.

**Observed:** ffprobe on both real `voice.mp3` files, **before** any mixing: mono, 48000Hz, 64000bps CBR — confirmed identical in the muxed `video.mp4` audio stream. Bitrate math confirms this is native API output, not a downstream re-encode: `2,935,725 B × 8 / 366.9s ≈ 64.0 kbps`, exact match to the ffprobe-reported bitrate. `audio_mixer_service.py` has zero `-ac`/`channel_layout` references anywhere — mono is not introduced by the mixer.

**Root cause:** **D) AI Model/API Limitation** — OpenAI's `audio.speech.create` has no channel parameter; mono+CBR64 is native to `gpt-4o-mini-tts`.
**Effort:** Medium (provider swap or stereo-widening post-process — the latter is cosmetic, not a real fidelity gain since the source is mono at generation). **Improvement if fixed:** +1 (technical spec only).
**Evidence:** ffprobe on `voice.mp3`/`video.mp4` for both real runs; `openai_text_to_speech_provider.py:68-74`; zero `-ac` matches in `audio_mixer_service.py`.

### 1.18 Voice Expressiveness — 6/10

**Implementation:** `voice_profiles.py` defines 7 static profiles with hand-written `instructions` strings, resolved **once per whole script**, not per scene/beat (`voice_generation_service.py:40`). `voice_direction_planner.py:21-34`'s own docstring states: *"F28 (AI Director) is expected to add an LLM-driven implementation of this interface later"* — it never did, despite F28 being marked "COMPLETED" in `PROJECT_STATE.md`.

**Observed:** F28's actual scope, confirmed against `PROJECT_STATE.md`, was `TimelinePlan + CompositionPlan` only — voice direction was never included, so the same static instructions apply uniformly across ~458s of narration regardless of scene tone shifts (climax vs. setup get identical delivery instructions).

**Root cause:** **B) Missing Feature** — the interface was explicitly designed to be swapped for an AI-Director-driven implementation; that swap never happened.
**Effort:** Medium (interface already exists; needs an LLM-driven planner + per-segment instruction splitting, mirroring what F28 did for `TimelinePlan`). **Improvement if fixed:** +2–3 — **the highest-leverage audio fix identified, since the interface is already built and waiting.**
**Evidence:** `voice_direction_planner.py:21-34`; `voice_generation_service.py:40`; `PROJECT_STATE.md` F28 scope description.

### 1.19 Background Music — 1/10

**Implementation:** `local_audio_library_provider.py:60-86` does keyword-matched selection from `settings.music_library_root` (default `"assets/audio/music"`), gated by `audio_engine_service.py:98-111`, which short-circuits if `background_music_enabled` is False or no match is found.

**Observed:** `background_music_enabled: bool = False` by default (`config.py:78`), **not overridden anywhere** for either real full run (zero music-related log lines in `mansa_musa_run.log`). Additionally, **`assets/audio/music` does not exist on disk at all** — even with the flag flipped on, matching would return `None` and the feature would silently skip by design. This is a double gap: config default + empty asset library. Every real production run to date has narration-only audio.

**Root cause:** **B) Missing Feature** in practice (no asset library exists) compounded by a config default that suppresses it even once content exists.
**Effort:** Small (flip flag) / Large (source and organize a real royalty-free music library). **Improvement if fixed:** +4–5 — **one of the largest single perceived-production-value levers identified in this audit.**
**Evidence:** `config.py:78,80`; absence of `assets/audio/music` on disk; zero music log lines in `mansa_musa_run.log`.

### 1.20 Sound Effects — 1/10

**Implementation:** Identical pattern to Background Music — `LocalSoundEffectLibraryProvider`, gated by `sound_effects_enabled` (`config.py:79`, default False), root `assets/audio/sfx`.

**Observed:** Same double gap — flag off by default, directory doesn't exist, zero SFX log activity in `mansa_musa_run.log`.

**Root cause:** **B) Missing Feature** (empty library) + config default.
**Effort:** Small (flag) / Large (source/tag a real CC0 SFX library). **Improvement if fixed:** +2–3.
**Evidence:** `config.py:79,81`; absence of `assets/audio/sfx`; zero SFX log lines.

### 1.21 Audio Mixing — 7/10 (code quality) / unvalidated in production

**Implementation:** `audio_mixer_service.py:108-172` builds a real, non-trivial ffmpeg `filter_complex`: per-source volume/fade/delay, `sidechaincompress` ducking under narration, `amix`, master fade, `loudnorm=I=-14.0:TP=-1.5:LRA=11`.

**Observed:** `volumedetect` on both real runs: mean −14.4dB, max 0.0dB (identical mastering curve, matches the loudnorm target). `silencedetect` at −30dB/0.5s shows only natural sentence-boundary pauses — clean single-track concatenation, no structural dead air. **But because music/SFX inputs are always empty (§1.19–1.20), `stream_labels` never exceeds 1, so `amix`/`sidechaincompress` never execute in any real run** — the mixer degenerates to "narration → master fade → loudnorm." The sophisticated multi-track/ducking logic exists, looks sound, and has **zero real-world executions**.

**Root cause:** **F) Architecture Limitation** (downstream consequence of §1.19/1.20 — not a defect in the mixer itself).
**Effort:** None for the mixer; entirely dependent on §1.19/1.20 shipping. **Improvement if fixed:** 0 direct — the gain lives in §1.19/1.20, unlocking this dormant, already-tested code path for free.
**Evidence:** `volumedetect`/`silencedetect` on both real runs; `audio_mixer_service.py:108-172`.

### 1.22 Overall Cinematic Feeling — ~3–4/10 (composite)

No run in `storage/runs/` currently represents "the pipeline working as designed" end-to-end. The two runs that hit 1080p (§1.16) both carry the aspect-ratio stretch defect (§1.14) on every frame and have no music/SFX (§1.19–1.20) and no character consistency (§1.10). The four runs without the stretch/resolution issues also never had 1080p or the current render profile. **The gap between "premium documentary" and current output is concentrated in a small number of root causes that touch many categories at once** (see Executive Summary).

---

## 2. Prioritized Backlog

| ID | Finding | Priority | Difficulty | Expected ROI | Quality Δ | Cost impact | Risk |
|---|---|---|---|---|---|---|---|
| FND-01 | 1080p delivery unreliable (stale server process / uncommitted code) | **Critical** | Small | Very High | 3→9 | None | Low |
| FND-02 | Anamorphic stretch: square source force-resized to 16:9 with no crop-to-fill | **Critical** | Medium | Very High | 3→8 | None | Low–Medium (touches 8 movement builders + tests) |
| FND-03 | No character/reference consistency across image generations | **Critical** | Large | Very High | 3→7–8 | Possible per-image cost increase (reference conditioning) | Medium |
| FND-04 | Music/SFX off by default + asset libraries don't exist on disk | **Critical** | Small (flag) / Large (content) | Very High | 1→5–6 | Licensing cost for a real library | Low |
| FND-05 | Review has no quality gate; `review.md` never persisted; `script.md` is stale vs. actual narration | **Critical** (observability) / High (gate) | Small–Medium | High | 4→7 | None | Low |
| FND-06 | No persistence of AI Director / Composition / Timeline plan JSON | High | Small | High | n/a (unblocks measurement) | None | Low |
| FND-12 | Camera movement/shot selection not actually AI-Director-driven despite F28 claim | High | Medium | High | 6→8 | LLM call cost per shot | Medium |
| FND-11 | Image generation always requests square 1024×1024, ignoring available widescreen sizes | High | Medium | High | (feeds FND-02) | Marginal (larger images cost slightly more) | Low |
| FND-07 | Scene Planning ignores Writer's own scene markers; fixed 8-scene split, no narrative weighting | High | Medium | High | 5→7 | None | Low |
| FND-10 | Voice expressiveness stuck on static per-script instructions; interface ready but unused | Medium | Medium | High | 6→8–9 | LLM call cost per segment | Low |
| FND-08 | Composition Planning beat counts cluster at the hard ceiling, not the stated target | Medium | Medium | Medium–High | 6→8–9 | None (same budget) | Low |
| FND-13 | Historical consistency: landmark geometry drifts; garbled on-image text | Medium | Medium | Medium | 5→7–8 | None | Low |
| FND-14 | Occasional multi-panel image collage failures, no validation/re-roll | Medium | Small | High | 7→8–9 | +1 re-roll cost on failure only | Low |
| FND-15 | Thumbnail character design mismatches body images | Medium (High if bundled with FND-03) | Small (once FND-03 lands) | High | 7→9–10 | None extra | Low |
| FND-09 | Transition variety collapses to 2 render-level types vs. 6 planned energies | Medium | Large | Medium | 7→9 | None | Medium |
| FND-12b | Cost preview stale (pre-visual-beats formula, ~3–4× undercounts real image spend); no aggregate per-run cost logged | High | Small–Medium | High (governance) | n/a | None | Low |
| FND-19 | Voice mono/64kbps ceiling (OpenAI TTS API native limit) | Low–Medium | Medium | Low–Medium | 6→7 | Possible provider-switch cost | Medium |
| FND-16 | Agent-ID resolution anti-pattern (literal-UUID probe before slug lookup) causes noisy always-on DB errors | Low | Small | Medium | n/a (log hygiene) | None | Low |
| FND-17 | "Timeline Planning" invisible as a discrete telemetry stage | Low | Small | Low–Medium | n/a (observability) | None | Low |
| FND-18 | Script hook/CTA phrasing formulaic across unrelated topics | Low | Small | Low–Moderate | 8→9 | None | Low |
| — | Render encoder/profile itself (CRF18/AAC48k/GOP) | — | — | — | Already 8/10 — **do not rework** | — | — |
| — | Script factual grounding/prose quality | — | — | — | Already 8/10 — **do not rework** | — | — |
| — | AI Director / Visual Beats duration-weighting core logic | — | — | — | Already 7–8/10 — **do not rework** | — | — |

**Recommended implementation order** (highest ROI-per-effort, unblock-first):

1. **FND-01** (restart/commit rendering code) — trivial fix, single largest quality jump available.
2. **FND-06** (persist AI Director/Composition plan JSON) — near-zero cost, unblocks validating everything else.
3. **FND-05 observability half** (persist `review.md`, log real scores) — near-zero cost, same reason.
4. **FND-02** (crop-to-fill before zoompan) — fixes a defect present on every frame of every good run.
5. **FND-04 flag flip + minimal starter library** — cheapest large perceptual win available.
6. **FND-11** (widescreen image sizing) — cheap, directly reduces the material FND-02 has to compensate for.
7. **FND-03** (character consistency) — largest single quality lever, but correctly sequenced after the cheaper wins above since it's the most expensive to build.
8. Everything else, in priority order above.

---

## 3. Feature Assignment (F30–F35)

### F30 — Production Quality Validation (this feature: bugs, config, observability, validation gaps)
- FND-01 — 1080p delivery unreliable (stale process / uncommitted code)
- FND-02 — Anamorphic stretch bug (also cross-assigned to F32 for the camera-movement-filter rework)
- FND-04 — Music/SFX disabled-by-default config gap (content sourcing itself is F33)
- FND-05 — Review quality-gate + persistence gap
- FND-06 — AI Director/Composition/Timeline plan persistence gap
- FND-07 — Scene Planning/Writer scene-marker disconnect (flag here; fix work is F34)
- FND-08 — Composition Planning beat-count clustering (flag here; prompt fix is F34)
- FND-12b — Stale cost estimate + missing aggregate cost logging
- FND-16 — Agent-ID resolution anti-pattern (noisy errors)
- FND-17 — Timeline Planning telemetry invisibility
- FND-18 — Formulaic script hook/CTA phrasing (flag here; prompt fix is F34)

### F31 — Photorealistic Visual Engine
- FND-03 — Character/reference consistency (centerpiece of this feature)
- FND-11 — Widescreen-aware image size requests
- FND-13 — Historical/landmark consistency + on-image text reliability
- FND-14 — Multi-panel collage detection/re-roll
- FND-15 — Thumbnail/body character alignment (shares fix with FND-03)
- FND-10 — Voice expressiveness (AI-Director-driven voice direction) — cross-assigned, see F33

### F32 — Cinematic Camera Language
- FND-02 — Aspect-ratio crop-to-fill rework inside the zoompan filter chain
- FND-09 — Renderable transition-type variety (expand beyond dissolve/fadeblack)
- FND-12 — Wire AI Director output into shot/camera-movement selection

### F33 — Premium Audio Experience
- FND-04 — Music/SFX asset library sourcing and tagging (the "build the content" half)
- FND-10 — AI-Director-driven voice direction planner implementation
- FND-19 — Voice fidelity ceiling (provider evaluation for stereo/higher-bitrate narration)
- FND-21 (audio mixing dormancy) — no code change needed; validates automatically once FND-04 ships

### F34 — Production Polish
- FND-07 — Narrative-weight-aware scene duration allocation
- FND-08 — Composition Planning prompt rework toward the stated target rather than the ceiling
- FND-18 — Script hook/CTA phrasing variety

### F35 — Automated Publishing
- No findings from this audit map here — correctly deferred; publishing automation should not begin until the Critical/High items above are resolved, since automating distribution of a video with FND-01–FND-04 present would scale the defects, not the quality.

---

## 4. Executive Summary

**Why does the current output not yet look like a premium documentary?**
Not because the architecture is wrong — F25–F29 are real, and several of their core mechanisms (AI Director reasoning, visual-beat duration weighting, the render encoder profile, script prose quality) demonstrably work when exercised. The gap is concentrated in a small number of root causes that each touch several of the 21 evaluated categories simultaneously: (1) the 1080p render path is not reliably reached in production (FND-01), (2) every frame of every run that *does* reach 1080p is visibly stretched because square 1024×1024 source images are force-resized into 16:9 with no crop-to-fill step (FND-02, FND-11), (3) there is no mechanism to keep a recurring character's appearance consistent across shots or between the thumbnail and the body (FND-03, FND-15), and (4) background music and sound effects are off by default with no asset library on disk, so every real production to date is narration-only despite F26 documentation describing "professional mixing and mastering" (FND-04). Fix these four families and the composite "Overall Cinematic Feeling" score should move from ~3–4 to ~7–8 without any architectural redesign.

**What are the highest-ROI improvements?**
In order: FND-01 (restart/commit — near-zero effort, fixes the majority of "why does this look bad" complaints), FND-06/FND-05 (persist intermediate plan JSON and review output — near-zero effort, unblocks validating everything downstream), FND-04's flag flip (near-zero effort, large perceptual gain the moment even a small starter music library exists), FND-02 (medium effort, fixes a defect on literally every frame of the only good runs), and FND-03 (the most expensive fix, but the single largest quality lever in the whole audit).

**Which improvements are bugs?** FND-01 (stale process/uncommitted code), FND-02 (stretch instead of crop), FND-05's agent-lookup half, FND-12b's stale cost formula, FND-16 (noisy agent-resolution errors).

**Which require new features?** FND-03 (character consistency — needs reference-image conditioning), FND-05's quality-gate half, FND-06 (plan persistence), FND-09 (more renderable transition types), FND-10 (AI-Director-driven voice direction), FND-12 (AI-Director-driven shot selection), FND-14 (image validation/re-roll), FND-19 (voice fidelity, if pursued via provider change).

**Which are prompt-only?** FND-08 (composition beat-count target vs. ceiling), FND-18 (hook/CTA phrasing variety), and partially FND-07 (a prompt-side mitigation is possible before the fuller architectural fix).

**Which require changing AI providers (or accepting a hard model limitation)?** FND-19 (voice is mono/64kbps because OpenAI's `audio.speech.create` has no channel parameter — this is a genuine ceiling, not a bug) and part of FND-13 (on-image text rendering reliability is a diffusion-model limitation, not something prompt-tuning alone fixes).

**Which require architecture work?** FND-02 and FND-03 both require touching core rendering/generation call chains (not just config or prompts); FND-07's full fix (narrative-weight-aware scene allocation) and FND-21's dormant multi-track mixing (already built, just unreachable) round these out.

**What should be implemented first?** The six-step order in §2: (1) FND-01, (2) FND-06, (3) FND-05's observability half, (4) FND-02, (5) FND-04's flag + starter library, (6) FND-11, before moving to the larger FND-03 build. This sequencing fixes the cheapest, highest-leverage issues first, restores the ability to validate future work with real evidence (closing the exact gap this F30 audit had to work around), and defers the most expensive item (FND-03, character consistency) to last among the Critical-priority items — not because it matters less, but because it's correctly sequenced after the near-free wins.

**On the $5/documentary cost target:** this cannot currently be verified from real evidence. The only cost figure ever logged (`$0.38` estimated image cost) uses a pre-F28B formula that undercounts real image volume by roughly 3–4×, and no run persists an aggregate total across LLM + image + TTS spend (FND-12b). Closing this gap should be treated as a prerequisite for any future F31–F35 work that might change per-image or per-call costs (particularly FND-03's likely per-image cost increase from reference conditioning).
