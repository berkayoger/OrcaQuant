import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { api } from '../services/api';

interface User {
  id: string;
  email: string;
  role?: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,

      login: async (email: string, password: string) => {
        try {
          const response = await api.post('/auth/login', {
            email,
            password
          });

          const { access_token, user } = response.data;
          
          set({
            user,
            token: access_token,
            isAuthenticated: true
          });

          // Set token for future requests
          api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
          
        } catch (error: any) {
          throw new Error(error.response?.data?.message || 'Login failed');
        }
      },

      logout: () => {
        set({
          user: null,
          token: null,
          isAuthenticated: false
        });
        
        delete api.defaults.headers.common['Authorization'];
      },

      checkAuth: async () => {
        const { token } = get();
        
        if (!token) {
          return;
        }

        try {
          api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
          const response = await api.get('/auth/status');
          
          if (response.data.authenticated) {
            set({
              user: response.data.user,
              isAuthenticated: true
            });
          } else {
            get().logout();
          }
        } catch {
          get().logout();
        }
      }
    }),
    {
      name: 'orcaquant-auth',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated
      })
    }
  )
);

// Initialize auth on app start
useAuthStore.getState().checkAuth();
