#!/usr/bin/env python3
"""One-off WeChat bill import via server-side parser + DB (mirrors upload API)."""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from typing import Dict, List, Set, Tuple

from sqlalchemy.orm import Session

from config.database import SessionLocal
from models.bill import Bill, BillCategory
from models.family import FamilyMember
from parsers.wechat_parser import WeChatParser


def get_family_user_ids(db: Session, user_id: int) -> List[int]:
    member = db.query(FamilyMember).filter(FamilyMember.user_id == user_id).first()
    if not member:
        return [user_id]
    members = db.query(FamilyMember).filter(FamilyMember.family_id == member.family_id).all()
    return [m.user_id for m in members]


def prefetch_wechat_pairs(db: Session, family_user_ids: List[int], records: List[dict]) -> Set[Tuple[datetime, str]]:
    import_ids: Set[str] = set()
    for record in records:
        tid = (record.get("raw_data") or {}).get("transaction_id")
        if tid is not None:
            tid_str = str(tid).strip()
            if tid_str and tid_str != "/":
                import_ids.add(tid_str)
    if not import_ids:
        return set()
    rows = (
        db.query(Bill.transaction_time, Bill.raw_data.op("->>")("transaction_id"))
        .filter(
            Bill.user_id.in_(family_user_ids),
            Bill.source_type == "wechat",
            Bill.raw_data.op("->>")("transaction_id").in_(list(import_ids)),
        )
        .all()
    )
    return {(row[0], str(row[1])) for row in rows}


def import_wechat_file(file_path: str, user_id: int, filename: str, auto_categorize: bool = True) -> Dict:
    parser = WeChatParser()
    parse_result = parser.parse_file(file_path)
    if parse_result.errors and not parse_result.success_records:
        raise RuntimeError("; ".join(parse_result.errors))

    db = SessionLocal()
    try:
        family_user_ids = get_family_user_ids(db, user_id)
        existing_pairs = prefetch_wechat_pairs(db, family_user_ids, parse_result.success_records)

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
                tx_time = record.get("transaction_time")
                tx_id = str((record.get("raw_data") or {}).get("transaction_id") or "").strip()
                if tx_id and tx_id != "/" and tx_time is not None:
                    if (tx_time, tx_id) in existing_pairs:
                        skipped += 1
                        continue

                bill = Bill(
                    user_id=user_id,
                    amount=record["amount"],
                    transaction_time=record["transaction_time"],
                    transaction_type=record["transaction_type"],
                    transaction_desc=record.get("transaction_desc", ""),
                    source_type="wechat",
                    source_filename=filename,
                    category_id=default_category.id if default_category else None,
                    currency=record.get("currency", "CNY"),
                    raw_data=record.get("raw_data", {}),
                )
                db.add(bill)
                created_bills.append(bill)
                if tx_id and tx_id != "/" and tx_time is not None:
                    existing_pairs.add((tx_time, tx_id))
            except Exception:
                failed += 1

        db.commit()
        for bill in created_bills:
            db.refresh(bill)

        ai_classified = 0
        if auto_categorize and created_bills:
            from services.ai_classification_service import ai_classification_service

            if ai_classification_service.is_available():
                bills_data = []
                for bill in created_bills:
                    bills_data.append(
                        {
                            "id": bill.id,
                            "amount": float(bill.amount),
                            "transaction_type": bill.transaction_type,
                            "description": bill.transaction_desc or "",
                            "source_type": bill.source_type,
                        }
                    )
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
    ap.add_argument("--user-id", type=int, default=9, help="Bill owner user id (default: mitre)")
    ap.add_argument("--no-ai", action="store_true")
    args = ap.parse_args()
    filename = os.path.basename(args.file_path)
    result = import_wechat_file(
        args.file_path,
        args.user_id,
        filename,
        auto_categorize=not args.no_ai,
    )
    print(result)
