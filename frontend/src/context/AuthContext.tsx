import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { api } from '../api/client'
import type { User } from '../types'

interface AuthContextValue {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (payload: { email: string; full_name: string; phone_number: string; password: string }) => Promise<void>
  logout: () => void
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  const refreshUser = async () => {
    const token = localStorage.getItem('ecorevive_access')
    if (!token) {
      setUser(null)
      setLoading(false)
      return
    }
    try {
      const { data } = await api.get<User>('/auth/me/')
      setUser(data)
    } catch {
      localStorage.removeItem('ecorevive_access')
      localStorage.removeItem('ecorevive_refresh')
      setUser(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    // Authentication is restored once from browser storage on application start.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void refreshUser()
  }, [])

  const login = async (email: string, password: string) => {
    const { data } = await api.post<{ access: string; refresh: string }>('/auth/token/', { email, password })
    localStorage.setItem('ecorevive_access', data.access)
    localStorage.setItem('ecorevive_refresh', data.refresh)
    await refreshUser()
  }

  const register = async (payload: { email: string; full_name: string; phone_number: string; password: string }) => {
    await api.post('/auth/register/', payload)
    await login(payload.email, payload.password)
  }

  const logout = () => {
    localStorage.removeItem('ecorevive_access')
    localStorage.removeItem('ecorevive_refresh')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used inside AuthProvider')
  return context
}
