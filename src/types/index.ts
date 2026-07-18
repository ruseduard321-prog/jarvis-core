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
export interface User {
  id: string;
  email: string;
  name: string;
  avatar?: string;
  createdAt: string;
  updatedAt: string;
}

export interface AuthContext {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

// Conversation types
export interface Message {
  id: string;
  conversationId: string;
  role: "user" | "assistant";
  content: string;
  createdAt: string;
  metadata?: Record<string, unknown>;
}

export interface Conversation {
  id: string;
  title: string;
  description?: string;
  messages: Message[];
  createdAt: string;
  updatedAt: string;
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
  id: string;
  name: string;
  description: string;
  inputSchema?: Record<string, unknown>;
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
  name: string;
  description: string;
  tools: Tool[];
  createdAt: string;
  updatedAt: string;
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
