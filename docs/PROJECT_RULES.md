# Jarvis Project Rules

**Version**: 1.0  
**Last Updated**: 2026-07-18  
**Status**: Active

These rules define the permanent development workflow and architectural constraints for Jarvis Core. All contributors must follow these rules.

---

## Team Roles

### Claude (Implementation)
- **Responsibility**: Write code, implement features, fix bugs
- **Authority**: Full implementation control within approved architecture
- **Constraints**: Cannot deviate from approved architecture
- **Workflow**: 
  1. Read architecture doc for feature
  2. Ask architecture questions if unclear
  3. Implement according to specs
  4. Update documentation after completion

### ChatGPT (Architecture & Review)
- **Responsibility**: Design systems, review code, approve features
- **Authority**: Final decision on architecture
- **Constraints**: Must not force unnecessary complexity
- **Workflow**:
  1. Listen to requirements
  2. Design architecture/API
  3. Explain design decisions
  4. Review implementation
  5. Approve or request changes

---

## Core Development Rules

### 🚫 Never Implement Before Architecture is Approved

**Rule**: Do not write code until the feature architecture is reviewed and approved by ChatGPT.

**Process**:
1. Claude: Describe what you plan to implement
2. ChatGPT: Review design, ask questions, suggest improvements
3. ChatGPT: Approve architecture
4. Claude: Implement according to approved design

**Exceptions**: Bug fixes, documentation updates (if no architecture change)

**Violation Consequence**: Entire feature must be rewritten if architecture is wrong.

---

### 🚫 Never Skip Code Review

**Rule**: Every completed feature must be reviewed before merging to main.

**Process**:
1. Claude: Complete implementation
2. Claude: Update PROJECT_STATE.md
3. Claude: Run tests (if applicable)
4. ChatGPT: Review code for:
   - Architecture adherence
   - Code quality
   - Security implications
   - Performance impact
5. ChatGPT: Approve or request changes
6. Claude: Merge to main only after approval

**Violation Consequence**: Code reverted, feature must be rewritten.

---

### 📝 Update Documentation After Every Feature

**Rule**: Every completed feature must update project documentation.

**Required Updates**:
1. **PROJECT_STATE.md**
   - Move feature from "Current Feature" → "Completed Features"
   - Update "Current Goal" if changed
   - Update progress percentages (Backend/Frontend/etc.)
   - Update "Next Features" if roadmap changed
   - Update test coverage if tests added

2. **CHANGELOG.md**
   - Add entry at top with: Date, Version, Feature description, any breaking changes

3. **DECISIONS.md** (if architecture changed)
   - Create new ADR if significant architectural decision was made
   - Document context, decision, and consequences
   - Never remove old ADRs (history is important)

4. **Architecture Docs** (if applicable)
   - Update `/docs/architecture/` files
   - Add diagrams if structure changed
   - Update API docs if endpoints added

**When Not Required**: 
- Bug fixes (small fixes can update just CHANGELOG)
- Documentation-only changes
- Refactoring with no external behavior change

**Violation Consequence**: Feature is considered incomplete, blocks merge.

---

## Architecture Rules

### 🏗️ Keep Architecture Modular

**Rule**: Every component should be independent, testable, and replaceable.

**Principles**:
- Single Responsibility Principle (one job per class/function)
- Low coupling (minimal dependencies between modules)
- High cohesion (related functionality grouped together)
- Clear interfaces (well-defined inputs/outputs)

**Examples**:
- ✅ LLMProvider interface with OpenAI implementation (can swap providers)
- ✅ ConversationStore interface with in-memory implementation (can swap for DB)
- ❌ Hard-coded OpenAI calls scattered through code (can't swap providers)
- ❌ Database access mixed with business logic (can't test without DB)

---

### 💉 Dependency Injection Everywhere

**Rule**: All dependencies must be injected, never created directly.

**Backend Pattern** (FastAPI):
```python
# ✅ CORRECT
def my_endpoint(provider: LLMProvider = Depends(get_llm_provider)):
    response = provider.generate(...)
    return response

# ❌ WRONG
def my_endpoint():
    provider = OpenAI(api_key=...)  # Hard-coded, can't swap
    response = provider.generate(...)
    return response
```

**Frontend Pattern** (React):
```typescript
// ✅ CORRECT - Props passed down
function ChatComponent({ conversationService }: Props) {
  const messages = conversationService.getMessages();
  return ...;
}

// ❌ WRONG - Service imported directly
function ChatComponent() {
  const messages = conversationService.getMessages();  // Hard to test
  return ...;
}
```

**Benefits**:
- Easy to test (inject mock services)
- Easy to swap implementations
- Configuration centralized
- Clear dependencies visible

---

### 📦 Separation of Concerns

**Backend Layers**:
1. **API Layer** (`/backend/api/`) - HTTP endpoints only
   - Extract request parameters
   - Call service layer
   - Format response
   - Handle HTTP errors

2. **Service Layer** (`/backend/services/`) - Business logic
   - Validate inputs
   - Orchestrate operations
   - Apply business rules
   - Handle domain exceptions

3. **Repository Layer** (`/backend/repositories/`) - Data access
   - Query database
   - Create/update/delete records
   - Handle storage errors
   - Return domain objects

4. **Schema Layer** (`/backend/schemas/`) - Request/response validation
   - Pydantic models
   - Type validation
   - Serialization

**Frontend Layers**:
1. **Pages** (`/app/`) - Route entry points
   - Set up layout
   - Call services
   - Handle page-level state

2. **Components** (`/src/components/`) - Reusable UI
   - Render UI
   - Handle local state
   - Emit events

3. **Services** (`/src/services/`) - API clients
   - HTTP requests
   - Response parsing
   - Error handling

4. **Hooks** (`/src/hooks/`) - Reusable logic
   - Custom React hooks
   - State management
   - Side effects

**Rule**: Never bypass layers. API must go through service, service through repository.

---

### 🔒 Keep Dependencies Clean

**Rule**: Respect the dependency hierarchy. Lower levels should not depend on higher levels.

**Correct Hierarchy**:
```
API Routes
    ↓
Services
    ↓
Repositories
    ↓
Database Schemas
```

**❌ Wrong**: Repository calls API route  
**❌ Wrong**: Service imports API model directly  
**✅ Right**: API imports from service, service from repository

---

## Code Quality Rules

### 🎯 Type Safety (Both Languages)

**Backend (Python)**:
```python
# ✅ CORRECT - Full type hints
def create_conversation(
    user_id: str,
    title: str,
    messages: list[Message] = None
) -> Conversation:
    """Create a new conversation."""
    ...

# ❌ WRONG - Missing type hints
def create_conversation(user_id, title, messages=None):
    ...
```

**Frontend (TypeScript)**:
```typescript
// ✅ CORRECT - Strict types
interface ConversationProps {
  id: string;
  messages: Message[];
  onSendMessage: (text: string) => Promise<void>;
}

// ❌ WRONG - Using any
function Conversation(props: any) {
  ...
}
```

---

### 📚 Keep Documentation Synchronized

**Rule**: Code and documentation must stay in sync. If code changes, docs must update.

**What to Document**:
- Class/function purpose and behavior
- Parameters and return types
- Exceptions that can be raised
- Usage examples for complex functions
- Architectural decisions in code comments
- Configuration options in README

**Tools**:
- Python: Docstrings with Google format
- TypeScript: TSDoc comments
- Architecture: Markdown docs in `/docs/`

**Violation**: Out-of-sync documentation causes bugs when others read old docs.

---

### 🚮 Never Remove Functionality Without Request

**Rule**: Never delete features, endpoints, or code unless explicitly requested by user.

**Acceptable**: Deprecation with replacement  
**Acceptable**: Refactoring that preserves behavior  
**Not Acceptable**: Removing code because it looks unused (might be needed later)  
**Not Acceptable**: Deleting endpoints to "clean up" API

**Exception**: Security issues, dangerous code that crashes app

---

## Development Workflow

### Feature Implementation Workflow

1. **Understand Requirements**
   - Read feature description from PROJECT_STATE.md
   - Read any related architecture docs
   - Ask clarifying questions

2. **Design Architecture** (Claude) → **Review** (ChatGPT)
   - Describe what you'll build
   - Show data flow
   - Explain dependencies
   - Identify edge cases
   - ChatGPT: Approve or suggest improvements

3. **Implement** (Claude)
   - Create new files or modify existing
   - Follow code standards (type hints, naming, structure)
   - Write clear commit messages
   - Add logging where helpful

4. **Test Locally** (Claude)
   - Backend: Start server, test endpoints
   - Frontend: Test in browser
   - Test error cases
   - Verify no regressions

5. **Update Documentation** (Claude)
   - Update PROJECT_STATE.md
   - Update CHANGELOG.md
   - Create ADR if architecture changed
   - Update architecture docs if needed

6. **Request Review** (Claude → ChatGPT)
   - Summarize what was implemented
   - Point out key decisions
   - List any questions or concerns

7. **Code Review** (ChatGPT)
   - Check architecture adherence
   - Verify code quality
   - Check for security issues
   - Verify documentation updates
   - Approve or request changes

8. **Merge** (Claude)
   - Merge to main branch only after approval
   - Keep commit history clean

---

### What Counts as "Completed"

**Feature is NOT complete if**:
- ❌ It crashes or throws exceptions
- ❌ It breaks existing functionality
- ❌ It doesn't follow code standards
- ❌ It lacks type hints (both languages)
- ❌ It's not documented
- ❌ PROJECT_STATE.md and CHANGELOG.md not updated
- ❌ It hasn't been code reviewed

**Feature IS complete when**:
- ✅ All requirements met
- ✅ Code quality high (type hints, tests, documentation)
- ✅ No regressions
- ✅ Documentation updated
- ✅ Code reviewed and approved

---

### Debugging & Fixing Bugs

**For Bugs**:
1. Claude: Identify root cause (read error logs, trace execution)
2. Claude: Fix with minimal changes
3. Claude: Update CHANGELOG.md with fix
4. ChatGPT: Quick review of fix (no design approval needed for bugs)
5. Claude: Merge fix

**For Issues in Production**:
1. Immediately create hotfix branch
2. Fix bug with minimal changes
3. Test thoroughly
4. Get ChatGPT approval
5. Merge to main and deploy

---

## Naming & Organization Rules

### Backend (Python)

**Files & Directories**:
- Snake case: `conversation_engine.py`, `llm_provider.py`
- Group by layer: `/services/`, `/repositories/`, `/schemas/`
- Clear purpose: `conversation_service.py` not `util.py`

**Classes**:
- PascalCase: `ConversationEngine`, `OpenAIProvider`
- Descriptive: `ConversationEngine` not `Engine`
- Suffix with type: `LLMProvider`, `ConversationRepository`

**Functions**:
- Snake case: `create_conversation()`, `get_messages()`
- Clear action: `get_`, `create_`, `update_`, `delete_`, `process_`
- No `do_` or `make_` prefixes

**Variables**:
- Snake case: `conversation_id`, `message_text`
- Descriptive: `conversation_id` not `cid`
- No abbreviations unless universal: `id`, `api_key`, `llm`

### Frontend (TypeScript)

**Files & Components**:
- PascalCase: `ChatComponent.tsx`, `ConversationList.tsx`
- Hooks: `useChatMessages.ts`, `useConversation.ts`
- Services: `conversationService.ts`, `authService.ts`
- Types: `Message.ts`, `Conversation.ts`

**Components**:
- PascalCase: `ChatComponent`, `ConversationList`
- Descriptive: `ChatMessageItem` not `Item`
- Suffix with purpose: `Button`, `List`, `Modal`, `Provider`

**Functions & Variables**:
- camelCase: `handleSendMessage`, `fetchConversations`
- Clear action: `handle*` for events, `fetch*` for API calls
- Boolean prefixes: `is*`, `has*`, `can*`

**Types & Interfaces**:
- PascalCase: `Message`, `Conversation`, `ChatProps`
- Suffix: `Props`, `State`, `Context` where appropriate

---

## Security Rules

### 🔐 API Keys & Secrets

**NEVER**:
- ❌ Hardcode API keys in code
- ❌ Commit `.env` to version control
- ❌ Log API keys or sensitive data
- ❌ Pass secrets through unsecured channels

**ALWAYS**:
- ✅ Load from environment variables
- ✅ Use `.env` for local development (in `.gitignore`)
- ✅ Use secret management for production
- ✅ Validate secrets are loaded before startup

### 🛡️ Input Validation

**ALWAYS**:
- ✅ Validate all user input (Pydantic backend, types frontend)
- ✅ Validate API request bodies
- ✅ Sanitize before storing
- ✅ Check authentication before accessing user data

### 🔒 Authentication

**Rules**:
- All protected endpoints require valid JWT token
- Tokens must be refreshed before expiry
- Logout must invalidate tokens
- Session must be tied to specific user

---

## Testing Rules

### When Tests are Required

**Always**:
- ✅ Critical business logic (calculations, validations)
- ✅ Authentication flows
- ✅ API integration tests

**Nice to Have**:
- UI component tests
- Utility function tests

**Current Status**: MVP stage - no tests required yet

### Test Structure

**Backend**:
```
backend/
└── tests/
    ├── test_auth.py
    ├── test_conversations.py
    └── conftest.py
```

**Frontend**:
```
src/
└── __tests__/
    ├── components/
    ├── services/
    └── hooks/
```

---

## Common Mistakes to Avoid

| Mistake | Why Wrong | Solution |
|---------|-----------|----------|
| Hardcoding config | Can't change without code edit | Use environment variables |
| Skipping type hints | Bugs caught later | Use type hints everywhere |
| Circular imports | Code won't run | Keep hierarchy clean |
| Modifying shared state | Bugs in concurrent code | Use immutability, dependency injection |
| SQL in API routes | Code becomes unmaintainable | Always use repository layer |
| Direct OpenAI calls | Can't swap providers | Use LLMProvider interface |
| Storing sensitive data in logs | Security issue | Never log secrets |
| Removing old code | Might break something | Deprecate instead |
| Skipping documentation | Others can't understand | Always document |
| Skipping code review | Bugs slip through | Always get approval |

---

## Escalation Process

**If stuck, unclear, or disagree**:

1. **Clear Blocker**: Ask Claude/ChatGPT for clarification
2. **Design Disagreement**: ChatGPT makes final call
3. **Code Quality Issue**: ChatGPT reviews and guides
4. **Architecture Question**: Design discussion before implementation
5. **Timeline Pressure**: Prioritize by value, not speed

**Never**: Skip steps to move faster - this creates more problems.

---

## Summary

**In One Sentence**: 
*Jarvis uses modular async-first architecture with strict separation of concerns, full type safety, and dependency injection everywhere - always design before coding, always review before merging, always update docs after completing.*

**The Three Core Commitments**:
1. 🏗️ **Architecture First** - Never code without approval
2. 📝 **Documentation Always** - Keep docs in sync with code
3. ✅ **Quality Always** - Type hints, tests, reviews, no shortcuts

---

*End of PROJECT_RULES.md*
