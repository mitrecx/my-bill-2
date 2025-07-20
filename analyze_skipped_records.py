#!/usr/bin/env python3
"""
分析被跳过的重复记录
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from parsers.jd_parser import JDParser
import json

def analyze_skipped_records():
    """分析被跳过的记录"""
    
    # 文件路径
    file_path = "/Users/chenxing/projects/my-bills-2/bills/京东交易流水(申请时间2025年07月05日10时04分27秒)_739.csv"
    
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return
    
    # 解析文件
    parser = JDParser()
    parse_result = parser.parse_file(file_path)
    records = parse_result.success_records
    
    print(f"总记录数: {len(records)}")
    print(f"成功记录数: {parse_result.success_count}")
    print(f"失败记录数: {parse_result.failed_count}")
    if parse_result.errors:
        print(f"解析错误: {parse_result.errors[:5]}")  # 只显示前5个错误
    
    # 根据日志中的记录号分析被跳过的记录
    skipped_record_numbers = [28, 29, 68, 75, 76, 78, 94, 98, 104]
    
    print(f"\n=== 被跳过的记录分析 ===")
    
    # 按订单号分组
    order_id_groups = {}
    for i, record in enumerate(records):
        raw_data = record.get("raw_data", {})
        order_id = raw_data.get("order_id")
        if order_id:
            if order_id not in order_id_groups:
                order_id_groups[order_id] = []
            order_id_groups[order_id].append((i + 1, record))  # 记录号从1开始
    
    # 找出有多条记录的订单号
    duplicate_order_ids = {k: v for k, v in order_id_groups.items() if len(v) > 1}
    
    print(f"\n发现 {len(duplicate_order_ids)} 个重复的订单号:")
    for order_id, records_list in duplicate_order_ids.items():
        print(f"\n订单号: {order_id}")
        for record_num, record in records_list:
            print(f"  记录 {record_num}: 时间={record.get('transaction_time')}, 金额={record.get('amount')}, 描述={record.get('transaction_desc', '')[:50]}...")
            if record_num in skipped_record_numbers:
                print(f"    *** 这条记录被跳过了 ***")
    
    # 分析被跳过的记录
    print(f"\n=== 详细分析被跳过的记录 ===")
    for record_num in skipped_record_numbers:
        if record_num <= len(records):
            record = records[record_num - 1]  # 记录号从1开始，数组从0开始
            raw_data = record.get("raw_data", {})
            print(f"\n记录 {record_num}:")
            print(f"  订单号: {raw_data.get('order_id')}")
            print(f"  时间: {record.get('transaction_time')}")
            print(f"  金额: {record.get('amount')}")
            print(f"  商户: {record.get('merchant_name')}")
            print(f"  描述: {record.get('transaction_desc', '')[:100]}...")
            print(f"  支付方式: {raw_data.get('payment_method')}")
            print(f"  状态: {raw_data.get('transaction_status')}")

if __name__ == "__main__":
    analyze_skipped_records()