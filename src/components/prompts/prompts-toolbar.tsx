"use client";

import { useEffect, useState } from "react";
import { Search, X, Heart, Plus } from "lucide-react";
import { PromptCategory } from "@/types";

interface PromptsToolbarProps {
  searchQuery: string;
  onSearchChange: (query: string) => void;
  categoryFilter: PromptCategory | "";
  onCategoryFilterChange: (category: PromptCategory | "") => void;
  favoriteFilter: boolean;
  onFavoriteFilterChange: (favorite: boolean) => void;
  onReset: () => void;
  onNewClick: () => void;
}

const CATEGORIES: PromptCategory[] = [
  "Chat",
  "System",
  "Coding",
  "Analysis",
  "Writing",
  "Creative",
];

export function PromptsToolbar({
  searchQuery,
  onSearchChange,
  categoryFilter,
  onCategoryFilterChange,
  favoriteFilter,
  onFavoriteFilterChange,
  onReset,
  onNewClick,
}: PromptsToolbarProps) {
  const [debouncedQuery, setDebouncedQuery] = useState(searchQuery);

  // 500ms debounce for search
  useEffect(() => {
    const timer = setTimeout(() => {
      onSearchChange(debouncedQuery);
    }, 500);

    return () => clearTimeout(timer);
  }, [debouncedQuery, onSearchChange]);

  return (
    <div className="space-y-3">
      {/* Search input */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <input
          type="text"
          placeholder="Search prompts by name or content..."
          value={debouncedQuery}
          onChange={(e) => setDebouncedQuery(e.target.value)}
          className="w-full pl-9 pr-3 py-2 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {/* Filters and actions */}
      <div className="flex items-center gap-2 flex-wrap">
        {/* Category filter */}
        <select
          value={categoryFilter}
          onChange={(e) =>
            onCategoryFilterChange(e.target.value as PromptCategory | "")
          }
          className="px-3 py-2 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">All Categories</option>
          {CATEGORIES.map((category) => (
            <option key={category} value={category}>
              {category}
            </option>
          ))}
        </select>

        {/* Favorite filter toggle */}
        <button
          onClick={() => onFavoriteFilterChange(!favoriteFilter)}
          className={`px-3 py-2 border rounded-md text-sm transition-colors flex items-center gap-2 ${
            favoriteFilter
              ? "bg-yellow-100 border-yellow-300 text-yellow-800"
              : "hover:bg-gray-50"
          }`}
        >
          <Heart
            className={`w-4 h-4 ${favoriteFilter ? "fill-current" : ""}`}
          />
          Favorites
        </button>

        {/* Reset button */}
        {(searchQuery || categoryFilter || favoriteFilter) && (
          <button
            onClick={onReset}
            className="px-3 py-2 border rounded-md text-sm hover:bg-gray-50 transition-colors flex items-center gap-1"
          >
            <X className="w-4 h-4" />
            Reset
          </button>
        )}

        {/* Spacer */}
        <div className="flex-1" />

        {/* New button */}
        <button
          onClick={onNewClick}
          className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700 transition-colors flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          New Prompt
        </button>
      </div>
    </div>
  );
}
