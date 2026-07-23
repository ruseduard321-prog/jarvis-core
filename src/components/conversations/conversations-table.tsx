"use client";

import { Conversation } from "@/types";
import { MessageCircle } from "lucide-react";
import { ConversationsRow } from "./conversations-row";

/**
 * Conversations Table
 * Displays conversations in a table with inline empty state
 */
interface ConversationsTableProps {
  conversations: Conversation[];
  onEdit: (id: string) => void;
}

export function ConversationsTable({
  conversations,
  onEdit,
}: ConversationsTableProps) {
  // Empty state
  if (conversations.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center px-6">
        <div className="text-center">
          <MessageCircle className="h-12 w-12 text-gray-400 dark:text-gray-600 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            No conversations yet
          </h3>
          <p className="text-gray-600 dark:text-gray-400">
            Create one to get started
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-auto">
      <table className="w-full border-collapse">
        <thead className="sticky top-0 bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800">
          <tr>
            <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900 dark:text-white">
              Title
            </th>
            <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900 dark:text-white">
              Created
            </th>
            <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900 dark:text-white">
              Updated
            </th>
            <th className="px-6 py-3 text-right text-sm font-semibold text-gray-900 dark:text-white">
              Actions
            </th>
          </tr>
        </thead>
        <tbody>
          {conversations.map((conversation) => (
            <ConversationsRow
              key={conversation.id}
              conversation={conversation}
              onEdit={onEdit}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
}
