#!/usr/bin/env python3
"""
模拟京东账单上传过程，找出数据丢失的具体位置
"""

import sys
import os
from datetime import datetime, timedelta

# 添加backend目录到Python路径
sys.path.append('/Users/chenxing/projects/my-bills-2/backend')

from parsers.jd_parser import JDParser
from config.database import SessionLocal
from models.bill import Bill

def find_existing_jd_bill(record, family_id, db):
    """模拟find_existing_jd_bill函数"""
    order_id = record.get("order_id")
    
    if not order_id:
        return None
    
    # 通过order_id查找已存在的记录
    existing_bill = db.query(Bill).filter(
        Bill.order_id == order_id,
        Bill.family_id == family_id
    ).first()
    
    return existing_bill

def simulate_upload_process():
    """模拟完整的上传过程"""
    
    # 京东账单文件路径
    jd_file = '/Users/chenxing/projects/my-bills-2/bills/京东交易流水(申请时间2025年07月05日10时04分27秒)_739.csv'
    family_id = 1  # 假设family_id为1
    source_type = "jd"
    
    print("=== 模拟京东账单上传过程 ===")
    print(f"分析文件: {jd_file}")
    
    if not os.path.exists(jd_file):
        print(f"错误: 文件不存在 {jd_file}")
        return
    
    # 1. 解析文件
    parser = JDParser()
    result = parser.parse_file(jd_file)
    
    print(f"\n1. 解析结果:")
    print(f"   成功记录数: {len(result.success_records)}")
    print(f"   失败记录数: {len(result.failed_records)}")
    
    # 2. 模拟处理过程
    print(f"\n2. 模拟处理过程:")
    
    success_count = 0
    failed_count = 0
    updated_count = 0
    skipped_count = 0
    
    # 用于批次内去重的集合
    batch_records = set()
    
    # 数据库连接
    db = SessionLocal()
    
    try:
        for i, record in enumerate(result.success_records):
            print(f"\n   处理记录 {i+1}/{len(result.success_records)}:")
            
            # 检查必需字段
            required_fields = ["amount", "transaction_time", "transaction_type"]
            missing_fields = [field for field in required_fields if field not in record or record[field] is None]
            
            if missing_fields:
                print(f"     ❌ 缺少必需字段: {missing_fields}")
                failed_count += 1
                continue
            
            # 批次内去重检查
            record_key = (
                record["transaction_time"].isoformat() if hasattr(record["transaction_time"], 'isoformat') else str(record["transaction_time"]),
                str(record["amount"]),
                record.get("transaction_desc", "")
            )
            
            if record_key in batch_records:
                print(f"     ⚠️  批次内重复，跳过")
                skipped_count += 1
                continue
            
            batch_records.add(record_key)
            
            # 查找已存在的记录
            existing_bill = find_existing_jd_bill(record, family_id, db)
            
            if existing_bill:
                print(f"     🔄 找到已存在记录，将更新 (order_id: {record.get('order_id')})")
                updated_count += 1
            else:
                print(f"     ✅ 新记录，将创建 (order_id: {record.get('order_id')})")
                success_count += 1
        
        print(f"\n3. 处理统计:")
        print(f"   总记录数: {len(result.success_records)}")
        print(f"   新增记录: {success_count}")
        print(f"   更新记录: {updated_count}")
        print(f"   跳过记录: {skipped_count}")
        print(f"   失败记录: {failed_count}")
        print(f"   预期保存: {success_count + updated_count}")
        
        # 4. 检查数据库实际记录
        print(f"\n4. 数据库实际记录:")
        db_count = db.query(Bill).filter(
            Bill.source_type == 'jd',
            Bill.source_filename == '京东交易流水(申请时间2025年07月05日10时04分27秒)_739.csv'
        ).count()
        
        print(f"   数据库中记录数: {db_count}")
        print(f"   预期记录数: {success_count + updated_count}")
        print(f"   差异: {(success_count + updated_count) - db_count}")
        
        # 5. 分析order_id情况
        print(f"\n5. Order ID 分析:")
        
        # 统计解析记录中的order_id情况
        records_with_order_id = 0
        records_without_order_id = 0
        order_ids = set()
        
        for record in result.success_records:
            order_id = record.get("order_id")
            if order_id:
                records_with_order_id += 1
                order_ids.add(order_id)
            else:
                records_without_order_id += 1
        
        print(f"   解析记录中有order_id的: {records_with_order_id}")
        print(f"   解析记录中无order_id的: {records_without_order_id}")
        print(f"   唯一order_id数量: {len(order_ids)}")
        
        # 统计数据库中的order_id情况
        db_bills = db.query(Bill).filter(
            Bill.source_type == 'jd',
            Bill.source_filename == '京东交易流水(申请时间2025年07月05日10时04分27秒)_739.csv'
        ).all()
        
        db_with_order_id = 0
        db_without_order_id = 0
        db_order_ids = set()
        
        for bill in db_bills:
            if bill.order_id:
                db_with_order_id += 1
                db_order_ids.add(bill.order_id)
            else:
                db_without_order_id += 1
        
        print(f"   数据库中有order_id的: {db_with_order_id}")
        print(f"   数据库中无order_id的: {db_without_order_id}")
        print(f"   数据库唯一order_id数量: {len(db_order_ids)}")
        
        # 6. 找出缺失的记录
        print(f"\n6. 缺失记录分析:")
        
        # 找出解析成功但数据库中不存在的order_id
        missing_order_ids = order_ids - db_order_ids
        if missing_order_ids:
            print(f"   缺失的order_id数量: {len(missing_order_ids)}")
            print(f"   缺失的order_id: {list(missing_order_ids)[:10]}")  # 只显示前10个
        else:
            print(f"   没有缺失的order_id")
        
        # 找出没有order_id的记录差异
        no_order_id_diff = records_without_order_id - db_without_order_id
        if no_order_id_diff > 0:
            print(f"   缺失的无order_id记录: {no_order_id_diff}")
        
    finally:
        db.close()

if __name__ == "__main__":
    simulate_upload_process()