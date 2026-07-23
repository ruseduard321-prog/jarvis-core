"use client";

import React, { useEffect, useRef } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { MessageCircle, ChevronDown } from "lucide-react";
import { cn } from "@/utils";
import { UserMessage, AssistantMessage, TypingIndicator, ErrorMessage } from "./message-bubble";
import { useMessages, conversationKeys } from "@/hooks/use-chat-queries";
import type { Message } from "@/types";

interface ChatWindowProps {
  conversationId: string | null;
  isStreaming?: boolean;
  streamingContent?: string;
  optimisticUserMessage?: Message | null;
  error?: string | null;
  onRetry?: () => void;
  className?: string;
}

/**
 * Chat Window Component
 * Displays message history with auto-scroll to bottom
 */
export function ChatWindow({
  conversationId,
  isStreaming = false,
  streamingContent = "",
  optimisticUserMessage = null,
  error,
  onRetry,
  className,
}: ChatWindowProps) {
  const { data: messages = [], isLoading, error: fetchError } = useMessages(conversationId);
  console.log(`[FRONTEND TRACE] 🟢 STAGE 7: ChatWindow render - messages.length=${messages.length}, isStreaming=${isStreaming}, streamingContent.length=${streamingContent.length}`);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [showScrollButton, setShowScrollButton] = React.useState(false);
  const queryClient = useQueryClient();

  // A failed message load may mean the backend no longer recognizes this conversation
  // (e.g. it restarted). Refresh the authoritative list so ChatPage's reconciliation
  // effect can detect and clear a stale selection.
  useEffect(() => {
    if (fetchError) {
      queryClient.invalidateQueries({ queryKey: conversationKeys.list() });
    }
  }, [fetchError, queryClient]);

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isStreaming, streamingContent]);

  // Track scroll position to show/hide scroll button
  const handleScroll = () => {
    if (!containerRef.current) return;
    const { scrollHeight, scrollTop, clientHeight } = containerRef.current;
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 100;
    setShowScrollButton(!isAtBottom);
  };

  if (!conversationId) {
    return (
      <div className={cn("flex-1 flex flex-col items-center justify-center gap-4 text-center", className)}>
        <MessageCircle className="h-12 w-12 text-muted-foreground/30" />
        <div>
          <h2 className="text-lg font-semibold text-foreground">No Conversation Selected</h2>
          <p className="text-sm text-muted-foreground mt-1">Start a new conversation or select one from the sidebar</p>
        </div>
      </div>
    );
  }

  return (
    <div className={cn("flex flex-col h-full", className)}>
      {/* Messages Container */}
      <div
        ref={containerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto"
        role="log"
        aria-live="polite"
        aria-label="Chat messages"
      >
        <div className="max-w-4xl mx-auto px-4 py-6">
          {/* Loading State */}
          {isLoading && messages.length === 0 && (
            <div className="flex items-center justify-center h-full">
              <div className="text-center space-y-4">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto" />
                <p className="text-muted-foreground text-sm">Loading conversation...</p>
              </div>
            </div>
          )}

          {/* Error State */}
          {(fetchError || error) && (
            <ErrorMessage error={fetchError ? "Failed to load messages" : error || "An error occurred"} onRetry={onRetry} />
          )}

          {/* Empty State */}
          {messages.length === 0 && !isLoading && !fetchError && !error && (
            <div className="flex flex-col items-center justify-center h-full gap-4 text-center">
              <MessageCircle className="h-12 w-12 text-muted-foreground/30" />
              <div>
                <h3 className="text-sm font-medium text-muted-foreground">Start the conversation</h3>
                <p className="text-xs text-muted-foreground mt-1">Send a message to begin</p>
              </div>
            </div>
          )}

          {/* Messages */}
          {messages.map((message: Message) => (
            <div key={message.id}>
              {message.role === "user" ? (
                <UserMessage
                  content={message.content}
                  timestamp={message.created_at}
                  showTimestamp={false}
                />
              ) : (
                <AssistantMessage
                  content={message.content}
                  timestamp={message.created_at}
                  showTimestamp={false}
                />
              )}
            </div>
          ))}

          {/* Optimistic User Message (appears before streaming) */}
          {optimisticUserMessage && (
            <div key={optimisticUserMessage.id}>
              <UserMessage
                content={optimisticUserMessage.content}
                timestamp={optimisticUserMessage.created_at}
                showTimestamp={false}
              />
            </div>
          )}

          {/* Streaming Message */}
          {isStreaming && streamingContent && (
            <>
              {console.log(`[FRONTEND TRACE] 🟢 STAGE 8: AssistantMessage rendering with streamingContent - length=${streamingContent.length}`)}
              <AssistantMessage content={streamingContent} isStreaming={true} showTimestamp={false} />
            </>
          )}

          {/* Typing Indicator */}
          {isStreaming && !streamingContent && <TypingIndicator />}

          {/* Scroll Anchor */}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Scroll to Bottom Button */}
      {showScrollButton && (
        <button
          onClick={scrollToBottom}
          className={cn(
            "absolute bottom-24 left-1/2 -translate-x-1/2 p-2 rounded-full",
            "bg-primary text-primary-foreground hover:bg-primary/90",
            "shadow-lg transition-opacity duration-200 z-10"
          )}
          title="Scroll to bottom"
          aria-label="Scroll to bottom"
        >
          <ChevronDown className="h-4 w-4" />
        </button>
      )}
    </div>
  );
}
