from __future__ import annotations

from backend.core.event_bus_service import EventBusService
from backend.core.prompt_models import Prompt, PromptCategory
from backend.core.prompt_store import PromptStore


class PromptLibraryService:
    """Service layer for user prompt library CRUD operations with event publishing."""

    def __init__(self, store: PromptStore, event_bus_service: EventBusService) -> None:
        self._store = store
        self._event_bus_service = event_bus_service

    async def create_prompt(
        self,
        name: str,
        content: str,
        category: PromptCategory,
    ) -> Prompt:
        """Create a new prompt."""
        prompt = await self._store.create_prompt(name, content, category)
        await self._event_bus_service.publish_event(
            "PromptCreated",
            payload=self._serialize_prompt(prompt),
            metadata={"prompt_id": prompt.id},
        )
        return prompt

    async def read_prompt(self, prompt_id: str) -> Prompt:
        """Get a prompt by ID."""
        return await self._store.read_prompt(prompt_id)

    async def update_prompt(
        self,
        prompt_id: str,
        name: str | None = None,
        content: str | None = None,
        category: PromptCategory | None = None,
        favorite: bool | None = None,
    ) -> Prompt:
        """Update a prompt."""
        prompt = await self._store.update_prompt(prompt_id, name, content, category, favorite)
        await self._event_bus_service.publish_event(
            "PromptUpdated",
            payload=self._serialize_prompt(prompt),
            metadata={"prompt_id": prompt.id},
        )
        return prompt

    async def delete_prompt(self, prompt_id: str) -> None:
        """Delete a prompt."""
        await self._store.delete_prompt(prompt_id)
        await self._event_bus_service.publish_event(
            "PromptDeleted",
            payload={"id": prompt_id},
            metadata={"prompt_id": prompt_id},
        )

    async def list_prompts(self) -> list[Prompt]:
        """List all prompts."""
        return await self._store.list_prompts()

    @staticmethod
    def _serialize_prompt(prompt: Prompt) -> dict:
        """Serialize prompt for event payload."""
        return {
            "id": prompt.id,
            "name": prompt.name,
            "content": prompt.content,
            "category": prompt.category.value,
            "favorite": prompt.favorite,
            "created_at": prompt.created_at.isoformat(),
            "updated_at": prompt.updated_at.isoformat(),
        }
