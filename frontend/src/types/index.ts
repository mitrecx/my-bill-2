// 用户相关类型
export interface User {
  id: number;
  username: string;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
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
  family_id: number;
  user_id: number;
  category_id?: number;
  transaction_date: string;
  amount: number;
  transaction_type: 'income' | 'expense';
  transaction_desc: string;
  source_type: 'alipay' | 'jd' | 'cmb';
  raw_data: Record<string, any>;
  created_at: string;
  updated_at: string;
  category?: BillCategory;
  user?: User;
}

export interface BillCategory {
  id: number;
  name: string;
  category_type: 'income' | 'expense';
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface UploadRecord {
  id: number;
  family_id: number;
  user_id: number;
  filename: string;
  file_size: number;
  source_type: 'alipay' | 'jd' | 'cmb';
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
export interface BillQueryParams {
  page?: number;
  size?: number;
  family_id?: number;
  user_id?: number;
  category_id?: number;
  transaction_type?: 'income' | 'expense';
  source_type?: 'alipay' | 'jd' | 'cmb';
  start_date?: string;
  end_date?: string;
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
  period: string;
}

export interface CategoryStats {
  category_id: number;
  category_name: string;
  total_amount: number;
  transaction_count: number;
  percentage: number;
}

// 文件上传相关
export interface FileUploadResponse {
  filename: string;
  preview: Bill[];
  total_records: number;
  upload_id: string;
}

export interface FileUploadConfirm {
  upload_id: string;
  family_id: number;
}