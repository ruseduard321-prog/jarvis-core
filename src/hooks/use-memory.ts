"use client";

import {
  useQuery,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";
import { memoryService, CreateMemoryRequest, UpdateMemoryRequest } from "@/services/memory-service";

const MEMORY_QUERY_KEYS = {
  all: ["memory"],
  lists: () => [...MEMORY_QUERY_KEYS.all, "list"],
  list: (limit: number, offset: number) => [
    ...MEMORY_QUERY_KEYS.lists(),
    limit,
    offset,
  ],
  details: () => [...MEMORY_QUERY_KEYS.all, "detail"],
  detail: (id: string) => [...MEMORY_QUERY_KEYS.details(), id],
};

/**
 * Hook to fetch list of memories with pagination
 */
export function useMemoryList(limit: number = 20, offset: number = 0) {
  return useQuery({
    queryKey: MEMORY_QUERY_KEYS.list(limit, offset),
    queryFn: async () => {
      const response = await memoryService.listMemories(limit, offset);
      if (response.error) {
        throw new Error(response.error);
      }
      return response.data || [];
    },
    staleTime: 10 * 1000, // 10 seconds
    gcTime: 5 * 60 * 1000, // 5 minutes
    refetchInterval: 30 * 1000, // 30 seconds
  });
}

/**
 * Hook to fetch a single memory by ID
 */
export function useMemoryDetail(id: string) {
  return useQuery({
    queryKey: MEMORY_QUERY_KEYS.detail(id),
    queryFn: async () => {
      const response = await memoryService.getMemory(id);
      if (response.error) {
        throw new Error(response.error);
      }
      return response.data;
    },
    staleTime: 10 * 1000,
    gcTime: 5 * 60 * 1000,
  });
}

/**
 * Hook to create a new memory
 */
export function useMemoryCreate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateMemoryRequest) =>
      memoryService.createMemory(data),
    onSuccess: () => {
      // Invalidate and refetch the memory list
      queryClient.invalidateQueries({
        queryKey: MEMORY_QUERY_KEYS.lists(),
      });
    },
  });
}

/**
 * Hook to update a memory
 */
export function useMemoryUpdate(id: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: UpdateMemoryRequest) =>
      memoryService.updateMemory(id, data),
    onSuccess: () => {
      // Invalidate both the specific memory and the list
      queryClient.invalidateQueries({
        queryKey: MEMORY_QUERY_KEYS.detail(id),
      });
      queryClient.invalidateQueries({
        queryKey: MEMORY_QUERY_KEYS.lists(),
      });
    },
  });
}

/**
 * Hook to delete a memory
 */
export function useMemoryDelete(id: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => memoryService.deleteMemory(id),
    onSuccess: () => {
      // Remove the deleted memory from the cache and invalidate the list
      queryClient.removeQueries({
        queryKey: MEMORY_QUERY_KEYS.detail(id),
      });
      queryClient.invalidateQueries({
        queryKey: MEMORY_QUERY_KEYS.lists(),
      });
    },
  });
}
