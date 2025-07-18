#!/usr/bin/env python3
"""
分析京东账单中重复的order_id
"""

import sys
import os
from collections import Counter

# 添加backend目录到Python路径
sys.path.append('/Users/chenxing/projects/my-bills-2/backend')

from parsers.jd_parser import JDParser

def analyze_duplicate_order_ids():
    """分析重复的order_id"""
    
    # 京东账单文件路径
    jd_file = '/Users/chenxing/projects/my-bills-2/bills/京东交易流水(申请时间2025年07月05日10时04分27秒)_739.csv'
    
    print("=== 京东账单重复Order ID分析 ===")
    print(f"分析文件: {jd_file}")
    
    if not os.path.exists(jd_file):
        print(f"错误: 文件不存在 {jd_file}")
        return
    
    # 解析文件
    parser = JDParser()
    result = parser.parse_file(jd_file)
    
    print(f"\n1. 基本统计:")
    print(f"   总记录数: {len(result.success_records)}")
    
    # 统计order_id
    order_id_counter = Counter()
    records_by_order_id = {}
    
    for i, record in enumerate(result.success_records):
        order_id = record.get("order_id")
        if order_id:
            order_id_counter[order_id] += 1
            if order_id not in records_by_order_id:
                records_by_order_id[order_id] = []
            records_by_order_id[order_id].append((i+1, record))
    
    print(f"   有order_id的记录: {sum(order_id_counter.values())}")
    print(f"   唯一order_id数量: {len(order_id_counter)}")
    
    # 找出重复的order_id
    duplicate_order_ids = {oid: count for oid, count in order_id_counter.items() if count > 1}
    
    print(f"\n2. 重复Order ID分析:")
    print(f"   重复order_id数量: {len(duplicate_order_ids)}")
    print(f"   重复记录总数: {sum(duplicate_order_ids.values())}")
    print(f"   因重复丢失的记录数: {sum(duplicate_order_ids.values()) - len(duplicate_order_ids)}")
    
    if duplicate_order_ids:
        print(f"\n3. 重复Order ID详情:")
        for order_id, count in duplicate_order_ids.items():
            print(f"\n   Order ID: {order_id} (出现 {count} 次)")
            
            records = records_by_order_id[order_id]
            for record_num, record in records:
                print(f"     记录 {record_num}:")
                print(f"       时间: {record.get('transaction_time')}")
                print(f"       金额: {record.get('amount')}")
                print(f"       描述: {record.get('transaction_desc')}")
                print(f"       商户: {record.get('merchant_name')}")
                print(f"       类型: {record.get('transaction_type')}")
                
                # 显示原始数据的关键字段
                raw_data = record.get('raw_data', {})
                if raw_data:
                    print(f"       原始状态: {raw_data.get('交易状态', 'N/A')}")
                    print(f"       原始类型: {raw_data.get('交易类型', 'N/A')}")
                print()
    
    # 验证计算
    total_records = len(result.success_records)
    unique_order_ids = len(order_id_counter)
    expected_loss = total_records - unique_order_ids
    
    print(f"\n4. 验证:")
    print(f"   总记录数: {total_records}")
    print(f"   唯一order_id数: {unique_order_ids}")
    print(f"   预期丢失记录数: {expected_loss}")
    print(f"   实际丢失记录数: 8")
    print(f"   计算是否正确: {'✅' if expected_loss == 8 else '❌'}")

if __name__ == "__main__":
    analyze_duplicate_order_ids()