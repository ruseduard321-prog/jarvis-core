# T69 Backend API Reference

## Quick Start

### Environment Setup
Create `.env` file with:
```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
OPENAI_API_KEY=your_openai_api_key
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
```

### Run Backend
```bash
cd jarvis-core
.venv\Scripts\python.exe -m uvicorn backend.main:app --reload
```

Backend will be available at: `http://localhost:8000`

---

## API Endpoints Overview

### Base URL
```
http://localhost:8000/api/v1
```

### Health & Status
- `GET /health` - Application health
- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe
- `GET /metrics` - Application metrics

---

## Core APIs (T69 Implementation)

### 1. Conversations (Chat Management)

#### Create Conversation
```bash
POST /conversations
Content-Type: application/json

{
  "title": "Project Discussion",
  "metadata": {}
}
```

Response:
```json
{
  "id": "conv_123",
  "title": "Project Discussion",
  "created_at": "2026-07-18T10:00:00Z",
  "updated_at": "2026-07-18T10:00:00Z",
  "metadata": {}
}
```

#### Send Message (Non-Streaming)
```bash
POST /conversations/{conv_id}/chat
Content-Type: application/json

{
  "message": "What are the project milestones?",
  "use_rag": true,
  "stream": false
}
```

Response:
```json
{
  "conversation_id": "conv_123",
  "user_message_id": "msg_user_123",
  "assistant_message_id": "msg_asst_456",
  "content": "The project has milestones in Q3 and Q4 2026...",
  "tokens_used": 245,
  "rag_context_used": true
}
```

#### Stream Chat Completion
```bash
POST /conversations/{conv_id}/chat/stream
Content-Type: application/json

{
  "message": "Summarize the project",
  "use_rag": true
}
```

Returns: Server-Sent Events stream with tokens

#### List Messages
```bash
GET /conversations/{conv_id}/messages
```

#### Get Conversation
```bash
GET /conversations/{conv_id}
```

#### Update Conversation
```bash
PATCH /conversations/{conv_id}
Content-Type: application/json

{
  "title": "New Title",
  "metadata": {"archived": true}
}
```

#### Delete Conversation
```bash
DELETE /conversations/{conv_id}
```

---

### 2. Memory (Knowledge Retention)

#### Create Memory Record
```bash
POST /memory
Content-Type: application/json

{
  "record_type": "FACT",
  "content": "Project deadline is Q4 2026",
  "source": "project_doc",
  "tags": ["project", "deadline"],
  "attributes": {"priority": "high"}
}
```

#### Query Memory
```bash
POST /memory/query
Content-Type: application/json

{
  "query": "deadline",
  "tags": ["project"],
  "record_type": "FACT",
  "limit": 10
}
```

#### Get Memory Record
```bash
GET /memory/{memory_id}
```

#### Update Memory Record
```bash
PATCH /memory/{memory_id}
Content-Type: application/json

{
  "content": "Updated content",
  "tags": ["updated", "tag"]
}
```

#### Delete Memory Record
```bash
DELETE /memory/{memory_id}
```

---

### 3. Knowledge & Documents

#### Create Knowledge Document
```bash
POST /knowledge/documents
Content-Type: application/json

{
  "title": "Project Requirements",
  "content": "The project requires...",
  "source_type": "DOCUMENT",
  "source_identifier": "docs/requirements.md",
  "tags": ["project", "requirements"]
}
```

#### Upload & Ingest Document
```bash
POST /documents/upload
Content-Type: multipart/form-data

file: <binary file>
title: "Project Requirements"
namespace: "documents"
tags: "project,requirements"
chunk_size: 1000
chunk_overlap: 100
```

Response:
```json
{
  "document_id": "doc_123",
  "title": "Project Requirements",
  "file_size": 25000,
  "chunk_count": 15,
  "ingestion_status": "completed",
  "job_id": "job_456",
  "created_at": "2026-07-18T10:00:00Z"
}
```

#### Check Ingestion Job Status
```bash
GET /documents/ingestion-jobs/{job_id}
```

#### Get Knowledge Document
```bash
GET /knowledge/documents/{document_id}
```

#### Delete Knowledge Document
```bash
DELETE /knowledge/documents/{document_id}
```

#### Retrieve Context (RAG)
```bash
POST /retrieval/query
Content-Type: application/json

{
  "query": "What are the project milestones?",
  "namespace": "documents",
  "tags": ["project"],
  "limit": 5
}
```

Response:
```json
{
  "query": "What are the project milestones?",
  "documents": [
    {
      "id": "doc_123",
      "title": "Project Overview",
      "content": "The project milestones are...",
      "source": "docs/overview.md",
      "tags": ["project"],
      "similarity_score": 0.92
    }
  ],
  "total_count": 1,
  "augmented_prompt": "Based on retrieved documents: What are the project milestones?"
}
```

---

### 4. Tools (Agent Actions)

#### List Available Tools
```bash
GET /tools
```

Response:
```json
[
  {
    "id": "tool_search",
    "name": "Web Search",
    "description": "Search the web for information",
    "category": "search",
    "parameters": [
      {
        "name": "query",
        "type": "string",
        "description": "Search query",
        "required": true
      }
    ],
    "tags": ["search", "web"]
  }
]
```

#### Get Tool Details
```bash
GET /tools/{tool_id}
```

#### Execute Tool
```bash
POST /tools/{tool_id}/execute
Content-Type: application/json

{
  "arguments": {"query": "project requirements"},
  "timeout_seconds": 30
}
```

Response:
```json
{
  "tool_id": "tool_search",
  "execution_id": "exec_123",
  "status": "success",
  "output": {"results": [...]},
  "duration_ms": 145,
  "metadata": {}
}
```

---

### 5. Agents (AI Orchestration)

#### List Available Agents
```bash
GET /agents
```

#### Get Agent Details
```bash
GET /agents/{agent_id}
```

#### Execute Agent
```bash
POST /agents/{agent_id}/execute
Content-Type: application/json

{
  "message": "Research the latest AI developments",
  "conversation_id": "conv_123",
  "stream": false,
  "timeout_seconds": 60
}
```

Response:
```json
{
  "agent_id": "agent_research",
  "execution_id": "exec_456",
  "status": "completed",
  "response": "Based on recent research: ...",
  "tools_used": ["tool_search"],
  "duration_ms": 2341,
  "metadata": {}
}
```

#### Stream Agent Execution
```bash
POST /agents/{agent_id}/execute/stream
Content-Type: application/json

{
  "message": "Research the topic",
  "stream": true
}
```

Returns: Server-Sent Events stream

---

### 6. Workflows (Complex Pipelines)

#### Create Workflow
```bash
POST /workflows
Content-Type: application/json

{
  "name": "Document Processing",
  "description": "Process and analyze documents",
  "nodes": [
    {"id": "start", "type": "start"},
    {"id": "task_1", "type": "task", "agent_id": "agent_1"},
    {"id": "end", "type": "end"}
  ],
  "edges": [
    {"from": "start", "to": "task_1"},
    {"from": "task_1", "to": "end"}
  ]
}
```

#### Get Workflow
```bash
GET /workflows/{workflow_id}
```

#### Execute Workflow
```bash
POST /workflows/{workflow_id}/execute
Content-Type: application/json

{
  "input_data": {"document_id": "doc_123"},
  "timeout_seconds": 300
}
```

Response:
```json
{
  "workflow_id": "workflow_123",
  "execution_id": "exec_789",
  "status": "completed",
  "output_data": {"result": "Processing complete"},
  "duration_ms": 5432
}
```

---

## Common Patterns

### Error Handling
All endpoints return standard HTTP status codes:
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `404` - Not Found
- `500` - Server Error

Error response format:
```json
{
  "detail": "Error message describing what went wrong"
}
```

### Authentication
Include JWT token in Authorization header:
```bash
Authorization: Bearer <jwt_token>
```

### Pagination (Future)
Endpoints support optional parameters:
- `limit`: Max results (default 10)
- `offset`: Skip results (default 0)

### Filtering (Future)
Endpoints support tag-based filtering:
- `tags`: Comma-separated list of tags
- `namespace`: Filter by namespace

---

## Testing with cURL

### Example: Create conversation and send message
```bash
# 1. Create conversation
CONV_ID=$(curl -s -X POST http://localhost:8000/api/v1/conversations \
  -H "Content-Type: application/json" \
  -d '{"title":"Test"}' | jq -r '.id')

echo "Created conversation: $CONV_ID"

# 2. Send message
curl -X POST http://localhost:8000/api/v1/conversations/$CONV_ID/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello, how are you?","use_rag":false}'

# 3. List messages
curl http://localhost:8000/api/v1/conversations/$CONV_ID/messages
```

### Example: Upload document
```bash
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -F "file=@myfile.txt" \
  -F "title=My Document" \
  -F "namespace=documents" \
  -F "tags=important,project"
```

---

## WebSocket Support (Future)

Real-time features planned for future releases:
- Live agent execution updates
- Workflow execution progress
- Document ingestion notifications
- Message typing indicators

---

## Rate Limiting

Current rate limits:
- Global: 100 requests/minute
- Auth endpoints: 20 requests/minute
- Other endpoints: 100 requests/minute

Future: Per-user and per-tier rate limiting

---

## Documentation & OpenAPI

Interactive API documentation available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## Support

For issues or questions:
1. Check startup logs: `tail -f logs/app.log`
2. Run health check: `curl http://localhost:8000/health/ready`
3. Review configuration: Check `.env` file
4. Review architecture documentation: See `docs/architecture/ARCHITECTURE.md`
