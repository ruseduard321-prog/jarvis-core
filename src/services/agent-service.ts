import { apiClient } from "@/services/api-client";
import { API_ENDPOINTS } from "@/constants";
import type { Agent, ApiResponse } from "@/types";

export const agentService = {
  async listAgents(): Promise<ApiResponse<Agent[]>> {
    return apiClient.get(API_ENDPOINTS.AGENTS.LIST);
  },

  async getAgent(agentId: string): Promise<ApiResponse<Agent>> {
    return apiClient.get(API_ENDPOINTS.AGENTS.GET(agentId));
  },
};
