from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from sqlalchemy.orm import Session

from models.bill_delegation import BillDelegation
from models.family import FamilyMember

BillAction = Literal["create", "update", "delete"]

_ACTION_FIELD = {
    "create": "can_create",
    "update": "can_update",
    "delete": "can_delete",
}


def get_family_id_for_user(db: Session, user_id: int) -> Optional[int]:
    member = db.query(FamilyMember).filter(FamilyMember.user_id == user_id).first()
    return member.family_id if member else None


def get_family_member_user_ids(db: Session, user_id: int) -> List[int]:
    family_id = get_family_id_for_user(db, user_id)
    if family_id is None:
        return [user_id]
    members = db.query(FamilyMember).filter(FamilyMember.family_id == family_id).all()
    return [member.user_id for member in members]


def assert_same_family(db: Session, user_a: int, user_b: int) -> None:
    if user_a == user_b:
        return
    family_a = get_family_id_for_user(db, user_a)
    family_b = get_family_id_for_user(db, user_b)
    if family_a is None or family_b is None or family_a != family_b:
        raise ValueError("仅可授权同一家庭成员")


def _is_delegation_valid(delegation: BillDelegation, now: Optional[datetime] = None) -> bool:
    if not delegation.is_active:
        return False
    if delegation.expires_at is None:
        return True
    current = now or datetime.now(timezone.utc)
    expires = delegation.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    return expires > current


def get_active_delegation(
    db: Session,
    grantee_user_id: int,
    grantor_user_id: int,
) -> Optional[BillDelegation]:
    delegation = (
        db.query(BillDelegation)
        .filter(
            BillDelegation.grantor_user_id == grantor_user_id,
            BillDelegation.grantee_user_id == grantee_user_id,
            BillDelegation.is_active == True,
        )
        .first()
    )
    if delegation and _is_delegation_valid(delegation):
        return delegation
    return None


def can_manage_bill(
    db: Session,
    actor_user_id: int,
    owner_user_id: int,
    action: BillAction,
) -> bool:
    if actor_user_id == owner_user_id:
        return True
    delegation = get_active_delegation(db, actor_user_id, owner_user_id)
    if not delegation:
        return False
    return bool(getattr(delegation, _ACTION_FIELD[action]))


def require_manage_bill(
    db: Session,
    actor_user_id: int,
    owner_user_id: int,
    action: BillAction,
) -> None:
    assert_same_family(db, actor_user_id, owner_user_id)
    if not can_manage_bill(db, actor_user_id, owner_user_id, action):
        action_labels = {"create": "创建", "update": "修改", "delete": "删除"}
        raise ValueError(f"无权限{action_labels[action]}该成员的账单")


def delegation_audit_meta(
    actor_user_id: int,
    owner_user_id: int,
) -> Optional[Dict[str, Any]]:
    if actor_user_id == owner_user_id:
        return None
    return {
        "delegated": True,
        "grantor_user_id": owner_user_id,
        "grantee_user_id": actor_user_id,
    }
