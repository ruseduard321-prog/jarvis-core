import axios, { AxiosInstance, AxiosRequestConfig, AxiosError } from "axios";
import { API_BASE_URL, API_ENDPOINTS } from "@/constants";
import { useAuthStore } from "@/store";
import type { ApiResponse, AuthSession } from "@/types";

/**
 * API Client Service
 *
 * Handles HTTP requests with automatic token refresh and error handling.
 * This is a utility class that doesn't use React hooks directly.
 * Token state is read/written exclusively via the Zustand auth store
 * (useAuthStore.getState()) so there is a single source of truth — this class
 * must never read or write the "auth-storage" localStorage key directly, since
 * Zustand's persist middleware would silently clobber out-of-band writes.
 */
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

    // Request interceptor - add Bearer token to requests
    this.client.interceptors.request.use((config) => {
      const token = this.getAccessToken();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Response interceptor - handle 401 and refresh token
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean };

        // Only retry on 401 and not already retried
        if (error.response?.status === 401 && !originalRequest._retry) {
          // If refresh is already in progress, wait for it
          if (this.refreshPromise) {
            try {
              const newToken = await this.refreshPromise;
              if (newToken && originalRequest.headers) {
                originalRequest.headers.Authorization = `Bearer ${newToken}`;
              }
              return this.client(originalRequest);
            } catch {
              // Refresh failed, reject original request
              return Promise.reject(error);
            }
          }

          // Mark request as retried to prevent infinite loop
          originalRequest._retry = true;

          // Start refresh token flow
          this.refreshPromise = this.refreshAccessToken();

          try {
            const newToken = await this.refreshPromise;
            this.refreshPromise = null;

            if (newToken && originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${newToken}`;
            }
            return this.client(originalRequest);
          } catch {
            // Refresh failed, clear auth and reject
            this.clearTokens();
            this.refreshPromise = null;
            return Promise.reject(error);
          }
        }

        return Promise.reject(error);
      }
    );
  }

  /**
   * Get access token from the auth store
   */
  private getAccessToken(): string | null {
    return useAuthStore.getState().accessToken;
  }

  /**
   * Get refresh token from the auth store
   */
  private getRefreshToken(): string | null {
    return useAuthStore.getState().refreshToken;
  }

  /**
   * Update tokens in the auth store
   */
  private setTokens(accessToken: string, refreshToken: string, expiresAt: string): void {
    useAuthStore.getState().setTokens(accessToken, refreshToken, expiresAt);
  }

  /**
   * Clear tokens in the auth store
   */
  private clearTokens(): void {
    useAuthStore.getState().clearAuth();
  }

  /**
   * Refresh the access token using the refresh token
   */
  private async refreshAccessToken(): Promise<string> {
    try {
      const refreshToken = this.getRefreshToken();

      if (!refreshToken) {
        throw new Error("No refresh token available");
      }

      const response = await this.client.post<AuthSession>(
        API_ENDPOINTS.AUTH.REFRESH,
        { refresh_token: refreshToken }
      );

      const { access_token, refresh_token, expires_at } = response.data;

      // Update tokens in localStorage
      this.setTokens(access_token, refresh_token, expires_at);

      return access_token;
    } catch (error) {
      // Clear auth on refresh failure
      this.clearTokens();
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

  /**
   * Handle API errors and return normalized error response
   */
  private handleError(error: unknown): ApiResponse {
    if (axios.isAxiosError(error)) {
      return {
        error: error.response?.data?.error || error.response?.data?.message || error.message,
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
