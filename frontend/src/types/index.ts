// 用户相关类型
export interface User {
  id: number;
  username: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
  updated_at: string;
  family_name?: string;
  family_role?: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  full_name: string;
}

export interface AuthResponse {
  success: boolean;
  message: string;
  data: {
    access_token: string;
    token_type: string;
    user: User;
  };
}

// 家庭相关类型
export interface Family {
  id: number;
  family_name: string;
  description?: string;
  created_by: number;
  created_at: string;
  updated_at: string;
}

export interface FamilyMember {
  id: number;
  family_id: number;
  user_id: number;
  role: 'owner' | 'admin' | 'member';
  joined_at: string;
  user?: User;
  family?: Family;
}

// 账单相关类型
export interface Bill {
  id: number;
  user_id: number;
  category_id?: number;
  transaction_date: string;
  amount: number;
  transaction_type: 'income' | 'expense' | 'transfer';
  transaction_desc: string;
  source_type: 'alipay' | 'jd' | 'cmb' | 'wechat' | 'meituan' | 'manual';
  raw_data: Record<string, any>;
  created_at: string;
  updated_at: string;
  category?: BillCategory;
  user?: User;
  remark?: string;
}

export interface BillCategory {
  id: number;
  name: string;
  category_type: 'income' | 'expense';
  description?: string;
  icon?: string;
  color?: string;
  created_at: string;
  updated_at: string;
}

export interface UploadRecord {
  id: number;
  family_id: number;
  user_id: number;
  filename: string;
  file_size: number;
  source_type: 'alipay' | 'jd' | 'cmb' | 'wechat' | 'meituan' | 'manual';
  records_count: number;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  error_message?: string;
  uploaded_at: string;
  processed_at?: string;
}

// API响应类型
export interface ApiResponse<T> {
  data: T;
  message?: string;
  success: boolean;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// 查询参数类型
export interface BillListQueryParams {
  page?: number;
  size?: number;
  family_id?: number;
  user_id?: number | number[];
  // 支持单选或多选分类
  category_id?: number | number[];
  // 支持单选或多选交易类型
  transaction_type?: ('income' | 'expense' | 'transfer') | ('income' | 'expense' | 'transfer')[];
  // 改为支持单选或多选来源
  source_type?: ('alipay' | 'jd' | 'cmb' | 'wechat' | 'meituan' | 'manual') | ('alipay' | 'jd' | 'cmb' | 'wechat' | 'meituan' | 'manual')[];
  start_date?: string;
  end_date?: string;
  // 新增：金额区间筛选
  min_amount?: number;
  max_amount?: number;
  search?: string;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

// 统计数据类型
export interface BillStats {
  total_income: number;
  total_expense: number;
  net_amount: number;
  transaction_count: number;
  period?: string; // 新增：时间区间描述（可选）
}

export interface CategoryStats {
  category_id: number;
  category_name: string;
  total_amount: number;
  transaction_count: number;
  percentage: number;
}

// 文件上传相关
export interface UploadResponse {
  upload_id: number;
  filename: string;
  source_type: string;
  total_records: number;
  success_count: number;
  failed_count: number;
  status: string;
  created_bills: number[];
  errors: string[];
  warnings: string[];
  ai_classified_count?: number;  // AI分类成功数量
}

// 分类规则相关类型
export interface ClassificationRule {
  id: number;
  rule_text: string;
  source_type: 'alipay' | 'jd' | 'cmb' | 'wechat' | 'meituan' | 'manual' | 'all';
  target_category: string;
  transaction_type: 'expense' | 'income' | 'transfer' | 'all';
  priority: number;
  is_active: boolean;
  created_by: number;
  created_at: string;
  updated_at: string;
}

export interface ClassificationRuleCreate {
  rule_text: string;
  source_type: 'alipay' | 'jd' | 'cmb' | 'wechat' | 'meituan' | 'manual' | 'all';
  target_category: string;
  transaction_type?: 'expense' | 'income' | 'transfer' | 'all';
  priority?: number;
  is_active?: boolean;
}

export interface ClassificationRuleUpdate {
  rule_text?: string;
  source_type?: 'alipay' | 'jd' | 'cmb' | 'wechat' | 'meituan' | 'manual' | 'all';
  target_category?: string;
  transaction_type?: 'expense' | 'income' | 'transfer' | 'all';
  priority?: number;
  is_active?: boolean;
}

export interface ClassificationRuleListResponse {
  rules: ClassificationRule[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface SourceTypeOption {
  value: 'alipay' | 'jd' | 'cmb' | 'wechat' | 'meituan' | 'manual' | 'all';
  label: string;
}

export interface TransactionTypeOption {
  value: 'expense' | 'income' | 'transfer' | 'all';
  label: string;
}

export interface SourceTypeOptionsResponse {
  source_types: SourceTypeOption[];
}

export interface TransactionTypeOptionsResponse {
  transaction_types: TransactionTypeOption[];
}

// 导出其他模块的类型
export * from './family';
export * from './message';
export * from './system-config';

// 新增：财务汇总类型（对接后端 /finance-summary）
export interface FinanceSummary {
  year: number;
  month?: number;
  result_type: 'income' | 'expense' | 'surplus';
  amount: number;
  count: number;
}

// 新增：可用年份响应类型
export interface AvailableYearsResponse {
  years: number[];
  total_count: number;
}