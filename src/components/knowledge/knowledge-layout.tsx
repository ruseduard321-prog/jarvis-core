"use client";

import { useState } from "react";
import type { KnowledgeListResponse } from "@/types";
import { KnowledgeToolbar } from "./knowledge-toolbar";
import { UploadZone } from "./upload-zone";
import { DocumentTable } from "./document-table";
import { EmptyState } from "./empty-state";
import { knowledgeService } from "@/services/knowledge-service";

interface KnowledgeLayoutProps {
  knowledge: KnowledgeListResponse;
}

/**
 * Knowledge Base Layout
 * Arranges all sections in a responsive grid
 */
export function KnowledgeLayout({ knowledge }: KnowledgeLayoutProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [filterType, setFilterType] = useState("all");

  // Apply search and filters
  let filteredDocs = knowledge.documents;

  // Apply search
  filteredDocs = knowledgeService.searchDocuments(filteredDocs, searchQuery);

  // Apply type filter
  filteredDocs = knowledgeService.filterDocuments(filteredDocs, {
    type: filterType,
  });

  const isEmpty = filteredDocs.length === 0 && knowledge.total_count === 0;
  const isFilteredEmpty = filteredDocs.length === 0 && knowledge.total_count > 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Knowledge Base</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-2">
          Manage and organize your documents, files, and knowledge resources
        </p>
      </div>

      {/* Search and Filters */}
      <KnowledgeToolbar
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        filterType={filterType}
        onFilterTypeChange={setFilterType}
      />

      {/* Upload Zone */}
      <UploadZone />

      {/* Content */}
      {isEmpty ? (
        <EmptyState />
      ) : isFilteredEmpty ? (
        <div className="text-center py-12">
          <p className="text-gray-600 dark:text-gray-400">No documents match your filters</p>
          <button
            onClick={() => {
              setSearchQuery("");
              setFilterType("all");
            }}
            className="mt-3 text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 text-sm font-medium"
          >
            Clear filters
          </button>
        </div>
      ) : (
        <DocumentTable documents={filteredDocs} />
      )}
    </div>
  );
}
