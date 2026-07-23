"use client";

import { ActivityEvent } from "@/types";
import { ActivityItem } from "./activity-item";

interface ActivitySectionProps {
  activity: ActivityEvent[];
}

/**
 * Activity Section
 * Displays recent activity feed
 */
export function ActivitySection({ activity }: ActivitySectionProps) {
  return (
    <div className="bg-white dark:bg-gray-900 rounded-lg p-6 border border-gray-200 dark:border-gray-800">
      <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Recent Activity</h2>
      {activity.length > 0 ? (
        <div className="space-y-3">
          {activity.map((event) => (
            <ActivityItem key={event.id} event={event} />
          ))}
        </div>
      ) : (
        <p className="text-gray-600 dark:text-gray-400 text-center py-8">No recent activity</p>
      )}
    </div>
  );
}
