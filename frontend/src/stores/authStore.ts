/**
 * Authentication state management with Zustand
 */
import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { debugLog } from '../utils/debug'

interface User {
  id: number
  username: string
  email: string | null
  full_name: string | null
  is_active: boolean
  is_superuser: boolean
}

interface AuthState {
  token: string | null
  user: User | null
  isAuthenticated: boolean
  
  // Actions
  login: (token: string, user: User) => void
  logout: () => void
  updateUser: (user: User) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      isAuthenticated: false,

      login: (token: string, user: User) => {
        debugLog.info('User logged in', { userId: user.id, username: user.username }, 'AuthStore')
        set({
          token,
          user,
          isAuthenticated: true,
        })
      },

      logout: () => {
        debugLog.info('User logged out', undefined, 'AuthStore')
        set({
          token: null,
          user: null,
          isAuthenticated: false,
        })
      },

      updateUser: (user: User) => {
        set({ user })
      },
    }),
    {
      name: 'proper-prompts-auth',
      partialize: (state) => ({
        token: state.token,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)

