"use client";

import { useEffect, useState, useCallback } from "react";
import { Search, X } from "lucide-react";

/**
 * Conversations Toolbar
 * Search input with 500ms debounce and reset button
 */
interface ConversationsToolbarProps {
  searchQuery: string;
  onSearchChange: (query: string) => void;
}

export function ConversationsToolbar({
  searchQuery,
  onSearchChange,
}: ConversationsToolbarProps) {
  const [inputValue, setInputValue] = useState(searchQuery);

  // Debounce search input (500ms)
  useEffect(() => {
    const timer = setTimeout(() => {
      onSearchChange(inputValue);
    }, 500);

    return () => clearTimeout(timer);
  }, [inputValue, onSearchChange]);

  const handleReset = useCallback(() => {
    setInputValue("");
    onSearchChange("");
  }, [onSearchChange]);

  return (
    <div className="border-b border-gray-200 dark:border-gray-800 px-6 py-4">
      <div className="flex items-center gap-2">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400 dark:text-gray-600" />
          <input
            type="text"
            placeholder="Search by title..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        {searchQuery && (
          <button
            onClick={handleReset}
            className="inline-flex items-center gap-1 px-3 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
          >
            <X className="h-4 w-4" />
            Reset
          </button>
        )}
      </div>
    </div>
  );
}
