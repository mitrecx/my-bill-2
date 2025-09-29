import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User, LoginRequest, RegisterRequest } from '../types';
import { AuthService } from '../api/services';
import { TokenManager, UserManager } from '../api/client';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

interface AuthActions {
  login: (credentials: LoginRequest) => Promise<void>;
  register: (userData: RegisterRequest) => Promise<void>;
  logout: () => void;
  loadUser: () => Promise<void>;
  clearError: () => void;
  setLoading: (loading: boolean) => void;
  // 新增：允许手动设置当前用户，便于资料更新后立即刷新 UI
  setUser: (user: User | null) => void;
}

export const useAuthStore = create<AuthState & AuthActions>()(
  persist(
    (set, get) => ({
      // 状态
      user: UserManager.getUser(),
      isAuthenticated: !!TokenManager.getToken(),
      isLoading: false,
      error: null,

      // 操作
      login: async (credentials: LoginRequest) => {
        try {
          set({ isLoading: true, error: null });
          console.log('[login] start', credentials);
          const response = await AuthService.login(credentials);
          const { data, success, message } = response;
          if (!success) throw new Error(message || '登录失败');
          // 保存token和用户信息
          TokenManager.setToken(data.access_token);
          UserManager.setUser(data.user);
          console.log('[login] token set', TokenManager.getToken());
          console.log('[login] user set', UserManager.getUser());
          // 登录后立即刷新用户信息，确保状态同步
          await get().loadUser();
          set({
            isLoading: false,
            error: null,
          });
          console.log('[login] after loadUser', get().user, get().isAuthenticated);
        } catch (error: any) {
          // 优先使用友好的错误信息，然后是API返回的错误信息，最后是默认信息
          const errorMessage = error.friendlyMessage || 
                              error.response?.data?.message || 
                              error.response?.data?.detail || 
                              error.message || 
                              '登录失败，请重试';
          set({
            error: errorMessage,
            isLoading: false,
          });
          console.log('[login] error', errorMessage);
          throw error;
        }
      },

      register: async (userData: RegisterRequest) => {
        try {
          set({ isLoading: true, error: null });
          
          const response = await AuthService.register(userData);
          const { data } = response;
          // 保存token和用户信息
          TokenManager.setToken(data.access_token);
          UserManager.setUser(data.user);
          
          set({
            user: data.user,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error: any) {
          // 优先使用友好的错误信息，然后是API返回的错误信息，最后是默认信息
          const errorMessage = error.friendlyMessage || 
                              error.response?.data?.message || 
                              error.response?.data?.detail || 
                              '注册失败，请重试';
          set({
            error: errorMessage,
            isLoading: false,
          });
          throw error;
        }
      },

      logout: () => {
        UserManager.logout();
        set({
          user: null,
          isAuthenticated: false,
          error: null,
        });
      },

      loadUser: async () => {
        try {
          console.log('[loadUser] token', TokenManager.getToken());
          if (!TokenManager.isAuthenticated()) {
            console.log('[loadUser] not authenticated');
            return;
          }
          set({ isLoading: true });
          // 使用 /auth/me，避免在登录阶段触发管理员依赖的接口
          const response = await AuthService.getCurrentUser();
          const user = response.data;
          UserManager.setUser(user);
          set({
            user,
            isAuthenticated: true,
            isLoading: false,
          });
          console.log('[loadUser] user loaded from /auth/me', user);
        } catch (error: any) {
          // 仅在 401 时登出并跳转登录，其它错误保留会话，避免登录后闪退
          const status = error?.response?.status;
          if (status === 401) {
            get().logout();
          } else {
            const errorMessage = error.friendlyMessage || 
                                 error.response?.data?.message || 
                                 error.response?.data?.detail || 
                                 '获取用户信息失败，请稍后重试';
            set({ error: errorMessage });
          }
          set({ isLoading: false });
          console.log('[loadUser] error', status, error?.response?.data);
        }
      },

      clearError: () => {
        set({ error: null });
      },

      setLoading: (loading: boolean) => {
        set({ isLoading: loading });
      },

      // 新增：手动设置当前用户（会同步到本地缓存），用于个人资料更新后立即刷新展示
      setUser: (nextUser: User | null) => {
        if (nextUser) {
          UserManager.setUser(nextUser);
          set({ user: nextUser });
        } else {
          // 不清除 token，仅更新用户信息为空；真正退出登录应调用 logout()
          UserManager.setUser(null as any);
          set({ user: null });
        }
      },
    }),
    {
      name: 'auth-store',
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);