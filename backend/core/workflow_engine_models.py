from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any


@dataclass
class WorkflowArtifact:
    """A single named file produced by a workflow step, ready for export to disk.
    Text artifacts set `content`; binary artifacts (audio, images) set `content_bytes`
    instead and leave `content` empty."""

    filename: str
    content: str = ""
    content_bytes: bytes | None = None


@dataclass
class WorkflowStepResult:
    """Outcome of one `WorkflowStep.run()` call."""

    step_name: str
    status: str  # "success" | "failed"
    data: dict[str, Any] = field(default_factory=dict)
    artifacts: list[WorkflowArtifact] = field(default_factory=list)
    error: str | None = None


@dataclass
class WorkflowRunContext:
    """Shared, accumulating context threaded through every step of one workflow execution."""

    execution_id: str
    conversation_id: str
    user_id: str | None
    topic: str
    inputs: dict[str, Any] = field(default_factory=dict)
    artifacts: list[WorkflowArtifact] = field(default_factory=list)
    # F28B Production Budget Awareness — populated by WorkflowEngine from each
    # step's own __meta__ metrics artifact (build_step_metrics_artifact) as it
    # completes, keyed by step name. Lets a later step (Composition Planning)
    # answer "how much has this production spent so far" via
    # sum(context.cost_ledger.values()) without every earlier step needing to
    # change how it reports cost.
    cost_ledger: dict[str, float] = field(default_factory=dict)


class WorkflowStep(abc.ABC):
    """Contract every concrete workflow stage must implement. The engine knows nothing
    beyond this interface — no step, workflow, or domain (YouTube, Instagram, ...) may
    leak into `WorkflowEngine`."""

    @property
    @abc.abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    async def run(self, context: WorkflowRunContext) -> WorkflowStepResult:
        raise NotImplementedError


@dataclass
class WorkflowDefinition:
    """A named, ordered list of steps — the declarative unit a `WorkflowManager` registry
    entry resolves to. Adding a new workflow means adding a new definition, never touching
    the engine."""

    id: str
    name: str
    steps: list[WorkflowStep]
