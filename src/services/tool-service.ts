import { apiClient } from "@/services/api-client";
import { API_ENDPOINTS } from "@/constants";
import type { ApiResponse, Tool } from "@/types";

export const toolService = {
  async listTools(): Promise<ApiResponse<Tool[]>> {
    return apiClient.get(API_ENDPOINTS.TOOLS.LIST);
  },

  async getTool(slug: string): Promise<ApiResponse<Tool>> {
    return apiClient.get(API_ENDPOINTS.TOOLS.GET(slug));
  },
};
