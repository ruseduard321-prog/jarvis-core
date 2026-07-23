"use client";

import { QuickAction } from "@/types";
import { useRouter } from "next/navigation";
import { Plus, BookOpen, Bot, Settings } from "lucide-react";

interface ActionCardProps {
  action: QuickAction;
}

/**
 * Reusable Action Card
 * Displays a quick action button with icon and description
 */
export function ActionCard({ action }: ActionCardProps) {
  const router = useRouter();

  const handleClick = () => {
    router.push(action.href);
  };

  const renderIcon = () => {
    switch (action.icon) {
      case "plus":
        return <Plus className="w-6 h-6 mb-2 text-gray-700 dark:text-gray-300" />;
      case "book":
        return <BookOpen className="w-6 h-6 mb-2 text-gray-700 dark:text-gray-300" />;
      case "bot":
        return <Bot className="w-6 h-6 mb-2 text-gray-700 dark:text-gray-300" />;
      case "settings":
        return <Settings className="w-6 h-6 mb-2 text-gray-700 dark:text-gray-300" />;
      default:
        return <Plus className="w-6 h-6 mb-2 text-gray-700 dark:text-gray-300" />;
    }
  };

  return (
    <button
      onClick={handleClick}
      className="flex flex-col items-center justify-center p-4 rounded-lg bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors text-center border border-transparent hover:border-gray-300 dark:hover:border-gray-600"
    >
      {renderIcon()}
      <h3 className="font-semibold text-sm text-gray-900 dark:text-white">{action.label}</h3>
      <p className="text-xs text-gray-600 dark:text-gray-400 mt-1 line-clamp-2">{action.description}</p>
    </button>
  );
}
