from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncIterator, Callable

from backend.core.conversation_engine import ConversationEngine
from backend.core.conversation_models import ConversationMessage, ConversationRole
from backend.core.llm_models import LLMMessage, LLMRequest
from backend.core.llm_provider import LLMProvider
from backend.core.config import settings
from backend.core.workflow_engine import WorkflowEngine
from backend.core.workflow_engine_models import WorkflowDefinition
from backend.core.workflow_history_store import WorkflowHistoryStore
from backend.services.youtube_production_workflow import WORKFLOW_ID

logger = logging.getLogger(__name__)


class WorkflowManager:
    """Detects free-form chat requests that ask for a complete, finished piece of content
    and executes the matching registered `WorkflowDefinition` via the generic `WorkflowEngine`,
    streaming progress in the same SSE event shape the normal chat stream already uses.
    Adding a new workflow means adding one entry to `workflow_factories` — no dispatch logic
    changes."""

    def __init__(
        self,
        llm_provider: LLMProvider,
        conversation_engine: ConversationEngine,
        workflow_engine: WorkflowEngine,
        workflow_factories: dict[str, Callable[[], WorkflowDefinition]],
        workflow_history_store: WorkflowHistoryStore,
    ) -> None:
        self._llm_provider = llm_provider
        self._conversation_engine = conversation_engine
        self._workflow_engine = workflow_engine
        self._workflow_factories = workflow_factories
        self._workflow_history_store = workflow_history_store

    async def detect(self, message: str) -> dict[str, Any] | None:
        """Best-effort classification of whether this message requests a complete,
        production-ready deliverable. Any failure (model error, invalid JSON) yields
        None, which the caller must treat as "not a workflow" — never blocks normal chat."""
        prompt = (
            "Decide whether the user's request asks for a COMPLETE, finished piece of "
            "long-form content to be produced end-to-end (e.g. \"create a video about X\", "
            "\"write a full script and publishing package for X\"), or whether it is a "
            "normal conversational message (a question, a short task, or a simple lookup "
            "with no request for a finished script/video/publishing package).\n\n"
            'Respond with STRICT JSON only: {"is_full_production": true|false, "topic": "<string>", "reason": "<short string>"}\n\n'
            "Rules:\n"
            "- is_full_production=true ONLY when the user clearly wants a finished, "
            "production-ready deliverable, not just information or a short answer.\n"
            "- topic: a concise subject string suitable as a research topic, extracted "
            "from the request (e.g. \"Dyatlov Pass Incident\"). Empty string if not applicable.\n\n"
            f"User request: {message}"
        )
        parsed = await self._run_json_classification(prompt)
        if not parsed or not isinstance(parsed.get("is_full_production"), bool):
            return None
        if not parsed["is_full_production"]:
            return {"is_full_production": False}

        topic = str(parsed.get("topic") or "").strip() or message
        return {
            "is_full_production": True,
            "workflow_id": WORKFLOW_ID,
            "topic": topic,
            "reason": str(parsed.get("reason", "")),
        }

    async def stream_execute(
        self,
        *,
        conversation_id: str,
        message: str,
        topic: str,
        user_id: str | None,
        workflow_id: str = WORKFLOW_ID,
    ) -> AsyncIterator[dict[str, str]]:
        execution_id = str(uuid.uuid4())

        user_message = ConversationMessage(
            id=str(uuid.uuid4()),
            role=ConversationRole.USER,
            content=message,
            created_at=datetime.utcnow(),
            metadata={"workflow": "full_production", "execution_id": execution_id},
        )
        await self._conversation_engine.append_message(conversation_id, user_message)
        yield {"event": "start", "message_id": user_message.id}

        factory = self._workflow_factories.get(workflow_id)
        if factory is None:
            assistant_message = await self._finish_failed(conversation_id, "workflow_selection", f"Unknown workflow: {workflow_id}")
            yield {"event": "end", "message_id": assistant_message.id}
            return

        definition = factory()
        result: dict[str, Any] | None = None
        async for event in self._workflow_engine.stream_execute(
            definition, topic=topic, conversation_id=conversation_id, user_id=user_id
        ):
            if event["type"] == "progress":
                yield {"event": "token", "data": event["text"]}
            else:
                result = event["result"]

        if result is None or result.get("status") == "failed":
            failed_step = (result or {}).get("failed_step", "unknown")
            reason = (result or {}).get("error", "unknown reason")
            assistant_message = await self._finish_failed(conversation_id, failed_step, reason)
            yield {"event": "end", "message_id": assistant_message.id}
            return

        export_validation_reason = self._read_export_validation_failure(result["output_folder"])
        if export_validation_reason is not None:
            await self._workflow_history_store.record_failed(result["execution_id"], "Export Validation")
            assistant_message = await self._finish_failed(conversation_id, "Export Validation", export_validation_reason)
            yield {"event": "end", "message_id": assistant_message.id}
            return

        final_text = (
            f"Production complete. Files exported to: {result['output_folder']}\n\n"
            f"Artifacts: {', '.join(result['files_written'])}"
        )
        assistant_message = ConversationMessage(
            id=str(uuid.uuid4()),
            role=ConversationRole.ASSISTANT,
            content=final_text,
            created_at=datetime.utcnow(),
            metadata={
                "workflow": "full_production",
                "execution_id": result["execution_id"],
                "step_status": result["step_statuses"],
                "output_folder": result["output_folder"],
                "status": "success",
            },
        )
        await self._conversation_engine.append_message(conversation_id, assistant_message)
        yield {"event": "end", "message_id": assistant_message.id}

    def _read_export_validation_failure(self, output_folder: str) -> str | None:
        """Re-reads summary.json — written last by WorkflowExporter.export() — to catch
        the export-validation failures the engine's "success" event can't see (the engine
        always reports success once every step completes; WorkflowExporter is what actually
        determines the durable SUCCESS/FAILED status). Returns None when the export passed
        validation or summary.json is unreadable (never blocks a good run on a read glitch)."""
        summary_path = Path(output_folder) / "summary.json"
        try:
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        if summary.get("status") != "FAILED":
            return None
        workflow_json_path = Path(output_folder) / "workflow.json"
        try:
            workflow_json = json.loads(workflow_json_path.read_text(encoding="utf-8"))
            errors = workflow_json.get("validation_errors") or []
        except (OSError, json.JSONDecodeError):
            errors = []
        return "; ".join(errors) if errors else "export validation failed"

    async def _finish_failed(self, conversation_id: str, failed_step: str, reason: str) -> ConversationMessage:
        assistant_message = ConversationMessage(
            id=str(uuid.uuid4()),
            role=ConversationRole.ASSISTANT,
            content=f"The production workflow stopped at the {failed_step} step: {reason}",
            created_at=datetime.utcnow(),
            metadata={"workflow": "full_production", "status": "failed", "failed_step": failed_step},
        )
        await self._conversation_engine.append_message(conversation_id, assistant_message)
        logger.warning(
            "workflow_manager_finish_failed",
            extra={"conversation_id": conversation_id, "failed_step": failed_step, "reason": reason},
        )
        return assistant_message

    async def _run_json_classification(self, prompt: str) -> dict[str, Any] | None:
        try:
            request = LLMRequest(
                model=settings.default_llm_model,
                messages=[LLMMessage(role="system", content=prompt)],
                temperature=0.0,
                provider=settings.default_llm_provider,
                options={"response_format": {"type": "json_object"}},
            )
            raw = ""
            async for response in self._llm_provider.stream(request):
                if response.output:
                    raw += response.output
        except Exception:
            logger.warning("workflow_detection_failed", exc_info=True)
            return None
        return self._extract_json_object(raw)

    def _extract_json_object(self, content: str) -> dict[str, Any] | None:
        text = (content or "").strip()
        if not text:
            return None
        try:
            loaded = json.loads(text)
            return loaded if isinstance(loaded, dict) else None
        except json.JSONDecodeError:
            pass

        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        try:
            loaded = json.loads(text[start : end + 1])
            return loaded if isinstance(loaded, dict) else None
        except json.JSONDecodeError:
            return None
