import { apiClient } from "@/services/api-client";
import { API_ENDPOINTS } from "@/constants";
import type { ApiResponse, DashboardResponse } from "@/types";

/**
 * Dashboard Service
 * Handles dashboard data API operations
 */

export const dashboardService = {
  /**
   * Get complete dashboard data
   */
  async getDashboard(): Promise<ApiResponse<DashboardResponse>> {
    return apiClient.get(API_ENDPOINTS.DASHBOARD.GET);
  },
};
