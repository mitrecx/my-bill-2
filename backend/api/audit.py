from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc

from api.auth import get_current_user
from config.database import get_db
from models.audit_log import AuditLog
from models.bill import Bill
from models.user import User
from schemas.audit import AuditLogListResponse, AuditLogResponse
from schemas.common import ApiResponse
from services.bill_service import get_user_family_member_ids

router = APIRouter(prefix="/audit-logs", tags=["audit"])


def _to_audit_response(record: AuditLog) -> AuditLogResponse:
    return AuditLogResponse(
        id=record.id,
        entity_type=record.entity_type,
        entity_id=record.entity_id,
        action=record.action,
        actor_user_id=record.actor_user_id,
        actor_username=record.actor.username if record.actor else None,
        target_user_id=record.target_user_id,
        target_username=record.target_user.username if record.target_user else None,
        source=record.source,
        old_data=record.old_data,
        new_data=record.new_data,
        changed_fields=record.changed_fields,
        meta=record.meta,
        created_at=record.created_at,
    )


@router.get("", response_model=ApiResponse[AuditLogListResponse])
async def list_audit_logs(
    entity_type: str = Query("bill", description="实体类型"),
    entity_id: Optional[int] = Query(None, description="实体 ID，如账单 ID"),
    action: Optional[str] = Query(None, description="操作类型 create/update/delete"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """查询家庭范围内的数据变更审计日志。"""
    family_user_ids = get_user_family_member_ids(db, current_user.id)

    query = (
        db.query(AuditLog)
        .options(joinedload(AuditLog.actor), joinedload(AuditLog.target_user))
        .filter(AuditLog.entity_type == entity_type)
    )

    if entity_type == "bill":
        if entity_id is not None:
            bill = db.query(Bill).filter(
                Bill.id == entity_id,
                Bill.user_id.in_(family_user_ids),
            ).first()
            if not bill:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="账单不存在或无权限访问")
            query = query.filter(AuditLog.entity_id == entity_id)
        else:
            query = query.filter(
                AuditLog.entity_id.in_(
                    db.query(Bill.id).filter(Bill.user_id.in_(family_user_ids))
                )
            )

    if action:
        query = query.filter(AuditLog.action == action)

    total = query.count()
    records = (
        query.order_by(desc(AuditLog.created_at))
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )

    return ApiResponse(
        data=AuditLogListResponse(
            items=[_to_audit_response(record) for record in records],
            total=total,
            page=page,
            size=size,
        ),
        success=True,
    )
