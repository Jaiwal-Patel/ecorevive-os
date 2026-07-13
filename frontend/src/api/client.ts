import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const access = localStorage.getItem('ecorevive_access')
  if (access) config.headers.Authorization = `Bearer ${access}`
  return config
})

let refreshing = false
let queued: Array<(token: string | null) => void> = []

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as (InternalAxiosRequestConfig & { _retry?: boolean }) | undefined
    if (!original || error.response?.status !== 401 || original._retry) return Promise.reject(error)

    const refresh = localStorage.getItem('ecorevive_refresh')
    if (!refresh) return Promise.reject(error)
    original._retry = true

    if (refreshing) {
      return new Promise((resolve, reject) => {
        queued.push((token) => {
          if (!token) reject(error)
          else {
            original.headers.Authorization = `Bearer ${token}`
            resolve(api(original))
          }
        })
      })
    }

    refreshing = true
    try {
      const response = await axios.post(`${API_BASE_URL}/auth/token/refresh/`, { refresh })
      const access = response.data.access as string
      localStorage.setItem('ecorevive_access', access)
      if (response.data.refresh) localStorage.setItem('ecorevive_refresh', response.data.refresh)
      queued.forEach((callback) => callback(access))
      queued = []
      original.headers.Authorization = `Bearer ${access}`
      return api(original)
    } catch (refreshError) {
      queued.forEach((callback) => callback(null))
      queued = []
      localStorage.removeItem('ecorevive_access')
      localStorage.removeItem('ecorevive_refresh')
      return Promise.reject(refreshError)
    } finally {
      refreshing = false
    }
  },
)

export function errorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data
    if (typeof data === 'string') return data
    if (data && typeof data === 'object') {
      const first = Object.entries(data)[0]
      if (first) {
        const value = first[1]
        return `${first[0]}: ${Array.isArray(value) ? value.join(', ') : String(value)}`
      }
    }
    return error.message
  }
  return error instanceof Error ? error.message : 'An unexpected error occurred.'
}
