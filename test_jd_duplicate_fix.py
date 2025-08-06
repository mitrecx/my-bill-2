#!/usr/bin/env python3
"""
测试修复后的京东账单重复检查逻辑
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from datetime import datetime, timedelta
from config.database import SessionLocal
from models.bill import Bill
from parsers.jd_parser import JDParser

def test_jd_duplicate_logic():
    """测试京东账单重复检查逻辑"""
    
    print("=== 测试京东账单重复检查逻辑修复 ===\n")
    
    # 1. 解析京东账单文件
    print("1. 解析京东账单文件...")
    parser = JDParser()
    file_path = "/Users/chenxing/projects/my-bills-2/bills/京东交易流水(申请时间2025年07月05日10时04分27秒)_739.csv"
    
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return
    
    result = parser.parse_file(file_path)
    print(f"   解析成功记录: {len(result.success_records)}")
    
    # 2. 分析重复的order_id
    print("\n2. 分析重复的order_id...")
    order_id_count = {}
    for record in result.success_records:
        order_id = record.get("raw_data", {}).get("order_id")
        if order_id:
            order_id_count[order_id] = order_id_count.get(order_id, 0) + 1
    
    duplicate_order_ids = {oid: count for oid, count in order_id_count.items() if count > 1}
    print(f"   重复的order_id数量: {len(duplicate_order_ids)}")
    
    for order_id, count in duplicate_order_ids.items():
        print(f"   - {order_id}: {count}次")
        
        # 显示这些重复记录的详情
        duplicate_records = [r for r in result.success_records 
                           if r.get("raw_data", {}).get("order_id") == order_id]
        
        for i, record in enumerate(duplicate_records):
            print(f"     记录{i+1}: {record['transaction_time']} | {record['amount']} | {record['transaction_desc'][:50]}...")
    
    # 3. 模拟新的重复检查逻辑
    print("\n3. 模拟新的重复检查逻辑...")
    
    # 模拟find_existing_jd_bill函数的新逻辑
    def simulate_new_duplicate_check(records):
        """模拟新的重复检查逻辑"""
        seen_records = []
        duplicates_found = 0
        
        for record in records:
            is_duplicate = False
            
            raw_data = record.get("raw_data", {})
            order_id = raw_data.get("order_id")
            transaction_time = record.get("transaction_time")
            amount = record.get("amount")
            transaction_desc = record.get("transaction_desc", "")
            
            # 策略1: order_id + transaction_time + amount
            if order_id and transaction_time and amount is not None:
                for seen in seen_records:
                    seen_raw = seen.get("raw_data", {})
                    if (seen_raw.get("order_id") == order_id and
                        seen.get("transaction_time") == transaction_time and
                        seen.get("amount") == amount):
                        is_duplicate = True
                        duplicates_found += 1
                        print(f"   发现重复（策略1）: {order_id} | {transaction_time} | {amount}")
                        break
            
            # 策略2: transaction_time + amount + transaction_desc (时间容差1分钟)
            if not is_duplicate and transaction_time and amount is not None and transaction_desc:
                for seen in seen_records:
                    seen_time = seen.get("transaction_time")
                    if seen_time:
                        time_diff = abs((transaction_time - seen_time).total_seconds())
                        if (time_diff <= 60 and  # 1分钟容差
                            seen.get("amount") == amount and
                            seen.get("transaction_desc") == transaction_desc):
                            is_duplicate = True
                            duplicates_found += 1
                            print(f"   发现重复（策略2）: {transaction_time} | {amount} | {transaction_desc[:30]}...")
                            break
            
            if not is_duplicate:
                seen_records.append(record)
        
        return len(seen_records), duplicates_found
    
    unique_count, duplicate_count = simulate_new_duplicate_check(result.success_records)
    
    print(f"\n   原始记录数: {len(result.success_records)}")
    print(f"   去重后记录数: {unique_count}")
    print(f"   重复记录数: {duplicate_count}")
    
    # 4. 检查数据库当前状态
    print("\n4. 检查数据库当前状态...")
    db = SessionLocal()
    try:
        jd_bills = db.query(Bill).filter(Bill.source_type == "jd").all()
        print(f"   数据库中京东账单数: {len(jd_bills)}")
        
        # 检查是否有重复的order_id
        db_order_ids = {}
        for bill in jd_bills:
            order_id = bill.raw_data.get("order_id") if bill.raw_data else None
            if order_id:
                db_order_ids[order_id] = db_order_ids.get(order_id, 0) + 1
        
        db_duplicates = {oid: count for oid, count in db_order_ids.items() if count > 1}
        print(f"   数据库中重复order_id数: {len(db_duplicates)}")
        
        if db_duplicates:
            print("   数据库中的重复order_id:")
            for order_id, count in db_duplicates.items():
                print(f"   - {order_id}: {count}次")
    
    finally:
        db.close()
    
    print("\n=== 测试完成 ===")
    print(f"预期结果: 修复后应该能保存所有 {len(result.success_records)} 条记录")
    print("建议: 清空数据库中的京东账单，然后重新上传文件进行测试")

if __name__ == "__main__":
    test_jd_duplicate_logic()