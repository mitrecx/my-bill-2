export interface BillDelegation {
  id: number;
  family_id: number;
  grantor_user_id: number;
  grantee_user_id: number;
  grantor_name?: string | null;
  grantee_name?: string | null;
  can_create: boolean;
  can_update: boolean;
  can_delete: boolean;
  is_active: boolean;
  expires_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface BillDelegationList {
  granted: BillDelegation[];
  received: BillDelegation[];
}

export interface BillDelegationCreate {
  grantee_user_id: number;
  can_create?: boolean;
  can_update?: boolean;
  can_delete?: boolean;
  expires_at?: string | null;
}
