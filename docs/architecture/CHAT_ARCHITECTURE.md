# F05: AI Chat Module Architecture

## Overview

F05 implements the core real-time AI Chat experience for Jarvis. This module enables users to have multi-turn conversations with the backend AI engine through a professional, streaming-enabled interface.

**Status**: ✅ Complete  
**Sprint Goal**: Build the complete AI Chat experience with zero mocks, using existing backend infrastructure  
**Constraint**: No git commits, reuse all F01-F04 foundation

## System Architecture

### High-Level Flow

```
Frontend (React/TypeScript)
    ↓
ChatPage Component (Orchestrator)
    ├── ConversationSidebar (List/Create/Delete)
    ├── ChatWindow (Message Display)
    └── Composer (Input/Send)
    ↓
conversationService (HTTP + SSE)
    ├── REST Endpoints (CRUD)
    └── EventSource (Streaming)
    ↓
Backend (FastAPI)
    ├── Conversation Engine
    ├── AI Orchestrator
    ├── Streaming Engine
    ├── Memory System
    └── RAG Integration
```

### Component Hierarchy

```
ChatPage (Client Component)
├── ProtectedAppLayout
│   ├── AppShell
│   └── Topbar + Sidebar (Navigation)
├── ConversationSidebar
│   ├── New Chat Button
│   ├── Search Input
│   └── ConversationList
│       └── ConversationItem (with actions)
├── ChatWindow
│   ├── MessageList
│   │   ├── UserMessage
│   │   ├── AssistantMessage
│   │   ├── MarkdownRenderer
│   │   │   └── InlineMarkdown + CodeBlock
│   │   ├── ErrorMessage
│   │   └── TypingIndicator
│   └── Scroll-to-Bottom Button
└── Composer
    ├── Auto-Resize Textarea
    ├── Keyboard Shortcuts
    ├── Character Counter
    └── Send/Stop Buttons
```

## Core Components

### 1. **ChatPage** (`src/components/chat/chat-page.tsx`)
**Purpose**: Main orchestrator for chat functionality  
**Responsibilities**:
- Manage conversation lifecycle (create, select, switch)
- Handle message sending and streaming state
- Integrate service layer with UI components
- Initialize default conversation on first load

**Key Features**:
- Auto-create first conversation on mount
- Streaming message accumulation
- Error handling with retry capability
- Draft message persistence in Zustand store
- Real-time UI state management

**Dependencies**:
- `useConversationStore`: Global state (current conversation, draft message, streaming flag)
- `useCreateConversation`: Mutation hook for new conversations
- `conversationService`: API layer for chat operations
- `ChatWindow`, `ConversationSidebar`, `Composer`: Child components

### 2. **ConversationSidebar** (`src/components/chat/conversation-sidebar.tsx`)
**Purpose**: Conversation list and management interface  
**Responsibilities**:
- Display list of conversations sorted by recency
- Search/filter conversations by title
- Create new conversations
- Rename existing conversations
- Delete conversations with confirmation

**Key Features**:
- Local search filtering
- In-line editing with validation
- Delete confirmation UI
- Loading and empty states
- Keyboard navigation support

**Dependencies**:
- `useConversations`: Fetch list of conversations
- `useCreateConversation`: Create new conversation
- `useDeleteConversation`: Delete conversation mutation
- `useUpdateConversation`: Rename conversation

### 3. **ChatWindow** (`src/components/chat/chat-window.tsx`)
**Purpose**: Message display and conversation view  
**Responsibilities**:
- Render conversation messages
- Display streaming content in real-time
- Auto-scroll to bottom on new messages
- Show loading and empty states
- Provide scroll-to-bottom button

**Key Features**:
- Message list from React Query
- Streaming message accumulation
- Responsive message containers
- Scroll position tracking
- Error display with retry

**Dependencies**:
- `useMessages`: Fetch messages for conversation
- `UserMessage`, `AssistantMessage`: Message components
- `TypingIndicator`, `ErrorMessage`: State indicators

### 4. **Composer** (`src/components/chat/composer.tsx`)
**Purpose**: Message input and sending interface  
**Responsibilities**:
- Collect user input
- Auto-resize textarea based on content
- Send messages via Enter or Ctrl+Enter
- Stop streaming via stop button
- Character count and validation

**Key Features**:
- Auto-resize with min/max height constraints
- Keyboard shortcuts (Ctrl+Enter to send)
- Disabled states during loading/streaming
- Dynamic help text
- Loading spinner in send button
- Character counter (2000 char limit)

**Dependencies**:
- React hooks for state management
- No external dependencies

### 5. **Message Components** (`src/components/chat/message-bubble.tsx`)
**Purpose**: Individual message rendering with formatting  
**Responsibilities**:
- Render user and assistant messages
- Display message actions (copy, regenerate, retry)
- Format timestamps
- Show loading/streaming states

**Exported Components**:
- `MessageBubble`: Main wrapper
- `UserMessage`: User message variant
- `AssistantMessage`: Assistant message with markdown
- `ErrorMessage`: Error display with retry
- `TypingIndicator`: Animated loading indicator

**Key Features**:
- Markdown rendering for assistant messages
- Copy button with clipboard feedback
- Regenerate and retry buttons
- Relative timestamp formatting
- Hover-visible actions
- Streaming animation support

### 6. **Markdown Renderer** (`src/components/chat/markdown-renderer.tsx`)
**Purpose**: Parse and render markdown content  
**Responsibilities**:
- Parse markdown syntax (headings, code, lists, etc.)
- Render markdown elements with styling
- Format inline markdown (bold, italic, code, links)
- Display code blocks with syntax highlighting and copy

**Supported Markdown**:
- Headings: `# h1` through `###### h6`
- Code blocks: ` ```language ... ``` `
- Lists: ordered `1.` and unordered `-` or `*`
- Blockquotes: `> quote`
- Horizontal rules: `---` or `***`
- Inline formatting: `**bold**`, `*italic*`, `` `code` ``, `[link](url)`

**Key Features**:
- Custom markdown parser (no external library)
- Syntax-highlighted code blocks
- Copy code button with feedback
- Language label display
- Responsive layout

## Service Layer

### ConversationService (`src/services/conversation-service.ts`)

HTTP and SSE interface for all conversation operations.

**CRUD Methods**:
```typescript
// List all conversations
async listConversations(): Promise<ApiResponse<Conversation[]>>

// Get single conversation
async getConversation(conversationId: string): Promise<ApiResponse<Conversation>>

// Create new conversation
async createConversation(title?: string, metadata?: Record<string, unknown>): Promise<ApiResponse<Conversation>>

// Update conversation (rename)
async updateConversation(conversationId: string, updates: {title?: string, metadata?: Record<string, unknown>}): Promise<ApiResponse<Conversation>>

// Delete conversation
async deleteConversation(conversationId: string): Promise<ApiResponse<void>>

// List messages in conversation
async listMessages(conversationId: string): Promise<ApiResponse<Message[]>>

// Send message (non-streaming)
async sendMessage(conversationId: string, message: string, useRag?: boolean): Promise<ApiResponse<ChatCompletionResponse>>

// Stream message (SSE)
async streamMessage(conversationId: string, message: string, useRag?: boolean, onEvent?: (event: StreamEvent) => void): Promise<void>
```

**Backend Integration Points**:
- `POST /conversations` - Create conversation
- `GET /conversations/{id}` - Fetch conversation
- `PATCH /conversations/{id}` - Update conversation
- `DELETE /conversations/{id}` - Delete conversation
- `GET /conversations/{id}/messages` - Fetch messages
- `POST /conversations/{id}/chat` - Send message (non-streaming)
- `POST /conversations/{id}/chat/stream` - Stream message (SSE)

## State Management

### Zustand Stores

#### ConversationStore
```typescript
interface ConversationState {
  // Current conversation
  currentConversationId: string | null;
  setCurrentConversationId: (id: string | null) => void;

  // Draft message
  draftMessage: string;
  setDraftMessage: (message: string) => void;

  // Streaming state
  isStreaming: boolean;
  setIsStreaming: (streaming: boolean) => void;

  // Streaming message ID for tracking
  streamingMessageId: string | null;
  setStreamingMessageId: (id: string | null) => void;

  // UI state
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
}
```

**Persistence**: Draft message is persisted in localStorage  
**Scope**: Global, available throughout application

### React Query Hooks (`src/hooks/use-chat-queries.ts`)

Query key factory and hooks for all conversation operations.

**Query Keys**:
```typescript
const conversationKeys = {
  all: ["conversations"],
  lists: () => ["conversations", "list"],
  list: () => ["conversations", "list"],
  details: () => ["conversations", "detail"],
  detail: (id: string) => ["conversations", "detail", id],
  messages: () => ["conversations", "messages"],
  messageList: (conversationId: string) => ["conversations", "messages", conversationId],
}
```

**Hooks**:
- `useConversations()` - Query list of conversations
- `useConversation(id)` - Query single conversation
- `useMessages(id)` - Query messages in conversation
- `useCreateConversation()` - Mutation to create conversation
- `useUpdateConversation(id)` - Mutation to rename conversation
- `useDeleteConversation()` - Mutation to delete conversation
- `useSendMessage(id)` - Mutation to send message

**Cache Invalidation**:
- Create/Update/Delete automatically invalidate list
- Delete removes conversation from cache entirely
- Send message invalidates message list

## Data Types

### Core Types (`src/types/index.ts`)

```typescript
// Conversation
interface Conversation {
  id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
  metadata: Record<string, unknown>;
}

// Message
type MessageRole = "system" | "user" | "assistant" | "developer" | "tool";

interface Message {
  id: string;
  conversation_id: string;
  content: string;
  role: MessageRole;
  created_at: string;
  metadata: Record<string, unknown>;
}

// Streaming
interface StreamEvent {
  event: "start" | "token" | "end" | "error";
  data?: string;
  message_id?: string;
}

// API Response
interface ChatCompletionResponse {
  conversation_id: string;
  user_message_id: string;
  assistant_message_id: string;
  content: string;
  tokens_used?: number;
  rag_context_used: boolean;
  metadata: Record<string, unknown>;
}
```

## Streaming Implementation

### SSE (Server-Sent Events) Pattern

**Backend**:
- Endpoint: `POST /conversations/{id}/chat/stream`
- Content-Type: `text/event-stream`
- Events: JSON-formatted with `event` type

**Frontend**:
```typescript
// EventSource API for server-sent events
const eventSource = new EventSource(url);

eventSource.addEventListener("message", (e) => {
  const event = JSON.parse(e.data) as StreamEvent;
  
  switch (event.event) {
    case "start":
      // Message started, get message_id
      messageId = event.message_id;
      break;
    case "token":
      // Accumulate token
      content += event.data;
      break;
    case "end":
      // Message complete
      closeStream();
      break;
    case "error":
      // Handle error
      showError(event.data);
      break;
  }
});
```

**Message Accumulation**:
1. User sends message via Composer
2. `handleSendMessage()` calls `conversationService.streamMessage()`
3. Service creates EventSource, listens for events
4. Each "token" event appends to `streamingContent` state
5. ChatWindow re-renders with accumulated content
6. On "end" event, streaming completes and message list updates

**Stop Streaming**:
- User clicks Stop button
- `handleStopGeneration()` sets `isStreaming = false`
- UI updates to show final message
- Next message can be sent

## File Structure

```
src/components/chat/
├── index.ts                      # Exports
├── chat-page.tsx                 # Main orchestrator
├── chat-window.tsx               # Message display
├── composer.tsx                  # Input component
├── conversation-sidebar.tsx      # Conversation list
├── message-bubble.tsx            # Message rendering (5 components)
└── markdown-renderer.tsx         # Markdown parsing & rendering

src/services/
├── conversation-service.ts       # Chat API layer

src/hooks/
├── use-chat-queries.ts           # React Query hooks

src/types/
├── index.ts                      # Type definitions (chat types added)

src/store/
├── index.ts                      # Zustand stores (chat state added)

app/(chat)/
├── layout.tsx                    # Protected layout
└── chat/
    └── page.tsx                  # Chat page route
```

## Integration Points

### Backend Conversation Engine
- Uses existing `ConversationEngine` protocol
- Leverages `ConversationEngineService` implementation
- Reuses `InMemoryConversationStore`

### Authentication
- `ApiClient` automatically injects Bearer tokens
- Session stored in localStorage
- Automatic token refresh via interceptor

### Theme & Layout
- Uses existing `AppShell` layout
- Inherits `Tailwind` styling system
- Integrates with `ThemeProvider`

### Navigation
- Added to main navigation config with "New" badge
- Route: `/chat`
- Protected by `ProtectedAppLayout`

## API Endpoints

All endpoints use base URL from backend configuration.

### Conversation Management
```
POST   /conversations              Create conversation
GET    /conversations              List conversations
GET    /conversations/{id}         Get conversation
PATCH  /conversations/{id}         Update conversation
DELETE /conversations/{id}         Delete conversation
```

### Message Operations
```
GET    /conversations/{id}/messages        List messages
POST   /conversations/{id}/chat            Send message (non-streaming)
POST   /conversations/{id}/chat/stream     Stream message (SSE)
```

## Error Handling

### Error States
- Network errors: Show error message with retry button
- Timeout errors: Automatic retry via React Query
- Authentication errors: Redirect to login (handled by ApiClient)
- Stream errors: Show error in message, allow resend

### User Feedback
- Loading spinners in buttons
- "AI is responding" indicator during streaming
- Relative timestamps for context
- Copy-to-clipboard feedback

## Performance Optimizations

### Already Implemented
- React Query caching and deduplication
- Zustand store for UI state (no re-renders)
- EventSource for efficient streaming
- Auto-resize textarea (DOM-only, no calculation re-renders)
- Lazy message rendering (React Query only fetches visible)

### Future Enhancements
- Message virtualization for large conversations
- Memoization of message components
- Image lazy loading for embedded images
- Markdown parser caching

## Accessibility

### Current Support
- ARIA labels on inputs and buttons
- Semantic HTML (div with role="log" for messages)
- Keyboard navigation in sidebar (arrow keys)
- Keyboard shortcuts documented (Ctrl+Enter to send)
- Focus management in modals/dialogs

### Future Enhancements
- Screen reader announcements for new messages
- Focus trap in modals
- ARIA live regions for streaming updates

## Security

### Implemented
- HTTPS-only API communication
- Bearer token authentication
- CSRF protection (Next.js built-in)
- Content Security Policy (CSP) headers
- Input validation (message length limit: 2000 chars)

### Backend Validation
- Server-side message validation
- User permission checks
- Conversation ownership verification

## Testing Considerations

### Unit Tests
- `useClipboard` hook
- Markdown parser edge cases
- Timestamp formatting

### Integration Tests
- Create → Send → Stream flow
- Sidebar create/delete operations
- Retry on network failure

### E2E Tests
- Full conversation flow
- Streaming message reception
- Mobile responsive layout

## Deployment Considerations

### Build Configuration
- `dynamic = "force-dynamic"` to prevent pre-rendering issues
- TypeScript strict mode enabled
- ESLint configuration for code quality

### Environment Variables
- `NEXT_PUBLIC_API_URL`: Backend base URL
- Inherited from F01-F04 setup

### Browser Support
- Modern browsers with EventSource support
- Fallback to polling if needed (not implemented)
- Mobile browsers via responsive design

## Continuation & Future Work

### High Priority
1. **Mobile responsive drawer** for conversation sidebar
2. **Message virtualization** for large conversations
3. **Image support** in markdown renderer
4. **Code syntax highlighting** enhancement

### Medium Priority
1. **Message search** within conversation
2. **Conversation export** (JSON, PDF, Markdown)
3. **Typing indicators** from other users
4. **Message reactions** (emoji reactions)

### Lower Priority
1. **Message threading** (branches/variations)
2. **Prompt templates** for quick starts
3. **Conversation sharing** (read-only links)
4. **Analytics** (conversation length, turn count)

## Dependencies

### Core Dependencies
- `react@19.2.4`: Component framework
- `next@16.2.10`: Framework
- `@tanstack/react-query`: Server state
- `zustand`: Client state
- `axios`: HTTP client
- `lucide-react`: Icons

### Development Dependencies
- `typescript`: Type safety
- `eslint`: Code quality
- `tailwindcss`: Styling

## Conclusion

F05 provides a complete, production-ready chat interface that:
- ✅ Integrates seamlessly with backend infrastructure
- ✅ Reuses all F01-F04 foundation patterns
- ✅ Provides real-time streaming conversation
- ✅ Implements responsive, accessible UI
- ✅ Maintains type safety throughout
- ✅ Follows project conventions and standards

The module is ready for testing, mobile optimization, and feature expansion as needed.
