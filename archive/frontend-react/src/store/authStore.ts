import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { client, plainClient, registerAuthHandlers, withErrorHandling } from '@/api/client';

export type UserRole = 'user' | 'admin';

export interface AuthUser {
  id: string;
  email: string;
  name: string;
  role: UserRole;
}

interface AuthResponse {
  accessToken: string;
  refreshToken: string;
  user: AuthUser;
}

interface RefreshResponse {
  accessToken: string;
  refreshToken?: string;
  user?: AuthUser;
}

interface AuthCredentials {
  email: string;
  password: string;
}

interface RegisterPayload extends AuthCredentials {
  name: string;
}

interface AuthState {
  user: AuthUser | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  hasHydrated: boolean;
  login: (credentials: AuthCredentials) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => void;
  refreshTokens: () => Promise<string | null>;
  setHydrated: () => void;
  clearError: () => void;
}

const STORAGE_KEY = 'orcaquant-auth-state';

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      hasHydrated: false,
      async login(credentials) {
        set({ isLoading: true, error: null });
        try {
          const data = await withErrorHandling<AuthResponse>(() => client.post('/auth/login', credentials));
          set({
            user: data.user,
            accessToken: data.accessToken,
            refreshToken: data.refreshToken,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error) {
          const message = error instanceof Error ? error.message : 'Unable to login';
          set({ error: message, isLoading: false, isAuthenticated: false });
          throw error;
        }
      },
      async register(payload) {
        set({ isLoading: true, error: null });
        try {
          const data = await withErrorHandling<AuthResponse>(() => client.post('/auth/register', payload));
          set({
            user: data.user,
            accessToken: data.accessToken,
            refreshToken: data.refreshToken,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error) {
          const message = error instanceof Error ? error.message : 'Unable to register';
          set({ error: message, isLoading: false });
          throw error;
        }
      },
      logout() {
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
          error: null,
        });
      },
      async refreshTokens() {
        const refreshTokenValue = get().refreshToken;
        if (!refreshTokenValue) {
          set({
            accessToken: null,
            refreshToken: null,
            user: null,
            isAuthenticated: false,
          });
          return null;
        }
        try {
          const data = await withErrorHandling<RefreshResponse>(() =>
            plainClient.post('/auth/refresh', { refreshToken: refreshTokenValue }),
          );
          set({
            accessToken: data.accessToken,
            refreshToken: data.refreshToken ?? refreshTokenValue,
            user: data.user ?? get().user,
            isAuthenticated: true,
          });
          return data.accessToken;
        } catch (error) {
          set({
            accessToken: null,
            refreshToken: null,
            user: null,
            isAuthenticated: false,
          });
          return null;
        }
      },
      setHydrated() {
        const token = get().accessToken;
        set({ hasHydrated: true, isAuthenticated: Boolean(token) });
      },
      clearError() {
        set({ error: null });
      },
    }),
    {
      name: STORAGE_KEY,
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
      }),
      onRehydrateStorage: () => (state) => {
        state?.setHydrated();
      },
    },
  ),
);

registerAuthHandlers({
  getAccessToken: () => useAuthStore.getState().accessToken,
  refreshAccessToken: () => useAuthStore.getState().refreshTokens(),
  onLogout: () => useAuthStore.getState().logout(),
});

export const selectIsAuthenticated = () => useAuthStore.getState().isAuthenticated;
