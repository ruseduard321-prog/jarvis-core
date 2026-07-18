/**
 * Route Protection Utilities
 * 
 * Provides mechanisms for protecting routes based on authentication state
 */

import { useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/providers/auth-provider";

/**
 * Hook to protect a route - redirects to login if not authenticated
 */
export function useProtectedRoute() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isAuthenticated, isLoading, status } = useAuth();

  useEffect(() => {
    if (isLoading) return; // Still loading auth state

    if (status === "unauthenticated") {
      // Not authenticated, redirect to login with return URL
      const currentUrl = typeof window !== "undefined" ? window.location.pathname : "/";
      router.push(`/login?redirect=${encodeURIComponent(currentUrl)}`);
    }
  }, [status, isLoading, router, searchParams]);

  return { isLoading, canAccess: isAuthenticated };
}

/**
 * Hook to ensure route is guest-only (redirects to dashboard if authenticated)
 */
export function useGuestRoute() {
  const router = useRouter();
  const { isAuthenticated, isLoading, status } = useAuth();

  useEffect(() => {
    if (isLoading) return; // Still loading auth state

    if (status === "authenticated") {
      // Already authenticated, redirect to dashboard
      router.push("/dashboard");
    }
  }, [status, isLoading, router]);

  return { isLoading, canAccess: !isAuthenticated };
}
