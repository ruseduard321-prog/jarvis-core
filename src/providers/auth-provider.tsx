"use client";

import React, { createContext, useContext, useEffect, useCallback, useRef } from "react";
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
  // Use a ref so the one-time init effect can read current store state
  // without taking the entire store as a reactive dependency.
  const storeRef = useRef(store);
  useEffect(() => {
    storeRef.current = store;
  });

  // Initialize session from persisted storage — runs ONCE on mount.
  // Reading from storeRef.current (stable) avoids the infinite-loop caused
  // by store being a new reference after every setState call.
  useEffect(() => {
    const initializeAuth = async () => {
      const s = storeRef.current;
      s.setLoading(true);

      // Check if we have a valid session in storage
      if (s.accessToken && s.expiresAt) {
        // Check if token is expired
        if (!s.isTokenExpired()) {
          // Token is still valid, try to fetch user
          const response = await authService.getCurrentUser();
          if (response.status === 200 && response.data) {
            s.setUser(response.data);
          } else {
            // User fetch failed, clear auth
            s.clearAuth();
          }
        } else {
          // Token is expired, try to refresh
          if (s.refreshToken) {
            const response = await authService.refreshToken(s.refreshToken);
            if (response.status === 200 && response.data) {
              s.setAuth(response.data, s.user || { id: "", email: "" });
            } else {
              // Refresh failed, clear auth
              s.clearAuth();
            }
          } else {
            // No refresh token, clear auth
            s.clearAuth();
          }
        }
      }

      s.setLoading(false);
    };

    initializeAuth();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // intentionally empty — run once on mount

  // Login
  const login = useCallback(
    async (email: string, password: string) => {
      const s = storeRef.current;
      s.setLoading(true);
      s.setError(null);

      try {
        // Sign in with credentials
        const signInResponse = await authService.signIn(email, password);

        if (signInResponse.status !== 200 || !signInResponse.data) {
          throw new Error(signInResponse.error || "Failed to sign in");
        }

        const session = signInResponse.data;

        // CRITICAL: Store tokens immediately so they're available for subsequent requests
        s.setTokens(session.access_token, session.refresh_token, session.expires_at);

        // Now fetch current user (this request will have the Authorization header with the token)
        const userResponse = await authService.getCurrentUser();

        if (userResponse.status !== 200 || !userResponse.data) {
          throw new Error(userResponse.error || "Failed to fetch user");
        }

        const user = userResponse.data;

        // Store full session with user data
        s.setAuth(session, user);
        s.setLoading(false);
      } catch (error) {
        const message = error instanceof Error ? error.message : "Sign in failed";
        storeRef.current.setError(message);
        storeRef.current.setLoading(false);
        throw error;
      }
    },
    []
  );

  // Logout
  const logout = useCallback(async () => {
    const s = storeRef.current;
    s.setLoading(true);

    try {
      // Try to sign out on backend
      if (s.refreshToken) {
        await authService.signOut(s.refreshToken);
      }
    } catch (_error) {
      // Ignore errors on sign-out
    } finally {
      // Clear local auth state
      s.clearAuth();
      s.setLoading(false);
    }
  }, []);

  // Restore session (manual trigger)
  const restoreSession = useCallback(async () => {
    const s = storeRef.current;
    s.setLoading(true);

    try {
      const response = await authService.getCurrentUser();

      if (response.status === 200 && response.data) {
        s.setUser(response.data);
      } else {
        s.clearAuth();
      }
    } catch (_error) {
      s.clearAuth();
    } finally {
      s.setLoading(false);
    }
  }, []);

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
