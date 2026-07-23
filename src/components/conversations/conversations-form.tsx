"use client";

import { useState } from "react";
import { Conversation } from "@/types";
import {
  useCreateConversation,
  useUpdateConversation,
} from "@/hooks/use-chat-queries";
import { Dialog } from "@/components/ui/dialog";

/**
 * Conversations Form
 * Modal form for creating or renaming conversations
 */
interface ConversationsFormProps {
  conversation?: Conversation | null;
  onClose: () => void;
}

export function ConversationsForm({
  conversation,
  onClose,
}: ConversationsFormProps) {
  const [title, setTitle] = useState(conversation?.title || "");
  const createConversation = useCreateConversation();
  const updateConversation = useUpdateConversation(conversation?.id || "");

  const isEdit = !!conversation;
  const isPending = isEdit
    ? updateConversation.isPending
    : createConversation.isPending;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!title.trim()) {
      return;
    }

    if (isEdit) {
      await updateConversation.mutateAsync({
        title: title.trim(),
      });
    } else {
      await createConversation.mutateAsync({
        title: title.trim(),
      });
    }

    onClose();
  };

  return (
    <Dialog
      isOpen={true}
      onClose={onClose}
      title={isEdit ? "Rename Conversation" : "New Conversation"}
      description={isEdit ? "Update the conversation title" : "Create a new conversation"}
      footer={
        <div className="flex gap-2">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-200 dark:bg-gray-800 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-700 transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={!title.trim() || isPending}
            onClick={handleSubmit}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 dark:bg-blue-700 dark:hover:bg-blue-800 transition-colors"
          >
            {isPending ? "Saving..." : isEdit ? "Rename" : "Create"}
          </button>
        </div>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-900 dark:text-white mb-2">
            Title
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Enter conversation title"
            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            autoFocus
          />
        </div>
      </form>
    </Dialog>
  );
}
