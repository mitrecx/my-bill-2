from contextvars import ContextVar
from typing import Optional

current_mcp_user_id: ContextVar[Optional[int]] = ContextVar("current_mcp_user_id", default=None)


def get_current_mcp_user_id() -> int:
    user_id = current_mcp_user_id.get()
    if user_id is None:
        raise RuntimeError("MCP 用户上下文未设置")
    return user_id
