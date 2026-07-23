from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file.
    
    Uses Pydantic v2 model_config (ConfigDict) instead of deprecated class Config.
    Loads from .env file in project root.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        extra="ignore",  # Ignore unknown environment variables
        case_sensitive=False,  # Allow lowercase env var names
    )
    
    app_name: str = "Jarvis API"
    app_version: str = "0.1.0"
    debug: bool = False
    supabase_url: str | None = None
    supabase_key: str | None = None
    cors_allowed_origins: list[str] = ["http://localhost:3000"]
    trusted_hosts: list[str] = ["*"]
    gzip_minimum_size: int = 500
    hsts_header: str = "max-age=31536000; includeSubDomains"
    default_llm_provider: str = "openai"
    default_llm_model: str = "gpt-5.5"
    openai_api_key: str | None = None
    openai_api_base: str | None = None
    openai_api_version: str | None = None
    default_embedding_provider: str = "openai"
    openai_embedding_model: str = "text-embedding-3-small"
    brave_search_api_key: str | None = None
    brave_search_timeout_seconds: float = 15.0
    youtube_oauth_client_id: str | None = None
    youtube_oauth_client_secret: str | None = None
    youtube_oauth_refresh_token: str | None = None
    youtube_oauth_token_uri: str = "https://oauth2.googleapis.com/token"
    workflow_output_root: str = r"D:\Jarvis\Videos"
    run_storage_root: str = "storage/runs"
    image_provider: str = "openai"
    tts_provider: str = "openai"
    stt_provider: str = "openai"
    openai_image_model: str = "gpt-image-1"
    # F31 Photorealistic Visual Engine: native landscape generation. gpt-image-1
    # supports 1024x1024, 1024x1536, and 1536x1024 — every previous production
    # requested the square size unconditionally, forcing the renderer to crop/stretch
    # square stills into the 16:9 output container (see docs/F30_PRODUCTION_QUALITY_REPORT.md
    # §1.14). 1536x1024 is the closest native option to 16:9 and needs no renderer
    # change (F32 remains untouched) — the image itself now arrives already
    # oriented for cinematic framing instead of being corrected after the fact.
    openai_image_size: str = "1536x1024"
    # Production default is "medium", not "high": image generation is the largest
    # single API expense in the production workflow (see cost audit), and "high"
    # quality is ~4x the per-image cost of "medium" for no reliably-visible gain
    # in a slideshow-style video. Still fully overridable via the OPENAI_IMAGE_QUALITY
    # env var / .env for anyone who deliberately wants the higher tier.
    openai_image_quality: str = "medium"
    # F31 Photorealistic Visual Engine — Visual Identity: one shared HistoricalVisualContext
    # plus canonical CharacterVisualIdentity per recurring figure, built once per production
    # from the finalized research/script and reused by every scene/beat/thumbnail prompt.
    # Manual operator override; the real safety net is VisualIdentityService's own
    # automatic fallback to an empty (no-op) context on any failure — CompositionPromptEnricher
    # and ThumbnailGenerationService already treat an empty context as "no identity guidance",
    # identical to pre-F31 behavior.
    visual_identity_enabled: bool = True
    # F31 Character Consistency: generate one canonical reference portrait per detected
    # recurring figure. Bounded so a script with many named people never turns into an
    # unbounded number of extra paid image calls.
    character_reference_images_enabled: bool = True
    max_characters_per_video: int = 3
    # F31 Image Validation: after each generation, one cheap vision-model classification
    # call checks for obvious generation failures (multi-panel/split-screen composition,
    # garbled/unreadable text, broken anatomy, other obvious artifacts) and triggers at
    # most one regeneration attempt. Fails open (treats a validator outage as "valid")
    # so a QA-call failure never blocks the pipeline — the same fallback discipline every
    # other optional stage in this pipeline already follows.
    image_validation_enabled: bool = True
    image_validation_model: str = "gpt-5.5"
    image_validation_max_retries: int = 1
    # F26 Audio Engine — gpt-4o-mini-tts replaces tts-1/alloy: same provider/client,
    # but its `instructions` parameter is the first delivery-style control this
    # pipeline has ever had (see docs/F26_ARCHITECTURE_PROPOSAL.md). These two
    # remain the raw provider defaults/manual override; VoiceGenerationService
    # normally sources model/voice/pace from the selected VoiceProfile instead.
    openai_tts_model: str = "gpt-4o-mini-tts"
    openai_tts_voice: str = "onyx"
    openai_tts_speed: float = 1.0
    openai_stt_model: str = "whisper-1"
    ffmpeg_binary: str = "ffmpeg"
    # Selects the VoiceProfile (backend/services/voice_profiles.py) VoiceGenerationService
    # asks DeterministicVoiceDirectionPlanner to resolve. Adding a profile is a registry
    # entry, not a code change — see VOICE_PROFILES.
    voice_profile: str = "documentary_male"
    # Narration Processing: a single ffmpeg loudnorm pass on the raw TTS output so every
    # narration track starts from a consistent level before mixing. Local/free.
    narration_normalization_enabled: bool = True
    narration_target_lufs: float = -16.0
    # Audio Engine master toggle. When False, AudioEngineStep is skipped entirely and
    # Video Assembly falls back to the raw (normalized) narration track untouched —
    # same fallback discipline as cinematic rendering falling back to the slideshow.
    audio_engine_enabled: bool = True
    # Background music/SFX ship as real, tested interfaces (MusicGenerationProvider,
    # SoundEffectProvider) with a local-library implementation, but default OFF since
    # no asset library ships with this repository — flip these on once a library is
    # populated under the paths below. Music/SFX must always remain optional.
    background_music_enabled: bool = False
    sound_effects_enabled: bool = False
    music_library_root: str = "assets/audio/music"
    sound_effect_library_root: str = "assets/audio/sfx"
    audio_music_volume_db: float = -18.0
    # Final mix mastering target. -14 LUFS is YouTube's own loudness normalization
    # reference, so videos aren't further turned down/up on playback.
    audio_master_loudness_lufs: float = -14.0
    audio_master_fade_in_seconds: float = 1.0
    audio_master_fade_out_seconds: float = 2.0
    # F25 Cinematic Video Engine — all local ffmpeg rendering, zero added API cost.
    # cinematic_rendering_enabled is a manual operator override; the real safety net is
    # VideoAssemblyService's automatic fallback to the legacy slideshow path on any
    # cinematic-rendering failure (unsupported filter, timeout, non-zero exit).
    cinematic_rendering_enabled: bool = True
    # F28A: output resolution (and every other technical rendering/export
    # parameter) is now owned exclusively by RenderProfile — see
    # backend/schemas/render_profile.py and render_profile_name below.
    cinematic_transition_style: str = "dissolve"  # "dissolve" | "fadeblack"
    cinematic_transition_duration_seconds: float = 0.6
    # None = no atmosphere overlay applied ("only when instructed"); one of
    # AtmosphereOverlayType's values (e.g. "film_grain") to force one on every video.
    cinematic_default_atmosphere_overlay: str | None = None
    # Hard ceiling on scenes generated per video. The LLM's own scene count must
    # never be the thing that decides how many paid gpt-image-1 calls get made —
    # this is what makes per-video image cost predictable regardless of how the
    # model breaks down the script. Enforced in both ScenePlanningService (asks
    # for exactly this many, trims if it returns more) and
    # SceneImageGenerationService (final safety layer, independent of Scene
    # Planning's own trimming).
    max_scenes_per_video: int = 8
    # Two-tier safety threshold for scene counts, on top of max_scenes_per_video:
    #   count <= max_scenes_per_video        -> used as-is
    #   max_scenes_per_video < count <= this  -> trimmed to max_scenes_per_video,
    #                                            logged as a warning (normal LLM
    #                                            overshoot, not a bug)
    #   count > this                          -> WorkflowSafetyError, run aborts
    #                                            before the first paid request
    #                                            (likely a prompt/workflow bug,
    #                                            not something to silently absorb)
    # LLM output is never trusted to self-limit; production cost must stay
    # deterministic and under application control, not the model's. Image
    # generation is the largest API expense in this pipeline, so this is the
    # single most important cost guardrail in the workflow.
    max_scene_hard_limit: int = 50
    # F28 AI Director — single creative authority for TimelinePlan/CompositionPlan.
    # The real safety net is CompositionPlanningService's automatic fallback to the
    # deterministic F27 planners on any AI Director unavailability/validation
    # failure; this is a manual operator override, same role
    # cinematic_rendering_enabled/audio_engine_enabled already play.
    ai_director_enabled: bool = True
    ai_director_genre: str = "documentary"
    # F28A Render Profiles — the single named selector for every technical
    # rendering/export parameter (see backend/services/render_profile_registry.py).
    # An unrecognized/empty name resolves to the default "youtube_long" profile —
    # existing productions keep working automatically with no config change.
    render_profile_name: str = "youtube_long"
    # F28B Adaptive Visual Storytelling Engine — configured production budget and
    # visual-beat guardrails. The AI Director must never invent its own cost
    # limits or beat counts; these are the single source of truth it reasons
    # against (see AIDirectorRequest) and the only ceiling
    # ai_director_plan_builder.clamp_visual_beats_per_scene()/
    # enforce_visual_beat_budget() enforce afterward — mirroring
    # max_scenes_per_video's guardrail role above, one layer deeper (per-scene
    # image count instead of per-video scene count). SceneImageGenerationService's
    # existing safety net scales its hard ceiling by maximum_visual_beats_per_scene
    # so beat-expanded productions aren't silently truncated back to one image per
    # scene.
    maximum_video_budget_usd: float = 5.0
    target_video_budget_usd: float = 4.0
    maximum_image_budget_usd: float = 3.0
    target_image_budget_usd: float = 2.0
    # minimum/target are prompt guidance only — never force-padded with invented
    # beats. maximum is a hard ceiling, enforced in code regardless of what the AI
    # Director returns.
    minimum_visual_beats_per_scene: int = 1
    target_visual_beats_per_scene: int = 2
    maximum_visual_beats_per_scene: int = 4


settings = Settings()
