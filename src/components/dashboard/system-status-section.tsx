"use client";

import { SystemStatus } from "@/types";
import { StatusIndicator } from "./status-indicator";

interface SystemStatusSectionProps {
  status: SystemStatus;
}

/**
 * System Status Section
 * Displays health status of all system components
 */
export function SystemStatusSection({ status }: SystemStatusSectionProps) {
  return (
    <div className="bg-white dark:bg-gray-900 rounded-lg p-6 border border-gray-200 dark:border-gray-800">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">System Status</h2>
        <div className={`px-3 py-1 rounded-full text-sm font-medium ${
          status.status === "healthy" ? "bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-100" :
          status.status === "degraded" ? "bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-100" :
          "bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-100"
        }`}>
          {status.status.charAt(0).toUpperCase() + status.status.slice(1)}
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatusIndicator indicator={status.backend} />
        <StatusIndicator indicator={status.database} />
        <StatusIndicator indicator={status.ai_provider} />
      </div>
    </div>
  );
}
