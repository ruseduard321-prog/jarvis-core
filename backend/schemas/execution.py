from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field
from enum import Enum


# ============================================================
# TOOL SCHEMAS
# ============================================================

class ToolParameterType(str, Enum):
    """Tool parameter types."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    LIST = "list"
    OBJECT = "object"


class ToolParameter(BaseModel):
    """Tool parameter definition."""

    name: str = Field(description="Parameter name")
    type: ToolParameterType = Field(description="Parameter type")
    description: str | None = Field(None, description="Parameter description")
    required: bool = Field(default=False, description="Whether parameter is required")
    default: Any = Field(None, description="Default value")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "query",
                "type": "string",
                "description": "Search query",
                "required": True,
            }
        }


class ToolMetadataResponse(BaseModel):
    """Metadata for a tool."""

    id: str = Field(description="Tool ID")
    name: str = Field(description="Tool name")
    description: str | None = Field(None, description="Tool description")
    category: str | None = Field(None, description="Tool category")
    parameters: list[ToolParameter] = Field(default_factory=list, description="Input parameters")
    tags: list[str] = Field(default_factory=list, description="Tags")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "tool_search",
                "name": "Web Search",
                "description": "Search the web for information",
                "category": "search",
                "parameters": [
                    {
                        "name": "query",
                        "type": "string",
                        "description": "Search query",
                        "required": True,
                    }
                ],
                "tags": ["search", "web"],
            }
        }


class ToolExecutionRequest(BaseModel):
    """Request to execute a tool."""

    tool_id: str = Field(description="Tool ID")
    arguments: dict[str, Any] = Field(default_factory=dict, description="Tool arguments")
    timeout_seconds: int | None = Field(None, description="Execution timeout in seconds")

    class Config:
        json_schema_extra = {
            "example": {
                "tool_id": "tool_search",
                "arguments": {"query": "project requirements"},
                "timeout_seconds": 30,
            }
        }


class ToolExecutionResponse(BaseModel):
    """Response from tool execution."""

    tool_id: str = Field(description="Tool ID")
    execution_id: str = Field(description="Execution ID")
    status: str = Field(description="Status (success, failed, timeout)")
    output: Any = Field(description="Tool output")
    duration_ms: int = Field(description="Execution time in milliseconds")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "tool_id": "tool_search",
                "execution_id": "exec_123",
                "status": "success",
                "output": {"results": [{"title": "Project", "url": "..."}]},
                "duration_ms": 145,
                "metadata": {},
            }
        }


# ============================================================
# AGENT SCHEMAS
# ============================================================

class AgentStatus(str, Enum):
    """Agent execution status."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentMetadataResponse(BaseModel):
    """Metadata for an agent."""

    id: str = Field(description="Agent ID")
    name: str = Field(description="Agent name")
    description: str | None = Field(None, description="Agent description")
    capabilities: list[str] = Field(default_factory=list, description="Agent capabilities")
    tools: list[str] = Field(default_factory=list, description="Tool IDs available to agent")
    status: AgentStatus = Field(default=AgentStatus.IDLE, description="Current status")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "agent_research",
                "name": "Research Agent",
                "description": "Performs research and information gathering",
                "capabilities": ["search", "summarize", "analyze"],
                "tools": ["tool_search", "tool_summarize"],
                "status": "idle",
                "metadata": {"version": "1.0"},
            }
        }


class AgentExecutionRequest(BaseModel):
    """Request to execute an agent."""

    agent_id: str = Field(description="Agent ID")
    message: str = Field(description="Input message for agent")
    conversation_id: str | None = Field(None, description="Conversation context")
    stream: bool = Field(default=False, description="Whether to stream responses")
    timeout_seconds: int | None = Field(None, description="Execution timeout in seconds")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "agent_id": "agent_research",
                "message": "Research the latest AI developments",
                "conversation_id": "conv_123",
                "stream": False,
                "timeout_seconds": 60,
                "metadata": {},
            }
        }


class AgentExecutionResponse(BaseModel):
    """Response from agent execution."""

    agent_id: str = Field(description="Agent ID")
    execution_id: str = Field(description="Execution ID")
    status: AgentStatus = Field(description="Execution status")
    response: str = Field(description="Agent response")
    tools_used: list[str] = Field(default_factory=list, description="Tools used")
    duration_ms: int = Field(description="Execution time in milliseconds")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "agent_id": "agent_research",
                "execution_id": "exec_456",
                "status": "completed",
                "response": "Based on recent research: ...",
                "tools_used": ["tool_search"],
                "duration_ms": 2341,
                "metadata": {},
            }
        }


# ============================================================
# WORKFLOW SCHEMAS
# ============================================================

class WorkflowNodeType(str, Enum):
    """Workflow node types."""
    START = "start"
    END = "end"
    TASK = "task"
    DECISION = "decision"
    PARALLEL = "parallel"
    MERGE = "merge"


class WorkflowStatus(str, Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowDefinitionRequest(BaseModel):
    """Request to create a workflow."""

    name: str = Field(description="Workflow name")
    description: str | None = Field(None, description="Workflow description")
    nodes: list[dict[str, Any]] = Field(description="Workflow nodes")
    edges: list[dict[str, Any]] = Field(description="Workflow edges (connections)")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Document Processing",
                "description": "Process and analyze documents",
                "nodes": [
                    {"id": "start", "type": "start"},
                    {"id": "task_1", "type": "task", "agent_id": "agent_1"},
                    {"id": "end", "type": "end"},
                ],
                "edges": [
                    {"from": "start", "to": "task_1"},
                    {"from": "task_1", "to": "end"},
                ],
                "metadata": {},
            }
        }


class WorkflowExecutionRequest(BaseModel):
    """Request to execute a workflow."""

    workflow_id: str = Field(description="Workflow ID")
    input_data: dict[str, Any] = Field(default_factory=dict, description="Workflow input data")
    timeout_seconds: int | None = Field(None, description="Execution timeout in seconds")

    class Config:
        json_schema_extra = {
            "example": {
                "workflow_id": "workflow_123",
                "input_data": {"document_id": "doc_123"},
                "timeout_seconds": 300,
            }
        }


class WorkflowExecutionResponse(BaseModel):
    """Response from workflow execution."""

    workflow_id: str = Field(description="Workflow ID")
    execution_id: str = Field(description="Execution ID")
    status: WorkflowStatus = Field(description="Execution status")
    output_data: dict[str, Any] = Field(default_factory=dict, description="Output data")
    duration_ms: int = Field(description="Execution time in milliseconds")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "workflow_id": "workflow_123",
                "execution_id": "exec_789",
                "status": "completed",
                "output_data": {"result": "Document processed successfully"},
                "duration_ms": 5432,
                "metadata": {},
            }
        }
