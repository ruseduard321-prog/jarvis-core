"use client";

import { useState } from "react";
import { Memory } from "@/types";
import { memoryService } from "@/services/memory-service";
import { MemoryToolbar } from "./memory-toolbar";
import { MemoryTable } from "./memory-table";
import { MemoryForm } from "./memory-form";
import { Plus } from "lucide-react";

interface MemoryLayoutProps {
  memories: Memory[];
}

export function MemoryLayout({ memories }: MemoryLayoutProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [filterCategory, setFilterCategory] = useState<string>("all");
  const [filterImportance, setFilterImportance] = useState<string>("all");
  const [showCreateForm, setShowCreateForm] = useState(false);

  // Apply search and filters
  let filtered = memories;
  filtered = memoryService.searchMemories(filtered, searchQuery);
  filtered = memoryService.filterMemories(filtered, {
    category: filterCategory,
    importance: filterImportance,
  });

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Memory</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Store and manage your memories
          </p>
        </div>
        <button
          onClick={() => setShowCreateForm(true)}
          className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
        >
          <Plus className="h-4 w-4" />
          New Memory
        </button>
      </div>

      {/* Toolbar */}
      <MemoryToolbar
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        filterCategory={filterCategory}
        onCategoryChange={setFilterCategory}
        filterImportance={filterImportance}
        onImportanceChange={setFilterImportance}
      />

      {/* Table */}
      <MemoryTable memories={filtered} />

      {/* Create Form Modal */}
      <MemoryForm
        mode="create"
        isOpen={showCreateForm}
        onClose={() => setShowCreateForm(false)}
      />
    </div>
  );
}
