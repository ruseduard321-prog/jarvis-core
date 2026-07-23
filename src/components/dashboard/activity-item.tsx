"use client";

import { ActivityEvent } from "@/types";
import { MessageSquare, Plus, Zap, BookOpen } from "lucide-react";
import { formatRelativeTime } from "@/utils/date";

interface ActivityItemProps {
  event: ActivityEvent;
}

/**
 * Activity Item
 * Displays a single activity event
 */
export function ActivityItem({ event }: ActivityItemProps) {
  const getIcon = () => {
    switch (event.type) {
      case "conversation_created":
        return <Plus className="w-4 h-4 text-blue-600" />;
      case "message_sent":
        return <MessageSquare className="w-4 h-4 text-green-600" />;
      case "document_uploaded":
        return <BookOpen className="w-4 h-4 text-purple-600" />;
      case "agent_executed":
        return <Zap className="w-4 h-4 text-orange-600" />;
      default:
        return <MessageSquare className="w-4 h-4 text-gray-600" />;
    }
  };

  return (
    <div className="flex items-start gap-3 p-2 rounded hover:bg-gray-50 dark:hover:bg-gray-800">
      <div className="mt-1 p-2 bg-gray-100 dark:bg-gray-800 rounded">
        {getIcon()}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm text-gray-700 dark:text-gray-300 line-clamp-2">{event.description}</p>
        <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">{formatRelativeTime(event.timestamp)}</p>
      </div>
    </div>
  );
}
