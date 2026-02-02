import axios, {
  AxiosError,
  AxiosHeaders,
  AxiosInstance,
  AxiosRequestConfig,
  AxiosRequestHeaders,
  InternalAxiosRequestConfig,
} from 'axios';

type RefreshHandler = () => Promise<string | null>;
type LogoutHandler = () => void;
type TokenGetter = () => string | null;

type AuthHandlers = {
  getAccessToken: TokenGetter;
  refreshAccessToken: RefreshHandler;
  onLogout?: LogoutHandler;
};

const defaultBaseUrl = 'http://localhost:8000/api';
export const API_BASE_URL = import.meta.env.VITE_API_URL ?? defaultBaseUrl;

export const client: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  timeout: 15000,
});

export const plainClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  timeout: 15000,
});

let getToken: TokenGetter = () => null;
let refreshToken: RefreshHandler = async () => null;
let logoutHandler: LogoutHandler | undefined;
let isRefreshing = false;
let pendingQueue: Array<(token: string | null) => void> = [];

type RetriableRequest = InternalAxiosRequestConfig & {
  _retry?: boolean;
};

const ensureHeaders = (headers?: AxiosRequestHeaders): AxiosHeaders => {
  if (!headers) {
    return new AxiosHeaders();
  }
  return headers instanceof AxiosHeaders ? headers : new AxiosHeaders(headers);
};

const applyAuthHeader = (request: RetriableRequest, token: string): void => {
  const headers = ensureHeaders(request.headers as AxiosRequestHeaders | undefined);
  headers.set('Authorization', `Bearer ${token}`);
  request.headers = headers;
};

export const registerAuthHandlers = ({
  getAccessToken,
  refreshAccessToken,
  onLogout,
}: AuthHandlers): void => {
  getToken = getAccessToken;
  refreshToken = refreshAccessToken;
  logoutHandler = onLogout;
};

client.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = getToken();
  if (token) {
    const headers = ensureHeaders(config.headers as AxiosRequestHeaders | undefined);
    headers.set('Authorization', `Bearer ${token}`);
    config.headers = headers;
  }
  return config;
});

client.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const status = error.response?.status;
    const originalRequest = error.config as RetriableRequest | undefined;

    if (status === 401 && originalRequest && !originalRequest._retry) {
      if (!getToken()) {
        logoutHandler?.();
        return Promise.reject(error);
      }

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          pendingQueue.push((tokenValue) => {
            if (!tokenValue) {
              reject(error);
              return;
            }
            applyAuthHeader(originalRequest, tokenValue);
            resolve(client(originalRequest));
          });
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const newToken = await refreshToken();
        pendingQueue.forEach((cb) => cb(newToken));
        pendingQueue = [];

        if (newToken) {
          applyAuthHeader(originalRequest, newToken);
          return client(originalRequest);
        }
        logoutHandler?.();
        return Promise.reject(error);
      } catch (refreshError) {
        pendingQueue.forEach((cb) => cb(null));
        pendingQueue = [];
        logoutHandler?.();
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  },
);

export const withErrorHandling = async <T>(request: () => Promise<{ data: T }>): Promise<T> => {
  try {
    const response = await request();
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const message =
        (error.response?.data as { message?: string } | undefined)?.message ??
        error.message ??
        'Unexpected error occurred';
      throw new Error(message);
    }
    throw error;
  }
};

export const setAuthHeader = (config: AxiosRequestConfig, token: string | null): AxiosRequestConfig => {
  if (!token) {
    return config;
  }
  const headers = ensureHeaders(config.headers as AxiosRequestHeaders | undefined);
  headers.set('Authorization', `Bearer ${token}`);
  return {
    ...config,
    headers,
  };
};
