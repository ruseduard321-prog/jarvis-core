import { useQuery } from "@tanstack/react-query";
import { dashboardService } from "@/services/dashboard-service";

// Query Keys
const dashboardKeys = {
  all: ["dashboard"] as const,
  data: () => [...dashboardKeys.all, "data"] as const,
};

/**
 * Hook to fetch complete dashboard data
 * Auto-refetches every 30 seconds to keep data fresh
 */
export function useDashboard() {
  return useQuery({
    queryKey: dashboardKeys.data(),
    queryFn: async () => {
      const response = await dashboardService.getDashboard();
      if (response.status !== 200 || !response.data) {
        throw new Error(response.error || "Failed to fetch dashboard");
      }
      return response.data;
    },
    refetchInterval: 30 * 1000, // Refetch every 30 seconds
    staleTime: 10 * 1000, // Data is fresh for 10 seconds
    gcTime: 5 * 60 * 1000, // Keep in cache for 5 minutes (formerly cacheTime)
  });
}
