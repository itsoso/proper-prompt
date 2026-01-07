/**
 * API client for backend communication
 */
import axios, { AxiosError, AxiosInstance } from 'axios'
import { debugLog } from './debug'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1'

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    const startTime = performance.now()
    config.metadata = { startTime }

    debugLog.debug(`API Request: ${config.method?.toUpperCase()} ${config.url}`, config.data, 'API')
    
    // Add auth token if available
    const authData = localStorage.getItem('proper-prompts-auth')
    if (authData) {
      try {
        const { state } = JSON.parse(authData)
        if (state?.token) {
          config.headers['Authorization'] = `Bearer ${state.token}`
        }
      } catch {
        // Ignore parse errors
      }
    }
    
    // Add API key if available
    const apiKey = localStorage.getItem('api_key')
    if (apiKey) {
      config.headers['X-API-Key'] = apiKey
    }

    return config
  },
  (error) => {
    debugLog.error('API Request Error', error, 'API')
    return Promise.reject(error)
  }
)

// Response interceptor
apiClient.interceptors.response.use(
  (response) => {
    const duration = performance.now() - (response.config.metadata?.startTime || 0)
    debugLog.info(
      `API Response: ${response.status} ${response.config.url} (${duration.toFixed(0)}ms)`,
      { data: response.data },
      'API'
    )
    return response
  },
  (error: AxiosError) => {
    const duration = performance.now() - (error.config?.metadata?.startTime || 0)
    debugLog.error(
      `API Error: ${error.response?.status || 'Network Error'} ${error.config?.url} (${duration.toFixed(0)}ms)`,
      { error: error.response?.data || error.message },
      'API'
    )
    return Promise.reject(error)
  }
)

// Add metadata type to axios
declare module 'axios' {
  export interface AxiosRequestConfig {
    metadata?: { startTime: number }
  }
}

// API methods
export const api = {
  // Authentication
  auth: {
    login: (username: string, password: string) =>
      apiClient.post('/auth/login', new URLSearchParams({ username, password }), {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      }),
    loginJson: (username: string, password: string) =>
      apiClient.post('/auth/login/json', { username, password }),
    me: () => apiClient.get('/auth/me'),
    changePassword: (currentPassword: string, newPassword: string) =>
      apiClient.post('/auth/change-password', {
        current_password: currentPassword,
        new_password: newPassword,
      }),
    logout: () => apiClient.post('/auth/logout'),
    createUser: (data: { username: string; password: string; email?: string; full_name?: string; is_superuser?: boolean }) =>
      apiClient.post('/auth/users', data),
  },

  // Groups
  groups: {
    list: (params?: { page?: number; size?: number; type?: string; search?: string }) =>
      apiClient.get('/groups', { params }),
    get: (id: number) => apiClient.get(`/groups/${id}`),
    create: (data: GroupCreateData) => apiClient.post('/groups', data),
    update: (id: number, data: GroupUpdateData) => apiClient.patch(`/groups/${id}`, data),
    delete: (id: number) => apiClient.delete(`/groups/${id}`),
    types: () => apiClient.get('/groups/types/list'),
  },

  // Prompts
  prompts: {
    templates: {
      list: (params?: { group_type?: string; time_granularity?: string; style?: string }) =>
        apiClient.get('/prompts/templates', { params }),
      get: (id: number) => apiClient.get(`/prompts/templates/${id}`),
      create: (data: TemplateCreateData) => apiClient.post('/prompts/templates', data),
      update: (id: number, data: TemplateUpdateData) => apiClient.patch(`/prompts/templates/${id}`, data),
      delete: (id: number) => apiClient.delete(`/prompts/templates/${id}`),
    },
    execute: (data: ExecutePromptData) => apiClient.post('/prompts/execute', data),
    executions: {
      list: (params?: { template_id?: number; group_id?: number; status?: string }) =>
        apiClient.get('/prompts/executions', { params }),
      get: (id: number) => apiClient.get(`/prompts/executions/${id}`),
    },
    generate: (data: GeneratePromptsData) => apiClient.post('/prompts/generate', data),
    builtin: () => apiClient.get('/prompts/builtin'),
  },

  // Analysis
  analysis: {
    tasks: {
      list: (params?: { group_id?: number; status?: string }) =>
        apiClient.get('/analysis/tasks', { params }),
      get: (id: number) => apiClient.get(`/analysis/tasks/${id}`),
      create: (data: AnalysisRequestData) => apiClient.post('/analysis/tasks', data),
      run: (id: number, chatContent: string) =>
        apiClient.post(`/analysis/tasks/${id}/run`, null, { params: { chat_content: chatContent } }),
    },
    results: {
      list: (params?: { task_id?: number }) => apiClient.get('/analysis/results', { params }),
      get: (id: number) => apiClient.get(`/analysis/results/${id}`),
    },
    quick: (data: QuickAnalysisData) => apiClient.post('/analysis/quick', data),
  },

  // Evaluations
  evaluations: {
    list: (params?: { limit?: number; offset?: number }) =>
      apiClient.get('/evaluations', { params }),
    get: (id: number) => apiClient.get(`/evaluations/${id}`),
    create: (data: EvaluationCreateData) => apiClient.post('/evaluations', data),
    score: (id: number, data: { execution_id: number; scores: Record<string, number> }) =>
      apiClient.post(`/evaluations/${id}/score`, data),
    compare: (data: ComparePromptsData) => apiClient.post('/evaluations/compare', data),
    delete: (id: number) => apiClient.delete(`/evaluations/${id}`),
  },

  // API Keys
  apiKeys: {
    list: (params?: { integration_type?: string; is_active?: boolean }) =>
      apiClient.get('/api-keys', { params }),
    get: (id: number) => apiClient.get(`/api-keys/${id}`),
    create: (data: APIKeyCreateData) => apiClient.post('/api-keys', data),
    update: (id: number, data: APIKeyUpdateData) => apiClient.patch(`/api-keys/${id}`, data),
    revoke: (id: number) => apiClient.delete(`/api-keys/${id}`),
    validate: (key: string) => apiClient.post('/api-keys/validate', { key }),
  },

  // Health
  health: () => apiClient.get('/health'),
}

// Type definitions
interface GroupCreateData {
  external_id: string
  name: string
  type: string
  description?: string
  member_count?: number
}

interface GroupUpdateData {
  name?: string
  type?: string
  description?: string
  member_count?: number
  is_active?: boolean
}

interface TemplateCreateData {
  name: string
  description?: string
  group_type: string
  time_granularity: string
  style: string
  system_prompt: string
  user_prompt_template: string
  required_variables?: string[]
  optional_variables?: string[]
}

interface TemplateUpdateData {
  name?: string
  description?: string
  system_prompt?: string
  user_prompt_template?: string
  is_active?: boolean
}

interface ExecutePromptData {
  template_id: number
  group_id?: number
  variables?: Record<string, unknown>
  start_date?: string
  end_date?: string
  member_filter?: string[]
  chat_data?: string
}

interface GeneratePromptsData {
  group_type: string
  time_granularity: string
  styles?: string[]
  custom_requirements?: string
}

interface AnalysisRequestData {
  group_id: number
  template_id?: number
  start_date: string
  end_date: string
  member_filter?: string[]
  keyword_filter?: string[]
}

interface QuickAnalysisData {
  group_type: string
  chat_content: string
  time_period?: string
  focus_members?: string[]
  analysis_focus?: string
}

interface EvaluationCreateData {
  name: string
  description?: string
  execution_ids: number[]
  criteria?: Record<string, number>
}

interface ComparePromptsData {
  template_ids: number[]
  group_id?: number
  variables?: Record<string, unknown>
  chat_data: string
  start_date?: string
  end_date?: string
}

interface APIKeyCreateData {
  name: string
  scopes?: string[]
  rate_limit?: number
  integration_type?: string
  webhook_url?: string
}

interface APIKeyUpdateData {
  name?: string
  scopes?: string[]
  rate_limit?: number
  is_active?: boolean
}

export default apiClient

