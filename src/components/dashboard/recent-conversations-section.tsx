"use client";

import { ConversationSummary } from "@/types";
import { ConversationListItem } from "./conversation-list-item";

interface RecentConversationsSectionProps {
  conversations: ConversationSummary[];
}

/**
 * Recent Conversations Section
 * Displays list of recent conversations
 */
export function RecentConversationsSection({ conversations }: RecentConversationsSectionProps) {
  return (
    <div className="bg-white dark:bg-gray-900 rounded-lg p-6 border border-gray-200 dark:border-gray-800">
      <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Recent Conversations</h2>
      {conversations.length > 0 ? (
        <div className="space-y-2">
          {conversations.map((conversation) => (
            <ConversationListItem key={conversation.id} conversation={conversation} />
          ))}
        </div>
      ) : (
        <p className="text-gray-600 dark:text-gray-400 text-center py-8">No conversations yet. Start a new chat!</p>
      )}
    </div>
  );
}
