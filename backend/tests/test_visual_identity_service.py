from __future__ import annotations

import json
from datetime import datetime

import pytest

from backend.core.config import Settings
from backend.models.agent import Agent
from backend.schemas.research import ResearchPackage, ReviewedScript
from backend.services.visual_identity_service import VisualIdentityService


def _agent(agent_id: str, slug: str, is_active: bool = True) -> Agent:
    now = datetime(2026, 1, 1)
    return Agent(
        id=agent_id, slug=slug, owner_user_id="system", name=slug, mission="test",
        is_active=is_active, created_at=now, updated_at=now,
    )


class FakeConversation:
    class _Context:
        conversation_id = "conv-1"

    context = _Context()


class FakeConversationEngine:
    async def create_conversation(self, title=None, metadata=None):
        return FakeConversation()


class FakeAgentRuntime:
    def __init__(self, content: str | None = None, raises: Exception | None = None):
        self._content = content
        self._raises = raises
        self.called_with: dict | None = None

    async def execute(self, **kwargs):
        self.called_with = kwargs
        if self._raises:
            raise self._raises
        return {"content": self._content}


class FakeAgentService:
    def __init__(self, agents: list[Agent] | None = None):
        self._agents = agents or []

    async def get_agent(self, agent_id: str) -> Agent:
        raise KeyError(agent_id)

    async def list_agents(self, active_only: bool = True) -> list[Agent]:
        return [agent for agent in self._agents if agent.is_active] if active_only else self._agents


def _research_package() -> ResearchPackage:
    return ResearchPackage(
        topic="Mansa Musa",
        executive_summary="summary",
        key_facts=["Mansa Musa ruled the Mali Empire", "He made a famous pilgrimage to Mecca"],
        recommended_angle="angle",
    )


def _reviewed_script(text: str = "Mansa Musa rode across the desert with his caravan.") -> ReviewedScript:
    return ReviewedScript(
        topic="Mansa Musa", revised_script=text, quality_score=90.0, readability_score=90.0,
        engagement_score=90.0, status="success",
    )


_VALID_RESPONSE = json.dumps(
    {
        "historical_context": {
            "time_period": "14th century",
            "geography": "West Africa, Mali Empire",
            "architecture": "mudbrick minarets",
            "materials": "",
            "clothing": "flowing robes",
            "weapons_and_tools": "",
            "symbols_and_landmarks": "",
            "vegetation": "",
            "weather_and_atmosphere": "",
            "culture_notes": "",
            "color_palette": "",
        },
        "characters": [
            {
                "name": "Mansa Musa",
                "aliases": ["the king"],
                "role": "protagonist",
                "face_description": "a calm, dignified expression",
                "hair": "short black hair, trimmed beard",
                "skin_tone": "deep brown",
                "clothing": "cream robes trimmed in gold",
                "accessories": "a simple gold crown",
                "body_build": "tall and upright",
                "age_appearance": "middle-aged",
                "distinguishing_features": "",
            }
        ],
        "status": "success",
    }
)


def _service(agent_runtime: FakeAgentRuntime, settings: Settings | None = None) -> VisualIdentityService:
    return VisualIdentityService(
        conversation_engine=FakeConversationEngine(),
        agent_runtime=agent_runtime,
        agent_service=FakeAgentService(agents=[_agent("agent-1", "media")]),
        settings=settings or Settings(),
    )


@pytest.mark.asyncio
async def test_execute_parses_historical_context_and_characters():
    service = _service(FakeAgentRuntime(content=_VALID_RESPONSE))

    context = await service.execute(
        research_package=_research_package(), reviewed_script=_reviewed_script(), user_id="user-1"
    )

    assert context.metadata["status"] == "success"
    assert context.historical_context.time_period == "14th century"
    assert context.historical_context.architecture == "mudbrick minarets"
    assert len(context.characters) == 1
    assert context.characters[0].name == "Mansa Musa"
    assert context.characters[0].aliases == ["the king"]


@pytest.mark.asyncio
async def test_execute_returns_empty_context_when_disabled():
    service = _service(FakeAgentRuntime(content=_VALID_RESPONSE), settings=Settings(visual_identity_enabled=False))

    context = await service.execute(research_package=_research_package(), reviewed_script=_reviewed_script(), user_id=None)

    assert context.metadata["status"] == "skipped"
    assert context.characters == []
    assert context.historical_context.is_empty()


@pytest.mark.asyncio
async def test_execute_returns_empty_context_when_script_is_unusable():
    service = _service(FakeAgentRuntime(content=_VALID_RESPONSE))

    context = await service.execute(
        research_package=_research_package(), reviewed_script=_reviewed_script(""), user_id=None
    )

    assert context.metadata["status"] == "skipped"


@pytest.mark.asyncio
async def test_execute_returns_empty_context_when_no_agent_available():
    service = VisualIdentityService(
        conversation_engine=FakeConversationEngine(),
        agent_runtime=FakeAgentRuntime(content=_VALID_RESPONSE),
        agent_service=FakeAgentService(agents=[]),
        settings=Settings(),
    )

    context = await service.execute(research_package=_research_package(), reviewed_script=_reviewed_script(), user_id=None)

    assert context.metadata["status"] == "skipped"


@pytest.mark.asyncio
async def test_execute_returns_empty_context_on_invalid_json():
    service = _service(FakeAgentRuntime(content="not json"))

    context = await service.execute(research_package=_research_package(), reviewed_script=_reviewed_script(), user_id=None)

    assert context.metadata["status"] == "skipped"
    assert context.characters == []


@pytest.mark.asyncio
async def test_execute_bounds_character_count_to_max_characters_per_video():
    many_characters = json.dumps(
        {
            "historical_context": {},
            "characters": [
                {"name": f"Figure {i}", "aliases": [], "role": "", "face_description": "", "hair": "",
                 "skin_tone": "", "clothing": "", "accessories": "", "body_build": "", "age_appearance": "",
                 "distinguishing_features": ""}
                for i in range(5)
            ],
        }
    )
    service = _service(FakeAgentRuntime(content=many_characters), settings=Settings(max_characters_per_video=2))

    context = await service.execute(research_package=_research_package(), reviewed_script=_reviewed_script(), user_id=None)

    assert len(context.characters) == 2


@pytest.mark.asyncio
async def test_execute_skips_character_entries_without_a_name():
    response = json.dumps({"historical_context": {}, "characters": [{"name": ""}, {"name": "Named Figure"}]})
    service = _service(FakeAgentRuntime(content=response))

    context = await service.execute(research_package=_research_package(), reviewed_script=_reviewed_script(), user_id=None)

    assert [character.name for character in context.characters] == ["Named Figure"]
