// User and Authentication Types
export interface User {
  id: string;
  username: string;
  email: string;
  subscription_level: 'trial' | 'basic' | 'premium' | 'enterprise';
  subscription_end?: string;
  api_key: string;
  trial_remaining_days?: number;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  username: string;
  api_key: string;
  subscription_level: string;
  subscription_end?: string;
  access_token: string;
  refresh_token: string;
}

// Prediction Types
export interface Prediction {
  id: string;
  symbol: string;
  trend_type: 'bullish' | 'bearish' | 'neutral';
  target_price: number;
  expected_gain_pct: number;
  expected_gain_days?: number;
  confidence_score: number;
  confidence?: number;
  status: 'active' | 'completed' | 'expired';
  remaining_time?: string;
  description: string;
  created_at: string;
}

export interface PredictionFilters {
  trend_type?: string;
  min_confidence?: number;
  page?: number;
  per_page?: number;
}

export interface PredictionResponse {
  items: Prediction[];
  filters?: {
    available_trend_types: string[];
    min_confidence_range: [number, number];
  };
  pagination?: {
    page: number;
    per_page: number;
    total: number;
    pages: number;
  };
}

// Technical Analysis Types
export interface TechnicalAnalysis {
  rsi: number;
  macd: number;
  signal: string;
  created_at: string;
}

// API Response Types
export interface ApiResponse<T = any> {
  data: T;
  message?: string;
  error?: string;
}

// Notification Types
export interface Notification {
  id: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  timestamp: number;
}

// App State Types
export interface AppState {
  theme: 'light' | 'dark';
  notifications: Notification[];
  loading: boolean;
}

// Route Types
export interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredSubscription?: User['subscription_level'];
}