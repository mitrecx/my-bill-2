#!/usr/bin/env python3
"""将数据库中已导入的支付+退款配对账单都改为不计收支。"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import SessionLocal
from models.bill import Bill
from models.family import FamilyMember
from parsers.refund_pairing import (
    _amount_value,
    _deposit_products_related,
    _is_deposit_record,
    _is_payment_record,
    _is_refund_record,
    _is_round_deposit_amount,
    _merchant,
    _product_key,
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


def _find_matching_deposits(payment: Bill, deposit_bills: list[Bill]) -> list[Bill]:
    pay_record = _bill_record(payment)
    pay_amount = _amount_value(payment.amount)
    if pay_amount is None:
        return []

    pay_desc = payment.transaction_desc or ""
    pay_product = _product_key(pay_desc)
    matches = []

    for candidate in deposit_bills:
        if candidate.id == payment.id:
            continue
        dep_amount = _amount_value(candidate.amount)
        if dep_amount is None or dep_amount >= pay_amount:
            continue
        if not _is_round_deposit_amount(dep_amount):
            continue
        dep_desc = candidate.transaction_desc or ""
        dep_product = _product_key(dep_desc)
        if not _deposit_products_related(
            _merchant(pay_desc),
            pay_product,
            pay_desc,
            _merchant(dep_desc),
            dep_product,
            dep_desc,
        ):
            continue
        matches.append(candidate)

    return matches


def _is_tail_payment(bill: Bill, payments: list[Bill]) -> bool:
    record = _bill_record(bill)
    all_records = [_bill_record(p) for p in payments]
    return _is_payment_record(record) and not _is_deposit_record(record, all_records)


def fix_refund_pairs(db, user_ids: list[int], source_type: str, dry_run: bool = True) -> dict:
    bills = (
        db.query(Bill)
        .filter(Bill.user_id.in_(user_ids), Bill.source_type == source_type)
        .order_by(Bill.transaction_time.asc(), Bill.id.asc())
        .all()
    )

    payments = []
    refunds = []
    deposit_bills = []
    for bill in bills:
        record = _bill_record(bill)
        if _is_refund_record(record):
            refunds.append(bill)
            continue
        amount = _amount_value(bill.amount)
        if amount is not None and _is_round_deposit_amount(amount):
            deposit_bills.append(bill)
        if _is_payment_record(record):
            payments.append(bill)

    deposit_records = [_bill_record(b) for b in deposit_bills]
    updated_ids = []
    updated_pairs = []
    used_refunds = set()
    used_deposits = set()

    tail_payments = [p for p in payments if _is_tail_payment(p, payments)]

    for payment in tail_payments:
        pay_record = _bill_record(payment)
        matching_deposits = _find_matching_deposits(payment, deposit_bills)

        for refund in refunds:
            if refund.id in used_refunds:
                continue
            refund_record = _bill_record(refund)
            if not _records_match(pay_record, refund_record, deposit_records):
                continue

            matched_deposit = None
            pay_amount = _amount_value(payment.amount)
            refund_amount = _amount_value(refund.amount)
            if pay_amount != refund_amount:
                for dep in matching_deposits:
                    if dep.id in used_deposits:
                        continue
                    dep_amount = _amount_value(dep.amount)
                    if dep_amount and pay_amount + dep_amount == refund_amount:
                        matched_deposit = dep
                        break

            pair_info = f"[已配对] 支付退款对: {payment.transaction_desc}"
            if matched_deposit:
                pair_info += f"（含定金 {matched_deposit.amount}）"

            for bill in (payment, refund):
                if bill.transaction_type != "不计收支":
                    updated_ids.append(bill.id)
                bill.transaction_type = "不计收支"
                if bill.remark:
                    if pair_info not in (bill.remark or ""):
                        bill.remark = f"{bill.remark}; {pair_info}"
                else:
                    bill.remark = pair_info

            if matched_deposit:
                if matched_deposit.transaction_type != "不计收支":
                    updated_ids.append(matched_deposit.id)
                matched_deposit.transaction_type = "不计收支"
                if matched_deposit.remark:
                    if pair_info not in (matched_deposit.remark or ""):
                        matched_deposit.remark = f"{matched_deposit.remark}; {pair_info}"
                else:
                    matched_deposit.remark = pair_info
                used_deposits.add(matched_deposit.id)

            used_refunds.add(refund.id)
            updated_pairs.append({
                "match_type": "deposit+tail" if matched_deposit or pay_amount != refund_amount else "exact",
                "tail_id": payment.id,
                "tail_amount": float(payment.amount),
                "tail_desc": payment.transaction_desc,
                "refund_id": refund.id,
                "refund_amount": float(refund.amount),
                "deposit_id": matched_deposit.id if matched_deposit else None,
                "deposit_amount": float(matched_deposit.amount) if matched_deposit else None,
            })
            break

    if not dry_run and updated_ids:
        db.commit()

    return {
        "scanned": len(bills),
        "payments": len(payments),
        "tail_payments": len(tail_payments),
        "refunds": len(refunds),
        "updated_ids": sorted(set(updated_ids)),
        "updated_pairs": updated_pairs,
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
        import json
        print(json.dumps(result, ensure_ascii=False, indent=2))
    finally:
        db.close()
