export interface AuditLog {
  id: number;
  entity_type: string;
  entity_id: number;
  action: 'create' | 'update' | 'delete' | string;
  actor_user_id?: number | null;
  actor_username?: string | null;
  target_user_id?: number | null;
  target_username?: string | null;
  source: string;
  old_data?: Record<string, unknown> | null;
  new_data?: Record<string, unknown> | null;
  changed_fields?: Record<string, { old?: unknown; new?: unknown }> | null;
  meta?: Record<string, unknown> | null;
  created_at: string;
}

export interface AuditLogListResponse {
  items: AuditLog[];
  total: number;
  page: number;
  size: number;
}

export interface AuditLogQueryParams {
  entity_type?: string;
  entity_id?: number;
  action?: string;
  page?: number;
  size?: number;
}
