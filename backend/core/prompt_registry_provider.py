from __future__ import annotations

from backend.core.prompt_registry import PromptRegistry
from backend.core.prompt_store import InMemoryPromptStore


prompt_template_store = InMemoryPromptStore()
prompt_registry = PromptRegistry(prompt_template_store)
