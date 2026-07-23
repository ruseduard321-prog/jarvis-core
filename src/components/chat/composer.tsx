"use client";

import React, { useRef, useEffect } from "react";
import { Send, Square } from "lucide-react";
import { cn } from "@/utils";

interface ComposerProps {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  onStop?: () => void;
  isLoading?: boolean;
  isStreaming?: boolean;
  disabled?: boolean;
  placeholder?: string;
  className?: string;
}

/**
 * Message Composer Component
 * Professional input for composing and sending messages
 * Features:
 * - Multi-line input with auto-resize
 * - Keyboard shortcuts (Ctrl+Enter / Cmd+Enter to send)
 * - Character counter
 * - Loading/streaming states
 * - Stop generation button
 * - Responsive
 */
export function Composer({
  value,
  onChange,
  onSend,
  onStop,
  isLoading = false,
  isStreaming = false,
  disabled = false,
  placeholder = "Type your message...",
  className,
}: ComposerProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const minHeight = 44;
  const maxHeight = 200;

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    textarea.style.height = "auto";
    const scrollHeight = textarea.scrollHeight;
    textarea.style.height = `${Math.min(Math.max(scrollHeight, minHeight), maxHeight)}px`;
  }, [value, minHeight, maxHeight]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Send on Ctrl+Enter or Cmd+Enter
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      e.preventDefault();
      if (!disabled && !isLoading && value.trim()) {
        onSend();
      }
    }

    // Allow normal Enter for new line
    if (e.key === "Enter" && !e.ctrlKey && !e.metaKey) {
      return;
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    onChange(e.target.value);
  };

  const isSendDisabled = disabled || isLoading || !value.trim();

  return (
    <div className={cn("flex flex-col gap-2", className)}>
      {/* Input Container */}
      <div className="flex gap-2 items-end rounded-lg border border-border bg-background p-3 focus-within:border-primary/50 transition-colors">
        {/* Textarea */}
        <textarea
          ref={textareaRef}
          value={value}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled || isLoading}
          rows={1}
          className={cn(
            "flex-1 resize-none bg-transparent text-foreground placeholder:text-muted-foreground",
            "outline-none text-sm leading-relaxed",
            "max-h-[200px] overflow-y-auto",
            (disabled || isLoading) && "opacity-50 cursor-not-allowed"
          )}
          aria-label="Message input"
        />

        {/* Action Buttons */}
        <div className="flex gap-1 flex-shrink-0">
          {isStreaming && onStop ? (
            // Stop Generation Button
            <button
              onClick={onStop}
              className={cn(
                "p-2 rounded-md hover:bg-muted transition-colors",
                "text-destructive hover:text-destructive/80",
                "flex items-center justify-center"
              )}
              title="Stop generation (Esc)"
              aria-label="Stop generation"
            >
              <Square className="h-4 w-4 fill-current" />
            </button>
          ) : (
            // Send Button
            <button
              onClick={onSend}
              disabled={isSendDisabled}
              className={cn(
                "p-2 rounded-md transition-colors",
                "flex items-center justify-center",
                isSendDisabled
                  ? "text-muted-foreground/50 cursor-not-allowed"
                  : "text-primary hover:bg-primary/10"
              )}
              title="Send message (Ctrl+Enter)"
              aria-label="Send message"
            >
              {isLoading ? (
                <LoadingSpinner className="h-4 w-4" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </button>
          )}
        </div>
      </div>

      {/* Help Text */}
      <div className="flex items-center justify-between px-3 text-xs text-muted-foreground">
        <span>
          {isStreaming && "AI is responding..."}
          {isLoading && !isStreaming && "Sending..."}
          {!isLoading && !isStreaming && "Press Ctrl+Enter to send"}
        </span>
        {value.length > 0 && (
          <span className={cn(value.length > 2000 && "text-destructive")}>
            {value.length}/2000
          </span>
        )}
      </div>
    </div>
  );
}

/**
 * Loading Spinner for Send Button
 */
function LoadingSpinner({ className }: { className?: string }) {
  return (
    <div className={cn("animate-spin", className)}>
      <svg
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        className="h-full w-full"
      >
        <circle
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          strokeWidth="2"
          opacity="0.3"
        />
        <path
          d="M12 2a10 10 0 0110 10"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
        />
      </svg>
    </div>
  );
}
