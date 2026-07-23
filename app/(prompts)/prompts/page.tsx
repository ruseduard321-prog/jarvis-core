"use client";

import { useQuery } from "@tanstack/react-query";
import { promptsService } from "@/services/prompts-service";
import { PromptsLayout } from "@/components/prompts/prompts-layout";

export default function Page() {
  const { data: response, isLoading, error } = useQuery({
    queryKey: ["prompts"],
    queryFn: () => promptsService.listPrompts(),
    staleTime: 10000,
    gcTime: 5 * 60 * 1000,
    refetchInterval: 30000,
  });

  const prompts = response?.data || [];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-3"></div>
          <p className="text-gray-600">Loading prompts...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center p-12">
        <div className="text-center">
          <p className="text-red-600 font-medium mb-2">Failed to load prompts</p>
          <p className="text-gray-600 text-sm">{error.message}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Prompts Library</h1>
        <p className="text-gray-600 mt-1">Manage and organize your reusable prompts</p>
      </div>
      <PromptsLayout prompts={prompts} />
    </div>
  );
}
