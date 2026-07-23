"use client";

import { useState } from "react";
import { Conversation } from "@/types";
import { Edit2, Trash2 } from "lucide-react";
import { useDeleteConversation } from "@/hooks/use-chat-queries";
import { Dialog } from "@/components/ui/dialog";

/**
 * Conversations Row
 * Individual table row with edit and delete actions
 */
interface ConversationsRowProps {
  conversation: Conversation;
  onEdit: (id: string) => void;
}

export function ConversationsRow({
  conversation,
  onEdit,
}: ConversationsRowProps) {
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const deleteConversation = useDeleteConversation();

  const handleDelete = async () => {
    await deleteConversation.mutateAsync(conversation.id);
    setShowDeleteDialog(false);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  return (
    <>
      <tr className="border-b border-gray-200 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-900/50 transition-colors">
        <td className="px-6 py-4 text-sm text-gray-900 dark:text-white font-medium">
          {conversation.title || "Untitled"}
        </td>
        <td className="px-6 py-4 text-sm text-gray-600 dark:text-gray-400">
          {formatDate(conversation.created_at)}
        </td>
        <td className="px-6 py-4 text-sm text-gray-600 dark:text-gray-400">
          {formatDate(conversation.updated_at)}
        </td>
        <td className="px-6 py-4 text-right">
          <div className="flex items-center justify-end gap-2">
            <button
              onClick={() => onEdit(conversation.id)}
              className="inline-flex items-center gap-1 px-3 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-800 rounded-lg transition-colors"
              title="Edit conversation"
            >
              <Edit2 className="h-4 w-4" />
            </button>
            <button
              onClick={() => setShowDeleteDialog(true)}
              className="inline-flex items-center gap-1 px-3 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
              title="Delete conversation"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          </div>
        </td>
      </tr>

      {/* Delete Confirmation Dialog */}
      <Dialog
        isOpen={showDeleteDialog}
        onClose={() => setShowDeleteDialog(false)}
        title="Delete Conversation"
        description="Are you sure you want to delete this conversation? This action cannot be undone."
        footer={
          <div className="flex gap-2">
            <button
              onClick={() => setShowDeleteDialog(false)}
              className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-200 dark:bg-gray-800 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-700 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleDelete}
              disabled={deleteConversation.isPending}
              className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 disabled:opacity-50 dark:bg-red-700 dark:hover:bg-red-800 transition-colors"
            >
              {deleteConversation.isPending ? "Deleting..." : "Delete"}
            </button>
          </div>
        }
      />
    </>
  );
}
