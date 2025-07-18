#!/usr/bin/env python3
"""
验证招商银行PDF账单重复导入修复效果的脚本
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from config.database import get_db
from models.bill import Bill
from sqlalchemy import func
from collections import defaultdict

def verify_cmb_duplicate_fix():
    """验证招商银行账单重复导入修复效果"""
    
    print("=== 招商银行账单重复导入修复验证 ===")
    
    db = next(get_db())
    try:
        # 查询所有招商银行账单
        cmb_bills = db.query(Bill).filter(Bill.source_type == 'cmb').all()
        
        print(f"数据库中招商银行账单总数: {len(cmb_bills)}")
        
        if len(cmb_bills) == 0:
            print("❌ 数据库中没有招商银行账单记录")
            return
        
        # 按日期分组统计
        date_groups = defaultdict(list)
        for bill in cmb_bills:
            date_key = bill.transaction_time.date()
            date_groups[date_key].append(bill)
        
        print(f"涉及的交易日期数: {len(date_groups)}")
        
        # 显示每个日期的记录数
        print("\n--- 各日期记录数统计 ---")
        total_expected = 0
        for date_key in sorted(date_groups.keys()):
            bills_on_date = date_groups[date_key]
            print(f"{date_key}: {len(bills_on_date)} 条记录")
            total_expected += len(bills_on_date)
        
        print(f"\n预期总记录数: {total_expected}")
        print(f"实际总记录数: {len(cmb_bills)}")
        
        if total_expected == len(cmb_bills):
            print("✅ 记录数统计正确")
        else:
            print("❌ 记录数统计不匹配")
        
        # 检查是否有重复记录（相同时间、金额、描述）
        print("\n--- 重复记录检查 ---")
        record_signatures = defaultdict(list)
        
        for bill in cmb_bills:
            signature = (
                bill.transaction_time,
                bill.amount,
                bill.transaction_desc or "",
                bill.counter_party or ""
            )
            record_signatures[signature].append(bill.id)
        
        duplicate_count = 0
        for signature, bill_ids in record_signatures.items():
            if len(bill_ids) > 1:
                duplicate_count += 1
                print(f"发现重复记录: {signature[0]} | {signature[1]} | {signature[2][:30]}... | 记录ID: {bill_ids}")
        
        if duplicate_count == 0:
            print("✅ 没有发现重复记录")
        else:
            print(f"❌ 发现 {duplicate_count} 组重复记录")
        
        # 检查最新的记录ID范围
        print("\n--- 记录ID范围检查 ---")
        bill_ids = [bill.id for bill in cmb_bills]
        min_id = min(bill_ids)
        max_id = max(bill_ids)
        print(f"记录ID范围: {min_id} - {max_id}")
        
        # 检查ID是否连续（应该是连续的，因为是最后一次导入的）
        expected_ids = set(range(max_id - len(cmb_bills) + 1, max_id + 1))
        actual_ids = set(bill_ids)
        
        if expected_ids == actual_ids:
            print("✅ 记录ID连续，说明是最后一次导入的结果")
        else:
            print("ℹ️ 记录ID不完全连续，可能包含多次导入的结果")
            missing_ids = expected_ids - actual_ids
            extra_ids = actual_ids - expected_ids
            if missing_ids:
                print(f"  缺失的ID: {sorted(missing_ids)[:10]}{'...' if len(missing_ids) > 10 else ''}")
            if extra_ids:
                print(f"  额外的ID: {sorted(extra_ids)[:10]}{'...' if len(extra_ids) > 10 else ''}")
        
        print("\n=== 验证结果 ===")
        if len(cmb_bills) == 63 and duplicate_count == 0:
            print("✅ 招商银行账单重复导入修复成功！")
            print("  - 总记录数正确 (63条)")
            print("  - 没有重复记录")
            print("  - 重复导入时正确替换了旧数据")
        else:
            print("❌ 修复可能存在问题")
            if len(cmb_bills) != 63:
                print(f"  - 记录数不正确: 期望63条，实际{len(cmb_bills)}条")
            if duplicate_count > 0:
                print(f"  - 存在重复记录: {duplicate_count}组")
        
    except Exception as e:
        print(f"验证过程中出错: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    verify_cmb_duplicate_fix()