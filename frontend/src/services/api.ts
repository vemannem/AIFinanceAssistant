/**
 * API Client
 * Axios instance with configuration and interceptors
 */

import axios, {
  AxiosInstance,
  AxiosError,
  InternalAxiosRequestConfig,
} from 'axios'
import { configManager } from '../config/index'

/**
 * Create axios instance with base URL and interceptors
 */
function createApiClient(): AxiosInstance {
  const instance = axios.create({
    baseURL: configManager.getApiUrl(),
    timeout: 30000,
    headers: {
      'Content-Type': 'application/json',
    },
  })

  // Request interceptor
  instance.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
      if (configManager.isDebugMode()) {
        console.log('📤 API Request:', config.method?.toUpperCase(), config.url)
      }
      return config
    },
    (error: AxiosError) => {
      console.error('❌ Request Error:', error)
      return Promise.reject(error)
    }
  )

  // Response interceptor with retry logic
  instance.interceptors.response.use(
    (response) => {
      if (configManager.isDebugMode()) {
        console.log('📥 API Response:', response.status, response.config.url)
      }
      return response
    },
    async (error: AxiosError) => {
      const config = error.config as InternalAxiosRequestConfig & {
        _retry?: number
      }

      if (!config) {
        return Promise.reject(error)
      }

      // Retry logic
      if (!config._retry) {
        config._retry = 0
      }

      if (config._retry < 3 && error.response?.status === 503) {
        config._retry += 1
        const delay = 1000 * Math.pow(2, config._retry - 1)
        await new Promise((resolve) => setTimeout(resolve, delay))
        return instance(config)
      }

      console.error('❌ API Error:', error.response?.status, error.message)
      return Promise.reject(error)
    }
  )

  return instance
}

export const apiClient = createApiClient()
