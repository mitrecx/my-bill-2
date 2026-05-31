"""支付/退款配对：将已全额退款的买卖两条都标记为不计收支。"""

from __future__ import annotations

import logging
import re
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


def _amount_value(amount: Any) -> Optional[Decimal]:
    if amount is None:
        return None
    if isinstance(amount, Decimal):
        return abs(amount)
    try:
        return abs(Decimal(str(amount).strip()))
    except Exception:
        return None


def _merchant(desc: str) -> str:
    if not desc:
        return ""
    return desc.split(" - ", 1)[0].strip()


def _product_key(desc: str) -> str:
    if not desc:
        return ""
    tail = desc.split(" - ", 1)[1].strip() if " - " in desc else desc.strip()
    tail = re.sub(r"^退款\s*[-–—]?\s*", "", tail)
    return tail.strip()


def _is_refund_record(record: Dict[str, Any]) -> bool:
    desc = str(record.get("transaction_desc") or "")
    tx_type = str(record.get("transaction_type") or "")
    raw = record.get("raw_data") or {}
    category = str(raw.get("category") or raw.get("transaction_category") or "")

    if "退款" in desc or "退款" in category:
        return True
    if tx_type in ("不计收支", "transfer") and "退款" in desc:
        return True
    return False


def _is_payment_record(record: Dict[str, Any]) -> bool:
    tx_type = str(record.get("transaction_type") or "")
    return tx_type in ("支出", "expense")


def _records_match(payment: Dict[str, Any], refund: Dict[str, Any]) -> bool:
    pay_amount = _amount_value(payment.get("amount"))
    refund_amount = _amount_value(refund.get("amount"))
    if pay_amount is None or refund_amount is None or pay_amount != refund_amount:
        return False

    pay_desc = str(payment.get("transaction_desc") or "")
    refund_desc = str(refund.get("transaction_desc") or "")
    if not pay_desc or not refund_desc:
        return False

    pay_merchant = _merchant(pay_desc)
    refund_merchant = _merchant(refund_desc)
    if not pay_merchant or pay_merchant != refund_merchant:
        return False

    pay_product = _product_key(pay_desc)
    refund_product = _product_key(refund_desc)
    if not pay_product or not refund_product:
        return pay_merchant and pay_merchant in refund_desc

    return pay_product in refund_product or refund_product in pay_product


def pair_payment_refund_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """配对支付与退款，将匹配的两条都改为不计收支。"""
    paired_records: List[Dict[str, Any]] = []
    processed_indices: set[int] = set()

    payment_records: List[Tuple[int, Dict[str, Any]]] = []
    refund_records: List[Tuple[int, Dict[str, Any]]] = []

    for index, record in enumerate(records):
        if _is_payment_record(record):
            payment_records.append((index, record))
        elif _is_refund_record(record):
            refund_records.append((index, record))

    logger.info("支付退款配对: %d 笔支出, %d 笔退款", len(payment_records), len(refund_records))

    for payment_idx, payment_record in payment_records:
        if payment_idx in processed_indices:
            continue

        for refund_idx, refund_record in refund_records:
            if refund_idx in processed_indices:
                continue
            if not _records_match(payment_record, refund_record):
                continue

            pay_desc = payment_record.get("transaction_desc", "")
            pair_info = f"[已配对] 支付退款对: {pay_desc}"

            payment_copy = payment_record.copy()
            payment_copy["transaction_type"] = "不计收支"
            payment_copy["income_expense"] = "不计收支"

            refund_copy = refund_record.copy()
            refund_copy["transaction_type"] = "不计收支"
            refund_copy["income_expense"] = "不计收支"

            if payment_copy.get("remark"):
                payment_copy["remark"] = f"{payment_copy['remark']}; {pair_info}"
            else:
                payment_copy["remark"] = pair_info

            if refund_copy.get("remark"):
                refund_copy["remark"] = f"{refund_copy['remark']}; {pair_info}"
            else:
                refund_copy["remark"] = pair_info

            logger.info("配对成功: %s, 金额: %s", pay_desc, payment_record.get("amount"))
            paired_records.append(payment_copy)
            paired_records.append(refund_copy)
            processed_indices.add(payment_idx)
            processed_indices.add(refund_idx)
            break

    for index, record in enumerate(records):
        if index not in processed_indices:
            paired_records.append(record)

    logger.info(
        "支付退款配对完成: 共 %d 条, 其中 %d 条参与配对",
        len(paired_records),
        len(processed_indices),
    )
    return paired_records
