/**
 * API Configuration Module
 * Loads backend server URL from environment variables
 * Configurable for development, staging, and production environments
 */

interface ApiConfig {
  baseURL: string;
  wsURL: string;
  timeout: number;
  retryAttempts: number;
  retryDelay: number;
  logLevel: 'debug' | 'info' | 'warn' | 'error';
}

class ConfigManager {
  private config: ApiConfig;

  constructor() {
    this.config = this.loadConfig();
  }

  private loadConfig(): ApiConfig {
    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';
    const logLevel = (import.meta.env.VITE_LOG_LEVEL || 'info') as
      | 'debug'
      | 'info'
      | 'warn'
      | 'error';

    return {
      baseURL: apiUrl,
      wsURL: wsUrl,
      timeout: 30000, // 30 seconds
      retryAttempts: 3,
      retryDelay: 1000, // 1 second
      logLevel,
    };
  }

  /**
   * Get the full API configuration
   */
  getConfig(): ApiConfig {
    return { ...this.config };
  }

  /**
   * Get the base URL for REST API calls
   */
  getBaseURL(): string {
    return this.config.baseURL;
  }

  /**
   * Get the WebSocket URL
   */
  getWSURL(): string {
    return this.config.wsURL;
  }

  /**
   * Get request timeout in milliseconds
   */
  getTimeout(): number {
    return this.config.timeout;
  }

  /**
   * Get retry configuration
   */
  getRetryConfig(): { attempts: number; delay: number } {
    return {
      attempts: this.config.retryAttempts,
      delay: this.config.retryDelay,
    };
  }

  /**
   * Get log level
   */
  getLogLevel(): string {
    return this.config.logLevel;
  }

  /**
   * Check if debug mode is enabled
   */
  isDebugMode(): boolean {
    return import.meta.env.VITE_ENABLE_DEBUG === 'true';
  }

  /**
   * Log configuration (for debugging)
   */
  logConfig(): void {
    console.group('API Configuration');
    console.log('Base URL:', this.config.baseURL);
    console.log('WebSocket URL:', this.config.wsURL);
    console.log('Timeout:', this.config.timeout, 'ms');
    console.log('Retry Attempts:', this.config.retryAttempts);
    console.log('Log Level:', this.config.logLevel);
    console.log('Debug Mode:', this.isDebugMode());
    console.groupEnd();
  }
}

// Export singleton instance
export const configManager = new ConfigManager();

// Export for testing
export default ConfigManager;
