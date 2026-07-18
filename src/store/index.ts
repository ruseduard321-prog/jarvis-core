import { create } from "zustand";
import { persist } from "zustand/middleware";

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
  token: string | null;
  userId: string | null;
  setAuth: (token: string, userId: string) => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      userId: null,
      setAuth: (token, userId) => set({ token, userId }),
      clearAuth: () => set({ token: null, userId: null }),
    }),
    {
      name: "auth-storage",
    }
  )
);

// Conversation Store
interface ConversationState {
  currentConversationId: string | null;
  setCurrentConversationId: (id: string | null) => void;
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
}

export const useConversationStore = create<ConversationState>((set) => ({
  currentConversationId: null,
  setCurrentConversationId: (id) => set({ currentConversationId: id }),
  isLoading: false,
  setIsLoading: (loading) => set({ isLoading: loading }),
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
