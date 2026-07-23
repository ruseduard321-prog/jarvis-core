"use client";

import React, { useEffect, useCallback, useRef } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useConversationStore } from "@/store";
import { useConversations, useCreateConversation, conversationKeys } from "@/hooks/use-chat-queries";
import { conversationService } from "@/services/conversation-service";
import { ChatWindow, ConversationSidebar, Composer } from "@/components/chat";
import type { StreamEvent, Message } from "@/types";

/**
 * Main Chat Page Component
 * Orchestrates:
 * - Conversation selection and creation
 * - Message display and streaming
 * - Composer interaction
 * - Real-time updates
 */
export function ChatPage() {
  const {
    currentConversationId,
    setCurrentConversationId,
    draftMessage,
    setDraftMessage,
    isStreaming,
    setIsStreaming,
    setStreamingMessageId,
  } = useConversationStore();

  const queryClient = useQueryClient();
  const createConversationMutation = useCreateConversation();
  const { data: conversations } = useConversations();

  const [streamingContent, setStreamingContent] = React.useState("");
  const [error, setError] = React.useState<string | null>(null);
  const [isSending, setIsSending] = React.useState(false);
  const [optimisticUserMessage, setOptimisticUserMessage] = React.useState<Message | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  // Ensure the SSE connection is closed if the component unmounts mid-stream.
  useEffect(() => {
    return () => {
      eventSourceRef.current?.close();
      eventSourceRef.current = null;
    };
  }, []);

  // Create a new conversation
  const handleNewConversation = useCallback(async () => {
    try {
      const newConversation = await createConversationMutation.mutateAsync({
        title: "New Conversation",
      });
      setCurrentConversationId(newConversation.id);
      setDraftMessage("");
      setStreamingContent("");
      setError(null);
    } catch {
      setError("Failed to create conversation");
    }
  }, [createConversationMutation, setCurrentConversationId, setDraftMessage]);

  // Select a conversation
  const handleSelectConversation = useCallback(
    (conversationId: string) => {
      setCurrentConversationId(conversationId);
      setDraftMessage("");
      setStreamingContent("");
      setError(null);
      setStreamingMessageId(null);
    },
    [setCurrentConversationId, setDraftMessage, setStreamingMessageId]
  );

  // Handle message sending
  const handleSendMessage = useCallback(async () => {
    if (!currentConversationId || !draftMessage.trim()) return;

    setIsSending(true);
    setError(null);
    setStreamingContent("");
    setOptimisticUserMessage(null);

    try {
      // Add optimistic user message immediately
      const optimisticMessage: Message = {
        id: `optimistic-${Date.now()}`,
        conversation_id: currentConversationId,
        role: "user",
        content: draftMessage,
        created_at: new Date().toISOString(),
        metadata: {},
      };
      setOptimisticUserMessage(optimisticMessage);
      setDraftMessage("");

      // Start streaming
      setIsStreaming(true);
      let messageId: string | null = null;
      let fullContent = "";

      await conversationService.streamMessage(
        currentConversationId,
        draftMessage,
        true,
        (event: StreamEvent) => {
          console.log(`[FRONTEND TRACE] 🟢 STAGE 3: handleSendMessage callback received event=${event.event}`);
          switch (event.event) {
            case "start":
              messageId = event.message_id || null;
              setStreamingMessageId(messageId);
              console.log(`[FRONTEND TRACE] 🟢 STAGE 3a: START - messageId set to ${messageId}`);
              break;
            case "token":
              fullContent += event.data || "";
              console.log(`[FRONTEND TRACE] 🟢 STAGE 3b: TOKEN - accumulating, length now=${fullContent.length}`);
              setStreamingContent(fullContent);
              break;
            case "end":
              console.log(`[FRONTEND TRACE] 🟢 STAGE 3c: END - setIsStreaming(false)`);
              setIsStreaming(false);
              break;
            case "error":
              console.log(`[FRONTEND TRACE] 🔴 STAGE 3d: ERROR - ${event.data}`);
              setError(event.data || "Streaming error");
              setIsStreaming(false);
              // The failure may mean the backend no longer recognizes this conversation
              // (e.g. it restarted). Refresh the authoritative list so the reconciliation
              // effect can detect and clear a stale selection.
              queryClient.invalidateQueries({ queryKey: conversationKeys.list() });
              break;
          }
        },
        undefined,
        (es) => {
          eventSourceRef.current = es;
        }
      );
      eventSourceRef.current = null;

      // Invalidate and refetch messages to replace optimistic messages with real ones
      if (currentConversationId) {
        console.log(`[FRONTEND TRACE] 🟢 STAGE 5: invalidateQueries() executing for query=["conversations", "messages", "${currentConversationId}"]`);
        await queryClient.invalidateQueries({
          queryKey: ["conversations", "messages", currentConversationId],
        });
        console.log(`[FRONTEND TRACE] 🟢 STAGE 5: invalidateQueries() completed`);
      }

      setStreamingContent("");
      setStreamingMessageId(null);
      setOptimisticUserMessage(null);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to send message";
      setError(message);
      setIsStreaming(false);
      setStreamingContent("");
      setOptimisticUserMessage(null);
      // Same reconciliation trigger as the in-stream error case above.
      queryClient.invalidateQueries({ queryKey: conversationKeys.list() });
    } finally {
      setIsSending(false);
    }
  }, [currentConversationId, draftMessage, setIsStreaming, setStreamingMessageId, setDraftMessage, queryClient]);

  // Handle stop generation
  const handleStopGeneration = useCallback(() => {
    eventSourceRef.current?.close();
    eventSourceRef.current = null;
    setIsStreaming(false);
    setStreamingContent("");
    setStreamingMessageId(null);
  }, [setIsStreaming, setStreamingMessageId]);

  // Handle retry
  const handleRetry = useCallback(() => {
    setError(null);
    if (draftMessage.trim()) {
      handleSendMessage();
    }
  }, [draftMessage, handleSendMessage]);

  // Reconcile the selected conversation against the backend's authoritative list. The
  // backend's conversation store does not persist across restarts, so a conversation_id
  // held in this tab (e.g. from before a restart) can stop existing server-side. Once the
  // list has loaded, clear a selection that isn't in it so the effect below can recover.
  useEffect(() => {
    if (
      currentConversationId &&
      conversations &&
      !conversations.some((conversation) => conversation.id === currentConversationId)
    ) {
      setCurrentConversationId(null);
    }
  }, [currentConversationId, conversations, setCurrentConversationId]);

  // Create initial conversation on first load (also reached after the reconciliation
  // effect above clears a stale id, restoring the "always have a valid conversation" invariant).
  useEffect(() => {
    if (!currentConversationId && !createConversationMutation.isPending) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      handleNewConversation();
    }
  }, [currentConversationId, handleNewConversation, createConversationMutation.isPending]);

  return (
    <div className="flex h-screen w-full bg-background">
      {/* Sidebar */}
      <div className="hidden md:flex w-64 flex-col border-r border-border">
        <ConversationSidebar
          currentConversationId={currentConversationId}
          onSelectConversation={handleSelectConversation}
          onNewConversation={handleNewConversation}
        />
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col min-h-0">
        {/* Messages */}
        <ChatWindow
          conversationId={currentConversationId}
          isStreaming={isStreaming}
          streamingContent={streamingContent}
          optimisticUserMessage={optimisticUserMessage}
          error={error}
          onRetry={handleRetry}
          className="flex-1"
        />

        {/* Composer */}
        <div className="border-t border-border p-4 bg-background">
          <div className="max-w-4xl mx-auto">
            <Composer
              value={draftMessage}
              onChange={setDraftMessage}
              onSend={handleSendMessage}
              onStop={handleStopGeneration}
              isLoading={isSending}
              isStreaming={isStreaming}
              disabled={!currentConversationId || createConversationMutation.isPending}
              placeholder="Type your message (Ctrl+Enter to send)..."
            />
          </div>
        </div>
      </div>

      {/* Mobile Sidebar (overlay) */}
      {/* Add mobile drawer implementation here */}
    </div>
  );
}
