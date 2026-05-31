export interface McpApiKeyStatus {
  has_key: boolean;
  key_prefix?: string;
  name?: string;
  created_at?: string;
  last_used_at?: string;
}

export interface McpApiKeyCreateResult {
  api_key: string;
  key_prefix: string;
  created_at: string;
}

export interface McpToolInfo {
  name: string;
  description: string;
}

export interface McpServerInfo {
  server_name: string;
  mcp_url: string;
  tools: McpToolInfo[];
  cursor_config_example: Record<string, unknown>;
}
