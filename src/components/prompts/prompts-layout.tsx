"use client";

import { useState, useMemo } from "react";
import { Prompt, PromptCategory } from "@/types";
import { PromptsToolbar } from "./prompts-toolbar";
import { PromptsTable } from "./prompts-table";
import { PromptsForm } from "./prompts-form";

interface PromptsLayoutProps {
  prompts: Prompt[];
}

export function PromptsLayout({ prompts }: PromptsLayoutProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [categoryFilter, setCategoryFilter] = useState<PromptCategory | "">(""); 
  const [favoriteFilter, setFavoriteFilter] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);

  // Search and filter helpers
  const searchPrompts = (items: Prompt[], query: string): Prompt[] => {
    if (!query) return items;
    const lowerQuery = query.toLowerCase();
    return items.filter(
      (prompt) =>
        prompt.name.toLowerCase().includes(lowerQuery) ||
        prompt.content.toLowerCase().includes(lowerQuery)
    );
  };

  const applyFilters = (
    items: Prompt[],
    category: PromptCategory | "",
    favorite: boolean
  ): Prompt[] => {
    let filtered = items;

    if (category) {
      filtered = filtered.filter((prompt) => prompt.category === category);
    }

    if (favorite) {
      filtered = filtered.filter((prompt) => prompt.favorite);
    }

    return filtered;
  };

  // Apply search and filters
  const filteredPrompts = useMemo(() => {
    let result = searchPrompts(prompts, searchQuery);
    result = applyFilters(result, categoryFilter, favoriteFilter);
    return result;
  }, [prompts, searchQuery, categoryFilter, favoriteFilter]);

  const handleReset = () => {
    setSearchQuery("");
    setCategoryFilter("");
    setFavoriteFilter(false);
  };

  const handleNewClick = () => {
    setEditingId(null);
    setShowCreateForm(true);
  };

  const handleEditClick = (id: string) => {
    setEditingId(id);
    setShowCreateForm(true);
  };

  const handleFormClose = () => {
    setShowCreateForm(false);
    setEditingId(null);
  };

  const editingPrompt = editingId
    ? prompts.find((p) => p.id === editingId)
    : undefined;

  return (
    <div className="flex flex-col gap-4">
      <PromptsToolbar
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        categoryFilter={categoryFilter}
        onCategoryFilterChange={setCategoryFilter}
        favoriteFilter={favoriteFilter}
        onFavoriteFilterChange={setFavoriteFilter}
        onReset={handleReset}
        onNewClick={handleNewClick}
      />

      <PromptsTable
        prompts={filteredPrompts}
        onEditClick={handleEditClick}
      />

      {showCreateForm && (
        <PromptsForm
          prompt={editingPrompt}
          onClose={handleFormClose}
        />
      )}
    </div>
  );
}
