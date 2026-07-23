"use client";

import { useState, useEffect } from "react";
import { Search, X } from "lucide-react";
import { SEARCH_DEBOUNCE_DELAY } from "@/constants";

interface KnowledgeToolbarProps {
  searchQuery: string;
  onSearchChange: (query: string) => void;
  filterType: string;
  onFilterTypeChange: (type: string) => void;
}

/**
 * Knowledge Toolbar
 * Combines search and filter controls
 */
export function KnowledgeToolbar({
  searchQuery,
  onSearchChange,
  filterType,
  onFilterTypeChange,
}: KnowledgeToolbarProps) {
  const [inputValue, setInputValue] = useState(searchQuery);

  // Debounce search input using useEffect
  useEffect(() => {
    const timer = setTimeout(() => {
      onSearchChange(inputValue);
    }, SEARCH_DEBOUNCE_DELAY);

    return () => clearTimeout(timer);
  }, [inputValue, onSearchChange]);

  const handleClearSearch = () => {
    setInputValue("");
  };

  return (
    <div className="space-y-4">
      {/* Search Bar */}
      <div className="relative">
        <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
        <input
          type="text"
          placeholder="Search documents by name or tags..."
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          className="w-full pl-10 pr-10 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-900 dark:border-gray-700 dark:text-white dark:placeholder-gray-400"
        />
        {inputValue && (
          <button
            onClick={handleClearSearch}
            className="absolute right-3 top-3 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            aria-label="Clear search"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* Filter Bar */}
      <div className="flex gap-3 flex-wrap">
        {/* Type Filter */}
        <select
          value={filterType}
          onChange={(e) => onFilterTypeChange(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-900 dark:border-gray-700 dark:text-white text-sm"
        >
          <option value="all">All Types</option>
          <option value="pdf">PDF</option>
          <option value="text">Text</option>
          <option value="markdown">Markdown</option>
          <option value="docx">DOCX</option>
          <option value="csv">CSV</option>
          <option value="json">JSON</option>
        </select>

        {/* Reset Filters */}
        {(filterType !== "all" || inputValue) && (
          <button
            onClick={() => {
              setInputValue("");
              onFilterTypeChange("all");
            }}
            className="px-3 py-2 text-sm font-medium text-blue-600 hover:bg-blue-50 rounded-lg dark:text-blue-400 dark:hover:bg-blue-900"
          >
            Reset
          </button>
        )}
      </div>
    </div>
  );
}
