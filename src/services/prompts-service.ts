import { API_BASE_URL, API_ENDPOINTS } from "@/constants";
import {
  ApiResponse,
  Prompt,
  PromptCategory,
} from "@/types";

export interface PromptCreateRequest {
  name: string;
  content: string;
  category: PromptCategory;
}

export interface PromptUpdateRequest {
  name?: string;
  content?: string;
  category?: PromptCategory;
  favorite?: boolean;
}

class PromptsService {
  async listPrompts(): Promise<ApiResponse<Prompt[]>> {
    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.PROMPTS.LIST}`, {
      method: "GET",
      credentials: "include",
    });

    if (!response.ok) {
      return {
        data: undefined,
        error: `Failed to fetch prompts: ${response.statusText}`,
        status: response.status,
      };
    }

    const prompts = await response.json();
    return {
      data: prompts,
      status: response.status,
    };
  }

  async getPrompt(id: string): Promise<ApiResponse<Prompt>> {
    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.PROMPTS.GET(id)}`, {
      method: "GET",
      credentials: "include",
    });

    if (!response.ok) {
      return {
        data: undefined,
        error: `Failed to fetch prompt: ${response.statusText}`,
        status: response.status,
      };
    }

    const prompt = await response.json();
    return {
      data: prompt,
      status: response.status,
    };
  }

  async createPrompt(data: PromptCreateRequest): Promise<ApiResponse<Prompt>> {
    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.PROMPTS.CREATE}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
      credentials: "include",
    });

    if (!response.ok) {
      return {
        data: undefined,
        error: `Failed to create prompt: ${response.statusText}`,
        status: response.status,
      };
    }

    const prompt = await response.json();
    return {
      data: prompt,
      status: response.status,
    };
  }

  async updatePrompt(
    id: string,
    data: PromptUpdateRequest
  ): Promise<ApiResponse<Prompt>> {
    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.PROMPTS.UPDATE(id)}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
      credentials: "include",
    });

    if (!response.ok) {
      return {
        data: undefined,
        error: `Failed to update prompt: ${response.statusText}`,
        status: response.status,
      };
    }

    const prompt = await response.json();
    return {
      data: prompt,
      status: response.status,
    };
  }

  async deletePrompt(id: string): Promise<ApiResponse<void>> {
    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.PROMPTS.DELETE(id)}`, {
      method: "DELETE",
      credentials: "include",
    });

    if (!response.ok) {
      return {
        data: undefined,
        error: `Failed to delete prompt: ${response.statusText}`,
        status: response.status,
      };
    }

    return {
      data: undefined,
      status: response.status,
    };
  }
}

export const promptsService = new PromptsService();
