import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from api.auth import get_current_user
from config.database import get_db
from models.bill_delegation import BillDelegation
from models.family import FamilyMember
from models.user import User
from schemas.bill_delegations import (
    BillDelegationCreate,
    BillDelegationListResponse,
    BillDelegationResponse,
)
from schemas.common import ApiResponse
from services.bill_permission_service import (
    assert_same_family,
    get_family_id_for_user,
    is_delegation_valid,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/bill-delegations", tags=["bill-delegations"])


def _user_display_name(user: Optional[User]) -> Optional[str]:
    if not user:
        return None
    return user.full_name or user.username


def _to_response(delegation: BillDelegation) -> BillDelegationResponse:
    return BillDelegationResponse(
        id=delegation.id,
        family_id=delegation.family_id,
        grantor_user_id=delegation.grantor_user_id,
        grantee_user_id=delegation.grantee_user_id,
        grantor_name=_user_display_name(delegation.grantor),
        grantee_name=_user_display_name(delegation.grantee),
        can_create=delegation.can_create,
        can_update=delegation.can_update,
        can_delete=delegation.can_delete,
        is_active=delegation.is_active,
        expires_at=delegation.expires_at,
        created_at=delegation.created_at,
        updated_at=delegation.updated_at,
    )


@router.get("", response_model=ApiResponse[BillDelegationListResponse])
async def list_bill_delegations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """列出当前用户授予他人、以及他人授予当前用户的账单代管授权。"""
    try:
        family_id = get_family_id_for_user(db, current_user.id)
        if family_id is None:
            return ApiResponse(
                data=BillDelegationListResponse(granted=[], received=[]),
                success=True,
                message="当前用户未加入家庭",
            )

        base_query = (
            db.query(BillDelegation)
            .options(
                joinedload(BillDelegation.grantor),
                joinedload(BillDelegation.grantee),
            )
            .filter(
                BillDelegation.family_id == family_id,
                BillDelegation.is_active == True,
            )
        )

        granted = [
            item
            for item in base_query.filter(BillDelegation.grantor_user_id == current_user.id).all()
            if is_delegation_valid(item)
        ]
        received = [
            item
            for item in base_query.filter(BillDelegation.grantee_user_id == current_user.id).all()
            if is_delegation_valid(item)
        ]

        return ApiResponse(
            data=BillDelegationListResponse(
                granted=[_to_response(item) for item in granted],
                received=[_to_response(item) for item in received],
            ),
            success=True,
            message="获取账单授权成功",
        )
    except Exception as exc:
        logger.error("获取账单授权失败: %s", exc)
        raise HTTPException(status_code=500, detail="获取账单授权失败")


@router.post("", response_model=ApiResponse[BillDelegationResponse])
async def create_or_update_bill_delegation(
    payload: BillDelegationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """授予家庭成员代管本人账单的权限（仅授权人可操作）。"""
    try:
        if payload.grantee_user_id == current_user.id:
            raise HTTPException(status_code=400, detail="不能授权给自己")

        family_id = get_family_id_for_user(db, current_user.id)
        if family_id is None:
            raise HTTPException(status_code=400, detail="请先加入家庭后再设置账单授权")

        grantee_member = (
            db.query(FamilyMember)
            .filter(
                FamilyMember.family_id == family_id,
                FamilyMember.user_id == payload.grantee_user_id,
            )
            .first()
        )
        if not grantee_member:
            raise HTTPException(status_code=400, detail="被授权成员不在当前家庭中")

        assert_same_family(db, current_user.id, payload.grantee_user_id)

        if payload.expires_at is not None:
            expires_at = payload.expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if expires_at <= datetime.now(timezone.utc):
                raise HTTPException(status_code=400, detail="过期时间必须晚于当前时间")

        if not (payload.can_create or payload.can_update or payload.can_delete):
            raise HTTPException(status_code=400, detail="至少勾选一项账单操作权限")

        existing = (
            db.query(BillDelegation)
            .options(
                joinedload(BillDelegation.grantor),
                joinedload(BillDelegation.grantee),
            )
            .filter(
                BillDelegation.grantor_user_id == current_user.id,
                BillDelegation.grantee_user_id == payload.grantee_user_id,
            )
            .first()
        )

        if existing:
            existing.family_id = family_id
            existing.can_create = payload.can_create
            existing.can_update = payload.can_update
            existing.can_delete = payload.can_delete
            existing.expires_at = payload.expires_at
            existing.is_active = True
            existing.updated_at = datetime.now(timezone.utc)
            delegation = existing
        else:
            delegation = BillDelegation(
                family_id=family_id,
                grantor_user_id=current_user.id,
                grantee_user_id=payload.grantee_user_id,
                can_create=payload.can_create,
                can_update=payload.can_update,
                can_delete=payload.can_delete,
                expires_at=payload.expires_at,
                is_active=True,
            )
            db.add(delegation)

        db.commit()
        db.refresh(delegation)
        delegation = (
            db.query(BillDelegation)
            .options(
                joinedload(BillDelegation.grantor),
                joinedload(BillDelegation.grantee),
            )
            .filter(BillDelegation.id == delegation.id)
            .first()
        )

        return ApiResponse(
            data=_to_response(delegation),
            success=True,
            message="账单授权已保存",
        )
    except HTTPException:
        db.rollback()
        raise
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        db.rollback()
        logger.error("保存账单授权失败: %s", exc)
        raise HTTPException(status_code=500, detail="保存账单授权失败")


@router.delete("/{delegation_id}", response_model=ApiResponse[dict])
async def revoke_bill_delegation(
    delegation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """撤销本人授予他人的账单代管授权。"""
    try:
        delegation = (
            db.query(BillDelegation)
            .filter(
                BillDelegation.id == delegation_id,
                BillDelegation.grantor_user_id == current_user.id,
            )
            .first()
        )
        if not delegation:
            raise HTTPException(status_code=404, detail="授权记录不存在或无权限撤销")

        delegation.is_active = False
        delegation.updated_at = datetime.now(timezone.utc)
        db.commit()

        return ApiResponse(
            data={"message": "账单授权已撤销"},
            success=True,
            message="账单授权已撤销",
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.error("撤销账单授权失败: %s", exc)
        raise HTTPException(status_code=500, detail="撤销账单授权失败")
