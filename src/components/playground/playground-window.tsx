"use client";

import { MessageBubble } from "@/components/chat/message-bubble";
import { Redo2, Copy } from "lucide-react";
import type { Message } from "@/types";

interface PlaygroundWindowProps {
  messages: Message[];
  streamingContent: string;
  isStreaming: boolean;
  onRegenerate: () => void;
  onCopyMessage: (content: string) => void;
}

export function PlaygroundWindow({
  messages,
  streamingContent,
  isStreaming,
  onRegenerate,
  onCopyMessage,
}: PlaygroundWindowProps) {
  return (
    <div className="flex-1 overflow-y-auto space-y-4 p-6 bg-gray-50">
      {/* Empty state */}
      {messages.length === 0 && !streamingContent && (
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <p className="text-gray-500 text-lg">No messages yet</p>
            <p className="text-gray-400 text-sm mt-2">Send a message to start the conversation</p>
          </div>
        </div>
      )}

      {/* Messages */}
      {messages.map((message) => (
        <div key={message.id} className="relative group">
          <MessageBubble
            content={message.content}
            isUser={message.role === "user"}
            isLoading={false}
          />
          {message.role === "assistant" && (
            <div className="flex items-center gap-2 mt-2 ml-12 opacity-0 group-hover:opacity-100 transition-opacity">
              <button
                onClick={() => onCopyMessage(message.content)}
                className="p-1.5 hover:bg-gray-200 rounded transition-colors"
                title="Copy message"
              >
                <Copy className="w-4 h-4 text-gray-600" />
              </button>
            </div>
          )}
        </div>
      ))}

      {/* Streaming content */}
      {streamingContent && (
        <div className="relative group">
          <MessageBubble
            content={streamingContent}
            isUser={false}
            isStreaming={isStreaming}
            isLoading={isStreaming}
          />
          {!isStreaming && (
            <div className="flex items-center gap-2 mt-2 ml-12 opacity-0 group-hover:opacity-100 transition-opacity">
              <button
                onClick={() => onCopyMessage(streamingContent)}
                className="p-1.5 hover:bg-gray-200 rounded transition-colors"
                title="Copy message"
              >
                <Copy className="w-4 h-4 text-gray-600" />
              </button>
              <button
                onClick={onRegenerate}
                className="p-1.5 hover:bg-gray-200 rounded transition-colors"
                title="Regenerate response"
              >
                <Redo2 className="w-4 h-4 text-gray-600" />
              </button>
            </div>
          )}
        </div>
      )}

      {/* Streaming indicator */}
      {isStreaming && !streamingContent && (
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <div className="animate-spin rounded-full h-4 w-4 border-2 border-blue-600 border-t-transparent"></div>
          <span>Generating response...</span>
        </div>
      )}
    </div>
  );
}
