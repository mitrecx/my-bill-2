#!/usr/bin/env python3
"""
分析招商银行PDF中的重复记录问题
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from parsers.cmb_parser import CMBParser
from collections import defaultdict

def analyze_duplicates():
    """分析PDF中的重复记录"""
    
    # 解析PDF文件
    pdf_path = "/Users/chenxing/projects/my-bills-2/bills/招商银行交易流水(申请时间2025年07月05日10时27分05秒).pdf"
    
    print("=== 分析招商银行PDF重复记录问题 ===")
    print(f"文件: {pdf_path}")
    
    parser = CMBParser()
    result = parser.parse_file(pdf_path)
    records = result.success_records
    
    print(f"\n解析结果:")
    print(f"  总记录数: {result.total_count}")
    print(f"  成功记录数: {result.success_count}")
    print(f"  失败记录数: {result.failed_count}")
    
    # 分析重复记录
    duplicate_key_counts = defaultdict(list)
    
    for i, record in enumerate(records):
        # 使用与上传API相同的重复检测逻辑
        transaction_time = record.get('transaction_time')
        if isinstance(transaction_time, str):
            time_str = transaction_time.replace(' ', 'T')
        elif transaction_time:
            time_str = str(transaction_time)
        else:
            time_str = ''
            
        key = (
            time_str,
            str(record.get('amount', '')),
            record.get('transaction_desc', '')
        )
        duplicate_key_counts[key].append((i + 1, record))
    
    # 找出重复的记录
    duplicates = {k: v for k, v in duplicate_key_counts.items() if len(v) > 1}
    
    print(f"\n重复记录分析:")
    print(f"  唯一记录组数: {len(duplicate_key_counts)}")
    print(f"  重复记录组数: {len(duplicates)}")
    
    if duplicates:
        print(f"\n详细重复记录:")
        total_duplicated_records = 0
        for key, record_list in duplicates.items():
            print(f"\n重复组 - 关键字: {key}")
            for record_num, record in record_list:
                print(f"  记录 {record_num}: {record}")
                total_duplicated_records += 1
        
        # 计算实际应该保存的记录数
        unique_records = len(duplicate_key_counts)
        duplicated_records = total_duplicated_records - len(duplicates)  # 减去每组保留的1条
        
        print(f"\n统计:")
        print(f"  总记录数: {len(records)}")
        print(f"  重复记录数: {duplicated_records}")
        print(f"  应保存记录数: {unique_records}")
        print(f"  实际保存记录数: 60")
        print(f"  差异: {unique_records - 60}")
    
    # 检查具体的重复记录
    print(f"\n=== 检查具体重复记录 ===")
    for key, record_list in duplicates.items():
        print(f"\n重复组: {key}")
        for i, (record_num, record) in enumerate(record_list):
            status = "保留" if i == 0 else "跳过"
            print(f"  记录 {record_num} ({status}): ")
            print(f"    时间: {record.get('transaction_time')}")
            print(f"    金额: {record.get('amount')}")
            print(f"    描述: {record.get('transaction_desc')}")
            print(f"    对手方: {record.get('counter_party')}")

if __name__ == "__main__":
    analyze_duplicates()