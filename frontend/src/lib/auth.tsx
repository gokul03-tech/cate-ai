/**
 * LexOrch-KG — Auth Context
 * React context for authentication state management.
 */

import React, { createContext, useContext, useEffect, useState } from 'react'
import { authApi } from './api'

export interface AuthUser {
  id: string
  email: string
  first_name: string
  last_name: string
  role: 'admin' | 'judge' | 'lawyer' | 'analyst' | 'viewer'
  is_active: boolean
  created_at: string
}

interface AuthContextValue {
  user: AuthUser | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (data: RegisterData) => Promise<void>
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
}

interface RegisterData {
  email: string
  password: string
  first_name: string
  last_name: string
  role: string
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const refreshUser = async () => {
    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        setUser(null)
        return
      }
      const { data } = await authApi.me()
      setUser(data)
    } catch {
      setUser(null)
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
    }
  }

  useEffect(() => {
    refreshUser().finally(() => setIsLoading(false))
  }, [])

  const login = async (email: string, password: string) => {
    const { data } = await authApi.login({ email, password })
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    await refreshUser()
  }

  const register = async (registerData: RegisterData) => {
    await authApi.register(registerData)
    // Auto-login after register
    await login(registerData.email, registerData.password)
  }

  const logout = async () => {
    try {
      await authApi.logout()
    } finally {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      setUser(null)
    }
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        register,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}

export function useRole(requiredRole: string[]): boolean {
  const { user } = useAuth()
  if (!user) return false
  return requiredRole.includes(user.role)
}
