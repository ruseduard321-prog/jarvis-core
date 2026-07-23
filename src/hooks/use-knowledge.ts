"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { knowledgeService } from "@/services/knowledge-service";
import type { KnowledgeListResponse, Document } from "@/types";

const KNOWLEDGE_QUERY_KEYS = {
  all: ["knowledge"] as const,
  lists: () => [...KNOWLEDGE_QUERY_KEYS.all, "list"] as const,
  list: () => [...KNOWLEDGE_QUERY_KEYS.lists()] as const,
  details: () => [...KNOWLEDGE_QUERY_KEYS.all, "detail"] as const,
  detail: (id: string) => [...KNOWLEDGE_QUERY_KEYS.details(), id] as const,
};

/**
 * Hook to fetch list of knowledge documents
 */
export function useKnowledgeList() {
  return useQuery({
    queryKey: KNOWLEDGE_QUERY_KEYS.list(),
    queryFn: async () => {
      const response = await knowledgeService.listDocuments();
      if (response.error) {
        throw new Error(response.error);
      }
      return response.data as KnowledgeListResponse;
    },
    refetchInterval: 30_000, // Auto-refetch every 30 seconds
    staleTime: 10_000, // Data stale after 10 seconds
    gcTime: 5 * 60_000, // Keep in cache for 5 minutes
  });
}

/**
 * Hook to fetch a single knowledge document
 */
export function useKnowledgeDetail(documentId: string) {
  return useQuery({
    queryKey: KNOWLEDGE_QUERY_KEYS.detail(documentId),
    queryFn: async () => {
      const response = await knowledgeService.getDocument(documentId);
      if (response.error) {
        throw new Error(response.error);
      }
      return response.data as Document;
    },
    staleTime: 10_000,
    gcTime: 5 * 60_000,
  });
}

/**
 * Hook to delete a knowledge document
 */
export function useKnowledgeDelete() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (documentId: string) => {
      const response = await knowledgeService.deleteDocument(documentId);
      if (response.error) {
        throw new Error(response.error);
      }
    },
    onSuccess: () => {
      // Invalidate the list query to refetch
      queryClient.invalidateQueries({ queryKey: KNOWLEDGE_QUERY_KEYS.list() });
    },
  });
}

/**
 * Hook to upload a knowledge document
 */
export function useKnowledgeUpload() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (params: {
      file: File;
      title?: string;
      namespace?: string;
      tags?: string[];
    }) => {
      const response = await knowledgeService.uploadDocument(params.file, params);
      if (response.error) {
        throw new Error(response.error);
      }
      return response.data;
    },
    onSuccess: () => {
      // Invalidate the list query to refetch
      queryClient.invalidateQueries({ queryKey: KNOWLEDGE_QUERY_KEYS.list() });
    },
  });
}
