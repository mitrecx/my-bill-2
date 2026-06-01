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
    tail = re.sub(r"^付定金\s*", "", tail)
    return tail.strip()


def _is_payment_record(record: Dict[str, Any]) -> bool:
    tx_type = str(record.get("transaction_type") or "")
    return tx_type in ("支出", "expense")


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


def _product_matches(pay_product: str, other_product: str, pay_desc: str, other_desc: str) -> bool:
    if pay_product and other_product:
        if pay_product in other_product or other_product in pay_product:
            return True
        normalized_pay = pay_product.replace("蓆下", "蕉下")
        normalized_other = other_product.replace("蓆下", "蕉下")
        if normalized_pay in normalized_other or normalized_other in normalized_pay:
            return True
    if pay_desc and other_desc:
        if pay_desc in other_desc or other_desc in pay_desc:
            return True
        norm_pay = pay_desc.replace("蓆下", "蕉下")
        norm_other = other_desc.replace("蓆下", "蕉下")
        if norm_pay in norm_other or norm_other in norm_pay:
            return True
    return False


_PRESALE_PREFIX_RE = re.compile(r"^【.*?付定金】")


def _meaningful_product(desc: str) -> str:
    product = _product_key(desc)
    return _PRESALE_PREFIX_RE.sub("", product).strip()


def _shared_product_prefix_len(left: str, right: str) -> int:
    limit = min(len(left), len(right))
    index = 0
    while index < limit and left[index] == right[index]:
        index += 1
    return index


def _deposit_products_related(
    pay_merchant: str,
    pay_product: str,
    pay_desc: str,
    other_merchant: str,
    other_product: str,
    other_desc: str,
    min_prefix: int = 6,
) -> bool:
    if not _merchant_matches(pay_merchant, other_merchant):
        return False
    if _product_matches(pay_product, other_product, pay_desc, other_desc):
        return True

    meaningful_pairs = (
        (_meaningful_product(pay_desc), _meaningful_product(other_desc)),
        (pay_product, other_product),
    )
    for left, right in meaningful_pairs:
        if left and right and _shared_product_prefix_len(left, right) >= min_prefix:
            return True
    return False


def _products_related(
    pay_product: str,
    other_product: str,
    pay_desc: str,
    other_desc: str,
    min_prefix: int = 12,
) -> bool:
    """同一订单定金/尾款/退款描述常有细微差异（如 SKU 后缀）。"""
    if _product_matches(pay_product, other_product, pay_desc, other_desc):
        return True

    pairs = (
        (pay_product, other_product),
        (pay_desc, other_desc),
        (pay_product, other_desc),
        (pay_desc, other_product),
    )
    for left, right in pairs:
        if left and right and _shared_product_prefix_len(left, right) >= min_prefix:
            return True
    return False


def _merchant_matches(pay_merchant: str, other_merchant: str) -> bool:
    if not pay_merchant or not other_merchant:
        return False
    if pay_merchant == other_merchant:
        return True
    if pay_merchant.endswith("**店") and other_merchant.endswith("**店"):
        pay_prefix = pay_merchant[:-3]
        other_prefix = other_merchant[:-3]
        if not pay_prefix or not other_prefix:
            return False
        return _shared_product_prefix_len(pay_prefix, other_prefix) >= 2
    return False


def _is_round_deposit_amount(amount: Decimal) -> bool:
    return amount <= 50 and amount == amount.to_integral_value()


def _is_deposit_record(record: Dict[str, Any], all_payments: List[Dict[str, Any]]) -> bool:
    """同一商品存在更大金额尾款时，较小且为整数金额的视为定金（如 20 元定金）。"""
    if not _is_payment_record(record):
        return False
    amount = _amount_value(record.get("amount"))
    if amount is None or not _is_round_deposit_amount(amount):
        return False
    desc = str(record.get("transaction_desc") or "")
    product = _product_key(desc)
    pay_merchant = _merchant(desc)
    for other in all_payments:
        if other is record:
            continue
        other_amount = _amount_value(other.get("amount"))
        if other_amount is None or other_amount <= amount:
            continue
        other_desc = str(other.get("transaction_desc") or "")
        other_product = _product_key(other_desc)
        if _deposit_products_related(
            pay_merchant, product, desc, _merchant(other_desc), other_product, other_desc
        ):
            return True
    return False


def _records_match(
    payment: Dict[str, Any],
    refund: Dict[str, Any],
    deposits: Optional[List[Dict[str, Any]]] = None,
) -> bool:
    pay_amount = _amount_value(payment.get("amount"))
    refund_amount = _amount_value(refund.get("amount"))
    if pay_amount is None or refund_amount is None:
        return False

    pay_desc = str(payment.get("transaction_desc") or "")
    refund_desc = str(refund.get("transaction_desc") or "")
    if not pay_desc or not refund_desc:
        return False

    pay_merchant = _merchant(pay_desc)
    refund_merchant = _merchant(refund_desc)
    if not _merchant_matches(pay_merchant, refund_merchant):
        return False

    pay_product = _product_key(pay_desc)
    refund_product = _product_key(refund_desc)
    if not _product_matches(pay_product, refund_product, pay_desc, refund_desc):
        return False

    if pay_amount == refund_amount:
        return True

    if not deposits:
        return False

    pay_product_norm = pay_product or pay_desc
    for deposit in deposits:
        dep_amount = _amount_value(deposit.get("amount"))
        if dep_amount is None:
            continue
        dep_desc = str(deposit.get("transaction_desc") or "")
        dep_product = _product_key(dep_desc)
        dep_merchant = _merchant(dep_desc)
        if not _merchant_matches(pay_merchant, dep_merchant):
            continue
        if not (
            _deposit_products_related(
                pay_merchant, pay_product_norm, pay_desc, dep_merchant, dep_product, dep_desc
            )
            or _deposit_products_related(
                refund_merchant, refund_product, refund_desc, dep_merchant, dep_product, dep_desc
            )
        ):
            continue
        if pay_amount + dep_amount == refund_amount:
            return True

    return False


def pair_payment_refund_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """配对支付与退款，将匹配的两条都改为不计收支。"""
    paired_records: List[Dict[str, Any]] = []
    processed_indices: set[int] = set()
    used_deposits: set[int] = set()

    all_payments = [r for r in records if _is_payment_record(r)]
    payment_records: List[Tuple[int, Dict[str, Any]]] = []
    refund_records: List[Tuple[int, Dict[str, Any]]] = []
    deposit_records = [r for r in all_payments if _is_deposit_record(r, all_payments)]

    for index, record in enumerate(records):
        if _is_payment_record(record) and not _is_deposit_record(record, all_payments):
            payment_records.append((index, record))
        elif _is_refund_record(record):
            refund_records.append((index, record))

    logger.info(
        "支付退款配对: %d 笔尾款/支出, %d 笔退款, %d 笔定金",
        len(payment_records),
        len(refund_records),
        len(deposit_records),
    )

    for payment_idx, payment_record in payment_records:
        if payment_idx in processed_indices:
            continue

        for refund_idx, refund_record in refund_records:
            if refund_idx in processed_indices:
                continue
            if not _records_match(payment_record, refund_record, deposit_records):
                continue

            pay_desc = payment_record.get("transaction_desc", "")
            pay_amount = _amount_value(payment_record.get("amount"))
            refund_amount = _amount_value(refund_record.get("amount"))
            pair_info = f"[已配对] 支付退款对: {pay_desc}"

            matched_deposit_idx = None
            if pay_amount != refund_amount:
                pay_product_norm = _product_key(pay_desc) or pay_desc
                for dep_idx, deposit in enumerate(deposit_records):
                    if dep_idx in used_deposits:
                        continue
                    dep_amount = _amount_value(deposit.get("amount"))
                    if dep_amount is None or pay_amount is None:
                        continue
                    if pay_amount + dep_amount != refund_amount:
                        continue
                    dep_desc = str(deposit.get("transaction_desc") or "")
                    dep_product = _product_key(dep_desc)
                    refund_desc = str(refund_record.get("transaction_desc") or "")
                    refund_product = _product_key(refund_desc)
                    dep_merchant = _merchant(dep_desc)
                    pay_merchant = _merchant(pay_desc)
                    refund_merchant = _merchant(refund_desc)
                    if not (
                        _deposit_products_related(
                            pay_merchant, pay_product_norm, pay_desc, dep_merchant, dep_product, dep_desc
                        )
                        or _deposit_products_related(
                            refund_merchant, refund_product, refund_desc, dep_merchant, dep_product, dep_desc
                        )
                    ):
                        continue
                    matched_deposit_idx = dep_idx
                    pair_info += f"（含定金 {dep_amount}）"
                    break

            payment_copy = payment_record.copy()
            payment_copy["transaction_type"] = "不计收支"
            payment_copy["income_expense"] = "不计收支"
            if payment_copy.get("remark"):
                payment_copy["remark"] = f"{payment_copy['remark']}; {pair_info}"
            else:
                payment_copy["remark"] = pair_info

            refund_copy = refund_record.copy()
            refund_copy["transaction_type"] = "不计收支"
            refund_copy["income_expense"] = "不计收支"
            if refund_copy.get("remark"):
                refund_copy["remark"] = f"{refund_copy['remark']}; {pair_info}"
            else:
                refund_copy["remark"] = pair_info

            paired_records.append(payment_copy)
            paired_records.append(refund_copy)
            processed_indices.add(payment_idx)
            processed_indices.add(refund_idx)

            if matched_deposit_idx is not None:
                used_deposits.add(matched_deposit_idx)
                deposit = deposit_records[matched_deposit_idx]
                for index, record in enumerate(records):
                    if record is deposit:
                        deposit_copy = deposit.copy()
                        deposit_copy["transaction_type"] = "不计收支"
                        deposit_copy["income_expense"] = "不计收支"
                        if deposit_copy.get("remark"):
                            deposit_copy["remark"] = f"{deposit_copy['remark']}; {pair_info}"
                        else:
                            deposit_copy["remark"] = pair_info
                        paired_records.append(deposit_copy)
                        processed_indices.add(index)
                        break

            logger.info("配对成功: %s, 金额: %s", pay_desc, payment_record.get("amount"))
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
