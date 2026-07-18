"use client";

import React from "react";
import { cn } from "@/utils";
import { ChevronLeft, ChevronRight } from "lucide-react";

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  siblingCount?: number;
  showFirstLast?: boolean;
}

const getPaginationRange = (
  currentPage: number,
  totalPages: number,
  siblingCount: number
): (number | string)[] => {
  const totalPageNumbers = siblingCount + 5;

  if (totalPages <= totalPageNumbers) {
    return Array.from({ length: totalPages }, (_, i) => i + 1);
  }

  const leftSiblingIndex = Math.max(currentPage - siblingCount, 1);
  const rightSiblingIndex = Math.min(currentPage + siblingCount, totalPages);

  const showLeftDots = leftSiblingIndex > 2;
  const showRightDots = rightSiblingIndex < totalPages - 2;

  if (!showLeftDots && showRightDots) {
    const range = Array.from(
      { length: 3 + 2 * siblingCount },
      (_, i) => i + 1
    );
    return [...range, "...", totalPages];
  }

  if (showLeftDots && !showRightDots) {
    const range = Array.from(
      { length: 3 + 2 * siblingCount },
      (_, i) => totalPages - (3 + 2 * siblingCount) + i + 1
    );
    return [1, "...", ...range];
  }

  if (showLeftDots && showRightDots) {
    const range = Array.from(
      { length: 2 * siblingCount + 1 },
      (_, i) => leftSiblingIndex + i
    );
    return [1, "...", ...range, "...", totalPages];
  }

  return [];
};

const Pagination = React.forwardRef<HTMLDivElement, PaginationProps>(
  (
    {
      currentPage,
      totalPages,
      onPageChange,
      siblingCount = 1,
      showFirstLast = true,
    },
    ref
  ) => {
    const paginationRange = getPaginationRange(currentPage, totalPages, siblingCount);

    return (
      <div ref={ref} className="flex items-center justify-center gap-2">
        <button
          onClick={() => onPageChange(Math.max(1, currentPage - 1))}
          disabled={currentPage === 1}
          className="p-2 hover:bg-muted rounded disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          aria-label="Previous page"
        >
          <ChevronLeft className="h-4 w-4" />
        </button>

        {showFirstLast && currentPage > siblingCount + 3 && (
          <>
            <button
              onClick={() => onPageChange(1)}
              className="px-3 py-1 rounded hover:bg-muted transition-colors"
            >
              1
            </button>
            {currentPage > siblingCount + 4 && <span className="px-2">...</span>}
          </>
        )}

        {paginationRange.map((page, index) => (
          <button
            key={index}
            onClick={() => typeof page === "number" && onPageChange(page)}
            disabled={page === "..." || page === currentPage}
            className={cn(
              "px-3 py-1 rounded transition-colors",
              page === currentPage
                ? "bg-primary text-primary-foreground"
                : page === "..."
                  ? "cursor-default"
                  : "hover:bg-muted"
            )}
          >
            {page}
          </button>
        ))}

        <button
          onClick={() => onPageChange(Math.min(totalPages, currentPage + 1))}
          disabled={currentPage === totalPages}
          className="p-2 hover:bg-muted rounded disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          aria-label="Next page"
        >
          <ChevronRight className="h-4 w-4" />
        </button>
      </div>
    );
  }
);

Pagination.displayName = "Pagination";

export { Pagination };
export type { PaginationProps };
