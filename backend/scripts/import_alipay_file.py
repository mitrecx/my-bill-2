#!/usr/bin/env python3
"""One-off Alipay bill import via server-side parser + DB (mirrors upload API)."""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, List

from sqlalchemy.orm import Session

from config.database import SessionLocal
from models.bill import Bill, BillCategory
from models.family import FamilyMember
from parsers.alipay_parser import AlipayParser


def get_family_user_ids(db: Session, user_id: int) -> List[int]:
    member = db.query(FamilyMember).filter(FamilyMember.user_id == user_id).first()
    if not member:
        return [user_id]
    members = db.query(FamilyMember).filter(FamilyMember.family_id == member.family_id).all()
    return [m.user_id for m in members]


def is_duplicate_alipay_record(db: Session, family_user_ids: List[int], record: dict) -> bool:
    transaction_time = record.get("transaction_time")
    amount = record.get("amount")
    transaction_desc = record.get("transaction_desc") or ""
    if not transaction_time or amount is None:
        return False
    existing = (
        db.query(Bill)
        .filter(
            Bill.user_id.in_(family_user_ids),
            Bill.source_type == "alipay",
            Bill.transaction_time == transaction_time,
            Bill.amount == amount,
            Bill.transaction_desc == transaction_desc,
        )
        .first()
    )
    return existing is not None


def import_alipay_file(file_path: str, user_id: int, filename: str, auto_categorize: bool = True) -> Dict:
    parser = AlipayParser()
    parse_result = parser.parse_file(file_path)
    if parse_result.errors and not parse_result.success_records:
        raise RuntimeError("; ".join(parse_result.errors))

    db = SessionLocal()
    try:
        family_user_ids = get_family_user_ids(db, user_id)
        default_category = (
            db.query(BillCategory)
            .filter(BillCategory.category_name == "其他", BillCategory.is_deleted == False)
            .first()
        )

        created_bills: List[Bill] = []
        skipped = 0
        failed = 0

        for record in parse_result.success_records:
            try:
                if is_duplicate_alipay_record(db, family_user_ids, record):
                    skipped += 1
                    continue

                category = default_category
                if auto_categorize and record.get("category"):
                    matched = (
                        db.query(BillCategory)
                        .filter(
                            BillCategory.category_name == record["category"],
                            BillCategory.is_deleted == False,
                        )
                        .first()
                    )
                    if matched:
                        category = matched

                bill = Bill(
                    user_id=user_id,
                    amount=record["amount"],
                    transaction_time=record["transaction_time"],
                    transaction_type=record["transaction_type"],
                    transaction_desc=record.get("transaction_desc", ""),
                    source_type="alipay",
                    source_filename=filename,
                    category_id=category.id if category else None,
                    currency=record.get("currency", "CNY"),
                    raw_data=record.get("raw_data", {}),
                )
                db.add(bill)
                created_bills.append(bill)
            except Exception:
                failed += 1

        db.commit()
        for bill in created_bills:
            db.refresh(bill)

        ai_classified = 0
        if auto_categorize and created_bills:
            from services.ai_classification_service import ai_classification_service

            if ai_classification_service.is_available():
                bills_data = [
                    {
                        "id": bill.id,
                        "amount": float(bill.amount),
                        "transaction_type": bill.transaction_type,
                        "description": bill.transaction_desc or "",
                        "source_type": bill.source_type,
                    }
                    for bill in created_bills
                ]
                results = ai_classification_service.classify_bills_batch_optimized(
                    bills_data, db, user_id
                )
                for bill_id, category_name in results:
                    if not category_name:
                        continue
                    bill = db.query(Bill).filter(Bill.id == bill_id).first()
                    category = (
                        db.query(BillCategory)
                        .filter(
                            BillCategory.category_name == category_name,
                            BillCategory.is_deleted == False,
                        )
                        .first()
                    )
                    if bill and category:
                        bill.category_id = category.id
                        ai_classified += 1
                db.commit()

        return {
            "parsed": parse_result.success_count,
            "created": len(created_bills),
            "skipped_duplicates": skipped,
            "failed": failed + parse_result.failed_count,
            "ai_classified": ai_classified,
            "bill_ids": [b.id for b in created_bills],
        }
    finally:
        db.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("file_path")
    ap.add_argument("--user-id", type=int, default=2, help="Bill owner user id (default: josie)")
    ap.add_argument("--no-ai", action="store_true")
    args = ap.parse_args()
    filename = os.path.basename(args.file_path)
    result = import_alipay_file(
        args.file_path,
        args.user_id,
        filename,
        auto_categorize=not args.no_ai,
    )
    print(result)
