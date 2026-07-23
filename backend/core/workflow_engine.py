from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from typing import Any, AsyncIterator

from backend.core.workflow_engine_models import (
    WorkflowDefinition,
    WorkflowRunContext,
    WorkflowStepResult,
)
from backend.core.workflow_history_store import WorkflowHistoryStore
from backend.services.workflow_exporter import WorkflowExporter

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """Generic execution core for declarative workflows. Runs `definition.steps` in order,
    threads outputs forward via `WorkflowRunContext.inputs`, streams progress, stops on the
    first failed step without exporting, exports every artifact on success, and records
    execution history. Knows nothing about any specific workflow's domain."""

    def __init__(self, exporter: WorkflowExporter, history_store: WorkflowHistoryStore) -> None:
        self._exporter = exporter
        self._history_store = history_store

    async def stream_execute(
        self,
        definition: WorkflowDefinition,
        *,
        topic: str,
        conversation_id: str,
        user_id: str | None,
        execution_id: str | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        # F1: callers that need the execution_id BEFORE the run finishes (e.g. an
        # async production trigger that must return it immediately) can pre-generate
        # and pass it in; every existing caller that doesn't keeps today's exact
        # auto-generated-uuid4 behavior.
        execution_id = execution_id or str(uuid.uuid4())
        started_at = datetime.utcnow()
        await self._history_store.record_started(execution_id, definition.id, topic)
        logger.info(
            "workflow_started",
            extra={"execution_id": execution_id, "workflow_id": definition.id, "topic": topic},
        )

        context = WorkflowRunContext(
            execution_id=execution_id,
            conversation_id=conversation_id,
            user_id=user_id,
            topic=topic,
        )
        step_statuses: dict[str, str] = {}

        for step in definition.steps:
            yield {"type": "progress", "text": f"▶ {step.name} Started\n"}
            try:
                result = await step.run(context)
            except Exception as exc:  # pragma: no cover - defensive path for step-internal bugs
                logger.exception("workflow_step_raised", extra={"execution_id": execution_id, "step": step.name})
                result = WorkflowStepResult(step_name=step.name, status="failed", error=str(exc))

            step_statuses[step.name] = result.status

            if result.status == "failed":
                yield {"type": "progress", "text": f"⚠️ {step.name} failed: {result.error}\n"}
                await self._history_store.record_failed(execution_id, step.name)
                logger.warning(
                    "workflow_failed",
                    extra={"execution_id": execution_id, "failed_step": step.name, "reason": result.error},
                )
                yield {
                    "type": "result",
                    "result": {
                        "status": "failed",
                        "execution_id": execution_id,
                        "failed_step": step.name,
                        "error": result.error,
                        "step_statuses": step_statuses,
                    },
                }
                return

            context.inputs[step.name] = result.data
            context.artifacts.extend(result.artifacts)
            self._record_step_cost(context, step.name, result)
            await self._history_store.record_step_executed(execution_id, step.name)
            yield {"type": "progress", "text": f"✅ {step.name} Finished\n"}

        yield {"type": "progress", "text": "📦 Export Started\n"}
        completed_at = datetime.utcnow()
        export_result = self._exporter.export(
            execution_id=execution_id,
            workflow_id=definition.id,
            workflow_name=definition.name,
            topic=topic,
            artifacts=context.artifacts,
            step_statuses=step_statuses,
            started_at=started_at,
            completed_at=completed_at,
        )
        yield {"type": "progress", "text": f"✅ Export Finished — {export_result.output_folder}\n"}

        await self._history_store.record_completed(
            execution_id,
            artifacts_generated=export_result.files_written,
            output_folder=export_result.output_folder,
        )
        logger.info(
            "workflow_finished",
            extra={"execution_id": execution_id, "output_folder": export_result.output_folder},
        )

        yield {
            "type": "result",
            "result": {
                "status": "success",
                "execution_id": execution_id,
                "step_statuses": step_statuses,
                "output_folder": export_result.output_folder,
                "files_written": export_result.files_written,
            },
        }

    def _record_step_cost(self, context: WorkflowRunContext, step_name: str, result: WorkflowStepResult) -> None:
        """Extracts `estimated_cost_usd` from the step's own `__meta__/<name>.json`
        metrics artifact (build_step_metrics_artifact's established convention)
        into `context.cost_ledger`, so a later step can answer "cost so far"
        without every step needing a bespoke cost-reporting channel."""
        metrics_filename = f"__meta__/{step_name}.json"
        for artifact in result.artifacts:
            if artifact.filename != metrics_filename or not artifact.content:
                continue
            try:
                payload = json.loads(artifact.content)
            except json.JSONDecodeError:
                continue
            cost_estimate = payload.get("cost_estimate") or {}
            cost = cost_estimate.get("estimated_cost_usd")
            if isinstance(cost, (int, float)):
                context.cost_ledger[step_name] = float(cost)
