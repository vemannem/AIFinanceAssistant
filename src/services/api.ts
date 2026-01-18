/**
 * API Client Module
 * Handles all HTTP requests to the backend
 * Uses configurable base URL from environment variables
 */

import axios, {
  AxiosInstance,
  AxiosError,
  InternalAxiosRequestConfig,
} from 'axios';
import { configManager } from '../config';

export interface ApiError {
  message: string;
  status?: number;
  code?: string;
  details?: Record<string, unknown>;
}

export interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: ApiError;
}

class ApiClient {
  private axiosInstance: AxiosInstance;
  private retryAttempts: Map<string, number> = new Map();

  constructor() {
    const config = configManager.getConfig();

    this.axiosInstance = axios.create({
      baseURL: config.baseURL,
      timeout: config.timeout,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add request interceptor
    this.axiosInstance.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        // Add any auth tokens or headers here
        const token = this.getAuthToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error: AxiosError) => {
        return Promise.reject(error);
      }
    );

    // Add response interceptor for error handling
    this.axiosInstance.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        // Handle 429 (rate limit) and 5xx errors with retry logic
        if (
          error.response?.status === 429 ||
          (error.response?.status && error.response.status >= 500)
        ) {
          const config = error.config;
          if (config && this.shouldRetry(error)) {
            return this.retry(config);
          }
        }
        return Promise.reject(error);
      }
    );

    if (configManager.isDebugMode()) {
      configManager.logConfig();
    }
  }

  /**
   * GET request
   */
  async get<T = unknown>(
    url: string,
    config?: Record<string, unknown>
  ): Promise<T> {
    try {
      const response = await this.axiosInstance.get<T>(url, config);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * POST request
   */
  async post<T = unknown>(
    url: string,
    data?: unknown,
    config?: Record<string, unknown>
  ): Promise<T> {
    try {
      const response = await this.axiosInstance.post<T>(url, data, config);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * PUT request
   */
  async put<T = unknown>(
    url: string,
    data?: unknown,
    config?: Record<string, unknown>
  ): Promise<T> {
    try {
      const response = await this.axiosInstance.put<T>(url, data, config);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * DELETE request
   */
  async delete<T = unknown>(
    url: string,
    config?: Record<string, unknown>
  ): Promise<T> {
    try {
      const response = await this.axiosInstance.delete<T>(url, config);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Check if request should be retried
   */
  private shouldRetry(error: AxiosError): boolean {
    const config = error.config;
    if (!config) return false;

    const url = config.url || '';
    const attempts = this.retryAttempts.get(url) || 0;
    const { attempts: maxAttempts } = configManager.getRetryConfig();

    return attempts < maxAttempts;
  }

  /**
   * Retry failed request
   */
  private async retry(config: InternalAxiosRequestConfig): Promise<unknown> {
    const url = config.url || '';
    const attempts = this.retryAttempts.get(url) || 0;
    const { delay } = configManager.getRetryConfig();

    this.retryAttempts.set(url, attempts + 1);

    // Wait before retrying
    await new Promise((resolve) => setTimeout(resolve, delay * (attempts + 1)));

    try {
      const response = await this.axiosInstance.request(config);
      this.retryAttempts.delete(url); // Reset on success
      return response.data;
    } catch (error) {
      if (attempts + 1 >= configManager.getRetryConfig().attempts) {
        this.retryAttempts.delete(url);
      }
      throw error;
    }
  }

  /**
   * Handle API errors
   */
  private handleError(error: unknown): ApiError {
    if (axios.isAxiosError(error)) {
      const status = error.response?.status;
      const data = error.response?.data as Record<string, unknown>;

      return {
        message: data?.message || error.message || 'Unknown error occurred',
        status,
        code: data?.code as string,
        details: data?.details as Record<string, unknown>,
      };
    }

    if (error instanceof Error) {
      return {
        message: error.message,
        code: 'UNKNOWN_ERROR',
      };
    }

    return {
      message: 'An unexpected error occurred',
      code: 'UNKNOWN_ERROR',
    };
  }

  /**
   * Get authentication token (from localStorage or other source)
   */
  private getAuthToken(): string | null {
    // TODO: Implement token retrieval logic
    // return localStorage.getItem('authToken');
    return null;
  }

  /**
   * Get the axios instance (for advanced usage)
   */
  getInstance(): AxiosInstance {
    return this.axiosInstance;
  }
}

// Export singleton instance
export const apiClient = new ApiClient();

export default ApiClient;
