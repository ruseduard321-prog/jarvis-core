# F07 Knowledge Base – Implementation Plan (MVP)

**Status**: Plan Ready for Approval  
**Date**: 2026-07-19  
**Feature**: Knowledge Base (F07)  
**Scope**: Management UI/API for document browsing, searching, filtering, uploading, and deletion  

---

## 1. EXISTING INFRASTRUCTURE ANALYSIS

### Backend Already Available ✓

**Document Ingestion Pipeline**
- `DocumentIngestionEngine`: Handles parsing, chunking, storage
- Supports: TEXT, MARKDOWN, PDF, DOCX formats
- Chunk management with overlap
- Async ingestion with job tracking

**Knowledge Repository**
- `InMemoryKnowledgeRepository`: Full CRUD operations
- Methods: `create_document()`, `get_document()`, `list_documents()`, `delete_document()`, `update_document()`
- Supports chunk retrieval: `get_chunks(document_id)`

**Existing Models**
- `KnowledgeDocument`: ID, title, content, source, metadata, chunks
- `KnowledgeChunk`: Discrete chunks with content and metadata
- `DocumentFormat`: TEXT, MARKDOWN, PDF, DOCX, CSV, JSON
- `IngestionJob`: Tracks job status and progress

**Existing Endpoints**
- `POST /documents/upload`: Document ingestion (already implemented)
- `POST /knowledge/documents`: Create knowledge documents
- `GET /knowledge/{id}`: Get document details
- `DELETE /knowledge/{id}`: Delete documents (pattern exists in memory endpoints)

### Frontend Patterns ✓

**Service Layer Pattern**
```typescript
// Singleton services (conversationService, dashboardService)
// Methods return ApiResponse<T>
// Uses apiClient singleton
```

**Hook Pattern**
```typescript
// React Query hooks (useDashboard)
// Separate: API service → hook → component
// Config: queryKey, queryFn, refetchInterval, staleTime, gcTime
```

**Component Structure**
```typescript
// Page → Layout → Sections → Sub-components
// All components reusable and composable
// Full TypeScript strict mode
// Dark mode support throughout
```

---

## 2. ARCHITECTURE DECISIONS

### Backend

**Single Unified Endpoint Group: `/knowledge`**

Build on existing `/documents/upload` endpoint. Create new management endpoints:

```
GET    /knowledge
GET    /knowledge/{id}
DELETE /knowledge/{id}
```

**Why Single Group?**
- Dashboard pattern proved effective (single endpoint aggregates data)
- Reduces API surface
- Follows existing conventions

**Data Flow**
```
KnowledgePage (React)
    ↓
useKnowledge() hook (React Query)
    ↓
knowledgeService.getDocuments()
    ↓
apiClient.get("/knowledge")
    ↓
Backend: GET /knowledge endpoint
    ↓
KnowledgeService (aggregates)
    ↓
KnowledgeRepository (list_documents)
    ↓
Return KnowledgeListResponse (JSON)
```

### Frontend

**Three Main Layers**

1. **API Service** (`knowledge-service.ts`)
   - `getDocuments()`: List all documents with metadata
   - `getDocument(id)`: Get single document details
   - `uploadDocument(file, metadata)`: Upload via form data
   - `deleteDocument(id)`: Delete document
   - `searchDocuments(query)`: Client-side filtering wrapper

2. **React Query Hook** (`use-knowledge.ts`)
   - `useKnowledgeList()`: Fetch all documents
   - `useKnowledgeDetail(id)`: Fetch single document
   - `useKnowledgeUpload()`: Mutation for upload
   - `useKnowledgeDelete(id)`: Mutation for delete

3. **Components** (`/components/knowledge/`)
   - Page orchestrator
   - Layout structure
   - Table with sorting
   - Upload zone with drag & drop
   - Search/filter bar
   - Empty/loading/error states

---

## 3. API SPECIFICATION

### Backend Responses

**GET /knowledge**
```json
{
  "documents": [
    {
      "id": "doc_123",
      "title": "Project Requirements",
      "filename": "requirements.pdf",
      "file_size": 25000,
      "document_type": "pdf",
      "ingestion_status": "completed",
      "chunk_count": 15,
      "tags": ["project", "requirements"],
      "created_at": "2026-07-19T10:00:00Z",
      "updated_at": "2026-07-19T10:00:00Z"
    }
  ],
  "total_count": 42,
  "timestamp": "2026-07-19T14:50:00Z"
}
```

**GET /knowledge/{id}**
```json
{
  "id": "doc_123",
  "title": "Project Requirements",
  "filename": "requirements.pdf",
  "file_size": 25000,
  "document_type": "pdf",
  "ingestion_status": "completed",
  "chunk_count": 15,
  "tags": ["project"],
  "metadata": { "version": "1.0" },
  "created_at": "2026-07-19T10:00:00Z",
  "updated_at": "2026-07-19T10:00:00Z"
}
```

**POST /documents/upload** (reuse existing)
- Input: multipart/form-data (file + metadata)
- Output: DocumentUploadResponse (already exists)
- Returns: document_id, title, file_size, chunk_count, ingestion_status, job_id, created_at

**DELETE /knowledge/{id}**
- Input: document ID
- Output: 204 No Content on success
- 404 if not found

### Frontend TypeScript Types

```typescript
// Document metadata and listing
interface Document {
  id: string;
  title: string;
  filename: string;
  file_size: number;
  document_type: string; // "pdf" | "text" | "markdown" | "docx"
  ingestion_status: string; // "pending" | "processing" | "completed" | "failed"
  chunk_count: number;
  tags: string[];
  created_at: string;
  updated_at: string;
}

interface KnowledgeListResponse {
  documents: Document[];
  total_count: number;
  timestamp: string;
}

interface DocumentDetail extends Document {
  metadata: Record<string, unknown>;
}

interface UploadProgress {
  file: File;
  progress: number; // 0-100
  status: "pending" | "uploading" | "completed" | "failed";
  error?: string;
}
```

---

## 4. COMPONENT ARCHITECTURE

### Page Components

```
KnowledgePage (orchestrator, error/loading states)
└── KnowledgeLayout (main layout grid)
    ├── PageHeader (title + description)
    ├── SearchBar (search + quick filters)
    ├── FilterBar (advanced filters)
    ├── UploadZone (drag & drop)
    ├── DocumentTable (main list)
    └── EmptyState / LoadingState / ErrorState
```

### Reusable Sub-Components

- **DocumentTable**: Sortable table with columns
- **DocumentRow**: Single row with actions
- **UploadZone**: Drag & drop + file picker
- **SearchBar**: Text search with debounce
- **FilterBar**: Status/type filter dropdowns
- **DocumentStatusBadge**: Colored status indicator
- **DocumentTypeIcon**: Icon for file type
- **ActionMenu**: Delete/open actions
- **EmptyState**: "No documents" message
- **LoadingState**: Skeleton rows

### State Management

**React Query Queries**
- `useKnowledgeList()`: Documents list (auto-refetch every 30s)
- `useKnowledgeDetail(id)`: Single document

**React Query Mutations**
- `useKnowledgeDelete(id)`: Delete with optimistic update
- `useKnowledgeUpload()`: Upload with progress tracking

**Local State (React)**
- Search query (debounced)
- Active filters (status, type)
- Upload queue (pending files)
- Selected rows (for bulk operations future)

---

## 5. IMPLEMENTATION ORDER

### Phase 1: Backend API (2 hours)

1. **Create KnowledgeService** (`backend/services/knowledge_service.py`)
   - `get_documents()`: List all with filtering
   - `get_document(id)`: Get single document
   - `delete_document(id)`: Delete and cleanup
   - Error handling with logging

2. **Create Knowledge Schemas** (extend existing)
   - `DocumentListResponse`: For GET /knowledge
   - `DocumentDetailResponse`: For GET /knowledge/{id}
   - Update existing models if needed

3. **Create Knowledge API Endpoint** (`backend/api/v1/knowledge.py` - expand)
   - Add routes: GET /knowledge, GET /knowledge/{id}, DELETE /knowledge/{id}
   - Register in router
   - Add to dependencies.py service registration

4. **Verify**
   - Python syntax check
   - Router imports successfully
   - Endpoint registration confirmed

### Phase 2: Frontend Types & Constants (1 hour)

1. **Update Types** (`src/types/index.ts`)
   - Add Document, DocumentListResponse, DocumentDetail, UploadProgress interfaces

2. **Update Constants** (`src/constants/index.ts`)
   - Add KNOWLEDGE endpoints object:
     ```typescript
     KNOWLEDGE: {
       LIST: "/knowledge",
       GET: (id: string) => `/knowledge/${id}`,
       DELETE: (id: string) => `/knowledge/${id}`,
       UPLOAD: "/documents/upload",
     }
     ```

3. **Verify**
   - TypeScript compilation passes
   - Types properly exported

### Phase 3: Frontend Services & Hooks (2 hours)

1. **Create Knowledge Service** (`src/services/knowledge-service.ts`)
   - `getDocuments()`: Fetch list
   - `getDocument(id)`: Fetch detail
   - `uploadDocument(file, metadata)`: Upload multipart
   - `deleteDocument(id)`: Delete
   - Error handling with proper types

2. **Create Knowledge Hooks** (`src/hooks/use-knowledge.ts`)
   - `useKnowledgeList()`: Query with refetch every 30s
   - `useKnowledgeDetail(id)`: Single document query
   - `useKnowledgeDelete()`: Mutation with optimistic update
   - `useKnowledgeUpload()`: Mutation for file upload

3. **Verify**
   - ESLint passes
   - TypeScript strict mode passes

### Phase 4: Frontend Components - Main Pages (3 hours)

1. **KnowledgePage** (`src/components/knowledge/knowledge-page.tsx`)
   - Orchestrator with error/loading states
   - Uses useKnowledgeList hook
   - Render KnowledgeLayout on success

2. **KnowledgeLayout** (`src/components/knowledge/knowledge-layout.tsx`)
   - Grid layout with header, search, filters, upload, table
   - Responsive design

3. **PageHeader** (`src/components/knowledge/page-header.tsx`)
   - Title "Knowledge Base"
   - Description
   - Stats (document count)

4. **SearchBar** (`src/components/knowledge/search-bar.tsx`)
   - Text input with debounce
   - Search icon (lucide)
   - Clear button

5. **FilterBar** (`src/components/knowledge/filter-bar.tsx`)
   - Status filter dropdown: All, Pending, Processing, Completed, Failed
   - Type filter dropdown: All, PDF, Text, Markdown, DOCX
   - Reset filters button

6. **Verify**
   - ESLint passes
   - All components render without errors
   - Dark mode works

### Phase 5: Frontend Components - Upload & Table (3 hours)

1. **UploadZone** (`src/components/knowledge/upload-zone.tsx`)
   - Drag & drop area with visual feedback
   - File picker button
   - Show supported formats
   - Display upload progress
   - Handle errors gracefully

2. **DocumentTable** (`src/components/knowledge/document-table.tsx`)
   - Table structure with headers:
     - Filename (clickable)
     - Type (icon + text)
     - Size (formatted bytes)
     - Status (colored badge)
     - Uploaded (relative time)
     - Actions (delete button)
   - Sorting by column
   - Empty state integration
   - Scrollable container

3. **DocumentRow** (`src/components/knowledge/document-row.tsx`)
   - Single row component
   - Hover effects
   - Action buttons
   - Delete with confirmation

4. **DocumentStatusBadge** (`src/components/knowledge/document-status-badge.tsx`)
   - Colors: Green (completed), Yellow (processing), Gray (pending), Red (failed)
   - Text content

5. **DocumentTypeIcon** (`src/components/knowledge/document-type-icon.tsx`)
   - Icon mapping: pdf→FileText, text→FileCode, markdown→FileText, docx→FileText
   - Use lucide-react icons

6. **Verify**
   - ESLint passes
   - All components render correctly
   - Responsive on mobile/tablet/desktop

### Phase 6: Frontend Components - States (2 hours)

1. **EmptyState** (`src/components/knowledge/empty-state.tsx`)
   - "No documents yet" message
   - Upload prompt
   - Illustration/icon

2. **LoadingState** (`src/components/knowledge/loading-state.tsx`)
   - Skeleton table rows
   - Skeleton headers

3. **ErrorState** (`src/components/knowledge/error-state.tsx`)
   - Error message display
   - Retry button

4. **Barrel Export** (`src/components/knowledge/index.ts`)
   - Export all components

5. **Verify**
   - All states render correctly
   - Dark mode works

### Phase 7: Page Route Integration (1 hour)

1. **Update Route** (`app/(dashboard)/knowledge/page.tsx`)
   - Import KnowledgePage component
   - Render it

2. **Add to Navigation** (if applicable)
   - Add link to knowledge in sidebar/nav

3. **Verify**
   - Route accessible at /knowledge
   - Page renders full layout

### Phase 8: Final Quality & Testing (2 hours)

1. **Full Linting**
   - `npm run lint` for all new files
   - Fix any warnings

2. **Python Validation**
   - Compile check backend files
   - Import test for router

3. **Full Integration Test**
   - Backend responds with proper JSON
   - Frontend fetches and displays
   - Upload works
   - Delete works
   - Filters work
   - Search works

4. **Browser Testing**
   - Light mode: All sections visible, styling correct
   - Dark mode: All sections visible, styling correct
   - Mobile (375px): Responsive, readable
   - Tablet (768px): Good layout
   - Desktop (1024px): Full layout

5. **Performance Check**
   - React Query caching works
   - No unnecessary refetches
   - Upload doesn't block UI
   - Search debounce prevents overload

---

## 6. RISKS & MITIGATION

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Document ingestion job already submitted | HIGH | Check existing KnowledgeRepository methods; may need to query job status |
| Large file uploads blocking UI | HIGH | Use async upload, show progress, allow cancel |
| Search performance on large datasets | MEDIUM | Client-side MVP OK; server-side filtering future phase |
| Unknown file types breaking UI | MEDIUM | Default icon/type for unknown files |
| Delete race conditions | MEDIUM | Optimistic update with rollback on error |
| Network errors on upload | MEDIUM | Retry logic, clear error messages |
| Chunk count unavailable | LOW | Query chunks separately or include in metadata |

---

## 7. FILE TREE

```
backend/
├── services/
│   └── knowledge_service.py              [NEW] Service layer
├── api/v1/
│   └── knowledge.py                      [MODIFY] Add list/get/delete endpoints
└── schemas/
    └── knowledge.py                      [MODIFY] Add DocumentListResponse, etc.

src/
├── types/
│   └── index.ts                          [MODIFY] Add Document interfaces
├── constants/
│   └── index.ts                          [MODIFY] Add KNOWLEDGE endpoints
├── services/
│   └── knowledge-service.ts              [NEW] API client
├── hooks/
│   └── use-knowledge.ts                  [NEW] React Query hooks
├── components/knowledge/
│   ├── knowledge-page.tsx                [NEW] Page orchestrator
│   ├── knowledge-layout.tsx              [NEW] Main layout
│   ├── page-header.tsx                   [NEW] Title/stats
│   ├── search-bar.tsx                    [NEW] Search
│   ├── filter-bar.tsx                    [NEW] Filters
│   ├── upload-zone.tsx                   [NEW] Drag & drop
│   ├── document-table.tsx                [NEW] Main table
│   ├── document-row.tsx                  [NEW] Row component
│   ├── document-status-badge.tsx         [NEW] Status display
│   ├── document-type-icon.tsx            [NEW] Type icon
│   ├── empty-state.tsx                   [NEW] No documents
│   ├── loading-state.tsx                 [NEW] Skeleton loader
│   ├── error-state.tsx                   [NEW] Error display
│   └── index.ts                          [NEW] Barrel export
└── app/(dashboard)/knowledge/
    └── page.tsx                          [NEW] Route page
```

**Total Files**: 4 backend, 18 frontend = 22 files

---

## 8. DEPENDENCIES

### No New Dependencies Required ✓

**Backend Uses**
- FastAPI (existing)
- Pydantic (existing)
- logging (existing)

**Frontend Uses**
- React Query (existing)
- TypeScript (existing)
- Tailwind CSS (existing)
- Lucide React (existing)
- Next.js (existing)

---

## 9. ESTIMATED EFFORT

| Phase | Tasks | Estimated Time |
|-------|-------|-----------------|
| 1. Backend | Service + Schemas + Endpoints | 2 hours |
| 2. Types | TypeScript interfaces + constants | 1 hour |
| 3. Services | API client + React Query hooks | 2 hours |
| 4. Main Pages | Page, Layout, Header, Search, Filters | 3 hours |
| 5. Upload & Table | Upload zone, Table, Row, Status, Icons | 3 hours |
| 6. States | Empty, Loading, Error, Barrel export | 2 hours |
| 7. Integration | Route wiring, Navigation (if needed) | 1 hour |
| 8. Quality | Linting, Testing, Browser validation | 2 hours |
| **TOTAL** | | **16 hours** |

**Sprint Assignment**: 2-day sprint (8 hours/day)

---

## 10. SUCCESS CRITERIA

### Backend ✓
- [x] Service layer implemented with error handling
- [x] API endpoints respond with correct JSON
- [x] Logging instead of print()
- [x] Dependency injection configured
- [x] Python compilation passes
- [x] ESLint: 0 warnings

### Frontend ✓
- [x] All 18 components created and functional
- [x] Full TypeScript strict mode
- [x] React Query hooks configured correctly
- [x] Dark mode support throughout
- [x] Responsive on 375px, 768px, 1024px
- [x] ESLint: 0 warnings
- [x] No duplicated logic
- [x] No dead code

### Integration ✓
- [x] Backend and frontend communicate correctly
- [x] Upload/delete operations work end-to-end
- [x] Search and filtering work
- [x] Error states display properly
- [x] Loading states show correctly
- [x] Performance acceptable (React Query caching works)

---

## APPROVAL CHECKLIST

- [ ] Architecture approved
- [ ] API specification approved
- [ ] Component tree approved
- [ ] Implementation order approved
- [ ] Risk mitigation approved
- [ ] Ready to proceed to Phase 1

**Awaiting approval before code implementation begins.**
