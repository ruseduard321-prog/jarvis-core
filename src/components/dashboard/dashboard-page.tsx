"use client";

import { useDashboard } from "@/hooks/use-dashboard";
import { DashboardLayout } from "./dashboard-layout";
import { Skeleton } from "@/components/ui/skeleton";

/**
 * Dashboard Page
 * Main dashboard component that orchestrates all sections
 */
export function DashboardPage() {
  const { data: dashboard, isLoading, error } = useDashboard();

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-red-600 mb-2">Error</h2>
          <p className="text-gray-600">{(error as Error).message || "Failed to load dashboard"}</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (isLoading || !dashboard) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => (
            <Skeleton key={i} className="h-24 rounded-lg" />
          ))}
        </div>
        <Skeleton className="h-64 rounded-lg" />
      </div>
    );
  }

  return <DashboardLayout dashboard={dashboard} />;
}
