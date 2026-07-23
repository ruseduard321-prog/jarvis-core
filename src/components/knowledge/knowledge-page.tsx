"use client";

import { useKnowledgeList } from "@/hooks/use-knowledge";
import { KnowledgeLayout } from "./knowledge-layout";
import { Skeleton } from "@/components/ui/skeleton";

/**
 * Knowledge Base Page
 * Main orchestrator for the knowledge base feature
 */
export function KnowledgePage() {
  const { data: knowledge, isLoading, error } = useKnowledgeList();

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-red-600 dark:text-red-500 mb-2">Error</h2>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            {(error as Error).message || "Failed to load documents"}
          </p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 dark:bg-blue-700 dark:hover:bg-blue-800"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (isLoading || !knowledge) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-12 rounded-lg" />
        <Skeleton className="h-48 rounded-lg" />
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <Skeleton key={i} className="h-16 rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  return <KnowledgeLayout knowledge={knowledge} />;
}
