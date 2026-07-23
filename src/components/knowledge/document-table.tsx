"use client";

import { useState } from "react";
import { ChevronUp, ChevronDown } from "lucide-react";
import type { Document } from "@/types";
import { DocumentRow } from "./document-row";

interface DocumentTableProps {
  documents: Document[];
}

type SortKey = "title" | "created_at" | "chunk_count";
type SortOrder = "asc" | "desc";

/**
 * Document Table
 * Displays list of documents with sorting capabilities
 */
export function DocumentTable({ documents }: DocumentTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>("created_at");
  const [sortOrder, setSortOrder] = useState<SortOrder>("desc");

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortKey(key);
      setSortOrder("asc");
    }
  };

  // Sort documents
  const sortedDocs = [...documents].sort((a, b) => {
    let aValue: string | number = "";
    let bValue: string | number = "";

    switch (sortKey) {
      case "title":
        aValue = a.title.toLowerCase();
        bValue = b.title.toLowerCase();
        break;
      case "created_at":
        aValue = new Date(a.created_at).getTime();
        bValue = new Date(b.created_at).getTime();
        break;
      case "chunk_count":
        aValue = a.chunk_count;
        bValue = b.chunk_count;
        break;
    }

    if (aValue < bValue) return sortOrder === "asc" ? -1 : 1;
    if (aValue > bValue) return sortOrder === "asc" ? 1 : -1;
    return 0;
  });

  const renderSortIcon = (key: SortKey) => {
    if (sortKey !== key) {
      return <div className="h-4 w-4 text-gray-400" />;
    }
    return sortOrder === "asc" ? (
      <ChevronUp className="h-4 w-4 text-blue-600 dark:text-blue-400" />
    ) : (
      <ChevronDown className="h-4 w-4 text-blue-600 dark:text-blue-400" />
    );
  };

  return (
    <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          {/* Table Header */}
          <thead className="bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
            <tr>
              <th className="px-6 py-3 text-left">
                <button
                  onClick={() => handleSort("title")}
                  className="flex items-center gap-2 font-medium text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white text-sm"
                >
                  Name
                  {renderSortIcon("title")}
                </button>
              </th>
              <th className="px-6 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300">Type</th>
              <th className="px-6 py-3 text-right text-sm font-medium text-gray-700 dark:text-gray-300">Chunks</th>
              <th className="px-6 py-3 text-left">
                <button
                  onClick={() => handleSort("created_at")}
                  className="flex items-center gap-2 font-medium text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white text-sm"
                >
                  Uploaded
                  {renderSortIcon("created_at")}
                </button>
              </th>
              <th className="px-6 py-3 text-right text-sm font-medium text-gray-700 dark:text-gray-300">Actions</th>
            </tr>
          </thead>

          {/* Table Body */}
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {sortedDocs.map((doc) => (
              <DocumentRow key={doc.id} document={doc} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
