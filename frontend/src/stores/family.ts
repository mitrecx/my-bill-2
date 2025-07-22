import { create } from 'zustand';
import { familyApi } from '../api/services';
import type { Family, FamilyMember, FamilyCreate, FamilyUpdate, UserSearchResult } from '../types/family';

interface FamilyState {
  families: Family[];
  currentFamily: Family | null;
  members: FamilyMember[];
  loading: boolean;
  error: string | null;
}

interface FamilyActions {
  fetchFamilies: () => Promise<void>;
  createFamily: (data: FamilyCreate) => Promise<void>;
  updateFamily: (id: number, data: FamilyUpdate) => Promise<void>;
  deleteFamily: (id: number) => Promise<void>;
  fetchFamilyMembers: (familyId: number) => Promise<void>;
  leaveFamily: (familyId: number) => Promise<void>;
  searchUsers: (query: string) => Promise<UserSearchResult[]>;
  setCurrentFamily: (family: Family | null) => void;
  clearError: () => void;
}

export const useFamilyStore = create<FamilyState & FamilyActions>((set, get) => ({
  families: [],
  currentFamily: null,
  members: [],
  loading: false,
  error: null,

  fetchFamilies: async () => {
    set({ loading: true, error: null });
    try {
      const response = await familyApi.getFamilies();
      const families = response.data || [];
      set({ 
        families,
        currentFamily: families.length > 0 ? families[0] : null,
        loading: false 
      });
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : '获取家庭列表失败',
        loading: false 
      });
    }
  },

  createFamily: async (data: FamilyCreate) => {
    set({ loading: true, error: null });
    try {
      const response = await familyApi.createFamily(data);
      const newFamily = response.data;
      const { families } = get();
      set({ 
        families: [...families, newFamily],
        currentFamily: newFamily,
        loading: false 
      });
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : '创建家庭失败',
        loading: false 
      });
      throw error;
    }
  },

  updateFamily: async (id: number, data: FamilyUpdate) => {
    set({ loading: true, error: null });
    try {
      const response = await familyApi.updateFamily(id, data);
      const updatedFamily = response.data;
      const { families, currentFamily } = get();
      const updatedFamilies = families.map(family => 
        family.id === id ? updatedFamily : family
      );
      set({ 
        families: updatedFamilies,
        currentFamily: currentFamily?.id === id ? updatedFamily : currentFamily,
        loading: false 
      });
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : '更新家庭失败',
        loading: false 
      });
      throw error;
    }
  },

  deleteFamily: async (id: number) => {
    set({ loading: true, error: null });
    try {
      await familyApi.deleteFamily(id);
      const { families, currentFamily } = get();
      const updatedFamilies = families.filter(family => family.id !== id);
      set({ 
        families: updatedFamilies,
        currentFamily: currentFamily?.id === id ? 
          (updatedFamilies.length > 0 ? updatedFamilies[0] : null) : 
          currentFamily,
        members: currentFamily?.id === id ? [] : get().members,
        loading: false 
      });
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : '删除家庭失败',
        loading: false 
      });
      throw error;
    }
  },

  fetchFamilyMembers: async (familyId: number) => {
    set({ loading: true, error: null });
    try {
      const response = await familyApi.getFamilyMembers(familyId);
      set({ 
        members: response.data || [],
        loading: false 
      });
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : '获取家庭成员失败',
        loading: false 
      });
    }
  },

  leaveFamily: async (familyId: number) => {
    set({ loading: true, error: null });
    try {
      await familyApi.leaveFamily(familyId);
      const { families, currentFamily } = get();
      const updatedFamilies = families.filter(family => family.id !== familyId);
      set({ 
        families: updatedFamilies,
        currentFamily: currentFamily?.id === familyId ? 
          (updatedFamilies.length > 0 ? updatedFamilies[0] : null) : 
          currentFamily,
        members: currentFamily?.id === familyId ? [] : get().members,
        loading: false 
      });
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : '退出家庭失败',
        loading: false 
      });
      throw error;
    }
  },

  searchUsers: async (query: string): Promise<UserSearchResult[]> => {
    try {
      const response = await familyApi.searchUsers(query);
      return response.data || [];
    } catch (error) {
      console.error('搜索用户失败:', error);
      return [];
    }
  },

  setCurrentFamily: (family: Family | null) => {
    set({ currentFamily: family });
  },

  clearError: () => {
    set({ error: null });
  },
}));