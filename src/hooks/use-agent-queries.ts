import { useQuery } from "@tanstack/react-query";
import { agentService } from "@/services/agent-service";

const agentKeys = {
  all: ["agents"] as const,
  list: () => [...agentKeys.all, "list"] as const,
  detail: (id: string) => [...agentKeys.all, "detail", id] as const,
};

export function useAgents() {
  return useQuery({
    queryKey: agentKeys.list(),
    queryFn: async () => {
      const response = await agentService.listAgents();
      if (response.status !== 200 || !response.data) {
        throw new Error(response.error || "Failed to fetch agents");
      }
      return response.data;
    },
  });
}

export function useAgent(agentId: string | null) {
  return useQuery({
    queryKey: agentId ? agentKeys.detail(agentId) : [],
    queryFn: async () => {
      if (!agentId) throw new Error("No agent ID");
      const response = await agentService.getAgent(agentId);
      if (response.status !== 200 || !response.data) {
        throw new Error(response.error || "Failed to fetch agent");
      }
      return response.data;
    },
    enabled: !!agentId,
  });
}
