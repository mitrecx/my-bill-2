import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import type { Message, MessageListResponse, MessageActionCreate } from '../types/message';
import { MessageService, messageApi } from '../api/services';

interface MessageState {
  messages: Message[];
  loading: boolean;
  total: number;
  page: number;
  pageSize: number;
  unreadCount: number;
  
  // Actions
  fetchMessages: (page?: number, pageSize?: number, isRead?: boolean) => Promise<void>;
  fetchUnreadCount: () => Promise<void>;
  markAsRead: (messageId: number) => Promise<void>;
  createMessageAction: (messageId: number, actionType: string) => Promise<void>;
  deleteMessage: (messageId: number) => Promise<void>;
  reset: () => void;
}

const initialState = {
  messages: [],
  loading: false,
  total: 0,
  page: 1,
  pageSize: 20,
  unreadCount: 0,
};

export const useMessageStore = create<MessageState>()(
  devtools(
    (set, get) => ({
      ...initialState,

      fetchMessages: async (page = 1, pageSize = 20, isRead?: boolean) => {
        set({ loading: true });
        try {
          const response = await messageApi.getMessages(page, pageSize, isRead);
          const data = response.data as MessageListResponse;
          
          set({
            messages: data.items,
            total: data.total,
            page: data.page,
            pageSize: data.size,
            loading: false,
          });
          
          // 同时更新未读数量
          get().fetchUnreadCount();
        } catch (error) {
          console.error('获取消息列表失败:', error);
          set({ loading: false });
          throw error;
        }
      },

      fetchUnreadCount: async () => {
        try {
          const response = await messageApi.getUnreadCount();
          set({ unreadCount: response.data });
        } catch (error) {
          console.error('获取未读消息数量失败:', error);
        }
      },

      markAsRead: async (messageId: number) => {
        try {
          await MessageService.markAsRead(messageId);
          
          // 更新本地状态
          set((state) => ({
            messages: state.messages.map((msg) =>
              msg.id === messageId ? { ...msg, is_read: true } : msg
            ),
            unreadCount: Math.max(0, state.unreadCount - 1),
          }));
        } catch (error) {
          console.error('标记消息已读失败:', error);
          throw error;
        }
      },

      createMessageAction: async (messageId: number, actionType: string) => {
        try {
          const actionData: MessageActionCreate = {
            message_id: messageId,
            action_type: actionType,
          };
          
          await messageApi.createMessageAction(messageId, actionData);
          
          // 标记消息为已读
          await get().markAsRead(messageId);
        } catch (error) {
          console.error('创建消息操作失败:', error);
          throw error;
        }
      },

      deleteMessage: async (messageId: number) => {
        try {
          await messageApi.deleteMessage(messageId);
          
          // 更新本地状态
          set((state) => {
            const deletedMessage = state.messages.find(msg => msg.id === messageId);
            const newUnreadCount = deletedMessage && !deletedMessage.is_read 
              ? Math.max(0, state.unreadCount - 1)
              : state.unreadCount;
              
            return {
              messages: state.messages.filter((msg) => msg.id !== messageId),
              total: Math.max(0, state.total - 1),
              unreadCount: newUnreadCount,
            };
          });
        } catch (error) {
          console.error('删除消息失败:', error);
          throw error;
        }
      },

      reset: () => {
        set(initialState);
      },
    }),
    {
      name: 'message-store',
    }
  )
);