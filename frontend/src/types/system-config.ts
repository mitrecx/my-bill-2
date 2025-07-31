// 系统配置相关类型
export interface SystemConfig {
  id: number;
  config_key: string;
  config_value: string;
  config_type: 'string' | 'int' | 'float' | 'bool' | 'json';
  description?: string;
  is_encrypted: boolean;
  created_at: string;
  updated_at: string;
}

export interface SystemConfigCreate {
  config_key: string;
  config_value: string;
  config_type?: 'string' | 'int' | 'float' | 'bool' | 'json';
  description?: string;
  is_encrypted?: boolean;
}

export interface SystemConfigUpdate {
  config_value?: string;
  config_type?: 'string' | 'int' | 'float' | 'bool' | 'json';
  description?: string;
  is_encrypted?: boolean;
}

export interface DefaultPasswordConfig {
  default_password: string;
}

export interface SystemConfigBatch {
  configs: SystemConfigCreate[];
}

export interface SystemConfigResponse {
  id: number;
  config_key: string;
  config_value: string;
  config_type: string;
  description?: string;
  is_encrypted: boolean;
  created_at: string;
  updated_at: string;
}