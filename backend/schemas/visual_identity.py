from __future__ import annotations

import re

from pydantic import BaseModel, Field

_WORD_PATTERN = re.compile(r"[A-Za-z']+")


class HistoricalVisualContext(BaseModel):
    """F31: one shared visual-continuity anchor for an entire production, built once
    from the finalized research/script and reused by every scene/beat/thumbnail
    prompt. Purely descriptive guidance — it never times or plans anything, mirroring
    how SceneRetention/ContinuityMotif are guidance-only. Every field is optional text
    (empty means 'no guidance for this facet'), so a partially-populated context still
    degrades gracefully rather than blocking prompt enrichment."""

    time_period: str = Field(default="", description="Era/date range this production is set in")
    geography: str = Field(default="", description="Real-world region/location the visuals should reflect")
    architecture: str = Field(default="", description="Recurring building/structure style and materials")
    materials: str = Field(default="", description="Recurring physical materials/textures (stone, bronze, cloth, etc.)")
    clothing: str = Field(default="", description="Recurring clothing/costume conventions for the period and culture")
    weapons_and_tools: str = Field(default="", description="Recurring weapons, tools, or instruments of the period")
    symbols_and_landmarks: str = Field(default="", description="Recurring symbols, emblems, or real landmarks")
    vegetation: str = Field(default="", description="Recurring plant life/terrain cover")
    weather_and_atmosphere: str = Field(default="", description="Recurring weather/atmospheric conditions")
    culture_notes: str = Field(default="", description="Recurring cultural conventions relevant to the visuals")
    color_palette: str = Field(default="", description="Recurring dominant color palette for the production")

    def as_prompt_fragment(self) -> str:
        """Joins every non-empty field into one flowing descriptive clause. Field
        order is deliberate: setting first (time/place), then built environment,
        then people/objects, then atmosphere/color — a natural documentary
        photographer's mental checklist."""
        parts: list[str] = []
        if self.time_period:
            parts.append(f"set in {self.time_period}")
        if self.geography:
            parts.append(f"in {self.geography}")
        if self.architecture:
            parts.append(f"architecture: {self.architecture}")
        if self.materials:
            parts.append(f"materials: {self.materials}")
        if self.clothing:
            parts.append(f"period-accurate clothing: {self.clothing}")
        if self.weapons_and_tools:
            parts.append(f"period-accurate weapons/tools: {self.weapons_and_tools}")
        if self.symbols_and_landmarks:
            parts.append(f"recurring symbols/landmarks: {self.symbols_and_landmarks}")
        if self.vegetation:
            parts.append(f"vegetation: {self.vegetation}")
        if self.weather_and_atmosphere:
            parts.append(f"atmosphere: {self.weather_and_atmosphere}")
        if self.culture_notes:
            parts.append(f"cultural detail: {self.culture_notes}")
        if self.color_palette:
            parts.append(f"color palette: {self.color_palette}")
        return ", ".join(parts)

    def is_empty(self) -> bool:
        return not self.as_prompt_fragment()


class CharacterVisualIdentity(BaseModel):
    """F31: one recurring historical figure's canonical visual identity, generated
    once per production and reused verbatim across every scene/beat/thumbnail that
    depicts them — the centerpiece mechanism for eliminating character drift. Text
    fields are the provider-agnostic consistency anchor (work with any text-to-image
    provider); `reference_image_filename` is an optional stronger anchor a provider
    MAY use for image-conditioned generation when it supports it (see
    ImageGenerationProvider.generate_image's `reference_image` parameter) — its
    absence never blocks prompt-based consistency."""

    name: str = Field(description="Canonical name this figure is referred to by")
    aliases: list[str] = Field(default_factory=list, description="Other names/titles this figure is referred to by in the script")
    role: str = Field(default="", description="This figure's role in the story, e.g. 'protagonist', 'king'")
    face_description: str = Field(default="", description="Face shape, expression, notable features")
    hair: str = Field(default="", description="Hair color, style, length, facial hair")
    skin_tone: str = Field(default="", description="Skin tone")
    clothing: str = Field(default="", description="Canonical outfit worn across scenes")
    accessories: str = Field(default="", description="Canonical accessories: crown, jewelry, weapons, tools")
    body_build: str = Field(default="", description="Build/posture/height impression")
    age_appearance: str = Field(default="", description="Apparent age")
    distinguishing_features: str = Field(default="", description="Any other single distinguishing visual trait")
    reference_image_filename: str = Field(
        default="", description="Filename of this character's generated canonical reference portrait, once created"
    )

    def as_prompt_fragment(self) -> str:
        parts = [f"{self.name}"]
        if self.age_appearance:
            parts.append(f"a {self.age_appearance}")
        if self.body_build:
            parts.append(self.body_build)
        if self.face_description:
            parts.append(f"face: {self.face_description}")
        if self.skin_tone:
            parts.append(f"skin tone: {self.skin_tone}")
        if self.hair:
            parts.append(f"hair: {self.hair}")
        if self.clothing:
            parts.append(f"wearing {self.clothing}")
        if self.accessories:
            parts.append(f"with {self.accessories}")
        if self.distinguishing_features:
            parts.append(self.distinguishing_features)
        return ", ".join(parts)

    def reference_portrait_prompt(self, historical_context: "HistoricalVisualContext | None" = None) -> str:
        """Prompt for this character's own canonical reference portrait: a neutral,
        single-subject studio-lit reference so later scene generations (or
        image-conditioned edits, when a provider supports them) have one clean
        anchor to match rather than a busy scene composition."""
        context_fragment = historical_context.as_prompt_fragment() if historical_context else ""
        parts = [
            f"Studio reference portrait of {self.as_prompt_fragment()}",
            context_fragment,
            "neutral plain background, centered composition, eye-level angle, 85mm portrait lens, soft even studio "
            "lighting, sharp focus on the face, photorealistic documentary character reference sheet",
        ]
        return ", ".join(part for part in parts if part)

    def _search_terms(self) -> list[str]:
        return [self.name, *self.aliases]

    def matches(self, text: str) -> bool:
        """Deterministic whole-word, case-insensitive match of this character's
        name/aliases against a scene/beat description — the same keyword-matching
        discipline CompositionPlanner._detect_motifs already uses for continuity
        tags, applied to character identity instead of generic nouns."""
        if not text:
            return False
        haystack_words = {word.lower() for word in _WORD_PATTERN.findall(text)}
        for term in self._search_terms():
            term_words = [word.lower() for word in _WORD_PATTERN.findall(term)]
            if term_words and all(word in haystack_words for word in term_words):
                return True
        return False


class VisualIdentityContext(BaseModel):
    """F31: bundle of everything Visual Identity produces for one production —
    the single object CompositionPromptEnricher/ThumbnailGenerationService/
    SceneImageGenerationService consume to keep every generated image visually
    consistent with the same historical setting and the same recurring figures."""

    topic: str = Field(description="Original topic")
    historical_context: HistoricalVisualContext = Field(default_factory=HistoricalVisualContext)
    characters: list[CharacterVisualIdentity] = Field(default_factory=list)
    metadata: dict[str, object] = Field(default_factory=dict, description="Execution metadata including status")

    def character_for(self, text: str) -> CharacterVisualIdentity | None:
        """First character whose name/alias matches somewhere in `text`, or None.
        First-match (not best-match) is deliberate: characters are few (bounded by
        _MAX_CHARACTERS) and a beat depicting two named figures at once is rare;
        keeping this deterministic and simple avoids a scoring mechanism no caller
        needs yet."""
        for character in self.characters:
            if character.matches(text):
                return character
        return None
