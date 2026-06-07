import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from sqlalchemy.orm import joinedload

from config.database import SessionLocal
from bill_mcp.context import get_current_mcp_user_id
from models.family import Family, FamilyMember
from schemas.bills import BillCreate, BillUpdate
from schemas.classification_rule import ClassificationRuleCreate, ClassificationRuleUpdate
from services.bill_service import (
    create_bill_record,
    create_bills_batch as create_bills_batch_records,
    delete_bill_record,
    delete_bills_batch as delete_bills_batch_records,
    list_bill_categories,
    query_bills,
    update_bill_record,
    update_bills_batch as update_bills_batch_records,
)
from services.bill_permission_service import can_manage_bill, get_family_id_for_user
from services.classification_rule_service import (
    create_classification_rule_record,
    delete_classification_rule_record,
    list_classification_rules,
    serialize_classification_rule,
    update_classification_rule_record,
)

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
        target_user_id=data.get("target_user_id"),
    )


def _list_family_members_for_actor(db, actor_user_id: int) -> Dict[str, Any]:
    family_id = get_family_id_for_user(db, actor_user_id)
    if family_id is None:
        return {
            "family_id": None,
            "family_name": None,
            "members": [],
            "hint": "当前用户未加入家庭；创建账单时 target_user_id 请使用 API Key 对应用户 ID",
        }

    family = db.query(Family).filter(Family.id == family_id).first()
    members = (
        db.query(FamilyMember)
        .options(joinedload(FamilyMember.user))
        .filter(FamilyMember.family_id == family_id)
        .order_by(FamilyMember.id.asc())
        .all()
    )

    serialized = []
    for member in members:
        uid = member.user_id
        user = member.user
        serialized.append(
            {
                "user_id": uid,
                "username": user.username if user else None,
                "full_name": user.full_name if user else None,
                "role": member.role,
                "is_self": uid == actor_user_id,
                "bill_permissions": {
                    "can_create": can_manage_bill(db, actor_user_id, uid, "create"),
                    "can_update": can_manage_bill(db, actor_user_id, uid, "update"),
                    "can_delete": can_manage_bill(db, actor_user_id, uid, "delete"),
                },
            }
        )

    return {
        "family_id": family_id,
        "family_name": family.family_name if family else None,
        "members": serialized,
        "hint": "创建账单时 target_user_id 填成员的 user_id；仅 bill_permissions.can_create 为 true 的成员可作为归属人",
    }


@mcp.tool()
def query_family_members() -> str:
    """查询当前用户所在家庭的成员列表及账单操作权限。

    用于确定 create_bill / create_bills_batch 的 target_user_id（账单归属成员）。
    返回每位成员的 user_id、姓名，以及当前 API Key 用户对其账单的录入/修改/删除权限。
    """
    actor_user_id = get_current_mcp_user_id()
    db = SessionLocal()
    try:
        data = _list_family_members_for_actor(db, actor_user_id)
        return json.dumps({"success": True, **data}, ensure_ascii=False)
    except Exception as exc:
        logger.error("MCP query_family_members failed: %s", exc)
        return json.dumps({"success": False, "message": str(exc)}, ensure_ascii=False)
    finally:
        db.close()


@mcp.tool()
def create_bill(
    amount: float,
    transaction_time: str,
    transaction_type: str = "expense",
    transaction_desc: Optional[str] = None,
    category_id: Optional[int] = None,
    remark: Optional[str] = None,
    source_type: str = "manual",
    target_user_id: Optional[int] = None,
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
        target_user_id: 账单归属成员用户 ID（可选，默认 API Key 用户；可先调用 query_family_members 获取）
    """
    user_id = get_current_mcp_user_id()
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
                "target_user_id": target_user_id,
            }
        )
        bill = create_bill_record(db, user_id, payload, source="mcp")
        return json.dumps(
            {
                "success": True,
                "message": "创建账单成功",
                "bill": {"id": bill.id, "amount": bill.amount, "user_id": bill.user_id},
            },
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
        bills: 账单列表，每项包含 amount、transaction_time、transaction_type 等字段；
               可选 target_user_id 指定归属成员（可先调用 query_family_members）
    """
    user_id = get_current_mcp_user_id()
    db = SessionLocal()
    try:
        payloads = [_build_bill_create(item) for item in bills]
        created: List[Any] = []
        by_owner: Dict[int, List[BillCreate]] = {}
        for payload in payloads:
            owner_id = payload.target_user_id or user_id
            by_owner.setdefault(owner_id, []).append(payload)

        for owner_id, owner_payloads in by_owner.items():
            if len(owner_payloads) == 1:
                created.append(
                    create_bill_record(db, user_id, owner_payloads[0], owner_user_id=owner_id, source="mcp")
                )
            else:
                created.extend(
                    create_bills_batch_records(
                        db, user_id, owner_payloads, owner_user_id=owner_id, source="mcp"
                    )
                )
        return json.dumps(
            {
                "success": True,
                "message": f"成功创建 {len(created)} 条账单",
                "created_count": len(created),
                "bill_ids": [bill.id for bill in created],
                "bills": [{"id": bill.id, "user_id": bill.user_id} for bill in created],
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
    user_id = get_current_mcp_user_id()
    db = SessionLocal()
    try:
        from datetime import date as date_type

        parsed_start = date_type.fromisoformat(start_date) if start_date else None
        parsed_end = date_type.fromisoformat(end_date) if end_date else None
        result = query_bills(
            db,
            user_id,
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


@mcp.tool()
def query_bill_categories(
    category_type: Optional[str] = None,
    search: Optional[str] = None,
) -> str:
    """查询账单分类列表，用于创建/修改账单时确定 category_id。

    Args:
        category_type: 分类类型，可选 income（收入）或 expense（支出）
        search: 按分类名称或描述关键词筛选
    """
    db = SessionLocal()
    try:
        if category_type and category_type not in ("income", "expense"):
            return json.dumps(
                {"success": False, "message": "category_type 仅支持 income 或 expense"},
                ensure_ascii=False,
            )
        categories = list_bill_categories(db, category_type=category_type, search=search)
        return json.dumps(
            {
                "success": True,
                "total": len(categories),
                "categories": categories,
            },
            ensure_ascii=False,
        )
    except Exception as exc:
        logger.error("MCP query_bill_categories failed: %s", exc)
        return json.dumps({"success": False, "message": str(exc)}, ensure_ascii=False)
    finally:
        db.close()


@mcp.tool()
def query_classification_rules(
    page: int = 1,
    page_size: int = 20,
    scope: Optional[str] = None,
    source_type: Optional[str] = None,
    target_category: Optional[str] = None,
    transaction_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
) -> str:
    """查询当前用户可见的自定义分类规则（个人规则 + 家庭规则）。

    Args:
        page: 页码，从 1 开始
        page_size: 每页条数，最大 100
        scope: 作用域 personal/family
        source_type: 来源类型 alipay/jd/cmb/wechat/meituan/manual/all
        target_category: 目标分类名称
        transaction_type: 交易类型 expense/income/transfer
        is_active: 是否启用
        search: 搜索规则文本或目标分类
    """
    user_id = get_current_mcp_user_id()
    db = SessionLocal()
    try:
        result = list_classification_rules(
            db,
            user_id,
            page=page,
            page_size=page_size,
            scope=scope,
            source_type=source_type,
            target_category=target_category,
            transaction_type=transaction_type,
            is_active=is_active,
            search=search,
        )
        return json.dumps({"success": True, **result}, ensure_ascii=False)
    except Exception as exc:
        logger.error("MCP query_classification_rules failed: %s", exc)
        return json.dumps({"success": False, "message": str(exc)}, ensure_ascii=False)
    finally:
        db.close()


@mcp.tool()
def create_classification_rule(
    rule_text: str,
    source_type: str,
    target_category: str,
    transaction_type: str = "expense",
    scope: str = "personal",
    priority: int = 0,
    is_active: bool = True,
) -> str:
    """创建分类规则（personal 仅对自己生效，family 对家庭所有成员生效；AI 自动分类时注入提示词供优先参考）。

    Args:
        rule_text: 供 AI 参考的自然语言描述（如商户名、关键词短语），非正则表达式
        source_type: 来源类型 alipay/jd/cmb/wechat/meituan/manual/all
        target_category: 目标分类名称（须为系统中已存在的分类名）
        transaction_type: 适用交易类型 expense/income/transfer
        scope: 作用域 personal/family，默认 personal
        priority: 优先级，数字越大越优先
        is_active: 是否启用
    """
    user_id = get_current_mcp_user_id()
    db = SessionLocal()
    try:
        payload = ClassificationRuleCreate(
            rule_text=rule_text,
            source_type=source_type,
            target_category=target_category,
            transaction_type=transaction_type,
            scope=scope,
            priority=priority,
            is_active=is_active,
        )
        rule = create_classification_rule_record(db, user_id, payload)
        return json.dumps(
            {
                "success": True,
                "message": "分类规则创建成功",
                "rule": serialize_classification_rule(rule),
            },
            ensure_ascii=False,
        )
    except Exception as exc:
        logger.error("MCP create_classification_rule failed: %s", exc)
        return json.dumps({"success": False, "message": str(exc)}, ensure_ascii=False)
    finally:
        db.close()


@mcp.tool()
def update_classification_rule(
    rule_id: int,
    rule_text: Optional[str] = None,
    source_type: Optional[str] = None,
    target_category: Optional[str] = None,
    transaction_type: Optional[str] = None,
    scope: Optional[str] = None,
    priority: Optional[int] = None,
    is_active: Optional[bool] = None,
) -> str:
    """更新分类规则（个人规则仅创建者可改，家庭规则家庭成员均可改）。

    Args:
        rule_id: 规则 ID
        rule_text: 供 AI 参考的自然语言描述（可选）
        source_type: 来源类型（可选）
        target_category: 目标分类名称（可选）
        transaction_type: 适用交易类型 expense/income/transfer（可选）
        scope: 作用域 personal/family（可选）
        priority: 优先级（可选）
        is_active: 是否启用（可选）
    """
    user_id = get_current_mcp_user_id()
    db = SessionLocal()
    try:
        payload = ClassificationRuleUpdate(
            rule_text=rule_text,
            source_type=source_type,
            target_category=target_category,
            transaction_type=transaction_type,
            scope=scope,
            priority=priority,
            is_active=is_active,
        )
        rule = update_classification_rule_record(db, user_id, rule_id, payload)
        return json.dumps(
            {
                "success": True,
                "message": "分类规则更新成功",
                "rule": serialize_classification_rule(rule),
            },
            ensure_ascii=False,
        )
    except Exception as exc:
        logger.error("MCP update_classification_rule failed: %s", exc)
        return json.dumps({"success": False, "message": str(exc)}, ensure_ascii=False)
    finally:
        db.close()


@mcp.tool()
def delete_classification_rule(rule_id: int) -> str:
    """删除分类规则（个人规则仅创建者可删，家庭规则家庭成员均可删）。

    Args:
        rule_id: 规则 ID
    """
    user_id = get_current_mcp_user_id()
    db = SessionLocal()
    try:
        delete_classification_rule_record(db, user_id, rule_id)
        return json.dumps(
            {"success": True, "message": "分类规则删除成功", "rule_id": rule_id},
            ensure_ascii=False,
        )
    except Exception as exc:
        logger.error("MCP delete_classification_rule failed: %s", exc)
        return json.dumps({"success": False, "message": str(exc)}, ensure_ascii=False)
    finally:
        db.close()


@mcp.tool()
def delete_bill(bill_id: int) -> str:
    """删除单条账单（可删除本人账单，或他人授权可删的账单）。

    Args:
        bill_id: 账单 ID
    """
    user_id = get_current_mcp_user_id()
    db = SessionLocal()
    try:
        delete_bill_record(db, user_id, bill_id, source="mcp")
        return json.dumps({"success": True, "message": "账单删除成功", "bill_id": bill_id}, ensure_ascii=False)
    except Exception as exc:
        logger.error("MCP delete_bill failed: %s", exc)
        return json.dumps({"success": False, "message": str(exc)}, ensure_ascii=False)
    finally:
        db.close()


@mcp.tool()
def delete_bills_batch(bill_ids: List[int]) -> str:
    """批量删除账单（可删除本人账单，或他人授权可删的账单）。

    Args:
        bill_ids: 要删除的账单 ID 列表
    """
    user_id = get_current_mcp_user_id()
    db = SessionLocal()
    try:
        result = delete_bills_batch_records(db, user_id, bill_ids, source="mcp")
        return json.dumps(
            {
                "success": len(result["failed"]) == 0,
                "message": f"成功删除 {len(result['deleted_ids'])} 条账单",
                **result,
            },
            ensure_ascii=False,
        )
    except Exception as exc:
        logger.error("MCP delete_bills_batch failed: %s", exc)
        return json.dumps({"success": False, "message": str(exc)}, ensure_ascii=False)
    finally:
        db.close()


@mcp.tool()
def update_bill(
    bill_id: int,
    amount: Optional[float] = None,
    transaction_type: Optional[str] = None,
    transaction_desc: Optional[str] = None,
    category_id: Optional[int] = None,
    remark: Optional[str] = None,
) -> str:
    """修改单条账单（可修改本人账单，或他人授权可改的账单；只更新传入的字段）。

    Args:
        bill_id: 账单 ID
        amount: 金额（可选）
        transaction_type: 交易类型 income/expense/transfer（可选）
        transaction_desc: 交易描述（可选）
        category_id: 分类 ID（可选）
        remark: 备注（可选）
    """
    user_id = get_current_mcp_user_id()
    db = SessionLocal()
    try:
        payload = BillUpdate(
            amount=amount,
            transaction_type=transaction_type,
            transaction_desc=transaction_desc,
            category_id=category_id,
            remark=remark,
        )
        bill = update_bill_record(db, user_id, bill_id, payload, source="mcp")
        return json.dumps(
            {"success": True, "message": "更新账单成功", "bill": {"id": bill.id, "amount": bill.amount}},
            ensure_ascii=False,
        )
    except Exception as exc:
        logger.error("MCP update_bill failed: %s", exc)
        return json.dumps({"success": False, "message": str(exc)}, ensure_ascii=False)
    finally:
        db.close()


@mcp.tool()
def update_bills_batch(bills: List[Dict[str, Any]]) -> str:
    """批量修改账单（可修改本人账单，或他人授权可改的账单）。

    Args:
        bills: 账单更新列表，每项需包含 bill_id，以及要更新的字段
    """
    user_id = get_current_mcp_user_id()
    db = SessionLocal()
    try:
        result = update_bills_batch_records(db, user_id, bills, source="mcp")
        return json.dumps(
            {
                "success": len(result["failed"]) == 0,
                "message": f"成功更新 {len(result['updated'])} 条账单",
                **result,
            },
            ensure_ascii=False,
        )
    except Exception as exc:
        logger.error("MCP update_bills_batch failed: %s", exc)
        return json.dumps({"success": False, "message": str(exc)}, ensure_ascii=False)
    finally:
        db.close()


def _tool_description_summary(description: Optional[str]) -> str:
    if not description:
        return ""
    first_line = description.strip().splitlines()[0].strip()
    return first_line.rstrip("：:")


def list_registered_mcp_tools() -> List[Dict[str, str]]:
    """Return MCP tools registered on the server (name + short description)."""
    return [
        {
            "name": tool.name,
            "description": _tool_description_summary(tool.description),
        }
        for tool in mcp._tool_manager.list_tools()
    ]
