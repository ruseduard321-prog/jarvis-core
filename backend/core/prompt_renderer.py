from __future__ import annotations

import string
from typing import Any

from backend.core.prompt_exceptions import PromptTemplateRenderingError, PromptTemplateValidationError
from backend.core.prompt_models import PromptMessage, PromptTemplate


class PromptTemplateRenderer:
    """Render prompt templates with variable interpolation and validation."""

    def __init__(self, template: PromptTemplate) -> None:
        self.template = template

    @staticmethod
    def _collect_placeholders(text: str) -> set[str]:
        placeholders: set[str] = set()
        for _, field_name, _, _ in string.Formatter().parse(text):
            if field_name is None or field_name == "":
                continue
            if "." in field_name:
                field_name = field_name.split(".")[0]
            if "[" in field_name:
                field_name = field_name.split("[")[0]
            placeholders.add(field_name)
        return placeholders

    def _validate_variables(self, variables: dict[str, Any]) -> None:
        required = set()
        for message in self.template.messages:
            required.update(self._collect_placeholders(message.content))

        missing = [name for name in sorted(required) if name not in variables]
        if missing:
            raise PromptTemplateValidationError(
                f"Missing required prompt variables: {', '.join(missing)}"
            )

    def render(self, variables: dict[str, Any]) -> list[PromptMessage]:
        self._validate_variables(variables)

        rendered_messages: list[PromptMessage] = []
        for message in self.template.messages:
            try:
                rendered_text = message.content.format(**variables)
            except KeyError as exc:
                raise PromptTemplateRenderingError(
                    f"Failed to render prompt message: missing variable {exc.args[0]}"
                ) from exc
            except Exception as exc:
                raise PromptTemplateRenderingError(
                    "Failed to render prompt message"
                ) from exc

            rendered_messages.append(
                PromptMessage(
                    role=message.role,
                    content=rendered_text,
                    name=message.name,
                    metadata=message.metadata,
                )
            )

        return rendered_messages
