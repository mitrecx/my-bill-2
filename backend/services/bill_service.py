from datetime import date, datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc

from models.bill import Bill, BillCategory
from models.family import FamilyMember
from schemas.bills import BillCreate, BillResponse


TRANSACTION_TYPE_TO_CN = {
    "income": "收入",
    "expense": "支出",
    "transfer": "不计收支",
}


def get_user_family_member_ids(db: Session, user_id: int) -> List[int]:
    family_member = db.query(FamilyMember).filter(FamilyMember.user_id == user_id).first()
    if not family_member:
        return [user_id]

    members = db.query(FamilyMember).filter(FamilyMember.family_id == family_member.family_id).all()
    return [member.user_id for member in members]


def _validate_category(db: Session, category_id: Optional[int]) -> None:
    if category_id is None:
        return
    valid = (
        db.query(BillCategory)
        .filter(BillCategory.id == category_id, BillCategory.is_deleted == False)
        .first()
    )
    if not valid:
        raise ValueError("分类不存在或已删除")


def create_bill_record(db: Session, user_id: int, payload: BillCreate) -> Bill:
    _validate_category(db, payload.category_id)

    transaction_type_cn = TRANSACTION_TYPE_TO_CN.get(payload.transaction_type, payload.transaction_type)
    bill = Bill(
        user_id=user_id,
        category_id=payload.category_id,
        transaction_time=payload.transaction_time,
        amount=payload.amount,
        transaction_type=transaction_type_cn,
        transaction_desc=payload.transaction_desc or payload.description,
        source_type=payload.source_type,
        remark=payload.remark or payload.notes,
        raw_data=payload.raw_data,
    )
    db.add(bill)
    db.commit()
    db.refresh(bill)
    return bill


def create_bills_batch(db: Session, user_id: int, bills: List[BillCreate]) -> List[Bill]:
    created: List[Bill] = []
    try:
        for payload in bills:
            _validate_category(db, payload.category_id)
            transaction_type_cn = TRANSACTION_TYPE_TO_CN.get(payload.transaction_type, payload.transaction_type)
            bill = Bill(
                user_id=user_id,
                category_id=payload.category_id,
                transaction_time=payload.transaction_time,
                amount=payload.amount,
                transaction_type=transaction_type_cn,
                transaction_desc=payload.transaction_desc or payload.description,
                source_type=payload.source_type,
                remark=payload.remark or payload.notes,
                raw_data=payload.raw_data,
            )
            db.add(bill)
            created.append(bill)
        db.commit()
        for bill in created:
            db.refresh(bill)
        return created
    except Exception:
        db.rollback()
        raise


def query_bills(
    db: Session,
    user_id: int,
    *,
    page: int = 1,
    size: int = 20,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    transaction_types: Optional[List[str]] = None,
    category_ids: Optional[List[int]] = None,
    user_ids: Optional[List[int]] = None,
    search: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
) -> Dict[str, Any]:
    family_user_ids = get_user_family_member_ids(db, user_id)
    query = (
        db.query(Bill)
        .options(joinedload(Bill.category), joinedload(Bill.user))
        .filter(Bill.user_id.in_(family_user_ids))
    )

    if user_ids:
        selected = [uid for uid in user_ids if uid in family_user_ids]
        if selected:
            query = query.filter(Bill.user_id.in_(selected))

    if category_ids:
        query = query.filter(Bill.category_id.in_(category_ids))

    if transaction_types:
        cn_types = [TRANSACTION_TYPE_TO_CN.get(t, t) for t in transaction_types]
        query = query.filter(Bill.transaction_type.in_(cn_types))

    if start_date:
        query = query.filter(Bill.transaction_time >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(Bill.transaction_time <= datetime.combine(end_date, datetime.max.time()))

    if min_amount is not None:
        query = query.filter(Bill.amount >= min_amount)
    if max_amount is not None:
        query = query.filter(Bill.amount <= max_amount)

    if search:
        like = f"%{search}%"
        query = query.filter(Bill.transaction_desc.ilike(like))

    total = query.count()
    items = (
        query.order_by(desc(Bill.transaction_time))
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )

    return {
        "total": total,
        "page": page,
        "size": size,
        "items": [BillResponse.from_bill(bill).model_dump(mode="json") for bill in items],
    }
