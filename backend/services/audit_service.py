from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from models.audit_log import AuditLog
from models.bill import Bill

BILL_TRACKED_FIELDS = [
    "user_id",
    "category_id",
    "transaction_time",
    "amount",
    "transaction_type",
    "transaction_desc",
    "source_type",
    "source_filename",
    "currency",
    "remark",
]


def _serialize_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, float):
        return round(value, 4)
    return value


def bill_snapshot(bill: Bill, *, include_id: bool = True) -> Dict[str, Any]:
    snapshot: Dict[str, Any] = {}
    if include_id and bill.id is not None:
        snapshot["id"] = bill.id
    for field in BILL_TRACKED_FIELDS:
        snapshot[field] = _serialize_value(getattr(bill, field, None))
    return snapshot


def compute_field_changes(
    old_data: Optional[Dict[str, Any]],
    new_data: Optional[Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    old_data = old_data or {}
    new_data = new_data or {}
    changes: Dict[str, Dict[str, Any]] = {}
    for field in set(old_data.keys()) | set(new_data.keys()):
        if field == "id":
            continue
        old_value = old_data.get(field)
        new_value = new_data.get(field)
        if old_value != new_value:
            changes[field] = {"old": old_value, "new": new_value}
    return changes


def _create_audit_log(
    db: Session,
    *,
    entity_type: str,
    entity_id: int,
    action: str,
    actor_user_id: Optional[int],
    target_user_id: Optional[int],
    source: str,
    old_data: Optional[Dict[str, Any]] = None,
    new_data: Optional[Dict[str, Any]] = None,
    changed_fields: Optional[Dict[str, Any]] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> AuditLog:
    record = AuditLog(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        actor_user_id=actor_user_id,
        target_user_id=target_user_id,
        source=source,
        old_data=old_data,
        new_data=new_data,
        changed_fields=changed_fields,
        meta=meta,
    )
    db.add(record)
    return record


def log_bill_create(
    db: Session,
    bill: Bill,
    *,
    actor_user_id: Optional[int],
    source: str,
    meta: Optional[Dict[str, Any]] = None,
) -> AuditLog:
    return _create_audit_log(
        db,
        entity_type="bill",
        entity_id=bill.id,
        action="create",
        actor_user_id=actor_user_id,
        target_user_id=bill.user_id,
        source=source,
        new_data=bill_snapshot(bill),
        meta=meta,
    )


def log_bill_update(
    db: Session,
    bill: Bill,
    *,
    old_snapshot: Dict[str, Any],
    actor_user_id: Optional[int],
    source: str,
    meta: Optional[Dict[str, Any]] = None,
) -> Optional[AuditLog]:
    new_snapshot = bill_snapshot(bill)
    changed_fields = compute_field_changes(old_snapshot, new_snapshot)
    if not changed_fields:
        return None
    return _create_audit_log(
        db,
        entity_type="bill",
        entity_id=bill.id,
        action="update",
        actor_user_id=actor_user_id,
        target_user_id=bill.user_id,
        source=source,
        old_data=old_snapshot,
        new_data=new_snapshot,
        changed_fields=changed_fields,
        meta=meta,
    )


def log_bill_delete(
    db: Session,
    bill: Bill,
    *,
    actor_user_id: Optional[int],
    source: str,
    meta: Optional[Dict[str, Any]] = None,
) -> AuditLog:
    return _create_audit_log(
        db,
        entity_type="bill",
        entity_id=bill.id,
        action="delete",
        actor_user_id=actor_user_id,
        target_user_id=bill.user_id,
        source=source,
        old_data=bill_snapshot(bill),
        meta=meta,
    )


def log_bill_creates_batch(
    db: Session,
    bills: List[Bill],
    *,
    actor_user_id: Optional[int],
    source: str,
    meta: Optional[Dict[str, Any]] = None,
) -> List[AuditLog]:
    return [
        log_bill_create(db, bill, actor_user_id=actor_user_id, source=source, meta=meta)
        for bill in bills
        if bill.id is not None
    ]


def log_bill_deletes_batch(
    db: Session,
    bills: List[Bill],
    *,
    actor_user_id: Optional[int],
    source: str,
    meta: Optional[Dict[str, Any]] = None,
) -> List[AuditLog]:
    return [
        log_bill_delete(db, bill, actor_user_id=actor_user_id, source=source, meta=meta)
        for bill in bills
        if bill.id is not None
    ]
