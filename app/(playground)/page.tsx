"use client";

import { useState, useCallback, useRef } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { conversationService } from "@/services/conversation-service";
import { useConversations, useMessages, useCreateConversation } from "@/hooks/use-chat-queries";
import { PlaygroundWindow } from "@/components/playground/playground-window";
import { PlaygroundComposer } from "@/components/playground/playground-composer";
import { PlaygroundControls } from "@/components/playground/playground-controls";
import { Plus, ChevronDown } from "lucide-react";

export default function Page() {
  // State declarations first
  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(null);
  const [showConversationDropdown, setShowConversationDropdown] = useState(false);

  // Settings state
  const [systemPrompt, setSystemPrompt] = useState("You are a helpful AI assistant.");
  const [temperature, setTemperature] = useState(0.7);
  const [maxTokens, setMaxTokens] = useState(2000);

  // Composer state
  const [draftMessage, setDraftMessage] = useState("");

  // Streaming state (reuse pattern)
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");

  // Regenerate state
  const [lastUserMessageContent, setLastUserMessageContent] = useState<string | null>(null);

  // EventSource ref for stopping
  const eventSourceRef = useRef<EventSource | null>(null);

  // Conversation queries (now have access to state variables)
  const { data: conversations = [] } = useConversations();
  const { data: messages = [] } = useMessages(selectedConversationId);
  const createConversationMutation = useCreateConversation();
  const queryClient = useQueryClient();

  // Auto-select first conversation
  if (!selectedConversationId && conversations.length > 0 && !selectedConversationId) {
    setSelectedConversationId(conversations[0].id);
  }

  // Handle create new conversation
  const handleNewConversation = useCallback(async () => {
    try {
      const newConv = await createConversationMutation.mutateAsync({
        title: `Playground ${new Date().toLocaleTimeString()}`,
      });
      setSelectedConversationId(newConv.id);
      setDraftMessage("");
      setStreamingContent("");
      setShowConversationDropdown(false);
    } catch (error) {
      console.error("Failed to create conversation", error);
    }
  }, [createConversationMutation]);

  // Handle send message
  const handleSendMessage = useCallback(async () => {
    if (!selectedConversationId || !draftMessage.trim()) return;

    setIsStreaming(true);
    setStreamingContent("");
    const userMessageContent = draftMessage;
    setDraftMessage("");

    try {
      let accumulatedContent = "";

      // Use streamMessage with custom parameters
      await conversationService.streamMessage(
        selectedConversationId,
        userMessageContent,
        false, // use_rag = false for playground
        (event) => {
          switch (event.event) {
            case "start":
              break;
            case "token":
              accumulatedContent += event.data || "";
              setStreamingContent(accumulatedContent);
              break;
            case "end":
              setIsStreaming(false);
              queryClient.invalidateQueries({ queryKey: ["conversations", selectedConversationId, "messages"] });
              setLastUserMessageContent(userMessageContent);
              break;
            case "error":
              console.error("Stream error:", event.data);
              setIsStreaming(false);
              break;
          }
        }
      );

      // Close EventSource if still open
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
    } catch (error) {
      console.error("Failed to send message", error);
      setIsStreaming(false);
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
    }
  }, [selectedConversationId, draftMessage, queryClient]);

  // Handle regenerate (resend last user message with current settings)
  const handleRegenerate = useCallback(async () => {
    if (!lastUserMessageContent || !selectedConversationId) return;
    setDraftMessage(lastUserMessageContent);
    // Manually trigger send
    setIsStreaming(true);
    setStreamingContent("");

    try {
      let accumulatedContent = "";

      await conversationService.streamMessage(
        selectedConversationId,
        lastUserMessageContent,
        false,
        (event) => {
          switch (event.event) {
            case "start":
              break;
            case "token":
              accumulatedContent += event.data || "";
              setStreamingContent(accumulatedContent);
              break;
            case "end":
              setIsStreaming(false);
              setDraftMessage("");
              queryClient.invalidateQueries({ queryKey: ["conversations", selectedConversationId, "messages"] });
              break;
            case "error":
              console.error("Stream error:", event.data);
              setIsStreaming(false);
              break;
          }
        }
      );

      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
    } catch (error) {
      console.error("Failed to regenerate message", error);
      setIsStreaming(false);
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
    }
  }, [lastUserMessageContent, selectedConversationId, queryClient]);

  // Handle stop generation
  const handleStop = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    setIsStreaming(false);
  }, []);

  // Handle copy message
  const handleCopyMessage = useCallback((content: string) => {
    navigator.clipboard.writeText(content);
  }, []);

  // Handle clear conversation (create new one instead of deleting)
  const handleClearConversation = useCallback(async () => {
    try {
      const newConv = await createConversationMutation.mutateAsync({
        title: `Playground ${new Date().toLocaleTimeString()}`,
      });
      setSelectedConversationId(newConv.id);
      setStreamingContent("");
      setDraftMessage("");
    } catch (error) {
      console.error("Failed to clear conversation", error);
    }
  }, [createConversationMutation]);

  return (
    <div className="flex flex-col h-screen bg-background">
      {/* Header */}
      <div className="border-b bg-white/50 backdrop-blur supports-[backdrop-filter]:bg-white/30 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">AI Playground</h1>
            <p className="text-sm text-gray-600 mt-1">Experiment with prompts, temperature, and tokens</p>
          </div>

          {/* Conversation Dropdown */}
          <div className="relative">
            <button
              onClick={() => setShowConversationDropdown(!showConversationDropdown)}
              className="flex items-center gap-2 px-4 py-2 border rounded-lg hover:bg-gray-50 transition-colors"
            >
              <span className="text-sm font-medium">
                {conversations.find((c) => c.id === selectedConversationId)?.title || "Select Conversation"}
              </span>
              <ChevronDown className="w-4 h-4" />
            </button>

            {showConversationDropdown && (
              <div className="absolute right-0 mt-2 w-64 bg-white border rounded-lg shadow-lg z-50">
                <div className="max-h-64 overflow-y-auto">
                  {conversations.map((conv) => (
                    <button
                      key={conv.id}
                      onClick={() => {
                        setSelectedConversationId(conv.id);
                        setShowConversationDropdown(false);
                        setStreamingContent("");
                      }}
                      className={`w-full text-left px-4 py-2 hover:bg-gray-100 transition-colors ${
                        selectedConversationId === conv.id ? "bg-blue-50 text-blue-700" : ""
                      }`}
                    >
                      <div className="text-sm font-medium truncate">{conv.title}</div>
                      <div className="text-xs text-gray-500">
                        {new Date(conv.updated_at).toLocaleDateString()}
                      </div>
                    </button>
                  ))}
                </div>
                <div className="border-t p-2">
                  <button
                    onClick={handleNewConversation}
                    className="w-full flex items-center gap-2 px-4 py-2 text-sm font-medium text-blue-600 hover:bg-blue-50 rounded transition-colors"
                  >
                    <Plus className="w-4 h-4" />
                    New Conversation
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Messages Window */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <PlaygroundWindow
            messages={messages}
            streamingContent={streamingContent}
            isStreaming={isStreaming}
            onRegenerate={handleRegenerate}
            onCopyMessage={handleCopyMessage}
          />

          {/* Composer + Settings */}
          <PlaygroundComposer
            userMessage={draftMessage}
            onUserMessageChange={setDraftMessage}
            systemPrompt={systemPrompt}
            onSystemPromptChange={setSystemPrompt}
            temperature={temperature}
            onTemperatureChange={setTemperature}
            maxTokens={maxTokens}
            onMaxTokensChange={setMaxTokens}
            onSend={handleSendMessage}
            onStop={handleStop}
            isStreaming={isStreaming}
            disabled={!selectedConversationId}
          />
        </div>
      </div>

      {/* Footer */}
      <div className="border-t bg-white/50 px-6 py-3">
        <PlaygroundControls
          onClearConversation={handleClearConversation}
          isDisabled={!selectedConversationId}
        />
      </div>
    </div>
  );
}
