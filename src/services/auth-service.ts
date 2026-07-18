/**
 * Authentication Service
 * 
 * Handles all authentication-related API calls:
 * - Sign in
 * - Get current user
 * - Refresh token
 */

import { apiClient } from "./api-client";
import { API_ENDPOINTS } from "@/constants";
import type { ApiResponse, AuthSession, AuthUser } from "@/types";

class AuthService {
  /**
   * Sign in with email and password
   */
  async signIn(email: string, password: string): Promise<ApiResponse<AuthSession>> {
    return apiClient.post<AuthSession>(API_ENDPOINTS.AUTH.SIGN_IN, {
      email,
      password,
    });
  }

  /**
   * Get current authenticated user
   */
  async getCurrentUser(): Promise<ApiResponse<AuthUser>> {
    return apiClient.get<AuthUser>(API_ENDPOINTS.AUTH.ME);
  }

  /**
   * Refresh access token
   */
  async refreshToken(refreshToken: string): Promise<ApiResponse<AuthSession>> {
    return apiClient.post<AuthSession>(API_ENDPOINTS.AUTH.REFRESH, {
      refresh_token: refreshToken,
    });
  }

  /**
   * Sign out the current user
   */
  async signOut(refreshToken: string): Promise<ApiResponse<void>> {
    // Send sign-out request if endpoint exists, but clear auth regardless
    try {
      return await apiClient.post<void>(API_ENDPOINTS.AUTH.SIGN_OUT, {
        refresh_token: refreshToken,
      });
    } catch (_error) {
      // Ignore errors on sign-out, auth will be cleared by caller
      return { status: 200 };
    }
  }
}

export const authService = new AuthService();
