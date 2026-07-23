"use client";

import React, { useMemo } from "react";
import { Plus, Search, Trash2, Pencil } from "lucide-react";
import { cn } from "@/utils";
import { useConversations, useDeleteConversation, useUpdateConversation } from "@/hooks/use-chat-queries";
import type { Conversation } from "@/types";

interface ConversationSidebarProps {
  currentConversationId: string | null;
  onSelectConversation: (id: string) => void;
  onNewConversation: () => void;
  className?: string;
}

/**
 * Conversation Sidebar Component
 * Features:
 * - List of all conversations
 * - Search/filter
 * - Create new conversation
 * - Delete conversation
 * - Rename conversation
 * - Current conversation highlighting
 */
export function ConversationSidebar({
  currentConversationId,
  onSelectConversation,
  onNewConversation,
  className,
}: ConversationSidebarProps) {
  const { data: conversations = [], isLoading } = useConversations();
  const [searchQuery, setSearchQuery] = React.useState("");
  const [editingId, setEditingId] = React.useState<string | null>(null);
  const [editingTitle, setEditingTitle] = React.useState("");

  // Filter conversations by search
  const filteredConversations = useMemo(() => {
    if (!searchQuery.trim()) return conversations;
    const query = searchQuery.toLowerCase();
    return conversations.filter((conv: Conversation) => (conv.title || "Untitled").toLowerCase().includes(query));
  }, [conversations, searchQuery]);

  // Sort by recent first
  const sortedConversations = useMemo(
    () => [...filteredConversations].sort((a: Conversation, b: Conversation) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()),
    [filteredConversations]
  );

  return (
    <div className={cn("flex flex-col h-full bg-muted/30 border-r border-border", className)}>
      {/* Header with New Button */}
      <div className="border-b border-border p-4 space-y-3">
        <button
          onClick={onNewConversation}
          className="w-full flex items-center gap-2 px-3 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
        >
          <Plus className="h-4 w-4" />
          <span className="text-sm font-medium">New Chat</span>
        </button>
      </div>

      {/* Search */}
      <div className="px-4 py-3 border-b border-border">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search conversations..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-2 text-sm rounded-md bg-background border border-border text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary/50"
            aria-label="Search conversations"
          />
        </div>
      </div>

      {/* Conversation List */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="flex items-center justify-center h-20">
            <div className="text-xs text-muted-foreground">Loading...</div>
          </div>
        ) : sortedConversations.length === 0 ? (
          <div className="p-4 text-center">
            <p className="text-xs text-muted-foreground">{searchQuery ? "No conversations found" : "No conversations yet"}</p>
          </div>
        ) : (
          <ul className="space-y-1 p-2">
            {sortedConversations.map((conversation) => (
              <ConversationItem
                key={conversation.id}
                conversation={conversation}
                isSelected={currentConversationId === conversation.id}
                isEditing={editingId === conversation.id}
                editingTitle={editingTitle}
                onSelect={() => onSelectConversation(conversation.id)}
                onEditStart={(title) => {
                  setEditingId(conversation.id);
                  setEditingTitle(title);
                }}
                onEditEnd={() => setEditingId(null)}
                onEditChange={setEditingTitle}
              />
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

/**
 * Individual Conversation Item
 */
interface ConversationItemProps {
  conversation: Conversation;
  isSelected: boolean;
  isEditing: boolean;
  editingTitle: string;
  onSelect: () => void;
  onEditStart: (title: string) => void;
  onEditEnd: () => void;
  onEditChange: (title: string) => void;
}

function ConversationItem({
  conversation,
  isSelected,
  isEditing,
  editingTitle,
  onSelect,
  onEditStart,
  onEditEnd,
  onEditChange,
}: ConversationItemProps) {
  const updateMutation = useUpdateConversation(conversation.id);
  const deleteMutation = useDeleteConversation();
  const [showActions, setShowActions] = React.useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = React.useState(false);

  const handleSaveEdit = async () => {
    if (editingTitle.trim()) {
      await updateMutation.mutateAsync({ title: editingTitle });
    }
    onEditEnd();
  };

  const handleDelete = async () => {
    await deleteMutation.mutateAsync(conversation.id);
    setShowDeleteConfirm(false);
  };

  const displayTitle = conversation.title || "Untitled";
  const shortTitle = displayTitle.length > 30 ? displayTitle.substring(0, 27) + "..." : displayTitle;

  if (isEditing) {
    return (
      <li className="px-2">
        <input
          type="text"
          autoFocus
          value={editingTitle}
          onChange={(e) => onEditChange(e.target.value)}
          onBlur={handleSaveEdit}
          onKeyDown={(e) => {
            if (e.key === "Enter") handleSaveEdit();
            if (e.key === "Escape") onEditEnd();
          }}
          className="w-full px-3 py-2 text-sm rounded-md bg-background border border-primary text-foreground focus:outline-none"
          placeholder="Conversation title..."
        />
      </li>
    );
  }

  return (
    <li
      className={cn(
        "relative group rounded-lg px-3 py-2 text-sm text-left cursor-pointer transition-colors",
        isSelected ? "bg-primary/10 text-primary font-medium" : "text-muted-foreground hover:bg-muted hover:text-foreground"
      )}
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => setShowActions(false)}
    >
      <button onClick={onSelect} className="w-full text-left truncate" title={displayTitle}>
        {shortTitle}
      </button>

      {/* Actions */}
      {showActions && (
        <div className="absolute right-2 top-1/2 -translate-y-1/2 flex gap-1">
          {/* Edit Button */}
          <button
            onClick={() => onEditStart(conversation.title || "")}
            className="p-1 rounded hover:bg-muted/50 transition-colors"
            title="Rename"
            aria-label="Rename conversation"
          >
            <Pencil className="h-3 w-3 text-muted-foreground hover:text-foreground" />
          </button>

          {/* Delete Button */}
          <button
            onClick={() => setShowDeleteConfirm(true)}
            className="p-1 rounded hover:bg-muted/50 transition-colors"
            title="Delete"
            aria-label="Delete conversation"
          >
            <Trash2 className="h-3 w-3 text-muted-foreground hover:text-destructive" />
          </button>
        </div>
      )}

      {/* Delete Confirmation */}
      {showDeleteConfirm && (
        <div className="absolute inset-0 bg-destructive/10 border border-destructive/30 rounded-lg flex items-center justify-center gap-1 text-xs">
          <button
            onClick={() => handleDelete()}
            disabled={deleteMutation.isPending}
            className="px-2 py-1 rounded bg-destructive text-destructive-foreground hover:bg-destructive/90 text-xs"
          >
            {deleteMutation.isPending ? "..." : "Delete"}
          </button>
          <button
            onClick={() => setShowDeleteConfirm(false)}
            className="px-2 py-1 rounded border border-destructive/50 hover:bg-muted text-xs"
          >
            Cancel
          </button>
        </div>
      )}
    </li>
  );
}
