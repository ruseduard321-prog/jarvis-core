from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from backend.core.config import Settings
from backend.core.cost_tracker import BudgetTracker
from backend.services.image_validation_service import ImageValidationService


class FakeOpenAIProvider:
    def __init__(self, client) -> None:
        self._client = client

    async def get_client(self):
        return self._client


def _client_returning(content: str):
    async def _create(**kwargs):
        message = SimpleNamespace(content=content)
        choice = SimpleNamespace(message=message)
        return SimpleNamespace(choices=[choice])

    return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=_create)))


def _client_raising(exc: Exception):
    async def _create(**kwargs):
        raise exc

    return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=_create)))


@pytest.mark.asyncio
async def test_validate_returns_valid_when_model_reports_no_issues():
    content = json.dumps({"valid": True, "issues": [], "reason": "single coherent shot"})
    service = ImageValidationService(openai_llm_provider=FakeOpenAIProvider(_client_returning(content)), settings=Settings())

    result = await service.validate(image_bytes=b"fake-bytes", context="a ship at sea")

    assert result.valid is True
    assert result.issues == []
    assert result.estimated_cost_usd > 0.0


@pytest.mark.asyncio
async def test_validate_returns_invalid_with_issues_when_model_flags_defects():
    content = json.dumps({"valid": False, "issues": ["multi-panel composition"], "reason": "split into three panels"})
    service = ImageValidationService(openai_llm_provider=FakeOpenAIProvider(_client_returning(content)), settings=Settings())

    result = await service.validate(image_bytes=b"fake-bytes", context="a ship at sea")

    assert result.valid is False
    assert result.issues == ["multi-panel composition"]
    assert result.reason == "split into three panels"


@pytest.mark.asyncio
async def test_validate_fails_open_when_provider_call_raises():
    service = ImageValidationService(
        openai_llm_provider=FakeOpenAIProvider(_client_raising(RuntimeError("network error"))), settings=Settings()
    )

    result = await service.validate(image_bytes=b"fake-bytes", context="a ship at sea")

    assert result.valid is True
    assert result.reason == "validation_unavailable"


@pytest.mark.asyncio
async def test_validate_fails_open_when_response_is_not_json():
    service = ImageValidationService(
        openai_llm_provider=FakeOpenAIProvider(_client_returning("not json")), settings=Settings()
    )

    result = await service.validate(image_bytes=b"fake-bytes", context="a ship at sea")

    assert result.valid is True
    assert result.reason == "validation_unavailable"


@pytest.mark.asyncio
async def test_validate_short_circuits_when_disabled_by_settings():
    service = ImageValidationService(
        openai_llm_provider=FakeOpenAIProvider(_client_raising(RuntimeError("should not be called"))),
        settings=Settings(image_validation_enabled=False),
    )

    result = await service.validate(image_bytes=b"fake-bytes", context="a ship at sea")

    assert result.valid is True
    assert result.reason == "validation_disabled"


@pytest.mark.asyncio
async def test_validate_skips_call_and_fails_open_when_budget_exhausted():
    service = ImageValidationService(
        openai_llm_provider=FakeOpenAIProvider(_client_raising(RuntimeError("should not be called"))),
        settings=Settings(),
    )
    budget = BudgetTracker(remaining_usd=0.0)

    result = await service.validate(image_bytes=b"fake-bytes", context="a ship at sea", budget_tracker=budget)

    assert result.valid is True
    assert result.reason == "validation_skipped_budget_exhausted"
    assert result.estimated_cost_usd == 0.0


@pytest.mark.asyncio
async def test_validate_records_spend_on_budget_tracker_after_a_real_call():
    content = json.dumps({"valid": True, "issues": [], "reason": "fine"})
    service = ImageValidationService(openai_llm_provider=FakeOpenAIProvider(_client_returning(content)), settings=Settings())
    budget = BudgetTracker(remaining_usd=1.0)

    result = await service.validate(image_bytes=b"fake-bytes", context="a ship at sea", budget_tracker=budget)

    assert budget.remaining_usd == pytest.approx(1.0 - result.estimated_cost_usd)


@pytest.mark.asyncio
async def test_validate_does_not_touch_budget_when_none_supplied():
    content = json.dumps({"valid": True, "issues": [], "reason": "fine"})
    service = ImageValidationService(openai_llm_provider=FakeOpenAIProvider(_client_returning(content)), settings=Settings())

    result = await service.validate(image_bytes=b"fake-bytes", context="a ship at sea")

    assert result.estimated_cost_usd > 0.0
