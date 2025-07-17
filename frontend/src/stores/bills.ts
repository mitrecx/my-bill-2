import { create } from 'zustand';
import type { 
  Bill, 
  BillCategory, 
  BillQueryParams, 
  // PaginatedResponse, 
  BillStats, 
  CategoryStats 
} from '../types';
import { BillService } from '../api/services';

interface BillsState {
  bills: Bill[];
  categories: BillCategory[];
  stats: BillStats | null;
  categoryStats: CategoryStats[];
  currentBill: Bill | null;
  pagination: {
    total: number;
    page: number;
    size: number;
    pages: number;
  };
  queryParams: BillQueryParams;
  isLoading: boolean;
  error: string | null;
}

interface BillsActions {
  // 账单操作
  fetchBills: (params?: BillQueryParams) => Promise<void>;
  fetchBill: (id: number) => Promise<void>;
  createBill: (billData: Partial<Bill>) => Promise<void>;
  updateBill: (id: number, billData: Partial<Bill>) => Promise<void>;
  deleteBill: (id: number) => Promise<void>;
  
  // 分类操作
  fetchCategories: () => Promise<void>;
  createCategory: (categoryData: { name: string; category_type: 'income' | 'expense'; description?: string }) => Promise<void>;
  
  // 统计操作
  fetchStats: (params?: { family_id?: number; start_date?: string; end_date?: string }) => Promise<void>;
  fetchCategoryStats: (params?: { family_id?: number; start_date?: string; end_date?: string }) => Promise<void>;
  
  // 查询参数管理
  setQueryParams: (params: Partial<BillQueryParams>) => void;
  resetQueryParams: () => void;
  
  // 状态管理
  clearError: () => void;
  setLoading: (loading: boolean) => void;
  resetState: () => void;
}

const initialQueryParams: BillQueryParams = {
  page: 1,
  size: 20,
  sort_by: 'transaction_date',
  sort_order: 'desc',
};

export const useBillsStore = create<BillsState & BillsActions>((set, get) => ({
  // 状态
  bills: [],
  categories: [],
  stats: null,
  categoryStats: [],
  currentBill: null,
  pagination: {
    total: 0,
    page: 1,
    size: 20,
    pages: 0,
  },
  queryParams: initialQueryParams,
  isLoading: false,
  error: null,

  // 操作
  fetchBills: async (params?: BillQueryParams) => {
    try {
      set({ isLoading: true, error: null });
      
      const queryParams = params || get().queryParams;
      const response = await BillService.getBills(queryParams);
      
      set({
        bills: response.data.items,
        pagination: {
          total: response.data.total,
          page: response.data.page,
          size: response.data.size,
          pages: response.data.pages,
        },
        queryParams,
        isLoading: false,
      });
    } catch (error: any) {
      const errorMessage = error.friendlyMessage || 
                          error.response?.data?.message || 
                          error.response?.data?.detail || 
                          '获取账单失败';
      set({
        bills: [],
        error: errorMessage,
        isLoading: false,
      });
    }
  },

  fetchBill: async (id: number) => {
    try {
      set({ isLoading: true, error: null });
      
      const response = await BillService.getBill(id);
      
      set({
        currentBill: response.data,
        isLoading: false,
      });
    } catch (error: any) {
      const errorMessage = error.friendlyMessage || 
                          error.response?.data?.message || 
                          error.response?.data?.detail || 
                          '获取账单详情失败';
      set({
        error: errorMessage,
        isLoading: false,
      });
    }
  },

  createBill: async (billData: Partial<Bill>) => {
    try {
      set({ isLoading: true, error: null });
      
      await BillService.createBill(billData);
      
      // 重新获取账单列表
      await get().fetchBills();
      
      set({ isLoading: false });
    } catch (error: any) {
      const errorMessage = error.friendlyMessage || 
                          error.response?.data?.message || 
                          error.response?.data?.detail || 
                          '创建账单失败';
      set({
        error: errorMessage,
        isLoading: false,
      });
      throw error;
    }
  },

  updateBill: async (id: number, billData: Partial<Bill>) => {
    try {
      set({ isLoading: true, error: null });
      
      const response = await BillService.updateBill(id, billData);
      
      // 更新当前账单
      set({
        currentBill: response.data,
        isLoading: false,
      });
      
      // 重新获取账单列表
      await get().fetchBills();
    } catch (error: any) {
      const errorMessage = error.friendlyMessage || 
                          error.response?.data?.message || 
                          error.response?.data?.detail || 
                          '更新账单失败';
      set({
        error: errorMessage,
        isLoading: false,
      });
      throw error;
    }
  },

  deleteBill: async (id: number) => {
    try {
      set({ isLoading: true, error: null });
      
      await BillService.deleteBill(id);
      
      // 重新获取账单列表
      await get().fetchBills();
      
      set({ isLoading: false });
    } catch (error: any) {
      const errorMessage = error.friendlyMessage || 
                          error.response?.data?.message || 
                          error.response?.data?.detail || 
                          '删除账单失败';
      set({
        error: errorMessage,
        isLoading: false,
      });
      throw error;
    }
  },

  fetchCategories: async () => {
    try {
      const response = await BillService.getCategories();
      set({ categories: response.data });
    } catch (error: any) {
      const errorMessage = error.friendlyMessage || 
                          error.response?.data?.message || 
                          error.response?.data?.detail || 
                          '获取分类失败';
      set({ error: errorMessage, categories: [] });
    }
  },

  createCategory: async (categoryData) => {
    try {
      set({ isLoading: true, error: null });
      
      await BillService.createCategory(categoryData);
      
      // 重新获取分类列表
      await get().fetchCategories();
      
      set({ isLoading: false });
    } catch (error: any) {
      const errorMessage = error.friendlyMessage || 
                          error.response?.data?.message || 
                          error.response?.data?.detail || 
                          '创建分类失败';
      set({
        error: errorMessage,
        isLoading: false,
      });
      throw error;
    }
  },

  fetchStats: async (params) => {
    try {
      const response = await BillService.getBillStats(params);
      set({ stats: response.data });
    } catch (error: any) {
      const errorMessage = error.friendlyMessage || 
                          error.response?.data?.message || 
                          error.response?.data?.detail || 
                          '获取统计数据失败';
      set({ error: errorMessage });
    }
  },

  fetchCategoryStats: async (params) => {
    try {
      const response = await BillService.getCategoryStats(params);
      set({ categoryStats: response.data });
    } catch (error: any) {
      const errorMessage = error.friendlyMessage || 
                          error.response?.data?.message || 
                          error.response?.data?.detail || 
                          '获取分类统计失败';
      set({ error: errorMessage });
    }
  },

  setQueryParams: (params: Partial<BillQueryParams>) => {
    const currentParams = get().queryParams;
    const newParams = { ...currentParams, ...params };
    set({ queryParams: newParams });
  },

  resetQueryParams: () => {
    set({ queryParams: initialQueryParams });
  },

  clearError: () => {
    set({ error: null });
  },

  setLoading: (loading: boolean) => {
    set({ isLoading: loading });
  },

  resetState: () => {
    set({
      bills: [],
      currentBill: null,
      stats: null,
      categoryStats: [],
      pagination: {
        total: 0,
        page: 1,
        size: 20,
        pages: 0,
      },
      queryParams: initialQueryParams,
      error: null,
    });
  },
}));