import { apiClient } from "@/services/api-client";
import { API_BASE_URL, API_ENDPOINTS } from "@/constants";
import type { ApiResponse, Conversation, Message, ChatCompletionResponse, StreamEvent } from "@/types";

/**
 * Conversation Service
 * Handles all conversation and message API operations
 */

export const conversationService = {
  /**
   * List all conversations
   */
  async listConversations(): Promise<ApiResponse<Conversation[]>> {
    return apiClient.get(API_ENDPOINTS.CONVERSATIONS.LIST);
  },

  /**
   * Create a new conversation
   */
  async createConversation(title?: string, metadata?: Record<string, unknown>): Promise<ApiResponse<Conversation>> {
    return apiClient.post(API_ENDPOINTS.CONVERSATIONS.CREATE, {
      title,
      metadata: metadata || {},
    });
  },

  /**
   * Get a conversation by ID
   */
  async getConversation(conversationId: string): Promise<ApiResponse<Conversation>> {
    return apiClient.get(API_ENDPOINTS.CONVERSATIONS.GET(conversationId));
  },

  /**
   * Update a conversation
   */
  async updateConversation(
    conversationId: string,
    updates: { title?: string; metadata?: Record<string, unknown> }
  ): Promise<ApiResponse<Conversation>> {
    return apiClient.patch(API_ENDPOINTS.CONVERSATIONS.UPDATE(conversationId), updates);
  },

  /**
   * Delete a conversation
   */
  async deleteConversation(conversationId: string): Promise<ApiResponse<void>> {
    return apiClient.delete(API_ENDPOINTS.CONVERSATIONS.DELETE(conversationId));
  },

  /**
   * List messages in a conversation
   */
  async listMessages(conversationId: string): Promise<ApiResponse<Message[]>> {
    return apiClient.get(API_ENDPOINTS.CONVERSATIONS.MESSAGES(conversationId));
  },

  /**
   * Send a message and get a non-streaming completion
   */
  async sendMessage(
    conversationId: string,
    message: string,
    useRag: boolean = true,
    agentId?: string
  ): Promise<ApiResponse<ChatCompletionResponse>> {
    return apiClient.post(`${API_ENDPOINTS.CONVERSATIONS.CHAT(conversationId)}`, {
      conversation_id: conversationId,
      message,
      use_rag: useRag,
      stream: false,
      agent_id: agentId,
      metadata: {},
    });
  },

  /**
   * Stream a message completion using Server-Sent Events
   */
  async streamMessage(
    conversationId: string,
    message: string,
    useRag: boolean = true,
    onEvent?: (event: StreamEvent) => void,
    agentId?: string,
    onOpen?: (eventSource: EventSource) => void
  ): Promise<void> {
    return new Promise((resolve, reject) => {
      const streamUrl = `${API_BASE_URL}${API_ENDPOINTS.CONVERSATIONS.CHAT(conversationId)}/stream?message=${encodeURIComponent(
        message
      )}&use_rag=${useRag}${agentId ? `&agent_id=${encodeURIComponent(agentId)}` : ""}`;
      const eventSource = new EventSource(streamUrl);
      console.log(`[FRONTEND TRACE] 🟢 EventSource created for: ${streamUrl}`);
      // Hand the live connection to the caller immediately so it can be closed on demand
      // (Stop button) or on component unmount — closing it here only happens on end/error.
      onOpen?.(eventSource);

      // Handle start event
      eventSource.addEventListener("start", (event: Event) => {
        try {
          const messageEvent = event as MessageEvent;
          const data = JSON.parse(messageEvent.data);
          console.log(`[FRONTEND TRACE] 🟢 STAGE 1: EventSource receives START - message_id=${data.message_id}`);
          if (onEvent) {
            onEvent({ event: "start", message_id: data.message_id });
          }
        } catch (error) {
          eventSource.close();
          reject(error);
        }
      });

      // Handle token events (plain text, not JSON)
      eventSource.addEventListener("token", (event: Event) => {
        try {
          const messageEvent = event as MessageEvent;
          console.log(`[FRONTEND TRACE] 🟢 STAGE 2: EventSource receives TOKEN - data=${JSON.stringify(messageEvent.data.substring(0, 20))}...`);
          if (onEvent) {
            onEvent({ event: "token", data: messageEvent.data });
          }
        } catch (error) {
          eventSource.close();
          reject(error);
        }
      });

      // Handle end event
      eventSource.addEventListener("end", (event: Event) => {
        try {
          const messageEvent = event as MessageEvent;
          const data = JSON.parse(messageEvent.data);
          console.log(`[FRONTEND TRACE] 🟢 STAGE 4: EventSource receives END - message_id=${data.message_id}`);
          if (onEvent) {
            onEvent({ event: "end", message_id: data.message_id });
          }
          eventSource.close();
          resolve();
        } catch (error) {
          eventSource.close();
          reject(error);
        }
      });

      // Handle error events
      eventSource.addEventListener("error", (event: Event) => {
        try {
          const messageEvent = event as MessageEvent;
          console.log(`[FRONTEND TRACE] 🔴 EventSource receives ERROR - data=${messageEvent.data}`);
          if (onEvent) {
            onEvent({ event: "error", data: messageEvent.data });
          }
          eventSource.close();
          resolve();
        } catch (error) {
          eventSource.close();
          reject(error);
        }
      });

      eventSource.onerror = () => {
        console.log(`[FRONTEND TRACE] 🔴 EventSource connection error`);
        eventSource.close();
        reject(new Error("Streaming connection error"));
      };
    });
  },
};
