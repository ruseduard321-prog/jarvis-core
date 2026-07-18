"use client";

import { useGuestRoute } from "@/hooks/use-route-protection";
import { LoginForm } from "@/components/auth/login-form";
import { LogIn } from "lucide-react";

/**
 * Guest-only Login Page Wrapper
 * Ensures user is NOT authenticated before showing login form
 * Redirects to dashboard if already authenticated
 */
export function GuestLoginPage() {
  const { isLoading } = useGuestRoute();

  // Show loading state while checking authentication
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto" />
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-b from-background to-muted/20">
      <div className="w-full max-w-md space-y-8">
        {/* Header */}
        <div className="text-center space-y-3">
          <div className="flex items-center justify-center gap-2">
            <LogIn className="h-8 w-8 text-primary" />
            <h1 className="text-3xl font-bold">Jarvis</h1>
          </div>
          <p className="text-muted-foreground">
            Sign in to your account to continue
          </p>
        </div>

        {/* Login Form */}
        <div className="bg-card rounded-lg border border-border p-6 shadow-sm">
          <LoginForm />
        </div>

        {/* Footer */}
        <p className="text-center text-xs text-muted-foreground">
          By signing in, you agree to our{" "}
          <a href="/terms" className="hover:underline">
            Terms of Service
          </a>{" "}
          and{" "}
          <a href="/privacy" className="hover:underline">
            Privacy Policy
          </a>
        </p>
      </div>
    </div>
  );
}
