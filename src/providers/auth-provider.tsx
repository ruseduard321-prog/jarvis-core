"use client";

import React, { createContext, useContext, useEffect, useCallback } from "react";
import { useAuthStore } from "@/store";
import { authService } from "@/services/auth-service";
import type { AuthContextValue } from "@/types";

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

/**
 * Auth Context Provider
 * Manages authentication state and session lifecycle
 */
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const store = useAuthStore();

  // Initialize session from persisted storage
  useEffect(() => {
    const initializeAuth = async () => {
      store.setLoading(true);

      // Check if we have a valid session in storage
      if (store.accessToken && store.expiresAt) {
        // Check if token is expired
        if (!store.isTokenExpired()) {
          // Token is still valid, try to fetch user
          const response = await authService.getCurrentUser();
          if (response.status === 200 && response.data) {
            store.setUser(response.data);
          } else {
            // User fetch failed, clear auth
            store.clearAuth();
          }
        } else {
          // Token is expired, try to refresh
          if (store.refreshToken) {
            const response = await authService.refreshToken(store.refreshToken);
            if (response.status === 200 && response.data) {
              store.setAuth(response.data, store.user || { id: "", email: "" });
            } else {
              // Refresh failed, clear auth
              store.clearAuth();
            }
          } else {
            // No refresh token, clear auth
            store.clearAuth();
          }
        }
      }

      store.setLoading(false);
    };

    initializeAuth();
  }, [store]);

  // Login
  const login = useCallback(
    async (email: string, password: string) => {
      store.setLoading(true);
      store.setError(null);

      try {
        // Sign in with credentials
        const signInResponse = await authService.signIn(email, password);

        if (signInResponse.status !== 200 || !signInResponse.data) {
          throw new Error(signInResponse.error || "Failed to sign in");
        }

        const session = signInResponse.data;

        // Fetch current user
        const userResponse = await authService.getCurrentUser();

        if (userResponse.status !== 200 || !userResponse.data) {
          throw new Error(userResponse.error || "Failed to fetch user");
        }

        const user = userResponse.data;

        // Store session and user
        store.setAuth(session, user);
        store.setLoading(false);
      } catch (error) {
        const message = error instanceof Error ? error.message : "Sign in failed";
        store.setError(message);
        store.setLoading(false);
        throw error;
      }
    },
    [store]
  );

  // Logout
  const logout = useCallback(async () => {
    store.setLoading(true);

    try {
      // Try to sign out on backend
      if (store.refreshToken) {
        await authService.signOut(store.refreshToken);
      }
    } catch (_error) {
      // Ignore errors on sign-out
    } finally {
      // Clear local auth state
      store.clearAuth();
      store.setLoading(false);
    }
  }, [store]);

  // Restore session (manual trigger)
  const restoreSession = useCallback(async () => {
    store.setLoading(true);

    try {
      const response = await authService.getCurrentUser();

      if (response.status === 200 && response.data) {
        store.setUser(response.data);
      } else {
        store.clearAuth();
      }
    } catch (_error) {
      store.clearAuth();
    } finally {
      store.setLoading(false);
    }
  }, [store]);

  const value: AuthContextValue = {
    user: store.user,
    status: store.isLoading ? "loading" : store.isAuthenticated ? "authenticated" : "unauthenticated",
    isAuthenticated: store.isAuthenticated,
    isLoading: store.isLoading,
    error: store.error,
    login,
    logout,
    restoreSession,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

/**
 * Hook to use auth context
 */
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
