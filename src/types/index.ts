// API Response types
export interface ApiResponse<T = unknown> {
  data?: T;
  error?: string;
  message?: string;
  status: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  hasMore: boolean;
}

// Auth types
export interface AuthUser {
  id: string;
  email: string;
  full_name?: string | null;
}

export interface AuthSession {
  access_token: string;
  refresh_token: string;
  expires_at: string; // ISO 8601 datetime
}

export interface User {
  id: string;
  email: string;
  name: string;
  avatar?: string;
  createdAt: string;
  updatedAt: string;
}

export type AuthStatus = "unauthenticated" | "authenticated" | "loading" | "error";

export interface AuthContextValue {
  user: AuthUser | null;
  status: AuthStatus;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  restoreSession: () => Promise<void>;
}

// Chat types
export interface Conversation {
  id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
  metadata: Record<string, unknown>;
}

export interface Prompt {
  id: string;
  name: string;
  content: string;
  category: PromptCategory;
  favorite: boolean;
  created_at: string;
  updated_at: string;
}

export type PromptCategory = "Chat" | "System" | "Coding" | "Analysis" | "Writing" | "Creative";

export type MessageRole = "system" | "user" | "assistant" | "developer" | "tool";

export interface Message {
  id: string;
  conversation_id: string;
  content: string;
  role: MessageRole;
  created_at: string;
  metadata: Record<string, unknown>;
}

export interface ChatCompletionRequest {
  conversation_id: string;
  message: string;
  use_rag: boolean;
  stream: boolean;
  metadata: Record<string, unknown>;
}

export interface ChatCompletionResponse {
  conversation_id: string;
  user_message_id: string;
  assistant_message_id: string;
  content: string;
  tokens_used?: number;
  rag_context_used: boolean;
  metadata: Record<string, unknown>;
}

export interface StreamEvent {
  event: "start" | "token" | "end" | "error";
  data?: string;
  message_id?: string;
}

// Knowledge types
export interface Knowledge {
  id: string;
  title: string;
  content: string;
  metadata?: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
}

// Tool types
export interface Tool {
  slug: string;
  name: string;
  description: string;
  capabilities: string[];
}

export interface ToolExecution {
  id: string;
  toolId: string;
  input: Record<string, unknown>;
  output: Record<string, unknown>;
  status: "pending" | "success" | "failed";
  createdAt: string;
}

// Agent types
export interface Agent {
  id: string;
  slug: string;
  owner_user_id: string;
  name: string;
  mission: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// Error types
export interface ApiError {
  code: string;
  message: string;
  status: number;
  details?: Record<string, unknown>;
}

// Request types
export interface RequestConfig {
  timeout?: number;
  retries?: number;
  headers?: Record<string, string>;
}

// Dashboard types
export interface StatusIndicator {
  name: string;
  status: "online" | "offline" | "degraded";
  message: string;
  timestamp: string;
}

export interface SystemStatus {
  status: "healthy" | "degraded" | "unhealthy";
  backend: StatusIndicator;
  database: StatusIndicator;
  ai_provider: StatusIndicator;
  timestamp: string;
}

export interface DashboardStatistics {
  total_conversations: number;
  total_messages: number;
  total_knowledge_items: number;
  total_agents: number;
  total_documents: number;
  today_activity: number;
}

export interface ConversationSummary {
  id: string;
  title: string;
  message_count: number;
  last_message_at: string;
  status: string;
}

export interface ActivityEvent {
  id: string;
  type: string;
  timestamp: string;
  description: string;
  metadata: Record<string, unknown>;
}

export interface QuickAction {
  id: string;
  label: string;
  description: string;
  icon: string;
  href: string;
}

export interface DashboardResponse {
  statistics: DashboardStatistics;
  recent_conversations: ConversationSummary[];
  activity: ActivityEvent[];
  system_status: SystemStatus;
  quick_actions: QuickAction[];
  timestamp: string;
}

// Knowledge Base / Document types
export interface Document {
  id: string;
  title: string;
  source_type: string;
  source_identifier?: string | null;
  chunk_count: number;
  tags: string[];
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface KnowledgeListResponse {
  documents: Document[];
  total_count: number;
  timestamp: string;
}

export type IngestionStatus = "pending" | "processing" | "completed" | "failed";
export type DocumentType = "pdf" | "text" | "markdown" | "docx" | "csv" | "json";

// Memory types
export type MemoryCategory = "FACT" | "REASONING" | "CONTEXT" | "INSIGHT" | "PATTERN" | "DECISION";
export type MemoryImportance = "high" | "medium" | "low";

export interface Memory {
  id: string;
  record_type: MemoryCategory;
  content: string;
  source?: string | null;
  tags: string[];
  attributes: Record<string, unknown> & { importance?: MemoryImportance };
  created_at: string;
  updated_at: string;
}

export interface MemoryListResponse {
  memories: Memory[];
  total_count: number;
  timestamp: string;
}
