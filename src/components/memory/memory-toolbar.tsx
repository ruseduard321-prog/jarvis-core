"use client";

import { useState, useEffect } from "react";
import { Search, Filter, X } from "lucide-react";

interface MemoryToolbarProps {
  searchQuery: string;
  onSearchChange: (query: string) => void;
  filterCategory: string;
  onCategoryChange: (category: string) => void;
  filterImportance: string;
  onImportanceChange: (importance: string) => void;
}

const CATEGORIES = [
  "all",
  "FACT",
  "REASONING",
  "CONTEXT",
  "INSIGHT",
  "PATTERN",
  "DECISION",
];

const IMPORTANCE_LEVELS = ["all", "high", "medium", "low"];

export function MemoryToolbar({
  searchQuery,
  onSearchChange,
  filterCategory,
  onCategoryChange,
  filterImportance,
  onImportanceChange,
}: MemoryToolbarProps) {
  const [debouncedSearch, setDebouncedSearch] = useState(searchQuery);

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      onSearchChange(debouncedSearch);
    }, 500); // 500ms debounce

    return () => clearTimeout(timer);
  }, [debouncedSearch, onSearchChange]);

  const hasFilters =
    filterCategory !== "all" ||
    filterImportance !== "all" ||
    debouncedSearch.trim() !== "";

  return (
    <div className="flex flex-col gap-3 p-4 bg-muted/50 rounded-lg border border-border">
      {/* Search Input */}
      <div className="flex items-center gap-2 px-3 py-2 bg-background border border-border rounded-lg">
        <Search className="h-4 w-4 text-muted-foreground" />
        <input
          type="text"
          placeholder="Search by content, tags, or source..."
          value={debouncedSearch}
          onChange={(e) => setDebouncedSearch(e.target.value)}
          className="flex-1 bg-transparent outline-none text-sm"
        />
        {debouncedSearch && (
          <button
            onClick={() => setDebouncedSearch("")}
            className="p-1 hover:bg-muted rounded transition-colors"
          >
            <X className="h-4 w-4 text-muted-foreground" />
          </button>
        )}
      </div>

      {/* Filters */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:gap-3">
        <Filter className="h-4 w-4 text-muted-foreground" />

        {/* Category Filter */}
        <select
          value={filterCategory}
          onChange={(e) => onCategoryChange(e.target.value)}
          className="px-3 py-1.5 text-sm bg-background border border-border rounded-lg outline-none hover:border-primary focus:border-primary transition-colors"
        >
          {CATEGORIES.map((cat) => (
            <option key={cat} value={cat}>
              {cat === "all" ? "All Categories" : cat}
            </option>
          ))}
        </select>

        {/* Importance Filter */}
        <select
          value={filterImportance}
          onChange={(e) => onImportanceChange(e.target.value)}
          className="px-3 py-1.5 text-sm bg-background border border-border rounded-lg outline-none hover:border-primary focus:border-primary transition-colors"
        >
          {IMPORTANCE_LEVELS.map((level) => (
            <option key={level} value={level}>
              {level === "all"
                ? "All Levels"
                : level.charAt(0).toUpperCase() + level.slice(1)}
            </option>
          ))}
        </select>

        {/* Reset Button */}
        {hasFilters && (
          <button
            onClick={() => {
              setDebouncedSearch("");
              onSearchChange("");
              onCategoryChange("all");
              onImportanceChange("all");
            }}
            className="px-3 py-1.5 text-sm text-muted-foreground hover:text-foreground hover:bg-muted rounded-lg transition-colors"
          >
            Reset
          </button>
        )}
      </div>
    </div>
  );
}
