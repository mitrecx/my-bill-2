#!/usr/bin/env python3
"""
调试京东账单批次内去重逻辑
"""

import sys
import os
from collections import defaultdict, Counter

# 添加backend目录到Python路径
sys.path.append('/Users/chenxing/projects/my-bills-2/backend')

from parsers.jd_parser import JDParser
from config.database import SessionLocal
from models.bill import Bill

def analyze_jd_dedup():
    """分析京东账单批次内去重问题"""
    
    # 京东账单文件路径
    jd_file = '/Users/chenxing/projects/my-bills-2/bills/京东交易流水(申请时间2025年07月05日10时04分27秒)_739.csv'
    
    print("=== 京东账单批次内去重分析 ===")
    print(f"分析文件: {jd_file}")
    
    if not os.path.exists(jd_file):
        print(f"错误: 文件不存在 {jd_file}")
        return
    
    # 使用解析器解析文件
    parser = JDParser()
    result = parser.parse_file(jd_file)
    
    print(f"\n1. 解析结果:")
    print(f"   成功记录数: {len(result.success_records)}")
    print(f"   失败记录数: {len(result.failed_records)}")
    
    # 分析批次内去重逻辑
    print(f"\n2. 批次内去重分析:")
    
    # 模拟upload.py中的去重逻辑
    seen_keys = set()
    duplicate_records = []
    unique_records = []
    
    for record in result.success_records:
        # 使用与upload.py相同的去重键
        dedup_key = (
            record.get('transaction_time'),
            record.get('amount'), 
            record.get('transaction_desc')
        )
        
        if dedup_key in seen_keys:
            duplicate_records.append(record)
            print(f"   发现重复记录: {dedup_key}")
            print(f"     订单ID: {record.get('order_id', 'N/A')}")
            print(f"     商户名: {record.get('merchant_name', 'N/A')}")
        else:
            seen_keys.add(dedup_key)
            unique_records.append(record)
    
    print(f"   原始记录数: {len(result.success_records)}")
    print(f"   去重后记录数: {len(unique_records)}")
    print(f"   重复记录数: {len(duplicate_records)}")
    
    # 分析重复记录的特征
    if duplicate_records:
        print(f"\n3. 重复记录详情:")
        for i, record in enumerate(duplicate_records):
            print(f"   重复记录 {i+1}:")
            print(f"     时间: {record.get('transaction_time')}")
            print(f"     金额: {record.get('amount')}")
            print(f"     描述: {record.get('transaction_desc')}")
            print(f"     订单ID: {record.get('order_id', 'N/A')}")
            print(f"     商户名: {record.get('merchant_name', 'N/A')}")
            print()
    
    # 分析去重键的分布
    print(f"\n4. 去重键分析:")
    key_counts = Counter()
    for record in result.success_records:
        dedup_key = (
            record.get('transaction_time'),
            record.get('amount'), 
            record.get('transaction_desc')
        )
        key_counts[dedup_key] += 1
    
    # 找出出现多次的键
    duplicate_keys = {k: v for k, v in key_counts.items() if v > 1}
    print(f"   总去重键数: {len(key_counts)}")
    print(f"   重复键数: {len(duplicate_keys)}")
    
    if duplicate_keys:
        print(f"   重复键详情:")
        for key, count in duplicate_keys.items():
            print(f"     键: {key}")
            print(f"     出现次数: {count}")
            
            # 找出使用这个键的所有记录
            matching_records = []
            for record in result.success_records:
                record_key = (
                    record.get('transaction_time'),
                    record.get('amount'), 
                    record.get('transaction_desc')
                )
                if record_key == key:
                    matching_records.append(record)
            
            print(f"     相关记录:")
            for j, record in enumerate(matching_records):
                print(f"       记录{j+1}: order_id={record.get('order_id', 'N/A')}, merchant={record.get('merchant_name', 'N/A')}")
            print()
    
    # 检查数据库中的记录
    print(f"\n5. 数据库记录检查:")
    try:
        db = SessionLocal()
        
        # 统计数据库中的京东账单
        db_count = db.query(Bill).filter(
            Bill.source_type == 'jd',
            Bill.source_filename == '京东交易流水(申请时间2025年07月05日10时04分27秒)_739.csv'
        ).count()
        
        print(f"   数据库中京东账单数: {db_count}")
        print(f"   预期记录数: {len(unique_records)}")
        print(f"   差异: {len(unique_records) - db_count}")
        
        db.close()
        
    except Exception as e:
        print(f"   数据库查询错误: {e}")
    
    # 总结
    print(f"\n=== 分析总结 ===")
    print(f"解析成功记录: {len(result.success_records)}")
    print(f"批次内去重后: {len(unique_records)}")
    print(f"批次内重复记录: {len(duplicate_records)}")
    print(f"数据库实际记录: {db_count if 'db_count' in locals() else '未知'}")
    
    if duplicate_records:
        print(f"\n问题分析:")
        print(f"- 发现 {len(duplicate_records)} 条记录因批次内去重被跳过")
        print(f"- 去重键使用 (transaction_time, amount, transaction_desc)")
        print(f"- 这可能导致不同订单但时间、金额、描述相同的记录被误判为重复")
        print(f"- 建议考虑将 order_id 加入去重键或调整去重逻辑")

if __name__ == "__main__":
    analyze_jd_dedup()