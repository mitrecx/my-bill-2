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
  role: 'admin' | 'member';
  created_at: string;
  user: {
    id: number;
    username: string;
    full_name?: string;
    email: string;
  };
}

export interface FamilyCreate {
  family_name: string;
  description?: string;
  invite_usernames?: string[];
}

export interface FamilyUpdate {
  family_name?: string;
  description?: string;
}

export interface UserSearchResult {
  id: number;
  username: string;
  full_name?: string;
  email: string;
}

export interface FamilyListResponse {
  families: Family[];
}

export interface FamilyMemberListResponse {
  members: FamilyMember[];
}