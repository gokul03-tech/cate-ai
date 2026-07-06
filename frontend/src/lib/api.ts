/**
 * LexOrch-KG — Axios API Client
 * Configured with JWT interceptors and refresh token rotation.
 */

import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: `${API_BASE}/api/v1`,
  headers: { 'Content-Type': 'application/json' },
  timeout: 60000, // 60s for long AI operations
})

// ── Request interceptor — attach access token ─────────────────────────────
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// ── Response interceptor — handle 401, refresh token ─────────────────────
let isRefreshing = false
let failedQueue: Array<{
  resolve: (value: string) => void
  reject: (error: unknown) => void
}> = []

const processQueue = (error: unknown, token: string | null = null) => {
  failedQueue.forEach(({ resolve, reject }) => {
    if (error) {
      reject(error)
    } else if (token) {
      resolve(token)
    }
  })
  failedQueue = []
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        }).then((token) => {
          originalRequest.headers.Authorization = `Bearer ${token}`
          return api(originalRequest)
        })
      }

      originalRequest._retry = true
      isRefreshing = true

      const refreshToken = localStorage.getItem('refresh_token')
      if (!refreshToken) {
        localStorage.clear()
        window.location.href = '/login'
        return Promise.reject(error)
      }

      try {
        const { data } = await axios.post(`${API_BASE}/api/v1/auth/refresh`, {
          refresh_token: refreshToken,
        })
        localStorage.setItem('access_token', data.access_token)
        localStorage.setItem('refresh_token', data.refresh_token)
        processQueue(null, data.access_token)
        originalRequest.headers.Authorization = `Bearer ${data.access_token}`
        return api(originalRequest)
      } catch (refreshError) {
        processQueue(refreshError, null)
        localStorage.clear()
        window.location.href = '/login'
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    return Promise.reject(error)
  },
)

// ── API Functions ─────────────────────────────────────────────────────────

// Auth
export const authApi = {
  register: (data: object) => api.post('/auth/register', data),
  login: (data: object) => api.post('/auth/login', data),
  logout: () => api.post('/auth/logout'),
  me: () => api.get('/auth/me'),
}

// Cases
export const casesApi = {
  upload: (formData: FormData) =>
    api.post('/cases/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  list: (page = 1, pageSize = 20) =>
    api.get('/cases', { params: { page, page_size: pageSize } }),
  get: (id: string) => api.get(`/cases/${id}`),
  analyze: (id: string) => api.post(`/cases/${id}/analyze`),
  entities: (id: string, type?: string) =>
    api.get(`/cases/${id}/entities`, { params: type ? { entity_type: type } : {} }),
  knowledgeGraph: (id: string) => api.get(`/cases/${id}/knowledge-graph`),
  debate: (id: string) => api.get(`/cases/${id}/debate`),
  explainability: (id: string) => api.get(`/cases/${id}/explainability`),
  submitReview: (id: string, data: object) => api.post(`/cases/${id}/review`, data),
  delete: (id: string) => api.delete(`/cases/${id}`),
}

// Reports
export const reportsApi = {
  list: (caseId: string) => api.get(`/reports/${caseId}`),
  download: (reportId: string) =>
    api.get(`/reports/${reportId}/download`, { responseType: 'blob' }),
}

// Admin
export const adminApi = {
  stats: () => api.get('/admin/stats'),
  users: (page = 1) => api.get('/admin/users', { params: { page } }),
  updateUser: (id: string, data: object) => api.patch(`/admin/users/${id}`, data),
  deactivateUser: (id: string) => api.delete(`/admin/users/${id}`),
  auditLogs: (limit = 50, userId?: string) =>
    api.get('/admin/audit-logs', { params: { limit, user_id: userId } }),
}
