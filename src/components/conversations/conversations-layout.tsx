"use client";

import { useState, useMemo } from "react";
import { Conversation } from "@/types";
import { Plus } from "lucide-react";
import { ConversationsToolbar } from "./conversations-toolbar";
import { ConversationsTable } from "./conversations-table";
import { ConversationsForm } from "./conversations-form";

/**
 * Conversations Layout
 * Main layout component with state management and search/filter helpers
 */
interface ConversationsLayoutProps {
  conversations: Conversation[];
}

export function ConversationsLayout({ conversations }: ConversationsLayoutProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);

  // Search conversations by title only (no N+1 requests for last message)
  const filteredConversations = useMemo(() => {
    if (!searchQuery.trim()) return conversations;
    const lowerQuery = searchQuery.toLowerCase();
    return conversations.filter((conv) =>
      (conv.title || "").toLowerCase().includes(lowerQuery)
    );
  }, [conversations, searchQuery]);

  const handleOpenCreate = () => {
    setEditingId(null);
    setShowCreateForm(true);
  };

  const handleOpenEdit = (id: string) => {
    setEditingId(id);
    setShowCreateForm(true);
  };

  const handleCloseForm = () => {
    setShowCreateForm(false);
    setEditingId(null);
  };

  const editingConversation = editingId
    ? conversations.find((c) => c.id === editingId)
    : null;

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="border-b border-gray-200 dark:border-gray-800 px-6 py-4">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Conversations
          </h1>
          <button
            onClick={handleOpenCreate}
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 dark:bg-blue-700 dark:hover:bg-blue-800 font-medium transition-colors"
          >
            <Plus className="h-4 w-4" />
            New Conversation
          </button>
        </div>
      </div>

      {/* Toolbar */}
      <ConversationsToolbar
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
      />

      {/* Table */}
      <ConversationsTable
        conversations={filteredConversations}
        onEdit={handleOpenEdit}
      />

      {/* Create/Edit Form Modal */}
      {showCreateForm && (
        <ConversationsForm
          conversation={editingConversation}
          onClose={handleCloseForm}
        />
      )}
    </div>
  );
}
