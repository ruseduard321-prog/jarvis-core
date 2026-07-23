"use client";

import { Trash2 } from "lucide-react";
import { useState } from "react";

interface PlaygroundControlsProps {
  onClearConversation: () => void;
  isDisabled: boolean;
}

export function PlaygroundControls({ onClearConversation, isDisabled }: PlaygroundControlsProps) {
  const [showConfirm, setShowConfirm] = useState(false);

  const handleClear = () => {
    onClearConversation();
    setShowConfirm(false);
  };

  if (showConfirm) {
    return (
      <div className="flex items-center justify-between bg-yellow-50 border border-yellow-200 rounded-lg px-4 py-3">
        <span className="text-sm text-yellow-800">Clear all messages and start a new conversation?</span>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowConfirm(false)}
            className="px-3 py-1 text-sm border rounded hover:bg-gray-100 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleClear}
            className="px-3 py-1 text-sm bg-yellow-600 text-white rounded hover:bg-yellow-700 transition-colors"
          >
            Clear
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-between">
      <p className="text-xs text-gray-500">Playground Mode: Reuse existing conversations, experiment freely</p>
      <button
        onClick={() => setShowConfirm(true)}
        disabled={isDisabled}
        className="flex items-center gap-2 px-3 py-1.5 text-sm text-red-600 border border-red-200 rounded hover:bg-red-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        title="Clear conversation"
      >
        <Trash2 className="w-4 h-4" />
        Clear Conversation
      </button>
    </div>
  );
}
