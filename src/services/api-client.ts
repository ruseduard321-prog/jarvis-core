import axios, { AxiosInstance, AxiosRequestConfig, AxiosError } from "axios";
import { API_BASE_URL } from "@/constants";
import { useAuthStore } from "@/store";
import type { ApiResponse } from "@/types";

class ApiClient {
  private client: AxiosInstance;
  private refreshPromise: Promise<string> | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        "Content-Type": "application/json",
      },
    });

    // Request interceptor
    this.client.interceptors.request.use((config) => {
      const { token } = useAuthStore();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean };

        if (error.response?.status === 401 && !originalRequest._retry) {
          if (this.refreshPromise) {
            const token = await this.refreshPromise;
            if (token && originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`;
            }
            return this.client(originalRequest);
          }

          originalRequest._retry = true;
          this.refreshPromise = this.refreshToken();

          try {
            const token = await this.refreshPromise;
            this.refreshPromise = null;

            if (token && originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`;
            }
            return this.client(originalRequest);
          } catch {
            useAuthStore().clearAuth();
            this.refreshPromise = null;
            throw error;
          }
        }

        return Promise.reject(error);
      }
    );
  }

  private async refreshToken(): Promise<string> {
    try {
      const response = await this.client.post<{ token: string }>("/auth/refresh");
      const { token } = response.data;
      useAuthStore().setAuth(token, useAuthStore().userId || "");
      return token;
    } catch (error) {
      useAuthStore().clearAuth();
      throw error;
    }
  }

  async get<T = unknown>(
    url: string,
    config?: AxiosRequestConfig
  ): Promise<ApiResponse<T>> {
    try {
      const response = await this.client.get<T>(url, config);
      return {
        data: response.data,
        status: response.status,
      };
    } catch (error) {
      return this.handleError(error) as ApiResponse<T>;
    }
  }

  async post<T = unknown>(
    url: string,
    data?: unknown,
    config?: AxiosRequestConfig
  ): Promise<ApiResponse<T>> {
    try {
      const response = await this.client.post<T>(url, data, config);
      return {
        data: response.data,
        status: response.status,
      };
    } catch (error) {
      return this.handleError(error) as ApiResponse<T>;
    }
  }

  async put<T = unknown>(
    url: string,
    data?: unknown,
    config?: AxiosRequestConfig
  ): Promise<ApiResponse<T>> {
    try {
      const response = await this.client.put<T>(url, data, config);
      return {
        data: response.data,
        status: response.status,
      };
    } catch (error) {
      return this.handleError(error) as ApiResponse<T>;
    }
  }

  async patch<T = unknown>(
    url: string,
    data?: unknown,
    config?: AxiosRequestConfig
  ): Promise<ApiResponse<T>> {
    try {
      const response = await this.client.patch<T>(url, data, config);
      return {
        data: response.data,
        status: response.status,
      };
    } catch (error) {
      return this.handleError(error) as ApiResponse<T>;
    }
  }

  async delete<T = unknown>(
    url: string,
    config?: AxiosRequestConfig
  ): Promise<ApiResponse<T>> {
    try {
      const response = await this.client.delete<T>(url, config);
      return {
        data: response.data,
        status: response.status,
      };
    } catch (error) {
      return this.handleError(error) as ApiResponse<T>;
    }
  }

  private handleError(error: unknown): ApiResponse {
    if (axios.isAxiosError(error)) {
      return {
        error: error.response?.data?.error || error.message,
        status: error.response?.status || 500,
      };
    }
    if (error instanceof Error) {
      return {
        error: error.message,
        status: 500,
      };
    }
    return {
      error: "An unexpected error occurred",
      status: 500,
    };
  }
}

export const apiClient = new ApiClient();
