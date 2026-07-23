from __future__ import annotations

import json
from datetime import datetime

import pytest

from backend.core.config import Settings
from backend.models.agent import Agent
from backend.schemas.ai_director import AIDirectorRequest
from backend.schemas.assets import Scene
from backend.services.ai_director_provider import (
    AgentRuntimeAIDirectorProvider,
    AIDirectorUnavailableError,
    AIDirectorValidationError,
)


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
    def __init__(self, agents: list[Agent] | None = None, get_agent_raises: bool = True):
        self._agents = agents or []
        self._get_agent_raises = get_agent_raises

    async def get_agent(self, agent_id: str) -> Agent:
        if self._get_agent_raises:
            raise KeyError(agent_id)
        for agent in self._agents:
            if agent.id == agent_id:
                return agent
        raise KeyError(agent_id)

    async def list_agents(self, active_only: bool = True) -> list[Agent]:
        return [agent for agent in self._agents if agent.is_active] if active_only else self._agents


def _request(count: int = 2) -> AIDirectorRequest:
    return AIDirectorRequest(
        topic="Test Topic",
        narration_script="Full narration text.",
        scenes=[Scene(scene_number=i) for i in range(1, count + 1)],
        total_duration_seconds=20.0,
    )


_VALID_RESPONSE = json.dumps(
    {
        "scenes": [
            {
                "scene_number": 1,
                "duration_seconds": 1.0,
                "pacing": "standard",
                "purpose": "introduction",
                "composition_style": "establishing_shot",
                "camera_intent": "neutral_observation",
            },
            {
                "scene_number": 2,
                "duration_seconds": 1.0,
                "pacing": "breathing",
                "purpose": "resolution",
                "composition_style": "wide_shot",
                "camera_intent": "emotional_focus",
            },
        ],
        "motifs": [],
    }
)


@pytest.mark.asyncio
async def test_direct_raises_unavailable_when_no_agent_resolvable():
    provider = AgentRuntimeAIDirectorProvider(
        conversation_engine=FakeConversationEngine(),
        agent_runtime=FakeAgentRuntime(content=_VALID_RESPONSE),
        agent_service=FakeAgentService(agents=[], get_agent_raises=True),
        settings=Settings(),
    )

    with pytest.raises(AIDirectorUnavailableError):
        await provider.direct(request=_request(), user_id=None)


@pytest.mark.asyncio
async def test_direct_resolves_agent_via_fallback_slug_list():
    agent_runtime = FakeAgentRuntime(content=_VALID_RESPONSE)
    provider = AgentRuntimeAIDirectorProvider(
        conversation_engine=FakeConversationEngine(),
        agent_runtime=agent_runtime,
        agent_service=FakeAgentService(agents=[_agent("agent-1", "creation")], get_agent_raises=True),
        settings=Settings(),
    )

    plan = await provider.direct(request=_request(), user_id=None)

    assert len(plan.scenes) == 2
    assert agent_runtime.called_with["agent_id"] == "agent-1"


@pytest.mark.asyncio
async def test_direct_parses_valid_json_into_ai_director_plan():
    provider = AgentRuntimeAIDirectorProvider(
        conversation_engine=FakeConversationEngine(),
        agent_runtime=FakeAgentRuntime(content=_VALID_RESPONSE),
        agent_service=FakeAgentService(agents=[_agent("agent-1", "media")], get_agent_raises=True),
        settings=Settings(),
    )

    plan = await provider.direct(request=_request(), user_id="user-1")

    assert [scene.scene_number for scene in plan.scenes] == [1, 2]
    assert plan.scenes[0].purpose.value == "introduction"


@pytest.mark.asyncio
async def test_direct_raises_validation_error_on_unparseable_content():
    provider = AgentRuntimeAIDirectorProvider(
        conversation_engine=FakeConversationEngine(),
        agent_runtime=FakeAgentRuntime(content="not json at all"),
        agent_service=FakeAgentService(agents=[_agent("agent-1", "media")], get_agent_raises=True),
        settings=Settings(),
    )

    with pytest.raises(AIDirectorValidationError):
        await provider.direct(request=_request(), user_id=None)


@pytest.mark.asyncio
async def test_direct_raises_validation_error_on_invalid_enum_value():
    bad_response = json.dumps(
        {
            "scenes": [
                {
                    "scene_number": 1,
                    "duration_seconds": 1.0,
                    "pacing": "not-a-real-pacing",
                    "purpose": "introduction",
                    "composition_style": "establishing_shot",
                    "camera_intent": "neutral_observation",
                }
            ]
        }
    )
    provider = AgentRuntimeAIDirectorProvider(
        conversation_engine=FakeConversationEngine(),
        agent_runtime=FakeAgentRuntime(content=bad_response),
        agent_service=FakeAgentService(agents=[_agent("agent-1", "media")], get_agent_raises=True),
        settings=Settings(),
    )

    with pytest.raises(AIDirectorValidationError):
        await provider.direct(request=_request(count=1), user_id=None)


@pytest.mark.asyncio
async def test_direct_raises_unavailable_when_agent_runtime_execute_fails():
    provider = AgentRuntimeAIDirectorProvider(
        conversation_engine=FakeConversationEngine(),
        agent_runtime=FakeAgentRuntime(raises=RuntimeError("network error")),
        agent_service=FakeAgentService(agents=[_agent("agent-1", "media")], get_agent_raises=True),
        settings=Settings(),
    )

    with pytest.raises(AIDirectorUnavailableError):
        await provider.direct(request=_request(), user_id=None)


@pytest.mark.asyncio
async def test_direct_extracts_json_embedded_in_prose():
    wrapped = f"Here is the plan:\n{_VALID_RESPONSE}\nHope this helps!"
    provider = AgentRuntimeAIDirectorProvider(
        conversation_engine=FakeConversationEngine(),
        agent_runtime=FakeAgentRuntime(content=wrapped),
        agent_service=FakeAgentService(agents=[_agent("agent-1", "media")], get_agent_raises=True),
        settings=Settings(),
    )

    plan = await provider.direct(request=_request(), user_id=None)
    assert len(plan.scenes) == 2
