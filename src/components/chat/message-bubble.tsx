"use client";

import React from "react";
import { Copy, Check, RotateCcw } from "lucide-react";
import { cn } from "@/utils";
import { MarkdownRenderer } from "./markdown-renderer";
import { useClipboard } from "@/hooks";

interface MessageBubbleProps {
  content: string;
  isUser: boolean;
  isStreaming?: boolean;
  showTimestamp?: boolean;
  timestamp?: string;
  onRetry?: () => void;
  onRegenerate?: () => void;
  isLoading?: boolean;
}

/**
 * Message Bubble Component
 * Displays individual messages in the chat
 */
export function MessageBubble({
  content,
  isUser,
  isStreaming = false,
  showTimestamp = true,
  timestamp,
  onRetry,
  onRegenerate,
  isLoading = false,
}: MessageBubbleProps) {
  const [copied, copy] = useClipboard();
  const [showActions, setShowActions] = React.useState(false);

  return (
    <div className={cn("flex gap-3 mb-4", isUser ? "justify-end" : "justify-start")}>
      {/* Avatar or Status */}
      {!isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center text-xs font-bold text-primary">
          AI
        </div>
      )}

      {/* Message Content */}
      <div
        className={cn(
          "flex-shrink-0 max-w-[80%] lg:max-w-[60%] rounded-lg px-4 py-3",
          isUser ? "bg-primary text-primary-foreground rounded-br-none" : "bg-muted text-foreground rounded-bl-none"
        )}
        onMouseEnter={() => setShowActions(true)}
        onMouseLeave={() => setShowActions(false)}
      >
        {/* Message Text */}
        {isUser ? (
          <p className="whitespace-pre-wrap break-words">{content}</p>
        ) : (
          <MarkdownRenderer content={content} className="!prose-invert text-sm" />
        )}

        {/* Timestamp */}
        {showTimestamp && timestamp && (
          <p className="text-xs opacity-60 mt-2">{formatTime(timestamp)}</p>
        )}

        {/* Streaming Indicator */}
        {isStreaming && (
          <div className="flex gap-1 mt-2">
            <div className="animate-pulse h-2 w-2 rounded-full bg-current opacity-60" />
            <div className="animate-pulse h-2 w-2 rounded-full bg-current opacity-40 animation-delay-100" />
            <div className="animate-pulse h-2 w-2 rounded-full bg-current opacity-20 animation-delay-200" />
          </div>
        )}
      </div>

      {/* Actions */}
      {showActions && (
        <div className="flex gap-1 items-start pt-1">
          {!isUser && (
            <>
              {/* Copy Button */}
              <button
                onClick={() => copy(content)}
                className="p-1.5 rounded hover:bg-muted transition-colors"
                title="Copy message"
                aria-label="Copy message"
              >
                {copied ? (
                  <Check className="h-4 w-4 text-primary" />
                ) : (
                  <Copy className="h-4 w-4 text-muted-foreground hover:text-foreground" />
                )}
              </button>

              {/* Regenerate Button */}
              {onRegenerate && !isLoading && (
                <button
                  onClick={onRegenerate}
                  className="p-1.5 rounded hover:bg-muted transition-colors"
                  title="Regenerate response"
                  aria-label="Regenerate response"
                >
                  <RotateCcw className="h-4 w-4 text-muted-foreground hover:text-foreground" />
                </button>
              )}
            </>
          )}

          {/* Retry Button (for errors) */}
          {onRetry && (
            <button
              onClick={onRetry}
              className="p-1.5 rounded hover:bg-muted transition-colors"
              title="Retry message"
              aria-label="Retry message"
            >
              <RotateCcw className="h-4 w-4 text-muted-foreground hover:text-foreground" />
            </button>
          )}
        </div>
      )}
    </div>
  );
}

/**
 * User Message Component
 */
interface UserMessageProps {
  content: string;
  timestamp?: string;
  showTimestamp?: boolean;
}

export function UserMessage({ content, timestamp, showTimestamp = true }: UserMessageProps) {
  return (
    <MessageBubble
      content={content}
      isUser={true}
      showTimestamp={showTimestamp}
      timestamp={timestamp}
    />
  );
}

/**
 * Assistant Message Component
 */
interface AssistantMessageProps {
  content: string;
  timestamp?: string;
  showTimestamp?: boolean;
  isStreaming?: boolean;
  onRegenerate?: () => void;
}

export function AssistantMessage({
  content,
  timestamp,
  showTimestamp = true,
  isStreaming = false,
  onRegenerate,
}: AssistantMessageProps) {
  console.log(`[FRONTEND TRACE] 🟢 STAGE 8a: AssistantMessage component render - content.length=${content.length}, isStreaming=${isStreaming}`);
  return (
    <MessageBubble
      content={content}
      isUser={false}
      isStreaming={isStreaming}
      showTimestamp={showTimestamp}
      timestamp={timestamp}
      onRegenerate={onRegenerate}
    />
  );
}

/**
 * Error Message Component
 */
interface ErrorMessageProps {
  error: string;
  onRetry?: () => void;
}

export function ErrorMessage({ error, onRetry }: ErrorMessageProps) {
  return (
    <div className="flex gap-3 mb-4">
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-destructive/20 flex items-center justify-center text-xs font-bold text-destructive">
        !
      </div>
      <div className="flex-shrink-0 max-w-[80%] lg:max-w-[60%] rounded-lg px-4 py-3 bg-destructive/10 border border-destructive/30 rounded-bl-none">
        <p className="text-destructive text-sm">{error}</p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="mt-2 text-xs text-destructive hover:underline"
          >
            Retry
          </button>
        )}
      </div>
    </div>
  );
}

/**
 * Typing Indicator Component
 */
export function TypingIndicator() {
  return (
    <div className="flex gap-3 mb-4">
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center text-xs font-bold text-primary">
        AI
      </div>
      <div className="flex-shrink-0 rounded-lg px-4 py-3 bg-muted rounded-bl-none">
        <div className="flex gap-1">
          <div className="h-2 w-2 rounded-full bg-muted-foreground animate-bounce" />
          <div className="h-2 w-2 rounded-full bg-muted-foreground animate-bounce animation-delay-100" />
          <div className="h-2 w-2 rounded-full bg-muted-foreground animate-bounce animation-delay-200" />
        </div>
      </div>
    </div>
  );
}

/**
 * Format timestamp to display
 */
function formatTime(timestamp: string): string {
  try {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();

    // Less than a minute
    if (diff < 60000) {
      return "now";
    }

    // Less than an hour
    if (diff < 3600000) {
      const minutes = Math.floor(diff / 60000);
      return `${minutes}m ago`;
    }

    // Less than a day
    if (diff < 86400000) {
      const hours = Math.floor(diff / 3600000);
      return `${hours}h ago`;
    }

    // Same day
    if (date.toDateString() === now.toDateString()) {
      return date.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" });
    }

    // Same year
    if (date.getFullYear() === now.getFullYear()) {
      return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
    }

    // Different year
    return date.toLocaleDateString("en-US", { year: "2-digit", month: "short", day: "numeric" });
  } catch {
    return "";
  }
}
