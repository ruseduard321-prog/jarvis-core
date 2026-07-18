"use client";

import React from "react";
import { useProtectedRoute } from "@/hooks/use-route-protection";
import { AppShell } from "@/components/layout";

interface ProtectedAppLayoutProps {
  children: React.ReactNode;
}

/**
 * Protected App Layout Wrapper
 * Ensures user is authenticated before rendering the app shell
 * Redirects to login if not authenticated
 */
export function ProtectedAppLayout({ children }: ProtectedAppLayoutProps) {
  const { isLoading } = useProtectedRoute();

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

  // Render app shell with children
  return <AppShell>{children}</AppShell>;
}
