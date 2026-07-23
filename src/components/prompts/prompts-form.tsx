"use client";

import { useState } from "react";
import { Prompt, PromptCategory } from "@/types";
import { Dialog } from "@/components/ui/dialog";
import { promptsService } from "@/services/prompts-service";
import { useQueryClient, useMutation } from "@tanstack/react-query";

interface PromptsFormProps {
  prompt?: Prompt;
  onClose: () => void;
}

const CATEGORIES: PromptCategory[] = [
  "Chat",
  "System",
  "Coding",
  "Analysis",
  "Writing",
  "Creative",
];

export function PromptsForm({ prompt, onClose }: PromptsFormProps) {
  const isEditing = !!prompt;
  const queryClient = useQueryClient();

  const [formData, setFormData] = useState({
    name: prompt?.name || "",
    content: prompt?.content || "",
    category: (prompt?.category || "Chat") as PromptCategory,
  });

  const { mutate: submitForm, isPending } = useMutation({
    mutationFn: async () => {
      if (isEditing && prompt) {
        const result = await promptsService.updatePrompt(prompt.id, formData);
        if (result.error) throw new Error(result.error);
        return result;
      } else {
        const result = await promptsService.createPrompt(formData);
        if (result.error) throw new Error(result.error);
        return result;
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["prompts"] });
      onClose();
    },
  });

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim() || !formData.content.trim()) {
      alert("Name and content are required");
      return;
    }
    submitForm();
  };

  return (
    <Dialog
      isOpen={true}
      onClose={onClose}
      title={isEditing ? "Edit Prompt" : "Create Prompt"}
      description={isEditing ? "Update your prompt details" : "Create a new prompt"}
      footer={
        <div className="flex justify-end gap-2">
          <button
            onClick={onClose}
            className="px-4 py-2 border rounded-md hover:bg-gray-50 transition-colors"
            disabled={isPending}
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50"
            disabled={isPending}
          >
            {isPending ? "Saving..." : isEditing ? "Update" : "Create"}
          </button>
        </div>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Name field */}
        <div>
          <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
            Name *
          </label>
          <input
            id="name"
            type="text"
            name="name"
            value={formData.name}
            onChange={handleChange}
            placeholder="Enter prompt name"
            className="w-full px-3 py-2 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isPending}
          />
        </div>

        {/* Category field */}
        <div>
          <label htmlFor="category" className="block text-sm font-medium text-gray-700 mb-1">
            Category *
          </label>
          <select
            id="category"
            name="category"
            value={formData.category}
            onChange={handleChange}
            className="w-full px-3 py-2 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isPending}
          >
            {CATEGORIES.map((category) => (
              <option key={category} value={category}>
                {category}
              </option>
            ))}
          </select>
        </div>

        {/* Content field */}
        <div>
          <label htmlFor="content" className="block text-sm font-medium text-gray-700 mb-1">
            Content *
          </label>
          <textarea
            id="content"
            name="content"
            value={formData.content}
            onChange={handleChange}
            placeholder="Enter prompt content"
            rows={6}
            className="w-full px-3 py-2 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            disabled={isPending}
          />
        </div>
      </form>
    </Dialog>
  );
}
