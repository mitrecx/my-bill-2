import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from api.auth import get_current_user
from bill_mcp.context import current_mcp_user_id
from bill_mcp.server import mcp
from config.database import SessionLocal, get_db
from config.settings import settings
from models.user import User
from schemas.common import ApiResponse
from schemas.mcp import McpApiKeyCreateResponse, McpApiKeyResponse, McpServerInfoResponse
from services.mcp_api_key_service import (
    authenticate_mcp_api_key,
    create_mcp_api_key,
    get_active_mcp_api_key,
    revoke_mcp_api_key,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mcp", tags=["mcp"])

_mcp_asgi_handler = None


def _extract_api_key(request: Request) -> Optional[str]:
    auth_header = request.headers.get("authorization", "")
    if auth_header.lower().startswith("bearer "):
        return auth_header[7:].strip()
    return request.headers.get("x-mcp-api-key")


def _authenticate_request(request: Request) -> int:
    raw_key = _extract_api_key(request)
    if not raw_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="缺少 MCP API Key")

    db = SessionLocal()
    try:
        user = authenticate_mcp_api_key(db, raw_key)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的 MCP API Key")
        return user.id
    finally:
        db.close()


def _get_mcp_asgi_handler():
    global _mcp_asgi_handler
    if _mcp_asgi_handler is None:
        starlette_app = mcp.streamable_http_app()
        for route in starlette_app.routes:
            if getattr(route, "path", None) == mcp.settings.streamable_http_path:
                _mcp_asgi_handler = route.endpoint
                break
        if _mcp_asgi_handler is None:
            raise RuntimeError("MCP Streamable HTTP handler not found")
    return _mcp_asgi_handler


async def handle_mcp_transport(request: Request):
    """Streamable HTTP MCP 端点（标准路径 /mcp）。"""
    user_id = _authenticate_request(request)
    token = current_mcp_user_id.set(user_id)
    try:
        handler = _get_mcp_asgi_handler()
        await handler(request.scope, request.receive, request._send)
    finally:
        current_mcp_user_id.reset(token)


def register_mcp_transport(app) -> None:
    app.add_api_route(
        "/mcp",
        handle_mcp_transport,
        methods=["GET", "POST", "DELETE"],
        include_in_schema=False,
    )


def _build_mcp_url(request: Optional[Request] = None) -> str:
    if request is not None:
        base = str(request.base_url).rstrip("/")
        return f"{base}/mcp"
    host = settings.HOST if settings.HOST not in ("0.0.0.0", "::") else "localhost"
    return f"http://{host}:{settings.PORT}/mcp"


@router.get("/settings", response_model=ApiResponse[McpApiKeyResponse])
async def get_mcp_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = get_active_mcp_api_key(db, current_user.id)
    if not record:
        return ApiResponse(data=McpApiKeyResponse(has_key=False))
    return ApiResponse(
        data=McpApiKeyResponse(
            has_key=True,
            key_prefix=record.key_prefix,
            name=record.name,
            created_at=record.created_at,
            last_used_at=record.last_used_at,
        )
    )


@router.post("/settings/api-key", response_model=ApiResponse[McpApiKeyCreateResponse])
async def generate_mcp_api_key(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record, raw_key = create_mcp_api_key(db, current_user)
    return ApiResponse(
        data=McpApiKeyCreateResponse(
            api_key=raw_key,
            key_prefix=record.key_prefix,
            created_at=record.created_at,
        ),
        message="MCP API Key 已生成，请妥善保存，仅显示一次",
    )


@router.delete("/settings/api-key", response_model=ApiResponse)
async def delete_mcp_api_key(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    revoked = revoke_mcp_api_key(db, current_user.id)
    if not revoked:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="当前没有可用的 MCP API Key")
    return ApiResponse(message="MCP API Key 已撤销")


@router.get("/info", response_model=ApiResponse[McpServerInfoResponse])
async def get_mcp_server_info(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    mcp_url = _build_mcp_url(request)
    return ApiResponse(
        data=McpServerInfoResponse(
            server_name="Family Bills MCP",
            mcp_url=mcp_url,
            tools=[
                "create_bill",
                "create_bills_batch",
                "query_bills_batch",
                "update_bill",
                "update_bills_batch",
                "delete_bill",
                "delete_bills_batch",
            ],
            cursor_config_example={
                "mcpServers": {
                    "family-bills": {
                        "url": mcp_url,
                        "headers": {
                            "Authorization": "Bearer YOUR_MCP_API_KEY",
                        },
                    }
                }
            },
        )
    )
