import axios, { type AxiosInstance, type AxiosRequestConfig, type AxiosResponse } from 'axios';
import { API_CONFIG, getApiBaseUrl } from './config';
import type { ApiResponse } from '../types';

// 创建axios实例
const createApiClient = (): AxiosInstance => {
  // 自定义查询参数序列化：数组参数使用重复键格式 ?key=a&key=b，跳过空数组/undefined/null
  const serializeParams = (params: Record<string, any> | undefined): string => {
    const searchParams = new URLSearchParams();
    if (!params) return '';
    Object.entries(params).forEach(([key, value]) => {
      if (value === undefined || value === null) return;
      if (Array.isArray(value)) {
        if (value.length === 0) return;
        value.forEach((v) => {
          if (v === undefined || v === null) return;
          searchParams.append(key, String(v));
        });
      } else {
        searchParams.append(key, String(value));
      }
    });
    return searchParams.toString();
  };

  const client = axios.create({
    baseURL: getApiBaseUrl(),
    timeout: API_CONFIG.TIMEOUT,
    headers: {
      'Content-Type': 'application/json',
      'Cache-Control': 'no-cache', // 禁用所有请求的缓存，防止数据不刷新
    },
    paramsSerializer: {
      serialize: serializeParams,
    },
  });

  // 请求拦截器 - 添加token
  client.interceptors.request.use(
    (config) => {
      const token = localStorage.getItem(API_CONFIG.TOKEN_KEY);
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error) => {
      return Promise.reject(error);
    }
  );

  // 响应拦截器
  client.interceptors.response.use(
    (response: AxiosResponse) => {
      // 检查是否有新的token
      const newToken = response.headers['x-new-token'];
      if (newToken) {
        // 自动更新本地存储的token
        TokenManager.setToken(newToken);
        console.log('Token已自动刷新');
      }
      return response;
    },
    (error) => {
      // 处理401错误
      if (error.response?.status === 401) {
        // 清除本地token和用户信息
        TokenManager.removeToken();
        UserManager.removeUser();
        
        // 如果不是在登录页面，跳转到登录页面
        if (window.location.pathname !== '/login') {
          window.location.href = '/login';
        }
        
        error.friendlyMessage = '登录已过期，请重新登录';
      } else if (error.response?.status === 403) {
        // 权限不足
        error.friendlyMessage = '权限不足，无法访问该资源';
      } else if (error.response?.status >= 500) {
        // 服务器错误
        error.friendlyMessage = '服务器内部错误，请稍后重试';
      } else if (error.response?.status >= 400) {
        // 客户端错误
        error.friendlyMessage = error.response?.data?.message || '请求失败，请检查输入信息';
      } else if (!error.response) {
        // 无响应（可能是网络问题）
        error.friendlyMessage = '无法连接到服务器，请检查网络连接';
      }
      
      return Promise.reject(error);
    }
  );

  return client;
};

// 创建API客户端实例
export const apiClient = createApiClient();

// 通用API请求方法
export class ApiClient {
  static async get<T>(url: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    const response = await apiClient.get(url, config);
    return response.data;
  }

  static async post<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    const response = await apiClient.post(url, data, config);
    return response.data;
  }

  static async put<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    const response = await apiClient.put(url, data, config);
    return response.data;
  }

  static async patch<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    const response = await apiClient.patch(url, data, config);
    return response.data;
  }

  static async delete<T>(url: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    const response = await apiClient.delete(url, config);
    return response.data;
  }

  // 文件上传专用方法
  static async upload<T>(
    url: string,
    file: File,
    onProgress?: (progress: number) => void,
    extraFields?: Record<string, string | boolean>,
  ): Promise<ApiResponse<T>> {
    const formData = new FormData();
    formData.append('file', file);
    if (extraFields) {
      Object.entries(extraFields).forEach(([key, value]) => {
        formData.append(key, String(value));
      });
    }

    const config: AxiosRequestConfig = {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(progress);
        }
      },
    };

    const response = await apiClient.post(url, formData, config);
    return response.data;
  }
}

// Token 管理工具
export const TokenManager = {
  getToken(): string | null {
    return localStorage.getItem(API_CONFIG.TOKEN_KEY);
  },

  setToken(token: string): void {
    localStorage.setItem(API_CONFIG.TOKEN_KEY, token);
  },

  removeToken(): void {
    localStorage.removeItem(API_CONFIG.TOKEN_KEY);
  },

  isAuthenticated(): boolean {
    return !!this.getToken();
  },
};

// 用户信息管理工具
export const UserManager = {
  getUser(): any | null {
    try {
    const userStr = localStorage.getItem(API_CONFIG.USER_KEY);
      if (!userStr || userStr === 'undefined' || userStr === 'null') {
        return null;
      }
      return JSON.parse(userStr);
    } catch (error) {
      // 如果解析失败，清除无效数据并返回null
      console.warn('Failed to parse user data from localStorage:', error);
      localStorage.removeItem(API_CONFIG.USER_KEY);
      return null;
    }
  },

  setUser(user: any): void {
    if (user) {
    localStorage.setItem(API_CONFIG.USER_KEY, JSON.stringify(user));
    }
  },

  removeUser(): void {
    localStorage.removeItem(API_CONFIG.USER_KEY);
  },

  logout(): void {
    TokenManager.removeToken();
    this.removeUser();
  },
};