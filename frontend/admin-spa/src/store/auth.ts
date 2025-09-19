import { create } from 'zustand'
import { api } from '../lib/axios'

export type AdminUser = {
  id: string
  email: string
  role?: string
}

type AuthState = {
  token: string | null
  me?: AdminUser
  isSession: boolean
  isLoading: boolean
  loadMe: () => Promise<AdminUser>
  login: (token: string) => Promise<void>
  logout: () => void
}

const TOKEN_KEY = 'admin_token'

export const useAuthStore = create<AuthState>((set, get) => ({
  token: localStorage.getItem(TOKEN_KEY),
  me: undefined,
  isSession: !!localStorage.getItem(TOKEN_KEY),
  isLoading: false,
  async loadMe() {
    try {
      set({ isLoading: true })
      const response = await api.get<AdminUser>('/admin/me')
      set({ me: response.data, isSession: true })
      return response.data
    } catch (error) {
      set({ me: undefined, isSession: false })
      throw error
    } finally {
      set({ isLoading: false })
    }
  },
  async login(token: string) {
    localStorage.setItem(TOKEN_KEY, token)
    set({ token, isSession: true })
    await get().loadMe()
  },
  logout() {
    localStorage.removeItem(TOKEN_KEY)
    set({ token: null, me: undefined, isSession: false })
  }
}))
