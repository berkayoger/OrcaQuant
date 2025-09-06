import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import type { AppState, Notification } from '../../types';

// Initial state
const initialState: AppState = {
  theme: 'light',
  notifications: [],
  loading: false,
};

// Helper to generate unique IDs
const generateId = () => Date.now().toString(36) + Math.random().toString(36).substr(2);

// Create slice
const appSlice = createSlice({
  name: 'app',
  initialState,
  reducers: {
    setTheme: (state, action: PayloadAction<'light' | 'dark'>) => {
      state.theme = action.payload;
      localStorage.setItem('theme', action.payload);
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    addNotification: (state, action: PayloadAction<Omit<Notification, 'id' | 'timestamp'>>) => {
      const notification: Notification = {
        ...action.payload,
        id: generateId(),
        timestamp: Date.now(),
      };
      state.notifications.push(notification);
    },
    removeNotification: (state, action: PayloadAction<string>) => {
      state.notifications = state.notifications.filter(n => n.id !== action.payload);
    },
    clearNotifications: (state) => {
      state.notifications = [];
    },
  },
});

export const { 
  setTheme, 
  setLoading, 
  addNotification, 
  removeNotification, 
  clearNotifications 
} = appSlice.actions;

export default appSlice.reducer;