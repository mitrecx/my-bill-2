import axios, { type AxiosInstance, type AxiosRequestConfig, type AxiosResponse } from 'axios';
import { API_CONFIG, getApiBaseUrl } from './config';
import type { ApiResponse } from '../types';

// 创建axios实例
const createApiClient = (): AxiosInstance => {
  const client = axios.create({
    baseURL: getApiBaseUrl(),
    timeout: API_CONFIG.TIMEOUT,
    headers: {
      'Content-Type': 'application/json',
      'Cache-Control': 'no-cache', // 禁用所有请求的缓存，防止数据不刷新
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

  // 响应拦截器 - 处理错误
  client.interceptors.response.use(
    (response: AxiosResponse) => {
      return response;
    },
    (error) => {
      // 处理401未授权错误
      if (error.response?.status === 401) {
        // 清除本地存储的token和用户信息
        localStorage.removeItem(API_CONFIG.TOKEN_KEY);
        localStorage.removeItem(API_CONFIG.USER_KEY);
        
        // 重定向到登录页面
        if (window.location.pathname !== '/login') {
          window.location.href = '/login';
        }
      }
      
      // 处理网络错误和服务器错误，提供友好的错误信息
      if (error.code === 'ECONNABORTED' || error.code === 'ERR_NETWORK') {
        // 网络超时或连接失败
        error.friendlyMessage = '网络连接失败，请检查网络连接后重试';
      } else if (error.response?.status === 503 && error.response?.data?.error_code === 'DATABASE_CONNECTION_ERROR') {
        // 数据库连接错误
        error.friendlyMessage = error.response.data.message || '数据库服务暂时不可用，请稍后重试';
      } else if (error.response?.status >= 500) {
        // 服务器内部错误
        error.friendlyMessage = error.response?.data?.message || '服务器内部错误，请稍后重试';
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
  static async upload<T>(url: string, file: File, onProgress?: (progress: number) => void): Promise<ApiResponse<T>> {
    const formData = new FormData();
    formData.append('file', file);

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