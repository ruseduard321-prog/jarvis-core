import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { conversationService } from "@/services/conversation-service";
import type { Conversation } from "@/types";

/**
 * React Query Hooks for Chat Operations
 */

// Query Keys
export const conversationKeys = {
  all: ["conversations"] as const,
  lists: () => [...conversationKeys.all, "list"] as const,
  list: () => [...conversationKeys.lists()] as const,
  details: () => [...conversationKeys.all, "detail"] as const,
  detail: (id: string) => [...conversationKeys.details(), id] as const,
  messages: () => [...conversationKeys.all, "messages"] as const,
  messageList: (conversationId: string) => [...conversationKeys.messages(), conversationId] as const,
};

/**
 * Hook to get list of conversations
 */
export function useConversations() {
  return useQuery({
    queryKey: conversationKeys.list(),
    queryFn: async () => {
      const response = await conversationService.listConversations();
      if (response.status !== 200 || !response.data) {
        throw new Error(response.error || "Failed to fetch conversations");
      }
      return response.data;
    },
  });
}

/**
 * Hook to get a single conversation
 */
export function useConversation(conversationId: string | null) {
  return useQuery({
    queryKey: conversationId ? conversationKeys.detail(conversationId) : [],
    queryFn: async () => {
      if (!conversationId) throw new Error("No conversation ID");
      const response = await conversationService.getConversation(conversationId);
      if (response.status !== 200 || !response.data) {
        throw new Error(response.error || "Failed to fetch conversation");
      }
      return response.data;
    },
    enabled: !!conversationId,
  });
}

/**
 * Hook to get messages in a conversation
 */
export function useMessages(conversationId: string | null) {
  return useQuery({
    queryKey: conversationId ? conversationKeys.messageList(conversationId) : [],
    queryFn: async () => {
      if (!conversationId) throw new Error("No conversation ID");
      console.log(`[FRONTEND TRACE] 🟢 STAGE 6: React Query queryFn executing - fetching messages for ${conversationId}`);
      const response = await conversationService.listMessages(conversationId);
      if (response.status !== 200 || !response.data) {
        throw new Error(response.error || "Failed to fetch messages");
      }
      console.log(`[FRONTEND TRACE] 🟢 STAGE 6: React Query received ${response.data.length} messages from server`);
      return response.data;
    },
    enabled: !!conversationId,
  });
}

/**
 * Hook to create a new conversation
 */
export function useCreateConversation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (params: { title?: string; metadata?: Record<string, unknown> }) => {
      const response = await conversationService.createConversation(params.title, params.metadata);
      if (response.status !== 201 && response.status !== 200 || !response.data) {
        throw new Error(response.error || "Failed to create conversation");
      }
      return response.data;
    },
    onSuccess: (data) => {
      // Write the new conversation into the list cache directly (rather than only
      // invalidating) so callers that reconcile currentConversationId against the list
      // immediately after creation see it as present, with no refetch race.
      queryClient.setQueryData<Conversation[]>(conversationKeys.list(), (old) =>
        old ? [data, ...old] : [data]
      );
    },
  });
}

/**
 * Hook to update a conversation
 */
export function useUpdateConversation(conversationId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (updates: { title?: string; metadata?: Record<string, unknown> }) => {
      const response = await conversationService.updateConversation(conversationId, updates);
      if (response.status !== 200 || !response.data) {
        throw new Error(response.error || "Failed to update conversation");
      }
      return response.data;
    },
    onSuccess: (data) => {
      // Update conversation detail cache
      queryClient.setQueryData(conversationKeys.detail(conversationId), data);
      // Invalidate list to refresh
      queryClient.invalidateQueries({ queryKey: conversationKeys.list() });
    },
  });
}

/**
 * Hook to delete a conversation
 */
export function useDeleteConversation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (conversationId: string) => {
      const response = await conversationService.deleteConversation(conversationId);
      if (response.status !== 204 && response.status !== 200) {
        throw new Error(response.error || "Failed to delete conversation");
      }
    },
    onSuccess: (_, conversationId) => {
      // Remove from cache
      queryClient.removeQueries({ queryKey: conversationKeys.detail(conversationId) });
      queryClient.removeQueries({ queryKey: conversationKeys.messageList(conversationId) });
      // Invalidate list
      queryClient.invalidateQueries({ queryKey: conversationKeys.list() });
    },
  });
}

/**
 * Hook to send a message (non-streaming)
 */
export function useSendMessage(conversationId: string | null) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (params: { message: string; useRag?: boolean; agentId?: string }) => {
      if (!conversationId) throw new Error("No conversation ID");
      const response = await conversationService.sendMessage(
        conversationId,
        params.message,
        params.useRag ?? true,
        params.agentId
      );
      if (response.status !== 200 || !response.data) {
        throw new Error(response.error || "Failed to send message");
      }
      return response.data;
    },
    onSuccess: () => {
      // Invalidate messages to fetch updated list
      if (conversationId) {
        queryClient.invalidateQueries({ queryKey: conversationKeys.messageList(conversationId) });
      }
    },
  });
}
