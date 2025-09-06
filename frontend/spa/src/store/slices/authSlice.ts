import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { apiClient } from '../../services/api';
import type { AuthState, User, LoginRequest, LoginResponse } from '../../types';

// Initial state
const initialState: AuthState = {
  user: null,
  token: localStorage.getItem('auth_token'),
  refreshToken: localStorage.getItem('refresh_token'),
  isAuthenticated: false,
  isLoading: false,
  error: null,
};

// Async thunks
export const loginAsync = createAsyncThunk(
  'auth/login',
  async (credentials: LoginRequest, { rejectWithValue }) => {
    try {
      const response = await apiClient.login(credentials);
      
      // Persist tokens
      localStorage.setItem('auth_token', response.access_token);
      localStorage.setItem('refresh_token', response.refresh_token);
      
      // Also persist legacy session storage for backward compatibility
      sessionStorage.setItem('ytdcrypto_username', response.username);
      sessionStorage.setItem('ytdcrypto_api_key', response.api_key);
      sessionStorage.setItem('ytdcrypto_subscription_level', response.subscription_level);
      
      if (response.subscription_end) {
        const endDate = new Date(response.subscription_end);
        const now = new Date();
        const diffInDays = Math.ceil((endDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
        sessionStorage.setItem('ytdcrypto_trial_remaining_days', diffInDays.toString());
      }
      
      return response;
    } catch (error: any) {
      const message = error.response?.data?.error || 
                     error.response?.data?.message || 
                     'Giriş sırasında bir hata oluştu';
      return rejectWithValue(message);
    }
  }
);

export const logoutAsync = createAsyncThunk(
  'auth/logout',
  async (_, { dispatch }) => {
    try {
      await apiClient.logout();
    } catch (error) {
      console.error('Logout API error:', error);
    } finally {
      // Clear storage regardless of API call result
      localStorage.removeItem('auth_token');
      localStorage.removeItem('refresh_token');
      sessionStorage.removeItem('ytdcrypto_username');
      sessionStorage.removeItem('ytdcrypto_api_key');
      sessionStorage.removeItem('ytdcrypto_subscription_level');
      sessionStorage.removeItem('ytdcrypto_trial_remaining_days');
    }
  }
);

// Check if user is authenticated on app start
export const checkAuthAsync = createAsyncThunk(
  'auth/checkAuth',
  async (_, { getState, rejectWithValue }) => {
    const state = getState() as { auth: AuthState };
    const token = state.auth.token;
    
    if (!token) {
      return rejectWithValue('No token found');
    }

    try {
      // Try to decode JWT to check expiry
      const payload = JSON.parse(atob(token.split('.')[1]));
      const isExpired = payload.exp * 1000 < Date.now();
      
      if (isExpired) {
        return rejectWithValue('Token expired');
      }
      
      // If token is valid, reconstruct user from session storage
      const username = sessionStorage.getItem('ytdcrypto_username');
      const apiKey = sessionStorage.getItem('ytdcrypto_api_key');
      const subscriptionLevel = sessionStorage.getItem('ytdcrypto_subscription_level');
      const subscriptionEnd = sessionStorage.getItem('ytdcrypto_subscription_end');
      const trialDays = sessionStorage.getItem('ytdcrypto_trial_remaining_days');
      
      if (username && apiKey && subscriptionLevel) {
        return {
          id: payload.sub || payload.user_id || '1',
          username,
          email: payload.email || `${username}@example.com`,
          subscription_level: subscriptionLevel as User['subscription_level'],
          subscription_end: subscriptionEnd || undefined,
          api_key: apiKey,
          trial_remaining_days: trialDays ? parseInt(trialDays) : undefined,
        } as User;
      }
      
      return rejectWithValue('Incomplete user data');
    } catch (error) {
      return rejectWithValue('Invalid token');
    }
  }
);

// Create slice
const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    setTokens: (state, action: PayloadAction<{ token: string; refreshToken: string }>) => {
      state.token = action.payload.token;
      state.refreshToken = action.payload.refreshToken;
      localStorage.setItem('auth_token', action.payload.token);
      localStorage.setItem('refresh_token', action.payload.refreshToken);
    },
    logout: (state) => {
      state.user = null;
      state.token = null;
      state.refreshToken = null;
      state.isAuthenticated = false;
      state.isLoading = false;
      state.error = null;
      
      // Clear storage
      localStorage.removeItem('auth_token');
      localStorage.removeItem('refresh_token');
      sessionStorage.removeItem('ytdcrypto_username');
      sessionStorage.removeItem('ytdcrypto_api_key');
      sessionStorage.removeItem('ytdcrypto_subscription_level');
      sessionStorage.removeItem('ytdcrypto_trial_remaining_days');
    },
  },
  extraReducers: (builder) => {
    builder
      // Login
      .addCase(loginAsync.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(loginAsync.fulfilled, (state, action) => {
        state.isLoading = false;
        state.isAuthenticated = true;
        state.token = action.payload.access_token;
        state.refreshToken = action.payload.refresh_token;
        state.user = {
          id: '1', // Will be provided by backend
          username: action.payload.username,
          email: `${action.payload.username}@example.com`, // Will be provided by backend
          subscription_level: action.payload.subscription_level as User['subscription_level'],
          subscription_end: action.payload.subscription_end,
          api_key: action.payload.api_key,
        };
        state.error = null;
      })
      .addCase(loginAsync.rejected, (state, action) => {
        state.isLoading = false;
        state.isAuthenticated = false;
        state.error = action.payload as string;
      })
      // Logout
      .addCase(logoutAsync.fulfilled, (state) => {
        state.user = null;
        state.token = null;
        state.refreshToken = null;
        state.isAuthenticated = false;
        state.isLoading = false;
        state.error = null;
      })
      // Check auth
      .addCase(checkAuthAsync.pending, (state) => {
        state.isLoading = true;
      })
      .addCase(checkAuthAsync.fulfilled, (state, action) => {
        state.isLoading = false;
        state.isAuthenticated = true;
        state.user = action.payload;
        state.error = null;
      })
      .addCase(checkAuthAsync.rejected, (state) => {
        state.isLoading = false;
        state.isAuthenticated = false;
        state.user = null;
        state.token = null;
        state.refreshToken = null;
        localStorage.removeItem('auth_token');
        localStorage.removeItem('refresh_token');
      });
  },
});

export const { clearError, setTokens, logout } = authSlice.actions;
export default authSlice.reducer;