import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

export const api = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add CSRF token if available
    const csrfToken = sessionStorage.getItem('csrf_token');
    if (csrfToken) {
      (config.headers as any)['X-CSRF-Token'] = csrfToken;
    }
    
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config as any;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const response = await axios.post(`${API_BASE}/auth/refresh`);
        const { access_token } = response.data;
        
        // Update token
        (api.defaults.headers as any).common['Authorization'] = `Bearer ${access_token}`;
        originalRequest.headers['Authorization'] = `Bearer ${access_token}`;
        
        // Update store
        const { useAuthStore } = await import('../store/auth');
        useAuthStore.setState({ token: access_token });
        
        return api(originalRequest);
      } catch (refreshError) {
        // Refresh failed, logout user
        const { useAuthStore } = await import('../store/auth');
        useAuthStore.getState().logout();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);

// API Services
export const cryptoAPI = {
  analyze: (data: any) => api.post('/api/decision/score-multi', data),
  getPortfolio: () => api.get('/api/portfolio'),
  getTransactions: () => api.get('/api/portfolio/transactions'),
  getMarketData: () => api.get('/api/market/current'),
  getSymbols: () => api.get('/api/market/symbols'),
  adminSummary: () => api.get('/api/admin/analytics/summary')
};

export const paymentAPI = {
  getPlans: () => api.get('/api/payment/plans'),
  createCheckout: (planId: string) => api.post('/api/payment/checkout', { planId }),
  getStatus: (sessionId: string) => api.get(`/api/payment/status?sessionId=${sessionId}`)
};
