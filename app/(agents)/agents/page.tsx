"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useConversationStore } from "@/store";
import { useCreateConversation } from "@/hooks/use-chat-queries";
import { useAgents } from "@/hooks/use-agent-queries";
import { conversationService } from "@/services/conversation-service";
import { ChatWindow, Composer, ConversationSidebar } from "@/components/chat";
import { AgentSelector } from "@/components/agents/agent-selector";
import type { Message, StreamEvent } from "@/types";

export default function AgentsPage() {
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
  const { data: agents = [], isLoading: isAgentsLoading } = useAgents();
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);
  const defaultAgentId =
    agents.find((agent) => agent.slug === "general")?.id ?? (agents.length > 0 ? agents[0].id : null);
  const activeAgentId = selectedAgentId ?? defaultAgentId;
  const [streamingContent, setStreamingContent] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSending, setIsSending] = useState(false);
  const [optimisticUserMessage, setOptimisticUserMessage] = useState<Message | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  // Ensure the SSE connection is closed if the component unmounts mid-stream.
  useEffect(() => {
    return () => {
      eventSourceRef.current?.close();
      eventSourceRef.current = null;
    };
  }, []);

  const handleNewConversation = useCallback(async () => {
    try {
      const newConversation = await createConversationMutation.mutateAsync({
        title: "Agent Session",
      });
      setCurrentConversationId(newConversation.id);
      setDraftMessage("");
      setStreamingContent("");
      setError(null);
    } catch {
      setError("Failed to create conversation");
    }
  }, [createConversationMutation, setCurrentConversationId, setDraftMessage]);

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

  const handleSendMessage = useCallback(async () => {
    if (!currentConversationId || !draftMessage.trim() || !activeAgentId) return;

    setIsSending(true);
    setError(null);
    setStreamingContent("");
    setOptimisticUserMessage(null);

    try {
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

      setIsStreaming(true);
      let messageId: string | null = null;
      let fullContent = "";

      await conversationService.streamMessage(
        currentConversationId,
        draftMessage,
        true,
        (event: StreamEvent) => {
          switch (event.event) {
            case "start":
              messageId = event.message_id || null;
              setStreamingMessageId(messageId);
              break;
            case "token":
              fullContent += event.data || "";
              setStreamingContent(fullContent);
              break;
            case "end":
              setIsStreaming(false);
              break;
            case "error":
              setError(event.data || "Streaming error");
              setIsStreaming(false);
              break;
          }
        },
        activeAgentId,
        (es) => {
          eventSourceRef.current = es;
        }
      );
      eventSourceRef.current = null;

      if (currentConversationId) {
        await queryClient.invalidateQueries({
          queryKey: ["conversations", "messages", currentConversationId],
        });
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
    } finally {
      setIsSending(false);
    }
  }, [
    currentConversationId,
    draftMessage,
    queryClient,
    activeAgentId,
    setDraftMessage,
    setIsStreaming,
    setStreamingMessageId,
  ]);

  const handleStopGeneration = useCallback(() => {
    eventSourceRef.current?.close();
    eventSourceRef.current = null;
    setIsStreaming(false);
    setStreamingContent("");
    setStreamingMessageId(null);
  }, [setIsStreaming, setStreamingMessageId]);

  const handleRetry = useCallback(() => {
    setError(null);
    if (draftMessage.trim()) {
      handleSendMessage();
    }
  }, [draftMessage, handleSendMessage]);

  useEffect(() => {
    if (!currentConversationId && !createConversationMutation.isPending) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      handleNewConversation();
    }
  }, [currentConversationId, handleNewConversation, createConversationMutation.isPending]);

  return (
    <div className="flex h-screen w-full bg-background">
      <div className="hidden md:flex w-64 flex-col border-r border-border">
        <ConversationSidebar
          currentConversationId={currentConversationId}
          onSelectConversation={handleSelectConversation}
          onNewConversation={handleNewConversation}
        />
      </div>

      <div className="flex-1 flex flex-col min-h-0">
        <AgentSelector
          agents={agents}
          selectedAgentId={activeAgentId}
          onSelectAgent={setSelectedAgentId}
          disabled={isAgentsLoading || isStreaming}
        />

        <ChatWindow
          conversationId={currentConversationId}
          isStreaming={isStreaming}
          streamingContent={streamingContent}
          optimisticUserMessage={optimisticUserMessage}
          error={error}
          onRetry={handleRetry}
          className="flex-1"
        />

        <div className="border-t border-border p-4 bg-background">
          <div className="max-w-4xl mx-auto">
            <Composer
              value={draftMessage}
              onChange={setDraftMessage}
              onSend={handleSendMessage}
              onStop={handleStopGeneration}
              isLoading={isSending}
              isStreaming={isStreaming}
              disabled={!currentConversationId || !activeAgentId || createConversationMutation.isPending}
              placeholder="Send a message to the selected agent..."
            />
          </div>
        </div>
      </div>
    </div>
  );
}
