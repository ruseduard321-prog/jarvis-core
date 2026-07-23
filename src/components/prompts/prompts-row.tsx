"use client";

import { useState } from "react";
import { Prompt } from "@/types";
import { Trash2, Edit2, Heart } from "lucide-react";
import { Dialog } from "@/components/ui/dialog";
import { promptsService } from "@/services/prompts-service";
import { useQueryClient, useMutation } from "@tanstack/react-query";

interface PromptsRowProps {
  prompt: Prompt;
  onEditClick: (id: string) => void;
}

export function PromptsRow({ prompt, onEditClick }: PromptsRowProps) {
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const queryClient = useQueryClient();

  const { mutate: deletePrompt, isPending: isDeleting } = useMutation({
    mutationFn: () => promptsService.deletePrompt(prompt.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["prompts"] });
      setDeleteConfirmOpen(false);
    },
  });

  const { mutate: toggleFavorite } = useMutation({
    mutationFn: () =>
      promptsService.updatePrompt(prompt.id, {
        favorite: !prompt.favorite,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["prompts"] });
    },
  });

  const preview = prompt.content.substring(0, 60).replace(/\n/g, " ");
  const previewText = preview.length < prompt.content.length ? `${preview}...` : preview;
  const createdDate = new Date(prompt.created_at).toLocaleDateString();

  return (
    <>
      <tr className="border-b hover:bg-gray-50 transition-colors">
        <td className="px-4 py-3 font-medium text-gray-900">{prompt.name}</td>
        <td className="px-4 py-3 text-gray-700 text-xs">{previewText}</td>
        <td className="px-4 py-3 text-gray-700">{prompt.category}</td>
        <td className="px-4 py-3 text-center">
          <button
            onClick={() => toggleFavorite()}
            className="transition-colors hover:opacity-70"
          >
            <Heart
              className={`w-4 h-4 ${
                prompt.favorite ? "fill-yellow-400 text-yellow-400" : "text-gray-300"
              }`}
            />
          </button>
        </td>
        <td className="px-4 py-3 text-gray-600 text-xs">{createdDate}</td>
        <td className="px-4 py-3">
          <div className="flex justify-center gap-2">
            <button
              onClick={() => onEditClick(prompt.id)}
              className="p-1 hover:bg-blue-100 rounded transition-colors"
              title="Edit"
            >
              <Edit2 className="w-4 h-4 text-blue-600" />
            </button>
            <button
              onClick={() => setDeleteConfirmOpen(true)}
              className="p-1 hover:bg-red-100 rounded transition-colors"
              title="Delete"
            >
              <Trash2 className="w-4 h-4 text-red-600" />
            </button>
          </div>
        </td>
      </tr>

      {/* Delete confirmation dialog */}
      {deleteConfirmOpen && (
        <Dialog
          isOpen={deleteConfirmOpen}
          onClose={() => setDeleteConfirmOpen(false)}
          title="Delete Prompt"
          description={`Are you sure you want to delete "${prompt.name}"? This action cannot be undone.`}
          footer={
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setDeleteConfirmOpen(false)}
                className="px-4 py-2 border rounded-md hover:bg-gray-50 transition-colors"
                disabled={isDeleting}
              >
                Cancel
              </button>
              <button
                onClick={() => deletePrompt()}
                className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors disabled:opacity-50"
                disabled={isDeleting}
              >
                {isDeleting ? "Deleting..." : "Delete"}
              </button>
            </div>
          }
        />
      )}
    </>
  );
}
