// API endpoints
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export const API_ENDPOINTS = {
  // Auth
  AUTH: {
    LOGIN: "/auth/login",
    LOGOUT: "/auth/logout",
    REGISTER: "/auth/register",
    ME: "/auth/me",
    REFRESH: "/auth/refresh",
  },
  // Conversations
  CONVERSATIONS: {
    LIST: "/conversations",
    CREATE: "/conversations",
    GET: (id: string) => `/conversations/${id}`,
    UPDATE: (id: string) => `/conversations/${id}`,
    DELETE: (id: string) => `/conversations/${id}`,
    MESSAGES: (id: string) => `/conversations/${id}/messages`,
    CHAT: (id: string) => `/conversations/${id}/chat`,
  },
  // Knowledge
  KNOWLEDGE: {
    LIST: "/knowledge",
    CREATE: "/knowledge",
    GET: (id: string) => `/knowledge/${id}`,
    UPDATE: (id: string) => `/knowledge/${id}`,
    DELETE: (id: string) => `/knowledge/${id}`,
    SEARCH: "/knowledge/search",
  },
  // Documents
  DOCUMENTS: {
    LIST: "/documents",
    UPLOAD: "/documents/upload",
    GET: (id: string) => `/documents/${id}`,
    DELETE: (id: string) => `/documents/${id}`,
  },
  // Tools
  TOOLS: {
    LIST: "/tools",
    GET: (id: string) => `/tools/${id}`,
    EXECUTE: (id: string) => `/tools/${id}/execute`,
  },
  // Agents
  AGENTS: {
    LIST: "/agents",
    GET: (id: string) => `/agents/${id}`,
    EXECUTE: (id: string) => `/agents/${id}/execute`,
  },
};

// Feature flags
export const FEATURES = {
  CHAT: "chat",
  KNOWLEDGE: "knowledge",
  TOOLS: "tools",
  AGENTS: "agents",
  WORKFLOWS: "workflows",
  SETTINGS: "settings",
} as const;

// UI Constants
export const TOAST_DURATION = 3000;
export const MODAL_ANIMATION_DURATION = 200;
export const DEBOUNCE_DELAY = 300;
export const SEARCH_DEBOUNCE_DELAY = 500;

// Pagination
export const DEFAULT_PAGE_SIZE = 20;
export const DEFAULT_PAGE = 1;

// HTTP Methods
export const HTTP_METHODS = {
  GET: "GET",
  POST: "POST",
  PUT: "PUT",
  PATCH: "PATCH",
  DELETE: "DELETE",
} as const;

// Error messages
export const ERROR_MESSAGES = {
  NETWORK_ERROR: "Network error. Please check your connection.",
  UNAUTHORIZED: "Unauthorized. Please log in.",
  FORBIDDEN: "Access denied.",
  NOT_FOUND: "Resource not found.",
  SERVER_ERROR: "Server error. Please try again later.",
  VALIDATION_ERROR: "Validation error. Please check your input.",
} as const;

// Success messages
export const SUCCESS_MESSAGES = {
  CREATED: "Created successfully.",
  UPDATED: "Updated successfully.",
  DELETED: "Deleted successfully.",
  SAVED: "Saved successfully.",
  COPIED: "Copied to clipboard.",
} as const;

// Validation patterns
export const VALIDATION = {
  EMAIL: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  URL: /^https?:\/\/.+/,
  SLUG: /^[a-z0-9]+(?:-[a-z0-9]+)*$/,
} as const;

// Animation durations (ms)
export const DURATIONS = {
  INSTANT: 0,
  FAST: 150,
  BASE: 200,
  SLOW: 300,
} as const;

// Z-index scale
export const Z_INDEX = {
  DROPDOWN: 1000,
  STICKY: 1020,
  FIXED: 1030,
  MODAL_BACKDROP: 1040,
  MODAL: 1050,
  POPOVER: 1060,
  TOOLTIP: 1070,
} as const;

// Responsive breakpoints
export const BREAKPOINTS = {
  xs: 320,
  sm: 640,
  md: 768,
  lg: 1024,
  xl: 1280,
  "2xl": 1536,
} as const;
