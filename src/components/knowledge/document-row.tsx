"use client";

import { useState } from "react";
import { Trash2, AlertCircle, FileText, FileCode, Book } from "lucide-react";
import type { Document } from "@/types";
import { useKnowledgeDelete } from "@/hooks/use-knowledge";
import { formatRelativeTime } from "@/utils/date";

interface DocumentRowProps {
  document: Document;
}

/**
 * Document Row
 * Single row in the document table with inline status badge and type icon
 */
export function DocumentRow({ document }: DocumentRowProps) {
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const deleteMutation = useKnowledgeDelete();

  const handleDelete = async () => {
    try {
      await deleteMutation.mutateAsync(document.id);
      setShowDeleteConfirm(false);
    } catch (error) {
      console.error("Delete failed:", error);
    }
  };

  // Get document type icon
  const getTypeIcon = () => {
    const type = document.source_type?.toLowerCase() || "unknown";
    if (type.includes("pdf")) {
      return <FileText className="h-4 w-4 text-red-500" />;
    }
    if (type.includes("code") || type.includes("markdown")) {
      return <FileCode className="h-4 w-4 text-blue-500" />;
    }
    if (type.includes("document") || type.includes("docx")) {
      return <Book className="h-4 w-4 text-purple-500" />;
    }
    return <FileText className="h-4 w-4 text-gray-400" />;
  };

  // Format date
  const uploadedDate = formatRelativeTime(document.created_at);

  return (
    <>
      <tr className="hover:bg-gray-50 dark:hover:bg-gray-800/50 border-b border-gray-200 dark:border-gray-700">
        {/* Name */}
        <td className="px-6 py-4">
          <div className="font-medium text-gray-900 dark:text-white truncate">{document.title}</div>
          {document.tags.length > 0 && (
            <div className="flex gap-1 mt-1 flex-wrap">
              {document.tags.slice(0, 2).map((tag) => (
                <span
                  key={tag}
                  className="inline-block px-2 py-0.5 text-xs bg-gray-100 text-gray-700 rounded dark:bg-gray-800 dark:text-gray-300"
                >
                  {tag}
                </span>
              ))}
              {document.tags.length > 2 && (
                <span className="inline-block px-2 py-0.5 text-xs text-gray-600 dark:text-gray-400">
                  +{document.tags.length - 2}
                </span>
              )}
            </div>
          )}
        </td>

        {/* Type */}
        <td className="px-6 py-4">
          <div className="flex items-center gap-2">
            {getTypeIcon()}
            <span className="text-sm text-gray-600 dark:text-gray-400 capitalize">
              {document.source_type}
            </span>
          </div>
        </td>

        {/* Chunks */}
        <td className="px-6 py-4 text-right">
          <span className="text-sm text-gray-600 dark:text-gray-400">{document.chunk_count}</span>
        </td>

        {/* Uploaded */}
        <td className="px-6 py-4">
          <span className="text-sm text-gray-600 dark:text-gray-400">{uploadedDate}</span>
        </td>

        {/* Actions */}
        <td className="px-6 py-4 text-right">
          <button
            onClick={() => setShowDeleteConfirm(true)}
            disabled={deleteMutation.isPending}
            className="inline-flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-red-600 hover:bg-red-50 rounded dark:text-red-400 dark:hover:bg-red-900 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Trash2 className="h-4 w-4" />
            Delete
          </button>
        </td>
      </tr>

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <tr>
          <td colSpan={5} className="px-6 py-4 bg-red-50 dark:bg-red-900/20 border-b border-red-200 dark:border-red-800">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400" />
                <p className="text-sm font-medium text-red-800 dark:text-red-300">
                  Are you sure you want to delete &quot;{document.title}&quot;?
                </p>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setShowDeleteConfirm(false)}
                  className="px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded dark:text-gray-300 dark:hover:bg-gray-700"
                >
                  Cancel
                </button>
                <button
                  onClick={handleDelete}
                  disabled={deleteMutation.isPending}
                  className="px-3 py-1.5 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded dark:bg-red-700 dark:hover:bg-red-800 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {deleteMutation.isPending ? "Deleting..." : "Delete"}
                </button>
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  );
}
