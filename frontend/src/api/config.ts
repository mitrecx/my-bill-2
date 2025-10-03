// API配置
export const API_CONFIG = {
  // 开发环境API地址
  BASE_URL: 'http://localhost:8000',
  
  // 生产环境API地址 (部署的服务器)
  PROD_BASE_URL: 'https://jo.mitrecx.top',
  
  // 请求超时时间 (5分钟，支持大文件上传)
  TIMEOUT: 300000,
  
  // Token存储key
  TOKEN_KEY: 'bills_access_token',
  
  // 用户信息存储key
  USER_KEY: 'bills_user_info',
}

// 获取当前API基础URL
export const getApiBaseUrl = (): string => {
  // 仅当显式开启使用生产API时，才返回生产URL；否则统一使用本地开发URL，避免预览环境误连生产导致权限不一致
  if (import.meta.env.VITE_USE_PROD_API === 'true') {
    return API_CONFIG.PROD_BASE_URL;
  }
  return API_CONFIG.BASE_URL;
}

// API端点
export const API_ENDPOINTS = {
  // 认证相关
  AUTH: {
    LOGIN: '/api/v1/auth/login',
    REGISTER: '/api/v1/auth/register',
    ME: '/api/v1/auth/me',
    REFRESH: '/api/v1/auth/refresh',
  },
  
  // 用户相关
  USERS: {
    BASE: '/api/v1/users',
    PROFILE: '/api/v1/users/profile',
  },
  
  // 家庭相关
  FAMILIES: {
    BASE: '/api/v1/families',
    MEMBERS: (familyId: number) => `/api/v1/families/${familyId}/members`,
    JOIN: (familyId: number) => `/api/v1/families/${familyId}/join`,
    LEAVE: (familyId: number) => `/api/v1/families/${familyId}/leave`,
  },
  
  // 账单相关
  BILLS: {
    BASE: '/api/v1/bills',
    STATS: '/api/v1/bills/stats',
    FINANCE_SUMMARY: '/api/v1/bills/finance-summary',
    FINANCE_SUMMARY_BATCH: '/api/v1/bills/finance-summary/batch',
    CATEGORIES: '/api/v1/bills/categories',
    CATEGORIES_BY_ID: (id: number) => `/api/v1/bills/categories/${id}`,
    CATEGORIES_DELETE: (id: number) => `/api/v1/bills/categories/${id}/delete`,
    CATEGORIES_RESTORE: (id: number) => `/api/v1/bills/categories/${id}/restore`,
    YEARLY_EXPENSE_CHART: '/api/v1/bills/yearly-expense-chart',
    MONTHLY_EXPENSE_TREND: '/api/v1/bills/monthly-expense-trend', // 新增
    AVAILABLE_YEARS: '/api/v1/bills/available-years', // 新增：获取可用年份
    BY_ID: (id: number) => `/api/v1/bills/${id}`,
    BATCH: '/api/v1/bills/batch', // 新增：批量更新
  },
  
  // 文件上传相关
  UPLOAD: {
    BASE: '/api/v1/upload',
    PREVIEW: '/api/v1/upload/preview',
    CONFIRM: '/api/v1/upload/confirm',
    HISTORY: '/api/v1/upload/history',
  },
  
  // 系统配置相关
  SYSTEM_CONFIG: {
    BASE: '/api/v1/system-config',
    DEFAULT_PASSWORD: '/api/v1/system-config/default-password',
    INITIALIZE: '/api/v1/system-config/initialize',
  },
  
  // 分类规则相关
  CLASSIFICATION_RULES: {
    BASE: '/api/v1/classification-rules',
    SOURCE_TYPES: '/api/v1/classification-rules/source-types/options',
    TOGGLE_STATUS: (id: number) => `/api/v1/classification-rules/${id}/toggle`,
    BATCH: '/api/v1/classification-rules/batch',
  },

  // 消息相关
  MESSAGES: {
    BASE: '/api/v1/messages',
    FOR_USER: (userId: number) => `/api/v1/messages/user/${userId}`,
    UNREAD_COUNT: '/api/v1/messages/unread-count',
    BY_ID: (id: number) => `/api/v1/messages/${id}`,
    ACTION: (id: number) => `/api/v1/messages/${id}/actions`,
  },
}