/**
 * ConfigManager
 * Manages environment variables and configuration for the frontend
 */

class ConfigManager {
  private apiUrl: string
  private wsUrl: string
  private debugMode: boolean

  constructor() {
    // API URL - configurable via environment variable
    this.apiUrl =
      import.meta.env.VITE_API_URL || 'http://localhost:8000'

    // WebSocket URL - configurable via environment variable
    this.wsUrl =
      import.meta.env.VITE_WS_URL || 'ws://localhost:8000'

    // Debug mode
    this.debugMode =
      import.meta.env.MODE === 'development' ||
      import.meta.env.VITE_DEBUG === 'true'
  }

  /**
   * Get API base URL
   */
  getApiUrl(): string {
    return this.apiUrl
  }

  /**
   * Get WebSocket URL
   */
  getWsUrl(): string {
    return this.wsUrl
  }

  /**
   * Check if debug mode is enabled
   */
  isDebugMode(): boolean {
    return this.debugMode
  }

  /**
   * Get full API endpoint URL
   */
  getEndpoint(path: string): string {
    const url = new URL(path, this.apiUrl)
    return url.toString()
  }

  /**
   * Log configuration (only in debug mode)
   */
  logConfig(): void {
    if (this.debugMode) {
      console.group('📋 Configuration')
      console.log('API URL:', this.apiUrl)
      console.log('WebSocket URL:', this.wsUrl)
      console.log('Debug Mode:', this.debugMode)
      console.groupEnd()
    }
  }
}

// Create singleton instance
export const configManager = new ConfigManager()
