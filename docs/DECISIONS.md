# Architecture Decision Records (ADR)

**Purpose**: Document major architectural decisions for Jarvis Core  
**Format**: ADR (Architecture Decision Record) based on [adr.github.io](https://adr.github.io/)  
**Status**: All decisions are final unless explicitly reversed

---

## ADR-011: Automatic Two-Stage LLM Delegation Planning

**Date**: 2026-07-19
**Status**: ✅ **DECIDED** (Implemented)
**Authors**: Claude (Implementation)

### Context

Chat now executes through AgentRuntime/AgentOrchestrator by default (ADR-010), but the acting agent had no way to decide, from a free-form user message, whether the request should be handled by a specialist agent or a tool capability — that previously always required a caller (a workflow service) to pre-populate `capability_requests`/`delegation` metadata before calling `AgentOrchestrator.execute()`.

### Decision

Add two separate, narrowly-scoped LLM classification calls inside `AgentOrchestrator.execute()`:

1. **Delegation planning** — decide whether this request should be handed to one or more specialist agents, and in what order (produces a full ordered plan up front, not one hop re-decided at each level).
2. **Tool-use detection** — decide whether an already-assigned objective needs one of the acting agent's own tool capabilities. Delegation is deliberately not offered as an option here.

A single compound decision (delegate-or-tool-or-both in one call) was prototyped and rejected during implementation — it proved unreliable, with agents attempting to re-delegate work already assigned to them (e.g. a Research Agent handed "research Tesla" would sometimes delegate that straight back out to a sibling instead of doing it).

### Consequences

**Positive**:
- Free-form chat supports automatic specialist routing and multi-step chains (e.g. "research X and write a script") without new API endpoints or a new workflow engine
- Fully backward compatible with F13–F15 workflow services — gated off via `workflow`/`capability_requests`/`delegation` metadata presence, so existing explicit callers are unaffected

**Negative**:
- Adds 1–2 extra LLM calls per free-form chat turn (latency/cost)
- Classification is probabilistic, not a deterministic guarantee — empirically ~90–95% correct across repeated live testing against the real OpenAI API

### Related Files
- `backend/core/agent_orchestrator.py` — `_auto_plan_delegation`, `_auto_plan_tool_use`, `_execute_delegation_chain`, `_run_json_classification`

---

## ADR-010: AgentRuntime as the Default Chat Execution Path

**Date**: 2026-07-19
**Status**: ✅ **DECIDED** (Implemented)
**Authors**: Claude (Implementation)

### Context

F12 added AgentRuntime/AgentOrchestrator but wired them as an opt-in path only used when the frontend explicitly sent `agent_id` (the `/agents` page). The normal `/chat` page never sent `agent_id`, so real users never actually exercised the multi-agent architecture — an architecture audit found the agent system fully implemented but effectively unreachable from default chat.

### Decision

Resolve a default agent (`general` / General Assistant) in the API layer whenever `agent_id` is not supplied, and always route through AgentRuntime. The pre-existing direct-LLM/RAG branch is retained in code (not deleted, per "never remove functionality without request") but is no longer reachable in normal operation. If the default agent cannot be resolved, return a clean HTTP 503 — never fall back silently to the plain LLM path.

### Consequences

**Positive**:
- Every chat message, from either entry point, now benefits from the full agent architecture (roster awareness, tool execution, delegation)
- No duplicated execution path — default-agent resolution happens once, in the API layer, not inside AgentRuntime/AgentOrchestrator (which stay reusable by workflow services with their own explicit agent resolution)

**Negative**:
- RAG augmentation (`use_rag`) is no longer applied on the default chat path, since `AgentOrchestrator` doesn't call `RAGService` — this matches pre-existing `/agents` page behavior, but is a real behavior change from the old default-chat path
- AI Playground uses the same underlying endpoint and is now also routed through AgentRuntime by default (its custom system-prompt/temperature UI controls were already not being forwarded to the backend — a separate, pre-existing, unrelated gap)

### Related Files
- `backend/api/v1/conversations.py` — `_resolve_agent_id`, `chat_completion`, `chat_completion_stream`
- `backend/services/agent_service.py` — `get_default_agent`

---

## ADR-009: Supabase Configured for Agent/Project/User Persistence

**Date**: 2026-07-19
**Status**: ✅ **DECIDED** (Implemented)
**Authors**: Claude (Implementation), Supabase project provisioned by user

### Context

`AgentRepository`/`ProjectRepository`/`UserRepository` were always written against `SupabaseProvider`, but no environment had ever configured real `SUPABASE_URL`/`SUPABASE_KEY`. `SupabaseProvider.connect()` silently no-ops (sets `self.client = None`, raises nothing) when credentials are absent, so every agent operation — including startup seeding — failed with `DatabaseUnavailableError`, surfacing as a 503 on default-agent resolution.

### Decision

Configure real Supabase project credentials (service role key — this backend uses a single trusted global client rather than per-request RLS-scoped clients, so the service role is the correct key, not the anon key) in the root `.env`, and apply the three existing, previously-unapplied migrations (`20260719_f12_agents.sql`, `_f12_2_core_business_agents.sql`, `_f12_3_agent_slug.sql`) to provision the `agents` table and seed the 8 core business agents.

### Consequences

**Positive**:
- Agents/Projects/Users are now genuinely persisted; default-agent resolution and the full chat pipeline work end-to-end against a real database
- No code change was required to fix this — confirms the resolution logic (`AgentService.get_default_agent()`, `AgentRepository`) was already correct; the gap was purely missing infrastructure, not a defect

**Negative**:
- Conversations/Memory/Vector/Prompts remain in-memory (ADR-003, unchanged) — only the Supabase-backed repositories benefit from this change
- Real credentials now live in `.env` (confirmed gitignored via `.env*`) — must be rotated/managed per normal secret-handling practice before any shared or production deployment

### Related Files
- `.env` — `SUPABASE_URL`, `SUPABASE_KEY`
- `backend/migrations/20260719_f12_agents.sql`, `20260719_f12_2_core_business_agents.sql`, `20260719_f12_3_agent_slug.sql`
- `backend/core/supabase_provider.py`

---

## ADR-008: Pydantic v2 for Configuration Management

**Date**: 2026-07-18  
**Status**: ✅ **DECIDED** (Implemented)  
**Authors**: Claude (Implementation), ChatGPT (Review)

### Context

The Jarvis backend uses environment variables for configuration (database URLs, API keys, etc.). Initially, Pydantic v1 patterns were used with `class Config:` syntax. However:

1. Pydantic v2.x is installed (v2.13.4)
2. Old v1 syntax is deprecated in v2.x, removed in v3.0
3. Runtime deprecation warnings appeared during initialization
4. API key was not loading correctly from `.env` file

### Decision

Use **Pydantic v2 native pattern** with `model_config = SettingsConfigDict()` instead of deprecated `class Config:` syntax.

**Specific Implementation**:
```python
from pydantic import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str
    openai_api_key: str
    ...
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        extra="ignore",
        case_sensitive=False
    )
```

### Consequences

**Positive**:
- ✅ No deprecation warnings
- ✅ Future-proof (compatible with Pydantic v3)
- ✅ Clearer, more explicit configuration
- ✅ Environment variables load correctly on startup
- ✅ Better validation support for future extensions

**Negative**:
- 🔴 Breaking change (old code won't work with v2 syntax)
- 🔴 Requires knowledge of Pydantic v2 API

**Mitigation**: This is a one-time migration. All future settings management uses v2.

### Related Files
- `backend/core/config.py` - Settings class implementation
- `backend/main.py` - Settings loaded at app startup

---

## ADR-007: Environment Variables in Root `.env` Directory

**Date**: 2026-07-18  
**Status**: ✅ **DECIDED** (Implemented)  
**Authors**: Claude (Implementation), ChatGPT (Review)

### Context

The project had duplicate `.env` files:
- `backend/.env` (contained OPENAI_API_KEY)
- `.env` (root, contained only APP_NAME, APP_VERSION, DEBUG)

The Settings class loads from root `.env` (working directory), causing OPENAI_API_KEY to be None despite existing in `backend/.env`.

### Decision

**Single source of truth**: All environment variables must be in **root `.env`** file only.

**Rationale**:
1. Settings loads relative to working directory (root)
2. Deployment systems expect root `.env`
3. Single location easier to manage
4. Avoid confusion from duplicate files

**Implementation**:
```
jarvis-core/
├── .env                    # All runtime config here
├── .env.example           # Template for CI/CD
├── backend/
│   ├── main.py
│   ├── core/
│   └── ...                # No .env here
└── ...
```

### Consequences

**Positive**:
- ✅ Single source of truth
- ✅ API key loads correctly
- ✅ Clearer configuration management
- ✅ Matches deployment best practices

**Negative**:
- 🔴 `backend/.env` removed (old config lost)

**Mitigation**: `.env.example` documents all variables needed.

### Related Files
- `backend/core/config.py` - Loads from `.env`
- `.env` - Root configuration file
- `.env.example` - Template for new environments

---

## ADR-006: AsyncOpenAI 1.x for LLM Integration

**Date**: 2026-07-18  
**Status**: ✅ **DECIDED** (Implemented)  
**Authors**: Claude (Implementation), ChatGPT (Review)

### Context

Jarvis needs to integrate with OpenAI GPT models. The choice is between:
1. Sync `openai` library (blocking I/O)
2. Async `openai` library with AsyncOpenAI wrapper

FastAPI backend uses async/await throughout. Streaming requires non-blocking I/O.

### Decision

Use **AsyncOpenAI 1.109.1** with async/await patterns throughout.

**Implementation Pattern**:
```python
from openai import AsyncOpenAI

class OpenAIProvider(LLMProvider):
    async def generate(self, prompt: str) -> str:
        response = await self.client.chat.completions.create(...)
        return response.choices[0].message.content
    
    async def stream(self, prompt: str) -> AsyncGenerator[str, None]:
        stream = await self.client.chat.completions.create(
            stream=True,
            ...
        )
        async for chunk in stream:
            yield chunk.choices[0].delta.content or ""
```

### Consequences

**Positive**:
- ✅ Non-blocking I/O required for streaming
- ✅ Better resource utilization (handles many concurrent requests)
- ✅ Native async/await support in FastAPI
- ✅ Simpler error handling (no callback hell)

**Negative**:
- 🔴 All I/O must be async-compatible (can't use sync code in endpoints)
- 🔴 Requires async knowledge (steeper learning curve)

**Mitigation**: Established patterns (see `backend/core/openai_llm_provider.py`).

### Related Files
- `backend/core/openai_llm_provider.py` - LLM provider implementation
- `backend/api/v1/conversations.py` - Streaming endpoint using provider
- `backend/main.py` - Provider initialized at startup

---

## ADR-005: Server-Sent Events (SSE) for Real-Time Streaming

**Date**: 2026-07-18  
**Status**: ✅ **DECIDED** (Implemented)  
**Authors**: Claude (Implementation), ChatGPT (Review)

### Context

Jarvis needs real-time streaming of LLM responses (token-by-token). Transport options:
1. WebSockets (full duplex, complex)
2. Server-Sent Events (one-way server→client, simple)
3. Long polling (inefficient, old)
4. Polling (client-initiated, wasteful)

### Decision

Use **Server-Sent Events (SSE)** for streaming LLM responses.

**Rationale**:
1. One-way streaming (client only receives) matches chat perfectly
2. HTTP-based (works over any proxy/firewall)
3. Browser EventSource API native support
4. Simpler than WebSockets (no connection upgrade)
5. Perfect for chat use case (no client→server during stream)

**Implementation**:
```python
# Backend endpoint
@router.post("/api/v1/conversations/{id}/messages/stream")
async def stream_message(id: str):
    async def event_generator():
        yield f"data: {token}\n\n"  # SSE format
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )

# Frontend client
const eventSource = new EventSource(`/api/v1/conversations/${id}/messages/stream`);
eventSource.onmessage = (e) => console.log(e.data);  // Token received
```

### Consequences

**Positive**:
- ✅ Simpler than WebSockets
- ✅ Works over any HTTP proxy
- ✅ Browser native support (EventSource)
- ✅ Perfect for one-way server→client streams
- ✅ Automatic reconnection on drop

**Negative**:
- 🔴 No client→server messages during stream (acceptable for chat)
- 🔴 Browser must keep connection open (not suitable for all use cases)

**Future Consideration**: If two-way streaming needed, upgrade to WebSockets (different endpoint).

### Related Files
- `backend/api/v1/conversations.py` - Streaming endpoint
- `src/services/conversation-service.ts` - Frontend EventSource client
- `src/hooks/useStreamingMessage.ts` - React hook for streaming

---

## ADR-004: Dependency Injection via FastAPI `Depends`

**Date**: 2026-07-18  
**Status**: ✅ **DECIDED** (Implemented)  
**Authors**: Claude (Implementation), ChatGPT (Review)

### Context

FastAPI backend has multiple interchangeable services:
- LLM providers (OpenAI, future Claude, LLaMA)
- Vector stores (in-memory, future Pinecone, Weaviate)
- Conversation stores (in-memory, future PostgreSQL)

Services must be testable and swappable.

### Decision

Use **FastAPI Depends** for dependency injection. Never instantiate services directly.

**Implementation Pattern**:
```python
# In dependencies.py
def get_llm_provider() -> LLMProvider:
    return SERVICE_REGISTRY.get_llm_provider()

def get_conversation_store() -> ConversationStore:
    return SERVICE_REGISTRY.get_conversation_store()

# In API endpoints
@router.post("/api/v1/conversations/{id}/messages")
async def send_message(
    id: str,
    provider: LLMProvider = Depends(get_llm_provider),
    store: ConversationStore = Depends(get_conversation_store)
):
    response = await provider.generate(...)
    store.save_message(...)
    return response
```

### Consequences

**Positive**:
- ✅ Services easily testable (inject mocks)
- ✅ Services easily swappable (change registry)
- ✅ Configuration centralized (in registry)
- ✅ Dependencies explicitly visible (in function signature)

**Negative**:
- 🔴 Slightly more boilerplate (Depends() calls)
- 🔴 Requires understanding of FastAPI lifecycle

**Rule**: No direct imports of services (always use Depends).

### Related Files
- `backend/core/dependencies.py` - Dependency functions
- `backend/core/service_registry.py` - Service instantiation
- `backend/api/v1/*.py` - All endpoints use Depends

---

## ADR-003: In-Memory Stores with Provider Pattern (MVP)

**Date**: 2026-07-18  
**Status**: ✅ **DECIDED** (Implemented + Documented for future migration)  
**Authors**: Claude (Implementation), ChatGPT (Review)

### Context

Jarvis needs persistent data (conversations, messages, documents). Options:
1. Supabase PostgreSQL (fully managed, but requires schema design)
2. In-memory stores (fast for development, doesn't persist)
3. SQLite (simple, but limited concurrency)

MVP goal is rapid development. Long-term goal is production database.

### Decision

**MVP (Current)**: Use in-memory stores with provider pattern  
**Future**: Migrate to Supabase PostgreSQL via providers

**Implementation**:
```python
# Provider interface
class ConversationStore(ABC):
    @abstractmethod
    async def get(self, id: str) -> Optional[Conversation]:
        pass

# In-memory implementation
class InMemoryConversationStore(ConversationStore):
    def __init__(self):
        self.store: dict[str, Conversation] = {}
    
    async def get(self, id: str) -> Optional[Conversation]:
        return self.store.get(id)

# PostgreSQL implementation (future)
class PostgresConversationStore(ConversationStore):
    async def get(self, id: str) -> Optional[Conversation]:
        return await self.db.query(Conversation).filter_by(id=id).first()
```

### Consequences

**Positive**:
- ✅ Fast MVP development (no schema design)
- ✅ Easy to test (no database setup)
- ✅ Can swap providers later (extensible)
- ✅ Clearly marked for future migration

**Negative**:
- 🔴 Data not persistent (restarting backend loses data)
- 🔴 Single instance only (no horizontal scaling)
- 🔴 Not suitable for production without changes

**Migration Path**:
1. Implement PostgreSQL provider
2. Update service registry to use new provider
3. Run migration script
4. No API changes needed (interface unchanged)

**Timeline**: Plan PostgreSQL migration for Sprint+2 (production readiness).

### Related Files
- `backend/repositories/` - All store implementations
- `backend/core/service_registry.py` - Provider selection
- `backend/core/dependencies.py` - Provider injection

---

## ADR-002: Service + Repository Pattern for Clean Architecture

**Date**: 2026-07-18  
**Status**: ✅ **DECIDED** (Implemented)  
**Authors**: Claude (Implementation), ChatGPT (Review)

### Context

FastAPI backend needs clean separation between:
- HTTP concerns (request parsing, status codes)
- Business logic (validation, orchestration)
- Data access (database queries, persistence)

Without clear separation, code becomes tangled and hard to test.

### Decision

Use **Service + Repository pattern** with strict layer separation.

**Layer Structure**:
```
API Routes
    ↓ (call service)
Services (business logic)
    ↓ (call repository)
Repositories (data access)
    ↓ (execute)
Database
```

**Example**:
```python
# Repository (data access)
class ConversationRepository(ABC):
    async def save(self, conversation: Conversation) -> None:
        pass

# Service (business logic)
class ConversationService:
    def __init__(self, repo: ConversationRepository):
        self.repo = repo
    
    async def create_conversation(self, user_id: str, title: str):
        conversation = Conversation(id=uuid4(), user_id=user_id, title=title)
        await self.repo.save(conversation)
        return conversation

# API endpoint
@router.post("/api/v1/conversations")
async def create(body: CreateConversationRequest, service: ConversationService = Depends(...)):
    return await service.create_conversation(body.user_id, body.title)
```

### Consequences

**Positive**:
- ✅ Clear separation of concerns
- ✅ Easy to test (inject mock repository)
- ✅ Business logic independent of database
- ✅ Easy to swap data stores (in-memory → PostgreSQL)

**Negative**:
- 🔴 More files/classes (more structure)
- 🔴 Requires discipline to maintain

**Rule**: API endpoints never access database directly (always via service).

### Related Files
- `backend/api/v1/` - HTTP endpoints
- `backend/services/` - Business logic
- `backend/repositories/` - Data access

---

## ADR-001: Monorepo with Next.js Frontend + FastAPI Backend

**Date**: 2026-07-18  
**Status**: ✅ **DECIDED** (Implemented)  
**Authors**: Claude (Implementation), ChatGPT (Review)

### Context

Jarvis needs both frontend (UI) and backend (API). Options:
1. **Monorepo**: Both in single repository
2. **Separate repos**: Frontend and backend in different repositories

Tradeoffs:
- Monorepo: Easier to keep in sync, single build, harder at scale
- Separate: Independently scaled, harder to coordinate

### Decision

Use **monorepo structure** with frontend in `/app` and backend in `/backend`.

**Rationale**:
1. Smaller team (easier coordination in monorepo)
2. API and UI need to stay in sync
3. Single Docker build covers full stack
4. Simpler deployment (one repo to deploy)
5. Can migrate to separate repos later if needed

**Structure**:
```
jarvis-core/
├── app/                    # Next.js frontend
├── src/                    # Frontend source
├── backend/                # FastAPI backend
├── docs/                   # Shared documentation
├── .env                    # Shared environment
└── requirements.txt        # Python deps
```

### Consequences

**Positive**:
- ✅ Single repository to manage
- ✅ Easier API/UI synchronization
- ✅ Simpler deployment (one Docker build)
- ✅ Shared documentation location
- ✅ No duplication of config files

**Negative**:
- 🔴 Larger repository (slower clones)
- 🔴 Single CI/CD pipeline (all or nothing)
- 🔴 Frontend and backend changes in same PR

**Scaling Plan**: If project grows significantly, can split to separate repos (frontend static hosting + backend Vercel/Heroku).

### Related Files
- `package.json` - Frontend dependencies and scripts
- `requirements.txt` - Backend dependencies
- `next.config.ts` - Frontend configuration
- `backend/main.py` - Backend entry point

---

## Summary of Active Decisions

| ADR | Decision | Status | Impact |
|-----|----------|--------|--------|
| ADR-001 | Monorepo structure | ✅ Final | Architecture |
| ADR-002 | Service + Repository pattern | ✅ Final | Backend code org |
| ADR-003 | In-memory stores (MVP→PostgreSQL) | ✅ Final (Agents/Projects/Users now on real Supabase per ADR-009; Conversations/Memory/Vector/Prompts still in-memory) | Persistence |
| ADR-004 | Dependency injection via Depends | ✅ Final | Testability |
| ADR-005 | SSE for streaming | ✅ Final | Real-time delivery |
| ADR-006 | AsyncOpenAI 1.x | ✅ Final | LLM integration |
| ADR-007 | Root `.env` for config | ✅ Final | Configuration |
| ADR-008 | Pydantic v2 settings | ✅ Final | Type safety |
| ADR-009 | Supabase configured for Agent/Project/User persistence | ✅ Final | Persistence, unblocks default-agent resolution |
| ADR-010 | AgentRuntime as default chat execution path | ✅ Final | Chat architecture |
| ADR-011 | Automatic two-stage LLM delegation planning | ✅ Final | Agent orchestration |

---

## How to Add New ADRs

When making a significant architectural decision:

1. **Create new ADR**: `ADR-00X: Decision Title`
2. **Complete template**:
   - Date
   - Status (PROPOSED, DECIDED, DEPRECATED, SUPERSEDED)
   - Context (why this decision?)
   - Decision (what we're doing)
   - Consequences (positive/negative trade-offs)
   - Related files
3. **Keep history**: Never delete old ADRs (even if superseded)
4. **Link decisions**: Reference other ADRs if related

---

## Decision Evolution

### Future Reversals (If Circumstances Change)

- **ADR-003**: If single-instance limitation becomes blocking, migrate to PostgreSQL
- **ADR-005**: If two-way streaming needed, upgrade to WebSockets
- **ADR-001**: If team scales significantly, consider separate repos

All reversals must be documented as new ADRs (SUPERSEDED status).

---

*End of DECISIONS.md*
