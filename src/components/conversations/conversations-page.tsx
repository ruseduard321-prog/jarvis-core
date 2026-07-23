"use client";

import { useConversations } from "@/hooks/use-chat-queries";
import { Loader2, AlertCircle } from "lucide-react";
import { ConversationsLayout } from "./conversations-layout";

/**
 * Conversations Page
 * Orchestrator component that fetches conversations and handles loading/error states
 */
export function ConversationsPage() {
  const { data: conversations, isLoading, error } = useConversations();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen px-6">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-red-600 dark:text-red-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            Failed to load conversations
          </h3>
          <p className="text-gray-600 dark:text-gray-400">
            {error instanceof Error ? error.message : "An error occurred"}
          </p>
        </div>
      </div>
    );
  }

  return <ConversationsLayout conversations={conversations || []} />;
}
