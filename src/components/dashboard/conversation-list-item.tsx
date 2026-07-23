"use client";

import { ConversationSummary } from "@/types";
import { useRouter } from "next/navigation";
import { MessageCircle, Clock, MessageSquare } from "lucide-react";
import { formatRelativeTime } from "@/utils/date";

interface ConversationListItemProps {
  conversation: ConversationSummary;
}

/**
 * Conversation List Item
 * Displays a single conversation in the list
 */
export function ConversationListItem({ conversation }: ConversationListItemProps) {
  const router = useRouter();

  const handleClick = () => {
    router.push(`/chat/${conversation.id}`);
  };

  return (
    <button
      onClick={handleClick}
      className="w-full text-left p-4 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors border border-transparent hover:border-gray-200 dark:hover:border-gray-700"
    >
      <div className="flex items-start gap-3">
        <div className="mt-1">
          <MessageCircle className="w-5 h-5 text-blue-600 dark:text-blue-400" />
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-gray-900 dark:text-white truncate">{conversation.title}</h3>
          <div className="flex items-center gap-4 mt-1 text-sm text-gray-600 dark:text-gray-400">
            <div className="flex items-center gap-1">
              <MessageSquare className="w-4 h-4" />
              <span>{conversation.message_count} messages</span>
            </div>
            <div className="flex items-center gap-1">
              <Clock className="w-4 h-4" />
              <span>{formatRelativeTime(conversation.last_message_at)}</span>
            </div>
          </div>
        </div>
      </div>
    </button>
  );
}
