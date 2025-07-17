#!/usr/bin/env python3
"""
测试修复后的京东账单上传功能
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from datetime import datetime
from config.database import SessionLocal
from models.bill import Bill
from parsers.jd_parser import JDParser
from api.upload import find_existing_jd_bill, get_or_create_category
from models.user import User
from models.family import FamilyMember

def test_jd_upload_fix():
    """测试修复后的京东账单上传功能"""
    
    print("=== 测试修复后的京东账单上传功能 ===\n")
    
    # 1. 解析京东账单文件
    print("1. 解析京东账单文件...")
    parser = JDParser()
    file_path = "/Users/chenxing/projects/my-bills-2/bills/京东交易流水(申请时间2025年07月05日10时04分27秒)_739.csv"
    
    result = parser.parse_file(file_path)
    print(f"   解析成功记录: {len(result.success_records)}")
    
    # 2. 模拟上传过程
    print("\n2. 模拟上传过程...")
    
    db = SessionLocal()
    try:
        # 假设family_id为1
        family_id = 1
        source_filename = "京东交易流水(申请时间2025年07月05日10时04分27秒)_739.csv"
        
        new_records = 0
        updated_records = 0
        skipped_records = 0
        
        for i, record in enumerate(result.success_records):
            print(f"   处理记录 {i+1}/{len(result.success_records)}: {record.get('transaction_desc', '')[:30]}...")
            
            # 查找已存在的记录
            existing_bill = find_existing_jd_bill(record, family_id, db)
            
            if existing_bill:
                print(f"     -> 发现已存在记录，更新")
                updated_records += 1
                
                # 更新已存在记录的字段
                existing_bill.transaction_time = record["transaction_time"]
                existing_bill.amount = record["amount"]
                existing_bill.transaction_desc = record["transaction_desc"]
                existing_bill.counter_party = record.get("merchant_name", "")
                existing_bill.transaction_type = record.get("transaction_type", "")
                existing_bill.raw_data = record.get("raw_data", {})
                existing_bill.source_filename = source_filename
                existing_bill.updated_at = datetime.now()
                
            else:
                print(f"     -> 新记录，创建")
                new_records += 1
                
                # 创建新记录
                new_bill = Bill(
                    family_id=family_id,
                    transaction_time=record["transaction_time"],
                    amount=record["amount"],
                    transaction_desc=record["transaction_desc"],
                    counter_party=record.get("merchant_name", ""),
                    transaction_type=record.get("transaction_type", ""),
                    source_type="jd",
                    source_filename=source_filename,
                    raw_data=record.get("raw_data", {}),
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                
                db.add(new_bill)
            
            # 每10条记录提交一次
            if (i + 1) % 10 == 0:
                db.commit()
                print(f"     已提交前 {i+1} 条记录")
        
        # 最终提交
        db.commit()
        
        print(f"\n   处理完成:")
        print(f"   - 新增记录: {new_records}")
        print(f"   - 更新记录: {updated_records}")
        print(f"   - 跳过记录: {skipped_records}")
        print(f"   - 总计处理: {new_records + updated_records + skipped_records}")
        
        # 3. 验证数据库结果
        print("\n3. 验证数据库结果...")
        
        jd_bills = db.query(Bill).filter(Bill.source_type == "jd").all()
        print(f"   数据库中京东账单总数: {len(jd_bills)}")
        
        # 检查order_id分布
        order_id_count = {}
        for bill in jd_bills:
            order_id = bill.raw_data.get("order_id") if bill.raw_data else None
            if order_id:
                order_id_count[order_id] = order_id_count.get(order_id, 0) + 1
        
        unique_order_ids = len(order_id_count)
        duplicate_order_ids = {oid: count for oid, count in order_id_count.items() if count > 1}
        
        print(f"   唯一order_id数量: {unique_order_ids}")
        print(f"   重复order_id数量: {len(duplicate_order_ids)}")
        
        if duplicate_order_ids:
            print("   重复的order_id:")
            for order_id, count in duplicate_order_ids.items():
                print(f"   - {order_id}: {count}次")
                
                # 显示重复记录的详情
                duplicate_bills = [b for b in jd_bills 
                                 if b.raw_data and b.raw_data.get("order_id") == order_id]
                for j, bill in enumerate(duplicate_bills):
                    print(f"     记录{j+1}: {bill.transaction_time} | {bill.amount} | {bill.transaction_desc[:30]}...")
        
        # 4. 结果分析
        print("\n4. 结果分析...")
        expected_records = len(result.success_records)
        actual_records = len(jd_bills)
        
        print(f"   预期记录数: {expected_records}")
        print(f"   实际记录数: {actual_records}")
        print(f"   记录差异: {expected_records - actual_records}")
        
        if actual_records == expected_records:
            print("   ✅ 修复成功！所有记录都已正确保存")
        else:
            print("   ❌ 仍有记录丢失，需要进一步调试")
        
    except Exception as e:
        print(f"❌ 上传过程出错: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_jd_upload_fix()