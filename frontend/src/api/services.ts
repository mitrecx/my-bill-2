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
  CategoryStats,
  Family,
  FamilyMember,
  UploadRecord,
  UploadResponse,
  ApiResponse, // 新增ApiResponse类型导入
  SystemConfigCreate,
  SystemConfigUpdate,
  DefaultPasswordConfig,
  SystemConfigResponse,
  ClassificationRule,
  ClassificationRuleCreate,
  ClassificationRuleUpdate,
  ClassificationRuleListResponse,
  SourceTypeOptionsResponse,
  FinanceSummary,
} from '../types';
import type { MonthlyExpenseTrendResponse } from '../types/bills';
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
  }) {
    const response = await ApiClient.get<PaginatedResponse<User>>(API_ENDPOINTS.USERS.BASE, { params });
    return response;
  },

  async createUser(userData: Partial<User>): Promise<ApiResponse<User>> {
    const response = await ApiClient.post<User>(API_ENDPOINTS.USERS.BASE, userData);
    return response;
  },

  async updateUser(id: number, userData: Partial<User>): Promise<ApiResponse<User>> {
    const response = await ApiClient.put<User>(`${API_ENDPOINTS.USERS.BASE}/${id}`, userData);
    return response;
  },

  async deleteUser(id: number) {
    const response = await ApiClient.delete(`${API_ENDPOINTS.USERS.BASE}/${id}`);
    return response;
  },
};

// 家庭服务
export const FamilyService = {
  async getFamilies() {
    const response = await ApiClient.get<Family[]>(API_ENDPOINTS.FAMILIES.BASE);
    return response;
  },

  async createFamily(family: Partial<Family>) {
    const response = await ApiClient.post<Family>(API_ENDPOINTS.FAMILIES.BASE, family);
    return response;
  },

  async updateFamily(id: number, family: Partial<Family>) {
    const response = await ApiClient.put<Family>(`${API_ENDPOINTS.FAMILIES.BASE}/${id}`, family);
    return response;
  },

  async deleteFamily(id: number) {
    const response = await ApiClient.delete(`${API_ENDPOINTS.FAMILIES.BASE}/${id}`);
    return response;
  },

  async getMembers(family_id: number) {
    const response = await ApiClient.get<FamilyMember[]>(API_ENDPOINTS.FAMILIES.MEMBERS(family_id));
    return response;
  },
};

// 账单服务
export const BillService = {
  async getBills(params?: BillListQueryParams) {
    const response = await ApiClient.get<PaginatedResponse<Bill>>(API_ENDPOINTS.BILLS.BASE, { params });
    return response;
  },

  async getBill(id: number) {
    const response = await ApiClient.get<Bill>(API_ENDPOINTS.BILLS.BY_ID(id));
    return response;
  },

  async createBill(bill: Partial<Bill>) {
    const response = await ApiClient.post<Bill>(API_ENDPOINTS.BILLS.BASE, bill);
    return response;
  },
 
  async updateBill(id: number, bill: Partial<Bill>) {
    const response = await ApiClient.put<Bill>(API_ENDPOINTS.BILLS.BY_ID(id), bill);
    return response;
  },

  async updateBillsBatch(items: Array<{ id: number; amount?: number; transaction_type?: 'income' | 'expense' | 'transfer'; transaction_desc?: string; category_id?: number; remark?: string }>) {
    const payload = { items: items.map(({ id, ...rest }) => ({ bill_id: id, ...rest })) };
    const response = await ApiClient.post<Bill[]>(API_ENDPOINTS.BILLS.BATCH, payload);
    return response;
  },

  // 新增：创建分类
  async createCategory(category: { name: string; category_type: 'income' | 'expense'; description?: string; icon?: string; color?: string }) {
    // 后端 BillCategoryCreate 仅接收: name, description, icon, color
    const payload = {
      name: category.name,
      description: category.description,
      icon: category.icon,
      color: category.color,
    };
    const response = await ApiClient.post<BillCategory>(API_ENDPOINTS.BILLS.CATEGORIES, payload);
    return response;
  },

  async deleteBill(id: number) {
    const response = await ApiClient.delete(API_ENDPOINTS.BILLS.BY_ID(id));
    return response;
  },

  // NOTE: 后端 /bills/stats 返回的是裸 BillStatsResponse，而非 ApiResponse 包裹
  // 返回 any 以便在 store 中进行字段映射到 BillStats
  async getBillStats(params?: { family_id?: number; start_date?: string; end_date?: string }): Promise<any> {
    const resp = await ApiClient.get<any>(API_ENDPOINTS.BILLS.STATS, { params });
    return resp; // 返回原始数据供前端映射
  },

  async getCategoryStats(params?: { family_id?: number; start_date?: string; end_date?: string }) {
    const response = await ApiClient.get<CategoryStats[]>(`${API_ENDPOINTS.BILLS.STATS}/categories`, { params });
    return response;
  },

  // /bills/finance-summary 获取按年或按月的财务汇总
  async getFinanceSummary(params: { result_type: 'income' | 'expense' | 'surplus'; year: number; month?: number }) {
    const response = await ApiClient.get<FinanceSummary>(API_ENDPOINTS.BILLS.FINANCE_SUMMARY, { params });
    return response; // ApiResponse<FinanceSummary>
  },

  // 新增：/bills/finance-summary/batch 获取最近N个月的月度财务汇总
  async getFinanceSummaryBatch(params: { result_type: 'income' | 'expense' | 'surplus'; months?: number; end_year?: number; end_month?: number }) {
    const response = await ApiClient.get<FinanceSummary[]>(API_ENDPOINTS.BILLS.FINANCE_SUMMARY_BATCH, { params });
    return response; // ApiResponse<FinanceSummary[]>
  },

  async getCategories() {
    const response = await ApiClient.get<BillCategory[]>(API_ENDPOINTS.BILLS.CATEGORIES);
    return response;
  },

  // 获取年度支出图表数据
  async getYearlyExpenseChart(year?: number) {
    const params = year ? { year } : {};
    const response = await ApiClient.get<any>(API_ENDPOINTS.BILLS.YEARLY_EXPENSE_CHART, { params });
    return response;
  },

  // 获取月度支出趋势（按日）
  async getMonthlyExpenseTrend(params?: { year?: number; month?: number }) {
    const response = await ApiClient.get<MonthlyExpenseTrendResponse>(API_ENDPOINTS.BILLS.MONTHLY_EXPENSE_TREND, { params });
    return response;
  },
};

// 上传记录服务
export const UploadService = {
  async uploadFile(file: File, onProgress?: (progress: number) => void) {
    const response = await ApiClient.upload<UploadResponse>(API_ENDPOINTS.UPLOAD.BASE, file, onProgress);
    return response;
  },

  async getRecords(params?: { page?: number; page_size?: number }) {
    const response = await ApiClient.get<PaginatedResponse<UploadRecord>>(API_ENDPOINTS.UPLOAD.HISTORY, { params });
    return response;
  },

  async deleteRecord(id: number) {
    const response = await ApiClient.delete(`${API_ENDPOINTS.UPLOAD.HISTORY}/${id}`);
    return response;
  },
};

// 系统配置服务
export const SystemConfigService = {
  async getDefaultPasswordConfig(): Promise<ApiResponse<DefaultPasswordConfig>> {
    const response = await ApiClient.get<DefaultPasswordConfig>(API_ENDPOINTS.SYSTEM_CONFIG.DEFAULT_PASSWORD);
    return response;
  },

  async updateDefaultPasswordConfig(data: SystemConfigUpdate): Promise<ApiResponse<SystemConfigResponse>> {
    const response = await ApiClient.put<SystemConfigResponse>(API_ENDPOINTS.SYSTEM_CONFIG.DEFAULT_PASSWORD, data);
    return response;
  },
};

// 消息服务
export const MessageService = {
  async getMessages(params?: { page?: number; page_size?: number; is_read?: boolean }) {
    const response = await ApiClient.get<MessageListResponse>(API_ENDPOINTS.MESSAGES.BASE, { params });
    return response;
  },

  async markAsRead(id: number) {
    const response = await ApiClient.patch(API_ENDPOINTS.MESSAGES.BY_ID(id), { is_read: true });
    return response;
  },

  async markAllAsRead() {
    const response = await ApiClient.post(`${API_ENDPOINTS.MESSAGES.BASE}/mark-all-read`);
    return response;
  },

  async createAction(messageId: number, action: MessageActionCreate) {
    const response = await ApiClient.post(`${API_ENDPOINTS.MESSAGES.ACTION(messageId)}`, action);
    return response;
  },

  async updateMessage(id: number, update: MessageUpdate) {
    const response = await ApiClient.put(API_ENDPOINTS.MESSAGES.BY_ID(id), update);
    return response;
  },

  async deleteMessage(id: number) {
    const response = await ApiClient.delete(API_ENDPOINTS.MESSAGES.BY_ID(id));
    return response;
  },

  async getUnreadCount() {
    const response = await ApiClient.get<number>(API_ENDPOINTS.MESSAGES.UNREAD_COUNT);
    return response;
  },
};

// 兼容旧版 stores/message.ts 的包装导出
export const messageApi = {
  getMessages: (page?: number, pageSize?: number, isRead?: boolean) => {
    const params: { page?: number; page_size?: number; is_read?: boolean } = {};
    if (page !== undefined) params.page = page;
    if (pageSize !== undefined) params.page_size = pageSize;
    if (typeof isRead === 'boolean') params.is_read = isRead;
    return MessageService.getMessages(params);
  },
  getUnreadCount: () => MessageService.getUnreadCount(),
  updateMessage: (id: number, update: MessageUpdate) => MessageService.updateMessage(id, update),
  createMessageAction: (messageId: number, actionData: MessageActionCreate) => MessageService.createAction(messageId, actionData),
  deleteMessage: (id: number) => MessageService.deleteMessage(id),
};

// 兼容旧版 stores/family.ts 的包装导出
export const familyApi = {
  async getFamilies() {
    const resp = await FamilyService.getFamilies();
    return resp; // { data: Family[] }
  },
  async createFamily(data: Partial<Family>) {
    const resp = await FamilyService.createFamily(data);
    return resp.data; // stores/family 期望直接返回新建的 Family 对象
  },
  async updateFamily(id: number, data: Partial<Family>) {
    const resp = await FamilyService.updateFamily(id, data);
    return resp.data; // 返回更新后的 Family
  },
  async deleteFamily(id: number) {
    await FamilyService.deleteFamily(id);
  },
  async getFamilyMembers(familyId: number) {
    const resp = await FamilyService.getMembers(familyId);
    return { members: resp.data } as { members: FamilyMember[] };
  },
  async leaveFamily(familyId: number) {
    try {
      const r = await ApiClient.post(`${API_ENDPOINTS.FAMILIES.LEAVE(familyId)}`);
      return r;
    } catch {
      return;
    }
  },
  async searchUsers(query: string) {
    try {
      const r = await UserService.listUsers({ search: query });
      const items = (r.data?.items as any[]) || [];
      return items.map(u => ({ id: u.id, username: u.username })) as any;
    } catch {
      return [] as any[];
    }
  },
};

// 分类规则服务
export const ClassificationRuleService = {
  async getRules(params?: { page?: number; page_size?: number; source_type?: string; target_category?: string; is_active?: boolean; search?: string; }) {
    const response = await ApiClient.get<ClassificationRuleListResponse>(API_ENDPOINTS.CLASSIFICATION_RULES.BASE, { params });
    return response;
  },

  async createRule(data: ClassificationRuleCreate) {
    const response = await ApiClient.post<ClassificationRule>(API_ENDPOINTS.CLASSIFICATION_RULES.BASE, data);
    return response;
  },

  async updateRule(id: number, data: ClassificationRuleUpdate) {
    const response = await ApiClient.put<ClassificationRule>(`${API_ENDPOINTS.CLASSIFICATION_RULES.BASE}/${id}`, data);
    return response;
  },

  async deleteRule(id: number) {
    const response = await ApiClient.delete(`${API_ENDPOINTS.CLASSIFICATION_RULES.BASE}/${id}`);
    return response;
  },

  async getSourceTypeOptions() {
    const response = await ApiClient.get<SourceTypeOptionsResponse>(API_ENDPOINTS.CLASSIFICATION_RULES.SOURCE_TYPES);
    return response;
  },

  async toggleRuleStatus(id: number) {
    const response = await ApiClient.patch(`${API_ENDPOINTS.CLASSIFICATION_RULES.TOGGLE_STATUS(id)}`);
    return response;
  },
};

export default {
  AuthService,
  UserService,
  FamilyService,
  BillService,
  UploadService,
  SystemConfigService,
  MessageService,
  ClassificationRuleService,
};