"use client";

import { apiClient } from "@/services/api-client";
import { API_ENDPOINTS } from "@/constants";
import type { ApiResponse, Memory } from "@/types";

export interface CreateMemoryRequest {
  record_type: string;
  content: string;
  source?: string;
  tags?: string[];
  attributes?: Record<string, unknown>;
}

export interface UpdateMemoryRequest {
  content?: string;
  record_type?: string;
  tags?: string[];
  attributes?: Record<string, unknown>;
}

class MemoryService {
  async listMemories(
    limit: number = 20,
    offset: number = 0
  ): Promise<ApiResponse<Memory[]>> {
    return apiClient.get(API_ENDPOINTS.MEMORY.LIST, {
      params: { limit, offset },
    });
  }

  async getMemory(id: string): Promise<ApiResponse<Memory>> {
    return apiClient.get(API_ENDPOINTS.MEMORY.GET(id));
  }

  async createMemory(
    data: CreateMemoryRequest
  ): Promise<ApiResponse<Memory>> {
    return apiClient.post(API_ENDPOINTS.MEMORY.CREATE, data);
  }

  async updateMemory(
    id: string,
    data: UpdateMemoryRequest
  ): Promise<ApiResponse<Memory>> {
    return apiClient.patch(API_ENDPOINTS.MEMORY.UPDATE(id), data);
  }

  async deleteMemory(id: string): Promise<ApiResponse<void>> {
    return apiClient.delete(API_ENDPOINTS.MEMORY.DELETE(id));
  }

  /**
   * Client-side search: filter memories by content, tags, or source
   */
  searchMemories(
    memories: Memory[],
    query: string
  ): Memory[] {
    if (!query.trim()) return memories;

    const lowerQuery = query.toLowerCase();
    return memories.filter(
      (memory) =>
        memory.content.toLowerCase().includes(lowerQuery) ||
        memory.tags?.some((tag) =>
          tag.toLowerCase().includes(lowerQuery)
        ) ||
        memory.source?.toLowerCase().includes(lowerQuery)
    );
  }

  /**
   * Client-side filtering: filter memories by category and importance
   */
  filterMemories(
    memories: Memory[],
    filters: { category?: string; importance?: string }
  ): Memory[] {
    let filtered = memories;

    if (filters.category && filters.category !== "all") {
      filtered = filtered.filter(
        (m) => m.record_type === filters.category
      );
    }

    if (filters.importance && filters.importance !== "all") {
      filtered = filtered.filter(
        (m) => m.attributes.importance === filters.importance
      );
    }

    return filtered;
  }

  /**
   * Generate preview from memory content (first 60 chars)
   */
  getPreview(content: string, maxLength: number = 60): string {
    if (content.length <= maxLength) return content;
    return content.substring(0, maxLength) + "...";
  }
}

export const memoryService = new MemoryService();
