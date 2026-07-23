"use client";

import { QuickAction } from "@/types";
import { ActionCard } from "./action-card";

interface QuickActionsSectionProps {
  actions: QuickAction[];
}

/**
 * Quick Actions Section
 * Displays quick action cards for common operations
 */
export function QuickActionsSection({ actions }: QuickActionsSectionProps) {
  return (
    <div className="bg-white dark:bg-gray-900 rounded-lg p-6 border border-gray-200 dark:border-gray-800">
      <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Quick Actions</h2>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {actions.map((action) => (
          <ActionCard key={action.id} action={action} />
        ))}
      </div>
    </div>
  );
}
