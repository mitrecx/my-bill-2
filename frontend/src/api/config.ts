// API配置
export const API_CONFIG = {
  // 开发环境API地址
  BASE_URL: 'http://localhost:8000/api/v1',
  
  // 生产环境API地址 (部署的服务器)
  PROD_BASE_URL: 'http://jo.mitrecx.top:8000/api/v1',
  
  // 请求超时时间
  TIMEOUT: 30000,
  
  // Token存储key
  TOKEN_KEY: 'bills_access_token',
  
  // 用户信息存储key
  USER_KEY: 'bills_user_info',
}

// 获取当前API基础URL
export const getApiBaseUrl = (): string => {
  // 在生产环境或者配置了生产服务器时使用生产URL
  if (import.meta.env.PROD || import.meta.env.VITE_USE_PROD_API === 'true') {
    return API_CONFIG.PROD_BASE_URL;
  }
  // 开发环境使用开发环境URL
  return API_CONFIG.BASE_URL;
}

// API端点
export const API_ENDPOINTS = {
  // 认证相关
  AUTH: {
    LOGIN: '/auth/login',
    REGISTER: '/auth/register',
    ME: '/auth/me',
    REFRESH: '/auth/refresh',
  },
  
  // 用户相关
  USERS: {
    BASE: '/users',
    PROFILE: '/users/profile',
  },
  
  // 家庭相关
  FAMILIES: {
    BASE: '/families',
    MEMBERS: (familyId: number) => `/families/${familyId}/members`,
    JOIN: (familyId: number) => `/families/${familyId}/join`,
    LEAVE: (familyId: number) => `/families/${familyId}/leave`,
  },
  
  // 账单相关
  BILLS: {
    BASE: '/bills',
    STATS: '/bills/stats',
    CATEGORIES: '/bills/categories',
    BY_ID: (id: number) => `/bills/${id}`,
  },
  
  // 文件上传相关
  UPLOAD: {
    BASE: '/upload',
    PREVIEW: '/upload/preview',
    CONFIRM: '/upload/confirm',
    HISTORY: '/upload/history',
  },
}