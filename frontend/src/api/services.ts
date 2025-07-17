import { ApiClient } from './client';
import { API_ENDPOINTS } from './config';
import type {
  AuthResponse,
  LoginRequest,
  RegisterRequest,
  User,
  Bill,
  BillCategory,
  BillQueryParams,
  PaginatedResponse,
  BillStats,
  CategoryStats,
  Family,
  FamilyMember,
  UploadRecord,
  UploadResponse,
  ApiResponse, // 新增ApiResponse类型导入
} from '../types';

// 认证服务
export const AuthService = {
  async login(credentials: LoginRequest): Promise<ApiResponse<AuthResponse['data']>> {
    // 使用JSON格式，匹配main_production.py的UserLogin模型
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
};

// 家庭服务
export const FamilyService = {
  async getFamilies(): Promise<ApiResponse<Family[]>> {
    const response = await ApiClient.get<Family[]>(API_ENDPOINTS.FAMILIES.BASE);
    return response;
  },

  async createFamily(familyData: { family_name: string; description?: string }): Promise<ApiResponse<Family>> {
    const response = await ApiClient.post<Family>(API_ENDPOINTS.FAMILIES.BASE, familyData);
    return response;
  },

  async updateFamily(familyId: number, familyData: Partial<Family>): Promise<ApiResponse<Family>> {
    const response = await ApiClient.put<Family>(`${API_ENDPOINTS.FAMILIES.BASE}/${familyId}`, familyData);
    return response;
  },

  async deleteFamily(familyId: number): Promise<void> {
    await ApiClient.delete(`${API_ENDPOINTS.FAMILIES.BASE}/${familyId}`);
  },

  async getFamilyMembers(familyId: number): Promise<ApiResponse<FamilyMember[]>> {
    const response = await ApiClient.get<FamilyMember[]>(API_ENDPOINTS.FAMILIES.MEMBERS(familyId));
    return response;
  },

  async joinFamily(familyId: number): Promise<ApiResponse<FamilyMember>> {
    const response = await ApiClient.post<FamilyMember>(API_ENDPOINTS.FAMILIES.JOIN(familyId));
    return response;
  },

  async leaveFamily(familyId: number): Promise<void> {
    await ApiClient.delete(API_ENDPOINTS.FAMILIES.LEAVE(familyId));
  },
};

// 账单服务
export const BillService = {
  async getBills(params?: BillQueryParams): Promise<ApiResponse<PaginatedResponse<Bill>>> {
    const response = await ApiClient.get<PaginatedResponse<Bill>>(API_ENDPOINTS.BILLS.BASE, { params });
    return response;
  },

  async getBill(id: number): Promise<ApiResponse<Bill>> {
    const response = await ApiClient.get<Bill>(API_ENDPOINTS.BILLS.BY_ID(id));
    return response;
  },

  async createBill(billData: Partial<Bill>): Promise<ApiResponse<Bill>> {
    const response = await ApiClient.post<Bill>(API_ENDPOINTS.BILLS.BASE, billData);
    return response;
  },

  async updateBill(id: number, billData: Partial<Bill>): Promise<ApiResponse<Bill>> {
    const response = await ApiClient.put<Bill>(API_ENDPOINTS.BILLS.BY_ID(id), billData);
    return response;
  },

  async deleteBill(id: number): Promise<void> {
    await ApiClient.delete(API_ENDPOINTS.BILLS.BY_ID(id));
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
  uploadFile: async (file: File, familyId: number): Promise<ApiResponse<UploadResponse>> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('family_id', familyId.toString());
    formData.append('auto_categorize', 'true');
    
    const response = await ApiClient.post<UploadResponse>('/upload/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
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