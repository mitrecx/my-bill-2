#!/usr/bin/env python3
"""
验证招商银行PDF修复效果
检查之前被误判为重复的记录是否都正确导入了
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from config.database import get_db
from models.bill import Bill
from datetime import datetime

def verify_cmb_fix():
    """验证招商银行PDF修复效果"""
    
    print("=== 验证招商银行PDF修复效果 ===\n")
    
    db = next(get_db())
    
    try:
        # 查询所有招商银行记录
        cmb_bills = db.query(Bill).filter(Bill.source_type == 'cmb').all()
        print(f"数据库中招商银行账单总数: {len(cmb_bills)}")
        
        # 检查之前被误判为重复的记录
        print("\n=== 检查之前被误判为重复的记录 ===")
        
        # 1. 检查2025-01-10的"银联渠道转入"100.00元记录
        jan10_transfer = db.query(Bill).filter(
            Bill.source_type == 'cmb',
            Bill.transaction_time >= datetime(2025, 1, 10),
            Bill.transaction_time < datetime(2025, 1, 11),
            Bill.amount == 100.00,
            Bill.transaction_desc == '银联渠道转入'
        ).all()
        
        print(f"\n1. 2025-01-10 银联渠道转入 100.00元 记录数: {len(jan10_transfer)}")
        for i, bill in enumerate(jan10_transfer, 1):
            print(f"   记录{i}: 对手方={bill.counter_party}, ID={bill.id}")
        
        # 2. 检查2025-01-10的"基金申购"100.00元记录
        jan10_fund = db.query(Bill).filter(
            Bill.source_type == 'cmb',
            Bill.transaction_time >= datetime(2025, 1, 10),
            Bill.transaction_time < datetime(2025, 1, 11),
            Bill.amount == 100.00,
            Bill.transaction_desc == '基金申购'
        ).all()
        
        print(f"\n2. 2025-01-10 基金申购 100.00元 记录数: {len(jan10_fund)}")
        for i, bill in enumerate(jan10_fund, 1):
            print(f"   记录{i}: 对手方={bill.counter_party}, ID={bill.id}")
        
        # 3. 检查2025-04-07的"基金申购"50.00元记录
        apr07_fund = db.query(Bill).filter(
            Bill.source_type == 'cmb',
            Bill.transaction_time >= datetime(2025, 4, 7),
            Bill.transaction_time < datetime(2025, 4, 8),
            Bill.amount == 50.00,
            Bill.transaction_desc == '基金申购'
        ).all()
        
        print(f"\n3. 2025-04-07 基金申购 50.00元 记录数: {len(apr07_fund)}")
        for i, bill in enumerate(apr07_fund, 1):
            print(f"   记录{i}: 对手方={bill.counter_party}, ID={bill.id}")
        
        # 统计结果
        expected_duplicates = len(jan10_transfer) + len(jan10_fund) + len(apr07_fund)
        print(f"\n=== 修复效果总结 ===")
        print(f"之前被误判为重复的记录总数: {expected_duplicates}")
        print(f"预期应该有: 6条记录 (2+2+2)")
        
        if expected_duplicates == 6:
            print("✅ 修复成功！所有之前被误判为重复的记录都已正确导入")
        else:
            print(f"❌ 修复不完整，还有 {6 - expected_duplicates} 条记录缺失")
            
        # 验证总记录数
        print(f"\n总记录数验证:")
        print(f"  数据库中记录数: {len(cmb_bills)}")
        print(f"  预期记录数: 63")
        
        if len(cmb_bills) == 63:
            print("✅ 总记录数正确")
        else:
            print(f"❌ 总记录数不正确，差异: {63 - len(cmb_bills)}")
            
    except Exception as e:
        print(f"验证失败: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    verify_cmb_fix()