import { useQuery } from "@tanstack/react-query";
import { toolService } from "@/services/tool-service";

const toolKeys = {
  all: ["tools"] as const,
  list: () => [...toolKeys.all, "list"] as const,
  detail: (slug: string) => [...toolKeys.all, "detail", slug] as const,
};

export function useTools() {
  return useQuery({
    queryKey: toolKeys.list(),
    queryFn: async () => {
      const response = await toolService.listTools();
      if (response.status !== 200 || !response.data) {
        throw new Error(response.error || "Failed to fetch tools");
      }
      return response.data;
    },
  });
}

export function useTool(slug: string | null) {
  return useQuery({
    queryKey: slug ? toolKeys.detail(slug) : [],
    queryFn: async () => {
      if (!slug) throw new Error("No tool slug");
      const response = await toolService.getTool(slug);
      if (response.status !== 200 || !response.data) {
        throw new Error(response.error || "Failed to fetch tool");
      }
      return response.data;
    },
    enabled: !!slug,
  });
}
