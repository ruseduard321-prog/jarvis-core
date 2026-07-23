from __future__ import annotations

from backend.core.config import Settings
from backend.schemas.assets import Scene, ScenePlan, ScenePrompt, ScenePromptSet
from backend.schemas.composition import VisualBeat
from backend.schemas.visual_identity import CharacterVisualIdentity, HistoricalVisualContext
from backend.services.composition_planner import DeterministicCompositionPlanner
from backend.services.composition_prompt_enricher import CompositionPromptEnricher
from backend.services.timeline_planner import DeterministicTimelinePlanner


def _composition_plan(scene_plan: ScenePlan, total_duration_seconds: float = 30.0):
    timeline_plan = DeterministicTimelinePlanner(Settings()).plan(
        scene_plan=scene_plan, total_duration_seconds=total_duration_seconds
    )
    return DeterministicCompositionPlanner().plan(scene_plan=scene_plan, timeline_plan=timeline_plan)


def test_enrich_appends_composition_phrase_to_existing_prompt():
    scene_plan = ScenePlan(topic="Test", scenes=[Scene(scene_number=1)])
    composition_plan = _composition_plan(scene_plan)
    scene_prompts = ScenePromptSet(topic="Test", prompts=[ScenePrompt(scene_number=1, prompt="A dark forest clearing")])

    enriched = CompositionPromptEnricher().enrich(scene_prompts=scene_prompts, composition_plan=composition_plan)

    assert enriched.prompts[0].prompt.startswith("A dark forest clearing")
    assert "cinematic 16:9 composition" in enriched.prompts[0].prompt
    assert "no on-image text" in enriched.prompts[0].prompt


def test_enrich_handles_empty_original_prompt():
    scene_plan = ScenePlan(topic="Test", scenes=[Scene(scene_number=1)])
    composition_plan = _composition_plan(scene_plan)
    scene_prompts = ScenePromptSet(topic="Test", prompts=[ScenePrompt(scene_number=1, prompt="")])

    enriched = CompositionPromptEnricher().enrich(scene_prompts=scene_prompts, composition_plan=composition_plan)

    assert enriched.prompts[0].prompt.strip() != ""


def test_enrich_leaves_prompt_unchanged_when_scene_not_covered_by_plan():
    scene_plan = ScenePlan(topic="Test", scenes=[Scene(scene_number=1)])
    composition_plan = _composition_plan(scene_plan)
    scene_prompts = ScenePromptSet(
        topic="Test",
        prompts=[ScenePrompt(scene_number=1, prompt="Scene one"), ScenePrompt(scene_number=2, prompt="Scene two")],
    )

    enriched = CompositionPromptEnricher().enrich(scene_prompts=scene_prompts, composition_plan=composition_plan)

    assert enriched.prompts[1].prompt == "Scene two"


def test_enrich_includes_continuity_tags_when_present():
    scene_plan = ScenePlan(
        topic="Test",
        scenes=[
            Scene(scene_number=1, narration="An ancient lighthouse stood on the cliff."),
            Scene(scene_number=2, narration="The lighthouse appeared again through the fog."),
        ],
    )
    composition_plan = _composition_plan(scene_plan)
    scene_prompts = ScenePromptSet(
        topic="Test",
        prompts=[ScenePrompt(scene_number=1, prompt="A cliff at dusk"), ScenePrompt(scene_number=2, prompt="A foggy cliff")],
    )

    enriched = CompositionPromptEnricher().enrich(scene_prompts=scene_prompts, composition_plan=composition_plan)

    second_prompt = enriched.prompts[1].prompt
    assert "lighthouse" in second_prompt
    assert "maintain visual continuity" in second_prompt


def test_enrich_does_not_mutate_the_original_scene_prompt_set():
    scene_plan = ScenePlan(topic="Test", scenes=[Scene(scene_number=1)])
    composition_plan = _composition_plan(scene_plan)
    scene_prompts = ScenePromptSet(topic="Test", prompts=[ScenePrompt(scene_number=1, prompt="Original")])

    CompositionPromptEnricher().enrich(scene_prompts=scene_prompts, composition_plan=composition_plan)

    assert scene_prompts.prompts[0].prompt == "Original"


def test_enrich_expands_one_prompt_per_visual_beat():
    scene_plan = ScenePlan(topic="Test", scenes=[Scene(scene_number=1)])
    composition_plan = _composition_plan(scene_plan)
    composition_plan = composition_plan.model_copy(
        update={
            "scenes": [
                composition_plan.scenes[0].model_copy(
                    update={
                        "visual_beats": [
                            VisualBeat(beat_number=1, description="the ship leaves the dock"),
                            VisualBeat(beat_number=2, description="crowd waves goodbye"),
                        ]
                    }
                )
            ]
        }
    )
    scene_prompts = ScenePromptSet(topic="Test", prompts=[ScenePrompt(scene_number=1, prompt="Titanic departure")])

    enriched = CompositionPromptEnricher().enrich(scene_prompts=scene_prompts, composition_plan=composition_plan)

    assert len(enriched.prompts) == 2
    assert all(prompt.scene_number == 1 for prompt in enriched.prompts)
    assert [prompt.beat_number for prompt in enriched.prompts] == [1, 2]
    assert "the ship leaves the dock" in enriched.prompts[0].prompt
    assert "crowd waves goodbye" in enriched.prompts[1].prompt
    assert "Titanic departure" in enriched.prompts[0].prompt
    assert "Titanic departure" in enriched.prompts[1].prompt


def test_enrich_produces_a_single_prompt_with_beat_number_zero_when_no_beats():
    scene_plan = ScenePlan(topic="Test", scenes=[Scene(scene_number=1)])
    composition_plan = _composition_plan(scene_plan)
    scene_prompts = ScenePromptSet(topic="Test", prompts=[ScenePrompt(scene_number=1, prompt="A calm harbor")])

    enriched = CompositionPromptEnricher().enrich(scene_prompts=scene_prompts, composition_plan=composition_plan)

    assert len(enriched.prompts) == 1
    assert enriched.prompts[0].beat_number == 0


def test_enrich_produces_photorealistic_documentary_language():
    scene_plan = ScenePlan(topic="Test", scenes=[Scene(scene_number=1)])
    composition_plan = _composition_plan(scene_plan)
    scene_prompts = ScenePromptSet(topic="Test", prompts=[ScenePrompt(scene_number=1, prompt="A dark forest clearing")])

    enriched = CompositionPromptEnricher().enrich(scene_prompts=scene_prompts, composition_plan=composition_plan)

    prompt = enriched.prompts[0].prompt
    assert "photojournalistic documentary photography" in prompt
    assert "not an illustration" in prompt.lower()


def test_enrich_injects_historical_context_when_provided():
    scene_plan = ScenePlan(topic="Test", scenes=[Scene(scene_number=1)])
    composition_plan = _composition_plan(scene_plan)
    scene_prompts = ScenePromptSet(topic="Test", prompts=[ScenePrompt(scene_number=1, prompt="A desert caravan")])
    historical_context = HistoricalVisualContext(time_period="14th century", architecture="mudbrick minarets")

    enriched = CompositionPromptEnricher().enrich(
        scene_prompts=scene_prompts, composition_plan=composition_plan, historical_context=historical_context
    )

    assert "14th century" in enriched.prompts[0].prompt
    assert "mudbrick minarets" in enriched.prompts[0].prompt


def test_enrich_locks_matched_character_appearance_into_prompt():
    scene_plan = ScenePlan(topic="Test", scenes=[Scene(scene_number=1, narration="Mansa Musa rides west.")])
    composition_plan = _composition_plan(scene_plan)
    scene_prompts = ScenePromptSet(
        topic="Test", prompts=[ScenePrompt(scene_number=1, prompt="Mansa Musa crosses the desert")]
    )
    character = CharacterVisualIdentity(name="Mansa Musa", clothing="cream robes trimmed in gold")

    enriched = CompositionPromptEnricher().enrich(
        scene_prompts=scene_prompts, composition_plan=composition_plan, characters=[character]
    )

    assert "cream robes trimmed in gold" in enriched.prompts[0].prompt
    assert "maintain this exact appearance" in enriched.prompts[0].prompt


def test_enrich_does_not_lock_appearance_when_no_character_matches():
    scene_plan = ScenePlan(topic="Test", scenes=[Scene(scene_number=1)])
    composition_plan = _composition_plan(scene_plan)
    scene_prompts = ScenePromptSet(topic="Test", prompts=[ScenePrompt(scene_number=1, prompt="An empty desert horizon")])
    character = CharacterVisualIdentity(name="Mansa Musa", clothing="cream robes trimmed in gold")

    enriched = CompositionPromptEnricher().enrich(
        scene_prompts=scene_prompts, composition_plan=composition_plan, characters=[character]
    )

    assert "cream robes trimmed in gold" not in enriched.prompts[0].prompt


def test_enrich_uses_scene_environment_and_lighting_when_scene_plan_given():
    scene = Scene(scene_number=1, environment="a torch-lit royal court", lighting="warm flickering torchlight")
    scene_plan = ScenePlan(topic="Test", scenes=[scene])
    composition_plan = _composition_plan(scene_plan)
    scene_prompts = ScenePromptSet(topic="Test", prompts=[ScenePrompt(scene_number=1, prompt="The king holds court")])

    enriched = CompositionPromptEnricher().enrich(
        scene_prompts=scene_prompts, composition_plan=composition_plan, scene_plan=scene_plan
    )

    prompt = enriched.prompts[0].prompt
    assert "a torch-lit royal court" in prompt
    assert "warm flickering torchlight" in prompt
