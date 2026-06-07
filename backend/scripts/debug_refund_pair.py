#!/usr/bin/env python3
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import SessionLocal
from models.bill import Bill
from parsers.refund_pairing import (
    _amount_value,
    _is_payment_record,
    _is_refund_record,
    _merchant,
    _merchant_matches,
    _product_key,
    _product_matches,
    _records_match,
)


def rec(bill: Bill) -> dict:
    desc = bill.transaction_desc or ""
    return {
        "transaction_type": bill.transaction_type,
        "transaction_desc": desc,
        "amount": bill.amount,
        "raw_data": bill.raw_data or {},
    }


def main():
    db = SessionLocal()
    try:
        ids = [6524, 6583, 6512, 6526, 6579, 6513, 6525, 6527, 6574, 6578]
        bills = {b.id: b for b in db.query(Bill).filter(Bill.id.in_(ids)).all()}
        for bill_id in ids:
            bill = bills.get(bill_id)
            if bill:
                desc = bill.transaction_desc or ""
                print(
                    f"{bill_id}: type={bill.transaction_type} amt={bill.amount} "
                    f"desc={desc}"
                )
                print(
                    f"   merchant={_merchant(desc)} product={_product_key(desc)}"
                )
            else:
                print(f"{bill_id}: NOT FOUND")

        pay = rec(bills[6524])
        refund = rec(bills[6512])
        deposit = rec(bills[6583])
        print("\n6524 vs 6512 match:", _records_match(pay, refund, [deposit]))
        print(
            "amounts:",
            _amount_value(pay["amount"]),
            _amount_value(refund["amount"]),
            _amount_value(bills[6583].amount),
        )
        print(
            "merchant match:",
            _merchant_matches(
                _merchant(pay["transaction_desc"]),
                _merchant(refund["transaction_desc"]),
            ),
        )
        print(
            "product match:",
            _product_matches(
                _product_key(pay["transaction_desc"]),
                _product_key(refund["transaction_desc"]),
                pay["transaction_desc"],
                refund["transaction_desc"],
            ),
        )
        print("is refund 6512:", _is_refund_record(refund))
        print("is payment 6524:", _is_payment_record(pay))

        print("\nAll bills around 6508-6520:")
        for bill in db.query(Bill).filter(Bill.id.between(6508, 6520)).all():
            record = rec(bill)
            desc = bill.transaction_desc or ""
            print(
                f"  {bill.id} type={bill.transaction_type} "
                f"refund={_is_refund_record(record)} amt={bill.amount} "
                f"desc={desc[:80]}"
            )
    finally:
        db.close()


if __name__ == "__main__":
    main()
