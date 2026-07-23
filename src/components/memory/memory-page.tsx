"use client";

import { useMemoryList } from "@/hooks/use-memory";
import { MemoryLayout } from "./memory-layout";
import { AlertCircle, Loader } from "lucide-react";

export function MemoryPage() {
  const { data: memories = [], isLoading, error } = useMemoryList();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="flex flex-col items-center gap-2">
          <Loader className="h-8 w-8 animate-spin text-muted-foreground" />
          <p className="text-sm text-muted-foreground">Loading memories...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="flex flex-col items-center gap-3 p-6 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800 max-w-md">
          <AlertCircle className="h-8 w-8 text-red-600 dark:text-red-400" />
          <p className="text-sm font-medium text-red-800 dark:text-red-300">
            Failed to load memories
          </p>
          <p className="text-xs text-red-700 dark:text-red-400">
            {error instanceof Error ? error.message : "An unknown error occurred"}
          </p>
        </div>
      </div>
    );
  }

  return <MemoryLayout memories={memories} />;
}
