#!/usr/bin/env python3
"""Scan tail payments still marked as 支出 and check refund matching."""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import SessionLocal
from models.bill import Bill
from models.family import FamilyMember
from parsers.refund_pairing import (
    _amount_value,
    _is_deposit_record,
    _is_payment_record,
    _is_refund_record,
    _is_round_deposit_amount,
    _records_match,
)


def get_family_user_ids(db, user_id: int) -> list[int]:
    member = db.query(FamilyMember).filter(FamilyMember.user_id == user_id).first()
    if not member:
        return [user_id]
    rows = db.query(FamilyMember).filter(FamilyMember.family_id == member.family_id).all()
    return [row.user_id for row in rows]


def _bill_record(bill: Bill) -> dict:
    return {
        "transaction_type": bill.transaction_type,
        "transaction_desc": bill.transaction_desc or "",
        "amount": bill.amount,
        "raw_data": bill.raw_data or {},
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--user-id", type=int, default=9)
    parser.add_argument("--source-type", default="alipay")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        user_ids = get_family_user_ids(db, args.user_id)
        bills = (
            db.query(Bill)
            .filter(Bill.user_id.in_(user_ids), Bill.source_type == args.source_type)
            .order_by(Bill.transaction_time.asc(), Bill.id.asc())
            .all()
        )

        payments = [b for b in bills if _is_payment_record(_bill_record(b))]
        refunds = [b for b in bills if _is_refund_record(_bill_record(b))]
        all_recs = [_bill_record(p) for p in payments]
        deposit_recs = [
            _bill_record(p)
            for p in payments
            if _amount_value(p.amount) and _is_round_deposit_amount(_amount_value(p.amount))
        ]

        tails_expense = []
        for payment in payments:
            record = _bill_record(payment)
            if not _is_deposit_record(record, all_recs) and payment.transaction_type == "支出":
                tails_expense.append(payment)

        print(f"tail payments still 支出: {len(tails_expense)}")
        for payment in tails_expense:
            pay_record = _bill_record(payment)
            matched = []
            for refund in refunds:
                refund_record = _bill_record(refund)
                if _records_match(pay_record, refund_record, deposit_recs):
                    matched.append(refund)
            desc = (payment.transaction_desc or "")[:70]
            print(f"id={payment.id} amt={payment.amount} desc={desc}")
            if matched:
                for refund in matched[:2]:
                    print(
                        f"  match refund id={refund.id} amt={refund.amount} "
                        f"type={refund.transaction_type}"
                    )
            else:
                print("  NO MATCH")

        deps_expense = [
            p
            for p in payments
            if _is_deposit_record(_bill_record(p), all_recs) and p.transaction_type == "支出"
        ]
        print(f"\ndeposits still 支出: {len(deps_expense)}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
