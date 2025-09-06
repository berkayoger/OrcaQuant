import axios, { AxiosResponse } from 'axios';
import { store } from '../store/store';
import { logout, setTokens } from '../store/slices/authSlice';
import { addNotification } from '../store/slices/appSlice';
import type { 
  LoginRequest, 
  LoginResponse, 
  PredictionFilters, 
  PredictionResponse,
  TechnicalAnalysis 
} from '../types';

class ApiClient {
  private baseURL: string;
  private refreshPromise: Promise<boolean> | null = null;
  private readonly timeout = 15000;

  constructor() {
    // Use environment variable or fallback to default
    this.baseURL = import.meta.env.VITE_API_BASE_URL || '/api';
    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor
    axios.interceptors.request.use(
      (config) => {
        const state = store.getState();
        const token = state.auth.token;
        
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        
        // Add CSRF token if available
        const csrfToken = this.getCSRFToken();
        if (csrfToken) {
          config.headers['X-CSRF-Token'] = csrfToken;
        }

        config.headers['X-Requested-With'] = 'XMLHttpRequest';
        config.timeout = this.timeout;
        
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor
    axios.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;

        // Handle 401 errors with token refresh
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;
          
          const refreshed = await this.refreshAuthToken();
          if (refreshed) {
            const state = store.getState();
            const newToken = state.auth.token;
            if (newToken) {
              originalRequest.headers.Authorization = `Bearer ${newToken}`;
              return axios(originalRequest);
            }
          }
        }

        // Handle plan limit exceeded
        if (error.response?.status === 429) {
          this.handlePlanLimitExceeded(error.response.data);
        }

        // Handle insufficient permissions
        if (error.response?.status === 403) {
          this.handleInsufficientPermissions(error.response.data);
        }

        return Promise.reject(error);
      }
    );
  }

  private getCSRFToken(): string | null {
    const metaToken = document.querySelector('meta[name="csrf-token"]');
    if (metaToken) {
      return metaToken.getAttribute('content');
    }
    
    const match = document.cookie.match(/csrf_token=([^;]+)/);
    return match ? match[1] : null;
  }

  private async refreshAuthToken(): Promise<boolean> {
    // Prevent multiple simultaneous refresh attempts
    if (this.refreshPromise) {
      return this.refreshPromise;
    }

    this.refreshPromise = (async () => {
      try {
        const state = store.getState();
        const refreshToken = state.auth.refreshToken;

        if (!refreshToken) {
          store.dispatch(logout());
          return false;
        }

        const response = await axios.post(`${this.baseURL}/auth/refresh`, {
          refresh_token: refreshToken
        }, {
          headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
          }
        });

        if (response.data.access_token) {
          store.dispatch(setTokens({
            token: response.data.access_token,
            refreshToken: response.data.refresh_token || refreshToken
          }));
          return true;
        }
      } catch (error) {
        console.error('Token refresh failed:', error);
        store.dispatch(logout());
      } finally {
        this.refreshPromise = null;
      }
      
      return false;
    })();

    return this.refreshPromise;
  }

  private handlePlanLimitExceeded(errorData: any) {
    const message = `Plan limitiniz aşıldı: ${errorData.message || ''}`.trim();
    store.dispatch(addNotification({
      message,
      type: 'warning'
    }));

    if (errorData.upgrade_url) {
      setTimeout(() => {
        if (confirm('Planınızı yükseltmek ister misiniz?')) {
          window.location.href = errorData.upgrade_url;
        }
      }, 1200);
    }
  }

  private handleInsufficientPermissions(errorData: any) {
    const reason = errorData?.reason ? ` (Sebep: ${errorData.reason})` : '';
    const message = `Bu işlem için yetkiniz bulunmuyor${reason}.`;
    store.dispatch(addNotification({
      message,
      type: 'error'
    }));
  }

  // Authentication methods
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response: AxiosResponse<LoginResponse> = await axios.post(
      `${this.baseURL}/auth/login`,
      credentials
    );
    return response.data;
  }

  async logout(): Promise<void> {
    try {
      await axios.post(`${this.baseURL}/auth/logout`);
    } catch (error) {
      console.error('Logout API call failed:', error);
    }
  }

  // Prediction methods
  async getPredictions(filters: PredictionFilters = {}): Promise<PredictionResponse> {
    const params = new URLSearchParams();
    
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        params.append(key, value.toString());
      }
    });

    const response: AxiosResponse<PredictionResponse> = await axios.get(
      `${this.baseURL}/admin/predictions/public?${params.toString()}`
    );
    return response.data;
  }

  // Technical Analysis methods
  async getTechnicalAnalysis(): Promise<TechnicalAnalysis> {
    const response: AxiosResponse<TechnicalAnalysis> = await axios.get(
      `${this.baseURL}/technical/latest`
    );
    return response.data;
  }

  // Generic methods
  async get<T = any>(endpoint: string): Promise<T> {
    const response: AxiosResponse<T> = await axios.get(`${this.baseURL}${endpoint}`);
    return response.data;
  }

  async post<T = any>(endpoint: string, data?: any): Promise<T> {
    const response: AxiosResponse<T> = await axios.post(`${this.baseURL}${endpoint}`, data);
    return response.data;
  }

  async put<T = any>(endpoint: string, data?: any): Promise<T> {
    const response: AxiosResponse<T> = await axios.put(`${this.baseURL}${endpoint}`, data);
    return response.data;
  }

  async delete<T = any>(endpoint: string): Promise<T> {
    const response: AxiosResponse<T> = await axios.delete(`${this.baseURL}${endpoint}`);
    return response.data;
  }
}

// Export singleton instance
export const apiClient = new ApiClient();
export default apiClient;