"use client";

import { Prompt } from "@/types";
import { PromptsRow } from "./prompts-row";
import { BookOpen } from "lucide-react";

interface PromptsTableProps {
  prompts: Prompt[];
  onEditClick: (id: string) => void;
}

export function PromptsTable({ prompts, onEditClick }: PromptsTableProps) {
  if (prompts.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-center border rounded-lg bg-gray-50">
        <BookOpen className="w-12 h-12 text-muted-foreground mb-3" />
        <h3 className="text-lg font-medium text-gray-900">No prompts found</h3>
        <p className="text-sm text-muted-foreground mt-1">
          Create your first prompt or adjust your filters.
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto border rounded-lg">
      <table className="w-full text-sm">
        <thead className="bg-gray-50 border-b">
          <tr>
            <th className="px-4 py-3 text-left font-medium text-gray-700 w-1/4">
              Name
            </th>
            <th className="px-4 py-3 text-left font-medium text-gray-700 w-1/3">
              Preview
            </th>
            <th className="px-4 py-3 text-left font-medium text-gray-700 w-1/6">
              Category
            </th>
            <th className="px-4 py-3 text-center font-medium text-gray-700 w-16">
              ⭐
            </th>
            <th className="px-4 py-3 text-left font-medium text-gray-700 w-1/6">
              Created
            </th>
            <th className="px-4 py-3 text-center font-medium text-gray-700 w-20">
              Actions
            </th>
          </tr>
        </thead>
        <tbody>
          {prompts.map((prompt) => (
            <PromptsRow
              key={prompt.id}
              prompt={prompt}
              onEditClick={onEditClick}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
}
