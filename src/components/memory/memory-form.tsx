"use client";

import { useState } from "react";
import { Memory, MemoryCategory } from "@/types";
import { Dialog } from "@/components/ui/dialog";
import { useMemoryCreate, useMemoryUpdate } from "@/hooks/use-memory";
import { Loader } from "lucide-react";

interface MemoryFormProps {
  mode: "create" | "edit";
  initialData?: Memory;
  isOpen: boolean;
  onClose: () => void;
}

const CATEGORIES: MemoryCategory[] = ["FACT", "REASONING", "CONTEXT", "INSIGHT", "PATTERN", "DECISION"];
const IMPORTANCE_LEVELS = ["high", "medium", "low"];

export function MemoryForm({
  mode,
  initialData,
  isOpen,
  onClose,
}: MemoryFormProps) {
  const [content, setContent] = useState(initialData?.content || "");
  const [category, setCategory] = useState<MemoryCategory>(
    (initialData?.record_type as MemoryCategory) || "FACT"
  );
  const [importance, setImportance] = useState(
    (initialData?.attributes?.importance as string) || "medium"
  );
  const [tags, setTags] = useState(initialData?.tags?.join(", ") || "");
  const [source, setSource] = useState(initialData?.source || "");

  const createMutation = useMemoryCreate();
  const updateMutation = useMemoryUpdate(initialData?.id || "");

  const isLoading = createMutation.isPending || updateMutation.isPending;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!content.trim()) {
      alert("Content is required");
      return;
    }

    const parsedTags = tags
      .split(",")
      .map((t) => t.trim())
      .filter((t) => t.length > 0);

    const data = {
      content,
      record_type: category,
      tags: parsedTags,
      source: source || undefined,
      attributes: {
        importance,
      },
    };

    try {
      if (mode === "create") {
        await createMutation.mutateAsync(data);
      } else if (initialData) {
        await updateMutation.mutateAsync(data);
      }
      onClose();
      // Reset form
      setContent("");
      setCategory("FACT");
      setImportance("medium");
      setTags("");
      setSource("");
    } catch (error) {
      console.error("Submit failed:", error);
    }
  };

  return (
    <Dialog
      isOpen={isOpen}
      onClose={onClose}
      title={mode === "create" ? "Create Memory" : "Edit Memory"}
      size="lg"
      footer={
        <div className="flex gap-2 justify-end">
          <button
            onClick={onClose}
            disabled={isLoading}
            className="px-4 py-2 text-sm font-medium text-foreground hover:bg-muted rounded disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={isLoading}
            className="px-4 py-2 text-sm font-medium text-white bg-primary hover:bg-primary/90 rounded disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
          >
            {isLoading && <Loader className="h-4 w-4 animate-spin" />}
            {mode === "create" ? "Create" : "Update"}
          </button>
        </div>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Content */}
        <div className="space-y-2">
          <label className="text-sm font-medium">Content *</label>
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Enter memory content..."
            disabled={isLoading}
            rows={4}
            className="w-full px-3 py-2 text-sm bg-background border border-border rounded-lg outline-none focus:border-primary transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          />
        </div>

        {/* Category & Importance Row */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Category</label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value as MemoryCategory)}
              disabled={isLoading}
              className="w-full px-3 py-2 text-sm bg-background border border-border rounded-lg outline-none focus:border-primary transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {CATEGORIES.map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </select>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Priority</label>
            <select
              value={importance}
              onChange={(e) => setImportance(e.target.value)}
              disabled={isLoading}
              className="w-full px-3 py-2 text-sm bg-background border border-border rounded-lg outline-none focus:border-primary transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {IMPORTANCE_LEVELS.map((level) => (
                <option key={level} value={level}>
                  {level.charAt(0).toUpperCase() + level.slice(1)}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Tags */}
        <div className="space-y-2">
          <label className="text-sm font-medium">Tags</label>
          <input
            type="text"
            value={tags}
            onChange={(e) => setTags(e.target.value)}
            placeholder="Separate with commas (e.g., work, urgent, api)"
            disabled={isLoading}
            className="w-full px-3 py-2 text-sm bg-background border border-border rounded-lg outline-none focus:border-primary transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          />
        </div>

        {/* Source */}
        <div className="space-y-2">
          <label className="text-sm font-medium">Source</label>
          <input
            type="text"
            value={source}
            onChange={(e) => setSource(e.target.value)}
            placeholder="Where this memory came from (optional)"
            disabled={isLoading}
            className="w-full px-3 py-2 text-sm bg-background border border-border rounded-lg outline-none focus:border-primary transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          />
        </div>
      </form>
    </Dialog>
  );
}
