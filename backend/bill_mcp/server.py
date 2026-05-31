import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from config.database import SessionLocal
from bill_mcp.context import get_current_mcp_user
from schemas.bills import BillCreate
from services.bill_service import create_bill_record, create_bills_batch, query_bills

logger = logging.getLogger(__name__)

mcp = FastMCP(
    "Family Bills MCP",
    stateless_http=True,
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=[
            "127.0.0.1:*",
            "localhost:*",
            "[::1]:*",
            "bill.mitrecx.top",
            "bill.mitrecx.top:*",
        ],
    ),
)


def _parse_datetime(value: str) -> datetime:
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise ValueError(f"无法解析时间: {value}")


def _build_bill_create(data: Dict[str, Any]) -> BillCreate:
    transaction_time = data.get("transaction_time")
    if isinstance(transaction_time, str):
        transaction_time = _parse_datetime(transaction_time)

    return BillCreate(
        amount=float(data["amount"]),
        transaction_type=data.get("transaction_type", "expense"),
        transaction_time=transaction_time,
        source_type=data.get("source_type", "manual"),
        transaction_desc=data.get("transaction_desc") or data.get("description"),
        remark=data.get("remark") or data.get("notes"),
        category_id=data.get("category_id"),
        raw_data=data.get("raw_data"),
    )


@mcp.tool()
def create_bill(
    amount: float,
    transaction_time: str,
    transaction_type: str = "expense",
    transaction_desc: Optional[str] = None,
    category_id: Optional[int] = None,
    remark: Optional[str] = None,
    source_type: str = "manual",
) -> str:
    """录入单条家庭账单。

    Args:
        amount: 金额（正数）
        transaction_time: 交易时间，支持 YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS
        transaction_type: 交易类型 income/expense/transfer
        transaction_desc: 交易描述
        category_id: 分类 ID（可选）
        remark: 备注（可选）
        source_type: 来源类型，默认 manual
    """
    user = get_current_mcp_user()
    db = SessionLocal()
    try:
        payload = _build_bill_create(
            {
                "amount": amount,
                "transaction_time": transaction_time,
                "transaction_type": transaction_type,
                "transaction_desc": transaction_desc,
                "category_id": category_id,
                "remark": remark,
                "source_type": source_type,
            }
        )
        bill = create_bill_record(db, user.id, payload)
        return json.dumps(
            {"success": True, "message": "创建账单成功", "bill": {"id": bill.id, "amount": bill.amount}},
            ensure_ascii=False,
        )
    except Exception as exc:
        logger.error("MCP create_bill failed: %s", exc)
        return json.dumps({"success": False, "message": str(exc)}, ensure_ascii=False)
    finally:
        db.close()


@mcp.tool()
def create_bills_batch(bills: List[Dict[str, Any]]) -> str:
    """批量录入家庭账单。

    Args:
        bills: 账单列表，每项包含 amount、transaction_time、transaction_type 等字段
    """
    user = get_current_mcp_user()
    db = SessionLocal()
    try:
        payloads = [_build_bill_create(item) for item in bills]
        created = create_bills_batch(db, user.id, payloads)
        return json.dumps(
            {
                "success": True,
                "message": f"成功创建 {len(created)} 条账单",
                "created_count": len(created),
                "bill_ids": [bill.id for bill in created],
            },
            ensure_ascii=False,
        )
    except Exception as exc:
        logger.error("MCP create_bills_batch failed: %s", exc)
        return json.dumps({"success": False, "message": str(exc)}, ensure_ascii=False)
    finally:
        db.close()


@mcp.tool()
def query_bills_batch(
    page: int = 1,
    size: int = 20,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    transaction_types: Optional[List[str]] = None,
    category_ids: Optional[List[int]] = None,
    user_ids: Optional[List[int]] = None,
    search: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
) -> str:
    """批量查询家庭账单，支持多条件筛选。

    Args:
        page: 页码，从 1 开始
        size: 每页条数，最大 100
        start_date: 开始日期 YYYY-MM-DD
        end_date: 结束日期 YYYY-MM-DD
        transaction_types: 交易类型列表 income/expense/transfer
        category_ids: 分类 ID 列表
        user_ids: 家庭成员用户 ID 列表
        search: 描述关键词
        min_amount: 最小金额
        max_amount: 最大金额
    """
    user = get_current_mcp_user()
    db = SessionLocal()
    try:
        from datetime import date as date_type

        parsed_start = date_type.fromisoformat(start_date) if start_date else None
        parsed_end = date_type.fromisoformat(end_date) if end_date else None
        result = query_bills(
            db,
            user.id,
            page=max(page, 1),
            size=min(max(size, 1), 100),
            start_date=parsed_start,
            end_date=parsed_end,
            transaction_types=transaction_types,
            category_ids=category_ids,
            user_ids=user_ids,
            search=search,
            min_amount=min_amount,
            max_amount=max_amount,
        )
        return json.dumps({"success": True, "data": result}, ensure_ascii=False, default=str)
    except Exception as exc:
        logger.error("MCP query_bills_batch failed: %s", exc)
        return json.dumps({"success": False, "message": str(exc)}, ensure_ascii=False)
    finally:
        db.close()
