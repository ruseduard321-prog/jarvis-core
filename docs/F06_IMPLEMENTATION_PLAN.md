# F06 - Dashboard Implementation Plan

**Feature**: F06 Dashboard  
**Status**: Planning (Awaiting Approval)  
**Duration Estimate**: 4-5 sprints  
**Priority**: High (core platform feature)  
**Scalability**: Designed for future module expansion

---

## Executive Summary

F06 Dashboard is the permanent, scalable home page and central hub of Jarvis. It displays operational visibility across the entire platform with a focus on:

- **Statistics & Metrics**: Real-time platform health and usage data
- **Quick Actions**: Fast access to core operations
- **Recent Activity**: User's recent work and system events
- **System Status**: Infrastructure and AI provider health
- **Responsive Design**: Works on all screen sizes
- **Extensibility**: Designed to accommodate future modules (Knowledge, Agents, Documents, etc.)

The dashboard is NOT temporary. It will evolve with the platform and should never require a redesign as features are added.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      Dashboard Page (Route)                      │
│  /dashboard                                                       │
└────────┬──────────────────────────────────────────────────────────┘
         │
         ├─ DashboardLayout (Main container with grid)
         │
         ├── StatisticsSection
         │   ├─ StatCard (Conversations)
         │   ├─ StatCard (Messages)
         │   ├─ StatCard (Documents)
         │   └─ StatCard (Knowledge Items)
         │
         ├── QuickActionsSection
         │   ├─ ActionCard (New Chat)
         │   ├─ ActionCard (Upload Document)
         │   ├─ ActionCard (Knowledge Base)
         │   └─ ActionCard (Manage Agents)
         │
         ├── RecentConversationsSection
         │   └─ ConversationList (Recent 5-10)
         │
         ├── RecentActivitySection
         │   └─ ActivityFeed (Recent events)
         │
         └── SystemStatusSection
             ├─ StatusIndicator (Backend)
             ├─ StatusIndicator (Database)
             └─ StatusIndicator (AI Provider)

DATA FLOW:

Frontend (useDashboard hook)
    ↓
React Query + Zustand caching
    ↓
DashboardService (API client)
    ↓
GET /api/v1/dashboard/stats
GET /api/v1/dashboard/recent-conversations
GET /api/v1/dashboard/activity
GET /api/v1/dashboard/system-status
    ↓
Backend API Routes
    ↓
DashboardService (Business logic)
    ↓
Multiple Data Sources:
├─ ConversationStore (conversation stats)
├─ ConversationEngine (recent conversations)
├─ EventBusService (activity feed)
├─ MemoryService (knowledge items)
├─ AgentRegistry (agents count)
├─ HealthCheck (system status)
└─ MetricsProvider (usage data)
```

---

## Detailed Implementation Plan

### PHASE 1: Backend Foundation

#### 1.1 Create Dashboard Schemas
**File**: `backend/schemas/dashboard.py`

```python
# Type definitions for dashboard data

DashboardStatistics:
  - total_conversations: int
  - total_messages: int
  - total_documents: int
  - total_knowledge_items: int
  - total_agents: int
  - today_activity_count: int

ConversationSummary:
  - id: str
  - title: str
  - last_message_at: datetime
  - message_count: int
  - status: str

ActivityEvent:
  - id: str
  - type: str (conversation_created | message_sent | document_uploaded | agent_executed)
  - timestamp: datetime
  - description: str
  - metadata: dict

SystemStatusInfo:
  - status: str (healthy | degraded | unhealthy)
  - backend: StatusIndicator
  - database: StatusIndicator
  - ai_provider: StatusIndicator
  - timestamp: datetime

StatusIndicator:
  - name: str
  - status: str (online | offline | degraded)
  - message: str
  - timestamp: datetime

DashboardResponse (Complete dashboard state):
  - statistics: DashboardStatistics
  - recent_conversations: list[ConversationSummary]
  - activity_feed: list[ActivityEvent]
  - system_status: SystemStatusInfo
  - timestamp: datetime
```

#### 1.2 Create Dashboard Service
**File**: `backend/services/dashboard_service.py`

Inherits from `BaseService` pattern.

**Methods**:
```python
class DashboardService:
    def __init__(self, 
                 conversation_store: ConversationStore,
                 event_bus_service: EventBusService,
                 memory_service: MemoryService,
                 agent_registry: AgentRegistry,
                 llm_provider: LLMProvider):
        self.conversation_store = conversation_store
        self.event_bus_service = event_bus_service
        self.memory_service = memory_service
        self.agent_registry = agent_registry
        self.llm_provider = llm_provider
    
    async def get_statistics() -> DashboardStatistics:
        """Aggregate statistics from all systems."""
        # Count conversations, messages, documents, knowledge items, agents
        # Filter by today for activity count
    
    async def get_recent_conversations(limit: int = 10) -> list[ConversationSummary]:
        """Get recent conversations sorted by update time."""
        # Fetch from ConversationStore, sort by updated_at DESC
    
    async def get_activity_feed(limit: int = 20) -> list[ActivityEvent]:
        """Get recent system events from EventBus."""
        # Fetch from EventBusService
    
    async def get_system_status() -> SystemStatusInfo:
        """Check health of all systems."""
        # Call health checks for backend, DB, AI provider
    
    async def get_dashboard() -> DashboardResponse:
        """Get complete dashboard state (all sections)."""
        # Aggregates all above methods
```

#### 1.3 Create Dashboard API Endpoints
**File**: `backend/api/v1/dashboard.py`

**Endpoints**:
```
GET /api/v1/dashboard
  Returns: DashboardResponse (complete dashboard)
  Purpose: Main endpoint - fetch all dashboard data at once
  
GET /api/v1/dashboard/stats
  Returns: DashboardStatistics
  Purpose: Just statistics (lighter for refresh)
  
GET /api/v1/dashboard/recent-conversations
  Returns: list[ConversationSummary]
  Purpose: Just recent conversations
  Query params: limit (default 10, max 50)
  
GET /api/v1/dashboard/activity
  Returns: list[ActivityEvent]
  Purpose: Just activity feed
  Query params: limit (default 20, max 100)
  
GET /api/v1/dashboard/system-status
  Returns: SystemStatusInfo
  Purpose: Just system health
```

#### 1.4 Register Dashboard Routes
**File**: `backend/api/v1/router.py`

Add: `router.include_router(dashboard_router, prefix="/dashboard")`

#### 1.5 Update Dependencies
**File**: `backend/core/dependencies.py`

Add:
```python
def get_dashboard_service() -> DashboardService:
    return SERVICE_REGISTRY.get_dashboard_service()
```

---

### PHASE 2: Frontend API Client

#### 2.1 Create Dashboard Service
**File**: `src/services/dashboard-service.ts`

```typescript
class DashboardService {
  async getDashboard(): Promise<DashboardResponse>
  async getStatistics(): Promise<DashboardStatistics>
  async getRecentConversations(limit?: number): Promise<ConversationSummary[]>
  async getActivityFeed(limit?: number): Promise<ActivityEvent[]>
  async getSystemStatus(): Promise<SystemStatusInfo>
}
```

#### 2.2 Create Dashboard Hooks
**File**: `src/hooks/useDashboard.ts`

```typescript
// React Query hooks for dashboard data fetching

export function useDashboard(options?: UseQueryOptions) {
  // Fetch complete dashboard with React Query
  // Refetch interval: 30-60 seconds for freshness
  // Stale time: 10-15 seconds
}

export function useDashboardStatistics(options?: UseQueryOptions) {
  // Fetch just statistics (faster refresh)
  // Refetch interval: 20-30 seconds
}

export function useRecentConversations(limit?: number, options?: UseQueryOptions) {
  // Fetch recent conversations
}

export function useDashboardActivity(limit?: number, options?: UseQueryOptions) {
  // Fetch activity feed
}

export function useSystemStatus(options?: UseQueryOptions) {
  // Fetch system health
  // Refetch interval: 30-60 seconds
}
```

---

### PHASE 3: Frontend Components

#### 3.1 Create Component Files

**Core Components**:
```
src/components/dashboard/
├── index.ts (barrel export)
├── dashboard-page.tsx (Main page component)
├── dashboard-layout.tsx (Grid layout wrapper)
├── statistics-section.tsx
├── quick-actions-section.tsx
├── recent-conversations-section.tsx
├── activity-section.tsx
└── system-status-section.tsx

Sub-components:
├── stat-card.tsx (Reusable statistic card)
├── action-card.tsx (Quick action button/card)
├── conversation-list-item.tsx
├── activity-item.tsx (Activity feed item)
├── status-indicator.tsx (System status icon)
└── dashboard-skeleton.tsx (Loading state)
```

#### 3.2 Detailed Component Specs

**DashboardPage** (`dashboard-page.tsx`):
- Orchestrator component
- Uses `useDashboard()` hook
- Shows loading skeleton while fetching
- Shows error state with retry
- Shows empty state if no data
- Layout: responsive grid

**DashboardLayout** (`dashboard-layout.tsx`):
- Grid container (responsive 1-2-3 columns)
- Sections: top-to-bottom priority order
  1. Statistics (spans full width on mobile)
  2. Quick Actions
  3. Recent Conversations
  4. Activity Feed
  5. System Status

**StatCard** (`stat-card.tsx`):
- Label, value, trend (up/down/neutral)
- Icon support
- Loading state
- Dark/light theme
- Reusable for all stats

**ActionCard** (`action-card.tsx`):
- Icon, label, description
- Click handler
- Loading state
- Disabled state
- Hover effects
- Route navigation

**ConversationListItem** (`conversation-list-item.tsx`):
- Title, last updated, message count
- Click → navigate to chat
- Hover effects
- Timestamp formatting

**ActivityItem** (`activity-item.tsx`):
- Event type icon
- Description text
- Timestamp
- Metadata (if relevant)
- Color coding by type

**StatusIndicator** (`status-indicator.tsx`):
- Circular indicator (online/offline/degraded)
- Tooltip with details
- Label
- Pulse animation for "degraded"

---

### PHASE 4: Frontend Page Integration

#### 4.1 Update Dashboard Route
**File**: `app/(dashboard)/dashboard/page.tsx`

Replace placeholder with actual dashboard page component:
```typescript
import DashboardPage from "@/components/dashboard/dashboard-page";

export default function Dashboard() {
  return <DashboardPage />;
}
```

#### 4.2 Update Dashboard Type Definitions
**File**: `src/types/index.ts`

Add dashboard types:
```typescript
interface DashboardStatistics {
  total_conversations: number;
  total_messages: number;
  total_documents: number;
  total_knowledge_items: number;
  total_agents: number;
  today_activity_count: number;
}

interface ConversationSummary {
  id: string;
  title: string;
  last_message_at: string;
  message_count: number;
  status: string;
}

interface ActivityEvent {
  id: string;
  type: 'conversation_created' | 'message_sent' | 'document_uploaded' | 'agent_executed';
  timestamp: string;
  description: string;
  metadata: Record<string, any>;
}

interface SystemStatusInfo {
  status: 'healthy' | 'degraded' | 'unhealthy';
  backend: StatusIndicator;
  database: StatusIndicator;
  ai_provider: StatusIndicator;
  timestamp: string;
}

interface StatusIndicator {
  name: string;
  status: 'online' | 'offline' | 'degraded';
  message: string;
  timestamp: string;
}

interface DashboardResponse {
  statistics: DashboardStatistics;
  recent_conversations: ConversationSummary[];
  activity_feed: ActivityEvent[];
  system_status: SystemStatusInfo;
  timestamp: string;
}
```

---

## Data Sources & Calculations

### Statistics Calculations

| Stat | Source | Method |
|------|--------|--------|
| **Total Conversations** | ConversationStore | `len(conversations)` |
| **Total Messages** | ConversationStore | Sum of `len(conv.messages)` for all conversations |
| **Total Documents** | DocumentStore/KnowledgeRepository | Count stored documents |
| **Total Knowledge Items** | MemoryService/VectorStore | Count knowledge items |
| **Total Agents** | AgentRegistry | Count registered agents |
| **Today's Activity** | EventBusService | Filter events where `timestamp > today_start` |

### Recent Conversations

Sort by `updated_at DESC`, limit to 10-15 most recent.

### Activity Feed

Pull events from EventBusService, filter by:
- Last N hours (24-48)
- Event types: conversation_created, message_sent, document_uploaded, agent_executed
- Sort by timestamp DESC

### System Status

Run health checks:
- **Backend**: Check if API responsive (`GET /api/v1/health`)
- **Database**: Check database connectivity
- **AI Provider**: Check OpenAI API health

---

## Scalability & Future Modules

### Design Principles for Extensibility

1. **Modular Sections**: Each section is independent
   - Can add new sections without modifying others
   - Can reorder sections easily
   - Can enable/disable sections via feature flags

2. **Pluggable Data Sources**: DashboardService can be extended
   - Add new data source methods without changing existing
   - Statistics can include data from future modules
   - Activity feed can accept events from any system

3. **Component Composition**: Reusable building blocks
   - StatCard can display any metric
   - ActionCard can link to any feature
   - ActivityItem can display any event type

### Future Module Integration Points

When new modules are added:

**Knowledge Module**:
- Update statistics to include knowledge items from KnowledgeStore
- Add activity events for document uploads, searches
- Add action: "Browse Knowledge Base"

**Agents Module**:
- Add action: "Create Agent"
- Add statistics for agent count
- Add activity events for agent executions
- Add section: "Recent Agent Runs"

**Documents Module**:
- Add statistics for document count
- Add activity events for uploads
- Add action: "Upload Document"
- Add section: "Recent Documents"

**Automation Module**:
- Add statistics for workflow count
- Add activity events for workflow executions
- Add action: "Create Workflow"

**Settings Module**:
- Add quick action link to settings

---

## Files to Create

### Backend (6 files)
1. `backend/schemas/dashboard.py` - Dashboard data models (Pydantic schemas)
2. `backend/services/dashboard_service.py` - Business logic
3. `backend/api/v1/dashboard.py` - API endpoints and routes
4. `backend/repositories/dashboard_repository.py` - Optional, if database queries needed
5. `backend/core/dashboard_models.py` - Internal models (if complex)
6. `backend/core/dashboard_cache.py` - Optional caching layer

### Frontend (10 files)
1. `src/services/dashboard-service.ts` - API client
2. `src/hooks/useDashboard.ts` - React Query hooks
3. `src/components/dashboard/index.ts` - Barrel export
4. `src/components/dashboard/dashboard-page.tsx` - Main page
5. `src/components/dashboard/dashboard-layout.tsx` - Layout grid
6. `src/components/dashboard/statistics-section.tsx` - Statistics
7. `src/components/dashboard/quick-actions-section.tsx` - Quick actions
8. `src/components/dashboard/recent-conversations-section.tsx` - Conversations
9. `src/components/dashboard/activity-section.tsx` - Activity feed
10. `src/components/dashboard/system-status-section.tsx` - System status

### Documentation (2 files)
1. `docs/architecture/DASHBOARD_ARCHITECTURE.md` - Design doc
2. `docs/F06_IMPLEMENTATION_SUMMARY.md` - Completion summary

---

## Files to Modify

### Backend (3 files)
1. `backend/api/v1/router.py` - Register dashboard router
2. `backend/core/dependencies.py` - Add get_dashboard_service dependency
3. `backend/core/service_registry.py` - Register DashboardService in registry

### Frontend (2 files)
1. `app/(dashboard)/dashboard/page.tsx` - Replace placeholder
2. `src/types/index.ts` - Add dashboard type definitions

---

## API Endpoints

### Endpoint: GET /api/v1/dashboard
**Purpose**: Fetch complete dashboard state (all sections at once)

**Response**:
```json
{
  "statistics": {
    "total_conversations": 42,
    "total_messages": 1256,
    "total_documents": 18,
    "total_knowledge_items": 156,
    "total_agents": 5,
    "today_activity_count": 23
  },
  "recent_conversations": [
    {
      "id": "uuid",
      "title": "Project Planning",
      "last_message_at": "2026-07-19T14:30:00Z",
      "message_count": 24,
      "status": "active"
    },
    ...
  ],
  "activity_feed": [
    {
      "id": "uuid",
      "type": "message_sent",
      "timestamp": "2026-07-19T14:45:23Z",
      "description": "You sent a message in Project Planning",
      "metadata": { "conversation_id": "uuid" }
    },
    ...
  ],
  "system_status": {
    "status": "healthy",
    "backend": {
      "name": "Backend API",
      "status": "online",
      "message": "All systems operational",
      "timestamp": "2026-07-19T14:50:00Z"
    },
    "database": {
      "name": "Database",
      "status": "online",
      "message": "Connected",
      "timestamp": "2026-07-19T14:50:00Z"
    },
    "ai_provider": {
      "name": "OpenAI",
      "status": "online",
      "message": "API responsive",
      "timestamp": "2026-07-19T14:50:00Z"
    },
    "timestamp": "2026-07-19T14:50:00Z"
  },
  "timestamp": "2026-07-19T14:50:00Z"
}
```

### Endpoint: GET /api/v1/dashboard/stats
**Purpose**: Fetch statistics only (faster, for periodic refresh)

**Response**: `DashboardStatistics` object only

### Endpoint: GET /api/v1/dashboard/recent-conversations
**Purpose**: Fetch recent conversations

**Query Parameters**: `limit` (default: 10, max: 50)

**Response**: Array of `ConversationSummary`

### Endpoint: GET /api/v1/dashboard/activity
**Purpose**: Fetch activity feed

**Query Parameters**: `limit` (default: 20, max: 100)

**Response**: Array of `ActivityEvent`

### Endpoint: GET /api/v1/dashboard/system-status
**Purpose**: Fetch system health status

**Response**: `SystemStatusInfo` object

---

## React Components Summary

| Component | Purpose | Reusable | Props |
|-----------|---------|----------|-------|
| StatCard | Display single metric | Yes | label, value, trend, icon |
| ActionCard | Quick action button | Yes | icon, label, description, onClick |
| ConversationListItem | List item for conversations | Yes | conversation, onClick |
| ActivityItem | Activity feed item | Yes | event, onClick |
| StatusIndicator | Health status badge | Yes | name, status, message |
| DashboardSkeleton | Loading placeholder | Yes | sections |

---

## Risks & Mitigations

### Risk 1: Performance - Dashboard Takes Too Long to Load
**Severity**: High  
**Mitigation**: 
- Implement React Query caching with appropriate stale times (10-15s)
- Add loading skeletons for visual feedback
- Consider separate endpoints for heavy sections (can be loaded in parallel)
- Implement lazy loading for activity feed

### Risk 2: Data Accuracy - Dashboard Stats Out of Sync
**Severity**: Medium  
**Mitigation**:
- EventBusService should emit events in real-time
- Use React Query refetch intervals (20-60s depending on metric)
- Add manual refresh button for user
- Display timestamp to show data freshness

### Risk 3: Backend Crashes - Health Check Failures
**Severity**: Medium  
**Mitigation**:
- Wrap health check calls in try-catch
- Return "degraded" status if one check fails
- Set timeouts on health check calls (2-3s)
- Don't block main dashboard load if health check fails

### Risk 4: Extensibility - Hard to Add Modules Later
**Severity**: Low  
**Mitigation**:
- Use modular section design
- Use feature flags for new sections
- Keep DashboardService as simple data aggregator
- Document plugin points clearly

### Risk 5: Type Safety - Breaking API Changes
**Severity**: Low  
**Mitigation**:
- Keep schema versioning in mind (v1, v2, etc.)
- Add tests for API contracts
- Document breaking changes in CHANGELOG

---

## Implementation Phases

### Phase 1: Backend Foundation (1-2 sprints)
- Create schemas and service
- Create API endpoints
- Register routes
- Test endpoints with Postman/cURL

### Phase 2: Frontend API Client (0.5 sprint)
- Create dashboard service
- Create React Query hooks
- Update type definitions

### Phase 3: Frontend UI Components (1.5-2 sprints)
- Create all components
- Build component composition
- Implement loading/error states
- Test in browser

### Phase 4: Integration & Polish (0.5-1 sprint)
- Wire page to components
- Add animations/transitions
- Responsive design testing
- Dark mode verification
- Performance optimization

### Phase 5: Documentation & Testing (0.5 sprint)
- Write F06_IMPLEMENTATION_SUMMARY.md
- Create DASHBOARD_ARCHITECTURE.md
- Document component usage
- Create dashboard showcase page (optional)

---

## Testing Strategy

### Backend Tests
```python
# Test DashboardService
- test_get_statistics_returns_correct_counts
- test_get_statistics_includes_today_activity_only
- test_get_recent_conversations_sorted_by_update_time
- test_get_recent_conversations_limited_to_10
- test_get_activity_feed_filters_event_types
- test_get_system_status_returns_all_indicators
- test_get_dashboard_returns_complete_response
```

### Frontend Tests
```typescript
// Component rendering
- DashboardPage renders without errors
- All sections render
- Loading state shows skeleton
- Error state shows retry

// Data fetching
- useDashboard hook fetches data correctly
- React Query caching works
- Refetch intervals configured
- Error handling works

// Responsive design
- Mobile layout (1 column)
- Tablet layout (2 columns)
- Desktop layout (3 columns)
```

### Integration Tests
```
- Frontend calls correct API endpoints
- Data flows from backend to components
- Charts display correct data
- Actions navigate correctly
```

---

## Success Criteria

✅ **Functional**:
- All sections render with real data
- Statistics display correct counts
- Recent conversations list shows 10 most recent
- Activity feed shows recent events
- System status indicators working
- Quick actions navigate correctly

✅ **Performance**:
- Dashboard loads in < 2 seconds
- Skeleton shown immediately
- No layout shift (CLS < 0.1)
- Metrics refresh every 30-60s

✅ **UX**:
- Responsive on all screen sizes
- Works in dark and light mode
- Loading states visible
- Error states with retry
- Empty states handled

✅ **Code Quality**:
- All TypeScript strict mode
- Zero ESLint errors
- Full documentation
- Follows PROJECT_RULES.md
- No code duplication

✅ **Scalability**:
- Easy to add new sections
- Extensible for future modules
- Modular component design
- Clear plugin points

---

## Timeline Estimate

| Phase | Duration | Effort |
|-------|----------|--------|
| Phase 1: Backend | 1-2 sprints | 20-40 hours |
| Phase 2: Frontend API | 0.5 sprint | 5-8 hours |
| Phase 3: UI Components | 1.5-2 sprints | 30-40 hours |
| Phase 4: Integration | 0.5-1 sprint | 8-15 hours |
| Phase 5: Documentation | 0.5 sprint | 5-8 hours |
| **Total** | **4-6 sprints** | **68-111 hours** |

---

## Next Steps (After Approval)

1. ✅ Get approval on this plan
2. Create all backend files
3. Create backend tests
4. Create all frontend files
5. Create frontend tests
6. Integration testing
7. Performance optimization
8. Documentation
9. Code review
10. Merge to main

---

*End of F06_IMPLEMENTATION_PLAN.md*
