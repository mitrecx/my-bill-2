#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from parsers.jd_parser import JDParser
from collections import defaultdict

def analyze_duplicates():
    """分析重复记录的详细情况"""
    file_path = "/Users/chenxing/projects/my-bills-2/bills/京东交易流水(申请时间2025年07月05日10时04分27秒)_739.csv"
    
    # 解析文件
    parser = JDParser()
    parse_result = parser.parse_file(file_path)
    records = parse_result.success_records
    
    print(f"总记录数: {len(records)}")
    
    # 分析订单号重复
    order_id_count = defaultdict(list)
    for i, record in enumerate(records):
        order_id = record.get('order_id')
        if order_id:
            order_id_count[order_id].append((i+1, record))
    
    print("\n=== 订单号重复分析 ===")
    duplicate_order_ids = {k: v for k, v in order_id_count.items() if len(v) > 1}
    print(f"重复订单号数量: {len(duplicate_order_ids)}")
    
    for order_id, records_list in duplicate_order_ids.items():
        print(f"\n订单号 {order_id} 出现 {len(records_list)} 次:")
        for record_num, record in records_list:
            print(f"  记录 {record_num}: {record['transaction_time']} - {record['amount']} - {record['merchant_name']}")
    
    # 分析组合字段重复（时间+金额+商户）
    print("\n=== 组合字段重复分析 ===")
    combo_count = defaultdict(list)
    for i, record in enumerate(records):
        combo_key = (
            record.get('transaction_time'),
            record.get('amount'),
            record.get('merchant_name')
        )
        combo_count[combo_key].append((i+1, record))
    
    duplicate_combos = {k: v for k, v in combo_count.items() if len(v) > 1}
    print(f"重复组合字段数量: {len(duplicate_combos)}")
    
    for combo_key, records_list in duplicate_combos.items():
        time_str, amount, merchant = combo_key
        print(f"\n组合 ({time_str}, {amount}, {merchant}) 出现 {len(records_list)} 次:")
        for record_num, record in records_list:
            print(f"  记录 {record_num}: 订单号={record.get('order_id')} - 描述={record.get('transaction_desc', '')[:50]}...")
    
    # 统计被跳过的记录（根据日志）
    skipped_records = [9, 10, 11, 75, 76, 78, 94, 98, 104]  # 从日志中获取的被跳过记录号
    
    print(f"\n=== 被跳过记录详细分析 ===")
    print(f"被跳过记录数: {len(skipped_records)}")
    
    for record_num in skipped_records:
        if record_num <= len(records):
            record = records[record_num - 1]  # 转换为0索引
            print(f"\n记录 {record_num}:")
            print(f"  订单号: {record.get('order_id')}")
            print(f"  时间: {record.get('transaction_time')}")
            print(f"  金额: {record.get('amount')}")
            print(f"  商户: {record.get('merchant_name')}")
            print(f"  描述: {record.get('transaction_desc', '')[:100]}...")
            
            # 检查是否有相同订单号的其他记录
            same_order_records = [r for r in records if r.get('order_id') == record.get('order_id')]
            if len(same_order_records) > 1:
                print(f"  -> 订单号重复，共 {len(same_order_records)} 条记录")
            
            # 检查是否有相同组合的其他记录
            combo_key = (record.get('transaction_time'), record.get('amount'), record.get('merchant_name'))
            same_combo_records = [r for r in records if (r.get('transaction_time'), r.get('amount'), r.get('merchant_name')) == combo_key]
            if len(same_combo_records) > 1:
                print(f"  -> 组合字段重复，共 {len(same_combo_records)} 条记录")

if __name__ == "__main__":
    analyze_duplicates()