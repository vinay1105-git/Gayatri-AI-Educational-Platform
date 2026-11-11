import React, { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { api, getStoredToken, setStoredToken } from '../api/client'
import type { AuthResponse, UserSummary } from '../types'

interface AuthContextValue {
  user: UserSummary | null
  loading: boolean
  login: (email: string, password: string) => Promise<UserSummary>
  register: (payload: {
    full_name: string
    email: string
    password: string
    cohort: string
    program_track: string
  }) => Promise<UserSummary>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserSummary | null>(null)
  const [loading, setLoading] = useState<boolean>(true)

  useEffect(() => {
    const token = getStoredToken()
    if (!token) {
      setLoading(false)
      return
    }
    api
      .get<UserSummary>('/auth/me')
      .then((profile) => setUser(profile))
      .catch(() => {
        setStoredToken(null)
        setUser(null)
      })
      .finally(() => setLoading(false))
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const res = await api.post<AuthResponse>('/auth/login', { email, password })
    setStoredToken(res.access_token)
    setUser(res.user)
    return res.user
  }, [])

  const register = useCallback(
    async (payload: {
      full_name: string
      email: string
      password: string
      cohort: string
      program_track: string
    }) => {
      const res = await api.post<AuthResponse>('/auth/register', payload)
      setStoredToken(res.access_token)
      setUser(res.user)
      return res.user
    },
    []
  )

  const logout = useCallback(() => {
    setStoredToken(null)
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth must be used inside AuthProvider')
  }
  return ctx
}
