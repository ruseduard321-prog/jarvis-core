"use client";

import { DashboardStatistics } from "@/types";
import { StatCard } from "./stat-card";
import { MessageCircle, MessageSquare, BookOpen, Zap, FileText, TrendingUp } from "lucide-react";

interface StatisticsSectionProps {
  statistics: DashboardStatistics;
}

/**
 * Statistics Section
 * Displays key metrics in card format
 */
export function StatisticsSection({ statistics }: StatisticsSectionProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4">
      <StatCard
        icon={MessageCircle}
        label="Conversations"
        value={statistics.total_conversations}
        trend="neutral"
      />
      <StatCard
        icon={MessageSquare}
        label="Messages"
        value={statistics.total_messages}
        trend="up"
      />
      <StatCard
        icon={BookOpen}
        label="Knowledge Items"
        value={statistics.total_knowledge_items}
        trend="up"
      />
      <StatCard
        icon={Zap}
        label="Agents"
        value={statistics.total_agents}
        trend="neutral"
      />
      <StatCard
        icon={FileText}
        label="Documents"
        value={statistics.total_documents}
        trend="neutral"
      />
      <StatCard
        icon={TrendingUp}
        label="Today's Activity"
        value={statistics.today_activity}
        trend="up"
      />
    </div>
  );
}
