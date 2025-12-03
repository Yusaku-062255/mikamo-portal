import { create } from 'zustand'
import api from '../utils/api'

interface User {
  id: number
  email: string
  full_name: string
  department_id: number
  department_name?: string
  department_code?: string
  business_unit_id?: number
  tenant_id?: number
  role: string
  is_active: boolean
}

interface AuthState {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  fetchUser: () => Promise<void>
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  isLoading: true,
  isAuthenticated: false,

  login: async (email: string, password: string) => {
    const formData = new FormData()
    formData.append('username', email)
    formData.append('password', password)

    const response = await api.post('/api/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    })

    localStorage.setItem('access_token', response.data.access_token)
    await get().fetchUser()
  },

  logout: () => {
    localStorage.removeItem('access_token')
    set({ user: null, isAuthenticated: false })
  },

  fetchUser: async () => {
    const token = localStorage.getItem('access_token')
    if (!token) {
      set({ isLoading: false, isAuthenticated: false })
      return
    }

    try {
      const response = await api.get('/api/auth/me')
      set({
        user: response.data,
        isLoading: false,
        isAuthenticated: true,
      })
    } catch (error) {
      localStorage.removeItem('access_token')
      set({ user: null, isLoading: false, isAuthenticated: false })
    }
  },
}))

