from __future__ import annotations

import logging
import uuid
import json
from pathlib import Path
from typing import Any, AsyncIterator

from backend.core.agent_orchestration_models import AgentResult, AgentTask, ExecutionContext
from backend.core.config import settings
from backend.core.conversation_engine import ConversationEngine
from backend.core.event_bus_service import EventBusService
from backend.core.llm_models import LLMMessage, LLMRequest
from backend.core.llm_provider import LLMProvider
from backend.core.memory_models import MemoryQuery
from backend.core.memory_service import MemoryService
from backend.core.prompt_library_service import PromptLibraryService
from backend.core.tool import ToolRegistry
from backend.core.tool_manager import ToolManager
from backend.core.tool_models import ToolContext
from backend.services.agent_service import AgentService

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Minimal orchestrator for controlled agent execution and delegation."""

    MAX_DELEGATION_DEPTH = 3
    _seed_delegation_policy: dict[str, list[str]] | None = None

    def __init__(
        self,
        agent_service: AgentService,
        tool_registry: ToolRegistry,
        tool_manager: ToolManager,
        conversation_engine: ConversationEngine,
        memory_service: MemoryService,
        prompt_library_service: PromptLibraryService,
        llm_provider: LLMProvider,
        event_bus_service: EventBusService,
    ) -> None:
        self._agent_service = agent_service
        self._tool_registry = tool_registry
        self._tool_manager = tool_manager
        self._conversation_engine = conversation_engine
        self._memory_service = memory_service
        self._prompt_library_service = prompt_library_service
        self._llm_provider = llm_provider
        self._event_bus_service = event_bus_service

    async def execute(
        self,
        *,
        agent_id: str,
        objective: str,
        context: ExecutionContext,
        requesting_agent: str | None = None,
        visited_agents: tuple[str, ...] = (),
    ) -> AgentResult:
        """Run one agent turn to completion and return the final result.

        Thin wrapper around `stream_execute()` that drains the incremental deltas and
        returns only the terminal result — kept for callers that don't need streaming
        (delegation chain steps other than the last, tests, etc.).
        """
        result: AgentResult | None = None
        async for event in self.stream_execute(
            agent_id=agent_id,
            objective=objective,
            context=context,
            requesting_agent=requesting_agent,
            visited_agents=visited_agents,
        ):
            if event["type"] == "final":
                result = event["result"]

        if result is None:
            raise RuntimeError("stream_execute() completed without yielding a final result")
        return result

    async def stream_execute(
        self,
        *,
        agent_id: str,
        objective: str,
        context: ExecutionContext,
        requesting_agent: str | None = None,
        visited_agents: tuple[str, ...] = (),
    ) -> AsyncIterator[dict[str, Any]]:
        """Run one agent turn, streaming the final answer as it is generated.

        Yields `{"type": "delta", "text": str}` chunks for each piece of incremental
        output, followed by exactly one `{"type": "final", "result": AgentResult}` chunk
        carrying the complete, persistable result.
        """
        if context.execution_depth > self.MAX_DELEGATION_DEPTH:
            yield {
                "type": "final",
                "result": AgentResult(
                    summary="Delegation depth limit exceeded.",
                    status="failed",
                    output={"objective": objective},
                    metadata={"status": "failed", "reason": "max_depth_exceeded"},
                ),
            }
            return

        if agent_id in visited_agents:
            yield {
                "type": "final",
                "result": AgentResult(
                    summary=f"Circular delegation detected for agent '{agent_id}'.",
                    status="failed",
                    output={"objective": objective},
                    metadata={"status": "failed", "reason": "circular_delegation"},
                ),
            }
            return

        agent = await self._agent_service.get_agent(agent_id)
        if not agent.is_active:
            yield {
                "type": "final",
                "result": AgentResult(
                    summary=f"Target agent '{agent_id}' is inactive.",
                    status="failed",
                    output={"objective": objective},
                    metadata={"status": "failed", "reason": "inactive_agent"},
                ),
            }
            return

        execution_id = str(uuid.uuid4())
        await self._event_bus_service.publish_event(
            "AgentExecutionStarted",
            payload={
                "execution_id": execution_id,
                "conversation_id": context.conversation_id,
                "agent_id": agent_id,
                "requesting_agent": requesting_agent,
            },
            metadata={"agent_id": agent_id, "conversation_id": context.conversation_id},
        )

        allowed_delegations = self._resolve_allowed_delegations(agent)

        # Automatic delegation: only for free-form turns the caller hasn't already routed
        # itself (workflow services set "workflow"/"delegation"; dispatched chain steps set
        # "delegation_dispatched") — existing explicit callers are entirely unaffected.
        if (
            context.metadata.get("workflow") is None
            and context.metadata.get("delegation") is None
            and context.metadata.get("delegation_dispatched") is not True
            and allowed_delegations
        ):
            delegation_plan = await self._auto_plan_delegation(agent, objective, context, allowed_delegations)
            if delegation_plan and delegation_plan.get("action") == "delegate" and delegation_plan.get("steps"):
                logger.info(
                    "auto_delegation_planned",
                    extra={
                        "conversation_id": context.conversation_id,
                        "selected_agent": agent_id,
                        "detected_targets": [s.get("target_agent") for s in delegation_plan["steps"]],
                        "reason": delegation_plan.get("reason", ""),
                    },
                )
                async for event in self._stream_delegation_chain(
                    agent=agent,
                    agent_id=agent_id,
                    objective=objective,
                    context=context,
                    steps=delegation_plan["steps"],
                    requesting_agent=requesting_agent,
                    visited_agents=(*visited_agents, agent_id),
                    execution_id=execution_id,
                ):
                    yield event
                return

        # Automatic capability detection: only when the caller hasn't already decided
        # tool use for this exact turn (explicit workflow-service calls set this, even to []).
        if context.metadata.get("capability_requests") is None:
            tool_plan = await self._auto_plan_tool_use(agent, objective, context)
            if tool_plan and tool_plan.get("use_tool") and tool_plan.get("capability"):
                logger.info(
                    "auto_capability_detected",
                    extra={
                        "conversation_id": context.conversation_id,
                        "selected_agent": agent_id,
                        "detected_capability": tool_plan["capability"],
                        "reason": tool_plan.get("reason", ""),
                    },
                )
                context.metadata["capability_requests"] = [
                    {
                        "capability": tool_plan["capability"],
                        "args": tool_plan.get("capability_args") or {},
                        "reason": tool_plan.get("reason", "Automatically detected from objective."),
                    }
                ]

        # Tools run before the response is drafted so their real output can inform it,
        # instead of the model guessing at results it hasn't seen yet.
        tool_calls = await self._execute_requested_tools(agent_id=agent_id, context=context)
        tool_results_context = self._format_tool_results(tool_calls)

        reference_context = self._format_reference_context(context.documents, context.artifacts)

        llm_messages = await self._build_llm_messages(
            conversation_id=context.conversation_id,
            agent_id=agent_id,
            agent_name=agent.name,
            mission=agent.mission,
            allowed_delegations=allowed_delegations,
            tool_results_context=tool_results_context,
            reference_context=reference_context,
            user_id=context.user_id,
            current_message=objective,
        )
        request = LLMRequest(
            model=settings.default_llm_model,
            messages=llm_messages,
            temperature=context.metadata.get("temperature"),
            max_tokens=context.metadata.get("max_tokens"),
            provider=settings.default_llm_provider,
        )

        # Accumulate the complete answer for persistence while forwarding each delta to
        # the caller immediately. The provider's terminal chunk carries `is_final=True`
        # with empty `output`, so it is naturally skipped here without special-casing.
        output_text = ""
        async for response in self._llm_provider.stream(request):
            if response.output:
                output_text += response.output
                yield {"type": "delta", "text": response.output}

        delegated = await self._resolve_requested_delegations(
            requester_allowed_delegations=allowed_delegations,
            requester=agent_id,
            context=context,
            visited_agents=(*visited_agents, agent_id),
        )

        status = "success"
        if any(not call.get("success", False) for call in tool_calls) or any(
            item.get("status") != "completed" for item in delegated
        ):
            status = "partial"

        result = AgentResult(
            summary=output_text.strip() or f"Agent '{agent.name}' completed objective.",
            status=status,
            output={
                "text": output_text,
                "objective": objective,
                "artifacts": context.artifacts,
            },
            tool_calls=tool_calls,
            delegated_agents=delegated,
            metadata={
                "status": "completed",
                "agent_id": agent_id,
                "execution_id": execution_id,
                "requesting_agent": requesting_agent,
                "execution_depth": context.execution_depth,
            },
        )

        await self._event_bus_service.publish_event(
            "AgentExecutionCompleted",
            payload={
                "execution_id": execution_id,
                "conversation_id": context.conversation_id,
                "agent_id": agent_id,
            },
            metadata={"agent_id": agent_id, "conversation_id": context.conversation_id},
        )
        yield {"type": "final", "result": result}

    async def _execute_requested_tools(self, *, agent_id: str, context: ExecutionContext) -> list[dict[str, Any]]:
        raw_requests = context.metadata.get("capability_requests")
        if not isinstance(raw_requests, list):
            return []

        outputs: list[dict[str, Any]] = []
        for request in raw_requests:
            if not isinstance(request, dict):
                continue
            capability = str(request.get("capability", "")).strip()
            args = request.get("args") or {}
            if not capability or not isinstance(args, dict):
                continue

            matching_tools = self._tool_registry.find_by_capability(capability)
            if not matching_tools:
                outputs.append(
                    {
                        "capability": capability,
                        "success": False,
                        "output": None,
                        "error": f"No tool registered for capability: {capability}",
                        "metadata": {"capability": capability},
                    }
                )
                continue

            tool_slug = matching_tools[0].slug
            tool_result = await self._tool_manager.execute(
                tool_slug=tool_slug,
                args=args,
                context=ToolContext(
                    agent_id=agent_id,
                    conversation_id=context.conversation_id,
                    user_id=context.user_id,
                    metadata={"execution_depth": context.execution_depth},
                ),
            )
            outputs.append(
                {
                    "capability": capability,
                    "tool": tool_slug,
                    "success": tool_result.success,
                    "output": tool_result.output,
                    "error": tool_result.error,
                    "metadata": tool_result.metadata,
                }
            )
        return outputs

    async def _resolve_requested_delegations(
        self,
        *,
        requester_allowed_delegations: list[str],
        requester: str,
        context: ExecutionContext,
        visited_agents: tuple[str, ...],
    ) -> list[dict[str, Any]]:
        raw_delegation = context.metadata.get("delegation")
        if raw_delegation is None:
            return []

        requests: list[dict[str, Any]]
        if isinstance(raw_delegation, dict):
            requests = [raw_delegation]
        elif isinstance(raw_delegation, list):
            requests = [item for item in raw_delegation if isinstance(item, dict)]
        else:
            return []

        delegated_results: list[dict[str, Any]] = []
        for request in requests:
            target_agent = str(request.get("target_agent", "")).strip()
            objective = str(request.get("objective", "")).strip()
            reason = str(request.get("reason", "")).strip()
            if not target_agent or not objective:
                continue

            task = AgentTask(
                id=str(uuid.uuid4()),
                requesting_agent=requester,
                target_agent=target_agent,
                objective=objective,
                reason=reason or "No reason provided.",
                context=request.get("context") if isinstance(request.get("context"), dict) else {},
                status="running",
            )

            if target_agent not in requester_allowed_delegations:
                delegated_results.append(
                    {
                        **task.to_dict(),
                        "status": "failed",
                        "result": {
                            "summary": f"Delegation blocked: '{requester}' cannot delegate to '{target_agent}'.",
                            "status": "failed",
                            "metadata": {"reason": "delegation_not_allowed"},
                        },
                    }
                )
                continue

            if context.execution_depth + 1 > self.MAX_DELEGATION_DEPTH:
                delegated_results.append(
                    {
                        **task.to_dict(),
                        "status": "failed",
                        "result": {
                            "summary": "Delegation blocked: depth limit exceeded.",
                            "status": "failed",
                            "metadata": {"reason": "max_depth_exceeded"},
                        },
                    }
                )
                continue

            resolved_target_id = await self._resolve_agent_id_by_slug_or_id(target_agent)

            if resolved_target_id in visited_agents:
                delegated_results.append(
                    {
                        **task.to_dict(),
                        "status": "failed",
                        "result": {
                            "summary": f"Delegation blocked: circular delegation to '{target_agent}'.",
                            "status": "failed",
                            "metadata": {"reason": "circular_delegation"},
                        },
                    }
                )
                continue

            child_context = ExecutionContext(
                conversation_id=context.conversation_id,
                user_id=context.user_id,
                memory=context.memory,
                documents=context.documents,
                media_assets=context.media_assets,
                artifacts=context.artifacts,
                execution_depth=context.execution_depth + 1,
                metadata=(request.get("context") if isinstance(request.get("context"), dict) else {}),
            )

            child_result = await self.execute(
                agent_id=resolved_target_id,
                objective=objective,
                context=child_context,
                requesting_agent=requester,
                visited_agents=visited_agents,
            )
            task_status = "completed" if child_result.status in {"success", "partial"} else "failed"
            delegated_results.append(
                {
                    **task.to_dict(),
                    "status": task_status,
                    "result": child_result.to_dict(),
                }
            )
        return delegated_results

    def _delegation_blocked_result(self, task: AgentTask, reason: str, summary: str) -> dict[str, Any]:
        return {
            **task.to_dict(),
            "status": "failed",
            "result": {"summary": summary, "status": "failed", "metadata": {"reason": reason}},
        }

    async def _stream_delegation_chain(
        self,
        *,
        agent: Any,
        agent_id: str,
        objective: str,
        context: ExecutionContext,
        steps: list[dict[str, Any]],
        requesting_agent: str | None,
        visited_agents: tuple[str, ...],
        execution_id: str,
    ) -> AsyncIterator[dict[str, Any]]:
        """Run an automatically-planned sequence of delegations, threading each step's real
        output into the next step's objective so later agents work from actual results.
        visited_agents must already include agent_id (mirrors _resolve_requested_delegations).

        Only the last step's output becomes the user-visible answer, so only it is run via
        `stream_execute()` with its deltas forwarded live; earlier steps are hidden
        intermediate work and run via the buffered `execute()`.

        Yields the same `{"type": "delta"}` / `{"type": "final"}` shape as `stream_execute()`.
        """
        allowed_delegations = self._resolve_allowed_delegations(agent)
        delegated_results: list[dict[str, Any]] = []
        prior_output = ""
        prior_agent_id = ""
        final_text = ""
        final_status: str = "success"

        for index, step in enumerate(steps):
            is_last_step = index == len(steps) - 1
            target_agent = str(step.get("target_agent", "")).strip()
            step_objective = str(step.get("objective", "")).strip()
            if not target_agent or not step_objective:
                continue

            if prior_output:
                step_objective = f"{step_objective}\n\nUse this material from {prior_agent_id}:\n{prior_output}"

            task = AgentTask(
                id=str(uuid.uuid4()),
                requesting_agent=agent_id,
                target_agent=target_agent,
                objective=step_objective,
                reason="Automatically delegated from a free-form request.",
                context={},
                status="running",
            )

            if target_agent not in allowed_delegations:
                delegated_results.append(
                    self._delegation_blocked_result(
                        task, "delegation_not_allowed", f"Delegation blocked: cannot delegate to '{target_agent}'."
                    )
                )
                final_status = "partial"
                break

            if context.execution_depth + 1 > self.MAX_DELEGATION_DEPTH:
                delegated_results.append(
                    self._delegation_blocked_result(task, "max_depth_exceeded", "Delegation blocked: depth limit exceeded.")
                )
                final_status = "partial"
                break

            resolved_target_id = await self._resolve_agent_id_by_slug_or_id(target_agent)

            if resolved_target_id in visited_agents:
                delegated_results.append(
                    self._delegation_blocked_result(
                        task, "circular_delegation", f"Delegation blocked: circular delegation to '{target_agent}'."
                    )
                )
                final_status = "partial"
                break

            child_context = ExecutionContext(
                conversation_id=context.conversation_id,
                user_id=context.user_id,
                memory=context.memory,
                documents=context.documents,
                media_assets=context.media_assets,
                artifacts=context.artifacts,
                execution_depth=context.execution_depth + 1,
                metadata={"delegation_dispatched": True},
            )

            if is_last_step:
                child_result: AgentResult | None = None
                async for event in self.stream_execute(
                    agent_id=resolved_target_id,
                    objective=step_objective,
                    context=child_context,
                    requesting_agent=agent_id,
                    visited_agents=visited_agents,
                ):
                    if event["type"] == "delta":
                        yield event
                    else:
                        child_result = event["result"]
                assert child_result is not None
            else:
                child_result = await self.execute(
                    agent_id=resolved_target_id,
                    objective=step_objective,
                    context=child_context,
                    requesting_agent=agent_id,
                    visited_agents=visited_agents,
                )

            task_status = "completed" if child_result.status in {"success", "partial"} else "failed"
            delegated_results.append({**task.to_dict(), "status": task_status, "result": child_result.to_dict()})

            if child_result.status == "failed":
                final_status = "partial"
                break

            if child_result.status == "partial":
                final_status = "partial"

            output_payload = child_result.output if isinstance(child_result.output, dict) else {}
            prior_output = str(output_payload.get("text") or child_result.summary)
            prior_agent_id = target_agent
            final_text = prior_output

        result = AgentResult(
            summary=final_text.strip() or f"Agent '{agent.name}' could not complete the delegated request.",
            status=final_status if final_text else "failed",
            output={"text": final_text, "objective": objective, "artifacts": context.artifacts},
            tool_calls=[],
            delegated_agents=delegated_results,
            metadata={
                "status": "completed",
                "agent_id": agent_id,
                "execution_id": execution_id,
                "requesting_agent": requesting_agent,
                "execution_depth": context.execution_depth,
                "auto_delegated": True,
            },
        )

        await self._event_bus_service.publish_event(
            "AgentExecutionCompleted",
            payload={
                "execution_id": execution_id,
                "conversation_id": context.conversation_id,
                "agent_id": agent_id,
            },
            metadata={"agent_id": agent_id, "conversation_id": context.conversation_id},
        )
        yield {"type": "final", "result": result}

    async def _resolve_agent_id_by_slug_or_id(self, value: str) -> str:
        """Delegation targets are tracked by slug (allowed_delegations is slug-keyed), but
        execute() requires a real agent id. Resolve slug -> id; pass real ids through
        unchanged. Falls back to the original value if nothing matches, so execute()'s own
        not-found handling still applies."""
        try:
            candidate = await self._agent_service.get_agent(value)
            return candidate.id
        except Exception:
            pass

        try:
            agents = await self._agent_service.list_agents(active_only=True)
        except Exception:
            return value

        for candidate in agents:
            if candidate.slug == value:
                return candidate.id
        return value

    async def _get_delegatable_agents(self, allowed_delegations: list[str]) -> list[Any]:
        if not allowed_delegations:
            return []
        try:
            agents = await self._agent_service.list_agents(active_only=True)
        except Exception:
            return []
        allowed_slugs = set(allowed_delegations)
        return [sibling for sibling in agents if sibling.slug in allowed_slugs]

    async def _auto_plan_delegation(
        self,
        agent: Any,
        objective: str,
        context: ExecutionContext,
        allowed_delegations: list[str],
    ) -> dict[str, Any] | None:
        """Ask the acting agent's own LLM to decide whether this objective should be handed
        to one or more specialist agents, or answered directly. Best-effort: any failure
        (model error, invalid JSON, unsupported response_format) yields None, which falls
        back to the agent answering directly exactly as before this feature existed."""
        siblings = await self._get_delegatable_agents(allowed_delegations)
        if not siblings:
            return None

        roster_lines = "\n".join(f"- {sibling.name} (slug: {sibling.slug}): {sibling.mission}" for sibling in siblings)
        prompt = (
            f"You are {agent.name}. Mission: {agent.mission}\n\n"
            "Decide whether this request should be delegated to one or more specialist agents, "
            "or answered directly. Respond with STRICT JSON only, matching this shape:\n"
            '{"action": "delegate" | "answer", "steps": [{"target_agent": "<slug>", "objective": "<string>"}], "reason": "<short string>"}\n\n'
            "Rules:\n"
            '- action="answer": you can fully handle this yourself; steps must be [].\n'
            '- action="delegate": steps is an ORDERED list of 1 or more specialists whose combined '
            "work fulfills the request, in the order they must run. Each entry's objective must be "
            "a clear, self-contained instruction for that specialist covering ONLY their part of the work.\n"
            "- If the request needs more than one specialist in sequence (e.g. research something and "
            "then write about it), include ALL needed steps in order, don't just delegate to the first one.\n"
            "- Only use target_agent values from the roster below. Never invent new ones. Never include yourself.\n"
            "- Visual/media assets (thumbnails, images, video, audio) belong to the media specialist, "
            "not the content-writing specialist.\n\n"
            f"Specialist agents available:\n{roster_lines}\n\n"
            f"User request: {objective}"
        )

        parsed = await self._run_json_classification(prompt)
        if not parsed or parsed.get("action") not in {"delegate", "answer"}:
            return None

        if parsed.get("action") == "answer":
            return {"action": "answer", "steps": [], "reason": parsed.get("reason", "")}

        allowed_slugs = {sibling.slug for sibling in siblings}
        steps = []
        for step in parsed.get("steps") or []:
            if not isinstance(step, dict):
                continue
            target_agent = str(step.get("target_agent", "")).strip()
            step_objective = str(step.get("objective", "")).strip()
            if target_agent in allowed_slugs and step_objective:
                steps.append({"target_agent": target_agent, "objective": step_objective})

        if not steps:
            return None
        return {"action": "delegate", "steps": steps, "reason": parsed.get("reason", "")}

    async def _auto_plan_tool_use(
        self,
        agent: Any,
        objective: str,
        context: ExecutionContext,
    ) -> dict[str, Any] | None:
        """Ask whether completing this already-assigned objective requires one of this
        agent's own tool capabilities. Delegation is intentionally not offered here — that
        decision is made once, upfront, by _auto_plan_delegation."""
        tools = self._tool_registry.list_tools()
        if not tools:
            return None

        tool_lines = "\n".join(f"- {tool.slug}: {tool.description}" for tool in tools)
        prompt = (
            f"You are {agent.name}. Mission: {agent.mission}\n\n"
            "You have already been assigned the objective below. You will complete it yourself — "
            "delegation is not an option at this stage. Decide only whether completing it requires "
            "one of your tool capabilities first. Respond with STRICT JSON only:\n"
            '{"use_tool": true | false, "capability": "<capability id or null>", "capability_args": {}, "reason": "<short string>"}\n\n'
            f"Tool capabilities available to you:\n{tool_lines}\n\n"
            f"Objective: {objective}"
        )

        parsed = await self._run_json_classification(prompt)
        if not parsed or not isinstance(parsed.get("use_tool"), bool):
            return None

        if not parsed["use_tool"]:
            return {"use_tool": False}

        capability = str(parsed.get("capability") or "").strip()
        if not capability or not self._tool_registry.find_by_capability(capability):
            return None

        args = parsed.get("capability_args")
        return {
            "use_tool": True,
            "capability": capability,
            "capability_args": args if isinstance(args, dict) else {},
            "reason": parsed.get("reason", ""),
        }

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
            logger.warning("auto_plan_classification_failed", exc_info=True)
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

    def _format_tool_results(self, tool_calls: list[dict[str, Any]]) -> str:
        if not tool_calls:
            return ""
        lines = []
        for call in tool_calls:
            if call.get("success"):
                lines.append(f"- {call.get('capability')} ({call.get('tool')}): {call.get('output')}")
            else:
                lines.append(f"- {call.get('capability')} failed: {call.get('error')}")
        return "Tool results (use these, do not claim you cannot access external information):\n" + "\n".join(lines)

    def _format_reference_context(
        self, documents: list[dict[str, Any]], artifacts: list[dict[str, Any]]
    ) -> str:
        """Render caller-supplied documents/artifacts (e.g. an upstream workflow step's
        output passed via `ExecutionContext`) into prompt text. Without this, callers like
        the YouTube production workflow's step services can attach a research package to
        `context.documents`/`context.artifacts` and the agent would never actually see it."""
        if not documents and not artifacts:
            return ""

        parts: list[str] = []
        if documents:
            doc_lines = []
            for doc in documents:
                if not isinstance(doc, dict):
                    continue
                title = doc.get("title") or doc.get("url") or "Untitled"
                content = doc.get("content") or ""
                if content:
                    doc_lines.append(f"### {title}\n{content}")
            if doc_lines:
                parts.append("Reference documents:\n" + "\n\n".join(doc_lines))

        if artifacts:
            try:
                artifacts_json = json.dumps(artifacts, indent=2, default=str)
            except TypeError:
                artifacts_json = str(artifacts)
            parts.append(
                "Structured input data (this is your real supplied input — use it, "
                "do not claim it is missing):\n" + artifacts_json
            )

        return "\n\n".join(parts)

    async def _build_llm_messages(
        self,
        conversation_id: str,
        agent_id: str,
        agent_name: str,
        mission: str,
        allowed_delegations: list[str],
        tool_results_context: str,
        reference_context: str,
        user_id: str | None,
        current_message: str,
    ) -> list[LLMMessage]:
        conversation = await self._conversation_engine.load_conversation(conversation_id)
        memory_context = await self._load_memory_context(agent_id=agent_id, user_id=user_id)
        prompt_context = await self._load_prompt_context()
        roster_context = await self._load_agent_roster_context(allowed_delegations)

        system_prompt_parts = [
            f"You are {agent_name}.",
            f"Mission: {mission}",
        ]
        if roster_context:
            system_prompt_parts.append(roster_context)
        if prompt_context:
            system_prompt_parts.append(prompt_context)
        if memory_context:
            system_prompt_parts.append("Relevant memory:\n" + memory_context)
        if tool_results_context:
            system_prompt_parts.append(tool_results_context)
        if reference_context:
            system_prompt_parts.append(reference_context)

        llm_messages: list[LLMMessage] = [
            LLMMessage(role="system", content="\n\n".join(system_prompt_parts)),
        ]

        for message in conversation.messages[:-1]:
            llm_messages.append(LLMMessage(role=message.role.value, content=message.content))

        llm_messages.append(LLMMessage(role="user", content=current_message))
        return llm_messages

    async def _load_memory_context(self, agent_id: str, user_id: str | None) -> str:
        query = MemoryQuery(
            metadata_filters={
                "agent_id": agent_id,
                **({"user_id": user_id} if user_id else {}),
            },
            limit=5,
        )
        result = await self._memory_service.query_memory(query)
        if not result.records:
            return ""
        return "\n".join(f"- {record.content}" for record in result.records)

    async def _load_prompt_context(self) -> str:
        prompts = await self._prompt_library_service.list_prompts()
        system_prompt = next(
            (
                prompt.content
                for prompt in prompts
                if prompt.category.value.lower() == "system" and prompt.favorite
            ),
            "",
        )
        return system_prompt

    async def _load_agent_roster_context(self, allowed_delegations: list[str]) -> str:
        """Describe sibling agents this agent may delegate to."""
        siblings = await self._get_delegatable_agents(allowed_delegations)
        if not siblings:
            return ""

        roster_lines = [f"- {sibling.name} ({sibling.slug}): {sibling.mission}" for sibling in siblings]

        return (
            "You are part of a multi-agent system. You may delegate to these specialized agents "
            "when their expertise is a better fit than answering directly:\n" + "\n".join(roster_lines)
        )

    def _resolve_allowed_delegations(self, agent: Any) -> list[str]:
        if agent.allowed_delegations:
            return agent.allowed_delegations

        if self._seed_delegation_policy is None:
            seed_file = Path(__file__).resolve().parents[1] / "seeds" / "core_business_agents.json"
            try:
                data = json.loads(seed_file.read_text(encoding="utf-8"))
            except Exception:
                data = []

            policy: dict[str, list[str]] = {}
            if isinstance(data, list):
                for item in data:
                    if not isinstance(item, dict):
                        continue
                    slug = str(item.get("slug", "")).strip()
                    allowed = item.get("allowed_delegations", [])
                    if slug and isinstance(allowed, list):
                        policy[slug] = [str(target).strip() for target in allowed if str(target).strip()]
            self._seed_delegation_policy = policy

        return self._seed_delegation_policy.get(agent.slug, [])
