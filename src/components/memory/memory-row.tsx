"use client";

import { useState } from "react";
import { Memory } from "@/types";
import { useMemoryDelete } from "@/hooks/use-memory";
import { memoryService } from "@/services/memory-service";
import { Dialog } from "@/components/ui/dialog";
import { MemoryForm } from "./memory-form";
import { Edit, Trash2 } from "lucide-react";

interface MemoryRowProps {
  memory: Memory;
}

export function MemoryRow({ memory }: MemoryRowProps) {
  const [showEditForm, setShowEditForm] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const deleteMutation = useMemoryDelete(memory.id);

  const handleDelete = async () => {
    try {
      await deleteMutation.mutateAsync();
      setShowDeleteConfirm(false);
    } catch (error) {
      console.error("Delete failed:", error);
    }
  };

  const preview = memoryService.getPreview(memory.content, 60);
  const importance =
    (memory.attributes?.importance as string) || "medium";
  const created = new Date(memory.created_at).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "2-digit",
  });

  return (
    <>
      <tr className="hover:bg-muted/50 transition-colors">
        {/* Content Preview */}
        <td className="px-6 py-4">
          <div className="flex flex-col gap-1">
            <p className="text-sm font-medium break-words">{preview}</p>
            {memory.tags && memory.tags.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {memory.tags.slice(0, 2).map((tag) => (
                  <span
                    key={tag}
                    className="inline-block px-2 py-0.5 text-xs bg-primary/10 text-primary rounded"
                  >
                    {tag}
                  </span>
                ))}
                {memory.tags.length > 2 && (
                  <span className="text-xs text-muted-foreground">
                    +{memory.tags.length - 2}
                  </span>
                )}
              </div>
            )}
          </div>
        </td>

        {/* Category */}
        <td className="px-6 py-4">
          <span className="inline-block px-2 py-1 text-xs font-medium bg-muted text-muted-foreground rounded">
            {memory.record_type}
          </span>
        </td>

        {/* Importance */}
        <td className="px-6 py-4">
          <span
            className={`inline-block px-2 py-1 text-xs font-medium rounded ${
              importance === "high"
                ? "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400"
                : importance === "medium"
                  ? "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400"
                  : "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
            }`}
          >
            {importance.charAt(0).toUpperCase() + importance.slice(1)}
          </span>
        </td>

        {/* Source */}
        <td className="px-6 py-4">
          <p className="text-sm text-muted-foreground truncate">
            {memory.source || "—"}
          </p>
        </td>

        {/* Created Date */}
        <td className="px-6 py-4">
          <p className="text-sm text-muted-foreground">{created}</p>
        </td>

        {/* Actions */}
        <td className="px-6 py-4">
          <div className="flex items-center justify-end gap-2">
            <button
              onClick={() => setShowEditForm(true)}
              className="p-1.5 hover:bg-muted rounded transition-colors"
              title="Edit memory"
            >
              <Edit className="h-4 w-4 text-muted-foreground" />
            </button>
            <button
              onClick={() => setShowDeleteConfirm(true)}
              className="p-1.5 hover:bg-red-100 dark:hover:bg-red-900/20 rounded transition-colors"
              title="Delete memory"
            >
              <Trash2 className="h-4 w-4 text-red-600 dark:text-red-400" />
            </button>
          </div>
        </td>
      </tr>

      {/* Edit Form Modal */}
      <MemoryForm
        mode="edit"
        initialData={memory}
        isOpen={showEditForm}
        onClose={() => setShowEditForm(false)}
      />

      {/* Delete Confirmation Modal */}
      <Dialog
        isOpen={showDeleteConfirm}
        onClose={() => setShowDeleteConfirm(false)}
        title="Delete Memory?"
        description="This action cannot be undone. The memory will be permanently deleted."
        size="sm"
        footer={
          <div className="flex gap-2 justify-end">
            <button
              onClick={() => setShowDeleteConfirm(false)}
              disabled={deleteMutation.isPending}
              className="px-3 py-1.5 text-sm font-medium text-foreground hover:bg-muted rounded disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleDelete}
              disabled={deleteMutation.isPending}
              className="px-3 py-1.5 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded disabled:opacity-50 disabled:cursor-not-allowed transition-colors dark:bg-red-700 dark:hover:bg-red-800"
            >
              {deleteMutation.isPending ? "Deleting..." : "Delete"}
            </button>
          </div>
        }
      />
    </>
  );
}
