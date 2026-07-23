from __future__ import annotations

from backend.schemas.composition import CameraIntent, ColorLanguage, CompositionStyle
from backend.schemas.visual_identity import CharacterVisualIdentity, HistoricalVisualContext

# F31 Photorealistic Prompt Engine. Deterministic string templating — the same
# discipline CompositionPromptEnricher's old _STYLE_PHRASES already used — expanded
# from one generic style clause into the full documentary-photographer checklist:
# subject/action, environment, historical context, character identity, camera
# angle/framing/focal length/lens, depth of field, lighting, atmosphere, color
# palette, and an explicit photographic-realism directive. No LLM call, no added
# cost, no new provider — this only changes the prompt text SceneImageGenerationService
# and ThumbnailGenerationService already send to ImageGenerationProvider.

_FRAMING_PHRASES: dict[CompositionStyle, str] = {
    CompositionStyle.ESTABLISHING_SHOT: (
        "wide establishing aerial or landscape shot, 24mm wide-angle lens, deep focus holding "
        "foreground through background sharp"
    ),
    CompositionStyle.WIDE_SHOT: "wide documentary shot with generous negative space, 35mm lens, deep depth of field",
    CompositionStyle.CLOSE_UP: (
        "tight close-up framing, 85mm portrait telephoto lens, shallow depth of field with soft "
        "background blur"
    ),
    CompositionStyle.DETAIL_SHOT: (
        "macro detail shot isolating one focal object, 100mm macro lens, extremely shallow depth of field"
    ),
    CompositionStyle.REVEAL_SHOT: (
        "slow-reveal composition, 50mm lens, a staged foreground element gradually giving way to the subject"
    ),
    CompositionStyle.COMPARISON_SHOT: (
        "balanced symmetrical composition comparing two elements side by side, 35mm lens, even deep focus"
    ),
    CompositionStyle.REACTION_SHOT: (
        "intimate handheld-style close framing on emotional reaction, 50mm lens, shallow depth of field"
    ),
    CompositionStyle.TRANSITION_SHOT: (
        "transitional wide-to-medium composition bridging to the next scene, 35mm lens, natural depth of field"
    ),
}

_CAMERA_INTENT_PHRASES: dict[CameraIntent, str] = {
    CameraIntent.SLOW_REVEAL: "patient, deliberate camera position implying a slow reveal",
    CameraIntent.DRAMATIC_ZOOM: "dramatic tight framing implying a punch-in zoom",
    CameraIntent.INVESTIGATION: "observational documentary framing, as if the camera is investigating the scene",
    CameraIntent.SUSPENSE: "tense, slightly off-center framing that withholds visual information",
    CameraIntent.EMOTIONAL_FOCUS: "framing centered tightly on emotional presence",
    CameraIntent.NEUTRAL_OBSERVATION: "steady, neutral observational framing",
}

_COLOR_LANGUAGE_PHRASES: dict[ColorLanguage, str] = {
    ColorLanguage.NEUTRAL: "natural balanced color grade",
    ColorLanguage.WARM_PROGRESSION: "warm golden-hour color grade",
    ColorLanguage.COLD_PROGRESSION: "cool desaturated color grade",
    ColorLanguage.TENSION: "high-contrast tense color grade with deep shadows",
}

# Kept verbatim from the pre-F31 phrase set: the final render container is still
# 16:9 regardless of the F31 native-landscape source size (1536x1024 is close to
# but not exactly 16:9), so this instruction still matters.
_FRAMING_BASE_PHRASE = "cinematic 16:9 composition, safe margins, no on-image text"

# The explicit realism directive F31 requires: push toward documentary photography
# and away from illustration/painting/concept-art/fantasy-art language, which the
# pre-F31 generic prompt never addressed at all.
_REALISM_SUFFIX = (
    "shot on a full-frame digital cinema camera, photojournalistic documentary photography, "
    "physically accurate photographic realism, realistic skin and material textures, natural "
    "volumetric lighting, true-to-life color science, color-graded like a modern feature-length "
    "historical documentary film. Not an illustration, not a painting, not concept art, not "
    "fantasy art, not a digital render — a real photograph."
)


class PhotorealisticPromptBuilder:
    """Stateless prompt template assembler. One `build()` call produces one final
    image-generation prompt string from every structured signal the pipeline has
    already decided (composition, camera, color, continuity) plus F31's new visual
    identity signals (historical context, canonical character identity)."""

    def build(
        self,
        *,
        subject_and_action: str,
        composition_style: CompositionStyle,
        camera_intent: CameraIntent,
        color_language: ColorLanguage = ColorLanguage.NEUTRAL,
        environment: str = "",
        lighting: str = "",
        mood: str = "",
        continuity_tags: list[str] | None = None,
        historical_context: HistoricalVisualContext | None = None,
        character: CharacterVisualIdentity | None = None,
    ) -> str:
        parts: list[str] = []

        subject = subject_and_action.strip()
        if subject:
            parts.append(subject)

        if character is not None:
            parts.append(
                f"featuring {character.as_prompt_fragment()} — maintain this exact appearance, "
                "face, hair, skin tone, clothing, and accessories consistently"
            )

        if environment.strip():
            parts.append(f"environment: {environment.strip()}")

        if historical_context is not None and not historical_context.is_empty():
            parts.append(historical_context.as_prompt_fragment())

        parts.append(_FRAMING_PHRASES[composition_style])
        parts.append(_CAMERA_INTENT_PHRASES[camera_intent])

        lighting_clause = lighting.strip()
        color_clause = _COLOR_LANGUAGE_PHRASES[color_language]
        parts.append(f"lighting: {lighting_clause}, {color_clause}" if lighting_clause else color_clause)

        if mood.strip():
            parts.append(f"mood: {mood.strip()}")

        if continuity_tags:
            parts.append("maintain visual continuity with recurring " + ", ".join(continuity_tags))

        parts.append(_FRAMING_BASE_PHRASE)
        parts.append(_REALISM_SUFFIX)

        return ", ".join(part for part in parts if part) + "."
