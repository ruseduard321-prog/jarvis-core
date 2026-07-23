from __future__ import annotations

import json
import logging
import time
from typing import Any

from backend.core.agent_runtime import AgentRuntime
from backend.core.config import Settings
from backend.core.conversation_engine import ConversationEngine
from backend.core.cost_tracker import CostTracker
from backend.services.agent_service import AgentService
from backend.schemas.research import (
    ResearchFinding,
    ResearchPackage,
    ResearchSource,
)

logger = logging.getLogger(__name__)


class ResearchWorkflowService:
    """Concrete production research workflow built on existing agent runtime orchestration."""

    # Keep trying candidate sources until this many yield real, substantive content...
    TARGET_GOOD_SOURCES = 5
    # ...but never synthesize from fewer than this many — prefer a clean failure over
    # fabricated content when the retrieved material is insufficient.
    MIN_GOOD_SOURCES = 1
    # A real article/abstract is always well over this; DuckDuckGo's non-JS redirect
    # stub pages (see _STUB_MARKERS) land at ~100-200 chars.
    MIN_CONTENT_LENGTH = 300
    # Ceiling used to scope the _STUB_MARKERS check to genuinely stub-length pages.
    # Real articles routinely contain one of these phrases incidentally (a cookie
    # banner, a "enable JavaScript to view comments" widget notice, etc.) without
    # being a redirect stub — scanning content of any length for these substrings
    # rejected valid, substantial DuckDuckGo-sourced sources for that reason alone.
    _STUB_MAX_LENGTH = 500
    _STUB_MARKERS = ("you are being redirected", "non-javascript site", "enable javascript")
    # Keeps a single source's content well within gpt-3.5-turbo's context window even
    # after JSON-wrapping and conversation-history overhead across multiple sources.
    MAX_URL_CONTENT_LENGTH = 6000

    def __init__(
        self,
        conversation_engine: ConversationEngine,
        agent_runtime: AgentRuntime,
        agent_service: AgentService,
        settings: Settings | None = None,
        cost_tracker: CostTracker | None = None,
    ) -> None:
        self._conversation_engine = conversation_engine
        self._agent_runtime = agent_runtime
        self._agent_service = agent_service
        self._settings = settings or Settings()
        self._cost_tracker = cost_tracker or CostTracker()

    async def _timed_execute(self, **kwargs: Any) -> dict[str, Any]:
        """Wraps `AgentRuntime.execute()` with duration tracking, accumulating call
        metrics/cost onto `self._call_durations_ms`/`self._call_texts` for this run."""
        started_at = time.perf_counter()
        result = await self._agent_runtime.execute(**kwargs)
        self._call_durations_ms.append((time.perf_counter() - started_at) * 1000)
        self._call_texts.append((str(kwargs.get("message", "")), str(result.get("content", ""))))
        return result

    def _build_provider_metrics(self, success: bool, failure_reason: str | None = None) -> dict[str, Any]:
        model = self._settings.default_llm_model
        total_duration_ms = round(sum(self._call_durations_ms), 2)
        cost_estimate = self._cost_tracker.estimate_text_cost(
            provider="openai",
            model=model,
            input_text="\n".join(text for text, _ in self._call_texts),
            output_text="\n".join(text for _, text in self._call_texts),
        )
        provider_metrics = {
            "provider": "openai",
            "model": model,
            "call_count": len(self._call_durations_ms),
            "duration_ms": total_duration_ms,
            "success": success,
            "failure_reason": failure_reason,
        }
        return {"provider_metrics": provider_metrics, "cost_estimate": cost_estimate.__dict__}

    async def execute(
        self,
        topic: str,
        constraints: str | None,
        user_id: str | None,
    ) -> ResearchPackage:
        logger.info("Original topic received", extra={"topic": topic, "constraints": constraints})
        self._call_durations_ms: list[float] = []
        self._call_texts: list[tuple[str, str]] = []

        research_agent_id = await self._resolve_research_agent_id()
        if not research_agent_id:
            return self._build_failure_package(topic, "No active research agent is available")

        conversation = await self._conversation_engine.create_conversation(
            title=f"Research: {topic[:80]}",
            metadata={"workflow": "research_package"},
        )

        search_query = topic if not constraints else f"{topic} | constraints: {constraints}"
        logger.info("Search query generated", extra={"topic": topic, "search_query": search_query})
        search_result = await self._timed_execute(
            conversation_id=conversation.context.conversation_id,
            agent_id=research_agent_id,
            message=(
                "Use web search to find high quality sources. Return JSON only with shape: "
                '{"results":[{"title":"...","url":"...","snippet":"..."}]}. '
                f"Query: {search_query}"
            ),
            user_id=user_id,
            metadata={
                "workflow": "research_package",
                "artifacts": [],
                "capability_requests": [
                    {
                        "capability": "web.search",
                        "reason": "Find credible, recent sources for the requested topic",
                        "args": {"query": search_query, "limit": 8},
                    }
                ],
            },
        )

        # Prefer the search tool's own raw output over the agent's text relay of it —
        # relying on the LLM to transcribe results back out as JSON is an unnecessary and
        # unreliable extra hop when the tool already returned structured data directly.
        search_tool_output = self._extract_tool_output(search_result, "web.search")
        if search_tool_output and isinstance(search_tool_output.get("results"), list):
            candidate_sources = self._sources_from_raw_results(search_tool_output["results"])
        else:
            candidate_sources = self._extract_sources_from_text(search_result.get("content", ""))

        logger.info(
            "Search results received",
            extra={
                "topic": topic,
                "search_query": search_query,
                "result_count": len(candidate_sources),
                "results": [
                    {"title": s.title, "url": s.url, "snippet": s.snippet} for s in candidate_sources
                ],
            },
        )
        if not candidate_sources:
            return self._build_failure_package(topic, "No usable search results were produced")

        enriched_sources: list[ResearchSource] = []
        normalized_documents: list[dict[str, Any]] = []
        partial_failures: list[dict[str, str]] = []
        seen_urls: set[str] = set()

        for source in candidate_sources:
            if len(enriched_sources) >= self.TARGET_GOOD_SOURCES:
                break
            url = source.url.strip()
            if not url:
                continue
            try:
                read_result = await self._timed_execute(
                    conversation_id=conversation.context.conversation_id,
                    agent_id=research_agent_id,
                    message=(
                        "Read this URL and return JSON only with shape: "
                        '{"title":"...","content":"...","url":"..."}. '
                        "Relay the fetched content verbatim in 'content' — do not summarize, "
                        "paraphrase, or invent anything. If the tool result above contains no "
                        "real article content (e.g. a redirect notice or empty page), set "
                        '"content" to exactly "INSUFFICIENT_CONTENT" instead of making something up. '
                        f"URL: {url}"
                    ),
                    user_id=user_id,
                    metadata={
                        "workflow": "research_package",
                        "artifacts": normalized_documents,
                        "capability_requests": [
                            {
                                "capability": "url.read",
                                "reason": "Extract full page content for synthesis",
                                "args": {"url": url, "max_length": self.MAX_URL_CONTENT_LENGTH},
                            }
                        ],
                    },
                )

                # Same principle as the search step: use the URL Reader tool's own raw
                # output (real HTTP status, real fetched text) instead of asking the LLM
                # to relay it — an LLM asked to "return content" for a page with nothing
                # real to report will fabricate a plausible-looking article rather than
                # say so, which is exactly how unrelated topics end up in the package.
                raw_document = self._extract_tool_output(read_result, "url.read")
                if raw_document is not None:
                    http_status = (raw_document.get("metadata") or {}).get("status_code")
                    fetched_title = str(raw_document.get("title") or source.title or "")
                    fetched_content = str(raw_document.get("content") or "")
                    fetched_url = str(raw_document.get("url") or url)
                    tool_call_succeeded = True
                    text_parse_succeeded = True
                else:
                    parsed_doc = self._extract_document_from_text(read_result.get("content", ""), fallback_url=url)
                    http_status = None
                    fetched_title = str((parsed_doc or {}).get("title", ""))
                    fetched_content = str((parsed_doc or {}).get("content", ""))
                    fetched_url = str((parsed_doc or {}).get("url", url))
                    tool_call_succeeded = False
                    text_parse_succeeded = parsed_doc is not None

                # Diagnostics only — this does not affect the accept/reject decision below,
                # which still comes solely from self._is_content_sufficient().
                normalized_url = (fetched_url or url).strip()
                is_duplicate_url = normalized_url in seen_urls
                seen_urls.add(normalized_url)
                content_sufficient = self._is_content_sufficient(fetched_content)
                if content_sufficient:
                    rejection_reason = None
                elif is_duplicate_url:
                    rejection_reason = "duplicate"
                else:
                    rejection_reason = self._diagnostic_rejection_reason(
                        fetched_content, tool_call_succeeded, text_parse_succeeded
                    )

                logger.info(
                    "Source fetched",
                    extra={
                        "topic": topic,
                        "url": url,
                        "fetched_url": fetched_url,
                        "fetch_succeeded": tool_call_succeeded or text_parse_succeeded,
                        "http_status": http_status,
                        "title": fetched_title,
                        "text_length": len(fetched_content),
                        "content_sufficient": content_sufficient,
                        "is_duplicate_url": is_duplicate_url,
                        "rejection_reason": rejection_reason,
                    },
                )

                if not content_sufficient:
                    reason = "Extracted content too short or a redirect/stub page with no real article content"
                    logger.info(
                        "Source rejected — insufficient content, trying next candidate",
                        extra={
                            "topic": topic,
                            "url": url,
                            "text_length": len(fetched_content),
                            "rejection_reason": rejection_reason,
                        },
                    )
                    partial_failures.append({"url": url, "error": reason})
                    continue

                normalized_documents.append({"title": fetched_title, "content": fetched_content, "url": fetched_url})
                enriched_sources.append(
                    ResearchSource(
                        title=fetched_title or source.title,
                        url=fetched_url or url,
                        snippet=source.snippet,
                    )
                )
                logger.info(
                    "Source accepted",
                    extra={
                        "topic": topic,
                        "url": url,
                        "text_length": len(fetched_content),
                        "accepted_count": len(normalized_documents),
                    },
                )
            except Exception as exc:  # pragma: no cover - defensive path for tool/runtime issues
                logger.exception(
                    "Failed to read source URL",
                    extra={"topic": topic, "url": url, "rejection_reason": "fetch failure"},
                )
                partial_failures.append({"url": url, "error": str(exc)})

        logger.info(
            "Source gathering complete",
            extra={
                "topic": topic,
                "accepted_sources": len(normalized_documents),
                "rejected_sources": len(partial_failures),
                "candidate_sources": len(candidate_sources),
                "min_good_sources": self.MIN_GOOD_SOURCES,
                "target_good_sources": self.TARGET_GOOD_SOURCES,
            },
        )

        if len(normalized_documents) < self.MIN_GOOD_SOURCES:
            logger.warning(
                "Insufficient good sources gathered — workflow will stop",
                extra={
                    "topic": topic,
                    "normalized_documents_count": len(normalized_documents),
                    "min_good_sources": self.MIN_GOOD_SOURCES,
                    "candidate_sources_count": len(candidate_sources),
                    "partial_failures": partial_failures,
                },
            )
            return self._build_failure_package(
                topic,
                f"Insufficient research data: only {len(normalized_documents)} of "
                f"{len(candidate_sources)} candidate sources contained real, readable content",
            )

        # Embed the validated documents directly in the prompt text rather than relying on
        # conversation history to carry them — history also contains the read attempts for
        # sources that were rejected above, and letting the synthesis call rediscover which
        # turns were "good" from replayed history is exactly how off-topic/rejected material
        # was leaking into the final package. Explicit, validated-only input is reliable.
        documents_digest = "\n\n".join(
            f"Source {index + 1} — {doc.get('title') or doc.get('url')} ({doc.get('url')}):\n"
            f"{str(doc.get('content', ''))[:3000]}"
            for index, doc in enumerate(normalized_documents)
        )

        synthesis_prompt = (
            f"Topic: {topic}\n\n"
            "Synthesize ONLY the research documents below (and no other source) into strict "
            "JSON with keys: executive_summary (string), findings (array of {title, details, "
            "source_urls}), key_facts (array of strings), timeline (array of strings), "
            "open_questions (array of strings), recommended_angle (string). "
            "Use ONLY facts present in the documents below — never invent entities, people, "
            "places, or events that are not in them, and ignore any other topic mentioned "
            "earlier in this conversation. If these documents do not actually cover the "
            "requested topic, say so plainly in open_questions and keep findings/key_facts "
            "empty rather than fabricating unrelated content. Return JSON only.\n\n"
            f"{documents_digest}"
        )

        synthesis_result = await self._timed_execute(
            conversation_id=conversation.context.conversation_id,
            agent_id=research_agent_id,
            message=synthesis_prompt,
            user_id=user_id,
            metadata={
                "workflow": "research_package",
                "documents": normalized_documents,
                "artifacts": normalized_documents,
                "constraints": constraints,
            },
        )

        parsed_synthesis = self._extract_json_object(synthesis_result.get("content", ""))
        if not parsed_synthesis:
            return self._build_failure_package(topic, "Synthesis step did not produce valid JSON")

        findings = [
            ResearchFinding(
                title=str(item.get("title", "Untitled finding")),
                details=str(item.get("details", "")),
                source_urls=[str(url) for url in item.get("source_urls", []) if str(url).strip()],
            )
            for item in parsed_synthesis.get("findings", [])
            if isinstance(item, dict)
        ]

        status = "success" if not partial_failures else "partial"
        key_facts = [str(fact) for fact in parsed_synthesis.get("key_facts", []) if str(fact).strip()]
        package = ResearchPackage(
            topic=topic,
            executive_summary=str(parsed_synthesis.get("executive_summary", "")),
            findings=findings,
            key_facts=key_facts,
            timeline=[str(entry) for entry in parsed_synthesis.get("timeline", []) if str(entry).strip()],
            sources=enriched_sources,
            open_questions=[
                str(question)
                for question in parsed_synthesis.get("open_questions", [])
                if str(question).strip()
            ],
            recommended_angle=str(parsed_synthesis.get("recommended_angle", "")),
            metadata={
                "status": status,
                "constraints": constraints,
                "partial_failures": partial_failures,
                "conversation_id": conversation.context.conversation_id,
                "source_count": len(enriched_sources),
                **self._build_provider_metrics(success=True),
            },
        )

        logger.info(
            "ResearchPackage created",
            extra={
                "topic": package.topic,
                "facts": len(findings) + len(key_facts),
                "sources": len(enriched_sources),
                "status": status,
            },
        )
        logger.info("Workflow may continue" if status == "success" else "Workflow may continue (partial)")
        return package

    async def _resolve_research_agent_id(self) -> str | None:
        """Resolve an active research agent ID across ID/slug naming differences."""
        for candidate in ("research_agent", "research"):
            try:
                candidate_agent = await self._agent_service.get_agent(candidate)
                if candidate_agent.is_active:
                    return candidate_agent.id
            except Exception:
                continue

        try:
            agents = await self._agent_service.list_agents(active_only=True)
        except Exception:
            return None

        for agent in agents:
            if agent.slug == "research" or agent.name.lower() == "research agent":
                return agent.id
        return None

    def _build_failure_package(self, topic: str, reason: str) -> ResearchPackage:
        logger.warning(
            "Workflow halted — insufficient research data",
            extra={"topic": topic, "reason": reason, "min_good_sources": self.MIN_GOOD_SOURCES},
        )
        return ResearchPackage(
            topic=topic,
            executive_summary="",
            findings=[],
            key_facts=[],
            timeline=[],
            sources=[],
            open_questions=[reason],
            recommended_angle="",
            metadata={"status": "failed", "reason": reason, **self._build_provider_metrics(success=False, failure_reason=reason)},
        )

    def _extract_tool_output(self, runtime_result: dict[str, Any], capability: str) -> dict[str, Any] | None:
        """Pull a tool's raw structured output out of an AgentRuntime.execute() result,
        for the given capability. Returns None if that tool wasn't called or failed —
        callers must fall back to the agent's own text response in that case."""
        for call in runtime_result.get("tool_calls", []) or []:
            if call.get("capability") == capability and call.get("success") and isinstance(call.get("output"), dict):
                return call["output"]
        return None

    def _sources_from_raw_results(self, raw_results: list[Any]) -> list[ResearchSource]:
        sources: list[ResearchSource] = []
        for item in raw_results:
            if not isinstance(item, dict):
                continue
            url = str(item.get("url", "")).strip()
            if not url:
                continue
            sources.append(
                ResearchSource(
                    title=str(item.get("title", "")).strip() or None,
                    url=url,
                    snippet=str(item.get("snippet", "")).strip() or None,
                )
            )
        return sources

    def _is_content_sufficient(self, content: str) -> bool:
        """Reject content that is too short to be a real article, or matches a known
        redirect/stub pattern (e.g. DuckDuckGo's non-JS redirect interstitial) — prefer
        skipping a bad source over letting the synthesis step work from near-nothing.

        The stub-marker check only applies below `_STUB_MAX_LENGTH`: real articles are
        routinely several times longer than a redirect stub and may incidentally contain
        one of these phrases (e.g. a comments widget's own "enable JavaScript" notice)
        without themselves being a stub page."""
        text = (content or "").strip()
        if not text or text.upper() == "INSUFFICIENT_CONTENT":
            return False
        if len(text) < self.MIN_CONTENT_LENGTH:
            return False
        if len(text) <= self._STUB_MAX_LENGTH:
            lowered = text.lower()
            if any(marker in lowered for marker in self._STUB_MARKERS):
                return False
        return True

    def _diagnostic_rejection_reason(
        self,
        content: str,
        tool_call_succeeded: bool,
        text_parse_succeeded: bool,
    ) -> str:
        """Diagnostics-only categorization of why a source was rejected, for logging.
        Mirrors the same checks _is_content_sufficient() applies (in the same order) —
        it does not participate in the actual accept/reject decision and must never
        diverge from that method's outcome for a given input."""
        text = (content or "").strip()
        if not tool_call_succeeded and not text_parse_succeeded:
            return "parse failure"
        if not text or text.upper() == "INSUFFICIENT_CONTENT":
            return "fetch failure"
        if len(text) < self.MIN_CONTENT_LENGTH:
            return "too short"
        if len(text) <= self._STUB_MAX_LENGTH:
            lowered = text.lower()
            if any(marker in lowered for marker in self._STUB_MARKERS):
                return "stub page"
        return "other"

    def _extract_sources_from_text(self, content: str) -> list[ResearchSource]:
        payload = self._extract_json_object(content)
        if not payload:
            return []

        items = payload.get("results", [])
        sources: list[ResearchSource] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            url = str(item.get("url", "")).strip()
            if not url:
                continue
            sources.append(
                ResearchSource(
                    title=str(item.get("title", "")).strip() or None,
                    url=url,
                    snippet=str(item.get("snippet", "")).strip() or None,
                )
            )
        return sources

    def _extract_document_from_text(self, content: str, fallback_url: str) -> dict[str, Any] | None:
        payload = self._extract_json_object(content)
        if not payload:
            return None

        extracted_content = str(payload.get("content", "")).strip()
        if not extracted_content:
            return None

        return {
            "title": str(payload.get("title", "")).strip() or "Untitled",
            "content": extracted_content,
            "url": str(payload.get("url", "")).strip() or fallback_url,
        }

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

        snippet = text[start : end + 1]
        try:
            loaded = json.loads(snippet)
            return loaded if isinstance(loaded, dict) else None
        except json.JSONDecodeError:
            return None
