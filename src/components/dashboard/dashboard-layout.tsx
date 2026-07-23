"use client";

import { DashboardResponse } from "@/types";
import { StatisticsSection } from "./statistics-section";
import { QuickActionsSection } from "./quick-actions-section";
import { RecentConversationsSection } from "./recent-conversations-section";
import { ActivitySection } from "./activity-section";
import { SystemStatusSection } from "./system-status-section";

interface DashboardLayoutProps {
  dashboard: DashboardResponse;
}

/**
 * Dashboard Layout
 * Responsive grid layout for dashboard sections
 */
export function DashboardLayout({ dashboard }: DashboardLayoutProps) {
  return (
    <div className="space-y-6 pb-6">
      {/* Welcome Section */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1">Welcome to Jarvis. Your AI-powered workspace.</p>
      </div>

      {/* Statistics Grid */}
      <StatisticsSection statistics={dashboard.statistics} />

      {/* Quick Actions */}
      <QuickActionsSection actions={dashboard.quick_actions} />

      {/* Recent Conversations & Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <RecentConversationsSection conversations={dashboard.recent_conversations} />
        </div>
        <div>
          <ActivitySection activity={dashboard.activity} />
        </div>
      </div>

      {/* System Status */}
      <SystemStatusSection status={dashboard.system_status} />
    </div>
  );
}
