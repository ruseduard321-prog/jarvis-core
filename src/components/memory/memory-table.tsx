"use client";

import { Memory } from "@/types";
import { MemoryRow } from "./memory-row";

interface MemoryTableProps {
  memories: Memory[];
}

export function MemoryTable({ memories }: MemoryTableProps) {
  if (memories.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 p-6 bg-muted/30 rounded-lg border border-dashed border-border">
        <p className="text-sm text-muted-foreground text-center">
          No memories found. Create one to get started.
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-border overflow-hidden bg-background">
      <table className="w-full text-sm">
        <thead className="bg-muted/50 border-b border-border">
          <tr>
            <th className="px-6 py-3 text-left font-medium text-muted-foreground">
              Content
            </th>
            <th className="px-6 py-3 text-left font-medium text-muted-foreground w-24">
              Category
            </th>
            <th className="px-6 py-3 text-left font-medium text-muted-foreground w-20">
              Priority
            </th>
            <th className="px-6 py-3 text-left font-medium text-muted-foreground w-32">
              Source
            </th>
            <th className="px-6 py-3 text-left font-medium text-muted-foreground w-24">
              Created
            </th>
            <th className="px-6 py-3 text-right font-medium text-muted-foreground w-20">
              Actions
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {memories.map((memory) => (
            <MemoryRow key={memory.id} memory={memory} />
          ))}
        </tbody>
      </table>
    </div>
  );
}
