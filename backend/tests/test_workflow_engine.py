from __future__ import annotations

import json

import pytest

from backend.core.workflow_engine import WorkflowEngine
from backend.core.workflow_engine_models import (
    WorkflowArtifact,
    WorkflowDefinition,
    WorkflowRunContext,
    WorkflowStep,
    WorkflowStepResult,
)
from backend.core.workflow_history_store import InMemoryWorkflowHistoryStore
from backend.services.workflow_exporter import ExportResult


class FakeSuccessStep(WorkflowStep):
    def __init__(self, step_name: str, artifact_filename: str) -> None:
        self._name = step_name
        self._artifact_filename = artifact_filename

    @property
    def name(self) -> str:
        return self._name

    async def run(self, context: WorkflowRunContext) -> WorkflowStepResult:
        return WorkflowStepResult(
            step_name=self._name,
            status="success",
            data={"topic": context.topic},
            artifacts=[WorkflowArtifact(self._artifact_filename, f"content for {self._name}")],
        )


class FakeFailingStep(WorkflowStep):
    def __init__(self, step_name: str, error: str) -> None:
        self._name = step_name
        self._error = error

    @property
    def name(self) -> str:
        return self._name

    async def run(self, context: WorkflowRunContext) -> WorkflowStepResult:
        return WorkflowStepResult(step_name=self._name, status="failed", error=self._error)


class FakeExporter:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def export(self, **kwargs) -> ExportResult:
        self.calls.append(kwargs)
        return ExportResult(output_folder="/fake/output", files_written=[a.filename for a in kwargs["artifacts"]])


async def _drain(engine: WorkflowEngine, definition: WorkflowDefinition):
    progress_texts = []
    result = None
    async for event in engine.stream_execute(
        definition, topic="Dyatlov Pass Incident", conversation_id="conv-1", user_id=None
    ):
        if event["type"] == "progress":
            progress_texts.append(event["text"])
        else:
            result = event["result"]
    return progress_texts, result


@pytest.mark.asyncio
async def test_success_path_threads_context_and_exports():
    exporter = FakeExporter()
    history_store = InMemoryWorkflowHistoryStore()
    engine = WorkflowEngine(exporter=exporter, history_store=history_store)
    definition = WorkflowDefinition(
        id="fake_workflow",
        name="Fake Workflow",
        steps=[
            FakeSuccessStep("StepA", "a.md"),
            FakeSuccessStep("StepB", "b.md"),
        ],
    )

    progress_texts, result = await _drain(engine, definition)

    assert result["status"] == "success"
    assert result["step_statuses"] == {"StepA": "success", "StepB": "success"}
    assert result["output_folder"] == "/fake/output"
    assert result["files_written"] == ["a.md", "b.md"]
    assert any("StepA Started" in text for text in progress_texts)
    assert any("StepB Finished" in text for text in progress_texts)

    assert len(exporter.calls) == 1
    exported_filenames = [artifact.filename for artifact in exporter.calls[0]["artifacts"]]
    assert exported_filenames == ["a.md", "b.md"]
    assert exporter.calls[0]["step_statuses"] == {"StepA": "success", "StepB": "success"}

    record = await history_store.get(result["execution_id"])
    assert record.status == "success"
    assert record.steps_executed == ["StepA", "StepB"]
    assert record.output_folder == "/fake/output"


@pytest.mark.asyncio
async def test_stream_execute_accepts_a_pre_generated_execution_id():
    # F1: an async trigger needs the execution_id BEFORE the run finishes (to
    # return it immediately) — passing one in must be honored end to end instead
    # of the engine always minting its own uuid4.
    exporter = FakeExporter()
    history_store = InMemoryWorkflowHistoryStore()
    engine = WorkflowEngine(exporter=exporter, history_store=history_store)
    definition = WorkflowDefinition(id="fake_workflow", name="Fake Workflow", steps=[FakeSuccessStep("StepA", "a.md")])

    result = None
    async for event in engine.stream_execute(
        definition, topic="Test", conversation_id="conv-1", user_id=None, execution_id="pre-generated-id"
    ):
        if event["type"] == "result":
            result = event["result"]

    assert result["execution_id"] == "pre-generated-id"
    record = await history_store.get("pre-generated-id")
    assert record is not None
    assert record.status == "success"


@pytest.mark.asyncio
async def test_failure_stops_immediately_without_export():
    exporter = FakeExporter()
    history_store = InMemoryWorkflowHistoryStore()
    engine = WorkflowEngine(exporter=exporter, history_store=history_store)
    definition = WorkflowDefinition(
        id="fake_workflow",
        name="Fake Workflow",
        steps=[
            FakeSuccessStep("StepA", "a.md"),
            FakeFailingStep("StepB", "boom"),
            FakeSuccessStep("StepC", "c.md"),
        ],
    )

    progress_texts, result = await _drain(engine, definition)

    assert result["status"] == "failed"
    assert result["failed_step"] == "StepB"
    assert result["error"] == "boom"
    assert result["step_statuses"] == {"StepA": "success", "StepB": "failed"}
    assert "StepC" not in result["step_statuses"]
    assert not any("StepC" in text for text in progress_texts)

    assert exporter.calls == []

    record = await history_store.get(result["execution_id"])
    assert record.status == "failed"
    assert record.failed_step == "StepB"
    assert record.steps_executed == ["StepA"]


class FakeCostReportingStep(WorkflowStep):
    """Mirrors how a real step reports cost: a __meta__/<name>.json metrics
    artifact carrying a cost_estimate dict, exactly as build_step_metrics_artifact
    produces it."""

    def __init__(self, step_name: str, estimated_cost_usd: float) -> None:
        self._name = step_name
        self._cost = estimated_cost_usd

    @property
    def name(self) -> str:
        return self._name

    async def run(self, context: WorkflowRunContext) -> WorkflowStepResult:
        payload = {"cost_estimate": {"provider": "fake", "estimated_cost_usd": self._cost}}
        metrics_artifact = WorkflowArtifact(f"__meta__/{self._name}.json", content=json.dumps(payload))
        return WorkflowStepResult(step_name=self._name, status="success", data={}, artifacts=[metrics_artifact])


class FakeLedgerCaptureStep(WorkflowStep):
    """Snapshots context.cost_ledger as it exists when this step runs, so the test
    can assert on what a later F28B-style step would see."""

    def __init__(self, step_name: str, sink: list[dict]) -> None:
        self._name = step_name
        self._sink = sink

    @property
    def name(self) -> str:
        return self._name

    async def run(self, context: WorkflowRunContext) -> WorkflowStepResult:
        self._sink.append(dict(context.cost_ledger))
        return WorkflowStepResult(step_name=self._name, status="success", data={})


@pytest.mark.asyncio
async def test_cost_ledger_accumulates_from_each_steps_metrics_artifact():
    exporter = FakeExporter()
    history_store = InMemoryWorkflowHistoryStore()
    engine = WorkflowEngine(exporter=exporter, history_store=history_store)
    captured: list[dict] = []
    definition = WorkflowDefinition(
        id="fake_workflow",
        name="Fake Workflow",
        steps=[
            FakeCostReportingStep("StepA", 0.10),
            FakeCostReportingStep("StepB", 0.25),
            FakeLedgerCaptureStep("StepC", captured),
        ],
    )

    await _drain(engine, definition)

    assert captured == [{"StepA": 0.10, "StepB": 0.25}]


@pytest.mark.asyncio
async def test_cost_ledger_ignores_steps_without_a_cost_estimate():
    exporter = FakeExporter()
    history_store = InMemoryWorkflowHistoryStore()
    engine = WorkflowEngine(exporter=exporter, history_store=history_store)
    captured: list[dict] = []
    definition = WorkflowDefinition(
        id="fake_workflow",
        name="Fake Workflow",
        steps=[
            FakeSuccessStep("StepA", "a.md"),  # no __meta__ artifact at all
            FakeLedgerCaptureStep("StepB", captured),
        ],
    )

    await _drain(engine, definition)

    assert captured == [{}]
