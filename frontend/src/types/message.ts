export interface Message {
  id: number;
  sender_id?: number;
  receiver_id: number;
  message_type: string;
  title: string;
  content: string;
  data?: Record<string, any>;
  is_read: boolean;
  created_at: string;
  updated_at: string;
}

export interface MessageAction {
  id: number;
  message_id: number;
  user_id: number;
  action_type: string;
  created_at: string;
}

export interface MessageListResponse {
  items: Message[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface MessageCreate {
  receiver_id: number;
  sender_id?: number;
  message_type: string;
  title: string;
  content: string;
  data?: Record<string, any>;
}

export interface MessageUpdate {
  is_read?: boolean;
}

export interface MessageActionCreate {
  message_id: number;
  action_type: string;
}