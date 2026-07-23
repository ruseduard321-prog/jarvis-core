"use client";

import { useRef, useEffect, useState } from "react";
import { Send, Square, ChevronDown } from "lucide-react";

interface PlaygroundComposerProps {
  userMessage: string;
  onUserMessageChange: (message: string) => void;
  systemPrompt: string;
  onSystemPromptChange: (prompt: string) => void;
  temperature: number;
  onTemperatureChange: (temp: number) => void;
  maxTokens: number;
  onMaxTokensChange: (tokens: number) => void;
  onSend: () => void;
  onStop: () => void;
  isStreaming: boolean;
  disabled: boolean;
}

export function PlaygroundComposer({
  userMessage,
  onUserMessageChange,
  systemPrompt,
  onSystemPromptChange,
  temperature,
  onTemperatureChange,
  maxTokens,
  onMaxTokensChange,
  onSend,
  onStop,
  isStreaming,
  disabled,
}: PlaygroundComposerProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [showSettings, setShowSettings] = useState(true);
  const minHeight = 44;
  const maxHeight = 200;

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    textarea.style.height = "auto";
    const scrollHeight = textarea.scrollHeight;
    textarea.style.height = `${Math.min(Math.max(scrollHeight, minHeight), maxHeight)}px`;
  }, [userMessage]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      e.preventDefault();
      if (!disabled && !isStreaming && userMessage.trim()) {
        onSend();
      }
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    onUserMessageChange(e.target.value);
  };

  const handleSystemPromptChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    onSystemPromptChange(e.target.value);
  };

  const isSendDisabled = disabled || isStreaming || !userMessage.trim();

  return (
    <div className="border-t bg-white p-4 space-y-3">
      {/* Settings Toggle */}
      <button
        onClick={() => setShowSettings(!showSettings)}
        className="flex items-center gap-2 text-sm font-medium text-gray-700 hover:text-gray-900"
      >
        <ChevronDown className={`w-4 h-4 transition-transform ${showSettings ? "rotate-180" : ""}`} />
        Playground Settings
      </button>

      {/* Settings Panel */}
      {showSettings && (
        <div className="bg-gray-50 p-4 rounded-lg space-y-4 border">
          {/* System Prompt */}
          <div>
            <label htmlFor="system-prompt" className="block text-sm font-medium text-gray-700 mb-1">
              System Prompt
            </label>
            <textarea
              id="system-prompt"
              value={systemPrompt}
              onChange={handleSystemPromptChange}
              placeholder="You are a helpful AI assistant..."
              rows={2}
              className="w-full px-3 py-2 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              disabled={disabled}
            />
          </div>

          {/* Temperature */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label htmlFor="temperature" className="text-sm font-medium text-gray-700">
                Temperature
              </label>
              <span className="text-sm font-mono bg-gray-200 px-2 py-1 rounded">{temperature.toFixed(2)}</span>
            </div>
            <input
              id="temperature"
              type="range"
              min="0"
              max="2"
              step="0.1"
              value={temperature}
              onChange={(e) => onTemperatureChange(parseFloat(e.target.value))}
              className="w-full"
              disabled={disabled}
            />
            <p className="text-xs text-gray-500 mt-1">Lower = deterministic, Higher = creative</p>
          </div>

          {/* Max Tokens */}
          <div>
            <label htmlFor="max-tokens" className="block text-sm font-medium text-gray-700 mb-1">
              Max Tokens
            </label>
            <div className="flex items-center gap-2">
              <input
                id="max-tokens"
                type="number"
                min="100"
                max="4000"
                step="50"
                value={maxTokens}
                onChange={(e) => onMaxTokensChange(parseInt(e.target.value))}
                className="flex-1 px-3 py-2 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={disabled}
              />
              <span className="text-sm text-gray-500">(100-4000)</span>
            </div>
          </div>
        </div>
      )}

      {/* Message Input */}
      <div className="flex gap-2 items-end rounded-lg border border-border bg-background p-3 focus-within:border-primary/50 transition-colors">
        {/* Textarea */}
        <textarea
          ref={textareaRef}
          value={userMessage}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          placeholder="Type your message... (Ctrl+Enter to send)"
          disabled={disabled || isStreaming}
          rows={1}
          className="flex-1 resize-none bg-transparent text-foreground placeholder:text-muted-foreground outline-none text-sm leading-relaxed max-h-[200px] overflow-y-auto disabled:opacity-50 disabled:cursor-not-allowed"
          aria-label="Message input"
        />

        {/* Action Buttons */}
        <div className="flex gap-1 flex-shrink-0">
          {isStreaming ? (
            <button
              onClick={onStop}
              className="p-2 bg-red-100 text-red-600 hover:bg-red-200 rounded transition-colors"
              title="Stop generation"
            >
              <Square className="w-5 h-5" />
            </button>
          ) : (
            <button
              onClick={onSend}
              disabled={isSendDisabled}
              className="p-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              title="Send message (Ctrl+Enter)"
            >
              <Send className="w-5 h-5" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
