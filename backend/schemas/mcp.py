from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class McpApiKeyResponse(BaseModel):
    has_key: bool
    key_prefix: Optional[str] = None
    name: Optional[str] = None
    created_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None


class McpApiKeyCreateResponse(BaseModel):
    api_key: str = Field(..., description="明文 API Key，仅创建时返回一次")
    key_prefix: str
    created_at: datetime


class McpServerInfoResponse(BaseModel):
    server_name: str
    mcp_url: str
    tools: List[str]
    cursor_config_example: dict
