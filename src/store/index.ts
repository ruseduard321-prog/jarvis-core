import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { AuthUser, AuthSession } from "@/types";

// Theme Store
interface ThemeState {
  theme: "light" | "dark" | "system";
  setTheme: (theme: "light" | "dark" | "system") => void;
  resolvedTheme: "light" | "dark";
  setResolvedTheme: (theme: "light" | "dark") => void;
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set) => ({
      theme: "system",
      setTheme: (theme) => set({ theme }),
      resolvedTheme: "light",
      setResolvedTheme: (theme) => set({ resolvedTheme: theme }),
    }),
    {
      name: "theme-storage",
    }
  )
);

// UI Store
interface UiState {
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
  mobileMenuOpen: boolean;
  setMobileMenuOpen: (open: boolean) => void;
  notificationsOpen: boolean;
  setNotificationsOpen: (open: boolean) => void;
}

export const useUiStore = create<UiState>((set) => ({
  sidebarOpen: true,
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  mobileMenuOpen: false,
  setMobileMenuOpen: (open) => set({ mobileMenuOpen: open }),
  notificationsOpen: false,
  setNotificationsOpen: (open) => set({ notificationsOpen: open }),
}));

// Auth Store
interface AuthState {
  // Tokens
  accessToken: string | null;
  refreshToken: string | null;
  expiresAt: string | null;

  // User data
  user: AuthUser | null;
  userId: string | null; // For backward compatibility

  // Status
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  // Actions
  setAuth: (session: AuthSession, user: AuthUser) => void;
  setUser: (user: AuthUser) => void;
  setTokens: (accessToken: string, refreshToken: string, expiresAt: string) => void;
  clearAuth: () => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  getAccessToken: () => string | null;
  hasValidToken: () => boolean;
  isTokenExpired: () => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      accessToken: null,
      refreshToken: null,
      expiresAt: null,
      user: null,
      userId: null,
      isAuthenticated: false,
      // Starts true: AuthProvider's init effect is the source of truth for whether a
      // persisted session is actually valid, and route guards must wait for it before
      // deciding to redirect — otherwise a child effect can redirect before the parent
      // AuthProvider effect has had a chance to run (see useProtectedRoute).
      isLoading: true,
      error: null,

      setAuth: (session, user) =>
        set({
          accessToken: session.access_token,
          refreshToken: session.refresh_token,
          expiresAt: session.expires_at,
          user,
          userId: user.id,
          isAuthenticated: true,
          error: null,
        }),

      setUser: (user) =>
        set({
          user,
          userId: user.id,
        }),

      setTokens: (accessToken, refreshToken, expiresAt) =>
        set({
          accessToken,
          refreshToken,
          expiresAt,
          isAuthenticated: true,
        }),

      clearAuth: () =>
        set({
          accessToken: null,
          refreshToken: null,
          expiresAt: null,
          user: null,
          userId: null,
          isAuthenticated: false,
          error: null,
        }),

      setLoading: (loading) => set({ isLoading: loading }),
      setError: (error) => set({ error }),

      getAccessToken: () => get().accessToken,

      hasValidToken: () => {
        const token = get().accessToken;
        return !!token;
      },

      isTokenExpired: () => {
        const expiresAt = get().expiresAt;
        if (!expiresAt) return true;
        return new Date(expiresAt) <= new Date();
      },
    }),
    {
      name: "auth-storage",
      // Only persist sensitive fields
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        expiresAt: state.expiresAt,
        user: state.user,
        userId: state.userId,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

// Conversation Store
interface ConversationState {
  currentConversationId: string | null;
  setCurrentConversationId: (id: string | null) => void;
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
  draftMessage: string;
  setDraftMessage: (message: string) => void;
  isStreaming: boolean;
  setIsStreaming: (streaming: boolean) => void;
  streamingMessageId: string | null;
  setStreamingMessageId: (id: string | null) => void;
}

export const useConversationStore = create<ConversationState>((set) => ({
  currentConversationId: null,
  setCurrentConversationId: (id) => set({ currentConversationId: id }),
  isLoading: false,
  setIsLoading: (loading) => set({ isLoading: loading }),
  draftMessage: "",
  setDraftMessage: (message) => set({ draftMessage: message }),
  isStreaming: false,
  setIsStreaming: (streaming) => set({ isStreaming: streaming }),
  streamingMessageId: null,
  setStreamingMessageId: (id) => set({ streamingMessageId: id }),
}));

// Notifications Store
interface Notification {
  id: string;
  type: "success" | "error" | "info" | "warning";
  message: string;
  duration?: number;
}

interface NotificationsState {
  notifications: Notification[];
  addNotification: (notification: Omit<Notification, "id">) => void;
  removeNotification: (id: string) => void;
  clearNotifications: () => void;
}

export const useNotificationsStore = create<NotificationsState>((set) => ({
  notifications: [],
  addNotification: (notification) =>
    set((state) => ({
      notifications: [
        ...state.notifications,
        {
          id: Math.random().toString(36).substr(2, 9),
          ...notification,
        },
      ],
    })),
  removeNotification: (id) =>
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    })),
  clearNotifications: () => set({ notifications: [] }),
}));
