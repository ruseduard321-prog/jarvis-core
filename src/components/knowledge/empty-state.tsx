"use client";

import { BookOpen } from "lucide-react";

/**
 * Empty State
 * Displayed when no documents exist
 */
export function EmptyState() {
  return (
    <div className="text-center py-12 px-6">
      <BookOpen className="h-12 w-12 text-gray-400 dark:text-gray-600 mx-auto mb-4" />
      <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">No documents yet</h3>
      <p className="text-gray-600 dark:text-gray-400 mb-6">
        Start by uploading your first document to build your knowledge base
      </p>
      <a
        href="#upload"
        className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 dark:bg-blue-700 dark:hover:bg-blue-800 font-medium"
      >
        Upload Document
      </a>
    </div>
  );
}
