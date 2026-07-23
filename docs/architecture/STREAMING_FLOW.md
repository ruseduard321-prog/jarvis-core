# F05: Streaming Integration Flow

## Overview

This document describes the complete flow of streaming messages in the Jarvis chat system, from user input through real-time token delivery.

## Complete Message Flow

### 1. User Sends Message

```
User Types "Hello AI"
        ↓
[Composer Component]
- value = "Hello AI"
- Shows character counter: 9/2000
- Send button enabled
        ↓
User presses Ctrl+Enter
        ↓
onSend() callback fired
        ↓
handleSendMessage() invoked in ChatPage
```

### 2. Message Preparation

```
handleSendMessage() {
  // Validate
  if (!currentConversationId) return;
  if (!draftMessage.trim()) return;
  
  // Setup state
  setIsSending(true);
  setError(null);
  setStreamingContent("");
  
  // Begin streaming
  setIsStreaming(true);
}
```

### 3. Service Layer Call

```
conversationService.streamMessage(
  conversationId,        // Current conversation ID
  draftMessage,         // Message text
  true,                 // use_rag = true
  (event) => {...}      // Event callback
)
        ↓
Creates EventSource
        ↓
Connects to:
  POST /conversations/{id}/chat/stream
```

### 4. Backend Processing

```
FastAPI Backend receives POST request
        ↓
Authentication check
        ↓
Conversation ownership verification
        ↓
Message validation
        ↓
Invoke ConversationEngine
        ↓
Route to AI Orchestrator
        ↓
AI Orchestrator:
  - Check conversation history
  - Load context (RAG if enabled)
  - Stream model tokens
```

### 5. Streaming Event Sequence

#### Event 1: START
```
Backend sends:
{
  "event": "start",
  "message_id": "msg-uuid-123",
  "data": null
}
        ↓
Frontend receives via EventSource 'message' event
        ↓
onEvent callback triggered with parsed event
        ↓
setStreamingMessageId("msg-uuid-123")
        ↓
ChatWindow sees streamingMessageId set
        ↓
Shows TypingIndicator (three-dot animation)
```

#### Event 2: TOKEN (repeating)
```
Backend sends (multiple times):
{
  "event": "token",
  "message_id": "msg-uuid-123",
  "data": "Hello"
}
        ↓
Frontend accumulates
fullContent += "Hello"
setStreamingContent(fullContent)  // Now: "Hello"
        ↓
ChatWindow re-renders
AssistantMessage receives streamingContent
        ↓
User sees: "Hello"
```

#### More TOKEN Events
```
{
  "event": "token",
  "data": " "
}
fullContent = "Hello "
setStreamingContent("Hello ")
        ↓
{
  "event": "token",
  "data": "there"
}
fullContent = "Hello there"
setStreamingContent("Hello there")
        ↓
{
  "event": "token",
  "data": "! How"
}
fullContent = "Hello there! How"
setStreamingContent("Hello there! How")
        ↓
...continues until END event
```

#### Event 3: END
```
Backend sends:
{
  "event": "end",
  "message_id": "msg-uuid-123"
}
        ↓
Frontend processes
setIsStreaming(false)
setStreamingContent("")
setStreamingMessageId(null)
        ↓
Event source closes
        ↓
useMessages query refetches
        ↓
ChatWindow displays complete message
```

#### Event 4: ERROR (if occurred)
```
Backend sends:
{
  "event": "error",
  "data": "Rate limit exceeded"
}
        ↓
Frontend processes
setError("Rate limit exceeded")
setIsStreaming(false)
setStreamingContent("")
        ↓
User sees error message
Retry button available
```

## State Management During Streaming

### Zustand Store Updates

```
INITIAL STATE:
{
  currentConversationId: "conv-123",
  draftMessage: "Hello AI",
  isStreaming: false,
  streamingMessageId: null,
}

USER SENDS MESSAGE:
        ↓
TRANSITION (START EVENT):
{
  currentConversationId: "conv-123",
  draftMessage: "Hello AI",           // Unchanged until end
  isStreaming: true,                  // ← SET
  streamingMessageId: "msg-uuid-123", // ← SET
}

DURING STREAMING (TOKEN EVENTS):
  React state (not Zustand):
  streamingContent = "Hello there! H..."
        ↓
ON END:
{
  currentConversationId: "conv-123",
  draftMessage: "",                   // ← CLEARED
  isStreaming: false,                 // ← CLEARED
  streamingMessageId: null,           // ← CLEARED
}
```

## Component Render Cycle

### ChatPage Component

```
Render 1: User types in Composer
  - Composer value changes
  - handleSendMessage ready to call
  
Render 2: Send button clicked
  - setIsSending(true) → Spinner appears
  - setIsStreaming(true) → isStreaming prop updated
  
Render 3-N: TOKEN events received
  - setStreamingContent(accumulated) each time
  - ChatWindow re-renders with new content
  - AssistantMessage displays streaming text
  
Render Final: END event
  - setIsStreaming(false)
  - setStreamingContent("")
  - useMessages hook refetches
  - Message appears in list
  - Composer ready for next message
```

### ChatWindow Component

```
While NOT Streaming:
  Render messages from useMessages query
  
While Streaming:
  Render messages from useMessages query
  + AssistantMessage with streamingContent
  + "AI is responding..." text
  
On Scroll:
  Calculate distance from bottom
  Show/hide scroll-to-bottom button
```

### Composer Component

```
While NOT Streaming:
  - Send button visible, enabled
  - Help text: "Press Ctrl+Enter to send"
  
While Streaming (isStreaming=true):
  - Send button disabled
  - Stop button visible instead
  - Help text: "AI is responding..."
  - Textarea disabled
  
After Streaming Complete:
  - Return to normal state
  - Draft message cleared
  - Focus ready for next input
```

## Error Handling Scenarios

### Network Error During Streaming

```
EventSource encounters network error
        ↓
Error event triggered
        ↓
catch block in streamMessage:
  - Close EventSource
  - Throw error
        ↓
catch block in handleSendMessage:
  - setError("Failed to send message")
  - setIsStreaming(false)
  - setStreamingContent("")
        ↓
ChatWindow displays ErrorMessage
  - Shows error text
  - Retry button available
  
User clicks Retry
        ↓
handleRetry() called
        ↓
Resend same message
```

### Stream Timeout

```
No events received for 30 seconds
        ↓
Browser EventSource times out
        ↓
Handled as network error
        ↓
User sees error message
```

### User Stops Generation

```
User clicks Stop button
        ↓
onStop() callback fired
        ↓
handleStopGeneration() invoked:
  - setIsStreaming(false)
  - setStreamingContent("")
  - setStreamingMessageId(null)
        ↓
Stop button hidden
Send button enabled
        ↓
Current streaming content remains visible
Next message sends partial content
```

## Backend Streaming Implementation

### Event Format

```javascript
// All events are JSON newline-delimited
// Standard Server-Sent Events format

// START event
data: {"event":"start","message_id":"msg-123","data":null}

// TOKEN event (repeated many times)
data: {"event":"token","data":"token_text","message_id":"msg-123"}

// END event
data: {"event":"end","message_id":"msg-123"}

// ERROR event (optional)
data: {"event":"error","data":"error message","message_id":"msg-123"}
```

### Content-Type Header

```
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
```

### Streaming Constraints

- Timeout: Connection closes after 5 minutes
- Token limit: Max tokens per response (backend config)
- Max message length: 2000 characters (frontend enforced)
- Rate limiting: Based on user quota

## Frontend EventSource Implementation

### Basic EventSource Pattern

```typescript
// Create EventSource
const eventSource = new EventSource(url, { headers: {...} });

// Listen for any message
eventSource.addEventListener("message", (event) => {
  try {
    const parsed = JSON.parse(event.data);
    onEvent(parsed);
  } catch (error) {
    onEvent({
      event: "error",
      data: "Failed to parse event"
    });
  }
});

// Handle connection errors
eventSource.addEventListener("error", (event) => {
  if (eventSource.readyState === EventSource.CLOSED) {
    // Connection closed normally
  } else {
    // Connection error occurred
    onEvent({
      event: "error",
      data: "Connection error"
    });
  }
  eventSource.close();
});
```

### Event Parsing

```typescript
interface StreamEvent {
  event: "start" | "token" | "end" | "error";
  data?: string;
  message_id?: string;
}

// Parse incoming event
const event: StreamEvent = JSON.parse(eventData);

// Type-safe handling
switch (event.event) {
  case "start":
    // event.message_id available
    break;
  case "token":
    // event.data contains token string
    break;
  case "end":
    // Streaming complete
    break;
  case "error":
    // event.data contains error message
    break;
}
```

## Performance Characteristics

### Latency

```
User sends message
        ↓ (~50ms HTTP POST)
Backend processes request
        ↓ (~100-500ms AI inference)
First token arrives
        ↓ (~10ms per token over network)
User sees first token
        ↓
Total first-token latency: 200-700ms
```

### Throughput

```
Typical streaming rate: 20-50 tokens/second
With network latency: 10-20 tokens/second perceived
Efficient for real-time chat display
```

### Memory Usage

```
Streaming message state: ~1KB per message
EventSource connection: ~2KB overhead
Per-conversation cache: ~10KB for 10 messages
Total per user: ~50-100KB typical
```

## Testing Streaming

### Manual Testing

```
1. Navigate to /chat
2. Type a message
3. Click send or press Ctrl+Enter
4. Watch tokens appear in real-time
5. Message should complete automatically
6. New message is clickable after end event
7. Close browser DevTools Network tab to verify EventSource
```

### DevTools Inspection

```
F12 → Network tab
- Look for POST /conversations/{id}/chat/stream
- Content-Type: text/event-stream
- Status: 200 (not 101 WebSocket)
- Response shows JSON events as they arrive
```

### Debugging

```typescript
// Add console logs in streamMessage service
eventSource.addEventListener("message", (event) => {
  console.log("Stream event:", event.data);
  // ... rest of handler
});

eventSource.addEventListener("error", (event) => {
  console.error("Stream error:", event);
});
```

## Troubleshooting

### Messages Not Appearing

**Symptoms**: Send button shows spinner, nothing appears

**Causes**:
1. Backend connection issue
2. Authentication failed
3. Conversation ID invalid

**Solution**:
1. Check Network tab for request status
2. Verify auth token in localStorage
3. Check backend logs

### Streaming Stops Midway

**Symptoms**: Partial message, connection closes

**Causes**:
1. Network timeout
2. Backend error
3. Token limit reached

**Solution**:
1. Check browser console for error
2. Check backend logs for timeout
3. Retry with shorter message

### Stop Button Doesn't Work

**Symptoms**: Clicking Stop doesn't stop streaming

**Causes**:
1. EventSource already closed
2. Browser cache issue

**Solution**:
1. Refresh page
2. Clear browser cache
3. Check console for errors

## API Contract

### Request

```
POST /conversations/{conversation_id}/chat/stream
Content-Type: application/json
Authorization: Bearer {token}

{
  "message": "Hello AI",
  "use_rag": true,
  "stream": true,
  "metadata": {}
}
```

### Response Stream

```
HTTP/1.1 200 OK
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive

data: {"event":"start","message_id":"msg-123"}
data: {"event":"token","data":"Hello"}
data: {"event":"token","data":" "}
data: {"event":"token","data":"there"}
data: {"event":"end","message_id":"msg-123"}
```

## References

- [MDN: EventSource](https://developer.mozilla.org/en-US/docs/Web/API/EventSource)
- [Server-Sent Events Standard](https://html.spec.whatwg.org/multipage/server-sent-events.html)
- [React Query Documentation](https://tanstack.com/query/latest)
- [Zustand Documentation](https://github.com/pmndrs/zustand)
