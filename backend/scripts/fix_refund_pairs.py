#!/usr/bin/env python3
"""将数据库中已导入的支付+退款配对账单都改为不计收支。"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from decimal import Decimal

from config.database import SessionLocal
from models.bill import Bill
from models.family import FamilyMember
from parsers.refund_pairing import _is_payment_record, _is_refund_record, _records_match


def get_family_user_ids(db, user_id: int) -> list[int]:
    member = db.query(FamilyMember).filter(FamilyMember.user_id == user_id).first()
    if not member:
        return [user_id]
    rows = db.query(FamilyMember).filter(FamilyMember.family_id == member.family_id).all()
    return [row.user_id for row in rows]


def fix_refund_pairs(db, user_ids: list[int], source_type: str, dry_run: bool = True) -> dict:
    bills = (
        db.query(Bill)
        .filter(Bill.user_id.in_(user_ids), Bill.source_type == source_type)
        .order_by(Bill.transaction_time.asc(), Bill.id.asc())
        .all()
    )

    payments = []
    refunds = []
    for bill in bills:
        record = {
            "transaction_type": bill.transaction_type,
            "transaction_desc": bill.transaction_desc or "",
            "amount": bill.amount,
            "raw_data": bill.raw_data or {},
        }
        if _is_payment_record(record):
            payments.append(bill)
        elif _is_refund_record(record):
            refunds.append(bill)

    updated_ids = []
    used_refunds = set()

    for payment in payments:
        pay_record = {
            "transaction_type": payment.transaction_type,
            "transaction_desc": payment.transaction_desc or "",
            "amount": payment.amount,
            "raw_data": payment.raw_data or {},
        }
        for refund in refunds:
            if refund.id in used_refunds:
                continue
            refund_record = {
                "transaction_type": refund.transaction_type,
                "transaction_desc": refund.transaction_desc or "",
                "amount": refund.amount,
                "raw_data": refund.raw_data or {},
            }
            if not _records_match(pay_record, refund_record):
                continue

            pair_info = f"[已配对] 支付退款对: {payment.transaction_desc}"
            for bill in (payment, refund):
                if bill.transaction_type != "不计收支":
                    updated_ids.append(bill.id)
                bill.transaction_type = "不计收支"
                if bill.remark:
                    if pair_info not in bill.remark:
                        bill.remark = f"{bill.remark}; {pair_info}"
                else:
                    bill.remark = pair_info
            used_refunds.add(refund.id)
            break

    if not dry_run and updated_ids:
        db.commit()

    return {
        "scanned": len(bills),
        "payments": len(payments),
        "refunds": len(refunds),
        "updated_ids": updated_ids,
        "dry_run": dry_run,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="修复已导入账单的支付退款配对")
    parser.add_argument("--user-id", type=int, default=9, help="家庭成员中任一用户 ID")
    parser.add_argument("--source-type", default="alipay", help="来源类型")
    parser.add_argument("--apply", action="store_true", help="写入数据库（默认仅预览）")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        user_ids = get_family_user_ids(db, args.user_id)
        result = fix_refund_pairs(db, user_ids, args.source_type, dry_run=not args.apply)
        print(result)
    finally:
        db.close()
