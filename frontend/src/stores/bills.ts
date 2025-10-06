import { create } from 'zustand';
import type { 
  Bill, 
  BillCategory, 
  BillListQueryParams, 
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
  queryParams: BillListQueryParams;
  isLoading: boolean;
  error: string | null;
  lastUpdatedAt: number; // 新增：数据最后更新时间戳
  // --- 新增：仪表板范围（个人/家庭） ---
  dashboardScope: 'personal' | 'family';
  // --- 新增：年度图表共享控制 ---
  yearlyChartYear: number;
  yearlyChartType: 'line' | 'bar';
  // --- 新增：月度图表共享时间范围 ---
  monthlyChartYear: number;
  monthlyChartMonth: number;
  // --- 新增：可用年份列表 ---
  availableYears: number[];
}

interface BillsActions {
  // 账单操作
  fetchBills: (params?: BillListQueryParams) => Promise<void>;
  fetchBill: (id: number) => Promise<void>;
  createBill: (billData: Partial<Bill>) => Promise<void>;
  updateBill: (id: number, billData: Partial<Bill>) => Promise<void>;
  deleteBill: (id: number) => Promise<void>;
  batchUpdateBills: (ids: number[], updateData: { amount?: number; transaction_type?: 'income' | 'expense' | 'transfer'; transaction_desc?: string; category_id?: number; remark?: string }) => Promise<void>;
  // 分类操作
  fetchCategories: () => Promise<void>;
  createCategory: (categoryData: { name: string; category_type: 'income' | 'expense'; description?: string }) => Promise<void>;
  
  // 统计操作（增加 scope）
  fetchStats: (params?: { family_id?: number; start_date?: string; end_date?: string; scope?: 'personal' | 'family' }) => Promise<void>;
  fetchCategoryStats: (params?: { family_id?: number; start_date?: string; end_date?: string; scope?: 'personal' | 'family' }) => Promise<void>;
  
  // 查询参数管理
  setQueryParams: (params: Partial<BillListQueryParams>) => void;
  resetQueryParams: () => void;
  
  // 状态管理
  clearError: () => void;
  setLoading: (loading: boolean) => void;
  resetState: () => void;
  
  // --- 新增：仪表板范围设置 ---
  setDashboardScope: (scope: 'personal' | 'family') => void;
  // --- 新增：年度图表共享控制 ---
  setYearlyChartYear: (year: number) => void;
  setYearlyChartType: (type: 'line' | 'bar') => void;
  // --- 新增：月度图表共享时间范围 ---
  setMonthlyChartYear: (year: number) => void;
  setMonthlyChartMonth: (month: number) => void;
  // --- 新增：获取可用年份 ---
  fetchAvailableYears: () => Promise<void>;
}

const initialQueryParams: BillListQueryParams = {
  page: 1,
  size: 100,
  sort_by: 'transaction_time',
  sort_order: 'desc',
  // 金额区间默认未设置
  min_amount: undefined,
  max_amount: undefined,
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
    size: 100,
    pages: 0,
  },
  queryParams: initialQueryParams,
  isLoading: false,
  error: null,
  lastUpdatedAt: Date.now(),
  // --- 新增：仪表板范围（默认个人） ---
  dashboardScope: 'personal',
  // --- 新增：年度图表共享控制 ---
  yearlyChartYear: new Date().getFullYear(),
  yearlyChartType: 'line',
  // --- 新增：月度图表共享时间范围 ---
  monthlyChartYear: new Date().getFullYear(),
  monthlyChartMonth: new Date().getMonth() + 1,
  // --- 新增：可用年份列表 ---
  availableYears: [],

  // 操作
  fetchBills: async (params?: BillListQueryParams) => {
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
        lastUpdatedAt: Date.now(),
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
        currentBill: null,
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
      
      set({ isLoading: false, lastUpdatedAt: Date.now() });
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
        lastUpdatedAt: Date.now(),
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
      
      set({ isLoading: false, lastUpdatedAt: Date.now() });
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
      set({ isLoading: true, error: null });
      
      const response = await BillService.getCategories();
      
      set({
        categories: response.data,
        isLoading: false,
      });
    } catch (error: any) {
      const errorMessage = error.friendlyMessage || 
                          error.response?.data?.message || 
                          error.response?.data?.detail || 
                          '获取分类列表失败';
      set({
        categories: [],
        error: errorMessage,
        isLoading: false,
      });
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
      set({ isLoading: true, error: null });
      const scope = params?.scope ?? get().dashboardScope;
      const raw = await BillService.getBillStats({ ...(params || {}), scope });

      const period = (() => {
        if (params?.start_date && params?.end_date) return `${params.start_date} ~ ${params.end_date}`;
        if (params?.start_date) return `${params.start_date} ~ 今`;
        if (params?.end_date) return `至 ${params.end_date}`;
        return '全部';
      })();

      const mapped: BillStats = {
        total_income: Number(raw?.total_income ?? 0),
        total_expense: Number(raw?.total_expense ?? 0),
        net_amount: Number(raw?.total_income ?? 0) - Number(raw?.total_expense ?? 0),
        transaction_count: Number(raw?.total_count ?? 0),
        period,
      };

      set({ stats: mapped, isLoading: false });
    } catch (error: any) {
      const errorMessage = error.friendlyMessage || 
                          error.response?.data?.message || 
                          error.response?.data?.detail || 
                          '获取统计数据失败';
      set({ error: errorMessage, isLoading: false });
    }
  },

  fetchCategoryStats: async (params) => {
    try {
      const scope = params?.scope ?? get().dashboardScope;
      const response = await BillService.getCategoryStats({ ...(params || {}), scope });
      set({ categoryStats: response.data });
    } catch (error: any) {
      const errorMessage = error.friendlyMessage || 
                          error.response?.data?.message || 
                          error.response?.data?.detail || 
                          '获取分类统计失败';
      set({ error: errorMessage });
    }
  },

  setQueryParams: (params: Partial<BillListQueryParams>) => {
    const currentParams = get().queryParams;
    const newParams = { ...currentParams, ...params };
    set({ queryParams: newParams });
    // 自动触发数据重新获取
    get().fetchBills(newParams);
  },
  resetQueryParams: () => {
    set({ queryParams: initialQueryParams });
  },

  clearError: () => set({ error: null }),
  setLoading: (loading: boolean) => set({ isLoading: loading }),
  resetState: () => set({
    bills: [],
    categories: [],
    stats: null,
    categoryStats: [],
    currentBill: null,
    pagination: { total: 0, page: 1, size: 100, pages: 0 },
    queryParams: initialQueryParams,
    isLoading: false,
    error: null,
    lastUpdatedAt: Date.now(),
  }),

  // --- 新增：仪表板范围设置 ---
  setDashboardScope: (scope) => set({ dashboardScope: scope }),

  // --- 新增：年度图表共享控制 ---
  setYearlyChartYear: (year: number) => set({ yearlyChartYear: year }),
  setYearlyChartType: (type: 'line' | 'bar') => set({ yearlyChartType: type }),

  // --- 新增：月度图表共享时间范围 ---
  setMonthlyChartYear: (year: number) => set({ monthlyChartYear: year }),
  setMonthlyChartMonth: (month: number) => set({ monthlyChartMonth: month }),

  // --- 新增：获取可用年份 ---
  fetchAvailableYears: async () => {
    try {
      set({ isLoading: true, error: null });
      
      const response = await BillService.getAvailableYears();
      
      set({
        availableYears: response.data.years,
        isLoading: false,
      });
    } catch (error: any) {
      const errorMessage = error.friendlyMessage || 
                          error.response?.data?.message || 
                          error.response?.data?.detail || 
                          '获取可用年份失败';
      set({
        availableYears: [],
        error: errorMessage,
        isLoading: false,
      });
    }
  },

  // 批量更新账单（补回）
  batchUpdateBills: async (ids: number[], updateData: { amount?: number; transaction_type?: 'income' | 'expense' | 'transfer'; transaction_desc?: string; category_id?: number; remark?: string }) => {
    try {
      set({ isLoading: true, error: null });
      await BillService.updateBillsBatch(ids.map(id => ({ id, ...updateData })));
      await get().fetchBills();
      set({ isLoading: false, lastUpdatedAt: Date.now() });
    } catch (error: any) {
      const errorMessage = error?.friendlyMessage || error?.response?.data?.message || error?.response?.data?.detail || '批量更新账单失败';
      set({ error: errorMessage, isLoading: false });
      throw error;
    }
  },
}));