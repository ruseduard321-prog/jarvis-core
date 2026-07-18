import React from "react";

/**
 * Auth Layout
 * Wraps authentication pages (login, sign-up, etc.)
 * Does NOT include the AppShell - these are public-only routes
 */
export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
