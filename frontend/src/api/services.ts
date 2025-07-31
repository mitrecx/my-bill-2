import { ApiClient } from './client';
import { API_ENDPOINTS } from './config';
import type {
  AuthResponse,
  LoginRequest,
  RegisterRequest,
  User,
  Bill,
  BillCategory,
  BillListQueryParams,
  PaginatedResponse,
  BillStats,
  CategoryStats,
  Family,
  FamilyMember,
  UploadRecord,
  UploadResponse,
  ApiResponse, // 新增ApiResponse类型导入
  SystemConfig,
  SystemConfigCreate,
  SystemConfigUpdate,
  DefaultPasswordConfig,
  SystemConfigResponse,
} from '../types';
import type {
  Message,
  MessageListResponse,
  MessageUpdate,
  MessageActionCreate,
} from '../types/message';

// 认证服务
export const AuthService = {
  async login(credentials: LoginRequest): Promise<ApiResponse<AuthResponse['data']>> {
    const response = await ApiClient.post<AuthResponse['data']>(API_ENDPOINTS.AUTH.LOGIN, credentials, {
      headers: {
        'Content-Type': 'application/json',
      },
    });
    return response; // 返回完整响应，不要 .data
  },

  async register(userData: RegisterRequest): Promise<ApiResponse<AuthResponse['data']>> {
    const response = await ApiClient.post<AuthResponse['data']>(API_ENDPOINTS.AUTH.REGISTER, userData);
    return response;
  },

  async getCurrentUser(): Promise<ApiResponse<User>> {
    const response = await ApiClient.get<User>(API_ENDPOINTS.AUTH.ME);
    return response;
  },

  async refreshToken(): Promise<ApiResponse<AuthResponse['data']>> {
    const response = await ApiClient.post<AuthResponse['data']>(API_ENDPOINTS.AUTH.REFRESH);
    return response;
  },
};

// 用户服务
export const UserService = {
  async getProfile(): Promise<ApiResponse<User>> {
    const response = await ApiClient.get<User>(API_ENDPOINTS.USERS.PROFILE);
    return response;
  },

  async updateProfile(userData: Partial<User>): Promise<ApiResponse<User>> {
    const response = await ApiClient.put<User>(API_ENDPOINTS.USERS.PROFILE, userData);
    return response;
  },

  // ================= 管理员相关 =================
  async listUsers(params?: { 
    page?: number; 
    size?: number; 
    search?: string;
    username?: string;
    full_name?: string;
    role?: string;
  }): Promise<ApiResponse<PaginatedResponse<User>>> {
    const response = await ApiClient.get<PaginatedResponse<User>>(API_ENDPOINTS.USERS.BASE, { params });
    return response;
  },

  async createUser(userData: { username: string; password: string; full_name?: string; email?: string }): Promise<ApiResponse<User>> {
    const response = await ApiClient.post<User>(API_ENDPOINTS.USERS.BASE, userData);
    return response;
  },

  async updateUser(id: number, userData: { password?: string; full_name?: string; email?: string, is_active?: boolean }): Promise<ApiResponse<User>> {
    const response = await ApiClient.put<User>(`${API_ENDPOINTS.USERS.BASE}/${id}`, userData);
    return response;
  },

  async deleteUser(id: number): Promise<ApiResponse<string>> {
    const response = await ApiClient.delete<string>(`${API_ENDPOINTS.USERS.BASE}/${id}`);
    return response;
  },
};

// 家庭服务
export const FamilyService = {
  async getFamilies(): Promise<ApiResponse<Family[]>> {
    const response = await ApiClient.get<Family[]>('/families');
    return response;
  },

  async createFamily(familyData: { family_name: string; description?: string; invite_usernames?: string[] }): Promise<Family> {
    const response = await ApiClient.post<Family>('/families/', familyData);
    return response.data;
  },

  async updateFamily(familyId: number, familyData: { family_name?: string; description?: string }): Promise<Family> {
    const response = await ApiClient.put<Family>(`/families/${familyId}`, familyData);
    return response.data;
  },

  async deleteFamily(familyId: number): Promise<void> {
    await ApiClient.delete(`/families/${familyId}`);
  },

  async getFamilyMembers(familyId: number): Promise<{ members: FamilyMember[] }> {
    const response = await ApiClient.get<{ members: FamilyMember[] }>(`/families/${familyId}/members`);
    return response.data;
  },

  async joinFamily(familyId: number): Promise<FamilyMember> {
    const response = await ApiClient.post<FamilyMember>(`/families/${familyId}/join`);
    return response.data;
  },

  async leaveFamily(familyId: number): Promise<void> {
    await ApiClient.delete(`/families/${familyId}/leave`);
  },

  async searchUsers(query: string): Promise<{ id: number; username: string; full_name?: string; email: string }[]> {
    const response = await ApiClient.get<{ id: number; username: string; full_name?: string; email: string }[]>('/families/search-users', {
      params: { q: query }
    });
    return response.data;
  },
};

// 账单服务
export const BillService = {
  async getBills(params?: BillListQueryParams): Promise<ApiResponse<PaginatedResponse<Bill>>> {
    const response = await ApiClient.get<PaginatedResponse<Bill>>(API_ENDPOINTS.BILLS.BASE, { params });
    return response;
  },

  async getBill(id: number): Promise<ApiResponse<Bill>> {
    const response = await ApiClient.get<Bill>(`${API_ENDPOINTS.BILLS.BASE}/${id}`);
    return response;
  },

  async createBill(billData: Partial<Bill>): Promise<ApiResponse<Bill>> {
    const response = await ApiClient.post<Bill>(API_ENDPOINTS.BILLS.BASE, billData);
    return response;
  },

  async updateBill(id: number, billData: Partial<Bill>): Promise<ApiResponse<Bill>> {
    const response = await ApiClient.put<Bill>(`${API_ENDPOINTS.BILLS.BASE}/${id}`, billData);
    return response;
  },

  async deleteBill(id: number): Promise<void> {
    await ApiClient.delete(`${API_ENDPOINTS.BILLS.BASE}/${id}`);
  },

  async getBillStats(params?: { family_id?: number; start_date?: string; end_date?: string }): Promise<ApiResponse<BillStats>> {
    const response = await ApiClient.get<BillStats>(API_ENDPOINTS.BILLS.STATS, { params });
    return response;
  },

  async getCategoryStats(params?: { family_id?: number; start_date?: string; end_date?: string }): Promise<ApiResponse<CategoryStats[]>> {
    const response = await ApiClient.get<CategoryStats[]>(`${API_ENDPOINTS.BILLS.STATS}/categories`, { params });
    return response;
  },

  async getCategories(): Promise<ApiResponse<BillCategory[]>> {
    const response = await ApiClient.get<BillCategory[]>(API_ENDPOINTS.BILLS.CATEGORIES);
    return response;
  },

  async createCategory(categoryData: { name: string; category_type: 'income' | 'expense'; description?: string }): Promise<ApiResponse<BillCategory>> {
    const response = await ApiClient.post<BillCategory>(API_ENDPOINTS.BILLS.CATEGORIES, categoryData);
    return response;
  },
};

// 文件上传服务
export const UploadService = {
  uploadFile: async (file: File): Promise<ApiResponse<UploadResponse>> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('auto_categorize', 'true');
    
    const response = await ApiClient.post<UploadResponse>('/upload/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 120000,
    });
    return response;
  },

  async getUploadHistory(params?: { page?: number; size?: number; family_id?: number }): Promise<ApiResponse<PaginatedResponse<UploadRecord>>> {
    const response = await ApiClient.get<PaginatedResponse<UploadRecord>>(API_ENDPOINTS.UPLOAD.HISTORY, { params });
    return response;
  },

  async deleteUploadRecord(id: number): Promise<void> {
    await ApiClient.delete(`${API_ENDPOINTS.UPLOAD.BASE}/${id}`);
  },
};

// 消息服务
export const messageApi = {
  async getMessages(page = 1, size = 20, isRead?: boolean): Promise<ApiResponse<MessageListResponse>> {
    const params: any = { page, size };
    if (isRead !== undefined) {
      params.is_read = isRead;
    }
    const response = await ApiClient.get<MessageListResponse>('/messages/', { params });
    return response;
  },

  async getUnreadCount(): Promise<ApiResponse<number>> {
    const response = await ApiClient.get<number>('/messages/unread-count');
    return response;
  },

  async updateMessage(messageId: number, update: MessageUpdate): Promise<ApiResponse<Message>> {
    const response = await ApiClient.patch<Message>(`/messages/${messageId}`, update);
    return response;
  },

  async createMessageAction(messageId: number, action: MessageActionCreate): Promise<ApiResponse<any>> {
    const response = await ApiClient.post<any>(`/messages/${messageId}/actions`, action);
    return response;
  },

  async deleteMessage(messageId: number): Promise<ApiResponse<boolean>> {
    const response = await ApiClient.delete<boolean>(`/messages/${messageId}`);
    return response;
  },
};

// 系统配置服务
export const SystemConfigService = {
  // 获取所有系统配置
  async getConfigs(): Promise<ApiResponse<SystemConfigResponse[]>> {
    const response = await ApiClient.get<SystemConfigResponse[]>(API_ENDPOINTS.SYSTEM_CONFIG.BASE);
    return response;
  },

  // 获取单个配置
  async getConfig(key: string): Promise<ApiResponse<SystemConfigResponse>> {
    const response = await ApiClient.get<SystemConfigResponse>(`${API_ENDPOINTS.SYSTEM_CONFIG.BASE}/${key}`);
    return response;
  },

  // 创建配置
  async createConfig(configData: SystemConfigCreate): Promise<ApiResponse<SystemConfigResponse>> {
    const response = await ApiClient.post<SystemConfigResponse>(API_ENDPOINTS.SYSTEM_CONFIG.BASE, configData);
    return response;
  },

  // 更新配置
  async updateConfig(key: string, configData: SystemConfigUpdate): Promise<ApiResponse<SystemConfigResponse>> {
    const response = await ApiClient.put<SystemConfigResponse>(`${API_ENDPOINTS.SYSTEM_CONFIG.BASE}/${key}`, configData);
    return response;
  },

  // 删除配置
  async deleteConfig(key: string): Promise<ApiResponse<boolean>> {
    const response = await ApiClient.delete<boolean>(`${API_ENDPOINTS.SYSTEM_CONFIG.BASE}/${key}`);
    return response;
  },

  // 获取默认密码
  async getDefaultPassword(): Promise<ApiResponse<DefaultPasswordConfig>> {
    const response = await ApiClient.get<DefaultPasswordConfig>(API_ENDPOINTS.SYSTEM_CONFIG.DEFAULT_PASSWORD);
    return response;
  },

  // 设置默认密码
  async setDefaultPassword(passwordData: DefaultPasswordConfig): Promise<ApiResponse<SystemConfigResponse>> {
    const response = await ApiClient.put<SystemConfigResponse>(API_ENDPOINTS.SYSTEM_CONFIG.DEFAULT_PASSWORD, passwordData);
    return response;
  },

  // 初始化默认配置
  async initializeConfigs(): Promise<ApiResponse<boolean>> {
    const response = await ApiClient.post<boolean>(API_ENDPOINTS.SYSTEM_CONFIG.INITIALIZE);
    return response;
  },
};

// 别名导出
export const familyApi = FamilyService;