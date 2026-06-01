#!/usr/bin/env python3
"""为指定用户未分类账单补充分类（支付宝原始分类映射 + AI + 兜底）。"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, List, Optional

from config.database import SessionLocal
from models.bill import Bill, BillCategory
from services.ai_classification_service import ai_classification_service

# 支付宝导出「交易分类」→ 系统分类名
ALIPAY_CATEGORY_MAP = {
    "餐饮美食": "食品餐饮",
    "美容美发": "美妆个护",
    "医疗健康": "医疗保健",
    "家居家装": "日用百货",
    "数码电器": "日用百货",
    "文化休闲": "休闲玩乐",
    "服饰装扮": "服饰鞋包",
    "母婴亲子": "日用百货",
    "酒店旅游": "休闲玩乐",
    "充值缴费": "其他支出",
    "信用借还": "还款支出",
    "投资理财": "投资支出",
    "账户存取": "其他支出",
    "转账红包": "人情社交",
    "退款": "退款收入",
    "商业服务": "其他支出",
    "公共服务": "其他支出",
    "交通出行": "交通出行",
    "住房物业": "住房物业",
    "教育培训": "教育培训",
}


def load_categories(db) -> Dict[str, int]:
    rows = db.query(BillCategory).filter(BillCategory.is_deleted == False).all()
    return {row.category_name: row.id for row in rows}


def fallback_category_id(categories: Dict[str, int], transaction_type: str) -> Optional[int]:
    if transaction_type == "收入":
        return categories.get("其他收入") or categories.get("其他")
    if transaction_type == "支出":
        return categories.get("其他支出") or categories.get("其他")
    return categories.get("其他支出") or categories.get("其他")


def resolve_alipay_category(raw_data: dict, categories: Dict[str, int]) -> Optional[int]:
    if not raw_data:
        return None
    alipay_cat = raw_data.get("category")
    if not alipay_cat:
        return None
    if alipay_cat in categories:
        return categories[alipay_cat]
    mapped = ALIPAY_CATEGORY_MAP.get(alipay_cat)
    if mapped and mapped in categories:
        return categories[mapped]
    return None


def fix_uncategorized_bills(user_id: int, dry_run: bool = True, use_ai: bool = True) -> dict:
    db = SessionLocal()
    try:
        categories = load_categories(db)
        bills = (
            db.query(Bill)
            .filter(Bill.user_id == user_id, Bill.category_id.is_(None))
            .order_by(Bill.id.asc())
            .all()
        )

        mapped_count = 0
        ai_count = 0
        fallback_count = 0
        still_missing = 0
        ai_pending: List[Bill] = []

        for bill in bills:
            category_id = resolve_alipay_category(bill.raw_data or {}, categories)
            if category_id:
                if not dry_run:
                    bill.category_id = category_id
                mapped_count += 1
                continue
            ai_pending.append(bill)

        if use_ai and ai_pending and ai_classification_service.is_available():
            bills_data = [
                {
                    "id": bill.id,
                    "amount": float(bill.amount),
                    "transaction_type": bill.transaction_type,
                    "description": bill.transaction_desc or "",
                    "source_type": bill.source_type,
                }
                for bill in ai_pending
            ]
            results = ai_classification_service.classify_bills_batch_optimized(
                bills_data, db, user_id, batch_size=20
            )
            result_by_id = {bill_id: category_name for bill_id, category_name in results}
            remaining: List[Bill] = []
            for bill in ai_pending:
                category_name = result_by_id.get(bill.id)
                category_id = categories.get(category_name) if category_name else None
                if category_id:
                    if not dry_run:
                        bill.category_id = category_id
                    ai_count += 1
                else:
                    remaining.append(bill)
            ai_pending = remaining

        for bill in ai_pending:
            category_id = fallback_category_id(categories, bill.transaction_type or "")
            if category_id:
                if not dry_run:
                    bill.category_id = category_id
                fallback_count += 1
            else:
                still_missing += 1

        if not dry_run:
            db.commit()

        return {
            "user_id": user_id,
            "total_uncategorized": len(bills),
            "mapped_from_alipay": mapped_count,
            "classified_by_ai": ai_count,
            "fallback_assigned": fallback_count,
            "still_missing": still_missing,
            "dry_run": dry_run,
        }
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="补全未分类账单")
    parser.add_argument("--user-id", type=int, default=2, help="用户 ID（默认 josie）")
    parser.add_argument("--apply", action="store_true", help="写入数据库")
    parser.add_argument("--no-ai", action="store_true", help="跳过 AI，仅用映射与兜底")
    args = parser.parse_args()
    result = fix_uncategorized_bills(args.user_id, dry_run=not args.apply, use_ai=not args.no_ai)
    print(result)
