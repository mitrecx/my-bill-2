from contextvars import ContextVar
from typing import Optional

from models.user import User

current_mcp_user: ContextVar[Optional[User]] = ContextVar("current_mcp_user", default=None)


def get_current_mcp_user() -> User:
    user = current_mcp_user.get()
    if user is None:
        raise RuntimeError("MCP 用户上下文未设置")
    return user
